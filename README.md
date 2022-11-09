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

### Tips to use this application:
1. The user can save and load an MRML scene object, which is used to store all types of data, including the loaded Dicom data, any inputs by the user on the UI, markups, etc.
2. We can use 3D Slicer's "Markups" module to draw control points and planes. These markup data are stored based on the Anatomical coordinate system, which can be independent of the Dicom data.

### Simple workflow when our module is connected to the backend:
1. Load new patient Dicom data
2. Use the "Markups" module from 3D Slicer to mark the area of interest.
3. Select "AortaGeomReconDisplayModule", input any data that are necessary to process, and click the "Apply" button lied in the module to process.



