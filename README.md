# Aorta Geometry Reconstruction

Developer Names: Jingyi Lin

Date of project start: 2022/09/12

This project aims to provides a software tool to semi-automatically segment out a 3D aorta geometry from a chest CT scans. It uses the [3D Slicer software](https://www.slicer.org/), and provides a 3D Slicer extension in the source folder (SlicerExtension/AortaGeometryReconstructor) to accomplish the goal.

User must first install the 3D Slicer software, import the extension in the source folder, and load the CT scans in DICOM file format to 3D Slicer.

This is the [link](https://www.dropbox.com/s/vn8sqlof2kag2kk/SlicerWelcome-tutorial_Slicer4.8_SoniaPujol.pdf) to the Slicer Welcome tutorial.

This [link](https://slicer.readthedocs.io/en/latest/user_guide/user_interface.html#application-overview) described the 3D Slicer user-interface.

About [Volume rendering module](https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html)

The 3D Slicer's [developer guide](https://slicer.readthedocs.io/en/latest/developer_guide/index.html).

### Overview:
Automatic aorta segmentation in thoracic computed tomography (CT) scans is important for aortic calcification quantification and to guide the segmentation of other central vessels. The work to manually segmented region of interest can be time-consuming and repeatitve, and there are many automatic aorta segmentation algorithms posted.

This project implemented one of the aorta segmentation algorithm as 3D Slicer extension module. The algorithm first need user to crop the volume of interest (VOI) by using 3D Slicer' volume rendering module. Next, user needs to provide two important seeds, the centre point of descending Aorta and the centre point of the asceding Aorta, as shown on the image below.

<img src="https://user-images.githubusercontent.com/63418020/211897759-c54ffa90-760f-492f-8331-1e046ece35a7.png" height=300 width=400>

A simple diagram about the workflow:
![Untitled Diagram drawio](https://user-images.githubusercontent.com/63418020/211897588-eb7da723-919d-4c4d-b06a-8fefb9c8dd0b.png)

#### About 3D Slicer
3D Slicer is a open-sourced Desktop software that solves advanced image computing challenges with a focus on clinical and biomedical applications. 3D Slicer software provides a clean user-interface and a clear guide to develop highly customizable extension and modules. 

The folders and files for this project are as follows:

docs - Documentation for the project  
refs - Reference material used for the project, including papers  
src - Source code   
test - Test cases  
etc.  


### To install 3D Slicer and import an extension:
1. Download 3D Slicer from [here](https://download.slicer.org/). I used the stable release, version 5.0.3.
2. Open Slicer application, select "Edit" from the bar menu, then "Application Settings" from the drop-down menu.
    - Select "Modules", and add the "AortaGeomReconDisplayModule" folder in the additional module paths. This folder is located in the [display-module](https://github.com/smiths/aorta/tree/display-module) branch, in "src\SlicerExtension\AortaGeometryReconstructor\AortaGeomReconDisplayModule".
    - Restart the application as indicated to take into account the new module paths.
    - Find the "AortaGeomReconDisplayModule" module as shown below:
![image](https://user-images.githubusercontent.com/63418020/200126448-9aa863ac-b02d-4177-b3b9-698f66d31030.png)
3. (Optional) In "Application Settings", and "Modules", drag "AortaGeomReconDisplayModule" to your favorite modules to access this module quickly from UI. Restart the application for the changes to the UI to appear.

### To load DICOM data:
1. Select "File" from the bar menu, then "Add DICOM Data".
2. Notices that the uploaded volume must be a scalar volume object to be view in Volume Rendering module. 
    - To make sure that we are uploading volume as a scalar volume, in "Add DICOM data" module, unselected the plugin MultiVolumeImporterPlugin as shown below
![screenshot]()

3. Select "Import DICOM files", and select one of the patient's folders.
    - Once loaded, 3D Slicer will keep the patient record in the DICOM database, and the user can easily reload DICOM data from the DICOM database.

### To use Volume Rendering to crop a VOI:
The tutorial about use [Volume Rendering module](https://slicer.readthedocs.io/en/latest/user_guide/modules/volumerendering.html).
1. Load the dicom files as described in the section To load DICOM data.
2. Once loaded, select Volume Rendering module. Select the volume that you want to crop, and click on the eye icon on the left.  
![Screenshot 2022-11-28 095731](https://user-images.githubusercontent.com/63418020/204309728-c9ca1470-c9cd-4f6a-89f7-e3c2f4155fb5.png)
![Screenshot 2022-11-28 100009](https://user-images.githubusercontent.com/63418020/204309912-12301994-1d9a-4b96-9868-c1ad35eb1443.png)
3. Within the module UI, under Display, enable Crop Display ROI, then select CT-Bones for preset. You should be able to see the 3D rendering on top right corner. You can use the points controls to crop.  
![Screenshot 2022-11-28 100107](https://user-images.githubusercontent.com/63418020/204310154-9fd8df58-021d-416b-b64a-80f01ed7f49a.png)
![Screenshot 2022-11-28 100255](https://user-images.githubusercontent.com/63418020/204310637-f0c16410-0ad6-40ec-853e-9bbd993ed4ff.png)
4. Change back to AortaGeomReconDisplayModule, you should also have a Volume rendering ROI, or vtkMRMLMarkupsROINode object.
5. Select a new module, Crop volume sequence, in Sequences category. Click on the green button which has an arrow pointing right.  
![Screenshot 2022-11-28 100408](https://user-images.githubusercontent.com/63418020/204310886-322c9e33-a13e-42b4-aded-060dd229d71b.png)
![Screenshot 2022-11-28 100449](https://user-images.githubusercontent.com/63418020/204311044-bb3d4f10-ee01-4fcd-8a63-6ce4b879cec1.png)
6. For Input volume, select the volume to crop. For Input ROI, select the ROI we created with Volume Rendering module. For output volume, you can select create new volume or modify the original volume.
7. Click on Apply, and change back to AortaGeomReconDisplayModule, you shoule be able to find a new volume or the cropped volume.

### To get descending aorta seeds and ascending aorta seeds in phase 2 and phase 3
1. Make sure that you have done the cropping and have a cropped volume. If you are in phase 1 Crop Aorta, click on Skip to next phase to be at phase 2.
2. Right click on one of the red, green or yello window image area, you should see a list of options as shown below.
![Screenshot 2022-11-28 100408](https://user-images.githubusercontent.com/63418020/204310886-322c9e33-a13e-42b4-aded-060dd229d71b.png)
3. First check on "Slice intersection" option. Right click again and check Interaction.
4. Hold on Mouse left button to drag and place the intersection point on the point of interest, as described in the image from Overview section. 
5. If in phase 2, you should see that the value of DesAortaSeeds is changing when moving the intersection point. In phse 3, AscAortaSeeds should be changing.

### Additiaonl tips to use this application:
1. The user can save and load an MRML scene object, which is used to store all types of data, including the loaded Dicom data, any inputs by the user on the UI, markups, etc.
2. We can use 3D Slicer's "Markups" module to draw control points and planes. These markup data are stored based on the Anatomical coordinate system, which can be independent of the Dicom data.

