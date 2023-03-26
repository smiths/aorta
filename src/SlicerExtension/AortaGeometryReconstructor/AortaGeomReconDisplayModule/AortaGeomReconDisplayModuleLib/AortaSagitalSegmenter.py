import SimpleITK as sitk
import numpy as np


class AortaSagitalSegmenter():
    """This class performs Aorta segmentation through sagittal plane.

    Attributes:
        qualified_coef (float): This coefficient controls the lower and upper threshold of the number of white pixels to determine whether to accept each segmented slice or not.

        cropped_image (SITK::image): The original image that the user has only perform cropping.

        processing_image (SITK::image): The image that we are performing segmentation. This image should already performed descending and ascending aorta segmentation.

    """ # noqa

    def __init__(self, qualified_coef, processing_image, cropped_image):
        self._processing_image = processing_image
        self._cropped_image = cropped_image
        self._qualified_coef = qualified_coef

    def __segment_sag(self, threshold_coef, qualified_coef, imgSlice,
                      axial_seg, seg_type):
        """This function is the main segmentation algorithm implementation.
        The algorithm is very similar to the algorithm used in axial segmentation.
        First we get label stats with the existing segmented slice, and get the mean of the intensity values to calculate the threshold.
        Finally we use these threshold values to perform segmentation.

        Attributes:
            threshold_coef (float): The coefficient to control the range of threshold to be used in segmentation.

            imgSlice (SITK::image): The 2D image of the current processing slice.

            axial_seg (SITK::image): The 2D segmentation result from descending and ascending algorithm.

            seg_type (String): Segmentation type, sagitally or frontally.

        """ # noqa
        # determine threshold values based on seed location
        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(imgSlice, axial_seg)

        lower_threshold = stats.GetMean(1) - threshold_coef*stats.GetSigma(1)
        upper_threshold = stats.GetMean(1) + threshold_coef*stats.GetSigma(1)

        # use filter to apply threshold to image
        init_ls = sitk.SignedMaurerDistanceMap(
            axial_seg, insideIsPositive=True, useImageSpacing=True)

        # segment the aorta using the seed values and threshold values
        self._segment_filter.SetLowerThreshold(lower_threshold)
        self._segment_filter.SetUpperThreshold(upper_threshold)

        ls = self._segment_filter.Execute(
            init_ls, sitk.Cast(imgSlice, sitk.sitkFloat32))

        # set segmentation to both the sagittal segmentation
        # and the original axial segmentation
        sag_seg = ls > 0
        new_seg = axial_seg | sag_seg

        if seg_type != "frontally":
            new_size = np.count_nonzero(new_seg)
        else:
            new_size = np.count_nonzero(sag_seg)

        # make sure there is no drastic size difference.
        # otherwise change the threshold_coef and re-run this function
        if (new_size < self._current_size * qualified_coef):
            return new_seg
        elif (threshold_coef > 0.5):
            return self.__segment_sag(
                threshold_coef - 0.5, qualified_coef, imgSlice,
                axial_seg, seg_type)

    def begin_segmentation(self):
        """The main loop of the segmentation algorithm.
        For each sagittal slice, get the segmented result's number of pixel, compared it to our base_pixel_value.
        If the number is larger than the base_pixel_value,
        this implies that there are some areas of interest that we can smooth with sagittal segmentation.

        """ # noqa
        self._segment_filter = sitk.ThresholdSegmentationLevelSetImageFilter()
        self._segment_filter.SetMaximumRMSError(0.02)
        self._segment_filter.SetNumberOfIterations(1000)
        self._segment_filter.SetCurvatureScaling(.5)
        self._segment_filter.SetPropagationScaling(1)
        self._segment_filter.ReverseExpansionDirectionOn()

        self._total_pixels = self._processing_image.GetHeight() \
            * self._processing_image.GetDepth()

        # minimum number of pixels on a slice for us
        # to run the sagittal function
        self._base_pixel_value = self._total_pixels / 5000

        # goes through all the sagittal slices and fills in any gaps from
        # the-axial segmentation
        print("Sagital segmentation started")
        for sliceNum in range(1, self._cropped_image.GetWidth()):
            # only do segmentation if there is something on the slice.
            # This prevents the function from segmenting the whole thing
            self._current_size = np.count_nonzero(
                self._processing_image[sliceNum, :, :])
            if (self._current_size > self._base_pixel_value):
                # Recursive function
                imgSlice = self._cropped_image[sliceNum, :, :]
                axial_seg = self._processing_image[sliceNum, :, :]
                self._processing_image[sliceNum, :, :] = self.__segment_sag(
                    self._qualified_coef, 1.4, imgSlice, axial_seg, None)
        print("Sagittal segmentation finished")

        # goes through all the frontal slices and fills in any gaps
        # from the axial/sagittal segmentations
        print("Sagittal segmentation - frontally started")
        for sliceNum in range(1, self._cropped_image.GetHeight()):
            # only do segmentation if there is something on the slice.
            # This prevents the function from segmenting the whole thing
            self._current_size = np.count_nonzero(
                self._processing_image[:, sliceNum, :])
            if (self._current_size > self._base_pixel_value):
                imgSlice = self._cropped_image[:, sliceNum, :]
                axial_seg = self._processing_image[:, sliceNum, :]
                self._processing_image[:, sliceNum, :] = self.__segment_sag(
                    self._qualified_coef, 1.1,
                    imgSlice, axial_seg, "frontally")
        print("Sagittal segmentation - frontally finished")
