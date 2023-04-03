import os
import sys

import SimpleITK as sitk
import numpy as np
# for design document
project_path = os.path.abspath('.')
AGR_module_path = os.path.join(project_path, "src/SlicerExtension/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeometryReconstructor/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeomReconDisplayModule")
sys.path.insert(0, AGR_module_path)

# for debugging and numpy print operation
np.set_printoptions(threshold=sys.maxsize)

# import helpers enumeration classes
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import SegmentDirection as SegDir # noqa
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import SegmentType # noqa
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import PixelValue # noqa


class AortaSegmenter():
    """This class is used to perform Descending or Ascending aorta segmentation.

    Attributes:

        starting_slice (int): The seed slice's index (the index along the Z axis)

        aorta_centre (tuple): A tuple of two integers indicates the centre of Descending or Ascending aorta on the axial plane.

        num_slice_skipping (int): The number of slice allowed to consecutively skip by the algorithm.

        seg_type (AortaGeomReconEnums.SegmentType): Indicate the segmentation type, Descending aorta or Ascending aorta segmentation.

        qualified_coef (float): This coefficient controls the lower and upper threshold of the number of white pixels to determine whether to accept each segmented slice or not.

        cropped_image (SITK::image): The original image that the user has only perform cropping.

        processing_image (SITK::image): The processing image, this image could be none when performing Descending aorta segmentation. When performing Ascending aorta segmentation, it should have the Descending aorta segmentation result.

    """ # noqa

    def __init__(
            self, cropped_image, starting_slice, aorta_centre,
            num_slice_skipping, processing_image, seg_type,
            qualified_coef=2.2, threshold_coef=3.5, debug=False
    ):
        self._starting_slice = starting_slice
        self._aorta_centre = aorta_centre
        self._num_slice_skipping = num_slice_skipping
        self._seg_type = seg_type
        self._processing_image = processing_image
        self._qualified_coef = qualified_coef
        self._threshold_coef = threshold_coef
        self._cropped_image = cropped_image
        self._debug_mod = debug

    def begin_segmentation(self):
        """This is the main entry point of the axial segmentation.
        This api should be called to perform Descending aorta segmentation first
        (superior to inferior, then inferior to superior starting from the seed slice).
        After getting the result of Descending aorta segmentation, this api should perform Ascending aorta segmentation
        (superior to inferior, then inferior to superior starting from the seed slice).
    
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
        self._is_size_decreasing = False

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

        if self._debug_mod:
            return

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
            if self.__is_new_slice_qualified(total_coord, is_overlapping):
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

    def __is_new_slice_qualified(self, total_coord, is_overlapping):
        """Return True if it satisfies the following conditions:
        
        1. The number of white pixels of the segmented result is smaller than the previous size multiplis some ratio (the ratio could change depends on the segmentation type).
        
        2. The number of white pixels is smaller than qualified cofficient multiply the number of white pixels of the user's selected slice.
        
        3. The number of white pixels is larger than the number of white pixels of the user's selected slice divided by the qualified coefficient.

        Notes that in some cases, the conditions might change the qualified coefficient to some other values depending on the segmentation type and segmentation direction.

        Returns:
            Boolean
        """ # noqa
        cmp_prev_size = bool(total_coord < 2*self._previous_size)
        slicer_larger_than = bool(
            total_coord >
            (self._original_size/self._qualified_coef)
        )
        cmp_original_size = bool(
            total_coord <
            (self._original_size*self._qualified_coef)
        )
        if self._seg_dir == SegDir.Inferior_to_Superior:
            slicer_larger_than = bool(
                total_coord >
                (self._previous_size/self._qualified_coef)
            )
            cmp_original_size = bool(
                total_coord <
                (self._original_size*(self._qualified_coef+0.3))
            )
            if self._seg_type == SegmentType.ascending_aorta:
                self._qualified_overlap_coef = self._qualified_coef
                if not self._is_size_decreasing and is_overlapping:
                    self._qualified_overlap_coef = 2.8
                cmp_original_size = bool(total_coord < (self._original_size*4))
                cmp_prev_size = bool(
                    total_coord <
                    (self._qualified_overlap_coef * self._previous_size)
                )
        return cmp_prev_size and slicer_larger_than and cmp_original_size

    def __prepare_label_map(self):
        """Create a label map image that has a circle-like shape.
        The pixels within the circle are labeled as white pixels (value of 1), the other are labeled as black pixels (value of 0).

        Returns:
            SITK::IMAGE: A label map image that has a circle like shape.
        """ # noqa
        label_map = sitk.Image(self._cur_img_slice.GetSize(), sitk.sitkUInt8)
        label_map.CopyInformation(self._cur_img_slice)
        # add original seed and additional seeds three pixels apart
        spacing = 3
        for j in range(-1, 2):
            seed_with_space = self._prev_centre[0] + spacing * j
            label_map[
                (seed_with_space, self._prev_centre[1])
            ] = PixelValue.white_pixel.value
        for s in self._prev_seeds:
            label_map[s] = PixelValue.white_pixel.value
        label_map = sitk.BinaryDilate(label_map, [3] * 2)
        return label_map

    def __get_image_segment(self):
        """Use SITK::LabelStatisticsImageFilter to get the mean of the intensity values of white pixel (label of 1).
        Use the mean to calculate the threshold for segmentation image filter.
        Use SITK::SignedMaurerDistanceMap to calculate the signed squared Euclidean distance transform of the circle.
        Finally, get the segmentation value with the Euclidean distance transform.

        Returns:
            numpy.ndarray: Segmented image slice based on intensity values.

        """ # noqa
        label_map = self.__prepare_label_map()

        # calculate the Euclidean distance transform
        dis_map = sitk.SignedMaurerDistanceMap(
            label_map, insideIsPositive=True, useImageSpacing=True)

        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(self._cur_img_slice, label_map)

        intensity_mean = stats.GetMean(PixelValue.white_pixel.value)
        std = stats.GetSigma(PixelValue.white_pixel.value)
        lower_threshold = (intensity_mean - self._threshold_coef*std)
        upper_threshold = (intensity_mean + self._threshold_coef*std)

        self._segment_filter.SetLowerThreshold(lower_threshold)
        self._segment_filter.SetUpperThreshold(upper_threshold)

        segmented_slice = self._segment_filter.Execute(
            dis_map, sitk.Cast(self._cur_img_slice, sitk.sitkFloat32))
        
        if self._debug_mod:
            self.__debug(
                label_map,
                dis_map,
                lower_threshold,
                upper_threshold,
                segmented_slice
            )

        return segmented_slice

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
        list_x, list_y = np.where(nda == PixelValue.white_pixel.value)
        new_centre = (int(np.average(list_y)), int(np.average(list_x)))
        total_coord = len(list_x)
        if self._debug_mod:
            print(total_coord)
            print(self._aorta_centre, new_centre)
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
        list_y, _ = np.where(nda == PixelValue.white_pixel.value)
        max_y = max(list_y)
        min_y = min(list_y)
        total_coord = len(list_y)
        new_centre[1] = int(sum(list_y) / len(list_y))
        height = max_y - min_y
        list_x = np.where(
            nda[new_centre[1]] == PixelValue.white_pixel.value)[0]
        width = len(list_x)
        if (width == 0):
            _, list_x = np.where(nda == PixelValue.white_pixel.value)
        new_centre[0] = int(np.average(list_x))
        new_seeds = []
        y1 = int((max_y + new_centre[1])/2)
        y2 = int((min_y + new_centre[1])/2)
        next_seed_x1_list = np.where(
            nda[y1] == PixelValue.white_pixel.value)[0]
        next_seed_x2_list = np.where(
            nda[y2] == PixelValue.white_pixel.value)[0]
        width1 = len(next_seed_x1_list)
        width2 = len(next_seed_x2_list)
        if (width1 > width / 2):
            new_seeds.append([int(np.average(next_seed_x1_list)), y1])
        if (width2 > width / 2):
            new_seeds.append([int(np.average(next_seed_x2_list)), y2])
        x3 = int(new_centre[0] + width/2)
        x4 = int(new_centre[0] - width/2)
        next_seed_y3_list = np.where(
            nda[:, x3] == PixelValue.white_pixel.value)[0]
        next_seed_y4_list = np.where(
            nda[:, x4] == PixelValue.white_pixel.value)[0]
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
                # take the intersect of the previous and next segmented slice.
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
        return (overlap > 0)

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

    def __debug(self, label_map, dis_map, lt, ut, ss):
        nda_label = sitk.GetArrayFromImage(label_map)
        print(nda_label)
        nda = sitk.GetArrayFromImage(dis_map)
        print("lower:", lt, "upper:", ut)
        list_x, list_y = np.where(nda_label == PixelValue.white_pixel.value)
        print(len(list_x))
        print("\ndistance_map")
        print(nda)
        print()
        for i in range(len(list_x)):
            print(list_x[i], list_y[i], end=" ")
            print(nda[(list_x[i], list_y[i])])
        nda_ss = sitk.GetArrayFromImage(ss)
        list_x, list_y = np.where(nda_ss > PixelValue.black_pixel.value)
        for i in range(len(list_x)):
            print(list_x[i], list_y[i])