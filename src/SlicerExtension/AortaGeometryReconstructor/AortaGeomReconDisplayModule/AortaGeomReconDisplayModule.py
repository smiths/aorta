import logging
import os

import vtk

import slicer
from slicer.ScriptedLoadableModule import *  # noqa: F403
from slicer.util import VTKObservationMixin

import sitkUtils


#
# AortaGeomReconDisplayModule
#

class AortaGeomReconDisplayModule(ScriptedLoadableModule):  # noqa: F405
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)  # noqa: F405

        # TODO: make this more human readable by adding spaces
        self.parent.title = "AortaGeomReconDisplayModule"

        # TODO: set categories
        # (folders where the module shows up in the module selector)
        self.parent.categories = ["Segmentation"]

        # TODO: add here list of module names that this module requires
        self.parent.dependencies = ["Markups"]

        self.parent.contributors = ["Jingyi Lin (McMaster University)"]

        # TODO: update with short description of the module
        # and a link to online module documentation
        self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#AortaGeomReconDisplayModule">module documentation</a>.
"""  # noqa: E501

        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""  # noqa: E501

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#

def registerSampleData():
    """
    Add data sets to Sample Data module.
    """
    # It is always recommended to provide sample data
    # for users to make it easy to try the module,
    # but if no sample data is available then this method
    # (and associated startupCompeted signal connection) can be removed.

    import SampleData
    iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

    # To ensure that the source code repository remains small
    # (can be downloaded and installed quickly)
    # it is recommended to store data sets
    # that are larger than a few MB in a Github release.

    # AortaGeomReconDisplayModule1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='AortaGeomReconDisplayModule',
        sampleName='AortaGeomReconDisplayModule1',

        # Thumbnail should have size of approximately
        # 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module,
        # "Capture all views" option enabled,
        # "Number of images" set to "Single".

        thumbnailFileName=os.path.join(
            iconsPath, 'AortaGeomReconDisplayModule1.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",  # noqa: E501
        fileNames='AortaGeomReconDisplayModule1.nrrd',
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())  # noqa: E501
        checksums='SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',  # noqa: E501
        # This node name will be used when the data set is loaded
        nodeNames='AortaGeomReconDisplayModule1'
    )

    # AortaGeomReconDisplayModule2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='AortaGeomReconDisplayModule',
        sampleName='AortaGeomReconDisplayModule2',
        thumbnailFileName=os.path.join(iconsPath, 'AortaGeomReconDisplayModule2.png'),  # noqa: E501
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",  # noqa: E501
        fileNames='AortaGeomReconDisplayModule2.nrrd',
        checksums='SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',  # noqa: E501
        # This node name will be used when the data set is loaded
        nodeNames='AortaGeomReconDisplayModule2'
    )


#
# AortaGeomReconDisplayModuleWidget
#

class AortaGeomReconDisplayModuleWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):  # noqa: F405,E501
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time
        and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)  # noqa: F405

        # needed for parameter node observation
        VTKObservationMixin.__init__(self)

        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

    def setup(self):
        """
        Called when the user opens the module the first time
        and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)  # noqa: F405

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually
        # and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/AortaGeomReconDisplayModule.ui'))  # noqa: E501
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)
        # self.ui.applyButton.toolTip = "Compute output volume"
        self.ui.clearButton.enabled = True

        # Set scene in MRML widgets.
        # Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in
        # is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class.
        # Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = AortaGeomReconDisplayModuleLogic()

        # Connections

        # These connections ensure that we update parameter node
        # when scene is closed
        scene = slicer.mrmlScene
        self.addObserver(scene, scene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(scene, scene.EndCloseEvent, self.onSceneEndClose)

        # This will get Scene's all node objects

        # These connections ensure that
        # whenever user changes some settings on the GUI,
        # that is saved in the MRML scene
        # (in the selected parameter node).

        self.ui.cropIndex.connect(
            "coordinatesChanged(double*)", self.updateParameterNodeFromGUI)

        self.ui.cropSize.connect(
            "coordinatesChanged(double*)", self.updateParameterNodeFromGUI)

        self.ui.curveSeeds.connect(
            "coordinatesChanged(double*)", self.updateParameterNodeFromGUI)

        self.ui.segmentationFactor.connect(
            "valueChanged(double)", self.updateParameterNodeFromGUI)

        # Buttons
        self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
        self.ui.clearButton.connect('clicked(bool)', self.onClearButton)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes
        # (GUI wlil be updated when the user enters into the module)
        self.removeObserver(
            self._parameterNode,
            vtk.vtkCommand.ModifiedEvent,
            self.updateGUIFromParameterNode
        )

    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed
        # then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values,
        # node selections, etc.
        # so that when the scene is saved and reloaded,
        # these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

# Select default input nodes
# if nothing is selected yet to save a few clicks for the user
# if not self._parameterNode.GetNodeReference("cropIndex"):
#     first_widget = slicer.mrmlScene.GetFirstNodeByName("cropIndex")
#     if first_widget:
#         self._parameterNode.SetNodeReferenceID(
#             "cropIndex", first_widget.GetID())

# if not self._parameterNode.GetNodeReference("cropSize"):
#     second_widget = slicer.mrmlScene.GetFirstNodeByName("cropSize")
#     if second_widget:
#         self._parameterNode.SetNodeReferenceID(
#             "cropSize", second_widget.GetID())

        # print(self._parameterNode)

    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because
        when the parameter node is changed
        then the GUI must be updated immediately.
        """

        if inputParameterNode:
            self.logic.createDefaultParameters(inputParameterNode)

        # Unobserve previously selected parameter node
        # and add an observer to the newly selected.
        # Changes of parameter node are observed so that
        # whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.

        if self._parameterNode is not None:
            self.removeObserver(
                self._parameterNode,
                vtk.vtkCommand.ModifiedEvent,
                self.updateGUIFromParameterNode
            )

        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(
                self._parameterNode,
                vtk.vtkCommand.ModifiedEvent,
                self.updateGUIFromParameterNode
            )

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def anyEmptySeed(self):
        emptyCropSize = (self.ui.cropSize.coordinates == "0,0,0")
        emptyCropIndex = (self.ui.cropIndex.coordinates == "0,0,0")
        emptyCurveSeeds = (self.ui.curveSeeds.coordinates == "0,0,0")
        return emptyCurveSeeds or emptyCropIndex or emptyCropSize

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show
        the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI
        # (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        self.ui.cropSize.coordinates = self._parameterNode.GetParameter(
            "cropSize")

        self.ui.cropIndex.coordinates = self._parameterNode.GetParameter(
            "cropIndex")

        self.ui.curveSeeds.coordinates = self._parameterNode.GetParameter(
            "curveSeeds")

        self.ui.segmentationFactor.value = float(
            self._parameterNode.GetParameter("segmentationFactor"))
        self.ui.applyButton.enabled = (not self.anyEmptySeed())

# Update node selectors and sliders
# self.ui.inputSelector.setCurrentNode(self._parameterNode.GetParameter("InputVolume"))
# self.ui.outputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputVolume"))
# self.ui.invertedOutputSelector.setCurrentNode(
#     self._parameterNode.GetNodeReference("OutputVolumeInverse"))

# self.ui.imageThresholdSliderWidget.value = float(
#     self._parameterNode.GetParameter("Threshold"))
# self.ui.invertOutputCheckBox.checked = (
#     self._parameterNode.GetParameter("Invert") == "true")

# Update buttons states and tooltips
# if self._parameterNode.GetNodeReference("InputVolume")
#    and self._parameterNode.GetNodeReference("OutputVolume"):
#     self.ui.applyButton.toolTip = "Compute output volume"
#     self.ui.applyButton.enabled = True
# else:
#     self.ui.applyButton.toolTip = "Select input and output volume nodes"
#     self.ui.applyButton.enabled = False

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node
        (so that they are restored when the scene is saved and loaded).
        """
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return
        wasModified = self._parameterNode.StartModify()

        # Modify all properties in a single batch
        self._parameterNode.SetParameter(
            "cropIndex", self.ui.cropIndex.coordinates)

        self._parameterNode.SetParameter(
            "cropSize", self.ui.cropSize.coordinates)

        self._parameterNode.SetParameter(
            "curveSeeds", self.ui.curveSeeds.coordinates)

        self._parameterNode.SetParameter(
            "segmentationFactor", str(self.ui.segmentationFactor.value))

        self.ui.applyButton.enabled = (not self.anyEmptySeed())


# self._parameterNode.SetNodeReferenceID(
#     "InputVolume", self.ui.inputSelector.currentNodeID)
# self._parameterNode.SetNodeReferenceID(
#     "OutputVolume", self.ui.outputSelector.currentNodeID)
# self._parameterNode.SetNodeReferenceID(
#     "OutputVolumeInverse", self.ui.invertedOutputSelector.currentNodeID)

        self._parameterNode.EndModify(wasModified)

    def onClearButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        errorMessage = "Failed to clear inputs"
        with slicer.util.tryWithErrorDisplay(errorMessage, waitCursor=True):
            self.logic.setDefaultParameters(self.logic.getParameterNode())

    def onApplyButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        errorMessage = "Failed to compute results."
        
        with slicer.util.tryWithErrorDisplay(errorMessage, waitCursor=True):
            # Compute output
            self.logic.process(
                self._parameterNode.GetParameter("cropIndex"),
                self._parameterNode.GetParameter("cropSize"),
                self._parameterNode.GetParameter("curveSeeds"),
                self._parameterNode.GetParameter("segmentationFactor")
            )
            if "Phase 1" in self.ui.phaseLabel.text:
                self.ui.phaseLabel.text = "Phase 2"

# Compute inverted output (if needed)
# if self.ui.invertedOutputSelector.currentNode():
#     # If additional output volume is selected
#     # then result with inverted threshold is written there
#     self.logic.process(
#                        self.ui.inputSelector.currentNode(),
#                        self.ui.invertedOutputSelector.currentNode(),
#                        self.ui.imageThresholdSliderWidget.value,
#                        not self.ui.invertOutputCheckBox.checked,
#                        showResult=False
#     )


#
# AortaGeomReconDisplayModuleLogic
#

class AortaGeomReconDisplayModuleLogic(ScriptedLoadableModuleLogic):  # noqa: F405,E501
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated.
        Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)  # noqa: F405

    def get_images(self, num_slices):
        # list of the number of slices in the z direction for each dicom image
        # these are manually entered as each dicom folder has far more .dcm files
        # than slices. If you do not manually enter these values,
        # the images will have many repeats of a singular CT

        list_dcm = os.listdir(path)
        list_dcm.sort()

        list_dcm = list_dcm[1:num_slices:]
        # change list to include path of .dcm files instead of just their names
        s = path + "/{0}"
        list_dcm = [s.format(dcm) for dcm in list_dcm]

        # convert the .dcm files to 3D images
        image = sitk.ReadImage(list_dcm)
        return image

    """Get cropped and normalized image and stored as self._segmenting_image
    """
    def prepared_segmenting_image(self, image, index, size):
        # crop the image
        crop_filter = sitk.ExtractImageFilter()
        crop_filter.SetIndex(index)
        crop_filter.SetSize(size)

        cropped_image = crop_filter.Execute(image)

        # change intensity range to go from 0-255   +++++++
        cropped_image_255 = sitk.Cast(sitk.RescaleIntensity(image),
                                      sitk.sitkUInt8)

        # ensure that the spacing in the image is correct
        cropped_image.SetOrigin(image.GetOrigin())
        cropped_image.SetSpacing(image.GetSpacing())
        cropped_image.SetDirection(image.GetDirection())

        # Contrast Enhancement
        # Histogram Equalization
        img_array = sitk.GetArrayFromImage(
            (sitk.Cast(sitk.RescaleIntensity(cropped_image), sitk.sitkUInt8))
        )

        # flatten image array and calculate histogram via binning
        histogram_array = np.bincount(img_array.flatten(), minlength=256)

        # normalize image
        num_pixels = np.sum(histogram_array)
        histogram_array = histogram_array/num_pixels

        # normalized cumulative histogram
        chistogram_array = np.cumsum(histogram_array)

        # create pixel mapping lookup table
        transform_map = np.floor(255 * chistogram_array).astype(np.uint8)

        # flatten image array into 1D list
        # so they can be used with the pixel mapping table
        img_list = list(img_array.flatten())

        # transform pixel values to equalize
        eq_img_list = [transform_map[p] for p in img_list]

        # reshape and write back into img_array
        eq_img_array = np.reshape(np.asarray(eq_img_list), img_array.shape)

        # save image
        eq_img = sitk.GetImageFromArray(eq_img_array)
        eq_img.CopyInformation(cropped_image)

        # Median Image Filter
        median = sitk.MedianImageFilter()
        median_img = sitk.Cast(median.Execute(eq_img), sitk.sitkUInt8)

        self._segmenting_image = median_img
        self._segmenting_image_255 = cropped_image_255

    def createDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """
        # if not parameterNode.GetParameter("Threshold"):
        #     parameterNode.SetParameter("Threshold", "100.0")
        # if not parameterNode.GetParameter("Invert"):
        #     parameterNode.SetParameter("Invert", "false")
        if not parameterNode.GetParameter("cropIndex"):
            parameterNode.SetParameter("cropIndex", "0,0,0")
        if not parameterNode.GetParameter("cropSize"):
            parameterNode.SetParameter("cropSize", "0,0,0")
        if not parameterNode.GetParameter("curveSeeds"):
            parameterNode.SetParameter("curveSeeds", "0,0,0")
        if not parameterNode.GetParameter("segmentationFactor"):
            parameterNode.SetParameter("segmentationFactor", "0.0")

    def setDefaultParameters(self, parameterNode):
        if parameterNode.GetParameter("cropIndex"):
            parameterNode.SetParameter("cropIndex", "0,0,0")
        if parameterNode.GetParameter("cropSize"):
            parameterNode.SetParameter("cropSize", "0,0,0")
        if parameterNode.GetParameter("curveSeeds"):
            parameterNode.SetParameter("curveSeeds", "0,0,0")
        if parameterNode.GetParameter("segmentationFactor"):
            parameterNode.SetParameter("segmentationFactor", "0.0")

    def process(self, cropSize, cropIndex, curveSeeds, segmentationFactor):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        """

        # cropSize = parameterNodes.GetParameter("cropSize")
        # cropIndex = parameterNodes.GetParameter("cropIndex")
        # curveSeeds = parameterNodes.GetParameter("curveSeeds")

        print(cropSize, cropIndex)

        logging.info('Processing completed')
        # if not inputVolume or not outputVolume:
        #     raise ValueError("Input or output volume is invalid")

        # import time
        # startTime = time.time()
        # logging.info('Processing started')

        # # Compute the thresholded output volume using
        # # the "Threshold Scalar Volume" CLI module
        # cliParams = {
        #     'InputVolume': inputVolume.GetID(),
        #     'OutputVolume': outputVolume.GetID(),
        #     'ThresholdValue': imageThreshold,
        #     'ThresholdType': 'Above' if invert else 'Below'
        # }
        # cliNode = slicer.cli.run(
        #     slicer.modules.thresholdscalarvolume,
        #     None,
        #     cliParams,
        #     wait_for_completion=True,
        #     update_display=showResult
        # )
        # # We don't need the CLI module node anymore,
        # # remove it to not clutter the scene with it
        # slicer.mrmlScene.RemoveNode(cliNode)

        # stopTime = time.time()
        # logging.info(
        #     f'Processing completed in {stopTime-startTime:.2f} seconds')


#
# AortaGeomReconDisplayModuleTest
#

class AortaGeomReconDisplayModuleTest(ScriptedLoadableModuleTest):  # noqa: F405,E501
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state
        - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_AortaGeomReconDisplayModule1()

    def test_AortaGeomReconDisplayModule1(self):
        """ Ideally you should have several levels of tests.
        At the lowest level tests should exercise
        the functionality of the logic
        with different inputs (both valid and invalid).
        At higher levels your tests should emulate the
        way the user would interact with your code
        and confirm that it still works the way you intended.
        One of the most important features of the tests is that
        it should alert other
        developers when their changes will have an impact on
        the behavior of your module.
        For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData
        registerSampleData()
        inputVolume = SampleData.downloadSample('AortaGeomReconDisplayModule1')
        self.delayDisplay('Loaded test data set')

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = AortaGeomReconDisplayModuleLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay('Test passed')
