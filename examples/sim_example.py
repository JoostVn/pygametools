import pygame
from pygametools.color.color import Color
from pygametools.gui.base import Application
from pygametools.gui.elements import Button, Slider, Label
import numpy as np
from numba import jit, float64, int32, boolean, prange
from math import pi

# DONE / THIS COMMIT

# TO DO / THIS COMMIT

# PRIORITIZED
# TODO: make sure pos is always an integer
# TODO: bot accent slider and accent in group color
# TODO: jit get_neigbours function (used in blur and trail following)
# TODO: add trail detection and following

# UNPRIORITIZED
# Refactor: move bot vars to BotSwarm class, all pos/angle etc. methods to functions
# TODO: why are the trails so dull? fix.
# TODO: debug array: override all drawing to just display one array (for example, debug trails)
# TODO: Move bounce to outside function
# TODO: Add more options for edge handling (nudge + teleport)
# TODO: test performance for parrallel / non parrallel functions


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
            num_bot_groups: int,
            num_bots_per_group: int):
        self.env_dim = env_dim
        self.window_size = window_size

        # Settings
        self.brightness = 0.1
        self.bot_accent = 0.5
        self.blur_factor = 0
        self.decay = 0
        self.bot_speed = 0.2
        self.randomness = 0.1

        # Bot contants
        self.num_bot_groups = num_bot_groups
        self.num_bots_per_group = num_bots_per_group
        self.num_bots = self.num_bot_groups * self.num_bots_per_group

        # Bot data
        self.bot_pos = np.full((self.num_bots, 2), np.divide(self.env_dim, 2))
        self.bot_angles = np.random.uniform(0, 2*pi, size=self.num_bots)
        self.bot_group = np.repeat(np.arange(num_bot_groups), num_bots_per_group)

        # Group data
        self.group_trails = np.zeros((num_bot_groups, *self.env_dim))
        self.group_col = np.vstack([Color.random_vibrant() for i in self.group_idx])

    @property
    def group_idx(self):
        return np.arange(self.num_bot_groups)

    def update(self):
        
        # Randomly adjust bot angles
        self.bot_angles += np.random.uniform(
            low=-self.randomness,
            high=self.randomness,
            size=self.num_bots)

        # Update bot pos
        self.bot_pos += self.bot_speed * np.column_stack([
            np.cos(self.bot_angles),
            np.sin(self.bot_angles)])
        
        # Bounce bots that are out of bounds back (change angle and pos)
        max_x = self.env_dim[0] - 1
        lb_x = self.bot_pos[:,0] < 0
        ub_x = self.bot_pos[:,0] > max_x
        mask_x = ub_x | lb_x
        self.bot_angles[mask_x] = pi - self.bot_angles[mask_x]
        self.bot_pos[lb_x, 0] = - self.bot_pos[lb_x, 0]
        self.bot_pos[ub_x, 0] = 2 * max_x - self.bot_pos[ub_x, 0]

        # Same for y axis
        max_y = self.env_dim[1] - 1
        lb_y = self.bot_pos[:,1] < 0
        ub_y = self.bot_pos[:,1] > max_y
        mask_y = ub_y | lb_y
        self.bot_angles[mask_y] = - self.bot_angles[mask_y]
        self.bot_pos[lb_y, 1] = - self.bot_pos[lb_y, 1]
        self.bot_pos[ub_y, 1] = 2 * max_y - self.bot_pos[ub_y, 1]

        # Set angle back to [0, 2pi]
        self.bot_angles = self.bot_angles % (2 * pi)

        # Update the trails of each group with the new positions of its bot members
        for i in self.group_idx:
            bot_int_pos = self.bot_pos[self.bot_group==i].astype(int).T
            self.group_trails[i, *bot_int_pos] = 1

        # Blur and apply decay to the trails of each group
        for i in self.group_idx:
            self.group_trails[i] = blur_array(self.group_trails[i], self.blur_factor)

        self.group_trails *= (1 - self.decay)

    def draw(self, screen, zoom, pan_offset):
        
        # Initialize color array
        arr_draw_rgb = arr_draw_rgb = np.zeros((*self.env_dim, 3))

        # apply bot color to trails and combine into color array
        for i in self.group_idx:
            trail_col = self.group_col[i] * self.group_trails[i,:,:,np.newaxis]
            arr_draw_rgb += trail_col
        
        arr_draw_rgb = arr_draw_rgb / self.num_bot_groups
        
        # Accent bots positions on color array by making them brighter
        bot_x = tuple(self.bot_pos[:,0].flatten().astype(int))
        bot_y = tuple(self.bot_pos[:,1].flatten().astype(int))
        arr_draw_rgb[bot_x, bot_y, :] += self.bot_accent * (255 - arr_draw_rgb[bot_x, bot_y, :])

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


def main():
    window_size = (200,200)
    simulation = Simulation(
        env_dim=(100, 100),
        window_size=window_size,
        num_bot_groups=4,
        num_bots_per_group=50)
    app = App(window_size, simulation)

    app.set_gui([
        Slider(simulation, 'brightness', domain=(0, 1), default=0.1, pos=(10, 10), width=60, height=20),
        Slider(simulation, 'bot_accent', domain=(0, 1), default=0.2, pos=(10, 20), width=60, height=20),
        Slider(simulation, 'blur_factor', domain=(0, 0.5), default=0.25, pos=(10, 30), width=60, height=20),
        Slider(simulation, 'decay', domain=(0, 0.2), default=0.01, pos=(10, 40), width=60, height=20),
        Slider(simulation, 'bot_speed', domain=(-5, 5), default=2, pos=(10, 50), width=60, height=20),
        Slider(simulation, 'randomness', domain=(0, 1), default=0.1, pos=(10, 60), width=60, height=20),
    ])

    app.run()
    pygame.quit()


if __name__ == '__main__':
    main()