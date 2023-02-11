import abc


class AortaSegmenterBase():

    def __init__(self, cropped_image, qualified_slice_factor=2.2):
        self._qualified_slice_factor = qualified_slice_factor
        self._cropped_image = cropped_image

    @property
    def qualified_slice_factor(self):
        return self._qualified_slice_factor

    @property
    def cropped_image(self):
        return self._cropped_image

    @qualified_slice_factor.setter
    def qualified_slice_factor(self, qualified_slice_factor):
        self._qualified_slice_factor = qualified_slice_factor

    @property
    def processing_image(self):
        return self._processing_image

    @cropped_image.setter
    def cropped_image(self, image):
        self._cropped_image = image

    @abc.abstractmethod
    def begin_segmentation(self):
        # process segmenting image and assign the result to _segmented_image
        pass
