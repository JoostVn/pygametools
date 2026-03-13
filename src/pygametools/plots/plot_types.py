from abc import ABC, abstractmethod
from typing import Callable
import numpy as np

from pygametools.plots.types import XYPlotData
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

    def __init__(self, color: tuple, label: str):
        self.color = color
        self.label = label
        self._on_data_added: Callable | None = None

    @abstractmethod
    def draw(self, ctx: DrawContext): ...

    @abstractmethod
    def on_metrics_changed(self, metric_name: str | None, metrics: PlotMetrics): ...


class ScatterPlot(PlotType):

    def __init__(self, color: tuple, label: str, radius: int = 3, alpha: float = 1):
        super().__init__(color, label)
        self.radius = radius
        self.alpha = alpha
        self.data = np.empty((0,2))

    def add_data(self, points: XYPlotData, check_domain: bool = False):
        points = np.reshape(points, (-1, 2))
        self.data = np.vstack([self.data, points])
        
        if self._on_data_added and check_domain:
            self._on_data_added(points)

    def draw(self, ctx: DrawContext):
        if self.data.shape[0] == 0:
            return
    
        for xy in self.data:
            ctx.renderer.point(xy, self.color, ctx.metrics, self.radius, self.alpha)

    def on_metrics_changed(self, metric_name: str | None, metrics: PlotMetrics):
        pass
