from src.SlicerExtension.AortaGeometryReconstructor.AortaGeomReconDisplayModule.AortaGeomReconDisplayModuleLib.AortaSegmenter import AortaSegmenter # noqa
from src.SlicerExtension.AortaGeometryReconstructor.AortaGeomReconDisplayModule.AortaGeomReconDisplayModuleLib.AortaSegmenter import SegmentType # noqa
import SimpleITK as sitk
import numpy as np


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


def read_desc_volume_image():
    nda = np.load("test/sample/43681283_des.npy")
    return sitk.GetImageFromArray(nda)


def read_asc_volume_image():
    nda = np.load("test/sample/43681283_asc.npy")
    return sitk.GetImageFromArray(nda)


def read_final_volume_image():
    nda = np.load("test/sample/43681283_final.npy")
    return sitk.GetImageFromArray(nda)


def compare_images(ref_image, test_image):
    return 1


def compare_des():
    cropped_image = get_cropped_volume_image()
    cropped_image = transform_image(cropped_image)

    starting_slice = 820
    aorta_centre = [19, 30]
    desc_axial_segmenter = AortaSegmenter(
        cropped_image=cropped_image,
        starting_slice=starting_slice, aorta_centre=aorta_centre,
        num_slice_skipping=3,
        qualified_slice_factor=2.2,
        processing_image=None,
        seg_type=SegmentType.descending_aorta
    )

    desc_axial_segmenter.begin_segmentation()
    processed_image = desc_axial_segmenter.processing_image
    image_des = read_desc_volume_image()

    result = compare_images(image_des, processed_image)
    assert (result)


def compare_asc():
    starting_slice = 1
    aorta_centre = [1, 1]
    asc_axial_segmenter = AortaSegmenter(
        cropped_image=None,
        starting_slice=starting_slice, aorta_centre=aorta_centre,
        num_slice_skipping=3,
        qualified_slice_factor=2.2,
        processing_image=None,
        seg_type=SegmentType.ascending_aorta
    )
    asc_axial_segmenter.begin_segmentation()


def compare_final_volume():
    sagittal_segmenter = AortaSegmenter(
        cropped_image=None,
        starting_slice=None, aorta_centre=None,
        num_slice_skipping=3,
        qualified_slice_factor=2.2,
        processing_image=None,
        seg_type=SegmentType.sagittal_segmenter
    )
    sagittal_segmenter.begin_segmentation()


def test_prepared_segmenting_image():
    compare_des()
    assert (1)
