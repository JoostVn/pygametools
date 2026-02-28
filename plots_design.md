# Plots

The `plots` module is a redo of the original `plotting` module that support both static and dynamic plotting (bar plot, line plots, etc.) in Pygame. The main use of the `plots` module is visualizing statistics on simulations in real-time. Some example use cases: 

- Plotting the position of a one dimensional random walk over time. 
- Plotting the scores of different players in a game.
- Plotting the genomes of a whole population in a genetic algorithm as a grayscale 2d array.
- Plotting the accuracy of a neural network as it is optimized over different iterations. 

## TODO
1. Go trough files and fill the lists of requirements
2. Let Claude rewrite and cleanup / error check the design file a bit. (also: dots after sentences, grammar, marking references to code/objects/attributes with ``, sentence build etc.)
3. Let Claude add addition design choices that have to be made.
4. Further fill in the list and let claude add additional design requirements or functional suggestions.
5. Make an ASCII figure of the canvas class and all possible elements such as the Axes, Axis
6. Make a high-over plan and decide on some design patterns such as OO vs. functional design with dataclasses.


## Objects and terminology

The `plots` module, for the most part, follows Matplotlib terminology. Objects are named as follows:

Objects and elements 

- Canvas: contains all other elements (matplotlib: Figure).
- Axes: Area within a Canvas that contains the actual plots.
- Axis: X- and Y axis of plot; the horizontal/vertical lines that meet at (0,0)
- Ticks: Small lines that cross and axis to indicate dimensions and spacing.
- Tick labels: Numbers or string labels left of (y) or below (x) the two axis.
- Axis labels: Single labels for the x- and y axis.
- Title: Single string title of the plot.
- Legend: Legend that optionally contains the color and name of elements in the plot.
- Grid: A grid that extend from ticks.

> More?


Metrics
- pos: the (X, Y) position of the Canvas on the top-level Pygame screen in Pygame coordinates.
- dim: the (X, Y) dimensions of the Canvas in Pygame coordinates.
- dom: the (X, Y) domain of a plot in plot coordinates.


> More?


Note: graph coordinates are Y-reversed and scaled with respect to Pygame coordinates. 



## Functional requirements


### Plot elements and the Canvas object

- A plot is a collection of elements, contained within a `Canvas` object.
- Any type of plot can be added on a Canvas object, so it may contain different types of plots such as lines and scatter plots.
- The Canvas object contains a Pygame surface. This is the surface on which all other elements are drawn.


### Dynamic plotting
- Plots are dynamic. Dynamic plots allow for real-time changes in:
    - The data contained within the plot.
    - X- and Y domains.
    - The Canvas `pos`.
    - The positioning and dimensions of plot elements.
    - Adding/removing plots.

> Static plots are just dynamic plots that are not being updated.


### PlotMetrics
- The dimensions and domains of a Canvas object are stored in the PlotMetrics dataclass.


### Drawing 

- Only one class or module is responsible for drawing anything to the Pygame screen.
- Drawing is done in two different coordinate systems:
    - Pygame coordinates: regular pygame coordinates, but relative to the Canvas (except for the `pos` of Canvas itself, those coordinates are relative to the top-level screen).
    - Graph coordinates: coordinates relative to the X/Y domains of the `axes` object. Hence, drawing something to `(0,0)` in graph coordinates will always draw to the origin of the plot.
- In this class/module, Pygame drawing functions such as `pygame.draw.rect()` are wrapped such that it becomes easy to switch between pygame- and graph coordinates. 


### Adding data to plots

- When data is added to a plot, it is stored in the instance of that plot object.
- Only when a plot is drawn, datapoints are checked on whether they fit within the plot bounds.
- Once a point is checked, it shouldn't be checked again, unless the metrics of a plot change.
- Dynamic plots only need to be updated when their data changes. Otherwise, the Canvas surface is just re-drawn as it was in the previous tick.


## Supported plot types

The following plot types will be supported:

- Line plot
- Bar plot 
- Scatterplot
- 2D array plot (Matplotlib: Imshow)

## Questions / design choices

- How to handle the dimensions and locations of elements within the canvas? For example, where should the axes coordinates live? If they are a property of the `axes` instance, how will the title be able to center itself above it?
- How to handle the different coordinate systems (pygame / plot)
- Where should plot metrics live? How to handle the fact that any metric could be changed at any time and that all elements should adjust accordingly?