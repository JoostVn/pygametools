import pygame
from pygametools.gui.base import Application, State
from pygametools.gui.elements import Button, Slider, Label, CheckBox, TextBox
import numpy as np
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import Tk
from pygametools.gui.file_manager import load_theme, save_theme


"""
TODO:
    - Create dummy versions of all GUI elements that override the update
    function and stay in the state given at instantializing.
"""



class DummyButton(Button):

    def __init__(self, state, text, pos, width, height):
        super().__init__(text, lambda: 0, pos, width, height)
        self.dummystate = state

    def update(self, key_events, mouse_pos):
        pass

    def draw(self, screen):
        self.state = self.dummystate
        super().draw(screen)
        self.state = State.PASSIVE


class DummySlider:

    pass


class DummyCheckbox:

    pass

class DummyTextBox:

    pass





class ColorRectangle:

    def __init__(self, default_color, left, top, width, height):
        self.rect = (left, top, width, height)
        self.R, self.G, self.B = default_color
    def draw(self, screen):
        color = (self.R, self.G, self.B)

        # Inner square
        pygame.draw.rect(screen, color, self.rect)

        # Border
        pygame.draw.rect(screen, (150,150,150), self.rect, 1)



class ThemeCreator(Application):

    def __init__(self, window_size):
        super().__init__(window_size)
        self.greyscale_option = False
        self.create_gui()

        theme = load_theme('default')
        self.set_theme_from_dict(theme)

    def create_gui(self):

        # Spacing constants
        x = 10
        y = 40
        square_width = 30
        square_heigth = 30
        slider_width = 80
        x_pad = 25
        y_pad = 8
        y_pad_settings = 30

        # Spacing intermediate calculations
        header_width = square_width + slider_width + x_pad
        x_settings = x + x_pad + header_width
        x_test_gui = x_settings + header_width + x_pad
        y_pad_slider = int(square_heigth/3)

        # Lists of rectangles and gui elements
        self.rectangles = []
        self.headers = []
        self.sliders_color = []
        self.sliders_greyscale = []
        self.settings = []
        self.dummy_gui = []

        # Creating headers
        self.headers.append(Label(
            'Theme Colors', (x, 10), header_width, 22, font_size=12))
        self.headers.append(Label(
            'Settings', (x_settings, 10), header_width, 22, font_size=12))
        self.headers.append(Label(
            'Example GUI', (x_test_gui, 10),
            self.window_size[0] - x_test_gui - x_pad , 22, font_size=12))

        # Creating sliders and color squares
        for i in range(8):
            rect = ColorRectangle(
                (100,250,100), x + slider_width + x_pad,
                y + y_pad + (square_heigth + y_pad) * i, square_width, square_heigth)
            self.rectangles.append(rect)

            # Color sliders
            for j, color in enumerate(['R', 'G', 'B']):
                self.sliders_color.append(Slider(
                    obj=rect, attribute=color, domain=(0, 255), default=100,
                    pos=(x, y + y_pad + (square_heigth + y_pad) * i + y_pad_slider * j),
                    width=slider_width, height=20, text=color))

            # Greyscale sliders
            self.sliders_greyscale.append(Slider(
                obj=rect, attribute='R', domain=(0, 255), default=100,
                pos=(x, y + y_pad + (square_heigth + y_pad) * i + y_pad_slider),
                width=slider_width, height=20, text=''))

        # Creating settings
        self.greyscale_checkbox = CheckBox(
            self, 'greyscale_option', False, (x_settings, y + y_pad),
            text='Greyscales')
        self.settings.append(self.greyscale_checkbox)
        self.settings.append(Button(
            'Load file', self.load_file, (x_settings, y + y_pad_settings), 60, 25))
        self.settings.append(Button(
            'Save file ', self.save_file,
            (x_settings + header_width-60, y + y_pad_settings), 60, 25))

        # Creating dummy GUI
        buttonwidth = 65
        buttonheight = 25
        buttonpad = buttonwidth + 8
        self.dummy_gui = [
            DummyButton(
                State.PASSIVE, 'Passive', (x_test_gui, y + y_pad),
                buttonwidth,
                buttonheight),
            DummyButton(
                State.HOOVER, 'Hoover', (x_test_gui + buttonpad, y + y_pad),
                buttonwidth, buttonheight),
            DummyButton(
                State.TRIGGERED, 'Triggered',
                (x_test_gui + buttonpad * 2, y + y_pad), buttonwidth,
                buttonheight),
            DummyButton(
                State.ACTIVE, 'Active', (x_test_gui + buttonpad*3, y + y_pad),
                buttonwidth, buttonheight)]

        # Lists of all gui options for looping and switching
        self.gui_color = (
            self.headers + self.sliders_color + self.settings +
            self.dummy_gui)
        self.gui_greyscale = (
            self.headers + self.sliders_greyscale + self.settings +
            self.dummy_gui)
        self.gui_all = (
            self.headers + self.sliders_greyscale + self.sliders_color +
            self.settings + self.dummy_gui)

    def get_theme_from_sliders(self):
        """
        Reads the value of all colors sliders and returns them as a theme
        dictionary.
        """
        # Load correct colors based on greyscale option
        if self.greyscale_option:
            colors = [slider.val for slider in self.sliders_greyscale]
            colors = np.vstack((colors, colors, colors)).T
        else:
            colors = [slider.val for slider in self.sliders_color]
            colors = np.reshape(colors, (-1, 3))

        # Format theme into a theme dict and return
        theme = {}
        for i, key in enumerate(self.theme.keys()):
            theme[key] = colors[i].tolist()
        return theme

    def set_theme_from_dict(self, theme):
        """
        Loads the theme based on a given theme dict. Applies theme to both
        the values of all sliders and the application/gui elements.
        """
        # Setting sliders
        colors = np.reshape(list(theme.values()), -1)
        for slider, color in zip(self.sliders_color, colors):
            slider.set_value(color)

        # Applying theme to gui
        self.theme = theme
        self.set_theme()
        for element in self.gui_all:
            element.theme = self.theme
            element.set_theme()

    def save_file(self):
        """
        Loads the current value of all sliders and saves them as a JSON file
        with a user-given filename.
        """

        # Reading theme from values
        theme = self.get_theme_from_sliders()

        # Opening dialog box
        root = Tk()
        root.withdraw()
        path = asksaveasfilename(
            initialdir='themes/', title="Save a theme",
            filetypes=[("JSON files", "*.json")])
        if path == '':
            return
        path += '.json'

        # Saving theme file
        save_theme(theme, path)

    def load_file(self):
        """
        Triggered from the load button. Opens a dialog box that allows
        the user to select a saved theme as a JSON file.
        """

        # Opening dialog box
        root = Tk()
        root.withdraw()
        path  = askopenfilename(
            initialdir='./themes/', title="Open a theme",
            filetypes=[("JSON files", "*.json")])
        if path == '':
            return

        # Sets greyscaleoption to false to allow for RGB theme
        if self.greyscale_checkbox.val:
            self.greyscale_checkbox.switch()

        # Extracting theme name and loading theme
        theme_name = path.split('/')[-1].split('.')[0]

        theme = load_theme(theme_name)
        self.set_theme_from_dict(theme)

    def update(self):
        """
        Updates the theme based on the most recent slider values and selects
        the correct GUI based on the greyscale option.
        """
        # Set theme based on most recent slider values
        theme = self.get_theme_from_sliders()
        self.set_theme_from_dict(theme)

        # Set GUI and set color sliders and squares to match greyscale sliders
        if self.greyscale_option:
            self.container.elements = self.gui_greyscale
            for slider in self.sliders_color:
                slider.val = slider.obj.R

        # Set GUI and set greyscale sliders to match color sliders (R)
        else:
            self.container.elements = self.gui_color
            for slider in self.sliders_greyscale:
                slider.val = slider.obj.R

    def draw(self):
        """
        Draws all rectangles to the screen.
        """
        for rect in self.rectangles:
            rect.draw(self.screen)


def main():

    app = ThemeCreator((650,400))
    app.run()



if __name__ == '__main__':
    main()