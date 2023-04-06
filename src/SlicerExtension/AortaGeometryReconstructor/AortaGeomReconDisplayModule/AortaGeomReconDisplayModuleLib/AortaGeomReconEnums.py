from enum import Enum


class SegmentDirection(Enum):
    """Enum type describing the segmentation direction.
    Superior is where the human head is located.
    Inferior is where the human feet is located.
    """
    Superior_to_Inferior = 1
    Inferior_to_Superior = 2


class SegmentType(Enum):
    """Enum type describing the segmentation phase,
    this will be used in the algorithm to run different codes.
    """
    descending_aorta = 1
    ascending_aorta = 2

    def __eq__(self, other):
        """Overrides the default implementation"""
        return self.value == other.value

    def __format__(self, obj):
        return "%s segmentation" % (self._name_.replace("_", " "))


class PixelValue(Enum):
    """Enum type describing the values of the pixel in the image.
    """
    white_pixel = 1
    black_pixel = 0
