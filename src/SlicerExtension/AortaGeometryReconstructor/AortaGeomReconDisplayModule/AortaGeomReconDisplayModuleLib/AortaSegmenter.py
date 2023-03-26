import os
import sys

import SimpleITK as sitk
import numpy as np
project_path = os.path.abspath('.')
AGR_module_path = os.path.join(project_path, "src/SlicerExtension/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeometryReconstructor/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeomReconDisplayModule")
sys.path.insert(0, AGR_module_path)

from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import SegmentDirection as SegDir # noqa
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import SegmentType # noqa
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import PixelValue # noqa


class AortaSegmenter():
    """This class is used to perform Descending or Ascending aorta segmentation.

    Attributes:

        starting_slice (float): The seed slice's index (the index along the Z axis)

        aorta_centre (tuple): A tuple of two integers indicates the centre of Descending or Ascending aorta on the axial plane.

        num_slice_skipping (int): The number of slice allowed to consecutively skip by the algorithm.

        seg_type (AortaGeomReconEnums.SegmentType): Indicate the segmentation type, Descending aorta segmentation or Ascending aorta

        qualified_coef (float): This coefficient controls the lower and upper threshold of the number of white pixels to determine whether to accept each segmented slice or not.

        cropped_image (SITK::image): The original image that the user has only perform cropping.

        processing_image (SITK::image): The processing image, this image could be none when performing descending aorta segmentation. When performing ascending aorta segmentation, it should have the Descending aorta segmentation result.

    """ # noqa

    def __init__(
            self, cropped_image, starting_slice, aorta_centre,
            num_slice_skipping, processing_image, seg_type,
            qualified_coef=2.2, threshold_coef=3.5
    ):
        self._starting_slice = starting_slice
        self._aorta_centre = aorta_centre
        self._num_slice_skipping = num_slice_skipping
        self._seg_type = seg_type
        self._processing_image = processing_image
        self._qualified_coef = qualified_coef
        self._threshold_coef = threshold_coef
        self._cropped_image = cropped_image

    def __is_overlapping(self, img1, i):
        """Compare the current 2D segmented slice with the previous two processed 2D slices,
        return True if there are any voxel intersect or overlaps on each other between the new slice and processed slice.

        Returns:
            Boolean

        """ # noqa
        img2 = self._processing_image[:, :, i]
        overlap = np.count_nonzero(img1 * img2)
        if (overlap <= 0):
            img2 = self._processing_image[:, :, i - 1]
            overlap = np.count_nonzero(img1 * img2)
        if (overlap <= 0):
            img2 = self._processing_image[:, :, i - 2]
            overlap = np.count_nonzero(img1 * img2)
        return (overlap > PixelValue.black_pixel.value)

    @property
    def cropped_image(self):
        """cropped image getter. The cropped image is the untouched cropped image that user has input.

        """ # noqa
        return self._cropped_image

    @property
    def processing_image(self):
        """processing image getter. The prcoessing image is the segmentation result.

        """ # noqa
        return self._processing_image

    def begin_segmentation(self):
        """The api is available to the user's to perform axial segmentation.
        Depending on the user's inputs, it will perform Descending aorta segmentation or Ascending aorta segmentation.
        It first set up a few variables, get the original seed values,
        then jump to the main loop which perform segmentation superior to inferior from the user's seed slice,
        and the main loop that performs segmentation inferior to superior from the user's seed slice.

        """ # noqa
        rms_error = 0.02
        no_iteration = 600
        curvature_scaling = 0.5
        propagation_scaling = 1
        # self._stats_filter = sitk.LabelStatisticsImageFilter()
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
        self._seg_dir = None
        self._original_size = None
        self._seeds = None
        self._is_size_decreasing = False
        if SegmentType.is_axial_seg(self._seg_type):
            # Get more values from the seed slice
            self._start = self._starting_slice - 1
            self._prev_centre = self._aorta_centre
            self._prev_seeds = []
            # Initialize parameters for superior to inferior segmentation
            slice_num = self._starting_slice
            self._cur_img_slice = self._cropped_image[:, :, slice_num]
            segmented_slice = self.__get_image_segment()
            new_slice = segmented_slice > PixelValue.black_pixel.value
            seeds = []
            if self._seg_type == SegmentType.descending_aorta:
                total_coord, centre = self.__count_pixel_des(new_slice)
                self._processing_image[:, :, slice_num] = new_slice
            else:
                total_coord, centre, seeds = self.__count_pixel_asc(new_slice)
                self._processing_image[:, :, slice_num] = (
                    new_slice | self._processing_image[:, :, slice_num])
            self._prev_seeds = seeds
            self._original_size = total_coord
            self._previous_size = total_coord
            self._prev_centre = centre
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
            self._prev_seeds = seeds
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
        """The main loop of the segmentation algorithm.
        For each axial slice, the algorithm performs segmetation with get_image_segment function.
        Next, the algorithm counts the number of white pixels of the segmentation result, and calculates a new centre based on the result.
        Finally, the algorithm decides whether to accept the new slice or not. If accepted, the new centre will be used as seed for next slice's segmentation.
        If not, and it reached the point where maximum consecutive skips is allowed, the algorithm hault and return the segmentation result.

        """ # noqa
        counter = 0
        is_overlapping = False
        for slice_i in range(self._start, self._end, self._step):
            self._cur_img_slice = self._cropped_image[:, :, slice_i]
            segmented_slice = self.__get_image_segment()
            new_slice_i = segmented_slice > PixelValue.black_pixel.value
            if self._seg_type == SegmentType.descending_aorta:
                total_coord, centre = self.__count_pixel_des(new_slice_i)
                seeds = []
            else:
                total_coord, centre, seeds = self.__count_pixel_asc(
                    new_slice_i)
                is_overlapping = self.__is_overlapping(new_slice_i, slice_i)
            if self.__is_new_centre_qualified(total_coord, is_overlapping):
                counter = 0
                if self._seg_type == SegmentType.descending_aorta:
                    self._processing_image[:, :, slice_i] = new_slice_i
                else:
                    self._processing_image[:, :, slice_i] = (
                        new_slice_i | self._processing_image[:, :, slice_i]
                    )
                self._prev_centre = centre
                self._prev_seeds = seeds
                if (self._seg_type == SegmentType.ascending_aorta
                        and self._seg_dir == SegDir.Inferior_to_Superior
                        and total_coord > 2*self._original_size
                        and total_coord < self._previous_size):
                    self._is_size_decreasing = True
                    self._qualified_overlap_coef = 1.2
            else:
                counter += 1
                self._skipped_slices.append(slice_i)
                if (counter >= self._num_slice_skipping):
                    self._skipped_slices = self._skipped_slices[
                        ::-self._num_slice_skipping]
                    break
                total_coord = self._previous_size
            self._previous_size = total_coord

    def __is_new_centre_qualified(self, total_coord, is_overlapping):
        """Return True if it satisfies the following conditions:
        
        1. The number of white pixels of the segmented result is smaller than the previous size multiplis some ratio (the ratio could change depends on the segmentation type).
        
        2. The number of white pixels is smaller than qualified cofficient multiply the number of white pixels of the user's selected slice.
        
        3. The number of white pixels is larger than the number of white pixels of the user's selected slice divided by the qualified coefficient.

        Notes that in some cases, the conditions might change the qualified coefficient to some other values depending on the segmentation type and segmentation direction.

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
        """Get a seed from the original image. The algorithm will overwrite three pixels as white pixels. The pixels are decided by the previous centre, derived by count_pixels function.
        For ascending aorta segmentation, the algorithm also takes extra seeds.

        Returns:
            SITK::IMAGE: An image slice with some pixels value overwrite to white pixel (value of 1)
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

    def __get_image_segment(self):
        """Use SITK::LabelStatisticsImageFilter to get the mean of the intensity values of white pixel (label of 1).
        Use the mean to calculate the threshold for segmentation image filter.
        Use SITK::SignedMaurerDistanceMap to calculate the signed squared Euclidean distance transform of the circle.
        Finally, get the segmentation value with the Euclidean distance transform.

        Returns:
            numpy.ndarray: Segmented image slice based on intensity values.

        """ # noqa
        seed = self.__prepare_seed()

        # determine threshold values based on seed location
        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(self._cur_img_slice, seed)
        lower_threshold = (
            stats.GetMean(1) - self._threshold_coef*stats.GetSigma(1))
        upper_threshold = (
            stats.GetMean(1) + self._threshold_coef*stats.GetSigma(1))

        # calculate the Euclidean distance transform
        init_ls = sitk.SignedMaurerDistanceMap(
            seed, insideIsPositive=True, useImageSpacing=True)

        # use filter to apply threshold to image
        # segment the aorta using the seed values and threshold values
        self._segment_filter.SetLowerThreshold(lower_threshold)
        self._segment_filter.SetUpperThreshold(upper_threshold)

        ls = self._segment_filter.Execute(
            init_ls, sitk.Cast(self._cur_img_slice, sitk.sitkFloat32))
        return ls

    def __count_pixel_des(self, new_slice):
        """Get the number of white pixels, and calculate a new centre based on the segmentation result.

        Returns:
            (tuple): tuple containing:
                int: The total number of the white pixels.
                tuple: The new derived centre calculated by the mean of white pixe's X coordinates and Y coordinates.
        """ # noqa
        # assign segmentation to fully_seg_slice
        # get array from segmentation
        nda = sitk.GetArrayFromImage(new_slice)
        list_x, list_y = np.where(nda == 1)
        new_centre = (int(np.average(list_y)), int(np.average(list_x)))
        total_coord = len(list_x)
        return total_coord, new_centre

    def __count_pixel_asc(self, new_slice):
        """Get the number of white pixels, and calculate a new centre based on the segmentation result.
        This function adds extra seeds with the mean of white pixels' white coordinate.

        Returns:
            (tuple): tuple containing:
                int: The total number of the white pixels.
                tuple: The new derived centre calculated by the mean of white pixe's X coordinates and Y coordinates.
                list: More possible coordinates based on the new derived centre
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
        """The helper function to replace the missing slice that was not accepted during the descending aorta segmentation.
        This function will replace the missing slice by reading the previous slice and the next slice, 
        fill the slice with the overlapping area of both slices.
        """ # noqa
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
