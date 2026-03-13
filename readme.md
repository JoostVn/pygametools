# pygametools

A collection of tools for building Pygame applications, including color utilities, a GUI system, and a plotting module.

## Modules

### `color`
Provides color constants and color generation utilities.

- **`Color`** — class with predefined RGB color constants (greys, blues, greens, reds, yellows, oranges, purples, cyans) and static methods:
  - `Color.random_vibrant()` — returns a random high-contrast RGB color
  - `Color.random_dull()` — returns a random muted RGB color
  - `Color.random_different(n)` — returns `n` colors with maximized mutual difference
- **`ColorGradient`** — interpolates between two colors based on a 0–1 value

### `gui`
Provides building blocks for Pygame applications with GUI elements.

- **`Application`** — abstract base class for a Pygame application. Handles the main loop, event processing, ticking, zoom/pan, and theming. Subclass and implement `update()` and `draw()`.
- **`Container`** — manages a list of GUI elements, ensuring only one is active at a time.
- **`Ticker`** — controls tick rate and tracks computational load statistics.
- Themes are loaded from JSON files (built-in options: `default`, `default_dark`, `default_light`, `darkblue`, `lightblue`).

### `plots` *(in development)*
A new plotting module built from scratch. Renders plots directly onto a Pygame surface.

- **`Canvas`** — top-level container for a plot. Holds all elements and manages metrics (position, dimensions, domains). Usage:
  ```python
  canvas = Canvas(pos=(50, 50), dim=(400, 300), xdom=(0, 10), ydom=(0, 100))
  canvas.draw(screen)
  ```
- **`PlotMetrics`** — single source of truth for position, dimensions, and x/y domains. Notifies registered elements when any metric changes.
- **`PlotTheme`** — controls colors and fonts for all plot elements.
- **`PlotDraw`** — handles drawing primitives (lines, rectangles, text, vectors) in either canvas or axes coordinates.
- **`Axes`** — the inner rectangle where data is plotted.
- **`Axis`** — x or y axis with configurable ticks and labels.
- **`Title`** — plot title, centered above the axes.


## Used fonts

Inter: https://fonts.google.com/specimen/Inter
JetBrains Mono: https://www.jetbrains.com/lp/mono/
