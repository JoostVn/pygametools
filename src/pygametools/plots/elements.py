import numpy as np
import numpy.typing as npt
from pygametools.plots.types import MetricCoordinatePair, Domain
from .drawing import PlotTheme, PlotMetrics, PlotRenderer, DrawContext
from .plot_types import PlotType
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
        self._elements: list[Element | PlotType] = []

        metrics = PlotMetrics(pos, dim, xdom, ydom)
        theme = PlotTheme(**kwargs)
        renderer = PlotRenderer(metrics.dim, metrics.axes_dim)
        self._ctx = DrawContext(theme=theme, metrics=metrics, renderer=renderer)

        # Build element registry
        self.axes = Axes()
        self.title = Title(kwargs.get("title", ""))
        self.axisx = Axis(Axis.X)
        self.axisy = Axis(Axis.Y)
        self._elements = [self.axes, self.title, self.axisx, self.axisy]

        self.domain_margin: float = 0.05

        # Push current metrics to all elements so they compute their initial state.
        self._on_metrics_changed()

    def _on_metrics_changed(self, metric_name: str | None = None):
        """
        Called by Canvas property setters when any metric changes.

        Resizes renderer surfaces when layout-affecting metrics change, then
        fans the notification out to every registered element.
        """
        metrics = self._ctx.metrics
        renderer = self._ctx.renderer

        # Only on dim/axes padding: resize the surfaces of plotrenderer
        if metric_name in ('dim', None, 'xpad', 'ypad'):
            renderer.resize(metrics.dim, metrics.axes_dim)

        # For all changes: call metric change on elements
        for element in self._elements:
            element.on_metrics_changed(metric_name, metrics)
            
    def draw(self, surface: pygame.Surface):
        ctx = self._ctx
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

    def add_plot(self, plot: PlotType):
        """Register a plot element and wire up its data-added callback."""
        plot._on_data_added = self._check_domain_expansion
        self._elements.append(plot)
        plot.on_metrics_changed(None, self._ctx.metrics)

    def _check_domain_expansion(self, points: np.ndarray):
        """Expand xdom/ydom if new data falls outside the current domain.

        When expansion is needed, a margin of `domain_margin * new_span` is
        added so the data doesn't sit right at the edge. Checking against the
        pre-margin bounds prevents the margin from compounding on every call.
        """
        xdom = self._ctx.metrics.xdom
        ydom = self._ctx.metrics.ydom
        xmin, xmax = points[:,0].min(), points[:,0].max()
        ymin, ymax = points[:,1].min(), points[:,1].max()

        if xmin < xdom[0] or xmax > xdom[1]:
            lo, hi = min(xmin, xdom[0]), max(xmax, xdom[1])
            pad = self.domain_margin * (hi - lo)
            self.xdom = (lo - pad, hi + pad)

        if ymin < ydom[0] or ymax > ydom[1]:
            lo, hi = min(ymin, ydom[0]), max(ymax, ydom[1])
            pad = self.domain_margin * (hi - lo)
            self.ydom = (lo - pad, hi + pad)

    # ---- Settable metric properties
    @property
    def pos(self) -> npt.NDArray[np.int_]:
        return self._ctx.metrics.pos

    @pos.setter
    def pos(self, val: MetricCoordinatePair):
        self._ctx.metrics._pos = np.array(val, dtype=int)
        self._on_metrics_changed('pos')

    @property
    def dim(self) -> npt.NDArray[np.int_]:
        return self._ctx.metrics.dim

    @dim.setter
    def dim(self, val: MetricCoordinatePair):
        self._ctx.metrics._dim = np.array(val, dtype=int)
        self._on_metrics_changed('dim')

    @property
    def xdom(self) -> npt.NDArray[np.float64]:
        return self._ctx.metrics.xdom

    @xdom.setter
    def xdom(self, val: Domain):
        assert val[0] < val[1], "Invalid x domain"
        self._ctx.metrics._xdom = np.array(val, dtype=float)
        self._on_metrics_changed('xdom')

    @property
    def ydom(self) -> npt.NDArray[np.float64]:
        return self._ctx.metrics.ydom

    @ydom.setter
    def ydom(self, val: Domain):
        assert val[0] < val[1], "Invalid y domain"
        self._ctx.metrics._ydom = np.array(val, dtype=float)
        self._on_metrics_changed('ydom')

    @property
    def axes_xpad(self) -> npt.NDArray[np.int_]:
        return self._ctx.metrics.axes_xpad

    @axes_xpad.setter
    def axes_xpad(self, val: MetricCoordinatePair):
        self._ctx.metrics._axes_xpad = np.array(val, dtype=int)
        self._on_metrics_changed('xpad')

    @property
    def axes_ypad(self) -> npt.NDArray[np.int_]:
        return self._ctx.metrics.axes_ypad

    @axes_ypad.setter
    def axes_ypad(self, val: MetricCoordinatePair):
        self._ctx.metrics._axes_ypad = np.array(val, dtype=int)
        self._on_metrics_changed('ypad')

    # ---- Read-only derived properties
    @property
    def axes_pos(self) -> npt.NDArray[np.int_]:
        return self._ctx.metrics.axes_pos

    @property
    def axes_dim(self) -> npt.NDArray[np.int_]:
        return self._ctx.metrics.axes_dim

    @property
    def xdom_span(self) -> float:
        return self._ctx.metrics.xdom_span

    @property
    def ydom_span(self) -> float:
        return self._ctx.metrics.ydom_span


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
        ...

    @abstractmethod
    def draw(self, ctx: DrawContext): ...


class Axes(Element):

    def __init__(self):
        """Contains the rectangular plot area within the Canvas."""
        self.dim = np.zeros(2)
        self.pos = np.zeros(2)

    def on_metrics_changed(self, metric_name: str | None, metrics: PlotMetrics):
        # TODO: pos and dim should probably be private methods here to preserve a single source of truth
        # Or, even better, just fetch the dimensions directly from PlotMetrics at draw
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
        """
        self.orientation = orientation
        self.tick_margin = kwargs.get("margin", 0.1)
        self.tick_length = kwargs.get("length", 3)
        
        # Cached derived properties from PlotMetrics
        self._dom = np.zeros(2)
        self._span = 0
        self._axes_dim = np.zeros(2)
        self._axis_line_endpoints = np.zeros((2,2))

        # Private attributes
        self._tick_num = kwargs.get("num_ticks", 6)
        self._tick_pos = np.zeros((0, 2))
        self._labels = []
        
        # Tick mode: either fixed locations or fixed values
        self.tick_mode = None
        
        # Label mode: either numberical or text
        self.label_mode = None
        
    def on_metrics_changed(self, metric_name: str | None, metrics: PlotMetrics):
        """
        Recompute tick positions and labels whenever layout or domain changes.
        
        Some derived properties of metrics will be cached such that API-accessable 
        setters can work properly.
        """
        # Calculate/cache plot metrics
        self._dom = metrics.xdom if self.orientation == Axis.X else metrics.ydom
        self._span = metrics.xdom_span if self.orientation == Axis.X else metrics.ydom_span
        self._axes_dim = metrics.axes_dim
        self._axis_line_endpoints = np.vstack([
            metrics.axes_sw,
            metrics.axes_sw + self.axis_direction * metrics.axes_dim])
                
        # Recompute tick positions
        if self.tick_mode == Axis.FIXED_TICK_POSITIONS:
            self._compute_fixed_tick_num_coordinates()
        elif self.tick_mode == Axis.FIXED_TICK_VALUES:
            self._compute_fixed_tick_val_coordinates()
        
        # Recompute labels
        if self.label_mode == Axis.LABELS_NUMERICAL:
            self._update_numerical_labels()
        
    def draw(self, ctx: DrawContext):
        if self._labels is None or len(self._labels) == 0:
            return

        tick_vector = self.tick_direction * self.tick_length
        font, color = ctx.theme.fonts["tick"]
        text_offset = self.tick_direction * (2 + self.tick_length)

        for pos, label in zip(self._tick_pos, self._labels):
            ctx.renderer.vector(
                pos, tick_vector, ctx.theme.colors["axes_line"],
                ctx.metrics, on_axes=False)
            ctx.renderer.text(
                label, font, color, pos,
                self.text_ha, self.text_va, ctx.metrics,
                text_offset, on_axes=False)    
    
    # ---- Properties settable from the API
    @property
    def tick_num(self):
        return self._tick_num
        
    @tick_num.setter
    def tick_num(self, val: int):
        """Set a fixed number of evenly spaced tick locations."""
        self.tick_mode = Axis.FIXED_TICK_POSITIONS
        self.label_mode = Axis.LABELS_NUMERICAL
        self._tick_num = val
        
        self._compute_fixed_tick_num_coordinates()
        if self.label_mode == Axis.LABELS_NUMERICAL:
            self._update_numerical_labels()
        
    @property 
    def tick_pos(self):
        return self._tick_pos
    
    @tick_pos.setter
    def tick_pos(self, val: npt.NDArray[np.float64]):
        """Set custom ticks fixed positions."""
        self.tick_mode = Axis.FIXED_TICK_VALUES
        raise NotImplementedError
    
    @property
    def labels(self):
        return self._labels
    
    @labels.setter
    def labels(self, val: tuple[str]):
        self.label_mode = Axis.LABELS_TEXT
        self._labels = val
        
    
    # ---- Properties/methods that fetch the correct metrics based on orientation
    @property
    def text_va(self) -> Literal['bottom', 'center']:
        return 'bottom' if self.orientation == Axis.X else 'center'

    @property
    def text_ha(self) -> Literal['center', 'right']:
        return 'center' if self.orientation == Axis.X else 'right'

    @property
    def tick_direction(self) -> np.ndarray:
        """Return a vector in the direction of ticks, from away from the axes."""
        return np.array((0, 1)) if self.orientation == Axis.X else np.array((-1, 0))

    @property
    def axis_direction(self) -> np.ndarray:
        """Return a vector in the direction of the axis, starting at the SW point."""
        return np.array((1, 0)) if self.orientation == Axis.X else np.array((0, -1))
       
    # ---- Compute ticks, axis endpoints and labels
        
    def _compute_fixed_tick_num_coordinates(self):
        """Calculate the coordinates of ticks based on the amount."""
        outer_tick_offset = self.axis_direction * self.tick_margin * self._axes_dim
        self._tick_pos = np.linspace(
            start=self._axis_line_endpoints[0] + outer_tick_offset,
            stop=self._axis_line_endpoints[1] - outer_tick_offset,
            num=self.tick_num,
            endpoint=True)
        
    def _compute_fixed_tick_val_coordinates(self):
         """Calculate the coordinates of ticks based on their values."""
         raise NotImplementedError   

    def _update_numerical_labels(self):
        """Format tick labels based on the current domain magnitude."""
        numbers = np.linspace(
            self._dom[0] + self._span * self.tick_margin,
            self._dom[1] - self._span * self.tick_margin,
            num=self._tick_num,
            endpoint=True)

        order_of_magnitude = floor(log10(max(abs(numbers))))

        if -4 < order_of_magnitude < 5:
            round_to = max(0, 1 - order_of_magnitude)
            self._labels = [f"%.{round_to}f" % x for x in numbers]
        else:
            self._labels = [
                np.format_float_scientific(x, precision=0, trim='-', sign=False)
                for x in numbers]


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
