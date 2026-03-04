
"""
Development testing for plots (plotting 2) module


TODO:
 - Sliders for other metrics such as axes padding
 - checkboxes for plot types (all in the same plot)
 - 

"""

from pygametools.plots.elements import Canvas
from pygametools.gui.base import Application
import pygame
from pygametools.gui.elements import Button, Slider, Label

class PlotTestApp(Application):

    def __init__(self, window_size):
        super().__init__(window_size)
        self.plot: Canvas = []
        
        # Slider values
        self._plot_xpos = 0
        self._plot_ypos = 0
        self._plot_xdim = 0
        self._plot_ydim = 0
        self._num_yticks = 0
        self._num_xticks = 0
        
    def set_canvas(self, plot):
        self.plot = plot
        
    def update(self):
        pass

    def draw(self):
        self.plot.draw(self.screen)
        
    # GUI values
    @property
    def plot_xpos(self):
        return self._plot_xpos
    
    @plot_xpos.setter
    def plot_xpos(self, val):  
        self._plot_xpos = val
        old_pos = self.plot.metrics.pos
        self.plot.metrics.pos = (val, old_pos[1])
        
    @property
    def plot_ypos(self):
        return self._plot_ypos
    
    @plot_ypos.setter
    def plot_ypos(self, val):
        self._plot_ypos = val
        old_pos = self.plot.metrics.pos
        self.plot.metrics.pos = (old_pos[0], val)
        
    @property
    def plot_xdim(self):
        return self._plot_xdim
    
    @plot_xdim.setter
    def plot_xdim(self, val):
        self._plot_xdim = val
        old_dim = self.plot.metrics.dim
        self.plot.metrics.dim = (val, old_dim[1])
          
    @property
    def plot_ydim(self):
        return self._plot_ydim
    
    @plot_ydim.setter
    def plot_ydim(self, val):
        self._plot_ydim = val
        old_dim = self.plot.metrics.dim
        self.plot.metrics.dim = (old_dim[0], val)
        
    @property
    def num_xticks(self):
        return self._num_xticks
    
    @num_xticks.setter
    def num_xticks(self, val):
        self._num_xticks = int(val)
        self.plot.axisx.set_num_ticks(self._num_xticks)
    
    @property
    def num_yticks(self):
        return self._num_yticks
    
    @num_yticks.setter
    def num_yticks(self, val):
        self._num_yticks = int(val)
        self.plot.axisy.set_num_ticks(self._num_yticks)
    

def main():

    # Create test plot
    canvas = Canvas(
        pos=(150,10),
        dim=(300,200),
        xdom=(-5,10),
        ydom=(-10,30),
        title="Test plot title")

    canvas.axisx.set_num_ticks(11)
    canvas.axisy.set_num_ticks(6)

    # Create app 
    app = PlotTestApp(window_size=(600,400))
    
    # Add plots
    app.set_canvas(canvas)
    
    # Create gui
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
        app, 'num_xticks', domain=(1, 20), default=6, pos=(10, 70),
        width=60, height=20),
    Slider(
        app, 'num_yticks', domain=(1, 20), default=4, pos=(10, 85),
        width=60, height=20),
    ])
    
    app.run()
    pygame.quit()


if __name__ == "__main__":
    main()


