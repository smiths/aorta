Glossary of Terms Used in AortaGeomRecon Documentation
======================================================


.. glossary::

    Aorta 
        The aorta is the largest artery of the body and carries blood from the heart to the circulatory system. It has several sections: The Aortic Root is the transition point where blood first exits the heart. It functions as the water main of the body.
        The Aortic arch, is the curved segment that gives the aorta its cane-like shape. It bridges the ascending and descending aorta.

    Ascending Aorta
        The ascending aorta is the first part of the aorta, which is the largest blood vessel in the body. It comes out of your heart and pumps blood through the aortic arch and into the descending aorta.

    Descending Aorta
        The descending aorta is the longest part of your aorta (the largest artery in your body). It begins after your left subclavian artery branches from your aortic arch, and it extends down into your belly. The descending aorta runs from your chest (thoracic aorta) to your abdominal area (abdominal aorta).

    Organ Segmentation
        The definition of the organ boundary or organ segmentation is helpful for the orientation and identification of the regions of interest inside the organ during the diagnostic or treatment procedure. Further, it allows the volume estimation of the organ, such as the aorta.

    inferior
        Inferior is the direction away from the head; the lower (e.g., the foot is part of the inferior extremity).

    superior
        Superior is the direction toward the head end of the body; the upper (e.g., the hand is part of the superior extremity).

    slice
        A 2-dimensional image is retrieved from a 3-dimensional volume.

    label map
         A labeled map or a label image is an image that labels each pixel of a source image. For example, the time zone map shown below has 4 labels to label the time zone for each state in the U.S.

         .. figure:: united-states-map.png
           :height: 400
           :alt: U.S. time zone map

           Fig 1. U.S. time zone map with 4 labels.

    binary dilation
        Binary dilation is a mathematical morphology operation that uses a structuring element (kernel) for expanding the shapes in an image. Using `scipy.binary_dilation <https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.binary_dilation.html>`_ as example:

         .. code-block:: console

            >>> from scipy import ndimage
            >>> a
            array([[ 0.,  0.,  0.,  0.,  0.],
                   [ 0.,  0.,  0.,  0.,  0.],
                   [ 0.,  0.,  1.,  0.,  0.],
                   [ 0.,  0.,  0.,  0.,  0.],
                   [ 0.,  0.,  0.,  0.,  0.]])
            >>> # the default kernel shape of scipy is a 3x3 structuring element with connectivity 1
            >>> ndimage.binary_dilation(a).astype(a.dtype)
            array([[ 0.,  0.,  0.,  0.,  0.],
                   [ 0.,  0.,  1.,  0.,  0.],
                   [ 0.,  1.,  1.,  1.,  0.],
                   [ 0.,  0.,  1.,  0.,  0.],
                   [ 0.,  0.,  0.,  0.,  0.]])

    segmented slice
        A 2-dimensional image retrieved by applying `SITK\:\:ThresholdSegmentationLevelSetImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ThresholdSegmentationLevelSetImageFilter.html>`_ with the euclidean distance transform image, the original image, and the threshold value calculated with the mean and the standard deviation of the intensity values that were labeled as the white pixel.

    contour line
        A contour line (also isoline, isopleth, or isarithm) of a function of two variables is a curve along which the function has a constant value so that the curve joins points of equal value.

        .. figure:: Contour2D.png
           :alt: Controu line map
           :width: 300
           :height: 300

           Fig 2. A contour line map

    Level sets
        `Level Sets <https://profs.etsmtl.ca/hlombaert/levelset/>`_ are an important category of modern image segmentation techniques based on partial differential equations (PDE), i.e. progressive evaluation of the differences among neighboring pixels to find object boundaries. The pictures below demonstrate an example of how Level Sets method work on finding the region of the heart

        .. figure:: heart-1.png
           :alt: Distance transformation

           Fig 3. The seed contour

        .. figure:: heart-2.png
           :alt: Distance transformation

           Fig 4. The result after some iterations

        .. figure:: heart-3.png
           :alt: Distance transformation

           Fig 5. The final result
    
    threshold
        A threshold is an amount, level, or limit on a scale. When the threshold is reached, something else happens or changes.

    threshold coefficient
        This coefficient is used to compute the lower and upper threshold passing through the segmentation filter `SITK\:\:ThresholdSegmentationLevelSetImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ThresholdSegmentationLevelSetImageFilter.html>`_. The algorithm first uses `SITK\:\:LabelStatisticsImageFilter  <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1LabelStatisticsImageFilter.html>`_ to get the mean and the standard deviation of the intensity values of the pixels that are labeled as the white pixel. Larger values with this coefficient imply a larger range of thresholds when performing the segmentation, which leads to a larger segmented region.

        .. note::
            The lower threshold is calculated as the mean of the intensity values subtract from the threshold coefficient multiplied by the standard deviation. The upper threshold is calculated by adding the threshold multiplied by the standard deviation.

        .. note::

           The threshold coefficient is fixed at 3.5 for now. To let the user chooses the values, we need to implement a UI parameter in the AortaGeomReconDisplay module (our 3D Slicer extension module) and mapped the value from UI to the logic module.

    Qualified coefficient
        This coefficient is used when the algorithm is determining whether a new segmented slice is acceptable in terms of the size of the segmented regions. The larger the coefficient, the looser the condition to accept the new segmented slice.

    Euclidean distance transform
        The euclidean distance transform is the map labeling each pixel of the image with the distance to the nearest obstacle pixel (black pixel for this project).

        .. figure:: Distance_Transformation.gif
           :alt: Distance transformation

           The euclidean distance transform image

    DICOM
        Digital Imaging and Communications in Medicine (DICOM) is the standard for the communication and management of medical imaging information and related data.

    3D Slicer
        `3D Slicer <https://www.slicer.org/>`_ (Slicer) is a free and open source software package for image analysis and scientific visualization. Slicer is used in a variety of medical applications, including autism, multiple sclerosis, systemic lupus erythematosus, prostate cancer, lung cancer, breast cancer, schizophrenia, orthopedic biomechanics, COPD, cardiovascular disease, and neurosurgery.
    