import numpy as np
from pygametools.color import Color, ColorGradient



class Plot:

    def __init__(self, canvas, label, color):
        """
        Plot parent class for basic plot elements. Contains the attributes and
        methods that any plot subclass must contain.

        Parameters
        ----------
        label : String
            Plot label. Used in the legend.
        color : Tuple
            Plot color. Used for coloring plot elements and in the legend.
        """
        self.canvas = canvas
        self.label = label
        self.color = color
        self.x = np.empty(0, float)
        self.y = np.empty(0, float)
        canvas.add_plot(self)

    def set_dimensions(self):
        """
        Called from canvas. Overidden by sub classes.
        """
        raise NotImplementedError

    def draw(self, screen):
        """
        Called from canvas. Overidden by sub classes.
        """
        raise NotImplementedError



class DataPlot(Plot):

    def __init__(self, canvas, label, color, size):
        """
        DataPlot parentclass from which all data-oriented plots (Line, Scatter,
        and Bar) inherited. This class adds the size, x, y, and in_scope
        attributesfrom to the Plot base class, as well as an implementation
        for the set_dimensions method and the add_data and set_data methods.

        Parameters
        ----------
        label : String
            Plot label. Used in the legend.
        color : Tuple
            Plot color. Used for coloring plot elements and in the legend.
        size : Integer
            interpreted based on context (markersize / linewidth / bar width..)
        """
        super().__init__(canvas, label, color)
        self.size = size
        self.in_scope = np.empty(0, bool)

    def set_dimensions(self):
        """
        Called from canvas at domain changes. Determines  in scope points
        for the x and y dataset with respect to the Canvas domain.
        """
        self.in_scope = self.canvas.pdraw.inscope_points(self.x, self.y)

    def add_data(self, x, y):
        """
        Add x and y data to the dataset. Used for dynamic plots. Returns self
        to allow one-line instantiating and addding data.
        """

        x = np.reshape(x, -1)
        y = np.reshape(y, -1)

        self.x = np.concatenate((self.x, x))
        self.y = np.concatenate((self.y, y))
        new_in_scope = self.canvas.pdraw.inscope_points(x, y)
        self.in_scope = np.concatenate((self.in_scope, new_in_scope))
        return self

    def set_data(self, x, y):
        """
        Replace and set x and y data in the dataset. Returns self
        to allow one-line instantiating and addding data.
        """
        self.x = np.reshape(x, -1)
        self.y = np.reshape(y, -1)
        self.in_scope = self.canvas.pdraw.inscope_points(self.x, self.y)
        return self


class Line(DataPlot):

    def __init__(self, canvas, label, color, line_width):
        """
        Line plot, inherits from the DataPlot class.
        """
        super().__init__(canvas, label, color, size=line_width)

    def draw(self, screen):
        """
        Splits the data into in-scope line segments and draws them using
        the plotdraw instance.
        """
        if len(self.x) < 2:
            return
        indices = np.nonzero(self.in_scope[1:] != self.in_scope[:-1])[0] + 1
        segments = np.split(np.transpose((self.x, self.y)), indices)
        segments = segments[0::2] if self.in_scope[0] else segments[1::2]
        for segment in segments:
            if len(segment) >= 2:
                self.canvas.pdraw.grc_lines(
                    screen, self.color, segment, self.size, aa=True)



class Scatter(DataPlot):

    MARKERS = ['o', 'x', '+']

    def __init__(self, canvas, label, color, marker_size=3, marker='o'):
        """
        Scatter plot. Inherits from the DataPlot class.
        """
        super().__init__(canvas, label, color, marker_size)
        assert marker in self.MARKERS, f'Supported markers: {self.MARKERS}'
        self.marker = marker

    def draw(self, screen):
        """
        Uses the plotdraw instance to draw each data point. Some marker
        options are drawn as a collection of lines (ticks) offsetted from the
        point coordinate.
        """
        points = np.transpose((self.x[self.in_scope], self.y[self.in_scope]))

        for point in points:
            if self.marker == 'o':
                self.canvas.pdraw.grc_point(screen, self.color, point, self.size)
            elif self.marker == '+':
                l = self.size/2
                for offset in [(-l,0),(l,0),(0,-l),(0,l)]:
                    self.canvas.pdraw.grc_tick(screen, self.color, point, offset)
            elif self.marker == 'x':
                l = self.size/2
                for offset in [(l,l),(-l,l),(l,-l),(-l,-l)]:
                    self.canvas.pdraw.grc_tick(screen, self.color, point, offset)



class Bar(DataPlot):

    def __init__(self, canvas, plot, color, width, label):
        """
        Bar plot. Inherits from the DataPlot class. The x coordinates
        determine the bar positioning, the y coordinates the bar heigth.
        """
        super().__init__(canvas, plot, color, width, label)

    def draw(self, screen):
        """
        Uses the plotdraw instance to draw each bar.
        """
        bars = zip(self.x[self.in_scope], self.y[self.in_scope])
        for center, top in bars:
            top_left = (center - self.size/2, top)
            lower_right = (center + self.size/2, 0)
            self.canvas.pdraw.grc_rect(screen, self.color, top_left, lower_right)



class Network(Plot):

        # TODO:
        #    - Compute coordinates in class with size parameter
        #    - Handle in_scope points

    def __init__(self, canvas, label, node_coords, edge_coords, **kwargs):
        """
        Plots a network that dynamically colors nodes and edges based on
        node_value and edge_values.

        Parameters
        ----------
        label : String
            Plot label. Used in the legend.
        node_coords : Array of size (n, 2)
            Graph coordinates for all nodes.
        edge_coords : Array of size (n, 2, 2)
            Graph coordinates for all edges, where each edge is given as a two
            coordinate pair: ((x,x),(y,y))
        **kwargs : dict
            Color and size keyword arguments. Defaults are small nodes, with
            colors neg/mid/pos -> red/grey/green. Activated nodes are marked
            with a border (default black) set by self.color_lit.
        """
        super().__init__(canvas, label, color=(0,0,0))
        self.node_size = kwargs.get('node_size', 3)
        self.color_mid = kwargs.get('color_mid', Color.GREY8)
        self.color_pos = kwargs.get('color_pos', Color.GREEN2)
        self.color_neg = kwargs.get('color_neg', Color.RED2)
        self.color_lit = kwargs.get('color_lit', Color.BLACK)
        self.colgradient_pos = ColorGradient(self.color_mid, self.color_pos)
        self.colgradient_neg = ColorGradient(self.color_mid, self.color_neg)

        # Node/edge coordinates and values
        self.node_coords = np.array(node_coords)
        self.edge_coords = np.array(edge_coords)
        self.node_values = np.full(self.node_coords.shape[1], np.nan)
        self.edge_values = np.full(self.edge_coords.shape[0], np.nan)

        # Set self.x and self.y for autofitting canvas domain
        self.x, self.y = self.node_coords

    def set_dimensions(self):
        pass

    def set_values(self, node_values, edge_values):
        """
        Set values for nodes, edges, or both. Values depecit the coloring of
        elements as follows: red: val < 0, white/grey: val = 0, green: val > 0.
        Values are between (1-, 1). When the values for nodes or edges are
        np.nan, they will be colored grey in the plot.
        """
        self.node_values = node_values
        self.edge_values = edge_values

    def draw(self, screen):
        """
        Draws all edges and nodes of the network. Nodes and edges are colored
        according to their values in self.node_values and self.edge_values.
        The smaller a value is to zero, the closer a color gets to
        self.color_mid. Edges are sorted on their absolute value prior to
        drawing so thtat the 'high opacity' edges are drawn last.
        """
        # Draw edges in order of abs value to mimmic opacity
        e_order = np.argsort(abs(self.edge_values))
        e_coords = self.edge_coords[e_order]
        e_vals = self.edge_values[e_order]
        for edge, val in zip(e_coords, e_vals):
            if str(val) == 'nan':
                col = Color.GREY3
            elif val >= 0:
                col = self.colgradient_pos.get_color(val)
            elif val < 0:
                col = self.colgradient_neg.get_color(abs(val))
            self.canvas.pdraw.grc_line(screen, col, edge.T, aa=True)

        # Draw nodes
        n_coords = self.node_coords.T
        n_vals = self.node_values
        for node, val in zip(n_coords, n_vals):
            if str(val) == 'nan':
                col = Color.GREY3
            elif val >= 0:
                col = self.colgradient_pos.get_color(val)
            elif val < 0:
                col = self.colgradient_neg.get_color(abs(val))
            self.canvas.pdraw.grc_point(screen, col, node, self.node_size)

        # Draw lit node circles
        output_layer = n_coords.T[0] == n_coords.T[0].max()
        lit_nodes = ((n_vals >= 0.5) & output_layer)
        for node, val in zip(n_coords[lit_nodes], n_vals[lit_nodes]):
            self.canvas.pdraw.grc_circle(
                screen, self.color_lit, node, self.node_size+1)



class ArrayImage(Plot):

    def __init__(self, canvas, label):
        """
        Image plot based on a scalar numpy array. Images are scaled such that
        they fill the complete canvas regardless of dimensions.
        """
        super().__init__(canvas, label, color=(0,0,0))
        self.arr = None

    def set_image_grayscale(self, arr, color_hi, color_lo=Color.WHITE):
        """
        Set a greyscale image with a scalar 2d numpy array. Returns self
        to allow one-line instantiating and addding an image.

        Parameters
        ----------
        arr : Array with two dimensions.
            The array image to be projected as an image. All values in the
            array are clipped to (0 <= val <= 1)
        color_hi : tuple of len 3
            The color for values equal to 1.
        color_lo : Tuple of len 3, optional
            the color for values equal to 0. The default is (255,255,255).
        """
        assert len(arr.shape) == 2
        self.color = color_hi
        arr_clipped = np.clip(arr.T, 0, 1)
        arr_rgb = np.stack([arr_clipped] * 3, axis=2)
        color_diff = np.subtract(color_hi, color_lo)
        arr_rgb = color_lo + arr_rgb * color_diff
        self.arr = arr_rgb
        return self

    def set_image_rgb(self, arr):
        """
        Set an RGB image. Returns self to allow one-line instantiating and
        addding an image.

        Parameters
        ----------
        arr : Array of size (w,h,3)
            The RGB array image to be projected as an image. All values in the
            array are clipped to (0 <= val <= 1). Higher values indicate
            brighter coloring.
        """
        assert len(arr.shape) == 3 and arr.shape[2] == 3
        arr_clipped = np.clip(np.transpose(arr, (1,0,2)), 0, 1)
        arr_rgb = arr_clipped * 255
        self.arr = arr_rgb
        return self

    def draw(self, screen):
        """
        Draw the image to the screen with the plotdraw instance.
        """
        if self.arr is None:
            return
        self.canvas.pdraw.grc_array_image(screen, self.arr)




