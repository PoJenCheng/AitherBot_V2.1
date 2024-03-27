# from fileinput import filename
# from turtle import update
import typing
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from FunctionLib_Robot._class import *
from FunctionLib_Robot._subFunction import *
from FunctionLib_Robot.__init__ import *
from FunctionLib_Robot._globalVar import *
from time import sleep
from datetime import datetime
import abc
import copy
import sys
import numpy
import math
import cv2
import logging
import threading
import os
import FunctionLib_UI.ui_coordinate_system
import FunctionLib_UI.ui_coordinate_system_manual
# import FunctionLib_UI.ui_set_point_system
import FunctionLib_UI.ui_processing
import FunctionLib_UI.ui_matplotlib_pyqt
# from FunctionLib_UI.ui_matplotlib_pyqt import *
from FunctionLib_Vision._class import *
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingCore import vtkCellPicker
from vtkmodules.all import vtkCallbackCommand
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
ConnectCount = 0

        
    

class MainWidget(QMainWindow,Ui_MainWindow, MOTORSUBFUNCTION, LineLaser):
    
    viewPortL = None
    viewPortH = None
    signalProgress = pyqtSignal(float)
    currentRenderer = None
    currentStyle = None
    bFullView = False
    def __init__(self, parent = None):
        # try:
        """initial main ui"""       
        super(MainWidget, self).__init__()
        QMainWindow.__init__(self)

        self.setupUi(self)
        self._init_log()
        self._init_ui()
        self.logUI.info('initial UI')

        self.ui = Ui_MainWindow()

        self.dcmFn = DICOM()
        self.regFn = REGISTRATION()
        self.dicomLow = DISPLAY()
        self.dicomHigh = DISPLAY()
        
        # self.tabWidget.setCurrentWidget(self.tabWidget_Low)
        self.tabWidget.setCurrentWidget(self.tabWidget_Dynamic)

        self.PlanningPath = []

        "initialize dcm Low"
        self.dcmTagLow = {}
        self.dcmTagLow.update({"ww": 1})
        self.dcmTagLow.update({"wl": 1})
        self.dcmTagLow.update({"imageTag": []})
        "registration ball"
        # self.dcmTagLow.update({"selectedBall": []})
        self.dcmTagLow.update({"regBall": []})
        self.dcmTagLow.update({"flageSelectedBall": False})
        self.dcmTagLow.update({"candidateBall": []})
        self.dcmTagLow.update({"selectedBallKey": []})
        "set point"
        self.dcmTagLow.update({"selectedPoint": []})
        self.dcmTagLow.update({"flageSelectedPoint": False})
        self.dcmTagLow.update({"flageShowPointButton": False})
        "show point"
        # self.dcmTagLow.update({"sectionTag":[]})

        "initialize dcm High"
        self.dcmTagHigh = {}
        self.dcmTagHigh.update({"ww": 1})
        self.dcmTagHigh.update({"wl": 1})
        self.dcmTagHigh.update({"imageTag": []})
        "registration ball"
        # self.dcmTagHigh.update({"selectedBall": []})
        self.dcmTagHigh.update({"regBall": []})
        self.dcmTagHigh.update({"flageSelectedBall": False})
        self.dcmTagHigh.update({"candidateBall": []})
        self.dcmTagHigh.update({"selectedBallKey": []})
        "set point"
        self.dcmTagHigh.update({"selectedPoint": []})
        self.dcmTagHigh.update({"flageSelectedPoint": False})
        self.dcmTagHigh.update({"flageShowPointButton": False})
        "show point"
        # self.dcmTagHigh.update({"sectionTag":[]})

        self.Slider_WW_L.setMinimum(1)
        self.Slider_WW_L.setMaximum(3071)
        self.Slider_WW_L.setValue(0)
        self.Slider_WW_H.setMinimum(1)
        self.Slider_WW_H.setMaximum(3071)
        self.Slider_WW_H.setValue(0)

        self.Slider_WL_L.setMinimum(-1024)
        self.Slider_WL_L.setMaximum(3071)
        self.Slider_WL_L.setValue(0)
        self.Slider_WL_H.setMinimum(-1024)
        self.Slider_WL_H.setMaximum(3071)
        self.Slider_WL_H.setValue(0)

        self.Slider_WW_L.valueChanged.connect(self.SetWidth_L)
        self.Slider_WL_L.valueChanged.connect(self.SetLevel_L)
        self.Slider_WW_H.valueChanged.connect(self.SetWidth_H)
        self.Slider_WL_H.valueChanged.connect(self.SetLevel_H)

        self.Action_ImportDicom_L.triggered.connect(self.ImportDicom_L)
        self.Action_ImportDicom_H.triggered.connect(self.ImportDicom_H)
        
        self.Button_ToEntry.clicked.connect(self.OnClick_Button_ToEntryL)
        self.Button_ToTarget.clicked.connect(self.OnClick_Button_ToTargetL)
        
        self.Button_ToEntryH.clicked.connect(self.OnClick_Button_ToEntryH)
        self.Button_ToTargetH.clicked.connect(self.OnClick_Button_ToTargetH)
        
        self.vtkWidgets_L = {}
        self.vtkWidgets_L['LT'] = self.qvtkWidget_3D_L
        self.vtkWidgets_L['RT'] = self.qvtkWidget_Axial_L
        self.vtkWidgets_L['LB'] = self.qvtkWidget_Sagittal_L
        self.vtkWidgets_L['RB'] = self.qvtkWidget_Coronal_L
        
        self.vtkWidgets_H = {}
        self.vtkWidgets_H['LT'] = self.qvtkWidget_3D_H
        self.vtkWidgets_H['RT'] = self.qvtkWidget_Axial_H
        self.vtkWidgets_H['LB'] = self.qvtkWidget_Sagittal_H
        self.vtkWidgets_H['RB'] = self.qvtkWidget_Coronal_H
        
        self.viewScrolls_L = {}
        self.viewScrolls_L['LT'] = self.SliceSelect_3D_L
        self.viewScrolls_L['RT'] = self.SliceSelect_Axial_L
        self.viewScrolls_L['LB'] = self.SliceSelect_Sagittal_L
        self.viewScrolls_L['RB'] = self.SliceSelect_Coronal_L
        
        self.viewScrolls_H = {}
        self.viewScrolls_H['LT'] = self.SliceSelect_3D_H
        self.viewScrolls_H['RT'] = self.SliceSelect_Axial_H
        self.viewScrolls_H['LB'] = self.SliceSelect_Sagittal_H
        self.viewScrolls_H['RB'] = self.SliceSelect_Coronal_H
        
        self.listViewSelectorL = {}
        self.listViewSelectorL['LT'] = self.cbxViewSelection1
        self.listViewSelectorL['RT'] = self.cbxViewSelection2
        self.listViewSelectorL['LB'] = self.cbxViewSelection3
        self.listViewSelectorL['RB'] = self.cbxViewSelection4
        
        self.listViewSelectorH = {}
        self.listViewSelectorH['LT'] = self.cbxViewSelection1_H
        self.listViewSelectorH['RT'] = self.cbxViewSelection2_H
        self.listViewSelectorH['LB'] = self.cbxViewSelection3_H
        self.listViewSelectorH['RB'] = self.cbxViewSelection4_H
        
        self.styleList = {}
        self.currentStyle = None
        # self.initSignal()
        
        self.logUI.debug('initial main UI')
        print('initial main UI')
        # except Exception as e:
        #     print("Initial System Error - UI")
        #     print(repr(e))
        #     QMessageBox.critical(self, "error", "Initial System Error - UI")
        try:
            "robot control initial"
            MOTORSUBFUNCTION.__init__(self)
            global g_homeStatus
            g_homeStatus = False
            self.homeStatus = g_homeStatus
            print('initial main robot control')
        except:
            print("Initial System Error - robot control")
            QMessageBox.critical(self, "error", "Initial System Error - robot control")
        # try:
        
        
        # "Line Laser initial"
        # LineLaser.__init__(self)
        # LineLaser.TriggerSetting(self)
        # # self.recordBreathingBase = False        
        
        # "Laser Button Color Initialization"
        self.Button_StartLaserDisplay.setStyleSheet("background-color:#DCDCDC")
        # # self.Button_StopLaserDisplay.setStyleSheet("background-color:#DCDCDC")
        # # self.Button_RecordCycle.setStyleSheet("background-color:#DCDCDC")
        # # self.Button_StopRecording.setStyleSheet("background-color:#DCDCDC")
        # # self.Button_StartTracking.setStyleSheet("background-color:#DCDCDC")
        # # self.Button_StopLaserTracking.setStyleSheet("background-color:#DCDCDC")
        
        # "Laser Button Disable Setting"
        # self.Button_StartLaserDisplay.setEnabled(True)
        # self.Button_StopLaserDisplay.setEnabled(False)
        # self.Button_RecordCycle.setEnabled(False)
        # self.Button_StopRecording.setEnabled(False)
        # self.Button_StartTracking.setEnabled(False)
        # self.Button_StopLaserTracking.setEnabled(False)
        # self.Button_Accuracy.setEnabled(False)
        
        # self.yellowLightCriteria = yellowLightCriteria_LowAccuracy
        # self.greenLightCriteria = greenLightCriteria_LowAccuracy
        
        # "LCD setting"
        # self.breathingRatio.setDecMode()
        # print('initial main Line Laser')
        # except:
        #     print("Initial System Error - Line Laser")
        #     QMessageBox.critical(self, "error", "Initial System Error - Line Laser")
        
          
    
    
    def initSignal(self):
        pass
        # self.dicomLow.signalUpdateView.connect(self.UpdateView_L)
        
    def ResetUI(self, dicomType:str):
        if dicomType.lower() == 'low':
            for selector in self.listViewSelectorL.values():
                # selector = self.listViewSelectorL[i]
                index = list(self.listViewSelectorL.values()).index(selector)
                selector.blockSignals(True)
                selector.setCurrentIndex(index)
                selector.blockSignals(False)
                count = selector.count()
                if count > 4:
                    for j in range(4, count):
                        selector.removeItem(j)
                        
            for widget in self.vtkWidgets_L.values():
                renderWindow = widget.GetRenderWindow()
                renderers = renderWindow.GetRenderers()
                renderer = renderers.GetFirstRenderer()
                while renderer:
                    renderWindow.RemoveRenderer(renderer)
                    renderer = renderers.GetNextItem()
                
        elif dicomType.lower() == 'high':
            for selector in self.listViewSelectorH.values():
                # selector = self.listViewSelectorH[i]
                index = list(self.listViewSelectorH.values()).index(selector)
                selector.blockSignals(True)
                selector.setCurrentIndex(index)
                selector.blockSignals(False)
                count = selector.count()
                if count > 4:
                    for j in range(4, count):
                        selector.removeItem(j)
                        
            for widget in self.vtkWidgets_H.values():
                renderWindow = widget.GetRenderWindow()
                renderers = renderWindow.GetRenderers()
                renderer = renderers.GetFirstRenderer()
                while renderer:
                    renderWindow.RemoveRenderer(renderer)
                    renderer = renderers.GetNextItem()
        
    def GetViewPort(self):
        indexL = self.tabWidget.indexOf(self.tabWidget_Low)
        indexH = self.tabWidget.indexOf(self.tabWidget_High)
        
        if self.tabWidget.currentIndex() == indexL:
            return self.viewPortL
        elif self.tabWidget.currentIndex() == indexH:
            return self.viewPortH
        
        return None
    
    def GetScroll(self, index:int, vtkWidget:QVTKRenderWindowInteractor):
        if vtkWidget is None:
            return
        
        index = min(max(index, 0), 3)
        
        for key, widget in self.vtkWidgets_L.items():
            if vtkWidget == widget:
                return self.viewScrolls_L.get(key)
            
    def Focus(self, pos):
        indexL = self.tabWidget.indexOf(self.tabWidget_Low)
        indexH = self.tabWidget.indexOf(self.tabWidget_High)
        
        if self.tabWidget.currentIndex() == indexL:
            for key, view in self.viewPortL.items():
                view.Focus(pos)
                # view.MapPositionToImageSlice(pos)
        elif self.tabWidget.currentIndex() == indexH:
            for key, view in self.viewPortH.items():
                view.Focus(pos)
                
    def SetViewToFull(self, key):
        # self.viewPortL['Full'].SetViewPort(view.orientation, view.renderer)
        self.bFullView = not self.bFullView
        if self.bFullView:
            self.gridLayout_Full.addWidget(self.listViewSelectorL[key], 0, 0, 1, 2)
            self.gridLayout_Full.addWidget(self.vtkWidgets_L[key], 1, 0, 1, 1)
            self.gridLayout_Full.addWidget(self.viewScrolls_L[key], 1, 1, 1, 1)
                
            self.stkViewport.setCurrentIndex(1)
        else:
            index = list(self.vtkWidgets_L.keys()).index(key)
            row = int(index / 2) * 2
            col = (index % 2) * 2
            
            self.gridLayout_4View.addWidget(self.listViewSelectorL[key], row, col, 1, 2)
            self.gridLayout_4View.addWidget(self.vtkWidgets_L[key], row + 1, col, 1, 1)
            self.gridLayout_4View.addWidget(self.viewScrolls_L[key], row + 1, col + 1, 1, 1)
                
            self.stkViewport.setCurrentIndex(0)
    def OnSignalOutRange(self, bFlagBack, bFlagNext):
        
        self.btnStepBack.setEnabled(bFlagBack)
        self.btnStepNext.setEnabled(bFlagNext)
        
    def onClick_Button_ShowTarget(self):
        bVisible = self.btnShowTarget.isChecked()
        for view in self.viewPortL.values():
            view.SetTargetVisible(bVisible)
        self.UpdateView_L()
        
    def OnClick_Button_FullView(self):
        
        for key, button in self.btnFullView.items():
            if button == self.sender():
                self.SetViewToFull(key)
        
    def OnClick_Button_EnableClipper(self):
        if not hasattr(self, 'tmpWidget'):
            image = self.viewPortL['LT'].renderer.image
            iren = self.viewPortL['LT'].vtkWidget.GetRenderWindow().GetInteractor()
            
            pWidget = vtkWidgetCall(self.viewPortL['LT'].renderer.volume, self.viewPortL['LT'].renderer, self.viewPortL['LT'].iren, self.dicomLow.windowLevelLookup)
            
            pWidget.SetInteractor(iren)
            pWidget.SetInputData(image)
            pWidget.SetResolution(10)
            pWidget.GetPlaneProperty().SetColor(0.9, 0.4, 0.4)
            pWidget.GetHandleProperty().SetColor(0, 0.4, 0.7)
            pWidget.GetHandleProperty().SetLineWidth(1.5)
            pWidget.SetRepresentationToOff()
            pWidget.SetPlaceFactor(1.0)
            pWidget.PlaceWidget()
            pWidget.On()
            
            pWidget.SetNormal(0, 0, 1)
            self.tmpWidget = pWidget
            
            pWidget.Update()
        else:
            bEnable = self.btnEnableClipper.isChecked()
            self.tmpWidget.SetEnabled(bEnable)    
        
        self.UpdateView_L()
    
    def OnClick_Button_ClipperXY(self):
        self.tmpWidget.SetNormal(0, 0, 1)
        self.tmpWidget.Update()
        self.UpdateView_L()
        
    def OnClick_Button_ClipperYZ(self):
        self.tmpWidget.SetNormal(1, 0, 0)
        self.tmpWidget.Update()
        self.UpdateView_L()
        
    def OnClick_Button_ClipperXZ(self):
        self.tmpWidget.SetNormal(0, 1, 0)
        self.tmpWidget.Update()
        self.UpdateView_L()
        
    def OnClick_Button_FocusMode(self):
        if not hasattr(self, 'viewPortL'):
            return
        
        button = self.sender()
        checked = button.isChecked()
        for view in self.viewPortL.values():
            view.SetFocusMode(checked)
        
                
    def OnClickStepBack(self):
        style = self.styleList.get('drawContour')
        if style is not None:
            style.StepBack()
            self.UpdateView_L()
            #     self.btnStepNext.setEnabled(True)
            # else:
            #     self.btnStepBack.setEnabled(False)
        
    def OnClickStepNext(self):
        style = self.styleList.get('drawContour')
        if style is not None:
            style.StepNext()
            self.UpdateView_L()
            #     self.btnStepBack.setEnabled(True)
            # else:
            #     self.btnStepNext.setEnabled(False)
                
    def OnClickBtnCutIn(self):
        if self.btnCutIn.isChecked():
            for button in self.buttonGroup['imageFunction']:
                if button != self.btnCutIn:
                    button.setChecked(False)
           
            style = self.styleList.get('drawContour')        
            if style is not None:
                style.ResumeRendererStyle()
                
            imageFunction = SegmentationFunction()
            imageFunction.SetInputData(self.currentRenderer.image)
            
            style = InteractorStyleSegmentation(self.currentRenderer)
            style.CallbackSetOutRange(self.OnSignalOutRange)
            style.SetInput(imageFunction)
            style.CallbackUpdateView(self.UpdateView_L)
            
            if self.currentRenderer.orientation == VIEW_3D:
                style.SetActor(self.currentRenderer.volume)
            else:
                style.SetActor(self.currentRenderer.actorImage)
            # self.currentStyle = style
            self.styleList['drawContour'] = style
            self.currentStyle = style
                
            # else:
            #     style.SetModeCutIn()
            #     style.StartInteractor(self.currentRenderer)
                # style.CutInside()
        else:
            self.styleList['drawContour'].EndInteractor(True)
            del self.styleList['drawContour']
            self.ResetVolumeEditUI()
            self.currentStyle = None
            
        self.UpdateView_L()
        
       
        
    def OnClickBtnCutOut(self):
        
        if self.btnCutOut.isChecked():
            for button in self.buttonGroup['imageFunction']:
                if button != self.btnCutOut:
                    button.setChecked(False)
                    
            style = self.styleList.get('drawContour')
            
            if style is not None:
                style.ResumeRendererStyle()
                
            imageFunction = SegmentationFunction()
            imageFunction.SetInputData(self.currentRenderer.image)
            
            style = InteractorStyleSegmentation(self.currentRenderer)
            style.CallbackSetOutRange(self.OnSignalOutRange)
            style.SetInput(imageFunction)
            style.SetModeCutOut()
            style.CallbackUpdateView(self.UpdateView_L)
            
            if self.currentRenderer.orientation == VIEW_3D:
                style.SetActor(self.currentRenderer.volume)
            else:
                style.SetActor(self.currentRenderer.actorImage)
                
            self.styleList['drawContour'] = style
            self.currentStyle = style
            # else:
            #     style.SetModeCutOut()
            #     style.StartInteractor(self.currentRenderer)
                # style.CutOutside()
        else:
            self.styleList['drawContour'].EndInteractor(True)
            del self.styleList['drawContour']
            self.ResetVolumeEditUI()
            self.currentStyle = None
            
        self.UpdateView_L() 
            
    def OnClick_Button_ResetImage(self):
        if hasattr(self, 'viewPortL'):
            # for view in self.viewPortL.values():
            #     view.renderer.ResetImage()
            self.viewPortL['LT'].renderer.ResetImage()
            
        style = self.styleList.get('drawContour')
        
        if style:
            style.ResetImage(self.viewPortL['LT'].renderer.image)
            
        self.UpdateView_L()
        self.ResetVolumeEditUI()
        
    def OnClick_Button_InverseImage(self):
        style = self.styleList.get('drawContour')
        if style:
            style.Inverse()
            self.UpdateView_L()
        
    def ResetVolumeEditUI(self):
        self.btnStepBack.setEnabled(False)
        self.btnStepNext.setEnabled(False)
            
    def OnClick_Button_ToEntryL(self):
        entryPoint = self.dicomLow.entryPoint
        if entryPoint is not None:
            bHasCrossSection = False
            for view in self.viewPortL.values():
                if view.orientation == VIEW_AXIAL or \
                    view.orientation == VIEW_CORONAL or \
                    view.orientation == VIEW_SAGITTAL:
                        
                    view.MapPositionToImageSlice(entryPoint)
                    if bHasCrossSection == True:
                        break
                elif view.orientation == VIEW_CROSS_SECTION:
                    bHasCrossSection = True
                    view.uiScrollSlice.blockSignals(True)
                    view.uiScrollSlice.setValue(view.uiScrollSlice.maximum())
                    view.uiScrollSlice.blockSignals(False)
                
    def OnClick_Button_ToTargetL(self):
        targetPoint = self.dicomLow.targetPoint
        if targetPoint is not None:
            bHasCrossSection = False
            for view in self.viewPortL.values():
                if view.orientation == VIEW_AXIAL or \
                    view.orientation == VIEW_CORONAL or \
                    view.orientation == VIEW_SAGITTAL:
                        
                    view.MapPositionToImageSlice(targetPoint)
                    if bHasCrossSection == True:
                        break
                elif view.orientation == VIEW_CROSS_SECTION:
                    bHasCrossSection = True
                    view.uiScrollSlice.blockSignals(True)
                    view.uiScrollSlice.setValue(0)
                    view.uiScrollSlice.blockSignals(False)
                    
    def OnClick_Button_ToEntryH(self):
        entryPoint = self.dicomHigh.entryPoint
        if entryPoint is not None:
            bHasCrossSection = False
            for view in self.viewPortH.values():
                if view.orientation == VIEW_AXIAL or \
                    view.orientation == VIEW_CORONAL or \
                    view.orientation == VIEW_SAGITTAL:
                        
                    view.MapPositionToImageSlice(entryPoint)
                    if bHasCrossSection == True:
                        break
                elif view.orientation == VIEW_CROSS_SECTION:
                    bHasCrossSection = True
                    view.uiScrollSlice.blockSignals(True)
                    view.uiScrollSlice.setValue(view.uiScrollSlice.maximum())
                    view.uiScrollSlice.blockSignals(False)
                
    def OnClick_Button_ToTargetH(self):
        targetPoint = self.dicomHigh.targetPoint
        if targetPoint is not None:
            bHasCrossSection = False
            for view in self.viewPortH.values():
                if view.orientation == VIEW_AXIAL or \
                    view.orientation == VIEW_CORONAL or \
                    view.orientation == VIEW_SAGITTAL:
                        
                    view.MapPositionToImageSlice(targetPoint)
                    if bHasCrossSection == True:
                        break
                elif view.orientation == VIEW_CROSS_SECTION:
                    bHasCrossSection = True
                    view.uiScrollSlice.blockSignals(True)
                    view.uiScrollSlice.setValue(0)
                    view.uiScrollSlice.blockSignals(False)
    
    def OnChangeIndex_ViewSelect(self, viewName):
        
        senderObj = self.sender()
        
        widget   = None
        for view in self.viewPortL.values():
            if view.uiCbxOrientation == senderObj:
                widget = view.vtkWidget
            
                if widget is not None:
                    #remove old renderer
                    renderWindow = widget.GetRenderWindow()
                    iren = renderWindow.GetInteractor()
                
                    viewName = viewName.split()[0]

                    #檢查該視窗是否已存在，若是則交換
                    bExist = False
                    for existView in self.viewPortL.values():
                        if existView.orientation == viewName:
                            bExist = True
                            break
                        
                    if bExist == True:
                        view.Swap(existView)
                    else:
                        
                        view.SetViewPort(viewName, self.dicomLow.rendererList[viewName])
                        
                        iStyle = MyInteractorStyle(self, viewName)
                        iStyle.signalObject.ConnectUpdateHU(self.UpdateHU_L)
                        iStyle.signalObject.ConnectGetRenderer(self.GetCurrentRendererCallback)
                        
                        iren.SetInteractorStyle(iStyle)
                        iren.Initialize()
                        iren.Start()
                    
        
    def OnChangeIndex_ViewSelect_H(self, viewName):
        senderObj = self.sender()
        
        widget   = None
        for view in self.viewPortH.values():
            if view.uiCbxOrientation == senderObj:
                widget = view.vtkWidget
            
                if widget is not None:
                    #remove old renderer
                    renderWindow = widget.GetRenderWindow()
                    iren = renderWindow.GetInteractor()
                
                    viewName = viewName.split()[0]

                    #檢查該視窗是否已存在，若是則交換
                    bExist = False
                    for existView in self.viewPortH.values():
                        if existView.orientation == viewName:
                            bExist = True
                            break
                        
                    if bExist == True:
                        view.Swap(existView)
                    else:
                        
                        view.SetViewPort(viewName, self.dicomHigh.rendererList[viewName])
                        iren.SetInteractorStyle(MyInteractorStyle(self, viewName))
                            
                        iren.Initialize()
                        iren.Start()

    def closeEvent(self, event):
        print("close~~~~~~~~")
        try:
            ## 移除VTK道具 ############################################################################################
            # self.irenSagittal_L.RemoveAllViewProps() 
            if hasattr(self.dicomLow, 'rendererSagittal'):
                self.dicomLow.rendererSagittal.RemoveAllViewProps()
                
            if hasattr(self.dicomLow, 'rendererCoronal'):
                self.dicomLow.rendererCoronal.RemoveAllViewProps()
                
            if hasattr(self.dicomLow, 'rendererAxial'):
                self.dicomLow.rendererAxial.RemoveAllViewProps()
                
            if hasattr(self.dicomLow, 'renderer3D'):
                self.dicomLow.renderer3D.RemoveAllViewProps()
                
            ############################################################################################
            ## 關閉VTK Widget ############################################################################################
            # self.irenSagittal_L.close()
            self.qvtkWidget_Sagittal_L.close()
            self.qvtkWidget_Coronal_L.close()
            self.qvtkWidget_Axial_L.close()
            self.qvtkWidget_3D_L.close()
            ############################################################################################
            print("remove dicomLow VTk success")
        except Exception as e:
            print(e)
            print("remove dicomLow VTk error")
        try:
            ## 移除VTK道具 ############################################################################################
            if hasattr(self.dicomHigh, 'rendererSagittal'):
                self.dicomHigh.rendererSagittal.RemoveAllViewProps()
                
            if hasattr(self.dicomHigh, 'rendererCoronal'):
                self.dicomHigh.rendererCoronal.RemoveAllViewProps()
                
            if hasattr(self.dicomHigh, 'rendererAxial'):
                self.dicomHigh.rendererAxial.RemoveAllViewProps()
                
            if hasattr(self.dicomHigh, 'renderer3D'):
                self.dicomHigh.renderer3D.RemoveAllViewProps()
                
                 
            
            ############################################################################################
            ## 關閉VTK Widget ############################################################################################
            
            self.qvtkWidget_Sagittal_H.close()
            self.qvtkWidget_Coronal_H.close()
            self.qvtkWidget_Axial_H.close()
            self.qvtkWidget_3D_H.close()
            
            ############################################################################################
            print("remove dicomHigh VTk success")
        except Exception as e:
            print(e)
            print("remove dicomHigh VTk error")
        try:
            ## 接受關閉事件 ############################################################################################
            event.accept()
            ############################################################################################
        except Exception as e:
            print(e)
    
    def HomeProcessing(self):
        MOTORSUBFUNCTION.HomeProcessing(self)
        print("Home processing is done!")
        QMessageBox.information(self, "information", "Home processing is done!")
        self.homeStatus = True

    def RobotRun(self):
        if self.homeStatus is True:
            MOTORSUBFUNCTION.P2P(self)
            print("Robot run processing is done!")
            QMessageBox.information(self, "information", "Robot run processing is done!")
        else:
            print("Please execute home processing first.")
            QMessageBox.information(self, "information", "Please execute home processing first.")
        
    def LaserAdjustment(self):
        while self.showLaserProfileCommand:
            self.laserProfileFigure.update_figure(self.PlotProfile())
        print("Laser Adjust Done!")
        
        # with open('laser_output1.txt', mode='w') as f:
        #     f.write(receiveDataTemp)
            
               # LineLaser.CloseLaser(self)
            
    def ShowLaserProfile(self):
        self.Button_StartLaserDisplay.setStyleSheet("background-color:#4DE680")
        self.Button_StopLaserDisplay.setEnabled(True)
        self.laserProfileFigure = Canvas(self,dpi=200)
        self.layout = QtWidgets.QVBoxLayout(self.MplWidget)
        self.layout.addWidget(self.laserProfileFigure)
        self.showLaserProfileCommand = True
        t = threading.Thread(target=self.LaserAdjustment)
        t.start()
        
    def StopLaserProfile(self):
        if self.Button_StopLaserDisplay.isChecked():
            self.Button_StopLaserDisplay.setStyleSheet("background-color:#4DE680")
            self.Button_StartLaserDisplay.setStyleSheet("")
            self.Button_StartLaserDisplay.setEnabled(False)
            self.Button_RecordCycle.setEnabled(True)
            self.showLaserProfileCommand  = False
        self.Button_StopLaserDisplay.setChecked(False)
        

                        
    def RecordBreathing(self):
        receiveDataTemp = []
        receiveData = []
        # self.TriggerSetting()
        print("Cheast Breathing Measure Start")
        while self.recordBreathingCommand is True:
            receiveDataTemp.append(self.ModelBuilding())
            self.laserProfileFigure.update_figure(self.PlotProfile())
            self.recordBreathingBase = True
        print("Breathing recording stopped.")
        
        
        
        receiveDataTemp = [subarray for subarray in receiveDataTemp if subarray]
        # rearrange receiveData
        for item in receiveDataTemp:
            receiveData.append(item[0]) 
        self.DataBaseChecking(receiveData) # make sure no data lost
        self.DataRearrange(receiveData, self.yellowLightCriteria, self.greenLightCriteria) 
    
    def StartRecordBreathingBase(self):
        self.Button_StopLaserDisplay.setEnabled(False)
        self.Button_StopRecording.setEnabled(True)
        self.Button_StopLaserDisplay.setStyleSheet("")
        self.Button_RecordCycle.setStyleSheet("background-color:#4DE680")
        self.recordBreathingBase = False
        self.recordBreathingCommand = True
        
        t = threading.Thread(target = self.RecordBreathing)
        t.start()
        
    def StopRecordBreathingBase(self):
        print("Stop")
        if self.Button_StopRecording.isChecked():
            self.Button_RecordCycle.setStyleSheet("")
            self.Button_StopRecording.setStyleSheet("background-color:#4DE680")
            self.Button_StartTracking.setEnabled(True)
            self.Button_Accuracy.setEnabled(True)
            self.recordBreathingCommand = False
            self.Button_StopRecording.setChecked(False)
            self.tabWidget.setCurrentWidget(self.tabWidget_Low)
        else:
            self.recordBreathingCommand = True
            
        # with open('laser_output.txt', mode='a', encoding='utf-8') as f:
        #     f.write(receiveData[0])
        print("Stop Breathing Recording")
        
    def callbackFunc(self, caller, eventId):
        tracerWidget = self.tracer
        if not tracerWidget.IsClosed():
            print('not close!')
            return
        path = vtk.vtkPolyData()
        
        tracerWidget.GetPath(path)
        print(f'path has {path.GetNumberOfPoints()} points')
        
        
    def keyPressEvent(self, event):
        
        if event.key() == Qt.Key_E:
            with open('AVG_data.txt', mode='r') as f:
                strData = f.read()
                avgData = strData.split(',')
                avgData = [data for data in avgData if data != '']
            
            sim_laser = threading.Thread(target = self.Sim_LaserTracking, args = [avgData])
            sim_laser.start()
        elif event.key() == Qt.Key_C:
            plane = vtk.vtkPlane()
            plane.SetOrigin(250, 250, 130)
            plane.SetNormal(1, 0, 0)
            
            # cutter = vtk.vtkCutter()
            image = self.viewPortL['LT'].renderer.image
            # cutter.SetInputData(volume)
            # cutter.SetCutFunction(plane)
            
            iren = self.viewPortL['LT'].vtkWidget.GetRenderWindow().GetInteractor()
            # iren.SetInteractorStyle(InteractorStylePlaneWidget())
            
            pWidget = vtkWidgetCall(self.viewPortL['LT'].renderer.volume, self.viewPortL['LT'].renderer, self.viewPortL['LT'].iren, self.dicomLow.windowLevelLookup)
            
            pWidget.SetInteractor(iren)
            pWidget.SetInputData(image)
            pWidget.SetResolution(10)
            pWidget.GetPlaneProperty().SetColor(0.9, 0.4, 0.4)
            pWidget.GetHandleProperty().SetColor(0, 0.4, 0.7)
            pWidget.GetHandleProperty().SetLineWidth(1.5)
            
            # pWidget.NormalToZAxisOn()
            # pWidget.SetRepresentationToSurface()
            pWidget.SetRepresentationToOff()
            pWidget.SetPlaceFactor(1.0)
            pWidget.PlaceWidget()
            pWidget.On()
            
            pWidget.SetNormal(0, 0, 1)
            
            iren.Initialize()
            iren.Start()
           
            self.tmpWidget = pWidget
            
            
            # self.tmpData = clipper
            
            # mapper = self.viewPortL['LT'].renderer.volume.GetMapper()
            # mapper.SetInputConnection(clipper.GetOutputPort())
            
            
        
            # self.viewPortL['LT'].iren.SetInteractorStyle(self.styleTmp.originalStyle)
            # print('press ESC')

    def Sim_LaserTracking(self, data):
        index = 0
        print(f'len = {len(data)}')
        while index < len(data):
            
            value = float(data[index])
            index += 1
            self.breathingRatio.display(value)
        
            if value is not None:
                if self.greenLightCriteria is not None and self.yellowLightCriteria is not None:
                    if value >= self.greenLightCriteria:  #綠燈
                        self.breathingRatio.setStyleSheet("border: 2px solid black; color: green; background: silver;")
                    elif value >= self.yellowLightCriteria and value < self.greenLightCriteria: #黃燈
                        self.breathingRatio.setStyleSheet("border: 2px solid black; color: yellow; background: silver;")
                    else:
                        self.breathingRatio.setStyleSheet("border: 2px solid black; color: red; background: silver;")
            sleep(0.1)
                
        
    def Fun_LaserTracking(self):
        self.avgValueDataTmp = []
        
        while self.trackingBreathingCommand is True:
            breathingPercentageTemp = self.RealTimeHeightAvg(self.yellowLightCriteria, self.greenLightCriteria) #透過計算出即時的HeightAvg, 顯示燈號
            
            self.breathingRatio.display(breathingPercentageTemp)
            
            if breathingPercentageTemp is not None:
                if self.greenLightCriteria is not None and self.yellowLightCriteria is not None:
                    if breathingPercentageTemp >= self.greenLightCriteria:  #綠燈
                        self.breathingRatio.setStyleSheet("border: 2px solid black; color: green; background: silver;")
                    elif breathingPercentageTemp >= self.yellowLightCriteria and breathingPercentageTemp < self.greenLightCriteria: #黃燈
                        self.breathingRatio.setStyleSheet("border: 2px solid black; color: yellow; background: silver;")
                    else:
                        self.breathingRatio.setStyleSheet("border: 2px solid black; color: red; background: silver;")
                        
                self.laserProfileFigure.update_figure(self.PlotProfile())
                
                self.avgValueDataTmp.append(breathingPercentageTemp)
                
                if type(breathingPercentageTemp) is np.float64:
                    self.breathingPercentage = breathingPercentageTemp                
                    print(self.breathingPercentage)
        with open('AVG_data.txt', mode='w') as f:
            for data in self.avgValueDataTmp:
                f.write(f'{data},')
                
    def AdjustTrackingAccuracy(self):
        self.Button_Accuracy.setStyleSheet("background-color:#0066FF")
        self.yellowLightCriteria = yellowLightCriteria_HighAccuracy
        self.greenLightCriteria = greenLightCriteria_HighAccuracy
            
    def LaserTracking(self):
        print("即時量測呼吸狀態")
        if self.recordBreathingBase is True:
            self.Button_StopRecording.setStyleSheet("")
            self.Button_StartTracking.setStyleSheet("background-color:#4DE680")
            
            self.Button_StopLaserTracking.setStyleSheet("")
            self.Button_StopLaserTracking.setEnabled(True)
            self.trackingBreathingCommand = True
            
            t_laser = threading.Thread(target = self.Fun_LaserTracking)
            t_laser.start()
        else:
            print("Please build cheast breathing model first.")
            
    def StopLaserTracking(self):
        if self.Button_StopLaserTracking.isChecked():
            self.Button_StartTracking.setStyleSheet("")
            self.Button_StopLaserTracking.setStyleSheet("background-color:#4DE680")
            self.trackingBreathingCommand = False
            self.Button_StopLaserTracking.setChecked(False)
            try:
                self.RealTimeTracking(self.breathingPercentage)
                self.MoveToPoint()
            except:
                print("Robot Compensation error")
        else:
            self.trackingBreathingCommand = True

    def StringSplit(self, string):
        stringTemp = string.split(",")
        dataTemp = []
        for i in range(3):
            dataTemp.append(stringTemp[i])
        return dataTemp

    def RobotAutoRun(self):
        entryPointReturn = str(self.lineEdit_EntryPoint_RCA.text())
        targetPointReturn = str(self.lineEdit_TargetPoint_RCA.text())
        "decouple string"
        entryPointReturn = self.StringSplit(entryPointReturn)
        targetPointReturn = self.StringSplit(targetPointReturn)
        if len(entryPointReturn) == 3 and len(targetPointReturn) == 3:
            MOTORSUBFUNCTION.P2P_Manual(
                self, entryPointReturn, targetPointReturn)
        else:
            print("point typing error, check your points again.")

    def RobotCycleRun(self):
        point1 = self.lineEdit_Point_1_RCA.text()
        point2 = self.lineEdit_Point_2_RCA.text()
        point3 = self.lineEdit_Point_3_RCA.text()
        point4 = self.lineEdit_Point_4_RCA.text()
        cycleTimes = self.lineEdit_CycleTimes_RCA.text()
        "decople string"
        point1 = self.StringSplit(point1)
        point2 = self.StringSplit(point2)
        point3 = self.StringSplit(point3)
        point4 = self.StringSplit(point4)
        MOTORSUBFUNCTION.CycleRun(
            self, point1, point2, point3, point4, int(cycleTimes))
            
    def CloseRobotSystem(self):
        MOTORSUBFUNCTION.HomeProcessing(self)
        print("Home processing is done!")
        QMessageBox.information(self, "information", "AitherBot will be closed!")
        os.system("shutdown -s -t 0 ")


    def _init_log(self):
        ## log設定 ############################################################################################
        self.logUI: logging.Logger = logging.getLogger(name='UI')
        self.logUI.setLevel(logging.INFO)
        "set log level"
        # self.log_INFO: logging.Logger = logging.getLogger(name='INFO')
        # self.log_INFO.setLevel(logging.DEBUG)

        handler: logging.StreamHandler = logging.StreamHandler()
        handler: logging.StreamHandler = logging.FileHandler('my.log', 'w', 'utf-8')

        formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.logUI.addHandler(handler)
        ############################################################################################

    def _init_ui(self):
        ## initial ui ############################################################################################
        "DICOM planning ui disable"
        self.Button_Planning.setEnabled(False)

        "DICOM Low ui disable (turn on after the function is enabled)"
        self.Button_Registration_L.setEnabled(False)
        self.Button_ShowRegistration_L.setEnabled(False)
        self.comboBox_L.setEnabled(False)
        # self.Button_SetPoint_L.setEnabled(False)
        self.Button_ShowPoint_L.setEnabled(False)

        self.Slider_WW_L.setEnabled(False)
        self.Slider_WL_L.setEnabled(False)
        self.SliceSelect_Axial_L.setEnabled(False)
        self.SliceSelect_Sagittal_L.setEnabled(False)
        self.SliceSelect_Coronal_L.setEnabled(False)

        "DICOM High ui disable (turn on after the function is enabled)"
        self.Button_Registration_H.setEnabled(False)
        self.Button_ShowRegistration_H.setEnabled(False)
        self.comboBox_H.setEnabled(False)
        # self.Button_SetPoint_H.setEnabled(False)
        self.Button_ShowPoint_H.setEnabled(False)

        self.Slider_WW_H.setEnabled(False)
        self.Slider_WL_H.setEnabled(False)
        self.SliceSelect_Axial_H.setEnabled(False)
        self.SliceSelect_Sagittal_H.setEnabled(False)
        self.SliceSelect_Coronal_H.setEnabled(False)
        
        self.indexOfTabWidget = self.tabWidget.currentIndex()
        
        # self.btnGroupImageFunction.buttonToggled.connect(self.OnToggleImageFunc)
        self.buttonGroup = {}
        imageFunction = []
        imageFunction.append(self.btnCutIn)
        imageFunction.append(self.btnCutOut)
        self.buttonGroup['imageFunction'] = imageFunction
        
        
        self.btnCutIn.clicked.connect(self.OnClickBtnCutIn)
        self.btnCutOut.clicked.connect(self.OnClickBtnCutOut)
        
        self.btnStepBack.clicked.connect(self.OnClickStepBack)
        self.btnStepNext.clicked.connect(self.OnClickStepNext)
        self.btnStepBack.setEnabled(False)
        self.btnStepNext.setEnabled(False)
        
        self.btnResetImage.clicked.connect(self.OnClick_Button_ResetImage)
        self.btnInverse.clicked.connect(self.OnClick_Button_InverseImage)
        
        self.btnFocusMode.clicked.connect(self.OnClick_Button_FocusMode)
        
        
        self.btnEnableClipper.clicked.connect(self.OnClick_Button_EnableClipper)
        self.btnClipperXY.clicked.connect(self.OnClick_Button_ClipperXY)
        self.btnClipperXZ.clicked.connect(self.OnClick_Button_ClipperXZ)
        self.btnClipperYZ.clicked.connect(self.OnClick_Button_ClipperYZ)
        
        self.btnShowTarget.clicked.connect(self.onClick_Button_ShowTarget)
        
        # create toolbox
        _translate = QtCore.QCoreApplication.translate
        self.btnFullView = {}
        # Left Top View
        fullView = QPushButton(self.qvtkWidget_3D_L)
        fullView.setText(_translate("MainWindow", "Full"))
        fullView.setObjectName("btnFullViewLT")
        
        layout = QHBoxLayout()
        layout.addStretch(1)
        layout.addWidget(fullView)
        
        layoutInVTK = QVBoxLayout(self.qvtkWidget_3D_L)
        layoutInVTK.addStretch(1)
        layoutInVTK.addLayout(layout)
        
        self.btnFullView['LT'] = fullView
        
        # Right Top View
        fullView = QPushButton(self.qvtkWidget_Axial_L)
        fullView.setText(_translate("MainWindow", "Full"))
        fullView.setObjectName("btnFullViewRT")
        
        layout = QHBoxLayout()
        layout.addStretch(1)
        layout.addWidget(fullView)
        
        layoutInVTK = QVBoxLayout(self.qvtkWidget_Axial_L)
        layoutInVTK.addStretch(1)
        layoutInVTK.addLayout(layout)
        
        self.btnFullView['RT'] = fullView
        
        # Left Bottom View
        fullView = QPushButton(self.qvtkWidget_Sagittal_L)
        fullView.setText(_translate("MainWindow", "Full"))
        fullView.setObjectName("btnFullViewLB")
        
        layout = QHBoxLayout()
        layout.addStretch(1)
        layout.addWidget(fullView)
        
        layoutInVTK = QVBoxLayout(self.qvtkWidget_Sagittal_L)
        layoutInVTK.addStretch(1)
        layoutInVTK.addLayout(layout)
        
        self.btnFullView['LB'] = fullView
        
        # Left Bottom View
        fullView = QPushButton(self.qvtkWidget_Coronal_L)
        fullView.setText(_translate("MainWindow", "Full"))
        fullView.setObjectName("btnFullViewRB")
        
        layout = QHBoxLayout()
        layout.addStretch(1)
        layout.addWidget(fullView)
        
        layoutInVTK = QVBoxLayout(self.qvtkWidget_Coronal_L)
        layoutInVTK.addStretch(1)
        layoutInVTK.addLayout(layout)
        
        self.btnFullView['RB'] = fullView
        
        # # Left Bottom View
        # fullView = QPushButton(self.qvtkFullView)
        # fullView.setText(_translate("MainWindow", "Full"))
        # fullView.setObjectName("btnFullView")
        
        # layout = QHBoxLayout()
        # layout.addStretch(1)
        # layout.addWidget(fullView)
        
        # layoutInVTK = QVBoxLayout(self.qvtkFullView)
        # layoutInVTK.addStretch(1)
        # layoutInVTK.addLayout(layout)
        
        # self.btnFullView['Full'] = fullView
        
        for button in self.btnFullView.values():
            button.clicked.connect(self.OnClick_Button_FullView)

        "Navigation Robot ui disable (turn on after the function is enabled)"
        # self.Button_RobotHome.setEnabled(False)
        # self.Button_RobotAutoRun.setEnabled(False)

        ############################################################################################
        
    

    def ImportDicom_L(self):
        """load inhale (Low breath) DICOM to get image array and metadata
        """
        ## 開啟視窗選取資料夾 ############################################################################################
        self.logUI.info('Import Dicom inhale/_Low')
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setFilter(QDir.Files)

        if dlg.exec_():
            filePath = dlg.selectedFiles()[0] + '/'
        else:
            return
        ############################################################################################
        
        self.ui_SP = SystemProcessing()
        
        # self.ui_SP.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.ui_SP.show()
        QApplication.processEvents()
        
        self.dcmFn.signalProcess.connect(self.ui_SP.UpdateProgress)
        self.signalProgress.connect(self.ui_SP.UpdateProgress)
        self.dicomLow.signalProgress.connect(self.ui_SP.UpdateProgress)
        ## load dicom files ############################################################################################
        "pydicom stage"
        # metadata, metadataSeriesNum, filePathList = self.dcmFn.LoadPath(filePath)
        filePathList = self.dcmFn.LoadPath(filePath)
        # print(f'metadata = {metadata}')
        # print(f'metadataSeriesNum = {metadataSeriesNum}')
        # print(f'filePathList = {filePathList}')
        # if metadata == 0 or metadataSeriesNum == 0:
        #     self.ui_SP.close()
        #     QMessageBox.critical(self, "error", "please load one DICOM")
        #     self.logUI.info('not loading one DICOM')
        #     return
        print("-------------------------------------------------------------------")
        print("load inhale/Low DICOM path:")
        print(filePath)
        print("-------------------------------------------------------------------")
        logStr = 'Load inhale/Low Dicom: ' + filePath
        self.logUI.info(logStr)
        ############################################################################################
        ## 清除殘留的VTK ############################################################################################
        "reset VTK"
        if self.dcmTagLow.get("imageTag") != []:
            self.dicomLow.Reset()
            self.ResetUI('low')
            # "render"
            # "Sagittal"
            # self.dicomLow.rendererSagittal.RemoveActor(self.dicomLow.actorSagittal)
            # "Coronal"
            # self.dicomLow.rendererCoronal.RemoveActor(self.dicomLow.actorCoronal)
            # "Axial"
            # self.dicomLow.rendererAxial.RemoveActor(self.dicomLow.actorAxial)
            # "3D"
            # self.dicomLow.renderer3D.RemoveActor(self.dicomLow.actorSagittal)
            # self.dicomLow.renderer3D.RemoveActor(self.dicomLow.actorAxial)
            # self.dicomLow.renderer3D.RemoveActor(self.dicomLow.actorCoronal)
            
            # self.dicomLow.rendererSagittal.RemoveActor(self.dicomLow.actorPointEntry)
            
            # self.irenSagittal_L.Initialize()
            # self.irenCoronal_L.Initialize()
            # self.irenAxial_L.Initialize()
            # self.iren3D_L.Initialize()
            
            # self.irenSagittal_L.Start()
            # self.irenCoronal_L.Start()
            # self.irenAxial_L.Start()
            # self.iren3D_L.Start()
            # self.dicomLow.UpdateView()
        ############################################################################################
        ## reset dicom 資料 ############################################################################################
        "reset dcm"
        self.dcmTagLow = {}
        self.dcmTagLow.update({"ww": 1})
        self.dcmTagLow.update({"wl": 1})
        self.dcmTagLow.update({"imageTag": []})
        "registration ball"
        # self.dcmTagLow.update({"selectedBall": []})
        self.dcmTagLow.update({"regBall": []})
        self.dcmTagLow.update({"flageSelectedBall": False})
        self.dcmTagLow.update({"candidateBall": []})
        self.dcmTagLow.update({"selectedBallKey": []})
        "set point"
        self.dcmTagLow.update({"selectedPoint": []})
        self.dcmTagLow.update({"flageSelectedPoint": False})
        self.dcmTagLow.update({"flageShowPointButton": False})
        "show point"
        # self.dcmTagLow.update({"sectionTag":[]})
        "ui disable"
        self.label_Error_L.setText('Registration difference: mm')
        self.Button_Planning.setEnabled(False)
        self.Button_Registration_L.setEnabled(False)
        self.Button_ShowRegistration_L.setEnabled(False)
        self.comboBox_L.setEnabled(False)
        # self.Button_SetPoint_L.setEnabled(False)
        self.Button_ShowPoint_L.setEnabled(False)
        # self.Button_RobotHome.setEnabled(False)
        # self.Button_RobotAutoRun.setEnabled(False)
        ############################################################################################
        ## 依照 series 排序 dicom ############################################################################################
        # seriesNumberLabel, dicDICOM, dirDICOM = self.dcmFn.SeriesSort(metadata, metadataSeriesNum, filePathList)
        ############################################################################################
        ## 讀取要的 dicom files ############################################################################################
        # imageTag, folderDir = self.dcmFn.ReadDicom(seriesNumberLabel, dicDICOM, dirDICOM)
        ############################################################################################
        ## 儲存 dicom 的 tag ############################################################################################
        # self.dcmTagLow.update({"imageTag": imageTag})
        ############################################################################################
        ## 儲存影像 ############################################################################################
        # image = self.dcmFn.GetImage(self.dcmTagLow.get("imageTag"))
        ############################################################################################
        ## 如果 load 大於一組影像，跳提示 ############################################################################################
        
        # if image != 0:
        #     self.dcmTagLow.update({"image": np.array(image)})
        # else:
        # self.ui_SP.close()
        # QMessageBox.critical(self, "error", "please load one DICOM")
        # self.logUI.warning('fail to get image')
        # return
        ############################################################################################
        ## 儲存 dicom 影像基本資料 ############################################################################################
        rescaleSlope = self.dcmTagLow.get("imageTag")[0].RescaleSlope
        rescaleIntercept = self.dcmTagLow.get("imageTag")[0].RescaleIntercept
        self.dcmTagLow.update({"imageHu": np.array(self.dcmFn.Transfer2Hu(self.dcmTagLow.get("image"), rescaleSlope, rescaleIntercept))})
        self.dcmTagLow.update({"pixel2Mm": self.dcmFn.GetPixel2Mm(self.dcmTagLow.get("imageTag")[0])})
        self.dcmTagLow.update({"imageHuMm": np.array(self.dcmFn.ImgTransfer2Mm(self.dcmTagLow.get("imageHu"), self.dcmTagLow.get("pixel2Mm")))})
        patientPosition = self.dcmTagLow.get("imageTag")[0].PatientPosition
        
        
        
        ############################################################################################
        ## 用 VTK 顯示 + 儲存 VT形式的影像 ############################################################################################
        "VTK stage"
        print(f'folder = {folderDir}')
        self.dcmTagLow.update({"folderDir":folderDir})
        imageVTKHu = self.dicomLow.LoadImage(folderDir)
        self.dcmTagLow.update({"imageVTKHu":imageVTKHu})
        # self.dicomLow.CreateActorAndRender(int((self.dicomLow.imageDimensions[0])/2))
        
        # if not hasattr(self, 'irenSagittal_L'):
        #     self.irenSagittal_L = self.qvtkWidget_Sagittal_L.GetRenderWindow().GetInteractor()
        #     self.irenCoronal_L = self.qvtkWidget_Coronal_L.GetRenderWindow().GetInteractor()
        #     self.irenAxial_L = self.qvtkWidget_Axial_L.GetRenderWindow().GetInteractor()
        #     self.iren3D_L = self.qvtkWidget_3D_L.GetRenderWindow().GetInteractor()
        #     self.dicomLow.irenList["sagittal"] = self.irenSagittal_L
        #     self.dicomLow.irenList["coronal"] = self.irenCoronal_L
        #     self.dicomLow.irenList["axial"] = self.irenAxial_L
        #     self.dicomLow.irenList["3D"] = self.iren3D_L
        
            
        ############################################################################################
        ## 設定 UI 初始值 ############################################################################################
        # self.SliceSelect_Sagittal_L.setMinimum(0)
        # self.SliceSelect_Sagittal_L.setMaximum(self.dicomLow.imageDimensions[0] - 1)
        # self.SliceSelect_Sagittal_L.setValue(int((self.dicomLow.imageDimensions[0])/2))
        # self.SliceSelect_Coronal_L.setMinimum(0)
        # self.SliceSelect_Coronal_L.setMaximum(self.dicomLow.imageDimensions[1] - 1)
        # self.SliceSelect_Coronal_L.setValue(int((self.dicomLow.imageDimensions[1])/2))
        
        
        # self.SliceSelect_Axial_L.setMinimum(0)
        # self.SliceSelect_Axial_L.setMaximum(5)
        # self.SliceSelect_Axial_L.setValue(0)
        # self.SliceSelect_Axial_L.setMinimum(0)
        # self.SliceSelect_Axial_L.setMaximum(self.dicomLow.imageDimensions[2] - 1)
        # self.SliceSelect_Axial_L.setValue(int((self.dicomLow.imageDimensions[2])/2))
        
        ############################################################################################
        ## 設定 window width 和 window level 初始值 ############################################################################################
        ### 公式1
        thresholdValue = int(((self.dicomLow.dicomGrayscaleRange[1] - self.dicomLow.dicomGrayscaleRange[0]) / 6) + self.dicomLow.dicomGrayscaleRange[0])
        "WindowWidth"
        self.Slider_WW_L.setMinimum(0)
        self.Slider_WW_L.setMaximum(int(abs(self.dicomLow.dicomGrayscaleRange[0]) + self.dicomLow.dicomGrayscaleRange[1]))
        self.dcmTagLow.update({"ww": abs(thresholdValue*2)})
        self.Slider_WW_L.setValue(self.dcmTagLow.get("ww"))
        "WindowCenter / WindowLevel"
        self.Slider_WL_L.setMinimum(int(self.dicomLow.dicomGrayscaleRange[0]))
        self.Slider_WL_L.setMaximum(int(self.dicomLow.dicomGrayscaleRange[1]))
        self.dcmTagLow.update({"wl": thresholdValue})
        self.Slider_WL_L.setValue(self.dcmTagLow.get("wl"))
        ############################################################################################
        self.logUI.debug('Loaded inhale/Low Dicom')
        ############################################################################################
        ## 顯示 dicom 到 ui 上 ############################################################################################
        self.ShowDicom_L()
        ## 啟用 ui ############################################################################################
        "Enable ui"
        self.Slider_WW_L.setEnabled(True)
        self.Slider_WL_L.setEnabled(True)
        self.SliceSelect_Axial_L.setEnabled(True)
        self.SliceSelect_Sagittal_L.setEnabled(True)
        self.SliceSelect_Coronal_L.setEnabled(True)
        self.Button_Registration_L.setEnabled(True)
        self.tabWidget.setCurrentWidget(self.tabWidget_Low)
        ############################################################################################
        self.ui_SP.close()
        return
    
    def SetSliceValue_L(self, iPos):
    
        self.lblSagittal.setText(f'{iPos[0]}')
        self.lblCoronal.setText(f'{iPos[1]}')
        self.lblAxial.setText(f'{iPos[2]}')
        
        
    def SetSliceValue_H(self, iPos):
        
        self.lblSagittal_H.setText(f'{iPos[0]}')
        self.lblCoronal_H.setText(f'{iPos[1]}')
        self.lblAxial_H.setText(f'{iPos[2]}')
       
                  

    def ShowDicom_L(self):
        """show low dicom to ui
        """
        ## 用 vtk 顯示 diocm ############################################################################################
        if self.viewPortL is not None:
            for view in self.viewPortL.values():
                view.Reset() 
                
        self.viewPortL = {}
        
        self.viewPortL["LT"] = ViewPortUnit(self, self.dicomLow, self.qvtkWidget_3D_L, '3D', self.SliceSelect_3D_L, self.cbxViewSelection1)
        self.viewPortL["RT"] = ViewPortUnit(self, self.dicomLow, self.qvtkWidget_Axial_L, 'Axial', self.SliceSelect_Axial_L, self.cbxViewSelection2)
        self.viewPortL["LB"] = ViewPortUnit(self, self.dicomLow, self.qvtkWidget_Sagittal_L, 'Sagittal', self.SliceSelect_Sagittal_L, self.cbxViewSelection3)
        self.viewPortL["RB"] = ViewPortUnit(self, self.dicomLow, self.qvtkWidget_Coronal_L, 'Coronal', self.SliceSelect_Coronal_L, self.cbxViewSelection4)
        self.syncInteractorStyle = SynchronInteractorStyle(self.viewPortL)
        
        # imageViewer = vtk.vtkImageViewer2()
        # imageViewer.SetInputData(self.dicomLow.vtkImage)
        # renderWindow = self.qvtkWidget_Axial_L.GetRenderWindow()
        # imageViewer.SetRenderWindow(renderWindow)
        # imageViewer.SetRenderer(self.dicomLow.rendererAxial)
        
        # iren = renderWindow.GetInteractor()
        # iren.SetInteractorStyle(MyInteractorStyle(self, VIEW_AXIAL))
        # imageViewer.SetupInteractor(iren)
        # imageViewer.SetSliceOrientationToXY()
        # imageViewer.Render()
        # iren.Start()
        # self.viewPortL["RT"] = imageViewer
        
        
        
        # imageViewer = vtk.vtkImageViewer2()
        # imageViewer.SetInputData(self.dicomLow.vtkImage)
        # renderWindow = self.qvtkWidget_Sagittal_L.GetRenderWindow()
        # imageViewer.SetRenderWindow(renderWindow)
        # imageViewer.SetRenderer(self.dicomLow.rendererSagittal)
        
        # iren = renderWindow.GetInteractor()
        # iren.SetInteractorStyle(MyInteractorStyle(self, VIEW_SAGITTAL))
        # imageViewer.SetupInteractor(iren)
        # imageViewer.SetSliceOrientationToYZ()
        
        # self.viewPortL["LB"] = imageViewer
        
        # imageViewer = vtk.vtkImageViewer2()
        # imageViewer.SetInputData(self.dicomLow.vtkImage)
        # renderWindow = self.qvtkWidget_Coronal_L.GetRenderWindow()
        # imageViewer.SetRenderWindow(renderWindow)
        # imageViewer.SetRenderer(self.dicomLow.rendererCoronal)
        
        # iren = renderWindow.GetInteractor()
        # iren.SetInteractorStyle(MyInteractorStyle(self, VIEW_CORONAL))
        # imageViewer.SetupInteractor(iren)
        # imageViewer.SetSliceOrientationToXZ()
        # self.viewPortL["RB"] = imageViewer
        
        self.currentRenderer = self.viewPortL['LT'].renderer
        self.currentRenderer.SetSelectedOn()
        # 綁定GetRenderer signal
        # for widget in self.vtkWidgets_L:
        #     iStyle = widget.GetRenderWindow().GetInteractor().GetInteractorStyle()
            
        
        for view in self.viewPortL.values():
            iStyle = view.iren.GetInteractorStyle()
            iStyle.signalObject.ConnectUpdateHU(self.UpdateHU_L)
            iStyle.signalObject.ConnectGetRenderer(self.GetCurrentRendererCallback)
            
            # view.SetFocusMode(False)
            view.signalUpdateSlice.connect(self.ChangeSlice_L)
            view.signalUpdateAll.connect(self.UpdateTarget)
            view.signalUpdateExcept.connect(self.UpdateTarget)
            view.signalFocus.connect(self.Focus)
            view.signalSetSliceValue.connect(self.SetSliceValue_L)
        
        # 強制更新第一次
        # self.SetSliceValue_L(self.dicomLow.imagePosition)
        
        self.UpdateView_L()
            
    def GetCurrentRendererCallback(self, renderer):
        bUpdate = False
        if self.currentRenderer is not None and self.currentRenderer != renderer:
            self.currentRenderer.SetSelectedOff()
            bUpdate = True
            
            if self.currentStyle:
                if isinstance(self.currentStyle, InteractorStyleImageAlgorithm):
                    self.currentStyle.ResumeRendererStyle()
                    
                    # imageFunction = SegmentationFunction()
                    # imageFunction.SetInputData(renderer.image)
                    self.currentStyle.StartInteractor(renderer)
                    # self.currentStyle = InteractorStyleSegmentation(renderer)
                    # self.currentStyle.CallbackSetOutRange(self.OnSignalOutRange)
                    # self.currentStyle.SetInput(imageFunction)
                    if renderer.orientation == VIEW_3D:
                        self.currentStyle.SetActor(renderer.volume)
                    else:
                        self.currentStyle.SetActor(renderer.actorImage)
                    
        self.currentRenderer = renderer
        renderer.SetSelectedOn()
        
        if bUpdate:
            self.UpdateView_L()
    
    
    def ChangeTabIndex(self, index):
        indexL = self.tabWidget.indexOf(self.tabWidget_Low)
        indexH = self.tabWidget.indexOf(self.tabWidget_High)
        if index == indexL:
            if not hasattr(self, 'viewPort_L'):                
                self.irenSagittal_L = self.qvtkWidget_Sagittal_L.GetRenderWindow().GetInteractor()
                self.irenAxial_L = self.qvtkWidget_Axial_L.GetRenderWindow().GetInteractor()
                self.irenCoronal_L = self.qvtkWidget_Coronal_L.GetRenderWindow().GetInteractor()
                self.iren3D_L = self.qvtkWidget_3D_L.GetRenderWindow().GetInteractor()
                self.dicomLow.irenList["sagittal"] = self.irenSagittal_L
                self.dicomLow.irenList["coronal"] = self.irenCoronal_L
                self.dicomLow.irenList["axial"] = self.irenAxial_L
                self.dicomLow.irenList["3D"] = self.iren3D_L
                
                self.irenSagittal_L.Initialize()
                self.irenAxial_L.Initialize()
                self.irenCoronal_L.Initialize()
                self.iren3D_L.Initialize()
                
                self.irenSagittal_L.Start()
                self.irenCoronal_L.Start()
                self.irenAxial_L.Start()
                self.iren3D_L.Start()
            
            if self.viewPortL is not None:
                self.syncInteractorStyle.SetViewport(self.viewPortL)
            
        elif index == indexH:
            if not hasattr(self, 'viewPort_H'):                 
                self.irenSagittal_H = self.qvtkWidget_Sagittal_H.GetRenderWindow().GetInteractor()
                self.irenAxial_H = self.qvtkWidget_Axial_H.GetRenderWindow().GetInteractor()
                self.irenCoronal_H = self.qvtkWidget_Coronal_H.GetRenderWindow().GetInteractor()
                self.iren3D_H = self.qvtkWidget_3D_H.GetRenderWindow().GetInteractor()
                self.dicomHigh.irenList["sagittal"] = self.irenSagittal_H
                self.dicomHigh.irenList["coronal"] = self.irenCoronal_H
                self.dicomHigh.irenList["axial"] = self.irenAxial_H
                self.dicomHigh.irenList["3D"] = self.iren3D_H
                
                self.irenSagittal_H.Initialize()
                self.irenAxial_H.Initialize()
                self.irenCoronal_H.Initialize()
                self.iren3D_H.Initialize()
                
                self.irenSagittal_H.Start()
                self.irenCoronal_H.Start()
                self.irenAxial_H.Start()
                self.iren3D_H.Start()
                
            if self.viewPortH is not None:
                self.syncInteractorStyle.SetViewport(self.viewPortH)
        
    
    def GetTrajectoryInfo(self, target:np.ndarray, entry:np.ndarray):
        if isinstance(target, tuple) or isinstance(target, list):
            target = np.array(target)
            
        if isinstance(entry, tuple) or isinstance(entry, list):
            entry = np.array(entry)
            
        if not isinstance(target, np.ndarray) or not isinstance(entry, np.ndarray):
            print(f'varient "target" or "entry" type error')
            return None, None
        
        if target.shape[0] != entry.shape[0]:
            print(f'target and entry have different dimension')
            return None, None
        
        if len(target.shape) > 1 or len(entry.shape) > 1:
            print(f'target or entry dimension error')
            return None, None
        
        vector = entry - target
        length = np.linalg.norm(vector)
        vector = vector / length
        
        return vector, length
    
    def ChangeSlice_L(self, pos):
        
        if isinstance(pos, list) or isinstance(pos, tuple):
            pos = np.array(pos)
        elif not isinstance(pos, np.ndarray):
            self.logUI.debug(f'variant {pos} is not array')
            return
        
        self.lblSagittal.setText(f'{pos[0]}')
        self.lblCoronal.setText(f'{pos[1]}')
        self.lblAxial.setText(f'{pos[2]}')
        
        for view in self.viewPortL.values():
            view.ChangeSliceView(pos)
            
            
        
        
    
    def ChangeSlice_H(self, pos):
        
        if isinstance(pos, list) or isinstance(pos, tuple):
            pos = np.array(pos)
        elif not isinstance(pos, np.ndarray):
            self.logUI.debug(f'variant {pos} is not array')
            return
        
        self.lblSagittal_H.setText(f'{pos[0]}')
        self.lblCoronal_H.setText(f'{pos[1]}')
        self.lblAxial_H.setText(f'{pos[2]}')
        
        for view in self.viewPortH.values():
            view.ChangeSliceView(pos)
    
    def ScrollBarChangeSagittal_L(self):
        """while ScrollBar Change (Sagittal), update ui plot
        """
        self.dicomLow.ChangeSagittalView(self.SliceSelect_Sagittal_L.value())
        ## 調整 planning path 的 point 顯示 ############################################################################################
        if np.array(self.dcmTagLow.get("selectedPoint")).shape[0] == 2:
            pointEntry = self.dcmTagLow.get("selectedPoint")[0]
            pointTarget = self.dcmTagLow.get("selectedPoint")[1]
            if abs(self.SliceSelect_Sagittal_L.value()*self.dcmTagLow.get("pixel2Mm")[0]-pointEntry[0]) < self.dicomLow.radius:
                self.dicomLow.rendererSagittal.AddActor(self.dicomLow.actorPointEntry)
            else:
                self.dicomLow.rendererSagittal.RemoveActor(self.dicomLow.actorPointEntry)
            if abs(self.SliceSelect_Sagittal_L.value()*self.dcmTagLow.get("pixel2Mm")[0]-pointTarget[0]) < self.dicomLow.radius:
                self.dicomLow.rendererSagittal.AddActor(self.dicomLow.actorPointTarget)
            else:
                self.dicomLow.rendererSagittal.RemoveActor(self.dicomLow.actorPointTarget)
        ############################################################################################
        # self.irenSagittal_L.Initialize()
        # self.iren3D_L.Initialize()
        
        # self.irenSagittal_L.Start()
        # self.iren3D_L.Start()
        self.UpdateView_L()
        
        self.logUI.debug('Show Low Dicom Sagittal')
        return
        
    def ScrollBarChangeCoronal_L(self):
        """while ScrollBar Change (Coronal), update ui plot
        """
        
        self.dicomLow.ChangeCoronalView(self.SliceSelect_Coronal_L.value())
        ## 調整 planning path 的 point 顯示 ############################################################################################
        if np.array(self.dcmTagLow.get("selectedPoint")).shape[0] == 2:
            pointEntry = self.dcmTagLow.get("selectedPoint")[0]
            pointTarget = self.dcmTagLow.get("selectedPoint")[1]
            if abs(self.SliceSelect_Coronal_L.value()*self.dcmTagLow.get("pixel2Mm")[1]-pointEntry[1]) < self.dicomLow.radius:
                self.dicomLow.rendererCoronal.AddActor(self.dicomLow.actorPointEntry)
            else:
                self.dicomLow.rendererCoronal.RemoveActor(self.dicomLow.actorPointEntry)
            if abs(self.SliceSelect_Coronal_L.value()*self.dcmTagLow.get("pixel2Mm")[1]-pointTarget[1]) < self.dicomLow.radius:
                self.dicomLow.rendererCoronal.AddActor(self.dicomLow.actorPointTarget)
            else:
                self.dicomLow.rendererCoronal.RemoveActor(self.dicomLow.actorPointTarget)
        ############################################################################################
        # self.irenCoronal_L.Initialize()
        # self.iren3D_L.Initialize()
        
        # self.irenCoronal_L.Start()
        # self.iren3D_L.Start()
        self.UpdateView_L()
        
        self.logUI.debug('Show Low Dicom Coronal')

    def ScrollBarChangeAxial_L(self):
        """while ScrollBar Change (Axial), update ui plot
        """
        # renderers = self.qvtkWidget_Axial_L.GetRenderWindow().GetRenderers()
        # renderer = renderers.GetFirstRenderer()
        
        # while renderer is not None:
        #     if  renderer == self.dicomLow.rendererCrossSection:
                
        #         # vector, length = self.GetTrajectoryInfo([0, 0, 0], [10, 10, 10])
        #         # value = self.SliceSelect_Axial_L.value()
        #         # vectorZ = [0, 0, value]
        #         # lengthZ = np.linalg.norm(vectorZ)
        #         # if lengthZ != 0:
        #         #     cosThelta = np.dot(vectorZ, vector) / lengthZ
        #         #     N = value / cosThelta
        #         #     #position = target + vectorT_unit * N，這邊測試時position是0，之後要改
        #         #     pos = vector * N
        #         #     print(f'pos = {pos}')
                    
        #         #     renderer.imageReslice.SetResliceAxesOrigin(pos)
        #         pass
                    
                
        #     else:
        #         self.dicomLow.ChangeAxialView(self.SliceSelect_Axial_L.value())
        #     renderer = renderers.GetNextItem()
            
            
        ## 調整 planning path 的 point 顯示 ############################################################################################
        if np.array(self.dcmTagLow.get("selectedPoint")).shape[0] == 2:
            pointEntry = self.dcmTagLow.get("selectedPoint")[0]
            pointTarget = self.dcmTagLow.get("selectedPoint")[1]
            if abs(self.SliceSelect_Axial_L.value()*self.dcmTagLow.get("pixel2Mm")[2]-pointEntry[2]) < self.dicomLow.radius:
                self.dicomLow.rendererAxial.AddActor(self.dicomLow.actorPointEntry)
            else:
                self.dicomLow.rendererAxial.RemoveActor(self.dicomLow.actorPointEntry)
            if abs(self.SliceSelect_Axial_L.value()*self.dcmTagLow.get("pixel2Mm")[2]-pointTarget[2]) < self.dicomLow.radius:
                self.dicomLow.rendererAxial.AddActor(self.dicomLow.actorPointTarget)
            else:
                self.dicomLow.rendererAxial.RemoveActor(self.dicomLow.actorPointTarget)
        ############################################################################################
        # self.irenAxial_L.Initialize()
        # self.iren3D_L.Initialize()
        
        # self.irenAxial_L.Start()
        # self.iren3D_L.Start()
        # self.updateView_L()
        
        self.logUI.debug('Show Low Dicom Axial')
        
    def UpdateHU_L(self, value):
        self.lblHuValue.setText(f'{int(value)}')
        
    def UpdateHU_H(self, value):
        self.lblHuValue_H.setText(f'{value}')
        
    def UpdateTarget(self, orientation:str = None, pos = None, bFocus = True):
        viewPort = self.GetViewPort()
        
        if viewPort is None:
            print(f'viewPort is not exist')
            return
        
        for view in viewPort.values():
            if (orientation is None) or (orientation != view.orientation):
                
                # print(f'orientation = {orientation}, view.orientation = {view.orientation}')
                if bFocus == True:
                    view.Focus()
                view.renderer.SetTarget(pos)
                view.UpdateView()
                
        # if not hasattr(self, 'tabWidget') or \
        #     not hasattr(self, 'tabWidget_Low') or \
        #     not hasattr(self, 'tabWidget_High'):
        #     QMessageBox.critical(None, 'ERROR', 'tabWidget loss')
        #     return
        
        
        
        # indexL = self.tabWidget.indexOf(self.tabWidget_Low)
        # indexH = self.tabWidget.indexOf(self.tabWidget_High)
        # dicom = None
        # if self.tabWidget.currentIndex() == indexL:
        #     dicom = self.dicomLow
        # elif self.tabWidget.currentIndex() == indexH:
        #     dicom = self.dicomHigh
            
        # if bForcus == True:
        #     self.Focus(pos)
        # dicom.UpdateTarget(pos)
   
    def UpdateView_H(self):
        if not hasattr(self, 'viewPortH'):
            return
        
        if self.viewPortH is None:
            return
        
        for view in self.viewPortH.values():
            view.UpdateView()
        # self.dicomHigh.UpdateView()
        
        # irenList = self.dicomHigh.irenList
        # if isinstance(irenList, dict): 
        #     for iren in irenList.values():
        #         iren.Initialize()
        #         iren.Start()
    
    def UpdateView_L(self):
        if not hasattr(self, 'viewPortL'):
            return
        
        if self.viewPortL is None:
            return
        
        for view in self.viewPortL.values():
            view.UpdateView()
        
        # irenList = self.dicomLow.irenList
        # if isinstance(irenList, dict):            
        #     for iren in irenList.values():
        #         iren.Initialize()
        #         iren.Start()
        
    def addCrossSectionItemInSelector(self):
        indexL = self.tabWidget.indexOf(self.tabWidget_Low)
        indexH = self.tabWidget.indexOf(self.tabWidget_High)
        
        viewName = VIEW_CROSS_SECTION + ' View'
        if self.tabWidget.currentIndex() == indexL:
            for combobox in self.listViewSelectorL.values():
                if combobox.findText(viewName) == -1:
                    combobox.addItem(viewName)
            
        elif self.tabWidget.currentIndex() == indexH:
            for combobox in self.listViewSelectorH.values():
                if combobox.findText(viewName) == -1:
                    combobox.addItem(viewName)
        
    def modifyTrajectory(self, dicom, entry, target):
        dicom.CreateLine(entry, target)
        
        if dicom == self.dicomLow:
            for view in self.viewPortL.values():
                length = np.linalg.norm(np.array(entry) - np.array(target))
                if view.orientation == VIEW_CROSS_SECTION:
                    view.uiScrollSlice.setMaximum(length)
        else:
            for view in self.viewPortH.values():
                length = np.linalg.norm(np.array(entry) - np.array(target))
                if view.orientation == VIEW_CROSS_SECTION:
                    view.uiScrollSlice.setMaximum(length)
            
                    
    
    def SetEntry_L(self):
        if self.dcmTagLow.get("pickPoint") is None:
            return
        
        pickPoint = self.dcmTagLow.get("pickPoint").copy()
        if pickPoint is not None:
            
            self.dicomLow.DrawPoint(pickPoint, 1)      
            self.dcmTagLow["selectedPoint1"] = np.array(pickPoint)
            self.dicomLow.entryPoint = pickPoint
            
            if self.dcmTagLow.get("selectedPoint2") is not None:
                self.dcmTagLow.update({"flageSelectedPoint": True})
                
                point2 = self.dcmTagLow.get("selectedPoint2")
                # self.dicomLow.CreateLine(pickPoint, point2)
                self.modifyTrajectory(self.dicomLow, pickPoint, point2)
                
                self.addCrossSectionItemInSelector()
            self.UpdateView_L()
            
    
    def SetTarget_L(self):
        if self.dcmTagLow.get("pickPoint") is None:
            return
        
        pickPoint = self.dcmTagLow.get("pickPoint").copy()
        if pickPoint is not None:
            self.dicomLow.DrawPoint(pickPoint, 2)
            self.dicomLow.targetPoint = pickPoint
            
            self.dcmTagLow["selectedPoint2"] = np.array(pickPoint)
            if self.dcmTagLow.get("selectedPoint1") is not None:
                self.dcmTagLow.update({"flageSelectedPoint": True})
                
                point1 = self.dcmTagLow.get("selectedPoint1")
                # self.dicomLow.CreateLine(point1, pickPoint)
                self.modifyTrajectory(self.dicomLow, point1, pickPoint)
                self.addCrossSectionItemInSelector()
            self.UpdateView_L()
        
    def SetEntry_H(self):
        pickPoint = self.dcmTagHigh.get("pickPoint").copy()
        if pickPoint is not None:
            self.dicomHigh.DrawPoint(pickPoint, 1)        
            self.dcmTagHigh["selectedPoint1"] = np.array(pickPoint)
            self.dicomHigh.entryPoint = pickPoint
            if self.dcmTagHigh.get("selectedPoint2") is not None:
                self.dcmTagHigh.update({"flageSelectedPoint": True})
                
                point2 = self.dcmTagHigh.get("selectedPoint2")
                # self.dicomHigh.CreateLine(pickPoint, point2)
                self.modifyTrajectory(self.dicomHigh, pickPoint, point2)
                self.addCrossSectionItemInSelector()
                self.dicomHigh.entryPoint = pickPoint
            self.UpdateView_H()
    
    def SetTarget_H(self):
        pickPoint = self.dcmTagHigh.get("pickPoint").copy()
        if pickPoint is not None:
            self.dicomHigh.DrawPoint(pickPoint, 2)
            self.dicomHigh.targetPoint = pickPoint
            self.dcmTagHigh["selectedPoint2"] = np.array(pickPoint)
            if self.dcmTagHigh.get("selectedPoint1") is not None:
                self.dcmTagHigh.update({"flageSelectedPoint": True})
                
                point1 = self.dcmTagHigh.get("selectedPoint1")
                # self.dicomHigh.CreateLine(pickPoint, point1)
                self.modifyTrajectory(self.dicomHigh, point1, pickPoint)
                self.addCrossSectionItemInSelector()
                self.dicomHigh.targetPoint = pickPoint
            self.UpdateView_H()

    def SetWidth_L(self):
        """set window width and show changed DICOM to ui
        """
        ## 設定 window width ############################################################################################
        self.dcmTagLow.update({"ww": int(self.Slider_WW_L.value())})
        
        # wl = self.Slider_WL_L.value()
        # ww = self.Slider_WW_L.value()
        # compositeOpacity = vtk.vtkPiecewiseFunction()
        # compositeOpacity.AddPoint(wl - ww, 0.0)
        # compositeOpacity.AddPoint( wl, 0.8)
        # compositeOpacity.AddPoint( wl + ww, 1.0)
        # volumeProperty.SetScalarOpacity(compositeOpacity)
        
        self.dicomLow.ChangeWindowWidthView(self.Slider_WW_L.value())
        self.UpdateView_L()
        
        ############################################################################################
        self.logUI.debug('Set Low Dicom Window Width')

    def SetLevel_L(self):
        """set window center/level and show changed DICOM to ui
        """
        ## 設定 window level ############################################################################################
        self.dcmTagLow.update({"wl": int(self.Slider_WL_L.value())})
        
        self.dicomLow.ChangeWindowLevelView(self.Slider_WL_L.value())
        self.UpdateView_L()
        ############################################################################################
        self.logUI.debug('Set Low Dicom Window Level')

    def ImportDicom_H(self):
        """load exhale (High breath) DICOM to get image array and metadata
        """
        self.logUI.info('Import Dicom exhale/_High')
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setFilter(QDir.Files)

        if dlg.exec_():
            filePath = dlg.selectedFiles()[0] + '/'
        else:
            return
        
        self.ui_SP = SystemProcessing()
        self.ui_SP.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.ui_SP.show()
        QApplication.processEvents()
        
        self.dcmFn.signalProcess.connect(self.ui_SP.UpdateProgress)
        self.dicomHigh.signalProgress.connect(self.ui_SP.UpdateProgress)
        
        "pydicom stage"
        metadata, metadataSeriesNum, filePathList = self.dcmFn.LoadPath(filePath)
        if metadata == 0 or metadataSeriesNum == 0:
            self.ui_SP.close()
            QMessageBox.critical(self, "error", "please load one DICOM")
            self.logUI.info('not loading one DICOM')
            return
        print("-------------------------------------------------------------------")
        print("load exhale/High DICOM path:")
        print(filePath)
        print("-------------------------------------------------------------------")
        logStr = 'Load exhale/High Dicom: ' + filePath
        self.logUI.info(logStr)

        "reset VTK"
        if self.dcmTagHigh.get("imageTag") != []:
            self.dicomHigh.Reset()
            self.ResetUI('high')
            # "render"
            # "Sagittal"
            # self.dicomHigh.rendererSagittal.RemoveActor(self.dicomHigh.actorSagittal)
            # "Coronal"
            # self.dicomHigh.rendererCoronal.RemoveActor(self.dicomHigh.actorCoronal)
            # "Axial"
            # self.dicomHigh.rendererAxial.RemoveActor(self.dicomHigh.actorAxial)
            # "3D"
            # self.dicomHigh.renderer3D.RemoveActor(self.dicomHigh.actorSagittal)
            # self.dicomHigh.renderer3D.RemoveActor(self.dicomHigh.actorAxial)
            # self.dicomHigh.renderer3D.RemoveActor(self.dicomHigh.actorCoronal)
            
            # self.dicomHigh.rendererSagittal.RemoveActor(self.dicomHigh.actorPointEntry)
            
            # self.irenSagittal_H.Initialize()
            # self.irenCoronal_H.Initialize()
            # self.irenAxial_H.Initialize()
            # self.iren3D_H.Initialize()
            
            # self.irenSagittal_H.Start()
            # self.irenCoronal_H.Start()
            # self.irenAxial_H.Start()
            # self.iren3D_H.Start()
        
        "reset dcm"
        self.dcmTagHigh = {}
        self.dcmTagHigh.update({"ww": 1})
        self.dcmTagHigh.update({"wl": 1})
        self.dcmTagHigh.update({"imageTag": []})
        "registration ball"
        # self.dcmTagHigh.update({"selectedBall": []})
        self.dcmTagHigh.update({"regBall": []})
        self.dcmTagHigh.update({"flageSelectedBall": False})
        self.dcmTagHigh.update({"candidateBall": []})
        self.dcmTagHigh.update({"selectedBallKey": []})
        "set point"
        self.dcmTagHigh.update({"selectedPoint": []})
        self.dcmTagHigh.update({"flageSelectedPoint": False})
        self.dcmTagHigh.update({"flageShowPointButton": False})
        "show point"
        # self.dcmTagHigh.update({"sectionTag":[]})
        "ui disable"
        self.label_Error_H.setText('Registration difference: mm')
        self.Button_Planning.setEnabled(False)
        self.Button_Registration_H.setEnabled(False)
        self.Button_ShowRegistration_H.setEnabled(False)
        self.comboBox_H.setEnabled(False)
        # self.Button_SetPoint_H.setEnabled(False)
        self.Button_ShowPoint_H.setEnabled(False)
        # self.Button_RobotHome.setEnabled(False)
        # self.Button_RobotAutoRun.setEnabled(False)

        seriesNumberLabel, dicDICOM, dirDICOM = self.dcmFn.SeriesSort(metadata, metadataSeriesNum, filePathList)
        imageTag, folderDir = self.dcmFn.ReadDicom(seriesNumberLabel, dicDICOM, dirDICOM)
        self.dcmTagHigh.update({"imageTag": imageTag})
        image = self.dcmFn.GetImage(self.dcmTagHigh.get("imageTag"))
        if image != 0:
            self.dcmTagHigh.update({"image": np.array(image)})
        else:
            self.ui_SP.close()
            QMessageBox.critical(self, "error", "please load one DICOM")
            self.logUI.warning('fail to get image')
            return

        rescaleSlope = self.dcmTagHigh.get("imageTag")[0].RescaleSlope
        rescaleIntercept = self.dcmTagHigh.get("imageTag")[0].RescaleIntercept
        self.dcmTagHigh.update({"imageHu": np.asarray(self.dcmFn.Transfer2Hu(self.dcmTagHigh.get("image"), rescaleSlope, rescaleIntercept))})
        self.dcmTagHigh.update({"pixel2Mm": self.dcmFn.GetPixel2Mm(self.dcmTagHigh.get("imageTag")[0])})
        self.dcmTagHigh.update({"imageHuMm": np.array(self.dcmFn.ImgTransfer2Mm(self.dcmTagHigh.get("imageHu"), self.dcmTagHigh.get("pixel2Mm")))})
        patientPosition = self.dcmTagHigh.get("imageTag")[0].PatientPosition

        "VTK stage"
        self.dcmTagHigh.update({"folderDir":folderDir})
        imageVTKHu = self.dicomHigh.LoadImage(folderDir)
        self.dcmTagHigh.update({"imageVTKHu":imageVTKHu})
        # self.dicomHigh.CreateActorAndRender(int((self.dicomHigh.imageDimensions[0])/2))
        
        # if not hasattr(self, 'irenSagittal_H'):
        #     self.irenSagittal_H = self.qvtkWidget_Sagittal_H.GetRenderWindow().GetInteractor()
        #     self.irenCoronal_H = self.qvtkWidget_Coronal_H.GetRenderWindow().GetInteractor()
        #     self.irenAxial_H = self.qvtkWidget_Axial_H.GetRenderWindow().GetInteractor()
        #     self.iren3D_H = self.qvtkWidget_3D_H.GetRenderWindow().GetInteractor()
        #     self.dicomHigh.irenList["sagittal"] = self.irenSagittal_H
        #     self.dicomHigh.irenList["coronal"] = self.irenCoronal_H
        #     self.dicomHigh.irenList["axial"] = self.irenAxial_H
        #     self.dicomHigh.irenList["3D"] = self.iren3D_H
            
        
        # self.SliceSelect_Sagittal_H.setMinimum(1)
        # self.SliceSelect_Sagittal_H.setMaximum(self.dicomHigh.imageDimensions[0])
        # self.SliceSelect_Sagittal_H.setValue(int((self.dicomHigh.imageDimensions[0])/2))
        # self.SliceSelect_Coronal_H.setMinimum(1)
        # self.SliceSelect_Coronal_H.setMaximum(self.dicomHigh.imageDimensions[1])
        # self.SliceSelect_Coronal_H.setValue(int((self.dicomHigh.imageDimensions[1])/2))
        # self.SliceSelect_Axial_H.setMinimum(1)
        # self.SliceSelect_Axial_H.setMaximum(self.dicomHigh.imageDimensions[2])
        # self.SliceSelect_Axial_H.setValue(int((self.dicomHigh.imageDimensions[2])/2))

        thresholdValue = int(((self.dicomHigh.dicomGrayscaleRange[1] - self.dicomHigh.dicomGrayscaleRange[0]) / 6) + self.dicomHigh.dicomGrayscaleRange[0])
        "WindowWidth"
        self.Slider_WW_H.setMinimum(0)
        self.Slider_WW_H.setMaximum(int(abs(self.dicomHigh.dicomGrayscaleRange[0]) + self.dicomHigh.dicomGrayscaleRange[1]))
        self.dcmTagHigh.update({"ww": abs(thresholdValue*2)})
        self.Slider_WW_H.setValue(self.dcmTagHigh.get("ww"))
        "WindowCenter / WindowLevel"
        self.Slider_WL_H.setMinimum(int(self.dicomHigh.dicomGrayscaleRange[0]))
        self.Slider_WL_H.setMaximum(int(self.dicomHigh.dicomGrayscaleRange[1]))
        self.dcmTagHigh.update({"wl": thresholdValue})
        self.Slider_WL_H.setValue(self.dcmTagHigh.get("wl"))

        self.logUI.debug('Loaded exhale/High Dicom')
        self.ShowDicom_H()

        "Enable ui"
        self.Slider_WW_H.setEnabled(True)
        self.Slider_WL_H.setEnabled(True)
        self.SliceSelect_Axial_H.setEnabled(True)
        self.SliceSelect_Sagittal_H.setEnabled(True)
        self.SliceSelect_Coronal_H.setEnabled(True)
        self.Button_Registration_H.setEnabled(True)
        self.tabWidget.setCurrentWidget(self.tabWidget_High)
        
        self.ui_SP.close()
        return

    def ShowDicom_H(self):
        """show high dicom to ui
        """
        if self.viewPortH is not None:
            for view in self.viewPortH.values():
                view.Reset() 
                
        self.viewPortH = {}
        self.viewPortH["RT"] = ViewPortUnit(self, self.dicomHigh, self.qvtkWidget_Axial_H, VIEW_AXIAL, self.SliceSelect_Axial_H, self.cbxViewSelection2_H)
        self.viewPortH["LB"] = ViewPortUnit(self, self.dicomHigh, self.qvtkWidget_Sagittal_H, VIEW_SAGITTAL, self.SliceSelect_Sagittal_H, self.cbxViewSelection3_H)
        self.viewPortH["RB"] = ViewPortUnit(self, self.dicomHigh, self.qvtkWidget_Coronal_H, VIEW_CORONAL, self.SliceSelect_Coronal_H, self.cbxViewSelection4_H)
        self.viewPortH["LT"] = ViewPortUnit(self, self.dicomHigh, self.qvtkWidget_3D_H, VIEW_3D, self.SliceSelect_3D_H, self.cbxViewSelection1_H)
        self.syncInteractorStyle = SynchronInteractorStyle(self.viewPortH)
        
        for view in self.viewPortH.values():
            iStyle = view.iren.GetInteractorStyle()
            iStyle.signalObject.ConnectUpdateHU(self.UpdateHU_H)
            
            view.signalUpdateSlice.connect(self.ChangeSlice_H)
            view.signalUpdateAll.connect(self.UpdateTarget)
            view.signalUpdateExcept.connect(self.UpdateTarget)
            view.signalFocus.connect(self.Focus)
            view.signalSetSliceValue.connect(self.SetSliceValue_H)
            # 強制更新第一次
            self.SetSliceValue_H(self.dicomLow.imagePosition)

    def ScrollBarChangeSagittal_H(self):
        """while ScrollBar Change (Sagittal), update ui plot
        """
        self.dicomHigh.ChangeSagittalView(self.SliceSelect_Sagittal_H.value())
        
        if np.array(self.dcmTagHigh.get("selectedPoint")).shape[0] == 2:
            pointEntry = self.dcmTagHigh.get("selectedPoint")[0]
            pointTarget = self.dcmTagHigh.get("selectedPoint")[1]
            if abs(self.SliceSelect_Sagittal_H.value()*self.dcmTagHigh.get("pixel2Mm")[0]-pointEntry[0]) < self.dicomHigh.radius:
                self.dicomHigh.rendererSagittal.AddActor(self.dicomHigh.actorPointEntry)
            else:
                self.dicomHigh.rendererSagittal.RemoveActor(self.dicomHigh.actorPointEntry)
            if abs(self.SliceSelect_Sagittal_H.value()*self.dcmTagHigh.get("pixel2Mm")[0]-pointTarget[0]) < self.dicomHigh.radius:
                self.dicomHigh.rendererSagittal.AddActor(self.dicomHigh.actorPointTarget)
            else:
                self.dicomHigh.rendererSagittal.RemoveActor(self.dicomHigh.actorPointTarget)
        
        # self.irenSagittal_H.Initialize()
        # self.iren3D_H.Initialize()
        
        # self.irenSagittal_H.Start()
        # self.iren3D_H.Start()
        self.UpdateView_H()
        
        self.logUI.debug('Show High Dicom Sagittal')
    
    def ScrollBarChangeCoronal_H(self):
        """while ScrollBar Change (Coronal), update ui plot
        """
        self.dicomHigh.ChangeCoronalView(self.SliceSelect_Coronal_H.value())
        
        if np.array(self.dcmTagHigh.get("selectedPoint")).shape[0] == 2:
            pointEntry = self.dcmTagHigh.get("selectedPoint")[0]
            pointTarget = self.dcmTagHigh.get("selectedPoint")[1]
            if abs(self.SliceSelect_Coronal_H.value()*self.dcmTagHigh.get("pixel2Mm")[1]-pointEntry[1]) < self.dicomHigh.radius:
                self.dicomHigh.rendererCoronal.AddActor(self.dicomHigh.actorPointEntry)
            else:
                self.dicomHigh.rendererCoronal.RemoveActor(self.dicomHigh.actorPointEntry)
            if abs(self.SliceSelect_Coronal_H.value()*self.dcmTagHigh.get("pixel2Mm")[1]-pointTarget[1]) < self.dicomHigh.radius:
                self.dicomHigh.rendererCoronal.AddActor(self.dicomHigh.actorPointTarget)
            else:
                self.dicomHigh.rendererCoronal.RemoveActor(self.dicomHigh.actorPointTarget)
        
        # self.irenCoronal_H.Initialize()
        # self.iren3D_H.Initialize()
        
        # self.irenCoronal_H.Start()
        # self.iren3D_H.Start()
        self.UpdateView_H()
        
        self.logUI.debug('Show High Dicom Coronal')
    
    def ScrollBarChangeAxial_H(self):
        """while ScrollBar Change (Axial), update ui plot
        """
        self.dicomHigh.ChangeAxialView(self.SliceSelect_Axial_H.value())
        
        if np.array(self.dcmTagHigh.get("selectedPoint")).shape[0] == 2:
            pointEntry = self.dcmTagHigh.get("selectedPoint")[0]
            pointTarget = self.dcmTagHigh.get("selectedPoint")[1]
            if abs(self.SliceSelect_Axial_H.value()*self.dcmTagHigh.get("pixel2Mm")[2]-pointEntry[2]) < self.dicomHigh.radius:
                self.dicomHigh.rendererAxial.AddActor(self.dicomHigh.actorPointEntry)
            else:
                self.dicomHigh.rendererAxial.RemoveActor(self.dicomHigh.actorPointEntry)
            if abs(self.SliceSelect_Axial_H.value()*self.dcmTagHigh.get("pixel2Mm")[2]-pointTarget[2]) < self.dicomHigh.radius:
                self.dicomHigh.rendererAxial.AddActor(self.dicomHigh.actorPointTarget)
            else:
                self.dicomHigh.rendererAxial.RemoveActor(self.dicomHigh.actorPointTarget)
        
        # self.irenAxial_H.Initialize()
        # self.iren3D_H.Initialize()
        
        # self.irenAxial_H.Start()
        # self.iren3D_H.Start()
        self.UpdateView_H()
        
        self.logUI.debug('Show High Dicom Axial')

    def SetWidth_H(self):
        """set window width and show changed DICOM to ui
        """
        ## 設定 window width ############################################################################################
        self.dcmTagHigh.update({"ww": int(self.Slider_WW_H.value())})
        
        self.dicomHigh.ChangeWindowWidthView(self.Slider_WW_H.value())
        self.UpdateView_H()
        
        
        self.logUI.debug('Set High Dicom Window Width')

    def SetLevel_H(self):
        """set window center/level and show changed DICOM to ui
        """
        ## 設定 window level ############################################################################################
        self.dcmTagHigh.update({"wl": int(self.Slider_WL_H.value())})
        
        self.dicomHigh.ChangeWindowLevelView(self.Slider_WL_H.value())
        self.UpdateView_H()
        
        self.logUI.debug('Set High Dicom Window Level')

    def SetRegistration_L(self):
        """automatic find registration ball center + open another ui window to let user selects ball in order (origin -> x axis -> y axis)
        """
        self.ui_SP = SystemProcessing()
        self.ui_SP.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.ui_SP.show()
        QApplication.processEvents()
        if self.dcmTagLow.get("regBall") != [] or self.dcmTagLow.get("candidateBall") != []:
            self.ui_SP.close()
            reply = QMessageBox.information(self, "information", "already registration, reset now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            ## 重新設定儲存的資料 ############################################################################################
            if reply == QMessageBox.Yes:
                # self.dcmTagLow.update({"selectedBall": []})
                self.dcmTagLow.update({"regBall": []})
                self.dcmTagLow.update({"flageSelectedBall": False})
                
                self.dcmTagLow.update({"candidateBall": []})
                self.dcmTagLow.update({"selectedBallKey": []})
                self.dcmTagLow.update({"regMatrix": []})
                # self.dcmTagLow.update({"sectionTag": []})
                self.dcmTagLow.update({"selectedPoint": []})
                self.dcmTagLow.update({"flageSelectedPoint": False})
                
                "UI"
                self.label_Error_L.setText('Registration difference: mm')
                self.Button_ShowRegistration_L.setEnabled(False)
                self.comboBox_L.setEnabled(False)
                # self.Button_SetPoint_L.setEnabled(False)
                self.Button_ShowPoint_L.setEnabled(False)
                
                "VTK"
                try:
                    self.dicomLow.RemovePoint()
                    # self.irenSagittal_L.Initialize()
                    # self.irenCoronal_L.Initialize()
                    # self.irenAxial_L.Initialize()
                    # self.iren3D_L.Initialize()
                    
                    # self.irenSagittal_L.Start()
                    # self.irenCoronal_L.Start()
                    # self.irenAxial_L.Start()
                    # self.iren3D_L.Start()
                    # self.dicomLow.UpdateView()
                except:
                    pass
                
                self.logUI.info('reset selected ball (Low)')
                print("reset selected ball (Low)")
                
                return
            else:
                self.ui_SP.close()
                return
            ############################################################################################
        "automatic find registration ball center"
        try:
            ## 自動找球心 + 辨識定位球位置 ############################################################################################
            flage, answer = self.regFn.GetBallAuto(self.dcmTagLow.get("imageVTKHu"), self.dcmTagLow.get("pixel2Mm"), self.dcmTagLow.get("imageTag"))
            ############################################################################################
        except Exception as e:
            self.ui_SP.close()
            self.logUI.warning('get candidate ball error / SetRegistration_L() error')
            QMessageBox.critical(self, "error", "get candidate ball error / SetRegistration_L() error")
            print('get candidate ball error / SetRegistration_L() error')
            print(e)
            return
        
        if flage == True:
            self.logUI.info('get candidate ball of inhale/Low DICOM in VTK:')
            i = 0
            for key, value in answer.items():
                tmp = str(i) + ": " + str(key) + str(value)
                self.logUI.info(tmp)
                i += 1
            self.dcmTagLow.update({"candidateBallVTK": answer})
            ## 顯示定位球註冊結果 ############################################################################################
            "open another ui window to check registration result"
            self.ui_CS = CoordinateSystem(self.dcmTagLow, self.dicomLow)
            self.ui_SP.close()
            self.ui_CS.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.ui_CS.show()
            ############################################################################################
            self.Button_ShowRegistration_L.setEnabled(True)
        else:
            self.ui_SP.close()
            self.logUI.warning('get candidate ball error')
            QMessageBox.critical(self, "error", "get candidate ball error")
            print('get candidate ball error / SetRegistration_L() error')
            ## 顯示手動註冊定位球視窗 ############################################################################################
            "Set up the coordinate system manually"
            self.ui_CS = CoordinateSystemManual(self.dcmTagLow, self.dicomLow, answer)
            self.ui_CS.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.ui_CS.show()
            ############################################################################################
            self.Button_ShowRegistration_L.setEnabled(True)
            return
        
        return

    def ShowRegistrationDifference_L(self):
        """map/pair/match ball center between auto(candidateBall) and manual(selectedBall)
           calculate error/difference of relative distance
        """
        "map/pair/match ball center between auto(candidateBall) and manual(selectedBall)"
        candidateBallVTK = self.dcmTagLow.get("candidateBallVTK")
        selectedBallKey = self.dcmTagLow.get("selectedBallKey")
        if selectedBallKey is None or selectedBallKey == []:
            QMessageBox.critical(self, "error", "please redo registration, select the ball")
            print("pair error / ShowRegistrationDifference_L() error")
            self.logUI.warning('pair error / ShowRegistrationDifference_L() error')
            return
        else:
            selectedBallAll = np.array(candidateBallVTK.get(tuple(selectedBallKey)))
            selectedBall = selectedBallAll[:,0:3]
            ## 儲存定位球中心 ############################################################################################
            self.dcmTagLow.update({"regBall": selectedBall})
            self.logUI.info('get registration balls of inhale/Low DICOM:')
            for tmp in self.dcmTagLow.get("regBall"):
                self.logUI.info(tmp)
            ############################################################################################
            ## 計算定位誤差 ############################################################################################
            "calculate error/difference of relative distance"
            error = self.regFn.GetError(self.dcmTagLow.get("regBall"))
            logStr = 'registration error of inhale/Low DICOM (min, max, mean): ' + str(error)
            self.logUI.info(logStr)
            self.label_Error_L.setText('Registration difference: {:.2f} mm'.format(error[2]))
            ############################################################################################
            ## 計算轉換矩陣 ############################################################################################
            "calculate transformation matrix"
            regMatrix = self.regFn.TransformationMatrix(self.dcmTagLow.get("regBall"))
            self.logUI.info('get registration matrix of inhale/Low DICOM: ')
            for tmp in regMatrix:
                self.logUI.info(tmp)
            self.dcmTagLow.update({"regMatrix": regMatrix})
            ############################################################################################
            # self.Button_SetPoint_L.setEnabled(True)
            self.comboBox_L.setEnabled(True)
        return

    def SetPoint_L(self):
        """set/select entry and target points
        """
        if self.dcmTagLow.get("flageSelectedPoint") == False:
            ## 設定 entry 和 target 點 ############################################################################################
            if self.comboBox_L.currentText() == "Axial":
                self.ui_SPS = SetPointSystem(self.dcmTagLow, self.comboBox_L.currentText(), self.SliceSelect_Axial_L.value())# * self.dcmTagLow.get("pixel2Mm")[2])
                self.ui_SPS.show()
            elif self.comboBox_L.currentText() == "Coronal":
                self.ui_SPS = SetPointSystem(self.dcmTagLow, self.comboBox_L.currentText(), self.SliceSelect_Coronal_L.value())# * self.dcmTagLow.get("pixel2Mm")[1])
                self.ui_SPS.show()
            elif self.comboBox_L.currentText() == "Sagittal":
                self.ui_SPS = SetPointSystem(self.dcmTagLow, self.comboBox_L.currentText(), self.SliceSelect_Sagittal_L.value())# * self.dcmTagLow.get("pixel2Mm")[0])
                self.ui_SPS.show()
            else:
                print("comboBox_L error / SetPoint_L() error")
                self.logUI.warning('comboBox_L error / SetPoint_L() error')

            self.Button_ShowPoint_L.setEnabled(True)
            return
            ############################################################################################
        elif self.dcmTagLow.get("flageSelectedPoint") == True:
            reply = QMessageBox.information(self, "information", "already selected points, reset now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            ## 重設 entry 和 target 點 ############################################################################################
            if reply == QMessageBox.Yes:
                self.dcmTagLow.update({"selectedPoint": []})
                self.dcmTagLow.update({"flageSelectedPoint": False})
                self.Button_Planning.setEnabled(False)
                self.dcmTagLow.update({"flageShowPointButton": False})
                # self.dcmTagLow.update({"sectionTag":[]})
                strInfo = "reset selected point (LoW)"
                self.logUI.info(strInfo)
                print(strInfo)
                self.Button_ShowPoint_L.setEnabled(False)
                
                "VTK"
                try:
                    self.dicomLow.RemovePoint()
                except:
                    pass
                self.irenSagittal_L.Initialize()
                self.irenCoronal_L.Initialize()
                self.irenAxial_L.Initialize()
                self.iren3D_L.Initialize()
                
                self.irenSagittal_L.Start()
                self.irenCoronal_L.Start()
                self.irenAxial_L.Start()
                self.iren3D_L.Start()
                
                return
            else:
                return
            ############################################################################################
        return

    def ShowPoint_L(self):
        """show selected entry and target points 
        """
        tmpResult = []
        try:
            print("-------------------------------------------------------------------")
            strInfo = "inhale/Low DICOM entry and target point position (in VTK image coodinate)"
            print(strInfo)
            self.logUI.info(strInfo)
            for tmp in self.dcmTagLow.get("selectedPoint"):
                print(tmp)
                self.logUI.info(tmp)
                sys.stdout.flush()
            print("-------------------------------------------------------------------")
            
            self.dcmTagLow.update({"flageShowPointButton": True})
            if self.dcmTagLow.get("flageShowPointButton") is True and self.dcmTagHigh.get("flageShowPointButton") is True:
                self.Button_Planning.setEnabled(True)
            ## 顯示 planning path, 依照情況調整顯示 planning path 的 point ############################################################################################
            "VTK"
            pointEntry = self.dcmTagLow.get("selectedPoint")[0]
            pointTarget = self.dcmTagLow.get("selectedPoint")[1]
            
            self.dicomLow.CreatePath(np.array([pointEntry, pointTarget]))
            
            if self.dcmTagLow.get("selectedPoint") == []:
                pass
            else:
                if abs(self.SliceSelect_Sagittal_L.value()*self.dcmTagLow.get("pixel2Mm")[0]-pointEntry[0]) < self.dicomLow.radius:
                    self.dicomLow.rendererSagittal.AddActor(self.dicomLow.actorPointEntry)
                else:
                    self.dicomLow.rendererSagittal.RemoveActor(self.dicomLow.actorPointEntry)
                if abs(self.SliceSelect_Sagittal_L.value()*self.dcmTagLow.get("pixel2Mm")[0]-pointTarget[0]) < self.dicomLow.radius:
                    self.dicomLow.rendererSagittal.AddActor(self.dicomLow.actorPointTarget)
                else:
                    self.dicomLow.rendererSagittal.RemoveActor(self.dicomLow.actorPointTarget)
                    
                if abs(self.SliceSelect_Coronal_L.value()*self.dcmTagLow.get("pixel2Mm")[1]-pointEntry[1]) < self.dicomLow.radius:
                    self.dicomLow.rendererCoronal.AddActor(self.dicomLow.actorPointEntry)
                else:
                    self.dicomLow.rendererCoronal.RemoveActor(self.dicomLow.actorPointEntry)
                if abs(self.SliceSelect_Coronal_L.value()*self.dcmTagLow.get("pixel2Mm")[1]-pointTarget[1]) < self.dicomLow.radius:
                    self.dicomLow.rendererCoronal.AddActor(self.dicomLow.actorPointTarget)
                else:
                    self.dicomLow.rendererCoronal.RemoveActor(self.dicomLow.actorPointTarget)
                    
                if abs(self.SliceSelect_Axial_L.value()*self.dcmTagLow.get("pixel2Mm")[2]-pointEntry[2]) < self.dicomLow.radius:
                    self.dicomLow.rendererAxial.AddActor(self.dicomLow.actorPointEntry)
                else:
                    self.dicomLow.rendererAxial.RemoveActor(self.dicomLow.actorPointEntry)
                if abs(self.SliceSelect_Axial_L.value()*self.dcmTagLow.get("pixel2Mm")[2]-pointTarget[2]) < self.dicomLow.radius:
                    self.dicomLow.rendererAxial.AddActor(self.dicomLow.actorPointTarget)
                else:
                    self.dicomLow.rendererAxial.RemoveActor(self.dicomLow.actorPointTarget)
                
            # self.irenSagittal_L.Initialize()
            # self.irenCoronal_L.Initialize()
            # self.irenAxial_L.Initialize()
            # self.iren3D_L.Initialize()
            
            # self.irenSagittal_L.Start()
            # self.irenCoronal_L.Start()
            # self.irenAxial_L.Start()
            # self.iren3D_L.Start()
            # self.dicomLow.UpdateView()
            ############################################################################################
            return
        except:
            self.logUI.warning('show points error / SetPoint_L() error')
            QMessageBox.critical(self, "error", "show points error")
            print('show points error / SetPoint_L() error')
            return
        return

    def SetRegistration_H(self):
        """automatic find registration ball center + open another ui window to let user selects ball in order (origin -> x axis -> y axis)
        """
        self.ui_SP = SystemProcessing()
        self.ui_SP.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.ui_SP.show()
        QApplication.processEvents()
        if self.dcmTagHigh.get("regBall") != [] or self.dcmTagHigh.get("candidateBall") != []:
            self.ui_SP.close()
            reply = QMessageBox.information(self, "information", "already registration, reset now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                # self.dcmTagHigh.update({"selectedBall": []})
                self.dcmTagHigh.update({"regBall": []})
                self.dcmTagHigh.update({"flageSelectedBall": False})
                
                self.dcmTagHigh.update({"candidateBall": []})
                self.dcmTagHigh.update({"selectedBallKey": []})
                self.dcmTagHigh.update({"regMatrix": []})
                # self.dcmTagHigh.update({"sectionTag": []})
                self.dcmTagHigh.update({"selectedPoint": []})
                self.dcmTagHigh.update({"flageSelectedPoint": False})
                
                "UI"
                self.label_Error_H.setText('Registration difference: mm')
                self.Button_ShowRegistration_H.setEnabled(False)
                self.comboBox_H.setEnabled(False)
                # self.Button_SetPoint_H.setEnabled(False)
                self.Button_ShowPoint_H.setEnabled(False)
                
                "VTK"
                try:
                    self.dicomHigh.RemovePoint()
                    self.irenSagittal_H.Initialize()
                    self.irenCoronal_H.Initialize()
                    self.irenAxial_H.Initialize()
                    self.iren3D_H.Initialize()
                    
                    self.irenSagittal_H.Start()
                    self.irenCoronal_H.Start()
                    self.irenAxial_H.Start()
                    self.iren3D_H.Start()
                except:
                    pass
                
                self.logUI.info('reset selected ball (High)')
                print("reset selected ball (High)")
                return
            else:
                self.ui_SP.close()
                return
        "automatic find registration ball center"
        try:
            flage, answer = self.regFn.GetBallAuto(self.dcmTagHigh.get("imageVTKHu"), self.dcmTagHigh.get("pixel2Mm"), self.dcmTagHigh.get("imageTag"))
        except:
            self.ui_SP.close()
            self.logUI.warning('get candidate ball error / SetRegistration_H() error')
            QMessageBox.critical(self, "error", "get candidate ball error")
            print('get candidate ball error / SetRegistration_H() error')
            return
        if flage == True:
            self.logUI.info('get candidate ball of exhale/High DICOM in VTK:')
            i = 0
            for key, value in answer.items():
                tmp = str(i) + ": " + str(key) + str(value)
                self.logUI.info(tmp)
                i += 1
            self.dcmTagHigh.update({"candidateBallVTK": answer})
            
            "open another ui window to check registration result"
            self.ui_CS = CoordinateSystem(self.dcmTagHigh, self.dicomHigh)
            self.ui_SP.close()
            self.ui_CS.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.ui_CS.show()
            self.Button_ShowRegistration_H.setEnabled(True)
        else:
            self.ui_SP.close()
            self.logUI.warning('get candidate ball error')
            QMessageBox.critical(self, "error", "get candidate ball error")
            print('get candidate ball error / SetRegistration_H() error')
            
            "Set up the coordinate system manually"
            self.ui_CS = CoordinateSystemManual(self.dcmTagHigh, self.dicomHigh, answer)
            self.ui_CS.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.ui_CS.show()
            
            self.Button_ShowRegistration_H.setEnabled(True)
            return

        return

    def ShowRegistrationDifference_H(self):
        """map/pair/match ball center between auto(candidateBall) and manual(selectedBall)
           calculate error/difference of relative distance
        """
        "map/pair/match ball center between auto(candidateBall) and manual(selectedBall)"
        candidateBallVTK = self.dcmTagHigh.get("candidateBallVTK")
        selectedBallKey = self.dcmTagHigh.get("selectedBallKey")
        if selectedBallKey is None or selectedBallKey == []:
            QMessageBox.critical(self, "error", "please redo registration, select the ball")
            print("pair error / ShowRegistrationDifference_H() error")
            self.logUI.warning('pair error / ShowRegistrationDifference_H() error')
            return
        else:
            selectedBallAll = np.array(candidateBallVTK.get(tuple(selectedBallKey)))
            selectedBall = selectedBallAll[:,0:3]
            self.dcmTagHigh.update({"regBall": selectedBall})
            self.logUI.info('get registration balls of exhale/High DICOM:')
            for tmp in self.dcmTagHigh.get("regBall"):
                self.logUI.info(tmp)
            "calculate error/difference of relative distance"
            error = self.regFn.GetError(self.dcmTagHigh.get("regBall"))
            logStr = 'registration error of exhale/High DICOM (min, max, mean): ' + str(error)
            self.logUI.info(logStr)
            self.label_Error_H.setText('Registration difference: {:.2f} mm'.format(error[2]))
            "calculate transformation matrix"
            regMatrix = self.regFn.TransformationMatrix(self.dcmTagHigh.get("regBall"))
            self.logUI.info('get registration matrix of exhale/High DICOM: ')
            for tmp in regMatrix:
                self.logUI.info(tmp)
            self.dcmTagHigh.update({"regMatrix": regMatrix})
            # self.Button_SetPoint_H.setEnabled(True)
            self.comboBox_H.setEnabled(True)
        return

    def SetPoint_H(self):
        """set/select entry and target points
        """
        if self.dcmTagHigh.get("flageSelectedPoint") == False:
            if self.comboBox_H.currentText() == "Axial":
                self.ui_SPS = SetPointSystem(self.dcmTagHigh, self.comboBox_H.currentText(), self.SliceSelect_Axial_H.value())# * self.dcmTagHigh.get("pixel2Mm")[2])
                self.ui_SPS.show()
            elif self.comboBox_H.currentText() == "Coronal":
                self.ui_SPS = SetPointSystem(self.dcmTagHigh, self.comboBox_H.currentText(), self.SliceSelect_Coronal_H.value())# * self.dcmTagHigh.get("pixel2Mm")[1])
                self.ui_SPS.show()
            elif self.comboBox_H.currentText() == "Sagittal":
                self.ui_SPS = SetPointSystem(self.dcmTagHigh, self.comboBox_H.currentText(), self.SliceSelect_Sagittal_H.value())# * self.dcmTagHigh.get("pixel2Mm")[0])
                self.ui_SPS.show()
            else:
                print("comboBox_H error / SetPoint_H() error")
                self.logUI.warning('comboBox_H error / SetPoint_H() error')

            self.Button_ShowPoint_H.setEnabled(True)
            return
        elif self.dcmTagHigh.get("flageSelectedPoint") == True:
            reply = QMessageBox.information(self, "information", "already selected points, reset now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.dcmTagHigh.update({"selectedPoint": []})
                self.dcmTagHigh.update({"flageSelectedPoint": False})
                self.Button_Planning.setEnabled(False)
                self.dcmTagHigh.update({"flageShowPointButton": False})
                # self.dcmTagHigh.update({"sectionTag":[]})
                strInfo = "reset selected point (High)"
                self.logUI.info(strInfo)
                print(strInfo)
                self.Button_ShowPoint_H.setEnabled(False)
                
                "VTK"
                try:
                    self.dicomHigh.RemovePoint()
                except:
                    pass
                self.irenSagittal_H.Initialize()
                self.irenCoronal_H.Initialize()
                self.irenAxial_H.Initialize()
                self.iren3D_H.Initialize()
                
                self.irenSagittal_H.Start()
                self.irenCoronal_H.Start()
                self.irenAxial_H.Start()
                self.iren3D_H.Start()
                
                return
            else:
                return
        return

    def ShowPoint_H(self):
        """show selected entry and target points 
        """
        try:
            print("-------------------------------------------------------------------")
            strInfo = "exhale/High DICOM entry and target point position (in VTK image coodinate)"
            print(strInfo)
            self.logUI.info(strInfo)
            for tmp in self.dcmTagHigh.get("selectedPoint"):
                print(tmp)
                self.logUI.info(tmp)
            print("-------------------------------------------------------------------")

            self.dcmTagHigh.update({"flageShowPointButton": True})
            if self.dcmTagLow.get("flageShowPointButton") is True and self.dcmTagHigh.get("flageShowPointButton") is True:
                self.Button_Planning.setEnabled(True)
            
            "VTK"
            pointEntry = self.dcmTagHigh.get("selectedPoint")[0]
            pointTarget = self.dcmTagHigh.get("selectedPoint")[1]
            
            self.dicomHigh.CreatePath(np.array([pointEntry, pointTarget]))
            if self.dcmTagHigh.get("selectedPoint") == []:
                pass
            else:
                if abs(self.SliceSelect_Sagittal_H.value()*self.dcmTagHigh.get("pixel2Mm")[0]-pointEntry[0]) < self.dicomHigh.radius:
                    self.dicomHigh.rendererSagittal.AddActor(self.dicomHigh.actorPointEntry)
                else:
                    self.dicomHigh.rendererSagittal.RemoveActor(self.dicomHigh.actorPointEntry)
                if abs(self.SliceSelect_Sagittal_H.value()*self.dcmTagHigh.get("pixel2Mm")[0]-pointTarget[0]) < self.dicomHigh.radius:
                    self.dicomHigh.rendererSagittal.AddActor(self.dicomHigh.actorPointTarget)
                else:
                    self.dicomHigh.rendererSagittal.RemoveActor(self.dicomHigh.actorPointTarget)
                    
                if abs(self.SliceSelect_Coronal_H.value()*self.dcmTagHigh.get("pixel2Mm")[1]-pointEntry[1]) < self.dicomHigh.radius:
                    self.dicomHigh.rendererCoronal.AddActor(self.dicomHigh.actorPointEntry)
                else:
                    self.dicomHigh.rendererCoronal.RemoveActor(self.dicomHigh.actorPointEntry)
                if abs(self.SliceSelect_Coronal_H.value()*self.dcmTagHigh.get("pixel2Mm")[1]-pointTarget[1]) < self.dicomHigh.radius:
                    self.dicomHigh.rendererCoronal.AddActor(self.dicomHigh.actorPointTarget)
                else:
                    self.dicomHigh.rendererCoronal.RemoveActor(self.dicomHigh.actorPointTarget)
                    
                if abs(self.SliceSelect_Axial_H.value()*self.dcmTagHigh.get("pixel2Mm")[2]-pointEntry[2]) < self.dicomHigh.radius:
                    self.dicomHigh.rendererAxial.AddActor(self.dicomHigh.actorPointEntry)
                else:
                    self.dicomHigh.rendererAxial.RemoveActor(self.dicomHigh.actorPointEntry)
                if abs(self.SliceSelect_Axial_H.value()*self.dcmTagHigh.get("pixel2Mm")[2]-pointTarget[2]) < self.dicomHigh.radius:
                    self.dicomHigh.rendererAxial.AddActor(self.dicomHigh.actorPointTarget)
                else:
                    self.dicomHigh.rendererAxial.RemoveActor(self.dicomHigh.actorPointTarget)
                
            self.irenSagittal_H.Initialize()
            self.irenCoronal_H.Initialize()
            self.irenAxial_H.Initialize()
            self.iren3D_H.Initialize()
            
            self.irenSagittal_H.Start()
            self.irenCoronal_H.Start()
            self.irenAxial_H.Start()
            self.iren3D_H.Start()
            return
        except:
            self.logUI.warning('show points error / SetPoint_H() error')
            QMessageBox.critical(self, "error", "show points error")
            print('show points error / SetPoint_H() error')
            return
        return

    def ShowPlanningPath(self):
        """show planning path in regBall coordinate system
           (high entry and target points + low entry and target points )
        """
        ## 把 planning path 合在一起傳給 robot ############################################################################################
        tmpPointLow = np.array([[0.0, 0.0, 0.0],[0.0, 0.0, 0.0]])
        tmpPointHigh = np.array([[0.0, 0.0, 0.0],[0.0, 0.0, 0.0]])
        tmpPointLow[0] = self.regFn.TransformPointVTK(self.dcmTagLow.get("imageTag"), self.dcmTagLow.get("selectedPoint")[0])
        tmpPointLow[1] = self.regFn.TransformPointVTK(self.dcmTagLow.get("imageTag"), self.dcmTagLow.get("selectedPoint")[1])
        tmpPointHigh[0] = self.regFn.TransformPointVTK(self.dcmTagHigh.get("imageTag"), self.dcmTagHigh.get("selectedPoint")[0])
        tmpPointHigh[1] = self.regFn.TransformPointVTK(self.dcmTagHigh.get("imageTag"), self.dcmTagHigh.get("selectedPoint")[1])
        self.dcmTagLow.update({"PlanningPath":self.regFn.GetPlanningPath(self.dcmTagLow.get("regBall")[0], tmpPointLow, self.dcmTagLow.get("regMatrix"))})
        self.dcmTagHigh.update({"PlanningPath":self.regFn.GetPlanningPath(self.dcmTagHigh.get("regBall")[0], tmpPointHigh, self.dcmTagHigh.get("regMatrix"))})
        try:
            # 把兩組PlanningPath合在一起
            self.PlanningPath = []
            for tmpPoint in self.dcmTagHigh.get("PlanningPath"):
                self.PlanningPath.append(tmpPoint*[1, 1, -1])
            for tmpPoint in self.dcmTagLow.get("PlanningPath"):
                self.PlanningPath.append(tmpPoint*[1, 1, -1])
            
            strInfo = "PlanningPath: (in mm unit, High: entry-target, Low: entry-target)"
            print(strInfo)
            self.logUI.info(strInfo)
            for p in self.PlanningPath:
                print(p)
                self.logUI.info(p)
            print("-------------------------------------------------------------------")
            self.Button_RobotHome.setEnabled(True)
            self.Button_RobotAutoRun.setEnabled(True)
            "Qmessage"
            QMessageBox.information(self, "Information", "Ready to robot navigation")
            ############################################################################################
            "VTK"
            # self.irenSagittal_L.Initialize()
            # self.irenCoronal_L.Initialize()
            # self.irenAxial_L.Initialize()
            # self.iren3D_L.Initialize()
            
            # self.irenSagittal_L.Start()
            # self.irenCoronal_L.Start()
            # self.irenAxial_L.Start()
            # self.iren3D_L.Start()
            # self.dicomLow.UpdateView()
            
            # self.irenSagittal_H.Initialize()
            # self.irenCoronal_H.Initialize()
            # self.irenAxial_H.Initialize()
            # self.iren3D_H.Initialize()
            
            # self.irenSagittal_H.Start()
            # self.irenCoronal_H.Start()
            # self.irenAxial_H.Start()
            # self.iren3D_H.Start()
            self.dicomHigh.UpdateView()
            
        except:
            self.logUI.warning('fail to Set Planning Path / SetPlanningPath() error')
            print("fail to Set Planning Path / SetPlanningPath() error")
            QMessageBox.critical(self, "error", "fail to Set Planning Path")

        return


class ViewPortUnit(QObject):
    
    
    signalUpdateExcept  = pyqtSignal(str)
    signalUpdateAll     = pyqtSignal()
    signalUpdateSlice   = pyqtSignal(np.ndarray)
    signalFocus         = pyqtSignal(np.ndarray)
    signalSetSliceValue = pyqtSignal(np.ndarray)
    bUpdateOtherView = True
    bSelected = False
    bFocusMode = True
    renderer   = None
    position = None
    imagePosition = None
    
    def __init__(self, mainWidget, dicom:DISPLAY, vtkWidget:QVTKRenderWindowInteractor, orientation:str, uiScrollSlice:QScrollBar, uiCbxOrientation:QComboBox):
        
        super().__init__()
        self.parentWidget       = mainWidget
        self.dicom              = dicom
        self.uiCbxOrientation   = uiCbxOrientation
        self.vtkWidget          = vtkWidget
        self.uiScrollSlice      = uiScrollSlice
        self.orientation        = orientation
        self.currentIndex       = uiCbxOrientation.currentIndex()
        self.uiScrollSlice.valueChanged.connect(self.OnValueChanged_ViewScroll)
        self.uiScrollSlice.setMinimum(0)
        self.iren               = vtkWidget.GetRenderWindow().GetInteractor()
        
        if not dicom:
            iStyle = MyInteractorStyle(mainWidget, VIEW_3D)
            self.iren.SetInteractorStyle(iStyle)
            return
        
        self.position           = dicom.target
        self.imagePosition      = dicom.imagePosition
        
        
        if orientation == VIEW_AXIAL:
            self.renderer = self.dicom.rendererAxial
            self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
            iStyle = MyInteractorStyle(mainWidget, VIEW_AXIAL)
            self.iren.SetInteractorStyle(iStyle) 
            
            self.uiScrollSlice.setMaximum(self.dicom.imageDimensions[2] - 1)
            self.uiScrollSlice.setValue(int((self.dicom.imageDimensions[2])/2))
        elif orientation == VIEW_SAGITTAL:
            self.renderer = self.dicom.rendererSagittal
            self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)    
            iStyle = MyInteractorStyle(mainWidget, VIEW_SAGITTAL)    
            self.iren.SetInteractorStyle(iStyle)
            
            self.uiScrollSlice.setMaximum(self.dicom.imageDimensions[0] - 1)
            self.uiScrollSlice.setValue(int((self.dicom.imageDimensions[0])/2))
        elif orientation == VIEW_CORONAL:
            self.renderer = self.dicom.rendererCoronal
            self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
            iStyle = MyInteractorStyle(mainWidget, VIEW_CORONAL)    
            self.iren.SetInteractorStyle(iStyle)
            
            self.uiScrollSlice.setMaximum(self.dicom.imageDimensions[1] - 1)
            self.uiScrollSlice.setValue(int((self.dicom.imageDimensions[1])/2))
        elif orientation == VIEW_3D:
            self.renderer = self.dicom.renderer3D
            self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
            self.iren.SetInteractorStyle(MyInteractorStyle(mainWidget, VIEW_3D))
            self.uiScrollSlice.setEnabled(False)
        elif orientation == VIEW_CROSS_SECTION:
            self.renderer = self.dicom.rendererCrossSection
            self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
            self.iren.SetInteractorStyle(MyInteractorStyle(mainWidget, VIEW_CROSS_SECTION))
            
            length = self.renderer.GetTrajectoryLength()
            if length is not None:
                self.uiScrollSlice.setMinimum(0)
                self.uiScrollSlice.setMaximum(length)
                self.uiScrollSlice.setValue(0)
            
        # self.renderer.signalUpdateView.connect(self.UpdateView)
        self.renderer.SetTarget()
        self.renderer.initalBorder()
        self.UpdateView()
        
    def Reset(self):
        self.uiScrollSlice.valueChanged.disconnect(self.OnValueChanged_ViewScroll)
        
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
            self.signalUpdateSlice.emit(imagePos)
        elif posCS is not None:
            pos = self.dicom.rendererCrossSection.GetPositionFromCrossSection(posCS)
            # print(f'pos = {pos}, posCS = {posCS}')
            
            if self.orientation == VIEW_CROSS_SECTION:
                self.renderer.SetTarget(pos = posCS, posOriginal = pos)
                self.renderer.image.ComputeStructuredCoordinates(pos, imagePos, pcoord)
                imagePos += np.round(pcoord)
                self.imagePosition[:] = imagePos
                
            self.signalFocus.emit(pos)
            self.signalUpdateAll.emit()
            self.signalUpdateSlice.emit(imagePos)
    
    def ChangeSliceView(self, pos):
        if not self.renderer:
            return
        
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
    

class CoordinateSystem(QWidget, FunctionLib_UI.ui_coordinate_system.Ui_Form):
    def __init__(self, dcmTag, dicomVTK):
        super(CoordinateSystem, self).__init__()
        self.setupUi(self)
        self.SetWindow2Center()
        
        "create VTK"
        ## 建立 VTK 物件 ############################################################################################
        self.reader = vtkDICOMImageReader()
        
        self.windowLevelLookup = vtkWindowLevelLookupTable()
        self.mapColors = vtkImageMapToColors()
        self.camera3D = vtkCamera()
        
        self.renderer3D = vtkRenderer()
        
        self.actorBallRed = vtkActor()
        self.actorBallGreen = vtkActor()
        self.actorBallBlue = vtkActor()
        ############################################################################################
        self.dcmTag = dcmTag
        self.dicomVTK = dicomVTK
        
        "addComboBox"
        ## 新增 combo box 選項 ############################################################################################
        tmpKey = []
        
        self.candidateBallVTK = self.dcmTag.get("candidateBallVTK")
        for k in self.candidateBallVTK.keys():
            tmpKey.append(k)
        self.keys = np.array(tmpKey)
        
        for i in range(len(self.keys)):
            self.comboBox_label.addItem(str(i+1))
        
        self.comboBox_label.setCurrentIndex(0)
        self.comboBox_label.currentIndexChanged.connect(self.SelectionChange)
        self.SelectionChange(0)
        ############################################################################################
        return
    
    def SetWindow2Center(self):
        ## 視窗置中 ############################################################################################
        "screen size"
        screen = QDesktopWidget().screenGeometry()
        "window size"
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
        ############################################################################################
        return
    
    def SelectionChange(self,i):
        ## combo box slot, 更改顯示的定位球 ############################################################################################
        currentKey = self.keys[i,:]
        
        currentValue = np.array(self.candidateBallVTK.get(tuple(currentKey)))
        
        self.DisplayImage(currentKey[3:6])
        
        centerBallRed = currentValue[0,3:6]
        centerBallGreen = currentValue[1,3:6]
        centerBallBlue = currentValue[2,3:6]
        radius = 10
        self.CreateBallRed(centerBallRed, radius)
        self.CreateBallGreen(centerBallGreen, radius)
        self.CreateBallBlue(centerBallBlue, radius)
        
        self.iren3D_L.Initialize()
        self.iren3D_L.Start()
        ############################################################################################
        return
    
    def CreateBallRed(self, center, radius):
        ## 建立原點定位球 VTK 物件 ############################################################################################
        sphereSource = vtkSphereSource()
        sphereSource.SetCenter(center)
        sphereSource.SetRadius(radius)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.actorBallRed.SetMapper(mapper)
        self.actorBallRed.GetProperty().SetColor(1, 0, 0)
        
        self.renderer3D.AddActor(self.actorBallRed)
        ############################################################################################
        return
    
    def CreateBallGreen(self, center, radius):
        ## 建立 x 方向定位球 VTK 物件 ############################################################################################
        sphereSource = vtkSphereSource()
        sphereSource.SetCenter(center)
        sphereSource.SetRadius(radius)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.actorBallGreen.SetMapper(mapper)
        self.actorBallGreen.GetProperty().SetColor(0, 1, 0)
        
        self.renderer3D.AddActor(self.actorBallGreen)
        ############################################################################################
        return
    
    def CreateBallBlue(self, center, radius):
        ## 建立 y 方向定位球 VTK 物件 ############################################################################################
        sphereSource = vtkSphereSource()
        sphereSource.SetCenter(center)
        sphereSource.SetRadius(radius)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.actorBallBlue.SetMapper(mapper)
        self.actorBallBlue.GetProperty().SetColor(0, 0, 1)
        
        self.renderer3D.AddActor(self.actorBallBlue)
        ############################################################################################
        return
    
    def DisplayImage(self, value):
        ## 顯示 ############################################################################################
        try:
            self.renderer3D.RemoveActor(self.actorSagittal)
            self.renderer3D.RemoveActor(self.actorAxial)
            self.renderer3D.RemoveActor(self.actorCoronal)
            self.iren3D_L.Initialize()
            self.iren3D_L.Start()
        except:
            pass
        
        "folderPath"
        folderDir = self.dcmTag.get("folderDir")
        "vtk"
        
        self.reader.SetDirectoryName(folderDir)
        self.reader.Update()
        self.vtkImage = self.reader.GetOutput()
        self.vtkImage.SetOrigin(0, 0, 0)
        self.dicomGrayscaleRange = self.vtkImage.GetScalarRange()
        self.dicomBoundsRange = self.vtkImage.GetBounds()
        self.imageDimensions = self.vtkImage.GetDimensions()
        self.pixel2Mm = self.vtkImage.GetSpacing()
        
        self.windowLevelLookup.Build()
        thresholdValue = int(((self.dicomGrayscaleRange[1] - self.dicomGrayscaleRange[0]) / 6) + self.dicomGrayscaleRange[0])
        self.windowLevelLookup.SetWindow(abs(thresholdValue*2))
        self.windowLevelLookup.SetLevel(thresholdValue)
        
        self.mapColors.SetInputConnection(self.reader.GetOutputPort())
        self.mapColors.SetLookupTable(self.windowLevelLookup)
        self.mapColors.Update()
        
        self.camera3D.SetViewUp(0, 1, 0)
        self.camera3D.SetPosition(0.8, 0.3, 1)
        self.camera3D.SetFocalPoint(0, 0, 0)
        self.camera3D.ComputeViewPlaneNormal()
        
        self.actorSagittal = vtkImageActor()
        self.actorCoronal = vtkImageActor()
        self.actorAxial = vtkImageActor()

        self.actorSagittal.GetMapper().SetInputConnection(self.mapColors.GetOutputPort())
        self.actorSagittal.SetDisplayExtent(int(value[0]/self.pixel2Mm[0]), int(value[0]/self.pixel2Mm[0]), 0, self.imageDimensions[1], 0, self.imageDimensions[2])
        self.actorCoronal.GetMapper().SetInputConnection(self.mapColors.GetOutputPort())
        self.actorCoronal.SetDisplayExtent(0, self.imageDimensions[0], int(value[1]/self.pixel2Mm[1]), int(value[1]/self.pixel2Mm[1]), 0, self.imageDimensions[2])
        self.actorAxial.GetMapper().SetInputConnection(self.mapColors.GetOutputPort())
        self.actorAxial.SetDisplayExtent(0, self.imageDimensions[0], 0, self.imageDimensions[1], int(value[2]), int(value[2]))
        
        self.renderer3D.SetBackground(0, 0, 0)
        self.renderer3D.AddActor(self.actorSagittal)
        self.renderer3D.AddActor(self.actorAxial)
        self.renderer3D.AddActor(self.actorCoronal)
        self.renderer3D.SetActiveCamera(self.camera3D)
        self.renderer3D.ResetCamera(self.dicomBoundsRange)
        
        "show"
        self.iren3D_L = self.qvtkWidget_registrtion.GetRenderWindow().GetInteractor()
        self.qvtkWidget_registrtion.GetRenderWindow().AddRenderer(self.renderer3D)
        self.iren3D_L.SetInteractorStyle(MyInteractorStyle3D(self.renderer3D))
        
        self.iren3D_L.Initialize()
        self.iren3D_L.Start()
        ############################################################################################
        return

    def okAndClose(self):
        ## 確認+選定定位球後, 儲存資料 ############################################################################################
        selectLabel = self.comboBox_label.currentText()
        selectKey = self.keys[int(selectLabel)-1,:]
        selectValue = self.candidateBallVTK.get(tuple(selectKey))
        print("-------------------------------------------------------------------")
        print("selectLabel = ", selectLabel, ", \nkey = ", selectKey, ", \nvalue = ", selectValue)
        print("-------------------------------------------------------------------")
        self.dcmTag.update({"selectedBallKey":selectKey})
        ############################################################################################
        self.close()
        return

    def Cancel(self):
        ## 關閉視窗 ############################################################################################
        self.close()
        ############################################################################################

class CoordinateSystemManual(QWidget, FunctionLib_UI.ui_coordinate_system_manual.Ui_Form, REGISTRATION):
    def __init__(self, dcmTag, dicom, answer):
        super(CoordinateSystemManual, self).__init__()
        self.setupUi(self)
        self.SetWindow2Center()
        
        "create VTK"
        ## 建立 VTK 物件 ############################################################################################
        self.reader = vtkDICOMImageReader()
        
        self.actorAxial = vtkImageActor()
        
        self.windowLevelLookup = vtkWindowLevelLookupTable()
        self.mapColors = vtkImageMapToColors()
        self.cameraAxial = vtkCamera()
        
        self.renderer = vtkRenderer()
        
        self.actorBallRed = vtkActor()
        self.actorBallGreen = vtkActor()
        self.actorBallBlue = vtkActor()
        ############################################################################################
        "hint: self.dicomLow = dicomLow = dicom"
        "hint: self.dcmTagLow = dcmTagLow = dcmTag"
        self.dcmTag = dcmTag
        self.dicom = dicom
        self.answer = answer
        
        self.Display()
        
        return
        
    def Display(self):
        ## 顯示 ############################################################################################
        "folderPath"
        folderDir = self.dcmTag.get("folderDir")
        "vtk"
        self.reader.SetDirectoryName(folderDir)
        self.reader.Update()
        
        self.iren = self.qvtkWidget_registrtion.GetRenderWindow().GetInteractor()
        
        self.vtkImage = self.reader.GetOutput()
        self.vtkImage.SetOrigin(0, 0, 0)
        self.dicomGrayscaleRange = self.vtkImage.GetScalarRange()
        self.dicomBoundsRange = self.vtkImage.GetBounds()
        self.imageDimensions = self.vtkImage.GetDimensions()
        self.pixel2Mm = self.vtkImage.GetSpacing()
        
        "ui"
        self.ScrollBar.setMinimum(1)
        self.ScrollBar.setMaximum(self.imageDimensions[2]-1)
        self.ScrollBar.setValue(int((self.imageDimensions[2])/2))
        
        "vtk"
        
        self.windowLevelLookup.Build()
        thresholdValue = int(((self.dicomGrayscaleRange[1] - self.dicomGrayscaleRange[0]) / 6) + self.dicomGrayscaleRange[0])
        self.windowLevelLookup.SetWindow(abs(thresholdValue*2))
        self.windowLevelLookup.SetLevel(thresholdValue)
        
        self.mapColors.SetInputConnection(self.reader.GetOutputPort())
        self.mapColors.SetLookupTable(self.windowLevelLookup)
        self.mapColors.Update()
        
        self.cameraAxial.SetViewUp(0, 1, 0)
        self.cameraAxial.SetPosition(0, 0, 1)
        self.cameraAxial.SetFocalPoint(0, 0, 0)
        self.cameraAxial.ComputeViewPlaneNormal()
        self.cameraAxial.ParallelProjectionOn()
        
        self.actorAxial.GetMapper().SetInputConnection(self.mapColors.GetOutputPort())
        self.actorAxial.SetDisplayExtent(0, self.imageDimensions[0], 0, self.imageDimensions[1], self.ScrollBar.value(), self.ScrollBar.value())
        
        self.renderer.SetBackground(0, 0, 0)
        self.renderer.SetBackground(.2, .3, .4)
        self.renderer.AddActor(self.actorAxial)
        self.renderer.SetActiveCamera(self.cameraAxial)
        self.renderer.ResetCamera(self.dicomBoundsRange)
        
        "show"
        self.qvtkWidget_registrtion.GetRenderWindow().AddRenderer(self.renderer)
        self.istyle = CoordinateSystemManualInteractorStyle(self)
        self.pick_point = self.iren.SetInteractorStyle(self.istyle)
        
        self.iren.Initialize()
        self.iren.Start()
        ############################################################################################
        return
        
    def SetWindow2Center(self):
        ## 視窗置中 ############################################################################################
        "screen size"
        screen = QDesktopWidget().screenGeometry()
        "window size"
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
        ############################################################################################
        return
    
    def ScrollBarChange(self):
        ## 調整顯示切面 ############################################################################################
        self.actorAxial.SetDisplayExtent(0, self.imageDimensions[0]-1, 0, self.imageDimensions[1]-1, self.ScrollBar.value(), self.ScrollBar.value())
            ## 調整是否顯示點 ############################################################################################
        try:
            ballRed = self.dcmTag.get("candidateBall")[0]
            if abs(self.ScrollBar.value()*self.dcmTag.get("pixel2Mm")[2]-ballRed[2]) < self.dicom.radius:
                self.renderer.AddActor(self.actorBallRed)
            else:
                self.renderer.RemoveActor(self.actorBallRed)
            ballGreen = self.dcmTag.get("candidateBall")[0]
            if abs(self.ScrollBar.value()*self.dcmTag.get("pixel2Mm")[2]-ballGreen[2]) < self.dicom.radius:
                self.renderer.AddActor(self.actorBallGreen)
            else:
                self.renderer.RemoveActor(self.actorBallGreen)
            ballBlue = self.dcmTag.get("candidateBall")[0]
            if abs(self.ScrollBar.value()*self.dcmTag.get("pixel2Mm")[2]-ballBlue[2]) < self.dicom.radius:
                self.renderer.AddActor(self.actorBallBlue)
            else:
                self.renderer.RemoveActor(self.actorBallBlue)
        except:
            pass
            ############################################################################################
        self.iren.Initialize()
        self.iren.Start()
        ############################################################################################
        return

    def okAndClose(self):
        ## 確認後儲存定位球資料 ############################################################################################
        if np.array(self.dcmTag.get("candidateBall")).shape[0] >= 3:
            flage, answer = self.GetBallManual(self.dcmTag.get("candidateBall"), self.dcmTag.get("pixel2Mm"), self.answer, self.dcmTag.get("imageTag"))
            if flage == True:
                self.dcmTag.update({"candidateBallVTK": answer})
                self.close()
                
                "open another ui window to check registration result"
                self.ui_CS = CoordinateSystem(self.dcmTag, self.dicom)
                self.ui_CS.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
                self.ui_CS.show()
            else:
                QMessageBox.critical(self, "error", "get candidate ball error")
                print('get candidate ball error / SetRegistration_L() error')
                
            return
        else:
            QMessageBox.information(self, "information", "need to set 3 balls")
            return
        ############################################################################################
    def Cancel(self):
        ## 關閉視窗 ############################################################################################
        self.close()
        ############################################################################################

class CoordinateSystemManualInteractorStyle(vtkInteractorStyleTrackballCamera):
    def __init__(self, setPointWindow):
        self.setPointWindow = setPointWindow
        
        self.AddObserver('LeftButtonPressEvent', self.left_button_press_event)
        
        self.AddObserver('RightButtonPressEvent', self.right_button_press_event)
        
        return
    
    def right_button_press_event(self, obj, event):
        """turn off right button"""
        ## 關閉右鍵功能 ############################################################################################
        pass
        ############################################################################################
        return
    
    
    def left_button_press_event(self, obj, event):
        """Get the location of the click (in window coordinates)"""
        ## 左鍵點選點 ############################################################################################
        points = self.GetInteractor().GetEventPosition()
        picker = vtkCellPicker()
        picker.Pick(points[0], points[1], 0, self.GetInteractor().FindPokedRenderer(points[0], points[1]))
        pick_point = picker.GetPickPosition()
        ############################################################################################
        ## 儲存點 ############################################################################################
        if picker.GetCellId() != -1:
            if np.array(self.setPointWindow.dcmTag.get("candidateBall")).shape[0] >= 3:
                QMessageBox.critical(self.setPointWindow, "error", "there are already selected 3 balls")
                return
            elif np.array(self.setPointWindow.dcmTag.get("candidateBall")).shape[0] == 0:
                self.setPointWindow.dcmTag.update({"candidateBall":np.array([np.array(pick_point)])})
                flage = 1
                print("pick_point - ",flage," : ", pick_point)
            elif np.array(self.setPointWindow.dcmTag.get("candidateBall")).shape[0] == 1:
                tmpPoint = np.insert(self.setPointWindow.dcmTag.get("candidateBall"), 1, pick_point, 0)
                self.setPointWindow.dcmTag.update({"candidateBall": tmpPoint})
                flage = 2
                print("pick_point - ",flage," : ", pick_point)
            elif np.array(self.setPointWindow.dcmTag.get("candidateBall")).shape[0] == 2:
                tmpPoint = np.insert(self.setPointWindow.dcmTag.get("candidateBall"), 2, pick_point, 0)
                self.setPointWindow.dcmTag.update({"candidateBall": tmpPoint})
                self.setPointWindow.dcmTag.update({"flagecandidateBall": True})
                flage = 3
                print("pick_point - ",flage," : ", pick_point)
            else:
                print("GetClickedPosition error / Set candidateBall System error / else")
                return
            self.DrawPoint(pick_point, flage)
        else:
            print("picker.GetCellId() = -1")
        ############################################################################################
        return
    
    def DrawPoint(self, pick_point, flage):
        """draw point"""
        ## 畫點 ############################################################################################
        radius = 3.5
        if flage == 1:
            "red"
            self.CreateBallRed(pick_point, radius)
        elif flage == 2:
            "green"
            self.CreateBallGreen(pick_point, radius)
        elif flage == 3:
            "blue"
            self.CreateBallBlue(pick_point, radius)
        ############################################################################################
        return
    
    def CreateBallGreen(self, pick_point, radius):
        ## 建立綠球 ############################################################################################
        sphereSource = vtkSphereSource()
        sphereSource.SetCenter(pick_point)
        sphereSource.SetRadius(radius)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.setPointWindow.actorBallGreen.SetMapper(mapper)
        self.setPointWindow.actorBallGreen.GetProperty().SetColor(0, 1, 0)
        
        self.setPointWindow.renderer.AddActor(self.setPointWindow.actorBallGreen)
        self.setPointWindow.iren.Initialize()
        self.setPointWindow.iren.Start()
        ############################################################################################
        return
    
    def CreateBallRed(self, pick_point, radius):
        ## 建立紅球 ############################################################################################
        sphereSource = vtkSphereSource()
        sphereSource.SetCenter(pick_point)
        sphereSource.SetRadius(radius)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.setPointWindow.actorBallRed.SetMapper(mapper)
        self.setPointWindow.actorBallRed.GetProperty().SetColor(1, 0, 0)
        
        self.setPointWindow.renderer.AddActor(self.setPointWindow.actorBallRed)
        self.setPointWindow.iren.Initialize()
        self.setPointWindow.iren.Start()
        ############################################################################################
        return
    
    def CreateBallBlue(self, pick_point, radius):
        ## 建立藍球 ############################################################################################
        sphereSource = vtkSphereSource()
        sphereSource.SetCenter(pick_point)
        sphereSource.SetRadius(radius)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.setPointWindow.actorBallBlue.SetMapper(mapper)
        self.setPointWindow.actorBallBlue.GetProperty().SetColor(0, 0, 1)
        
        self.setPointWindow.renderer.AddActor(self.setPointWindow.actorBallBlue)
        self.setPointWindow.iren.Initialize()
        self.setPointWindow.iren.Start()
        ############################################################################################
        return

# class SetPointSystem(QWidget, FunctionLib_UI.ui_set_point_system.Ui_Form):
#     def __init__(self, dcmTag, comboBox, scrollBar):
#         super(SetPointSystem, self).__init__()
#         self.setupUi(self)

#         self.dcmTag = dcmTag
#         self.comboBox = comboBox
#         if scrollBar < 1:
#            self.scrollBar = 1
#         else:
#             self.scrollBar = scrollBar
#         self.DisplayImage()
#         self.flage = 0

#     def DisplayImage(self):
#         ## 顯示 ############################################################################################
#         self.pixel2Mm = self.dcmTag.get("pixel2Mm")
#         showSection = self.comboBox
#         ww = self.dcmTag.get("ww")
#         wl = self.dcmTag.get("wl")

#         self.dicom_dir = self.dcmTag.get("folderDir")
#         self.reader = vtkDICOMImageReader()
#         self.reader.SetDirectoryName(self.dicom_dir)
#         self.reader.Update()
        
#         self.vtkImage = self.reader.GetOutput()
#         self.vtkImage.SetOrigin(0, 0, 0)
#         self.imageDimensions = self.vtkImage.GetDimensions()
        
#         windowLevelLookup = vtkWindowLevelLookupTable()
#         windowLevelLookup.Build()
#         windowLevelLookup.SetWindow(ww)
#         windowLevelLookup.SetLevel(wl)

#         self.mapColors = vtkImageMapToColors()
#         self.mapColors.SetInputConnection(self.reader.GetOutputPort())
#         self.mapColors.SetLookupTable(windowLevelLookup)
#         self.mapColors.Update()
        
#         self.actor = vtkImageActor()
#         self.actor.GetMapper().SetInputConnection(self.mapColors.GetOutputPort())
        
#         self.renderer = vtkRenderer()
        
#         if showSection == "Axial":
#             self.cameraAxial = vtkCamera()
#             self.cameraAxial.SetViewUp(0, 1, 0)
#             self.cameraAxial.SetPosition(0, 0, 1)
#             self.cameraAxial.SetFocalPoint(0, 0, 0)
#             self.cameraAxial.ComputeViewPlaneNormal()
#             self.cameraAxial.ParallelProjectionOn()
            
#             self.actor.SetDisplayExtent(0, self.imageDimensions[0], 0, self.imageDimensions[1], int(self.scrollBar), int(self.scrollBar))
            
#             self.renderer.AddActor(self.actor)
#             self.renderer.SetActiveCamera(self.cameraAxial)
#         elif showSection == "Coronal":
#             self.cameraCoronal = vtkCamera()
#             self.cameraCoronal.SetViewUp(0, 0, -1)
#             self.cameraCoronal.SetPosition(0, 1, 0)
#             self.cameraCoronal.SetFocalPoint(0, 0, 0)
#             self.cameraCoronal.ComputeViewPlaneNormal()
#             self.cameraCoronal.ParallelProjectionOn()
            
#             self.actor.SetDisplayExtent(0, self.imageDimensions[0], int(self.scrollBar), int(self.scrollBar), 0, self.imageDimensions[2])
            
#             self.renderer.AddActor(self.actor)
#             self.renderer.SetActiveCamera(self.cameraCoronal)
#         elif showSection == "Sagittal":
#             self.cameraSagittal = vtkCamera()
#             self.cameraSagittal.SetViewUp(0, 0, -1)
#             self.cameraSagittal.SetPosition(1, 0, 0)
#             self.cameraSagittal.SetFocalPoint(0, 0, 0)
#             self.cameraSagittal.ComputeViewPlaneNormal()
#             self.cameraSagittal.ParallelProjectionOn()
            
#             self.actor.SetDisplayExtent(int(self.scrollBar), int(self.scrollBar), 0, self.imageDimensions[1], 0, self.imageDimensions[2])
            
#             self.renderer.AddActor(self.actor)
#             self.renderer.SetActiveCamera(self.cameraSagittal)
#         else:
#             print("DisplayImage error / Set Point System error")
#             return
            
#         self.renderer.ResetCamera()
#         self.qvtkWidget.GetRenderWindow().AddRenderer(self.renderer)
#         self.iren = self.qvtkWidget.GetRenderWindow().GetInteractor()
#         self.istyle = SetPointInteractorStyle(self)
#         self.pick_point = self.iren.SetInteractorStyle(self.istyle)

#         self.iren.Initialize()
#         self.iren.Start()
#         ############################################################################################
#         return

#     def okAndClose(self):
#         ## 關閉視窗 ############################################################################################
#         self.close()
#         ############################################################################################
        
class SetPointInteractorStyle(vtkInteractorStyleTrackballCamera):
    def __init__(self, setPointWindow):
        self.setPointWindow = setPointWindow
        self.pick_point = None
        
        self.actorBallRed = vtkActor()
        self.actorBallGreen = vtkActor()
        
        self.AddObserver('LeftButtonPressEvent', self.left_button_press_event)
        self.AddObserver('RightButtonPressEvent', self.right_button_press_event)
    
        return
        
    def right_button_press_event(self, obj, event):
        """turn off right button"""
        pass
        return
        
    def left_button_press_event(self, obj, event):
        """Get the location of the click (in window coordinates)"""
        ## 左鍵點選點 ############################################################################################
        points = self.GetInteractor().GetEventPosition()
        picker = vtkCellPicker()
        picker.Pick(points[0], points[1], 0, self.GetInteractor().FindPokedRenderer(points[0], points[1]))
        pick_point = picker.GetPickPosition()
        ############################################################################################
        ## 儲存點 ############################################################################################
        if picker.GetCellId() != -1:
            if np.array(self.setPointWindow.dcmTag.get("selectedPoint")).shape[0] >= 2:
                QMessageBox.critical(self.setPointWindow, "error", "there are already selected 2 points")
                return
            elif np.array(self.setPointWindow.dcmTag.get("selectedPoint")).shape[0] == 0:
                self.setPointWindow.dcmTag.update({"selectedPoint":np.array([np.array(pick_point)])})
                flage = 1
            elif np.array(self.setPointWindow.dcmTag.get("selectedPoint")).shape[0] == 1:
                tmpPoint = np.insert(self.setPointWindow.dcmTag.get("selectedPoint"), 1, pick_point, 0)
                self.setPointWindow.dcmTag.update({"selectedPoint": tmpPoint})
                self.setPointWindow.dcmTag.update({"flageSelectedPoint": True})
                flage = 2
            else:
                print("GetClickedPosition error / Set Point System error / else")
                return
            self.DrawPoint(pick_point, flage)
        else:
            print("picker.GetCellId() = -1")
        "return pick_point in mm"
        ############################################################################################
        return pick_point
            
    def DrawPoint(self, pick_point, flage):
        """draw point"""
        ## 畫點 ############################################################################################
        radius = 2
        if flage == 1:
            "entry point"
            "green"
            self.CreateBallGreen(pick_point, radius)
        elif flage == 2:
            "target point"
            "red"
            self.CreateBallRed(pick_point, radius)
        ############################################################################################
        return
    
    def CreateBallGreen(self, pick_point, radius):
        ## 建立 entry point ############################################################################################
        sphereSource = vtkSphereSource()
        sphereSource.SetCenter(pick_point)
        sphereSource.SetRadius(radius)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.actorBallGreen.SetMapper(mapper)
        self.actorBallGreen.GetProperty().SetColor(0, 1, 0)
        
        self.setPointWindow.renderer.AddActor(self.actorBallGreen)
        self.setPointWindow.iren.Initialize()
        self.setPointWindow.iren.Start()
        ############################################################################################
        return
    
    def CreateBallRed(self, pick_point, radius):
        ## 建立 target point ############################################################################################
        sphereSource = vtkSphereSource()
        sphereSource.SetCenter(pick_point)
        sphereSource.SetRadius(radius)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.actorBallRed.SetMapper(mapper)
        self.actorBallRed.GetProperty().SetColor(1, 0, 0)
        
        self.setPointWindow.renderer.AddActor(self.actorBallRed)
        self.setPointWindow.iren.Initialize()
        self.setPointWindow.iren.Start()
        ############################################################################################
        return
    
class SystemProcessing(QWidget, FunctionLib_UI.ui_processing.Ui_Form):
    def __init__(self):
        """show loading window"""
        ## 顯示 loading 畫面 ############################################################################################
        super(SystemProcessing, self).__init__()
        self.setupUi(self)
        ############################################################################################
        
    def UpdateProgress(self, value):
        self.pgbLoadDIcom.setValue(int(value * 100))
    


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
        obj.parent.UpdateView_L()
        
    def OnMouseWheelBackward(self, obj, event):
        for view in self.viewport.values():
            if view.orientation in self.listOrientation:
                iStyle = view.iren.GetInteractorStyle()
                iStyle.CallMouseWheelBackward()
        obj.parent.UpdateTarget(bFocus = False)
        obj.parent.UpdateView_L()
    

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
        indexL = self.parent.tabWidget.indexOf(self.parent.tabWidget_Low)
        indexH = self.parent.tabWidget.indexOf(self.parent.tabWidget_High)
                
        if self.parent.tabWidget.currentIndex() == indexL:
            if not hasattr(self.parent, 'dicomLow'):
                return
            self.viewPort     = self.parent.viewPortL
            self.currentDicom = self.parent.dicomLow            
            self.irenSagittal = self.parent.irenSagittal_L
            self.irenAxial    = self.parent.irenAxial_L
            self.irenCoronal  = self.parent.irenCoronal_L
            self.iren3D       = self.parent.iren3D_L
            self.currentTag   = self.parent.dcmTagLow
            self.sliderWW     = self.parent.Slider_WW_L
            self.sliderWL     = self.parent.Slider_WL_L
            self.dicomType    = 'LOW'
        elif self.parent.tabWidget.currentIndex() == indexH:
            if not hasattr(self.parent, 'dicomHigh'):
                return
            self.viewPort     = self.parent.viewPortH
            self.currentDicom = self.parent.dicomHigh
            self.irenSagittal = self.parent.irenSagittal_H
            self.irenAxial    = self.parent.irenAxial_H
            self.irenCoronal  = self.parent.irenCoronal_H
            self.iren3D       = self.parent.iren3D_H
            self.currentTag   = self.parent.dcmTagHigh
            self.sliderWW     = self.parent.Slider_WW_H
            self.sliderWL     = self.parent.Slider_WL_H
            self.dicomType    = 'HIGH'
            
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
            self.parent.UpdateTarget(bFocus = False)
            self.parent.UpdateView_L()
            # self.signalObject.EmitZoomIn(event)
        
    def CallMouseWheelForward(self):
         super(MyInteractorStyle, self).OnMouseWheelForward()
        
        
    def OnMouseWheelBackward(self, obj, event):
        listView = [VIEW_AXIAL, VIEW_CORONAL, VIEW_SAGITTAL]
        
        if self.renderView in listView:
            self.parent.syncInteractorStyle.OnMouseWheelBackward(obj, event)
        else:
            super(MyInteractorStyle, self).OnMouseWheelBackward()
            self.parent.UpdateTarget(bFocus = False)
            self.parent.UpdateView_L()
            # self.signalObject.EmitZoomIn()
        
    def CallMouseWheelBackward(self):
        super(MyInteractorStyle, self).OnMouseWheelBackward()
    
    def OnMouseMove(self, obj, event):
        self.GetCurrentState()
        points = [0, 0]
        picker, pick_point = self.GetPickPosition(points)
        
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
            self.sliderWW.setValue(windowWidth)
            self.sliderWL.setValue(windowLevel)
            
            self.currentPos = np.array(points)
            
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
                    if isinstance(self.currentRenderer, RendererCrossSectionObj):
                        view.MapPositionToImageSlice(posCS = pick_point)
                    else:
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
            print(f'picked a {type(actor)} object')
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
            print("no objects be picked")
       
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
    

class MyInteractorStyle3D(vtkInteractorStyleTrackballCamera):
    
    def __init__(self, renderer = None):
        pass
    
    

#画布控件继承自 matplotlib.backends.backend_qt5agg.FigureCanvasQTAgg 类
class Canvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi) #创建画布,设置宽高，每英寸像素点数
        self.axes = fig.add_subplot(111)#
        FigureCanvasQTAgg.__init__(self, fig)#调用基类的初始化函数
        self.setParent(parent)
        FigureCanvasQTAgg.updateGeometry(self)
        
    def update_figure(self,receiveData):
        if not hasattr(self, 'line'):
            self.line, = self.axes.plot([], [])
            # self.axes.cla()#清除已绘的图形
            self.axes.set_xlim([1,640])
            self.axes.set_ylim([-125,-65])
            # self.axes.set_xticks([])
            # self.axes.set_yticks([])
            # self.axes.plot(receiveData[0])
            
        self.line.set_data(range(len(receiveData[0])), receiveData[0])
        self.draw()#重新绘制
        
        
        
            
        
# class Canvas_Cont(FigureCanvasQTAgg):
#     def __init__(self, parent=None, width=5, height=4, dpi=100):
#         fig = Figure(figsize=(width, height), dpi=dpi) #创建画布,设置宽高，每英寸像素点数
#         self.axes = fig.add_subplot(111)#
#         FigureCanvasQTAgg.__init__(self, fig)#调用基类的初始化函数
#         self.setParent(parent)
#         FigureCanvasQTAgg.updateGeometry(self)
        
#     def update_figure(self,receiveData):
#         self.axes.cla()#清除已绘的图形
#         self.axes.set_xlim([1,640])
#         self.axes.set_ylim([-125,-65])
#         self.axes.set_xticks([])
#         self.axes.set_yticks([])
#         self.axes.plot(receiveData[0])
#         self.draw()#重新绘制

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     w = MainWidget()
#     w.show()
#     sys.exit(app.exec_())
