
"""
Development testing for plots (plotting 2) module

TODO:
 - checkboxes for plot types (all in the same plot)
"""

from typing import Callable
import numpy as np
from pygametools.color.color import Color
from pygametools.plots.elements import Canvas
from pygametools.gui.base import Application
import pygame
from pygametools.gui.elements import Button, CheckBox, Slider, Label, TextBox
from pygametools.plots.plot_types import PlotType, ScatterPlot, LinePlot

class PlotTestApp(Application):

    def __init__(self, window_size):
        super().__init__(window_size)
        self.canvas: Canvas = None  # type: ignore[assignment]
        
        self.update_funcs = []
        self.enable_funcs = []
        
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
        
        # Checkbox values
        self._enable_scatterplot = False
        
    def add_plot_funcs(self, update_func: Callable):
        self.update_funcs.append(update_func)
        
    def update(self):
        for func in self.update_funcs:
            func()

    def draw(self):
        self.canvas.draw(self.screen)
        
    # GUI values
    @property
    def plot_xpos(self):
        return self._plot_xpos
    
    @plot_xpos.setter
    def plot_xpos(self, val: int | float):
        self._plot_xpos = int(val)
        self.canvas.pos = (self._plot_xpos, self.canvas.pos[1])

    @property
    def plot_ypos(self):
        return self._plot_ypos

    @plot_ypos.setter
    def plot_ypos(self, val: int | float):
        self._plot_ypos = int(val)
        self.canvas.pos = (self.canvas.pos[0], self._plot_ypos)

    @property
    def plot_xdim(self):
        return self._plot_xdim

    @plot_xdim.setter
    def plot_xdim(self, val: int | float):
        self._plot_xdim = int(val)
        self.canvas.dim = (self._plot_xdim, self.canvas.dim[1])

    @property
    def plot_ydim(self):
        return self._plot_ydim

    @plot_ydim.setter
    def plot_ydim(self, val: int | float):
        self._plot_ydim = int(val)
        self.canvas.dim = (self.canvas.dim[0], self._plot_ydim)
        
    @property
    def num_xticks(self):
        return self._num_xticks
    
    @num_xticks.setter
    def num_xticks(self, val: int | float):
        self._num_xticks = int(val)
        self.canvas.axisx.tick_num = self._num_xticks
    
    @property
    def num_yticks(self):
        return self._num_yticks
    
    @num_yticks.setter
    def num_yticks(self, val):
        self._num_yticks = int(val)
        self.canvas.axisy.tick_num = self._num_yticks

    @property
    def xdom_min(self):
        return self._xdom_min

    @xdom_min.setter
    def xdom_min(self, val: float):
        self._xdom_min = -(10 ** val)
        self.canvas.xdom = (self._xdom_min, self.canvas.xdom[1])

    @property
    def xdom_max(self):
        return self._xdom_max

    @xdom_max.setter
    def xdom_max(self, val: float):
        self._xdom_max = 10 ** val
        self.canvas.xdom = (self.canvas.xdom[0], self._xdom_max)

    @property
    def ydom_min(self):
        return self._ydom_min

    @ydom_min.setter
    def ydom_min(self, val: float):
        self._ydom_min = -(10 ** val)
        self.canvas.ydom = (self._ydom_min, self.canvas.ydom[1])

    @property
    def ydom_max(self):
        return self._ydom_max

    @ydom_max.setter
    def ydom_max(self, val: float):
        self._ydom_max = 10 ** val
        self.canvas.ydom = (self.canvas.ydom[0], self._ydom_max)
    

def main():

    # Create app first so that pygame.init() is called early
    app = PlotTestApp(window_size=(600,400))

    # Create test canvas
    canvas = Canvas(
        pos=(150,10),
        dim=(300,200),
        xdom=(-5,10),
        ydom=(-5,10),
        title="Test plot title")
    canvas.axisx.tick_num = 11
    canvas.axisy.tick_num = 6
    
    # Create plots to add to canvas
    scatterplot = ScatterPlot(Color.BLUE2, 'scatter_test', radius=1, alpha=0.5)

    def update_scatterplot():
        scatterplot.add_data(np.random.normal(0, 1, 2))

    app.add_plot_funcs(update_scatterplot)
    canvas.add_plot(scatterplot)

    lineplot = LinePlot(Color.RED3, 'random_walk')
    _walk_x = [0.0]
    _walk_y = [0.0]

    def update_lineplot():
        _walk_x.append(_walk_x[-1] + 0.01)
        _walk_y.append(_walk_y[-1] + np.random.choice([-0.1, 0.1]))
        lineplot.add_data((_walk_x[-1], _walk_y[-1]))

    app.add_plot_funcs(update_lineplot)
    canvas.add_plot(lineplot)
    
    # Add canvas to app and set GUI
    app.canvas = canvas

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
        app, 'plot_ydim', domain=(80, 320), default=200, pos=(10, 55),
        width=60, height=20),
    Slider(
        app, 'num_xticks', domain=(1, 20), default=6, pos=(10, 85),
        width=60, height=20),
    Slider(
        app, 'num_yticks', domain=(1, 20), default=4, pos=(10, 100),
        width=60, height=20),
    
    Slider(
        app, 'xdom_min', domain=(-5, 6), default=-0.3, pos=(10, 130),
        width=60, height=20),
    Slider(
        app, 'xdom_max', domain=(-5, 6), default=0.3, pos=(10, 145),
        width=60, height=20),
    Slider(
        app, 'ydom_min', domain=(-5, 6), default=-0.3, pos=(10, 175),
        width=60, height=20),
    Slider(
        app, 'ydom_max', domain=(-5, 6), default=0.3, pos=(10, 190),
        width=60, height=20),
    
    Label('ScatterPlot', pos=(10,335), width=80, height=18, hcenter=True, vcenter=True),
    CheckBox(scatterplot, 'enabled', default=False, pos=(10, 360)),
    
    Label('LinePlot', pos=(100,335), width=80, height=18, hcenter=True, vcenter=True),
    CheckBox(lineplot, 'enabled', default=False, pos=(100, 360))
    
    
    ])
    
    app.run()

if __name__ == "__main__":
    main()


