import abc
import copy
import logging

import cv2
import numpy
from PyQt5.QtCore import *
from PyQt5.QtCore import QModelIndex, QObject
from PyQt5.QtGui import *
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QStyleOptionViewItem
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingCore import vtkCellPicker

import FunctionLib_UI.ui_processing
from FunctionLib_Robot.__init__ import *
# from vtkmodules.all import vtkCallbackCommand
from FunctionLib_Robot.logger import logger
from FunctionLib_Vision._class import *


class ViewPortUnit(QObject):
    
    signalChangedTrajPosition = pyqtSignal(int)
    signalUpdateExcept  = pyqtSignal(str)
    signalUpdateAll     = pyqtSignal()
    signalUpdateSlice   = pyqtSignal(np.ndarray)
    signalFocus         = pyqtSignal(np.ndarray)
    signalSetSliceValue = pyqtSignal(np.ndarray)
    
    def __init__(self, mainWidget, dicom:DISPLAY, vtkWidget:QVTKRenderWindowInteractor, orientation:str, uiScrollSlice:QScrollBar, uiCbxOrientation:QComboBox):
        
        super().__init__()
        
        self.bUpdateOtherView = True
        self.bSelected = False
        self.bFocusMode = True
        self.renderer   = None
    
        self.parentWidget       = mainWidget
        self.dicom              = dicom
        self.uiCbxOrientation   = uiCbxOrientation
        self.vtkWidget          = vtkWidget
        self.uiScrollSlice      = uiScrollSlice
        self.orientation        = orientation
        self.currentIndex       = uiCbxOrientation.currentIndex()
        self.uiScrollSlice.valueChanged.connect(self.OnValueChanged_ViewScroll)
        self.uiScrollSlice.setMinimum(0)
        self.renderWindow       = vtkWidget.GetRenderWindow()
        self.iren               = self.renderWindow.GetInteractor()
        
        if not dicom:
            iStyle = MyInteractorStyle(mainWidget, VIEW_3D)
            self.iren.SetInteractorStyle(iStyle)
            return
        
        self.position           = dicom.target
        self.imagePosition      = dicom.imagePosition
        
        
        if orientation == VIEW_AXIAL:
            # self.renderer = self.dicom.rendererAxial
            # renderWindow = self.vtkWidget.GetRenderWindow()
            self.changeRenderer(self.dicom.rendererAxial)
            
            iStyle = MyInteractorStyle(mainWidget, VIEW_AXIAL)
            self.iren.SetInteractorStyle(iStyle) 
            
            self.uiScrollSlice.setMaximum(self.dicom.imageDimensions[2] - 1)
            self.uiScrollSlice.setValue(int((self.dicom.imageDimensions[2])/2))
        elif orientation == VIEW_SAGITTAL:
            # self.renderer = self.dicom.rendererSagittal
            # self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer) 
            
            self.changeRenderer(self.dicom.rendererSagittal) 
              
            iStyle = MyInteractorStyle(mainWidget, VIEW_SAGITTAL)    
            self.iren.SetInteractorStyle(iStyle)
            
            self.uiScrollSlice.setMaximum(self.dicom.imageDimensions[0] - 1)
            self.uiScrollSlice.setValue(int((self.dicom.imageDimensions[0])/2))
        elif orientation == VIEW_CORONAL:
            # self.renderer = self.dicom.rendererCoronal
            # self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
            self.changeRenderer(self.dicom.rendererCoronal) 
            iStyle = MyInteractorStyle(mainWidget, VIEW_CORONAL)    
            self.iren.SetInteractorStyle(iStyle)
            
            self.uiScrollSlice.setMaximum(self.dicom.imageDimensions[1] - 1)
            self.uiScrollSlice.setValue(int((self.dicom.imageDimensions[1])/2))
        elif orientation == VIEW_3D:
            # self.renderer = self.dicom.renderer3D
            # self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
            self.changeRenderer(self.dicom.renderer3D)
            self.iren.SetInteractorStyle(MyInteractorStyle(mainWidget, VIEW_3D))
            self.uiScrollSlice.setEnabled(False)
        elif orientation == VIEW_CROSS_SECTION:
            # self.renderer = self.dicom.rendererCrossSection
            # self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
            self.changeRenderer(self.dicom.rendererCrossSection)
            self.iren.SetInteractorStyle(MyInteractorStyle(mainWidget, VIEW_CROSS_SECTION))
            
            length = self.renderer.GetTrajectoryLength()
            if length is not None:
                self.uiScrollSlice.setMinimum(0)
                self.uiScrollSlice.setMaximum(int(length))
                self.uiScrollSlice.setValue(0)
        # self.renderer.signalUpdateView.connect(self.UpdateView)
        self.renderer.SetTarget()
        self.renderer.initalBorder()
        self.UpdateView()
        
    def changeRenderer(self, renderer:vtkRenderer):
        oldRenderers = self.renderWindow.GetRenderers()
        oldRenderer = oldRenderers.GetFirstRenderer()
        
        while oldRenderer is not None:
            self.renderWindow.RemoveRenderer(oldRenderer)
            oldRenderer = oldRenderers.GetNextItem()
            
        self.renderer = renderer
        self.renderWindow.AddRenderer(self.renderer)
            
    def Reset(self):
        self.uiScrollSlice.valueChanged.disconnect(self.OnValueChanged_ViewScroll)
        # self.renderer.RemoveAllViewProps()
        self.renderWindow.Finalize()
        
    def Close(self):
        self.renderer.RemoveAllViewProps()
        self.Reset()
        
    def Focus(self, pos = None):
        if not self.renderer:
            return
        
        if self.bFocusMode:
            if hasattr(self, 'renderer') and \
                self.orientation != VIEW_3D and \
                self.orientation != VIEW_CROSS_SECTION:
                if pos is None:
                    pos = self.renderer.target
                self.renderer.SetCameraToTarget(pos)
    def OnValueChanged_ViewScroll(self):
        if not self.dicom or not self.renderer:
            return
        
        value = self.uiScrollSlice.value()
        self.renderer.ChangeView(value)
        
        if self.orientation == VIEW_AXIAL:
            self.dicom.target[2] = value * self.dicom.pixel2Mm[2]
            self.dicom.imagePosition[2] = value
        elif self.orientation == VIEW_CORONAL:
            self.dicom.target[1] = value * self.dicom.pixel2Mm[1]
            self.dicom.imagePosition[1] = value
        elif self.orientation == VIEW_SAGITTAL:
            self.dicom.target[0] = value * self.dicom.pixel2Mm[0]
            self.dicom.imagePosition[0] = value
        
        self.signalSetSliceValue.emit(self.dicom.imagePosition)
        
        if self.orientation == VIEW_CROSS_SECTION:
            self.signalChangedTrajPosition.emit(value)
            self.signalUpdateExcept.emit(VIEW_CROSS_SECTION)
        else:
            self.signalUpdateAll.emit()
            
        self.UpdateView()
        
    def MapPositionToImageSlice(self, pos = None, posCS = None):
        if not self.renderer:
            return
        
        if isinstance(pos, tuple) or isinstance(pos, list):
            pos = np.array(pos)
        
        imagePos = [0, 0, 0]
        pcoord = [0, 0, 0]
        
        if pos is not None:
            self.signalFocus.emit(pos)
            
            if self.orientation == VIEW_CROSS_SECTION:
                self.renderer.SetTarget(posOriginal = pos)
            else:
                self.renderer.image.ComputeStructuredCoordinates(pos, imagePos, pcoord)
                imagePos += np.round(pcoord)
                self.renderer.SetTarget(pos)
                self.ChangeSliceView(imagePos)
                self.imagePosition[:] = imagePos
                
                # self.renderer.Segmentation(pos)
                
            self.signalUpdateAll.emit()
            self.signalUpdateSlice.emit(np.array(imagePos))
        elif posCS is not None:
            pos = self.dicom.rendererCrossSection.GetPositionFromCrossSection(posCS)
            # print(f'pos = {pos}, posCS = {posCS}')
            
            if self.orientation == VIEW_CROSS_SECTION:
                self.renderer.SetTarget(pos = posCS, posOriginal = pos)
                self.renderer.image.ComputeStructuredCoordinates(pos, imagePos, pcoord)
                imagePos += np.round(pcoord)
                self.imagePosition[:] = imagePos
                
            # self.signalFocus.emit(pos)
            self.signalUpdateAll.emit()
            self.signalUpdateSlice.emit(imagePos)
            
    
    
    def ChangeSliceView(self, pos = None):
        if not self.renderer:
            return
        
        if pos is None:
            pos = np.round(self.renderer.target / self.renderer.pixel2Mm)
        iPos = np.array(pos).astype(int)
        
        scrollValue = None
        if self.orientation == VIEW_CROSS_SECTION:
            # self.renderer.SetCrossSectionPosition(self.renderer.target)
            pass
        else:
            if self.orientation == VIEW_SAGITTAL:
                scrollValue = iPos[0]
            elif self.orientation == VIEW_CORONAL:
                scrollValue = iPos[1]
            elif self.orientation == VIEW_AXIAL:
                scrollValue = iPos[2]
        
            self.renderer.ChangeView(scrollValue)
            
        if scrollValue is not None:
            self.uiScrollSlice.blockSignals(True)
            self.uiScrollSlice.setValue(scrollValue)
            self.uiScrollSlice.blockSignals(False)
            
        # self.parentWidget.UpdateView_L()
        self.UpdateView()
        
    def ChangeTrajectoryPosition(self, delta = 0, pos = None):
        if delta >= 0:
            if self.orientation != VIEW_CROSS_SECTION:
                return
            
            self.uiScrollSlice.setValue(delta)
            
        if pos is not None:
            if isinstance(pos, list) or isinstance(pos, tuple):
                pos = np.array(pos)
                
            iPos = np.round(pos / self.renderer.pixel2Mm)
        
    def Assign(self, viewPortUnit):
        self.dicom              = viewPortUnit.dicom
        self.uiCbxOrientation   = viewPortUnit.uiCbxOrientation
        self.vtkWidget          = viewPortUnit.vtkWidget
        self.uiScrollSlice      = viewPortUnit.uiScrollSlice
        self.orientation        = viewPortUnit.orientation
        self.iren               = viewPortUnit.iren
        
    def SetViewPort(self, orientation:str, renderer:RendererObj):
        if renderer is not None:
            renderWindow = self.vtkWidget.GetRenderWindow()
            if self.renderer:
                renderWindow.RemoveRenderer(self.renderer)
            renderWindow.AddRenderer(renderer)
            
            self.renderer = renderer
            self.orientation = orientation
            
            # self.position           = self.dicom.target
            # self.imagePosition      = self.dicom.imagePosition
            dimension = renderer.imageDimensions
            
            if orientation == VIEW_AXIAL:
                self.uiScrollSlice.setMaximum(dimension[2] - 1)
                self.MapPositionToImageSlice(self.renderer.target)
            elif orientation == VIEW_CORONAL:
                self.uiScrollSlice.setMaximum(dimension[1] - 1)
                self.MapPositionToImageSlice(self.renderer.target)
            elif orientation == VIEW_SAGITTAL:
                self.uiScrollSlice.setMaximum(dimension[0] - 1)
                self.MapPositionToImageSlice(self.renderer.target)
            elif orientation == VIEW_CROSS_SECTION:
                length = renderer.GetTrajectoryLength()
                self.uiScrollSlice.setMaximum(int(length))
                self.renderer.SetTarget(posOriginal = self.renderer.target)
                
                self.renderer.FocusTarget()
            
            # self.uiScrollSlice.setValue(0)
            # renderer.signalUpdateView.connect(self.UpdateView)
            self.UpdateView()
    def Swap(self, viewPortUnit):
        # if isinstance(viewPortUnit, str):
        #     viewPortUnit = self.parentWidget.vi
        if self.renderer:
            self.vtkWidget.GetRenderWindow().RemoveRenderer(self.renderer)
            viewPortUnit.vtkWidget.GetRenderWindow().AddRenderer(self.renderer) 
            
        if viewPortUnit.renderer:
            viewPortUnit.vtkWidget.GetRenderWindow().RemoveRenderer(viewPortUnit.renderer)
            self.vtkWidget.GetRenderWindow().AddRenderer(viewPortUnit.renderer)
        
        self.renderer, viewPortUnit.renderer = viewPortUnit.renderer, self.renderer
        self.orientation, viewPortUnit.orientation = viewPortUnit.orientation, self.orientation
        
        self.position, viewPortUnit.position = viewPortUnit.position, self.position
        self.imagePosition, viewPortUnit.imagePosition = viewPortUnit.imagePosition, self.imagePosition
        
        viewPortUnit.uiCbxOrientation.blockSignals(True)
        viewPortUnit.uiCbxOrientation.setCurrentIndex(self.currentIndex)
        viewPortUnit.currentIndex = self.currentIndex
        viewPortUnit.uiCbxOrientation.blockSignals(False)
        self.currentIndex = self.uiCbxOrientation.currentIndex()
        
        minimum = self.uiScrollSlice.minimum()
        maximum = self.uiScrollSlice.maximum()
        value = self.uiScrollSlice.value()
        
        self.uiScrollSlice.setMinimum(viewPortUnit.uiScrollSlice.minimum())
        self.uiScrollSlice.setMaximum(viewPortUnit.uiScrollSlice.maximum())
        self.uiScrollSlice.setValue(viewPortUnit.uiScrollSlice.value())
        
        viewPortUnit.uiScrollSlice.setMinimum(minimum)
        viewPortUnit.uiScrollSlice.setMaximum(maximum)
        viewPortUnit.uiScrollSlice.setValue(value)
        
        # swap interactorStyle
        # self.iren.SetInteractorStyle(MyInteractorStyle(self.parentWidget, self.orientation))
        self.iren.GetInteractorStyle().SetOrientation(self.orientation)
        if self.orientation != '3D':
            self.uiScrollSlice.setEnabled(True)
        else:
            self.uiScrollSlice.setEnabled(False)
        # else:
        #     self.iren.SetInteractorStyle(MyInteractorStyle3D(None))
        #     self.uiScrollSlice.setEnabled(False)
            
        # viewPortUnit.iren.SetInteractorStyle(MyInteractorStyle(viewPortUnit.parentWidget, viewPortUnit.orientation))
        viewPortUnit.iren.GetInteractorStyle().SetOrientation(viewPortUnit.orientation)
        if viewPortUnit.orientation != '3D':
            viewPortUnit.uiScrollSlice.setEnabled(True)
        else:
            viewPortUnit.uiScrollSlice.setEnabled(False)
        # else:
        #     viewPortUnit.iren.SetInteractorStyle(MyInteractorStyle3D(None))
        #     viewPortUnit.uiScrollSlice.setEnabled(False)
        
        self.UpdateView()
        viewPortUnit.UpdateView()
        
    def SetFocusMode(self, bEnable):
        if not self.renderer:
            return
        
        self.bFocusMode = bEnable
        self.renderer.SetFocusMode(self.bFocusMode)
        if self.bFocusMode:
            self.Focus()
        self.renderer.SetTarget()
        self.UpdateView()
        
    def SetTargetVisible(self, bVisible):
        self.renderer.SetTargetVisible(bVisible)
        
    def UpdateView(self):
        if not self.renderer:
            return
        
        self.iren.Initialize()
        self.iren.Start()
        
class TreeViewDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        if option.state & QStyle.State_Selected:
            selData = index.data(Qt.UserRole + 4)
            
            if selData is not None:
                color = QColor()
                if selData == 1:
                    color = QColor(100, 0, 0)
                elif selData == 2:
                    color = QColor(0, 100, 0)
                
                painter.save()
                painter.fillRect(option.rect, color)
                painter.restore()
                
                option.palette.setBrush(QPalette.Text, QBrush(QColor(255, 255, 255)))
        
        super().paint(painter, option, index)
class TrajectoryViewDelegate(QStyledItemDelegate):
    def __init__(self):
        
        super().__init__()
        
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        super().paint(painter, option, index)
        
        strColor = index.data(ROLE_COLOR)
        
        if strColor is not None:
            color = QColor(strColor)
            
            painter.fillRect(option.rect, color)
            option.palette.setBrush(QPalette.Text, QBrush(QColor(255, 255, 255)))
        
# class SystemProcessing(QWidget, FunctionLib_UI.ui_processing.Ui_Form):
#     def __init__(self, nParts = 1):
#         """show loading window"""
#         ## 顯示 loading 畫面 ############################################################################################
#         self.nParts = max(nParts, 1)
#         super().__init__()
#         self.setupUi(self)
#         ############################################################################################
        
#     def _AddProgress(self, value):
#         percent = self.pgbLoadDIcom.value()
#         self.pgbLoadDIcom.setValue(min(percent + value, 100))
    
#     def UpdateProgress(self, value):
#         if self.nParts == 1:
#             self.pgbLoadDIcom.setValue(int(value * 100))
#         else:
#             value = int(value / self.nParts)
#             self._AddProgress(value)
    


class SynchronInteractorStyle(vtkInteractorStyleTrackballCamera):
    
    listOrientation = [VIEW_AXIAL, VIEW_CORONAL, VIEW_SAGITTAL]
    def __init__(self, viewport):
        self.viewport = viewport
    
    # def AddChild(self, *listInteractorStyle):
    #     for iStyle in listInteractorStyle:
    #         self.listInteractorStyle.append(iStyle)
            
    def SetViewport(self, viewport):
        self.viewport = viewport
    
    def OnMouseWheelForward(self, obj, event):
        for view in self.viewport.values():
            # if not hasattr(view, 'orientation'):
            #     iStyle = view.GetInteractorStyle()
            #     iStyle.CallMouseWheelForward()
            # else:
            if view.orientation in self.listOrientation:
                iStyle = view.iren.GetInteractorStyle()
                iStyle.CallMouseWheelForward()
        obj.parent.UpdateTarget(bFocus = False)
        obj.parent.UpdateView()
        
    def OnMouseWheelBackward(self, obj, event):
        for view in self.viewport.values():
            if view.orientation in self.listOrientation:
                iStyle = view.iren.GetInteractorStyle()
                iStyle.CallMouseWheelBackward()
        obj.parent.UpdateTarget(bFocus = False)
        obj.parent.UpdateView()
    

class MyInteractorStyle(vtkInteractorStyleTrackballCamera):
    
    def __init__(self, parent, renderView):
        # vtkInteractorStyleTrackballCamera.__init__()
        # QObject.__init__()
        self.signalObject = QSignalObject()
        # syncIStyle = parent.syncInteractorStyle
        self.AddObserver('MiddleButtonPressEvent', self.OnMiddleButtonPress)
        self.AddObserver('MiddleButtonReleaseEvent', self.OnMiddleButtonRelease)
        self.AddObserver('RightButtonPressEvent', self.OnRightButtonPress)
        self.AddObserver('RightButtonReleaseEvent', self.OnRightButtonRelease)
        self.AddObserver('LeftButtonPressEvent', self.OnLeftButtonPress)
        self.AddObserver('LeftButtonReleaseEvent', self.OnLeftButtonRelease)
        self.AddObserver('MouseMoveEvent', self.OnMouseMove)
        self.AddObserver('MouseWheelForwardEvent', self.OnMouseWheelForward)
        self.AddObserver('MouseWheelBackwardEvent', self.OnMouseWheelBackward)
        self.parent = parent
        self.renderView = renderView
        self.isMiddlePress = False
        self.isRightPress = False
        self.isLeftPress = False
        self.currentRenderer = None
        self.currentPos = []
        
        self.renderSagittal = None
        self.renderCoronal = None
        self.renderAxial = None
        self.irenSagittal = None
        self.irenAxial = None
        self.irenCoronal = None
        self.iren3D = None
        
        self.currentDicom = None
        self.currentTag = {}
        self.sliderWW = None
        self.sliderWL = None
        self.dicomType = None
                
        self.actorBallRed = vtkActor()
        self.actorBallGreen = vtkActor()
        self.actorTarget = vtkAssembly()
        return
    
    def GetCurrentSlider(self):      
        
        self.GetCurrentState()        
        
        slider = None  
        for view in self.viewPort.values():
            if view.orientation == self.renderView:
                return view.uiScrollSlice
        # if self.renderView == 'Coronal':
        #     if self.dicomType == 'LOW':
        #         slider = self.parent.SliceSelect_Coronal_L
        #     elif self.dicomType == 'HIGH':
        #         slider = self.parent.SliceSelect_Coronal_H
        # elif self.renderView == 'Sagittal':
        #     if self.dicomType == 'LOW':
        #         slider = self.parent.SliceSelect_Sagittal_L
        #     elif self.dicomType == 'HIGH':
        #         slider = self.parent.SliceSelect_Sagittal_H
        # elif self.renderView == 'Axial':
        #     if self.dicomType == 'LOW':
        #         slider = self.parent.SliceSelect_Axial_L
        #     elif self.dicomType == 'HIGH':
        #         slider = self.parent.SliceSelect_Axial_H
        # return slider
    
    def GetCurrentState(self):
        # indexL = self.parent.tabWidget.indexOf(self.parent.tabWidget_Low)
        # indexH = self.parent.tabWidget.indexOf(self.parent.tabWidget_High)
                
        # if self.parent.tabWidget.currentIndex() == indexL:
        if not hasattr(self.parent, 'dicomLow'):
            return
        self.viewPort     = self.parent.viewport_L
        self.currentTag   = self.parent.currentTag        
        # self.currentDicom = self.parent.dicomLow    
        self.currentDicom = self.currentTag.get('display')   
        if not self.currentDicom:
            logger.warning('current dicom is None at MyInteractorStyle') 
        # self.irenSagittal = self.parent.irenSagittal_L
        # self.irenAxial    = self.parent.irenAxial_L
        # self.irenCoronal  = self.parent.irenCoronal_L
        # self.iren3D       = self.parent.iren3D_L
        # self.currentTag   = self.parent.dcmTagLow
        # self.sliderWW     = self.parent.Slider_WW_L
        # self.sliderWL     = self.parent.Slider_WL_L
        self.dicomType    = 'LOW'
        # elif self.parent.tabWidget.currentIndex() == indexH:
        #     if not hasattr(self.parent, 'dicomHigh'):
        #         return
        #     self.viewPort     = self.parent.viewPortH
        #     self.currentDicom = self.parent.dicomHigh
        #     self.irenSagittal = self.parent.irenSagittal_H
        #     self.irenAxial    = self.parent.irenAxial_H
        #     self.irenCoronal  = self.parent.irenCoronal_H
        #     self.iren3D       = self.parent.iren3D_H
        #     self.currentTag   = self.parent.dcmTagHigh
        #     self.sliderWW     = self.parent.Slider_WW_H
        #     self.sliderWL     = self.parent.Slider_WL_H
        #     self.dicomType    = 'HIGH'
            
        self.renderSagittal = self.currentDicom.rendererSagittal
        self.renderCoronal  = self.currentDicom.rendererCoronal
        self.renderAxial    = self.currentDicom.rendererAxial
        self.render3D       = self.currentDicom.renderer3D
        
    def SetOrientation(self, orientation):
        self.renderView = orientation
        
    def OnMouseWheelForward(self, obj, event):
        listView = [VIEW_AXIAL, VIEW_CORONAL, VIEW_SAGITTAL]
        
        if self.renderView in listView:
            self.parent.syncInteractorStyle.OnMouseWheelForward(obj, event)
        else:
            super(MyInteractorStyle, self).OnMouseWheelForward()
            self.parent.UpdateTarget()
            # self.parent.UpdateView()
            # self.signalObject.EmitZoomIn(event)
        
    def CallMouseWheelForward(self):
         super(MyInteractorStyle, self).OnMouseWheelForward()
        
        
    def OnMouseWheelBackward(self, obj, event):
        listView = [VIEW_AXIAL, VIEW_CORONAL, VIEW_SAGITTAL]
        
        if self.renderView in listView:
            self.parent.syncInteractorStyle.OnMouseWheelBackward(obj, event)
        else:
            super(MyInteractorStyle, self).OnMouseWheelBackward()
            self.parent.UpdateTarget()
            # self.parent.UpdateView_L()
            # self.signalObject.EmitZoomIn()
        
    def CallMouseWheelBackward(self):
        super(MyInteractorStyle, self).OnMouseWheelBackward()
    
    def OnMouseMove(self, obj, event):
        self.GetCurrentState()
        points = [0, 0]
        picker, pick_point = self.GetPickPosition(points)
        
        if not self.currentTag:
            logger.warning('dicom tag is Null')
            return
        
        if self.isRightPress == True:
            windowWidth = self.currentTag.get("ww")   
            windowLevel = self.currentTag.get("wl")         
            # points = self.GetInteractor().GetEventPosition()
            diff = np.array(points) - self.currentPos
            
            windowWidth = windowWidth + diff[0] * 5
            windowLevel = windowLevel + diff[1] * 5
            self.currentDicom.ChangeWindowWidthView(windowWidth)
            self.currentDicom.ChangeWindowLevelView(windowLevel)
            self.currentTag.update({"ww":windowWidth})
            self.currentTag.update({"wl":windowLevel})
            # self.sliderWW.setValue(windowWidth)
            # self.sliderWL.setValue(windowLevel)
            
            self.currentPos = np.array(points)
            self.signalObject.EmitUpdateView()
            
        elif self.isMiddlePress == True:
            if self.currentRenderer != self.render3D:
                diff = np.array(points) - self.currentPos
                self.currentPos = np.array(points)
                
                slider = self.GetCurrentSlider()
                        
                value = slider.value() + diff[1]
                slider.setValue(value)
            else:
                super(MyInteractorStyle, self).OnMouseMove()
        elif self.isLeftPress == True:
            if not isinstance(self.currentRenderer, RendererCrossSectionObj):
                super(MyInteractorStyle, self).OnMouseMove()
                
                if self.currentRenderer.bFocusMode:
                    picker, pick_point = self.GetPickViewCenter()
                    if picker is None:
                        return
                    
                    isValidActor = False
                    
                    actor = picker.GetProp3D()
                    # while actor is not None:
                    if isinstance(actor, vtkImageActor):
                        for view in self.viewPort.values():
                            if view.renderer == self.currentRenderer:
                                break
                        
                        view.MapPositionToImageSlice(pos = pick_point)
                        isValidActor = True
                        # actor = actors.GetNextProp3D()

                    if isValidActor == True:
                        self.currentTag["pickPoint"] = self.currentDicom.target
                else:
                    self.parent.UpdateTarget(bFocus = False)
        else:
            actor = picker.GetProp3D()
            if isinstance(actor, vtkImageActor):
                if self.currentRenderer.orientation == VIEW_CROSS_SECTION:
                    pos = self.currentRenderer.GetPositionFromCrossSection(pick_point)
                    self.signalObject.EmitUpdateHU(self.GetHUValue(pos))
                else:
                    self.signalObject.EmitUpdateHU(self.GetHUValue(pick_point))

    def OnMiddleButtonPress(self, obj, event):
        points = self.GetCurrentRenderer()
        self.isMiddlePress = True
        if self.currentRenderer != self.render3D:
            # points = self.GetInteractor().GetEventPosition()
            self.currentPos = np.array(points)
        else:
            super(MyInteractorStyle, self).OnMiddleButtonDown()
        
    
    def OnMiddleButtonRelease(self, obj, event):
        points = self.GetCurrentRenderer()
        self.isMiddlePress = False
        if self.currentRenderer == self.render3D:
            super(MyInteractorStyle, self).OnMiddleButtonUp()
    
    def OnRightButtonPress(self, obj, event):
        self.isRightPress = True
        points = self.GetInteractor().GetEventPosition()
        self.currentPos = np.array(points)
        return
    
    def OnRightButtonRelease(self, obj, event):
        self.isRightPress = False
        return
    
    def OnLeftButtonPress(self, obj, event):
        # points = self.GetInteractor().GetEventPosition()
        points = self.GetCurrentRenderer()
        self.isLeftPress = True
        self.currentPos = np.array(points)
        if self.currentRenderer != self.render3D:
            super(MyInteractorStyle, self).OnMiddleButtonDown()
        else:
            super().OnLeftButtonDown()
    
    def OnLeftButtonRelease(self, obj, event):
        self.isLeftPress = False
        if self.currentRenderer == self.render3D:
            super().OnLeftButtonUp()
        
        """Get the location of the click (in window coordinates)"""
        ## 取得點選位置 ############################################################################################

        points = [0, 0]
        picker, pick_point = self.GetPickPosition(points)
        if picker is None:
            return
        
        distance = np.linalg.norm(np.array(self.currentPos) - np.array(points))
        if distance > 1:
            super(MyInteractorStyle, self).OnMiddleButtonUp()
            if self.currentRenderer != self.render3D:
                self.parent.UpdateTarget(bFocus = False)
            return
        
        # pick_point = picker.GetPickPosition()        
        self.GetCurrentSlider()
                    
        ############################################################################################
        ## 儲存點 ############################################################################################
        # if picker.GetCellId() != -1:
        #     actors = picker.GetProp3Ds()
        #     actor = actors.GetItemAsObject(0)
            
        actor = picker.GetProp3D()
        isValidActor = False
        # while actor is not None:
            # actor = picker.GetActor()
            
        if isinstance(actor, vtk.vtkImageSlice) or isinstance(actor, vtkVolume):
            for view in self.viewPort.values():
                if view.renderer == self.currentRenderer:
                    break
            # image = self.currentDicom.vtkImage    
            # if actor == self.currentDicom.rendererCrossSection.actorImage:
            if isinstance(self.currentRenderer, RendererCrossSectionObj):
                view.MapPositionToImageSlice(posCS = pick_point)
                
            else:
                view.MapPositionToImageSlice(pos = pick_point)
            
            isValidActor = True
                    # break
                
            # actor = actors.GetNextProp3D()
                
            if isValidActor == True:
                
                self.currentTag["pickPoint"] = self.currentDicom.target
        else:
            logger.warning("no objects be picked")
       
    def GetCurrentRenderer(self):
        points = self.GetInteractor().GetEventPosition()
        self.currentRenderer = self.GetInteractor().FindPokedRenderer(points[0], points[1])
        
        if self.currentRenderer:
            self.signalObject.EmitGetRenderer(self.currentRenderer)
        return points
    
    def GetPickPosition(self, points = None):
        picker = vtkCellPicker()
        if points is not None:
            points[:] = self.GetCurrentRenderer()
        else:
            points = self.GetCurrentRenderer()
            
        if self.currentRenderer is None:
            return None, None
        
        picker.Pick(points[0], points[1], 0, self.currentRenderer)
        pick_point = picker.GetPickPosition()  
        return picker, pick_point 
    
    def GetPickViewCenter(self):
        if self.currentRenderer is None:
            return None, None
        
        picker = vtkCellPicker()
        centerPos = self.currentRenderer.GetCenter()
        picker.Pick(centerPos[0], centerPos[1], 0, self.currentRenderer)
        pick_point = picker.GetPickPosition()
        return picker, pick_point
        
        
    def GetHUValue(self, pick_point):
        
        # self.currentTag["pickPoint"] = pick_point
        # convert from image size to image slices
        
        value = self.currentDicom.GetHUValue(pick_point)
        return value
    
    # type:0 pick_point = normal slice view coordinate
    # type:1 pick_point = cross section view coordinate
    def DrawPlusLine(self, pos, posCS, pcoord):
        pass
        
        # for renderer in self.currentDicom.rendererList[:-1]:
        #     # renderer.InitTarget(pos)
        #     renderer.SetTarget(pos)
            
        # if posCS is not None:
        #     self.currentDicom.rendererCrossSection.SetTarget(posCS)
            
        # self.currentDicom.pcoord[:] = pcoord