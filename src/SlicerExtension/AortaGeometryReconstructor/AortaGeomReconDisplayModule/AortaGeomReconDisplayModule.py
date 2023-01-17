import logging
import os
from datetime import datetime

import vtk

import slicer
from slicer.ScriptedLoadableModule import *  # noqa: F403
from slicer.util import VTKObservationMixin

from AortaGeomReconDisplayModuleLib.AortaDescendingAxialSegmenter \
    import AortaDescendingAxialSegmenter

from AortaGeomReconDisplayModuleLib.AortaAscendingAxialSegmenter \
    import AortaAscendingAxialSegmenter

from AortaGeomReconDisplayModuleLib.AortaSagitalSegmenter \
    import AortaSagitalSegmenter


import sitkUtils
import numpy as np  # noqa: F401
import SimpleITK as sitk


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
        self.ui.applyButton.enabled = False
        self.ui.clearButton.enabled = True
        self.ui.resetButton.enabled = True
        self.ui.skipButton.enabled = True

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

        self.ui.ascAortaSeeds.connect(
            "coordinatesChanged(double*)", self.updateParameterNodeFromGUI)

        self.ui.descAortaSeeds.connect(
            "coordinatesChanged(double*)", self.updateParameterNodeFromGUI)

        self.ui.segmentationFactor.connect(
            "valueChanged(double)", self.updateParameterNodeFromGUI)

        self.ui.numOfSkippingSlice.connect(
            "valueChanged(double)", self.updateParameterNodeFromGUI)

        # Buttons
        self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
        self.ui.clearButton.connect('clicked(bool)', self.onClearButton)
        self.ui.resetButton.connect('clicked(bool)', self.onResetButton)
        self.ui.skipButton.connect('clicked(bool)', self.onSkipButton)

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

        # Make sure GUI changes do not call updateParameterNodeFromGUI
        # (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        self.ui.ascAortaSeeds.coordinates = self._parameterNode.GetParameter(
            "ascAortaSeeds")

        self.ui.descAortaSeeds.coordinates = self._parameterNode.GetParameter(
            "descAortaSeeds")

        self.ui.segmentationFactor.value = float(
            self._parameterNode.GetParameter("segmentation_factor"))

        self.ui.numOfSkippingSlice.value = int(
            float(self._parameterNode.GetParameter("numOfSkippingSlice")))

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
            "ascAortaSeeds", self.ui.ascAortaSeeds.coordinates)

        self._parameterNode.SetParameter(
            "descAortaSeeds", self.ui.descAortaSeeds.coordinates)

        self._parameterNode.SetParameter(
            "segmentation_factor", str(self.ui.segmentationFactor.value))

        self._parameterNode.SetParameter(
            "numOfSkippingSlice", str(self.ui.numOfSkippingSlice.value))

        self.ui.applyButton.enabled = not self.logic.anyEmptySeed(
            self.ui,
            self._parameterNode.GetParameter("phase")
        )

        self._parameterNode.EndModify(wasModified)

    def onClearButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        errorMessage = "Failed to clear inputs"
        with slicer.util.tryWithErrorDisplay(errorMessage, waitCursor=True):
            self.logic.setDefaultParameters(self.logic.getParameterNode())

    def onResetButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        errorMessage = "Failed to clear inputs"
        with slicer.util.tryWithErrorDisplay(errorMessage, waitCursor=True):
            self.logic.resetDefaultParameters(self.logic.getParameterNode())
            self.ui.phaseLabel.text = "Phase 1 Crop Aorta"
            self.ui.skipButton.enabled = True

    def onSkipButton(self):
        errorMessage = "Failed to skip this phase"
        with slicer.util.tryWithErrorDisplay(errorMessage, waitCursor=True):
            if self._parameterNode.GetParameter("phase") == "1":
                # Update phase
                self._parameterNode.SetParameter("phase", "2")
                self.ui.phaseLabel.text = "Phase 2"

            elif self._parameterNode.GetParameter("phase") == "2":
                self._parameterNode.SetParameter("phase", "3")
                self.ui.phaseLabel.text = "Phase 3"
                self.ui.skipButton.enabled = False

    def onApplyButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        errorMessage = "Failed to compute results."
        sceneObj = slicer.mrmlScene
        with slicer.util.tryWithErrorDisplay(errorMessage, waitCursor=True):
            # Compute output
            if self._parameterNode.GetParameter("phase") == "1":
                size = len(slicer.util.getNodes("*cropped*", useLists=True))
                if not size:
                    logging.info("Cannot found cropped volume")
                elif size == 1:
                    self._parameterNode.SetParameter("phase", "2")
                    self.ui.phaseLabel.text = "Phase 2"
                else:
                    logging.info("Found multiple cropped volumes")

            elif self._parameterNode.GetParameter("phase") == "2":
                descAortaSeeds = self._parameterNode.GetParameter(
                    "descAortaSeeds")

                segmentation_factor = self._parameterNode.GetParameter(
                    "segmentation_factor")

                num_slice_skipping = self._parameterNode.GetParameter(
                    "numOfSkippingSlice")

                volume = sceneObj.GetFirstNode("cropped", None, None, False)

                self.logic.transform_image(volume)

                image = self.logic.processDescendingAorta(
                    descAortaSeeds,
                    segmentation_factor,
                    num_slice_skipping
                )

                sitkUtils.PushVolumeToSlicer(
                    image,
                    name="Segmented Descending Aorta Volume",
                    className="vtkMRMLScalarVolumeNode"
                )
                self._parameterNode.SetParameter("phase", "3")
                self.ui.phaseLabel.text = "Phase 3"
                self.ui.skipButton.enabled = False

            elif self._parameterNode.GetParameter("phase") == "3":
                ascAortaSeeds = self._parameterNode.GetParameter(
                    "ascAortaSeeds")

                segmentation_factor = self._parameterNode.GetParameter(
                    "segmentation_factor")

                num_slice_skipping = self._parameterNode.GetParameter(
                    "numOfSkippingSlice")

                volume = sceneObj.GetFirstNode("cropped", None, None, False)

                image = self.logic.processAscendingAorta(
                    ascAortaSeeds,
                    segmentation_factor,
                    num_slice_skipping
                )

                sitkUtils.PushVolumeToSlicer(
                    image,
                    name="Segmented Ascending Aorta Volume",
                    className="vtkMRMLScalarVolumeNode"
                )
                self._parameterNode.SetParameter("phase", "3")
                self.ui.phaseLabel.text = "Phase 3"
                self.ui.skipButton.enabled = False

    def onMouseMoved(self, observer, eventid):
        # ras = [0, 0, 0]
        volume = slicer.mrmlScene.GetFirstNode("cropped", None, None, False)
        if volume:
            axialNode = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
            ortho1Node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
            ortho2Node = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
            point_Ijk = self.logic.getPlaneIntersectionPoint(
                volume, axialNode, ortho1Node, ortho2Node)
            # infoWidget = slicer.modules.DataProbeInstance.infoWidget
            # self.crosshairNode.GetCursorPositionRAS(ras)
            ijk = ",".join([str(int(i)) for i in point_Ijk])
            if self._parameterNode.GetParameter("phase") == "2":
                self._parameterNode.SetParameter(
                    "descAortaSeeds", ijk)
            elif self._parameterNode.GetParameter("phase") == "3":
                self._parameterNode.SetParameter(
                    "ascAortaSeeds", ijk)
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
        self._processing_image = None
        ScriptedLoadableModuleLogic.__init__(self)  # noqa: F405

    def getPlaneIntersectionPoint(
        self,
        volumeNode,
        axialNode,
        ortho1Node,
        ortho2Node
    ):
        # Compute the center of rotation
        # (common intersection point of the three planes)
        # http://mathworld.wolfram.com/Plane-PlaneIntersection.html

        axialSliceToRas = axialNode.GetSliceToRAS()
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

        ortho1SliceToRas = ortho1Node.GetSliceToRAS()
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

        ortho2SliceToRas = ortho2Node.GetSliceToRAS()
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
        volumeNode.GetRASToIJKMatrix(volumeRasToIjk)

        point_Ijk = [0, 0, 0, 1]
        # >>> x
        # [-30.069400063396387, -55.78618109487266, -44.595018435746994]
        point_VolumeRas = transformRasToVolumeRas.TransformPoint(x)
        volumeRasToIjk.MultiplyPoint(
            np.append(point_VolumeRas, 1.0), point_Ijk)

        point_Ijk = [int(round(c)) for c in point_Ijk[0:3]]

        return point_Ijk

    def anyEmptySeed(self, ui, phase):
        if phase == "2":
            return (ui.descAortaSeeds.coordinates == "0,0,0")
        elif phase == "3":
            return (ui.ascAortaSeeds.coordinates == "0,0,0")
        return False

    """Get cropped and normalized image and stored as self._segmenting_image
    """
    def prepareSegmentingImage(self, image, index, size):
        # crop the image
        crop_filter = sitk.ExtractImageFilter()
        crop_filter.SetIndex(index)
        crop_filter.SetSize(size)

        cropped_image = crop_filter.Execute(image)

        # ensure that the spacing in the image is correct
        cropped_image.SetOrigin(image.GetOrigin())
        cropped_image.SetSpacing(image.GetSpacing())
        cropped_image.SetDirection(image.GetDirection())

        selectCastFilter = sitk.VectorIndexSelectionCastImageFilter()
        selectCastFilter.SetIndex(0)
        selectCastFilter.SetOutputPixelType(sitk.sitkUInt32)
        cropped_image = selectCastFilter.Execute(cropped_image)
        return cropped_image

    def transform_image(self, cropped_volume):
        cropped_image = sitkUtils.PullVolumeFromSlicer(cropped_volume)

        logging.info("Transformed to 32 bits unsigned")
        img_array = sitk.GetArrayFromImage(
            (sitk.Cast(sitk.RescaleIntensity(cropped_image), sitk.sitkUInt8)))
        logging.info("Transformed to 8 bits unsigned")

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
        """
        Initialize parameter node with default settings.
        """
        if not parameterNode.GetParameter("cropIndex"):
            parameterNode.SetParameter("cropIndex", "0,0,0")
        if not parameterNode.GetParameter("cropSize"):
            parameterNode.SetParameter("cropSize", "0,0,0")
        if not parameterNode.GetParameter("ascAortaSeeds"):
            parameterNode.SetParameter("ascAortaSeeds", "0,0,0")
        if not parameterNode.GetParameter("segmentation_factor"):
            parameterNode.SetParameter("segmentation_factor", "0.0")
        parameterNode.SetParameter("phase", "1")
        if not parameterNode.GetParameter("descAortaSeeds"):
            parameterNode.SetParameter("descAortaSeeds", "0,0,0")
        if not parameterNode.GetParameter("numOfSkippingSlice"):
            parameterNode.SetParameter("numOfSkippingSlice", "0")

    def setDefaultParameters(self, parameterNode):
        if parameterNode.GetParameter("cropIndex"):
            parameterNode.SetParameter("cropIndex", "0,0,0")
        if parameterNode.GetParameter("cropSize"):
            parameterNode.SetParameter("cropSize", "0,0,0")
        if parameterNode.GetParameter("ascAortaSeeds"):
            parameterNode.SetParameter("ascAortaSeeds", "0,0,0")
        if parameterNode.GetParameter("segmentation_factor"):
            parameterNode.SetParameter("segmentation_factor", "0.0")
        if parameterNode.GetParameter("descAortaSeeds"):
            parameterNode.SetParameter("descAortaSeeds", "0,0,0")
        if parameterNode.GetParameter("numOfSkippingSlice"):
            parameterNode.SetParameter("numOfSkippingSlice", "0")

    def resetDefaultParameters(self, parameterNode):
        self.setDefaultParameters(parameterNode)
        if parameterNode.GetParameter("phase"):
            parameterNode.SetParameter("phase", "1")

    def processCropImage(self, cropIndex, cropSize, volume):
        indexStr = cropIndex.split(",")
        sizeStr = cropSize.split(",")
        index = [int(i) for i in indexStr]
        size = [int(i) for i in sizeStr]
        now = datetime.now()
        logging.info(f"{now} Pulling Volume from Slicer")
        sitkImage = sitkUtils.PullVolumeFromSlicer(volume)
        # logging.info(sitkImage)
        outputImage = self.prepareSegmentingImage(sitkImage, index, size)
        now = datetime.now()
        logging.info(f"{now} Finished cropping image")
        # logging.info(outputImage)
        return outputImage

    def processDescendingAorta(
                self,
                descAortaSeeds,
                segmentation_factor,
                num_slice_skipping,
            ):
        descAortaSeedsStr = descAortaSeeds.split(",")
        dASnumber = [int(i) for i in descAortaSeedsStr]
        now = datetime.now()
        logging.info(f"{now} processing Descending Aorta Segmentation")
        print("starting_slice", dASnumber[2])
        print("aorta_centre", dASnumber[:2])

        desc_axial_segmenter = AortaDescendingAxialSegmenter(
            starting_slice=dASnumber[2],
            aorta_centre=dASnumber[:2],
            num_slice_skipping=int(float(num_slice_skipping)),
            segmentation_factor=float(segmentation_factor),
            cropped_image=self._cropped_image
        )
        desc_axial_segmenter.begin_segmentation()
        logging.info(
            f"{now} Finished processing Descending Aorta Segmentation")
        self._processing_image = desc_axial_segmenter.processing_image
        return self._processing_image

    def processAscendingAorta(
                self,
                ascAortaSeeds,
                segmentation_factor,
                num_slice_skipping,
            ):
        ascAortaSeedsStr = ascAortaSeeds.split(",")
        aASnumber = [int(i) for i in ascAortaSeedsStr]
        now = datetime.now()
        logging.info(f"{now} processing Ascending Aorta Segmentation")
        print("starting_slice", aASnumber[2])
        print("aorta_centre", aASnumber[:2])

        if not self._cropped_image:
            volume = slicer.mrmlScene.GetFirstNode(
                    "cropped", None, None, False)
            self.transform_image(volume)

        if not self._processing_image:
            volume = slicer.mrmlScene.GetFirstNode(
                    "Segmented Descending Aorta Volume", None, None, False)
            self._processing_image = sitkUtils.PullVolumeFromSlicer(volume)

        asc_axial_segmenter = AortaAscendingAxialSegmenter(
            starting_slice=aASnumber[2],
            aorta_centre=aASnumber[:2],
            num_slice_skipping=int(float(num_slice_skipping)),
            segmentation_factor=float(segmentation_factor),
            cropped_image=self._cropped_image,
            processing_image=self._processing_image
        )
        asc_axial_segmenter.begin_segmentation()
        logging.info(
            f"{now} Finished processing Ascending Aorta Segmentation")
        self._segmenting_image = asc_axial_segmenter.processing_image
        return self._segmenting_image

    def processSagittalAorta(self, segmentation_factor):
        logging.info(AortaSagitalSegmenter)


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
