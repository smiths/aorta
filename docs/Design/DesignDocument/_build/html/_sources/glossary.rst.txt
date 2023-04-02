Glossary of Terms Used in AortaGeomRecon Documentation
======================================================


.. glossary::

    Aorta 
        The aorta is the largest artery of the body and carries blood from the heart to the circulatory system. It has several sections: The Aortic Root is the transition point where blood first exits the heart. It functions as the water main of the body.
        The Aortic arch, the curved segment that gives the aorta its cane-like shape. It bridges the ascending and descending aorta.

    Ascending Aorta
        The ascending aorta is the first part of the aorta, which is the largest blood vessel in the body. It comes out of your heart and pumps blood through the aortic arch and into the descending aorta.

    Descending Aorta
        The descending aorta is the longest part of your aorta (the largest artery in your body). It begins after your left subclavian artery branches from your aortic arch, and it extends downward into your belly. Descending aorta runs from your chest (thoracic aorta) to your abdominal area (abdominal aorta).

    Organ Segmentation
        The definition of the organ boundary or the organ segmentation is helpful for orientation and identification of the regions of interests inside the organ during the diagnostic or treatment procedure. Further, it allows the volume estimation of the organ, such as aorta.

    inferior
        Inferior is the direction away from the head; lower (e.g., the foot is part of the inferior extremity).

    superior
        Superior is the direction toward the head end of the body; upper (e.g., the hand is part of the superior extremity).

    Slice
        A 2 dimensional image retrived from a 3 dimensional volume.

    label map
         A label map or a label image is an image that label each pixel of a source image. For example, the time zone map shown below has 4 labels to label the time zone for each state in U.S.

         .. figure:: united-states-map.png
           :height: 400
           :alt: U.S. time zone map

           U.S. time zone map with 4 labels.

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

    Segmented slice
        A 2 dimensinoal image retrivied by applying `SITK\:\:ThresholdSegmentationLevelSetImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ThresholdSegmentationLevelSetImageFilter.html>`_ with the euclidean distance transform image and the original image.

    Threshold coefficient
        This coefficient is used to compute the lower and upper threshold passing through the segmentation filter `SITK\:\:ThresholdSegmentationLevelSetImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ThresholdSegmentationLevelSetImageFilter.html>`_. The algorithm first uses `SITK\:\:LabelStatisticsImageFilter  <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1LabelStatisticsImageFilter.html>`_ to get the mean and the sigma intensity values of the pixels that are labeled as part of the brighter pixel. Larger values with this coefficient implies a larger range of threshold when performing the segmentation. The larger the values, more pixels will be labeled as brighter pixel.

        .. note::
            Lower threshold is calculated as the mean of the intensity values substract the threhold coefficient multiply by the sigma. Upper threshold is calculated by adding the threshold multiply by the sigma.

        .. note::

           Threshold coefficient is fixed at 3.5 for now. To let the user choses the values, we need to implement an UI parameter in AortaGeomReconDisplay module (our 3D Slicer extension module), and mapped the value from UI to the logic module.

    Qualified coefficient
        This coefficient is used when comparing the number of the white pixels of the new segmented slice to the number of the white pixels of the user's chosen seed slice. The larger the coefficient, the looser the condition to accept the new segmented slice.

    Euclidean distance transform
        The euclidean distance transform is the map labeling each pixel of the image with the distance to the nearest obstacle pixel (black pixel for this project).

        .. figure:: Distance_Transformation.gif
           :alt: Distance transformation

           The euclidean distance tranform image

    DICOM
        Digital Imaging and Communications in Medicine (DICOM) is the standard for the communication and management of medical imaging information and related data.

    3D Slicer
        `3D Slicer <https://www.slicer.org/>`_ (Slicer) is a free and open source software package for image analysis and scientific visualization. Slicer is used in a variety of medical applications, including autism, multiple sclerosis, systemic lupus erythematosus, prostate cancer, lung cancer, breast cancer, schizophrenia, orthopedic biomechanics, COPD, cardiovascular disease and neurosurgery.
    