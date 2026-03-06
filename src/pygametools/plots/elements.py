"""
# TODO: remove all axis logic from axis objects such that only ticks and labels remain
# TODO: have ticks and labels drawn on the canvas surface instead of the axes surface
      
OLD
# TODO: fix the circle reference between metrics and elements. Maybe remove update responsibiliy from metrics?
# TODO: in draw function, make sure on_axes converts coordinates instead of drawing on axes surface
# TODO: fix line of axes not showing up
# TODO: Change update_dimensions functions to update_metrics with a Literal metric
# TODO: render axes without surface (to prevent out of bound ticks)
# TODO: Fix axes: tick generation, orientation settings etc.
# TODO: make sure all elements are registered to metrics and update on changes
# TODO: make sure title, labels, ticks are drawn correctly after updates
# TODO: Implement legend element
# TODO: optimize metrics updates: only update elemements where relevant metrics have changed
 
"""
import numpy as np
import numpy.typing as npt

from pygametools.plots.types import CoordinatePair
from .draw import PlotRenderer, PlotTheme
from pygametools.color import Color
from abc import ABC, abstractmethod
from math import floor, log10
from typing import Literal


class Element(ABC):

    def __init__(self, parent_canvas):
        self.parent_canvas = parent_canvas
  
    @property
    def canvas(self):
        return self.parent_canvas

    @property
    def metrics(self):
        return self.canvas.metrics

    @property
    def theme(self):
        return self.canvas.theme

    @property
    def colors(self):
        return self.theme.colors

    @property
    def fonts(self):
        return self.theme.fonts

    @property
    def pr(self):
        return self.canvas.pr

    @abstractmethod
    def update_metrics(
            self, metric: Literal['pos', 'dim', 'xdom', 'ydom', 'xpad', 'ypad'] | None=None):
        pass

    @abstractmethod
    def draw(self):
        pass
        

class PlotMetrics:

    def __init__(
            self, 
            pos: CoordinatePair, 
            dim: CoordinatePair, 
            xdom: CoordinatePair,
            ydom: CoordinatePair, 
            axes_xpad: CoordinatePair=(30,10), 
            axes_ypad: CoordinatePair=(30,20)):
        
        assert xdom[0] < xdom[1], "Invalid x domain"
        assert ydom[0] < ydom[1], "Invalid y domain"

        self._pos = np.array(pos, dtype=int)
        self._dim = np.array(dim, dtype=int) 
        self._xdom = np.array(xdom, dtype=float) 
        self._ydom = np.array(ydom, dtype=float) 
        self._axes_xpad = np.array(axes_xpad, dtype=int)
        self._axes_ypad = np.array(axes_ypad, dtype=int)

        # List of objects to notify on changes
        self._notify_objects = []  

    def add_object(self, element: Element):
        """Add an object that needs to be notified of changes"""
        self._notify_objects.append(element)

    def update_metrics(self, metric: Literal['pos', 'dim', 'xdom', 'ydom', 'xpad', 'ypad']):
        """
        Notify all objects that metrics have changed.

        The changed metric is included in the function call such that underlying objects can 
        update only their relevant dimensions to improve performance.
        """
        for obj in self._notify_objects:
            obj.update_metrics(metric)

    # Top-level metrics and properties
    @property
    def pos(self) -> npt.NDArray[np.int_]:
        return self._pos
    
    @pos.setter
    def pos(self, val: CoordinatePair):
        self._pos = np.array(val, dtype=int)
        self.update_metrics(metric='pos')
    
    @property
    def dim(self) -> npt.NDArray[np.int_]:
        return self._dim
    
    @dim.setter
    def dim(self, val: CoordinatePair):
        self._dim = np.array(val, dtype=int)
        self.update_metrics(metric='dim')
    
    @property
    def xdom(self) -> npt.NDArray[np.float64]:
        return self._xdom

    @xdom.setter
    def xdom(self, val: tuple[float, float]):
        assert val[0] < val[1], "Invalid x domain"
        self._xdom = np.array(val, dtype=float)
        self.update_metrics(metric='xdom')

    @property
    def ydom(self) -> npt.NDArray[np.float64]:
        return self._ydom

    @ydom.setter
    def ydom(self, val: tuple[float, float]):
        assert val[0] < val[1], "Invalid y domain"
        self._ydom = np.array(val, dtype=float)
        self.update_metrics(metric='ydom')

    @property
    def axes_xpad(self) -> npt.NDArray[np.int_]:
        return self._axes_xpad

    @axes_xpad.setter
    def axes_xpad(self, val: CoordinatePair):
        self._axes_xpad = np.array(val, dtype=int)
        self.update_metrics(metric='xpad')

    @property
    def axes_ypad(self) -> npt.NDArray[np.int_]:
        return self._axes_ypad

    @axes_ypad.setter
    def axes_ypad(self, val: CoordinatePair):
        self._axes_ypad = np.array(val, dtype=int)
        self.update_metrics(metric='ypad')

    # Derived properties
    @property
    def xdom_span(self) -> float:
        return np.diff(self._xdom)[0]

    @property
    def ydom_span(self) -> float:
        return np.diff(self._ydom)[0]

    @property
    def axes_pos(self) -> npt.NDArray[np.int_]:
        """Position of the axis in pygame coordinates on the Canvas surface."""
        return np.hstack([self._axes_xpad[0], self._axes_ypad[0]])

    @property
    def axes_dim(self) -> npt.NDArray[np.int_]:
        """Dimensions of the axes in pygame coordinates."""
        return self.dim - np.hstack([self._axes_xpad.sum(), self._axes_ypad.sum()])

    @property
    def axes_nw(self) -> npt.NDArray[np.int_]:
        """NW point of axes on Canvas surface in pygame coordinates"""
        return self.axes_pos

    @property
    def axes_sw(self) -> npt.NDArray[np.int_]:
        """SW point of axes on Canvas surface in pygame coordinates"""
        return self.axes_pos + [0, self.axes_dim[1]]

    @property
    def axes_ne(self) -> npt.NDArray[np.int_]:
        """NE point of axes on Canvas surface in pygame coordinates"""
        return self.axes_pos + [self.axes_dim[0], 0]

    @property
    def axes_se(self) -> npt.NDArray[np.int_]:
        """SE point of axes on Canvas surface in pygame coordinates"""
        return self.axes_pos + self.axes_dim


class Canvas:

    def __init__(
            self,
            pos: tuple[int, int],
            dim: tuple[int, int],
            xdom: tuple[float, float], 
            ydom: tuple[float, float],
            **kwargs):
        """
        Container for all plot elements and single source of truth for dimensions and domains.
        
        Args:
            pos: Canvas position (x, y) in screen coordinates
            dim: Canvas dimensions (width, height) in pixels
            xdom: X-axis domain (min, max) in data coordinates
            ydom: Y-axis domain (min, max) in data coordinates                                            
        """
        self.metrics = PlotMetrics(pos, dim, xdom, ydom)
        self.theme = PlotTheme(**kwargs)

        # Plot draw and element instances to metrics        
        self.axes = Axes(self)
        self.title = Title(self, kwargs.get("title", ""))
        self.axisx = Axis(self, Axis.X)
        self.axisy = Axis(self, Axis.Y)
        
        # Instantiate plotrenderer and add objects to notify on metric changes
        self.pr = PlotRenderer(self)
        
        for obj in [self.pr, self.axes, self.title, self.axisx, self.axisy]:
            self.metrics.add_object(obj)

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

    def __init__(self, parent_canvas):
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

    def __init__(self, parent_canvas, orientation: int, **kwargs):
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
        # TODO: clarify the type of coordinate system
        # TODO: calculate the number of ticks based on dimensions
        # TODO: move tick updatiting to its own method such that it can also be called from set_num_ticks
        
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
        Get string numberical labels with appropiate formatting.
        """
        numbers = np.linspace(
            self.dom[0] + self.span * self.tick_margin,
            self.dom[1] - self.span * self.tick_margin,
            num=self.num_ticks,
            endpoint=True) 

        order_of_magnitude = floor(log10(max(abs(numbers))))

        if -5 < order_of_magnitude < 5:
            round_to = max(0, 1 - order_of_magnitude)
            self.labels = [f"%.{round_to}f" % x for x in numbers]
        else:
            self.labels = [np.format_float_scientific(x, 1) for x in numbers]

    def set_num_ticks(self, num_ticks):
        """
        Set a fixed number of evenly spaced tick locations

        Ticks will change their value to keep their relative location.
        """
        # TODO Decide how different tick styles get set.
    
        self.tick_mode = Axis.FIXED_TICK_POSITIONS
        self.label_mode = Axis.LABELS_NUMERICAL
        self.num_ticks = num_ticks
        self.update_metrics()

    def set_ticks(self, ticks, labels):
        """
        Set custom tick locations with a 1d array and optional string labels.

        Ticks will change their location to retain their value.
        """
        self.mode = self.FIXED_TICK_VALUES
        self.label_mode = Axis.LABELS_TEXT
        self.label_mode = Axis.LABELS_NUMERICAL

        # Also implement label mode here
        raise NotImplementedError

    def set_labels(self, labels):
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

    def __init__(self, parent_canvas, title):
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

    def __init__(self, parent_canvas):
        """
        Legend element for plots.
        """
        super().__init__(parent_canvas)
