"""
# TODO: remove all axis logic from axis objects such that only ticks and labels remain
# TODO: have ticks and labels drawn on the canvas surface instead of the axes surface
"""

import numpy as np
import numpy.typing as npt
from pygametools.plots.types import CoordinatePair, Domain
from .drawing import PlotTheme, PlotMetrics, PlotRenderer, DrawContext
from pygametools.color import Color
from abc import ABC, abstractmethod
from math import floor, log10
from typing import Literal


class Element(ABC):

    def __init__(self, parent_canvas):
        self.parent_canvas = parent_canvas
  
    # @property
    # def canvas(self):
    #     return self.parent_canvas

    # @property
    # def metrics(self):
    #     return self.canvas.metrics

    # @property
    # def theme(self):
    #     return self.canvas.theme

    # @property
    # def colors(self):
    #     return self.theme.colors

    # @property
    # def fonts(self):
    #     return self.theme.fonts

    # @property
    # def pr(self):
    #     return self.canvas.pr
    
    # @abstractmethod
    # def update_metrics(
    #         self, metric: Literal['pos', 'dim', 'xdom', 'ydom', 'xpad', 'ypad'] | None=None):
    #     pass
    
    @abstractmethod
    def on_metrics_changed(self, metric_name: str, metrics: PlotMetrics):
        pass

    @abstractmethod
    def draw(self, drawcontext: DrawContext):
        pass
        

class Canvas:

    def __init__(
            self,
            pos: tuple[int, int],
            dim: tuple[int, int],
            xdom: Domain, 
            ydom: Domain,
            **kwargs):
        """
        Container for all plot elements and single source of truth for dimensions and domains.
        
        Args:
            pos: Canvas position (x, y) in screen coordinates
            dim: Canvas dimensions (width, height) in pixels
            xdom: X-axis domain (min, max) in data coordinates
            ydom: Y-axis domain (min, max) in data coordinates                                            
        """
        self.drawcontext = DrawContext(
            theme=PlotTheme(**kwargs),
            metrics=PlotMetrics(pos, dim, xdom, ydom),
            renderer=PlotRenderer(self))
        
        # Elements and element registry        
        self.axes = Axes(self)
        self.title = Title(self, kwargs.get("title", ""))
        self.axisx = Axis(self, Axis.X)
        self.axisy = Axis(self, Axis.Y)
        self._elements = [self.axes, self.title, self.axisx, self.axisy]
        
        
        
        # Instantiate plotrenderer and add objects to notify on metric changes
        # self.pr = PlotMetrics
        
        # for obj in [self.pr, self.axes, self.title, self.axisx, self.axisy]:
        #     self.metrics.add_object(obj)
        
        
        

    def draw(self, surface):
        self.pr.clear()

        # Draw a border around the canvas itself
        self.pr.rect(
            np.array([0,0]), self.metrics.dim, self.theme.colors["canvas_bg"],
            self.theme.colors["canvas_line"], on_axes=False)
        
        # Draw all other elements
        # TODO: list of drawables?
        self.axes.draw()
        self.title.draw()
        self.axisx.draw()
        self.axisy.draw()
        
        # TODO: does it make sense to call draw on the renderer itself?
        self.pr.draw(surface)


class Axes(Element):

    def __init__(self, parent_canvas: Canvas):
        """
        Contains a rectangle within parent_canvas containing all plots.
        """
        super().__init__(parent_canvas)
        self.dim = np.zeros(2)
        self.update_metrics()

        self.dim = np.zeros(2)
        self.pos = np.zeros(2)

        self.update_metrics()

    def update_metrics(
            self, metric: Literal['pos', 'dim', 'xdom', 'ydom', 'xpad', 'ypad'] | None=None):
        if metric == 'pos' or metric is None:
            self.pos = self.metrics.axes_pos
        if metric == 'dim' or metric is None:
            self.dim = self.metrics.axes_dim
        
    def draw(self):
        # Draw a line around the axes surface itself (1 pixel wider)
        self.pr.rect(
            self.metrics.axes_pos-1,  self.metrics.axes_dim+2, facecol=self.colors["axes_bg"],
            linecol=self.colors["axes_line"], on_axes=False)


class Axis(Element):
    X = 0
    Y = 1
    FIXED_TICK_POSITIONS = 0
    FIXED_TICK_VALUES = 1
    LABELS_NUMERICAL = 0
    LABELS_TEXT = 1

    def __init__(
            self,
            parent_canvas: Canvas,
            orientation: int,
            **kwargs):
        """
        Axis element containing ticks and labels.

        Args:
            parent_canvas : Canvas
                Canvas to which the axis in linked.
            orientation : int
                Determines whether X or Y axis.
        """
        super().__init__(parent_canvas)
        self.orientation = orientation          
        self.tick_margin = kwargs.get("margin", 0.1)
        self.tick_length = kwargs.get("length", 3) 
        self.num_ticks = kwargs.get("length", 6) 
        self.pos_ticks = np.zeros(2)
        self.labels = None

        # Tick mode: either fixed locations or fixed values
        self.tick_mode = None
        self.label_mode = None

        self.update_metrics()
        
    @property
    def dom(self) -> np.ndarray:
        """Return the domain of this axis in graph coordinates."""
        return self.canvas.metrics.xdom if self.orientation == Axis.X else self.canvas.metrics.ydom
    
    @property
    def span(self) -> float:
        """Return the span of this axis domain."""
        return np.diff(self.dom)[0]

    @property
    def text_va(self) -> str:
        """Passed to PlotRenderer"""
        return 'bottom' if self.orientation == Axis.X else 'center'
    
    @property
    def text_ha(self) -> str:
        """Passed to PlotRenderer"""
        return 'center' if self.orientation == Axis.X else 'right'

    @property
    def tick_direction(self) -> np.ndarray:
        """Unit vector of tick direction from axis, depending on the axis orientation."""
        return np.array((0, 1)) if self.orientation == Axis.X else np.array((-1, 0))
    
    @property
    def axis_direction(self) -> np.ndarray:
        """Unit vector of axis direction from origin, depending on the axis orientation."""
        return np.array((1, 0)) if self.orientation == Axis.X else np.array((0, -1))
 
    def update_metrics(
            self, metric: Literal['pos', 'dim', 'xdom', 'ydom', 'xpad', 'ypad'] | None=None):
        """
        Recalculate the ticks locations and axis line.
        """
        # TODO: use the `metrics` parameter to only update the part of axis that is needed.
        # TODO: move tick updating to its own method such that it can also be called from set_num_ticks
        
        # Alias for metrics
        metrics = self.canvas.metrics
        
        # Axis line in [[x1, y1], [x2, y2]]
        axis_line_endpoints = np.vstack([
            metrics.axes_sw,
            metrics.axes_sw + self.axis_direction * metrics.axes_dim])
    
        # Update ticks
        if self.tick_mode == Axis.FIXED_TICK_POSITIONS:
            offset = self.axis_direction * self.tick_margin * self.metrics.axes_dim
            self.pos_ticks = np.linspace(
                axis_line_endpoints[0] + offset,
                axis_line_endpoints[1] - offset,
                self.num_ticks,
                endpoint=True)
            
        elif self.tick_mode == Axis.FIXED_TICK_VALUES:
            raise NotImplementedError

        # Update labels
        if self.label_mode == Axis.LABELS_NUMERICAL:
            self.update_numerical_labels()

        elif self.label_mode == Axis.LABELS_TEXT:
            raise NotImplementedError

    def update_numerical_labels(self):
        """
        Get string numberical labels with appropiate formatting (based on
        the size of the axis label numbers: decimal, integer, or scientific).
        """
        numbers = np.linspace(
            self.dom[0] + self.span * self.tick_margin,
            self.dom[1] - self.span * self.tick_margin,
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

    def set_num_ticks(self, num_ticks: int):
        """
        Set a fixed number of evenly spaced tick locations

        Ticks will change their value to keep their relative location.
        """
        # TODO Decide how different tick styles get set.
    
        self.tick_mode = Axis.FIXED_TICK_POSITIONS
        self.label_mode = Axis.LABELS_NUMERICAL
        self.num_ticks = num_ticks
        self.update_metrics()

    def set_ticks(self, ticks: npt.NDArray, labels: tuple):
        """
        Set custom tick locations with a 1d array and optional string labels.

        Ticks will change their location to retain their value.
        """
        self.mode = self.FIXED_TICK_VALUES
        self.label_mode = Axis.LABELS_TEXT
        self.label_mode = Axis.LABELS_NUMERICAL

        # Also implement label mode here
        raise NotImplementedError

    def set_labels(self, labels: tuple):
        pass

    def draw(self):

        # Draw ticks
        tick_vector = self.tick_direction * self.tick_length
        for i, (pos, label) in enumerate(zip(self.pos_ticks, self.labels)):

            self.pr.vector(
                pos, tick_vector, self.colors["axes_line"],
                on_axes=False)

            font, color =  self.fonts["tick"]
            offset = self.tick_direction * (2 + self.tick_length)
            self.pr.text(
                label, font, color, pos, self.text_ha, self.text_va,
                offset, on_axes=False)


class Title(Element):

    def __init__(self, parent_canvas: Canvas, title: str):
        """
        Contains the plot title and title dimensions, centered above axes.
        """
        super().__init__(parent_canvas)
        self.title = title
        self.update_metrics()
        
    def update_metrics(
            self, metric: Literal['pos', 'dim', 'xdom', 'ydom', 'xpad', 'ypad'] | None=None):
        """
        Update the title position to a point centered above the axes.
        """
        self.pos = np.array([
            self.metrics.axes_xpad[0] + self.canvas.axes.dim[0] / 2, 
            self.metrics.axes_ypad[0] / 2])

    def draw(self):
        font, color =  self.fonts["title"]
        self.pr.text(
            self.title, font, color, self.pos, ha="center",
            va="center", on_axes=False)


class Legend(Element):

    def __init__(self, parent_canvas: Canvas):
        """
        Legend element for plots.
        """
        super().__init__(parent_canvas)
