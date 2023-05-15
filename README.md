# Aorta Geometry Reconstruction

Developer Names: Jingyi Lin   
> *Segmentation algorithm implemented partly based the [work](https://github.com/smiths/GeomRecon/tree/master/People/Kailin) from Kailin Chu

Date of project update: 2023/05/15

The AortaGeomRecon [design document](https://joviel25.github.io/AortaGR-design-document/index.html) explains in detail of the algorithm workflow; It includes a detailed glossary of the terms used throughout the other documentation. 

This project provides a software tool to semi-automatically segment a 3D aorta geometry from a chest CT scan. It uses a [3D Slicer](https://www.slicer.org/) extension in the source folder ([SlicerExtension/AortaGeometryReconstructor](https://github.com/smiths/aorta/tree/main/src/SlicerExtension/AortaGeometryReconstructor)) to accomplish the goal.

Users must first install the 3D Slicer software, import the extension in the source folder, and load the CT scans in DICOM file format to 3D Slicer. Valuable resources for using 3D Slicer includes a [Welcome tutorial](https://www.dropbox.com/s/vn8sqlof2kag2kk/SlicerWelcome-tutorial_Slicer4.8_SoniaPujol.pdf), a description of [3D Slicer user-interface](https://slicer.readthedocs.io/en/latest/user_guide/user_interface.html#application-overview), information on the [Volume rendering module](https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html), and the 3D Slicer's [developer guide](https://slicer.readthedocs.io/en/latest/developer_guide/index.html).

## Overview
Automatic aorta segmentation in thoracic computed tomography (CT) scans is important for aortic calcification quantification and to guide the segmentation of other central vessels. The work to manually segment regions of interest can be time-consuming and repetitive, and there are some automatic aorta segmentation algorithms posted.

This project implemented one of the aorta segmentation algorithms as 3D Slicer extension module. The algorithm first needs the user to crop the volume of interest (VOI) by using the 3D Slicer's volume rendering module. Next, the user needs to provide two important seeds, the center point of the descending Aorta and the center point of the ascending Aorta, as shown by the yellow dots in the image below.

<p align="center">
    <img src="https://github.com/smiths/aorta/blob/main/src/screenshots/Aorta_seeds.png" height=300 width=400 />
</p>


### About 3D Slicer
3D Slicer is an open-sourced desktop software that solves advanced image computing challenges with a focus on clinical and biomedical applications. 3D Slicer software provides a clean user interface and a clear guide to developing highly customizable extensions and modules.  

The folders and files for this project are as follows:

docs - Documentation for the project  
refs - Reference material used for the project, including papers  
src - Source code   
test - Test cases  
src/SlicerExtension/AortaGeometryReconstructor - 3D Slicer extension folder to be loaded to 3D Slicer

## To install 3D Slicer and import an extension:

1. Download 3D Slicer from [here](https://download.slicer.org/). This project has been tested with the stable release, version 5.0.3.

2. Click on the image below for a video demonstrating the import of AortaGeomRecon module, and the complete workflow to perform aorta segmentation.
[![AortaGeomRecon Video instruction](https://github.com/smiths/aorta/blob/main/src/screenshots/Thumbnail.jpg)](https://youtu.be/1eK5k6bazNs)

## To apply the segmentation algorithm
1. Make sure that you have done the cropping and have a cropped volume in phase 1 Crop Aorta, then click on Apply to move to next phase.
2. Once you are in phase 2 Aorta Segmentation, right click on one of the red, green or yellow window image area, you should see a list of options as shown below.
3. Select the "Slice intersection" option once you have loaded AGR module. Right click and check "Interaction" option. Alternatively, you can hold "shift" and move around mouse cursor to move around the intersection point.
<p align="center">
    <img src="https://github.com/smiths/aorta/blob/main/src/screenshots/Interaction.png" />
</p>

4. Hold on Mouse left button to drag and place the intersection point on the point of interest, as described in the image from Overview section. 
5. In phase 2 Aorta Segmentation, you should see that the values of DesAortaSeeds and AscAortaSeeds coordinate are changing when moving the intersection point. Simply lock one of the two seeds with the corresponding checkbox and use intersection to input the other one. Make sure you select the two seeds from the same slice. Once you have entered all hyperparameters, click on Apply. After a few minutes, you should see a new volume named "Seg_th{a number}\_k{a number}\_c{a number}\_p{a number}", the name simply takes some of the important hyperparameters as the name, where "th" stands for threshold coefficient, k stands for kernel size, c for curvature scaling, and p for propagation scaling.

### Additional tips for hyperparmeters optimization (based on the 6 samples).
1. As tested with the current 6 samples, I would always start with a threshold coefficient range of 2-3, a stop limit of 5-6, and kernel size of 7-10. This would ensure that the noises (blood vessels, backbones) are excluded as much as possible. Then start increasing the stop limit, threshold coefficient.
2. Curvature scaling adds weight to the segmentation speed term at the curvature. This implies the segmentation result would have high probability to include the curvature. However, this might not be the best hyperparameter to tune up, because usually the aorta is not an isolated island, and it connects to the backbone or other noises. Tune this hyperparameter up will segment out any connected island (noises). 
3. Propagation scaling adds weight to the segmentation speed term in general, this means that if not reaching the boarder, the segmentation filter will include the next layer of pixels. 

## To display the segmentation label image
1. Use Volume Rendering Module and follow the [step 2](https://github.com/smiths/aorta/tree/main#to-use-volume-rendering-to-crop-a-voi) to display the segmented volume. For example, to show the segmented result from phase 2 Descending Aorta Segmentation, you should select the volume with the name "Segmented Descending Aorta Volume" by default.
2. You can see both the original volume and the segmented volume to see the overlaps between the two volumes. Make sure you select the eye icon for both volumes, and make sure that the original volume use preset of CT-Bones to have the different coloring.

### Get the vtk output of the cropped volume or segmentation label image
1. Use file dialog to select a path.
2. If on phase 1, the program outputs the cropped volume. Otherwise, the program outputs the segmentation label image.

## Additional tips to use this application:
1. The user can save and load an MRML scene object, which is used to store all types of data, including the loaded Dicom data, any inputs by the user on the UI, markups, etc.
2. In "Application Settings", and "Modules", drag "AortaGeomReconDisplayModule", "Volume Rendering", and "Crop Volume" modules to your favorite modules to access these modules quickly from UI. Restart the application for the changes to the UI to appear.


## The text description version of how to import an extension, load DICOM data, use volume rendering and crop volume:

### To import AortaGeomReconDisplay module
1. Open Slicer application, select "Edit" from the bar menu, then "Application Settings" from the drop-down menu.
    - Select "Modules", and add the "AortaGeomReconDisplayModule" folder in the additional module paths. This folder is located in src\SlicerExtension\AortaGeometryReconstructor\\[AortaGeomReconDisplayModule](https://github.com/smiths/aorta/tree/main/src/SlicerExtension/AortaGeometryReconstructor).
    - Restart the application to take into account the new module paths.
    - Find the "AortaGeomReconDisplayModule" module as shown below:
    <p align="center">
        <img src="https://github.com/smiths/aorta/blob/main/src/screenshots/ARG_module.png" />
    </p>

### To load DICOM data:
1. Select "File" from the bar menu, then "Add DICOM Data".
2. The uploaded volume must be a scalar volume object to be viewed in the Volume Rendering module. Therefore, to make sure that we are uploading volume as a scalar volume, in "Add DICOM data" module, unselect the plugin MultiVolumeImporterPlugin as shown below,

<p align="center">
<img src="https://github.com/smiths/aorta/blob/main/src/screenshots/MultiVolumePlugin.png" />
</p>

3. Select "Import DICOM files", and select one of the patient's folders.
    - Once loaded, 3D Slicer will keep the patient record in the DICOM database, and the user can easily reload DICOM data from the DICOM database.
4. Select the patient file, click "load" button or double-click on the patient file to load the data into the program.


### To use Volume Rendering to crop a VOI:
For this step we use the [Volume Rendering module](https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html), a built-in module for 3D Slicer.
1. Load the Dicom files as described in the section To load DICOM [data](https://github.com/smiths/aorta#to-load-dicom-data).
2. Once loaded, select the Volume Rendering module. Select the volume that you want to crop, and click on the eye icon on the left. 

<p align="center">
    <img src="https://github.com/smiths/aorta/blob/main/src/screenshots/Volume_Rendering_module.png" />
</p>

3. Within the module UI, under Display, enable Crop Display ROI, open the eye for ROI, and select CT-Bones for the preset. You should be able to see the 3D rendering in the top right corner. You can drag the points controls to control the crop, and use the sliders at the top of the image to scroll through the slice.  

<p align="center">
    <img src="https://github.com/smiths/aorta/blob/main/src/screenshots/Volume_Rendering_UI.png" />
</p>

<p align="center">
    <img src="https://github.com/smiths/aorta/blob/main/src/screenshots/Crop.png" />
</p>

4. Change back to AortaGeomReconDisplayModule, you should also have a Volume rendering ROI or vtkMRMLMarkupsROINode object.
5. Select a new module, Crop volume, in Converters category. Select CreateNewVolumeParameters on Crop Volume Parameter Set.
<p align="center">
    <img src="https://github.com/smiths/aorta/blob/main/src/screenshots/Crop_volume_create_new_parameter.png" />
</p>
6. For Input volume, select the volume to crop. For Input ROI, select the ROI we created with Volume Rendering module. The default name of the ROI is "Volume rendering ROI". If you are unable to select ROI, go back to step 2 and use Volume Rendering module to create a ROI. For output volume, you can select create new volume or modify the original volume.  
<p align="center">
    <img src="https://github.com/smiths/aorta/blob/main/src/screenshots/Crop_volume_parameters.png" />
</p>
7. Clicks on "Apply", and change back to AortaGeomReconDisplayModule, you should be able to find a new volume or the cropped volume.
