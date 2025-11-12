import pygame
from pygametools.color.color import Color
from pygametools.gui.base import Application
from pygametools.gui.elements import Button, Slider, Label
import numpy as np
from numba import jit, float64, int32, boolean, prange
from math import pi



# TODO: bounce agents on the border
# TODO: agent membership in arrays or with membership arr (note: maybe membership arr is easier to change?)
# TODO: jist get_neigbours function (used in blur and trail following)
# TODO: why are the trails so dull? fix.
# TODO: debug array: override all drawing to just display one array (for example, debug trails)


@jit(float64[:,:](float64[:,:], float64), nopython=True, parallel=True)
def blur_array(arr, fact):
    """
    Blur a 2d array by combining the value in each cell with the mean value of the
    cells around it.
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

        # Settings
        self.brightness = 0.1
        self.blur_factor = 0
        self.decay = 0
        self.agent_speed = 0.2
        self.randomness = 0.1

        # Agents
        self.num_agent_groups = num_agent_groups
        self.num_agents_per_group = num_agents_per_group

        self.agent_pos = np.full((
            num_agent_groups, num_agents_per_group, 2), np.divide(self.env_dim, 2))
        self.agent_angles = np.random.uniform(
            0*pi, 2*pi, (num_agent_groups, num_agents_per_group))
        self.agent_trails = np.zeros(
            (num_agent_groups, *self.env_dim))
        
        self.agent_col = Color.random_different(num_agent_groups)

    @property
    def group_idx(self):
        return np.arange(self.num_agent_groups)

    def update(self):
        
        # Update agent angles with some randomness
        self.agent_angles = self.agent_angles + np.random.uniform(
            low=-self.randomness,
            high=self.randomness,
            size=(self.num_agent_groups, self.num_agents_per_group))

        # Update agent pos
        self.agent_pos[:,:,0] += self.agent_speed * np.cos(self.agent_angles)
        self.agent_pos[:,:,1] += self.agent_speed * np.sin(self.agent_angles)

        # Bounce agents that are out of bounds back (change angle and pos)
        lb_x = self.agent_pos[:,:,0] < 0
        ub_x = self.agent_pos[:,:,0] > self.env_dim[0] - 1
        mask_x = ub_x | lb_x
        self.agent_angles[mask_x] = pi - self.agent_angles[mask_x]
        self.agent_pos[lb_x, 0] = - self.agent_pos[lb_x, 0]
        self.agent_pos[ub_x, 0] = 2 * self.env_dim[0] - 2 - self.agent_pos[ub_x, 0]

        # Same for y axis
        lb_y = self.agent_pos[:,:,1] < 0
        ub_y = self.agent_pos[:,:,1] > self.env_dim[1] - 1
        mask_y = ub_y | lb_y
        self.agent_angles[mask_y] = - self.agent_angles[mask_y]
        self.agent_pos[lb_y, 1] = - self.agent_pos[lb_y, 1]
        self.agent_pos[ub_y, 1] = 2 * self.env_dim[1] - 2 - self.agent_pos[ub_y, 1]

        # Set angle back to [0, 2pi]
        self.agent_angles = self.agent_angles % (2 * pi)

        # Add new positions to agent trails
        for i in self.group_idx:
            agent_int_pos = tuple(self.agent_pos[i].astype(int).T)
            self.agent_trails[i, *agent_int_pos] = 1

        # Blur and apply decay to agent trails
        for i in self.group_idx:
            self.agent_trails[i] = blur_array(self.agent_trails[i], self.blur_factor)

        self.agent_trails = self.agent_trails * (1 - self.decay)

    def draw(self, screen, zoom, pan_offset):
        
        # Initialize color array
        arr_draw_rgb = arr_draw_rgb = np.zeros((*self.env_dim, 3))

        # apply agent color to trails and combine into color array
        for i in self.group_idx:
            trail_col = self.agent_col[i] * self.agent_trails[i,:,:,np.newaxis]
            arr_draw_rgb += trail_col
        
        arr_draw_rgb = arr_draw_rgb / self.num_agent_groups
        
        # Place agents on color array
        agent_x = tuple(self.agent_pos[:,:,0].flatten().astype(int))
        agent_y = tuple(self.agent_pos[:,:,1].flatten().astype(int))
        arr_draw_rgb[agent_x, agent_y, :] = 210

        # Adjust brightness and draw zoomed/panned color array
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
    window_size = (600,600)
    simulation = Simulation(
        env_dim=(300, 300),
        window_size=window_size,
        num_agent_groups=4,
        num_agents_per_group=50)
    app = App(window_size, simulation)

    app.set_gui([
        Slider(
            obj=simulation,
            attribute='brightness',
            domain=(0, 1),
            default=1,
            pos=(10, 10),
            width=60,
            height=20),
        Slider(
            obj=simulation,
            attribute='blur_factor',
            domain=(0, 0.5),
            default=0.25,
            pos=(10, 20),
            width=60,
            height=20),
        Slider(
            obj=simulation,
            attribute='decay',
            domain=(0, 0.2),
            default=0.01,
            pos=(10, 30),
            width=60,
            height=20),
        Slider(
            obj=simulation,
            attribute='agent_speed',
            domain=(-5, 5),
            default=2,
            pos=(10, 40),
            width=60,
            height=20),
        Slider(
            obj=simulation,
            attribute='randomness',
            domain=(0, 1),
            default=0.1,
            pos=(10, 50),
            width=60,
            height=20),
    ])

    app.run()
    pygame.quit()


if __name__ == '__main__':

    gui_test()