# Aorta Geometry Reconstruction

Developer Names: Jingyi Lin

Date of project start: 2022/09/12

This project is to generate 3D aorta geometry (.vtk) from CT scans (.dicom).

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
3. (Optional) In "Application Settings", and "Modules", drag "AortaGeomReconDisplayModule" to your favorite modules to access this module quickly from UI.

### To load DICOM data:
1. Select "File" from the bar menu, then "Add DICOM Data".
2. Select "Import DICOM files", and select one of the patient's folders.
    - Once loaded, 3D Slicer will keep the patient record in the DICOM database, and the user can easily reload DICOM data from the DICOM database.

### To use Volume Rendering to crop image:
1. Load the dicom files as described in the section To load DICOM data.
2. Notices that the uploaded volume must be a scalar volume object to be view in Volume Rendering module
    - Some of the current samples contain repeated slices. When loading this dicom data to Slicer, the result volume will automatically becomes a multi volume object. 
![Screenshot 2022-11-28 154534](https://user-images.githubusercontent.com/63418020/204377349-ed4fe11f-cc42-49b8-9175-27cbb6895f33.png)
    - For example, sample 22429388 has 1341 .dicom files, but when loaded as a volume, it has a depth of 447 (slice 0 to 446). You can verify it by inspecting the axial axis (Red window by Slicer's default). Drag the axial high and low to see the maximum depth. 
![Screenshot 2022-11-28 154816](https://user-images.githubusercontent.com/63418020/204378395-cba96ad0-70b2-4756-bb9f-a43ab9b3f174.png)
![Screenshot 2022-11-28 154901](https://user-images.githubusercontent.com/63418020/204378397-1ed83a9e-9354-4e81-907e-f6fdf6b62022.png)
    - Sort the folder containing the sample, and copy the first 447 dicom files to a new folder. Then load the new folder as dicom data.
3. Once loaded, select Volume Rendering module. Select the volume that you want to crop, and click on the eye icon on the left.  
![Screenshot 2022-11-28 095731](https://user-images.githubusercontent.com/63418020/204309728-c9ca1470-c9cd-4f6a-89f7-e3c2f4155fb5.png)
![Screenshot 2022-11-28 100009](https://user-images.githubusercontent.com/63418020/204309912-12301994-1d9a-4b96-9868-c1ad35eb1443.png)
4. Within the module UI, under Display, enable Crop Display ROI, then select CT-Bones for preset. You should be able to see the 3D rendering on top right corner. You can use the points controls to crop.  
![Screenshot 2022-11-28 100107](https://user-images.githubusercontent.com/63418020/204310154-9fd8df58-021d-416b-b64a-80f01ed7f49a.png)
![Screenshot 2022-11-28 100255](https://user-images.githubusercontent.com/63418020/204310637-f0c16410-0ad6-40ec-853e-9bbd993ed4ff.png)
5. Change back to AortaGeomReconDisplayModule, you should also have a Volume rendering ROI, or vtkMRMLMarkupsROINode object.
6. Select a new module, Crop volume sequence, in Sequences category. Click on the green button which has an arrow pointing right.  
![Screenshot 2022-11-28 100408](https://user-images.githubusercontent.com/63418020/204310886-322c9e33-a13e-42b4-aded-060dd229d71b.png)
![Screenshot 2022-11-28 100449](https://user-images.githubusercontent.com/63418020/204311044-bb3d4f10-ee01-4fcd-8a63-6ce4b879cec1.png)
7. For Input volume, select the volume to crop. For Input ROI, select the ROI we created with Volume Rendering module. For output volume, you can select create new volume or modify the original volume.
8. Click on Apply, and change back to AortaGeomReconDisplayModule, you shoule be able to find a new volume or the cropped volume.
### Tips to use this application:
1. The user can save and load an MRML scene object, which is used to store all types of data, including the loaded Dicom data, any inputs by the user on the UI, markups, etc.
2. We can use 3D Slicer's "Markups" module to draw control points and planes. These markup data are stored based on the Anatomical coordinate system, which can be independent of the Dicom data.

### Simple workflow when our module is connected to the backend:
1. Load new patient Dicom data
2. Use the "Markups" module from 3D Slicer to mark the area of interest.
3. Select "AortaGeomReconDisplayModule", input any data that are necessary to process, and click the "Apply" button lied in the module to process.



