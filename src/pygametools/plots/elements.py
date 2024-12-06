"""
Elements:
    - Canvas: Rectangle that contains ALL other plot elements. Also contains
    all properties of the plot such as its

"""
import numpy as np
from .draw import PlotDraw
from pygametools.color import Color
from abc import ABC, abstractmethod
import pygame
from math import floor, log10


class Canvas:

    def __init__(self, pos, dim, domx, domy, **kwargs):
        """
        Rectangle that contains ALL other plot elements for a single plot.

        Single source of truth for all plot properties.

        Parameters
        ----------
        pos : iterable of shape (2)
            Pygame (x, y) coordinates of top-left corner.
        dim : iterable of shape (2)
            Pygame (width, height) dimensions.
        domx : iterable of shape (2)
            Plot (x_min, x_max) domain.
        domy : iterable of shape (2)
            Plot (y_min, y_max) domain.
        """
        # Plot position and dimensions
        self.dim = np.array(dim, dtype=np.int32)
        self.pos = np.array(pos, dtype=np.int32)
        self.dom = np.vstack((domx, domy), dtype=np.float64)

        # Axes padding (left, top, right, bottom) relative to the canvas.
        # The location of all other alements is based on this padding.
        self.pad = np.array((20,20,10,10), dtype=np.int32)

        # Plot color properties
        self.colors = {
            "canvas_bg": kwargs.get("cols_canvas_bg", Color.GREY5),
            "canvas_line": kwargs.get("cols_canvas_line", Color.GREY3),
            "axes_bg": kwargs.get("cols_axes_bg", Color.WHITE),
            "axes_line": kwargs.get("cols_axes_line", Color.GREY3),
            "axis": kwargs.get("cols_axis", Color.GREY4)}

        # Plot fonts
        pygame.init()
        font_type = "msreferencesansserif"
        self.fonts = {
            "title": (pygame.font.SysFont(font_type, 12), Color.BLACK),
            "legend": (pygame.font.SysFont(font_type, 10), Color.BLACK),
            "tick": (pygame.font.SysFont(font_type, 8), Color.BLACK)
            }

        # Plot draw and element instances

        self.axes = Axes(self)
        self.title = Title(self, kwargs.get("title", ""))
        self.axisx = Axis(self, Axis.X, margin=0.1)
        self.axisy = Axis(self, Axis.Y, margin=0.1)
        self.pdraw = PlotDraw(self)


        # Update dimensions in all plot elements
        self.update_dimensions()




    def update_dimensions(self, **args):
        """
        Update all plot dimensions. Options for args:
        dim, pos, domx, domy, pad.
        TODO: use getters and setters
        """
        assert all((hasattr, self, key) for key in args)

        for key, value in args.items():
            setattr(self, key, value)

        self.axes.update_dimensions(**args)
        self.title.update_dimensions(**args)
        self.axisx.update_dimensions(**args)
        self.axisy.update_dimensions(**args)
        self.pdraw.update_dimensions(**args)

    def draw(self, surface):

        self.pdraw.clear()

        # Draw the canvas itself
        self.pdraw.rect(
            (0,0), self.dim, self.colors["canvas_bg"],
            self.colors["canvas_line"], on_axes=False)


        self.axes.draw()
        self.title.draw()
        self.axisx.draw()
        self.axisy.draw()

        self.pdraw.draw(surface)














class Element(ABC):

    def __init__(self, parent_canvas):
        self.canvas = parent_canvas

    @property
    def colors(self):
        return self.canvas.colors

    @property
    def fonts(self):
        return self.canvas.fonts

    @property
    def pdraw(self):
        return self.canvas.pdraw

    @abstractmethod
    def update_dimensions(self, **args):
        pass

    @abstractmethod
    def draw(self):
        pass



class Axes(Element):

    def __init__(self, parent_canvas):
        """
        Contains a rectangle within parent_canvas containing all plots.
        """
        super().__init__(parent_canvas)




    @property
    def dim(self):

        return self.canvas.dim - self.canvas.pad[:2] - self.canvas.pad[2:]


    def update_dimensions(self, **args):
        pass


    def draw(self):



        axes_top_left = (self.canvas.dom[0,0], self.canvas.dom[1,1])




        self.pdraw.rect(
            axes_top_left, self.dim, self.colors["axes_bg"],
            self.colors["axes_line"], on_axes=True)





class Title(Element):

    def __init__(self, parent_canvas, title):
        """
        Contains the plot title and title dimensions, centered above axes.
        """
        self.pos = np.zeros(2)
        self.title = title
        super().__init__(parent_canvas)

    def update_dimensions(self, **args):
        """
        Update the title position to a point centered above the axes.
        """
        self.pos[0] = self.canvas.pad[0] + self.canvas.axes.dim[0] / 2
        self.pos[1] = self.canvas.pad[1] / 2

    def draw(self):
        font, color =  self.fonts["title"]
        self.pdraw.text(
            self.title, font, color, self.pos, ha="center",
            va="center", on_axes=False)



class Axis(Element):

    X = 0
    Y = 1

    FIXED_TICK_POSITIONS = 0
    FIXED_TICK_VALUES = 1

    LABELS_NUMERICAL = 0
    LABELS_TEXT = 1


    def __init__(self, parent_canvas, orientation, margin=0.1, length=3):
        """


        Parameters
        ----------
        parent_canvas : Canvas
            Canvas to which the axis in linked.
        margin : float, optional
            margin between min, max bounds and the first, last ticks,
            expressed as a ratio of the full domain width. The default is 0.1.

        """
        super().__init__(parent_canvas)
        self.margin = margin
        self.pos_ticks = np.empty((0,2))
        self.pos_line = np.empty(2)
        self.labels = None
        self.length = length

        # Orientation: determines whether X or Y axis
        self.orientation = orientation

        # Tick mode: either fixed locations or fixed values
        self.tick_mode = None
        self.label_mode = None

        # axis_specific drawing paramaters
        if self.orientation == Axis.X:
            self.tick_direction = np.array((0, 1))
            self.text_va = "bottom"
            self.text_ha = "center"
        if self.orientation == Axis.Y:
            self.tick_direction = np.array((-1, 0))
            self.text_va = "center"
            self.text_ha = "right"

    @property
    def crossing(self):
        """
        Return the coordinates of the other axis at which the axis crosses.

        For an X-axis this would generally be at y = 0. However, this is not
        the case when 0 is not contained in the y-domain. In such cases, the
        X-axis crosses at either the min or max y value within the domain.
        """
        return np.clip(0, *self.canvas.dom[1 - self.orientation])

    def update_dimensions(self, **kwargs):
        """
        Recalculate the ticks locations and axis line.
        """
        # Create diagonal line
        pos_line = self.canvas.dom.T.copy()
        pos_line[:,1-self.orientation] = self.crossing
        self.pos_line = pos_line

        # Update ticks
        if self.tick_mode == Axis.FIXED_TICK_POSITIONS:

            # Compute diagonal ticks
            n = kwargs.get("num_ticks", self.pos_ticks.shape[0])
            span = np.diff(self.canvas.dom, axis=1)[:,0]
            offset = self.margin * span
            pos_ticks = np.linspace(
                *(self.canvas.dom.T + (offset, - offset)), n)

            # Set other axis to either zero or min/max other domain
            pos_ticks[:,1-self.orientation] = self.crossing
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


        self.pdraw.line(
            self.pos_line, self.colors["axis"], on_axes=True)

        tick_vector = self.tick_direction * self.length

        for i, (pos, label) in enumerate(zip(self.pos_ticks, self.labels)):

            self.pdraw.vector(
                pos, tick_vector, self.colors["axis"],
                on_axes=True)

            font, color =  self.fonts["tick"]
            offset = self.tick_direction * (2 + self.length)
            self.pdraw.text(
                label, font, color, pos, self.text_ha, self.text_va,
                offset, on_axes=True)


