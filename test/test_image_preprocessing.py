from src.SlicerExtension.AortaGeometryReconstructor.AortaGeomReconDisplayModule.AortaGeomReconDisplayModuleLib.AortaSegmenter import AortaSegmenter # noqa
from src.SlicerExtension.AortaGeometryReconstructor.AortaGeomReconDisplayModule.AortaGeomReconDisplayModuleLib.AortaSegmenter import SegmentType # noqa
import SimpleITK as sitk
import numpy as np


def print_result(arr1, arr2):
    print(
        "{} mean_square_error".format(SegmentType.descending_aorta),
        mean_square_error(arr1, arr2)
    )
    print(
        "{} mean_absolute_error".format(SegmentType.ascending_aorta),
        mean_absolute_error(arr1, arr2)
    )
    print(
        "{} root_mse".format(SegmentType.ascending_aorta),
        root_mse(arr1, arr2)
    )
    print(
        "{} Sørensen–Dice coefficient".format(
            SegmentType.descending_aorta),
        DSC(arr1, arr2)
    )


def transform_image(cropped_image):
    img_array = sitk.GetArrayFromImage(
        (sitk.Cast(sitk.RescaleIntensity(cropped_image), sitk.sitkUInt8)))
    histogram_array = np.bincount(img_array.flatten(), minlength=256)
    num_pixels = np.sum(histogram_array)
    histogram_array = histogram_array/num_pixels
    chistogram_array = np.cumsum(histogram_array)
    transform_map = np.floor(255 * chistogram_array).astype(np.uint8)
    img_list = list(img_array.flatten())
    eq_img_list = [transform_map[p] for p in img_list]
    eq_img_array = np.reshape(np.asarray(eq_img_list), img_array.shape)
    eq_img = sitk.GetImageFromArray(eq_img_array)
    eq_img.CopyInformation(cropped_image)
    median = sitk.MedianImageFilter()
    median_img = sitk.Cast(median.Execute(eq_img), sitk.sitkUInt8)
    return median_img


def get_cropped_volume_image():
    nda = np.load("test/sample/43681283_crop.npy")
    return sitk.GetImageFromArray(nda)


cropped_image = get_cropped_volume_image()
cropped_image = transform_image(cropped_image)


def read_desc_volume_image():
    nda = np.load("test/sample/43681283_des.npy")
    return sitk.GetImageFromArray(nda)


def read_asc_volume_image():
    nda = np.load("test/sample/43681283_asc.npy")
    return sitk.GetImageFromArray(nda)


def read_final_volume_image():
    nda = np.load("test/sample/43681283_final.npy")
    return sitk.GetImageFromArray(nda)


def DSC(arr1, arr2):
    two_TP = np.count_nonzero(np.logical_and(arr1, arr2))*2
    return two_TP/(np.count_nonzero(arr1) + np.count_nonzero(arr2))


def root_mse(arr1, arr2):
    return np.sqrt(mean_square_error(arr1, arr2))


def mean_absolute_error(arr1, arr2):
    npsum = np.sum(np.abs(np.subtract(arr1, arr2)))
    return npsum/np.count_nonzero(np.logical_or(arr1, arr2))


def mean_square_error(arr1, arr2):
    npsum = np.sum(np.square(np.subtract(arr1, arr2)))
    return npsum/np.count_nonzero(np.logical_or(arr1, arr2))


def test_compare_des(limit, qsf, ffactor):
    starting_slice = 820
    aorta_centre = [18, 26]

    # starting_slice = 700
    # aorta_centre = [5, 60]
    desc_axial_segmenter = AortaSegmenter(
        cropped_image=cropped_image,
        starting_slice=starting_slice, aorta_centre=aorta_centre,
        num_slice_skipping=3,
        qualified_slice_factor=qsf,
        filter_factor=ffactor,
        processing_image=None,
        seg_type=SegmentType.descending_aorta
    )
    desc_axial_segmenter.begin_segmentation()
    test_image = desc_axial_segmenter.processing_image
    ref_image = read_desc_volume_image()
    print("qualified slicefactor : {}".format(qsf))
    print("filter factor : {}".format(ffactor))
    nda_ref = sitk.GetArrayFromImage(ref_image)
    nda_test = sitk.GetArrayFromImage(test_image)
    DSC_error = 1-DSC(nda_ref, nda_test)
    print_result(nda_ref, nda_test)
    assert (DSC_error < limit)
    return test_image


def test_compare_asc(limit, qsf, ffactor, processing_image=None):
    if not processing_image:
        processing_image = read_desc_volume_image()
    starting_slice = 733
    aorta_centre = [87, 131]
    asc_axial_segmenter = AortaSegmenter(
        cropped_image=cropped_image,
        starting_slice=starting_slice, aorta_centre=aorta_centre,
        num_slice_skipping=3,
        qualified_slice_factor=qsf,
        filter_factor=ffactor,
        processing_image=processing_image,
        seg_type=SegmentType.ascending_aorta
    )
    asc_axial_segmenter.begin_segmentation()
    test_image = asc_axial_segmenter.processing_image
    ref_image = read_asc_volume_image()
    print("qualified slicefactor : {}".format(qsf))
    print("filter factor : {}".format(ffactor))
    nda_ref = sitk.GetArrayFromImage(ref_image)
    nda_test = sitk.GetArrayFromImage(test_image)
    DSC_error = 1-DSC(nda_ref, nda_test)
    print_result(nda_ref, nda_test)
    assert (DSC_error < limit)
    return test_image


def test_compare_final_volume(limit, qsf, ffactor, processing_image=None):
    if not processing_image:
        processing_image = read_asc_volume_image()
    if not qsf:
        qsf = 2.2
    if not ffactor:
        ffactor = 3.5
    sagittal_segmenter = AortaSegmenter(
        cropped_image=cropped_image,
        starting_slice=None, aorta_centre=None,
        num_slice_skipping=3,
        qualified_slice_factor=qsf,
        filter_factor=ffactor,
        processing_image=processing_image,
        seg_type=SegmentType.sagittal_segmenter
    )
    sagittal_segmenter.begin_segmentation()
    test_image = sagittal_segmenter.processing_image
    ref_image = read_final_volume_image()
    print("qualified slicefactor : {}".format(qsf))
    print("filter factor : {}".format(ffactor))
    nda_ref = sitk.GetArrayFromImage(ref_image)
    nda_test = sitk.GetArrayFromImage(test_image)
    DSC_error = 1-DSC(nda_ref, nda_test)
    print_result(nda_ref, nda_test)
    assert (DSC_error < limit)
    return test_image


def test_prepared_segmenting_image(limit, qsf, ffactor):
    limit = float(limit)
    processing_image = test_compare_des(limit)
    processing_image = test_compare_asc(limit, processing_image)
    processing_image = test_compare_final_volume(limit, processing_image)
