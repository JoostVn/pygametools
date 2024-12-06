import pygame
import pygame.gfxdraw
import numpy as np
from pygametools.color import Color
# from scipy.ndimage import zoom
# from debug.time import ConsecutiveLineTimer, FuncStats



class PlotDraw:

    """
    Contains methods for drawing plot elements to the pygame
    screen. Plotting methods are either based on pygame
    coordinates (pgc), which refer to positions in the screen,
    or graph coordinates (grc), which refer to postions in the
    graph with respect to its domain. Functions based on the latter
    coordinate system first have to convert to pgc prior to drawing.
    """

    FONT = 'msreferencesansserif'

    def __init__(self, plot):
        pygame.init()

        # Parent plot instance and dimensions
        self.plot = plot

        # Fonts
        self.font_l = (pygame.font.SysFont(self.FONT, 14), Color.BLACK)
        self.font_m = (pygame.font.SysFont(self.FONT, 10), Color.BLACK)
        self.font_s = (pygame.font.SysFont(self.FONT, 8), Color.BLACK)

        # Standard colors
        self.color_bg = Color.WHITE
        self.color_lines = Color.BLACK

    def coords(self, points):
        """
        Converts graph coordinate (grc) points to Pygame coordinates (pgc)
        for drawing. Adjusts for scaling and reverses the y-coordinates.
        if a list of points is passed, it should have shape (nr_points, 2)
        """
        scaled = (points - self.plot.d_min) / self.plot.d_len
        if scaled.ndim == 2:
            scaled[:,1] = 1 - scaled[:,1]
        else:
            scaled[1] = 1 - scaled[1]
        coordinates = self.plot.dim * scaled + self.plot.pos
        coordinates = coordinates.astype(int)
        return coordinates

    def inscope_points(self, x, y):
        """
        Return a boolean vector that indicates for each given point
        wether it is within the drawing domain. Used for preventing plot
        points to get drawn outside the plot border.
        """
        isnan_values = (np.isnan(y) | np.isnan(x))
        num_indices = np.arange(x.shape[0])[~isnan_values]
        num_inscope = np.all((
            x[num_indices] >= self.plot.xaxis.domain[0],
            x[num_indices] <= self.plot.xaxis.domain[1],
            y[num_indices] >= self.plot.yaxis.domain[0],
            y[num_indices] <= self.plot.yaxis.domain[1]),
            axis=0)
        inscope_indices = num_indices[num_inscope]
        inscope_all = np.zeros(x.shape[0]).astype(bool)
        inscope_all[inscope_indices] = True

        return inscope_all

    def grc_lines(self, screen, color, points, width=1, aa=False):
        """
        >> Graph coordinates
        Draws a line on the screen trough a list of points.
        """
        points = self.coords(points)
        self.pgc_lines(screen, color, points, width, aa)

    def pgc_lines(self, screen, color, points, width=1, aa=False):
        """
        >> Pygame coordinates
        Draws a line on the screen trough a list of points.
        """
        if aa and width == 1:
            pygame.draw.aalines(screen, color, False, points)
        else:
            pygame.draw.lines(screen, color, False, points, width)

    def grc_line(self, screen, color, endpoints, width=1, aa=False):
        """
        >> Graph coordinates
        Draws a line on the screen between two endpoints.
        """
        endpoints = self.coords(endpoints)
        self.pgc_line(screen, color, endpoints, width, aa)

    def pgc_line(self, screen, color, endpoints, width=1, aa=False):
        """
        >> Pygame coordinates
        Draws a line on the screen between two endpoints.
        """
        if aa and width == 1:
            pygame.draw.aaline(screen, color, *endpoints, width)
        else:
            pygame.draw.line(screen, color, *endpoints, width)

    def grc_tick(self, screen, color, position, offset):
        """
        >> Graph coordinates / Pygame coordinates
        Draws a line from a graph coordinate point to a given offset in
        pgc. Used from drawing lines of fixed lenght from graph points,
        such as axis ticks and scatterpoint '+' markers.
        """
        position = self.coords(position)
        pygame.draw.line(screen, color, position, position + offset)

    def grc_point(self, screen, color, point, size):
        """
        >> Graph coordinates
        Draws a filled circle on the screen with a given size.
        """
        point = self.coords(point)
        self.pgc_point(screen, color, point, size)

    def pgc_point(self, screen, color, point, size):
        """
        >> Pygame coordinates
        Draws a filled circle on the screen with a given size.
        """
        pygame.gfxdraw.aacircle(screen, *point, size, color)
        pygame.gfxdraw.filled_circle(screen, *point, size, color)

    def grc_circle(self, screen, color, point, size):
        """
        >> Graph coordinates
        Draws an unfilled circle on the screen with a given size.
        """
        point = self.coords(point)
        self.pgc_circle(screen, color, point, size)

    def pgc_circle(self, screen, color, point, size):
        """
        >> Pygame coordinates
        Draws an unfilled circle on the screen with a given size.
        """
        pygame.gfxdraw.aacircle(screen, *point, size, color)

    def grc_rect(self, screen, color, top_left, lower_right, border=False, fill=False):
        """
        >> Graph coordinates
        Draws a rectangle on the screen with optional border.
        """
        dimensions = self.coords(np.vstack((top_left, lower_right)))
        self.pgc_rect(screen, color, *dimensions, border, fill)

    def pgc_rect(self, screen, color, top_left, lower_right, border=False, fill=False):
        """
        >> Pygame coordinates
        Draws a rectangle on the screen with optional border.
        """
        (left, top), (right, bottom) = (top_left, lower_right)
        rect = pygame.Rect(left, top, right-left, bottom-top)
        if fill:
            pygame.draw.rect(screen, color, rect)
        if border:
            corners = ((left,top),(right,top),(right,bottom),(left,bottom))
            pygame.draw.lines(screen, Color.BLACK, True, corners, 1)

    def grc_text(self, screen, text, pos, font, offset=(0,0), centerx=False,
                 rjustx=False):
        """
        >> Graph coordinates
        Draws centerd text at a given position. The optional offset parameter
        offsets the text position by some pygame coodinate value for x and y.
        """
        pos = self.coords(pos) + offset
        self.pgc_text(screen, text, pos, font, centerx, rjustx)

    def pgc_text(self, screen, text, pos, font, centerx=False, rjustx=False):
        """
        >> Pygame coordinates
        Draws left-alligned text at a given position. Options:
            - centerx: overrides pos[0] to center text relative to original
            pos[0]
            - rjustx: overrides pos[0] to right-adjust text relative to
            original [pos[0]]
        """
        font_type, font_color = font
        pygame_text = font_type.render(text, True, font_color)

        # Alliging text block
        if centerx or rjustx:
            rect = pygame_text.get_rect()
            x, y = pos
        if centerx:
            pos = (x - rect.width / 2, y)
        if rjustx:
            pos = (x - rect.width, y)

        screen.blit(pygame_text, pos)

    def grc_array_image(self, screen, arr):
        """
        >> Graph coordinates
        Draw array of RGB colors as an image on the plot. The image is
        positioned such that the full plot dimensions is filled.
        """

        # TODO: Only scale when dimensions change
        # TODO: Implement zoom without scipy

        return 

        # TODO: Only scale when dimensions change

        # Scale array to plot dimensions
        scale_levels = np.divide(self.plot.dim, arr.shape[:-1])
        # scaled_arr = zoom(arr, [*scale_levels, 1], order=0).astype(int)

        # Create surface from array and draw
        surface = pygame.surfarray.make_surface(scaled_arr)
        screen.blit(surface, self.plot.pos)


