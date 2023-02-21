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
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import SegmentType # noqa
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import PixelValue # noqa


class AortaSegmenter():

    def __init__(
            self, cropped_image, starting_slice, aorta_centre,
            num_slice_skipping, processing_image, seg_type,
            qualified_coef=2.2, filter_factor=3.5
    ):
        self._starting_slice = starting_slice
        self._aorta_centre = aorta_centre
        self._num_slice_skipping = num_slice_skipping
        self._seg_type = seg_type
        if seg_type == SegmentType.sagittal_front:
            self._seg_type = SegmentType.sagittal
        self._processing_image = processing_image
        self._qualified_coef = qualified_coef
        self._filter_factor = filter_factor
        self._cropped_image = cropped_image

    def __is_overlapping(self, img1, i):
        """Compare the current segmented slice with the next two slices,
        return True if any overlaps otherwise False

        Returns:
            Boolean: comparison result
        """ # noqa
        img2 = self._cropped_image[:, :, i]
        overlap = np.count_nonzero(img1 * img2)
        if (overlap <= 0):
            img2 = self._cropped_image[:, :, i + 1]
            overlap = np.count_nonzero(img1 * img2)
        if (overlap <= 0):
            img2 = self._cropped_image[:, :, i + 2]
            overlap = np.count_nonzero(img1 * img2)
        return (overlap > PixelValue.black_pixel.value)

    @property
    def cropped_image(self):
        return self._cropped_image

    @property
    def processing_image(self):
        return self._processing_image

    def begin_segmentation(self):
        # Initializing filter
        rms_error = 0.02
        no_iteration = 600
        curvature_scaling = 0.5
        propagation_scaling = 1
        self._stats_filter = sitk.LabelStatisticsImageFilter()
        self._segment_filter = sitk.ThresholdSegmentationLevelSetImageFilter()
        self._segment_filter.SetMaximumRMSError(rms_error)
        self._segment_filter.SetNumberOfIterations(no_iteration)
        self._segment_filter.SetCurvatureScaling(curvature_scaling)
        self._segment_filter.SetPropagationScaling(propagation_scaling)
        self._segment_filter.ReverseExpansionDirectionOn()
        self._skipped_slices = []

        # Initializing current total pixels
        if not self._processing_image:
            self._processing_image = sitk.Image(
                self._cropped_image.GetSize(), sitk.sitkUInt8)
            self._processing_image.CopyInformation(self._cropped_image)
        if self._seg_type == SegmentType.sagittal:
            self._total_pixels = (
                self._processing_image.GetHeight()
                * self._processing_image.GetDepth()
            )
        else:
            self._total_pixels = (
                self._processing_image.GetWidth()
                * self._processing_image.GetDepth()
            )
        self._seg_dir = None
        self._original_size = None
        self._seeds = None
        max_aorta_slice = 5000
        # minimum number of pixels on a slice for us
        # to run the sagittal function
        self._base_pixel_value = self._total_pixels / max_aorta_slice
        self._is_size_decreasing = False
        if SegmentType.is_axial_seg(self._seg_type):
            # Get more values from the seed slice
            self._start = self._starting_slice - 1
            self._prev_centre = self._aorta_centre
            self._prev_seeds = []
            # Initialize parameters for superior to inferior segmentation
            slice_num = self._starting_slice
            self._cur_img_slice = self._cropped_image[:, :, slice_num]
            label_stats = self.__get_label_statistics()
            new_slice = label_stats > PixelValue.black_pixel.value
            seeds = []
            if self._seg_type == SegmentType.descending_aorta:
                total_coord, centre = self.__count_pixel_des(new_slice)
            else:
                total_coord, centre, seeds = self.__count_pixel_asc(new_slice)
            self._prev_seeds = seeds
            self._original_size = total_coord
            self._previous_size = total_coord
            self._prev_centre = centre
            self._processing_image[:, :, slice_num] = new_slice
            self._skipped_slice_counter = 0
            self._end = -1
            self._step = -1
            self._seg_dir = SegDir.Superior_to_Inferior

            # SEGMENT FROM SEED VALUE TO BOTTOM OF THE AORTA
            print("{} - top to bottom started".format(self._seg_type))
            self.__segmentation()
            print("{} - top to bottom finished".format(self._seg_type))

            self._seg_dir = SegDir.Inferior_to_Superior
            self._start = self._starting_slice + 1
            self._prev_centre = self._aorta_centre
            self._previous_size = self._original_size
            self._end = self._cropped_image.GetDepth()
            self._step = 1
            self._skipped_slice_counter = len(self._skipped_slices)

            print("{} - bottom to top started".format(self._seg_type))
            self.__segmentation()
            print("{} - bottom to top finished".format(self._seg_type))

            if self._seg_type == SegmentType.descending_aorta:
                # Fill in missing slices of descending aorta
                self.__filling_missing_slices()

    def __segmentation(self):
        """From the starting slice to the superior or the inferior,
        use label statistics to see if a circle can be segmented.
        """
        counter = 0
        is_overlapping = False
        for sliceNum in range(self._start, self._end, self._step):
            self._cur_img_slice = self._cropped_image[:, :, sliceNum]
            label_stats = self.__get_label_statistics()
            new_slice = label_stats > PixelValue.black_pixel.value
            if self._seg_type == SegmentType.descending_aorta:
                total_coord, centre = self.__count_pixel_des(new_slice)
                seeds = []
            else:
                total_coord, centre, seeds = self.__count_pixel_asc(new_slice)
                if self._seg_dir == SegDir.Inferior_to_Superior:
                    if total_coord > 2*self._original_size:
                        if (total_coord < self._previous_size):
                            self._is_size_decreasing = True
                            self._qualified_overlap_coef = 1.2
                    is_overlapping = self.__is_overlapping(new_slice, sliceNum)
            if self.__is_new_centre_qualified(total_coord, is_overlapping):
                counter = 0
                if self._seg_type == SegmentType.descending_aorta:
                    self._processing_image[:, :, sliceNum] = new_slice
                else:
                    self._processing_image[:, :, sliceNum] = (
                        new_slice | self._processing_image[:, :, sliceNum]
                    )
                self._prev_centre = centre
                self._prev_seeds = seeds
            else:
                counter += 1
                self._skipped_slices.append(sliceNum)
                if (counter >= self._num_slice_skipping):
                    self._skipped_slices = self._skipped_slices[
                        ::-self._num_slice_skipping]
                    break
                total_coord = self._previous_size
            self._previous_size = total_coord

    def __is_new_centre_qualified(self, total_coord, is_overlapping):
        """Return True if the number of coordiante in the segmented centre is qualified

        Returns:
            Boolean
        """ # noqa
        cmp_prev_size = bool(total_coord < 2*self._previous_size)
        if self._seg_dir == SegDir.Superior_to_Inferior:
            slicer_larger_than = bool(
                total_coord >
                (self._original_size/self._qualified_coef)
            )
            cmp_original_size = bool(
                total_coord <
                (self._original_size*self._qualified_coef)
            )
            if self._seg_type == SegmentType.ascending_aorta:
                cmp_prev_size = bool(
                    total_coord < 2 * self._previous_size
                )
        else:
            slicer_larger_than = bool(
                total_coord >
                (self._previous_size/self._qualified_coef)
            )
            if self._seg_type == SegmentType.ascending_aorta:
                if not self._is_size_decreasing and is_overlapping:
                    self._qualified_overlap_coef = 2.8
                else:
                    self._qualified_overlap_coef = self._qualified_coef
                cmp_original_size = bool(total_coord < (self._original_size*4))
                cmp_prev_size = bool(
                    total_coord <
                    (self._qualified_overlap_coef * self._previous_size)
                )
            else:
                cmp_original_size = bool(
                    total_coord <
                    (self._original_size*(self._qualified_coef+0.3))
                )
        return cmp_prev_size and slicer_larger_than and cmp_original_size

    def __prepare_seed(self):
        """Get a seed from the original image. We will add extra space
        and use it to get the labeled image statistics.

        Returns:
            SITK::IMAGE: An image slice with aorta centre and some extra spacing.
        """ # noqa
        seed = sitk.Image(self._cur_img_slice.GetSize(), sitk.sitkUInt8)
        seed.CopyInformation(self._cur_img_slice)
        # add original seed and additional seeds three pixels apart
        spacing = 3
        for j in range(-1, 2):
            seed_with_space = self._prev_centre[0] + spacing * j
            seed[(seed_with_space, self._prev_centre[1])] = 1
        for s in self._prev_seeds:
            seed[s] = 1
        seed = sitk.BinaryDilate(seed, [3] * 2)
        return seed

    def __get_label_statistics(self):
        """From the labeled image we can derive descriptive intensity.

        Returns:
            numpy.ndarray: labeled statistics of the original image.
        """
        seed = self.__prepare_seed()
        # determine threshold values based on seed location
        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(self._cur_img_slice, seed)
        lower_threshold = (
            stats.GetMean(PixelValue.white_pixel.value)
            - self._filter_factor*stats.GetSigma(PixelValue.white_pixel.value))
        upper_threshold = (
            stats.GetMean(PixelValue.white_pixel.value)
            + self._filter_factor*stats.GetSigma(PixelValue.white_pixel.value))
        # use filter to apply threshold to image
        init_ls = sitk.SignedMaurerDistanceMap(
            seed, insideIsPositive=True, useImageSpacing=True)

        # segment the aorta using the seed values and threshold values
        self._segment_filter.SetLowerThreshold(lower_threshold)
        self._segment_filter.SetUpperThreshold(upper_threshold)

        ls = self._segment_filter.Execute(
            init_ls, sitk.Cast(self._cur_img_slice, sitk.sitkFloat32))
        return ls

    def __count_pixel_des(self, new_slice):
        """Use label statistics to calculate the number of counted pixels for descending aorta segmentation.

        Returns:
            (tuple): tuple containing:
                int: The total number of the counted X coordinates
                tupple: The new derived centre calculated by the mean of counted X coordinates and Y coordinates
        """ # noqa
        # assign segmentation to fully_seg_slice
        # get array from segmentation
        nda = sitk.GetArrayFromImage(new_slice)
        list_x, list_y = np.where(nda == 1)
        new_centre = (int(np.average(list_y)), int(np.average(list_x)))
        total_coord = len(list_x)
        return total_coord, new_centre

    def __count_pixel_asc(self, new_slice):
        """Use label statistics to calculate the number of counted pixels for ascending aorta segmentation.

        Returns:
            (tuple): tuple containing:
                int: The total number of the counted X coordinates
                tupple: The new derived centre calculated by the mean of counted X coordinates and Y coordinates
                list: The new seeds coordinates based on the new derived centre
        """ # noqa
        nda = sitk.GetArrayFromImage(new_slice)
        new_centre = [0, 0]

        list_y, _ = np.where(nda == 1)
        max_y = max(list_y)
        min_y = min(list_y)

        total_coord = len(list_y)

        new_centre[1] = int(sum(list_y) / len(list_y))
        height = max_y - min_y

        list_x = np.where(nda[new_centre[1]] == 1)[0]
        width = len(list_x)

        if (width == 0):
            _, list_x = np.where(nda == 1)
        new_centre[0] = int(np.average(list_x))

        new_seeds = []
        y1 = int((max_y + new_centre[1])/2)
        y2 = int((min_y + new_centre[1])/2)

        next_seed_x1_list = np.where(nda[y1] == 1)[0]
        next_seed_x2_list = np.where(nda[y2] == 1)[0]
        width1 = len(next_seed_x1_list)
        width2 = len(next_seed_x2_list)

        if (width1 > width / 2):
            new_seeds.append([int(np.average(next_seed_x1_list)), y1])
        if (width2 > width / 2):
            new_seeds.append([int(np.average(next_seed_x2_list)), y2])

        x3 = int(new_centre[0] + width/2)
        x4 = int(new_centre[0] - width/2)

        next_seed_y3_list = np.where(nda[:, x3] == 1)[0]
        next_seed_y4_list = np.where(nda[:, x4] == 1)[0]
        height3 = len(next_seed_y3_list)
        height4 = len(next_seed_y4_list)

        if (height3 > height / 2):
            new_seeds.append([x3, int(np.average(next_seed_y3_list))])
        if (height4 > height / 2):
            new_seeds.append([x4, int(np.average(next_seed_y4_list))])

        return total_coord, new_centre, new_seeds

    def __filling_missing_slices(self):
        for index in range(len(self._skipped_slices)):
            # ensure there is at least one slice
            # before and after the skipped slice
            slice_num = self._skipped_slices[index]
            if (slice_num > 0 and slice_num <
                    self._cropped_image.GetDepth() - 1):
                next_index = index + 1

                # if there are two skipped slices in a row,
                # take the overlap of the two skipped slice.
                # otherwise take the overlap of accepted slices.
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
