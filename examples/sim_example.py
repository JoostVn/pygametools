import pygame
from pygametools.color.color import Color
from pygametools.gui.base import Application
from pygametools.gui.elements import Button, Slider, Label
import numpy as np
from numba import jit, float64, int32, boolean, prange
from math import pi



@jit(float64[:,:](float64[:,:], float64), nopython=True, parallel=True)
def blur_array(arr, fact):
    """
    Blur a 2d array by combining the value in each cell with the mean value of the
    cells aruond it.
    """
    for i in prange(arr.shape[0]):
        for j in prange(arr.shape[1]):
            mean = arr[i-1:i+2,j-1:j+2].sum() / 9
            arr[i,j] = max(0, (1-fact) * arr[i,j] + fact * mean)
    return arr


class Simulation:

    def __init__(
            self,
            env_dim: tuple[int, int],
            window_size: tuple[int, int],
            num_agent_groups: int,
            num_agents_per_group: int):
        self.env_dim = env_dim
        self.window_size = window_size

        self.arr = np.zeros((*self.env_dim, 3))

        # Settings
        self.brightness = 0.1
        self.blur_factor = 0
        self.decay = 0

        # Agents
        self.agent_pos = np.random.randint(
            *env_dim, size=(num_agent_groups, num_agents_per_group, 2))
        self.agent_angle = np.random.uniform(
            0, 2*pi, (num_agent_groups, num_agents_per_group))
        self.agent_trail = np.zeros(
            (num_agent_groups, *self.env_dim))
        self.agent_col = np.array([
            Color.random_dull() for i in range(num_agent_groups)])

    def blur_test(self):
        """
        Blur the R, G, and B values of self.arr individually
        """
        # TODO: move blur to update
        for c in range(3):
            self.arr[:,:,c] = blur_array(self.arr[:,:,c], self.blur_factor)
        self.arr = self.arr * (1-self.decay)

    def update(self):
        
        # Update agent angle
        # TODO

        # Update agent pos
        # TODO

        # Update agent trails (new pos, blur, decay)
        # TODO

   

    def draw(self, screen, zoom, pan_offset):
        


        # apply agent color to trails and combine
        # TODO

        arr_draw_rgb = self.arr

        # 
        

        # Place agents on arr
        # TODO

         

        # Draw zoomed/panned rgb arr
        arr_draw_rgb = arr_draw_rgb * self.brightness
        arr_surface = pygame.surfarray.make_surface(arr_draw_rgb)
        zoomed_window_size = tuple(np.multiply(zoom, self.window_size).astype(int))
        arr_surface = pygame.transform.scale(arr_surface, zoomed_window_size)
        rect = arr_surface.get_rect()
        rect = rect.move(pan_offset)
        screen.blit(arr_surface, rect)


class App(Application):

    def __init__(self, window_size, simulation):
        super().__init__(window_size, theme_name="default_dark")
        self.simulation = simulation

    def update(self):
        self.simulation.update()

    def draw(self):
        self.simulation.draw(self.screen, self.zoom, self.pan_offset)


def gui_test():
    window_size = (150,150)
    simulation = Simulation(
        env_dim=(50, 50),
        window_size=window_size,
        num_agent_groups=2,
        num_agents_per_group=10)
    app = App(window_size, simulation)

    app.set_gui([
        Slider(
            obj=simulation,
            attribute='brightness',
            domain=(0, 255),
            default=50,
            pos=(10, 10),
            width=60,
            height=20),
        Slider(
            obj=simulation,
            attribute='blur_factor',
            domain=(0, 1),
            default=0,
            pos=(10, 20),
            width=60,
            height=20),
        Slider(
            obj=simulation,
            attribute='decay',
            domain=(0, 1),
            default=0,
            pos=(10, 30),
            width=60,
            height=20)
    ])

    app.run()
    pygame.quit()


if __name__ == '__main__':

    gui_test()