from AortaGeomReconDisplayModuleLib.AortaAxialSegmenter \
    import AortaAxialSegmenter
import SimpleITK as sitk
import numpy as np


class AortaDescendingAxialSegmenter(AortaAxialSegmenter):

    def __init__(self, startingSlice, aortaCentre, numSliceSkipping,
                 segmentationFactor, segmentingImage,
                 normalized=False, outputBinary=True):
        super().__init__(startingSlice=startingSlice, aortaCentre=aortaCentre,
                         numSliceSkipping=numSliceSkipping,
                         segmentationFactor=segmentationFactor,
                         segmentingImage=segmentingImage,
                         normalized=normalized,
                         outputBinary=outputBinary)

    """Segmentation helper function, return filtered slice
       and new aorta centre.
    """
    def __circle_filter(self, sliceNum, centre):
        imgSlice = self._segmenting_image[:, :, sliceNum]

        if self._normalized:
            imgSlice = sitk.Cast(
                sitk.RescaleIntensity(imgSlice), sitk.sitkUInt8)

        # make new image for putting seed in
        seg_2d = sitk.Image(imgSlice.GetSize(), sitk.sitkUInt8)
        seg_2d.CopyInformation(imgSlice)

        # add original seed and additional seeds three pixels apart
        spacing = 3
        for j in range(-1, 2):
            one = centre[0] + spacing*j
            seg_2d[(one, centre[1])] = 1

        seg_2d = sitk.BinaryDilate(seg_2d, [3] * 2)

        # determine threshold values based on seed location
        factor = 3.5
        stats = sitk.LabelStatisticsImageFilter()
        stats.Execute(imgSlice, seg_2d)
        lower_threshold = stats.GetMean(1) - factor*stats.GetSigma(1)
        upper_threshold = stats.GetMean(1) + factor*stats.GetSigma(1)

        # use filter to apply threshold to image
        init_ls = sitk.SignedMaurerDistanceMap(
            seg_2d, insideIsPositive=True, useImageSpacing=True)

        # segment the aorta using the seed values and threshold values
        self._segment_filter.SetLowerThreshold(lower_threshold)
        self._segment_filter.SetUpperThreshold(upper_threshold)

        ls = self._segment_filter.Execute(
            init_ls, sitk.Cast(imgSlice, sitk.sitkFloat32))

        # assign segmentation to fully_seg_slice
        if self._is_output_binary:
            fully_seg_slice = ls > 0
        else:
            fully_seg_slice = sitk.LabelOverlay(
                self._segmenting_image[:, :, sliceNum], ls > 0)

        # get array from segmentation
        ndimension_array = sitk.GetArrayFromImage(ls > 0)

        # calculate average x and average y values,
        # to get the new centre value
        list_x, list_y = np.where(ndimension_array == 1)

        centre_new = (int(np.average(list_y)), int(np.average(list_x)))

        return fully_seg_slice, len(list_x), centre_new

    def segmentation(self, factor, top_to_bottom):

        if top_to_bottom:
            fully_seg_slice, total_coord, _ = self.__circle_filter(
                self._starting_slice, self._aorta_centre)

            self._segmented_image[:, :, self._starting_slice] = fully_seg_slice
            self._original_size = total_coord
            previous_size = total_coord
            # counts how many slices have been skipped
            counter = 0
            startingSlice = self._starting_slice
            endingSlice = -1
            step = -1
        else:
            startingSlice = self._starting_slice
            endingSlice = self._segmenting_image.GetDepth()
            previous_size = self._original_size
            step = 1

        centre_previous = self._aorta_centre
        more_circles = True
        counter = len(self._skipped_slices)

        for sliceNum in range(startingSlice, endingSlice, step):
            if (more_circles):

                # perform segmentation on slice i
                fully_seg_slice, total_coord, centre = self.__circle_filter(
                    sliceNum, centre_previous)
                # determine whether the size of this slice "qualifies" it
                # to be accurate
                is_new_center_qualified = (
                    (total_coord < 2 * previous_size)
                    and (total_coord < factor * self._original_size)
                )
                if top_to_bottom:
                    is_new_center_qualified = (
                        is_new_center_qualified
                        and total_coord > (1 / factor * self._original_size)
                    )
                else:
                    is_new_center_qualified = (
                        is_new_center_qualified
                        and total_coord > (1 / factor * previous_size)
                    )

                if is_new_center_qualified:
                    counter = 0
                    # add slice to new_image
                    self._segmented_image[:, :, sliceNum] = fully_seg_slice
                    centre_previous = centre
                else:
                    counter += 1
                    self._skipped_slices.append(sliceNum)
                    # myshow(sitk.LabelOverlay(
                    # cropped_images[ct_number][:,:,i], fully_seg_slice))
                    if (counter >= self._num_slice_skipping):
                        more_circles = False

                        # when it gets to this point,
                        # remove the last 3 skipped slices
                        self._skipped_slices = self._skipped_slices[::-3]

                    # Ignore skipped slice by not assigning new slice back to
                    # segmenting image
                    total_coord = previous_size

            elif not self._is_output_binary:
                self._segmented_image[:, :, sliceNum] = sitk.Cast(
                    self._segmenting_image_255[:, :, sliceNum],
                    sitk.sitkVectorUInt8)

            previous_size = total_coord

    def begin_segmentation(self):
        # Descending Aorta Segmentation
        self._segment_filter = sitk.ThresholdSegmentationLevelSetImageFilter()
        self._segment_filter.SetMaximumRMSError(0.02)
        self._segment_filter.SetNumberOfIterations(1000)
        self._segment_filter.SetCurvatureScaling(.5)
        self._segment_filter.SetPropagationScaling(1)
        self._segment_filter.ReverseExpansionDirectionOn()
        self._skipped_slices = []
        self._segmented_image = sitk.Image(
            self._segmenting_image.GetSize(), sitk.sitkUInt8)
        self._segmented_image.CopyInformation(self._segmenting_image)
        print(self._segmenting_image.GetSize())
        print("Descending aorta segmentation - top to bottom started")
        self.segmentation(self._segmentation_factor, True)
        print("Descending aorta segmentation - top to bottom finished")

        print("Descending aorta segmentation - bottom to top started")
        self.segmentation(self._segmentation_factor + 0.3, False)
        print("Descending aorta segmentation - bottom to top finished")

        # Fill in missing slices of descending aorta
        for index in range(len(self._skipped_slices)):
            # ensure there is at least one slice
            # before and after the skipped slice
            slice_num = self._skipped_slices[index]
            if (slice_num > 0 and slice_num <
                    self._segmenting_image.GetDepth() - 1):
                next_index = index + 1

                # if there are two skipped slices in a row,
                # take the overlap of the segmentations
                # before and after those two. otherwise just take the
                # overlap of the segmentations around the skipped slice
                if (len(self._skipped_slices) > next_index):
                    next_slice = self._skipped_slices[next_index]

                    if (next_slice == slice_num + 1 and next_slice
                            < self._segmenting_image.GetDepth() - 1):
                        self._segmented_image[:, :, slice_num] = (
                            self._segmented_image[:, :, slice_num - 1]
                            + self._segmented_image[:, :, next_slice + 1] > 1
                        )
                        self._segmented_image[:, :, next_slice] = \
                            self._segmented_image[:, :, slice_num]
                    else:
                        self._segmented_image[:, :, slice_num] = (
                            self._segmented_image[:, :, slice_num - 1]
                            + self._segmented_image[:, :, slice_num + 1] > 1
                        )
                else:
                    self._segmented_image[:, :, slice_num] = (
                        self._segmented_image[:, :, slice_num - 1]
                        + self._segmented_image[:, :, slice_num + 1] > 1)
