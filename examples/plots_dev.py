
"""
Development testing for plots (plotting 2) module


TODO
    - GUI slides for pos, dim, domain, pad

"""
from pygametools.plots.elements import Canvas
from pygametools.gui.base import Application
import pygame
from pygametools.gui.elements import Button, Slider, Label

class PlotTestApp(Application):

    def __init__(self, window_size):
        super().__init__(window_size)
        self.plots = []

    def add_plot(self, plot):
        self.plots.append(plot)

    def update(self):

        pass
        # Testing dynamic pos
        if False:
            self.plots[0].update_dimensions(pos=self.plots[0].pos + 1)

        # Testing dynamic pad
        if False:
            new_pad = self.plots[0].pad.copy()
            new_pad[0] = new_pad[0] + 2
            new_pad[1] = new_pad[1] + 1
            new_pad[2] = new_pad[2] + 1
            new_pad[3] = new_pad[3] + 1
            self.plots[0].update_dimensions(pad=new_pad)

        # Testing dynamic domain
        if False:
            new_dom = self.plots[0].dom.copy().astype(float)

            new_dom[0,1] = new_dom[0,1] * 1.01
            new_dom[1,1] = new_dom[1,1] * 1.01

            self.plots[0].update_dimensions(dom=new_dom)

    def draw(self):
        for plot in self.plots:
            plot.draw(self.screen)



def main():

    # Create test plot
    plot = Canvas(
        pos=(20,40),
        dim=(350,250),
        xdom=(-5,10),
        ydom=(-10,30),
        title="Plot for testing purposes")

    plot.axisx.set_num_ticks(10)
    plot.axisy.set_num_ticks(6)

    # Create app and gui
    app = PlotTestApp(window_size=(600,400))

    # Add plot and run app
    app.add_plot(plot)
    app.run()
    pygame.quit()


if __name__ == "__main__":
    main()


