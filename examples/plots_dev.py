
"""
Development testing for plots (plotting 2) module

TODO:
 - checkboxes for plot types (all in the same plot)
"""

from pygametools.plots.elements import Canvas
from pygametools.gui.base import Application
import pygame
from pygametools.gui.elements import Button, Slider, Label

class PlotTestApp(Application):

    def __init__(self, window_size):
        super().__init__(window_size)
        self.plot: Canvas = None  # type: ignore[assignment]
        
        # Slider values
        self._plot_xpos = 0
        self._plot_ypos = 0
        self._plot_xdim = 0
        self._plot_ydim = 0
        self._xdom_min = 0
        self._xdom_max = 0
        self._ydom_min = 0
        self._ydom_max = 0
        self._num_yticks = 0
        self._num_xticks = 0
        
    def update(self):
        pass

    def draw(self):
        self.plot.draw(self.screen)
        
    # GUI values
    @property
    def plot_xpos(self):
        return self._plot_xpos
    
    @plot_xpos.setter
    def plot_xpos(self, val: int | float):
        self._plot_xpos = int(val)
        self.plot.pos = (self._plot_xpos, self.plot.pos[1])

    @property
    def plot_ypos(self):
        return self._plot_ypos

    @plot_ypos.setter
    def plot_ypos(self, val: int | float):
        self._plot_ypos = int(val)
        self.plot.pos = (self.plot.pos[0], self._plot_ypos)

    @property
    def plot_xdim(self):
        return self._plot_xdim

    @plot_xdim.setter
    def plot_xdim(self, val: int | float):
        self._plot_xdim = int(val)
        self.plot.dim = (self._plot_xdim, self.plot.dim[1])

    @property
    def plot_ydim(self):
        return self._plot_ydim

    @plot_ydim.setter
    def plot_ydim(self, val: int | float):
        self._plot_ydim = int(val)
        self.plot.dim = (self.plot.dim[0], self._plot_ydim)
        
    @property
    def num_xticks(self):
        return self._num_xticks
    
    @num_xticks.setter
    def num_xticks(self, val: int | float):
        self._num_xticks = int(val)
        self.plot.axisx.tick_num = self._num_xticks
    
    @property
    def num_yticks(self):
        return self._num_yticks
    
    @num_yticks.setter
    def num_yticks(self, val):
        self._num_yticks = int(val)
        self.plot.axisy.tick_num = self._num_yticks

    @property
    def xdom_min(self):
        return self._xdom_min

    @xdom_min.setter
    def xdom_min(self, val: float):
        self._xdom_min = -(10 ** val)
        self.plot.xdom = (self._xdom_min, self.plot.xdom[1])

    @property
    def xdom_max(self):
        return self._xdom_max

    @xdom_max.setter
    def xdom_max(self, val: float):
        self._xdom_max = 10 ** val
        self.plot.xdom = (self.plot.xdom[0], self._xdom_max)

    @property
    def ydom_min(self):
        return self._ydom_min

    @ydom_min.setter
    def ydom_min(self, val: float):
        self._ydom_min = -(10 ** val)
        self.plot.ydom = (self._ydom_min, self.plot.ydom[1])

    @property
    def ydom_max(self):
        return self._ydom_max

    @ydom_max.setter
    def ydom_max(self, val: float):
        self._ydom_max = 10 ** val
        self.plot.ydom = (self.plot.ydom[0], self._ydom_max)
    

def main():

    # Create app first so that pygame.init() is called early
    app = PlotTestApp(window_size=(600,400))

    # Create test plot
    canvas = Canvas(
        pos=(150,10),
        dim=(300,200),
        xdom=(-5,10),
        ydom=(-5,10),
        title="Test plot title")
    canvas.axisx.tick_num = 11
    canvas.axisy.tick_num = 6
    
    # Add plot to app and set GUI
    app.plot = canvas

    app.set_gui([
    Slider(
        app, 'plot_xpos', domain=(150, 300), default=150, pos=(10, 10),
        width=60, height=20),
    Slider(
        app, 'plot_ypos', domain=(10, 200), default=10, pos=(10, 25),
        width=60, height=20),
    Slider(
        app, 'plot_xdim', domain=(80, 450), default=300, pos=(10, 40),
        width=60, height=20),
    Slider(
        app, 'plot_ydim', domain=(80, 390), default=200, pos=(10, 55),
        width=60, height=20),
    Slider(
        app, 'num_xticks', domain=(1, 20), default=6, pos=(10, 85),
        width=60, height=20),
    Slider(
        app, 'num_yticks', domain=(1, 20), default=4, pos=(10, 100),
        width=60, height=20),
    
    Slider(
        app, 'xdom_min', domain=(-5, 6), default=-1, pos=(10, 130),
        width=60, height=20),
    Slider(
        app, 'xdom_max', domain=(-5, 6), default=1, pos=(10, 145),
        width=60, height=20),
    Slider(
        app, 'ydom_min', domain=(-5, 6), default=-1, pos=(10, 175),
        width=60, height=20),
    Slider(
        app, 'ydom_max', domain=(-5, 6), default=1, pos=(10, 190),
        width=60, height=20),
    ])
    
    app.run()

if __name__ == "__main__":
    main()


