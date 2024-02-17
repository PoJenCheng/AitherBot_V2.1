
from PyQt5.QtCore import Qt
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
from FunctionLib_UI.ViewPortUnit import *
from FunctionLib_Robot.__init__ import *
import FunctionLib_Robot._class as Robot
import FunctionLib_UI.ui_processing

from cycler import cycler
import matplotlib as mpl
import matplotlib.pyplot as plt
mpl.use('QT5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
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
    player = QMediaPlayer()
    robot = None
    
    vtkImageLow = None
    vtkImageHigh = None
    selectedSeries = None
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
    
    #robot parameter
    bTrackingBreathing = False
    
    #Laser parameter
    bLaserShowProfile = False
    bLaserTracking = False
    bLaserRecording = False
    bLaserForceClose = False
    Laser = None
    recordBreathingBase = False 
    
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
        self.dicomData = []
        
        todayStr = datetime.strftime(datetime.now() - timedelta(days = 3), '%Y/%m/%d %H:%M')
        self.dicomData.append(['高金生', 'F123456789', 'M', 'CT', '512 x 512 x 209', todayStr])
        
        todayStr = datetime.strftime(datetime.now() - timedelta(days = 15, hours = 3), '%Y/%m/%d %H:%M')
        self.dicomData.append(['高金生', 'F123456789', 'M', 'MR', '512 x 512 x 128', todayStr])
        
        todayStr = datetime.strftime(datetime.now() - timedelta(days = 6, hours = 9), '%Y/%m/%d %H:%M')
        self.dicomData.append(['克蕾兒', 'F229034126', 'F', 'MR', '256 x 256 x 78', todayStr])
        
        todayStr = datetime.strftime(datetime.now() - timedelta(days = 4, hours = 14), '%Y/%m/%d %H:%M')
        self.dicomData.append(['克蕾兒', 'F229034126', 'F', 'CT', '512 x 512 x 978', todayStr])
        
        todayStr = datetime.strftime(datetime.now() - timedelta(days = 41, hours = 4), '%Y/%m/%d %H:%M')
        self.dicomData.append(['克蕾兒', 'F229034126', 'F', 'MR', '256 x 256 x 74', todayStr])
        
        todayStr = datetime.strftime(datetime.now() - timedelta(days = 5, hours = 6), '%Y/%m/%d %H:%M')
        self.dicomData.append(['高金生', 'F123456789', 'M', 'CT', '512 x 512 x 329', todayStr])
        
        todayStr = datetime.strftime(datetime.now() - timedelta(days = 4), '%Y/%m/%d %H:%M')
        self.dicomData.append(['浅川 悠', 'A299919191', 'F', 'CT', '512 x 512 x 209', todayStr])
        
        todayStr = datetime.strftime(datetime.now() - timedelta(days = 4), '%Y/%m/%d %H:%M')
        self.dicomData.append(['史塔克', 'E125392530', 'M', 'CT', '512 x 512 x 224', todayStr])
        
        todayStr = datetime.strftime(datetime.now() - timedelta(days = 30), '%Y/%m/%d %H:%M')
        self.dicomData.append(['史塔克', 'E125392530', 'M', 'MR', '512 x 512 x 132', todayStr])
        
        todayStr = datetime.strftime(datetime.now() - timedelta(days = 2), '%Y/%m/%d %H:%M')
        self.dicomData.append(['里昂', 'F123987940', 'M', 'CT', '512 x 512 x 365', todayStr])
        
        
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
        
        #Laser =================================================
        self.yellowLightCriteria = yellowLightCriteria_LowAccuracy
        self.greenLightCriteria = greenLightCriteria_LowAccuracy
        
        self.SetUIEnable_Trajectory(False)
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
                    itemDimension = QStandardItem(f'{dim[2]} x {dim[1]} x {dim[0]}')
                    
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
                        QMessageBox.critical(None, 'dicom error', f'series UID [{slice.SeriesInstanceUID}] missing spacing infomation')
                        strSpacing = 'NONE'
                    else:
                        spacing = spacingXY[:]
                        if spacingZ:
                            spacing.append(spacingZ)
                        else:
                            spacing.append('NONE')
                        strSpacing = f'{spacing[0]:.3f} x {spacing[1]:.3f} x {spacing[2]:.3f}'.rstrip('.0')
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
        self.treeDicom.selectionModel().currentRowChanged.connect(self.OnCurrentRowChanged_treeDicom)
        # header = self.treeDicomFilter.header()
        # header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.selectedSeries = None
        
        
        
        
        
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
        
        # self.btnBack_scanCT.clicked.connect(self.BackScene)
        # self.btnBack_settingLaser.clicked.connect(self.BackScene)
        # self.btnBack_settingRobot.clicked.connect(self.BackScene)
        
        # self.btnNext_scanCT.clicked.connect(self.NextScene)
        # self.btnNext_settingLaser.clicked.connect(self.NextScene)
        # self.btnNext_settingRobot.clicked.connect(self.NextScene)
        
        self.signalSetCheck.connect(self.onSignal_SetCheck)
        
        # self.btnNext_confirmHomingStep2.clicked.connect(self.StartHoming)
        self.btnNext_settingRobot.clicked.connect(self.Robot_StartHoming)
        
        self.laserFigure = Canvas(self, dpi = 200)
        self.lytLaserAdjust = QVBoxLayout(self.wdgLaserPlot)
        self.lytLaserAdjust.addWidget(self.laserFigure)
        self.lytLaserModel = QVBoxLayout(self.wdgLaserPlot2)
        
        
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
        
        header = self.treeDicom.header()
        # header.setMinimumSectionSize(120)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignHCenter)
        
        modelFilter.sort(1, Qt.AscendingOrder)
        self.treeDicomFilter.setModel(modelFilter)
        self.treeDicomFilter.expandAll()
        
        header = self.treeDicomFilter.header()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
        self.treeDicom.selectionModel().currentRowChanged.connect(self.OnCurrentRowChanged_treeDicom)
        
        # self.importDicom(self.dicomData)
        self.player.error.connect(lambda:print(f'media player error:{self.player.errorString()}'))
        
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
        self.vtkImageLow = self.reader.GetData()
        if self.vtkImageLow is None:
            QMessageBox.critical(None, 'ERROR', 'image error')
            return False
        
        # if self.currentTag == self.dicDicom.get(self.btnDicomLow.objectName()):
        self.dicomLow.LoadImage(self.vtkImageLow)
        dicomTag = self.SetDicomData(self.dicomLow, 'LOW')
        
        if not dicomTag:
            QMessageBox.critical(None, 'DICOM TAG ERROR', 'missing current tag [LOW]')
            return False
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
        self.vtkImageHigh = self.reader.GetDataFromIndex(0, 0, -1)
        if self.vtkImageHigh is None:
            QMessageBox.critical(None, 'ERROR', 'image error')
            return False
        
        # if self.currentTag == self.dicDicom.get(self.btnDicomHigh.objectName()):
        self.dicomHigh.LoadImage(self.vtkImageHigh)
        dicomTag = self.SetDicomData(self.dicomHigh, 'HIGH')
        
        if not dicomTag:
            QMessageBox.critical(None, 'DICOM TAG ERROR', 'missing current tag [HIGH]')
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
        
        self.listSubDialog = []
        
        dlgRobotMoving = DlgRobotMoving()
        dlgRobotMoving.signalStop.connect(self.Robot_Stop)
        dlgRobotMoving.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        dlgRobotMoving.setModal(True)
        dlgRobotMoving.exec_()
        
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
                            QMessageBox.critical(None, 'DICOM ERROR', 'missing current dicom')
                        
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
            
    def OnCurrentRowChanged_treeDicom(self, current:QModelIndex, previous:QModelIndex):
        index = current.sibling(current.row(), 0)
        model:QStandardItemModel = self.treeDicom.model()
        item:QStandardItem = model.itemFromIndex(index)
        if item:
            idPatient = item.data(Qt.UserRole + 1)
            idStudy   = item.data(Qt.UserRole + 2)
            idSeries  = item.data(Qt.UserRole + 3)
            print(f'patient ID = {idPatient}')
            print(f'Study ID   = {idStudy}')
            print(f'Series ID  = {idSeries}')
            self.selectedSeries = [idPatient, idStudy, idSeries]
            self.reader.SelectDataFromID(idPatient, idStudy, idSeries)
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
                if not self.selectedSeries:
                    QMessageBox.critical(None, 'ERROR', 'please select at least one series')
                    return
                
                self.ImportDicom_H()
                if not self.ImportDicom_L():
                    return
                print('dicom changed')
            elif button == self.btnNext_startAdjustLaser:
                self.Laser_StopLaserProfile()
                print('stopped Adjust laser')
            elif button == self.btnNext_startBuildModel:
                self.Laser_StartRecordBreathingBase()
                print('start model building')
            elif button == self.btnNext_endBuildModel:
                self.Laser_StopRecordBreathingBase()
                print('end model building')
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
                    print(f'dicom dir = {filePath}')
                    self.importDicom(filePath)
                    
                else:
                    return
            elif button == self.btnFromCD:
                return
                
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
            QMessageBox.critical(None, 'dicom error', 'dicom name not exists')
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
        
    def MainSceneChanged(self, index):
        if self.stkMain.currentWidget() == self.page_loading:
            # self.stkMain.setCurrentWidget(self.pgScene)
            # self.stkScene.setCurrentWidget(self.pgImportDicom)
            # self.stkScene.setCurrentWidget(self.pgLaser)
            
            # self.loadingRobot = 100
            self.Laser = Robot.LineLaser()
            self.Laser.signalProgress.connect(self.Laser_OnLoading)
            self.Laser.signalModelPassed.connect(self.Laser_OnSignalModelPassed)
            self.Laser.signalBreathingRatio.connect(self.Laser_GetAverageRatio)
            tLaser= threading.Thread(target = self.Laser.Initialize)
            tLaser.start()
            
            # self.loadingLaser = 100
            self.robot = Robot.MOTORSUBFUNCTION()
            self.robot.signalProgress.connect(self.Robot_OnLoading)
            
            self.tRobot = threading.Thread(target = self.robot.Initialize)
            # self.tRobot = threading.Thread(target = self.robot.sti_init)
            self.tRobot.start()
            
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
        elif currentWidget == self.pgDicomList:
            pass
            # if self.bDicomChanged:
            #     self.importDicom('C:\\Leon\\CT')
                # self.importDicom('C:\\Leon\\dicom_test')
            
        elif currentWidget == self.pgRobotRegSphere:
            self.player.stop()
            self.playVedio(self.wdgSetupBall, 'video/ball_setup.mp4')
            
        elif currentWidget == self.pgRobotSupportArm:
            self.player.stop()
            self.playVedio(self.wdgSetupRobot, 'video/robot_mount_support_arm.mp4')
        elif currentWidget == self.pgSterileStep3:
            self.GetRobotPosition()
        else:
            self.player.stop()
        
        self.CheckStage(index)
        
        if self.IsStage(index, STAGE_IMAGE):
            self.SetStage(STAGE_IMAGE)
        elif self.IsStage(index, STAGE_DICOM) and \
            self.bFinishLaser and self.bFinishRobot and self.bFinishDicom:
            self.SetStage(STAGE_IMAGE)
        elif self.IsStage(index, STAGE_LASER) and self.bFinishLaser:
            self.SetStage(STAGE_IMAGE)
        elif self.IsStage(index, STAGE_ROBOT) and self.bFinishRobot:
            self.SetStage(STAGE_LASER)
            
        # 紀錄目前已經完成的階段
        self.indexDoneStage = max(self.indexCurrentStage, index)
        
        self.SetStageButtonStyle(self.indexDoneStage)
        self.indexCurrentStage = index
        # if self.stkScene.currentWidget() == self.pgImageView:
        #     self.wdgNaviBar.hide()
        
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
            
    def SetStage(self, stage:str, bToStage:bool = True):
        
        index = 0
        if stage == STAGE_ROBOT:
            self.bFinishRobot = False
            self.btnSceneRobot.setEnabled(False)
            self.btnSceneLaser.setEnabled(False)
            self.btnSceneView.setEnabled(False)
            if bToStage:
                # self.stkScene.setCurrentWidget(self.pgHomingCheckStep1)
                index = self.stkScene.indexOf(self.pgHomingCheckStep1)
                self.stkScene.setCurrentIndex(index)
                
        elif stage == STAGE_LASER:
            # self.bFinishRobot = True
            self.bFinishLaser = False
            self.btnSceneRobot.setEnabled(True)
            self.btnSceneLaser.setEnabled(False)
            self.btnSceneView.setEnabled(False)
            if bToStage:
                # self.stkScene.setCurrentWidget(self.pgLaser)
                index = self.stkScene.indexOf(self.pgLaser)
                self.stkScene.setCurrentIndex(index)
        elif stage == STAGE_DICOM:
            # self.bFinishRobot = True
            # self.bFinishLaser = True
            self.bFinishDicom = False
            self.btnSceneRobot.setEnabled(True)
            self.btnSceneLaser.setEnabled(True)
            self.btnSceneView.setEnabled(False)
            if bToStage:
                # self.stkScene.setCurrentWidget(self.pgImportDicom)
                index = self.stkScene.indexOf(self.pgImportDicom)
                self.stkScene.setCurrentIndex(index)
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
        if self.IsStage(index, STAGE_LASER):
            self.bFinishRobot = True
            self.btnSceneRobot.setEnabled(True)
        elif self.IsStage(index, STAGE_DICOM):
            self.bFinishLaser = True
            self.btnSceneLaser.setEnabled(True)
        elif self.IsStage(index, STAGE_IMAGE):
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
        else:
            videoWidget = layout.itemAt(0).widget()
            self.player.setVideoOutput(videoWidget)
        
        self.player.play()
        self.player.mediaStatusChanged.connect(self.OnStatusChanged)
        
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
            
        return self.dataTmp
    
    def sti_RunLaser(self):
        self.startNum = -110
        self.recordTime = datetime.now().timestamp()
        delta = datetime.now().timestamp() - self.recordTime
        while delta < 5:
            delta = datetime.now().timestamp() - self.recordTime
            self.laserFigure.update_figure(self.sti_LaserOutput())
            self.startNum += np.sin(delta * np.pi) * 2
            
            sleep(0.1)
        
    def closeEvent(self, event):
        self.Laser_Close()
        try:
            
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
        if self.Robot_SetLoadingMessage(strState) == False:
            self.Laser.bStop = True
            QMessageBox.critical(None, 'ERROR', 'Robot connection Failed, system will shutdown')
            self.close()
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

        self.player.stop()
        if not self.robot:
            return
        
        self.robot.signalProgress.disconnect(self.Robot_OnLoading)
        
        self.uiHoming = HomingWidget(self)
        self.uiHoming.finished.connect(lambda:self.NextScene())
        self.uiHoming.signalHoming.connect(self.Robot_HomingProcess)
        self.robot.signalHomingProgress.connect(self.uiHoming.OnSignal_Percent)
        
        self.uiHoming.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.uiHoming.setModal(True)
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
                
    def Robot_Stop(self):
        QMessageBox.information(None, 'Info', 'Robot Stop')
        
    def Laser_SetLoadingMessage(self, msg:str):
        fmt = QTextCharFormat()
        if msg.startswith('[ERROR]'):
            fmt.setForeground(QColor(100, 0, 0))
        else:
            msg = '[SUCCEED]' + msg
            fmt.setForeground(QColor(  0, 100, 0))
            
        self.pteProgress.mergeCurrentCharFormat(fmt) 
        self.pteProgress.appendPlainText(msg)
        
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
                    
    def Laser_OnSignalModelPassed(self, bPass):
        if self.bLaserForceClose:
            return
        
        if bPass:
            QMessageBox.information(None, 'Model Building Succeed', 'Model Base Checking done!')
        else:
            QMessageBox.critical(None, 'Model Building Failed', 'Please try to build chest model again.')
                    
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
        t = threading.Thread(target = self.Laser_Adjustment)
        t.start()
        
    def Laser_Adjustment(self):
        while self.bLaserShowProfile:
            self.laserFigure.update_figure(self.Laser.PlotProfile())
            # FPS 30
            sleep(0.033)
        print("Laser Adjust Done!")
        
    def Laser_StopLaserProfile(self):
        # if self.Button_StopLaserDisplay.isChecked():
        #     self.Button_StopLaserDisplay.setStyleSheet("background-color:#4DE680")
        #     self.Button_StartLaserDisplay.setStyleSheet("")
        #     self.Button_StartLaserDisplay.setEnabled(False)
        #     self.Button_RecordCycle.setEnabled(True)
        self.bLaserShowProfile  = False
        # self.Button_StopLaserDisplay.setChecked(False)
        
    def Laser_StartRecordBreathingBase(self):
        if self.Laser is None:
            return
        
        # self.Button_StopLaserDisplay.setEnabled(False)
        # self.Button_StopRecording.setEnabled(True)
        # self.Button_StopLaserDisplay.setStyleSheet("")
        # self.Button_RecordCycle.setStyleSheet("background-color:#4DE680")
        self.recordBreathingBase = False
        self.bLaserRecording = True
        self.lytLaserModel.addWidget(self.laserFigure)
        t = threading.Thread(target = self.Laser_RecordBreathing)
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
        
        receiveDataTemp = []
        receiveData = []
        # self.TriggerSetting()
        print("Cheast Breathing Measure Start")
        while self.bLaserRecording is True:
            receiveDataTemp.append(self.Laser.ModelBuilding())
            self.laserFigure.update_figure(self.Laser.PlotProfile())
            self.recordBreathingBase = True
        print("Breathing recording stopped.")
        
        receiveDataTemp = [subarray for subarray in receiveDataTemp if subarray]
        # rearrange receiveData
        for item in receiveDataTemp:
            receiveData.append(item[0]) 
        self.Laser.DataBaseChecking(receiveData) # make sure no data lost
        self.Laser.DataRearrange(receiveData, self.yellowLightCriteria, self.greenLightCriteria) 
        
    def Laser_OnTracking(self):
        if self.Laser is None:
            return
        
        print("即時量測呼吸狀態")
        if self.recordBreathingBase is True:
            # self.Button_StopRecording.setStyleSheet("")
            # self.Button_StartTracking.setStyleSheet("background-color:#4DE680")
            
            # self.Button_StopLaserTracking.setStyleSheet("")
            # self.Button_StopLaserTracking.setEnabled(True)
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
                self.robot.RealTimeTracking(self.breathingPercentage)
                self.MoveToPoint()
            except:
                print("Robot Compensation error")
        # else:
        #     self.trackingBreathingCommand = True
        
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
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # plt.rcParams['figure.facecolor'] = 'r'
        # plt.rcParams['axes.facecolor'] = 'b'
        plt.rcParams['axes.prop_cycle'] = cycler(color=['r', 'g'])
        # plt.rcParams['axes.unicode_minus'] = False
        
        fig = Figure(figsize=(width, height), dpi=dpi) #创建画布,设置宽高，每英寸像素点数
        
        self.axes = fig.add_subplot(111)#
        
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
            self.axes.set_ylim([-125,-65])
            
            # 在設置tick label之前設置ticks，來免除警告
            self.axes.set_yticks(self.axes.get_yticks())
            # 不顯示負號
            self.axes.set_yticklabels([str(abs(tick)) for tick in self.axes.get_yticks()])
        
        
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
        
        
class DlgInstallAdaptor(QDialog, FunctionLib_UI.Ui_dlgInstallAdaptor.Ui_dlgInstallAdaptor):
    signalRobotStartMoving = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        
        self.player = QMediaPlayer()
        
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile('video/InstallHolder.mp4')))
        
        videoWidget = QVideoWidget()
        videoWidget.setAspectRatioMode(Qt.KeepAspectRatio)
        self.player.setVideoOutput(videoWidget)
        
        layout = QVBoxLayout(self.wdgMedia)
        layout.addWidget(videoWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.player.play()
        
        self.player.mediaStatusChanged.connect(self.statusChanged)
        # self.player.playbackStateChanged(self.statusChanged)
        self.btnConfirm.clicked.connect(self.OnClicked_btnConfirm)
        
    def statusChanged(self, status):
        if status == QMediaPlayer.EndOfMedia:
            sleep(0.5)
            self.player.play()
            
    def closeEvent(self, event: QCloseEvent):
        self.player.stop()
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
        
    def UpdateProgress(self, value):
        progress = int(value * 100)
        self.pgbLoadDIcom.setValue(progress)
        if progress >= 100:
            self.close()