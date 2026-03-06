from .types import CoordinatePair, CoordinateArray, Coordinates
from typing import Literal
import pygame
import pygame
import pygame.gfxdraw
import numpy as np
from pygametools.color import Color


class PlotTheme:

    def __init__(self, **kwargs):
        """
        Plot color and font properties.
        """
        pygame.init()
        
        self.colors = {
            "canvas_bg": kwargs.get("cols_canvas_bg", Color.GREY6),
            "canvas_line": kwargs.get("cols_canvas_line", Color.GREY3),
            "axes_bg": kwargs.get("cols_axes_bg", Color.WHITE),
            "axes_line": kwargs.get("cols_axes_line", Color.GREY3)}        
        font_type = "msreferencesansserif"
        self.fonts = {
            "title": (pygame.font.SysFont(font_type, 12), Color.BLACK),
            "legend": (pygame.font.SysFont(font_type, 10), Color.BLACK),
            "tick": (pygame.font.SysFont(font_type, 8), Color.BLACK)}


class PlotRenderer:

    def __init__(self, parent_canvas, **kwargs):
        self.parent_canvas = parent_canvas
        self.surface_canvas = pygame.Surface(self.canvas.metrics.dim)
        self.surface_axes = pygame.Surface(self.canvas.axes.dim)
        
    @property
    def canvas(self):
        return self.parent_canvas

    @property
    def metrics(self):
        return self.canvas.metrics

    def update_metrics(self, metric: Literal['pos', 'dim', 'xdom', 'ydom', 'xpad', 'ypad'] | None=None):

        if metric == 'dim':
            self.surface_canvas = pygame.Surface(self.canvas.metrics.dim)
            self.surface_axes = pygame.Surface(self.canvas.metrics.axes_dim)

        if metric == "pad":
            self.surface_axes = pygame.Surface(self.canvas.axes_dim)

    def clear(self):
        """
        Reset the draw surfaces to allow the plots to be re-drawn.
        """
        self.surface_canvas.fill(self.canvas.theme.colors["canvas_bg"])
        self.surface_axes.fill(self.canvas.theme.colors["axes_bg"])
        
    def draw(self, surface):
        """
        Draw the plot surface on another Pygame surface.
        """
        self.surface_canvas.blit(
            self.surface_axes,
            (self.canvas.metrics.axes_xpad[0], self.canvas.metrics.axes_ypad[0]))

        surface.blit(self.surface_canvas, self.metrics.pos)

    def get_surface_pos(
            self, pos: Coordinates,
            on_axes: bool) -> tuple[pygame.Surface, Coordinates]:
        """
        Return either the canvas or axes sureface and convert coordinates.

        If on_axes == False, return the canvas surface with pygame
        coordinates, where (0,0) is the top left of canvas. If on_axes == True,
        return the axes coordinates and convert graph coordinates to pygame
        coordinates, where (0,0) is the top left of axes.

        To convert coordinates, scale based on the x and y domains and and
        reverse the y-coordinates. If pos is a list of points, it should have
        shape (nr_points, 2).
        """

        if not on_axes:
            return self.surface_canvas, pos

        # Compute position of point as a ratio of domains
        relative_pos = np.array([
            (pos[0] - self.metrics.xdom[0]) / self.metrics.xdom_span,
            (pos[1] - self.metrics.ydom[0]) / self.metrics.ydom_span
        ])

        # Reverse y coordinate
        if relative_pos.ndim == 2:
            relative_pos[:,1] = 1 - relative_pos[:,1]
        else:
            relative_pos[1] = 1 - relative_pos[1]

        # Apply relative coordinates to pygame coordinates
        pos_axes = self.canvas.axes.dim * relative_pos
        pos_axes = pos_axes.astype(int)

        return self.surface_axes, pos_axes

    def circle(self, on_axes=True):
        raise NotImplementedError

    def line(self, pos: Coordinates, col: tuple, width=1, on_axes: bool=True):
        """
        Draw a line between two points in pos given as [[x1, y1], [x2, y2]].
        """
        draw_surface, draw_pos = self.get_surface_pos(pos, on_axes)

        pygame.draw.line(draw_surface, col, *draw_pos, width)

    def vector(
            self, pos: CoordinatePair,
            vector: CoordinatePair,
            col: tuple, 
            on_axes: bool=True):
        """
        Draw a vector from a given pos and direction.

        Pos can either be given in graph coordinates or pygame coordinates, but
        the vector is always in pygame coorindates. This makes it useful to
        draw graph elements of contant size such as axis ticks and markers.
        """
        draw_surface, draw_pos = self.get_surface_pos(pos, on_axes)
        pygame.draw.line(draw_surface, col, draw_pos, draw_pos+vector)

    def rect(
            self,
            pos: CoordinatePair,
            dim: CoordinatePair,
            facecol: tuple | None=None,
            linecol: tuple | None=None,
            on_axes: bool=True):

        draw_surface, draw_pos = self.get_surface_pos(pos, on_axes)
        rect = pygame.Rect(*draw_pos, *dim)

        if facecol is not None:
            pygame.draw.rect(draw_surface, facecol, rect)

        if linecol is not None:
            pygame.draw.rect(draw_surface, linecol, rect, width=1)

    def text(
            self,
            text: str,
            font: pygame.font.Font,
            col: tuple,
            pos: CoordinatePair,
            ha: Literal["left", "center", "right"],
            va: Literal["top", "center", "bottom"],
            offset: CoordinatePair = (0,0),
            on_axes: bool=True):
        """
        offset : TYPE, optional
            Offset in Pygame coordinates. Useful when drawing text with graph
            coordinates that needs to be slightly but contantly ofsset to
            prevent overlap with data or ticks. The default is (0,0).
        graph_coords : TYPE, optional
            DESCRIPTION. The default is False.
        """
        draw_surface, draw_pos = self.get_surface_pos(pos, on_axes)

        text_block = font.render(text, True, col)

        # Text block dimensions for alignment
        rect = text_block.get_rect()
        x, y = draw_pos + offset

        # Horizontal alignment
        if ha == "center":
            x = x - rect.width / 2
        elif ha == "right":
            x = x - rect.width
        elif ha == "left":
            pass

        # Vertical alignment
        if va == "center":
            y = y - rect.height / 2
        elif va == "top":
            y = y - rect.height
        elif va == "bottom":
            pass

        draw_surface.blit(text_block, (x,y))
