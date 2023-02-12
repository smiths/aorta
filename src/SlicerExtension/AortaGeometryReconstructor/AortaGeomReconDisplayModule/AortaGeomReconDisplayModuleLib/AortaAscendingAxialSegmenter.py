from AortaGeomReconDisplayModuleLib.AortaAxialSegmenter\
    import AortaAxialSegmenter
import SimpleITK as sitk
import numpy as np


class AortaAscendingAxialSegmenter(AortaAxialSegmenter):

    def __init__(
            self, starting_slice, aorta_centre, num_slice_skipping,
            qualified_coef, cropped_image, processing_image):
        self._processing_image = processing_image

        super().__init__(starting_slice, aorta_centre, num_slice_skipping,
                         qualified_coef, cropped_image)

    def __get_overlap(self, img1, i):
        img2 = self._cropped_image[:, :, i]
        overlap = np.count_nonzero(img1 * img2)

        if (overlap <= 0):
            img2 = self._cropped_image[:, :, i + 1]
            overlap = np.count_nonzero(img1 * img2)

        if (overlap <= 0):
            img2 = self._cropped_image[:, :, i + 2]
            overlap = np.count_nonzero(img1 * img2)

        return (overlap > 0)

    def __segmentation(self, top_to_bottom):
        if top_to_bottom:
            fully_seg_slice, self._original_size, centre_previous, _, _, \
                self._seeds = self.__circle_filter(
                    self._starting_slice, self._aorta_centre, [])

            previous_size = self._original_size
            seeds_previous = self._seeds

            # assign both the circle from the ascending aorta
            # and descending aorta to the current slice
            self._processing_image[:, :, self._starting_slice] = \
                (fully_seg_slice > 0) \
                | self._processing_image[:, :, self._starting_slice]
            start = self._starting_slice
            end = -1
            step = -1
        else:
            # reset values to correspond with the seed value's slice
            centre_previous = self._aorta_centre
            seeds_previous = self._seeds
            previous_size = self._original_size

            # factor size that starts like normal,
            # but may change depending on overlap
            factor_size_overlap = self._qualified_coef
            decreasing_size = False
            start = self._starting_slice
            end = self._cropped_image.GetDepth()
            previous_size = self._original_size
            step = 1

        # counts how many slices have been skipped
        counter = 0
        num_skips = 3
        more_circles = True
        # goes from current slice to the bottom of the ascending aorta
        # (opposite direction from the arch)

        for sliceNum in range(start, end, step):
            if (more_circles):
                # perform segmentation on slice i

                seg, total_coord, centre, l, u, seeds = self.__circle_filter(
                    sliceNum, centre_previous, seeds_previous)

                if not top_to_bottom:
                    if (self.__get_overlap(seg > 0, sliceNum)):
                        factor_size_overlap = 2.8
                    else:
                        factor_size_overlap = self._qualified_coef
                    if (decreasing_size):
                        # if size of segmentation is decreasing,
                        # try to maintain decreasing nature
                        factor_size_overlap = 1.2
                    is_new_center_qualified = (
                        total_coord >
                        1 / self._qualified_coef * previous_size
                    )
                    is_new_center_qualified = (
                        is_new_center_qualified
                        and (total_coord < factor_size_overlap * previous_size)
                        and (total_coord < 4 * self._original_size)
                    )
                else:

                    is_new_center_qualified = (
                        total_coord >
                        (self._original_size / self._qualified_coef)
                    )
                    is_new_center_qualified = (
                        is_new_center_qualified
                        and total_coord < self._qualified_coef
                        * self._original_size
                        and total_coord < 2 * previous_size
                    )

                if is_new_center_qualified:
                    counter = 0
                    self._processing_image[:, :, sliceNum] = (
                        (seg > 0)
                        | self._processing_image[:, :, sliceNum]
                    )
                    centre_previous = centre
                    seeds_previous = seeds

                    # check for double size
                    if not top_to_bottom:
                        if total_coord > 2*self._original_size:
                            if (total_coord < previous_size):
                                decreasing_size = True

                # otherwise skip slice and don't change previous centre
                # and seed values
                else:
                    counter += 1
                    if (counter >= num_skips):
                        more_circles = False

            previous_size = total_coord

    def begin_segmentation(self):

        self._segment_filter = sitk.ThresholdSegmentationLevelSetImageFilter()
        self._segment_filter.SetMaximumRMSError(0.02)
        self._segment_filter.SetNumberOfIterations(1000)
        self._segment_filter.SetCurvatureScaling(.5)
        self._segment_filter.SetPropagationScaling(1)
        self._segment_filter.ReverseExpansionDirectionOn()

        # SEGMENT FROM SEED VALUE TO BOTTOM OF THE ASCENDING AORTA
        print("Ascending aorta segmentation - top to bottom started")
        self.__segmentation(True)
        print("Ascending aorta segmentation - top to bottom finished")

        print("Ascending aorta segmentation - bottom to top started")
        self.__segmentation(False)
        print("Ascending aorta segmentation - bottom to top finished")

    def __circle_filter(self, sliceNum, centre, seeds_previous):
        # def circle_filter_arch(i, centre, seeds, image_type="reg"):
        # set slice
        imgSlice = self._cropped_image[:, :, sliceNum]

        # make new image for putting seed in
        seg_2d = sitk.Image(imgSlice.GetSize(), sitk.sitkUInt8)
        seg_2d.CopyInformation(imgSlice)

        # add original seed and additional seeds three pixels apart
        spacing = 3

        for j in range(-1, 2):
            seed_with_space = centre[0] + spacing * j
            seg_2d[(seed_with_space, centre[1])] = 1

        # add seeds from previous slice

        for seed in seeds_previous:
            seg_2d[seed] = 1
        seg_2d = sitk.BinaryDilate(seg_2d, [3] * 2)

        # determine threshold values based on seed location
        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(imgSlice, seg_2d)

        factor = 3.5
        lower_threshold = stats.GetMean(1) - factor*stats.GetSigma(1)
        upper_threshold = stats.GetMean(1) + factor*stats.GetSigma(1)

        # use filter to apply threshold to image
        init_ls = sitk.SignedMaurerDistanceMap(
            seg_2d, insideIsPositive=True, useImageSpacing=True)

        # segment the aorta using the seed values and threshold values
        self._segment_filter.SetLowerThreshold(lower_threshold)
        self._segment_filter.SetUpperThreshold(upper_threshold)
        ls = self._segment_filter.Execute(init_ls, sitk.Cast(imgSlice,
                                          sitk.sitkFloat32))

        # make array from segmentation
        nda = sitk.GetArrayFromImage(ls > 0)

        # Calculate the centre of the segmentation
        # by 1st getting the average y value.
        # Then, finding the average x value on that y-value to ensure
        # there is an actual point there
        # Also determine 4 seed values by going 25% outwards
        # in the x, -x, y and -y directions.
        centre_new = [0, 0]

        # calculate the average y value of the pixels
        # and the height (Δy) of the aorta
        list_y, _ = np.where(nda == 1)
        max_y = max(list_y)
        min_y = min(list_y)

        total_coord = len(list_y)

        centre_new[1] = int(sum(list_y) / len(list_y))
        height = max_y - min_y

        # calculate the average x value of the pixels
        # along the predetermined y value.
        # also calulate the width (Δx) along that height
        list_x = np.where(nda[centre_new[1]] == 1)[0]
        width = len(list_x)

        # if there were no pixels along that y value for whatever reason,
        # just get the centre of gravity of the segmentation
        # by finding the overall average x value
        if (width == 0):
            _, list_x = np.where(nda == 1)
        centre_new[0] = int(np.average(list_x))

        # determine next seed values; y1,x1, y2,x2 are vertical values;
        # y3,x3, y4,x4 are horizontal the seed values are 25% outwards
        # from the centre.
        # 25% refers to 25% of the entire width or height of the segmentation
        seeds = []

        # vertical
        y1 = int((max_y + centre_new[1])/2)
        y2 = int((min_y + centre_new[1])/2)

        # find x values along those y values

        next_seed_x1_list = np.where(nda[y1] == 1)[0]
        next_seed_x2_list = np.where(nda[y2] == 1)[0]
        width1 = len(next_seed_x1_list)
        width2 = len(next_seed_x2_list)

        # only assign seed if width is relatively large
        if (width1 > width / 2):
            seeds.append([int(np.average(next_seed_x1_list)), y1])
        if (width2 > width / 2):
            seeds.append([int(np.average(next_seed_x2_list)), y2])

        # horizontal
        x3 = int(centre_new[0] + width/2)
        x4 = int(centre_new[0] - width/2)

        # find y values along those x values
        next_seed_y3_list = np.where(nda[:, x3] == 1)[0]
        next_seed_y4_list = np.where(nda[:, x4] == 1)[0]
        height3 = len(next_seed_y3_list)
        height4 = len(next_seed_y4_list)

        # only assign seed if width is relatively large
        if (height3 > height / 2):
            seeds.append([x3, int(np.average(next_seed_y3_list))])
        if (height4 > height / 2):
            seeds.append([x4, int(np.average(next_seed_y4_list))])

        return ls, total_coord, centre_new, \
            lower_threshold, upper_threshold, seeds
