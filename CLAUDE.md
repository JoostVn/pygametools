# Plots

The `plots` module is a redo of the original `plotting` module that supports both static and dynamic plotting (bar plots, line plots, etc.) in Pygame. The main use of the `plots` module is visualizing statistics on simulations in real-time. Some example use cases:

- Plotting the position of a one-dimensional random walk over time.
- Plotting the scores of different players in a game.
- Plotting the genomes of a whole population in a genetic algorithm as a grayscale 2D array.
- Plotting the accuracy of a neural network as it is optimized over different iterations.

## TODO / implementation

Only start with implementation when the design file is ready!

0. Salvage the old `plotting` module for useful code (such as the color preview).

1. Refactor the current implementation of the `plots` module to match the design decisions in this file.
    - General
        - Proper typehinting with `npt`.
        - Make sure that private attributes and methods are prefixed by an underscore.
        - Implement getters and setters for attributes with additional logic (instead of dedicated methods like `set_num_ticks`).
    - `DrawContext`
        - Implement `DrawContext` as a simple dataclass holding `renderer: PlotRenderer`, `metrics: PlotMetrics`, `theme: PlotTheme`.
        - Instantiate it once in `Canvas.__init__`.
    - `PlotMetrics`
        - Remove all `Element` references from `PlotMetrics`; replace with a single `_on_change: Callable[[str], None]` callback to `Canvas`.
        - Add `Canvas._on_metrics_changed(metric_name: str)` as the mediator method that propagates changes to all registered elements.
        - Add `on_metrics_changed(metric_name: str, metrics: PlotMetrics)` to the `Element` abstract base class.
        - Register all elements with `Canvas` (not `PlotMetrics`) at construction time.
    - `PlotRenderer`
        - Remove `parent_canvas` reference; `PlotRenderer.__init__` takes `dim` and `axes_dim` directly. Canvas calls `pr.resize(dim, axes_dim)` when metrics change.
        - Implement two draw method families: `draw_[shape]_canvas(...)` for canvas coordinates and `draw_[shape]_graph(...)` for graph coordinates.
        - Implement `_graph_to_canvas(pos, metrics) -> tuple[int, int]` as a private method on `PlotRenderer`.
        - Surface selection is internal to `PlotRenderer`: canvas-coord methods draw to `surface_canvas`; graph-coord methods convert and draw to `surface_axes`.
        - Enforce strict input types: `tuple[int, int]` for individual positions, `npt.NDArray[np.float64]` for bulk data. No implicit conversion.
    - `Canvas`
        - Replace the hardcoded draw list in `Canvas.draw()` with a proper element registry (`_elements: list[Element]`).
    - `Elements`
        - Remove `parent_canvas` reference from `Element` and all subclasses.
        - Remove any `PlotMetrics` reference from all `Element` subclasses; receive it as a parameter in `on_metrics_changed`.
        - Draw functions receive `DrawContext`; `on_metrics_changed` receives `metric_name` and `metrics`.

2. Implement `Grid` element.

3. Complete `Legend` element (stub exists).

4. Add `LinePlot` and `ScatterPlot` plot types.

5. Implement domain auto-expansion.
    - In `Canvas.add_plot(plot)`, register an `_on_data_added` callback on the plot.
    - Implement `Canvas._check_domain_expansion(x, y)` that updates `metrics.xdom` / `metrics.ydom` when new data falls outside the current domain.

6. Make sure docstrings of methods and classes reflect key design decisions (only when not obvious from the code).

7. Improve the test/example script `examples\plots_dev.py`:
    - GUI sliders for plot metrics for easy testing.
    - Dynamic and static data examples:
        - Random walk (dynamic line)
        - Double dice throw (dynamic bar)
        - GIF (dynamic array)
        - Test image (static array)
        - Normal distribution draws (dynamic scatter)

## Dependency Tree

```text
Canvas
├── DrawContext
│   ├── PlotMetrics
│   ├── PlotTheme
│   └── PlotRenderer
│       ├── surface_canvas
│       └── surface_axes
├── Axes
├── Title
├── Legend
├── Grid
└── [XAxis | YAxis]
└── [LinePlot | ScatterPlot | BarPlot | ArrayPlot]
```

Dependency flow (what holds a reference to what):

- `Canvas` → `PlotMetrics`, `PlotRenderer`, `PlotTheme`, `DrawContext`, all `Element` instances
- `PlotMetrics` → `Canvas` (via `_on_change` callback only)
- Plot-data elements → `Canvas` (via `_on_data_added` callback only)
- All other `Element` subclasses → nothing (receive `DrawContext` as a method argument for draw calls; receive `PlotMetrics` as a method argument for `on_metrics_changed`)

## Objects and Terminology

### Overview

The `plots` module, for the most part, follows Matplotlib terminology.

| Object | Description |
| --- | --- |
| `Canvas` | Contains all other elements (Matplotlib: `Figure`). |
| `Axes` | Area within a `Canvas` that contains the actual plots. |
| `Axis` | The X- or Y-axis. X runs along the bottom border of `Axes`; Y runs along the left border. |
| Ticks | Small lines that cross an axis to indicate scale and spacing. Implemented within `Axis`, not a separate class. |
| Tick labels | Numbers or strings to the left of (Y) or below (X) the axes. Implemented within `Axis`, not a separate class. |
| `Axis labels` | Single descriptive label per axis. |
| `Title` | A single string title centered above the axes. |
| `Legend` | Optionally shows the color and name of each plot element. |
| `Grid` | Optional lines extending from ticks across the axes area. |
| `PlotTheme` | Holds color and font configuration. |
| `PlotRenderer` | Owns the two Pygame surfaces; sole drawing layer. |
| `DrawContext` | Lightweight dataclass bundling `PlotRenderer`, `PlotMetrics`, and `PlotTheme`. Passed to element draw calls so elements need no permanent references to any of the three. |
| `Element` | Abstract base class for all drawable plot elements. |
| `LinePlot` / `ScatterPlot` / `BarPlot` / `ArrayPlot` | Concrete plot-data elements that hold data. |

*Note: Graph coordinates are Y-reversed and scaled with respect to Pygame coordinates.*

### Layout

```text
┌──────────────────────────────────────────────┐ 
│Canvas                    Title               │ 
│                ┌─────┬─────┬─────┬─────────┐ │ 
│yticks/labels 4─┤Axes ┼─ ─ ─┼─ ─ ─┼ ┌──────┐│ │ 
│                │                   │Legend││ │ 
│              3─┤     │     │     │ │      ││ │ 
│                │            Grid   └───┬──┘│ │ 
│ylabel        2─┤ ─ ─ ┼─ ─ ─┼─ ─ ─┼─ ─ ─┼── │ │ 
│                │                           │ │ 
│              1─┤yaxis│     │     │     │   │ │ 
│                │     xaxis                 │ │ 
│              0─┼──┬──┬──┬──┬──┬──┬──┬──┬───┘ │ 
│                0  1  2  3  4  5  6  7  8  9  │ 
│                       xticks/labels          │ 
│                           xlabel             │ 
└──────────────────────────────────────────────┘ 
```

### Canvas

- A plot is a collection of elements contained within a `Canvas` object.
- Any type of plot can be added to a `Canvas` object, so it may contain different plot types such as line plots and scatter plots.
- The `Canvas` object holds a `PlotRenderer` instance, which owns the two Pygame surfaces: `surface_canvas` for all chrome elements (axes border, ticks, tick labels, axis labels, title, legend), and `surface_axes` for plot data.

### Axes

- A `Canvas` always contains a single `Axes` object.
- Plot data is drawn onto `surface_axes`. Because plot data is drawn on a separate surface, out-of-bounds data is clipped automatically without any per-point bounds checking.

### Axis and ticks

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
- The legend can be positioned at a fixed corner of the `Axes` (inside or outside), or hidden.
- The legend has no dedicated surface. It is drawn on `surface_canvas` after `surface_axes` is blitted, so it appears on top of plot data regardless of position.

### Grid

- `Grid` is an optional element that extends tick positions as horizontal/vertical lines across the `Axes`.
- Grid lines are drawn before plot data so they appear behind the data.
- Grid color is part of `PlotTheme`.

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
- `PlotMetrics` holds a single `_on_change: Callable[[str], None]` callback to `Canvas`. When any metric changes, it calls this callback with the name of the changed metric.
- `Canvas` acts as the mediator: on receiving the notification, it calls `on_metrics_changed(metric_name, metrics)` on all registered `Element` instances so they can recompute their layout.
- Each `Element` receives the metric name and the `PlotMetrics` instance as arguments — elements hold no permanent reference to `PlotMetrics`.
- `PlotMetrics` holds only high-level shared layout data that multiple elements need. Element-specific config (e.g. title padding, tick length) lives as attributes on the element itself. `PlotTheme` holds colors and fonts only.

#### List of metrics

- `pos`: The `(X, Y)` position of the `Canvas` on the top-level Pygame screen, in Pygame coordinates.
- `dim`: The `(X, Y)` dimensions of the `Canvas` in Pygame coordinates.
- `axes_xpad`: Horizontal pixel margins around the axes area, as `(left, right)`.
- `axes_ypad`: Vertical pixel margins around the axes area, as `(top, bottom)`.
- `axes_pos`: Computed property — top-left of the axes area in canvas coordinates, derived from `axes_xpad` and `axes_ypad`.
- `axes_dim`: Computed property — size of the axes area, derived from `dim`, `axes_xpad`, and `axes_ypad`.
- `xdom` / `ydom`: The domain of a plot along each axis, in plot coordinates.

### Theming

- Colors and fonts are defined in a `PlotTheme` object attached to the `Canvas`.
- `PlotTheme` holds only shared visual style — colors and fonts. Element-specific sizing and spacing (e.g. `canvas.title.padding`, `canvas.xaxis.tick_length`) are attributes on the element itself.

### Drawing

- Only `PlotRenderer` is responsible for drawing anything to the Pygame screen.
- `PlotRenderer` owns `surface_canvas` and `surface_axes`. On each frame, `surface_axes` is blitted onto `surface_canvas` at `axes_pos`, and `surface_canvas` is then blitted onto the top-level Pygame screen at `pos`.
- Drawing is done in two different coordinate systems:
    - Canvas coordinates: Pygame coordinates relative to the top-left of `surface_canvas`.
    - Graph coordinates: Coordinates relative to the X/Y domains of `Axes`. Used only when drawing plot data onto `surface_axes`.
- `Canvas` creates a `DrawContext` at init, holding references to `PlotRenderer`, `PlotMetrics`, and `PlotTheme`. It is passed as a single argument to all element draw calls: `element.draw(ctx)`.
- `PlotRenderer` exposes two families of drawing methods — one per coordinate system (e.g. `draw_line_canvas` / `draw_line_graph`). Elements access the renderer via `ctx.renderer`, call the appropriate family, and pass raw coordinates; `PlotRenderer` handles conversion and surface selection internally. Elements never call a coordinate conversion function directly.
- Frame render order:
    1. draw grid and plot data onto `surface_axes`.
    2. draw chrome elements (border, ticks, labels, title) onto `surface_canvas`.
    3. blit `surface_axes` onto `surface_canvas`.
    4. draw legend onto `surface_canvas`.
    5. blit `surface_canvas` to screen. This ensures the legend always appears above plot data.

### Adding Data to Plots

- When data is added to a plot, it is stored within that plot object.
- When data is added, the plot fires an `_on_data_added` callback registered by `Canvas.add_plot()`. `Canvas` then calls `_check_domain_expansion(x, y)` and updates `metrics.xdom` / `metrics.ydom` if the new data falls outside the current domain.
- Out-of-bounds data is clipped automatically by `surface_axes`; no per-point bounds checking is required.
- Dynamic plots only need to be updated when their data or metrics change. Otherwise, `surface_canvas` is reblitted as it was in the previous tick.

## Supported Plot Types

The following plot types will be supported:

- Line plot.
- Bar plot.
- Scatter plot.
- 2D array plot (Matplotlib: `imshow`).
