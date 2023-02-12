import abc


class AortaSegmenterBase():

    def __init__(self, cropped_image, qualified_coef=2.2):
        self._qualified_coef = qualified_coef
        self._cropped_image = cropped_image

    @property
    def qualified_coef(self):
        return self._qualified_slice_factor

    @property
    def cropped_image(self):
        return self._cropped_image

    @qualified_coef.setter
    def qualified_coef(self, qualified_coef):
        self._qualified_slice_factor = qualified_coef

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
