import pygame
from pygametools.color.color import Color
from pygametools.gui.base import Application
from pygametools.gui.elements import Button, Slider, Label
import numpy as np

# TODO: scale arr
# TODO: don't re-make surface each tick
# TODO: understand the draw function: can we adjust where the surface is drawn? (now it's always window filling)


class Simulation:

    def __init__(self, env_dim: tuple[int, int], window_size: tuple[int, int]):
        self.env_dim = env_dim
        self.window_size = window_size
        self.arr = np.zeros((*self.env_dim, 3))
        self.brightness = 0.1

    def update(self):
        self.arr = np.random.uniform(0, 1, size=(*self.env_dim, 3))

    def draw(self, screen):
        arr_rgb = self.arr * self.brightness
        surface = pygame.surfarray.make_surface(arr_rgb)
        pygame.transform.scale(surface, self.window_size, screen)


class App(Application):

    def __init__(self, window_size, simulation):
        super().__init__(window_size, theme_name="default_dark")
        self.simulation = simulation

    def update(self):
        self.simulation.update()

    def draw(self):
        self.simulation.draw(self.screen)


def gui_test():
    window_size = (100,100)
    simulation = Simulation(env_dim=(50, 50), window_size=window_size)
    app = App(window_size, simulation)

    app.set_gui([
        Slider(
            obj=simulation,
            attribute='brightness',
            domain=(0, 255),
            default=50,
            pos=(10, 10),
            width=60,
            height=20)
    ])

    app.run()
    pygame.quit()


if __name__ == '__main__':

    gui_test()