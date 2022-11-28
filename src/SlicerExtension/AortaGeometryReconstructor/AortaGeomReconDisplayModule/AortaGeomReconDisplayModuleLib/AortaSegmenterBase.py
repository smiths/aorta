import abc


class AortaSegmenterBase():

    def __init__(self, segmentingImage, segmentationFactor=2.2):
        self._segmentation_factor = segmentationFactor
        self._segmenting_image = segmentingImage

    @property
    def segmentation_factor(self):
        return self._segmentation_factor

    @property
    def segmenting_image(self):
        return self._segmenting_image

    @segmentation_factor.setter
    def segmentation_factor(self, segmentationFactor):
        self._segmentation_factor = segmentationFactor

    @property
    def segmented_image(self):
        return self._segmented_image

    @segmenting_image.setter
    def segmenting_image(self, image):
        self._segmenting_image = image

    @abc.abstractmethod
    def begin_segmentation(self):
        # process segmenting image and assign the result to _segmented_image
        pass
