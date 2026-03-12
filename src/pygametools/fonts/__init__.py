import io
import pygame
from importlib.resources import files


def load_font(filename: str, size: int) -> pygame.font.Font:
    """
    Load a font from the pygametools.fonts package directory.

    Args:
        filename: Font filename.
        size: Font size in points.
    """ 
    data = files("pygametools.fonts").joinpath(filename).read_bytes()
    return pygame.font.Font(io.BytesIO(data), size)
 
