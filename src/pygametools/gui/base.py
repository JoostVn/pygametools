import pygame
import numpy as np
import time
from abc import ABC, abstractmethod
from .file_manager import load_theme
import sys
# import pkg_resources
from importlib.resources import files
from enum import Enum


class State(Enum):
    PASSIVE = 0     # No mouse hoover an element is not active
    HOOVER = 1      # Element is nog active but mouse is hoovering over it
    TRIGGERED = 2   # Element is clicked
    ACTIVE = 3      # Element is in prolonged active state
    

class Ticker:

    def __init__(self, start_time, tick_len):
        self.start_time = start_time
        self.tick_start = start_time
        self.tick_len = tick_len
        self.i = 0
        self.hist = np.zeros(20)

    def next_tick(self):
        """
        Records the used computational time of tick. Then pauses the programm
        until the time to next tick has elapsed.
        """
        t = time.time() - self.tick_start
        time.sleep(max(0, self.tick_len - t))
        self.i += 1
        self.tick_start = time.time()
        self.update_stats(t)

    def update_stats(self, t):
        """
        Record the last 20 tick durations.
        """
        self.hist = np.roll(self.hist, 1)
        self.hist[0] = t / self.tick_len

    def get_stats(self):
        """
        Returns all current stats values as a list of printeable strings
        """
        t_min = self.hist.min().round(2)
        t_max = self.hist.max().round(2)
        t_avg = self.hist.mean().round(2)
        stats_list = []
        tick_str = 'load min/max/avg: '
        tick_str += str(t_min if t_min < 1 else '>1,0').ljust(4) + '/'
        tick_str += str(t_max if t_max < 1 else '>1.0').ljust(4) + '/'
        tick_str += str(t_avg if t_avg < 1 else '>1.0').ljust(4)
        stats_list.append(tick_str)
        return stats_list





class Application(ABC):

    # TODO: explanation of drawing with pan_offset and zoom
    # TODO: ticker stats font

    def __init__(
            self, window_size, tick_len=1/30, name='Application', theme_name='default'):
        """
        Handles the main Pygame window, events, and ticks.

        Parameters
        ----------
        tick_len : float
            Duration in seconds for a programm tick.
        window_size : array, tuple, list
            Dimensions (x,y) of Pygame window.

        """
        # Pygame init and window settings
        pygame.init()
        pygame.display.set_caption(name)



        ## NEW
        icon_path = files("pygametools.gui.icons").joinpath(f"icon.png")
        with icon_path.open() as file:
            pygame.display.set_icon(pygame.image.load(file))
        ## NEW


        # icon_path = pkg_resources.resource_filename(
        #     'gui', 'resources/icon.png')
        # with open(icon_path, 'r') as file:
        #     pygame.display.set_icon(pygame.image.load(file))





        # Class main settings
        self.ticker = Ticker(start_time=time.time(), tick_len=tick_len)
        self.window_size = np.array(window_size)
        self.container = Container()

        # Loading theme, background color and font
        self.theme = load_theme(theme_name)
        self.set_theme()
        self.font_debug = pygame.font.SysFont('monospace', 12)

        # Creating key events dict
        self.key_events = {'up': [],'down': [],'hold': []}

        # Zooming and panning
        self.pan_offset = np.array([0,0])
        self.zoom = 1

        # Defining screen
        self.screen = pygame.display.set_mode(self.window_size)

    def set_theme(self):
        """
        Reloads all theme colors. Used at init or called externally when
        self.theme has been changed.
        """
        self.background_color = self.theme['background']

    def _update_key_events(self, events):
        """
        Reads all up, down, and hold key events. The up and down events are
        based on the given list of raw Pygame events. The hold events are
        triggered at 'down' and released at 'up'. Key events are added to the
        list based on their Pygame constant. Examples:
            - pygame.K_a,
            - pygame.BUTTON_LEFT
            - pygame.BUTTON_MIDDLE
            - pygame.BUTTON_RIGHT
            - pygame.BUTTON_WHEELUP
            - pygame.BUTTON_WHEELDOWN

        Parameters
        ----------
        events : list
            list of raw Pygame events; [e for e in Pygame.event.get()].

        """
        self.key_events['up'] = []
        self.key_events['down'] = []
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.key_events['down'].append(event.button)
                self.key_events['hold'].append(event.button)
            elif event.type == pygame.KEYDOWN:
                self.key_events['down'].append(event.key)
                self.key_events['hold'].append(event.key)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.key_events['up'].append(event.button)
                self.key_events['hold'].remove(event.button)
            elif event.type == pygame.KEYUP:
                self.key_events['up'].append(event.key)
                self.key_events['hold'].remove(event.key)

    def run(self):
        """
        Pygame main loop. Handles events, updates and drawing.
        """
        running = True


        while running:
            self.ticker.next_tick()
            self.screen.fill(self.background_color)

            # event handling and mouse info
            events = [event for event in pygame.event.get()]
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

            # GUI and program updates
            self._update_key_events(events)
            self.container.update(self.key_events, pygame.mouse.get_pos())
            self.update()

            # Zooming and panning
            if pygame.BUTTON_WHEELUP in self.key_events['down']:
                self.change_zoom(scaler=1.2)
            elif pygame.BUTTON_WHEELDOWN in self.key_events['down']:
                self.change_zoom(scaler=0.8)
            elif pygame.BUTTON_MIDDLE in self.key_events['down']:
                self.mouse_pan()

            # Draw everything to screen
            self.call_draw()

        pygame.display.quit()
        pygame.quit()
        sys.exit()

    def call_draw(self):
        """
        Cals all drawing methods. Called from self.run, but can also be called
        externally or from other methods such as self.mouse_pan.
        """
        self.screen.fill(self.theme['background'])
        self.draw()
        self.container.draw(self.screen)
        self.display_textlist(self.ticker.get_stats(), self.theme['5'], 5, 5)
        pygame.display.flip()

    def set_gui(self, elements):
        """
        Place a list of GUI elements. Any current elements are replaced.

        Parameters
        ----------
        elements : list
            List of GUI element objects such as buttons and sliders.

        """
        self.container.elements = elements


    def mouse_pan(self):
        """
        Pans the program screen using the middle mouse button.
        """
        initial_offset = self.pan_offset.copy()
        mouse_start = np.array(pygame.mouse.get_pos())
        while True:
            mouse_current = np.array(pygame.mouse.get_pos())
            self.pan_offset = initial_offset + mouse_current - mouse_start
            self.call_draw()
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONUP:
                    return

    def change_zoom(self, scaler):
        """
        Zooms in or out (centered on mouse position) and adjusts self.pan
        offset to allign the screen.
        """
        prev_zoom = self.zoom
        self.zoom = min(max(self.zoom * scaler, 0.2), 5)
        midpoint = np.array(pygame.mouse.get_pos()) - self.pan_offset
        delta = midpoint - (self.zoom / prev_zoom) * midpoint
        self.pan_offset = self.pan_offset + delta

    def display_text(self, text, color, x, y):
        """
        Draws one line of text on specified coordinates.
        """
        textblock = self.font_debug.render(text, True, color)
        self.screen.blit(textblock, (x,y))

    def display_textlist(self, text_list, color, x, y):
        """
        Draws a list of text on specified coordinates.
        """
        for line in text_list:
            self.display_text(line, color, x, y)
            y += 15

    @abstractmethod
    def update(self):
        """
        Implement specific application behaviour here.
        """
        pass

    @abstractmethod
    def draw(self):
        """
        Implement specific application behaviour here.
        """
        pass




class Container:

    def __init__(self):
        """
        Handles events and GUI elements. Makes sure that only one GUI element
        is active simultaniously.
        """
        self.elements = []


    def set_gui(self, elements):
        self.elements = elements

    def update(self, key_events, mouse_pos):

        # Find any active or triggered element, only update it and return
        for element in self.elements:
            if element.state in (State.ACTIVE, State.TRIGGERED):
                element.update(key_events, mouse_pos)
                return

        # If no element is active, update all elements
        for element in self.elements:
            element.update(key_events, mouse_pos)

    def draw(self, screen):
        for element in self.elements:
            element.draw(screen)

