from abc import ABC, abstractmethod
from typing import Callable
import numpy as np
import numpy.typing as npt

from .drawing import DrawContext, PlotMetrics


class PlotType(ABC):
    """
    Abstract base class for all plot data elements (LinePlot, BarPlot, etc.).

    PlotType is intentionally independent of the Element ABC to avoid a
    circular import between elements.py and plot_types.py. Concrete subclasses
    implement the same draw / on_metrics_changed interface as Element.

    Responsibilities:
    - Draw plot data onto surface_axes in graph coordinates.
    - Expose name and color for the Legend.
    - Fire _on_data_added (set by Canvas.add_plot) when new data is added,
      so Canvas can check whether the domain needs expanding.
    """

    def __init__(self, color: tuple[int, int, int], label: str):
        self.color = color
        self.label = label
        self._on_data_added: Callable[[npt.NDArray[np.float64]], None] | None = None
        
        # Disables drawing and _on_data_added callback
        self.enabled = True

    @abstractmethod
    def draw(self, ctx: DrawContext): ...

    @abstractmethod
    def on_metrics_changed(self, metric_name: str | None, metrics: PlotMetrics): ...


class ScatterPlot(PlotType):

    def __init__(self, color: tuple[int, int, int], label: str, radius: int = 3, alpha: float = 1):
        super().__init__(color, label)
        self.radius = radius
        self.alpha = alpha
        self.data = np.empty((0, 2), dtype=np.float64)

    def add_data(self, points: npt.ArrayLike, check_domain: bool | None = None):
        """Add data. Check_domain overrides self.enabled for domain checks."""
        points = np.reshape(points, (-1, 2))
        self.data = np.vstack([self.data, points])
        
        if self._on_data_added and check_domain is None and self.enabled:
            self._on_data_added(points)
            
        elif self._on_data_added and check_domain:
            self._on_data_added(points)

    def draw(self, ctx: DrawContext):
        if not self.enabled or self.data.shape[0] == 0:
            return
    
        for xy in self.data:
            ctx.renderer.point(ctx.metrics, xy, self.color, self.radius, self.alpha)

    def on_metrics_changed(self, metric_name: str | None, metrics: PlotMetrics):
        pass


class LinePlot(PlotType):

    def __init__(self, color: tuple[int, int, int], label: str, width: int = 1):
        super().__init__(color, label)
        self.data = np.empty((0, 2), dtype=np.float64)

    def add_data(self, points: npt.ArrayLike, check_domain: bool | None = None):
        points = np.reshape(points, (-1, 2))
        self.data = np.vstack([self.data, points])

        if self._on_data_added and check_domain is None and self.enabled:
            self._on_data_added(points)
        elif self._on_data_added and check_domain:
            self._on_data_added(points)

    def draw(self, ctx: DrawContext):
        if not self.enabled or self.data.shape[0] < 2:
            return
        ctx.renderer.polyline(ctx.metrics, self.data, self.color)

    def on_metrics_changed(self, metric_name: str | None, metrics: PlotMetrics):
        pass

