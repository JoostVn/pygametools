from dataclasses import dataclass
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
            "canvas_bg": kwargs.get("cols_canvas_bg", Color.GREY7),
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
            pos: npt.ArrayLike,
            dim: npt.ArrayLike,
            xdom: npt.ArrayLike,
            ydom: npt.ArrayLike,
            axes_xpad: npt.ArrayLike = (40, 10),
            axes_ypad: npt.ArrayLike = (22, 18)
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
        self.surface_axes = pygame.Surface(tuple(np.array(axes_dim, dtype=int)), pygame.SRCALPHA)

    def resize(self, dim: npt.ArrayLike, axes_dim: npt.ArrayLike):
        """Recreate surfaces when canvas or axes dimensions change."""
        self.surface_canvas = pygame.Surface(tuple(np.array(dim, dtype=int)))
        self.surface_axes = pygame.Surface(tuple(np.array(axes_dim, dtype=int)), pygame.SRCALPHA)

    def clear(self, theme: PlotTheme):
        """Reset draw surfaces to background colors before a new frame."""
        self.surface_canvas.fill(theme.colors["canvas_bg"])
        self.surface_axes.fill(theme.colors["axes_bg"])

    def draw(self, metrics: PlotMetrics, surface: pygame.Surface):
        """Blit axes onto canvas, then canvas onto the target surface."""
        self.surface_canvas.blit(
            self.surface_axes,
            (metrics.axes_xpad[0], metrics.axes_ypad[0]))
        surface.blit(self.surface_canvas, tuple(metrics.pos))

    def _graph_to_canvas(
            self,
            pos: npt.ArrayLike,
            metrics: PlotMetrics) -> npt.NDArray[np.int_]:
        """Convert graph coordinates to axes-surface pixel coordinates.

        Handles both a single point (shape (2,)) and arrays of points (shape
        (N, 2)). Y axis is flipped: higher graph Y maps to lower pixel Y.
        """
        pos = np.asarray(pos, dtype=float)
        rel_x = (pos[..., 0] - metrics.xdom[0]) / metrics.xdom_span
        rel_y = 1.0 - (pos[..., 1] - metrics.ydom[0]) / metrics.ydom_span
        return (np.stack([rel_x, rel_y], axis=-1) * metrics.axes_dim).astype(int)

    # ---- Internal helpers ----

    def _draw_point(
            self,
            surface: pygame.Surface,
            pos_px: npt.NDArray[np.int_],
            col: tuple[int, int, int],
            radius: int,
            alpha: float):
        """Draw an anti-aliased filled circle on a surface at pixel coordinates.

        Uses a per-point SRCALPHA temp surface so that overlapping semi-transparent
        circles accumulate opacity correctly via src-over compositing on blit.
        """
        x, y = int(pos_px[0]), int(pos_px[1])
        rgba = (*col[:3], int(round(255 * alpha)))
        size = radius * 2 + 1
        tmp = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.gfxdraw.aacircle(tmp, radius, radius, radius, rgba)
        pygame.gfxdraw.filled_circle(tmp, radius, radius, radius, rgba)
        surface.blit(tmp, (x - radius, y - radius))

    def _draw_text(
            self,
            surface: pygame.Surface,
            text: str,
            font: pygame.font.Font,
            col: tuple[int, int, int],
            pos_px: npt.NDArray,
            ha: Literal["left", "center", "right"],
            va: Literal["top", "center", "bottom"],
            offset: npt.ArrayLike = (0, 0)):
        """Render and blit text on a surface at pixel coordinates."""
        text_block = font.render(text, True, col)
        text_rect = text_block.get_rect()
        x, y = np.asarray(pos_px) + offset
        if ha == "center":
            x = x - text_rect.width // 2
        elif ha == "right":
            x = x - text_rect.width
        if va == "center":
            y = y - text_rect.height // 2
        elif va == "top":
            y = y - text_rect.height
        surface.blit(text_block, (x, y))

    # ---- Canvas-coordinate draw methods ----

    def draw_circle_canvas(
            self,
            pos: npt.ArrayLike,
            col: tuple[int, int, int],
            radius: int):
        raise NotImplementedError

    def draw_line_canvas(
            self,
            pos: npt.ArrayLike,
            col: tuple[int, int, int]):
        """Draw an anti-aliased line between two canvas-coordinate points [[x1,y1],[x2,y2]]."""
        pos = np.asarray(pos)
        pygame.draw.aaline(
            self.surface_canvas, col,
            tuple(pos[0].astype(int)), tuple(pos[1].astype(int)))

    def draw_vector_canvas(
            self,
            pos: npt.ArrayLike,
            vector: npt.ArrayLike,
            col: tuple[int, int, int]):
        """Draw a line from pos to pos+vector in canvas coordinates.

        vector is always a pixel offset; useful for fixed-size elements like axis ticks.
        """
        pos = np.asarray(pos)
        end = (pos + np.asarray(vector)).astype(int)
        pygame.draw.line(self.surface_canvas, col, tuple(pos.astype(int)), tuple(end))

    def draw_point_canvas(
            self,
            pos: npt.ArrayLike,
            col: tuple[int, int, int],
            radius: int,
            alpha: float = 1):
        """Draw an anti-aliased filled circle at a canvas-coordinate position."""
        self._draw_point(self.surface_canvas, np.asarray(pos), col, radius, alpha)

    def draw_polyline_canvas(
            self,
            points: npt.ArrayLike,
            col: tuple[int, int, int]):
        """Draw a connected polyline through an (N, 2) array of canvas-coordinate points."""
        pts = np.asarray(points, dtype=int)
        if len(pts) < 2:
            return
        pygame.draw.aalines(self.surface_canvas, col, False, pts.tolist())

    def draw_rect_canvas(
            self,
            pos: npt.ArrayLike,
            dim: npt.ArrayLike,
            facecol: tuple[int, int, int] | None = None,
            linecol: tuple[int, int, int] | None = None):
        """Draw a rectangle at a canvas-coordinate position."""
        rect = pygame.Rect(*np.asarray(pos).astype(int), *dim)
        if facecol is not None:
            pygame.draw.rect(self.surface_canvas, facecol, rect)
        if linecol is not None:
            pygame.draw.rect(self.surface_canvas, linecol, rect, width=1)

    def draw_text_canvas(
            self,
            text: str,
            font: pygame.font.Font,
            col: tuple[int, int, int],
            pos: npt.ArrayLike,
            ha: Literal["left", "center", "right"],
            va: Literal["top", "center", "bottom"],
            offset: npt.ArrayLike = (0, 0)):
        """Render text at a canvas-coordinate position."""
        self._draw_text(self.surface_canvas, text, font, col, np.asarray(pos), ha, va, offset)

    # ---- Graph-coordinate draw methods ----

    def draw_circle_graph(
            self,
            metrics: PlotMetrics,
            pos: npt.ArrayLike,
            col: tuple[int, int, int],
            radius: int):
        raise NotImplementedError

    def draw_line_graph(
            self,
            metrics: PlotMetrics,
            pos: npt.ArrayLike,
            col: tuple[int, int, int]):
        """Draw an anti-aliased line between two graph-coordinate points [[x1,y1],[x2,y2]]."""
        pts = self._graph_to_canvas(np.asarray(pos, dtype=float), metrics)
        pygame.draw.aaline(self.surface_axes, col, tuple(pts[0]), tuple(pts[1]))

    def draw_vector_graph(
            self,
            metrics: PlotMetrics,
            pos: npt.ArrayLike,
            vector: npt.ArrayLike,
            col: tuple[int, int, int]):
        """Draw a line from pos to pos+vector; pos in graph coordinates, vector in pixels."""
        draw_pos = self._graph_to_canvas(pos, metrics)
        end = (draw_pos + np.asarray(vector)).astype(int)
        pygame.draw.line(self.surface_axes, col, tuple(draw_pos), tuple(end))

    def draw_point_graph(
            self,
            metrics: PlotMetrics,
            pos: npt.ArrayLike,
            col: tuple[int, int, int],
            radius: int,
            alpha: float = 1):
        """Draw an anti-aliased filled circle at a graph-coordinate position."""
        self._draw_point(self.surface_axes, self._graph_to_canvas(pos, metrics), col, radius, alpha)

    def draw_polyline_graph(
            self,
            metrics: PlotMetrics,
            points: npt.ArrayLike,
            col: tuple[int, int, int]):
        """Draw a connected polyline through an (N, 2) array of graph-coordinate points."""
        pts = np.asarray(points, dtype=float)
        if len(pts) < 2:
            return
        pygame.draw.aalines(self.surface_axes, col, False, self._graph_to_canvas(pts, metrics).tolist())

    def draw_rect_graph(
            self,
            metrics: PlotMetrics,
            pos: npt.ArrayLike,
            dim: npt.ArrayLike,
            facecol: tuple[int, int, int] | None = None,
            linecol: tuple[int, int, int] | None = None):
        """Draw a rectangle; pos is the bottom-left corner and dim is (width, height), both in graph coordinates."""
        pos = np.asarray(pos, dtype=float)
        dim = np.asarray(dim, dtype=float)
        bl_px = self._graph_to_canvas(pos, metrics)
        tr_px = self._graph_to_canvas(pos + dim, metrics)
        top_left = np.minimum(bl_px, tr_px)
        size = np.abs(tr_px - bl_px)
        rect = pygame.Rect(*top_left, *size)
        if facecol is not None:
            pygame.draw.rect(self.surface_axes, facecol, rect)
        if linecol is not None:
            pygame.draw.rect(self.surface_axes, linecol, rect, width=1)

    def draw_text_graph(
            self,
            metrics: PlotMetrics,
            text: str,
            font: pygame.font.Font,
            col: tuple[int, int, int],
            pos: npt.ArrayLike,
            ha: Literal["left", "center", "right"],
            va: Literal["top", "center", "bottom"],
            offset: npt.ArrayLike = (0, 0)):
        """Render text at a graph-coordinate position."""
        self._draw_text(self.surface_axes, text, font, col, self._graph_to_canvas(pos, metrics), ha, va, offset)


@dataclass
class DrawContext:

    theme: PlotTheme
    metrics: PlotMetrics
    renderer: PlotRenderer
