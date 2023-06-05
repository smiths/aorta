from enum import Enum


class SegmentDirection(Enum):
    """Enum type describing the segmentation direction.
    Superior is where the human head is located.
    Inferior is where the human feet is located.
    """
    Superior_to_Inferior = 1
    Inferior_to_Superior = 2


class PixelValue(Enum):
    """Enum type describing the values of the pixel in the image.
    """
    white_pixel = 1
    black_pixel = 0
