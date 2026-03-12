from dataclasses import dataclass
from .types import CoordinatePair, CoordinateArray, Coordinates, Domain
from typing import Literal, Callable
import numpy.typing as npt
import pygame
import pygame.gfxdraw
import numpy as np
from pygametools.color import Color
from pygametools.fonts import load_font


class PlotTheme:

    def __init__(self, **kwargs):
        """
        Plot color and font properties.
        """
        self.colors = {
            "canvas_bg": kwargs.get("cols_canvas_bg", Color.GREY6),
            "canvas_line": kwargs.get("cols_canvas_line", Color.GREY3),
            "axes_bg": kwargs.get("cols_axes_bg", Color.WHITE),
            "axes_line": kwargs.get("cols_axes_line", Color.GREY3)}
        self.fonts = {
            "title":  (load_font('Inter-VariableFont_opsz,wght.ttf', 12), Color.BLACK),
            "legend": (load_font('Inter-VariableFont_opsz,wght.ttf', 10), Color.BLACK),
            "tick":   (load_font('Inter-VariableFont_opsz,wght.ttf', 8), Color.BLACK)}


class PlotMetrics:

    def __init__(
            self,
            on_change: Callable[[str], None],
            pos: CoordinatePair,
            dim: CoordinatePair,
            xdom: Domain,
            ydom: Domain,
            axes_xpad: CoordinatePair=(40,10),
            axes_ypad: CoordinatePair=(22,18)
            ):
        """
        Holds shared layout data for a Canvas.

        When any metric is changed via its setter, ``on_change`` is called with
        the name of the changed metric. ``Canvas`` supplies its
        ``_on_metrics_changed`` method as this callback so it can propagate the
        update to all registered elements.
        """
        assert xdom[0] < xdom[1], "Invalid x domain"
        assert ydom[0] < ydom[1], "Invalid y domain"

        self._on_change = on_change
        self._pos = np.array(pos, dtype=int)
        self._dim = np.array(dim, dtype=int)
        self._xdom = np.array(xdom, dtype=float)
        self._ydom = np.array(ydom, dtype=float)
        self._axes_xpad = np.array(axes_xpad, dtype=int)
        self._axes_ypad = np.array(axes_ypad, dtype=int)

    # Top-level metrics and properties
    @property
    def pos(self) -> npt.NDArray[np.int_]:
        return self._pos

    @pos.setter
    def pos(self, val: CoordinatePair):
        self._pos = np.array(val, dtype=int)
        self._on_change('pos')

    @property
    def dim(self) -> npt.NDArray[np.int_]:
        return self._dim

    @dim.setter
    def dim(self, val: CoordinatePair):
        self._dim = np.array(val, dtype=int)
        self._on_change('dim')

    @property
    def xdom(self) -> npt.NDArray[np.float64]:
        return self._xdom

    @xdom.setter
    def xdom(self, val: Domain):
        assert val[0] < val[1], "Invalid x domain"
        self._xdom = np.array(val, dtype=float)
        self._on_change('xdom')

    @property
    def ydom(self) -> npt.NDArray[np.float64]:
        return self._ydom

    @ydom.setter
    def ydom(self, val: Domain):
        assert val[0] < val[1], "Invalid y domain"
        self._ydom = np.array(val, dtype=float)
        self._on_change('ydom')

    @property
    def axes_xpad(self) -> npt.NDArray[np.int_]:
        return self._axes_xpad

    @axes_xpad.setter
    def axes_xpad(self, val: CoordinatePair):
        self._axes_xpad = np.array(val, dtype=int)
        self._on_change('xpad')

    @property
    def axes_ypad(self) -> npt.NDArray[np.int_]:
        return self._axes_ypad

    @axes_ypad.setter
    def axes_ypad(self, val: CoordinatePair):
        self._axes_ypad = np.array(val, dtype=int)
        self._on_change('ypad')

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


class PlotRenderer:

    # TODO: Should we use typing.py coordinate pairs here? That would also resolve the casting to int below
    def __init__(self, dim: npt.ArrayLike, axes_dim: npt.ArrayLike):
        self.surface_canvas = pygame.Surface(tuple(np.array(dim, dtype=int)))
        self.surface_axes = pygame.Surface(tuple(np.array(axes_dim, dtype=int)))

    def resize(self, dim: npt.ArrayLike, axes_dim: npt.ArrayLike):
        """Recreate surfaces when canvas or axes dimensions change."""
        self.surface_canvas = pygame.Surface(tuple(np.array(dim, dtype=int)))
        self.surface_axes = pygame.Surface(tuple(np.array(axes_dim, dtype=int)))

    def clear(self, theme: PlotTheme):
        """Reset draw surfaces to background colors before a new frame."""
        self.surface_canvas.fill(theme.colors["canvas_bg"])
        self.surface_axes.fill(theme.colors["axes_bg"])

    def draw(self, surface: pygame.Surface, metrics: PlotMetrics):
        """Blit axes onto canvas, then canvas onto the target surface."""
        self.surface_canvas.blit(
            self.surface_axes,
            (metrics.axes_xpad[0], metrics.axes_ypad[0]))
        surface.blit(self.surface_canvas, tuple(metrics.pos))

    # TODO: make metrics the second argument in all draw functions (after self)
    def get_surface_pos(
            self,
            pos: Coordinates,
            on_axes: bool,
            metrics: PlotMetrics) -> tuple[pygame.Surface, npt.NDArray]:
        """
        Return either the canvas or axes surface and convert coordinates.

        If on_axes == False, return the canvas surface with pygame
        coordinates, where (0,0) is the top left of canvas. If on_axes == True,
        return the axes surface and convert graph coordinates to pygame
        coordinates, where (0,0) is the top left of axes.
        """
        if not on_axes:
            return self.surface_canvas, np.asarray(pos)

        # Compute position of point as a ratio of domains
        pos = np.asarray(pos)
        relative_pos = np.array([
            (pos[0] - metrics.xdom[0]) / metrics.xdom_span,
            (pos[1] - metrics.ydom[0]) / metrics.ydom_span
        ])

        # Reverse y coordinate (graph y-up --> pygame y-down)
        if relative_pos.ndim == 2:
            relative_pos[:,1] = 1 - relative_pos[:,1]
        else:
            relative_pos[1] = 1 - relative_pos[1]

        pos_axes = (metrics.axes_dim * relative_pos).astype(int)
        return self.surface_axes, pos_axes

    def circle(self, on_axes=True):
        raise NotImplementedError

    def line(
            self,
            pos: Coordinates,
            col: tuple,
            metrics: PlotMetrics,
            width: int = 1,
            on_axes: bool = True):
        """Draw a line between two points in pos given as [[x1, y1], [x2, y2]]."""
        draw_surface, draw_pos = self.get_surface_pos(pos, on_axes, metrics)
        pygame.draw.line(draw_surface, col, *draw_pos, width)

    def vector(
            self,
            pos: Coordinates,
            vector: Coordinates,
            col: tuple,
            metrics: PlotMetrics,
            on_axes: bool = True):
        """
        Draw a vector from a given pos and direction.

        pos can be in graph or canvas coordinates; vector is always in pygame
        coordinates. Useful for fixed-size elements like axis ticks.
        """
        draw_surface, draw_pos = self.get_surface_pos(pos, on_axes, metrics)
        end = (draw_pos + np.asarray(vector)).astype(int)
        pygame.draw.line(draw_surface, col, tuple(draw_pos.astype(int)), tuple(end))

    def rect(
            self,
            pos: Coordinates,
            dim: Coordinates,
            metrics: PlotMetrics,
            facecol: tuple | None = None,
            linecol: tuple | None = None,
            on_axes: bool = True):

        draw_surface, draw_pos = self.get_surface_pos(pos, on_axes, metrics)
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
            pos: Coordinates,
            ha: Literal["left", "center", "right"],
            va: Literal["top", "center", "bottom"],
            metrics: PlotMetrics,
            offset: Coordinates = (0, 0),
            on_axes: bool = True):
        """
        Args:
            ha: horizontal alignment
            va: vertical alignment
            offset : TYPE, optional
                Offset in Pygame coordinates. Useful when drawing text with graph
                coordinates that needs to be slightly but contantly ofsset to
                prevent overlap with data or ticks. The default is (0,0).
        """

        draw_surface, draw_pos = self.get_surface_pos(pos, on_axes, metrics)

        text_block = font.render(text, True, col)
        text_rect = text_block.get_rect()
        x, y = draw_pos + offset

        # Horizontal alignment
        if ha == "center":
            x = x - text_rect.width // 2
        elif ha == "right":
            x = x - text_rect.width

        # Vertical alignment
        if va == "center":
            y = y - text_rect.height // 2
        elif va == "top":
            y = y - text_rect.height

        draw_surface.blit(text_block, (x, y))


@dataclass
class DrawContext:

    theme: PlotTheme
    metrics: PlotMetrics
    renderer: PlotRenderer
