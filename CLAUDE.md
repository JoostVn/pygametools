# Plots

The `plots` module is a redo of the original `plotting` module that supports both static and dynamic plotting (bar plots, line plots, etc.) in Pygame. The main use of the `plots` module is visualizing statistics on simulations in real-time. Some example use cases:

- Plotting the position of a one-dimensional random walk over time.
- Plotting the scores of different players in a game.
- Plotting the genomes of a whole population in a genetic algorithm as a grayscale 2D array.
- Plotting the accuracy of a neural network as it is optimized over different iterations.

## TODO / implementation

All points apply only to the `src\pygametools\plots` module. The current module will require a substantial refactor after which new features will be added. The steps to achieve this are listed below.

Any change in `src\pygametools\plots` should also be reflected in the test file `examples\plots_dev.py`.

Some general formatting rules to keep in mind during the refactor:

- Proper typehinting using numpy.typing and the `plots\types.py` module
- Make sure that private attributes and methods are prefixed by an underscore.
- Implement getters and setters for attributes with additional logic (instead of dedicated methods like `set_num_ticks`).

1. `DrawContext` class and module
    - ✅ Implement `DrawContext` as a simple dataclass holding `renderer: PlotRenderer`, `metrics: PlotMetrics`, `theme: PlotTheme`.
    - ✅ Move DrawContext, PlotRenderer, PlotMetrics, PlotTheme to their own module (drawing.py).
    - ✅ Import all classes in `elements.py`
    - ✅ Instantiate `DrawContext` once in `Canvas.__init__`.

2. Metrics and elements
    - ✅ Register all elements with `Canvas` (not `PlotMetrics`) at construction time.
    - ✅ Replace the hardcoded draw list in `Canvas.draw()` with a proper element registry (`_elements: list[Element]`).
    - ✅ Add `on_metrics_changed(metric_name: str | None, metrics: PlotMetrics)` to the `Element` abstract base class.
    - ✅ Remove all `Element` references from `PlotMetrics`; replace with a single `_on_change: Callable[[str], None]` callback to `Canvas`.
    - ✅ Add `Canvas._on_metrics_changed(metric_name: str | None)` as the mediator method that propagates changes to all registered elements.
    - ✅ Draw functions receive `DrawContext`; `on_metrics_changed` receives `metric_name` and `metrics`.
    - Expose all metrics on `Canvas` as pass-through properties, making `Canvas` the sole public API for metric access:
        - Settable properties with validation and `_on_metrics_changed` call: `pos`, `dim`, `xdom`, `ydom`, `axes_xpad`, `axes_ypad`.
        - Read-only derived properties on `Canvas` (only those useful externally): `axes_pos`, `axes_dim`, `xdom_span`, `ydom_span`.
        - Rename `ctx` → `_ctx` to prevent external code from bypassing Canvas.
        - Remove the `_on_change` callback from `PlotMetrics`; Canvas setters write directly to `PlotMetrics` private attributes and call `_on_metrics_changed` themselves. Validation and numpy conversion move to Canvas setters.
        - `PlotMetrics` stores private attributes (`_xdom`, `_dim`, etc.) with public **getters only** (no public setters) so elements can read but not write. Derived computed properties (`axes_pos`, `axes_dim`, etc.) stay on `PlotMetrics` for internal element use.
        - Elements are read-only consumers of `PlotMetrics` — they receive `metrics` as a method argument and only read from it. This is enforced by convention; `_ctx` being private ensures external code cannot reach `metrics` at all.
    - Remove `Axis._metrics` — the only stored reference to `PlotMetrics` still left in an element. `_dom()` and `_span()` should be computed from the `metrics` argument passed to `on_metrics_changed`, not a cached copy.
    - Replace `set_tick_num` / `set_tick_pos` dedicated methods with `num_ticks` / `tick_positions` property setters (see general formatting rules).

3. `PlotRenderer` refactor
    - ✅ Remove `parent_canvas` reference; `PlotRenderer.__init__` takes `dim` and `axes_dim` directly. Canvas calls `pr.resize(dim, axes_dim)` when metrics change.
    - ✅ Surface selection is internal to `PlotRenderer` (via `get_surface_pos` and `on_axes` flag).
    - Replace the `on_axes: bool` flag pattern with two explicit draw method families: `draw_[shape]_canvas(...)` for canvas coordinates and `draw_[shape]_graph(...)` for graph coordinates. Remove `get_surface_pos`.
    - Extract coordinate conversion into `_graph_to_canvas(pos, metrics) -> CoordinatePair` as a private method on `PlotRenderer`.
    - Enforce strict input types: `CoordinatePair` for individual positions, `CoordinateArray` for bulk data. No implicit conversion. 
    - Decide whether to add numpy array to `Domain` in `types.py`.
    - Make `metrics` the second positional argument (after `self`) in all draw methods for consistency.

4. Add more features to the existing elements:
    - Text labels for ticks.
    - Axis labels (single descriptive string per axis, X centered below tick labels, Y rotated 90°).

5. Add `LinePlot`, `BarPlot`, and `ScatterPlot` plot types.

6. Implement domain auto-expansion.
    - In `Canvas.add_plot(plot)`, register an `_on_data_added` callback on the plot.
    - Implement `Canvas._check_domain_expansion(x, y)` that updates `metrics.xdom` / `metrics.ydom` when new data falls outside the current domain.

7. Complete `Legend` element (stub exists).

8. Implement `Grid` element.

9. Improve the test/example script `examples\plots_dev.py`:
    - GUI sliders for plot metrics for easy testing.
    - Dynamic and static data examples:
        - Random walk (dynamic line)
        - Double dice throw (dynamic bar)
        - GIF (dynamic array)
        - Test image (static array)
        - Normal distribution draws (dynamic scatter)

10. Make sure docstrings of methods and classes reflect key design decisions (only when not obvious from the code).

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
- `PlotMetrics` → nothing (plain data container; no back-reference to `Canvas`)
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

- The dimensions and domains of a `Canvas` object are stored in `PlotMetrics`. `Canvas` is the sole writer: its property setters validate input, write directly to `PlotMetrics` private attributes, and call `Canvas._on_metrics_changed` themselves. `PlotMetrics` has no `_on_change` callback and no public setters.
- `Canvas` acts as the mediator: `_on_metrics_changed` calls `on_metrics_changed(metric_name, metrics)` on all registered `Element` instances so they can recompute their layout.
- `PlotMetrics` exposes public **getters only** so elements can read metrics but not write to them. Derived computed properties (`axes_pos`, `axes_dim`, etc.) also live on `PlotMetrics` for internal element use.
- `Canvas` additionally exposes a subset of derived properties as read-only pass-throughs (`axes_pos`, `axes_dim`, `xdom_span`, `ydom_span`) for external use. `_ctx` is private, so external code cannot bypass `Canvas` to reach `PlotMetrics` directly.
- Each `Element` receives the metric name and the `PlotMetrics` instance as arguments and only reads from it — elements hold no permanent reference to `PlotMetrics`.
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
- When data is added, the plot fires an `_on_data_added` callback registered by `Canvas.add_plot()`. `Canvas` then calls `_check_domain_expansion(x, y)` and updates `canvas.xdom` / `canvas.ydom` via its own property setters if the new data falls outside the current domain.
- Out-of-bounds data is clipped automatically by `surface_axes`; no per-point bounds checking is required.
- Dynamic plots only need to be updated when their data or metrics change. Otherwise, `surface_canvas` is reblitted as it was in the previous tick.

## Public API Examples

```python
# Create a canvas (Application must be initialised first)
canvas = Canvas(pos=(10, 10), dim=(580, 380), xdom=(0, 10), ydom=(-5, 10), title="My Plot")

# Set metrics — always through Canvas
canvas.xdom = (0, 20)
canvas.ydom = (-1, 1)
canvas.dim = (400, 300)
canvas.axes_xpad = (50, 10)

# Read derived properties — also through Canvas
print(canvas.axes_dim)    # size of the axes area in pixels
print(canvas.axes_pos)    # top-left of axes area in canvas coordinates
print(canvas.xdom_span)   # 20.0  (xdom[1] - xdom[0])
print(canvas.ydom_span)   # 2.0

# Add a plot and data
line = LinePlot(color=(255, 80, 80), name="signal")
canvas.add_plot(line)
line.add_data(...)

# Draw each frame
canvas.draw(screen)

# Element-specific config lives on the element, not on Canvas
canvas.title.padding = 12
canvas.axisx.tick_length = 6
canvas.axisx.num_ticks = 5
```

## Supported Plot Types

The following plot types will be supported:

- Line plot.
- Bar plot.
- Scatter plot.
- 2D array plot (Matplotlib: `imshow`).
