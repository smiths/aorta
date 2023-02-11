import os
import sys
project_path = os.path.abspath('.')
AGR_module_path = os.path.join(project_path, "src/SlicerExtension/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeometryReconstructor/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeomReconDisplayModule")
sys.path.insert(0, AGR_module_path)

from AortaGeomReconDisplayModuleLib.AortaAxialSegmenter \
    import AortaAxialSegmenter
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums \
    import SegmentDirection as SegDir
import SimpleITK as sitk
import numpy as np


class AortaDescendingAxialSegmenter(AortaAxialSegmenter):

    def __init__(self, starting_slice, aorta_centre, num_slice_skipping,
                 qualified_slice_factor, cropped_image,
                 normalized=False, outputBinary=True):
        super().__init__(starting_slice=starting_slice,
                         aorta_centre=aorta_centre,
                         num_slice_skipping=num_slice_skipping,
                         qualified_slice_factor=qualified_slice_factor,
                         cropped_image=cropped_image,
                         normalized=normalized,
                         output_binary=outputBinary)

    """Segmentation helper function, return filtered slice
       and new aorta centre.
    """
    def __circle_filter(self, sliceNum, centre):
        imgSlice = self._cropped_image[:, :, sliceNum]

        # if self._normalized:
        #     imgSlice = sitk.Cast(
        #         sitk.RescaleIntensity(imgSlice), sitk.sitkUInt8)

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
                self._cropped_image[:, :, sliceNum], ls > 0)

        # get array from segmentation
        ndimension_array = sitk.GetArrayFromImage(ls > 0)

        # calculate average x and average y values,
        # to get the new centre value
        list_x, list_y = np.where(ndimension_array == 1)

        centre_new = (int(np.average(list_y)), int(np.average(list_x)))

        return fully_seg_slice, len(list_x), centre_new

    def segmentation(self):
        centre_previous = self._aorta_centre
        more_circles = True
        counter = len(self._skipped_slices)

        for sliceNum in range(self._start, self._end, self._step):
            if (more_circles):

                # perform segmentation on slice i
                fully_seg_slice, total_coord, centre = self.__circle_filter(
                    sliceNum, centre_previous)

                # determine whether the size of this slice "qualifies" it
                # to be accurate
                cmp_prev_size = (total_coord < 2*self._previous_size)
                if self._seg_dir == SegDir.Superior_to_Inferior:
                    slicer_larger_than = (
                        total_coord >
                        (self._original_size/self.qualified_slice_factor)
                    )
                    cmp_original_size = (
                        total_coord <
                        (self._original_size*self.qualified_slice_factor)
                    )
                else:
                    slicer_larger_than = (
                        total_coord >
                        (self._previous_size/self.qualified_slice_factor)
                    )
                    cmp_original_size = (
                        total_coord <
                        (self._original_size*
                            (self.qualified_slice_factor+0.3)
                        )
                    )

                is_new_center_qualified = (
                    cmp_prev_size
                    and slicer_larger_than
                    and cmp_original_size
                )

                if is_new_center_qualified:
                    counter = 0
                    self._processing_image[:, :, sliceNum] = fully_seg_slice
                    centre_previous = centre
                else:
                    counter += 1
                    self._skipped_slices.append(sliceNum)
                    if (counter >= self._num_slice_skipping):
                        more_circles = False

                        # when it gets to this point,
                        # remove the last 3 skipped slices
                        self._skipped_slices = self._skipped_slices[::-3]

                    # Ignore skipped slice by not assigning new slice back to
                    # segmenting image
                    total_coord = self._previous_size

            elif not self._is_output_binary:
                self._processing_image[:, :, sliceNum] = sitk.Cast(
                    self._cropped_image_255[:, :, sliceNum],
                    sitk.sitkVectorUInt8)

            self._previous_size = total_coord

    def initializeParameterStoI(self):
        fully_seg_slice, total_coord, _ = self.__circle_filter(
            self._starting_slice, self._aorta_centre)
        self._original_size = total_coord
        self._previous_size = total_coord
        self._processing_image[
            :, :, self._starting_slice] = fully_seg_slice
        self._skipped_counter = 0
        self._start = self._starting_slice
        self._end = -1
        self._step = -1
        self._seg_dir = SegDir.Superior_to_Inferior

    def initializeParameterItoS(self):
        self._start = self._starting_slice
        self._end = self._cropped_image.GetDepth()
        self._previous_size = self._original_size
        self._step = 1
        self._seg_dir = SegDir.Inferior_to_Superior

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

        self.initializeParameterStoI()
        print("Descending aorta segmentation - top to bottom started")
        self.segmentation()
        print("Descending aorta segmentation - top to bottom finished")


        self.initializeParameterItoS()
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
