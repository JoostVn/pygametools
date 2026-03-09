from typing import Union
import numpy as np
import numpy.typing as npt


# Simple (x, y) input for metric parameters
# Can be direct coordinates as well as dimensions, domains, and padding.
CoordinatePair = tuple[int, int]

# Domain range (min, max) for x or y axis.
# TODO: add numpy array? Domains are converted to arrays internally 
Domain = tuple[float, float]

# Bulk coordinate input for plotting data.
CoordinateArray = npt.NDArray[np.float64]

# Union of the above for flexible input.
Coordinates = Union[CoordinatePair, CoordinateArray]


 