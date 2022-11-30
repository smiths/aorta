from datetime import datetime
import os
import SimpleITK as sitk
import numpy as np


def prepared_segmenting_image(image, index, size):
    # crop the image
    crop_filter = sitk.ExtractImageFilter()
    crop_filter.SetIndex(index)
    crop_filter.SetSize(size)

    cropped_image = crop_filter.Execute(image)

    # change intensity range to go from 0-255   +++++++
    # cropped_image_255 = sitk.Cast(sitk.RescaleIntensity(image),
    #                               sitk.sitkUInt8)

    # ensure that the spacing in the image is correct
    cropped_image.SetOrigin(image.GetOrigin())
    cropped_image.SetSpacing(image.GetSpacing())
    cropped_image.SetDirection(image.GetDirection())

    # Contrast Enhancement
    # Histogram Equalization

    img_array = sitk.GetArrayFromImage(
        (sitk.Cast(sitk.RescaleIntensity(cropped_image), sitk.sitkUInt8)))

    # flatten image array and calculate histogram via binning
    histogram_array = np.bincount(img_array.flatten(), minlength=256)
    # normalize image
    num_pixels = np.sum(histogram_array)
    histogram_array = histogram_array/num_pixels

    # normalized cumulative histogram
    chistogram_array = np.cumsum(histogram_array)

    # create pixel mapping lookup table
    transform_map = np.floor(255 * chistogram_array).astype(np.uint8)

    # flatten image array into 1D list
    # so they can be used with the pixel mapping table
    img_list = list(img_array.flatten())

    # transform pixel values to equalize
    eq_img_list = [transform_map[p] for p in img_list]

    # reshape and write back into img_array
    eq_img_array = np.reshape(np.asarray(eq_img_list), img_array.shape)

    # save image
    eq_img = sitk.GetImageFromArray(eq_img_array)
    eq_img.CopyInformation(cropped_image)

    # Median Image Filter
    median = sitk.MedianImageFilter()
    median_img = sitk.Cast(median.Execute(eq_img), sitk.sitkUInt8)

    return median_img


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
    image = prepared_segmenting_image(
        image=image,
        index=(190, 165, 40),
        size=(191, 216, 335)
    )
    # print("here")
    print(image.GetNumberOfPixels())
    # exit(0)
    # desc_axial_segmenter.prepared_segmenting_image(
    #     image=image, index=(190, 165, 40), size=(191, 216, 335))

    # # break

    # desc_axial_segmenter = AortaDescendingAxialSegmenter(
    #     startingSlice=86, aortaCentre=[112, 151], numSliceSkipping=3,
    #     segmentationFactor=2.2, segmentingImage=image)

    # desc_axial_segmenter.begin_segmentation()

    # cropped_image = desc_axial_segmenter.segmenting_image
    # processed_image = desc_axial_segmenter.segmented_image
    # writer = sitk.ImageFileWriter()
    # writer.SetImageIO("VTKImageIO")
    # outFilePath = "result/result_desc_0_.vtk"
    # writer.SetFileName(outFilePath)
    # writer.Execute(processed_image)

    # asc_axial_segmenter = AortaAscendingAxialSegmenter(
    #     startingSlice=114, aortaCentre=[40, 40], numSliceSkipping=3,
    #     segmentationFactor=2.2, segmentingImage=cropped_image,
    #     segmentedImage=processed_image)

    # asc_axial_segmenter.begin_segmentation()
    # processed_image = asc_axial_segmenter.segmented_image

    # writer = sitk.ImageFileWriter()
    # writer.SetImageIO("VTKImageIO")
    # outFilePath = "result/result_asc_0_.vtk"
    # writer.SetFileName(outFilePath)
    # writer.Execute(processed_image)

    # sag_segmenter = AortaSagitalSegmenter(
    #     segmentationFactor=3.5, segmentedImage=processed_image,
    #     original_cropped_image=cropped_image)

    # sag_segmenter.begin_segmentation()

    # writer = sitk.ImageFileWriter()
    # writer.SetImageIO("VTKImageIO")
    outFilePath = "result/result_{datetime}_.vtk".format(
        datetime=datetime.now().strftime("%Y-%m-%d_%H%M"))
    # writer.SetFileName(outFilePath)
    # writer.Execute(sag_segmenter.segmented_image)
