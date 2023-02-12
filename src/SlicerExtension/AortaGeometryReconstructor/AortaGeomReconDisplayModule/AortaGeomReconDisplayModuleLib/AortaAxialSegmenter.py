from AortaGeomReconDisplayModuleLib.AortaSegmenterBase \
    import AortaSegmenterBase
import abc


class AortaAxialSegmenter(AortaSegmenterBase):

    def __init__(self, starting_slice, aorta_centre, num_slice_skipping,
                 qualified_slice_factor, cropped_image):
        self._starting_slice = starting_slice
        self._aorta_centre = aorta_centre
        self._num_slice_skipping = num_slice_skipping
        super().__init__(cropped_image, qualified_slice_factor)

    @abc.abstractmethod
    def circle_filter(self):
        pass
