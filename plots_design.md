# Plots

The `plots` module is a redo of the original `plotting` module that supports both static and dynamic plotting (bar plots, line plots, etc.) in Pygame. The main use of the `plots` module is visualizing statistics on simulations in real-time. Some example use cases:

- Plotting the position of a one-dimensional random walk over time.
- Plotting the scores of different players in a game.
- Plotting the genomes of a whole population in a genetic algorithm as a grayscale 2D array.
- Plotting the accuracy of a neural network as it is optimized over different iterations.

## TODO
1. ✅ Go through files and fill the lists of requirements.
2. ✅ Let Claude rewrite and clean up / error-check the design file a bit. (Also: dots after sentences, grammar, marking references to code/objects/attributes with ``, sentence structure, etc.)
3. Let Claude add additional design choices that have to be made.
4. Further fill in the list and let Claude add additional design requirements or functional suggestions.
5. Make an ASCII figure of the `Canvas` class and all possible elements such as `Axes` and `Axis`.
6. Make a high-level plan and decide on some design patterns such as OO vs. functional design with dataclasses.


## Objects and Terminology

The `plots` module, for the most part, follows Matplotlib terminology. Objects are named as follows.

- `Canvas`: Contains all other elements (Matplotlib: `Figure`).
- `Axes`: Area within a `Canvas` that contains the actual plots.
- `Axis`: The X- and Y-axis of a plot; the horizontal/vertical lines that meet at `(0, 0)`.
- `Ticks`: Small lines that cross an axis to indicate scale and spacing.
- `Tick labels`: Numbers or string labels to the left of (Y) or below (X) the axes.
- `Axis labels`: Single labels for the X- and Y-axis.
- `Title`: A single string title of the plot.
- `Legend`: A legend that optionally contains the color and name of elements in the plot.
- `Grid`: A grid that extends from ticks across the plot area.

> More?


**Metrics:**

- `pos`: The `(X, Y)` position of the `Canvas` on the top-level Pygame screen, in Pygame coordinates.
- `dim`: The `(X, Y)` dimensions of the `Canvas` in Pygame coordinates.
- `dom`: The `(X, Y)` domain of a plot in plot coordinates.

> More?


Note: Graph coordinates are Y-reversed and scaled with respect to Pygame coordinates.


## Functional Requirements


### Plot Elements and the Canvas Object

- A plot is a collection of elements contained within a `Canvas` object.
- Any type of plot can be added to a `Canvas` object, so it may contain different plot types such as line plots and scatter plots.
- The `Canvas` object contains a Pygame surface on which all other elements are drawn.


### Dynamic Plotting

- Plots are dynamic. Dynamic plots allow for real-time changes in:
    - The data contained within the plot.
    - X- and Y-domains.
    - The `Canvas` `pos`.
    - The positioning and dimensions of plot elements.
    - Adding/removing plots.

> Static plots are just dynamic plots that are not being updated.


### PlotMetrics

- The dimensions and domains of a `Canvas` object are stored in the `PlotMetrics` dataclass.


### Drawing

- Only one class or module is responsible for drawing anything to the Pygame screen.
- Drawing is done in two different coordinate systems:
    - Pygame coordinates: Regular Pygame coordinates, relative to the `Canvas` (except for the `pos` of `Canvas` itself, which is relative to the top-level screen).
    - Graph coordinates: Coordinates relative to the X/Y domains of the `Axes` object. Drawing something to `(0, 0)` in graph coordinates will always draw to the origin of the plot.
- In this class/module, Pygame drawing functions such as `pygame.draw.rect()` are wrapped to make switching between Pygame and graph coordinates straightforward.


### Adding Data to Plots

- When data is added to a plot, it is stored within that plot object.
- Only when a plot is drawn are datapoints checked against the plot bounds.
- Once a point is checked, it should not be checked again unless the metrics of the plot change.
- Dynamic plots only need to be updated when their data changes. Otherwise, the `Canvas` surface is redrawn as it was in the previous tick.


## Supported Plot Types

The following plot types will be supported:

- Line plot.
- Bar plot.
- Scatter plot.
- 2D array plot (Matplotlib: `imshow`).


## Questions / Design Choices

- How to handle the dimensions and locations of elements within the canvas? For example, where should the axes coordinates live? If they are a property of the `Axes` instance, how will the `Title` be able to center itself above it?
- How to handle the different coordinate systems (Pygame / plot)?
- Where should plot metrics live? How to handle the fact that any metric could be changed at any time and that all elements should adjust accordingly?