from src.SlicerExtension.AortaGeometryReconstructor.AortaGeomReconDisplayModule.AortaGeomReconDisplayModuleLib.AortaSegmenter import AortaSegmenter # noqa
from src.SlicerExtension.AortaGeometryReconstructor.AortaGeomReconDisplayModule.AortaGeomReconDisplayModuleLib.AortaGeomReconEnums import SegmentType as SegType # noqa

import SimpleITK as sitk
import numpy as np
import os


def print_result(ref_image, test_image, seg_type):
    """Print mean square error, mean absolute error, root mean square error 
    and Sørensen–Dice coefficient between the reference image and the test image

    Args:
        ref_image (numpy.ndarrays): reference image's numpy ndarrays representation

        test_image (numpy.ndarrays): test image's numpy ndarrays representation
    """ # noqa
    print(
        "{} mean_square_error".format(seg_type),
        mean_square_error(ref_image, test_image)
    )
    print(
        "{} mean_absolute_error".format(seg_type),
        mean_absolute_error(ref_image, test_image)
    )
    print(
        "{} root_mse".format(seg_type),
        root_mse(ref_image, test_image)
    )
    print(
        "{} Sørensen–Dice coefficient".format(seg_type),
        DSC(ref_image, test_image)
    )


def transform_image(cropped_image):
    """Perform histogram equalization for Digital Image Enhancement

    Args:
        cropped_image (SITK::image): The cropped image read from /project-repo/test/sample/folder
    Returns:
        (SITK::image): equalized cropped image.
    """ # noqa
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


def get_cropped_volume_image(testCase):
    """Read the cropped volume from /project-repo/test/sample

    Returns:
        SITK: The cropped volume sitk image
    """
    sample = 43681283
    if testCase == 1:
        sample = 22429388
    elif testCase == 2:
        sample = 62023082
    elif testCase == 3:
        sample = 75962810
    elif testCase == 4:
        sample = "07323651"
    elif testCase == 5:
        sample = "05937785"
    abspath = os.path.abspath("test/sample/{}_crop.vtk".format(sample))
    return sitk.ReadImage(abspath)


def read_desc_volume_image(testCase):
    """Read the segmented descending aorta volume from /project-repo/test/sample

    Returns:
        SITK: The segmented descending aorta sitk image
    """ # noqa
    sample = 43681283
    if testCase == 1:
        sample = 22429388
    elif testCase == 2:
        sample = 62023082
    elif testCase == 3:
        sample = 75962810
    elif testCase == 4:
        sample = "07323651"
    elif testCase == 5:
        sample = "05937785"
    abspath = os.path.abspath("test/sample/{}_des.vtk".format(sample))
    return sitk.ReadImage(abspath)


def read_asc_volume_image(testCase):
    """Read the segmented ascending and descending aorta volume from /project-repo/test/sample

    Returns:
        SITK: The segmented ascending and descending aorta sitk image
    """ # noqa
    sample = 43681283
    if testCase == 1:
        sample = 22429388
    elif testCase == 2:
        sample = 62023082
    elif testCase == 3:
        sample = 75962810
    elif testCase == 4:
        sample = "07323651"
    elif testCase == 5:
        sample = "05937785"
    abspath = os.path.abspath("test/sample/{}_asc.vtk".format(sample))
    return sitk.ReadImage(abspath)


def read_final_volume_image(testCase):
    """Read the sagittal segmented aorta volume from /project-repo/test/sample


    Returns:
        SITK: The final segmented aorta sitk image
    """ # noqa
    sample = 43681283
    if testCase == 1:
        sample = 22429388
    elif testCase == 2:
        sample = 62023082
    elif testCase == 3:
        sample = 75962810
    elif testCase == 4:
        sample = "07323651"
    elif testCase == 5:
        sample = "05937785"
    abspath = os.path.abspath("test/sample/{}_final.vtk".format(sample))
    return sitk.ReadImage(abspath)


def DSC(ref_image, test_image):
    """Calculate the Dice similarity coefficient.

    Args:
        ref_image (numpy.ndarrays): reference image's numpy ndarrays representation

        test_image (numpy.ndarrays): test image's numpy ndarrays representation

    Returns:
        float: The Dice similarity coefficient of the reference and test image
    """ # noqa
    two_TP = np.count_nonzero(np.logical_and(ref_image, test_image))*2
    total = (np.count_nonzero(ref_image) + np.count_nonzero(test_image))
    return two_TP/total


def root_mse(ref_image, test_image):
    """Calculate the root mean square error between reference image and test image.

    Args:
        ref_image (numpy.ndarrays): reference image's numpy ndarrays representation

        test_image (numpy.ndarrays): test image's numpy ndarrays representation

    Returns:
        float: The Dice similarity coefficient of the reference and test image
    """ # noqa
    return np.sqrt(mean_square_error(ref_image, test_image))


def mean_absolute_error(ref_image, test_image):
    """Calculate the mean absolute error between reference image and test image.

    Args:
        ref_image (numpy.ndarrays): reference image's numpy ndarrays representation

        test_image (numpy.ndarrays): test image's numpy ndarrays representation

    Returns:
        float: The Dice similarity coefficient of the reference and test image
    """ # noqa
    npsum = np.sum(np.abs(np.subtract(ref_image, test_image)))
    return npsum/np.count_nonzero(np.logical_or(ref_image, test_image))


def mean_square_error(ref_image, test_image):
    """Calculate the mean square error between reference image and test image.
    This function only counts if there is a white_pixel on either reference image or test image, ignoring the black pixels

    Args:
        ref_image (numpy.ndarrays): reference image's numpy ndarrays representation

        test_image (numpy.ndarrays): test image's numpy ndarrays representation

    Returns:
        float: The Dice similarity coefficient of the reference and test image
    """ # noqa
    npsum = np.sum(np.square(np.subtract(ref_image, test_image)))
    return npsum/np.count_nonzero(np.logical_or(ref_image, test_image))


def test_compare_des(limit, qualifiedCoef, thresholdCoef, testCase):
    """Read a test cases' cropped volume from /project-repo/test/sample,
    perform descending aorta segmentation,
    and compare the result with the existing volume from /project-repo/test/sample.

    Args:
        limit (float): the maximum Dice similarity coefficient difference allowed to pass the test.

        qualifiedCoef (float): the qualified coefficient value to process descending aorta segmentation.

        thresholdCoef (float): the factor used to determine the lower and upper threshold for label statistics image filter.

        testCase (int): the test case to run the test (0-5).

    Returns:
        Boolean: Pass the test if the Sørensen–Dice coefficient between test image and reference image is within the limit set by user.
    """ # noqa
    starting_slice = 829
    aorta_centre = [23, 28]
    cropped_image = get_cropped_volume_image(testCase)
    cropped_image = transform_image(cropped_image)
    if testCase == 1:
        starting_slice = 857
        aorta_centre = [90, 34]
    elif testCase == 2:
        starting_slice = 1202
        aorta_centre = [20, 15]
    elif testCase == 3:
        starting_slice = 962
        aorta_centre = [38, 26]
    elif testCase == 4:
        starting_slice = 824
        aorta_centre = [19, 20]
    elif testCase == 5:
        starting_slice = 919
        aorta_centre = [29, 15]
    desc_axial_segmenter = AortaSegmenter(
        cropped_image=cropped_image,
        starting_slice=starting_slice, aorta_centre=aorta_centre,
        num_slice_skipping=3,
        qualified_coef=qualifiedCoef,
        threshold_coef=thresholdCoef,
        processing_image=None,
        seg_type=SegType.descending_aorta
    )

    desc_axial_segmenter.begin_segmentation()
    test_image = desc_axial_segmenter.processing_image
    ref_image = read_desc_volume_image(testCase)
    print("qualified slicefactor : {}".format(qualifiedCoef))
    print("filter factor : {}".format(thresholdCoef))
    nda_ref = sitk.GetArrayFromImage(ref_image)
    nda_test = sitk.GetArrayFromImage(test_image)
    DSC_error = 1-DSC(nda_ref, nda_test)
    print_result(nda_ref, nda_test, SegType.descending_aorta)
    assert (DSC_error < limit)
    return test_image


def test_compare_asc(
    limit,
    qualifiedCoef,
    thresholdCoef,
    testCase,
    processing_image=None
        ):
    """Read a test cases' partially segmented volume (descending aorta) from /project-repo/test/sample,
    perform ascending aorta segmentation,
    and compare the result with the existing ascending aorta volume from /project-repo/test/sample

    Args:
        limit (float): the maximum Dice similarity coefficient difference allowed to pass the test.

        qualifiedCoef (float): the qualified coefficient value to process descending aorta segmentation.

        thresholdCoef (float): the factor used to determine the lower and upper threshold for label statistics image filter.

        testCase (int): the test case to run the test (0-5).

    Returns:
        Boolean: Pass the test if the Sørensen–Dice coefficient between test image and reference image is within the limit set by user.
    """ # noqa
    cropped_image = get_cropped_volume_image(testCase)
    cropped_image = transform_image(cropped_image)
    if not processing_image:
        processing_image = read_desc_volume_image(testCase)
    starting_slice = 749
    aorta_centre = [87, 130]
    if testCase == 1:
        starting_slice = 857
        aorta_centre = [164, 168]
    elif testCase == 2:
        starting_slice = 1273
        aorta_centre = [25, 88]
    elif testCase == 3:
        starting_slice = 1010
        aorta_centre = [88, 161]
    elif testCase == 4:
        starting_slice = 873
        aorta_centre = [76, 94]
    elif testCase == 5:
        starting_slice = 926
        aorta_centre = [72, 116]
    asc_axial_segmenter = AortaSegmenter(
        cropped_image=cropped_image,
        starting_slice=starting_slice, aorta_centre=aorta_centre,
        num_slice_skipping=3,
        qualified_coef=qualifiedCoef,
        threshold_coef=thresholdCoef,
        processing_image=processing_image,
        seg_type=SegType.ascending_aorta
    )
    asc_axial_segmenter.begin_segmentation()
    test_image = asc_axial_segmenter.processing_image
    ref_image = read_asc_volume_image(testCase)
    print("qualified slicefactor : {}".format(qualifiedCoef))
    print("filter factor : {}".format(thresholdCoef))
    nda_ref = sitk.GetArrayFromImage(ref_image)
    nda_test = sitk.GetArrayFromImage(test_image)
    DSC_error = 1-DSC(nda_ref, nda_test)
    print_result(nda_ref, nda_test, SegType.ascending_aorta)
    assert (DSC_error < limit)
    return test_image


def test_asc_and_final(
    limit,
    qualifiedCoef,
    thresholdCoef,
    testCase,
    processing_image=None
        ):
    """Compare the  partially segmented aorta volume (descending and ascending aorta)
    to a fully segmented aorta volume (descending, ascending and sagittal).

    Args:
        limit (float): the maximum Dice similarity coefficient difference allowed to pass the test.

        qualifiedCoef (float): the qualified coefficient value to process descending aorta segmentation.

        thresholdCoef (float): the factor used to determine the lower and upper threshold for label statistics image filter.

        testCase (int): the test case to run the test (0-5).

    Returns:
        Boolean: Pass the test if the Sørensen–Dice coefficient between test image and reference image is within the limit set by user.
    """ # noqa
    ref_image = read_asc_volume_image(testCase)
    test_image = read_final_volume_image(testCase)
    nda_ref = sitk.GetArrayFromImage(ref_image)
    nda_test = sitk.GetArrayFromImage(test_image)
    DSC_error = 1-DSC(nda_ref, nda_test)
    print_result(nda_ref, nda_test, SegType.ascending_aorta)
    assert (DSC_error < limit)


def test_compare_final_volume(
    limit,
    qualifiedCoef,
    thresholdCoef,
    testCase,
    processing_image=None
        ):
    """Read a test cases' partially segmented volume (descending and ascending aorta) from /project-repo/test/sample,
    perform sagittal aorta segmentation,
    and compare the result with the existing sagittal aorta volume from /project-repo/test/sample

    Args:
        limit (float): the maximum Dice similarity coefficient difference allowed to pass the test.

        qualifiedCoef (float): the qualified coefficient value to process descending aorta segmentation.

        thresholdCoef (float): the factor used to determine the lower and upper threshold for label statistics image filter.

        testCase (int): the test case to run the test (0-5).

    Returns:
        Boolean: Pass the test if the Sørensen–Dice coefficient between test image and reference image is within the limit set by user.
    """ # noqa
    cropped_image = get_cropped_volume_image(testCase)
    cropped_image = transform_image(cropped_image)
    if not processing_image:
        processing_image = read_asc_volume_image()
    if not qualifiedCoef:
        qualifiedCoef = 2.2
    if not thresholdCoef:
        thresholdCoef = 3.5
    sagittal_segmenter = AortaSegmenter(
        cropped_image=cropped_image,
        starting_slice=None, aorta_centre=None,
        num_slice_skipping=3,
        qualified_slice_factor=qualifiedCoef,
        threshold_coef=thresholdCoef,
        processing_image=processing_image,
        seg_type=SegType.sagittal_segmenter
    )
    sagittal_segmenter.begin_segmentation()
    test_image = sagittal_segmenter.processing_image
    ref_image = read_final_volume_image(testCase)
    print("qualified slicefactor : {}".format(qualifiedCoef))
    print("filter factor : {}".format(thresholdCoef))
    nda_ref = sitk.GetArrayFromImage(ref_image)
    nda_test = sitk.GetArrayFromImage(test_image)
    DSC_error = 1-DSC(nda_ref, nda_test)
    print_result(nda_ref, nda_test)
    assert (DSC_error < limit)
    return test_image


def test_debug(limit, qualifiedCoef, thresholdCoef, testCase):
    """Debug the general workflow of the axial segmentation algorithm.

    Args:
        limit (float): the maximum Dice similarity coefficient difference allowed to pass the test.

        qualifiedCoef (float): the qualified coefficient value to process descending aorta segmentation.

        thresholdCoef (float): the factor used to determine the lower and upper threshold for label statistics image filter.

        testCase (int): the test case to run the test (0-5).

    Returns:
        Boolean: Pass the test if the Sørensen–Dice coefficient between test image and reference image is within the limit set by user.
    """ # noqa
    starting_slice = 829
    aorta_centre = [23, 28]
    cropped_image = get_cropped_volume_image(testCase)
    cropped_image = transform_image(cropped_image)
    if testCase == 1:
        starting_slice = 857
        aorta_centre = [90, 34]
    elif testCase == 2:
        starting_slice = 1202
        aorta_centre = [20, 15]
    elif testCase == 3:
        starting_slice = 962
        aorta_centre = [38, 26]
    elif testCase == 4:
        starting_slice = 824
        aorta_centre = [19, 20]
    elif testCase == 5:
        starting_slice = 919
        aorta_centre = [29, 15]
    desc_axial_segmenter = AortaSegmenter(
        cropped_image=cropped_image,
        starting_slice=starting_slice, aorta_centre=aorta_centre,
        num_slice_skipping=3,
        qualified_coef=qualifiedCoef,
        threshold_coef=thresholdCoef,
        processing_image=None,
        seg_type=SegType.descending_aorta,
        debug=True
    )

    desc_axial_segmenter.begin_segmentation()
