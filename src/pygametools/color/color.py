import numpy as np
from math import ceil
from itertools import product


class Color:

    BLACK = (0, 0, 0)
    GREY1 = (40, 40, 40)
    GREY2 = (80, 80, 80)
    GREY3 = (120, 120, 120)
    GREY4 = (160, 160, 160)
    GREY5 = (200, 200, 200)
    GREY6 = (215, 215, 215)
    GREY7 = (230, 230, 230)
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

