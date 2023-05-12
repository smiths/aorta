# flake8: noqa
import SimpleITK as sitk
import numpy as np
import os
import sys
sys.path.append("../src/SlicerExtension/AortaGeometryReconstructor/AortaGeomReconDisplayModule/AortaGeomReconDisplayModuleLib")
from AortaSegmenter import AortaSegmenter
from AortaSegmenterNew import AortaSegmenterNew
from AortaGeomReconEnums import SegmentType as SegType

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


def get_cropped_volume_image():
    """Read the cropped volume from /project-repo/sample

    Returns:
        SITK: The cropped volume sitk image
    """
    sample = 43681283
    abspath = os.path.abspath("sample/{}_crop.vtk".format(sample))
    return sitk.ReadImage(abspath)


def read_desc_volume_image():
    """Read the segmented descending aorta volume from /project-repo/sample

    Returns:
        SITK: The segmented descending aorta sitk image
    """ # noqa
    sample = 43681283
    abspath = os.path.abspath("sample/{}_des.vtk".format(sample))
    return sitk.ReadImage(abspath)


def read_asc_volume_image():
    """Read the segmented ascending and descending aorta volume from /project-repo/sample

    Returns:
        SITK: The segmented ascending and descending aorta sitk image
    """ # noqa
    sample = 43681283
    abspath = os.path.abspath("sample/{}_asc.vtk".format(sample))
    return sitk.ReadImage(abspath)


def read_final_volume_image(testCase):
    """Read the sagittal segmented aorta volume from /project-repo/sample


    Returns:
        SITK: The final segmented aorta sitk image
    """ # noqa
    sample = 43681283
    abspath = os.path.abspath("sample/{}_final.vtk".format(sample))
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


if __name__ == '__main__':
    des_seed = [18, 26, 830]
    asc_seed = [65, 116, 830]
    cropped_image = get_cropped_volume_image()

    segmenter = AortaSegmenterNew(
        cropped_image=cropped_image, des_seed=des_seed,
        asc_seed=asc_seed, aortic_seed=None,
        processing_image=None,
        seg_type=None, qualified_coef=2.2,
        threshold_coef=3.5,
        num_slice_skipping=3,
        kernel_size=8,
        rms_error=2.2, no_ite=600,
        curvature_scaling=0.5,
        propagation_scaling=1, debug=False
    )
    segmenter.begin_segmentation()
