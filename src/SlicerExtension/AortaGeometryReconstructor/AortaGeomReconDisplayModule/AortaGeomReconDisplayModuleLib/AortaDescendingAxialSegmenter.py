import os
import sys

import SimpleITK as sitk
import numpy as np
project_path = os.path.abspath('.')
AGR_module_path = os.path.join(project_path, "src/SlicerExtension/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeometryReconstructor/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeomReconDisplayModule")
sys.path.insert(0, AGR_module_path)

from AortaGeomReconDisplayModuleLib.AortaAxialSegmenter import AortaAxialSegmenter # noqa
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import SegmentDirection as SegDir # noqa
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import SegmentType as SegType # noqa


class AortaDescendingAxialSegmenter(AortaAxialSegmenter):

    def __init__(self, starting_slice, aorta_centre, num_slice_skipping,
                 qualified_slice_factor, cropped_image):
        super().__init__(starting_slice=starting_slice,
                         aorta_centre=aorta_centre,
                         num_slice_skipping=num_slice_skipping,
                         qualified_slice_factor=qualified_slice_factor,
                         cropped_image=cropped_image)

    def __prepare_seed(self):
        """Get a seed from the original image. We will add extra space
        and use it to get the labeled image statistics.
        """
        seg_2d = sitk.Image(self._cur_img_slice.GetSize(), sitk.sitkUInt8)
        seg_2d.CopyInformation(self._cur_img_slice)
        # add original seed and additional seeds three pixels apart
        spacing = 3
        for j in range(-1, 2):
            one = self._prev_centre[0] + spacing*j
            seg_2d[(one, self._prev_centre[1])] = 1
        seg_2d = sitk.BinaryDilate(seg_2d, [3] * 2)
        return seg_2d

    def __get_label_statistics(self):
        """From the labeled image we can derive descriptive intensity.

        Returns:
            numpy.ndarray: labeled statistics of the original image.
        """
        seg_2d = self.__prepare_seed()
        # determine threshold values based on seed location
        factor = 3.5
        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(self._cur_img_slice, seg_2d)
        lower_threshold = stats.GetMean(1)-factor*stats.GetSigma(1)
        upper_threshold = stats.GetMean(1)+factor*stats.GetSigma(1)
        # use filter to apply threshold to image
        init_ls = sitk.SignedMaurerDistanceMap(
            seg_2d, insideIsPositive=True, useImageSpacing=True)

        # segment the aorta using the seed values and threshold values
        self._segment_filter.SetLowerThreshold(lower_threshold)
        self._segment_filter.SetUpperThreshold(upper_threshold)

        ls = self._segment_filter.Execute(
            init_ls, sitk.Cast(self._cur_img_slice, sitk.sitkFloat32))
        return ls

    def __count_pixel(self, label_stats):
        """Use label statistics to calculate the number of counted pixels.

        Returns:
            numpy.ndarray: A new slice where the labeled statistic of the seed image is greater than 1

            int: The total number of the counted X coordinates

            tupple: The new derived centre calculated by the mean of counted X coordinates and Y coordinates
        """ # noqa
        # assign segmentation to fully_seg_slice
        new_slice = label_stats > 0
        # get array from segmentation
        nda = sitk.GetArrayFromImage(new_slice)
        # calculate average x and average y values,
        # to get the new centre value
        list_x, list_y = np.where(nda == 1)
        new_centre = (int(np.average(list_y)), int(np.average(list_x)))
        total_coord = len(list_x)
        return new_slice, total_coord, new_centre

    def __is_new_centre_qualified(self, total_coord):
        """Determine whether the size of this slice "qualifies" it
        to be accurate

        Returns:
            Boolean
        """
        cmp_prev_size = bool(total_coord < 2*self._previous_size)
        if self._seg_dir == SegDir.Superior_to_Inferior:
            slicer_larger_than = bool(
                total_coord >
                (self._original_size/self.qualified_slice_factor)
            )
            cmp_original_size = bool(
                total_coord <
                (self._original_size*self.qualified_slice_factor)
            )
        else:
            slicer_larger_than = bool(
                total_coord >
                (self._previous_size/self.qualified_slice_factor)
            )
            cmp_original_size = bool(
                total_coord <
                (self._original_size*(self.qualified_slice_factor+0.3))
            )
        return cmp_prev_size and slicer_larger_than and cmp_original_size

    def segmentation(self):
        """From the starting slice to the superior or the inferior,
        use label statistics to see if a circle can be segmented.
        """
        counter = 0
        for sliceNum in range(self._start, self._end, self._step):
            self._cur_img_slice = self._cropped_image[:, :, sliceNum]
            label_stats = self.__get_label_statistics()
            new_slice, total_coord, centre = self.__count_pixel(label_stats)
            if self.__is_new_centre_qualified(total_coord):
                counter = 0
                self._processing_image[:, :, sliceNum] = new_slice
                self._prev_centre = centre
            else:
                counter += 1
                self._skipped_slices.append(sliceNum)
                if (counter >= self._num_slice_skipping):
                    self._skipped_slices = self._skipped_slices[
                        ::-self._num_slice_skipping]
                    break
                total_coord = self._previous_size
            self._previous_size = total_coord

    def begin_segmentation(self):
        # Descending Aorta Segmentation
        self._segment_filter = sitk.ThresholdSegmentationLevelSetImageFilter()
        self._segment_filter.SetMaximumRMSError(0.02)
        self._segment_filter.SetNumberOfIterations(1000)
        self._segment_filter.SetCurvatureScaling(.5)
        self._segment_filter.SetPropagationScaling(1)
        self._segment_filter.ReverseExpansionDirectionOn()
        self._skipped_slices = []
        self._processing_image = sitk.Image(
            self._cropped_image.GetSize(), sitk.sitkUInt8)
        self._processing_image.CopyInformation(self._cropped_image)
        self._start = self._starting_slice
        self._prev_centre = self._aorta_centre

        # Initialize parameters for superior to inferior segmentation
        slice_num = self._starting_slice
        self._cur_img_slice = self._cropped_image[:, :, slice_num]
        label_stats = self.__get_label_statistics()
        new_slice, total_coord, centre = self.__count_pixel(label_stats)
        self._original_size = total_coord
        self._previous_size = total_coord
        self._processing_image[:, :, slice_num] = new_slice
        self._skipped_counter = 0
        self._end = -1
        self._step = -1
        self._seg_dir = SegDir.Superior_to_Inferior
        print("Descending aorta segmentation - top to bottom started")
        self.segmentation()
        print("Descending aorta segmentation - top to bottom finished")

        # Initialize parameters for inferior to superior segmentation
        self._start = self._starting_slice+1
        self._end = self._cropped_image.GetDepth()
        self._previous_size = self._original_size
        self._prev_centre = self._aorta_centre
        self._step = 1
        self._seg_dir = SegDir.Inferior_to_Superior
        print("Descending aorta segmentation - bottom to top started")
        self.segmentation()
        print("Descending aorta segmentation - bottom to top finished")

        # Fill in missing slices of descending aorta
        for index in range(len(self._skipped_slices)):
            # ensure there is at least one slice
            # before and after the skipped slice
            slice_num = self._skipped_slices[index]
            if (slice_num > 0 and slice_num <
                    self._cropped_image.GetDepth() - 1):
                next_index = index + 1

                # if there are two skipped slices in a row,
                # take the overlap of the segmentations
                # before and after those two. otherwise just take the
                # overlap of the segmentations around the skipped slice
                if (len(self._skipped_slices) > next_index):
                    next_slice = self._skipped_slices[next_index]

                    if (next_slice == slice_num + 1 and next_slice
                            < self._cropped_image.GetDepth() - 1):
                        self._processing_image[:, :, slice_num] = (
                            self._processing_image[:, :, slice_num - 1]
                            + self._processing_image[:, :, next_slice + 1] > 1
                        )
                        self._processing_image[:, :, next_slice] = \
                            self._processing_image[:, :, slice_num]
                    else:
                        self._processing_image[:, :, slice_num] = (
                            self._processing_image[:, :, slice_num - 1]
                            + self._processing_image[:, :, slice_num + 1] > 1
                        )
                else:
                    self._processing_image[:, :, slice_num] = (
                        self._processing_image[:, :, slice_num - 1]
                        + self._processing_image[:, :, slice_num + 1] > 1)
