from dataclasses import dataclass
from .types import MetricCoordinatePair, MetricCoordinateArray, MetricCoordinates, Domain
from typing import Literal
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
            pos: MetricCoordinatePair,
            dim: MetricCoordinatePair,
            xdom: Domain,
            ydom: Domain,
            axes_xpad: MetricCoordinatePair=(40,10),
            axes_ypad: MetricCoordinatePair=(22,18)
            ):
        """
        Plain data container for shared Canvas layout metrics.

        Read-only from the outside: only `Canvas` writes to the private
        attributes directly. Elements receive a `PlotMetrics` instance as a
        method argument and may only read from it.
        """
        assert xdom[0] < xdom[1], "Invalid x domain"
        assert ydom[0] < ydom[1], "Invalid y domain"

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

    @property
    def dim(self) -> npt.NDArray[np.int_]:
        return self._dim

    @property
    def xdom(self) -> npt.NDArray[np.float64]:
        return self._xdom

    @property
    def ydom(self) -> npt.NDArray[np.float64]:
        return self._ydom

    @property
    def axes_xpad(self) -> npt.NDArray[np.int_]:
        return self._axes_xpad

    @property
    def axes_ypad(self) -> npt.NDArray[np.int_]:
        return self._axes_ypad

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

    def get_surface_pos(
            self,
            pos: MetricCoordinates,
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
            pos: MetricCoordinates,
            col: tuple,
            metrics: PlotMetrics,
            width: int = 1,
            on_axes: bool = True):
        """Draw a line between two points in pos given as [[x1, y1], [x2, y2]]."""
        draw_surface, draw_pos = self.get_surface_pos(pos, on_axes, metrics)
        pygame.draw.line(draw_surface, col, *draw_pos, width)

    def vector(
            self,
            pos: MetricCoordinates,
            vector: MetricCoordinates,
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

    def point(
            self,
            pos: MetricCoordinates,
            col: tuple,
            metrics: PlotMetrics,
            radius: int = 3,
            on_axes: bool = True):
        """Draw a filled circle at pos."""
        draw_surface, draw_pos = self.get_surface_pos(pos, on_axes, metrics)
        pygame.draw.circle(draw_surface, col, tuple(draw_pos.astype(int)), radius)

    def rect(
            self,
            pos: MetricCoordinates,
            dim: MetricCoordinates,
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
            pos: MetricCoordinates,
            ha: Literal["left", "center", "right"],
            va: Literal["top", "center", "bottom"],
            metrics: PlotMetrics,
            offset: MetricCoordinates = (0, 0),
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
