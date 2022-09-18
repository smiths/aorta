import AortaSegmenter
from datetime import datetime
import os
import SimpleITK as sitk

"""Return sitk.image by reading source .dcm files."""


def get_images(path, num_slices):
    # list of the number of slices in the z direction for each dicom image
    # these are manually entered as each dicom folder has far more .dcm files
    # than slices. If you do not manually enter these values,
    # the images will have many repeats of a singular CT

    list_dcm = os.listdir(path)
    list_dcm.sort()

    list_dcm = list_dcm[1:num_slices:]
    # change list to include path of .dcm files instead of just their names
    s = path + "/{0}"
    list_dcm = [s.format(dcm) for dcm in list_dcm]

    # convert the .dcm files to 3D images
    image = sitk.ReadImage(list_dcm)
    return image


if __name__ == '__main__':

    # os.environ["SITK_SHOW_COMMAND"] =
    # 'C:\\Program Files\\ITK-SNAP 3.8\\bin\\ITK-SNAP'

    # work on image 0
    image = get_images("../sample-dicom/43681283", 376)
    desc_axial_segmenter = AortaSegmenter.AortaDescendingAxialSegmenter(
        startingSlice=86, aortaCentre=[112, 151], numSliceSkipping=3,
        segmentationFactor=2.2, segmentingImage=image)

    desc_axial_segmenter.prepared_segmenting_image(
        image=image, index=(190, 165, 40), size=(191, 216, 335))
    desc_axial_segmenter.begin_segmentation()

    cropped_image = desc_axial_segmenter.segmenting_image
    processed_image = desc_axial_segmenter.segmented_image
    writer = sitk.ImageFileWriter()
    writer.SetImageIO("VTKImageIO")
    outFilePath = "../result/result_desc_0_.vtk"
    writer.SetFileName(outFilePath)
    writer.Execute(processed_image)

    asc_axial_segmenter = AortaSegmenter.AortaAscendingAxialSegmenter(
        startingSlice=114, aortaCentre=[40, 40], numSliceSkipping=3,
        segmentationFactor=2.2, segmentingImage=cropped_image,
        segmentedImage=processed_image)

    asc_axial_segmenter.begin_segmentation()
    processed_image = asc_axial_segmenter.segmented_image

    writer = sitk.ImageFileWriter()
    writer.SetImageIO("VTKImageIO")
    outFilePath = "../result/result_asc_0_.vtk"
    writer.SetFileName(outFilePath)
    writer.Execute(processed_image)

    sag_segmenter = AortaSegmenter.AortaSagitalSegmenter(
        segmentationFactor=3.5, segmentedImage=processed_image,
        original_cropped_image=cropped_image)

    sag_segmenter.begin_segmentation()

    writer = sitk.ImageFileWriter()
    writer.SetImageIO("VTKImageIO")
    outFilePath = "../result/result_{datetime}_.vtk".format(
        datetime=datetime.now().strftime("%Y-%m-%d_%H%M"))
    writer.SetFileName(outFilePath)
    writer.Execute(sag_segmenter.segmented_image)