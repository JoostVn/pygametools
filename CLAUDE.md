# Plots

The `plots` module is a redo of the original `plotting` module that supports both static and dynamic plotting (bar plots, line plots, etc.) in Pygame. The main use of the `plots` module is visualizing statistics on simulations in real-time. Some example use cases:

- Plotting the position of a one-dimensional random walk over time.
- Plotting the scores of different players in a game.
- Plotting the genomes of a whole population in a genetic algorithm as a grayscale 2D array.
- Plotting the accuracy of a neural network as it is optimized over different iterations.

## TODO / plot_design file

1. ✅ Go through files and fill the lists of requirements.
2. ✅ Let Claude rewrite and clean up / error-check the design file a bit. (Also: dots after sentences, grammar, marking references to code/objects/attributes with ``, sentence structure, etc.)
3. ✅ Further fill in the requirements with Claude; make sure any obvious additions in all lists are taken into account.
4. ✅ Let Claude add additional design choices that have to be made.
5. Find solutions for all design choices.
6. Make an ASCII figure of the `Canvas` class and all possible elements such as `Axes` and `Axis`.
7. Make a high-level plan and decide on some design patterns such as OO vs. functional design with dataclasses.

## TODO / implementation

Only start with implementation when the design file is ready!

0. Salvage the old `plotting` module for usefol code (such as the color preview)
1. Improve the test/example script `examples\plots_dev.py`:
    - GUI sliders for plot metrics for easy testing

2. Refactor the current implementation of the `plots` module such that it is in line with-/supports the design decisions as described in this file.
    - General
        - Proper typehinting with npt
        - Make sure that private attributes and methods are prefixed by an underscore.
        - Implement getters and setters for attributes with additional logic (instead deidcated methods like set_num_ticks
    - `PlotMetrics`
        - Consequent location for any element-specific metric (such as axes padding, title size, legend size etc.)
        - Order of operations in metric updates (what updates what?)
        - Make it easy to change dimensions from `Canvas` without having to type `canvas.metrics.dim = ...` each time.
        - 
    - `PlotRenderer`
        - Pass to elements for drawing or have elements hold a reference to the instance itself.
    - `Elements`
        - Remove coupling between `Element` and each parent `Canvas`: they shouldn't be aware of the `PlotRenderer` and `Canvas` objects. Any update and draw functions should just reveive the required data.
        - TODO: does this make sense?

> ADD INTERMEDIATE STEPS

99. Improve the test/example script `examples\plots_dev.py` with dynamic and static data for plots such has:
    - Randomwalks (dynamic line)
    - Double dice throw (dynamic bar)
    - gif (dynamic array)
    - test image (static array)
    - normal distribution draws (dynamic scatter plot)

## Objects and Terminology

### Overview

TODO: move to a table

The `plots` module, for the most part, follows Matplotlib terminology. Objects are named as follows.

- `Canvas`: Contains all other elements (Matplotlib: `Figure`).
- `Axes`: Area within a `Canvas` that contains the actual plots.
- `Axis`: The X- and Y-axis of a plot. The X-axis runs along the bottom border of `Axes`; the Y-axis runs along the left border.
- `Ticks`: Small lines that cross an axis to indicate scale and spacing.
- `Tick labels`: Numbers or string labels to the left of (Y) or below (X) the axes.
- `Axis labels`: Single labels for the X- and Y-axis.
- `Title`: A single string title of the plot.
- `Legend`: A legend that optionally contains the color and name of elements in the plot.
- `Grid`: A grid that extends from ticks across the plot area.
- `PlotTheme`: Holds color and font configuration for all elements.
- `PlotRenderer`: Owns the two Pygame surfaces and is the single drawing layer responsible for coordinate conversion and all Pygame drawing calls.
- `Element`: Abstract base class for all drawable plot elements (`Axes`, `Axis`, `Title`, `Legend`, …).
- `LinePlot` / `ScatterPlot` / `BarPlot` / `ArrayPlot`: Concrete plot-data elements that live inside `Axes`.

Note: Graph coordinates are Y-reversed and scaled with respect to Pygame coordinates.

### Canvas

- A plot is a collection of elements contained within a `Canvas` object.
- Any type of plot can be added to a `Canvas` object, so it may contain different plot types such as line plots and scatter plots.
- The `Canvas` object holds a `PlotRenderer` instance, which owns the two Pygame surfaces: `surface_canvas` for all chrome elements (axes border, ticks, tick labels, axis labels, title, legend), and `surface_axes` for plot data.

### Axes

- A `Canvas` always contains a single `Axes` object.
- Plot data is drawn onto `surface_axes`. Because plot data is drawn on a separate surface, out-of-bounds data is clipped automatically without any per-point bounds checking.

### Axis Lines and Ticks

- The X-axis line runs along the bottom border of `Axes`; the Y-axis line runs along the left border. Axis lines do not move with the domain.
- An `Axis` supports two tick modes:
    - Fixed positions: evenly spaced ticks whose displayed values update when the domain changes.
    - Fixed values: ticks at specified data values whose pixel positions update when the domain changes.
- Tick labels are either numerical (auto-formatted based on magnitude) or user-supplied strings.
- Ticks and tick labels are drawn on `surface_canvas`, positioned relative to the edges of `Axes`. Tick pixel positions are computed directly from `axes_pos`, `axes_dim`, and the domain — no graph-to-canvas coordinate conversion is needed.

### Axis Labels

- Each `Axis` is optionally labeled with an `axis_label`: a single descriptive text label (e.g., "Time (s)").
- The X-axis label is centered below the tick labels; the Y-axis label is rotated 90° and placed to the left.

### Title

- Centered above the `axes`.

### Legend

- The `Legend` element auto-populates from plot objects registered with the `Axes`.
- Each plot element provides a color swatch and a name string to the legend.
- The legend can be positioned at a fixed corner of the `Axes`, or hidden.

### Grid

- `Grid` is an optional element that extends tick positions as horizontal/vertical lines across the `Axes`.
- Grid lines are drawn before plot data so they appear behind the data.
- Grid visibility and style (color, line width) are configurable via `PlotTheme`.

## Functional Requirements

### Dynamic Plotting

- Plots are dynamic. Dynamic plots allow for real-time changes in:
    - The data contained within the plot.
    - X- and Y-domains.
    - The `Canvas` `pos`.
    - The positioning and dimensions of plot elements.
    - Adding/removing plots.
- Static plots are just dynamic plots that are not being updated.

### PlotMetrics

- The dimensions and domains of a `Canvas` object are stored in the `PlotMetrics` dataclass.
- When any metric changes, `PlotMetrics` notifies all registered `Element` instances so they can recompute their layout.
- Each `Element` receives the name of the changed metric, allowing it to skip recomputation for unrelated metrics.

#### List of metrics

- `pos`: The `(X, Y)` position of the `Canvas` on the top-level Pygame screen, in Pygame coordinates.
- `dim`: The `(X, Y)` dimensions of the `Canvas` in Pygame coordinates.
- `xdom` / `ydom`: The domain of a plot along each axis, in plot coordinates.

### Theming

- All colors and fonts are defined in a `PlotTheme` object attached to the `Canvas`.

### Drawing

- Only `PlotRenderer` is responsible for drawing anything to the Pygame screen.
- `PlotRenderer` owns `surface_canvas` and `surface_axes`. On each frame, `surface_axes` is blitted onto `surface_canvas` at `axes_pos`, and `surface_canvas` is then blitted onto the top-level Pygame screen at `pos`.
- Drawing is done in two different coordinate systems:
    - Canvas coordinates: Pygame coordinates relative to the top-left of `surface_canvas`.
    - Graph coordinates: Coordinates relative to the X/Y domains of `Axes`. Used only when drawing plot data onto `surface_axes`.
- `PlotRenderer` wraps Pygame drawing functions to accept either coordinate system and route to the correct surface.

### Adding Data to Plots

- When data is added to a plot, it is stored within that plot object.
- Out-of-bounds data is clipped automatically by `surface_axes`; no per-point bounds checking is required.
- Dynamic plots only need to be updated when their data or metrics change. Otherwise, `surface_canvas` is reblitted as it was in the previous tick.

### Public Data API

- on the surface, users interact only directly with:
    - `Canvas`, which, at instantiation, also inits base elements such as `Title`, `Axes`, `PlotMetrics`, etc.
    - Plots (such as `LinePlot`, `ScatterPlot`, etc.) that are added to the canvas with:

    ```python
    canvas.add_plot(plot)
    ```

- Attributes of other elements can be adjusted by accessing them from the `Canvas` objects:

    ```pyhton
    canvas.metrics.pos = (20, 30)
    ```

    - All public attributes of elements should be set/retreived with getters and setters.
    - All private attributes should be prefixed with an underscore.


> TODO: add more

## Supported Plot Types

The following plot types will be supported:

- Line plot.
- Bar plot.
- Scatter plot.
- 2D array plot (Matplotlib: `imshow`).

## Questions / Design Choices

- `PlotMetrics`
    - In the current configuration, `PlotMetrics` holds all objects / elements it must update. But, each element also holds a referencem to `PlotMetrics` because they need it for their own logic. Is this circle reference a problem? If yes, fix.
    - **Observer pattern scope**: `PlotMetrics` currently notifies all elements. Should plot-data elements (`LinePlot`, etc.) also register directly with `PlotMetrics`, or should `Axes` be responsible for propagating metric changes to its child plots?
    - Should `PlotMetrics` be responsible for update calls to other elements?
    - How to handle the dimensions and locations of elements within the canvas? For example, where should the axes pos live? If they are a property of the `Axes` instance, how will the `Title` be able to center itself above it?
    - There should be support for automatically updating xdom/ydom when adding new data if that new data is out of bounds of the current domains. Where should that logic live?
- Drawing and coordinates
    - How to handle the different coordinate systems (Pygame / plot)? Mainly
        - Is the coordinate conversion function (graph to pygame) a method of `PlotRenderer` or a separate function?
        - Is the coordinate conversion called from elements or within the `PlotRenderer` based on a parameter?
        - Should the draw surfaces be passed to the `PlotRenderer` or selected based on a parameter?
    - **Coordinate input types**: Should `PlotRenderer` accept plain tuples, lists, and numpy arrays interchangeably, or enforce a single type for performance?

- Structure
    - Should elements be aware of their parent canvas? Or should the parent canvas just call a draw method for all plot it's holding and pass the `PlotRenderer` object?

- Other
    - Should the plot legend have its own surface?