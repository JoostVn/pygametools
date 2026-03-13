from inspect import getmembers
from matplotlib import pyplot as plt
import numpy as np
from math import ceil, floor, sqrt
from itertools import product


class Color:

    BLACK = (0, 0, 0)
    GREY1 = (40, 40, 40)
    GREY2 = (80, 80, 80)
    GREY3 = (120, 120, 120)
    GREY4 = (160, 160, 160)
    GREY5 = (195, 195, 195)
    GREY6 = (210, 210, 210)
    GREY7 = (225, 225, 225)
    GREY8 = (240, 240, 240)
    WHITE = (255, 255, 255)
    BLUE1 = (20, 20, 120)
    BLUE2 = (40, 40, 200)
    BLUE3 = (110, 110, 255)
    GREEN1 = (40, 100, 40)
    GREEN2 = (50, 200, 50)
    GREEN3 = (70, 255, 70)
    RED1 = (130, 0, 0)
    RED2 = (200, 40, 40)
    RED3 = (255, 90, 90)
    YELLOW1 = (180, 170, 0)
    YELLOW2 = (220, 220, 0)
    YELLOW3 = (255, 255, 0)
    ORANGE1 = (150, 100, 0)
    ORANGE2 = (200, 150, 0)
    ORANGE3 = (255, 210, 0)
    PURPLE1 = (100, 0, 100)
    PURPLE2 = (170, 0, 170)
    PURPLE3 = (255, 0, 255)
    CYAN1 = (20, 120, 130)
    CYAN2 = (50, 160, 180)
    CYAN3 = (150, 220, 230)

    @staticmethod
    def random_vibrant():
        """
        Return one random vibrant RGB color.
        """
        while True:
            rgb = np.random.randint(0, 256, 3)
            dif = abs(rgb - np.roll(rgb, 1)).sum()
            if dif > 350:
                return rgb

    @staticmethod
    def random_dull():
        """
        Return one random dull RGB color.
        """
        while True:
            rgb = np.random.randint(0, 256, 3)
            dif = abs(rgb - np.roll(rgb, 1)).sum()
            tot = rgb.sum()
            if (80 < dif < 150) and (200 < tot < 500):
                return rgb

    @staticmethod
    def random_different(n):
        """
        Return n random colors with maximized difference.

        The number of colors to return is given by n.
        """
        stepsize = int(255 / (ceil(n**(1/3))-1))
        steps = np.arange(0, 256, stepsize)
        cols = np.array(tuple(product(steps, repeat=3)))
        selected_idx = np.random.choice(np.arange(len(cols)), n, replace=False)
        return cols[selected_idx]



class ColorGradient:

    def __init__(self, color_1, color_2):
        self.c1 = np.array(color_1)
        self.c2 = np.array(color_2)
        self.width = self.c2 - self.c1

    def get_color(self, value):
        value = min(1, max(0, value))
        return self.c1 + self.width * value


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


if __name__ == '__main__':
    colorpreview()
