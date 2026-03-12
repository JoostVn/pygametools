import numpy as np
import numpy.typing as npt
from pygametools.plots.types import CoordinatePair, Domain
from .drawing import PlotTheme, PlotMetrics, PlotRenderer, DrawContext
from pygametools.color import Color
from abc import ABC, abstractmethod
from math import floor, log10
from typing import Literal
import pygame


class Canvas:

    def __init__(
            self,
            pos: tuple[int, int],
            dim: tuple[int, int],
            xdom: Domain,
            ydom: Domain,
            **kwargs):
        """
        Container for all plot elements.

        Args:
            pos: Canvas position (x, y) in screen coordinates
            dim: Canvas dimensions (width, height) in pixels
            xdom: X-axis domain (min, max) in data coordinates
            ydom: Y-axis domain (min, max) in data coordinates
            kwargs: TODO: find out where kwargs are used and update docstring
        """
        # Initialise element registry before creating metrics so the callback
        # `_on_metrics_changed` is safe to call even if a setter fires during construction.
        self._elements: list[Element] = []

        metrics = PlotMetrics(pos, dim, xdom, ydom, on_change=self._on_metrics_changed)
        theme = PlotTheme(**kwargs)
        renderer = PlotRenderer(metrics.dim, metrics.axes_dim)
        self.drawcontext = DrawContext(theme=theme, metrics=metrics, renderer=renderer)

        # Build element registry
        self.axes = Axes()
        self.title = Title(kwargs.get("title", ""))
        self.axisx = Axis(Axis.X)
        self.axisy = Axis(Axis.Y)
        self._elements = [self.axes, self.title, self.axisx, self.axisy]

        # Push current metrics to all elements so they compute their initial state.
        # TODO: support for no value for metric name? Passing None is weird.
        self._on_metrics_changed(None)

    def _on_metrics_changed(self, metric_name: str | None):
        """
        Mediator: called by PlotMetrics when any metric changes.

        Resizes renderer surfaces when layout-affecting metrics change, then
        fans the notification out to every registered element.
        """
        metrics = self.drawcontext.metrics
        renderer = self.drawcontext.renderer

        # Only on dim/axes padding: resize the surfaces of plotrenderer
        if metric_name in ('dim', None, 'xpad', 'ypad'):
            renderer.resize(metrics.dim, metrics.axes_dim)

        # For all changes: call metric change on elements
        for element in self._elements:
            element.on_metrics_changed(metric_name, metrics)

    def draw(self, surface: pygame.Surface):
        # TODO: Just rename drawcontext to ctx?
        ctx = self.drawcontext
        ctx.renderer.clear(ctx.theme)

        # Border around the whole canvas
        ctx.renderer.rect(
            np.array([0, 0]), ctx.metrics.dim, ctx.metrics,
            facecol=ctx.theme.colors["canvas_bg"],
            linecol=ctx.theme.colors["canvas_line"],
            on_axes=False)

        for element in self._elements:
            element.draw(ctx)

        ctx.renderer.draw(surface, ctx.metrics)


class Element(ABC):

    @abstractmethod
    def on_metrics_changed(self, metric_name: str | None, metrics: PlotMetrics):
        """
        Called by Canvas whenever a metric changes.

        `metric_name` is the name of the changed metric (e.g. 'dim',
        'xdom'), or None when all metrics should be considered changed
        (e.g. on initial setup). `metrics` is the current `PlotMetrics`
        instance; elements must not store a permanent reference to it.
        """
        pass

    @abstractmethod
    def draw(self, ctx: DrawContext):
        pass


class Axes(Element):

    def __init__(self):
        """Contains the rectangular plot area within the Canvas."""
        self.dim = np.zeros(2)
        self.pos = np.zeros(2)

    def on_metrics_changed(self, metric_name: str | None, metrics: PlotMetrics):
        # TODO: pos and dim should probably be private methods here to preserve a single source of truth
        # Or, even better, just fethc the dimensions directly from PlotMetrics at draw
        if metric_name in ('pos', 'xpad', 'ypad', None):
            self.pos = metrics.axes_pos
        if metric_name in ('dim', 'xpad', 'ypad', None):
            self.dim = metrics.axes_dim

    def draw(self, ctx: DrawContext):
        ctx.renderer.rect(
            ctx.metrics.axes_pos - 1, ctx.metrics.axes_dim + 2, ctx.metrics,
            facecol=ctx.theme.colors["axes_bg"],
            linecol=ctx.theme.colors["axes_line"],
            on_axes=False)


class Axis(Element):
    
    # TODO: should this be an enum?
    
    X = 0
    Y = 1
    FIXED_TICK_POSITIONS = 0
    FIXED_TICK_VALUES = 1
    LABELS_NUMERICAL = 0
    LABELS_TEXT = 1

    def __init__(self, orientation: int, **kwargs):
        """
        Axis element containing ticks and labels.

        Args:
            orientation: `Axis.X` or `Axis.Y`
        """
        self.orientation = orientation
        self.tick_margin = kwargs.get("margin", 0.1)
        self.tick_length = kwargs.get("length", 3)
        self.num_ticks = kwargs.get("num_ticks", 6)
        self.pos_ticks = np.zeros((0, 2))
        self.labels = None

        # Tick mode: either fixed locations or fixed values
        self.tick_mode = None
        self.label_mode = None

        # Most recent metrics snapshot; set on first on_metrics_changed call.
        # TODO: remove reference to metrics. Should only be passed on method calls
        self._metrics: PlotMetrics | None = None

    def on_metrics_changed(self, metric_name: str | None, metrics: PlotMetrics):
        """Recompute tick positions and labels whenever layout or domain changes."""
        self._metrics = metrics
        self._recompute_ticks(metrics)

    # TODO: just set from `on_metrics_changed`
    def _dom(self, metrics: PlotMetrics) -> npt.NDArray[np.float64]:
        return metrics.xdom if self.orientation == Axis.X else metrics.ydom

    def _span(self, metrics: PlotMetrics) -> float:
        return float(np.diff(self._dom(metrics))[0])

    @property
    def text_va(self) -> Literal['bottom', 'center']:
        return 'bottom' if self.orientation == Axis.X else 'center'

    @property
    def text_ha(self) -> Literal['center', 'right']:
        return 'center' if self.orientation == Axis.X else 'right'

    @property
    def tick_direction(self) -> np.ndarray:
        return np.array((0, 1)) if self.orientation == Axis.X else np.array((-1, 0))

    @property
    def axis_direction(self) -> np.ndarray:
        return np.array((1, 0)) if self.orientation == Axis.X else np.array((0, -1))

    def _recompute_ticks(self, metrics: PlotMetrics):
        """Recalculate tick positions and numerical labels."""
        # TODO: move tick updating to its own method such that it can also be called from set_num_ticks
        axis_line_endpoints = np.vstack([
            metrics.axes_sw,
            metrics.axes_sw + self.axis_direction * metrics.axes_dim])

        if self.tick_mode == Axis.FIXED_TICK_POSITIONS:
            offset = self.axis_direction * self.tick_margin * metrics.axes_dim
            self.pos_ticks = np.linspace(
                axis_line_endpoints[0] + offset,
                axis_line_endpoints[1] - offset,
                self.num_ticks,
                endpoint=True)

        elif self.tick_mode == Axis.FIXED_TICK_VALUES:
            raise NotImplementedError

        if self.label_mode == Axis.LABELS_NUMERICAL:
            self._update_numerical_labels(metrics)
        elif self.label_mode == Axis.LABELS_TEXT:
            raise NotImplementedError

    def _update_numerical_labels(self, metrics: PlotMetrics):
        """Format tick labels based on the current domain magnitude."""
        dom = self._dom(metrics)
        span = self._span(metrics)
        numbers = np.linspace(
            dom[0] + span * self.tick_margin,
            dom[1] - span * self.tick_margin,
            num=self.num_ticks,
            endpoint=True)

        order_of_magnitude = floor(log10(max(abs(numbers))))

        if -4 < order_of_magnitude < 5:
            round_to = max(0, 1 - order_of_magnitude)
            self.labels = [f"%.{round_to}f" % x for x in numbers]
        else:
            self.labels = [
                np.format_float_scientific(x, precision=0, trim='-', sign=False)
                for x in numbers]

    def set_tick_num(self, num_ticks: int):
        """
        Set a fixed number of evenly spaced tick locations.
        Ticks will change their value to keep their relative location.
        """
        self.tick_mode = Axis.FIXED_TICK_POSITIONS
        self.label_mode = Axis.LABELS_NUMERICAL
        self.num_ticks = num_ticks
        if self._metrics is not None:
            self._recompute_ticks(self._metrics)

    def set_tick_pos(self, ticks: npt.NDArray, labels: list[str] | None = None):
        """
        Set custom ticks fixed positions with optional string labels.
        Ticks will change their location to retain their value.
        """
        self.tick_mode = Axis.FIXED_TICK_VALUES
        self.label_mode = Axis.LABELS_TEXT
        raise NotImplementedError

    def set_labels(self, labels: tuple):
        pass

    def draw(self, ctx: DrawContext):
        if self.labels is None or len(self.labels) == 0:
            return

        tick_vector = self.tick_direction * self.tick_length
        font, color = ctx.theme.fonts["tick"]
        text_offset = self.tick_direction * (2 + self.tick_length)

        for pos, label in zip(self.pos_ticks, self.labels):
            ctx.renderer.vector(
                pos, tick_vector, ctx.theme.colors["axes_line"],
                ctx.metrics, on_axes=False)
            ctx.renderer.text(
                label, font, color, pos,
                self.text_ha, self.text_va, ctx.metrics,
                text_offset, on_axes=False)


class Title(Element):

    def __init__(self, title: str):
        """Title string centered above the axes."""
        self.title = title
        self.pos = np.zeros(2)

    def on_metrics_changed(self, metric_name: str | None, metrics: PlotMetrics):
        self.pos = np.array([
            metrics.axes_xpad[0] + metrics.axes_dim[0] / 2,
            metrics.axes_ypad[0] / 2])

    def draw(self, ctx: DrawContext):
        font, color = ctx.theme.fonts["title"]
        ctx.renderer.text(
            self.title, font, color, self.pos,
            ha="center", va="center", metrics=ctx.metrics, on_axes=False)


class Legend(Element):

    def __init__(self):
        """Legend element for plots (stub)."""
        pass

    def on_metrics_changed(self, metric_name: str | None, metrics: PlotMetrics):
        pass

    def draw(self, ctx: DrawContext):
        pass
