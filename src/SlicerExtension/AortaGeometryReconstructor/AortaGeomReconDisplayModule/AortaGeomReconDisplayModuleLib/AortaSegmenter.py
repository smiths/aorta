import SimpleITK as sitk
import numpy as np
from enum import Enum


class SegmentType(Enum):
    descending_aorta = 1
    ascending_aorta = 2
    sagittal_front = 3
    sagittal = 4

    def is_axial_segmentation(seg_type):
        return (seg_type == SegmentType.descending_aorta
                or seg_type == SegmentType.ascending_aorta)

    def is_sagittal_segmentation(seg_type):
        return (seg_type == SegmentType.sagittal_front
                or seg_type == SegmentType.sagittal)

    def __repr__(self):
        return f'{self.name.replace("_"," ")} segmentation'


class SegmentDirection(Enum):
    S_to_I = 1
    I_to_S = 2


class PixelValue():
    white_pixel = 1
    black_pixel = 0


class AortaSegmenter():

    def __init__(
            self, cropped_image, starting_slice, aorta_centre,
            num_slice_skipping, processing_image, seg_type,
            is_normalized=False, segmentation_factor=2.2,
            is_output_binary=True
    ):
        self._starting_slice = starting_slice
        self._aorta_centre = aorta_centre
        self._num_slice_skipping = num_slice_skipping
        self._seg_type = seg_type
        self._processing_image = processing_image
        self._segmentation_factor = segmentation_factor
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

        return (overlap > PixelValue.black_pixel)

    @property
    def segmentation_factor(self):
        return self._segmentation_factor

    @property
    def cropped_image(self):
        return self._cropped_image

    @segmentation_factor.setter
    def segmentation_factor(self, segmentation_factor):
        self._segmentation_factor = segmentation_factor

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

        self._total_pixels = (
            self._processing_image.GetHeight()
            * self._processing_image.GetDepth()
        )

        max_aorta_slice = 5000
        # minimum number of pixels on a slice for us
        # to run the sagittal function
        self._base_pixel_value = self._total_pixels / max_aorta_slice

        # Get more values from the seed slice
        new_filtered_slice, seed_slice = self.__circle_filter(
            self._starting_slice, self._aorta_centre, [])

        # Initialize seed values
        # [total_coord, new_size, new_centre, new_seeds]
        var_list = list(self.__count_pixels(new_filtered_slice, seed_slice))
        self._processing_image[
            :, :, self._starting_slice] = new_filtered_slice
        self._original_size = var_list[0]
        self._seeds = var_list[3]

        # SEGMENT FROM SEED VALUE TO BOTTOM OF THE AORTA
        print("{} - top to bottom started".format(self._seg_type))
        self.__segmentation(SegmentDirection.S_to_I)
        print("{} - top to bottom finished".format(self._seg_type))

        print("{} - bottom to top started".format(self._seg_type))
        self.__segmentation(SegmentDirection.I_to_S)
        print("{} - bottom to top finished".format(self._seg_type))

        if self._seg_type == SegmentType.descending_aorta:
            # Fill in missing slices of descending aorta
            self.__filling_missing_slices()

    def __segmentation(self, seg_dir):
        # initialize loop variables
        if seg_dir == SegmentDirection.S_to_I:
            end = -1
            step = -1
            skipped_slice_counter = 0
        else:
            end = self._cropped_image.GetDepth()
            step = 1
            skipped_slice_counter = len(self._skipped_slices)

        decreasing_size = False
        start = self._starting_slice
        centre_previous = self._aorta_centre
        seeds_previous = self._seeds
        previous_size = self._original_size
        more_circles = True

        for sliceNum in range(start, end, step):
            if (more_circles):
                # perform segmentation on slice i
                # Get new filtered slice and the seed slice
                new_filtered_slice, seed_slice = self.__circle_filter(
                    sliceNum, centre_previous, seeds_previous)

                # Get more determinants
                # [total_coord, new_size, new_centre, new_seeds]
                var_list = list(
                    self.__count_pixels(new_filtered_slice, seed_slice)
                )
                total_coord = var_list[0]

                is_new_centre_qualified = self.__is_new_slice_qualified(
                    new_filtered_slice, seg_dir, sliceNum,
                    decreasing_size, total_coord, previous_size)
                # If qualified, replacing processing image slice
                if is_new_centre_qualified:
                    skipped_slice_counter = 0
                    if self._seg_type == SegmentType.descending_aorta:
                        self._processing_image[:, :, sliceNum] = (
                            new_filtered_slice)
                    else:
                        self._processing_image[:, :, sliceNum] = (
                            new_filtered_slice
                            | self._processing_image[:, :, sliceNum]
                        )
                    centre_previous = var_list[2]
                    seeds_previous = var_list[3]

                    # check for double size
                    if seg_dir == SegmentDirection.I_to_S:
                        if total_coord > self._original_size * 2:
                            if (total_coord < previous_size):
                                decreasing_size = True

                # otherwise skip slice and don't change previous centre
                # and seed values
                else:
                    skipped_slice_counter += 1
                    if (skipped_slice_counter >= self._num_slice_skipping):
                        more_circles = False
                        if not self._is_output_binary:
                            self._processing_image[:, :, sliceNum] = sitk.Cast(
                                self._cropped_image_255[:, :, sliceNum],
                                sitk.sitkVectorUInt8
                            )

            previous_size = total_coord

    def __is_new_slice_qualified(
        self, new_slice, seg_dir, slice_num, decreasing_size,
        total_coord, previous_size
    ):
        is_new_centre_qualified = False
        if self._seg_type == SegmentType.descending_aorta:
            factor = self._segmentation_factor

            if seg_dir == SegmentDirection.I_to_S:
                factor += 0.3

            is_new_centre_qualified = (
                (total_coord < 2 * previous_size)
                and
                (total_coord < factor * self._original_size)
            )
            if seg_dir == SegmentDirection.I_to_S:
                is_new_centre_qualified = (
                    is_new_centre_qualified
                    and total_coord > (1 / factor * self._original_size)
                )
            else:
                is_new_centre_qualified = (
                    is_new_centre_qualified
                    and total_coord > (1 / factor * previous_size)
                )
        elif self._seg_type == SegmentType.ascending_aorta:
            if seg_dir == SegmentDirection.I_to_S:
                if (self.__get_overlap(new_slice, slice_num)):
                    # We are going to accept a larger slice
                    # because overlap still exists from current slice
                    # to next two slices
                    factor_size_overlap = 2.8
                else:
                    factor_size_overlap = self._segmentation_factor
                if (decreasing_size):
                    # if size of segmentation is decreasing,
                    # try to maintain decreasing nature
                    factor_size_overlap = 1.2
                is_new_centre_qualified = (
                    total_coord >
                    1 / self._segmentation_factor * previous_size
                ) and (
                    (total_coord < factor_size_overlap * previous_size)
                    and (total_coord < 4 * self._original_size)
                )
            elif seg_dir == SegmentDirection.S_to_I:
                is_new_centre_qualified = (
                    total_coord >
                    (1 / self._segmentation_factor)
                    * self._original_size
                ) and (
                    total_coord <
                    self._segmentation_factor * self._original_size
                    and total_coord < 2 * previous_size
                )
        else:
            is_new_centre_qualified = (
                np.count_nonzero(self._segmented_image[slice_num, :, :])
                > self._base_pixel_value
            )
        return is_new_centre_qualified

    def __circle_filter(self, slice_num, centre, seeds_previous):
        # factor, size_factor, current_size
        img_slice = self._cropped_image[:, :, slice_num]
        seed = self.__prepare_seed(
            img_slice, centre, seeds_previous, slice_num)

        # determine threshold values based on seed location
        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(img_slice, seed)

        # #TODO is this factor changeable?
        # Factor should be adjustable for threshold
        factor = 3.5
        lower_threshold = (
            stats.GetMean(PixelValue.white_pixel)
            - factor*stats.GetSigma(PixelValue.white_pixel)
        )
        upper_threshold = (
            stats.GetMean(PixelValue.white_pixel)
            + factor*stats.GetSigma(PixelValue.white_pixel)
        )

        # use filter to apply threshold to image
        init_ls = sitk.SignedMaurerDistanceMap(
            seed, insideIsPositive=True, useImageSpacing=True)

        # segment the aorta using the seed values and threshold values
        self._segment_filter.SetLowerThreshold(lower_threshold)
        self._segment_filter.SetUpperThreshold(upper_threshold)
        ls = self._segment_filter.Execute(init_ls, sitk.Cast(img_slice,
                                          sitk.sitkFloat32))

        new_filtered_slice = self.__get_new_slice(ls, seed, slice_num)

        return new_filtered_slice, seed

    def __get_new_slice(self, ls, seed, slice_num):
        fully_seg_slice = ls > PixelValue.black_pixel
        if self._seg_type == SegmentType.descending_aorta:
            # assign segmentation to fully_seg_slice
            if not self._is_output_binary:
                fully_seg_slice = sitk.LabelOverlay(
                    self._cropped_image[:, :, slice_num],
                    ls > PixelValue.black_pixel
                )
        elif self._seg_type != SegmentType.ascending_aorta:
            sag_seg = ls > PixelValue.black_pixel
            fully_seg_slice = seed | sag_seg
        return fully_seg_slice

    def __count_pixels(self, ls, seed):
        new_seeds = None
        new_centre = None
        total_coord = None
        new_size = None
        sag_seg = ls > PixelValue.black_pixel
        if self._seg_type == SegmentType.descending_aorta:
            # get array from segmentation
            nda = sitk.GetArrayFromImage(ls > PixelValue.black_pixel)

            # calculate average x and average y values,
            # to get the new centre value
            list_x, list_y = np.where(nda == PixelValue.white_pixel)
            new_centre = (int(np.average(list_y)), int(np.average(list_x)))
            total_coord = len(list_x)
        elif self._seg_type == SegmentType.ascending_aorta:
            # make array from segmentation
            nda = sitk.GetArrayFromImage(ls > PixelValue.black_pixel)

            # Calculate the centre of the segmentation
            # First getting the average y value.
            # Then, finding the average x value on that y-value to ensure
            # there is an actual point there
            # Also determine 4 seeds values by going 25% outwards
            # in the x, -x, y and -y directions.
            new_centre = [0, 0]

            # calculate the average y value of the pixels
            # and the height (Δy) of the aorta
            list_y, _ = np.where(nda == PixelValue.white_pixel)
            max_y = max(list_y)
            min_y = min(list_y)
            total_coord = len(list_y)

            new_centre[1] = int(sum(list_y) / len(list_y))
            height = max_y - min_y

            # calculate the average x value of the pixels
            # along the predetermined y value.
            # also calulate the width (Δx) along that height
            list_x = np.where(
                nda[new_centre[1]] == PixelValue.white_pixel
            )[0]

            width = len(list_x)

            # if there were no pixels along that y value for whatever reason,
            # just get the centre of gravity of the segmentation
            # by finding the overall average x value
            if (width == 0):
                _, list_x = np.where(nda == PixelValue.white_pixel)
            new_centre[0] = int(np.average(list_x))

            # determine next seed values; y1,x1, y2,x2 are vertical values;
            # y3,x3, y4,x4 are horizontal the seed values are 25% outwards
            # from the centre.
            # 25% refers to 25% of the entire width or
            # height of the segmentation
            new_seeds = []

            # vertical
            y1 = int((max_y + new_centre[1])/2)
            y2 = int((min_y + new_centre[1])/2)

            # find x values along those y values

            next_seed_x1_list = np.where(
                nda[y1] == PixelValue.white_pixel)[0]

            next_seed_x2_list = np.where(
                nda[y2] == PixelValue.white_pixel)[0]

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
                nda[:, x3] == PixelValue.white_pixel)[0]

            next_seed_y4_list = np.where(
                nda[:, x4] == PixelValue.white_pixel)[0]

            height3 = len(next_seed_y3_list)
            height4 = len(next_seed_y4_list)

            # only assign seed if width is relatively large
            if (height3 > height / 2):
                new_seeds.append([x3, int(np.average(next_seed_y3_list))])
            if (height4 > height / 2):
                new_seeds.append([x4, int(np.average(next_seed_y4_list))])
        elif self._seg_type == SegmentType.sagittal_front:
            new_size = np.count_nonzero(sag_seg | seed)
        else:
            new_size = np.count_nonzero(sag_seg)

        return total_coord, new_size, new_centre, new_seeds

    def __prepare_seed(self, img_slice, centre, seeds_previous, slice_num):
        if SegmentType.is_sagittal_segmentation(self._seg_type):
            seed = self._segmented_image[slice_num, :, :]
        else:
            if self._normalized:
                img_slice = sitk.Cast(sitk.RescaleIntensity(img_slice),
                                      sitk.sitkUInt8)
            # make new image for putting seed in
            seed = sitk.Image(img_slice.GetSize(), sitk.sitkUInt8)
            seed.CopyInformation(img_slice)
            # add original seed and additional seeds three pixels apart
            spacing = 3
            for j in range(-1, 2):
                one = centre[0] + spacing*j
                seed[(one, centre[1])] = 1

            if self._seg_type == SegmentType.ascending_aorta:
                for s in seeds_previous:
                    seed[s] = 1
            seed = sitk.BinaryDilate(seed, [3] * 2)

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
