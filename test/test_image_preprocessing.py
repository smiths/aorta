import SimpleITK as sitk
import numpy as np
import os
os.environ["OMP_NUM_THREADS"] = '1'
import glob
import json

from src.SlicerExtension.AortaGeometryReconstructor.AortaGeomReconDisplayModule.AortaGeomReconDisplayModuleLib.AortaSegmenter import AortaSegmenter # noqa

def print_result(ref_image, test_image):
    """Print mean square error, mean absolute error, root mean square error 
    and Sørensen–Dice coefficient between the reference image and the test image

    Args:
        ref_image (numpy.ndarrays): reference image's numpy ndarrays representation

        test_image (numpy.ndarrays): test image's numpy ndarrays representation
    """ # noqa
    print(
        "mean_square_error", mean_square_error(ref_image, test_image)
    )
    print(
        "mean_absolute_error", mean_absolute_error(ref_image, test_image)
    )
    print(
        "root_mse", root_mse(ref_image, test_image)
    )
    print(
        "Sørensen–Dice coefficient", DSC(ref_image, test_image)
    )


def get_cropped_volume_image(sample):
    """Read the cropped volume from /project-repo/test/sample

    Returns:
        SITK: The cropped volume sitk image
    """
    abspath = glob.glob("test/sample/{}-crop.vtk".format(sample))[0]
    abspath = os.path.abspath(abspath)
    return sitk.ReadImage(abspath)


def read_volume_image(sample):
    """Read the segmented descending aorta volume from /project-repo/test/sample

    Returns:
        SITK: The segmented descending aorta sitk image
    """ # noqa
    abspath = glob.glob("test/sample/{}_Seg*.vtk".format(sample))[0]
    abspath = os.path.abspath(abspath)
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


def test_compare_segmentation(testCase, limit):
    """Read a test cases' cropped volume from /project-repo/test/sample,
    perform descending aorta segmentation,
    and compare the result with the existing volume from /project-repo/test/sample.

    Args:

        testCase (int): the test case to run the test. The test cases are:
            001-43681283
            028-07323651
            029-05937785
            030-75962810
            031-62023082
            032-22429388

    Returns:
        Boolean: Pass the test if the Sørensen–Dice coefficient between test image and reference image is within the limit set by user.
    """ # noqa

    sample = "001-43681283"
    if testCase == "028":
        sample = "028-07323651"
    elif testCase == "029":
        sample = "029-05937785"
    elif testCase == "030":
        sample = "030-75962810"
    elif testCase == "031":
        sample = "031-62023082"
    elif testCase == "032":
        sample = "032-22429388"
    file_p = os.path.abspath(glob.glob("test/*.json")[0])
    print(sample)
    with open(file_p, "r") as f:
        parameters = json.load(f)[sample]
    print(parameters)
    cropped_image = get_cropped_volume_image(sample)
    segmenter = AortaSegmenter(
        cropped_image=cropped_image, des_seed=parameters["des_seed"],
        asc_seed=parameters["asc_seed"], stop_limit=parameters["stop_limit"],
        threshold_coef=parameters["threshold_coef"],
        kernel_size=parameters["kernel_size"], rms_error=0.02, no_ite=600,
        curvature_scaling=2, propagation_scaling=0.5, debug=False
    )

    segmenter.begin_segmentation()
    test_image = segmenter.processing_image
    ref_image = read_volume_image(sample)
    nda_ref = sitk.GetArrayFromImage(ref_image)
    nda_test = sitk.GetArrayFromImage(test_image)
    DSC_error = 1-DSC(nda_ref, nda_test)
    print_result(nda_ref, nda_test)
    assert (DSC_error < limit)
    return test_image
