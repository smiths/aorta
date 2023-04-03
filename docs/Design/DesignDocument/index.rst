.. AortaGeomRecon documentation master file, created by
   sphinx-quickstart on Wed Feb  8 12:25:31 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to AortaGeomRecon's design document!
============================================

This is the design document for the AortaGeomRecon module, a :term:`3D Slicer` extension to perform :term:`Aorta` segmentation and Aorta geometry reconstruction. 

You can find the source code, the installation guide, and the user manual in the project's `repository <https://github.com/smiths/aorta>`_.


Overview
********
Automatic aorta segmentation in thoracic computed tomography (CT) scans is important for aortic calcification quantification and to guide the segmentation of other central vessels. The work to manually segment regions of interest can be time-consuming and repetitive, and there are some automatic aorta segmentation algorithms posted. This project implemented a semi-automatic algorithm that can extract the 3-dimensional segmentation of the aorta. 

------------

The steps before applying the main algorithm
********************************************

The algorithm works best with the chest volume cropped to a rectangular prism that contains the aorta and parts of the other organs such as the backbone, blood vessels, and the heart. This can be done with :term:`3D Slicer` and its submodule `Volume rendering <https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html>`_. A detailed guide can be found on the `volume rendering and cropping section <https://github.com/smiths/aorta#to-use-volume-rendering-to-crop-a-voi>`_ of the user instructions. 

After cropping the volume, which only contains the region of interest, the algorithm needs a set of variables inputs from the user. These variables are:

1. A centre coordinate of :term:`Descending Aorta` and :term:`Ascending Aorta` located on a :term:`slice` (a voxel).
2. :term:`Qualified coefficient`
3. An integer to indicate the number of slices that the algorithm is allowed to skip consecutively.


The main ideas of the algorithm
*******************************

At the beginning of the algorithm, the user inputs the integer coordinates indicating the position of the descending aorta or ascending aorta centre on a single :term:`slice`. The algorithm works separately on the descending aorta segmentation and the ascending aorta segmentation. Thus, it will ask users to input the coordinate of the descending aorta centre. After completing this segmentation, it will prompt the user for the input variable of the ascending aorta.

.. note::
   The user's chosen slice will be used as a reference throughout the workflow of the algorithm. Therefore, changing the input of the centre coordinates on a different slice could generate a slightly different segmentation result.
   

This algorithm segments each :term:`slice` with `SITK\:\:ThresholdSegmentationLevelSetImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ThresholdSegmentationLevelSetImageFilter.html>`_. The principles of this image filter can be explained with two terms: :term:`Level sets` segmentation method, and a :term:`threshold` range that defines the intensity of the acceptable pixel. The following steps elaborate on how the algorithm calculated the necessary values to perform segmentation.

For each slice starting from the user's selected slice, going in the :term:`inferior` first, then :term:`superior` direction:

1. By using `SITK\:\:BinaryDilateImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1BinaryDilateImageFilter.html>`_ to perform :term:`binary dilation`, the algorithm generates a :term:`label map` image which contains a circle-like shape around the centre coordinate (user input's or calculated by the algorithm). Each pixel within the circle will be labeled as a white pixel (value of 1), and the rest of the pixels are labeled as black pixels (value of 0).


2. By using `SITK\:\:LabelStatisticsImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1LabelStatisticsImageFilter.html>`_, the algorithm gets the mean and the standard deviation of the intensity values of the pixels that were labeled as the white pixel in the previous step. The algorithm uses :term:`threshold coefficient` to calculate the lower and upper :term:`threshold` to be used in the next step.


3. With `SITK\:\:SignedMaurerDistanceMapImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1SignedMaurerDistanceMapImageFilter.html>`_, the algorithm creates another image, the :term:`Euclidean distance transform` of the label image created in step 1, and uses it as the seed image (:term:`contour line`) in `SITK\:\:ThresholdSegmentationLevelSetImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ThresholdSegmentationLevelSetImageFilter.html>`_, with the lower and upper threshold value calculated in step 2. The filtered image is the :term:`segmented slice`.


4. The algorithm determines whether to accept the :term:`segmented slice` or not, based on the number of white pixels on the segmented slice, and the :term:`Qualified coefficient` to control the limit.

    .. note::

       To determine whether a segmented slice is acceptable, different conditions are verified for :term:`Descending Aorta` and :term:`Ascending Aorta`. These conditions check are all involved with the :term:`Qualified coefficient`, which is decided by the user. In simple terms, the larger the :term:`Qualified coefficient`, the looser the condition on accepting a segmented slice.


5. If the algorithm accepted this segmented slice, a new centre coordinate is calculated and used as the seed coordinate for segmenting the next slice.


6. When a segmented slice is not acceptable, the algorithm will skip this slice if the number of consecutive skipped slices is less than the user's limit. Otherwise, the algorithm will stop the segmentation loop. 

    .. note::
       
       The algorithm will replace these skipped slices with the calculated intersection of the previous and the next slice.

The simplified version of the algorithm
***************************************

.. code-block:: python
   :linenos:

   """
   inputs to the program
      cropped_image: n-dimensional array with a shape of (x, y, z)
      seed_aorta_centre: tuple (int, int)
      seed_slice_index: int
      qualified_coefficient: float
      num_skipped_slice: int

   outputs:
      processing_image: n-dimensional array with a shape of (x, y, z) with segmented volume

   """
   processing_image = cropped_image.copy()
   white_pixel = 1
   black_pixel = 0
   skip_counter = 0
   segment_filter = sitk.ThresholdSegmentationLevelSetImageFilter()
   skipped_slice = []

   # The statistics of the user's chosen slice will be used as reference
   # to determine whether a new segmented slice is acceptable
   segmented_slice = segment_single_slice(seed_slice_index, seed_aorta_centre)
   
   # Any pixel with positive intensity value will be set to white_pixel
   new_slice = Array[segmented_slice[0].length][segmented_slice.length]
   for x from 0 to segmented_slice[0].length:
      for y from 0 to segmented_slice.length:
         if segmented_slice[x][y] > black_pixel:
            new_slice[x][y] = white_pixel
         else:
            new_slice[x][y] = black_pixel

   # orginal_size will be used to compare new slice's size
   # to determine if the new slice is acceptable
   original_size, prev_centre = count_pixels(new_slice)
   prev_size = original_size

   # Repeat the above process for each slice
   for slice_i in range(start, end, step):
       # prev_centre is the new derived centre from last segmented slice
       segmented_slice = segment_single_slice(slice_i, prev_centre)

       # element-wise operation
       # exactly what we doing with the double for-loop
       # to assign white pixel and black pixel
       new_slice = segmented_slice > black_pixel

       total_coord, centre = count_pixels(new_slice)
       if is_new_slice_qualified(total_coord):
          skip_counter = 0
          # processing_image is the segmented volume returned
          processing_image[:, :, slice_i] = new_slice
          prev_centre = centre
          prev_size = total_coord
          # for ascending aorta, we will generate more possible coordinates
          # and use it in segmentation algorithm
          # prev_seeds = seeds
       else:
          skipped_slice.append(slice_i)
          skip_counter += 1
          if skip_counter == num_skipped_slice:
              break

   for slice_i in skipped_slice:
       # replace processing_image[slice_i] with the intersection of its previous and next slice

   return processing_image

   def generate_label_map(curr_slice, prev_centre):
      # Create a label map based on the centre coordinate
      # sitk.BinaryDilate populate a circle-liked shape where pixel in the circle is marked as 1
      label_map = curr_slice.copy_size()
      spacing = 3
      for i = -1 to 1 do:
         circle_x = prev_centre[0] + spacing*i
         label_map[(circle_x, prev_centre[1])] = white_pixel
      label_map = sitk.BinaryDilate(label_map, [3] * 2) 
      return label_map

   def segment_single_slice(current_index, prev_centre):
      # retrieve the 2d slice to be processed
      curr_slice = cropped_image[:,:, current_index]
      # create a label map
      label_map = generate_label_map(curr_slice, prev_centre)
      # Calculate statistics associated with white_pixel label
      stats = sitk.LabelStatisticsImageFilter()
      stats.Execute(curr_slice, label_map)
      # Threshold for SITK::ThresholdSegmentationLevelSetImageFilter
      # stats.GetMean(white_pixel) returns the mean intensity values of the pixels labeled white pixels.
      lower_threshold = (stats.GetMean(white_pixel) - threshold_coef*stats.GetSigma(white_pixel))
      upper_threshold = (stats.GetMean(white_pixel) + threshold_coef*stats.GetSigma(white_pixel))
      # calculate the Euclidean distance transform and use it to perform segmentation
      dis_map = sitk.SignedMaurerDistanceMap(label_map)
      segment_filter.SetLowerThreshold(lower_threshold)
      segment_filter.SetUpperThreshold(upper_threshold)
      # Segmentated slice, a ndarrays of shape (x, y)
      return segment_filter.Execute(dis_map, curr_slice)

   def count_pixels(segmented_slice):
      # This function will count the number of white pixels in this segmented slice
      # and calculate a new centre based on the result
      num_of_white_pixel = 0
      x_coord = 0
      y_coord = 0
      for x from 0 to segmented_slice[0].length:
         for y from 0 to segmented_slice.length:
            if segmented_slice[x][y] == white_pixel:
               x_coord += x
               y_coord += y
               num_of_white_pixel += 1
      new_centre = (x_coord/num_of_white_pixel, y_coord/num_of_white_pixel)
      return num_of_white_pixel, new_centre

   def is_new_slice_qualified(new_size):
      # compare new slice's number of white pixel to
      # the original slice and the previous size

      condition_1 = new_size < original_size*qualified_coefficient
      condition_2 = new_size > original_size/qualified_coefficient
      condition_3 = new_size < prev_size*qualified_coefficient

      return condition_1 and condition_2 and condition_3

.. note::

   You can find the definitions of each function within the module below

.. toctree::
   :maxdepth: 2
   :caption: Modules documentation:

   modules


Indices and tables
******************

| :ref:`genindex`
| :ref:`modindex`

.. toctree::
   :maxdepth: 1
   
   Glossary <glossary>
