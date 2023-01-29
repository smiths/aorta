# Aorta Geometry Reconstruction

Developer Names: Jingyi Lin,   
> *Algorithm implemented based on the work from Kailin Chu

Date of project update: 2022/09/12

This project provides a software tool to semi-automatically segment a 3D aorta geometry from a chest CT scan. It uses a [3D Slicer](https://www.slicer.org/) extension in the source folder ([SlicerExtension/AortaGeometryReconstructor](https://github.com/smiths/aorta/tree/main/src/SlicerExtension/AortaGeometryReconstructor)) to accomplish the goal.

Users must first install the 3D Slicer software, import the extension in the source folder, and load the CT scans in DICOM file format to 3D Slicer. Valuable resources for using 3D Slicer includes a [Welcome tutorial](https://www.dropbox.com/s/vn8sqlof2kag2kk/SlicerWelcome-tutorial_Slicer4.8_SoniaPujol.pdf), a description of [3D Slicer user-interface](https://slicer.readthedocs.io/en/latest/user_guide/user_interface.html#application-overview), information on the [Volume rendering module](https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html), and the 3D Slicer's [developer guide](https://slicer.readthedocs.io/en/latest/developer_guide/index.html).

### Overview
Automatic aorta segmentation in thoracic computed tomography (CT) scans is important for aortic calcification quantification and to guide the segmentation of other central vessels. The work to manually segment regions of interest can be time-consuming and repetitive, and there are some automatic aorta segmentation algorithms posted.


This project implemented one of the aorta segmentation algorithms as 3D Slicer extension module. The algorithm first needs the user to crop the volume of interest (VOI) by using the 3D Slicer's volume rendering module. Next, the user needs to provide two important seeds, the center point of the descending Aorta and the center point of the ascending Aorta, as shown by the yellow dots in the image below.

<img src="https://user-images.githubusercontent.com/63418020/211897759-c54ffa90-760f-492f-8331-1e046ece35a7.png" height=300 width=400>

A simple diagram of the workflow:
![Untitled Diagram drawio (1)](https://user-images.githubusercontent.com/63418020/212496091-1d2b64e4-afc5-49e0-b758-07bf8b8d2798.png)


#### About 3D Slicer
3D Slicer is an open-sourced desktop software that solves advanced image computing challenges with a focus on clinical and biomedical applications. 3D Slicer software provides a clean user interface and a clear guide to developing highly customizable extensions and modules.  

The folders and files for this project are as follows:

docs - Documentation for the project  
refs - Reference material used for the project, including papers  
src - Source code   
test - Test cases  
src/SlicerExtension/AortaGeometryReconstructor - 3D Slicer extension folder to be loaded to 3D Slicer

Instructions for installing and using Aorta Geometry Reconstruction (AGR) are provided below.

### To install 3D Slicer and import an extension:
1. Download 3D Slicer from [here](https://download.slicer.org/). This project has been dated with the stable release, version 5.0.3.
2. Open Slicer application, select "Edit" from the bar menu, then "Application Settings" from the drop-down menu.
    - Select "Modules", and add the "AortaGeomReconDisplayModule" folder in the additional module paths. This folder is located in src\SlicerExtension\AortaGeometryReconstructor\\[AortaGeomReconDisplayModule](https://github.com/smiths/aorta/tree/main/src/SlicerExtension/AortaGeometryReconstructor).
    - Restart the application to take into account the new module paths.
    - Find the "AortaGeomReconDisplayModule" module as shown below:
![modules](https://user-images.githubusercontent.com/63418020/215304002-f2be0b08-9ad4-4b36-ba9d-c96db14bde80.png)
3. (Optional) In "Application Settings", and "Modules", drag "AortaGeomReconDisplayModule" to your favorite modules to access this module quickly from UI. Restart the application for the changes to the UI to appear.

### To load DICOM data:
1. Select "File" from the bar menu, then "Add DICOM Data".
2. The uploaded volume must be a scalar volume object to be viewed in the Volume Rendering module. Therefore, to make sure that we are uploading volume as a scalar volume, in "Add DICOM data" module, unselect the plugin MultiVolumeImporterPlugin as shown below,
![MultiVolumePlugin](https://user-images.githubusercontent.com/63418020/215304072-f8575886-3667-4eef-8d8b-17fd6b0dba4b.png)
3. Select "Import DICOM files", and select one of the patient's folders.
    - Once loaded, 3D Slicer will keep the patient record in the DICOM database, and the user can easily reload DICOM data from the DICOM database.
4. Select the patient file, click "load" button or double-click on the patient file to load the data into the program.


### To use Volume Rendering to crop a VOI:
For this step we use the [Volume Rendering module](https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html), a built-in module for 3D Slicer.
1. Load the Dicom files as described in the section To load DICOM [data](https://github.com/smiths/aorta#to-load-dicom-data).
2. Once loaded, select the Volume Rendering module. Select the volume that you want to crop, and click on the eye icon on the left.  
![Volume Rendering](https://user-images.githubusercontent.com/63418020/215304104-6d467cf7-8d71-4491-8d89-fbb4d0e6c834.png)
3. Within the module UI, under Display, enable Crop Display ROI, open the eye for ROI, and select CT-Bones for the preset. You should be able to see the 3D rendering in the top right corner. You can drag the points controls to control the crop, and use the sliders at the top of the image to scroll through the slice.  
![Volume Rendering UI](https://user-images.githubusercontent.com/63418020/215304132-72dfa530-d875-4b7f-9afa-546867204dd9.png)
![Crop](https://user-images.githubusercontent.com/63418020/215304142-9e8fcddd-69f6-4197-8c1c-3a0d8e46bf6e.png)
4. Change back to AortaGeomReconDisplayModule, you should also have a Volume rendering ROI or vtkMRMLMarkupsROINode object.
5. Select a new module, Crop volume sequence, in Sequences category. Select CreateNewVolumeParameters on Crop volume settings, and click on the green button which has an arrow pointing right.
![crop volume sequence option](https://user-images.githubusercontent.com/63418020/215304163-ff540c2a-7c34-45f8-9282-0aaf92813248.png)
![Crop volume sequence](https://user-images.githubusercontent.com/63418020/215304168-c737cd7b-ecc9-49e5-a8de-043d6d0c601b.png)
6. For Input volume, select the volume to crop. For Input ROI, select the ROI we created with Volume Rendering module. The default name of the ROI is "Volume rendering ROI". For output volume, you can select create new volume or modify the original volume.  
![Crop volume sequence 2](https://user-images.githubusercontent.com/63418020/215304173-b4353e4d-0100-44b6-a190-c3640443e65c.png)
7. Clicks on "Apply", and change back to AortaGeomReconDisplayModule, you should be able to find a new volume or the cropped volume.

### To get descending aorta seeds and ascending aorta seeds in phase 2 and phase 3
1. Make sure that you have done the cropping and have a cropped volume. If you are in phase 1 Crop Aorta, click on Skip to next phase to be at phase 2.
2. Right click on one of the red, green or yellow window image area, you should see a list of options as shown below.
3. "Slice intersection" option is selected once you have loaded AGR module. Right click and check "Interaction" option.
![Screenshot 2023-01-14 152226](https://user-images.githubusercontent.com/63418020/212496147-be5f060b-16a2-458f-98d6-411a88898b93.png)
4. Hold on Mouse left button to drag and place the intersection point on the point of interest, as described in the image from Overview section. 
5. If in phase 2, you should see that the value of DesAortaSeeds is changing when moving the intersection point. In phase 3, AscAortaSeeds should be changing.

### Additional tips to use this application:
1. The user can save and load an MRML scene object, which is used to store all types of data, including the loaded Dicom data, any inputs by the user on the UI, markups, etc.
2. We can use 3D Slicer's "Markups" module to draw control points and planes. These markup data are stored based on the Anatomical coordinate system, which can be independent of the Dicom data.

