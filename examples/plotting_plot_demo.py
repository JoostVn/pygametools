import numpy as np
from pygametools.color import Color
from pygametools.plotting import Canvas, colorpreview, PlotTester
from pygametools.plotting.plots import Line, Scatter, Bar, ArrayImage
from PIL import Image, ImageSequence



def plot_functions(tester, pos, dim):

    # Creating canvas
    xdomain, ydomain = (-80, 70), (-30, 40)
    canvas = Canvas(xdomain, ydomain, pos, dim)
    canvas.set_xaxis_nr_ticks(6)
    canvas.set_yaxis_nr_ticks(7)
    canvas.set_title('Scatterplot and functions')
    canvas.set_legend(width=80)

    # Creating plots
    f1 = np.vectorize(lambda x: ((x-5)**3 - 20*x**2 - 30*x)/500+1)
    f2 = np.vectorize(lambda x: (x**2)/100)
    x = np.linspace(*xdomain, num=300)
    s1 = np.random.normal(loc=(20, 10), scale=(10,5), size=(100, 2)).T
    line_1 = Line(canvas, 'Function 1', Color.BLUE1, 1).add_data(x, f1(x))
    line_2 = Line(canvas, 'Function 2', Color.RED1, 1).add_data(x, f2(x))
    scatter = Scatter(canvas, 'Scatter', Color.GREY3, 3, 'x').add_data(*s1)

    # Adding canvas to tester
    tester.add_static(canvas)



def plot_randomwalk(tester, pos, dim):

    # Creating canvas
    xdomain, ydomain = (0,1), (-1,1)
    canvas = Canvas(xdomain, ydomain, pos, dim)
    canvas.set_xaxis_nr_ticks(4)
    canvas.set_yaxis_nr_ticks(7)
    canvas.set_yaxis_locked(True)
    canvas.set_title('Dynamic randomwalk plot')
    canvas.set_legend(width=80)

    # Creating plot
    walk = Line(canvas, 'walk', Color.GREEN2, 1).add_data(0, 0)

    # Plot update function
    def update_func(canvas):
        plot = canvas.get_plot('walk')
        new_x = plot.x[-1] + 1
        new_y = plot.y[-1] + np.random.uniform(-1, 1)
        plot.add_data(new_x,new_y)
        canvas.fit_xdomain()
        canvas.fit_ydomain()

    # Adding canvas and update function to tester
    tester.add_dynamic(canvas, update_func)



def plot_testimg(tester, pos, dim):

    # Creating canvas
    canvas = Canvas((0,1), (0,1), pos, dim)
    canvas.set_title('Static Array image')

    # Loading/normalizing image and adding noise
    with open('./examples/plotting_test_resources/test_img.csv', 'r', encoding='utf-8-sig') as file:
        value_arr = np.genfromtxt(file, dtype=float, delimiter=';')
    value_arr = (value_arr / value_arr.max())
    value_arr = value_arr + np.random.uniform(-0.2,0.2,size=value_arr.shape)

    # Creating image plot
    plot = ArrayImage(canvas, 'Test image')
    plot.set_image_grayscale(value_arr, Color.BLUE1)

    # Adding canvas to tester
    tester.add_static(canvas)



def plot_gif(tester, pos, dim):

    # Creating canvas
    canvas = Canvas((0,1), (0,1), pos, dim)
    canvas.set_title('GIF test')

    # Loading gif frames
    img = Image.open('./examples/plotting_test_resources/ra.gif')
    frames = []
    for frame in ImageSequence.Iterator(img):
        rgb_frame = np.array(frame.copy().convert('RGB').getdata(),dtype=np.uint8)
        rgb_frame = rgb_frame.reshape(frame.size[1],frame.size[0],3) / 255
        frames.append(rgb_frame)
    gif_frames = np.stack(frames)

    # Creating plot
    plot = ArrayImage(canvas, 'gif')

    # Gif update function as class
    class GifUpdate:

        def __init__(self, plot, gif_frames):
            self.plot = plot
            self.gif_frames = gif_frames
            self.i = 0

        def __call__(self, canvas):
            arr = self.gif_frames[self.i]
            self.plot.set_image_rgb(arr)
            self.i += 1
            if not self.i < len(self.gif_frames):
                self.i = 0

    # Adding canvas and update function to tester
    tester.add_dynamic(canvas, GifUpdate(plot, gif_frames))



if __name__ == '__main__':

    # Parameters
    dim = (200,120)
    rows, cols = 2, 2
    margins = (40, 40)

    # Plot positions
    pos = {}
    for c in range(cols):
        for r in range(rows):
            x = 50 + c * (margins[0] + dim[0])
            y = 40 + r * (margins[1] + dim[1])
            pos[(r,c)] = (x,y)

    # Creatnig plot tester instance
    tester = PlotTester((530,340), 1/25)

    # Adding plots
    plot_gif(tester, pos[1,0], dim)
    plot_testimg(tester, pos[0,0], dim)
    plot_randomwalk(tester, pos[0,1], dim)
    plot_functions(tester, pos[1,1], dim)

    tester.show()


