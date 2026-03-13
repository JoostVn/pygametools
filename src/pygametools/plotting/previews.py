from inspect import getmembers
import pygame
import time
from pygametools.color import Color
import numpy as np
from math import sqrt, ceil, floor
from matplotlib import pyplot as plt



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

