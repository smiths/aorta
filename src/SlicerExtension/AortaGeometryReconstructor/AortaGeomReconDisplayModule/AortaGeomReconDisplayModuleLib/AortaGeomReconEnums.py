from enum import Enum


class SegmentDirection(Enum):
    """Enum type describing the segmentation direction.
    Superior is where the human head is located.
    Inferior is where the human feet is located.
    """
    Superior_to_Inferior = 1
    Inferior_to_Superior = 2


class SegmentType(Enum):
    descending_aorta = 1
    ascending_aorta = 2
    sagittal_front = 3
    sagittal = 4

    def is_axial_seg(seg_type):
        """Return True if the segmentation type is
        descending or ascending aorta segmentation, False otherwise.
        """
        return (seg_type.value == SegmentType.descending_aorta.value
                or seg_type.value == SegmentType.ascending_aorta.value)

    def is_sagittal_seg(seg_type):
        return (seg_type.value == SegmentType.sagittal_front.value
                or seg_type.value == SegmentType.sagittal.value)

    def __eq__(self, other):
        """Overrides the default implementation"""
        return self.value == other.value

    def __format__(self, obj):
        return "%s segmentation" % (self._name_.replace("_", " "))


class PixelValue(Enum):
    white_pixel = 1
    black_pixel = 0
