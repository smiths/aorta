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

    DICOM
        Digital Imaging and Communications in Medicine (DICOM) is the standard for the communication and management of medical imaging information and related data.

    Label Statistic coefficient
        This coefficient is used to compute the lower and upper threshold passing through the segmentation filter `SITK\:\:ThresholdSegmentationLevelSetImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ThresholdSegmentationLevelSetImageFilter.html>`_. Larger values with this coefficient implies a larger range of threshold when performing the segmentation. This could be adjusted based on the area of the aorta center.

        .. note::

           Label Statistic coefficient is fixed at 3.5 for now. To let the user choses the values, we need to implement an UI parameter in AortaGeomReconDisplay module (our 3D Slicer extension module), and mapped the value from UI to the logic module.

    Organ Segmentation
      The definition of the organ boundary or the organ segmentation is helpful for orientation and identification of the regions of interests inside the organ during the diagnostic or treatment procedure. Further, it allows the volume estimation of the organ.

    Qualified coefficient
        This coefficient is used when comparing the number of the white pixels of the new slice to the number of the white pixels of the user's chosen seed slice. The larger the coefficient, the looser the condition to accept the new slice.

    slice
        A 2 dimensional image retrived from a 3 dimensional volume.

    segmented slice
        A 2 dimensinoal image retrivied by applying `SITK\:\:ThresholdSegmentationLevelSetImageFilter <https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ThresholdSegmentationLevelSetImageFilter.html>`_ with the euclidean distance transform image and the original image.

    3D Slicer
        `3D Slicer <https://www.slicer.org/>`_ (Slicer) is a free and open source software package for image analysis and scientific visualization. Slicer is used in a variety of medical applications, including autism, multiple sclerosis, systemic lupus erythematosus, prostate cancer, lung cancer, breast cancer, schizophrenia, orthopedic biomechanics, COPD, cardiovascular disease and neurosurgery.