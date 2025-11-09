"""
Elements:
    - Canvas: Rectangle that contains ALL other plot elements.
    - PlotMetrics: contains top-level dimensions, positions, domains. Also 
      notifies elements of changes. 



      # TODO: get running without error
      # TODO: make sure all elements are registered to metrics and update on changes
      # TODO: test different cases
      # TODO: make sure title, labels, ticks are drawn correctly after updates
      # TODO: Implement legend element
 
"""
import numpy as np
from .draw import PlotDraw
from pygametools.color import Color
from abc import ABC, abstractmethod
import pygame
from math import floor, log10


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
    def pdraw(self):
        return self.canvas.pdraw

    @abstractmethod
    def update_dimensions(self, **args):
        pass

    @abstractmethod
    def draw(self):
        pass


class PlotTheme:

    def __init__(self, **kwargs):
        """
        Plot color and font properties.
        """
        self.colors = {
            "canvas_bg": kwargs.get("cols_canvas_bg", Color.GREY5),
            "canvas_line": kwargs.get("cols_canvas_line", Color.GREY3),
            "axes_bg": kwargs.get("cols_axes_bg", Color.WHITE),
            "axes_line": kwargs.get("cols_axes_line", Color.GREY3),
            "axis": kwargs.get("cols_axis", Color.GREY4)}        
        font_type = "msreferencesansserif"
        self.fonts = {
            "title": (pygame.font.SysFont(font_type, 12), Color.BLACK),
            "legend": (pygame.font.SysFont(font_type, 10), Color.BLACK),
            "tick": (pygame.font.SysFont(font_type, 8), Color.BLACK)}
        

class PlotMetrics:

    def __init__(
            self, 
            pos: tuple[int], 
            dim: tuple[int], 
            xdom: tuple[int],
            ydom: tuple[int], 
            axes_xpad: tuple[int]=(30,10), 
            axes_ypad: tuple[int]=(40,10)):
        
        assert xdom[0] < xdom[1], "Invalid x domain"
        assert ydom[0] < ydom[1], "Invalid y domain"

        self._pos = np.array(pos)
        self._dim = np.array(dim) 
        self._xdom = np.array(xdom) 
        self._ydom = np.array(ydom) 
        self._axes_xpad = np.array(axes_xpad)
        self._axes_ypad = np.array(axes_ypad)


        # List of elements to notify on changes
        self._elements = []  

    def add_element(self, element: Element):
        """Add an element that needs to be notified of changes"""
        self._elements.append(element)

    def update_elements(self, **args):
        """Notify all elements that metrics have changed"""
        for element in self._elements:
            element.update_dimensions(**args)

    # Top-level metrics and properties

    @property
    def pos(self) -> np.ndarray:
        return self._pos
    
    @pos.setter
    def pos(self, value: np.ndarray):
        self._pos = value
    
    @property
    def dim(self) -> np.ndarray:
        return self._dim
    
    @dim.setter
    def dim(self, value: np.ndarray):
        self._dim = value
    
    @property
    def xdom(self) -> np.ndarray:
        return self._xdom
    
    @xdom.setter
    def xdom(self, value: np.ndarray):
        assert value[0] < value[1], "Invalid x domain"
        self._xdom = value

    @property
    def ydom(self) -> np.ndarray:
        return self._ydom
    
    @ydom.setter
    def ydom(self, value: np.ndarray):
        assert value[0] < value[1], "Invalid y domain"
        self._ydom = value

    @property
    def axes_xpad(self) -> np.ndarray:
        return self._axes_xpad
    
    @axes_xpad.setter
    def axes_xpad(self, value: np.ndarray):
        self._axes_xpad = value

    @property
    def axes_ypad(self) -> np.ndarray:
        return self._axes_ypad
    
    @axes_ypad.setter
    def axes_ypad(self, value: np.ndarray):
        self._axes_ypad = value

    # Derived properties

    @property
    def xdom_span(self) -> float:
        return np.diff(self._xdom)[0]
    
    @property
    def ydom_span(self) -> float:
        return np.diff(self._ydom)[0]


class Axes(Element):

    def __init__(self, parent_canvas):
        """
        Contains a rectangle within parent_canvas containing all plots.
        """
        super().__init__(parent_canvas)
        self.dim = np.zeros(2)
        self.update_dimensions()

    def update_dimensions(self, **args):
        self.dim = self.metrics.dim - np.hstack([
            self.metrics._axes_xpad.sum(),
            self.metrics._axes_ypad.sum()]) 

    def draw(self):
        axes_top_left = (
            self.metrics.xdom[0],
            self.metrics.ydom[1])

        self.pdraw.rect(
            axes_top_left, self.dim, self.colors["axes_bg"],
            self.colors["axes_line"], on_axes=True)


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

        self.pos_line = np.zeros((2,2))
        self.pos_ticks = np.zeros(2)
        
        self.labels = None

        # Tick mode: either fixed locations or fixed values
        self.tick_mode = None
        self.label_mode = None

        self.update_dimensions()

    @property
    def text_va(self) -> str:
        return 'bottom' if self.orientation == Axis.X else 'center'
    
    @property
    def text_ha(self) -> str:
        return 'center' if self.orientation == Axis.X else 'right'

    @property
    def tick_direction(self) -> np.ndarray:
        return np.array((0, 1)) if self.orientation == Axis.X else np.array((-1, 0))

    @property
    def dom(self) -> np.ndarray:
        """
        Return the domain of this axis.
        """
        return self.canvas.metrics.xdom if self.orientation == Axis.X else self.canvas.metrics.ydom
    
    @property
    def dom_other(self) -> np.ndarray:
        """
        Return the domain of the other axis (x if y, y if x).
        """
        return self.canvas.metrics.ydom if self.orientation == Axis.X else self.canvas.metrics.xdom

    @property
    def span(self) -> float:
        """
        Return the span of this axis domain.
        """
        return np.diff(self.dom)

    @property
    def crossing(self) -> float:
        """
        Return the coordinate of the other axis at which the axis crosses.
        """
        # TODO: implement optional crossing at 0 if in domain
        return self.dom_other[0]

    def update_dimensions(self, **kwargs):
        """
        Recalculate the ticks locations and axis line.
        """
        # Compute this axis line coordinates as [[x1, y1], [x2, y2]]
        # First compute the diagonal line
        pos_line = np.transpose(np.vstack([
            self.canvas.metrics.xdom,
            self.canvas.metrics.ydom]))
        
        
    
        # Then set fix the position to either vertical or horizontal    
        pos_line[:,1-self.orientation] = self.crossing
        self.pos_line = pos_line

        # Update ticks
        if self.tick_mode == Axis.FIXED_TICK_POSITIONS:

            # Compute crossing ticks (diagnal for now)
            n = kwargs.get("num_ticks", self.pos_ticks.shape[0])
            offset = self.tick_margin * self.span

            start = pos_line[0]
            start[self.orientation] += offset

            end = pos_line[1]
            end[self.orientation] -= offset

            pos_ticks = np.linspace(start, end, n)

            self.pos_ticks = pos_ticks

        elif self.tick_mode == Axis.FIXED_TICK_VALUES:
            raise NotImplementedError

        # Update labels
        if self.label_mode == Axis.LABELS_NUMERICAL:
            self.update_numerical_labels()

        elif self.label_mode == Axis.LABELS_TEXT:
            raise NotImplementedError

    def update_fixed_position_ticks(self):
        """
        TODO: move fixed tick part from function above here.
        """
        pass

    def update_numerical_labels(self):
        """
        Get string numberical labels with appropiate formatting.
        """
        numbers = self.pos_ticks[:,self.orientation]
        mag = floor(log10(max(abs(numbers))))

        if -5 < mag < 5:
            round_to = max(0, 1 - mag)
            self.labels = [f"%.{round_to}f" % x for x in numbers]
        else:
            self.labels = [np.format_float_scientific(x, 1) for x in numbers]

    def set_num_ticks(self, num_ticks):
        """
        Set a fixed number of evenly spaced tick locations

        Ticks will change their value to keep their relative location.
        """
        self.tick_mode = Axis.FIXED_TICK_POSITIONS
        self.label_mode = Axis.LABELS_NUMERICAL
        self.update_dimensions(num_ticks=num_ticks)

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

        if self.orientation == self.X:
            pass
            self.pdraw.line(
                self.pos_line, Color.BLUE3, on_axes=True)
        else:
            pass
            # self.pdraw.line(
            #     self.pos_line, Color.RED3, on_axes=True)
        


        # Draw axis line
        # self.pdraw.line(
        #     self.pos_line, self.colors["axis"], on_axes=True)

    
        # Draw ticks
        tick_vector = self.tick_direction * self.tick_length
        for i, (pos, label) in enumerate(zip(self.pos_ticks, self.labels)):

            self.pdraw.vector(
                pos, tick_vector, self.colors["axis"],
                on_axes=True)

            font, color =  self.fonts["tick"]
            offset = self.tick_direction * (2 + self.tick_length)
            self.pdraw.text(
                label, font, color, pos, self.text_ha, self.text_va,
                offset, on_axes=True)


class Title(Element):

    def __init__(self, parent_canvas, title):
        """
        Contains the plot title and title dimensions, centered above axes.
        """
        super().__init__(parent_canvas)
        self.title = title

        self.update_dimensions()
        
    def update_dimensions(self, **args):
        """
        Update the title position to a point centered above the axes.
        """
        self.pos = np.array([
            self.metrics.axes_xpad[0] + self.canvas.axes.dim[0] / 2, 
            self.metrics.axes_ypad[0] / 2])

    def draw(self):
        font, color =  self.fonts["title"]
        self.pdraw.text(
            self.title, font, color, self.pos, ha="center",
            va="center", on_axes=False)


class Legend(Element):

    def __init__(self, parent_canvas):
        """
        Legend element for plots.
        """
        super().__init__(parent_canvas)


class Canvas:

    def __init__(
            self, pos: tuple[int], dim: tuple[int], xdom: tuple[float], 
            ydom: tuple[float], **kwargs):
        """
        Container for all plot elements and single source of truth for dimensions and domains.
        
        Args:
            pos: Canvas position (x, y) in screen coordinates
            dim: Canvas dimensions (width, height) in pixels
            xdom: X-axis domain (min, max) in data coordinates
            ydom: Y-axis domain (min, max) in data coordinates                                            
        """
        pygame.init()

        # Initialize metrics manager
        self.metrics = PlotMetrics(pos, dim, xdom, ydom)
        self.theme = PlotTheme(**kwargs)

        # Plot draw and element instances to metrics        
        self.axes = Axes(self)
        self.title = Title(self, kwargs.get("title", ""))
        self.axisx = Axis(self, Axis.X)
        self.axisy = Axis(self, Axis.Y)

        for element in [self.axes, self.title, self.axisx, self.axisy]:
            self.metrics.add_element(self.axes)

        self.pdraw = PlotDraw(self)

    def draw(self, surface):
        self.pdraw.clear()

        # Draw the canvas itself
        self.pdraw.rect(
            (0,0), self.metrics.dim, self.theme.colors["canvas_bg"],
            self.theme.colors["canvas_line"], on_axes=False)
        
        self.axes.draw()
        self.title.draw()
        self.axisx.draw()
        self.axisy.draw()

        self.pdraw.draw(surface)