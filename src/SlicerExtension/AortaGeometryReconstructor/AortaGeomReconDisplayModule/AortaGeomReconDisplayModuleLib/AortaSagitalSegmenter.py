import SimpleITK as sitk
import numpy as np


class AortaSagitalSegmenter():
    """This class performs Aorta Sagittal segmentation"""

    def __init__(self, qualified_coef, processing_image, cropped_image):
        self._processing_image = processing_image
        self._cropped_image = cropped_image
        self._qualified_coef = qualified_coef

    def __segment_sag(self, sliceNum, factor, size_factor,
                      current_size, imgSlice, axial_seg, seg_type):
        # determine threshold values based on seed location
        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(imgSlice, axial_seg)

        lower_threshold = stats.GetMean(1) - factor*stats.GetSigma(1)
        upper_threshold = stats.GetMean(1) + factor*stats.GetSigma(1)

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
        # otherwise change the factor and re-run this function
        if (new_size < current_size * size_factor):
            return new_seg
        elif (factor > 0.5):
            return self.__segment_sag(
                sliceNum, factor - 0.5, size_factor, current_size, imgSlice,
                axial_seg, seg_type)

    def begin_segmentation(self):
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
            current_size = np.count_nonzero(
                self._processing_image[sliceNum, :, :])
            if (current_size > self._base_pixel_value):
                # Recursive function
                imgSlice = self._cropped_image[sliceNum, :, :]
                axial_seg = self._processing_image[sliceNum, :, :]
                self._processing_image[sliceNum, :, :] = self.__segment_sag(
                    sliceNum, self._qualified_coef, 1.4,
                    current_size, imgSlice, axial_seg, None)
        print("Sagittal segmentation finished")

        # goes through all the frontal slices and fills in any gaps
        # from the axial/sagittal segmentations
        print("Sagittal segmentation - frontally started")
        for sliceNum in range(1, self._cropped_image.GetHeight()):
            # only do segmentation if there is something on the slice.
            # This prevents the function from segmenting the whole thing
            current_size = np.count_nonzero(
                self._processing_image[:, sliceNum, :])
            if (current_size > self._base_pixel_value):
                imgSlice = self._cropped_image[:, sliceNum, :]
                axial_seg = self._processing_image[:, sliceNum, :]
                self._processing_image[:, sliceNum, :] = self.__segment_sag(
                    sliceNum, self._qualified_coef, 1.1, current_size,
                    imgSlice, axial_seg, "frontally")
        print("Sagittal segmentation - frontally finished")
