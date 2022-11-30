import abc
import numpy as np
import SimpleITK as sitk


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

    """Get cropped and normalized image and stored as self._segmenting_image
    """
    def prepared_segmenting_image(self, image, index, size):
        # crop the image
        crop_filter = sitk.ExtractImageFilter()
        crop_filter.SetIndex(index)
        crop_filter.SetSize(size)

        cropped_image = crop_filter.Execute(image)

        # change intensity range to go from 0-255   +++++++
        cropped_image_255 = sitk.Cast(sitk.RescaleIntensity(image),
                                      sitk.sitkUInt8)

        # ensure that the spacing in the image is correct
        cropped_image.SetOrigin(image.GetOrigin())
        cropped_image.SetSpacing(image.GetSpacing())
        cropped_image.SetDirection(image.GetDirection())

        # Contrast Enhancement
        # Histogram Equalization
        # img_array = sitk.GetArrayFromImage(
        #     (sitk.Cast(sitk.RescaleIntensity(cropped_image), sitk.sitkUInt8))
        # )
        img_array = sitk.GetArrayFromImage(cropped_image)

        # flatten image array and calculate histogram via binning
        histogram_array = np.bincount(img_array.flatten(), minlength=256)

        # normalize image
        num_pixels = np.sum(histogram_array)
        histogram_array = histogram_array/num_pixels

        # normalized cumulative histogram
        chistogram_array = np.cumsum(histogram_array)

        # create pixel mapping lookup table
        transform_map = np.floor(255 * chistogram_array).astype(np.uint8)

        # flatten image array into 1D list
        # so they can be used with the pixel mapping table
        img_list = list(img_array.flatten())

        # transform pixel values to equalize
        eq_img_list = [transform_map[p] for p in img_list]

        # reshape and write back into img_array
        eq_img_array = np.reshape(np.asarray(eq_img_list), img_array.shape)

        # save image
        eq_img = sitk.GetImageFromArray(eq_img_array)
        eq_img.CopyInformation(cropped_image)

        # Median Image Filter
        median = sitk.MedianImageFilter()
        median_img = sitk.Cast(median.Execute(eq_img), sitk.sitkUInt8)

        self._segmenting_image = median_img
        self._segmenting_image_255 = cropped_image_255

    @abc.abstractmethod
    def begin_segmentation(self):
        # process segmenting image and assign the result to _segmented_image
        pass
