from enum import Enum
import logging
import os
from datetime import datetime

import vtk

import slicer
from slicer import ScriptedLoadableModule
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleWidget
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleLogic
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleTest
from slicer.ScriptedLoadableModule import *  # noqa
from slicer.util import VTKObservationMixin

from AortaGeomReconDisplayModuleLib.AortaSegmenter \
    import AortaSegmenter

import sitkUtils
import numpy as np  # noqa: F401
import SimpleITK as sitk


class AGR_phase(Enum):
    warning = "Warning!"
    crop_aorta = "Phase 1 Crop Aorta"
    segment_desc_aorta = "Phase 2 Aorta Segmentation"

    def __repr__(self):
        return f'{self.value}'

#
# AortaGeomReconDisplayModule
#


class AortaGeomReconDisplayModule(ScriptedLoadableModule):  # noqa: F405
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)  # noqa: F405

        self.crosshairNode = None
        self.parent.title = "AortaGeomReconDisplayModule"

        # (folders where the module shows up in the module selector)
        self.parent.categories = ["Segmentation"]

        self.parent.dependencies = ["Markups"]

        self.parent.contributors = ["Jingyi Lin (McMaster University)"]
        self.parent.helpText = """
<h2 style="text-align:center;">Warnings!</h2>
Only qualified persons who have reviewed the user instructions should use the software. The user instructions is available on
<a href="https://joviel25.github.io/AortaGR-design-document/UserInstructions.html">Design Documentation - User Instructions section</a>.
<h2 style="text-align:center;">Tips</h2>
Please select the correct aorta seeds and adjust the hyperparameters in little adjustment.
<br>
Please input a Chest CT Scans, AortaGeomRecon is not responsible to detect a correct CT Scans.
<br><br>
See more about the segmentation algorithm in <a href="https://joviel25.github.io/AortaGR-design-document/index.html">Design documentation</a>.
"""  # noqa: E501

        self.parent.acknowledgementText = """
        The segmentation algorithm was partialy developed by Kailin Chu.
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
        size = len(slicer.util.getNodes("*cropped*", useLists=True))
        self.ui.applyButton.enabled = False if not size else True
        self.ui.revertButton.enabled = False
        self.ui.resetButton.enabled = True
        self.ui.skipButton.enabled = True
        self.ui.getVTKButton.enabled = True
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
        self.crosshairNode = slicer.util.getNode("Crosshair")
        self.crosshairNode.AddObserver(
            slicer.vtkMRMLCrosshairNode.CursorPositionModifiedEvent,
            self.onMouseMoved
        )

        self.addObserver(scene, scene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(scene, scene.EndCloseEvent, self.onSceneEndClose)

        # This will get Scene's all node objects

        # These connections ensure that
        # whenever user changes some settings on the GUI,
        # that is saved in the MRML scene
        # (in the selected parameter node).
        self.ui.ascAortaSeed.connect(
            "coordinatesChanged(double*)", self.updateParameterNodeFromGUI)
        self.ui.descAortaSeed.connect(
            "coordinatesChanged(double*)", self.updateParameterNodeFromGUI)
        self.ui.stopLimit.connect(
            "valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.kernelSize.connect(
            "valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.thresholdCoefficient.connect(
            "valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.rmsError.connect(
            "valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.noIteration.connect(
            "valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.curvatureScaling.connect(
            "valueChanged(double)", self.updateParameterNodeFromGUI)
        self.ui.propagationScaling.connect(
            "valueChanged(double)", self.updateParameterNodeFromGUI)

        # Buttons
        self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
        self.ui.revertButton.connect('clicked(bool)', self.onRevertButton)
        self.ui.resetButton.connect('clicked(bool)', self.onResetButton)
        self.ui.skipButton.connect('clicked(bool)', self.onSkipButton)
        self.ui.getVTKButton.connect('clicked(bool)', self.onGetVTKButton)
        self.ui.warningConfirmButton.connect(
            'clicked(bool)', self.onConfirmWarningButton)

        sliceDisplayNodes = slicer.util.getNodesByClass(
            "vtkMRMLSliceDisplayNode")
        for sliceDisplayNode in sliceDisplayNodes:
            sliceDisplayNode.SetIntersectingSlicesVisibility(1)

        sliceNodes = slicer.util.getNodesByClass('vtkMRMLSliceNode')
        for sliceNode in sliceNodes:
            sliceNode.Modified()

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
        slicer.util.setDataProbeVisible(False)
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

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show
        the current state of the parameter node.
        """
        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        self.showWarning()

        # Make sure GUI changes do not call updateParameterNodeFromGUI
        # (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        self.ui.ascAortaSeed.coordinates = self._parameterNode.GetParameter(
            "ascAortaSeed")
        self.ui.descAortaSeed.coordinates = self._parameterNode.GetParameter(
            "descAortaSeed")
        self.ui.thresholdCoefficient.value = float(
            self._parameterNode.GetParameter("threshold_coef"))
        self.ui.kernelSize.value = float(self._parameterNode.GetParameter(
            "kernel_size"))

        self.ui.rmsError.value = float(self._parameterNode.GetParameter(
            "rms_error"))
        self.ui.noIteration.value = float(self._parameterNode.GetParameter(
            "no_ite"))
        self.ui.curvatureScaling.value = float(
            self._parameterNode.GetParameter("curv_scaling"))
        self.ui.propagationScaling.value = float(
            self._parameterNode.GetParameter("prop_scaling"))
        temp = self._parameterNode.GetParameter("stop_limit")
        if not temp:
            temp = 1
        self.ui.stopLimit.value = float(temp)

        self.ui.applyButton.enabled = not self.logic.anyEmptySeed(
            self.ui,
            self._parameterNode.GetParameter("phase")
        )

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
            "ascAortaSeed", self.ui.ascAortaSeed.coordinates)
        self._parameterNode.SetParameter(
            "descAortaSeed", self.ui.descAortaSeed.coordinates)
        self._parameterNode.SetParameter(
            "stop_limit", str(self.ui.stopLimit.value))
        self._parameterNode.SetParameter(
            "kernel_size", str(self.ui.kernelSize.value))
        self._parameterNode.SetParameter(
            "threshold_coef", str(self.ui.thresholdCoefficient.value))
        self._parameterNode.SetParameter(
            "rms_error", str(self.ui.rmsError.value))
        self._parameterNode.SetParameter(
            "no_ite", str(self.ui.noIteration.value))
        self._parameterNode.SetParameter(
            "curv_scaling", str(self.ui.curvatureScaling.value))
        self._parameterNode.SetParameter(
            "prop_scaling", str(self.ui.propagationScaling.value))
        self.ui.applyButton.enabled = not self.logic.anyEmptySeed(
            self.ui,
            self._parameterNode.GetParameter("phase")
        )
        crop = len(slicer.util.getNodes("*cropped*", useLists=True)) == 1
        des = len(slicer.util.getNodes("*Seg*", useLists=True)) > 0
        self.ui.getVTKButton.enabled = crop or des
        self._parameterNode.EndModify(wasModified)

    def showPhaseCropAorta(self):
        """
        This method is called when the user makes change the current phase to phase 1 crop aorta.
        This method includes all the ui elements that need to hide or to show.
        """ # noqa
        self._parameterNode.SetParameter("phase", "1")
        self.ui.applyButton.show()
        self.ui.revertButton.show()
        self.ui.resetButton.show()
        self.ui.skipButton.show()
        self.ui.getVTKButton.show()
        self.ui.revertButton.enabled = False
        self.ui.phaseLabel.text = AGR_phase.crop_aorta.value
        self.ui.SubjectHierarchyTreeView.show()
        self.ui.warningConfirmButton.hide()
        self.ui.warningEdit.hide()
        self.ui.ascAortaSeed.hide()
        self.ui.descAortaSeed.hide()
        self.ui.thresholdCoefficient.hide()
        self.ui.stopLimit.hide()
        self.ui.ascAortaSeedLabel.hide()
        self.ui.descAortaSeedLabel.hide()
        self.ui.stopLimitLabel.hide()
        self.ui.rmsLabel.hide()
        self.ui.noIteLabel.hide()
        self.ui.curScalingLabel.hide()
        self.ui.propScalingLabel.hide()
        self.ui.rmsError.hide()
        self.ui.noIteration.hide()
        self.ui.curvatureScaling.hide()
        self.ui.propagationScaling.hide()
        self.ui.thresholdCoefLabel.hide()
        self.ui.debugBox.hide()
        self.ui.ascSeedLocker.hide()
        self.ui.desSeedLocker.hide()
        self.ui.segmentationCollapsibleBox.hide()
        self.ui.inputsCollapsibleButton.hide()
        self.ui.kernelSizeLabel.hide()
        self.ui.kernelSize.hide()
        self.ui.skipButton.enabled = True
        self.ui.outputPath.show()

    def showWarning(self):
        """
        This method is called when the user makes change the current phase to phase 2 aorta segmentation.
        This method includes calling of all UI elements that need to show or to hide.
        """ # noqa
        self.ui.phaseLabel.text = AGR_phase.warning.value
        self.ui.revertButton.enabled = False
        self.ui.applyButton.hide()
        self.ui.revertButton.hide()
        self.ui.resetButton.hide()
        self.ui.skipButton.hide()
        self.ui.getVTKButton.hide()
        self.ui.SubjectHierarchyTreeView.hide()
        self.ui.ascAortaSeed.hide()
        self.ui.ascSeedLocker.hide()
        self.ui.desSeedLocker.hide()
        self.ui.ascAortaSeedLabel.hide()
        self.ui.descAortaSeed.hide()
        self.ui.descAortaSeedLabel.hide()
        self.ui.stopLimit.hide()
        self.ui.stopLimitLabel.hide()
        self.ui.rmsLabel.hide()
        self.ui.noIteLabel.hide()
        self.ui.curScalingLabel.hide()
        self.ui.propScalingLabel.hide()
        self.ui.rmsError.hide()
        self.ui.noIteration.hide()
        self.ui.curvatureScaling.hide()
        self.ui.propagationScaling.hide()
        self.ui.thresholdCoefficient.hide()
        self.ui.thresholdCoefLabel.hide()
        self.ui.debugBox.hide()
        self.ui.segmentationCollapsibleBox.hide()
        self.ui.inputsCollapsibleButton.hide()
        self.ui.kernelSizeLabel.hide()
        self.ui.kernelSize.hide()
        self.ui.outputPath.hide()

    def showPhaseAS(self):
        """
        This method is called when the user makes change the current phase to phase 2 aorta segmentation.
        This method includes calling of all UI elements that need to show or to hide.
        """ # noqa
        self._parameterNode.SetParameter("phase", "2")
        self.ui.phaseLabel.text = AGR_phase.segment_desc_aorta.value
        self.ui.revertButton.enabled = True
        self.ui.warningConfirmButton.hide()
        self.ui.applyButton.show()
        self.ui.revertButton.show()
        self.ui.resetButton.show()
        self.ui.skipButton.show()
        self.ui.getVTKButton.show()
        self.ui.warningEdit.hide()
        self.ui.ascAortaSeed.show()
        self.ui.ascSeedLocker.show()
        self.ui.desSeedLocker.show()
        self.ui.ascAortaSeedLabel.show()
        self.ui.descAortaSeed.show()
        self.ui.descAortaSeedLabel.show()
        self.ui.stopLimit.show()
        self.ui.stopLimitLabel.show()
        self.ui.rmsLabel.show()
        self.ui.noIteLabel.show()
        self.ui.curScalingLabel.show()
        self.ui.propScalingLabel.show()
        self.ui.rmsError.show()
        self.ui.noIteration.show()
        self.ui.curvatureScaling.show()
        self.ui.propagationScaling.show()
        self.ui.thresholdCoefficient.show()
        self.ui.thresholdCoefLabel.show()
        self.ui.debugBox.show()
        self.ui.segmentationCollapsibleBox.show()
        self.ui.inputsCollapsibleButton.show()
        self.ui.kernelSizeLabel.show()
        self.ui.kernelSize.show()
        self.ui.skipButton.enabled = False
        self.ui.outputPath.show()

    def onConfirmWarningButton(self):
        phase = self._parameterNode.GetParameter("phase")
        if not phase or phase == '1':
            print(phase)
            self.showPhaseCropAorta()
        elif phase == '2':
            self.showPhaseAS()

    def onGetVTKButton(self):
        """
        This method is called when the user click on Get VTK button.
        Depends on what state the module is in, the module output a vtk file under the root folder of Slicer application.

        """ # noqa
        sceneObj = slicer.mrmlScene
        if self._parameterNode.GetParameter("phase") == "1":
            size = len(slicer.util.getNodes("*cropped*", useLists=True))
            if size == 1:
                volume = sceneObj.GetFirstNode("cropped", None, None, False)
                self.logic.transform_image(volume)
                self.logic.saveVtk("crop_volume.vtk", None, 1)
        elif self._parameterNode.GetParameter("phase") == "2":
            size = len(slicer.util.getNodes("*Seg*", useLists=True))
            if size == 1:
                volume = sceneObj.GetFirstNode("Seg", None, None, False)
                self.logic.saveVtk(
                    "{}.vtk".format(volume.GetName()),
                    volume,
                    2
                )

    def onRevertButton(self):
        """
        Revert to the previous phase, stay unchanged if first state is reached.
        """
        errorMessage = "Failed to clear inputs"
        with slicer.util.tryWithErrorDisplay(errorMessage, waitCursor=True):
            phase = self._parameterNode.GetParameter("phase")
            if phase == '2':
                self.showPhaseCropAorta()
                self._parameterNode.SetParameter("phase", "1")

    def onResetButton(self):
        """
        Reset all stored variables.
        """
        errorMessage = "Failed to clear inputs"
        with slicer.util.tryWithErrorDisplay(errorMessage, waitCursor=True):
            self.logic.resetDefaultParameters(self.logic.getParameterNode())
            self.showPhaseCropAorta()

    def onSkipButton(self):
        """
        Go to next phase.
        """
        errorMessage = "Failed to skip this phase"
        with slicer.util.tryWithErrorDisplay(errorMessage, waitCursor=True):
            if self._parameterNode.GetParameter("phase") == "1":
                # Update phase
                self.showPhaseAS()
                self.ui.phaseLabel.text = AGR_phase.segment_desc_aorta.value

    def onApplyButton(self):
        """
        Go to next phase if on phase 1 crop aorta or perform segmentation if on phase 2 aorta segmentation.
        """ # noqa
        errorMessage = "Failed to compute results."
        sceneObj = slicer.mrmlScene
        stop_limit = self._parameterNode.GetParameter(
            "stop_limit")
        threshold_coef = self._parameterNode.GetParameter(
            "threshold_coef")
        rms_error = self._parameterNode.GetParameter("rms_error")
        no_ite = self._parameterNode.GetParameter("no_ite")
        curv_scaling = self._parameterNode.GetParameter(
            "curv_scaling")
        prop_scaling = self._parameterNode.GetParameter(
            "prop_scaling")
        kernel_size = self._parameterNode.GetParameter(
            "kernel_size")
        with slicer.util.tryWithErrorDisplay(errorMessage, waitCursor=True):
            # Compute output
            if self._parameterNode.GetParameter("phase") == "1":
                size = len(slicer.util.getNodes("*cropped*", useLists=True))
                if not size:
                    logging.info("Cannot find cropped volume")
                else:
                    self.showPhaseAS()
            else:
                descAortaSeed = self._parameterNode.GetParameter(
                    "descAortaSeed")
                ascAortaSeed = self._parameterNode.GetParameter(
                    "ascAortaSeed")
                volume = sceneObj.GetFirstNode("cropped", None, None, False)
                self.logic.transform_image(volume)
                image = self.logic.process(
                    descAortaSeed, ascAortaSeed, stop_limit,
                    threshold_coef, kernel_size, rms_error, no_ite,
                    curv_scaling, prop_scaling, self.ui.debugBox.checked
                )
                sitkUtils.PushVolumeToSlicer(
                    image,
                    name="Seg_th{}_k{}_c{}_p{}".format(
                        threshold_coef,
                        kernel_size,
                        curv_scaling,
                        prop_scaling),
                    className="vtkMRMLScalarVolumeNode"
                )

    def onMouseMoved(self, observer, eventid):
        """
        This method automatically updates the descending aorta seed
        or the ascending aorta seed when the cursor is moving,
        if the seeds are in unlocked state.
        """
        errorMsg = "Failed to load intersection data"
        volume = slicer.mrmlScene.GetFirstNode("cropped", None, None, False)
        if volume:
            axialNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
            ortho1Node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
            ortho2Node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
            point_Ijk = self.logic.getPlaneIntersectionPoint(
                volume, axialNode, ortho1Node, ortho2Node)
            ijk = ",".join([str(int(i)) for i in point_Ijk])
            with slicer.util.tryWithErrorDisplay(errorMsg, waitCursor=True):
                if not self.ui.desSeedLocker.checked:
                    self._parameterNode.SetParameter("descAortaSeed", ijk)
                if not self.ui.ascSeedLocker.checked:
                    self._parameterNode.SetParameter("ascAortaSeed", ijk)
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
        self._cropped_image = None
        ScriptedLoadableModuleLogic.__init__(self)  # noqa: F405

    def saveVtk(self, name, volume, phase):
        """
        Save vtk file of a volume.
        """
        writer = sitk.ImageFileWriter()
        writer.SetImageIO("VTKImageIO")
        writer.SetFileName(name)
        if phase == 1:
            image = sitkUtils.PullVolumeFromSlicer(self._cropped_image)
        else:
            image = sitkUtils.PullVolumeFromSlicer(volume)
        writer.Execute(image)

    def getPlaneIntersectionPoint(self, vN, aN, oN1, oN2):
        """
        Compute the center of rotation
        (common intersection point of the three planes)
        http://mathworld.wolfram.com/Plane-PlaneIntersection.html
        """
        axialSliceToRas = aN.GetSliceToRAS()
        n1 = [
            axialSliceToRas.GetElement(0, 2),
            axialSliceToRas.GetElement(1, 2),
            axialSliceToRas.GetElement(2, 2)
        ]
        x1 = [
            axialSliceToRas.GetElement(0, 3),
            axialSliceToRas.GetElement(1, 3),
            axialSliceToRas.GetElement(2, 3)
        ]
        ortho1SliceToRas = oN1.GetSliceToRAS()
        n2 = [
            ortho1SliceToRas.GetElement(0, 2),
            ortho1SliceToRas.GetElement(1, 2),
            ortho1SliceToRas.GetElement(2, 2)
        ]
        x2 = [
            ortho1SliceToRas.GetElement(0, 3),
            ortho1SliceToRas.GetElement(1, 3),
            ortho1SliceToRas.GetElement(2, 3)
        ]

        ortho2SliceToRas = oN2.GetSliceToRAS()
        n3 = [
            ortho2SliceToRas.GetElement(0, 2),
            ortho2SliceToRas.GetElement(1, 2),
            ortho2SliceToRas.GetElement(2, 2)
        ]
        x3 = [
            ortho2SliceToRas.GetElement(0, 3),
            ortho2SliceToRas.GetElement(1, 3),
            ortho2SliceToRas.GetElement(2, 3)
        ]

        # Computed intersection point of all planes
        x = [0, 0, 0]
        n2_xp_n3 = [0, 0, 0]
        x1_dp_n1 = vtk.vtkMath.Dot(x1, n1)
        vtk.vtkMath.Cross(n2, n3, n2_xp_n3)
        vtk.vtkMath.MultiplyScalar(n2_xp_n3, x1_dp_n1)
        vtk.vtkMath.Add(x, n2_xp_n3, x)
        n3_xp_n1 = [0, 0, 0]
        x2_dp_n2 = vtk.vtkMath.Dot(x2, n2)
        vtk.vtkMath.Cross(n3, n1, n3_xp_n1)
        vtk.vtkMath.MultiplyScalar(n3_xp_n1, x2_dp_n2)
        vtk.vtkMath.Add(x, n3_xp_n1, x)
        n1_xp_n2 = [0, 0, 0]
        x3_dp_n3 = vtk.vtkMath.Dot(x3, n3)
        vtk.vtkMath.Cross(n1, n2, n1_xp_n2)
        vtk.vtkMath.MultiplyScalar(n1_xp_n2, x3_dp_n3)
        vtk.vtkMath.Add(x, n1_xp_n2, x)
        normalMatrix = vtk.vtkMatrix3x3()
        normalMatrix.SetElement(0, 0, n1[0])
        normalMatrix.SetElement(1, 0, n1[1])
        normalMatrix.SetElement(2, 0, n1[2])
        normalMatrix.SetElement(0, 1, n2[0])
        normalMatrix.SetElement(1, 1, n2[1])
        normalMatrix.SetElement(2, 1, n2[2])
        normalMatrix.SetElement(0, 2, n3[0])
        normalMatrix.SetElement(1, 2, n3[1])
        normalMatrix.SetElement(2, 2, n3[2])
        normalMatrixDeterminant = normalMatrix.Determinant()
        if abs(normalMatrixDeterminant) > 0.01:
            # there is an intersection point
            vtk.vtkMath.MultiplyScalar(x, 1 / normalMatrixDeterminant)
        else:
            # no intersection point can be determined,
            # use just the position of the axial slice
            x = x1
        transformRasToVolumeRas = vtk.vtkGeneralTransform()
        volumeRasToIjk = vtk.vtkMatrix4x4()
        vN.GetRASToIJKMatrix(volumeRasToIjk)
        point_Ijk = [0, 0, 0, 1]
        point_VolumeRas = transformRasToVolumeRas.TransformPoint(x)
        volumeRasToIjk.MultiplyPoint(
            np.append(point_VolumeRas, 1.0), point_Ijk)
        point_Ijk = [int(round(c)) for c in point_Ijk[0:3]]
        return point_Ijk

    def anyEmptySeed(self, ui, phase):
        """Verify if the coordinates are not default value

        Returns:
            Boolean: Return True if desc aorta seed and asc aorta seed
            are not empty.
        """ # noqa
        cond1 = cond2 = False
        if phase == '2':
            cond1 = (ui.descAortaSeed.coordinates == "0,0,0")
            cond2 = (ui.ascAortaSeed.coordinates == "0,0,0")
        return cond1 or cond2

    def transform_image(self, cropped_volume):
        """
        Histogram Equalization for Digital Image Enhancement.
        https://levelup.gitconnected.com/introduction-to-histogram-equalization-for-digital-image-enhancement-420696db9e43
        """ # noqa
        cropped_image = sitkUtils.PullVolumeFromSlicer(cropped_volume)
        img_array = sitk.GetArrayFromImage(
            (sitk.Cast(sitk.RescaleIntensity(cropped_image), sitk.sitkUInt8)))
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
        self._cropped_image = median_img

    def createDefaultParameters(self, parameterNode):
        """Initialize parameter node with default settings.
        """
        if not parameterNode.GetParameter("ascAortaSeed"):
            parameterNode.SetParameter("ascAortaSeed", "0,0,0")
        if not parameterNode.GetParameter("stop_limit"):
            parameterNode.SetParameter("stop_limit", "10")
        if not parameterNode.GetParameter("threshold_coef"):
            parameterNode.SetParameter("threshold_coef", "3.0")
        if not parameterNode.GetParameter("phase"):
            parameterNode.SetParameter("phase", "1")
        if not parameterNode.GetParameter("descAortaSeed"):
            parameterNode.SetParameter("descAortaSeed", "0,0,0")
        if not parameterNode.GetParameter("rms_error"):
            parameterNode.SetParameter("rms_error", "0.02")
        if not parameterNode.GetParameter("no_ite"):
            parameterNode.SetParameter("no_ite", "600")
        if not parameterNode.GetParameter("curv_scaling"):
            parameterNode.SetParameter("curv_scaling", "2.0")
        if not parameterNode.GetParameter("prop_scaling"):
            parameterNode.SetParameter("prop_scaling", "0.5")
        if not parameterNode.GetParameter("kernel_size"):
            parameterNode.SetParameter("kernel_size", "7")

    def setDefaultParameters(self, parameterNode):
        """Set parameter node with default settings.
        """
        if parameterNode.GetParameter("ascAortaSeed"):
            parameterNode.SetParameter("ascAortaSeed", "0,0,0")
        if parameterNode.GetParameter("stop_limit"):
            parameterNode.SetParameter("stop_limit", "10")
        if parameterNode.GetParameter("threshold_coef"):
            parameterNode.SetParameter("threshold_coef", "3.0")
        if parameterNode.GetParameter("descAortaSeed"):
            parameterNode.SetParameter("descAortaSeed", "0,0,0")
        if parameterNode.GetParameter("rms_error"):
            parameterNode.SetParameter("rms_error", "0.02")
        if parameterNode.GetParameter("no_ite"):
            parameterNode.SetParameter("no_ite", "600")
        if parameterNode.GetParameter("curv_scaling"):
            parameterNode.SetParameter("curv_scaling", "2.0")
        if parameterNode.GetParameter("prop_scaling"):
            parameterNode.SetParameter("prop_scaling", "0.5")
        if parameterNode.GetParameter("kernel_size"):
            parameterNode.SetParameter("kernel_size", "7.0")

    def resetDefaultParameters(self, parameterNode):
        """Reset parameter node with default settings.
        """
        self.setDefaultParameters(parameterNode)
        if parameterNode.GetParameter("phase"):
            parameterNode.SetParameter("phase", "1")

    def process(self, des_seed, asc_seed, stop_limit, threshold_coef,
                kernel_size, rms_error, no_ite, curvature_scaling,
                propagation_scaling, debug):
        """Convert the parameters to the correct format and
        call begin_segmentation from AortaSegmenter.

        Returns:
            SITK::image: The processing image, or the segmentation label image
        """
        des_seed = des_seed.split(",")
        asc_seed = asc_seed.split(",")
        asc_seed = [int(i) for i in asc_seed]
        des_seed = [int(i) for i in des_seed]
        now = datetime.now()
        if not self._cropped_image:
            volume = slicer.mrmlScene.GetFirstNode(
                    "cropped", None, None, False)
            self.transform_image(volume)
        logging.info(f"{now} processing")
        segmenter = AortaSegmenter(
            cropped_image=self._cropped_image, des_seed=des_seed,
            asc_seed=asc_seed, stop_limit=float(stop_limit),
            threshold_coef=float(threshold_coef),
            kernel_size=int(float(kernel_size)),
            rms_error=float(rms_error), no_ite=int(no_ite.split(".")[0]),
            curvature_scaling=float(curvature_scaling),
            propagation_scaling=float(propagation_scaling), debug=debug
        )
        segmenter.begin_segmentation()
        now = datetime.now()
        logging.info(f"{now} Finished processing")
        return segmenter.processing_image

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
