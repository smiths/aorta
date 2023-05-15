# flake8: noqa
import SimpleITK as sitk
import numpy as np
import os
import sys
sys.path.append("../src/SlicerExtension/AortaGeometryReconstructor/AortaGeomReconDisplayModule/AortaGeomReconDisplayModuleLib")
from AortaSegmenter import AortaSegmenter
from AortaSegmenterNew import AortaSegmenterNew
from AortaGeomReconEnums import SegmentType as SegType


def get_cropped_volume_image(sample):
    """Read the cropped volume from /project-repo/test/sample

    Returns:
        SITK::image: The cropped volume sitk image
    """
    abspath = glob.glob("test/sample/{}-crop.vtk".format(sample))[0]
    abspath = os.path.abspath(abspath)
    return sitk.ReadImage(abspath)


def read_volume_image(sample):
    """Read the segmented descending aorta volume from /project-repo/test/sample

    Returns:
        SITK::image: The segmented descending aorta sitk image
    """ # noqa
    abspath = glob.glob("test/sample/{}_Seg*.vtk".format(sample))[0]
    abspath = os.path.abspath(abspath)
    return sitk.ReadImage(abspath)


if __name__ == '__main__':
    sample = "001-43681283"
    cropped_image = get_cropped_volume_image(sample)
    file_p = os.path.abspath(glob.glob("./*.json")[0])
    with open(file_p, "r") as f:
        parameters = json.load(f)[sample]

    segmenter = AortaSegmenter(
        cropped_image=cropped_image, des_seed=parameters["des_seed"],
        asc_seed=parameters["asc_seed"], stop_limit=parameters["stop_limit"],
        threshold_coef=parameters["threshold_coef"],
        kernel_size=parameters["kernel_size"], rms_error=0.02, no_ite=600,
        curvature_scaling=2, propagation_scaling=0.5, debug=False
    )
    segmenter.begin_segmentation()
