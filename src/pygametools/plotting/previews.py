from inspect import getmembers
import pygame
import time
from pygametools.color import Color
import numpy as np
from math import sqrt, ceil, floor
from matplotlib import pyplot as plt


def colorpreview():
    """
    Function that neatly plots a preview of all colors in the PygamePlot
    module in addition to previews of randomly generated colors.
    """
    fig, axs = plt.subplots(
        1, 2, figsize=(8,7), gridspec_kw={'width_ratios':(1,1.8)})

    # ______________________ Named colors
    ax = axs[1]

    # Fetch colors and colornames from Color class
    names, colors = [], []
    for i in getmembers(Color):
        if type(i[1]) is tuple:
            names.append(i[0])
            colors.append(np.array(i[1])/255)

    # Determine points for scatterplots
    nr_colors = len(colors)
    nr_columns = floor(sqrt(nr_colors))
    nr_rows = ceil(nr_colors / nr_columns)
    points = [
        (col, row) for row in range(nr_rows-1, -1, -1)
        for col in range(nr_columns)]

    # Create annotated scatterplot for colors
    for point, color, name in zip(points[:nr_colors], colors, names):
        ax.scatter(*point, s=1200, c=[color], marker='s')
        text_point = np.add(point, (0, 0.4))
        ax.text(*text_point, name, horizontalalignment='center', fontsize=10)
    ax.set_xlim(-0.5, nr_columns-0.5)
    ax.set_ylim(-0.5, nr_rows-0.4)
    ax.axis('off')
    ax.tick_params(left=False,bottom=False,labelleft=False,labelbottom=False)
    ax.set_title('Named colors', fontsize=19, pad=20)

    # ______________________ Random colors
    ax = axs[0]
    n = 4

    # Create point coordinates for color scatter plots
    vibr_points = np.indices((n, n)).reshape(2, n**2)
    vibr_colors = np.array([Color.random_vibrant() for i in range(n**2)]) / 255
    dull_points = np.vstack((vibr_points[0], vibr_points[1] + n + 2))
    dull_colors = np.array([Color.random_dull() for i in range(n**2)]) / 255
    diff_points = np.vstack((dull_points[0], dull_points[1] + n + 2))
    diff_colors = Color.random_different(n**2) / 255

    # Scatterplot showing different colors
    ax.scatter(*vibr_points, c=vibr_colors, s=350, marker='s')
    ax.scatter(*dull_points, c=dull_colors, s=350, marker='s')
    ax.scatter(*diff_points, c=diff_colors, s=350, marker='s')
    ax.text((n-1)/2, n, 'Random vibrant',
            horizontalalignment='center', fontsize=11)
    ax.text((n-1)/2, (n + 2) + n, 'Random dull',
            horizontalalignment='center', fontsize=11)
    ax.text((n-1)/2, 2 * (n + 2) + n, 'Random different',
            horizontalalignment='center', fontsize=11)
    ax.set_xlim(-1.5, n + 0.5)
    ax.set_ylim(-1, 3 * (n + 2)-1)
    ax.tick_params(left=False,bottom=False,labelleft=False,labelbottom=False)
    ax.axis('off')
    ax.set_title('Random colors', fontsize=19, pad=20)


    fig.tight_layout()
    plt.show()



class PlotTester:

    def __init__(self, window_size, tick_len=1/30):
        """
        Class that can show a simple Pygame screen and static or dynamic
        Pygame plots. Used for plot testing, examples and prototyping.
        """
        pygame.init()
        self.bg = Color.GREY7
        self.tick_len = tick_len
        self.window_size = window_size
        self.static_canvasses = []
        self.dynamic_canvasses = []
        self.dynamic_funcs = []
        self.screen = pygame.display.set_mode(window_size)
        self.font = (pygame.font.SysFont('msreferencesansserif', 10), Color.BLACK)

    def add_static(self, canvas):
        """
        Add a static Pygame canvas to the window.
        """
        self.static_canvasses.append(canvas)

    def add_dynamic(self, canvas, update_func):
        """
        Add a dynamic Pygame canvas to the window. update_func should be a
        function func(canvas) that adds new data to the canvas plots.
        """
        self.dynamic_canvasses.append(canvas)
        self.dynamic_funcs.append(update_func)

    def show(self):
        """
        Show Pygame window and plots.
        """
        tick_start = time.time()
        while True:
            self.screen.fill(self.bg)
            for canvas in self.static_canvasses:
                canvas.draw(self.screen)
            for canvas, func in zip(self.dynamic_canvasses, self.dynamic_funcs):
                func(canvas)
                canvas.draw(self.screen)
            pygame.display.flip()
            t = (time.time() - tick_start)
            time.sleep(max(0, self.tick_len - t))
            tick_start = time.time()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

