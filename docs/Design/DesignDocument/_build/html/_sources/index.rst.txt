.. AortaGeomRecon documentation master file, created by
   sphinx-quickstart on Wed Feb  8 12:25:31 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to AortaGeomRecon's documentation!
==========================================

This is the design document for AortaGeomRecon module, a :term:`3D Slicer` extension to perform :term:`Aorta` segmentation and Aorta geometry reconstruction. 

You can find the source code, the installation guide, and the user manual in this GitHub `repository <https://github.com/smiths/aorta>`_.

------------

The workflow of the algorithm
*****************************
The algorithm works better with the chest volume cropped to a rectangular prism that contains the aorta and parts of the other organs such as back bone, some blood tissues and the heart. This can be simply done with :term:`3D Slicer` and its submodule `Volume rendering <https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html>`_. A more detailed guide can be found on this GitHub repository `section <https://github.com/smiths/aorta#to-use-volume-rendering-to-crop-a-voi>`_. 

After cropped the volume which only contains the region of interest, the algorithm needed a set of variables inputs from the user. 

The seeds values contains the following:

1. :term:`Descending Aorta` or :term:`Ascending Aorta` center coordinate.
2. :term:`Qualified coefficient` larger values loose the conditiaon to accept a :term:`segmented` :term:`slice`, and vice-versa. 
3. An integer indicates the number of the slice that the algorithm can skip.

The algorithm generates a 2d circle image as the seed image by reading the aorta center coordiante and using `SITK\:\:LabelStatisticsImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1LabelStatisticsImageFilter.html>`_. A :term:`Label Statistic coefficient` can be used to control the size of the circle seed image. 

The algorithm then creates another image, the Euclidean distance transform of a binary image as the image intensity map, and use it with `SITK\:\:ThresholdSegmentationLevelSetImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ThresholdSegmentationLevelSetImageFilter.html>`_ to create a segmented slice.

To determine whether a segmented slice is acceptable, different conditions are verified for `Descending Aorta` and :term:`Ascending Aorta`. However, these conditions check are all invovled with the :term:`Qualified coefficient`, which is decided by the user. In simple terms, the larger the :term:`Qualified coefficient`, the loose condition on accepting a segmented slice. If the algorithm accepted this segmented slice, a new centre coordinate is calculated, and used as the seed coordinate for segmenting the next slice.

When a segmented slice is not acceptable, the algorithm will skip this slice if the number of skipped slice is less then the integer given by the user. The algorithm will try to replace these skipped slice by reading the overlapped area of the previous and the next slice.

.. note::

   You can find the definitions of each function within the module below

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules


Indices and tables
******************

| :ref:`genindex`
| :ref:`modindex`

.. toctree::
   :maxdepth: 1

   Glossary <glossary>
