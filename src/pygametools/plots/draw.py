import pygame
import pygame
import pygame.gfxdraw
import numpy as np
from pygametools.color import Color




# class PlotDraw:


#     def __init__(self, parent_canvas, **kwargs):
#         self.parent_canvas = parent_canvas
#         self.surface_canvas = pygame.Surface(self.canvas.metrics.dim)
      
#         # TODO surface for legend

#     @property
#     def canvas(self):
#         return self.parent_canvas

#     @property
#     def metrics(self):
#         return self.canvas.metrics

#     def update_dimensions(self, **args):
#         if "dim" in args:
#             self.surface_canvas = pygame.Surface(self.canvas.dim)
#             self.surface_axes = pygame.Surface(self.canvas.axes.dim)

#         if "pad" in args:
#             self.surface_axes = pygame.Surface(self.canvas.axes.dim)



#########################################################################

class PlotDraw:


    def __init__(self, parent_canvas, **kwargs):
        self.parent_canvas = parent_canvas


        self.surface_canvas = pygame.Surface(self.canvas.metrics.dim)
        
        # self.surface_axes = pygame.Surface(self.canvas.axes.dim)

        # TODO surface for legend

    @property
    def canvas(self):
        return self.parent_canvas

    @property
    def metrics(self):
        return self.canvas.metrics

    def update_dimensions(self, **args):
        """
        Updates the two draw surfaces.

        Parameters
        ----------
        **args : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """

        if "dim" in args:
            self.surface_canvas = pygame.Surface(self.canvas.dim)
            
            # self.surface_axes = pygame.Surface(self.canvas.axes.dim)

        if "pad" in args:
            pass
            # self.surface_axes = pygame.Surface(self.canvas.axes.dim)


    def clear(self):
        """
        Reset the draw surfaces to allow the plots to be re-drawn.
        """
        self.surface_canvas.fill(self.canvas.theme.colors["canvas_bg"])
        # self.surface_axes.fill(self.canvas.theme.colors["axes_bg"])


    def draw(self, surface):
        """
        Draw the plot surface on another Pygame surface.

        Parameters
        ----------
        surface : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """

        # TODO: what is this method doing here? shouldnt it be in Canvas?

        # self.surface_canvas.blit(
        #     self.surface_axes,
        #     (self.canvas.metrics.axes_xpad[0], self.canvas.metrics.axes_ypad[0]))

        surface.blit(self.surface_canvas, self.metrics.pos)


    def get_surface_pos(self, pos, on_axes):
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
        # TODO: what dimensions for pos do we allow? single point, list of points, numpy array?
        # TODO: don't return both surface and pos, but have separate methods

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
        #pos_axes = self.canvas.pos + self.canvas.pad[:2] + self.canvas.axes.dim * relative_pos
        pos_axes = self.canvas.axes.dim * relative_pos

        pos_axes = pos_axes.astype(int)




        return self.surface_axes, pos_axes


    def circle(self, on_axes=True):
        raise NotImplementedError

    def line(self, pos, col, width=1, on_axes=True):
        """
        Draw a line between two points in pos given as [[x1, y1], [x2, y2]].
        """
        draw_surface, draw_pos = self.get_surface_pos(pos, on_axes)

        pygame.draw.line(draw_surface, col, *draw_pos, width)


    def vector(self, pos, vector, col, on_axes=True):
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
            pos: np.ndarray,
            dim: np.ndarray,
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
            self, text, font, col, pos, ha, va, offset=(0,0), on_axes=True):
        """


        Params
        ----------
        text : TYPE
            DESCRIPTION.
        font : TYPE
            DESCRIPTION.
        col : TYPE
            DESCRIPTION.
        pos : TYPE
            DESCRIPTION.
        ha : TYPE
            DESCRIPTION.
        va : TYPE
            DESCRIPTION.
        offset : TYPE, optional
            Offset in Pygame coordinates. Useful when drawing text with graph
            coordinates that needs to be slightly but contantly ofsset to
            prevent overlap with data or ticks. The default is (0,0).
        graph_coords : TYPE, optional
            DESCRIPTION. The default is False.

        Returns
        -------
        None.

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






