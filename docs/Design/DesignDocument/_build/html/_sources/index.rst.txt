.. AortaGeomRecon documentation master file, created by
   sphinx-quickstart on Wed Feb  8 12:25:31 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to AortaGeomRecon's documentation!
==========================================

This is the design document for the AortaGeomRecon module, a :term:`3D Slicer` extension to perform :term:`Aorta` segmentation and Aorta geometry reconstruction. 

You can find the source code, the installation guide, and the user manual in the project's `repository <https://github.com/smiths/aorta>`_.

------------

The steps before applying the main algorithm
********************************************

The algorithm works best with the chest volume cropped to a rectangular prism that contains the aorta and parts of the other organs such as the backbone, blood vessels, and the heart. This can be done with :term:`3D Slicer` and its submodule `Volume rendering <https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html>`_. A detailed guide can be found on the `volume rendering and cropping section <https://github.com/smiths/aorta#to-use-volume-rendering-to-crop-a-voi>`_ of the user instructions. 

After cropping the volume, which only contains the region of interest, the algorithm needs a set of variables inputs from the user. These variables are:

1. :term:`Descending Aorta` and :term:`Ascending Aorta` centre coordinate.
2. :term:`Qualified coefficient`
3. An integer to indicate the number of slices that the algorithm is allowed to skip.


The main ideas of the algorithm
*******************************

At the beginning of the algorithm, the user's inputs two integers indicate the aorta centre. This coordinate is to generate the seed slice, 2-dimensional circle image. This seed slice will be used as a reference throughout the workflow of the algorithm. Therefore, changing the input of the centre coordinate could generate a slightly different segmentation result.

For each slice starting from the user's selected slice going in the :term:`inferior` or :term:`superior` direction

1. The algorithm generates a label image by making a grid of spacing 3 pixels aparts, overwrites these pixels to white pixel (value of 1).

2. By using `SITK\:\:LabelStatisticsImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1LabelStatisticsImageFilter.html>`_, the algorithm gets the mean and the sigma of the intensity image of the pixel labeled to white pixel. The algorithm uses :term:`Threshold coefficient` to calculate the lower and upper threshold to be used in the following steps.

3. The algorithm then creates another image with `SITK\:\:SignedMaurerDistanceMapImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1SignedMaurerDistanceMapImageFilter.html>`_, the :term:`Euclidean distance transform` of a binary image as the image intensity map, and uses it with `SITK\:\:ThresholdSegmentationLevelSetImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ThresholdSegmentationLevelSetImageFilter.html>`_ and the threhold values mentioned above to create a segmented slice.

4. The algorithm determines whether to accept the segmented slice or not, based on the number of white pixels on the segmented slice, and the qualified coefficient to control the limit.

    .. note::

       To determine whether a segmented slice is acceptable, different conditions are verified for :term:`Descending Aorta` and :term:`Ascending Aorta`. These conditions check are all involved with the :term:`Qualified coefficient`, which is decided by the user. In simple terms, the larger the :term:`Qualified coefficient`, the looser the condition on accepting a segmented slice.

5. If the algorithm accepted this segmented slice, a new centre coordinate is calculated and used as the seed coordinate for segmenting the next slice.

6. When a segmented slice is not acceptable, the algorithm will skip this slice if the number of the skipped slice is less than the integer given by the user. The algorithm will try to replace these skipped slices by reading the overlapped area of the previous and the next slice.

The pseudocode of the algorithm
*******************************

.. code-block:: python

   """inputs to the program
         seed_aorta_centre: tuple (int, int)
         seed_slice_index: int
         qualified_coefficient: float
         cropped_image: ndarray shape of (x, y, z)

      outputs:
         processing_image: ndarray shape of (x, y, z) with segmented volume
   """
   processing_image = cropped_image.copy()
   white_pixel = 1
   black_pixel = 0
   segment_filter = sitk.ThresholdSegmentationLevelSetImageFilter()
   skipped_slice = []

   def calculate_seed(curr_slice, prev_centre):
      # Create a seed slice based on user's chosen aorta-centre coordinate
      # Overwrites the values to white_pixel over a square around the centre
      seed = curr_slice.copy()
      spacing = 3
      for i = -1 to 2 do:
         circle_x = prev_centre[0] + spacing*j
         seed[(circle_x, prev_centre[1])] = white_pixel
      return seed

   def segment_single_slice(current_index, prev_centre):
      # retrieve the 2d slice to be processed
      curr_slice = cropped_image[:,:, current_index]
      # create a label map
      seed = calculate_seed(curr_slice, prev_centre)
      # Calculate statistics associated with white_pixel label
      stats = sitk.LabelStatisticsImageFilter()
      stats.Execute(curr_slice, seed)
      # Threshold for SITK::ThresholdSegmentationLevelSetImageFilter
      # stats.GetMean(white_pixel) returns the mean intensity values of the pixels labeled white pixels.
      # i.e the pixels around the white_pixel are within these range of thresholds
      # The pixel far from the white_pixel have lower intensity value
      lower_threshold = (stats.GetMean(white_pixel) - label_stats_coef*stats.GetSigma(white_pixel))
      upper_threshold = (stats.GetMean(white_pixel) + label_stats_coef*stats.GetSigma(white_pixel))
      # calculate the Euclidean distance transform and use it to perform segmentation
      init_ls = sitk.SignedMaurerDistanceMap(seed)
      segment_filter.SetLowerThreshold(lower_threshold)
      segment_filter.SetUpperThreshold(upper_threshold)
      # Segmentated slice, a ndarrays of shape (x, y)
      return segment_filter.Execute(init_ls, curr_slice)

   def count_pixels(segmented_slice):
      # This function will count the number of white pixels in this segmented slice
      # and calculate a new centre based on the 
      num_of_white_pixel = 0
      x_coord = 0
      y_coord = 0
      for x from 0 to segmented_slice[0].length:
         for y from 0 to segmented_slice.length:
            if segmented_slice[x][y] == 1:
               x_coord += x
               y_coord += y
               num_of_white_pixel += 1
      new_centre = (x_coord/num_of_white_pixel, y_coord/num_of_white_pixel)
      return num_of_white_pixel, new_centre

   def is_new_centre_qualified(new_size):
      # compare new slice's number of white pixel to
      # the original slice and the previous size

      condition_1 = new_size < original_size*qualified_coefficient
      condition_2 = new_size > original_size*qualified_coefficient
      condition_3 = new_size < prev_size*qualified_coefficient

      return condition_1 and condition_2 and condition_3

   # The stats of the user's chosen slice will be used as reference
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
   original_size, original_centre = count_pixels(new_slice)

   # Repeat the above process for each slice
   for slice_i in range(start, end, step):
       cur_img_slice = cropped_image[:, :, slice_i]

       # prev_centre is the new derived centre from last segmented slice
       segmented_slice = segment_single_slice(slice_i, prev_centre)

       # element-wise operation, exactly what we doing with the double for-loop
       new_slice = segmented_slice > PixelValue.black_pixel.value

       total_coord, centre = count_pixel(new_slice)
       if is_new_centre_qualified(total_coord):
          # processing_image is the segmented volume returned
          processing_image[:, :, slice_i] = new_slice
          prev_centre = centre
          # for ascending aorta, we will generate more possible coordinates
          # and use it in segmentation algorithm
          # prev_seeds = seeds
       else:
          skipped_slice.append(slice_i)

   for slice_i in skipped_slice:
       # replace processing_image[slice_i] with the intersection of its previous and next slice

   return processing_image

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
