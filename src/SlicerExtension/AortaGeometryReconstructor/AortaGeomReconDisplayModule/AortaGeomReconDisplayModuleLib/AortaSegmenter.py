import os
import sys

import SimpleITK as sitk
import numpy as np

# for design document
os.environ["OMP_NUM_THREADS"] = '1'
project_path = os.path.abspath('.')
AGR_module_path = os.path.join(project_path, "src/SlicerExtension/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeometryReconstructor/")
AGR_module_path = os.path.join(AGR_module_path, "AortaGeomReconDisplayModule")
sys.path.insert(0, AGR_module_path)

# for debugging and numpy print operation
np.set_printoptions(threshold=sys.maxsize)

from sklearn.cluster import KMeans

# import helpers enumeration classes
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import SegmentDirection as SegDir # noqa
from AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import PixelValue # noqa


class AortaSegmenter():
    """This class is used to perform Descending or Ascending aorta segmentation.
    Attributes:
        
        cropped_image (SITK::image): The original image that the user has only perform cropping.

        des_seed (tuple): A tuple of 3 integers indicates the centre of Descending aorta on an axial slice.

        asc_seed (tuple): A tuple of 3 integers indicates the centre of Ascending aorta on an axial slice.

        num_slice_skipping (int): The number of slice allowed to consecutively skip by the algorithm.

        stop_limit (float): The number to signal the stopping point in the segmentation loop.

        threshold_coef (float): This coefficient controls the lower and upper pixel intensity threshold.

        kernel_size (int): The size used to generate circle like shape for the label map. Large kernel size implies larger initial circle size.

        rms_error (float): The rms error for ThresholdSegmentationLevelSetImageFilter.
        
        no_ite (int): The maximum iterations for ThresholdSegmentationLevelSetImageFilter.

        curvature_scaling (float): The weight of curvature on calculating the speed term for ThresholdSegmentationLevelSetImageFilter.

        propagation_scaling (float): The weight of propagation on calculating the speed term for ThresholdSegmentationLevelSetImageFilter.

    """ # noqa

    def __init__(
            self, cropped_image, des_seed, asc_seed, stop_limit=10,
            threshold_coef=3, kernel_size=6, rms_error=0.02, no_ite=600,
            curvature_scaling=2, propagation_scaling=0.5, debug=False
    ):
        self._des_seed = des_seed
        self._des_prev_centre = des_seed[:2]
        self._asc_seed = asc_seed
        self._asc_prev_centre = asc_seed[:2]
        self._des_max_diff = 0
        self._asc_max_diff = 0
        self._stop_limit = stop_limit
        self._threshold_coef = threshold_coef
        self._cropped_image = cropped_image
        self._kernel_size = kernel_size
        self._debug_mod = debug
        nda = sitk.GetArrayFromImage(self._cropped_image[:,:,869])
        self._stats_filter = sitk.LabelStatisticsImageFilter()
        self._segment_filter = sitk.ThresholdSegmentationLevelSetImageFilter()
        self._segment_filter.SetMaximumRMSError(rms_error)
        self._segment_filter.SetNumberOfIterations(no_ite)
        self._segment_filter.SetCurvatureScaling(curvature_scaling)
        self._segment_filter.SetPropagationScaling(propagation_scaling)
        self._segment_filter.ReverseExpansionDirectionOn()
        self._skipped_slices = []
        self._k = 2

        # Initializing processing image
        self._processing_image = sitk.Image(
            self._cropped_image.GetSize(), sitk.sitkUInt8)
        self._processing_image.CopyInformation(self._cropped_image)
        self._seg_dir = None
        self._is_size_decreasing = False

    def begin_segmentation(self):
        """This is the main entry point of the axial segmentation.
        This api should be called to perform aorta segmentation first
        (superior to inferior, then inferior to superior starting from the seed slice).
    
        """ # noqa

        # from superior to inferior, the segmentation starts with the highest slice # noqa
        starting_slice = max(self._des_seed[2], self._asc_seed[2])
        self._start = starting_slice
        self._end = -1
        self._step = -1
        self._seg_dir = SegDir.Superior_to_Inferior

        # SEGMENT FROM SEED VALUE TO BOTTOM OF THE AORTA
        print("top to bottom started")
        self.__segmentation()
        print("top to bottom finished")

        self._seg_dir = SegDir.Inferior_to_Superior
        self._start = starting_slice + 1
        self._k = 2
        self._des_prev_centre = self._des_seed[:2]
        self._asc_prev_centre = self._asc_seed[:2]
        self._end = self._cropped_image.GetDepth()
        self._step = 1

        print("bottom to top started")
        self.__segmentation()
        print("bottom to top finished")

    def __prepare_label_map(self):
        """Create a label map image that has a circle-like shape around the previous descending aorta centre and ascending aorta centre (if any).
        The pixels within the circle are labeled as white pixels (value of 1), the other are labeled as black pixels (value of 0).

        Returns:
            SITK::IMAGE: A label map image that has a circle like shape around the previous descending aorta centre and ascending aorta centre.
        """ # noqa
        label_map = sitk.Image(self._cur_img_slice.GetSize(), sitk.sitkUInt8)
        label_map.CopyInformation(self._cur_img_slice)
        label_map[self._des_prev_centre] = PixelValue.white_pixel.value
        label_map[self._asc_prev_centre] = PixelValue.white_pixel.value
        label_map = sitk.BinaryDilate(label_map, [self._kernel_size] * 2)
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
        self._stats_filter.Execute(self._cur_img_slice, label_map)
        intensity_mean = self._stats_filter.GetMean(
            PixelValue.white_pixel.value)
        std = self._stats_filter.GetSigma(PixelValue.white_pixel.value)
        lower_threshold = (intensity_mean - self._threshold_coef*std)
        upper_threshold = (intensity_mean + self._threshold_coef*std)
        self._segment_filter.SetLowerThreshold(lower_threshold)
        self._segment_filter.SetUpperThreshold(upper_threshold)
        segmented_slice = self._segment_filter.Execute(
            dis_map, sitk.Cast(self._cur_img_slice, sitk.sitkFloat32))
        return segmented_slice, std

    def __segmentation(self):
        """The main loop of the segmentation algorithm.
        For each axial slice, the algorithm performs segmetation with get_image_segment function.
        Next, the algorithm calculates new centroids based on the segmented slice.
        Repeat this process until the stop condition has reached. The stop conditions are:
            1. The new centroid located too far from the previous centroid
            2. The difference of the std of the initial label image and of the final segmented image reaches the stop limit.

        """ # noqa
        for slice_i in range(self._start, self._end, self._step):
            if self._debug_mod and abs(slice_i-self._start) > 10:
                return
            self._cur_img_slice = self._cropped_image[:, :, slice_i]
            segmented_slice, std = self.__get_image_segment()
            new_slice = segmented_slice > PixelValue.black_pixel.value
            candidates = self.__get_new_centroids(new_slice)
            if len(candidates) == 2:
                des_c, asc_c = candidates
            else:
                des_c = candidates[0]
                asc_c = des_c
            if des_c[0] == float("inf"):
                break
            if self._seg_dir == SegDir.Inferior_to_Superior:
                self._stats_filter.Execute(self._cur_img_slice, new_slice)
                new_std = self._stats_filter.GetSigma(
                    PixelValue.white_pixel.value)
                if abs(new_std - std) > self._stop_limit:
                    break
            elif self._k == 2 and self.__is_asc_reaching_heart(asc_c):
                self._asc_prev_centre = self._des_prev_centre
                self._k = 1
                segmented_slice, _ = self.__get_image_segment()
                new_slice = segmented_slice > PixelValue.black_pixel.value
                des_c = self.__get_new_centroids(new_slice)[0]
                asc_c = des_c
            self._des_prev_centre = des_c
            self._asc_prev_centre = asc_c
            self._processing_image[:, :, slice_i] = new_slice

    def __is_asc_reaching_heart(self, asc_c):
        """The stop condition of ascending aorta segmentation from Superior to Inferior direction. Once the segmentation result reaches the heart, the new centroid will locate far from the previous ascending aorta centre.

        Returns:
            Boolean: The distance between new centroid and the previous ascending aorta centroid reaches the stop limit.
        """ # noqa
        dist = self.__get_dist(asc_c, self._asc_prev_centre)
        if dist > self._stop_limit:
            return True
        return False

    def __get_dist(self, p1, p2):
        """Calculate the Euclidean distance between any two points.

        Returns:
            float: The Euclidean distance between p1 and p2.
        """ # noqa
        return np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

    def __get_new_centroids(self, new_slice):
        """Calculate new centroids on the segmented slice.

        Returns:
            (tuple): tuple containing:
                tuple: The new derived centres closest to the previous descending aorta centre
                tuple: The new derived centres closest to the previous ascending aorta centre
        """ # noqa
        nda = sitk.GetArrayFromImage(new_slice)
        list_y_ind, list_x_ind = np.where(nda == PixelValue.white_pixel.value)
        points = np.array(
            [[list_x_ind[i], list_y_ind[i]] for i in range(len(list_y_ind))]
        )
        if len(points) <= 1:
            return (float("inf"), float("inf")), (float("inf"), float("inf"))

        init = np.array([self._des_prev_centre, self._asc_prev_centre])
        if self._k == 1:
            init = np.array([self._des_prev_centre])
        km = KMeans(
            n_clusters=self._k,
            init=init,
            n_init=1
        ).fit(points)
        if self._k == 2:
            centroid1, centroid2 = np.round(km.cluster_centers_).astype(int)
            centroid1 = [int(p) for p in centroid1]
            centroid2 = [int(p) for p in centroid2]
            c1_to_des = self.__get_dist(centroid1, self._des_prev_centre)
            c1_to_asc = self.__get_dist(centroid1, self._asc_prev_centre)
            des_centre = centroid1
            asc_centre = centroid2
            if c1_to_des > c1_to_asc:
                asc_centre, des_centre = des_centre, asc_centre
            return [des_centre, asc_centre]
        centroid1 = np.round(km.cluster_centers_).astype(int)
        return [[int(p) for p in centroid1[0]]]

    @property
    def cropped_image(self):
        """cropped image getter. The cropped image is the untouched cropped image provided by the user.

        """ # noqa
        return self._cropped_image

    @property
    def processing_image(self):
        """processing image getter. The prcoessing image is the segmentation result.

        """ # noqa
        return self._processing_image

    @property
    def stopping_slice(self):
        """stopping slice getter. Return the last processing slice for parameters tuning.

        """ # noqa
        return self._stopping_slice
