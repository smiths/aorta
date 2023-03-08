.. AortaGeomRecon documentation master file, created by
   sphinx-quickstart on Wed Feb  8 12:25:31 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to AortaGeomRecon's documentation!
==========================================

This is the design document for AortaGeomRecon module, a :term:`3D Slicer` extension to perform :term:`Aorta` segmentation and Aorta geometry reconstruction. 

You can find the source code, the installation guide, and the user manual in this GitHub `repository <https://github.com/smiths/aorta>`_.

------------

The steps before applying the main algorithm
********************************************

The algorithm works better with the chest volume cropped to a rectangular prism that contains the aorta and parts of the other organs such as back bone, some blood tissues and the heart. This can be simply done with :term:`3D Slicer` and its submodule `Volume rendering <https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html>`_. A more detailed guide can be found on this GitHub repository `section <https://github.com/smiths/aorta#to-use-volume-rendering-to-crop-a-voi>`_. 

After cropped the volume which only contains the region of interest, the algorithm needed a set of variables inputs from the user. 

The variables inputs are:

1. :term:`Descending Aorta` or :term:`Ascending Aorta` centre coordinate.
2. :term:`Qualified coefficient` larger values loose the conditiaon to accept a :term:`segmented` :term:`slice`, and vice-versa. 
3. An integer indicates the number of the slice that the algorithm can skip.


The main ideas of the algorithm
*******************************

At the beginning of the algorithm, the user's input on the aorta centre is used to generate the seed slice, 2 dimensional circle image. This seed slice will be used as a reference throughout the workflow of the algorithm. Therefore, changing the input of the centre coordiante could generate a completely different segmentation result.

For each slice starting from the user's selected slice going in the inferior or superior direction

1. The algorithm generates the seed image by using `SITK\:\:LabelStatisticsImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1LabelStatisticsImageFilter.html>`_. 

    .. note::

       A :term:`Label Statistic coefficient` can be used to control the size of the circle seed image. However, this is a constant which is not linked to UI for the user to select in the current version.


2. The algorithm then creates another image, the Euclidean distance transform of a binary image as the image intensity map, and use it with `SITK\:\:ThresholdSegmentationLevelSetImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ThresholdSegmentationLevelSetImageFilter.html>`_ to create a segmented slice.


3. The algorithm determine whether to accept the segmented slice or not, based on the number of white pixels on the segmented slice, and the qualified coefficient to control the limit.

    .. note::

       To determine whether a segmented slice is acceptable, different conditions are verified for :term:`Descending Aorta` and :term:`Ascending Aorta`. These conditions check are all invovled with the :term:`Qualified coefficient`, which is decided by the user. In simple terms, the larger the :term:`Qualified coefficient`, the looser condition on accepting a segmented slice.

4. If the algorithm accepted this segmented slice, a new centre coordinate is calculated, and used as the seed coordinate for segmenting the next slice.

5. When a segmented slice is not acceptable, the algorithm will skip this slice if the number of skipped slice is less then the integer given by the user. The algorithm will try to replace these skipped slice by reading the overlapped area of the previous and the next slice.

The pseudocode of the algorithm
*******************************

.. code-block:: python

   segmented_slice = get_image_segment()
   # Any value (grey-scaled) above 0 will be set to white pixel
   new_slice = segmented_slice > PixelValue.black_pixel.value
   total_coord, centre = count_pixels(new_slice)

   # start is always the index of the original slice
   # end could be the index of the superior or the inferior of the aorta
   for slice_i in range(start, end, step):
       cur_img_slice = cropped_image[:, :, slice_i]
       segmented_slice = get_image_segment()
       new_slice = segmented_slice > PixelValue.black_pixel.value
       total_coord, centre, seeds = count_pixel(new_slice)
       if is_new_centre_qualified(total_coord):
            processing_image[:, :, slice_i] = new_slice
            prev_centre = centre
            prev_seeds = seeds


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
