
"""
Development testing for plots (plotting 2) module
"""

from pygametools.plots.elements import Canvas
from pygametools.gui.base import Application
import pygame
from pygametools.gui.elements import Button, Slider, Label

class PlotTestApp(Application):

    def __init__(self, window_size):
        super().__init__(window_size)
        self.canvas_list = []
        
        # Slider values
        self._plot_xpos = 0
        self._plot_ypos = 0
        self._plot_xdim = 0
        self._plot_ydim = 0
        
    def add_canvas(self, plot):
        self.canvas_list.append(plot)
        
    def update(self):
        pass

    def draw(self):
        for plot in self.canvas_list:
            plot.draw(self.screen)
        
    # GUI values
    @property
    def plot_xpos(self):
        return self._plot_xpos
    
    @plot_xpos.setter
    def plot_xpos(self, val):  
        self._plot_xpos = val
        old_pos = self.canvas_list[0].metrics.pos
        self.canvas_list[0].metrics.pos = (val, old_pos[1])
        
    @property
    def plot_ypos(self):
        return self._plot_ypos
    
    @plot_ypos.setter
    def plot_ypos(self, val):
        self._plot_ypos = val
        old_pos = self.canvas_list[0].metrics.pos
        self.canvas_list[0].metrics.pos = (old_pos[0], val)
        
    @property
    def plot_xdim(self):
        return self._plot_xdim
    
    @plot_xdim.setter
    def plot_xdim(self, val):
        self._plot_xdim = val
        old_dim = self.canvas_list[0].metrics.dim
        self.canvas_list[0].metrics.dim = (val, old_dim[1])
          
    @property
    def plot_ydim(self):
        return self._plot_ydim
    
    @plot_ydim.setter
    def plot_ydim(self, val):
        self._plot_ydim = val
        old_dim = self.canvas_list[0].metrics.dim
        self.canvas_list[0].metrics.dim = (old_dim[0], val)
        
    

def main():

    # Create test plot
    canvas = Canvas(
        pos=(20,40),
        dim=(350,250),
        xdom=(-5,10),
        ydom=(-10,30),
        title="Plot for testing purposes")

    canvas.axisx.set_num_ticks(11)
    canvas.axisy.set_num_ticks(6)

    # Create app 
    app = PlotTestApp(window_size=(600,400))
    
    # Add plots
    app.add_canvas(canvas)
    
    # Create gui
    app.set_gui([
    Slider(
        app, 'plot_xpos', domain=(0, 200), default=10, pos=(10, 10),
        width=60, height=20),
    Slider(
        app, 'plot_ypos', domain=(0, 200), default=70, pos=(10, 25),
        width=60, height=20),
    Slider(
        app, 'plot_xdim', domain=(80, 500), default=350, pos=(10, 40),
        width=60, height=20),
    Slider(
        app, 'plot_ydim', domain=(80, 500), default=250, pos=(10, 55),
        width=60, height=20),
    ])
    
    app.run()
    pygame.quit()


if __name__ == "__main__":
    main()


