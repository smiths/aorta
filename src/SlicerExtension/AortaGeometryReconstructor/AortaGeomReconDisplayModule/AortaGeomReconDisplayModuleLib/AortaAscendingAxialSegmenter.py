from AortaGeomReconDisplayModuleLib.AortaAxialSegmenter\
    import AortaAxialSegmenter
import SimpleITK as sitk
import numpy as np
import os
import sys
project_path = os.path.abspath('.')
AGR_module_path = os.path.join(project_path, "src/SlicerExtension/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeometryReconstructor/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeomReconDisplayModule")
sys.path.insert(0, AGR_module_path)

from AortaGeomReconDisplayModuleLib.AortaAxialSegmenter import AortaAxialSegmenter # noqa
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import SegmentDirection as SegDir # noqa
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import SegmentType as SegType # noqa


class AortaAscendingAxialSegmenter(AortaAxialSegmenter):

    def __init__(
            self, starting_slice, aorta_centre, num_slice_skipping,
            qualified_coef, cropped_image, processing_image):
        self._processing_image = processing_image
        self._qualified_overlap_coef = qualified_coef
        super().__init__(starting_slice, aorta_centre, num_slice_skipping,
                         qualified_coef, cropped_image)

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

        return (overlap > 0)

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
        factor = 3.5
        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(self._cur_img_slice, seed)
        lower_threshold = stats.GetMean(1)-factor*stats.GetSigma(1)
        upper_threshold = stats.GetMean(1)+factor*stats.GetSigma(1)
        # use filter to apply threshold to image
        init_ls = sitk.SignedMaurerDistanceMap(
            seed, insideIsPositive=True, useImageSpacing=True)

        # segment the aorta using the seed values and threshold values
        self._segment_filter.SetLowerThreshold(lower_threshold)
        self._segment_filter.SetUpperThreshold(upper_threshold)

        ls = self._segment_filter.Execute(
            init_ls, sitk.Cast(self._cur_img_slice, sitk.sitkFloat32))
        return ls

    def __count_pixel(self, new_slice):
        """Use label statistics to calculate the number of counted pixels.

        Returns:
            (tuple): tuple containing:
                int: The total number of the counted X coordinates
                tupple: The new derived centre calculated by the mean of counted X coordinates and Y coordinates
        """ # noqa
        # make array from segmentation
        nda = sitk.GetArrayFromImage(new_slice)

        # Calculate the centre of the segmentation
        # by 1st getting the average y value.
        # Then, finding the average x value on that y-value to ensure
        # there is an actual point there
        # Also determine 4 seed values by going 25% outwards
        # in the x, -x, y and -y directions.
        new_centre = [0, 0]

        # calculate the average y value of the pixels
        # and the height (Δy) of the aorta
        list_y, _ = np.where(nda == 1)
        max_y = max(list_y)
        min_y = min(list_y)

        total_coord = len(list_y)

        new_centre[1] = int(sum(list_y) / len(list_y))
        height = max_y - min_y

        # calculate the average x value of the pixels
        # along the predetermined y value.
        # also calulate the width (Δx) along that height
        list_x = np.where(nda[new_centre[1]] == 1)[0]
        width = len(list_x)

        # if there were no pixels along that y value for whatever reason,
        # just get the centre of gravity of the segmentation
        # by finding the overall average x value
        if (width == 0):
            _, list_x = np.where(nda == 1)
        new_centre[0] = int(np.average(list_x))

        # determine next seed values; y1,x1, y2,x2 are vertical values;
        # y3,x3, y4,x4 are horizontal the seed values are 25% outwards
        # from the centre.
        # 25% refers to 25% of the entire width or height of the segmentation
        new_seeds = []

        # vertical
        y1 = int((max_y + new_centre[1])/2)
        y2 = int((min_y + new_centre[1])/2)

        # find x values along those y values
        next_seed_x1_list = np.where(nda[y1] == 1)[0]
        next_seed_x2_list = np.where(nda[y2] == 1)[0]
        width1 = len(next_seed_x1_list)
        width2 = len(next_seed_x2_list)

        # only assign seed if width is relatively large
        if (width1 > width / 2):
            new_seeds.append([int(np.average(next_seed_x1_list)), y1])
        if (width2 > width / 2):
            new_seeds.append([int(np.average(next_seed_x2_list)), y2])

        # horizontal
        x3 = int(new_centre[0] + width/2)
        x4 = int(new_centre[0] - width/2)

        # find y values along those x values
        next_seed_y3_list = np.where(nda[:, x3] == 1)[0]
        next_seed_y4_list = np.where(nda[:, x4] == 1)[0]
        height3 = len(next_seed_y3_list)
        height4 = len(next_seed_y4_list)

        # only assign seed if width is relatively large
        if (height3 > height / 2):
            new_seeds.append([x3, int(np.average(next_seed_y3_list))])
        if (height4 > height / 2):
            new_seeds.append([x4, int(np.average(next_seed_y4_list))])

        return total_coord, new_centre, new_seeds

    def __is_new_centre_qualified(self, total_coord, is_overlapping):
        """Return True if the number of coordiante in the segmented centre is qualified

        Returns:
            Boolean
        """ # noqa
        if self._seg_dir == SegDir.Superior_to_Inferior:
            cmp_prev_size = bool(
                total_coord < 2 * self._previous_size
            )
            cmp_original_size = bool(
                total_coord <
                (self._original_size*self._qualified_coef)
            )
            slicer_larger_than = bool(
                total_coord >
                (self._original_size/self._qualified_coef)
            )
        else:
            if not self._is_size_decreasing and is_overlapping:
                self._qualified_overlap_coef = 2.8
            else:
                self._qualified_overlap_coef = self._qualified_coef
            slicer_larger_than = bool(
                total_coord >
                (self._previous_size/self._qualified_coef)
            )
            cmp_original_size = bool(total_coord < (self._original_size*4))
            cmp_prev_size = bool(
                total_coord <
                (self._qualified_overlap_coef * self._previous_size)
            )
        return cmp_prev_size and slicer_larger_than and cmp_original_size

    def __segmentation(self):
        # counts how many slices have been skipped
        counter = 0
        # goes from current slice to the bottom of the ascending aorta
        # (opposite direction from the arch)
        for i in range(self._start, self._end, self._step):
            # perform segmentation on slice i
            self._cur_img_slice = self._cropped_image[:, :, i]
            label_stats = self.__get_label_statistics()
            new_slice = label_stats > 0
            total_coord, centre, seeds = self.__count_pixel(new_slice)
            is_overlapping = False
            if self._seg_dir == SegDir.Inferior_to_Superior:
                is_overlapping = self.__is_overlapping(new_slice, i)
            if self.__is_new_centre_qualified(total_coord, is_overlapping):
                counter = 0
                self._processing_image[:, :, i] = (
                    new_slice | self._processing_image[:, :, i]
                )
                self._prev_centre = centre
                self._prev_seeds = seeds

                # check for double size
                if self._seg_dir == SegDir.Inferior_to_Superior:
                    if total_coord > 2*self._original_size:
                        if (total_coord < self._previous_size):
                            self._is_size_decreasing = True
                            self._qualified_overlap_coef = 1.2
            # otherwise skip slice and don't change previous centre
            # and seed values
            else:
                counter += 1
                if (counter >= self._num_slice_skipping):
                    break
            self._previous_size = total_coord

    def begin_segmentation(self):
        self._segment_filter = sitk.ThresholdSegmentationLevelSetImageFilter()
        self._segment_filter.SetMaximumRMSError(0.02)
        self._segment_filter.SetNumberOfIterations(1000)
        self._segment_filter.SetCurvatureScaling(.5)
        self._segment_filter.SetPropagationScaling(1)
        self._segment_filter.ReverseExpansionDirectionOn()

        self._skipped_slices = []
        self._start = self._starting_slice
        self._prev_centre = self._aorta_centre
        self._prev_seeds = []

        # Initialize parameters for superior to inferior segmentation
        index = self._start
        self._cur_img_slice = self._cropped_image[:, :, index]
        label_stats = self.__get_label_statistics()
        new_slice = label_stats > 0
        total_coord, centre, seeds = self.__count_pixel(new_slice)
        self._original_size = total_coord
        self._previous_size = total_coord
        self._processing_image[:, :, index] = new_slice
        self._skipped_counter = 0
        self._end = -1
        self._step = -1
        self._seg_dir = SegDir.Superior_to_Inferior
        print("Ascending aorta segmentation - top to bottom started")
        self.__segmentation()
        print("Ascending aorta segmentation - top to bottom finished")

        # reset values to correspond with the seed value's slice
        self._prev_centre = self._aorta_centre
        self._prev_seeds = seeds
        self._previous_size = self._original_size
        self._is_size_decreasing = False
        self._start = self._starting_slice
        self._end = self._cropped_image.GetDepth()
        self._step = 1
        self._seg_dir = SegDir.Inferior_to_Superior
        print("Ascending aorta segmentation - bottom to top started")
        self.__segmentation()
        print("Ascending aorta segmentation - bottom to top finished")
