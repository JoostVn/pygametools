import pygame
from pygametools.color.color import Color
from pygametools.gui.base import Application
from pygametools.gui.elements import Button, Slider, Label
import numpy as np

class Environment:

    def __init__(self, dim):
        self.dim = dim
        self.arr = np.random.uniform(0, 1, size=dim)
    


class Simulation:

    def __init__(self, environment: Environment):
        self.environment = environment

    def update(self):
        
        self.environment.arr = np.random.uniform(0, 1, size=self.environment.dim)

    def draw(self, surface):
        pygame.surfarray.blit_array(surface, self.environment.arr) 


class App(Application):

    def __init__(self, window_size, simulation):
        super().__init__(window_size, theme_name="default_dark")

        self.simulation = simulation

        # Attributes for test object
        self.square_x = 200
        self.square_y = 50
        self.square_size = 50

    def update(self):
        pass
        # print(self.pan_offset)

    def draw(self):


        draw_x = self.square_x + self.pan_offset[0]
        draw_y = self.square_y + self.pan_offset[1]

        pygame.draw.rect(
            self.screen,
            Color.GREY2,
            (draw_x, draw_y, self.square_size, self.square_size))
        
        self.simulation.draw(self.screen)



def gui_test():

    environment = Environment(dim=(200, 300))
    simulation = Simulation(environment)

    app = App((400,400), simulation)

    app.set_gui([
        Slider(
            obj=app,
            attribute='square_size',
            domain=(10, 100),
            default=10,
            pos=(10, 10),
            width=60,
            height=20
        )
    ])

    app.run()
    pygame.quit()


if __name__ == '__main__':

    gui_test()