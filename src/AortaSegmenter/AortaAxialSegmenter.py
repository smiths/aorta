from AortaSegmenter import AortaSegmenter
import abc

class AortaAxialSegmenter(AortaSegmenter):

    def __init__(self, startingSlice, aortaCentre, numSliceSkipping, segmentationFactor,
                 segmentingImage, normalized = False, outputBinary = True):
        self._starting_slice = startingSlice
        self._aorta_centre = aortaCentre
        self._num_slice_skipping = numSliceSkipping
        self._normalized = normalized
        self._is_output_binary = outputBinary
        super().__init__(segmentingImage, segmentationFactor)

    @abc.abstractmethod
    def circle_filter(self):
        pass