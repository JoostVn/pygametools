import pygame
from pygametools.color.color import Color
from pygametools.gui.base import Application
from pygametools.gui.elements import Button, Slider, Label
import numpy as np
from numba import jit, float64, int32, int64, boolean, prange
from math import pi, cos, sin, ceil


@jit(float64[:,:](float64[:,:], int64, int64, float64), nopython=True)
def get_subarray(arr, i, j, span):
    """
    Return a single subarray of an array, centered at index and with a size given
    by the span parameter. Handles sub arrays that fall completely or partially
    outside the parent array bounds.
    """
    return arr[
        max(0, i-span) : min(arr.shape[0], i+span+1),
        max(0, j-span) : min(arr.shape[1], j+span+1)]


@jit(float64[:,:](float64[:,:], float64), nopython=True, parallel=True)
def blur_array(arr, fact):
    """
    Box blur a complete 2d array by combining each cell value and the mean neighbour value.
    """
    for i in prange(arr.shape[0]):
        for j in prange(arr.shape[1]):
            mean = get_subarray(arr, i, j, 1).sum() / 9
            arr[i,j] = fact * mean + (1-fact) * arr[i,j]
    return arr


@jit(float64(float64[:,:], float64[:], float64, float64, float64, float64),
     nopython=True)
def read_sensor(trail, pos, angle, sensor_reach, sensor_size, sensor_angle):
    """
    Read a single sensor value.

    Determine the (x,y) sensor midpoint based on an agent position, agent
    angle sensor reach, sensor size and sensor angle. Then, sum all
    arr elements around that point in a square with sides of size
    2*sensor_size and return the result.
    """
    true_angle = angle + sensor_angle
    i = int(pos[0] + sensor_reach * cos(true_angle))
    j = int(pos[1] + sensor_reach * sin(true_angle))
    return get_subarray(trail, i, j, sensor_size).sum()


@jit(float64[:](float64[:,:], float64[:,:], float64[:], float64, float64, float64),
     nopython=True, parallel=True)
def read_all_sensors(trail, bot_pos, bot_angles, sensor_reach, sensor_size, sensor_angle):
    """
    Calculate a sensor value for each bot in bot_pos and bot_angles.
    """
    sensor_values = np.zeros(shape=bot_pos.shape[0], dtype=float64)

    for b in prange(bot_pos.shape[0]):
        sensor_values[b] = read_sensor(
            trail, bot_pos[b], bot_angles[b], sensor_reach, sensor_size, sensor_angle)
    
    return sensor_values


@jit(nopython=True)
def deposit_segments(trail, prev_pos, pos):
    """
    Rasterize straight-line motion between consecutive bot positions.

    For each bot, interpolate between its previous position and its current
    position and write all intermediate grid cells into the trail array.
    This prevents gaps when bot speed > 1 grid cell per update.
    """
    x_max, y_max = trail.shape
    num_bots = pos.shape[0]

    for b in range(num_bots):

        # Start/end positions and displacement vector for current bot
        x0, y0 = prev_pos[b]
        x1, y1 = pos[b]
        dx = x1 - x0
        dy = y1 - y0

        # Number of interpolation steps: One step per grid cell crossed along the dominant axis
        num_steps = int(ceil(max(abs(dx), abs(dy))))

        # If the bot did not move enough to cross a cell,  still deposit at the final position
        if num_steps <= 0:
            trail[int(x1), int(y1)] = 1.0
            continue

        # Per-step (continuous) increment
        sx = dx / num_steps
        sy = dy / num_steps

        # Walk the line segment in small increments and write each visited grid cell into the trail
        x = x0
        y = y0
        for _ in range(num_steps + 1):
            trail[int(x), int(y)] = 1.0
            x += sx
            y += sy


class Simulation:

    def __init__(
            self,
            env_dim: tuple[int, int],
            window_size: tuple[int, int]):
        self.env_dim = env_dim
        self.window_size = window_size

        # Settings (constant)
        self.sensor_distance = 4
        self.sensor_size = 1
        self.sensor_angles = np.array([-0.2*pi, 0, 0.2*pi])

        # Settings (variable based on slider)
        self.brightness = 0.1
        self.bot_accent = 0.5
        self.blur_factor = 0
        self.decay = 0
        self.bot_speed = 0.2
        self.randomness = 0.1
        self.angle_nudge = 0.2
        self.avoidance = 0.5
        self.mouse_range = 100
        self.mouse_strenght = 2

        # Num bots and num bot groups
        self._num_bots = 1
        self._num_bot_groups = 1
        
        # Bot/group variable based on num bots/groups
        self.bot_membership = np.zeros((0,))
        self.bot_pos = np.zeros((0, 2))
        self.bot_prev_pos = np.zeros((0, 2))
        self.bot_angles = np.zeros((0,))
        self.group_trails = np.zeros((0, *self.env_dim))
        self.group_col = np.zeros((0, 3))
        self.update_bot_counts()

        # Mouse interaction
        self._mouse_pos = np.zeros(2)
        self.mouse_hold_right = False
        self.mouse_hold_left = False

    # Properties set by UI controls
    @property
    def num_bots(self):
        return self._num_bots
    
    @num_bots.setter
    def num_bots(self, val):
        self._num_bots = int(round(val, 0))
        self.update_bot_counts()

    @property
    def num_bot_groups(self):
        return self._num_bot_groups
    
    @num_bot_groups.setter
    def num_bot_groups(self, val):
        self._num_bot_groups = int(round(val, 0))
        self.update_bot_counts()

    # Derived properties
    @property
    def group_idx(self):
        return np.arange(self.num_bot_groups)
    
    @property
    def min_num_bots_per_group(self):
        return int(self._num_bots / self._num_bot_groups)

    # Other properties
    @property
    def mouse_pos(self):
        return self._mouse_pos
    
    @mouse_pos.setter
    def mouse_pos(self, val):
        """
        Mouse position in the simulation as coordinates on the bot array.
        """
        self._mouse_pos = val * np.divide(self.env_dim, self.window_size)
     
    # Methods called as a result of changes in properties
    def generate_colors(self):
        """
        Called from dedicated button in gui.
        """
        self.group_col = np.vstack([Color.random_vibrant() for i in self.group_idx])
        print(self.group_col)

    def reset_pos(self):
        """
        Called from dedicated button in gui.
        """
        self.bot_pos = np.full((self.num_bots, 2), np.divide(self.env_dim, 2))

    def reset_all(self):
        """
        Called from dedicated button in gui.
        """
        self.reset_pos()
        self.group_trails[:] = 0

    def update_bot_counts(self):
        """
        Called when the number of bots/groups are updateted to re-determine memberships.
        """
        # Update bot membership and deal with uneven bot group counts
        bot_membership = np.repeat(self.group_idx, self.min_num_bots_per_group)
        num_bots_too_little = self._num_bots - bot_membership.shape[0]
        extra_bots = self.group_idx[:num_bots_too_little]
        self.bot_membership = np.hstack([bot_membership, extra_bots])

        # Determine deltas
        delta_num_groups = self._num_bot_groups - self.group_trails.shape[0]
        delta_num_bots = self._num_bots - self.bot_pos.shape[0]

        # Update pos and prev pos
        if delta_num_bots > 0:
            new_pos = np.random.uniform((0,0), self.env_dim, (delta_num_bots, 2))
            self.bot_pos = np.vstack((self.bot_pos, new_pos))

            new_prev = new_pos.copy()
            self.bot_prev_pos = np.vstack((self.bot_prev_pos, new_prev))
        else:
            self.bot_pos = self.bot_pos[:self._num_bots]
            self.bot_prev_pos = self.bot_prev_pos[:self._num_bots]

        # Update angles
        if delta_num_bots > 0:
            new_angles = np.random.uniform(0, 2*pi, size=delta_num_bots)
            self.bot_angles = np.hstack((self.bot_angles, new_angles))
        else:
            self.bot_angles = self.bot_angles[:self._num_bots]

        # Update trails
        if delta_num_groups > 0:
            new_trails = np.zeros((delta_num_groups, *self.group_trails.shape[1:]))
            self.group_trails = np.vstack((self.group_trails, new_trails))
        else:
            self.group_trails = self.group_trails[:self._num_bot_groups]

        # Update colors
        if delta_num_groups > 0:
            new_colors = np.vstack([Color.random_vibrant() for i in range(delta_num_groups)])
            self.group_col = np.vstack((self.group_col, new_colors))
        else:
            self.group_col = self.group_col[:self._num_bot_groups]

    # Simulation methods
    def update(self, enable_mouse_interation: bool=False):

        # Save previous bot positions
        self.bot_prev_pos[:] = self.bot_pos
        
        # Read bot sensors and determine direction preference
        for g in self.group_idx:
            group_mask = self.bot_membership==g

            group_bot_pos = self.bot_pos[group_mask]
            group_bot_angles = self.bot_angles[group_mask]
            group_trail = self.group_trails[g]
            other_trail = self.group_trails[self.group_idx[self.group_idx!=g]].mean(axis=0)

            group_sensor_values = np.zeros((group_mask.sum(), len(self.sensor_angles)))

            for a, sensor_angle in enumerate(self.sensor_angles):
                sensor_group = read_all_sensors(
                    group_trail, group_bot_pos, group_bot_angles, self.sensor_distance, 
                    self.sensor_size, sensor_angle)
                sensor_other = read_all_sensors(
                    other_trail, group_bot_pos, group_bot_angles, self.sensor_distance, 
                    self.sensor_size, sensor_angle)
                
                if self._num_bot_groups > 1: 
                    group_sensor_values[:,a] = (1-self.avoidance) * sensor_group - self.avoidance * sensor_other
                else:
                    group_sensor_values[:,a] = sensor_group
 
            # Nudge angle to highest sensor value
            group_angle_preference = self.sensor_angles[group_sensor_values.argmax(axis=1)]
            self.bot_angles[group_mask] += self.angle_nudge * group_angle_preference 


        # Interaction with mouse (pull/push bots from the current mouse pos)
        if enable_mouse_interation:
    
            # Calculate bot-mouse distance and a linear distance factor (1 = closest)
            bot_mouse_vec = np.reshape(self.mouse_pos, (1,2)) - self.bot_pos
            bot_mouse_dis = np.linalg.norm(bot_mouse_vec, axis=1).reshape((-1,1))
            dist_factor = 1 - np.clip(bot_mouse_dis, 0, self.mouse_range) / self.mouse_range

            # Calculate the vector and angle from each bot to the mouse
            bot_mouse_vec_unit = bot_mouse_vec / bot_mouse_dis
            bot_mouse_angle = np.atan2(bot_mouse_vec_unit[:, 1], bot_mouse_vec_unit[:, 0])

            # Compute the smallest delta between current bot angles and the bot-mouse angles
            bot_mouse_angle_delta = (bot_mouse_angle - self.bot_angles + pi) % (2 * pi) - pi
    
            # Adjust positions and nudge angles
            if self.mouse_hold_left:
                self.bot_pos = self.bot_pos + dist_factor * self.mouse_strenght * bot_mouse_vec_unit
                self.bot_angles = self.bot_angles + 0.1 * dist_factor.flatten() * bot_mouse_angle_delta

            if self.mouse_hold_right:
                self.bot_pos = self.bot_pos - dist_factor * self.mouse_strenght * bot_mouse_vec_unit
                self.bot_angles = self.bot_angles - 0.1 * dist_factor.flatten() * bot_mouse_angle_delta

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
        # Also deposit trails for interpolated cells between prev pos and current pos 
        for g in self.group_idx:
            mask = self.bot_membership == g
            deposit_segments(self.group_trails[g], self.bot_prev_pos[mask], self.bot_pos[mask])

        # Blur and apply decay to the trails of each group
        for g in self.group_idx:
            self.group_trails[g] = blur_array(self.group_trails[g], self.blur_factor)

        self.group_trails *= (1 - self.decay)

    def draw(self, screen, zoom, pan_offset):
        
        # Initialize color array
        arr_draw_rgb = arr_draw_rgb = np.zeros((*self.env_dim, 3))

        # apply bot color to trails and combine their average into color array
        for i in self.group_idx:
            trail_col = self.group_col[i] * self.group_trails[i,:,:,np.newaxis]
            arr_draw_rgb += trail_col
        
        arr_draw_rgb = np.clip(arr_draw_rgb, 0, 255)
 
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
        self.simulation.update(
            enable_mouse_interation=(not self.container.is_active))

        # Calucate mouse pos adjusted by zoom and pan offset and pass to simulation
        self.simulation.mouse_pos = self.mouse_pos_draw

        if pygame.BUTTON_RIGHT in self.key_events['hold']:
            self.simulation.mouse_hold_right = True
        elif pygame.BUTTON_LEFT in self.key_events['hold']:
            self.simulation.mouse_hold_left = True
        else:
            self.simulation.mouse_hold_right = False
            self.simulation.mouse_hold_left = False

    def draw(self):
        self.simulation.draw(self.screen, self.zoom, self.pan_offset)


def main():

    
    # theme = 'default_light'
    theme = 'default_dark'
    ui_width = 60

    window_size = (500,500)
    simulation = Simulation(
        env_dim=(250, 250),
        window_size=window_size)
    simulation.reset_pos()

    app = App(window_size, simulation)

    gui_list = [
        Slider(
            simulation,
            'brightness',
            domain=(0, 1),
            default=0.5,
            pos=(10, 10),
            width=ui_width,
            height=20,
            theme_name=theme),
        Slider(
            simulation,
            'bot_accent',
            domain=(0, 1),
            default=0.2,
            pos=(10, 20),
            width=ui_width,
            height=20,
            theme_name=theme),


        Slider(
            simulation,
            'blur_factor',
            domain=(0, 0.5),
            default=0.25,
            pos=(10, 40),
            width=ui_width,
            height=20,
            theme_name=theme),
        Slider(
            simulation,
            'decay',
            domain=(0, 0.4),
            default=0.2,
            pos=(10, 50),
            width=ui_width,
            height=20,
            theme_name=theme),


        Slider(
            simulation,
            'num_bots',
            domain=(1, 10000),
            default=10,
            pos=(10, 70),
            width=ui_width,
            height=20,
            theme_name=theme),
        Slider(
            simulation,
            'num_bot_groups',
            domain=(1, 8),
            default=3,
            pos=(10, 80),
            width=ui_width,
            height=20,
            theme_name=theme),

        



        Slider(
            simulation,
            'bot_speed',
            domain=(0, 4),
            default=3,
            pos=(10, 100),
            width=ui_width,
            height=20,
            theme_name=theme),
        Slider(
            simulation,
            'randomness',
            domain=(0, 1),
            default=0.1,
            pos=(10, 110),
            width=ui_width,
            height=20,
            theme_name=theme),
        Slider(
            simulation,
            'angle_nudge',
            domain=(0, 1),
            default=0.9,
            pos=(10, 120),
            width=ui_width,
            height=20,
            theme_name=theme),
        Slider(
            simulation,
            'avoidance',
            domain=(0, 1),
            default=0.75,
            pos=(10, 130),
            width=ui_width,
            height=20,
            theme_name=theme),

        Slider(
            simulation,
            'mouse_range',
            domain=(10, 200),
            default=100,
            pos=(10, 150),
            width=ui_width,
            height=20,
            theme_name=theme),
        Slider(
            simulation,
            'mouse_strenght',
            domain=(0, 5),
            default=1,
            pos=(10, 160),
            width=ui_width,
            height=20,
            theme_name=theme),
        
        Button(
            text='colors',
            func=simulation.generate_colors,
            pos=(window_size[0]-70, 10),
            width=ui_width,
            height=20,
            theme_name=theme),
        Button(
            text='reset pos',
            func=simulation.reset_pos,
            pos=(window_size[0]-70, 40),
            width=ui_width,
            height=20,
            theme_name=theme),
        Button(
            text='reset all',
            func=simulation.reset_all,
            pos=(window_size[0]-70, 70),
            width=ui_width,
            height=20,
            theme_name=theme)
    ]

    app.set_gui(gui_list)

    app.run()
    pygame.quit()


if __name__ == '__main__':
    main()