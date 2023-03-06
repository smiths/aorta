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
The algorithm works better with the chest volume cropped to a rectangular prism that contains the aorta and parts of the other organs such as back bone, some blood tissues and the heart. This is can be simply done with :term:`3D Slicer` and its submodule `Volume rendering <https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html>`_. A more detailed guide can be found on this GitHub repository `section <https://github.com/smiths/aorta#to-use-volume-rendering-to-crop-a-voi>`_. 

After cropped the volume which only contains the region of interest, the algorithm needed a set of seed values from the user. 

The seeds values contains the following:

1. :term:`Descending Aorta` center coordinate.
2. :term:`Qualified coefficient` larger values loose the conditiaon to accept a segmented slice, and vice-versa. 
3. An integer indicates the number of the slice that the algorithm can skip.

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
