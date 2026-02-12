import pygame
from pygametools.gui.base import Application
from pygametools.gui.elements import Button, Slider, Label
from pygametools.color import Color
import numpy as np

"""
Real time GA TSP solver.

TODO: move to its own repo?
"""





class TSP: 

    def __init__(self):
        """
        Contains the current list of points and 
        """
        self.points = np.zeros(shape=(0,2), dtype=int)

    def add_point(self, pos: tuple[int, int]):
        self.points = np.vstack((self.points, pos))

    def del_point(self, pos: tuple[int, int], tolerance: int=5):
        vec = np.reshape(pos, (1,2)) - self.points
        dis = np.linalg.norm(vec, axis=1)
        closest_idx = np.argmin(dis)

        if dis[closest_idx] < tolerance:
            self.points = np.delete(self.points, closest_idx, axis=0)

class Simulation:

    def __init__(self, tsp: TSP):
        self.tsp = tsp
 
    def update(self,
               mouse_pos: tuple[int, int], 
               click_left: bool=False,
               click_right: bool=False):
        
        if click_left:
            self.tsp.add_point(mouse_pos)

            print(self.tsp.points)

        if click_right:
            self.tsp.del_point(mouse_pos)
            print(self.tsp.points)

    def draw(self, screen, zoom, pan_offset):
        
        for xy in self.tsp.points:
            xy_draw = (np.array(xy) * zoom + pan_offset).astype(int)
            rad = 1 + zoom
            pygame.draw.circle(screen, Color.GREY3, xy_draw, rad)


class TestApp(Application):

    def __init__(self, window_size: tuple[int, int], simulation: Simulation):
        super().__init__(window_size, theme_name="default_dark")
        self.simulation = simulation
    
    def update(self):

        if self.container.is_active:
            self.simulation.update(mouse_pos=self.mouse_pos_draw)
        elif pygame.BUTTON_RIGHT in self.key_events['down']:
            self.simulation.update(mouse_pos=self.mouse_pos_draw, click_right=True)
        elif pygame.BUTTON_LEFT in self.key_events['down']:
            self.simulation.update(mouse_pos=self.mouse_pos_draw, click_left=True)

    def draw(self):
        self.simulation.draw(self.screen, self.zoom, self.pan_offset)


def gui_test():

    tsp = TSP()
    sim = Simulation(tsp)

    app = TestApp((500, 500), sim)
    app.set_gui([])
    app.run()
    pygame.quit()


if __name__ == '__main__':
    gui_test()
