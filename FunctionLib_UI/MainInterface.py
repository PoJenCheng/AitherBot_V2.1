
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtCore import QTranslator, QCoreApplication
from time import sleep
from datetime import datetime, timedelta
import sys
import subprocess
# from PyQt5.QtWidgets import QWidget, QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QWidget
import numpy as np
import math
import cv2
import logging
import threading
import time
import os
# from FunctionLib_UI.ui_demo_1 import *
from FunctionLib_UI.Ui__Aitherbot import *
import FunctionLib_UI.Ui_step
from FunctionLib_UI.ViewPortUnit import *
from FunctionLib_UI.WidgetButton import *
from FunctionLib_UI.Ui_DlgHint import *
from FunctionLib_UI.Ui_step import *
from FunctionLib_Robot.__init__ import *
import FunctionLib_Robot._class as Robot
import FunctionLib_UI.ui_processing


from cycler import cycler
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.use('QT5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from functools import reduce
import FunctionLib_UI.Ui_homing
import FunctionLib_UI.Ui_dlgInstallAdaptor
import FunctionLib_UI.Ui_DlgRobotMoving

STAGE_ROBOT = 'ST_ROBOT'
STAGE_LASER = 'ST_LASER'
STAGE_DICOM = 'ST_DICOM'
STAGE_IMAGE = 'ST_IMAGE'

SKIP_SLICES = 5

LAN_EN = 0
LAN_CN = 1

class MainInterface(QMainWindow,Ui_MainWindow):
    signalLoadingReady = pyqtSignal()
    signalSetProgress = pyqtSignal(QProgressBar, int)
    signalSetCheck = pyqtSignal(QWidget, bool)
    signalShowPlot = pyqtSignal(float) # for Laser test
    signalShowMessage = pyqtSignal(str, str, bool)
    signalModelBuildingPass = pyqtSignal(bool)
    signalModelBuildingUI = pyqtSignal(bool)
    signalModelCycle = pyqtSignal(tuple, int)
    signalResetLaserUI = pyqtSignal()
    
    signalDemoLaserInit = pyqtSignal(int)
    signalDemoRobotInit = pyqtSignal(int)
    signalDemoInhale = pyqtSignal(bool, float)
    signalDemoExhale = pyqtSignal(bool, float)
    signalDemoHoming = pyqtSignal(float)
    
    player = QMediaPlayer()
    robot = None
    
    vtkImageLow = None
    vtkImageHigh = None
    dicSelectedSeries = {}
    listSubDialog = []
    indexDoneStage = 0
    indexCurrentStage = 0
    indexPrePage = 0
    indexCurrentPage = 0
    bFinishRobot = False
    bFinishLaser = False
    bFinishDicom = False
    bDicomChanged = True
    bDriveTo = False
    uiHoming = None
    laserFigure = None
    currentRenderer = None
    viewport_L = None
    viewport_H = None
    currentDicom = None
    currentTag   = None
    currentStyle = None
    bFull = True
    bToggleInhale = True
    bRegistration = False
    
    videoWidget = None
    
    errDevice = 0
    idEnabledDevice = 0
    
    dicStageFinished = {STAGE_ROBOT:False, STAGE_LASER:False, STAGE_DICOM:False, STAGE_IMAGE:False}
    #robot parameter
    bTrackingBreathing = False
    
    #Laser parameter
    bLaserShowProfile = False
    bLaserTracking = False
    bLaserRecording = False
    bLaserForceClose = False
    Laser = None
    recordBreathingBase = False 
    tInhale = None
    tExhale = None
    tCheckInhale = None
    tCheckExhale = None
    indicatorInhale = None
    indicatorExhale = None
    
    # laser manual recording
    bAutoRecord = False
    dicReceiveData = None
    lstRecordAvg = []
    dicDataCycle = None
    dicDataCycleManual = {}
    bUpdateCycleData = False
    nCycle = 1
    
    dicView = {}
    # dicView_H = {}
        
    dicSliceScroll_L = {}
    dicSliceScroll_H = {}
        
    dicViewSelector_L = {}
    dicViewSelector_H = {}
    
    dicDicom = {}
    
    def __init__(self, lang:int = LAN_EN, parent: QWidget = None):
        # super(MainInterface, self).__init__()
        QMainWindow.__init__(self)
        
        self.language = lang
        self.setupUi(self)
        self.ui = Ui_MainWindow()
    
        self.dicomLow = DISPLAY()
        self.dicomHigh = DISPLAY()
        
        self.modelHide = QStandardItemModel()
        
        self.regFn = REGISTRATION()
        self.dicView['LT'] = self.wdgLeftTop
        self.dicView['RT'] = self.wdgRightTop
        self.dicView['LB'] = self.wdgLeftBottom
        self.dicView['RB'] = self.wdgRightBottom
        
        # self.dicView_H['LT'] = self.wdgLeftTop
        # self.dicView_H['RT'] = self.wdgRightTop
        # self.dicView_H['LB'] = self.wdgLeftBottom
        # self.dicView_H['RB'] = self.wdgRightBottom
        
        self.dicSliceScroll_L['LT'] = self.sbrLeftTop
        self.dicSliceScroll_L['RT'] = self.sbrRightTop
        self.dicSliceScroll_L['LB'] = self.sbrLeftBottom
        self.dicSliceScroll_L['RB'] = self.sbrRightBottom
        
        # self.dicSliceScroll_H['LT'] = self.sbrLeftTop
        # self.dicSliceScroll_H['RT'] = self.sbrRightTop
        # self.dicSliceScroll_H['LB'] = self.sbrLeftBottom
        # self.dicSliceScroll_H['RB'] = self.sbrRightBottom
        
        self.dicViewSelector_L['LT'] = self.cbxLeftTop
        self.dicViewSelector_L['RT'] = self.cbxRightTop
        self.dicViewSelector_L['LB'] = self.cbxLeftBottom
        self.dicViewSelector_L['RB'] = self.cbxRightBottom
        
        # self.dicViewSelector_H['LT'] = self.cbxViewSelection1_H
        # self.dicViewSelector_H['RT'] = self.cbxViewSelection2_H
        # self.dicViewSelector_H['LB'] = self.cbxViewSelection3_H
        # self.dicViewSelector_H['RB'] = self.cbxViewSelection4_H
        
        self.currentDicom = self.buttonGroup.checkedButton().objectName()
        self.dicDicom[self.btnDicomLow.objectName()] = {}
        self.dicDicom[self.btnDicomHigh.objectName()] = {}
        self.currentTag = self.dicDicom.get(self.currentDicom)
        
        for item in self.dicDicom.values():
            for key, combox in self.dicViewSelector_L.items():
                strKey = 'index_' + key
                item[strKey] = combox.currentIndex()
        
        self.tabWidget.setCurrentWidget(self.tabPlanning)
        
        self.stkJoint1.setCurrentWidget(self.pgJoint1Fail)
        self.stkJoint2.setCurrentWidget(self.pgJoint2Fail)
        
        self.stkSignalLight.setCurrentWidget(self.pgRedLight)
        self.cbxLanguage.setCurrentIndex(self.language)
        
        # Figure in Inhale
        fig = Figure(figsize=(5,5))
        self.axInhale = fig.add_subplot(111)
        self.axInhale.axis('off')
        self.axInhale.set_facecolor('#640000')
        fig.set_facecolor('#640000')
        fig.subplots_adjust(0, 0.05, 1, 0.95)
        
        layout = QVBoxLayout(self.wdgInhale)
        self.canvasInhale = FigureCanvasQTAgg(fig)
        layout.addWidget(self.canvasInhale)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Figure in Exhale
        fig = Figure(figsize=(5,5))
        self.axExhale = fig.add_subplot(111)
        self.axExhale.set_facecolor('#006400')
        self.axExhale.axis('off')
        fig.set_facecolor('#006400')
        fig.subplots_adjust(0, 0.05, 1, 0.95)
        
        layout = QVBoxLayout(self.wdgExhale)
        self.canvasExhale = FigureCanvasQTAgg(fig)
        layout.addWidget(self.canvasExhale)
        layout.setContentsMargins(0, 0, 0, 0)
        
        wdgStep = WidgetStep(4)
        wdgStep.SetStepNames('Change instrument', 'release robot arm', 'sterile and drop robot', 'reposition robot arm')
        layout:QGridLayout = self.pgDriveRobotGuide.layout()
        layout.replaceWidget(self.wdgGuideLine, wdgStep)
        self.wdgStep = wdgStep
        
        
        
        #Laser =================================================
        self.yellowLightCriteria = yellowLightCriteria_LowAccuracy
        self.greenLightCriteria = greenLightCriteria_LowAccuracy
        
        self.btnNext_endBuildModel.setEnabled(True)
        self.SetUIEnable_Trajectory(False)
        self.spinBox.lineEdit().setHidden(True)
        #Robot =================================================
        self.btnRobotRelease.setEnabled(True)
        self.btnRobotFix.setEnabled(False)
        self.btnRobotSetTarget.setEnabled(False)
        self.btnRobotBackTarget.setEnabled(False)
        self.settingTarget = False
        
        
        self.init_ui()
        
    def addCrossSectionItemInSelector(self):
        # indexL = self.tabWidget.indexOf(self.tabWidget_Low)
        # indexH = self.tabWidget.indexOf(self.tabWidget_High)
        
        viewName = VIEW_CROSS_SECTION + ' View'
        # if self.tabWidget.currentIndex() == indexL:
        for combobox in self.dicViewSelector_L.values():
            if combobox.findText(viewName) == -1:
                combobox.addItem(viewName)
            
        # elif self.tabWidget.currentIndex() == indexH:
        #     for combobox in self.listViewSelectorH.values():
        #         if combobox.findText(viewName) == -1:
        #             combobox.addItem(viewName)
        
        
    def importDicom(self, path):
        self.ui_SP = SystemProcessing()
        self.ui_SP.show()
        QApplication.processEvents()
        
        self.reader = DICOM()
        self.reader.signalProcess.connect(self.ui_SP.UpdateProgress)
        
        # dicom = self.reader.LoadPath('C:/Leon/CT/sT1W_3D__2853')
        # dicom = self.reader.LoadPath('C:/Leon/CT/S62070')
        # dicom = self.reader.LoadPath('C:\\Leon\\CT\\20220615\\all\\S43520\\S3010')
        dicom = self.reader.LoadPath(path)
        # self.vtkImage = self.reader.GetData(-1, 0, 0)
        
        model = QStandardItemModel()
        stringList = ['patient name', 'patient ID', 'sex', 'Modality', 'dim', 'voxel size','acqusition date', 'path']
        model.setHorizontalHeaderLabels(stringList)
        # model = self.treeDicom.model()
        
        modelFilter = QStandardItemModel()
        stringList = ['patient name', 'patient ID', 'sex']
        modelFilter.setHorizontalHeaderLabels(stringList)
        # modelFilter = self.treeDicomFilter.model()
        # rowSelectAll = modelFilter.itemFromIndex(modelFilter.index(0, 0))
        
        rowSelectAll = [QStandardItem() for _ in range(3)]
        rowSelectAll[0].setCheckable(True)
        rowSelectAll[0].setAutoTristate(True)
        rowSelectAll[0].setCheckState(Qt.Checked)
        
        modelFilter.appendRow(rowSelectAll)
        modelFilter.itemChanged.connect(self.onTreeItemChanged)
        
        for keyPatien, dicPatient in dicom.items():
            for keyStudy, dicStudy in dicPatient.items():
                for keySeries, dicSeries in dicStudy.items():
                    slices = dicSeries.get('data')
                    if slices is None:
                        continue
                    
                    slice = dicSeries['data'][0]
                    
                    dim = np.array(slice.pixel_array).shape
                    if len(dim) == 2:
                        dim = np.append(len(dicSeries['data']), dim)
                        
                    # 如果slice張數小於SKIP_SLICES(5張)，則略過
                    if dim[0] <= SKIP_SLICES:
                        continue
                    strDim = f'{dim[2]:<6}x {dim[1]:<6}x {dim[0]:<6}'
                    itemDimension = QStandardItem(strDim)
                    
                    itemPatientName = QStandardItem(str(slice.PatientName))
                    itemPatientID = QStandardItem(str(slice.PatientID))
                    itemPatientSex = QStandardItem(str(slice.PatientSex))
                    itemModality = QStandardItem(str(slice.Modality))
                    itemAcquisitionTime = QStandardItem(dicSeries.get('acquisitionDate'))
                    
                    spacing = []
                    spacingXY = dicSeries.get('spacingXY')
                    spacingZ = dicSeries.get('spacingZ')
                    strSpacing = ''
                    if spacingXY is None:
                        # QMessageBox.critical(None, 'dicom error', f'series UID [{slice.SeriesInstanceUID}] missing spacing infomation')
                        MessageBox.ShowCritical('dicom error', f'series UID [{slice.SeriesInstanceUID}] missing spacing infomation')
                        strSpacing = 'NONE'
                    else:
                        spacing = spacingXY[:]
                        if spacingZ:
                            spacing.append(spacingZ)
                        else:
                            spacing.append('NONE')
                        strSpacingX = f'{spacing[0]:<.3f}'.ljust(6)
                        strSpacingY = f'{spacing[1]:<.3f}'.ljust(6)
                        strSpacingZ = f'{spacing[2]:<.3f}'.ljust(6)
                        strSpacing = f'{strSpacingX}x {strSpacingY}x {strSpacingZ}'
                        
                    itemSpacing = QStandardItem(strSpacing)
                    itemPath = QStandardItem(dicSeries.get('path'))
                    
                    itemPatientName.setData(keyPatien, Qt.UserRole + 1)
                    itemPatientName.setData(keyStudy, Qt.UserRole + 2)
                    itemPatientName.setData(keySeries, Qt.UserRole + 3)
                    
                    row = []
                    row.append(itemPatientName)
                    row.append(itemPatientID)
                    row.append(itemPatientSex)
                    row.append(itemModality)
                    row.append(itemDimension)
                    row.append(itemSpacing)
                    row.append(itemAcquisitionTime)
                    row.append(itemPath)
                    
                    # change background-color
                    for i in range(len(row)):
                        if i % 2 == 1:
                            row[i].setData(QColor(0, 0, 255, 30), role = Qt.BackgroundRole)
                        else:
                            row[i].setData(QColor(0, 255, 255, 30), role = Qt.BackgroundRole)
                    
                    model.appendRow(row)
                    
                    # filter
                    bHasChild = False
                    # for childRow in range(rowSelectAll[0].rowCount()):
                    for childRow in range(rowSelectAll[0].rowCount()):
                        # if not modelFilter.findItems(row[1].text(), column = 1):
                        if rowSelectAll[0].child(childRow, 1) is not None:
                            if rowSelectAll[0].child(childRow, 1).text() == row[1].text():
                                bHasChild = True
                                break
                        
                    if not bHasChild:
                        rowFilter = [QStandardItem(item.text()) for item in row[:3]]
                        rowFilter[0].setCheckable(True)
                        rowFilter[0].setCheckState(Qt.Checked)
                        rowSelectAll[0].appendRow(rowFilter)
                        # modelFilter.appendRow(rowFilter)
                        
                    # model.appendRow(rowNew)
                        
        # for row in range(len(data)):
        #     rowNew = []
        #     for col in range(len(data[row])):
        #         item = QStandardItem(data[row][col])
        #         if col % 2 == 1:
        #             item.setData(QColor(0, 0, 255, 30), role = Qt.BackgroundRole)
        #         else:
        #             item.setData(QColor(0, 255, 255, 30), role = Qt.BackgroundRole)
                    
        #         rowNew.append(item)
            
        #     bHasChild = False
        #     for childRow in range(rowSelectAll[0].rowCount()):
        #         # if not modelFilter.findItems(data[row][1], column = 1):
        #         if rowSelectAll[0].child(childRow, 1).text() == data[row][1]:
        #             bHasChild = True
        #             break
                
        #     if not bHasChild:
        #         rowFilter = [QStandardItem(item) for item in data[row][:3]]
        #         rowFilter[0].setCheckable(True)
        #         rowFilter[0].setCheckState(Qt.Checked)
        #         rowSelectAll[0].appendRow(rowFilter)
        #         # modelFilter.appendRow(rowFilter)
                
        #     model.appendRow(rowNew)
        
            
        model.sort(6, Qt.DescendingOrder)
        
        model.setHeaderData(0, Qt.Horizontal, QColor(0, 0, 255, 100), role = Qt.BackgroundRole)
        self.treeDicom.setModel(model)
        
        
        # header = self.treeDicom.header()
        # header.setSectionResizeMode(QHeaderView.ResizeToContents)
        # header.setDefaultAlignment(Qt.AlignHCenter)
        
        modelFilter.sort(1, Qt.AscendingOrder)
        modelFilter.itemChanged.connect(self.onTreeItemChanged)
        self.treeDicomFilter.setModel(modelFilter)
        self.treeDicomFilter.expandAll()
        # self.treeDicom.selectionModel().currentRowChanged.connect(self.OnCurrentRowChanged_treeDicom)
        self.treeDicom.selectionModel().selectionChanged.connect(self.OnSelectionChanged_treeDicom)
        # header = self.treeDicomFilter.header()
        # header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.dicSelectedSeries = {0:{'selected':[]}, 
                                  1:{'selected':[]}
                                  }
        
        
    def eventFilter(self, obj, event):
        if obj == self.treeDicom and event.type() == QEvent.Leave:
            pass
            # print("Mouse left QTreeView")
        return super().eventFilter(obj, event)
        
        
    def onTreeItemChanged(self, item:QStandardItem):
        if not item:
            return
        
        if item.isCheckable():
            if item.isAutoTristate():
                checkState = item.checkState()
                if checkState != Qt.PartiallyChecked:
                    self.treeItemCheckAll(item, checkState)
            else:
                checkState = self.checkChildAlterParent(item)
                parent = item.parent()
                if parent:
                    parent.setCheckState(checkState)
            
                self.treeDicomViewFilter(item)
            
                
    def checkChildAlterParent(self, item:QStandardItem):
                
        parent = item.parent()
        if parent is None:
            return item.checkState()
        
        siblingCount = parent.rowCount()
        checkCount = 0
        uncheckedCount = 0
        for iRow in range(siblingCount):
            item = parent.child(iRow)
            state = item.checkState()
            
            if state == Qt.Checked:
                checkCount += 1
            elif state == Qt.Unchecked:
                uncheckedCount += 1
                
            if checkCount > 0 and uncheckedCount > 0:
                return Qt.PartiallyChecked
        if checkCount > 0:
            return Qt.Checked
        return Qt.Unchecked
    
    def getSeriesFromModelIndex(self, index:QModelIndex):
        model = self.treeDicom.model()
        index = index.sibling(index.row(), 0)
        item:QStandardItem = model.itemFromIndex(index)
        if item:
            idPatient = item.data(Qt.UserRole + 1)
            idStudy   = item.data(Qt.UserRole + 2)
            idSeries  = item.data(Qt.UserRole + 3)
            # print(f'patient ID = {idPatient}')
            # print(f'Study ID   = {idStudy}')
            # print(f'Series ID  = {idSeries}')
            # print(f'No.{i} : {item.data(Qt.UserRole + 4)}')
            selectedSeries = [idPatient, idStudy, idSeries, index.row()]
            # self.selectedSeries.append(selectedSeries)
            # if len(self.selectedSeries) > 2:
            #     self.selectedSeries.pop(0)
            # self.reader.SelectDataFromID(idPatient, idStudy, idSeries, i)
            return selectedSeries
        else:
            return None
        
    def getInfoFromModelIndex(self, index:QModelIndex):
        model = self.treeDicom.model()
        row = index.row()
        item:QStandardItem = model.item(row, 4)
        dim = item.text()
        
        item:QStandardItem = model.item(row, 5)
        voxel = item.text()
        strDim = 'Dim'
        strVoxel = 'Voxel'
        strText = f'{strDim:10}{dim}\n{strVoxel:10}{voxel}'
        dimZ = int(dim.split('x')[-1])
        
        return strText, dimZ
    
    def resumeStored(self):
        """從已儲存的資料中，恢復至UI介面上"""
        trajectoryLength = self.currentTag.get('trajectoryLength')
        trajectoryValue  = self.currentTag.get('trajectoryValue')
        if trajectoryValue and trajectoryLength:
            self.sldTrajectory.setMaximum(trajectoryLength)
            self.sldTrajectory.setValue(trajectoryValue)
            
        for key, view in self.viewport_L.items():
            strKey = 'index_' + key
            index = self.currentTag.get(strKey)
            combox = view.uiCbxOrientation
            if index is not None and isinstance(combox, QComboBox):
                view.currentIndex = index
                combox.blockSignals(True)
                combox.setCurrentIndex(index)
                combox.blockSignals(False)
            else:
                print(f'Error: [{strKey}] = {index}')
        
        
            
    def treeDicomViewFilter(self, item:QStandardItem):
        if not item:
            return
        
        # if item.hasChildren():
        #     self.treeItemCheckAll(item, checkState)
        #     return
        checkState = item.checkState()
        rowSelectAll = self.treeDicomFilter.model().item(0, 0)
        item = rowSelectAll.child(item.row(), 1)
        
        text = item.text()
        col = item.column()
        if checkState == Qt.Unchecked:
            model = self.treeDicom.model()
            listItem = model.findItems(text, column = col)
            for item in listItem:
                rowData = model.takeRow(item.row())
                self.modelHide.appendRow(rowData)
        else:
            listItem = self.modelHide.findItems(text, column = col)
            for item in listItem:
                rowData = self.modelHide.takeRow(item.row())
                
                model = self.treeDicom.model()
                model.appendRow(rowData)
                model.sort(6, Qt.DescendingOrder)
            
    def treeItemCheckAll(self, item:QStandardItem, checkState:Qt.CheckState):
        # if checkState == Qt.Unchecked:
        for row in range(item.rowCount()):
            item.child(row, 0).setCheckState(checkState)
            
    def setTreeDicomUserRole(self, data, nRow:int = None, modelIndex = None):
        
        model:QStandardItemModel = self.treeDicom.model()
        column_count = model.columnCount()
        
        if nRow is not None:
            for col in range(column_count):
                item = model.item(nRow, col)
                item.setData(data, Qt.UserRole + 4)
                
        elif modelIndex is not None:
            if isinstance(modelIndex, QModelIndex):
                row = modelIndex.row()
                for col in range(column_count):
                    item = model.item(row, col)
                    item.setData(data, Qt.UserRole + 4)
                    
            elif isinstance(modelIndex, list):
                for index in modelIndex:
                    if not model.setItemData(index, {Qt.UserRole + 4: data}):
                        print('error occurred in set UserRole data')
                
            
        
    def init_ui(self):
        self.stkMain.setCurrentIndex(0)
        self.stkScene.setCurrentIndex(0)
        
        self.treeDicom.setStyleSheet("""
            QHeaderView::section {
                background-color: #3498db;  
                color: white;  
                text-align: center; 
                font-size:12pt; 
            }
            
            QTreeView::item{
                text-align:center;
            }
            """)
        
        self.wdgPlanning.clicked.connect(self.onClick_Planning)
        self.wdgGuidance.clicked.connect(self.OnClicked_btnGuidance)
        self.stkScene.currentChanged.connect(self.SceneChanged)
        self.stkMain.currentChanged.connect(self.MainSceneChanged)
        self.signalLoadingReady.connect(self.onSignal_LoadingReady)
        self.signalSetProgress.connect(self.onSignal_SetProgress)
        self.signalShowMessage.connect(self.onSignal_ShowMessage)
        self.signalModelBuildingUI.connect(self.onSignal_ModelBuilding)
        self.signalModelBuildingPass.connect(self.Laser_OnSignalModelPassed)
        
        self.signalSetCheck.connect(self.onSignal_SetCheck)
        
        self.btnNext_confirmHomingStep2.clicked.connect(self.Robot_StartHoming)
        # self.btnNext_settingRobot.clicked.connect(self.Robot_StartHoming)
        
        self.laserFigure = Canvas(self, dpi = 150)
        self.lytLaserAdjust = QVBoxLayout(self.wdgLaserPlot)
        self.lytLaserAdjust.addWidget(self.laserFigure)
        
        self.btnSceneLaser.setEnabled(False)
        self.btnSceneRobot.setEnabled(False)
        self.btnSceneRobot.clicked.connect(self.ToSceneRobotSetting)
        self.btnSceneLaser.clicked.connect(self.ToSceneLaser)
        self.btnSceneView.clicked.connect(self.ToSceneView)
        
        self.SetStageButtonStyle(0)
        
        self.wdgNaviBar.layout().setAlignment(self.btnSceneRobot, Qt.AlignCenter)
        self.wdgNaviBar.layout().setAlignment(self.btnSceneLaser, Qt.AlignCenter)
        self.wdgNaviBar.layout().setAlignment(self.btnSceneView, Qt.AlignCenter)
        
        self.sldWindowLevel.valueChanged.connect(self.OnChanged_sldWindowLevel)
        self.sldWindowWidth.valueChanged.connect(self.OnChanged_sldWindowWidth)
        self.currentDicom = self.buttonGroup.checkedButton().objectName()
        
        self.buttonGroup.buttonToggled.connect(self.OnToggled_buttonGroup)
        self.btgDicom.buttonToggled.connect(self.OnToggled_btgDIcom)
        
        self.btnDriveTo.clicked.connect(self.OnClicked_btnDriveTo)
        
        self.tbsCTScan.selectionChanged.connect(self.OnSelection)
        
        self.tabWidget.currentChanged.connect(self.OnCurrentChange_tabWidget)
        
        self.cbxLanguage.currentIndexChanged.connect(self.OnChanged_cbxLanguage)
        
        self.btnCancel.clicked.connect(self.OnClicked_btnCancel)
        self.btnSetEntry.clicked.connect(self.OnClicked_btnSetEntry)
        self.btnSetTarget.clicked.connect(self.OnClicked_btnSetTarget)
        
        self.btnToEntry.clicked.connect(self.OnClicked_btnToEntry)
        self.btnToTarget.clicked.connect(self.OnClicked_btnToTarget)
        self.sldTrajectory.valueChanged.connect(self.OnValueChanged_sldTrajectory)
        
        self.btnDicomLow.clicked.connect(self.OnClicked_btnDicomLow)
        self.btnDicomHigh.clicked.connect(self.OnClicked_btnDicomHigh)
        
        for combobox in self.dicViewSelector_L.values():
            combobox.currentIndexChanged['QString'].connect(self.OnChangeIndex_ViewSelect)
            
        model = QStandardItemModel()
        stringList = ['patient name', 'patient ID', 'sex', 'Modality', 'dim', 'voxel size','acqusition date', 'path']
        model.setHorizontalHeaderLabels(stringList)
        
        modelFilter = QStandardItemModel()
        stringList = ['patient name', 'patient ID', 'sex']
        modelFilter.setHorizontalHeaderLabels(stringList)
        
        rowSelectAll = [QStandardItem() for _ in range(3)]
        rowSelectAll[0].setCheckable(True)
        rowSelectAll[0].setCheckState(Qt.Checked)
        
        modelFilter.appendRow(rowSelectAll)
        modelFilter.itemChanged.connect(self.onTreeItemChanged)
        
        model.sort(6, Qt.DescendingOrder)
        model.setHeaderData(0, Qt.Horizontal, QColor(0, 0, 255, 100), role = Qt.BackgroundRole)
        self.treeDicom.setModel(model)
        self.treeDicom.setSelectionMode(QAbstractItemView.MultiSelection)
        
        header = self.treeDicom.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignHCenter)
        
        modelFilter.sort(1, Qt.AscendingOrder)
        self.treeDicomFilter.setModel(modelFilter)
        self.treeDicomFilter.expandAll()
        
        header = self.treeDicomFilter.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
        self.treeDicom.selectionModel().selectionChanged.connect(self.OnSelectionChanged_treeDicom)
        self.treeDicom.entered.connect(self.OnEntered_treeDicom)
        self.treeDicom.installEventFilter(self)
        self.treeDicom.setItemDelegate(TreeViewDelegate())
        
        self.player.error.connect(lambda:print(f'media player error:{self.player.errorString()}'))
        
        self.btnRobotRelease.clicked.connect(self.Robot_ReleaseArm)
        self.btnRobotFix.clicked.connect(self.Robot_FixArm)
        self.btnRobotSetTarget.clicked.connect(self.Robot_SettingTarget)
        self.btnRobotBackTarget.clicked.connect(self.Robot_BackToTarget)
        
        self.btnStartBuildModel_2.clicked.connect(self.Laser_StartRecordBreathingBase)
        self.spinBox.valueChanged.connect(self.OnValueChanged_spin)
        self.btnRecord.clicked.connect(self.Laser_OnClick_btnRecord)
        self.btnAutoRecord.clicked.connect(self.Laser_OnClick_btnAutoRecord)
        
        self.btnReloadDicom.clicked.connect(self.OnClicked_btnReloadDicom)
        
        self.btnDriveConfirm.clicked.connect(self.OnClicked_btnDriveConfirm)
        
        self.btnUnlockRobot.clicked.connect(self.Robot_ReleaseArm)
        
        self.btnUnlockRobot_2.clicked.connect(self.Robot_ReleaseArm)
        
        self.btnRobotRelease_2.clicked.connect(self.Robot_ReleaseArm)
        self.btnRobotTarget.clicked.connect(self.Robot_FixAndTarget)
        
    def Focus(self, pos):
        # indexL = self.tabWidget.indexOf(self.tabWidget_Low)
        # indexH = self.tabWidget.indexOf(self.tabWidget_High)
        
        # if self.tabWidget.currentIndex() == indexL:
        for view in self.viewport_L.values():
            view.Focus(pos)
                # view.MapPositionToImageSlice(pos)
        # elif self.tabWidget.currentIndex() == indexH:
        #     for key, view in self.viewPortH.items():
        #         view.Focus(pos)
             
    def ChangeSlice_L(self, pos):
        
        if isinstance(pos, list) or isinstance(pos, tuple):
            pos = np.array(pos)
        
        # self.lblSagittal.setText(f'{pos[0]}')
        # self.lblCoronal.setText(f'{pos[1]}')
        # self.lblAxial.setText(f'{pos[2]}')
        
        for view in self.viewport_L.values():
            view.ChangeSliceView(pos)
            
    def ChangeSlice_H(self, pos):
        
        if isinstance(pos, list) or isinstance(pos, tuple):
            pos = np.array(pos)
        
        # self.lblSagittal.setText(f'{pos[0]}')
        # self.lblCoronal.setText(f'{pos[1]}')
        # self.lblAxial.setText(f'{pos[2]}')
        
        for view in self.viewport_H.values():
            view.ChangeSliceView(pos)
            
    def GetCurrentRendererCallback(self, renderer):
        bUpdate = False
        if self.currentRenderer is not None and self.currentRenderer != renderer:
            self.currentRenderer.SetSelectedOff()
            bUpdate = True
            
            if self.currentStyle:
                if isinstance(self.currentStyle, InteractorStyleImageAlgorithm):
                    self.currentStyle.ResumeRendererStyle()
                    self.currentStyle.StartInteractor(renderer)
                    
                    if renderer.orientation == VIEW_3D:
                        self.currentStyle.SetActor(renderer.volume)
                    else:
                        self.currentStyle.SetActor(renderer.actorImage)
                    
        self.currentRenderer = renderer
        renderer.SetSelectedOn()
        
        if bUpdate:
            self.UpdateView()
                  
    def ImportDicom_L(self):
        """load inhale (Low breath) DICOM to get image array and metadata
        """
        ############################################################################################
        ## 用 VTK 顯示 + 儲存 VT形式的影像 ############################################################################################
        "VTK stage"
        self.vtkImageLow, spacing, listSeries = self.reader.GetData(index = 0)
        self.imageL = self.reader.arrImage
        
        if self.vtkImageLow is None:
            # QMessageBox.critical(None, 'ERROR', 'image error')
            MessageBox.ShowCritical('ERROR', 'image error')
            return False
        
        # if self.currentTag == self.dicDicom.get(self.btnDicomLow.objectName()):
        self.dicomLow.LoadImage(self.vtkImageLow)
        dicomTag = self.SetDicomData(self.dicomLow, 'LOW')
        
        if not dicomTag:
            # QMessageBox.critical(None, 'DICOM TAG ERROR', 'missing current tag [LOW]')
            MessageBox.ShowCritical( 'DICOM TAG ERROR', 'missing current tag [LOW]')
            return False
        
        self.currentTag['spacing'] = spacing
        self.currentTag['series'] = listSeries
        # elif self.currentTag == self.dicDicom.get(self.btnDicomHigh.objectName()):
        #     self.dicomHigh.LoadImage(self.vtkImageHigh)
        #     self.SetDicomData(self.dicomHigh, 'HIGH')
        
        
        # imageVTKHu = self.dicomLow.LoadImage('C:/Leon/CT/sT1W_3D__2853/sT1W_3D__2853', self.vtkImage)
        # self.dicomHigh.LoadImage('C:/Leon/CT/S62090/S3010')
        ############################################################################################
        ## 設定 window width 和 window level 初始值 ############################################################################################
        ### 公式1
        
        # thresholdValue = int(((self.dicomLow.dicomGrayscaleRange[1] - self.dicomLow.dicomGrayscaleRange[0]) / 6) + self.dicomLow.dicomGrayscaleRange[0])
        # self.SetDicomData(self.dicomLow, 'LOW')
        # self.SetDicomData(self.dicomHigh, 'HIGH')
        
        # if self.currentTag is None:
        #     self.currentTag = self.dicDicom.get(self.currentDicom)
        #     print(f'dicom name = {self.currentTag}')
        #     if self.currentTag is None:
        #         print('dicom tag name error')
        #         return False
            
        if not self.SetRegistration_L():
            # QMessageBox.critical(None, 'ERROR', 'Registration Failed')
            MessageBox.ShowCritical('ERROR', 'Registration Failed')
            return False
        
            
        ############################################################################################
        ## 顯示 dicom 到 ui 上 ############################################################################################
        self.ShowDicom_L()
        self.bDicomChanged = False
        ## 啟用 ui ############################################################################################
        "Enable ui"
        # self.Slider_WW_L.setEnabled(True)
        # self.Slider_WL_L.setEnabled(True)
        # self.SliceSelect_Axial_L.setEnabled(True)
        # self.SliceSelect_Sagittal_L.setEnabled(True)
        # self.SliceSelect_Coronal_L.setEnabled(True)
        # self.Button_Registration_L.setEnabled(True)
        # self.tabWidget.setCurrentWidget(self.tabWidget_Low)
        # ############################################################################################
        # self.ui_SP.close()
        return True
    
    def ImportDicom_H(self):
        "VTK stage"
        # self.vtkImageHigh = self.reader.GetDataFromIndex(0, 0, -1)
        self.vtkImageHigh, spacing, listSeries = self.reader.GetData(index = 1)
        self.imageH = self.reader.arrImage
        
        if self.vtkImageHigh is None:
            # QMessageBox.critical(None, 'ERROR', 'image error')
            MessageBox.ShowCritical('ERROR', 'image error')
            return False
        
        # if self.currentTag == self.dicDicom.get(self.btnDicomHigh.objectName()):
        self.dicomHigh.LoadImage(self.vtkImageHigh)
        dicomTag = self.SetDicomData(self.dicomHigh, 'HIGH')
        
        if not dicomTag:
            # QMessageBox.critical(None, 'DICOM TAG ERROR', 'missing current tag [HIGH]')
            MessageBox.ShowCritical('DICOM TAG ERROR', 'missing current tag [HIGH]')
            return False
        
        self.currentTag['spacing'] = spacing
        self.currentTag['series'] = listSeries
        
        if not self.SetRegistration_H():
            # QMessageBox.critical(None, 'ERROR', 'Registration Failed')
            MessageBox.ShowCritical('ERROR', 'Registration Failed')
            return False
        ############################################################################################
        ## 顯示 dicom 到 ui 上 ############################################################################################
        self.ShowDicom_H()
        self.bDicomChanged = False
        ## 啟用 ui ############################################################################################
        "Enable ui"
        return True
    
    
        
    def SetDicomData(self, dicom:DISPLAY, type:str):
        thresholdValue = int(((dicom.dicomGrayscaleRange[1] - dicom.dicomGrayscaleRange[0]) / 6) + dicom.dicomGrayscaleRange[0])
        
        if type.upper() == 'LOW':
            tag = self.dicDicom.get(self.btnDicomLow.objectName())
        elif type.upper() == 'HIGH':
            tag = self.dicDicom.get(self.btnDicomHigh.objectName())
            
        if tag is not None:
            tag['ww'] = abs(thresholdValue * 2)
            tag['wl'] = thresholdValue
            tag['display'] = dicom
            
            self.currentTag = tag
            return tag
        
                
    def SetUIEnable_Trajectory(self, bEnable):
        self.btnToEntry.setEnabled(bEnable)
        self.btnToTarget.setEnabled(bEnable)
        self.sldTrajectory.setEnabled(bEnable)
    
    def ShowDicom_L(self):
        """show low dicom to ui
        """
        #Initialize window level / window width
        #Dicom Low
        self.sldWindowWidth.blockSignals(True)
        self.sldWindowWidth.setMinimum(0)
        self.sldWindowWidth.setMaximum(int(abs(self.dicomLow.dicomGrayscaleRange[0]) + self.dicomLow.dicomGrayscaleRange[1]))
        # self.currentTag['ww'] = abs(thresholdValue * 2)
        self.sldWindowWidth.setValue(self.currentTag.get('ww'))
        self.sldWindowWidth.blockSignals(False)
        
        "WindowCenter / WindowLevel"
        self.sldWindowLevel.blockSignals(True)
        self.sldWindowLevel.setMinimum(int(self.dicomLow.dicomGrayscaleRange[0]))
        self.sldWindowLevel.setMaximum(int(self.dicomLow.dicomGrayscaleRange[1]))
        # self.currentTag['wl'] = thresholdValue
        self.sldWindowLevel.setValue(self.currentTag.get('wl'))
        self.sldWindowLevel.blockSignals(False)
        
        
            
        ## 用 vtk 顯示 diocm ############################################################################################
        # if self.viewport_L:
        #     for view in self.viewport_L.values():
        #         view.Reset() 
        self.ResetView()
                
        self.viewport_L = {}
        
        orientationLT = self.currentTag.get('O_LT')
        orientationRT = self.currentTag.get('O_RT')
        orientationLB = self.currentTag.get('O_LB')
        orientationRB = self.currentTag.get('O_RB')
        
        if not orientationLT:
            orientationLT = VIEW_3D
            
        if not orientationRT:
            orientationRT = VIEW_AXIAL
            
        if not orientationLB:
            orientationLB = VIEW_SAGITTAL
            
        if not orientationRB:
            orientationRB = VIEW_CORONAL
            
        self.viewport_L["LT"] = ViewPortUnit(self, self.dicomLow, self.wdgLeftTop, orientationLT, self.sbrLeftTop, self.cbxLeftTop)
        self.viewport_L["RT"] = ViewPortUnit(self, self.dicomLow, self.wdgRightTop, orientationRT, self.sbrRightTop, self.cbxRightTop)
        self.viewport_L["LB"] = ViewPortUnit(self, self.dicomLow, self.wdgLeftBottom, orientationLB, self.sbrLeftBottom, self.cbxLeftBottom)
        self.viewport_L["RB"] = ViewPortUnit(self, self.dicomLow, self.wdgRightBottom, orientationRB, self.sbrRightBottom, self.cbxRightBottom)
        self.syncInteractorStyle = SynchronInteractorStyle(self.viewport_L)
        
        
        
        self.currentRenderer = self.viewport_L['LT'].renderer
        self.currentRenderer.SetSelectedOn()
        # 綁定GetRenderer signal
        # for widget in self.vtkWidgets_L:
        #     iStyle = widget.GetRenderWindow().GetInteractor().GetInteractorStyle()
            
        
        for view in self.viewport_L.values():
            iStyle = view.iren.GetInteractorStyle()
            iStyle.signalObject.ConnectUpdateView(self.UpdateView)
            # iStyle.signalObject.ConnectUpdateHU(self.UpdateHU_L)
            iStyle.signalObject.ConnectGetRenderer(self.GetCurrentRendererCallback)
            
            # view.SetFocusMode(False)
            view.signalUpdateSlice.connect(self.ChangeSlice_L)
            view.signalUpdateAll.connect(self.UpdateTarget)
            view.signalUpdateExcept.connect(self.UpdateTarget)
            view.signalFocus.connect(self.Focus)
            view.signalChangedTrajPosition.connect(self.ChangeTrajectorySlider)
            # view.signalSetSliceValue.connect(self.SetSliceValue_L)
        
        # 強制更新第一次
        # self.SetSliceValue_L(self.dicomLow.imagePosition)
        
        """trajectory"""
        # trajectoryLength = self.currentTag.get('trajectoryLength')
        # trajectoryValue  = self.currentTag.get('trajectoryValue')
        # if trajectoryValue and trajectoryLength:
        #     self.sldTrajectory.setMaximum(trajectoryLength)
        #     self.sldTrajectory.setValue(trajectoryValue)
        self.resumeStored()
            
        self.UpdateView()
        
    def ShowDicom_H(self):
        """show low dicom to ui
        """
        #Dicom Low
        self.sldWindowWidth.blockSignals(True)
        self.sldWindowWidth.setMinimum(0)
        self.sldWindowWidth.setMaximum(int(abs(self.dicomHigh.dicomGrayscaleRange[0]) + self.dicomHigh.dicomGrayscaleRange[1]))
        self.sldWindowWidth.setValue(self.currentTag.get('ww'))
        self.sldWindowWidth.blockSignals(False)
        
        "WindowCenter / WindowLevel"
        self.sldWindowLevel.blockSignals(True)
        self.sldWindowLevel.setMinimum(int(self.dicomHigh.dicomGrayscaleRange[0]))
        self.sldWindowLevel.setMaximum(int(self.dicomHigh.dicomGrayscaleRange[1]))
        self.sldWindowLevel.setValue(self.currentTag.get('wl'))
        self.sldWindowLevel.blockSignals(False)
        ## 用 vtk 顯示 diocm ############################################################################################
        # if self.viewport_H:
        #     for view in self.viewport_H.values():
        #         view.Reset() 
        if self.viewport_L:
            for view in self.viewport_L.values():
                view.Reset() 
                
        # self.viewport_H = {}
        self.viewport_L = {}
        
        # self.viewport_H["LT"] = ViewPortUnit(self, self.dicomHigh, self.wdgLeftTop, VIEW_3D, self.sbrLeftTop, self.cbxLeftTop)
        # self.viewport_H["RT"] = ViewPortUnit(self, self.dicomHigh, self.wdgRightTop, VIEW_AXIAL, self.sbrRightTop, self.cbxRightTop)
        # self.viewport_H["LB"] = ViewPortUnit(self, self.dicomHigh, self.wdgLeftBottom, VIEW_SAGITTAL, self.sbrLeftBottom, self.cbxLeftBottom)
        # self.viewport_H["RB"] = ViewPortUnit(self, self.dicomHigh, self.wdgRightBottom, VIEW_CORONAL, self.sbrRightBottom, self.cbxRightBottom)
        # self.syncInteractorStyle = SynchronInteractorStyle(self.viewport_H)
        self.viewport_L["LT"] = ViewPortUnit(self, self.dicomHigh, self.wdgLeftTop, VIEW_3D, self.sbrLeftTop, self.cbxLeftTop)
        self.viewport_L["RT"] = ViewPortUnit(self, self.dicomHigh, self.wdgRightTop, VIEW_AXIAL, self.sbrRightTop, self.cbxRightTop)
        self.viewport_L["LB"] = ViewPortUnit(self, self.dicomHigh, self.wdgLeftBottom, VIEW_SAGITTAL, self.sbrLeftBottom, self.cbxLeftBottom)
        self.viewport_L["RB"] = ViewPortUnit(self, self.dicomHigh, self.wdgRightBottom, VIEW_CORONAL, self.sbrRightBottom, self.cbxRightBottom)
        self.syncInteractorStyle = SynchronInteractorStyle(self.viewport_L)
        
        
        # self.currentRenderer = self.viewport_H['LT'].renderer
        self.currentRenderer = self.viewport_L['LT'].renderer
        self.currentRenderer.SetSelectedOn()
        # 綁定GetRenderer signal
        # for widget in self.vtkWidgets_L:
        #     iStyle = widget.GetRenderWindow().GetInteractor().GetInteractorStyle()
            
        
        # for view in self.viewport_H.values():
        for view in self.viewport_L.values():
            iStyle = view.iren.GetInteractorStyle()
            iStyle.signalObject.ConnectUpdateView(self.UpdateView)
            # iStyle.signalObject.ConnectUpdateHU(self.UpdateHU_L)
            iStyle.signalObject.ConnectGetRenderer(self.GetCurrentRendererCallback)
            
            # view.SetFocusMode(False)
            # view.signalUpdateSlice.connect(self.ChangeSlice_H)
            view.signalUpdateSlice.connect(self.ChangeSlice_L)
            view.signalUpdateAll.connect(self.UpdateTarget)
            view.signalUpdateExcept.connect(self.UpdateTarget)
            view.signalFocus.connect(self.Focus)
            # view.signalSetSliceValue.connect(self.SetSliceValue_L)
        
        # 強制更新第一次
        # self.SetSliceValue_L(self.dicomLow.imagePosition)
        
        """trajectory"""
        # trajectoryLength = self.currentTag.get('trajectoryLength')
        # trajectoryValue  = self.currentTag.get('trajectoryValue')
        # if trajectoryValue and trajectoryLength:
        #     self.sldTrajectory.setMaximum(trajectoryLength)
        #     self.sldTrajectory.setValue(trajectoryValue)
        self.resumeStored()
        self.UpdateView()
        
    def UpdateView(self):
        for view in self.dicView.values():
            iren = view.GetRenderWindow().GetInteractor()
            iren.Initialize()
            iren.Start()
        
        if self.currentTag is not None:
            wl = self.currentTag.get('wl')
            if wl is not None:
                self.sldWindowLevel.setValue(wl)
                
            ww = self.currentTag.get('ww')
            if ww is not None:
                self.sldWindowWidth.setValue(ww)
            
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
                view.ChangeSliceView()
                # view.UpdateView()
                
    def GetViewPort(self):
        # indexL = self.tabWidget.indexOf(self.tabWidget_Low)
        # indexH = self.tabWidget.indexOf(self.tabWidget_High)
        
        # if self.tabWidget.currentIndex() == indexL:
        return self.viewport_L
        # elif self.tabWidget.currentIndex() == indexH:
        #     return self.viewPortH
        
        # return None
        
    def OnClicked_btnGuidance(self):
        self.stkMain.setCurrentWidget(self.page_loading)
        
    def OnClicked_btnDriveTo(self):
        if self.language == LAN_CN:
            translator = QTranslator()
            translator.load('FunctionLib_UI/Ui_dlgInstallAdaptor_tw.qm')
            QCoreApplication.installTranslator(translator)
            
        self.Laser_OnTracking()
        
        dlgDriveTo = DlgInstallAdaptor()
        dlgDriveTo.signalRobotStartMoving.connect(self.Laser_StopTracking)
        dlgDriveTo.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        dlgDriveTo.setModal(True)
        dlgDriveTo.exec_()
        # self.listSubDialog.append(dlgDriveTo)
        
        # dlgRobotMoving = DlgRobotMoving()
        # dlgRobotMoving.signalStop.connect(self.Robot_Stop)
        # dlgRobotMoving.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        # dlgRobotMoving.setModal(True)
        # dlgRobotMoving.exec_()
        
        self.stkSignalLight.setCurrentWidget(self.pgGreenLight)
        
    def OnClicked_btnCancel(self):
        self.stkScene.setCurrentIndex(self.indexPrePage)
        
    def OnClicked_btnSetEntry(self):
        
        if self.currentTag.get("pickPoint") is None:
            return
        
        pickPoint = self.currentTag.get("pickPoint").copy()
        currentDicom = self.currentTag.get('display')
        if pickPoint is not None and currentDicom is not None:
            currentDicom.DrawPoint(pickPoint, 1)      
            currentDicom.entryPoint = pickPoint
            self.currentTag["entry"] = np.array(pickPoint)
            
            if self.currentTag.get("target") is not None:
                self.currentTag.update({"flageSelectedPoint": True})
                
                point2 = self.currentTag.get("target")
                # currentDicom.CreateLine(pickPoint, point2)
                self.modifyTrajectory(currentDicom, pickPoint, point2)
                self.SetUIEnable_Trajectory(True)
                self.addCrossSectionItemInSelector()
            self.UpdateView()
            
    
    def OnClicked_btnSetTarget(self):
        
        if self.currentTag.get("pickPoint") is None:
            return
        
        pickPoint = self.currentTag.get("pickPoint").copy()
        currentDicom = self.currentTag.get('display')
        if pickPoint is not None and currentDicom is not None:
            currentDicom.DrawPoint(pickPoint, 2)
            currentDicom.targetPoint = pickPoint
            self.currentTag["target"] = np.array(pickPoint)
            
            if self.currentTag.get("entry") is not None:
                self.currentTag.update({"flageSelectedPoint": True})
                
                point1 = self.currentTag.get("entry")
                # self.dicomLow.CreateLine(point1, pickPoint)
                self.modifyTrajectory(currentDicom, point1, pickPoint)
                self.SetUIEnable_Trajectory(True)
                self.addCrossSectionItemInSelector()
            self.UpdateView()
            
    def OnClicked_btnToEntry(self):
        currentDicom = self.currentTag.get('display')
        if not currentDicom:
            return
        
        entryPoint = currentDicom.entryPoint
        if entryPoint is not None:
            bHasCrossSection = False
            self.sldTrajectory.setValue(self.sldTrajectory.maximum())
            # for view in self.viewport_L.values():
            #     if view.orientation == VIEW_AXIAL or \
            #         view.orientation == VIEW_CORONAL or \
            #         view.orientation == VIEW_SAGITTAL:
                        
            #         view.MapPositionToImageSlice(entryPoint)
            #         if bHasCrossSection == True:
            #             break
            #     elif view.orientation == VIEW_CROSS_SECTION:
            #         bHasCrossSection = True
            #         view.uiScrollSlice.blockSignals(True)
            #         view.uiScrollSlice.setValue(view.uiScrollSlice.maximum())
            #         view.uiScrollSlice.blockSignals(False)
    
    def OnClicked_btnToTarget(self):
        currentDicom = self.currentTag.get('display')
        if not currentDicom:
            return
        
        targetPoint = currentDicom.targetPoint
        if targetPoint is not None:
            bHasCrossSection = False
            self.sldTrajectory.setValue(0)
            # for view in self.viewport_L.values():
            #     if view.orientation == VIEW_AXIAL or \
            #         view.orientation == VIEW_CORONAL or \
            #         view.orientation == VIEW_SAGITTAL:
                        
            #         view.MapPositionToImageSlice(targetPoint)
            #         if bHasCrossSection == True:
            #             break
            #     elif view.orientation == VIEW_CROSS_SECTION:
            #         bHasCrossSection = True
            #         view.uiScrollSlice.blockSignals(True)
            #         view.uiScrollSlice.setValue(view.uiScrollSlice.minimum())
            #         view.uiScrollSlice.blockSignals(False)
            
    def OnClicked_btnDicomLow(self):
        # self.stkScene.setCurrentWidget(self.pgImportDicom)
        # self.ChangeCurrentDicom(self.btnDicomLow.objectName())
        pass
        
    def OnClicked_btnDicomHigh(self):
        # self.bDicomChanged = True
        # self.stkScene.setCurrentWidget(self.pgDicomList)
        # self.ChangeCurrentDicom(self.btnDicomHigh.objectName())
        pass
    
    def OnClicked_btnReloadDicom(self):
        ret = MessageBox.ShowWarning('This action will be import and replace existed dicom.\nconfirm that to press YES', 'YES', 'NO')
        if ret == 0:
            self.SetStage(STAGE_DICOM)
        # self.stkScene.setCurrentWidget(self.pgImportDicom)
        
    def OnClicked_btnDriveConfirm(self):
        nStep = self.wdgStep.Next()
        
        if nStep == 2:
            self.StopVedio()
            layout = self.wdgPicture.layout()
            layout.removeWidget(self.tmpWidget)
            self.tmpWidget = None
            self.wdgPicture.setStyleSheet('image:url(image/pedal_unlock.png);')
            
        elif nStep == 3:
            # self.btnUnlockRobot_2.setEnabled(False)
            self.btnUnlockRobot_2.setEnabled(True)
            self.btnDriveConfirm.setEnabled(False)
            
            self.lblDescription.setText("""
                                        <div style='color:#FFFFD0'>
                                        <p>1. Press <span style='color:#f00'>Unlock button</span> to release robot arm</p>
                                        <p>2. Press <span style='color:#f00'>foot pedal</span> and move robot arm <span style='color:#f00'>by hand</span></p>
                                        <p>3. Make sure the position is <span style='color:#f00'>convenient for draping robot arm</span></p>
                                        <p>4. Press Confirm to fix robot arm</p>
                                        </div>
                                        """)
            self.wdgPicture.setStyleSheet('image:url(image/draping-rob-surgical.jpg);')
        elif nStep == 4:
            self.Robot_FixArm()
            self.wdgPicture.setStyleSheet('image:url(image/pedal_lock.png);')
        elif nStep is None:
            self.stkScene.setCurrentWidget(self.pgImageView)
    
    def OnValueChanged_spin(self, value:int):
        fValue = value * 0.01
        gVars['toleranceLaserData'] = fValue
        self.lblThreshold.setText(str(fValue))
    
    def OnValueChanged_sldTrajectory(self, value):
        # print(f'value = {value}')
        # sldValue = self.sldTrajectory.maximum() - value
        entry  = self.currentTag.get('entry')
        target = self.currentTag.get('target')
        vector = entry - target
        
        vectorUnit = vector / np.linalg.norm(vector)
        newTarget = target + vectorUnit * value
        
        self.lblDistanceToTarget.setText(f'{value:.2f}mm')
        self.currentTag['trajectoryValue'] = value
        # print(f'target = {target}, value = {value}, newTarget = {newTarget}')
        
        bHasCrossSection = False
        for view in self.viewport_L.values():
            if view.orientation == VIEW_CROSS_SECTION:
                view.ChangeTrajectoryPosition(value)
                bHasCrossSection = True
                break
            
        if bHasCrossSection == False:
            for view in self.viewport_L.values():
                if view.orientation != VIEW_3D:
                    # view.MapPositionToImageSlice(pos = newTarget)
                    # imagePos = np.round(newTarget / view.renderer.pixel2Mm)
                    # view.ChangeSliceView(imagePos)
                    view.renderer.SetTarget(newTarget)
                    break
            self.UpdateTarget()
            self.UpdateView()
        # self.renderer.ChangeView(value)
        # # 還沒改完..
        
        # self.signalSetSliceValue.emit(self.dicom.imagePosition)
        
        # if self.orientation == VIEW_CROSS_SECTION:
        #     self.signalUpdateExcept.emit(VIEW_CROSS_SECTION)
        # else:
        #     self.signalUpdateAll.emit()
        # self.UpdateTarget(pos = newTarget)
        
        
        # for view in self.viewport_L.values():
        #     if (orientation is None) or (orientation != view.orientation):
                
        #         # print(f'orientation = {orientation}, view.orientation = {view.orientation}')
        #         if bFocus == True:
        #             view.Focus()
        #         view.renderer.SetTarget(pos)
        #         view.UpdateView()
            
    def OnChanged_sldWindowWidth(self, value):
        """set window width and show changed DICOM to ui
        """
        ## 設定 window width ############################################################################################
        currentDicom = self.currentTag.get('display')
        if not currentDicom:
            return
        
        # selectedDicomName = self.buttonGroup.checkedButton().objectName()
        # self.dicDicom[selectedDicomName]['ww'] = value
        self.currentTag['ww'] = value
        
        # wl = self.Slider_WL_L.value()
        # ww = self.Slider_WW_L.value()
        # compositeOpacity = vtk.vtkPiecewiseFunction()
        # compositeOpacity.AddPoint(wl - ww, 0.0)
        # compositeOpacity.AddPoint( wl, 0.8)
        # compositeOpacity.AddPoint( wl + ww, 1.0)
        # volumeProperty.SetScalarOpacity(compositeOpacity)
        
        # self.dicomLow.ChangeWindowWidthView(value)
        currentDicom.ChangeWindowWidthView(value)
        self.UpdateView()
        
    def OnChanged_sldWindowLevel(self, value):
        """set window width and show changed DICOM to ui
        """
        ## 設定 window level ############################################################################################
        currentDicom = self.currentTag.get('display')
        if not currentDicom:
            return
        
        # selectedDicomName = self.buttonGroup.checkedButton().objectName()
        # self.dicDicom[selectedDicomName]['wl'] = value
        self.currentTag['wl'] = value
        
        # wl = self.Slider_WL_L.value()
        # ww = self.Slider_WW_L.value()
        # compositeOpacity = vtk.vtkPiecewiseFunction()
        # compositeOpacity.AddPoint(wl - ww, 0.0)
        # compositeOpacity.AddPoint( wl, 0.8)
        # compositeOpacity.AddPoint( wl + ww, 1.0)
        # volumeProperty.SetScalarOpacity(compositeOpacity)
        
        # self.dicomLow.ChangeWindowLevelView(value)
        currentDicom.ChangeWindowLevelView(value)
        self.UpdateView()
        
    def OnChanged_cbxLanguage(self, index):
        
        python_exec = sys.executable
        scriptPath = sys.argv[0]
        # strLangaguePackage = 'C:/Leon/Aitherbot-Project-V1.9.5/FunctionLib_UI/Aitherbot_tw.qm'
        subprocess.Popen([python_exec, scriptPath, str(index)])
            
        
        sys.exit()
        
    def OnChangeIndex_ViewSelect(self, viewName):
        
        senderObj = self.sender()
        
        widget   = None
        for view in self.viewport_L.values():
            if view.uiCbxOrientation == senderObj:
                widget = view.vtkWidget
            
                if widget is not None:
                    #remove old renderer
                    renderWindow = widget.GetRenderWindow()
                    iren = renderWindow.GetInteractor()
                
                    viewName = viewName.split()[0]

                    #檢查該視窗是否已存在，若是則交換
                    bExist = False
                    for existView in self.viewport_L.values():
                        if existView.orientation == viewName:
                            bExist = True
                            break
                        
                    if bExist == True:
                        view.Swap(existView)
                    else:
                        currentDicom = self.currentTag.get('display')
                        if currentDicom is not None:
                            view.SetViewPort(viewName, currentDicom.rendererList[viewName])
                        else:
                            # QMessageBox.critical(None, 'DICOM ERROR', 'missing current dicom')
                            MessageBox.ShowCritical('DICOM ERROR', 'missing current dicom')
                        
                        iStyle = MyInteractorStyle(self, viewName)
                        # iStyle.signalObject.ConnectUpdateHU(self.UpdateHU_L)
                        iStyle.signalObject.ConnectGetRenderer(self.GetCurrentRendererCallback)
                        
                        # slider = self.dicSliceScroll_L['RT']
                        # rangeSlider = [slider.minimum(), slider.maximum(), slider.singleStep()]
                        
                        # slider = self.sldTrajectory
                        # rangeTraj = [slider.minimum(), slider.maximum(), slider.singleStep()]
                        # print(f'scroll = {rangeSlider}\nslider = {rangeTraj}')
                        
                        iren.SetInteractorStyle(iStyle)
                        iren.Initialize()
                        iren.Start()
        
        # 儲存目前view配置
        strList = ['LT', 'RT', 'LB', 'RB']
        for key in strList:
            strKey = 'O_' + key
            self.currentTag[strKey] = self.viewport_L[key].orientation
            
            strKey = 'index_' + key
            # self.currentTag[strKey] = self.viewport_L[key].currentIndex
            self.currentTag[strKey] = self.viewport_L[key].uiCbxOrientation.currentIndex()
            
    def OnEntered_treeDicom(self, index:QModelIndex):
        model:QStandardItemModel = self.treeDicom.model()
        # column_count = model.columnCount()
        
        index = index.sibling(index.row(), 0)
        selectedSeries = self.getSeriesFromModelIndex(index)
        
        if selectedSeries is not None:
            strText, dimZ = self.getInfoFromModelIndex(index)
            
            index = int(not self.bToggleInhale) # bToggleInhale == True, index = 0, else index = 1
            image = self.reader.GetSlice(selectedSeries[0], selectedSeries[1], selectedSeries[2], index, int(dimZ / 2))
            if index == 0:
                # if len(self.selectedSeries[0]) < 4:
                if len(self.dicSelectedSeries[0]['selected']) < 4:
                    self.lblInfoInhale.setText(strText)
                    if image is not None:
                        self.axInhale.imshow(image, cmap = plt.cm.gray)
                        self.canvasInhale.draw()
            else:
                # if len(self.selectedSeries[1]) < 4:
                if len(self.dicSelectedSeries[1]['selected']) < 4:
                    self.lblInfoExhale.setText(strText)
                    if image is not None:
                        self.axExhale.imshow(image, cmap = plt.cm.gray)
                        self.canvasExhale.draw()
    
    def OnSelectionChanged_treeDicom(self, selected:QItemSelection, deselected:QItemSelection):
        
        
        selectionModel = self.treeDicom.selectionModel()
        indexes:list = selectionModel.selectedRows()
        model:QStandardItemModel = self.treeDicom.model()
        column_count = model.columnCount()
        
        index = int(not self.bToggleInhale)
        # 將拖曳的複選取消
        if self.treeDicom.state() == QAbstractItemView.DragSelectingState:
            rows = []
            if len(selected.indexes()) > 0: 
                rows = selected.indexes()
                
                for index in rows:
                    selectedIndex = model.itemData(index).get(Qt.UserRole + 4)
                    if selectedIndex is None:
                        deselection = QItemSelection()
                        deselection.select(index, index)
                        
                        selectionModel.blockSignals(True)
                        selectionModel.select(deselection, QItemSelectionModel.Deselect)
                        selectionModel.blockSignals(False)
            elif len(deselected.indexes()) > 0:
                rows = deselected.indexes()
                
                for index in rows:
                    selectedIndex = model.itemData(index).get(Qt.UserRole + 4)
                    if selectedIndex is not None:
                        deselection = QItemSelection()
                        deselection.select(index, index)
                        
                        selectionModel.blockSignals(True)
                        selectionModel.select(deselection, QItemSelectionModel.Select)
                        selectionModel.blockSignals(False)
            return
        
        if selected.count() > 0:
            # get first column of selected.indexes() as currentIndex 
            currentIndex = selected.indexes()[0]
            selectedRow = self.getSeriesFromModelIndex(currentIndex)
                
            self.reader.SelectDataFromID(selectedRow[0], selectedRow[1], selectedRow[2], index)
            
            # when click once, auto switch to Exhale selection
            self.setTreeDicomUserRole(index + 1, modelIndex = selected.indexes())
                
            lstSelected = self.dicSelectedSeries[index].get('selected')
            if lstSelected is not None and len(lstSelected) == 4:
                oldRow = lstSelected[3]
                deselection = QItemSelection()
                deselection.select(model.index(oldRow, 0), model.index(oldRow, column_count - 1))
                
                self.setTreeDicomUserRole(None, oldRow)
                
                selectionModel.blockSignals(True)
                selectionModel.select(deselection, QItemSelectionModel.Deselect)
                selectionModel.blockSignals(False)
                
            patientID = selectedRow[0]
            studyID   = selectedRow[1]
            seriesID  = selectedRow[2]
            strText, dimZ = self.getInfoFromModelIndex(currentIndex)
            image = self.reader.GetSlice(patientID, studyID, seriesID, index, int(dimZ / 2))
            self.dicSelectedSeries[index]['selected'] = selectedRow
            
            if index == 0:
                self.lblInfoInhale.setText(strText)
                if image is not None:
                    self.axInhale.imshow(image, cmap = plt.cm.gray)
                    self.canvasInhale.draw()
            elif index == 1:
                self.lblInfoExhale.setText(strText)
                if image is not None:
                    self.axExhale.imshow(image, cmap = plt.cm.gray)
                    self.canvasExhale.draw()
                    
            if len(indexes) == 0:
                if self.bToggleInhale:
                    self.btnExhale.setChecked(True)
                else:
                    self.btnInhale.setChecked(True)
                
        elif deselected.count() > 0:
            
            itemDeselected = deselected.indexes()[0]
            itemIndex = model.itemData(itemDeselected).get(Qt.UserRole + 4)
            
            if itemIndex is not None:
                itemIndex -= 1
                # 欲取消選取的item必須同樣是inhale或是exhale才有效
                # 例如要取消選取的是inhale，但該item已經是exhale就無效
                if itemIndex == index:
                    self.reader.ClearSelectedSeries(itemIndex)
                    if itemIndex == 0:
                        self.axInhale.cla()
                        self.axInhale.axis('off')
                        self.canvasInhale.draw()
                    else:
                        self.axExhale.cla()
                        self.axExhale.axis('off')
                        self.canvasExhale.draw()
                        
                    self.setTreeDicomUserRole(None, modelIndex = deselected.indexes())
                    
                    if self.bToggleInhale:
                        self.dicSelectedSeries[0]['selected'] = []
                    else:
                        self.dicSelectedSeries[1]['selected'] = []
                else:
                    # 取消到不同type的item 將取消的item選取回來
                    lstDeselected = deselected.indexes()
                    deselection = QItemSelection()
                    deselection.select(lstDeselected[0], lstDeselected[-1])
                    
                    selectionModel.blockSignals(True)
                    selectionModel.select(deselection, QItemSelectionModel.Select)
                    selectionModel.blockSignals(False)
            
        # if len(indexes) < 2:
        if self.reader.GetNumOfSelectedSeries() < 2:
            
            self.btnImport.setEnabled(False)
        else:
            self.btnImport.setEnabled(True)
            
        self.treeDicom.viewport().update()
    
    def OnCurrentRowChanged_treeDicom(self, current:QModelIndex, previous:QModelIndex):
        pass
        # index = current.sibling(current.row(), 0)
        # model:QStandardItemModel = self.treeDicom.model()
        # item:QStandardItem = model.itemFromIndex(index)
        # if item:
        #     idPatient = item.data(Qt.UserRole + 1)
        #     idStudy   = item.data(Qt.UserRole + 2)
        #     idSeries  = item.data(Qt.UserRole + 3)
        #     print(f'patient ID = {idPatient}')
        #     print(f'Study ID   = {idStudy}')
        #     print(f'Series ID  = {idSeries}')
        #     self.selectedSeries = [idPatient, idStudy, idSeries]
        #     self.reader.SelectDataFromID(idPatient, idStudy, idSeries)
        # selectionModel:QItemSelectionModel = self.treeDicom.selectionModel()
        # model = self.treeDicom.model()
        # indexes = selectionModel.selectedIndexes()
        # for index in indexes:
        #     item = model.itemFromIndex(index)
        #     if item:
        #         print(f'item text = {item.text()}')
    def OnToggled_buttonGroup(self, button:QAbstractButton, bChecked:bool):
        if bChecked:
            self.ChangeCurrentDicom(button.objectName())
            
    def OnToggled_btgDIcom(self, button:QAbstractButton, bChecked:bool):
        if bChecked:
            if button == self.btnInhale:
                self.bToggleInhale = True
            else:
                self.bToggleInhale = False
            
    def OnCurrentChange_tabWidget(self, index:int):
        if self.tabWidget.currentWidget() == self.tabGuidance:
            self.NextScene()
        
    def OnSelection(self):
        tbsObj:QTextBrowser = self.sender()
        if isinstance(tbsObj, QTextBrowser):
            cursor = tbsObj.textCursor()
            cursor.clearSelection()
            tbsObj.setTextCursor(cursor)
            
    def OnStatusChanged(self, status):
        if status == QMediaPlayer.EndOfMedia:
            sleep(0.5)
            self.player.play()
            
    def OnBrightnessChanged(self, brightness:int):
        print(f'brightness = {brightness}')
        
    def OnConstrastChanged(self, contrast:int):
        print(f'contrast = {contrast}')
    
    ### Navigation Bar ###
    def ToSceneRobotSetting(self):
        # self.bFinishRobot = False
        # self.stkScene.setCurrentWidget(self.pgHomingCheckStep1)
        # self.btnSceneRobot.setEnabled(False)
        # self.btnSceneLaser.setEnabled(False)
        self.SetStage(STAGE_ROBOT)
        
    def ToSceneLaser(self):
        # self.bFinishLaser = False
        # self.stkScene.setCurrentWidget(self.pgLaser)
        # self.btnSceneLaser.setEnabled(False)
        self.SetStage(STAGE_LASER)
        
    def ToSceneView(self):
        self.stkScene.setCurrentWidget(self.pgImageView)
        
        
    ### End Navigation Bar ###
        
   
        
    def NextScene(self):
        button = self.sender()
        if isinstance(button, QPushButton):
            if button == self.btnImport:
                self.bDicomChanged = True
                self.btnImport.setEnabled(False)
                if not self.ImportDicom_L():
                    return
                self.ImportDicom_H()
            elif button == self.btnNext_startAdjustLaser:
                self.Laser_StopLaserProfile()
                print('stopped Adjust laser')
            # elif button == self.btnNext_startBuildModel:
            #     self.Laser_StartRecordBreathingBase()
            #     print('start model building')
            elif button == self.btnNext_startBuildModel:
                self.Laser_StopRecordBreathingBase()
            elif button == self.btnNext_endBuildModel:
                self.Laser_StopRecordBreathingBase()
                print('end model building')
            elif button == self.btnNext_scanCT:
                if self.tCheckInhale:
                    self.tCheckInhale.stop()
            elif button == self.btnNext_scanCT_2:
                if self.tCheckExhale:
                    self.tCheckExhale.stop()
            elif button == self.btnFromUSB:
                ## 開啟視窗選取資料夾 ############################################################################################
                # self.logUI.info('Import Dicom inhale/_Low')
                dlg = QFileDialog()
                dlg.setDirectory('C:\\Leon\\CT')
                dlg.setFileMode(QFileDialog.Directory)
                dlg.setFilter(QDir.Files)

                if dlg.exec_():
                    filePath = dlg.selectedFiles()[0]
                    # if self.bDicomChanged:
                    self.importDicom(filePath)
                    
                else:
                    return
            elif button == self.btnFromCD:
                return
            elif button == self.btnUnlockConfirm:
                self.Robot_FixArm()
                
        self.player.stop()
        index = self.stkScene.currentIndex()
        index = min(self.stkScene.count() - 1, index + 1)
        self.stkScene.setCurrentIndex(index)
        
        
        
    def BackScene(self):
        index = self.stkScene.currentIndex()
        index = max(0, index - 1)
        self.stkScene.setCurrentIndex(index)
        
    def ChangeCurrentDicom(self, dicomName:str):
        tag = self.dicDicom.get(dicomName)
        if not tag:
            # QMessageBox.critical(None, 'dicom error', 'dicom name not exists')
            MessageBox.ShowCritical('dicom error', 'dicom name not exists')
            return False
        
        self.currentTag = tag
        if dicomName == self.btnDicomLow.objectName():
            self.ShowDicom_L()
        elif dicomName == self.btnDicomHigh.objectName():
            self.ShowDicom_H()
        return True
        
    def ChangeTrajectorySlider(self, value:int):
        # 跟OnValueChanged_sldTrajectory不同的是
        # 這是單純為了讓拖動scrollBar同步改變sldTrajectory的值
        # 而不會觸發OnValueChanged
        # 以避免重複觸發slot事件的無限迴圈
        
        self.sldTrajectory.blockSignals(True)
        self.sldTrajectory.setValue(value)
        self.sldTrajectory.blockSignals(False)
    
    def onClick_Planning(self):
        print('planning')
        
    def onClick_Guidance(self):
        # index = self.stkScene.currentIndex()
        # self.stkScene.setCurrentIndex(index + 1)
        # self.stkScene.blockSignals(True)
        self.NextScene()
        
    def modifyTrajectory(self, dicom, entry, target):
        dicom.CreateLine(entry, target)
        
        length = np.linalg.norm(np.array(entry) - np.array(target))
        self.sldTrajectory.setMinimum(0)
        self.sldTrajectory.setSingleStep(1)
        self.sldTrajectory.setPageStep(1)
        self.sldTrajectory.setMaximum(int(length))
        self.sldTrajectory.setValue(0)
        
        self.currentTag['trajectoryLength'] = int(length)
        # if dicom == self.dicomLow:
        for view in self.viewport_L.values():
            if view.orientation == VIEW_CROSS_SECTION:
                view.uiScrollSlice.setMaximum(length)
                view.uiScrollSlice.setValue(0)
        # else:
        #     for view in self.viewport_H.values():
        #         length = np.linalg.norm(np.array(entry) - np.array(target))
        #         if view.orientation == VIEW_CROSS_SECTION:
        #             view.uiScrollSlice.setMaximum(length)
        
    def keyPressEvent(self, event):
        currentIndex = self.stkScene.currentIndex()
        if not hasattr(self, 'bFull'):
            self.bFull = True
        if event.key() == Qt.Key_Escape:
            if self.bFull:
                self.showNormal()
            else:
                self.showFullScreen()
        
        self.bFull = not self.bFull
        
    def enableDevice(self, nDevice:int = 0):
        
        self.idEnabledDevice = nDevice
        if nDevice == (DEVICE_ALL):
            self.robot = Robot.MOTORSUBFUNCTION()
            self.robot.signalProgress.connect(self.Robot_OnLoading)
            self.robot.signalInitFailed.connect(self.RobotSystem_OnFailed)
            
            self.tRobot = threading.Thread(target = self.robot.Initialize)
            self.tRobot.start()
            
            # self.RobotSupportArm = 100
            self.RobotSupportArm = Robot.RobotSupportArm()
            self.OperationLight = Robot.OperationLight()
            
            self.Laser = Robot.LineLaser()
            self.Laser.signalProgress.connect(self.Laser_OnLoading)
            self.Laser.signalModelPassed.connect(self.Laser_OnSignalModelPassed)
            self.Laser.signalBreathingRatio.connect(self.Laser_GetAverageRatio)
            self.Laser.signalInhaleProgress.connect(self.Laser_OnSignalInhale)
            self.Laser.signalExhaleProgress.connect(self.Laser_OnSignalExhale)
            self.Laser.signalCycleCounter.connect(self.Laser_OnSignalShowCounter)
            self.Laser.signalInitFailed.connect(self.RobotSystem_OnFailed)
            self.signalResetLaserUI.connect(self.Laser_SetBreathingCycleUI)
            self.signalModelCycle.connect(self.Laser_OnSignalUpdateCycle)
            self.tLaser= threading.Thread(target = self.Laser.Initialize)
            self.tLaser.start()
            
        elif nDevice == DEVICE_ROBOT:
            self.loadingLaser = 100
            self.robot = Robot.MOTORSUBFUNCTION()
            self.robot.signalProgress.connect(self.Robot_OnLoading)
            self.robot.signalInitFailed.connect(self.RobotSystem_OnFailed)
            
            self.tRobot = threading.Thread(target = self.robot.Initialize)
            self.tRobot.start()
            
            # self.RobotSupportArm = 100
            self.RobotSupportArm = Robot.RobotSupportArm()
            self.OperationLight = Robot.OperationLight()
        elif nDevice == DEVICE_LASER:
            self.stkScene.setCurrentWidget(self.pgLaser)
            
            self.loadingRobot = 100
            self.Laser = Robot.LineLaser()
            self.Laser.signalProgress.connect(self.Laser_OnLoading)
            self.Laser.signalModelPassed.connect(self.Laser_OnSignalModelPassed)
            self.Laser.signalBreathingRatio.connect(self.Laser_GetAverageRatio)
            self.Laser.signalInhaleProgress.connect(self.Laser_OnSignalInhale)
            self.Laser.signalExhaleProgress.connect(self.Laser_OnSignalExhale)
            self.Laser.signalCycleCounter.connect(self.Laser_OnSignalShowCounter)
            self.Laser.signalInitFailed.connect(self.RobotSystem_OnFailed)
            self.signalModelCycle.connect(self.Laser_OnSignalUpdateCycle)
            self.signalResetLaserUI.connect(self.Laser_SetBreathingCycleUI)
            self.tLaser= threading.Thread(target = self.Laser.Initialize)
            self.tLaser.start()
        else:
            self.stkMain.setCurrentWidget(self.pgScene)
            # self.stkScene.setCurrentWidget(self.pgImportDicom)
            self.stkScene.setCurrentWidget(self.pgImageView)
        
    def MainSceneChanged(self, index):
        if self.stkMain.currentWidget() == self.page_loading:
            # self.enableDevice(DEVICE_LASER)
            self.enableDevice(DEVICE_ALL)
            
    def SetStageButtonStyle(self, index:int): 
        if self.IsStage(index, STAGE_ROBOT):
            self.btnSceneRobot.setStyleSheet('background-color:rgb(109, 190, 247);')
            self.btnSceneLaser.setStyleSheet('')
            self.btnSceneView.setStyleSheet('')
        elif self.IsStage(index, STAGE_LASER):
            self.btnSceneRobot.setStyleSheet('')
            self.btnSceneLaser.setStyleSheet('background-color:rgb(109, 190, 247);')
            self.btnSceneView.setStyleSheet('')
        elif self.IsStage(index, STAGE_DICOM):
            self.btnSceneRobot.setStyleSheet('')
            self.btnSceneLaser.setStyleSheet('')
            self.btnSceneView.setStyleSheet('background-color:rgb(109, 190, 247);')
        else:
            self.btnSceneRobot.setStyleSheet('')
            self.btnSceneLaser.setStyleSheet('')
            self.btnSceneView.setStyleSheet('')
            
    def SceneChanged(self, index):
        
        self.indexPrePage = self.indexCurrentPage
        self.indexCurrentPage = index
        currentWidget = self.stkScene.currentWidget()
        if currentWidget == self.pgLaserAdjust:
            # self.Laser = Robot.LineLaser()
            # self.Laser.TriggerSetting(self)
            self.Laser_ShowLaserProfile()
        # elif currentWidget == self.pgModelBuilding:
        #     self.btnStartBuildModel.setEnabled(True)
        #     self.btnNext_startBuildModel.setEnabled(False)
        elif currentWidget == self.pgModelBuilding1:
            self.btnStartBuildModel_2.setEnabled(True)
            self.btnNext_startBuildModel_2.setEnabled(False)
        elif currentWidget == self.pgStartInhaleCT:
            self.Laser_CheckInhale()
        elif currentWidget == self.pgStartExhaleCT:
            self.Laser_CheckExhale()
        elif currentWidget == self.pgDicomList:
            self.btnImport.setEnabled(True)
            
            self.dlgHint = DlgHint()
            # self.dlgHint.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.dlgHint.setWindowFlags(Qt.WindowStaysOnTopHint)
            self.dlgHint.setWindowFlags(self.dlgHint.windowFlags() & ~Qt.WindowMinMaxButtonsHint)
            # self.dlgHint.setWindowFlags(Qt.WindowStaysOnTopHint)
            self.dlgHint.show()
            self.listSubDialog.append(self.dlgHint)
            # if self.bDicomChanged:
            #     self.importDicom('C:\\Leon\\CT')
                # self.importDicom('C:\\Leon\\dicom_test')
            
        elif currentWidget == self.pgRobotRegSphere:
            # self.player.stop()
            
            self.StopVedio()
            self.playVedio(self.wdgSetupBall, 'video/ball_setup.mp4')
            
        elif currentWidget == self.pgRobotSupportArm:
            # self.player.stop()
            self.StopVedio()
            self.playVedio(self.wdgSetupRobot, 'video/robot_mount_support_arm.mp4')
        elif currentWidget == self.pgDriveRobotGuide:
            self.wdgStep.GotoStep(1)
            self.StopVedio()
            self.btnDriveConfirm.setEnabled(True)
            self.btnUnlockRobot_2.setEnabled(False)
            
            tmpWidget = QWidget()
            tmpWidget.setMinimumSize(800, 600)
            tmpWidget.setMaximumSize(800, 600)
            
            layout = self.wdgPicture.layout()
            if layout is None:
                layout = QHBoxLayout(self.wdgPicture)
                layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(tmpWidget)
            self.tmpWidget = tmpWidget
            self.playVedio(self.tmpWidget, 'video/InstallHolder.mp4')
        elif currentWidget == self.pgSterileStep1:
            # self.player.stop()
            self.StopVedio()
            self.playVedio(self.wdgChangeTool, 'video/InstallHolder.mp4')            
        elif currentWidget == self.pgSterileStep3:
            self.GetRobotPosition()
        else:
            # self.player.stop()
            self.StopVedio()
        
        self.CheckStage(index)
        
        # if self.IsStage(index, STAGE_IMAGE):
        #     self.SetStage(STAGE_IMAGE)
        # elif self.IsStage(index, STAGE_DICOM) and \
        #     self.bFinishLaser and self.bFinishRobot and self.bFinishDicom:
        #     self.SetStage(STAGE_IMAGE)
        # elif self.IsStage(index, STAGE_LASER) and self.bFinishLaser:
        #     self.SetStage(STAGE_IMAGE)
        # elif self.IsStage(index, STAGE_ROBOT) and self.bFinishRobot:
        #     self.SetStage(STAGE_LASER)
        stage = self.GetStage(index)
        if stage is not None:
            bFoundStage = False
            # iterItem = iter(self.dicStageFinished.items())
            # try:
            #     # if now stage is finished, find next stage not finished
            #     while True:
            #         key, bFinish = iterItem.__next__()
            #         if bFoundStage and bFinish == False:
            #             self.SetStage(key)
            #             break
                        
            #         if key == stage and bFinish:
            #             bFoundStage = True
            # except StopIteration:
            #     pass
            
            # if now stage is finished, find next stage not finished
            for key, bFinish in self.dicStageFinished.items():
                if bFoundStage and bFinish == False:
                    self.SetStage(key)
                    break
                    
                if key == stage and bFinish:
                    bFoundStage = True
            
                        
            
            
        # 紀錄目前已經完成的階段
        self.indexDoneStage = max(self.indexCurrentStage, index)
        
        # self.SetStageButtonStyle(self.indexDoneStage)
        self.SetStageButtonStyle(index)
        self.indexCurrentStage = index
        # if self.stkScene.currentWidget() == self.pgImageView:
        #     self.wdgNaviBar.hide()
        
        if self.idEnabledDevice == DEVICE_ROBOT:
            if currentWidget == self.pgLaser:
                self.stkScene.setCurrentWidget(self.pgImportDicom)
        
    def IsStage(self,index:int, stage:str):
                
        if index == -1:
            return False
        
        if stage == STAGE_ROBOT:
            if index >= self.stkScene.indexOf(self.pgHomingCheckStep1) and \
               index <= self.stkScene.indexOf(self.pgRobotSupportArm):
                return True
            
        if stage == STAGE_LASER:
            if index >= self.stkScene.indexOf(self.pgLaser) and \
               index <= self.stkScene.indexOf(self.pgModelFinish):
                return True 
            
        if stage == STAGE_DICOM:
            if index >= self.stkScene.indexOf(self.pgImportDicom) and \
               index <= self.stkScene.indexOf(self.pgDicomList):
                return True
            
        if stage == STAGE_IMAGE:
            if index == self.stkScene.indexOf(self.pgImageView):
                return True
            
        return False
    
    def GetStage(self, index:int):
        for stage in self.dicStageFinished.keys():
            if self.IsStage(index, stage):
                return stage
        return None
            
    def SetStage(self, stage:str, bToStage:bool = True):
        
        index = 0
        self.dicStageFinished[stage] = False
        if stage == STAGE_ROBOT:
            self.bFinishRobot = False
            self.btnSceneRobot.setEnabled(True)
            self.btnSceneLaser.setEnabled(False)
            self.btnSceneView.setEnabled(False)
            if bToStage:
                # self.stkScene.setCurrentWidget(self.pgHomingCheckStep1)
                index = self.stkScene.indexOf(self.pgHomingCheckStep1)
                # self.stkScene.blockSignals(True)
                self.stkScene.setCurrentIndex(index)
                # self.stkScene.blockSignals(False)
                
        elif stage == STAGE_LASER:
            # self.bFinishRobot = True
            self.bFinishLaser = False
            # self.dicStageFinished[STAGE_LASER] = False
            self.btnSceneRobot.setEnabled(True)
            self.btnSceneLaser.setEnabled(True)
            self.btnSceneView.setEnabled(False)
            if bToStage:
                # self.stkScene.setCurrentWidget(self.pgLaser)
                index = self.stkScene.indexOf(self.pgLaser)
                # self.stkScene.blockSignals(True)
                self.stkScene.setCurrentIndex(index)
                # self.stkScene.blockSignals(False)
                self.pgbInhale.setValue(0)
                self.pgbExhale.setValue(0)
                self.bLaserShowProfile = False
                self.bLaserRecording = False
                self.bLaserTracking = False
                
        elif stage == STAGE_DICOM:
            # self.bFinishRobot = True
            # self.bFinishLaser = True
            self.bFinishDicom = False
            # self.dicStageFinished[STAGE_DICOM] = False
            self.btnSceneRobot.setEnabled(True)
            self.btnSceneLaser.setEnabled(True)
            self.btnSceneView.setEnabled(True)
            if bToStage:
                # self.stkScene.setCurrentWidget(self.pgImportDicom)
                index = self.stkScene.indexOf(self.pgImportDicom)
                # self.stkScene.blockSignals(True)
                self.stkScene.setCurrentIndex(index)
                # self.stkScene.blockSignals(False)
        elif stage == STAGE_IMAGE:
            # self.bFinishRobot = True
            # self.bFinishLaser = True
            # self.bFinishDicom = True
            self.btnSceneRobot.setEnabled(True)
            self.btnSceneLaser.setEnabled(True)
            self.btnSceneView.setEnabled(True)
            if bToStage:
                # self.stkScene.setCurrentWidget(self.pgImageView)
                index = self.stkScene.indexOf(self.pgImageView)
                self.stkScene.setCurrentIndex(index)
                
        self.indexCurrentStage = index
                
    def CheckStage(self, index:int):
        if self.IsStage(index, STAGE_ROBOT):
            self.btnSceneRobot.setEnabled(True)
        elif self.IsStage(index, STAGE_LASER):
            self.bFinishRobot = True
            self.dicStageFinished[STAGE_ROBOT] = True
            self.btnSceneRobot.setEnabled(True)
            self.btnSceneLaser.setEnabled(True)
        elif self.IsStage(index, STAGE_DICOM):
            self.bFinishLaser = True
            self.dicStageFinished[STAGE_LASER] = True
            self.btnSceneLaser.setEnabled(True)
        elif self.IsStage(index, STAGE_IMAGE):
            self.dicStageFinished[STAGE_DICOM] = True
            self.bFinishDicom = True
            
    def GetRobotPosition(self):
        QTimer.singleShot(2000, lambda:self.stkJoint1.setCurrentWidget(self.pgJoint1Pass))
        sleep(1.0)
        QTimer.singleShot(2000, lambda:self.stkJoint2.setCurrentWidget(self.pgJoint2Pass))
        QTimer.singleShot(3000, lambda:self.stkScene.setCurrentWidget(self.pgImageView))
        
    
        
    def playVedio(self, widget:QWidget, filePath:str):
        
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(filePath)))
        
        layout = widget.layout()
        if layout is None:
        
            videoWidget = QVideoWidget()
            videoWidget.setAspectRatioMode(Qt.KeepAspectRatio)
            self.player.setVideoOutput(videoWidget)
        
            layout = QVBoxLayout(widget)
            layout.addWidget(videoWidget)
            layout.setContentsMargins(0, 0, 0, 0)
            
            videoWidget.brightnessChanged.connect(self.OnBrightnessChanged)
            videoWidget.contrastChanged.connect(self.OnConstrastChanged)
            
            self.videoWidget = videoWidget
        else:
            videoWidget = layout.itemAt(0).widget()
            self.player.setVideoOutput(videoWidget)
        
        self.player.play()
        self.player.mediaStatusChanged.connect(self.OnStatusChanged)
        
    def StopVedio(self):
        if self.videoWidget is not None:
            parentWidget = self.videoWidget.parentWidget()
            parentWidget.layout().removeWidget(self.videoWidget)
            self.videoWidget = None
        # self.player.stop()
        # self.player.setVideoOutput(None)
        
    def thread_LoadLaser(self):
        # QThread.msleep(1000)
        self.loadingLaser = 0
        np.random.seed(0)
        while self.loadingLaser < 100:
            self.loadingLaser += int(np.random.rand() * 30 + 2)
            # self.loadingRobot += int(np.random.rand() * 20 + 2)
            self.loadingLaser = min(100, self.loadingLaser)
            sleep((np.random.rand() * 0.5) + 0.1)
            self.signalSetProgress.emit(self.pgbLaser, self.loadingLaser)
            # self.signalSetProgress.emit(self.pgbRobot, self.loadingRobot)
        self.signalSetCheck.emit(self.wdgCheckLaser, True)
        sleep(1)
        if hasattr(self, 'loadingRobot'):
            if self.loadingLaser >= 100 and self.loadingRobot >= 100:
                if self.stkMain.currentIndex() < 2:
                    self.signalLoadingReady.emit()
        
    def thread_LoadRobot(self):
        self.loadingRobot = 0
        # np.random.seed(5)
        while self.loadingRobot < 100:
            self.loadingRobot += int(np.random.rand() * 19 + 1)
            self.loadingRobot = min(100, self.loadingRobot)
            sleep((np.random.rand() * 0.5) + 0.1)
            self.signalSetProgress.emit(self.pgbRobot, self.loadingRobot)
        
        self.signalSetCheck.emit(self.wdgCheckRobot, True)
        sleep(1)
        if self.loadingLaser >= 100 and self.loadingRobot >= 100:
            if self.stkMain.currentIndex() < 2:
                self.signalLoadingReady.emit()
                
    
        
    def onSignal_LoadingReady(self):
        index = self.stkMain.currentIndex()
        self.stkMain.setCurrentIndex(index + 1)
        
    def onSignal_ModelBuilding(self, bValid):
        if bValid:
            self.btnNext_startBuildModel.setEnabled(True)
        else:
            self.btnNext_startBuildModel.setEnabled(False)
        
    def onSignal_SetProgress(self, progressBar, percent):
        if not isinstance(progressBar, QProgressBar):
            return
        
        progressBar.setValue(percent)
        
    def onSignal_SetCheck(self, widget, bCheck):
        if not isinstance(widget, QWidget):
            return
        
        if bCheck:
            widget.setStyleSheet('border-image:url(image/check.png);')
            widget.update()
        else:
            widget.setStyleSheet('border-image:none;')
            
    def onSignal_ShowMessage(self, msg:str, title:str, bIsError = False):
        if len(msg) > 0:
            if not bIsError:
                MessageBox.ShowInformation(msg)
            else:
                MessageBox.ShowCritical(msg)
            
            
    def sti_LaserOutput(self):
        # if not hasattr(self, 'dataTmp'):
        self.dataTmp = []
        d1 = []
        
        for i in range(700):
            # startNum += step
            y = self.startNum + np.sin(i/700 * np.pi) * 10
            d1.append(y)
        
        avg = np.average(d1)
        if avg < -120 or avg > -80:
            self.dataTmp.append(d1)
            self.dataTmp.append([])
        else:
            self.dataTmp.append([])
            self.dataTmp.append(d1)
        
        self.recordData.extend(d1)
            
        return self.dataTmp, avg
    
    def sti_RunLaser(self):
        self.startNum = -110
        self.recordTime = datetime.now().timestamp()
        delta = datetime.now().timestamp() - self.recordTime
        
        self.recordData = []
        
        xAxis = np.arange(1, 11)
        data1sec = []
        cycleCount = 0
        while delta < 10:
            delta = datetime.now().timestamp() - self.recordTime
            data, avg = self.sti_LaserOutput()
            self.laserFigure.update_figure(data)
            self.startNum += np.sin(delta * np.pi) * 2
            
            data1sec.append(avg)
            if len(data1sec) > 10:
                data1sec.pop(0)
                
                slope, intercept = np.polyfit(xAxis, data1sec, 1)
                if hasattr(self, 'lastSlope'):
                    if self.lastSlope * slope < 0:
                        cycleCount += 1
                self.lastSlope = slope
                print(f'slope = {slope}')
            sleep(0.1)
        # fft_result = np.fft.fft(self.recordData)
        
        print(f'total cycle = {cycleCount}')
        
    def closeEvent(self, event):
        self.Laser_Close()
        try:
            for dlg in self.listSubDialog:
                dlg.close()
            ## 移除VTK道具 ############################################################################################
            # self.irenSagittal_L.RemoveAllViewProps() 
            # if hasattr(self.dicomLow, 'rendererSagittal'):
            #     self.dicomLow.rendererSagittal.RemoveAllViewProps()
                
            # if hasattr(self.dicomLow, 'rendererCoronal'):
            #     self.dicomLow.rendererCoronal.RemoveAllViewProps()
                
            # if hasattr(self.dicomLow, 'rendererAxial'):
            #     self.dicomLow.rendererAxial.RemoveAllViewProps()
                
            # if hasattr(self.dicomLow, 'renderer3D'):
            #     self.dicomLow.renderer3D.RemoveAllViewProps()
                
            ############################################################################################
            ## 關閉VTK Widget ############################################################################################
            self.CloseView()
            
            
            ############################################################################################
            print("remove dicomLow VTk success")
            
            
        except Exception as e:
            print(e)
            print("remove dicomLow VTk error")
            
    def registration(self, image, spacing, series):
        """automatic find registration ball center + open another ui window to let user selects ball in order (origin -> x axis -> y axis)
        """
        # self.ui_SP = SystemProcessing()
        # self.ui_SP.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        # self.ui_SP.show()
        # QApplication.processEvents()
        self.ui_SP = SystemProcessing()
        self.ui_SP.setWindowTitle('Registration')
        self.ui_SP.label_Processing.setText('Registing Robot Position...')
        self.ui_SP.show()
        QApplication.processEvents()
        self.regFn.signalProgress.connect(self.ui_SP.UpdateProgress)
        
        
        if self.currentTag.get("regBall") != None or self.currentTag.get("candidateBall") != None:
            # self.ui_SP.close()
            # reply = QMessageBox.information(self, "information", "already registration, reset now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            reply = MessageBox.ShowInformation("information", "already registration, reset now?", 'Yes', 'No')
            ## 重新設定儲存的資料 ############################################################################################
            # if reply == QMessageBox.Yes:
            if reply == 0:
                # self.dcmTagLow.update({"selectedBall": []})
                self.currentTag.update({"regBall": []})
                self.currentTag.update({"flagSelectedBall": False})
                
                self.currentTag.update({"candidateBall": []})
                self.currentTag.update({"selectedBallKey": []})
                self.currentTag.update({"regMatrix": []})
                # self.dcmTagLow.update({"sectionTag": []})
                self.currentTag.update({"selectedPoint": []})
                self.currentTag.update({"flagSelectedPoint": False})
                
                "UI"
                # self.label_Error_L.setText('Registration difference: mm')
                # self.Button_ShowRegistration_L.setEnabled(False)
                # self.comboBox_L.setEnabled(False)
                # self.Button_SetPoint_L.setEnabled(False)
                # self.Button_ShowPoint_L.setEnabled(False)
                
                "VTK"
                # try:
                #     self.dicomLow.RemovePoint()
                # except:
                #     pass
                
                # self.logUI.info('reset selected ball (Low)')
                print("reset selected ball (Low)")
                
                
            # else:
            #     self.ui_SP.close()
            #     return
            ############################################################################################
        "automatic find registration ball center"
        try:
            ## 自動找球心 + 辨識定位球位置 ############################################################################################
            flag, answer = self.regFn.GetBallAuto(image, spacing, series)
            ############################################################################################
        except Exception as e:
            # self.ui_SP.close()
            # self.logUI.warning('get candidate ball error / SetRegistration_L() error')
            # QMessageBox.critical(self, "error", "get candidate ball error / SetRegistration_L() error")
            MessageBox.ShowCritical("get candidate ball error", "OK")
            print('get candidate ball error / SetRegistration_L() error')
            print(e)
            return False
        
        if flag == True:
            # self.logUI.info('get candidate ball of inhale/Low DICOM in VTK:')
            i = 0
            for key, value in answer.items():
                tmp = str(i) + ": " + str(key) + str(value)
                # self.logUI.info(tmp)
                i += 1
            self.currentTag.update({"candidateBallVTK": answer})
            ## 顯示定位球註冊結果 ############################################################################################
            "open another ui window to check registration result"
            # self.ui_CS = CoordinateSystem(self.dcmTagLow, self.dicomLow)
            # self.ui_SP.close()
            # self.ui_CS.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            # self.ui_CS.show()
            ############################################################################################
            # self.Button_ShowRegistration_L.setEnabled(True)
        else:
            # self.ui_SP.close()
            # self.logUI.warning('get candidate ball error')
            
            # QMessageBox.critical(self, "error", "get candidate ball error")
            MessageBox.ShowCritical("get candidate ball error", "OK")
            print('get candidate ball error / SetRegistration_L() error')
            ## 顯示手動註冊定位球視窗 ############################################################################################
            "Set up the coordinate system manually"
            # self.ui_CS = CoordinateSystemManual(self.currentTag, self.currentTag.get('display'), answer)
            # self.ui_CS.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            # self.ui_CS.show()
            ############################################################################################
            # self.Button_ShowRegistration_L.setEnabled(True)
            return False
        
        return True
            
    def SetRegistration_L(self):
        """automatic find registration ball center + open another ui window to let user selects ball in order (origin -> x axis -> y axis)
        """
        return self.registration(self.imageL, self.currentTag.get('spacing'), self.currentTag.get('series'))
    
    def SetRegistration_H(self):
        """automatic find registration ball center + open another ui window to let user selects ball in order (origin -> x axis -> y axis)
        """
        return self.registration(self.imageH, self.currentTag.get('spacing'), self.currentTag.get('series'))
    
    def ShowRegistrationDifference_L(self):
        """map/pair/match ball center between auto(candidateBall) and manual(selectedBall)
           calculate error/difference of relative distance
        """
        "map/pair/match ball center between auto(candidateBall) and manual(selectedBall)"
        candidateBallVTK = self.currentTag.get("candidateBallVTK")
        selectedBallKey = list(candidateBallVTK.keys())[-1]
        # selectedBallKey = self.currentTag.get("selectedBallKey")
        if selectedBallKey is None or selectedBallKey == []:
            # QMessageBox.critical(self, "error", "please redo registration, select the ball")
            MessageBox.ShowCritical("please redo registration, select the ball")
            print("pair error / ShowRegistrationDifference_L() error")
            # self.logUI.warning('pair error / ShowRegistrationDifference_L() error')
            return False
        else:
            selectedBallAll = np.array(candidateBallVTK.get(tuple(selectedBallKey)))
            selectedBall = selectedBallAll[:,0:3]
            ## 儲存定位球中心 ############################################################################################
            self.currentTag.update({"regBall": selectedBall})
            # self.logUI.info('get registration balls of inhale/Low DICOM:')
            # for tmp in self.dcmTagLow.get("regBall"):
            #     self.logUI.info(tmp)
            ############################################################################################
            ## 計算定位誤差 ############################################################################################
            "calculate error/difference of relative distance"
            error = self.regFn.GetError(self.currentTag.get("regBall"))
            logStr = 'registration error of inhale/Low DICOM (min, max, mean): ' + str(error)
            # self.logUI.info(logStr)
            # self.label_Error_L.setText('Registration difference: {:.2f} mm'.format(error[2]))
            # QMessageBox.information(None, 'Result', f'RMS：{error[2]:.3f} mm')
            ############################################################################################
            ## 計算轉換矩陣 ############################################################################################
            "calculate transformation matrix"
            regMatrix = self.regFn.TransformationMatrix(self.currentTag.get("regBall"))
            # self.logUI.info('get registration matrix of inhale/Low DICOM: ')
            # for tmp in regMatrix:
            #     self.logUI.info(tmp)
            self.currentTag.update({"regMatrix": regMatrix})
            ############################################################################################
            # self.Button_SetPoint_L.setEnabled(True)
            # self.comboBox_L.setEnabled(True)
        return True
            
    def ResetView(self):
        if self.viewport_L:
            for view in self.viewport_L.values():
                view.Reset()
                
    def CloseView(self):
        if self.viewport_L:
            for view in self.viewport_L.values():
                view.Close()
                
        for view in self.dicView.values():
                view.close()
                
    def Demo_InitLaser(self):
        sleep(0.2)
        self.signalDemoLaserInit.emit(20)
        sleep(0.2)
        self.signalDemoLaserInit.emit(40)
        sleep(0.2)
        self.signalDemoLaserInit.emit(60)
        sleep(0.2)
        self.signalDemoLaserInit.emit(80)
        sleep(0.2)
        self.signalDemoLaserInit.emit(80)
        sleep(0.2)
        self.signalDemoLaserInit.emit(100)
        
    def Demo_InitRobot(self):
        sleep(0.2)
        self.signalDemoRobotInit.emit(25)
        sleep(0.2)
        self.signalDemoRobotInit.emit(50)
        sleep(0.2)
        self.signalDemoRobotInit.emit(75)
        sleep(0.2)
        self.signalDemoRobotInit.emit(100)
                
    def Demo_OnRobotLoading(self, progress:int):
        self.loadingRobot = progress
        self.signalSetProgress.emit(self.pgbRobot, progress)
        
        if hasattr(self, 'loadingLaser'):
            if self.loadingLaser >= 100 and self.loadingRobot >= 100:
                if self.stkMain.currentIndex() < 2:
                    self.signalLoadingReady.emit()
                
    def Demo_OnLaserLoading(self, progress:int):
        self.loadingLaser = progress
        self.signalSetProgress.emit(self.pgbLaser, progress)
        
        sleep(1)
        if hasattr(self, 'loadingRobot'):
            if self.loadingLaser >= 100 and self.loadingRobot >= 100:
                if self.stkMain.currentIndex() < 2:
                    self.signalLoadingReady.emit()
                    self.stkMain.setCurrentWidget(self.pgScene)
                    
    def Demo_RecordBreathingCycle(self):
        for i in range(1, 6):
            sleep(1)
            self.signalModelCycle.emit((100, 0), i)
            
        self.signalModelBuildingPass.emit(True)
        
    def Demo_CheckInhale(self):
        if not hasattr(self, 'demoInhaleRage'):
            self.demoInhaleRage = 0
        percentage = np.sin(self.demoInhaleRage) * 3
        percentage = self.percentInhale + percentage
        self.signalDemoInhale.emit(True, percentage)
        self.demoInhaleRage += np.deg2rad(5)
        
    def Demo_CheckExhale(self):
        if not hasattr(self, 'demoExhaleRage'):
            self.demoExhaleRage = 0
        percentage = np.sin(self.demoExhaleRage) * 3
        percentage = self.percentExhale + percentage
        self.signalDemoExhale.emit(True, percentage)
        self.demoExhaleRage += np.deg2rad(5)
        
    def Demo_OnThreadHomingProcess(self):
        for i in range(1, 1001):
            sleep(0.01)
            percent = i * 0.001
            print(percent)
            self.signalDemoHoming.emit(percent)
                
    def RobotSystem_OnFailed(self, errDevice:int):
        if errDevice == DEVICE_ROBOT:
            msg = 'robot connection error'
        elif errDevice == DEVICE_LASER:
            msg = 'laser connection error'
            
        self.errDevice |= errDevice
        # if not hasattr(self, 'msgbox'):
        #     msgbox = MessageBox(QMessageBox.Question, msg + '\nRetry again?')
        #     msgbox.addButtons('Retry', 'Shutdown')
            
        #     self.msgbox = msgbox
        #     ret = msgbox.exec_()
        if not hasattr(self, 'showError'):
            self.showError = True
            ret = MessageBox.ShowQuestion(msg + '\nRetry again?', 'Retry', 'Shutdown')
            if ret == 0:
                del self.showError
                
                if (self.errDevice & DEVICE_ROBOT) != 0:
                    self.errDevice &= ~DEVICE_ROBOT
                    self.tRobot = threading.Thread(target = self.robot.Initialize)
                    self.tRobot.start()
                    
                if (self.errDevice & DEVICE_LASER) != 0:
                    self.errDevice &= ~DEVICE_LASER
                    self.tLaser= threading.Thread(target = self.Laser.Initialize)
                    self.tLaser.start()
                
            elif ret == 1:
                self.close()
                
    def Robot_SetLoadingMessage(self, msg:str):
        fmt = QTextCharFormat()
        bSucceed = True
        if msg.startswith('[ERROR]'):
            fmt.setForeground(QColor(100, 0, 0))
            bSucceed = False
        else:
            fmt.setForeground(QColor(0, 100, 0))
        self.pteProgress.mergeCurrentCharFormat(fmt)
        self.pteProgress.appendPlainText(msg)
        
        return bSucceed
            
    def Robot_OnLoading(self, strState:str, progress:int):
        self.loadingRobot = progress
        # while self.loadingRobot < 100:
        
        self.signalSetProgress.emit(self.pgbRobot, progress)
        self.Robot_SetLoadingMessage(strState)
        # if self.Robot_SetLoadingMessage(strState) == False:
            # # self.Laser.bStop = True
            # QMessageBox.critical(None, 'ERROR', 'Robot connection Failed, system will shutdown')
            # self.close()
        # text = self.pteProgress.toPlainText()
        # self.pteProgress.setPlainText(text + '\n' + strState)
        # self.pteProgress.moveCursor(QTextCursor.End)
        if hasattr(self, 'loadingLaser'):
            if self.loadingLaser >= 100 and self.loadingRobot >= 100:
                if self.stkMain.currentIndex() < 2:
                    self.signalLoadingReady.emit()
            
    def Robot_Compensation(self):
        if not self.robot:
            return
        
        # if self.Button_StopLaserTracking.isChecked():
            # self.Button_StartTracking.setStyleSheet("")
            # self.Button_StopLaserTracking.setStyleSheet("background-color:#4DE680")
            # self.Button_StopLaserTracking.setChecked(False)
        self.bTrackingBreathing = False
        try:
            self.robot.RealTimeTracking(self.breathingPercentage)
            self.robot.MoveToPoint()
        except:
            print("Robot Compensation error")
        # else:
        #     self.trackingBreathingCommand = True
        
    def Robot_StartHoming(self):
        if self.language == LAN_CN:
            translator = QTranslator()
            translator.load('FunctionLib_UI/Ui_homing_tw.qm')
            QCoreApplication.installTranslator(translator)
            
        self.StopVedio()
        if not self.robot:
            return
        
        # self.robot.signalProgress.disconnect(self.Robot_OnLoading)
        
        self.uiHoming = HomingWidget(self)
        self.uiHoming.finished.connect(lambda:self.NextScene())
        self.uiHoming.signalHoming.connect(self.Robot_HomingProcess)
        self.robot.signalHomingProgress.connect(self.uiHoming.OnSignal_Percent)
        
        self.uiHoming.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.uiHoming.setModal(False)
        self.uiHoming.exec_()
        self.listSubDialog.append(self.uiHoming)
        # self.NextScene()
        
    def Robot_HomingProcess(self):
        if self.robot is None:
            return
        
        tHoming = threading.Thread(target = self.Robot_OnThreadHomingProcess)
        tHoming.start()
        
                
    def Robot_OnThreadHomingProcess(self):
        if self.robot.bConnected == True:
            if self.robot.HomeProcessing() == True:
                print("Home processing is done!")
                # QMessageBox.information(self, "information", "Home processing is done!")
                self.homeStatus = True
                # self.RobotRun()
                
    def Robot_Stop(self):
        # QMessageBox.information(None, 'Info', 'Robot Stop')
        MessageBox.ShowInformation('Robot Stop')
        
    def RobotRun(self):
        if self.homeStatus is True:
            self.robot.P2P()
            print("Robot run processing is done!")
            # QMessageBox.information(self, "information", "Robot run processing is done!")
            
            #執行呼吸補償
            self.robot.breathingCompensation()
        else:
            print("Please execute home processing first.")
            # QMessageBox.information(self, "information", "Please execute home processing first.")
            MessageBox.ShowInformation("information", "Please execute home processing first.")
        
    def ReleaseRobotArm(self):
        self.FixArmStatus = False
        while self.FixArmStatus == False:
            self.RobotSupportArm.ReleaseAllEncoder()
            print('robot release')
        
    def Robot_ReleaseArm(self):
        self.btnRobotRelease.setEnabled(False)
        self.btnRobotFix.setEnabled(True)
        self.btnRobotSetTarget.setEnabled(False)
        self.btnRobotBackTarget.setEnabled(False)
        
        self.btnUnlockRobot.setEnabled(True)
        self.btnUnlockRobot_2.setEnabled(True)
        self.btnUnlockConfirm.setEnabled(True)
        self.btnDriveConfirm.setEnabled(True)
        self.btnRobotRelease_2.setEnabled(False)
        self.btnRobotTarget.setEnabled(True)
        
        self.tReleaseArm = threading.Thread(target = self.ReleaseRobotArm)
        self.tReleaseArm.start()
    
    def Robot_FixArm(self):
        self.btnRobotRelease.setEnabled(True)
        self.btnRobotFix.setEnabled(False)
        self.btnRobotSetTarget.setEnabled(True)
        
        self.btnUnlockRobot.setEnabled(True)
        self.btnUnlockRobot_2.setEnabled(True)
        self.btnUnlockConfirm.setEnabled(False)
        # self.btnDriveConfirm.setEnabled(False)
        self.btnRobotRelease_2.setEnabled(True)
        self.btnRobotTarget.setEnabled(False)
        
        if self.settingTarget == True:
            self.btnRobotBackTarget.setEnabled(True)
        else:
            self.btnRobotBackTarget.setEnabled(False)
        self.FixArmStatus = True
        print('fix arm')
        
    def Robot_SettingTarget(self):
        self.btnRobotSetTarget.setEnabled(False)
        self.btnRobotTarget.setEnabled(False)
        self.btnTargetRobotConfirm.setEnabled(True)
        
        if self.settingTarget:
            self.btnRobotBackTarget.setEnabled(True)
        else:
            self.btnRobotBackTarget.setEnabled(False)
        self.RobotSupportArm.SetTargetPos()
        self.settingTarget = True
        print('setting robot target')
        
    def Robot_FixAndTarget(self):
        self.Robot_FixArm()
        sleep(0.5)
        self.Robot_SettingTarget()
        
    def Robot_BackToTarget(self):
        self.btnRobotRelease.setEnabled(False)
        self.btnRobotFix.setEnabled(True)
        self.btnRobotSetTarget.setEnabled(False)
        self.btnRobotBackTarget.setEnabled(False)
        self.RobotSupportArm.BackToTargetPos()
        print('Back to target')
        
    def Laser_SetLoadingMessage(self, msg:str):
        fmt = QTextCharFormat()
        if msg.startswith('[ERROR]'):
            fmt.setForeground(QColor(100, 0, 0))
        else:
            msg = '[SUCCEED]' + msg
            fmt.setForeground(QColor(  0, 100, 0))
            
        self.pteProgress.mergeCurrentCharFormat(fmt) 
        self.pteProgress.appendPlainText(msg)
        
    def Laser_SetBreathingCycleUI(self, nID:int = -1, bEnabled:bool = None):
        lstItem = []
        if nID == -1:
            nNo = 1
            while True:
                if not self.Laser_SetBreathingCycleUI(nNo, bEnabled):
                    break
                nNo += 1
            if bEnabled is None:
                self.lytLaserModel.replaceWidget(self.laserFigure, self.lblHintModelBuilding)
                self.btnAutoRecord.setEnabled(True)
                self.lblCounter.setText('')
        else:
            strLabelName = 'lblCycle' + str(nID)
            if hasattr(self, strLabelName):
                label = eval('self.' + strLabelName)
                lstItem.append(label)
            else:
                return False
                
            strWdgName = 'wdgCheckCycle' + str(nID)
            if hasattr(self, strWdgName):
                wdg = eval('self.' + strWdgName)
                lstItem.append(wdg)
            else:
                return False
                
            for item in lstItem:
                if hasattr(item, 'setStyleSheet'):
                    if bEnabled == True:
                        item.setStyleSheet('background-color:rgb(0, 100, 0)')
                    elif bEnabled == False:
                        item.setStyleSheet('background-color:rgb(255, 0, 0)')
                    else:
                        item.setStyleSheet('')
                        
        return True
    
    def Laser_OnClick_btnAutoRecord(self):
        if self.btnAutoRecord.isChecked():
            self.btnAutoRecord.setText('ON')
            self.btnRecord.setEnabled(False)
            self.bAutoRecord = True
        else:
            self.bAutoRecord = False
            self.btnAutoRecord.setText('OFF')
            self.btnRecord.setEnabled(True)
    
    def Laser_OnClick_btnRecord(self):
        if self.Laser:
            # self.Laser.bManualRecord = True
            
            receiveData = self.dicReceiveData.copy()
            curTime = time.time()
            deltaTime = int((curTime - receiveData['startTime']) * 1000)
            
            # find closest time data
            dicDeltaTime = {keyTime: item for keyTime, item in receiveData.items() if isinstance(keyTime, int)}
            lstDeltaTime = np.array(list(dicDeltaTime.keys()))
            lstData = list(dicDeltaTime.values())
            
            lstSubDeltaTime = np.abs(lstDeltaTime - deltaTime)
            minIndex = np.argmin(lstSubDeltaTime)
            
            recordData = lstData[minIndex]
            
            if recordData is not None:
                
                avg = self.Laser.CalHeightAvg(recordData)
                self.lstRecordAvg.append(avg)
                
                lenOfAvg = len(self.lstRecordAvg)
                if lenOfAvg >= 2 and (lenOfAvg % 2) == 0:
                    if self.Laser.DataRearrange(dicDeltaTime, self.yellowLightCriteria, self.greenLightCriteria):  
                        
                        if self.lstRecordAvg[-2] > self.lstRecordAvg[-1]:
                            self.lstRecordAvg[-2], self.lstRecordAvg[-1] = self.lstRecordAvg[-1], self.lstRecordAvg[-2]
                            
                        lstPercent = self.Laser.GetPercentFromAvg(self.lstRecordAvg)
                        lstPercent = np.reshape(lstPercent, (-1, 2))
                        
                        for i, percent in enumerate(lstPercent, 1):
                            percent = tuple(percent)
                            percentIn, percentEx = percent
                            self.signalModelCycle.emit(percent, i)
                            print(f'cycle {i} = ({percentIn}, {percentEx})')
                        print('=' * 50)
                            
                        self.dicDataCycleManual[self.nCycle] = self.dicDataCycle[1].copy()
                        self.bUpdateCycleData = True
                        
                        self.dicDataCycleManual[self.nCycle]['avg'] = self.lstRecordAvg[-2:]
                        
                    if lenOfAvg >= 10:
                        
                        bValid = self.Laser_CheckCycles(self.dicDataCycleManual)
                        self.bLaserRecording = False
                        
                        if not bValid:
                                self.signalModelBuildingPass.emit(False)
                        else:
                            self.recordBreathingBase = True
                            self.signalModelBuildingPass.emit(True)
                            
                        self.lstRecordAvg = []
                        self.dicDataCycleManual = {}
                        self.nCycle = 0
                    self.nCycle += 1
            else:
                print('laser data is None')
        
    def Laser_OnLoading(self, strState:str, progress:int):
        # QThread.msleep(1000)
        self.loadingLaser = progress
        
        self.signalSetProgress.emit(self.pgbLaser, progress)
        # self.signalSetCheck.emit(self.wdgCheckLaser, True)
        # text = self.pteProgress.toPlainText()
        # self.pteProgress.setPlainText(text + '\n' + strState)
        self.Laser_SetLoadingMessage(strState)
        
        # self.pteProgress.moveCursor(QTextCursor.End)
        
        sleep(1)
        if hasattr(self, 'loadingRobot'):
            if self.loadingLaser >= 100 and self.loadingRobot >= 100:
                if self.stkMain.currentIndex() < 2:
                    # self.stkScene.setCurrentWidget(self.pgLaser)
                    self.signalLoadingReady.emit()
                    self.stkMain.setCurrentWidget(self.pgScene)
                    
    def Laser_autoNextPage(self, msgbox = None):
        if isinstance(msgbox, QMessageBox):
            msgbox.accept()
        # self.NextScene()
        self.stkScene.setCurrentWidget(self.pgStartInhaleCT)
                    
    def Laser_OnSignalModelPassed(self, bPass):
        if self.bLaserForceClose:
            return
        
        if bPass:
            # QMessageBox.information(None, 'Model Building Succeed', 'Model Base Checking done!')
            
            # msgbox = QMessageBox(text = 'Model Base Checking done!')
            msgbox = MessageBox(QMessageBox.Information, 'Model Base Checking done!')
            msgbox.addButtons('OK')
            QTimer.singleShot(2000, lambda: self.Laser_autoNextPage(msgbox))
            # msgbox.setWindowTitle('Model Building Succeed')
            # msgbox.setIcon(QMessageBox.Information)
            msgbox.exec_()
        else:
            # QMessageBox.critical(None, 'Model Building Failed', 'Please try to build chest model again.')
            MessageBox.ShowCritical('Model Building Failed', 'Please try to build chest model again.')
            # self.lytLaserModel.replaceWidget(self.laserFigure, self.lblHintModelBuilding)
            # self.Laser_SetBreathingCycleUI()
            self.ToSceneLaser()
           
    def Laser_OnSignalInhale(self, bInhale:bool, percentage:float):
        
        if bInhale:
            # self.stkSignalLightInhale.setCurrentWidget(self.pgGreenLightInhale)
            
            
            now = time.time()
            if self.tInhale is None:
                self.tInhale = now
                
            if now - self.tInhale >= 1:
                value = self.pgbInhale.value() + 20
                self.pgbInhale.setValue(value)
                self.tInhale = now
                
                if value == 100:
                    self.btnNext_scanCT.setEnabled(True)
                    # QTimer.singleShot(500, self.NextScene)
                    
                    # self.tCheckInhale.stop()
        else:
            # self.stkSignalLightInhale.setCurrentWidget(self.pgRedLightInhale)
            self.pgbInhale.setValue(0)
            self.btnNext_scanCT.setEnabled(False)
            self.tInhale = None
        self.indicatorInhale.setValue(percentage)
        
    def Laser_OnSignalExhale(self, bExhale:bool, percentage:float):
        
        if bExhale:
            # self.stkSignalLightExhale.setCurrentWidget(self.pgGreenLightExhale)
            
            now = time.time()
            if self.tExhale is None:
                self.tExhale = now
                
            if now - self.tExhale >= 1:
                value = self.pgbExhale.value() + 20
                self.pgbExhale.setValue(value)
                self.tExhale = now
                
                if value == 100:
                    self.btnNext_scanCT_2.setEnabled(True)
                    # self.NextScene()
                    # self.tCheckInhale.stop()
        else:
            # self.stkSignalLightExhale.setCurrentWidget(self.pgRedLightExhale)
            self.pgbExhale.setValue(0)
            self.btnNext_scanCT_2.setEnabled(False)
            self.tExhale = None
        self.indicatorExhale.setValue(percentage)
        
    def Laser_OnSignalShowCounter(self, ms:int):
        ms = int(ms * 0.001)
        self.lblCounter.setText(str(ms))
    
    def Laser_OnSignalUpdateCycle(self, tupPercent:tuple, nCycle:int):
        # strLabelName = 'lblCycle' + str(nCycle)
        # if hasattr(self, strLabelName):
        #     label = eval('self.' + strLabelName)
        #     # label.setText(f'Inhale:{tupAvg[0]:.3f}, Exhale:{tupAvg[1]:.3f}')
        #     if tupPercent[0] >= 80 and tupPercent[1] <= 20:
        #         label.setStyleSheet('background-color:rgb(0, 100, 0)')
        #     else:
        #         label.setStyleSheet('background-color:rgb(255, 0, 0)')
            
        # strWdgName = 'wdgCheckCycle' + str(nCycle)
        # if hasattr(self, strWdgName):
        #     wdg = eval('self.' + strWdgName)
        #     if tupPercent[0] >= 80 and tupPercent[1] <= 20:
        #         wdg.setStyleSheet('background-color:rgb(0, 100, 0);image:url("image/check.png");')
        #     else:
        #         wdg.setStyleSheet('background-color:rgb(255, 0, 0);')
        
        if tupPercent[0] >= 80 and tupPercent[1] <= 20:
            self.Laser_SetBreathingCycleUI(nCycle, True)
        else:
            self.Laser_SetBreathingCycleUI(nCycle, False)
         
        
                    
    def Laser_ShowLaserProfile(self):
        if self.Laser is None:
            return
        
        # self.Button_StartLaserDisplay.setStyleSheet("background-color:#4DE680")
        # self.Button_StopLaserDisplay.setEnabled(True)
        
        # self.laserProfileFigure = Canvas(self,dpi=200)
        # self.layout = QtWidgets.QVBoxLayout(self.MplWidget)
        # self.layout.addWidget(self.laserProfileFigure)
        self.bLaserShowProfile = True
        self.lytLaserAdjust.addWidget(self.laserFigure)
        
        self.signalShowPlot.connect(self.Laser_OnShowPlot)
        t = threading.Thread(target = self.Laser_Adjustment)
        # t = threading.Thread(target = self.sti_RunLaser)
        t.start()
        
    def Laser_OnShowPlot(self, cycle):
        y = self.Laser.slopeData
        x = np.arange(len(y))
        title = f'breathing cycle {cycle} times'
        plt.title(title)
        plt.ylabel('breathing speed')
        plt.plot(x, y)
        plt.show()
        
        # dataTemp = np.array(self.Laser.dataTemp)
        # xAxis = np.arange(len(dataTemp))
        # # slope, intercept = np.polyfit(xAxis, dataTemp, 1)
        # # yFit = xAxis * slope + intercept
        # diff = np.diff(dataTemp)
        # # fitDiff = np.array(np.array(dataTemp) - yFit)
        # mean = np.mean(dataTemp)
        # std_ev = np.std(dataTemp)
        # stdDiff = dataTemp - mean
        # threshold = std_ev * 3
        # with np.printoptions(formatter={'all':lambda x:f'{x:.3f}'}):
        #     if not hasattr(self, 'count'):
                
        #         print(f'diff = \n{diff}')
        #         print(f'std value = {std_ev}, diff=\n{stdDiff}')
        #         # print(f'fitDiff = \n{fitDiff}')
        #         self.count = 1
            
        # plt.plot(xAxis, dataTemp)
        # plt.show()
        
    def Laser_Adjustment(self):
        while self.bLaserShowProfile:
            plotData = self.Laser.PlotProfile()
            if plotData is not None:
                self.laserFigure.update_figure(plotData)
            
            # FPS 30
            sleep(0.033)
        print("Laser Adjust Done!")
        # self.signalShowPlot.emit()
        
        
    def Laser_CheckCycles(self, dataCycle):
        lstAvg = []
        nCycle = len(dataCycle)
        
        for i in range(nCycle):
            lstAvg.extend(dataCycle[i + 1]['avg'])
                                
        lstPercent = self.Laser.GetPercentFromAvg(lstAvg)
        lstPercent = np.reshape(lstPercent, (-1, 2))
                                
        indexes, = np.where((lstPercent[:, 0] < 80) | (lstPercent[:, 1] > 20))
        numOfIndexes = len(indexes)
        
        if numOfIndexes == 0:
            return True    
        elif numOfIndexes in range(1, 3):
            for i in indexes:
                del dataCycle[i + 1]
            
            nCycle = indexes[0] + 1
            
            
        elif numOfIndexes in range(3, 5):
            indexes = np.where((lstPercent[:, 0] >= 80) & (lstPercent[:, 1] <= 20))[0]
            for i in indexes:
                del dataCycle[i + 1]
                
        receiveData = {}
        for i, dicItem in dataCycle.items():
            for keyTime, cycleData in dicItem.items():
                if isinstance(keyTime, int):
                    receiveData[keyTime] = cycleData
            
        if self.Laser.DataRearrange(receiveData, self.yellowLightCriteria, self.greenLightCriteria):
            lstAvg = []
            indexes = []
            bPass = True
            for cycle, data in dataCycle.items():
                lstAvg.extend(data['avg'])
                indexes.append(cycle)
                
            lstPercent = self.Laser.GetPercentFromAvg(lstAvg)
            lstPercent = np.reshape(lstPercent, (-1, 2))
            
            for i, percent in zip(indexes, lstPercent):
                percent = tuple(percent)
                percentIn, percentEx = percent
                self.signalModelCycle.emit(percent, i)
                print(f'cycle {i} = ({percentIn}, {percentEx})')
                if percentIn < 80 or percentEx > 20:
                    bPass = False
                    
            if bPass:
                print('cycles reconstruction succeed')
            else:
                print('ccycles reconstruction failed')
                
            return bPass
        return False
        
    def Laser_StopLaserProfile(self):
        # if self.Button_StopLaserDisplay.isChecked():
        #     self.Button_StopLaserDisplay.setStyleSheet("background-color:#4DE680")
        #     self.Button_StartLaserDisplay.setStyleSheet("")
        #     self.Button_StartLaserDisplay.setEnabled(False)
        #     self.Button_RecordCycle.setEnabled(True)
        self.bLaserShowProfile  = False
        # self.Button_StopLaserDisplay.setChecked(False)
        
    def Laser_StartRecordBreathingBase(self):
        # if self.Laser is None:
        #     return
        
        self.btnStartBuildModel_2.setEnabled(False)
        self.btnAutoRecord.setEnabled(False)
        self.recordBreathingBase = False
        self.bLaserRecording = True
        # self.lytLaserModel.addWidget(self.laserFigure)
        self.lytLaserModel.replaceWidget(self.lblHintModelBuilding, self.laserFigure)
        # t = threading.Thread(target = self.Laser_RecordBreathing)
        # t = threading.Thread(target = self.Laser_RecordBreathingCycle)
        tLaser = threading.Thread(target = self.sti_RunLaser)
        tLaser.start()
        
        self.signalModelBuildingPass.connect(self.Laser_OnSignalModelPassed)
        self.signalModelCycle.connect(self.Laser_OnSignalUpdateCycle)
        t = threading.Thread(target = self.Demo_RecordBreathingCycle)
        t.start()
        
    def Laser_StopRecordBreathingBase(self):
        print("Stop")
        # if self.Button_StopRecording.isChecked():
        #     self.Button_RecordCycle.setStyleSheet("")
        #     self.Button_StopRecording.setStyleSheet("background-color:#4DE680")
        #     self.Button_StartTracking.setEnabled(True)
        #     self.Button_Accuracy.setEnabled(True)
        self.bLaserRecording = False
            # self.Button_StopRecording.setChecked(False)
            # self.tabWidget.setCurrentWidget(self.tabWidget_Low)
        # else:
        #     self.recordBreathingCommand = True
            
        # with open('laser_output.txt', mode='a', encoding='utf-8') as f:
        #     f.write(receiveData[0])
        
    def Laser_RecordBreathing(self):
        if self.Laser is None:
            return
        
        receiveDataTemp = {}
        receiveData = {}
        # self.TriggerSetting()
        print("Cheast Breathing Measure Start")
        startTime = preTime = time.time()
        
        while self.bLaserRecording is True:
            plotData = self.Laser.PlotProfile()
            curTime = time.time()
            deltaTime = int((curTime - startTime) * 1000)
            if plotData is not None:
                self.laserFigure.update_figure(plotData)
                rawData = self.Laser.ModelBuilding()
                if len(rawData) > 0:
                    receiveData[deltaTime] = rawData
                    if self.Laser.DataRearrange(receiveData, self.yellowLightCriteria, self.greenLightCriteria):
                        cycle, bValid = self.Laser.DataCheckCycle()
                        self.signalModelBuildingUI.emit(bValid)
                        if bValid:
                            self.bLaserRecording = False
                            
                        
        print(f"Breathing recording stopped.Total spends:{(curTime - startTime):.3f} sec")
        # receiveData = receiveDataTemp.copy()
        # delItems = [receiveData.pop(key, None) for key, item in receiveDataTemp.items() if not item]
        # print(f'del Items = {delItems}')
        # receiveData = [subarray for subarray in receiveDataTemp.values() if subarray]
        # receiveData = [subarray for subarray in receiveDataTemp if subarray]
        
        # rearrange receiveData
        # for item in receiveDataTemp:
        #     receiveData.append(item[0]) 
        # self.Laser.DataBaseChecking(receiveData) # make sure no data lost
        if self.Laser.DataRearrange(receiveData, self.yellowLightCriteria, self.greenLightCriteria):
            cycle, bValid = self.Laser.DataCheckCycle()
            # self.signalShowPlot.emit(cycle)
            if not bValid:
                self.signalModelBuildingPass.emit(False)
            else:
                self.recordBreathingBase = True
                self.signalModelBuildingPass.emit(True)
                # self.signalShowMessage.emit('Model building Succeed', 'Success', False)
                # print(f'parcentage = \n{self.Laser.percentageBase}')
                
    def Laser_RecordBreathingCycle(self):
        if self.Laser is None:
            return
        
        nCycle = 1
        self.dicDataCycle = {}
        self.dicDataCycle[nCycle] = {}
        print("Cheast Breathing Measure Start")
        startTime = time.time()
        
        if self.bAutoRecord:
            receiveData = {}
        else:
            receiveData = {'startTime':startTime}
            
            
        lastTime = startTime
        while self.bLaserRecording is True:
            plotData = self.Laser.PlotProfile()
            curTime = time.time()
            deltaTime = int((curTime - startTime) * 1000)
            
            if plotData is not None:
                self.laserFigure.update_figure(plotData)
                rawData = self.Laser.ModelBuilding()
                if len(rawData) > 0:
                    if len(receiveData) > 0:
                        lastData = list(receiveData.values())[-1]
                        diffData = np.abs(lastData - rawData)
                        avgDiff = np.mean(diffData)
                        if avgDiff < 0.05:
                            if curTime - lastTime > 10:
                                continue
                        else:
                            lastTime = curTime
                    
                    receiveData[deltaTime] = rawData
                    self.dicReceiveData = receiveData
                    
                    if self.bUpdateCycleData == True:
                        self.dicDataCycle[nCycle] = {}
                        self.bUpdateCycleData = False
                        
                    self.dicDataCycle[nCycle][deltaTime] = rawData
                    
                    # auto recording
                    if self.bAutoRecord:
                        tupAvg = self.Laser.ModelAnalyze(self.dicDataCycle[nCycle])
                        
                        if tupAvg is not None:
                            if self.Laser.DataRearrange(receiveData, self.yellowLightCriteria, self.greenLightCriteria):
                                
                                self.dicDataCycle[nCycle]['avg'] = tupAvg
                                lstAvg = []
                                for i in range(nCycle):
                                    if self.dicDataCycle.get(i + 1):
                                        lstAvg.extend(self.dicDataCycle[i + 1]['avg'])
                                        
                                lstPercent = self.Laser.GetPercentFromAvg(lstAvg)
                                lstPercent = np.reshape(lstPercent, (-1, 2))
                                
                                for i, percent in enumerate(lstPercent, 1):
                                    percent = tuple(percent)
                                    percentIn, percentEx = percent
                                    self.signalModelCycle.emit(percent, i)
                                    print(f'cycle {i} = ({percentIn}, {percentEx})')
                                print('=' * 50)
                            
                            while self.dicDataCycle.get(nCycle + 1) is not None:
                                nCycle += 1
                            nCycle += 1
                                
                            if nCycle > 5:
                                bValid = self.Laser_CheckCycles(self.dicDataCycle)
                                self.bLaserRecording = False
                                
                                if not bValid:
                                        self.signalModelBuildingPass.emit(False)
                                else:
                                    self.recordBreathingBase = True
                                    self.signalModelBuildingPass.emit(True)
                                
                            self.dicDataCycle[nCycle] = {}
                        
        print(f"Breathing recording stopped.Total spends:{(curTime - startTime):.3f} sec")
        self.signalResetLaserUI.emit()
        
    def Laser_OnTracking(self):
        if self.Laser is None:
            return
        
        print("即時量測呼吸狀態")
        if self.recordBreathingBase is True:
            self.bLaserTracking = True
            
            # t_laser = threading.Thread(target = self.Laser_FuncLaserTracking)
            t_laser = threading.Thread(target = self.Laser_OnThreadTracking)
            t_laser.start()
        else:
            print("Please build cheast breathing model first.")
            
    def Laser_OnThreadTracking(self):
        self.avgValueDataTmp = []
        
        while self.bLaserTracking is True:
            self.Laser.RealTimeHeightAvg() #透過計算出即時的HeightAvg, 顯示燈號
            
        with open('AVG_data.txt', mode='w') as f:
            for data in self.avgValueDataTmp:
                f.write(f'{data},')
                
    def Laser_StopTracking(self):
        # if self.Button_StopLaserTracking.isChecked():
        #     self.Button_StartTracking.setStyleSheet("")
        #     self.Button_StopLaserTracking.setStyleSheet("background-color:#4DE680")
        self.bLaserTracking = False
            # self.Button_StopLaserTracking.setChecked(False)
        if hasattr(self, 'robot'):
            try:
                # self.robot.RealTimeTracking(self.breathingPercentage)
                self.RobotRun()
            except:
                print("Robot Compensation error")
        # else:
        #     self.trackingBreathingCommand = True
    
    def Laser_CheckInhale(self):
        layout = self.wdgIndicatorInhale.layout()
        if layout is None:
            self.indicatorInhale = Indicator(TYPE_INHALE) 
            layout = QVBoxLayout(self.wdgIndicatorInhale)
            layout.addWidget(self.indicatorInhale)
            layout.setContentsMargins(0, 0, 0, 0)
        
        self.signalDemoInhale.connect(self.Laser_OnSignalInhale)
        
        self.percentInhale = 90
        
        self.tCheckInhale = QTimer()
        # self.tCheckInhale.timeout.connect(self.Laser.CheckInhale)
        self.tCheckInhale.timeout.connect(self.Demo_CheckInhale)
        self.tCheckInhale.start(50)
        
    def Laser_CheckExhale(self):
        layout = self.wdgIndicatorExhale.layout()
        if layout is None:
            self.indicatorExhale = Indicator(TYPE_EXHALE) 
            layout = QVBoxLayout(self.wdgIndicatorExhale)
            layout.addWidget(self.indicatorExhale)
            layout.setContentsMargins(0, 0, 0, 0)
        
        self.signalDemoExhale.connect(self.Laser_OnSignalExhale)
        
        self.percentExhale = 10
        
        self.tCheckExhale = QTimer()
        # self.tCheckExhale.timeout.connect(self.Laser.CheckExhale)
        self.tCheckExhale.timeout.connect(self.Demo_CheckExhale)
        self.tCheckExhale.start(50)
        
        
    def Laser_GetAverageRatio(self, ratio):
        self.avgValueDataTmp = []
        self.lcdBreathingRatio.display(ratio)
        
        if self.greenLightCriteria is not None and self.yellowLightCriteria is not None:
            if ratio >= self.greenLightCriteria:  #綠燈
                self.lcdBreathingRatio.setStyleSheet("#lcdBreathingRatio{border: 2px solid black; color: green; background: silver;}")
            elif ratio >= self.yellowLightCriteria and ratio < self.greenLightCriteria: #黃燈
                self.lcdBreathingRatio.setStyleSheet("#lcdBreathingRatio{border: 2px solid black; color: yellow; background: silver;}")
            else:
                self.lcdBreathingRatio.setStyleSheet("#lcdBreathingRatio{border: 2px solid black; color: red; background: silver;}")
                    
            # self.laserFigure.update_figure(self.Laser.PlotProfile())
            self.avgValueDataTmp.append(ratio)
            
            if type(ratio) is np.float64:
                self.breathingPercentage = ratio     
                
        
            
    def Laser_FuncLaserTracking(self):
        self.avgValueDataTmp = []
        
        while self.bLaserTracking is True:
            breathingPercentageTemp = self.Laser.RealTimeHeightAvg(self.yellowLightCriteria, self.greenLightCriteria) #透過計算出即時的HeightAvg, 顯示燈號
            
            self.lcdBreathingRatio.display(breathingPercentageTemp)
            
            if breathingPercentageTemp is not None:
                if self.greenLightCriteria is not None and self.yellowLightCriteria is not None:
                    if breathingPercentageTemp >= self.greenLightCriteria:  #綠燈
                        self.lcdBreathingRatio.setStyleSheet("#lcdBreathingRatio{border: 2px solid black; color: green; background: silver;}")
                    elif breathingPercentageTemp >= self.yellowLightCriteria and breathingPercentageTemp < self.greenLightCriteria: #黃燈
                        self.lcdBreathingRatio.setStyleSheet("#lcdBreathingRatio{border: 2px solid black; color: yellow; background: silver;}")
                    else:
                        self.lcdBreathingRatio.setStyleSheet("#lcdBreathingRatio{border: 2px solid black; color: red; background: silver;}")
                        
                # self.laserFigure.update_figure(self.Laser.PlotProfile())
                
                self.avgValueDataTmp.append(breathingPercentageTemp)
                
                if type(breathingPercentageTemp) is np.float64:
                    self.breathingPercentage = breathingPercentageTemp                
                    print(self.breathingPercentage)
        with open('AVG_data.txt', mode='w') as f:
            for data in self.avgValueDataTmp:
                f.write(f'{data},')
                
    def Laser_Close(self):
        if self.tCheckInhale:
            self.tCheckInhale.stop()
            
        if self.tCheckExhale:
            self.tCheckExhale.stop()
            
            
        if self.bLaserTracking or self.bLaserRecording or self.bLaserShowProfile:
            self.bLaserForceClose = True
            
        self.bLaserTracking = False
        self.bLaserRecording = False
        self.bLaserShowProfile = False
        try:
            # waiting for thread end
            sleep(1)
            if self.Laser is not None:
                self.Laser.CloseLaser()
        except Exception as e:
            print(e)
            print("close Laser error")
        
            
#画布控件继承自 matplotlib.backends.backend_qt5agg.FigureCanvasQTAgg 类
class Canvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=3, height=2.5, dpi=100):
        # plt.rcParams['figure.facecolor'] = 'r'
        # plt.rcParams['axes.facecolor'] = 'b'
        plt.rcParams['axes.prop_cycle'] = cycler(color=['r', 'g'])
        # plt.rcParams['axes.unicode_minus'] = False
        
        fig = Figure(figsize=(width, height), dpi=dpi) #创建画布,设置宽高，每英寸像素点数
        fig.set_facecolor('#4D84AD')
        
        self.axes = fig.add_subplot(111)#
        self.axes.set_facecolor('#4D84AD')
        self.axes.set_ylabel('Lung Volume (mL)')
        
        FigureCanvasQTAgg.__init__(self, fig)#调用基类的初始化函数
        self.setParent(parent)
        FigureCanvasQTAgg.updateGeometry(self)
        
    def update_figure(self,receiveData):
        if not hasattr(self, 'line1'):
            # self.line1, self.line2= self.axes.plot(range(len(receiveData[0])), receiveData[0], [], [])
            self.line1, self.line2 = self.axes.plot([], [], [], [])
            # self.line2 = self.axes.plot([], [])
            # self.axes.cla()#清除已绘的图形
            self.axes.set_xlim([1,640])
            self.axes.set_ylim([-125,-75])
            
            
            # 在設置tick label之前設置ticks，來免除警告
            self.axes.set_yticks(self.axes.get_yticks())
            # 不顯示負號
            self.axes.set_yticklabels([str((tick + 130) * 100) for tick in self.axes.get_yticks()])
            
        
        
        self.line1.set_data(range(len(receiveData[0])), receiveData[0])
        self.line2.set_data(range(len(receiveData[1])), receiveData[1])
        self.draw()#重新绘制
        
class WidgetProcess(QWidget):
    angle = 0
    angleStep = 3.6
    radius = 100
    circleWidth = 10
    signalPercent = pyqtSignal(float)
    signalFinished = pyqtSignal()
    bFinished = False
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        centerX = int(self.width() * 0.5)
        centerY = int(self.height() * 0.5)
        
        center = self.rect().center()
        painter.translate(center)
        
        conical = QConicalGradient(0, 0, self.angle)
        # conical = QConicalGradient(center.x(), center.y(), self.angle)
        conical.setColorAt(0, Qt.transparent)
        conical.setColorAt(0.4, Qt.red)
        conical.setColorAt(0.6, Qt.blue)
        conical.setColorAt(1, Qt.transparent)
        
        painter.setPen(Qt.transparent)
        painter.setBrush(conical)
        self.radius = min(self.radius, centerX, centerY)
        painter.drawPie( - self.radius,  - self.radius, self.radius * 2, self.radius * 2, 0 * 16, int(self.angle * 16))
        # painter.translate(-center)
        mask = QRegion(center.x() - self.radius, center.y() - self.radius, self.radius * 2, self.radius * 2, QRegion.Ellipse)
        maskRadius = self.radius - self.circleWidth
        mask2 = QRegion(center.x() - maskRadius, center.y() - maskRadius, maskRadius * 2, maskRadius * 2, QRegion.Ellipse)
        
        self.setMask(mask.subtracted(mask2))
        
        # painter.drawPie( - self.radius,  - self.radius, self.radius * 2, self.radius * 2, 0 * 16, int(self.angle * 16))
        
        # painter.fillRect(mask.boundingRect(), QBrush(conical))
        
    def UpdateProgress(self, percent:float):
        # self.angle = self.angle + self.angleStep
        # percent = min(self.angle / 360.0, 1)
        # self.signalPercent.emit(percent)
        self.angle = 360.0 * percent
        self.update()
        
        
        # if percent >= 1:
        #     QTimer.singleShot(1000, lambda:self.signalFinished.emit())
        
class HomingWidget(QDialog, FunctionLib_UI.Ui_homing.Ui_dlgHoming):
    nProgress = 0
    percent = 0
    signalFinish = pyqtSignal()
    signalHoming = pyqtSignal()
    signalProgress = pyqtSignal(float)
    
    def __init__(self, parent: QWidget):
        super().__init__()
        self.setupUi(self)
        
        
        # layout.removeWidget(self.wdgProcess)
        # layout.addWidget(self.wdgProcess, 1, 2, Qt.AlignCenter)
        
        # self.wdgHoming.setStyleSheet('border-image:url(image/robot.png)')
        self.player = QMediaPlayer()
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile('video/Homing Robot.mp4')))
        
        videoWidget = QVideoWidget()
        videoWidget.setAspectRatioMode(Qt.KeepAspectRatio)
        self.player.setVideoOutput(videoWidget)
    
        layout = self.wdgHoming.layout()
        layout.addWidget(videoWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.player.play()
        self.player.mediaStatusChanged.connect(self.OnStatusChanged)
        
        # layout = self.layout()
        layout = self.layoutH
        naviButton = NaviButton(self)
        naviButton.CopyPropertyFrom(self.btnStartHoming)
        layout.removeWidget(self.btnStartHoming)
        # layout.addWidget(naviButton, 1, 1, Qt.AlignCenter)
        layout.addWidget(naviButton)
        self.btnStartHoming = naviButton
        
        widget = WidgetProcess(self)
        widget.setMinimumSize(120, 120)
        # widget.signalPercent.connect(self.OnSignal_Percent)
        
        layoutButton = QVBoxLayout(self.btnStartHoming)
        layoutButton.addWidget(widget)
        self.circleWidget = widget
        
        self.initEvent()
        
    def initEvent(self):
        self.btnStartHoming.clicked.connect(self.onClick_StartHoming)
        self.signalProgress.connect(self.OnSignal_UpdateProgress)
        # self.t = QTimer()
        # self.t.timeout.connect(self.onTimeout)
        
        # self.circleWidget.signalFinished.connect(self.OnSignal_Finished)
        
    def onClick_StartHoming(self):
        styleSheet = self.btnStartHoming.styleSheet()
        
        bFound = False
        newStyle = None
        for substr in styleSheet.split('{'):
            for s in substr.split(';'):
                s = s.strip()
                if s.startswith("font"):
                    newStyle = styleSheet.replace(s, 'font:12px Arial')
                    bFound = True
            if bFound:
                break
        
        if newStyle:
            self.btnStartHoming.setStyleSheet(newStyle)
            
        # self.t.start(50)
        self.btnStartHoming.setEnabled(False)
        
        self.signalHoming.emit()
        
    def onTimeout(self):
        pass
        # self.circleWidget.UpdateProgress()
        # print('running')
        
    def OnSignal_Percent(self, percent:float):
        self.percent = percent
        percent = min(1, percent)
        # self.wdgProcess.OnSignal_Percent(percent)
        # self.btnStartHoming.OnSignal_Percent(percent)
        # self.circleWidget.UpdateProgress(percent)
        self.signalProgress.emit(percent)
        if percent >= 1:
            # self.t.stop()
            self.OnSignal_Finished()
            
    def OnSignal_UpdateProgress(self, percent:float):
        self.btnStartHoming.OnSignal_Percent(percent)
        self.circleWidget.UpdateProgress(percent)
            
    def OnSignal_Finished(self):
        # self.signalFinish.emit()
        # self.t.stop()
        self.player.stop()
        self.close()
        
    def OnStatusChanged(self, status):
        if status == QMediaPlayer.EndOfMedia:
            sleep(0.5)
            self.player.play()
            
class DlgHint(QWidget, FunctionLib_UI.Ui_DlgHint.Ui_Form):
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setupUi(self)
        
        self.player = QMediaPlayer()
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile('video/hintDicom.mp4')))
        
        videoWidget = QVideoWidget()
        videoWidget.setAspectRatioMode(Qt.KeepAspectRatio)
        self.player.setVideoOutput(videoWidget)
        
        layout = QVBoxLayout(self.wdgHintVideo)
        layout.addWidget(videoWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.player.play()
        self.player.mediaStatusChanged.connect(self.statusChanged)
        # self.player.playbackStateChanged(self.statusChanged)
        self.btnOK.clicked.connect(self.OnClicked_btnConfirm)
        
    def statusChanged(self, status):
        if status == QMediaPlayer.EndOfMedia:
            sleep(0.5)
            self.player.play()
            
    def closeEvent(self, event: QCloseEvent):
        self.player.stop()
        return super().closeEvent(event)
    
    def OnClicked_btnConfirm(self):
        self.close()
        
class DlgInstallAdaptor(QDialog, FunctionLib_UI.Ui_dlgInstallAdaptor.Ui_dlgInstallAdaptor):
    signalRobotStartMoving = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        
        # self.player = QMediaPlayer()
        
        # self.player.setMedia(QMediaContent(QUrl.fromLocalFile('video/InstallHolder.mp4')))
        
        # videoWidget = QVideoWidget()
        # videoWidget.setAspectRatioMode(Qt.KeepAspectRatio)
        # self.player.setVideoOutput(videoWidget)
        
        # layout = QVBoxLayout(self.wdgMedia)
        # layout.addWidget(videoWidget)
        # layout.setContentsMargins(0, 0, 0, 0)
        
        # self.player.play()
        
        # self.player.mediaStatusChanged.connect(self.statusChanged)
        self.btnConfirm.clicked.connect(self.OnClicked_btnConfirm)
        
    def statusChanged(self, status):
        if status == QMediaPlayer.EndOfMedia:
            sleep(0.5)
            self.player.play()
            
    def closeEvent(self, event: QCloseEvent):
        # self.player.stop()
        return super().closeEvent(event)
    
    def OnClicked_btnConfirm(self):
        self.signalRobotStartMoving.emit()
        self.close()
            
class DlgRobotMoving(QDialog, FunctionLib_UI.Ui_DlgRobotMoving.Ui_DlgRobotMoving):
    signalStop = pyqtSignal()
    alphaValue = 255
    alphaStep = 255.0 / 10.0
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateLabelText)
        self.timer.start(50)
        self.btnStop.clicked.connect(self.OnClicked_btnStop)
        
    def OnClicked_btnStop(self):
        self.timer.stop()
        self.close()
        self.signalStop.emit()
        
    def updateLabelText(self):
        strStyleSheet = f'font: 24pt "Arial";color:rgba(255, 0, 0, {self.alphaValue});'
        self.alphaValue = int(min(255, max(0, self.alphaValue - self.alphaStep)))
        if self.alphaValue == 0 or self.alphaValue == 255:
            self.alphaStep *= -1
        
        self.lblRobotMoving.setStyleSheet(strStyleSheet)
            
class SystemProcessing(QWidget, FunctionLib_UI.ui_processing.Ui_Form):
    def __init__(self):
        """show loading window"""
        ## 顯示 loading 畫面 ############################################################################################
        super(SystemProcessing, self).__init__()
        self.setupUi(self)
        ############################################################################################
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
    def UpdateProgress(self, value:float, content:str):
        progress = int(value * 100)
        self.pgbLoadDIcom.setValue(progress)
        content = content.replace('\\', '/')
        self.lblContent.setText('from ' + content)
        if progress >= 100:
            self.close()
            
class WidgetArrow(QWidget):
    styleBlack = 'image:url(image/arrow-black.png)'
    styleGolden = 'image:url(image/arrow-golden.png)'
    styleTextGolden = 'color:#ecec76;font-size:24pt;'
    styleTextWhite = 'color:white;font-size:16pt;'
    
    
    def __init__(self, num:int = 3):
        super().__init__()
        
        # itemName = 'wdgArrow'
        # while True:
        #     item = itemName + str(self.nArrow)
        #     if not hasattr(self, item):
        #         break
        #     self.lstArrow.append(eval('self.' + item))
        #     self.nArrow += 1
        # self.nArrow = 0
        
        self.setStyleSheet("""
                           QLabel{
                               font:16pt 'Arial';
                               color:#fff;
                           }
                           """)
        
        self.idArrow = 0
        self.timer = QTimer()
        self.lstArrow = []
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        for _ in range(num):
            arrow = QWidget()
            arrow.setMinimumSize(32, 32)
            arrow.setMaximumSize(32, 32)
            arrow.setStyleSheet(self.styleBlack)
            self.lstArrow.append(arrow)
            layout.addWidget(arrow)
            
        self.lblStepName = QLabel()
        self.lblStepName.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # self.lblStepName.setMinimumWidth(100)
        layout.addWidget(self.lblStepName)
        
        self.timer.timeout.connect(self.runArrow)
        # self.timer.start(200)
        
    def runArrow(self):
        arrowGold = self.lstArrow[self.idArrow]
        for arrow in self.lstArrow:
            if arrow == arrowGold:
                arrow.setStyleSheet(self.styleGolden)
            else:
                arrow.setStyleSheet(self.styleBlack)
        self.idArrow = (self.idArrow + 1) % len(self.lstArrow)
        
    def Active(self):
        self.timer.start(200)
        self.lblStepName.setStyleSheet(self.styleTextGolden)
        
    def Stop(self):
        self.timer.stop()
        self.lblStepName.setStyleSheet(self.styleTextWhite)
        for arrow in self.lstArrow:
            arrow.setStyleSheet(self.styleBlack)
        
    def SetStepName(self, name:str):
        self.lblStepName.setText(name)
        
class WidgetStep(QWidget):
    def __init__(self, nStep:int, arrowNum:int = 3, *stepName):
        super().__init__()
        
        self.nCurrentStep = 1
        self.lstWidgetStep = []
        
        layout = QHBoxLayout(self)
        for _ in range(nStep):
            wdgArrow = WidgetArrow(arrowNum)
            layout.addWidget(wdgArrow)
            self.lstWidgetStep.append(wdgArrow)
            
        layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding))
                
        self.SetStepNames(*stepName)
            
    def SetStepNames(self, *stepNames):
        if len(self.lstWidgetStep) == len(stepNames):
            for item, name in zip(self.lstWidgetStep, stepNames):
                item.SetStepName(name)
        
        # self.lstWidgetStep[0].StopArrow()
        
    def GotoStep(self, nStep:int):
        if nStep <= len(self.lstWidgetStep) and nStep > 0:
            for i, item in enumerate(self.lstWidgetStep):
                if i == nStep - 1:
                    item.Active()
                else:
                    item.Stop()
            self.nCurrentStep = nStep
            
    def Next(self):
        if self.nCurrentStep == len(self.lstWidgetStep):
            return None
        
        self.nCurrentStep += 1
        self.GotoStep(self.nCurrentStep)
        return self.nCurrentStep
        
    def Back(self):
        if self.nCurrentStep == 1:
            return None
        self.nCurrentStep -= 1
        self.GotoStep(self.nCurrentStep)
        return self.nCurrentStep
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
                # self.ui_CS = CoordinateSystem(self.dcmTag, self.dicom)
                # self.ui_CS.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
                # self.ui_CS.show()
            else:
                # QMessageBox.critical(self, "error", "get candidate ball error")
                MessageBox.ShowCritical("error", "get candidate ball error")
                print('get candidate ball error / SetRegistration_L() error')
                
            return
        else:
            # QMessageBox.information(self, "information", "need to set 3 balls")
            MessageBox.ShowInformation("information", "need to set 3 balls")
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
                # QMessageBox.critical(self.setPointWindow, "error", "there are already selected 3 balls")
                MessageBox.ShowCritical(setPointWindow, "error", "there are already selected 3 balls")
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
    
    