import abc


class AortaSegmenterBase():

    def __init__(self, cropped_image, segmentation_factor=2.2):
        self._segmentation_factor = segmentation_factor
        self._cropped_image = cropped_image

    @property
    def segmentation_factor(self):
        return self._segmentation_factor

    @property
    def cropped_image(self):
        return self._cropped_image

    @segmentation_factor.setter
    def segmentation_factor(self, segmentation_factor):
        self._segmentation_factor = segmentation_factor

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
