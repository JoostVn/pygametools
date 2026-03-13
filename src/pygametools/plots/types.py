from typing import Union
import numpy as np
import numpy.typing as npt

# Simple (x, y) input for metric parameters
# Can be direct coordinates as well as dimensions, domains, and padding.
MetricCoordinatePair = tuple[int, int]
MetricCoordinateArray = npt.NDArray[np.int_]
MetricCoordinates = Union[MetricCoordinatePair, MetricCoordinateArray]

# Domain range (min, max) for x or y axis.
Domain = tuple[float, float]

# Bulk coordinate input for plotting data.
XYPlotDataPoint = tuple[int | float, int | float]
XYPlotDataBatch = npt.NDArray[np.float64 | np.int_]
XYPlotData = XYPlotDataPoint | XYPlotDataBatch


 