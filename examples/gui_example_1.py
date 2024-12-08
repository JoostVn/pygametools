import pygame
from pygametools.gui.base import Application
from pygametools.gui.elements import Button, Slider, Label


class TestApp(Application):

    def __init__(self, window_size, simulation):
        super().__init__(window_size, theme_name="default_light")

        # Attributes for test object
        self.square_x = 200
        self.square_y = 50
        self.square_shade = 60

    def update(self):
        pass
        # print(self.pan_offset)

    def draw(self):


        draw_x = self.square_x + self.pan_offset[0]
        draw_y = self.square_y + self.pan_offset[1]


        pygame.draw.rect(
            self.screen,
            [self.square_shade]*3,
            (draw_x, draw_y,100,100))



def gui_test():
    app = TestApp((400,400), None)

    app.set_gui([
        Button(
            'test1', func=lambda: print('click 1'),
            pos=(10,10), width=60, height=20),
        Button(
            'test2', func=lambda: print('click 2'),
            pos=(10,40), width=60, height=20),
        Slider(
            app, 'square_x', domain=(100, 300), default=150, pos=(10, 70),
            width=60, height=20),
        Slider(
            app, 'square_y', domain=(100, 300), default=150, pos=(10, 90),
            width=60, height=20),
        Slider(
            app, 'square_shade', domain=(0, 255), default=60, pos=(10, 110),
            width=60, height=20)
        ])

    app.run()
    pygame.quit()


if __name__ == '__main__':

    gui_test()
