from pygametools.gui.base import Application
from pygametools.gui.elements import Button, Slider, Label
import pygame


class TestApp(Application):

    def __init__(self, window_size, simulation):
        super().__init__(window_size, theme_name="default")
        self.square_x = 200
        self.square_y = 50
        self.square_shade = 60

    def update(self):
        pass

    def draw(self):
        draw_x = self.zoom * self.square_x + self.pan_offset[0]
        draw_y = self.zoom * self.square_y + self.pan_offset[1]
        size = self.zoom * 100
        pygame.draw.rect(self.screen, [self.square_shade]*3, (draw_x, draw_y,size,size))


def gui_test():
    app = TestApp((400,400), None)
    app.set_gui([
        Button(
            'test 1', func=lambda: print('click 1'),
            pos=(10,10), width=60, height=20),
        Slider(
            app, 'square_x', domain=(100, 300), default=150, pos=(10, 40),
            width=60, height=20),
        Slider(
            app, 'square_y', domain=(100, 300), default=150, pos=(10, 60),
            width=60, height=20),
        Slider(
            app, 'square_shade', domain=(0, 255), default=200, pos=(10, 80),
            width=60, height=20)])
    app.run()
    pygame.quit()


if __name__ == '__main__':
    gui_test()
