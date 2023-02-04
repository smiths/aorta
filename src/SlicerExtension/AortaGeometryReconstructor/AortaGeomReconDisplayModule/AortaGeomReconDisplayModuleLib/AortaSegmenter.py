import SimpleITK as sitk
import numpy as np
from enum import Enum


class SegmentType(Enum):
    descending_aorta = 1
    ascending_aorta = 2
    sagittal_front = 3
    sagittal = 4

    def is_axial_seg(seg_type):
        return (seg_type == SegmentType.descending_aorta
                or seg_type == SegmentType.ascending_aorta)

    def is_sagittal_seg(seg_type):
        return (seg_type == SegmentType.sagittal_front
                or seg_type == SegmentType.sagittal)

    def __repr__(self):
        return f'{self.name.replace("_"," ")} segmentation'


class SegmentDirection(Enum):
    S_to_I = 1
    I_to_S = 2


class PixelValue(Enum):
    white_pixel = 1
    black_pixel = 0


class AortaSegmenter():

    def __init__(
            self, cropped_image, starting_slice, aorta_centre,
            num_slice_skipping, processing_image, seg_type,
            qualified_slice_factor=2.2, filter_factor=3.5,
            is_normalized=False, is_output_binary=True
    ):
        self._starting_slice = starting_slice
        self._aorta_centre = aorta_centre
        self._num_slice_skipping = num_slice_skipping
        self._seg_type = seg_type
        self._processing_image = processing_image
        self._qualified_slice_factor = qualified_slice_factor
        self._filter_factor = filter_factor
        self._cropped_image = cropped_image
        self._normalized = is_normalized
        self._is_output_binary = is_output_binary

    def __get_overlap(self, img1, slice_num):
        current_original_slice = self._cropped_image[:, :, slice_num]
        second_original_slice = self._cropped_image[:, :, slice_num+1]
        third_original_slice = self._cropped_image[:, :, slice_num+2]
        overlap = np.count_nonzero(img1 * current_original_slice)
        if (overlap <= 0):
            overlap = np.count_nonzero(img1 * second_original_slice)
        if (overlap <= 0):
            overlap = np.count_nonzero(img1 * third_original_slice)

        return (overlap > PixelValue.black_pixel.value)

    @property
    def qualified_slice_factor(self):
        return self._qualified_slice_factor

    @property
    def cropped_image(self):
        return self._cropped_image

    @qualified_slice_factor.setter
    def qualified_slice_factor(self, qualified_slice_factor):
        self._qualified_slice_factor = qualified_slice_factor

    @property
    def processing_image(self):
        return self._processing_image

    @cropped_image.setter
    def cropped_image(self, image):
        self._cropped_image = image

    def begin_segmentation(self):
        # Initializing filter
        rms_error = 0.02
        no_iteration = 1000
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
        self._decreasing_size = False
        if SegmentType.is_axial_seg(self._seg_type):
            # Get more values from the seed slice
            ls, new_slice, seed_slice = self.__circle_filter(
                self._starting_slice,
                self._aorta_centre,
                []
            )

            # Initialize seed values
            # [total_coord, new_size, new_centre, new_seeds]
            var_list = list(self.__count_pixels(ls, new_slice, seed_slice))
            self._processing_image[:, :, self._starting_slice] = new_slice
            self._original_size = var_list[0]
            self._seeds = var_list[3]
            self._start = self._starting_slice

            # SEGMENT FROM SEED VALUE TO BOTTOM OF THE AORTA
            print("{} - top to bottom started".format(self._seg_type))
            self._seg_dir = SegmentDirection.S_to_I
            self._end = -1
            self._step = -1
            self._skipped_slice_counter = 0
            self.__segmentation()
            print("{} - top to bottom finished".format(self._seg_type))

            print("{} - bottom to top started".format(self._seg_type))
            self._seg_dir = SegmentDirection.I_to_S
            self._end = self._cropped_image.GetDepth()
            self._step = 1
            self._skipped_slice_counter = len(self._skipped_slices)
            if self._seg_type == SegmentType.descending_aorta:
                self._qualified_slice_factor += 0.3
            self.__segmentation()
            print("{} - bottom to top finished".format(self._seg_type))

            if self._seg_type == SegmentType.descending_aorta:
                # Fill in missing slices of descending aorta
                self.__filling_missing_slices()
        else:
            self._start = 1
            self._step = 1
            self._end = self._cropped_image.GetWidth()
            self._size_factor = 1.4
            print("{} - started".format(self._seg_type))
            self.__segmentation()
            print("{} - finished".format(self._seg_type))

            self._seg_type = SegmentType.sagittal_front
            self._end = self._cropped_image.GetHeight()
            self._size_factor = 1.1
            print("{} - started".format(self._seg_type))
            self.__segmentation()
            print("{} - finished".format(self._seg_type))

    def __segmentation(self):
        # initialize loop variables
        centre_previous = self._aorta_centre
        seeds_previous = self._seeds
        previous_size = self._original_size
        more_circles = True

        for sliceNum in range(self._start, self._end, self._step):
            if SegmentType.is_sagittal_seg(self._seg_type):
                if self._seg_type == SegmentType.sagittal:
                    self._sag_current_size = np.count_nonzero(
                        self._processing_image[sliceNum, :, :])
                else:
                    self._sag_current_size = np.count_nonzero(
                        self._processing_image[:, sliceNum, :])
                more_circles = self._sag_current_size > self._base_pixel_value
            if more_circles:
                # perform segmentation on slice i
                # Get new filtered slice and the seed slice
                ls, new_filtered_slice, seed_slice = self.__circle_filter(
                    sliceNum, centre_previous, seeds_previous)

                # Get more determinants
                # [total_coord, new_size, new_centre, new_seeds]
                var_list = list(
                    self.__count_pixels(ls, new_filtered_slice, seed_slice)
                )
                total_coord = var_list[0]
                sag_new_size = var_list[1]
                is_new_slice_qualified = self.__is_new_slice_qualified(
                    sliceNum, total_coord, previous_size,
                    new_filtered_slice, sag_new_size
                )

                if SegmentType.is_sagittal_seg(self._seg_type):
                    factor = self._filter_factor
                    while not is_new_slice_qualified:
                        self._filter_factor -= 0.5
                        ls, new_filtered_slice, seed_slice = (
                            self.__circle_filter(
                                sliceNum, centre_previous, seeds_previous)
                        )
                        # Get more determinants
                        # [total_coord, new_size, new_centre, new_seeds]
                        var_list = list(
                            self.__count_pixels(
                                ls, new_filtered_slice, seed_slice)
                        )
                        sag_new_size = var_list[1]
                        is_new_slice_qualified = (
                            self.__is_new_slice_qualified(
                                0, 0, 0, new_filtered_slice, sag_new_size
                            )
                        )
                    self._filter_factor = factor
                if is_new_slice_qualified:
                    self._skipped_slice_counter = 0
                    if SegmentType.is_axial_seg(self._seg_type):
                        self._processing_image[:, :, sliceNum] = (
                            new_filtered_slice)
                    elif self._seg_type == SegmentType.sagittal:
                        self._processing_image[sliceNum, :, :] = (
                            new_filtered_slice | seed_slice
                        )
                    else:
                        self._processing_image[:, sliceNum, :] = (
                            new_filtered_slice | seed_slice
                        )
                    centre_previous = var_list[2]
                    seeds_previous = var_list[3]

                    # check for double size
                    if self._seg_dir == SegmentDirection.I_to_S:
                        if total_coord > self._original_size * 2:
                            if (total_coord < previous_size):
                                self._decreasing_size = True

                # otherwise skip slice and don't change previous centre
                # and seed values
                elif SegmentType.is_axial_seg(self._seg_type):
                    self._skipped_slice_counter += 1
                    if (
                        self._skipped_slice_counter >= self._num_slice_skipping
                    ):
                        more_circles = False
                        if not self._is_output_binary:
                            self._processing_image[:, :, sliceNum] = sitk.Cast(
                                self._cropped_image_255[:, :, sliceNum],
                                sitk.sitkVectorUInt8
                            )
            if SegmentType.is_axial_seg(self._seg_type):
                previous_size = total_coord

    def __is_new_slice_qualified(
        self, slice_num, total_coord, previous_size, new_slice, sag_new_size
    ):
        is_new_slice_qualified = False
        ps_factor = 2
        os_factor = self._qualified_slice_factor
        if SegmentType.is_axial_seg(self._seg_type):
            if self._seg_dir == SegmentDirection.S_to_I:
                comparing_size = self._original_size
            elif self._seg_dir == SegmentDirection.I_to_S:
                comparing_size = previous_size
                if self._seg_type == SegmentType.ascending_aorta:
                    os_factor = 4
                    if self._decreasing_size:
                        ps_factor = 1.2
                    elif (self.__get_overlap(new_slice, slice_num)):
                        ps_factor = 2.8
                    else:
                        ps_factor = self._qualified_slice_factor

            is_new_slice_qualified = (
                (total_coord < ps_factor * previous_size)
                and (total_coord < os_factor * self._original_size)
            )
            is_new_slice_qualified = (
                is_new_slice_qualified
                and total_coord > (
                    1 / self.qualified_slice_factor * comparing_size
                )
            )
        else:
            is_new_slice_qualified = (
                sag_new_size < self._sag_current_size * self._size_factor
            )
        return is_new_slice_qualified

    def __circle_filter(self, slice_num, centre, seeds_previous):
        if SegmentType.is_axial_seg(self._seg_type):
            img_slice = self._cropped_image[:, :, slice_num]
        elif self._seg_type == SegmentType.sagittal:
            img_slice = self._cropped_image[slice_num, :, :]
        else:
            img_slice = self._cropped_image[:, slice_num, :]
        seed = self.__prepare_seed(
                img_slice, centre, seeds_previous, slice_num)

        # determine threshold values based on seed location
        self._stats_filter.Execute(img_slice, seed)

        lower_threshold = (
            self._stats_filter.GetMean(PixelValue.white_pixel.value)
            - self._filter_factor
            * self._stats_filter.GetSigma(PixelValue.white_pixel.value)
        )
        upper_threshold = (
            self._stats_filter.GetMean(PixelValue.white_pixel.value)
            + self._filter_factor
            * self._stats_filter.GetSigma(PixelValue.white_pixel.value)
        )
        # use filter to apply threshold to image
        init_label_stats = sitk.SignedMaurerDistanceMap(
            seed, insideIsPositive=True, useImageSpacing=True)

        # segment the aorta using the seed values and threshold values
        self._segment_filter.SetLowerThreshold(lower_threshold)
        self._segment_filter.SetUpperThreshold(upper_threshold)
        label_stats = self._segment_filter.Execute(
            init_label_stats,
            sitk.Cast(img_slice, sitk.sitkFloat32)
        )

        new_filtered_slice = self.__get_new_slice(label_stats, slice_num)

        return label_stats, new_filtered_slice, seed

    def __get_new_slice(self, ls, slice_num):
        fully_seg_slice = ls > PixelValue.black_pixel.value
        if self._seg_type == SegmentType.descending_aorta:
            # assign segmentation to fully_seg_slice
            if not self._is_output_binary:
                fully_seg_slice = sitk.LabelOverlay(
                    self._cropped_image[:, :, slice_num],
                    fully_seg_slice
                )
        elif self._seg_type == SegmentType.ascending_aorta:
            fully_seg_slice = (
                fully_seg_slice
                | self._processing_image[:, :, slice_num]
            )
        return fully_seg_slice

    def __count_pixels(self, ls, new_filtered_slice, seed):
        new_seeds = None
        new_centre = None
        total_coord = None
        sag_new_size = None
        # get array from segmentation
        if self._seg_type == SegmentType.descending_aorta:
            nda = sitk.GetArrayFromImage(new_filtered_slice)
            # calculate average x and average y values,
            # to get the new centre value
            list_x, list_y = np.where(nda == PixelValue.white_pixel.value)
            new_centre = (int(np.average(list_y)), int(np.average(list_x)))
            total_coord = len(list_x)
        elif self._seg_type == SegmentType.ascending_aorta:
            nda = sitk.GetArrayFromImage(ls > 0)
            new_centre = [0, 0]
            list_y, _ = np.where(nda == PixelValue.white_pixel.value)

            max_y = max(list_y)
            min_y = min(list_y)
            total_coord = len(list_y)

            new_centre[1] = int(sum(list_y) / len(list_y))
            height = max_y - min_y

            list_x = np.where(
                nda[new_centre[1]] == PixelValue.white_pixel.value
            )[0]

            width = len(list_x)

            if (width == 0):
                _, list_x = np.where(nda == PixelValue.white_pixel.value)
            new_centre[0] = int(np.average(list_x))

            new_seeds = []

            # vertical
            y1 = int((max_y + new_centre[1])/2)
            y2 = int((min_y + new_centre[1])/2)

            # find x values along those y values
            next_seed_x1_list = np.where(
                nda[y1] == PixelValue.white_pixel.value)[0]

            next_seed_x2_list = np.where(
                nda[y2] == PixelValue.white_pixel.value)[0]

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
            next_seed_y3_list = np.where(
                nda[:, x3] == PixelValue.white_pixel.value)[0]

            next_seed_y4_list = np.where(
                nda[:, x4] == PixelValue.white_pixel.value)[0]

            height3 = len(next_seed_y3_list)
            height4 = len(next_seed_y4_list)

            # only assign seed if width is relatively large
            if (height3 > height / 2):
                new_seeds.append([x3, int(np.average(next_seed_y3_list))])
            if (height4 > height / 2):
                new_seeds.append([x4, int(np.average(next_seed_y4_list))])
        elif self._seg_type == SegmentType.sagittal_front:
            sag_new_size = np.count_nonzero(new_filtered_slice)
        elif self._seg_type == SegmentType.sagittal:
            sag_new_size = np.count_nonzero(new_filtered_slice | seed)

        return total_coord, sag_new_size, new_centre, new_seeds

    def __prepare_seed(self, img_slice, centre, seeds_previous, slice_num):
        if SegmentType.is_axial_seg(self._seg_type):
            if self._normalized:
                img_slice = sitk.Cast(sitk.RescaleIntensity(img_slice),
                                      sitk.sitkUInt8)
            # make new image for putting seed in
            seed = sitk.Image(img_slice.GetSize(), sitk.sitkUInt8)
            seed.CopyInformation(img_slice)
            # add original seed and additional seeds three pixels apart
            spacing = 3
            for j in range(-1, 2):
                seed_with_space = centre[0] + spacing*j
                seed[(seed_with_space, centre[1])] = 1

            if self._seg_type == SegmentType.ascending_aorta:
                for s in seeds_previous:
                    seed[s] = 1
            seed = sitk.BinaryDilate(seed, [3] * 2)
        elif self._seg_type == SegmentType.sagittal:
            seed = self._processing_image[slice_num, :, :]
        else:
            seed = self._processing_image[:, slice_num, :]
        return seed

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
