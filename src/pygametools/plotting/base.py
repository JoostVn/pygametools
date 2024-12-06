import numpy as np
from math import floor, log10
from .plotdraw import PlotDraw







"""
TODO / TESTING:
    - Bar size for bar plots
    - Work trough set_dimensions function
    - check antialising for lines
    - Check for refactor [elements -> plots] and [plot -> canvas] in all files

TODO / FEATURES:
    - Axis labels
    - Add legend bar to greyscale image plots
    - Make images and gifs from statis can dynamic plots
    
TODO / STRUCTURE:
    - Revise all docstrings
    - Merge all draw functions to just one, with use_graph_coordinates as
    paramter setting
    - Remove legend file
    
TODO / BUGS:
    -

IDEAS:
    -


"""


class Canvas:
    
    """
    Container that holds all plot components and attributes.
    """
    
    def __init__(self, xdomain, ydomain, pos, dim, **kwargs):
        xdomain = np.asarray(xdomain)
        ydomain = np.asarray(ydomain)
        self.pdraw = PlotDraw(self)
        self.xaxis = AxisX(self, xdomain, ydomain)
        self.yaxis = AxisY(self, ydomain, xdomain)
        self._update_domain_metrics()
        self.pos = np.array(pos)
        self.dim = np.array(dim)
        self.legend = None
        self.plots = []
        self.title = kwargs.get('title', '')
        self.border_visible = kwargs.get('border_visible', True)

    def _update_domain_metrics(self):
        """Used for PlotDraw fast coordinate conversion."""
        domain = np.vstack((self.xaxis.domain, self.yaxis.domain))
        self.d_len = np.diff(domain, axis=1).T[0]
        self.d_min = np.min(domain, axis=1)
        self.d_max = np.max(domain, axis=1)

    def fit_xdomain(self, margins=(-1,1)):
        """Fits the canvas domain to the plot data. Slower than set_dimensions"""
        x = np.concatenate([plot.x for plot in self.plots])
        xmin = np.min(x) + margins[0]
        xmax = np.max(x) + margins[1]
        self.set_dimensions(xdomain=(xmin,xmax))
        
    def fit_ydomain(self, margins=(-1,1)):
        """Fits the plot domain to the plot data. Slower than set_dimensions"""
        y = np.concatenate([plot.y for plot in self.plots])
        ymin = np.min(y) + margins[0]
        ymax = np.max(y) + margins[1]
        self.set_dimensions(ydomain=(ymin,ymax))

    def set_dimensions(self, xdomain=None, ydomain=None, pos=None, dim=None):
        """Updates pos/dim/domain of the canvas components."""
        
        # Convert and check domain inputs 
        xdomain = self.xaxis.domain if xdomain is None else np.asarray(xdomain)
        ydomain = self.yaxis.domain if ydomain is None else np.asarray(ydomain)
        assert xdomain[0] < xdomain[1], f'xdomain error; {str(xdomain)}'
        assert ydomain[0] < ydomain[1], f'ydomain error; {str(ydomain)}'
        
        # Set axis domains, update metrics, and set element domains
        self.xaxis.set_dimensions(xdomain, ydomain)
        self.yaxis.set_dimensions(ydomain, xdomain)
        self._update_domain_metrics()
        for plot in self.plots:
            plot.set_dimensions()
        
        # Update pos, dim , and legend dimensions
        if (self.legend is not None) and (pos is not None or dim is not None):
            self.pos = np.array(pos)
            self.dim = np.array(dim)
            self.legend.set_dimensions()
            
    def set_title(self, title):
        """ Set the canvas title header."""
        self.title = title
       
    def set_border_visible(self, visible):
        """Set border visible (True) or invisible (False)"""
        assert type(visible) is bool
        self.border_visible = visible
        
    def set_xaxis_custom_ticks(self, tick_intervals, tick_labels):
        """Define custom ticks for the x axis"""
        self.xaxis.tick_interval = tick_intervals
        self.xaxis.tick_labels = tick_labels
        self.xaxis.label_state = self.xaxis.LABELS_CUSTOM
                
    def set_yaxis_custom_ticks(self, tick_intervals, tick_labels):
        """Define custom ticks for the y axis"""
        self.yaxis.tick_interval = tick_intervals
        self.yaxis.tick_labels = tick_labels
        self.yaxis.label_state = self.yaxis.LABELS_CUSTOM
                
    def set_xaxis_nr_ticks(self, nr_ticks):
        """Set the number of auto generated tick for the x axis"""
        self.xaxis.nr_auto_ticks = nr_ticks
        self.xaxis.update_auto_ticks()
        
    def set_yaxis_nr_ticks(self, nr_ticks):
        """Set the number of auto generated tick for the y axis"""
        self.yaxis.nr_auto_ticks = nr_ticks
        self.yaxis.update_auto_ticks()
        
    def set_xaxis_ticks_disabled(self):
        """Resets tick lists to empty sequences."""
        self.xaxis.label_state = self.xaxis.LABELS_DISABLED
  
    def set_yaxis_ticks_disabled(self):
        """Resets tick lists to empty sequences."""
        self.yaxis.label_state = self.yaxis.LABELS_DISABLED
        
    def set_xaxis_locked(self, locked):
        """Lock the x axis position to the canvas left side"""
        assert type(locked) is bool
        self.xaxis.lock_position = locked

    def set_yaxis_locked(self, locked):
        """Lock the y axis position to the canvas bottom"""
        assert type(locked) is bool
        self.yaxis.lock_position = locked
    
    def set_legend(self, location='upper left', width=80, border=True):
        """Set and customize a legend for the canvas"""
        self.legend = Legend(self, location, width, border)
        self.legend.set_dimensions(self.pos, self.dim, self.plots)
    
    def add_plot(self, plot):
        """Add a plot to the canvas"""
        labels = [plot.label for plot in self.plots]
        assert not plot.label in labels, 'Pick a unique plot label'
        self.plots.append(plot)
        if self.legend is not None:
            self.legend.set_dimensions(self.pos, self.dim, self.plots)
   
    def get_plot(self, label):
        """Get a plot from self.plots based on a label"""
        labels = [plot.label for plot in self.plots]
        assert label in labels, 'Label not found in plot list'
        return self.plots[labels.index(label)]
   
    def draw(self, screen):
        """Draw all canvas components to the screen"""
        # Draw background
        top_left = (self.xaxis.domain[0], self.yaxis.domain[1])
        lower_right = (self.xaxis.domain[1], self.yaxis.domain[0])
        self.pdraw.grc_rect(
            screen, self.pdraw.color_bg, top_left, lower_right, fill=True)
            
        # Draw plots
        for plot in self.plots:
            plot.draw(screen)
        
        # Draw axis and title
        self.xaxis.draw(screen)
        self.yaxis.draw(screen)
        centerx = self.pos[0] + self.dim[0] / 2
        title_pos = (self.pos[0] + self.dim[0]/2, self.pos[1] - 22)
        self.pdraw.pgc_text(
            screen, self.title, title_pos, self.pdraw.font_l, centerx)
        
        # Draw canvas border
        if self.border_visible:
            self.pdraw.grc_rect(
                screen, self.pdraw.color_bg, top_left, lower_right, border=True)
        
        # Draw legend
        if self.legend:
            self.legend.draw(screen)



class Axis:
    
    LABELS_CUSTOM = 0
    LABELS_DISABLED = 1
    LABELS_AUTO = 2
    
    def __init__(self, canvas, domain, domain_other):
        """
        Axis for a canvas instance. The AxisX and AxisY classes inherit
        from this class. Axis contain the canvas domains and handle ticks,
        tick labels and axis lines.

        Parameters
        ----------
        canvas : Canvas instance
            The Instance of Canvas this axis belongs to. Used for accessing
            the PlotDraw instance.
        domain : Array of size 2
            Domain of the axis, given as (min, max).
        domain_other : Array of size 2
            Domain of the other axis, given as (min, max).

        """
        self.canvas = canvas
        self.domain = None
        self.domain_other = None
        self.cross = None                           # Other axis cross coord
        
        # Axis settings
        self.label_state = self.LABELS_AUTO         # Determines tick labels
        self.lock_position = False                  # Locks axis to canvas edge
        
        # Tick variables
        self.tick_interval = None                   # x OR y tick coordinates
        self.tick_labels = None                     # String tick labels
        self.nr_auto_ticks = 6                      # Nr auto generated ticks
                
        # Update dimensions
        self.set_dimensions(domain, domain_other)
    
    def update_auto_ticks(self):
        """
        Computes auto tick intervals and labels based on self.nr_auto_ticks
        and self.domain. Labels are formatted based on the canvas domain order
        of magnitude. Called from self.set_dimensions and from parent canvas
        when the number of axis ticks are updated.
        """
        
        # Compute tick interval
        margin = np.diff(self.domain)[0] * 0.1
        tick_domain = self.domain + (margin, -margin)
        self.tick_interval = np.linspace(*tick_domain, num=self.nr_auto_ticks)

        # Determine formatting based on order of magnitude of domain
        om_val = floor(log10(max(abs(self.domain))))
        om_dom = floor(log10(np.diff(self.domain)[0]))
        om = min(om_val, om_dom)
        if -5 < om < 5:
            format_str = lambda val: f'%.{max(0,-om + 1)}f' % val
        else:
            format_str = lambda val: np.format_float_scientific(val, 1)
        
        # Create string labels
        self.tick_labels = []
        for coordinate in self.tick_interval: 
            self.tick_labels.append(format_str(coordinate))
    
    def set_dimensions(self, domain, domain_other):
        """
        Set axis and other axis domains, recompute the axis crossing with the
        other axis and updates auto ticks/labels if applicable. Called when the 
        canvas domain is updated.

        Parameters
        ----------
        domain : Array of size 2
            Domain of the axis, given as (min, max).
        domain_other : Array of size 2
            Domain of the other axis, given as (min, max).
        """  
        self.domain_other = domain_other
        self.domain = domain
        
        # Get the axis crossing coordinate of the other axis
        nonzero_domain = not (self.domain_other[0] < 0 < self.domain_other[1])
        edge_axis = (self.lock_position or nonzero_domain)
        self.cross = self.domain_other.min() if edge_axis else 0

        # Update ticks
        if self.label_state == self.LABELS_AUTO:
            self.update_auto_ticks()
                    
    def draw(self, screen):
        """
        implemented in AxisX and AxisY
        """
        raise NotImplementedError



class AxisX(Axis):

    def draw(self, screen):
        """
        Draw the axis line, tick marks and tick labels on the screen.
        """
        # Draw axis line
        endpoints = np.vstack((self.domain, [self.cross]*2)).T
        color = self.canvas.pdraw.color_lines
        self.canvas.pdraw.grc_line(screen, color, endpoints)
        
        # Draw ticks and tick labels
        if self.label_state != self.LABELS_DISABLED:
            font = self.canvas.pdraw.font_s
            for x, label in zip(self.tick_interval, self.tick_labels):
                pos = (x, self.cross)
                self.canvas.pdraw.grc_tick(screen, color, pos, (0,3))
                self.canvas.pdraw.grc_text(
                    screen, label, pos, font, (0,5), centerx=True)
                
    
    
class AxisY(Axis):
                    
    def draw(self, screen):
        """
        Draw the axis line, tick marks and tick labels on the screen.
        """
        # Draw axis line
        endpoints = np.vstack(([self.cross]*2, self.domain)).T
        color = self.canvas.pdraw.color_lines
        self.canvas.pdraw.grc_line(screen, color, endpoints)
        
        # Draw ticks and tick labels
        if self.label_state != self.LABELS_DISABLED:
            font = self.canvas.pdraw.font_s
            for y, label in zip(self.tick_interval, self.tick_labels):
                pos = (self.cross, y)
                self.canvas.pdraw.grc_tick(screen, color, pos, (-3,0))
                self.canvas.pdraw.grc_text(
                    screen, label, pos, font, (-7,-7), rjustx=True)



class Legend:
    
    def __init__(self, canvas, location, width, border):
        """
        TODO: docstring

        Parameters
        ----------
        canvas : TYPE
            DESCRIPTION.
        location : TYPE
            DESCRIPTION.
        width : TYPE
            DESCRIPTION.
        border : TYPE
            DESCRIPTION.
        """
        
        # Parent canvas and layout attributes
        self.canvas = canvas
        self.border = border

        # Spacing and location constants
        self.location = location
        self.width = width
        self.x_spacing = 10
        self.y_spacing = 10
        self.label_yoffset = -5
        self.handle_dim = (6,6)
        self.margin = 4

        # Variable dimensions (NW/SE corners + line positioning)
        self.nw, self.se, self.handle_pos, self.label_pos = None, None, None, None

    def set_dimensions(self, pos, dim, plots):
        """
        Computes the NW and SE corners of the legend box, as well as the
        lable and handle positioning. Call this function after changing
        canvas domain/dim/pos or adding plots.
        """
        
        # Legend height
        n = len(plots)
        height = self.y_spacing * n + self.y_spacing

        # North-west and south-east corners
        if self.location == 'upper right':
            x = pos[0] + dim[0] - self.margin - self.width
            y = pos[1] + self.margin
        elif self.location == 'upper left':
            x = pos[0] + self.margin
            y = pos[1] + self.margin
        elif self.location == 'lower right':
            x = pos[0] + dim[0] - self.margin - self.width
            y = pos[1] + dim[1] - self.margin - height
        elif self.location == 'lower left':
            x = pos[0] + self.margin
            y = pos[1] + dim[1] - self.margin - height
        elif self.location == 'outer right':
            x = pos[0] + dim[0] + self.margin
            y = pos[1]
            
            
        self.nw = (x,y)
        self.se = np.add(self.nw, (self.width, height))

        # Handle and label positions
        handle_base = np.add(self.nw, self.handle_dim)
        label_base = np.add(handle_base, (self.x_spacing, self.label_yoffset))
        self.handle_pos, self.label_pos = [], []
        for i in range(n):
            self.handle_pos.append(np.add(handle_base, (0, i  * self.y_spacing)))
            self.label_pos.append(np.add(label_base, (0, i * self.y_spacing)))

    def draw(self, screen):
        """
        Draws the legend box, handles and labels.
        """
        self.canvas.pdraw.pgc_rect(
            screen, self.canvas.pdraw.color_bg, self.nw, self.se, self.border, 
            fill=True )
        for i, plot in enumerate(self.canvas.plots):
            handle_rect_dim = (
                self.handle_pos[i], np.add( self.handle_pos[i], self.handle_dim))
            self.canvas.pdraw.pgc_rect(
                screen, plot.color, *handle_rect_dim, fill=True)
            self.canvas.pdraw.pgc_text(
                screen, plot.label, self.label_pos[i], self.canvas.pdraw.font_m)

