
import nest_asyncio
import math
import os
import subprocess
import sys
import shutil
import threading
import time
from datetime import datetime, timedelta
from functools import reduce
from time import sleep
from xml.dom.minidom import parse
import xml.dom.minidom as xdom

import cv2
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import torch
# from skimage import io
from cycler import cycler
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from numpy._typing import _ArrayLike
from PyQt5.QtCore import *
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import *
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import *

import FunctionLib_Robot._class as Robot
import FunctionLib_UI.Ui_DlgFootPedal
import FunctionLib_UI.Ui_DlgHintBox
import FunctionLib_UI.Ui_DlgRobotMoving
import FunctionLib_UI.Ui_homing
import FunctionLib_UI.ui_processing
import FunctionLib_UI.Ui_step
from FunctionLib_UI.Ui_toolBox import *
from FunctionLib_UI.Ui_dlgInstallAdaptor import *
from FunctionLib_Robot.__init__ import *
from FunctionLib_Robot.logger import logger
from FunctionLib_UI.Ui__Aitherbot import *
from FunctionLib_UI.Ui_DlgFootPedal import *
from FunctionLib_UI.Ui_DlgHint import *
from FunctionLib_UI.Ui_step import *
from FunctionLib_UI.ViewPortUnit import *
from FunctionLib_UI.WidgetButton import *
from FunctionLib_UI.Ui_DlgExportLog import *
from FunctionLib_UI.Ui_formFluoroSlider import *
import FunctionLib_Vision.lungSegmentation as lung

mpl.use('QT5Agg')
nest_asyncio.apply()

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
    
    player = QMediaPlayer()
    robot = None
    RobotSupportArm = None
    
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
    viewport   = None
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
    bSterile = False
    
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
        self.dlgShowHint = None
        self.dlgSystemProcessing = None
        self.widgetSlider = None
        self.tempResumeData = {}
        
        # interactors
        self.lstInteractorWipe = []
        
        self.ui = Ui_MainWindow()
        self.dicomLow = DISPLAY()
        self.dicomHigh = DISPLAY()
        self.modelHide = QStandardItemModel()
        
        self.regFn = REGISTRATION()
        self.dicView['LT'] = self.wdgLeftTop
        self.dicView['RT'] = self.wdgRightTop
        self.dicView['LB'] = self.wdgLeftBottom
        self.dicView['RB'] = self.wdgRightBottom
        self.dicView['Fusion1'] = self.wdgFusionView1
        self.dicView['Fusion2'] = self.wdgFusionView2
        self.dicView['Fusion3'] = self.wdgFusionView3
        
        self.dicSliceScroll_L['LT'] = self.sbrLeftTop
        self.dicSliceScroll_L['RT'] = self.sbrRightTop
        self.dicSliceScroll_L['LB'] = self.sbrLeftBottom
        self.dicSliceScroll_L['RB'] = self.sbrRightBottom
        
        self.dicViewSelector_L['LT'] = self.cbxLeftTop
        self.dicViewSelector_L['RT'] = self.cbxRightTop
        self.dicViewSelector_L['LB'] = self.cbxLeftBottom
        self.dicViewSelector_L['RB'] = self.cbxRightBottom
        
        self.dicLastBootData = {}
        
        self.floatingBox = [WidgetToolBox() for _ in range(3)]
        
        self.currentDicom = self.buttonGroup.checkedButton().objectName()
        dicomL = self.btnDicomLow.objectName()
        dicomH = self.btnDicomHigh.objectName()
        self.dicDicom[dicomL] = {'name' : dicomL, 'trajectory':[]}
        self.dicDicom[dicomH] = {'name' : dicomH, 'trajectory':[]}
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
        
        self.lstAnimateWidget = []
        
        self.wdgAnimateUnlock = AnimationWidget('image/foot_pedal_press_hint.png')
        layout = QHBoxLayout(self.wdgBottomUnlockRobot)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.wdgAnimateUnlock)
        self.lstAnimateWidget.append(self.wdgAnimateUnlock)
        
        self.wdgAnimatePositionRobot = AnimationWidget('image/foot_pedal_press_hint.png')
        layout = QHBoxLayout(self.wdgBottomPositionRobot)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.wdgAnimatePositionRobot)
        self.lstAnimateWidget.append(self.wdgAnimatePositionRobot)
        
        self.prevSelection_trajectory = None
        
        self.stepDicom = 1
        
        #Laser =================================================
        self.yellowLightCriteria = yellowLightCriteria_LowAccuracy
        self.greenLightCriteria = greenLightCriteria_LowAccuracy
        self.showError = False
        self.nLaserErrorCount = 0
        self.lblThreshold.setText('0.004')
        
        self.btnNext_endBuildModel.setEnabled(True)
        self.SetUIEnable_Trajectory(False)
        self.spinBox.lineEdit().setHidden(True)
        #Robot =================================================
        self.btnRobotRelease.setEnabled(True)
        self.btnRobotFix.setEnabled(False)
        self.btnRobotSetTarget.setEnabled(False)
        self.btnRobotBackTarget.setEnabled(False)
        self.homeStatus = False
        self.settingTarget = False
        self.dlgFootPedal = None
        self.dlgResumeSupportArm = None
        self.dlgRobotDrive = None
        
        # trajectory tree view header item
        self.countOfVisibleItem = 0
        headerItem = QTreeWidgetItem(['', '', ''])
        headerItem.setIcon(0, QIcon(IMG_VISIBLE))
        headerItem.setData(0, ROLE_VISIBLE, 2)
        headerItem.setText(1, 'Trajectory Name')
        headerItem.setText(2, 'color')
        
        self.treeTrajectory.setHeaderItem(headerItem)
        
        # 暫時隱藏之後考慮刪除的button
        self.btnRobotFix.setHidden(True)
        self.btnRobotBackTarget.setHidden(True)
        
        widget:QWidget = self.toolBox.widget(1)
        self.toolBox.removeItem(1)
        widget.close()
        del widget
        
        widget:QWidget = self.toolTrajectory.widget(1)
        self.toolTrajectory.removeItem(1)
        widget.close()
        del widget
        
        self.init_ui()
        # self._SaveAnotherImages('image\\msgbox\\down_right_side\\dark', 'image\\msgbox\\temp')
        
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
        
        self.wdgPlanning.clicked.connect(self.OnClicked_btnPlanning)
        self.wdgGuidance.clicked.connect(self.NextSceneMain)
        self.stkScene.currentChanged.connect(self.SceneChanged)
        self.stkMain.currentChanged.connect(self.MainSceneChanged)
        self.signalLoadingReady.connect(self.OnSignal_LoadingReady)
        self.signalSetProgress.connect(self.OnSignal_SetProgress)
        self.signalShowMessage.connect(self.OnSignal_ShowMessage)
        self.signalModelBuildingUI.connect(self.OnSignal_ModelBuilding)
        self.signalModelBuildingPass.connect(self.Laser_OnSignalModelPassed)
        
        self.signalSetCheck.connect(self.OnSignal_SetCheck)
        
        self.btnNext_confirmHomingStep2.clicked.connect(self.Robot_StartHoming)
        # self.btnNext_settingRobot.clicked.connect(self.Robot_StartHoming)
        
        self.laserFigure = Canvas(self, dpi = 150)
        self.lytLaserAdjust = QVBoxLayout(self.wdgLaserPlot)
        self.lytLaserAdjust.addWidget(self.laserFigure)
        
        self.figModel = Canvas(self, dpi = 150, subplot = '121')
        layout = QVBoxLayout(self.wdgLaser)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.figModel)
        
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
        self.btnGroup_ref.buttonToggled.connect(self.OnToggled_btnGroup_ref)
        self.btnGroup_ref.setId(self.btnRef1, 0)
        self.btnGroup_ref.setId(self.btnRef2, 1)
        self.btnGroup_ref.setId(self.btnRef3, 2)
        
        self.btnGroup_fusion.idToggled.connect(self.OnToggled_btnGroup_fusion)
        self.btnGroup_fusion.setId(self.btnModeWipe, InteractorStyleWipe.MODE_WIPE)
        self.btnGroup_fusion.setId(self.btnModeBlend, InteractorStyleWipe.MODE_BLEND)
        self.btnGroup_fusion.setId(self.btnModeFluoro, InteractorStyleWipe.MODE_FLUORO)
        
        self.btnGroup_tool.idToggled.connect(self.OnToggled_btnGroup_tool)
        self.btnGroup_tool.setId(self.btnActionPointer, InteractorStyleWipe.ACTION_POINTER)
        self.btnGroup_tool.setId(self.btnActionPan, InteractorStyleWipe.ACTION_PAN)
        self.btnGroup_tool.setId(self.btnActionMove, InteractorStyleWipe.ACTION_MOVE)
        self.btnGroup_tool.setId(self.btnActionRotate, InteractorStyleWipe.ACTION_ROTATE)
        self.btnGroup_tool.setId(self.btnActionZoom, InteractorStyleWipe.ACTION_ZOOM)
        self.btnGroup_tool.setId(self.btnActionWindowLevel, InteractorStyleWipe.ACTION_WL)
        self.btnGroup_tool.setId(self.btnActionSlice, InteractorStyleWipe.ACTION_SLICE)
        
        self.btnGroup_Lung.idToggled.connect(self.OnToggled_btgGroup_Lung)
        self.btnGroup_Lung.setId(self.btnLungsInhale, InteractorStyleWipe.IMAGE_INHALE)
        self.btnGroup_Lung.setId(self.btnLungsExhale, InteractorStyleWipe.IMAGE_EXHALE)
        
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
        
        self.btnCloseToEntry.clicked.connect(self.OnClicked_btnCloseToEntry)
        self.btnCloseToTarget.clicked.connect(self.OnClicked_btnCloseToTarget)
        
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
        modelFilter.itemChanged.connect(self.OnItemChanged)
        
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
        
        self.installEventFilter(self)
        self.treeDicom.selectionModel().selectionChanged.connect(self.OnSelectionChanged_treeDicom)
        self.treeDicom.entered.connect(self.OnEntered_treeDicom)
        # self.treeDicom.installEventFilter(self)
        self.treeDicom.setItemDelegate(TreeViewDelegate())
        
        self.btnInhale.installEventFilter(self)
        self.btnExhale.installEventFilter(self)
        
        self.player.error.connect(lambda:logger.error(f'media player error:{self.player.errorString()}'))
        
        self.btnRobotRelease.clicked.connect(self.Robot_ReleaseArm)
        self.btnRobotFix.clicked.connect(self.Robot_FixArm)
        self.btnRobotSetTarget.clicked.connect(self.Robot_SettingTarget)
        self.btnRobotBackTarget.clicked.connect(self.Robot_BackToTarget)
        
        # self.btnStartBuildModel_2.clicked.connect(self.Laser_StartRecordBreathingBase)
        self.btnStartBuildModel.clicked.connect(self.Laser_StartRecordBreathingBase)
        self.spinBox.valueChanged.connect(self.OnValueChanged_spin)
        self.btnRecord.clicked.connect(self.Laser_OnClick_btnRecord)
        self.btnAutoRecord.clicked.connect(self.Laser_OnClick_btnAutoRecord)
        
        self.btnReloadDicom.clicked.connect(self.OnClicked_btnReloadDicom)
        
        self.btnDriveConfirm.clicked.connect(self.OnClicked_btnDriveConfirm)
        
        self.btnUnlockRobot_2.clicked.connect(self.Robot_ReleaseArm)
        # self.btnRobotTarget.clicked.connect(self.Robot_FixAndTarget)
        self.btnRobotResume.clicked.connect(self.Robot_BackToTarget)
        
        self.btnConfirmUniversal.clicked.connect(self._Robot_driveTo)
        
        self.btnConfirmFusion.clicked.connect(self.OnClicked_btnConfirmFusion)
        
        # fusion Axial view
        self.btnMoveUpA.clicked.connect(self.OnClicked_btnMoveUp)
        self.btnMoveDownA.clicked.connect(self.OnClicked_btnMoveDown)
        self.btnMoveLeftA.clicked.connect(self.OnClicked_btnMoveLeft)
        self.btnMoveRightA.clicked.connect(self.OnClicked_btnMoveRight)
        self.btnResetA.clicked.connect(self.OnClicked_btnReset)
        
        self.btnRotationLA.clicked.connect(self.OnClicked_btnRotationL)
        self.btnRotationRA.clicked.connect(self.OnClicked_btnRotationR)
        
        # fusion Sagittal view
        self.btnMoveUpS.clicked.connect(self.OnClicked_btnMoveUpS)
        self.btnMoveDownS.clicked.connect(self.OnClicked_btnMoveDownS)
        self.btnMoveLeftS.clicked.connect(self.OnClicked_btnMoveLeftS)
        self.btnMoveRightS.clicked.connect(self.OnClicked_btnMoveRightS)
        self.btnResetS.clicked.connect(self.OnClicked_btnResetS)
        
        self.btnRotationLS.clicked.connect(self.OnClicked_btnRotationLS)
        self.btnRotationRS.clicked.connect(self.OnClicked_btnRotationRS)
        
        # fusion Coronal view
        self.btnMoveUpC.clicked.connect(self.OnClicked_btnMoveUpC)
        self.btnMoveDownC.clicked.connect(self.OnClicked_btnMoveDownC)
        self.btnMoveLeftC.clicked.connect(self.OnClicked_btnMoveLeftC)
        self.btnMoveRightC.clicked.connect(self.OnClicked_btnMoveRightC)
        self.btnResetC.clicked.connect(self.OnClicked_btnResetC)
        
        self.btnRotationLC.clicked.connect(self.OnClicked_btnRotationLC)
        self.btnRotationRC.clicked.connect(self.OnClicked_btnRotationRC)
        
        self.wdgAnimate = AnimationWidget('image/foot_pedal_press_hint.png')
        self.lstAnimateWidget.append(self.wdgAnimate)
        
        # layout = self.wdgBottom.parentWidget().layout()
        # layout.replaceWidget(self.wdgBottom, self.wdgAnimate)
        layout = QVBoxLayout(self.wdgPedal)
        layout.addWidget(self.wdgAnimate)
        
        # layoutAnimate = QVBoxLayout(self.wdgAnimate)
        # layoutAnimate.setContentsMargins(0, 0, 0, 0)
        # layoutAnimate.addWidget(self.wdgBottom)
        
        # self.wdgAnimateUnlock.signalIdle.connect(self.Robot_GetPedal)
        # self.wdgAnimatePositionRobot.signalIdle.connect(self.Robot_GetPedal)
        # self.wdgAnimate.signalIdle.connect(self.Robot_GetPedal)
        for wdg in self.lstAnimateWidget:
            wdg.signalIdle.connect(self.Robot_GetPedal)
        
        self.treeTrajectory.setIconSize(QSize(32, 32))
        self.treeTrajectory.itemClicked.connect(self.OnItemClicked)
        self.treeTrajectory.itemSelectionChanged.connect(self.OnItemSelectionChanged_treeTrajectory)
        # self.treeTrajectory.itemDoubleClicked.connect(self.OnItemDoubleClicked_treeTrajectory)
        self.treeTrajectory.signalButtonClicked.connect(self.OnClicked_btnTrajectoryList)
        header:QHeaderView = self.treeTrajectory.header()
        header.setIconSize(QSize(32, 32))
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self.OnHeaderClicked_trajectory)
        self.treeTrajectory.setColumnWidth(0, 48)
        self.treeTrajectory.setColumnWidth(2, 32)
        self.treeTrajectory.setItemDelegate(TrajectoryViewDelegate(self.treeTrajectory))
        self.treeTrajectory.setDragDropMode(QAbstractItemView.InternalMove)
        self.treeTrajectory.setAcceptDrops(True)
        # self.treeTrajectory.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        self.btnAddTrajectory.clicked.connect(self.OnClicked_btnAddTrajectory)
        self.setFocus()
    
    def eventFilter(self, obj, event):
        if not hasattr(self, 'hiddenCodes'):
            self.hiddenCodes = []
            self.ans = [
                        Qt.Key_Up, 
                        Qt.Key_Up, 
                        Qt.Key_Down, 
                        Qt.Key_Down, 
                        Qt.Key_Left, 
                        Qt.Key_Right, 
                        Qt.Key_Left, 
                        Qt.Key_Right,
                        Qt.Key_A,
                        Qt.Key_B
                        ]
        if event.type() == QEvent.KeyPress:
            if event.key() != Qt.Key_Return:
                self.hiddenCodes.append(event.key())
            else:
                if self.hiddenCodes == self.ans:
                    dlg = DlgExportLog(self)
                    dlg.exec_()
                self.hiddenCodes = []
                
        elif obj == self.treeDicom:
            # if eventad.type() == QEvent.MouseButtonPress:
            #     self.stepDicom += 1
            # print(f'other event [{event.type()}] is been triggle')
            return False
        
        if obj in [self.btnInhale, self.btnExhale] and event.type() == QEvent.MouseButtonPress:
            if self.stepDicom == 1:
                dlg = DlgHintBox()
                dlg.SetText('select <span style="color:#f00">Inhale dicom</span> series first', self.treeDicom, None)
                if dlg.show():
                    return True
                
            elif self.stepDicom == 3:
                dlg = DlgHintBox()
                dlg.SetText('now select <span style="color:#f00">Exhale dicom</span> series', self.treeDicom, None)
                if dlg.show():
                    # 如果是step 3，按了inhale exhale button會被攔截
                    return True
                
        bFilter = super().eventFilter(obj, event)
        return bFilter
    
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
        
    def closeEvent(self, event):
        self.Laser_Close()
        try:
            for dlg in self.listSubDialog:
                dlg.close()
                
            DlgHintBox.Clear()
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
            
            try:
                os.remove('temp.xml')
            except FileNotFoundError:
                pass
            # self._XmlModifyTag('status', '0')
            ############################################################################################
            logger.info("remove dicomLow VTk success")
            
            
        except Exception as e:
            logger.critical(e)
            logger.error("remove dicomLow VTk error")
        
    def _AddCrossSectionItemInSelector(self):
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
        
    def _AddTrajectoryTreeItems(self, lstItem:list):
        currentIndex = self.treeTrajectory.topLevelItemCount()
        
        if lstItem is None or len(lstItem) == 0:
            return
        
        for i, dicItem in enumerate(lstItem):
            itemName = f'T {currentIndex + i + 1}'
            index = currentIndex + i
            
            item = QTreeWidgetItem()
            owner = dicItem['owner']
            item.setIcon(0, QIcon(IMG_VISIBLE))
            item.setText(1, itemName)
            item.setText(2, '')
            item.setData(0, ROLE_VISIBLE, True)
            item.setData(0, ROLE_TRAJECTORY, index)
            item.setData(2, ROLE_COLOR, DISPLAY.GetTrajectoryColor(index))
            item.setData(0, ROLE_DICOM, owner)
            self.treeTrajectory.AddItemToGroup(item)
            
        self.treeTrajectory.SortItems()
        
        self._CheckTrajectoryVisibleItem()
        self.treeTrajectory.blockSignals(True)
        item = self.treeTrajectory.GetCurrentItem(currentIndex)
        self.treeTrajectory.setCurrentItem(item)
        self.prevSelection_trajectory = item
        self.treeTrajectory.blockSignals(False)
            
        
    def _CalculateExhaleToInhaleMatrix(self):
        dicomInhale = list(self.dicDicom.values())[0]
        dicomExhale = list(self.dicDicom.values())[1]
        regBallInhale = dicomInhale.get('regBall')
        regBallExhale = dicomExhale.get('regBall')
        regMatrixInhale = dicomInhale.get('regMatrix')
        regMatrixExhale = dicomExhale.get('regMatrix')
        
        if any(matrix is None for matrix in (
                                                regBallInhale, 
                                                regBallExhale, 
                                                regMatrixInhale, 
                                                regMatrixExhale
                                            )):
            return None
        
        try:
            # 注意！這裡的regMatrix是改變座標系，而不會改變點在原世界座標系中的位置
            # 如需要進行真實的位置變換，regMatrix需要進行轉置(transpose)
            
            # 計算exhale原點偏移量translate
            mat_translate = np.identity(4)
            mat_translate[:3, 3] = -regBallExhale[0]
            matExhale = mat_translate
            
            # 從exhale 轉換到 inhale的矩陣
            rot_fromExhaleToInhale = np.identity(4)
            invExhale = regMatrixExhale # 等於 np.linalg.inv(regMatrixExhale.T)
            rot_fromExhaleToInhale[:3, :3] = np.matmul(regMatrixInhale.T, invExhale)
            matExhale = np.matmul(rot_fromExhaleToInhale, matExhale)
            
            # 映射到inhale local coordinate(世界座標位置不變，只改變座標軸)
            mat_mapToInhale = np.identity(4)
            mat_mapToInhale[:3, :3] = regMatrixInhale
            matExhaleToInhalePath = np.matmul(mat_mapToInhale, matExhale)
            
            # 儲存矩陣，這個矩陣是應用於trajectory 轉換上的
            REGISTRATION.matrixFromExhaleToInhalePath = matExhaleToInhalePath
            
            # 計算exhale 對應於 inhale空間的位置，世界座標系
            mat_translate[:3, 3] = regBallInhale[0]
            matExhale = np.matmul(mat_translate, matExhale)
            
            dicomInhale['matrix'] = np.linalg.inv(matExhale)
            dicomExhale['matrix'] = matExhale
        except Exception as msg:
            logger.error(msg)
            return None
        
        return dicomInhale['matrix']
                
    def _CheckChildAlterParent(self, item:QStandardItem):
                
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
    
    def _CheckTrajectoryVisibleItem(self):
        totalCount = self.treeTrajectory.topLevelItemCount()
        visibleCount = 0
        for i in range(totalCount):
            item:QTreeWidgetItem = self.treeTrajectory.topLevelItem(i)
            if item.data(0, ROLE_VISIBLE):
                visibleCount += 1
                
        headItem:QTreeWidgetItem = self.treeTrajectory.headerItem()
        
        visibleStatus = 0
        icon = IMG_HIDDEN
        if (totalCount == visibleCount):
            visibleStatus = 2
            icon = IMG_VISIBLE
        elif visibleCount > 0:
            visibleStatus = 1
            icon = IMG_PARTIAL
            
        headItem.setData(0, ROLE_VISIBLE, visibleStatus)
        headItem.setIcon(0, QIcon(icon))
        
    def _DetectUnexpectedShutdown(self):
        statusValue = self._GetBootFileInfo('status')
        if isinstance(statusValue, str) and int(statusValue) != 0:
            ret = MessageBox.ShowWarning('Detected unexpected shutdown, resume it?', 'YES', "NO")
            if ret == 0:
                return self._ResumeFromShutdown()
                
        return True
    
    def _EnableDevice(self, nDevice:int = 0):
        if nDevice == (DEVICE_ALL):
            logger.debug('ready to initial robot')
            self.robot = Robot.MOTORSUBFUNCTION()
            self.robot.signalProgress.connect(self.Robot_OnLoading)
            self.robot.signalInitFailed.connect(self.RobotSystem_OnFailed)
            
            logger.debug('ready to start robot thread')
            # tRobot = threading.Thread(target = self.robot.Initialize)
            # tRobot.start()
            
            self.RobotSupportArm = Robot.RobotSupportArm()
            self.RobotSupportArm.signalPedalPress.connect(self.Robot_OnSignalFootPedal)
            self.RobotSupportArm.signalTargetArrived.connect(self.Robot_OnSignalTargetArrived)
            self.RobotSupportArm.signalAxisDiff.connect(self.Robot_OnSignalAxisValue)
            self.RobotSupportArm.signalProgress.connect(self.Robot_OnLoading)
            # self.OperationLight = Robot.OperationLight()
            
            tRobot = threading.Thread(target = self.RobotSystem_Initialize)
            tRobot.start()
            
            logger.debug('ready to initial laser')
            self.Laser = Robot.LineLaser()
            self.Laser.signalProgress.connect(self.Laser_OnLoading)
            self.Laser.signalModelPassed.connect(self.Laser_OnSignalModelPassed)
            self.Laser.signalBreathingRatio.connect(self.Laser_OnSignalBreathingRatio)
            self.Laser.signalInhaleProgress.connect(self.Laser_OnSignalInhale)
            self.Laser.signalExhaleProgress.connect(self.Laser_OnSignalExhale)
            self.Laser.signalCycleCounter.connect(self.Laser_OnSignalShowCounter)
            self.Laser.signalInitFailed.connect(self.RobotSystem_OnFailed)
            self.Laser.signalShowHint.connect(self.Laser_OnSignalShowHint)
            self.signalResetLaserUI.connect(self.Laser_SetBreathingCycleUI)
            self.signalModelCycle.connect(self.Laser_OnSignalUpdateCycle)
            tLaser= threading.Thread(target = self.Laser.Initialize)
            tLaser.start()
        elif nDevice == DEVICE_ROBOT:
            self.loadingLaser = 100
            self.robot = Robot.MOTORSUBFUNCTION()
            self.robot.signalProgress.connect(self.Robot_OnLoading)
            self.robot.signalInitFailed.connect(self.RobotSystem_OnFailed)
            
            tRobot = threading.Thread(target = self.robot.Initialize)
            tRobot.start()
            
            self.RobotSupportArm = Robot.RobotSupportArm()
            self.RobotSupportArm.signalPedalPress.connect(self.Robot_OnSignalFootPedal)
            self.RobotSupportArm.signalTargetArrived.connect(self.Robot_OnSignalTargetArrived)
            self.RobotSupportArm.signalAxisDiff.connect(self.Robot_OnSignalAxisValue)
            self.OperationLight = Robot.OperationLight()
        elif nDevice == DEVICE_LASER:
            self.stkScene.setCurrentWidget(self.pgLaser)
            
            self.loadingRobot = 100
            self.Laser = Robot.LineLaser()
            self.Laser.signalProgress.connect(self.Laser_OnLoading)
            self.Laser.signalModelPassed.connect(self.Laser_OnSignalModelPassed)
            self.Laser.signalBreathingRatio.connect(self.Laser_OnSignalBreathingRatio)
            self.Laser.signalInhaleProgress.connect(self.Laser_OnSignalInhale)
            self.Laser.signalExhaleProgress.connect(self.Laser_OnSignalExhale)
            self.Laser.signalCycleCounter.connect(self.Laser_OnSignalShowCounter)
            self.Laser.signalInitFailed.connect(self.RobotSystem_OnFailed)
            self.Laser.signalShowHint.connect(self.Laser_OnSignalShowHint)
            self.signalModelCycle.connect(self.Laser_OnSignalUpdateCycle)
            self.signalResetLaserUI.connect(self.Laser_SetBreathingCycleUI)
            tLaser= threading.Thread(target = self.Laser.Initialize)
            tLaser.start()
        else:
            self.stkMain.setCurrentWidget(self.pgScene)
            self.stkScene.setCurrentWidget(self.pgImportDicom)
            # self.stkScene.setCurrentWidget(self.pgPositionRobot)
        
            self._DetectUnexpectedShutdown()
    
    def _GetSeriesFromModelIndex(self, index:QModelIndex):
        model = self.treeDicom.model()
        index = index.sibling(index.row(), 0)
        item:QStandardItem = model.itemFromIndex(index)
        if item:
            idPatient = item.data(Qt.UserRole + 1)
            idStudy   = item.data(Qt.UserRole + 2)
            idSeries  = item.data(Qt.UserRole + 3)
            selectedSeries = [idPatient, idStudy, idSeries, index.row()]
            # self.selectedSeries.append(selectedSeries)
            # if len(self.selectedSeries) > 2:
            #     self.selectedSeries.pop(0)
            # self.reader.SelectDataFromID(idPatient, idStudy, idSeries, i)
            return selectedSeries
        else:
            return None
        
    def _GetInfoFromModelIndex(self, index:QModelIndex):
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
    
    def _GetCurrentTrajectory(self):
        try:
            items = self.treeTrajectory.GetCurrentTrajectory()
            return items
        except Exception as msg:
            logger.critical(msg)
            
        return None
    
    def _ModifyTrajectory(
        self, 
        index:int, 
        dicom:DISPLAY
    ):
        dicom.CreateLine(index)
        # trajectory = dicom.trajectory[index]
        trajectory = DISPLAY.trajectory[index]
        
        if trajectory is not None:
            entry, target = trajectory
            
            length = np.linalg.norm(np.array(entry) - np.array(target))
            self.sldTrajectory.setMinimum(0)
            self.sldTrajectory.setSingleStep(1)
            self.sldTrajectory.setPageStep(1)
            self.sldTrajectory.setMaximum(int(length))
            self.sldTrajectory.setValue(0)
            
            self.currentTag['trajectoryLength'] = int(length)
            self.currentTag['trajectory'] = trajectory
            # if dicom == self.dicomLow:
            
            for view in self.viewport_L.values():
                if view.orientation == VIEW_CROSS_SECTION:
                    view.uiScrollSlice.setMaximum(int(length))
                    view.uiScrollSlice.setValue(0)
            
            # else:
            #     for view in self.viewport_H.values():
            #         length = np.linalg.norm(np.array(entry) - np.array(target))
            #         if view.orientation == VIEW_CROSS_SECTION:
            #             view.uiScrollSlice.setMaximum(length)
        
    def _PlayVedio(self, widget:QWidget, filePath:str):
        
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
            if layout.itemAt(0):
                videoWidget = layout.itemAt(0).widget()
                self.player.setVideoOutput(videoWidget)
        
        self.player.play()
        self.player.mediaStatusChanged.connect(self.OnStatusChanged)
        
    def _Registration(self, image, spacing):
        """automatic find registration ball center + open another ui window to let user selects ball in order (origin -> x axis -> y axis)
        """
        # self.ui_SP = SystemProcessing()
        # self.ui_SP.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        # self.ui_SP.show()
        # QApplication.processEvents()
        if self.dlgSystemProcessing is None:
            self.dlgSystemProcessing = SystemProcessing(2)
            self.dlgSystemProcessing.signalClose.connect(self.OnSignal_ProcessClose)
            
        self.dlgSystemProcessing.setWindowTitle('Registration')
        self.dlgSystemProcessing.label_Processing.setText('Registing Robot Position...')
        self.dlgSystemProcessing.show()
        QApplication.processEvents()
        self.regFn.signalProgress.connect(self.dlgSystemProcessing.UpdateProgress)
        
        
        if self.currentTag.get("regBall") is not None or self.currentTag.get("candidateBall") is not None:
            
            reply = MessageBox.ShowInformation("already registration, reset now?", 'Yes', 'No')
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
                logger.info("reset selected ball (Low)")
                
                
            # else:
            #     self.ui_SP.close()
            #     return
            ############################################################################################
        "automatic find registration ball center"
        try:
            ## 自動找球心 + 辨識定位球位置 ############################################################################################
            # self.regFn.GetBallAuto2(image, spacing)
            # flag, answer = self.regFn.GetBallAuto(image, spacing, series)
            flag, answer = self.regFn.GetBallAuto2(image, spacing)
            
            ############################################################################################
        except Exception as e:
            # self.ui_SP.close()
            # self.logUI.warning('get candidate ball error / SetRegistration_L() error')
            # QMessageBox.critical(self, "error", "get candidate ball error / SetRegistration_L() error")
            MessageBox.ShowCritical("get candidate ball error", "OK")
            logger.error('get candidate ball error / SetRegistration_L() error')
            logger.critical(e)
            self.dlgSystemProcessing.close()
            return False
        
        if flag == True:
            # self.logUI.info('get candidate ball of inhale/Low DICOM in VTK:')
            i = 0
            for key, value in answer.items():
                tmp = str(i) + ": " + str(key) + str(value)
                # self.logUI.info(tmp)
                i += 1
            self.currentTag.update({"candidateBallVTK": answer})
            self.ShowRegistrationDifference()
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
            logger.error('get candidate ball error / SetRegistration_L() error')
            self.dlgSystemProcessing.close()
            ## 顯示手動註冊定位球視窗 ############################################################################################
            "Set up the coordinate system manually"
            # self.ui_CS = CoordinateSystemManual(self.currentTag, self.currentTag.get('display'), answer)
            # self.ui_CS.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            # self.ui_CS.show()
            ############################################################################################
            # self.Button_ShowRegistration_L.setEnabled(True)
            return False
        
        return True
    
    def _ResumeStored(self):
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
                logger.debug(f'Error: [{strKey}] = {index}')
                
    def _ResumeFromShutdown(self):
        # 執行homing process
        
        # resume lost data
        if len(self.tempResumeData) == 0:
            logger.error(f'no available resume data')
            return False
            
        try:
            dicom = list(self.dicDicom.values())
            pathData = self.tempResumeData['path']
            dicom[0]['path'] = pathData[0]['text']
            dicom[1]['path'] = pathData[1]['text']
                    
            dataTrajectory = self.tempResumeData.get('trajectory')
            
            if dataTrajectory:
                for data in dataTrajectory:
                    strTrajectory:str = data['text']
                    owner = data['owner']
                    
                    trajectory = np.array([float(x) for x in strTrajectory.split(',')])
                    DISPLAY.trajectory.addEntry(trajectory[:3], owner)
                    DISPLAY.trajectory.addTarget(trajectory[3:], owner)
                
            pathInhale = dicom[0].get('path')
            pathExhale = dicom[1].get('path')
            
            if None in (pathInhale, pathExhale):
                logger.critical('resume dicom data is empty')
                return
        
            QApplication.processEvents()
            
            self.reader = DICOM()
            self.reader.LoadPath(pathInhale)
            if not self.ImportDicom_L(0, 0, 0):
                return
            
            self.reader.LoadPath(pathExhale)
            if not self.ImportDicom_H(0, 0, 0):
                return
            
            lstItem = []
            for i in range(DISPLAY.CountOfTrajectory()):
                owner = DISPLAY.trajectory.getOwner(i)
                
                idx = int(owner == 'E') # I = 0, E = 1
                # add to renderer
                self._ModifyTrajectory(i, dicom[idx]['display'])
                lstItem.append({'owner':owner})
                    
            self._AddTrajectoryTreeItems(lstItem)
            
            # self._SaveBootFile()
            
            self.ChangeCurrentDicom(self.btnDicomLow.objectName())
            self.ShowFusion()
            self.stkScene.setCurrentWidget(self.pgImageView)
        except Exception as msg:
            logger.critical(msg)
            return False
        
        return True
            
    def _Robot_driveTo(self):
        if self.language == LAN_CN:
            translator = QTranslator()
            translator.load('FunctionLib_UI/Ui_dlgInstallAdaptor_tw.qm')
            QCoreApplication.installTranslator(translator)
                
        self.stkScene.setCurrentWidget(self.pgImageView)
        
        self.Laser_OnTracking()
        
        dlgDriveTo = DlgInstallAdaptor()
        dlgDriveTo.signalRobotStartMoving.connect(self.Laser_StopTracking)
        dlgDriveTo.setWindowFlags(Qt.FramelessWindowHint)
        dlgDriveTo.setModal(True)
        self.dlgRobotDrive = dlgDriveTo
        
        dlgDriveTo.exec_()
        self.listSubDialog.append(dlgDriveTo)
        
        self.stkScene.setCurrentWidget(self.pgImageView)
        
    def _SaveAnotherImages(self, pathDir:str, pathOut:str):
        # 消除PNG影像警告用轉檔程式 需要skimage和cv2
        path = os.path.join(os.getcwd(), pathDir)
        out = os.path.join(os.getcwd(), pathOut)
        
        for dirPath, dirNames, fileNames in os.walk(path):
            for f in fileNames:
                pathImageIn = os.path.join(path, f)
                pathImageOut = os.path.join(out, f)
                image = io.imread(pathImageIn)
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGRA)
                cv2.imencode('.png', image)[1].tofile(pathImageOut)
                
    def _GetBootFileInfo(self, tagName:str):
        try:
            if os.path.exists('temp.xml'):
                dom = xdom.parse('temp.xml')
                root = dom.documentElement
                
                data = self._XmlGetNode(root, 'dicom')
                if len(data) > 0:
                    self.tempResumeData['path'] = data
                    
                    
                dataTrajectory = self._XmlGetNode(root, 'trajectory')
                if len(dataTrajectory) > 0:
                    self.tempResumeData['trajectory'] = dataTrajectory
                
                return dom.getElementsByTagName(tagName)[0].childNodes[0].nodeValue
        except Exception as msg:
            logger.critical(msg)
            
        return None
        
    def _XmlGetNode(self, dom:xdom.Element, tagName:str = None, data:list = None):
        nodeList = []
        dataList = []
        if data is not None:
            dataList = data
            
        if tagName is not None:
            nodeList = dom.getElementsByTagName(tagName)
        elif dom.nodeType == xdom.Node.ELEMENT_NODE:
            nodeList = dom.childNodes
        
        dicData = {}
        if dom.hasAttribute('owner'):
            dicData['owner'] = dom.getAttribute('owner')
            dataList.append(dicData)
            
        for node in nodeList:
            
            if node.nodeType == xdom.Node.TEXT_NODE:
                if isinstance(node.nodeValue, str):
                    nodeValue = node.nodeValue.strip()
                    if nodeValue:
                        dicData['text'] = nodeValue
                        if dicData not in dataList:
                            dataList.append(dicData)
                        return dataList 
            else:
                self._XmlGetNode(node, data = dataList)
            
        return dataList
                
    def _XmlModifyTag(self, tagName:str, value:str):
        """ 
        因為當dom.writexml再次輸出後，為了保持原有的縮排格和換行，newl和addindent都設為空白
        會使得root node緊接在document type node之後，太醜了…
        所以才另外這樣改寫
        """
         
        if os.path.exists('temp.xml'):
            dom = xdom.parse('temp.xml')
            dom.getElementsByTagName(tagName)[0].childNodes[0].nodeValue = value
            
            # 將原本的root完整內容轉成文字，且保留原本縮排和換行不進行改變
            root:xdom.Element = dom.documentElement
            # 原本的root node text，最前方加上換行以保持美觀
            root_text = '\n' + root.toprettyxml(indent = '', newl = '')
            
            # 開新的root，覆蓋掉原本的
            dom = xdom.Document()
            
            try:
                with open('temp.xml', 'w') as f:
                    # 這裡的dom.xwritexml只有輸出document type node
                    # 原本的root當成一般文字輸出
                    dom.writexml(f, encoding = 'UTF-8')
                    f.write(root_text)
            except Exception as msg:
                logger.critical(msg)
                
    def _XmlAppendTextNode(self, node:xdom.Element, value:str):
        nLayer = 1
        parent = node.parentNode
        while parent and parent.nodeType == node.ELEMENT_NODE:
            nLayer += 1
            parent = parent.parentNode
            
            
        indent = '\n' + '\t' * nLayer
        indentEnd = '\n' + '\t' * (nLayer - 1)
        value = indent + indent.join(value.split('\n')) + indentEnd
        
        textNode = xdom.Document().createTextNode(value)
        node.appendChild(textNode)
        
                
    def _SaveBootFile(self):
            
        dom = xdom.Document()
        root = dom.createElement('root')
        dom.appendChild(root)
        
        # close status, if close innormally it will keep 1 value, else 0
        sceneIndex = self.stkScene.currentIndex()
        statusTextNode = dom.createTextNode(str(sceneIndex))
        
        statusNode = dom.createElement('status')
        statusNode.appendChild(statusTextNode)
        
        root.appendChild(statusNode)
        
        # save dicom path
        # pathInhale = self.reader.GetSelectedDicomPath(0).replace('\\', '/')
        # pathExhale = self.reader.GetSelectedDicomPath(1).replace('\\', '/')
        dicom = list(self.dicDicom.values())
        pathInhale = dicom[0].get('path')
        pathExhale = dicom[1].get('path')
        logger.info(f'inhale dicom = {pathInhale}')
        logger.info(f'exhale dicom = {pathExhale}')
        
        # save to xml node
        inhaleNode = dom.createElement('inhale')
        exhaleNode = dom.createElement('exhale')
        
        if None not in (pathInhale, pathExhale):
            inhalePathNode = dom.createTextNode(pathInhale)
            exhalePathNode = dom.createTextNode(pathExhale)
            
            inhaleNode.appendChild(inhalePathNode)
            exhaleNode.appendChild(exhalePathNode)
        
        dicomNode = dom.createElement('dicom')
        dicomNode.appendChild(inhaleNode)
        dicomNode.appendChild(exhaleNode)
        
        root.appendChild(dicomNode)
        
        # registration result
        dicomInhale = list(self.dicDicom.values())[0]
        matrix = dicomInhale.get('matrix')
        if matrix is not None:
            logger.info(f'registration matrix = {matrix}')
            
            # save to xml node
            # indent = '\n' + '\t' * 2
            # strMatrix = indent.join([','.join(map(str, row)) for row in matrix])
            # strMatrix = indent + strMatrix + '\n\t'
            # matrixTextNode = dom.createTextNode(strMatrix)
            
            # matrixNode = dom.createElement('matrix')
            # matrixNode.appendChild(matrixTextNode)
            
            strMatrix = '\n'.join([','.join([f'{num:13.8f}' for num in row]) for row in matrix])
            matrixNode = dom.createElement('matrix')
            root.appendChild(matrixNode)
            # 要取得正確的縮排層數，必須先將node加入到node tree
            self._XmlAppendTextNode(matrixNode, strMatrix)
            
            
        # save trajectory (if exist)
        strTrajectoryList = []
        for i in range(DISPLAY.trajectory.count()):
            entry = DISPLAY.trajectory[i][0]
            target = DISPLAY.trajectory[i][1]
            
            logger.info(f'trajectory {i} entry : {entry}, target : {target}')
            
            text = ','.join([f'{num:.6f}' for num in np.append(entry, target)])
            strTrajectoryList.append(text)
            
        # save to xml node
        if len(strTrajectoryList) > 0:
            trajectoryNode = dom.createElement('trajectory')
            
            for i, text in enumerate(strTrajectoryList, 1):
                textNode = dom.createTextNode(text)
                
                numOfTrajectoryNode = dom.createElement(f'T{i}')
                numOfTrajectoryNode.appendChild(textNode)
                
                owner = DISPLAY.trajectory.getOwner(i - 1)
                if owner:
                    numOfTrajectoryNode.setAttribute('owner', owner)
                
                trajectoryNode.appendChild(numOfTrajectoryNode)
                
            root.appendChild(trajectoryNode)
            
        try:  
            with open('temp.xml', 'w', encoding = 'UTF-8') as f:
                dom.writexml(f, indent = '', addindent = '\t', newl = '\n', encoding = 'UTF-8')
        except Exception as msg:
            logger.error(msg)
                
    def _SetTrajectoryVisible(self, index:int, bVisible:bool):
        # display = self.currentTag.get('display')
        # if display is not None and isinstance(display, DISPLAY):
        #     display.SetTrajectoryVisibility(index, bVisible)
        DISPLAY.trajectory.setVisibility(index, bVisible)
        self.UpdateView()
            
    def _ShowTrajectoryList(self, lstTrajectory:list):
        # 用clear會導致item實體被刪除，如還想保留實體的話不能使用
        for i in range(self.treeTrajectory.topLevelItemCount()):
            self.treeTrajectory.takeTopLevelItem(0)
        
        self.treeTrajectory.insertTopLevelItems(0, lstTrajectory)
        
    def _TreeDicomViewFilter(self, item:QStandardItem):
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
            
    def _TreeItemCheckAll(self, item:QStandardItem, checkState:Qt.CheckState):
        # if checkState == Qt.Unchecked:
        for row in range(item.rowCount()):
            item.child(row, 0).setCheckState(checkState)
            
    def SetTreeDicomUserRole(self, data, nRow:int = None, modelIndex = None):
        
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
                        logger.error('error occurred in set UserRole data')
        
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
            
    def ImportDicom(self, path):
        self.dlgSystemProcessing = SystemProcessing()
        self.dlgSystemProcessing.signalClose.connect(self.OnSignal_ProcessClose)
        self.dlgSystemProcessing.show()
        QApplication.processEvents()
        
        self.reader = DICOM()
        self.reader.signalProcess.connect(self.dlgSystemProcessing.UpdateProgress)
        dicom = self.reader.LoadPath(path)
        
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
        modelFilter.itemChanged.connect(self.OnItemChanged)
        
        for keyPatien, dicPatient in dicom.items():
            for keyStudy, dicStudy in dicPatient.items():
                for keySeries, dicSeries in dicStudy.items():
                    slices = dicSeries.get('data')
                    if slices is None:
                        continue
                    
                    slice = dicSeries['data'][0]
                    
                    # dim = np.array(slice.pixel_array).shape
                    dim = dicSeries.get('dimension')
                    if dim is None:
                        logger.critical('dicom data missing dimension information')
                        continue
                    
                    numOfSlices = len(dicSeries['data'])
                    if len(dim) < 3 or (numOfSlices != dim[0] and numOfSlices > 1):
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
            
        model.sort(6, Qt.DescendingOrder)
        
        model.setHeaderData(0, Qt.Horizontal, QColor(0, 0, 255, 100), role = Qt.BackgroundRole)
        self.treeDicom.setModel(model)
        
        modelFilter.sort(1, Qt.AscendingOrder)
        modelFilter.itemChanged.connect(self.OnItemChanged)
        self.treeDicomFilter.setModel(modelFilter)
        self.treeDicomFilter.expandAll()
        self.treeDicom.selectionModel().selectionChanged.connect(self.OnSelectionChanged_treeDicom)
        self.dicSelectedSeries = {0:{'selected':[]}, 
                                  1:{'selected':[]}
                                  }
                  
    def ImportDicom_L(self, idxPatient:int = None, idxStudy:int = None, idxSeries:int = None):
        """load inhale (Low breath) DICOM to get image array and metadata
        """
        ############################################################################################
        ## 用 VTK 顯示 + 儲存 VT形式的影像 ############################################################################################
        "VTK stage"
        retData = tuple()
        pathInhale = ''
        if None not in (idxPatient, idxStudy, idxSeries):
            retData = self.reader.GetDataFromIndex(idxPatient, idxStudy, idxSeries)
            pathInhale = list(self.dicDicom.values())[0]['path']
        else:
            retData = self.reader.GetData(index = 0)
            pathInhale = self.reader.GetSelectedDicomPath(0).replace('\\', '/')
            
        if retData is None:
            logger.error(f'load inhale dicom failed')
            return False
            
        self.vtkImageLow, spacing, dimension, series = retData
        self.imageL = self.reader.arrImage
        
        if self.vtkImageLow is None:
            # QMessageBox.critical(None, 'ERROR', 'image error')
            MessageBox.ShowCritical('ERROR', 'image error')
            logger.critical('import dicom error')
            return False
        
        # if self.currentTag == self.dicDicom.get(self.btnDicomLow.objectName()):
        
        self.dicomLow.LoadImage(self.vtkImageLow)
        grayscaleRange = self.vtkImageLow.GetScalarRange()
        dicomTag = self.SetDicomData(self.dicomLow, pathInhale, 'LOW', grayscaleRange, dimension, spacing)
        
        if not dicomTag:
            # QMessageBox.critical(None, 'DICOM TAG ERROR', 'missing current tag [LOW]')
            MessageBox.ShowCritical( 'DICOM TAG ERROR', 'missing current tag [LOW]')
            return False
        
        # self.currentTag['dimension'] = dimension
        # self.currentTag['spacing'] = spacing
        # self.currentTag['series'] = series
            
        if not SKIP_REGISTRATION:
            if not self.SetRegistration_L():
                # QMessageBox.critical(None, 'ERROR', 'Registration Failed')
                MessageBox.ShowCritical('ERROR', 'Registration Failed')
                return False
            
        
        self.ShowDicom()
        # self.bDicomChanged = False
        
        return True
    
    def ImportDicom_H(self, idxPatient:int = None, idxStudy:int = None, idxSeries:int = None):
        "VTK stage"
        retData = tuple()
        pathExhale = ''
        if None not in (idxPatient, idxStudy, idxSeries):
            retData = self.reader.GetDataFromIndex(idxPatient, idxStudy, idxSeries)
            pathExhale = list(self.dicDicom.values())[1]['path']
        else:
            retData = self.reader.GetData(index = 1)
            pathExhale = self.reader.GetSelectedDicomPath(1).replace('\\', '/')
            
        if retData is None:
            logger.error(f'load exhale dicom failed')
            return False
        
        self.vtkImageHigh, spacing, dimension, series = retData
        self.imageH = self.reader.arrImage
        
        if self.vtkImageHigh is None:
            # QMessageBox.critical(None, 'ERROR', 'image error')
            MessageBox.ShowCritical('ERROR', 'image error')
            return False
        
        # self.dicomHigh.LoadImage(self.vtkImageHigh)
        
        grayscaleRange = self.vtkImageHigh.GetScalarRange()
        dicomTag = self.SetDicomData(self.dicomHigh, pathExhale, 'HIGH', grayscaleRange, dimension, spacing)
        
        if not dicomTag:
            # QMessageBox.critical(None, 'DICOM TAG ERROR', 'missing current tag [HIGH]')
            MessageBox.ShowCritical('DICOM TAG ERROR', 'missing current tag [HIGH]')
            logger.error('DICOM TAG ERROR', 'missing current tag [HIGH]')
            return False
        
        
        # thresholdValue = int(((grayscaleRange[1] - grayscaleRange[0]) / 6) + grayscaleRange[0])
        # self.currentTag['ww'] = abs(thresholdValue * 2)
        # self.currentTag['wl'] = thresholdValue
        # self.currentTag['dimension'] = dimension
        # self.currentTag['spacing'] = spacing
        # self.currentTag['series'] = series
        
        if not SKIP_REGISTRATION:
            if not self.SetRegistration_H():
                # QMessageBox.critical(None, 'ERROR', 'Registration Failed')
                MessageBox.ShowCritical('ERROR', 'Registration Failed')
                return False
        
        matrix = self._CalculateExhaleToInhaleMatrix()
        if matrix is not None:
            # transform image
            self.dicomHigh._TransformImage(self.vtkImageHigh, matrix)
        else:
            self.dicomHigh.LoadImage(self.vtkImageHigh)
            
        self.ShowDicom()
        # self.bDicomChanged = False
        return True
    
    
        
    def SetDicomData(
        self, 
        dicom:DISPLAY,
        path:str, 
        type:str, 
        grayscaleRange:_ArrayLike, 
        dimension:_ArrayLike,
        spacing:_ArrayLike
        ):
        
        if type.upper() == 'LOW':
            tag = self.dicDicom.get(self.btnDicomLow.objectName())
        elif type.upper() == 'HIGH':
            tag = self.dicDicom.get(self.btnDicomHigh.objectName())
            
        if tag is not None:
            tag['display'] = dicom
            tag['path'] = path
            thresholdValue = int(((grayscaleRange[1] - grayscaleRange[0]) / 6) + grayscaleRange[0])
            tag['ww'] = abs(thresholdValue * 2)
            tag['wl'] = thresholdValue
            tag['dimension'] = dimension
            tag['spacing'] = spacing
            # tag['series'] = series
            self.currentTag = tag
            return tag
        
                
    def SetUIEnable_Trajectory(self, bEnable):
        if bEnable:
            self.btnSetEntry.setEnabled(bEnable)
            self.btnSetTarget.setEnabled(bEnable)
        self.btnToEntry.setEnabled(bEnable)
        self.btnToTarget.setEnabled(bEnable)
        self.btnCloseToEntry.setEnabled(bEnable)
        self.btnCloseToTarget.setEnabled(bEnable)
        self.ledOffset.setEnabled(bEnable)
        self.sldTrajectory.setEnabled(bEnable)
        
    def ShowFusion(self):
        # setUI to Fusion page
        self.stkViewer.setCurrentWidget(self.pgCheckFusion)
        self.tabWidget.setHidden(True)
        
        self.ResetView()
        
        lstOrientation = [VIEW_AXIAL, VIEW_SAGITTAL, VIEW_CORONAL]
        self.viewport_L = {}
        self.viewport_L["Fusion1"] = ViewPortUnit(self, self.dicomLow, self.wdgFusionView1, lstOrientation[0], self.sbrFusion1)
        self.viewport_L["Fusion2"] = ViewPortUnit(self, self.dicomLow, self.wdgFusionView2, lstOrientation[1], self.sbrFusion2)
        self.viewport_L["Fusion3"] = ViewPortUnit(self, self.dicomLow, self.wdgFusionView3, lstOrientation[2], self.sbrFusion3)
        MainInterface.viewport = self.viewport_L
        
        # self.syncInteractorStyle = SynchronInteractorStyle(self.viewport_L)
        self.currentRenderer = self.viewport_L['Fusion1'].renderer
        
        self.dicomLow.rendererAxial.SetTargetVisible(False)
        self.dicomLow.rendererSagittal.SetTargetVisible(False)
        self.dicomLow.rendererCoronal.SetTargetVisible(False)
        
        for view in self.viewport_L.values():
            iStyle = view.iren.GetInteractorStyle()
            if isinstance(iStyle, MyInteractorStyle):
                iStyle.signalObject.ConnectUpdateView(self.UpdateView)
            
            view.signalUpdateSlice.connect(self.ChangeSlice_L)
            view.signalUpdateAll.connect(self.UpdateTarget)
            view.signalUpdateExcept.connect(self.UpdateTarget)
            view.signalFocus.connect(self.Focus)
            view.signalChangedTrajPosition.connect(self.ChangeTrajectorySlider)
        
        self.lstInteractorWipe = []
        
        for orientation in lstOrientation:
            interactorWipe = InteractorStyleWipe(orientation)
            interactorWipe.signalUpdate.ConnectUpdateView(self.UpdateTarget)
            self.lstInteractorWipe.append(interactorWipe)
        
        balls = list(self.dicDicom.values())[0].get('candidateBallVTK')
        if balls:
            reference = np.array(*list(balls.values()))
            self.currentRenderer.SetTarget(reference[0][:3])
            
        # add toolbox widget to Views
        views = [self.wdgFusionView1, self.wdgFusionView2, self.wdgFusionView3]
        for i in range(3):
            layoutView = QGridLayout(views[i])
            layoutView.addItem(QSpacerItem(0, 0, vPolicy = QSizePolicy.Expanding), 0, 1)
            layoutView.addItem(QSpacerItem(0, 0, hPolicy = QSizePolicy.Expanding), 1, 0)
            layoutView.addWidget(self.floatingBox[i], 1, 1)
            self.floatingBox[i].setVisible(False)
            
            self.floatingBox[i].signalSliceUp.connect(self.lstInteractorWipe[i].SliceUp)
            self.floatingBox[i].signalSliceDown.connect(self.lstInteractorWipe[i].SliceDown)
            views[i].GetRenderWindow().GetInteractor().AddObserver('MouseMoveEvent', self.OnMouseMove_views)
            
        for wipe in self.lstInteractorWipe:
            wipe.SetInput(self.dicomLow, self.dicomHigh)
        
        
        self.UpdateTarget()
        self.UpdateView()
            
    def ShowDicom(self):
        """show low dicom to ui
        """
        self.stkViewer.setCurrentWidget(self.pg4View)
        self.tabWidget.setHidden(False)
        
        #Initialize window level / window width
        #Dicom Low
        self.sldWindowWidth.blockSignals(True)
        self.sldWindowWidth.setMinimum(0)
        # self.sldWindowWidth.setMaximum(int(abs(self.dicomLow.dicomGrayscaleRange[0]) + self.dicomLow.dicomGrayscaleRange[1]))
        display = self.currentTag.get('display')
        if display is None:
            return
        
        self.sldWindowWidth.setMaximum(int(abs(display.dicomGrayscaleRange[0]) + display.dicomGrayscaleRange[1]))
        # self.currentTag['ww'] = abs(thresholdValue * 2)
        self.sldWindowWidth.setValue(self.currentTag.get('ww'))
        self.sldWindowWidth.blockSignals(False)
        
        "WindowCenter / WindowLevel"
        self.sldWindowLevel.blockSignals(True)
        # self.sldWindowLevel.setMinimum(int(self.dicomLow.dicomGrayscaleRange[0]))
        # self.sldWindowLevel.setMaximum(int(self.dicomLow.dicomGrayscaleRange[1]))
        self.sldWindowLevel.setMinimum(int(display.dicomGrayscaleRange[0]))
        self.sldWindowLevel.setMaximum(int(display.dicomGrayscaleRange[1]))
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
            
        self.viewport_L["LT"] = ViewPortUnit(self, display, self.wdgLeftTop, orientationLT, self.sbrLeftTop, self.cbxLeftTop)
        self.viewport_L["RT"] = ViewPortUnit(self, display, self.wdgRightTop, orientationRT, self.sbrRightTop, self.cbxRightTop)
        self.viewport_L["LB"] = ViewPortUnit(self, display, self.wdgLeftBottom, orientationLB, self.sbrLeftBottom, self.cbxLeftBottom)
        self.viewport_L["RB"] = ViewPortUnit(self, display, self.wdgRightBottom, orientationRB, self.sbrRightBottom, self.cbxRightBottom)
        MainInterface.viewport = self.viewport_L
        self.syncInteractorStyle = SynchronInteractorStyle(self.viewport_L)
        self.currentRenderer = self.viewport_L['LT'].renderer
        self.currentRenderer.SetSelectedOn()
        # 綁定GetRenderer signal
        # for widget in self.vtkWidgets_L:
        #     iStyle = widget.GetRenderWindow().GetInteractor().GetInteractorStyle()
            
        
        for view in self.viewport_L.values():
            iStyle = view.iren.GetInteractorStyle()
            if isinstance(iStyle, MyInteractorStyle):
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
        
        # self._ResumeStored()
        # # self.UpdateTarget()
        # self.UpdateView()
        
    def SwitchDicom(self, blendRatio:float):
        """show low dicom to ui
        """
        #Initialize window level / window width
        #Dicom Low
        self.sldWindowWidth.blockSignals(True)
        self.sldWindowWidth.setMinimum(0)
        # self.sldWindowWidth.setMaximum(int(abs(self.dicomLow.dicomGrayscaleRange[0]) + self.dicomLow.dicomGrayscaleRange[1]))
        display = self.currentTag.get('display')
        if display is None:
            return
        
        self.sldWindowWidth.setMaximum(int(abs(display.dicomGrayscaleRange[0]) + display.dicomGrayscaleRange[1]))
        self.sldWindowWidth.setValue(self.currentTag.get('ww'))
        self.sldWindowWidth.blockSignals(False)
        
        "WindowCenter / WindowLevel"
        self.sldWindowLevel.blockSignals(True)
        self.sldWindowLevel.setMinimum(int(display.dicomGrayscaleRange[0]))
        self.sldWindowLevel.setMaximum(int(display.dicomGrayscaleRange[1]))
        self.sldWindowLevel.setValue(self.currentTag.get('wl'))
        self.sldWindowLevel.blockSignals(False)
        
        DISPLAY.SetBlendImages(blendRatio)
        
        # self._ResumeStored()
        # self.UpdateTarget()
        self.UpdateView()
        
    def UpdateView(self):
        viewport = self.GetViewPort()
        for view in viewport.values():
            view.iren.Render()
        
        if self.currentTag is not None:
            wl = self.currentTag.get('wl')
            if wl is not None:
                self.sldWindowLevel.setValue(wl)
                
            ww = self.currentTag.get('ww')
            if ww is not None:
                self.sldWindowWidth.setValue(ww)
                
    def UpdateTarget(
        self, 
        orientation:str = None, 
        pos = None, 
        bFocus = True
    ):
        viewPort = self.GetViewPort()
        
        if viewPort is None:
            logger.debug(f'viewPort is not exist')
            return
        
        for view in viewPort.values():
            if (orientation is None) or (orientation != view.orientation):
                
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
        
    def OnClicked_btnAddTrajectory(self):
        display = self.currentTag.get('display')
        countOfTrajectory = DISPLAY.CountOfTrajectory()
        
        itemCount = self.treeTrajectory.topLevelItemCount()
        
        # 檢查treeWidget的item項目數量，和路徑是否一致，一致的時候才允許增加路徑
        if countOfTrajectory == itemCount:
            owner = 'E'
            if self.currentTag['name'] == self.btnDicomLow.objectName():
                owner = 'I'
                
            item = [{'owner':owner}]
            self._AddTrajectoryTreeItems(item)
            
            self.SetUIEnable_Trajectory(False)
        
        self.btnSetEntry.setEnabled(True)
        self.btnSetTarget.setEnabled(True)
        
    def OnClicked_btnPlanning(self):
        logger.debug('planning')
        
    def OnClicked_btnGuidance(self):
        # self.stkMain.setCurrentWidget(self.page_loading)
        pass
        
    def OnClicked_btnDriveTo(self):
        if (self.RobotSupportArm and self.RobotSupportArm.IsMove() == True) or self.bSterile == False:
                self.btnUnlockRobot_2.setHidden(True)
                self.btnDriveConfirm.setHidden(False)
                self.btnRobotResume.setHidden(True)
                self.btnUnlockRobot_2.setEnabled(False)
                self.NextScene()
                
        else:
            self._Robot_driveTo()
        
    def OnClicked_btnCancel(self):
        self.stkScene.setCurrentIndex(self.indexPrePage)
        
        DlgHintBox.Clear()
        
    def OnClicked_btnCloseToEntry(self):
        offset = int(self.ledOffset.text())
        if offset is not None:
            currentValue = self.sldTrajectory.value()
            currentValue = min(currentValue + offset, self.sldTrajectory.maximum())
            self.sldTrajectory.setValue(currentValue)
            
    def OnClicked_btnCloseToTarget(self):
        offset = int(self.ledOffset.text())
        if offset is not None:
            currentValue = self.sldTrajectory.value()
            currentValue = max(currentValue - offset, 0)
            self.sldTrajectory.setValue(currentValue)
            
    def OnClicked_btnConfirmFusion(self):
        for wipe in self.lstInteractorWipe:
            wipe.Close()
        self.lstInteractorWipe = []
        self.dicomLow.rendererAxial.SetTargetVisible(True)
        self.dicomLow.rendererSagittal.SetTargetVisible(True)
        self.dicomLow.rendererCoronal.SetTargetVisible(True)
        self.ShowDicom()
        
    def OnClicked_btnSetEntry(self):
        
        currentDicom:DISPLAY = self.currentTag.get("display")
        if currentDicom is None:
            return

        pickPoint = currentDicom.target.copy()
        if pickPoint is not None:
            currentDicom.DrawPoint(pickPoint, 1)    
            output = self._GetCurrentTrajectory()
            if output is None:
                return
            
            owner, idx = list(output.items())[0]
            if idx > -1:
                currentDicom.trajectory.setEntry(pickPoint, idx, owner)
                self.currentTag["entry"] = np.array(pickPoint)
                
                if DISPLAY.CountOfTrajectory() > idx:
                    self.currentTag.update({"flageSelectedPoint": True})
                    
                    self._ModifyTrajectory(idx, currentDicom)
                    self.SetUIEnable_Trajectory(True)
                    self._AddCrossSectionItemInSelector()
                    self._SaveBootFile()
                self.UpdateView()
            
    
    def OnClicked_btnSetTarget(self):

        currentDicom:DISPLAY = self.currentTag.get("display")
        if currentDicom is None:
            return

        pickPoint = currentDicom.target.copy()
        if pickPoint is not None:
            currentDicom.DrawPoint(pickPoint, 2)
            output = self._GetCurrentTrajectory()
            if output is None:
                return
            
            owner, idx = list(output.items())[0]
            if idx > -1:
                DISPLAY.trajectory.setTarget(pickPoint, idx, owner)
                self.currentTag["target"] = np.array(pickPoint)
                
                if DISPLAY.trajectory.count() > idx:
                    self.currentTag.update({"flageSelectedPoint": True})
                    
                    self._ModifyTrajectory(idx, currentDicom)
                    self.SetUIEnable_Trajectory(True)
                    self._AddCrossSectionItemInSelector()
                    self._SaveBootFile()
                self.UpdateView()
            
    def OnClicked_btnToEntry(self):
        currentDicom = self.currentTag.get('display')
        if not currentDicom:
            return
        
        # entryPoint = currentDicom.trajectory.getEntry()
        entryPoint = DISPLAY.trajectory.getEntry()
        if entryPoint is not None:
            bHasCrossSection = False
            nTrajectoryValue = self.sldTrajectory.maximum()
            self.sldTrajectory.blockSignals(True)
            self.sldTrajectory.setValue(nTrajectoryValue)
            self.sldTrajectory.blockSignals(False)
            self.OnValueChanged_sldTrajectory(nTrajectoryValue)
    
    def OnClicked_btnToTarget(self):
        currentDicom = self.currentTag.get('display')
        if not currentDicom:
            return
        
        # targetPoint = currentDicom.trajectory.getTarget()
        targetPoint = DISPLAY.trajectory.getTarget()
        if targetPoint is not None:
            bHasCrossSection = False
            self.sldTrajectory.blockSignals(True)
            self.sldTrajectory.setValue(0)
            self.sldTrajectory.blockSignals(False)
            self.OnValueChanged_sldTrajectory(0)
            
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
            for wdg in self.wdgPicture.children():
                if isinstance(wdg, QWidget):
                    self.wdgPicture.layout().removeWidget(wdg)
            # layout.removeWidget(self.tmpWidget)
            # self.tmpWidget = None
            
            if self.bSterile == True:
                self.OnClicked_btnDriveConfirm()
                return
            
            self.wdgPicture.setStyleSheet('image:url(image/foot_pedal_and_drapping.png);')
            self.wdgBottom.setHidden(False)
            self.btnUnlockRobot_2.setHidden(True)
            self.btnUnlockRobot_2.setEnabled(True)
            self.btnDriveConfirm.setHidden(False)
            
            # self.lblDescription.setText("""
            #                             <div style='color:#FFFFD0'>
            #                             <p>1. Press <span style='color:#f00'>Unlock button</span> to release robot arm</p>
            #                             <p>2. Press <span style='color:#f00'>foot pedal</span> and move robot arm <span style='color:#f00'>by hand</span></p>
            #                             <p>3. Make sure the position is <span style='color:#f00'>convenient for draping robot arm</span></p>
            #                             </div>
            #                             """)
            self.wdgAnimate.Start()
        elif nStep == 3:
            # self.btnUnlockRobot_2.setEnabled(False)
            self.lblDescription.setText('')
            self.Robot_FixArm()
            # self.wdgPicture.setStyleSheet('image:url(image/robot_back_target.png);')
            
            tmpWidget = QWidget()
            tmpWidget.setMinimumSize(1280, 720)
            tmpWidget.setMaximumSize(1280, 720)
            
            self.wdgPicture.setStyleSheet('')
            layout = self.wdgPicture.layout()
            if layout is None:
                layout = QHBoxLayout(self.wdgPicture)
                layout.setContentsMargins(0, 0, 0, 0)
            # self.tmpWidget = tmpWidget
            layout.addWidget(tmpWidget)
            self._PlayVedio(tmpWidget, 'video/resume_robot.mp4')
            
            self.btnUnlockRobot_2.setText('Unlock')
            self.wdgBottom.setHidden(True)
            # self.btnUnlockRobot_2.setEnabled(True)
            self.btnUnlockRobot_2.setHidden(False)
            self.btnUnlockRobot_2.setHidden(True)
            self.btnDriveConfirm.setHidden(True)
            self.btnRobotResume.setHidden(False)
            # self.btnRobotResume.setHidden(True)
            self.wdgAnimate.Start()
            
        elif nStep == 4:
            # self.wdgPicture.setStyleSheet('image:url(image/pedal_lock.png);')
            self.StopVedio()
            # self.stkScene.setCurrentWidget(self.pgPlaceHolder)
            self._Robot_driveTo()
            self.bSterile = True
        elif nStep is None:
            self._Robot_driveTo()
            # self.stkScene.setCurrentWidget(self.pgImageView)
            
    def OnClicked_btnMoveUp(self):
        iStyle = self.viewport_L['Fusion1'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.MoveUp()
    
    def OnClicked_btnMoveDown(self):
        iStyle = self.viewport_L['Fusion1'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.MoveDown()
    
    def OnClicked_btnMoveLeft(self):
        iStyle = self.viewport_L['Fusion1'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.MoveLeft()
    
    def OnClicked_btnMoveRight(self):
        iStyle = self.viewport_L['Fusion1'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.MoveRight()
    
    def OnClicked_btnReset(self):
        iStyle = self.viewport_L['Fusion1'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.Reset()
    
    def OnClicked_btnRotationL(self):
        iStyle = self.viewport_L['Fusion1'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.RotateL()
    
    def OnClicked_btnRotationR(self):
        iStyle = self.viewport_L['Fusion1'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.RotateR()
            
    def OnClicked_btnMoveUpS(self):
        iStyle = self.viewport_L['Fusion2'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.MoveUp()
    
    def OnClicked_btnMoveDownS(self):
        iStyle = self.viewport_L['Fusion2'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.MoveDown()
    
    def OnClicked_btnMoveLeftS(self):
        iStyle = self.viewport_L['Fusion2'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.MoveLeft()
    
    def OnClicked_btnMoveRightS(self):
        iStyle = self.viewport_L['Fusion2'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.MoveRight()
    
    def OnClicked_btnResetS(self):
        iStyle = self.viewport_L['Fusion2'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.Reset()
    
    def OnClicked_btnRotationLS(self):
        iStyle = self.viewport_L['Fusion2'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.RotateL()
    
    def OnClicked_btnRotationRS(self):
        iStyle = self.viewport_L['Fusion2'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.RotateR()
            
    def OnClicked_btnMoveUpC(self):
        iStyle = self.viewport_L['Fusion3'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.MoveUp()
    
    def OnClicked_btnMoveDownC(self):
        iStyle = self.viewport_L['Fusion3'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.MoveDown()
    
    def OnClicked_btnMoveLeftC(self):
        iStyle = self.viewport_L['Fusion3'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.MoveLeft()
    
    def OnClicked_btnMoveRightC(self):
        iStyle = self.viewport_L['Fusion3'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.MoveRight()
    
    def OnClicked_btnResetC(self):
        iStyle = self.viewport_L['Fusion3'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.Reset()
    
    def OnClicked_btnRotationLC(self):
        iStyle = self.viewport_L['Fusion3'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.RotateL()
    
    def OnClicked_btnRotationRC(self):
        iStyle = self.viewport_L['Fusion3'].iren.GetInteractorStyle()
        if isinstance(iStyle, InteractorStyleWipe):
            iStyle.RotateR()
            
    def OnClicked_btnTrajectoryList(self, idx:int, owner:str):
        # 切換Inhale / Exhale標識
        # owners = np.array(['I', 'E'])
        # objName = button.objectName()
        # if objName:
        #     owner, = owners[owners != button.text()]
        #     idx = int(objName[4:])
        #     item:QTreeWidgetItem = self.treeTrajectory.topLevelItem(idx)
        #     item.setData(0, ROLE_DICOM, owner)
        #     button.setText(owner)
            
        DISPLAY.trajectory.setOwner(idx, owner)
        self._SaveBootFile()
            
    def OnItemClicked(self, item:QTreeWidgetItem, column):
        if column == 0:
            bVisible = not item.data(0, ROLE_VISIBLE)
            # idx = self.treeTrajectory.indexOfTopLevelItem(item)
            idx = item.data(0, ROLE_TRAJECTORY)
            if not bVisible:
                item.setIcon(0, QIcon(IMG_HIDDEN))
            else:
                item.setIcon(0, QIcon(IMG_VISIBLE))
            
            item.setData(0, ROLE_VISIBLE, bVisible)
            
            self._CheckTrajectoryVisibleItem()
            self._SetTrajectoryVisible(idx, bVisible)
            
    def OnItemSelectionChanged_treeTrajectory(self, current:QTreeWidgetItem = None, prev:QTreeWidgetItem = None):
        column = self.treeTrajectory.currentColumn()
        # item = current
        item = self.treeTrajectory.currentItem()
        if column > 0:
            # idx = self.treeTrajectory.indexOfTopLevelItem(item)
            idx = item.data(0, ROLE_TRAJECTORY)
            display = self.currentTag.get('display')
            if None not in (idx, display) and isinstance(display, DISPLAY) and idx < DISPLAY.CountOfTrajectory():
                self.sldTrajectory.blockSignals(True)
                self._ModifyTrajectory(idx, display)
                self.sldTrajectory.blockSignals(False)
                display.SetCurrentTrajectory(idx)
                self.SetUIEnable_Trajectory(True)
            else:
                self.SetUIEnable_Trajectory(False)
            self.prevSelection_trajectory = item
            self.UpdateView()
        else:
            try:
                if self.prevSelection_trajectory is not None:
                    self.treeTrajectory.blockSignals(True)
                    self.treeTrajectory.setCurrentItem(self.prevSelection_trajectory)
                    self.treeTrajectory.blockSignals(False)
            except Exception as msg:
                logger.warning(msg)
                
    def OnItemDoubleClicked_treeTrajectory(self, item:QTreeWidgetItem, column:int):
        self.RobotRun()
                
    def OnHeaderClicked_trajectory(self, index:int):
        if index == 0:
            headItem:QTreeWidgetItem = self.treeTrajectory.headerItem()
            visibleStatus = headItem.data(0, ROLE_VISIBLE)
            # 0: all hidden 1:partial hidden 2:all visible
            bVisible = True
            icon = IMG_VISIBLE
            headerVisible = 2
            if visibleStatus == 2:
                bVisible = False
                icon = IMG_HIDDEN
                headerVisible = 0
                
            headItem.setData(0, ROLE_VISIBLE, headerVisible)
            headItem.setIcon(0, QIcon(icon))
            for i in range(self.treeTrajectory.topLevelItemCount()):
                item = self.treeTrajectory.topLevelItem(i)
                item.setIcon(0, QIcon(icon))
                item.setData(0, ROLE_VISIBLE, bVisible)
                self._SetTrajectoryVisible(i, bVisible)
                
    def OnMouseMove_views(self, obj, event, callData = None):
        views = [self.wdgFusionView1, self.wdgFusionView2, self.wdgFusionView3]
        if isinstance(obj, vtk.vtkRenderWindowInteractor):
            for i, view in enumerate(views):
                if obj == view.GetRenderWindow().GetInteractor():
                    self.floatingBox[i].setVisible(True)
                else:
                    self.floatingBox[i].setVisible(False)
    
    def OnValueChanged_spin(self, value:int):
        fValue = value * 0.001
        gVars['toleranceLaserData'] = fValue
        self.lblThreshold.setText(str(fValue))
    
    def OnValueChanged_sldTrajectory(self, value):
        dicOutput = self._GetCurrentTrajectory()
        if dicOutput is None:
            return
        
        idx = list(dicOutput.values())[0]
        
        trajectory = DISPLAY.trajectory[idx]
        if trajectory is not None:
            entry, target  = trajectory
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
        
            
    def OnChanged_sldWindowWidth(self, value):
        """set window width and show changed DICOM to ui
        """
        ## 設定 window width ############################################################################################
        currentDicom = self.currentTag.get('display')
        if not currentDicom:
            return
        
        self.currentTag['ww'] = value
        currentDicom.ChangeWindowWidthView(value)
        self.UpdateView()
        
    def OnChanged_sldWindowLevel(self, value):
        """set window width and show changed DICOM to ui
        """
        ## 設定 window level ############################################################################################
        currentDicom = self.currentTag.get('display')
        if not currentDicom:
            return
        
        self.currentTag['wl'] = value
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
                            view.signalChangedTrajPosition.connect(self.ChangeTrajectorySlider)
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
        selectedSeries = self._GetSeriesFromModelIndex(index)
        
        if selectedSeries is not None:
            strText, dimZ = self._GetInfoFromModelIndex(index)
            
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
                        
    def OnItemChanged(self, item:QStandardItem):
        if not item:
            return
        
        if item.isCheckable():
            if item.isAutoTristate():
                checkState = item.checkState()
                if checkState != Qt.PartiallyChecked:
                    self._TreeItemCheckAll(item, checkState)
            else:
                checkState = self._CheckChildAlterParent(item)
                parent = item.parent()
                if parent:
                    parent.setCheckState(checkState)
            
                self._TreeDicomViewFilter(item)
    
    def OnSelectionChanged_treeDicom(self, selected:QItemSelection, deselected:QItemSelection):
        if self.stepDicom == 1:
            dlg = DlgHintBox()
            dlg.SetText('then press <span style="color:#ff0000">Exhale button</span>', self.btnExhale, None)
            dlg.show()
            self.stepDicom += 1
        
        
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
            selectedRow = self._GetSeriesFromModelIndex(currentIndex)
                
            self.reader.SelectDataFromID(selectedRow[0], selectedRow[1], selectedRow[2], index)
            
            self.SetTreeDicomUserRole(index + 1, modelIndex = selected.indexes())
                
            lstSelected = self.dicSelectedSeries[index].get('selected')
            if lstSelected is not None and len(lstSelected) == 4:
                oldRow = lstSelected[3]
                deselection = QItemSelection()
                deselection.select(model.index(oldRow, 0), model.index(oldRow, column_count - 1))
                
                self.SetTreeDicomUserRole(None, oldRow)
                
                selectionModel.blockSignals(True)
                selectionModel.select(deselection, QItemSelectionModel.Deselect)
                selectionModel.blockSignals(False)
                
            patientID = selectedRow[0]
            studyID   = selectedRow[1]
            seriesID  = selectedRow[2]
            strText, dimZ = self._GetInfoFromModelIndex(currentIndex)
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
                        
                    self.SetTreeDicomUserRole(None, modelIndex = deselected.indexes())
                    
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
            if self.stepDicom == 3:
                dlg = DlgHintBox()
                dlg.SetText('Press confirm', self.btnImport, HINT_DOWN_RIGHT, 96)
                dlg.show()
                
                self.stepDicom += 1
            self.btnImport.setEnabled(True)
            
        self.treeDicom.viewport().update()
    
    def OnToggled_buttonGroup(self, button:QAbstractButton, bChecked:bool):
        if bChecked:
            self.ChangeCurrentDicom(button.objectName())
            
    def OnToggled_btgDIcom(self, button:QAbstractButton, bChecked:bool):
        if bChecked:
            if button == self.btnInhale:
                self.bToggleInhale = True
            else:
                self.bToggleInhale = False
                
                if self.stepDicom == 2:
                    dlg = DlgHintBox()
                    dlg.SetText('now select <span style="color:#f00">Exhale dicom</span> series', self.treeDicom, None)
                    dlg.show()
                    if self.stepDicom == 2:
                        self.stepDicom += 1
                        
    def OnToggled_btnGroup_ref(self, button:QAbstractButton, bChecked:bool):
        if bChecked:
            balls = self.currentTag.get('candidateBallVTK')
            if balls:
                reference = np.array(*list(balls.values()))
                renderer = self.viewport_L['LT'].renderer
                idx = self.btnGroup_ref.id(button)
                renderer.SetTarget(reference[idx][:3])
            
            self.UpdateTarget()
            self.UpdateView()
            
    def OnToggled_btnGroup_fusion(self, actionId:int, bChecked:bool):
        if bChecked:
            for i in range(1, 4):
                iStyle = self.viewport_L[f'Fusion{i}'].iren.GetInteractorStyle()
                if isinstance(iStyle, InteractorStyleWipe):
                    iStyle.SwitchMode(actionId)
                    
            if actionId == InteractorStyleWipe.MODE_FLUORO:
                if not self.widgetSlider:
                    self.widgetSlider = widgetFluoroSlider(self.btnModeFluoro)
                    self.widgetSlider.signalValueChange.connect(InteractorStyleWipe.SetFluoroSize)
                    self.listSubDialog.append(self.widgetSlider)
                
                self.widgetSlider.SetValue(InteractorStyleWipe.sizeFluoro)
                self.widgetSlider.show()
            else:
                if self.widgetSlider:
                    self.widgetSlider.close()
                        
            self.UpdateTarget()
            self.UpdateView()
            
    def OnToggled_btnGroup_tool(self, actionId:int, bChecked:bool):
        if bChecked:
            InteractorStyleWipe.action = actionId
            
    def OnToggled_btgGroup_Lung(self, imageId:int, bChecked:bool):
        if bChecked:
            InteractorStyleWipe.imageId = imageId
            
    def OnCurrentChange_tabWidget(self, index:int):
        if self.tabWidget.currentWidget() == self.tabGuidance:
            # msg = DlgHintBox()
            # msg.SetText('checkout the signal light is green for placing needle', self.stkSignalLight)
            # msg.show()
            pass
        
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
        logger.debug(f'brightness = {brightness}')
        
    def OnConstrastChanged(self, contrast:int):
        logger.debug(f'contrast = {contrast}')
    
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
    def NextSceneMain(self):
        currentIndex = self.stkMain.currentIndex()
        currentIndex = min(self.stkMain.count() - 1, currentIndex + 1)
        self.stkMain.setCurrentIndex(currentIndex)
        
    def NextScene(self):
        button = self.sender()
        if isinstance(button, QPushButton):
            if button == self.btnImport:
                
                #clear DlgHintBox
                DlgHintBox.Clear()
                
                self.bDicomChanged = True
                self.btnImport.setEnabled(False)
                
                if not self.ImportDicom_L():
                    return
                
                if not self.ImportDicom_H():
                    return
                
                self._SaveBootFile()
               
                self.ChangeCurrentDicom(self.btnDicomLow.objectName())
                self.ShowFusion()
                
                # self.dlgSystemProcessing = SystemProcessing(2)
                # self.dlgSystemProcessing.signalClose.connect(self.OnSignal_ProcessClose)
                # self.dlgSystemProcessing.setWindowTitle('Segmentation')
                # self.dlgSystemProcessing.label_Processing.setText('Lung volume calculating...')
                # self.dlgSystemProcessing.show()
                
                # tag = list(self.dicDicom.values())
                
                # lung.ShowImage(
                #     arrImage = self.imageL, 
                #     spacing = tag[0]['spacing'], 
                #     downSample = 256,
                #     signalCallback = self.dlgSystemProcessing.UpdateProgress
                # )
                # return
            elif button == self.btnNext_startAdjustLaser:
                self.Laser_StopLaserProfile()
                self.stkScene.setCurrentWidget(self.pgModelBuilding)
                return
            # elif button == self.btnNext_startBuildModel:
            #     self.Laser_StartRecordBreathingBase()
            #     print('start model building')
            elif button == self.btnNext_startBuildModel:
                self.Laser_StopRecordBreathingBase()
            elif button == self.btnNext_endBuildModel:
                self.Laser_StopRecordBreathingBase()
                logger.info('end model building')
            elif button == self.btnNext_scanCT:
                if self.tCheckInhale:
                    self.tCheckInhale.stop()
            elif button == self.btnNext_scanCT_2:
                if self.tCheckExhale:
                    self.tCheckExhale.stop()
            elif button == self.btnFromUSB:
                ## 開啟視窗選取資料夾 ############################################################################################
                # self.logUI.info('Import Dicom inhale/_Low')
                currentPath = os.path.join(os.getcwd(), 'database')
                
                dlg = QFileDialog()
                dlg.setDirectory(currentPath)
                dlg.setFileMode(QFileDialog.Directory)
                dlg.setFilter(QDir.Files)

                if dlg.exec_():
                    filePath = dlg.selectedFiles()[0]
                    self.ImportDicom(filePath)
                    
                else:
                    return
                
        self.player.stop()
        index = self.stkScene.currentIndex()
        index = min(self.stkScene.count() - 1, index + 1)
        self.stkScene.setCurrentIndex(index)
        
    def BackScene(self):
        index = self.stkScene.currentIndex()
        index = max(0, index - 1)
        self.stkScene.setCurrentIndex(index)
        
    def ChangeCurrentDicom(self, dicomName:str):
        # 取得原本的target point(十字標線交差點)
        display:DISPLAY = self.currentTag.get('display')
        # matrix = self.currentTag.get('matrix')
        crosshair = None
        if display:
            crosshair = display.target.copy()
            
        # if matrix is not None:
        #     crosshair = np.matmul(matrix, np.append(crosshair, 1))
            
        tag = self.dicDicom.get(dicomName)
        if tag is None:
            # QMessageBox.critical(None, 'dicom error', 'dicom name not exists')
            MessageBox.ShowCritical('dicom error', 'dicom name not exists')
            return False
        
        self.currentTag = tag
        
            
        # if dicomName == self.btnDicomLow.objectName():
        
        idxFrom = 0 # inhale
        idxTo = 1   # exhale
        if dicomName == self.btnDicomLow.objectName():
            idxFrom = 1
            idxTo = 0
        DISPLAY.CopyCamera(idxFrom, idxTo)
            
        self.ShowDicom()
        
        display = self.currentTag.get('display')
        if display and crosshair is not None:
            display.target[:] = crosshair[:3]
            
        self.UpdateTarget()
        self.UpdateView()
            
        return True
        
    def ChangeTrajectorySlider(self, value:int):
        # 跟OnValueChanged_sldTrajectory不同的是
        # 這是單純為了讓拖動scrollBar同步改變sldTrajectory的值
        # 而不會觸發OnValueChanged
        # 以避免重複觸發slot事件的無限迴圈
        self.sldTrajectory.blockSignals(True)
        self.sldTrajectory.setValue(value)
        self.sldTrajectory.blockSignals(False)
        
    def MainSceneChanged(self, index):
        if self.stkMain.currentWidget() == self.page_loading:
            self.StopVedio()
            self.idEnabledDevice = DEVICE_ENABLED
            self._EnableDevice(DEVICE_ENABLED)
        elif self.stkMain.currentWidget() == self.pgInstallSupportArm:
            self._PlayVedio(self.wdgInstallSupportArm, 'video/patient_install_support_arm.mp4')
            
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
        self.StopVedio()
        self.indexPrePage = self.indexCurrentPage
        self.indexCurrentPage = index
        currentWidget = self.stkScene.currentWidget()
        if currentWidget == self.pgUnlockRobot:
            self.wdgAnimateUnlock.Start()
        elif currentWidget == self.pgLaserAdjust:
            self.Laser_ShowLaserProfile()
        elif currentWidget == self.pgModelBuilding:
            self.btnStartBuildModel.setEnabled(True)
            self.btnNext_startBuildModel.setEnabled(False)
            self.figModel.Clear()
        elif currentWidget == self.pgStartInhaleCT:
            self.Laser_CheckInhale()
        elif currentWidget == self.pgStartExhaleCT:
            self.Laser_CheckExhale()
        elif currentWidget == self.pgDicomList:   
            self.btnImport.setEnabled(False)
                     
            # dlgHint = DlgHint()
            # dlgHint.setWindowFlags(Qt.WindowStaysOnTopHint)
            # dlgHint.setWindowFlags(dlgHint.windowFlags() & ~Qt.WindowMinMaxButtonsHint)
            # dlgHint.show()
            # self.listSubDialog.append(dlgHint)
            
            dlg = DlgHintBox()
            dlg.SetText('select Inhale dicom series first', self.treeDicom, None)
            dlg.show()
            
        elif currentWidget == self.pgRobotRegSphere:
            self._PlayVedio(self.wdgSetupBall, 'video/ball_setup.mp4')
        elif currentWidget == self.pgPositionRobot:
            self._PlayVedio(self.wdgPositionRobotPicture, 'video/robot_set_target.mp4')
            self.wdgAnimatePositionRobot.Start()
        elif currentWidget == self.pgRobotSupportArm:
            # self._PlayVedio(self.wdgSetupRobot, 'video/robot_mount_support_arm.mp4')
            self._PlayVedio(self.wdgSetupRobot, 'video/robot_install.mp4')
        elif currentWidget == self.pgDriveRobotGuide:
            self.wdgStep.GotoStep(1)
            self.wdgBottom.setHidden(False)
            self.btnDriveConfirm.setEnabled(True)
            self.btnUnlockRobot_2.setEnabled(False)
            self.btnRobotResume.setEnabled(False)
            
            tmpWidget = QWidget()
            tmpWidget.setMinimumSize(800, 600)
            tmpWidget.setMaximumSize(800, 600)
            
            self.wdgPicture.setStyleSheet('')
            layout = self.wdgPicture.layout()
            if layout is None:
                layout = QHBoxLayout(self.wdgPicture)
                layout.setContentsMargins(0, 0, 0, 0)
            # self.tmpWidget = tmpWidget
            layout.addWidget(tmpWidget)
            self._PlayVedio(tmpWidget, 'video/InstallHolder.mp4')
        elif currentWidget == self.pgSterileStep1:
            self._PlayVedio(self.wdgChangeTool, 'video/InstallHolder.mp4')            
        elif currentWidget == self.pgSterileStep3:
            self.GetRobotPosition()
        elif currentWidget == self.pgImportDicom:
            self._DetectUnexpectedShutdown()
        
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
                # self.Laser_SetBreathingCycleUI()
                if self.tCheckInhale is not None:
                    self.tCheckInhale.stop()
                    
                if self.tCheckExhale is not None:
                    self.tCheckExhale.stop()
                    
                self.dicDataCycleManual = {}
                self.lstRecordAvg = []
                self.nCycle = 1
                    
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
                if self.stkMain.currentWidget() != self.pgScene:
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
            if self.stkMain.currentWidget() != self.pgScene:
                self.signalLoadingReady.emit()
                
    
        
    def OnSignal_LoadingReady(self):
        # index = self.stkMain.currentIndex()
        # self.stkMain.setCurrentIndex(index + 1)
        self.stkMain.setCurrentWidget(self.pgScene)
        if self.stkScene.currentWidget() == self.pgUnlockRobot:
            self.wdgAnimateUnlock.Start()
        
    def OnSignal_ModelBuilding(self, bValid):
        if bValid:
            self.btnNext_startBuildModel.setEnabled(True)
        else:
            self.btnNext_startBuildModel.setEnabled(False)
        
    def OnSignal_SetProgress(self, progressBar, percent):
        if not isinstance(progressBar, QProgressBar):
            return
        
        progressBar.setValue(percent)
        
    def OnSignal_SetCheck(self, widget, bCheck):
        if not isinstance(widget, QWidget):
            return
        
        if bCheck:
            widget.setStyleSheet('border-image:url(image/check.png);')
            widget.update()
        else:
            widget.setStyleSheet('border-image:none;')
            
    def OnSignal_ShowMessage(self, msg:str, title:str, bIsError = False):
        if len(msg) > 0:
            if not bIsError:
                MessageBox.ShowInformation(msg)
            else:
                MessageBox.ShowCritical(msg)
                
    def OnSignal_ProcessClose(self):
        self.dlgSystemProcessing = None
            
            
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
            sleep(0.1)
        # fft_result = np.fft.fft(self.recordData)
        
        logger.debug(f'total cycle = {cycleCount}')
            
    def SetRegistration_L(self):
        """automatic find registration ball center + open another ui window to let user selects ball in order (origin -> x axis -> y axis)
        """
        return self._Registration(self.imageL, self.currentTag.get('spacing'))
    
    def SetRegistration_H(self):
        """automatic find registration ball center + open another ui window to let user selects ball in order (origin -> x axis -> y axis)
        """
        return self._Registration(self.imageH, self.currentTag.get('spacing'))
    
    def ShowRegistrationDifference(self):
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
            logger.warning("pair error / ShowRegistrationDifference_L() error")
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
            logStr = f'registration RMS: {error[2]:.2f} mm'
            logger.info(logStr)
            # MessageBox.ShowInformation(logStr)
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
                if self.stkMain.currentWidget() != self.pgScene:
                    self.signalLoadingReady.emit()
                
    def Demo_OnLaserLoading(self, progress:int):
        self.loadingLaser = progress
        self.signalSetProgress.emit(self.pgbLaser, progress)
        
        sleep(1)
        if hasattr(self, 'loadingRobot'):
            if self.loadingLaser >= 100 and self.loadingRobot >= 100:
                if self.stkMain.currentWidget() != self.pgScene:
                    self.signalLoadingReady.emit()
                    # self.stkMain.setCurrentWidget(self.pgScene)
                    
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
            self.signalDemoHoming.emit(percent)
            
    def RobotSystem_Initialize(self):
        self.robot.Initialize()
        self.RobotSupportArm.Initialize()
        # self.OperationLight.Initialize()
                
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
        if not self.showError:
            self.showError = True
           
            if ((self.errDevice & DEVICE_LASER) != 0 and self.nLaserErrorCount == 0):
                # 第一次Laser連線失敗直接重試
                self.errDevice &= ~DEVICE_LASER
                self.nLaserErrorCount += 1
                self.Laser.CloseLaser()
                sleep(0.5)
                logger.warning('Laser device suffered connection error in first switch on, re-connecting...')
                tLaser = threading.Thread(target = self.Laser.Initialize)
                tLaser.start()
                self.showError = False
            else:
                ret = MessageBox.ShowQuestion(msg + '\nRetry again?', 'Retry', 'Shutdown')
                self.showError = False
                if ret == 0:
                    
                    if (self.errDevice & DEVICE_ROBOT) != 0:
                        self.errDevice &= ~DEVICE_ROBOT
                        tRobot = threading.Thread(target = self.robot.Initialize)
                        tRobot.start()
                        
                    if (self.errDevice & DEVICE_LASER) != 0:
                        self.errDevice &= ~DEVICE_LASER
                        self.Laser.CloseLaser()
                        sleep(0.5)
                        tLaser = threading.Thread(target = self.Laser.Initialize)
                        tLaser.start()
                    
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
                if self.stkMain.currentWidget() != self.pgScene:
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
            logger.error("Robot Compensation error")
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
        self.Robot_HomingProcess()
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
            if self.robot.HomeProcessing_image() == True:
                print("Home processing is done!")
                # QMessageBox.information(self, "information", "Home processing is done!")
                self.homeStatus = True
                # self.RobotRun()
                
    def Robot_OnSignalFootPedal(self, bPress:bool):
        if bPress:
            currentWidget = self.stkScene.currentWidget()
            if self.wdgAnimateUnlock.IsActive():
                self.wdgAnimateUnlock.Stop()
                self.Robot_ReleaseArm()
            elif self.wdgAnimatePositionRobot.IsActive():
                self.wdgAnimatePositionRobot.Stop()
                self.Robot_ReleaseArm()
            elif self.wdgStep.GetStep() == 2 and self.wdgAnimate.IsActive():
                # self.wdgAnimate.Stop()
                self.wdgAnimate.SetPause()
                # self.tmPedal.stop()
                self.Robot_ReleaseArm()
            elif self.wdgStep.GetStep() == 3 and self.wdgAnimate.IsActive():
                self.wdgAnimate.Stop()
                # self.tmPedal.stop()
                self.Robot_BackToTarget()
        
        if self.dlgFootPedal is not None:
            self.dlgFootPedal.SetPress(bPress)
            # bNext = self.dlgFootPedal.IsToNextScene()
            # self.dlgFootPedal.close()
            # self.dlgFootPedal = None
            # if bNext:
            #     self.NextScene()
            
        if self.dlgResumeSupportArm is not None:
            self.dlgResumeSupportArm.SetPress(bPress)
            
    def Robot_OnSignalTargetArrived(self):
        if self.dlgResumeSupportArm is not None:
            self.dlgResumeSupportArm.accept()
            
        self.OnClicked_btnDriveConfirm()
        
    def Robot_OnSignalAxisValue(self, nAxisIndex:int, diffValue:float):
        greenZoneColor = QColor(0, 255, 0)
        if abs(diffValue) > 5000:        
            try:
                num = 52
                colorRed = np.linspace(0, 255, num, dtype = int)
                colorGreen = np.linspace(255, 0, num, dtype = int)
                index = (abs(diffValue) - 5000) // 500 + 1
                index = int(min(num - 1, index))
            
                greenZoneColor = QColor(colorRed[index], colorGreen[index], 0)
            except Exception as msg:
                logger.critical(msg)
        # 將數值-5000 ~ 5000轉換成 0 ~ 100
        # diffValue = (diffValue + 5000) * 0.01
        if self.dlgResumeSupportArm is not None:
            self.dlgResumeSupportArm.SetValue(nAxisIndex, diffValue, greenZoneColor)
                
    def Robot_Stop(self):
        # QMessageBox.information(None, 'Info', 'Robot Stop')
        MessageBox.ShowInformation('Robot Stop')
        
    def RobotRun(self):
        # 路徑轉換
        dicomInhale = list(self.dicDicom.values())[0]
        dicomExhale = list(self.dicDicom.values())[1]
        # pathInhale = dicomInhale.get('trajectory')
        # pathExhale = dicomExhale.get('trajectory')
        
        try:
            dicOutput:dict = self._GetCurrentTrajectory()
            if dicOutput is None:
                return
                
            if len(dicOutput) < 2:
                msgMissing = {'I':'Exhale', 'E':'Inhale'}
                logger.error(f'missing trajectory:{msgMissing[list(dicOutput.keys())[0]]}')
                return
            
            pathInhale = DISPLAY.trajectory[dicOutput['I']]
            pathExhale = DISPLAY.trajectory[dicOutput['E']]
            
            if pathInhale is not None and pathExhale is not None:
                regBallInhale = dicomInhale.get('regBall')
                # regBallExhale = dicomExhale.get('regBall')
                regMatrixInhale = dicomInhale.get('regMatrix')
                # regMatrixExhale = dicomExhale.get('regMatrix')
                # invMatrix = np.linalg.inv(regMatrixExhale)
                # regMatrixExhale = np.matmul(invMatrix, regMatrixInhale)
                
                # inhale和exhale dicome在完成註冊時，已轉換成同一座標，故原點和矩陣使用inhale的參數即可
                pathInhale = self.regFn.GetPlanningPath(regBallInhale[0], pathInhale, regMatrixInhale)
                pathExhale = self.regFn.GetPlanningPath(regBallInhale[0], pathExhale, regMatrixInhale)
                    
                logger.debug(f'inhale path = {pathInhale}')
                logger.debug(f'exhale path = {pathExhale}')
                
                pathInhale = [p * [1, 1, -1] for p in pathInhale]
                pathExhale = [p * [1, 1, -1] for p in pathExhale]
                
        except Exception as msg:
            logger.error(msg)
        
        if self.homeStatus is True:
            self.robot.P2P(pathInhale[0], pathInhale[1], pathExhale[0], pathExhale[1])
            print("Robot run processing is done!")
            # QMessageBox.information(self, "information", "Robot run processing is done!")
            
            #執行呼吸補償
            self.robot.breathingCompensation()
            
            nextPoint = input("是否執行下一個手術點?如果是，請按'Y'，若不是請按'N'")
            if nextPoint == 'Y':
                self.robot.P2P(entry_full_2, target_full_2, entry_halt_2, target_halt_2)
                #執行呼吸補償
                self.robot.breathingCompensation()
        else:
            logger.warning("Please execute home processing first.")
            # QMessageBox.information(self, "information", "Please execute home processing first.")
            MessageBox.ShowInformation("Please execute home processing first.")
        
    def ReleaseRobotArm(self):
        self.FixArmStatus = False
        while self.FixArmStatus == False:
            self.RobotSupportArm.ReleaseAllEncoder()
            # print('robot release')
        
    def Robot_ReleaseArm(self):
        self.btnRobotRelease.setEnabled(False)
        self.btnRobotFix.setEnabled(True)
        self.btnRobotSetTarget.setEnabled(False)
        self.btnRobotBackTarget.setEnabled(False)
        
        # self.btnUnlockRobot_2.setEnabled(False)
        # self.btnUnlockConfirm.setEnabled(True)
        self.btnDriveConfirm.setEnabled(True)
        # self.btnRobotTarget.setEnabled(True)
        self.btnRobotResume.setEnabled(False)
        
        for animateWidget in self.lstAnimateWidget:
            if animateWidget.IsActive():
                animateWidget.SetPause()
        
        if self.RobotSupportArm:
            self.tReleaseArm = threading.Thread(target = self.ReleaseRobotArm)
            self.tReleaseArm.start()

        sender = self.sender()
        self.dlgFootPedal = DlgFootPedal()
                
        # 發送指令不是透過解鎖按鈕
        if not isinstance(sender, QPushButton):
            currentWidget = self.stkScene.currentWidget()
            if currentWidget == self.pgPositionRobot:
                self.dlgFootPedal.SetAction(ACTION_POSITION_ROBOT)
            elif currentWidget == self.pgUnlockRobot:
                self.dlgFootPedal.SetAction(ACTION_NEXT_SCENE)
            elif currentWidget == self.pgDriveRobotGuide:
                self.dlgFootPedal.SetAction(ACTION_DRIVE_CONFIRM)
            
        self.dlgFootPedal.signalClose.connect(self.Robot_OnConfirmPosition)
        self.dlgFootPedal.exec_()
    
    # 當按下確定位置, 上鎖並前往下一步
    def Robot_OnConfirmPosition(self):
        self.Robot_FixArm()
        # currentWidget = self.stkScene.currentWidget()
        # if currentWidget == self.pgUnlockRobot:
        #     self.NextScene()
        # elif currentWidget == self.pgDriveRobotGuide:
        #     if self.wdgStep.GetStep() == 2:
        #         self.OnClicked_btnDriveConfirm()
        # elif currentWidget == self.pgPositionRobot:
        #     sleep(0.5)
        #     self.Robot_SettingTarget()
        #     self.NextScene()
        if self.dlgFootPedal:
            idAction = self.dlgFootPedal.GetAction()
            if idAction == ACTION_NEXT_SCENE:
                self.NextScene()
            # elif idAction == ACTION_DRIVE_CONFIRM:
            #     if self.wdgStep.GetStep() == 2:
            #         self.OnClicked_btnDriveConfirm()
            elif idAction == ACTION_POSITION_ROBOT:
                sleep(0.5)
                self.Robot_SettingTarget()
                self.NextScene()
            
        for animateWidget in self.lstAnimateWidget:
            animateWidget.SetPause(False)
            
        # self.wdgAnimate.Stop()
        self.dlgFootPedal = None
        
    def Robot_FixArm(self):
        self.btnRobotRelease.setEnabled(True)
        self.btnRobotFix.setEnabled(False)
        self.btnRobotSetTarget.setEnabled(True)
        # self.btnUnlockRobot_2.setEnabled(True)
        # self.btnUnlockConfirm.setEnabled(False)
        # self.btnDriveConfirm.setEnabled(False)
        # self.btnRobotTarget.setEnabled(False)
        
        if self.settingTarget == True:
            self.btnRobotBackTarget.setEnabled(True)
            self.btnRobotResume.setEnabled(True)
        else:
            self.btnRobotBackTarget.setEnabled(False)
            self.btnRobotResume.setEnabled(False)
            
        self.FixArmStatus = True
        
    def Robot_SettingTarget(self):
        
        self.btnRobotSetTarget.setEnabled(False)
        # self.btnRobotTarget.setEnabled(False)
        # self.btnTargetRobotConfirm.setEnabled(True)
        
        if self.settingTarget:
            self.btnRobotBackTarget.setEnabled(True)
            self.btnRobotResume.setEnabled(True)
        else:
            self.btnRobotBackTarget.setEnabled(False)
            self.btnRobotResume.setEnabled(False)
            
        if self.RobotSupportArm:
            self.RobotSupportArm.SetTargetPos()
        self.settingTarget = True
        
        logger.info('setting robot target')
        
    def Robot_FixAndTarget(self):
        self.Robot_FixArm()
        sleep(0.5)
        self.Robot_SettingTarget()
        
    def Robot_BackToTarget(self):
        self.btnRobotRelease.setEnabled(False)
        self.btnRobotFix.setEnabled(True)
        self.btnRobotSetTarget.setEnabled(False)
        self.btnRobotBackTarget.setEnabled(False)
        self.btnRobotResume.setEnabled(False)
        
        if self.RobotSupportArm:
            tBackToTarget = threading.Thread(target = self.RobotSupportArm.BackToTargetPos)
            tBackToTarget.start()
        
        self.dlgResumeSupportArm = DlgResumeSupportArm()
        self.dlgResumeSupportArm.exec_()
        
        self.Robot_FixArm()
        
    def Robot_GetPedal(self):
        if self.RobotSupportArm:
            self.RobotSupportArm.ReadPedal()
    
        
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
                            logger.debug(f'cycle {i} = ({percentIn}, {percentEx})')
                        logger.debug('=' * 50)
                            
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
                logger.warning('laser data is None')
        
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
                if self.stkMain.currentWidget() != self.pgScene:
                    # self.stkScene.setCurrentWidget(self.pgLaser)
                    self.signalLoadingReady.emit()
                    # self.stkMain.setCurrentWidget(self.pgScene)
                    
    def Laser_autoNextPage(self, msgbox = None):
        if isinstance(msgbox, QMessageBox):
            msgbox.accept()
        # self.NextScene()
        if self.idEnabledDevice == DEVICE_LASER:
            self.stkScene.setCurrentWidget(self.pgStartInhaleCT)
        else:
            self.stkScene.setCurrentWidget(self.pgRobotRegSphere)
        
    def Laser_runCheckData(self, avgData):
        percent = self.Laser.GetPercentFromAvg(avgData)
        percent = np.reshape(percent, (-1, 2))
        
        indexes, = np.where((percent[:, 0] >= 80) & (percent[:, 1] <= 20))
        score = len(indexes) / len(percent) * 100
        
        strScore = f'score:{score:5.1f}'
        logger.debug('=' * 30)
        logger.debug(f'{strScore:^30}')
        logger.debug('=' * 30)
        
        return score, percent
    
    def Laser_OnSignalBreathingRatio(self, ratio):
        # self.avgValueDataTmp = []
        
        if self.greenLightCriteria is not None and self.yellowLightCriteria is not None:
            if ratio >= self.greenLightCriteria:  #綠燈
                self.stkSignalLight.setCurrentWidget(self.pgGreenLight)
            elif ratio >= self.yellowLightCriteria and ratio < self.greenLightCriteria: #黃燈
                self.stkSignalLight.setCurrentWidget(self.pgOrangeLight)
            else:
                self.stkSignalLight.setCurrentWidget(self.pgRedLight)
                    
            # self.laserFigure.update_figure(self.Laser.PlotProfile())
            # self.avgValueDataTmp.append(ratio)
            
            if isinstance(ratio, float):
                self.breathingPercentage = ratio     
                
                if self.dlgRobotDrive:
                    if ratio >= self.greenLightCriteria:
                        self.dlgRobotDrive.SetState(True)
                        
                        if self.dlgShowHint is not None:
                            self.dlgShowHint.close()
                            self.dlgShowHint = None
                    else:
                        self.dlgRobotDrive.SetState(False)
                        
                        if self.dlgShowHint is None:
                            self.dlgShowHint = DlgHintBox()
                            if DlgHintBox.IsShow():
                                # pos = self.stkSignalLight.mapToGlobal(self.stkSignalLight.pos())
                                # self.dlgShowHint.SetPosition(pos)
                                self.dlgShowHint.SetText('Adjust patient\'s breath to reach green light', self.stkSignalLight)
                                self.dlgShowHint.show()
                    
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
            MessageBox.ShowCritical('Please try to build chest model again.')
            # self.lytLaserModel.replaceWidget(self.laserFigure, self.lblHintModelBuilding)
            # self.Laser_SetBreathingCycleUI()
            self.ToSceneLaser()
           
    # def Laser_OnSignalInhale(self, bInhale:bool, percentage:float, lstPercent:list):
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
        
        # if not hasattr(self, '_dataY'):
        #     plt.ion()
        #     plt.rc('font', family='Microsoft JhengHei')
        #     fig = plt.figure(figsize=(5, 5))
        #     self.fig = fig
        #     axe = fig.add_subplot(111)
        #     axe.set_xlabel('前100筆資料(percent由大到小)')
        #     axe.set_ylabel('percentage (%)')
            
        #     axe.set_xlim([0, 100])
        #     axe.set_ylim([-10, 110])
        #     self.axe = axe
        #     self._dataY, = axe.plot([], [])
            
        # if len(lstPercent) > 100:
        #     lstPercent = lstPercent[:100] 
            
        # self._dataY.set_data(range(len(lstPercent)), lstPercent)
        # plt.draw()
        
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
         
    def Laser_OnSignalShowHint(self, text:str):
        self.lblLaserHint.setText(text)
                    
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
        
    def Laser_Adjustment(self):
        while self.bLaserShowProfile:
            plotData = self.Laser.PlotProfile()
            if plotData is not None:
                # self.laserFigure.update_figure(plotData)
                self.laserFigure.update_figure(*plotData)
            
            # FPS 30
            sleep(0.033)
        logger.info("Laser Adjust Done!")
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
                logger.debug(f'cycle {i} = ({percentIn}, {percentEx})')
                if percentIn < 80 or percentEx > 20:
                    bPass = False
                    
            if bPass:
                logger.info('cycles reconstruction succeed')
            else:
                logger.warning('ccycles reconstruction failed')
                
            return bPass
        return False
    
    def Laser_FilterCycles(self, lstAvg, lstPercent):
        if isinstance(lstAvg, (tuple, list)):
            lstAvg = np.array(lstAvg)
            
        try:
            if isinstance(lstPercent, (tuple, list, np.ndarray)):
                lstPercent = np.reshape(lstPercent, (-1, 2))
        except Exception as msg:
            logger.critical(msg)
            return False
        
        nNum = len(lstPercent)
                                
        indexes, = np.where((lstPercent[:, 0] >= 80) & (lstPercent[:, 1] <= 20))
        numOfIndexes = len(indexes)
        score = (numOfIndexes / nNum) * 100
        logger.debug(f'first time score:{score}')
        
        if score > MODEL_SCORE:
            return True    
        else:
            nRound = 1
            # try:
            avgOrigin = np.reshape(lstAvg, (-1, 2))
            while score < MODEL_SCORE:
                if len(lstPercent) < VALID_CYCLE_NUM:
                    logger.warning('validated model data is not enough')
                    return False
                
                indexesInhale, = np.where(lstPercent[:, 0] < INHALE_AREA)
                indexesExhale, = np.where(lstPercent[:, 1] > EXHALE_AREA)
                
                if len(indexesInhale) > len(indexesExhale):
                    sortedAvg = sorted(avgOrigin[:, 0])
                    # 選擇第二小的值
                    avgMin = sortedAvg[1]
                    avgMax = np.max(avgOrigin[:, 1])
                    logger.debug('\ncase 1')
                    logger.debug(f'round {nRound} avg max = {avgMax}, avg min = {avgMin}\n')
                    nRound += 1
                    
                    self.Laser.FilterDataByAvgRange(avgMax, avgMin)
                    
                    indexes, = np.where(lstPercent[:, 0] < 100)
                    if len(indexes) > 0:
                        avgData = avgOrigin[indexes]
                        score, percent = self.Laser_runCheckData(avgData)
                        
                        for i, p, avg in zip(indexes, percent, avgData):
                            _a, _b = lstPercent[i]
                            logger.debug(f'[{i:2}] origin = [{_a:10.6f} {_b:10.6f}], after = [{p[0]:10.6f} {p[1]:10.6f}]')
                    
                        if score > MODEL_SCORE:
                            return True
                        
                        # 迭代
                        lstPercent = percent
                        avgOrigin = avgData
                    else:
                        logger.warning('test data empty')
                        return False
                    
                elif len(indexesInhale) < len(indexesExhale):
                    avgMin = np.min(avgOrigin[:, 0])
                    sortedAvg = sorted(avgOrigin[:, 1])
                    # 找第二大的值
                    avgMax = sortedAvg[-2]
                    logger.debug('\ncase 2')
                    logger.debug(f'round {nRound} avg max = {avgMax}, avg min = {avgMin}\n')
                    nRound += 1
                    
                    self.Laser.FilterDataByAvgRange(avgMax, avgMin)
                    
                    indexes, = np.where(lstPercent[:, 1] > 0)
                    if len(indexes) > 0:
                        avgData = avgOrigin[indexes]
                        score, percent = self.Laser_runCheckData(avgData)
                        
                        for i, p, avg in zip(indexes, percent, avgData):
                            _a, _b = lstPercent[i]
                            logger.debug(f'[{i:2}] origin = [{_a:10.6f} {_b:10.6f}], after = [{p[0]:10.6f} {p[1]:10.6f}]')
                    
                        if score > MODEL_SCORE:
                            return True
                        
                        # 迭代
                        lstPercent = percent
                        avgOrigin = avgData
                    else:
                        logger.warning('test data empty')
                elif len(indexesInhale) == len(indexesExhale):
                    # 選擇第二小的值
                    sortedAvg = sorted(avgOrigin[:, 0])
                    avgMin = sortedAvg[1]
                    
                    # 找第二大的值
                    sortedAvg = sorted(avgOrigin[:, 1])
                    avgMax = sortedAvg[-2]
                    
                    logger.debug('\ncase 3')
                    logger.debug(f'round {nRound} avg max = {avgMax}, avg min = {avgMin}\n')
                    nRound += 1
                    
                    self.Laser.FilterDataByAvgRange(avgMax, avgMin)
                    
                    indexes, = np.where((lstPercent[:, 0] < 100) & (lstPercent[:, 1] > 0))
                    if len(indexes) > 0:
                        avgData = avgOrigin[indexes]
                        score, percent = self.Laser_runCheckData(avgData)
                        
                        for i, p, avg in zip(indexes, percent, avgData):
                            _a, _b = lstPercent[i]
                            logger.debug(f'[{i:2}] origin = [{_a:10.6f} {_b:10.6f}], after = [{p[0]:10.6f} {p[1]:10.6f}]')
                        
                        if score > MODEL_SCORE:
                            return True
                        
                        # 迭代
                        lstPercent = percent
                        avgOrigin = avgData
                    else:
                        logger.warning('test data empty')
                        return False
            # except Exception as msg:
            #     print(f'error:{msg}')
            #     return False
            
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
        if self.Laser is None:
            return
        
        # self.btnStartBuildModel_2.setEnabled(False)
        self.btnStartBuildModel.setEnabled(False)
        # self.btnAutoRecord.setEnabled(False)
        self.recordBreathingBase = False
        self.bLaserRecording = True
        # self.lytLaserModel.replaceWidget(self.lblHintModelBuilding, self.laserFigure)
        # layout = self.wdgLaser.layout()
        # if layout is None:
        #     layout = QVBoxLayout(self.wdgLaser)
        #     layout.setContentsMargins(0, 0, 0, 0)
        # layout.addWidget(self.laserFigure)
        
        # t = threading.Thread(target = self.Laser_RecordBreathingCycle)
        t = threading.Thread(target = self.Laser_RecordBreathing)
        t.start()
        
    def Laser_StopRecordBreathingBase(self):
        logger.info("breath recording Stop")
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
        logger.info("Cheast Breathing Measure Start")
        
        # 紀錄初始時間戳記
        startTime = time.time()
        lastTime = startTime
        while self.bLaserRecording is True:
            # 取得 laser 資料
            plotData = self.Laser.PlotProfile()
            
            # 計算時間變化量
            curTime = time.time()
            deltaTime = int((curTime - startTime) * 1000)
            if plotData is not None:
                # 繪製 laser 資料線圖(plot)
                self.figModel.update_figure(*plotData, nIndex = 0)
                
                rawData = self.Laser.ModelBuilding()
                if len(rawData) > 0:
                    # 將資料紀錄成 dictionary，以時間變化為key
                    receiveData[deltaTime] = rawData
                    # 每隔1秒算一次，避免太過頻繁的運算
                    if curTime - lastTime > 1:
                        # 分析資料的週期，當週期數達到閾值，資料蒐集完成
                        bValid, data, lstTime = self.Laser.DataCheckCycle(receiveData, nValidCycle + 5)
                        
                        # 資料繪制於右側子圖，因目前座標軸範圍設定為負值，暫時轉換成負值處理
                        data = np.array(data) * -1
                        
                        # 更新子圖一(右側子圖)
                        # self.figModel.update_figure(data, nIndex = 1)
                        self.figModel.DrawData(lstTime, data, nIndex = 1)
                        if bValid:
                            self.bLaserRecording = False
                        lastTime = curTime
                            
                        
        logger.debug(f"Breathing recording stopped.Total spends:{(curTime - startTime):.3f} sec")
        # 完成資料蒐集後，進行資料編排處理、計算百分比等演算法
        if self.Laser.DataRearrange(receiveData, self.yellowLightCriteria, self.greenLightCriteria):
            # 對編排後的資料再進行一次週期分析，確保週期數目符合設定
            bValid, lstAvg, *_ = self.Laser.DataCheckCycle()
            
            # 篩選週期，目前暫定先不篩選，因前面已有就斜率變化進行過濾
            # lstPercent = self.Laser.GetPercentFromAvg(lstAvg)
            # bValid &= self.Laser_FilterCycles(lstAvg, lstPercent)
            # self.signalShowPlot.emit(cycle)
            
            # 發送是否建模成功的訊號
            if not bValid:
                self.signalModelBuildingPass.emit(False)
            else:
                self.recordBreathingBase = True
                self.signalModelBuildingPass.emit(True)
    def Laser_RecordBreathingCycle(self):
        if self.Laser is None:
            return
        
        nCycle = 1
        self.dicDataCycle = {}
        self.dicDataCycle[nCycle] = {}
        logger.info("Cheast Breathing Measure Start")
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
                                    logger.info(f'cycle {i} = ({percentIn}, {percentEx})')
                                logger.info('=' * 50)
                            
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
                                    
                                # save data
                                # try:
                                #     with open('dataCycle.txt', mode = 'w') as f:
                                #         for nCycleNum, (t, lstData) in self.dicDataCycle.items():
                                #             for data in lstData:
                                #                 f.write(f'{nCycleNum}, {t}, {data}\n')
                                # except Exception as msg:
                                #     print(msg)
                                
                            self.dicDataCycle[nCycle] = {}
                        
        logger.info(f"Breathing recording stopped.Total spends:{(curTime - startTime):.3f} sec")
        self.signalResetLaserUI.emit()
        
    def Laser_OnTracking(self):
        if self.Laser is None:
            return
        
        logger.info("即時量測呼吸狀態")
        if self.recordBreathingBase is True:
            self.bLaserTracking = True
            
            # t_laser = threading.Thread(target = self.Laser_FuncLaserTracking)
            t_laser = threading.Thread(target = self.Laser_OnThreadTracking)
            t_laser.start()
        else:
            logger.warning("Please build cheast breathing model first.")
            
    def Laser_OnThreadTracking(self):
        self.avgValueDataTmp = []
        
        while self.bLaserTracking is True:
            self.Laser.RealTimeHeightAvg() #透過計算出即時的HeightAvg, 顯示燈號
            
        # with open('AVG_data.txt', mode='w') as f:
        #     for data in self.avgValueDataTmp:
        #         f.write(f'{data},')
                
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
                logger.critical("Robot Compensation error")
        # else:
        #     self.trackingBreathingCommand = True
    
    def Laser_CheckInhale(self):
        layout = self.wdgIndicatorInhale.layout()
        if layout is None:
            self.indicatorInhale = Indicator(TYPE_INHALE) 
            layout = QVBoxLayout(self.wdgIndicatorInhale)
            layout.addWidget(self.indicatorInhale)
            layout.setContentsMargins(0, 0, 0, 0)
        
        self.tCheckInhale = QTimer()
        self.tCheckInhale.timeout.connect(self.Laser.CheckInhale)
        self.tCheckInhale.start(10)
        
    def Laser_CheckExhale(self):
        layout = self.wdgIndicatorExhale.layout()
        if layout is None:
            self.indicatorExhale = Indicator(TYPE_EXHALE) 
            layout = QVBoxLayout(self.wdgIndicatorExhale)
            layout.addWidget(self.indicatorExhale)
            layout.setContentsMargins(0, 0, 0, 0)
        
        self.tCheckExhale = QTimer()
        self.tCheckExhale.timeout.connect(self.Laser.CheckExhale)
        self.tCheckExhale.start(10)
        
            
    # def Laser_FuncLaserTracking(self):
    #     self.avgValueDataTmp = []
        
    #     while self.bLaserTracking is True:
    #         breathingPercentageTemp = self.Laser.RealTimeHeightAvg(self.yellowLightCriteria, self.greenLightCriteria) #透過計算出即時的HeightAvg, 顯示燈號
            
    #         self.lcdBreathingRatio.display(breathingPercentageTemp)
            
    #         if breathingPercentageTemp is not None:
    #             if self.greenLightCriteria is not None and self.yellowLightCriteria is not None:
    #                 if breathingPercentageTemp >= self.greenLightCriteria:  #綠燈
    #                     self.lcdBreathingRatio.setStyleSheet("#lcdBreathingRatio{border: 2px solid black; color: green; background: silver;}")
    #                 elif breathingPercentageTemp >= self.yellowLightCriteria and breathingPercentageTemp < self.greenLightCriteria: #黃燈
    #                     self.lcdBreathingRatio.setStyleSheet("#lcdBreathingRatio{border: 2px solid black; color: yellow; background: silver;}")
    #                 else:
    #                     self.lcdBreathingRatio.setStyleSheet("#lcdBreathingRatio{border: 2px solid black; color: red; background: silver;}")
                        
    #             # self.laserFigure.update_figure(self.Laser.PlotProfile())
                
    #             self.avgValueDataTmp.append(breathingPercentageTemp)
                
    #             if type(breathingPercentageTemp) is np.float64:
    #                 self.breathingPercentage = breathingPercentageTemp                
    #                 print(self.breathingPercentage)
    #     with open('AVG_data.txt', mode='w') as f:
    #         for data in self.avgValueDataTmp:
    #             f.write(f'{data},')
                
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
            logger.critical(e)
            logger.error("close Laser error")
            
    def Update(pos:np.ndarray = None):
        viewport = MainInterface.viewport
        for view in viewport.values():
            view.Focus()
                
            view.renderer.SetTarget(pos)
            view.ChangeSliceView()
            view.iren.Render()
        
            
#画布控件继承自 matplotlib.backends.backend_qt5agg.FigureCanvasQTAgg 类
class Canvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=3, height=2.5, dpi=100, subplot = '111'):
        # plt.rcParams['figure.facecolor'] = 'r'
        # plt.rcParams['axes.facecolor'] = 'b'
        plt.rcParams['axes.prop_cycle'] = cycler(color=['r', 'g'])
        # plt.rcParams['axes.unicode_minus'] = False
        
        fig = Figure(figsize=(width, height), dpi=dpi) #创建画布,设置宽高，每英寸像素点数
        fig.set_facecolor('#4D84AD')
        fig.subplots_adjust(wspace = 0.4, right = 1)
        
        self.subplot = str(subplot)
        nRow = int(self.subplot[0])
        nCol = int(self.subplot[1])
        # self.axes = fig.add_subplot(subplot)#
        self.line1 = []
        self.line2 = []
        self.axes = []
        
        nIndex = 1
        for row in range(nRow):
            for col in range(nCol):
                strPlotNum = f'{nRow}{nCol}{nIndex}'
                axe = fig.add_subplot(int(strPlotNum))
                axe.set_facecolor('#4D84AD')
                axe.set_ylabel('Lung Volume (mL)')
                
                
                # self.axes.cla()#清除已绘的图形
                # if nIndex == 1:
                line1, line2 = axe.plot([], [], [], [])
                self.line1.append(line1)
                self.line2.append(line2)
                if nIndex == 1:
                    axe.set_xlim([1,640])
                else:
                    axe.set_xlim([1,30])
                    axe.set_xlabel('time (second)')
                    
                axe.set_ylim([-125,-75])
                # else:
                #     self.pointPlot = axe.scatter([], [])
                
                # 在設置tick label之前設置ticks，來免除警告
                axe.set_yticks(axe.get_yticks())
                # 不顯示負號
                axe.set_yticklabels([str((tick + 130) * 100) for tick in axe.get_yticks()])
                self.axes.append(axe)
                nIndex += 1
        
        FigureCanvasQTAgg.__init__(self, fig)#调用基类的初始化函数
        self.setParent(parent)
        FigureCanvasQTAgg.updateGeometry(self)
        
    def Clear(self):
        self.line1 = []
        self.line2 = []
        
        for nIndex, axe in enumerate(self.axes, 1):
            axe.cla()
            axe.set_facecolor('#4D84AD')
            axe.set_ylabel('Lung Volume (mL)')
            if nIndex == 2:
                axe.set_xlabel('time (second)')
            
            
            # self.axes.cla()#清除已绘的图形
            # if nIndex == 1:
            line1, line2 = axe.plot([], [], [], [])
            self.line1.append(line1)
            self.line2.append(line2)
            if nIndex == 1:
                axe.set_xlim([1,640])
            else:
                axe.set_xlim([1,30])
                
            axe.set_ylim([-125,-75])
            # else:
            #     self.pointPlot = axe.scatter([], [])
            
            # 在設置tick label之前設置ticks，來免除警告
            axe.set_yticks(axe.get_yticks())
            # 不顯示負號
            axe.set_yticklabels([str((tick + 130) * 100) for tick in axe.get_yticks()])
            
            self.draw()
        
    def update_figure(self, *receiveData, nIndex = 0):
        # if not hasattr(self, 'line1'):
        
        lenOfData = len(receiveData)
        
        if lenOfData == 1 and nIndex < len(self.line1):
            if len(receiveData[0]) > 0:
                self.line1[nIndex].set_data(range(len(receiveData[0])), receiveData[0])
            
        if lenOfData == 2 and nIndex < len(self.line2):
            if len(receiveData[1]) > 0:
                self.line2[nIndex].set_data(range(len(receiveData[1])), receiveData[1])
                
        if nIndex == 0:
            self.draw()#重新绘制
            
    def DrawData(self, dataX:list, dataY:list, nIndex:int = 0):
        if nIndex < len(self.line2):
            if len(dataX) > 0:
                maxDataX = max(dataX)
                if maxDataX > 25:
                    self.axes[nIndex].set_xlim([0, maxDataX + 5])
            self.line2[nIndex].set_data(dataX, dataY)
            
    
        
class WidgetProcess(QWidget):
    signalPercent = pyqtSignal(float)
    signalFinished = pyqtSignal()
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        
        self.angle = 0
        self.angleStep = 3.6
        self.radius = 100
        self.circleWidth = 10
        self.bFinished = False
        
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
            
class DlgExportLog(QDialog, Ui_dlgExportLog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setupUi(self)
        
        # self.dateEdit.setContextMenuPolicy(Qt.NoContextMenu)
        
        # read log folder
        logPath = os.path.join(os.getcwd(), 'logs')
        lstTime = []
        for _, dirNames, _ in os.walk(logPath):
            for dirName in dirNames:
                try:
                    timeStamp = datetime.strptime(dirName, '%Y-%m-%d')
                    lstTime.append(timeStamp)
                except ValueError:
                    # 忽略非日期的目錄
                    continue
        self.selectedDateFrom = None
        self.selectedDateTo = None
        
        if lstTime:     
            minDate = min(lstTime)
            maxDate = max(lstTime)
                        
            currentDate = minDate
            expectDate = []
            while currentDate <= maxDate:
                if currentDate not in lstTime:
                    expectDate.append(currentDate)
                currentDate += timedelta(days = 1)
            # self.dateEdit.setDate(minDate)
            # self.dateEdit.setMinimumDate(minDate)
            # self.dateEdit.setMaximumDate(maxDate)
            
            self.calendarFrom.setSelectedDate(minDate)
            self.calendarFrom.setMinimumDate(minDate)
            self.calendarFrom.setMaximumDate(maxDate)
            self.calendarFrom.SetExceptDate(expectDate)
            # self.calendarFrom.setHidden(True)
            
            self.calendarTo.setSelectedDate(minDate)
            self.calendarTo.setMinimumDate(minDate)
            self.calendarTo.setMaximumDate(maxDate)
            self.calendarTo.SetExceptDate(expectDate)
            # self.calendarTo.setHidden(True)
            
        self.btnDateFrom.clicked.connect(self.OnClick_btnDateFrom)
        self.btnDateTo.clicked.connect(self.OnClick_btnDateTo)
        self.btnExport.clicked.connect(self.OnClick_btnExport)
            
        self.calendarFrom.signalSetCalendarTime.connect(self.OnSetFromDate)
        self.calendarTo.signalSetCalendarTime.connect(self.OnSetToDate)
        
        self.btnExport.setEnabled(False)
        
    def OnClick_btnDateFrom(self):
        self.calendarFrom.setHidden(False)
        
    def OnClick_btnDateTo(self):
        self.calendarTo.setHidden(False)
        
    def OnClick_btnExport(self):
        currentPath = os.getcwd()
                
        dlg = QFileDialog()
        dlg.setDirectory(currentPath)
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setFilter(QDir.Files)

        lstExportFilepath = []
        
        if dlg.exec_():
            logPath = os.path.join(os.getcwd(), 'logs')
            for _, dirNames, _ in os.walk(logPath):
                for dirName in dirNames:
                    try:
                        t = datetime.strptime(dirName, '%Y-%m-%d')
                        if t >= self.selectedDateFrom and t <= self.selectedDateTo:
                            # path = os.path.join(logPath, dirName)
                            lstExportFilepath.append(dirName)
                            
                    except ValueError:
                        # 忽略非日期的目錄
                        continue
                
            outFilePath = dlg.selectedFiles()[0]
            
            self.pbrProgress.setMaximum(len(lstExportFilepath))
            nValue = 0
            for dirname in lstExportFilepath:
                pathSrc = os.path.join(logPath, dirname)
                pathDst = os.path.join(outFilePath, dirname)
                shutil.copytree(pathSrc, pathDst)
                
                nValue += 1
                self.pbrProgress.setValue(nValue)
            MessageBox.ShowInformation('log export finished')
            self.close()
    def OnSetFromDate(self, date:QDate):
        self.btnDateFrom.setText(f'From:{date.year()}/{date.month()}/{date.day()}')
        
        self.selectedDateFrom = date
        if self.selectedDateTo is not None and self.selectedDateTo < date:
            self.OnSetToDate(date)
            self.calendarTo.setSelectedDate(date)
            
        # self.calendarFrom.setHidden(True)
        if None not in [self.selectedDateFrom, self.selectedDateTo]:
            self.btnExport.setEnabled(True)
        
    def OnSetToDate(self, date:QDate):
        self.btnDateTo.setText(f'To:{date.year()}/{date.month()}/{date.day()}')
        
        self.selectedDateTo = date
        if self.selectedDateFrom is not None and self.selectedDateFrom > date:
            self.OnSetFromDate(date)
            self.calendarFrom.setSelectedDate(date)
        
        # self.calendarTo.setHidden(True)
        if None not in [self.selectedDateFrom, self.selectedDateTo]:
            self.btnExport.setEnabled(True)
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
        
class DlgHintBox(QDialog, FunctionLib_UI.Ui_DlgHintBox.Ui_DlgHintBox):
    signalDontShow = pyqtSignal(bool)
    bShow = True
    stkDialog = []
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setupUi(self)
        
        if len(DlgHintBox.stkDialog) > 0:
            dlg = DlgHintBox.stkDialog.pop(0)
            dlg.close()
            # del dlg
        self.stkDialog.append(self)
        self.alignment = HINT_UP_RIGHT
        self.obj = None
        self.timer = QTimer()
        self.nFlashTime = 0
        self.timer.timeout.connect(self._OnTimerHightlight)
        self.bFlash = False
        self.colorizeEffect = QGraphicsColorizeEffect()
        self.colorizeEffect.setColor(QColor(255, 255, 255))
        self.colorizeEffect.setStrength(0.5)
        
        self.strText = ''
        self.nIndexText = 0
        self.timerText = QTimer()
        self.timerText.timeout.connect(self._OnTimerShowText)
        
        self.lstLabel = []
        self.lstLabel.append(self.lblHintText_URSide)
        self.lstLabel.append(self.lblHintText_ULSide)
        self.lstLabel.append(self.lblHintText_DRSide)
        self.lstLabel.append(self.lblHintText_DLSide)
        
        self.lstCheckBox = []
        self.lstCheckBox.append(self.chbKnown_URSide)
        self.lstCheckBox.append(self.chbKnown_ULSide)
        self.lstCheckBox.append(self.chbKnown_DRSide)
        self.lstCheckBox.append(self.chbKnown_DLSide)
        
        self.lstConfirm = []
        self.lstConfirm.append(self.btnConfirm_URSide)
        self.lstConfirm.append(self.btnConfirm_ULSide)
        self.lstConfirm.append(self.btnConfirm_DRSide)
        self.lstConfirm.append(self.btnConfirm_DLSide)
        
        for i in range(self.stackedWidget.count()):
            self.lstCheckBox[i].toggled.connect(self._CheckDontShow)
            self.lstConfirm[i].clicked.connect(self._OnClickConfirm)
        
        # self.chbKnown_ULSide.toggled.connect(self._CheckDontShow)
        # self.chbKnown_URSide.toggled.connect(self._CheckDontShow)
        # self.chbKnown_DLSide.toggled.connect(self._CheckDontShow)
        # self.chbKnown_DRSide.toggled.connect(self._CheckDontShow)
        # self.btnConfirm_ULSide.clicked.connect(self._OnClickConfirm)
        # self.btnConfirm_URSide.clicked.connect(self._OnClickConfirm)
        # self.btnConfirm_DLSide.clicked.connect(self._OnClickConfirm)
        # self.btnConfirm_DRSide.clicked.connect(self._OnClickConfirm)
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setMinimumSize(600, 300)
        # self.setFixedSize(800, 300)
        
    def closeEvent(self, event: QCloseEvent):
        self.timer.stop()
        self.timerText.stop()
        
        if self.obj is not None:
            self.colorizeEffect.setStrength(0)
            self.obj.setGraphicsEffect(self.colorizeEffect)
            DlgHintBox.stkDialog = []
            self.obj = None
        
        return super().closeEvent(event)
    
    def show(self):
        if DlgHintBox.bShow:
            super().show()
        return DlgHintBox.bShow
    
    def _AdjustSize(self, text:str, pixelSize:int):
        # 注意：此初始值有可能會變，這是根據Qt Designer中顯示的建議長寬所設
        # 因為在dialog使用show()方法前，取得的size會不正確
        # 而不想在調整長寬前，先呯叫一次show()，故把此值設為初始值
        labelWidth  = 500
        labelHeight = 78
        
        font = QFont()
        font.setFamily('Arial')
        font.setPixelSize(pixelSize)
        
        fm = QFontMetrics(font)
        rect = fm.boundingRect(text)
        
        width = max(rect.width() - labelWidth + 10, 0)
        height = max(rect.height() - labelHeight, 0)
        dlgWidth = self.width()
        dlgHeight = self.height()
        
        dlgWidth += width
        dlgHeight += height
        self.setFixedSize(dlgWidth, dlgHeight)
        
    def _CheckDontShow(self, bChecked:bool):
        self.signalDontShow.emit(bChecked)
        DlgHintBox.bShow = not bChecked
        
    def _OnTimerHightlight(self):
        if self.obj is not None:
            if self.nFlashTime >= 10:
                self.nFlashTime = 0
                self.timer.stop()
                self.colorizeEffect.setStrength(0)
                self.obj.setGraphicsEffect(self.colorizeEffect)
            else:
                fStrength = self.bFlash * 0.5
                self.colorizeEffect.setStrength(fStrength)
                self.obj.setGraphicsEffect(self.colorizeEffect)
                self.bFlash = not self.bFlash
                self.nFlashTime += 1
                
    def _OnTimerShowText(self):
        if self.nIndexText >= len(self.strText):
            self.timerText.stop()
            
        text = self.strText[:self.nIndexText]
        
        index = self.stackedWidget.currentIndex()
        self.lstLabel[index].setText(text)
        # if self.stackedWidget.currentWidget() == self.pgURSide:
        #     self.lblHintText_URSide.setText(text)
        # elif self.stackedWidget.currentWidget() == self.pgULSide:
        #     self.lblHintText_ULSide.setText(text)
        # elif self.stackedWidget.currentWidget() == self.pgDRSide:
        #     self.lblHintText_DRSide.setText(text)
        # elif self.stackedWidget.currentWidget() == self.pgDLSide:
        #     self.lblHintText_DLSide.setText(text)
            
        self.nIndexText += 1
        
    def _OnClickConfirm(self):
        # if self.stackedWidget.currentWidget() == self.pgRSide:
        #     self.SetSide('left')
        # else:
        #     self.SetSide('right')
        self.close()
            
    def Replay(self, tDuration:int):
        self.nIndexText = 0
        self.timerText.start(tDuration)
        
        
    def SetSide(self, side:int):
        # if side == HINT_UP_LEFT:
        #     self.lblHintText_ULSide.setText('')
        #     self.stackedWidget.setCurrentWidget(self.pgULSide)
        # elif side == HINT_DOWN_LEFT:
        #     self.lblHintText_DLSide.setText('')
        #     self.stackedWidget.setCurrentWidget(self.pgDLSide)
        # elif side == HINT_DOWN_RIGHT:
        #     self.lblHintText_DRSide.setText('')
        #     self.stackedWidget.setCurrentWidget(self.pgDRSide)
        # else:
        #     self.lblHintText_URSide.setText('')
        #     self.stackedWidget.setCurrentWidget(self.pgURSide)
        self.lstLabel[side].setText('')
        self.stackedWidget.setCurrentIndex(side)
            
        self.alignment = side
        # self.SetPosition(self.obj)
        # self.Replay(100)
            
    def SetText(self, text:str, widget, alignment:int = HINT_UP_RIGHT, pixelSize = 48, tDuration:int = 0):
        """show hint dialog box on the specified widget

        Args:
            text (str): description
            widget (QWidget): dialog position will be on this widget
            alignment (str, optional): dialog alignment, 'right' or 'left'. Defaults to None.
            tDuration (int, optional): Animation duration, minisecond. Defaults to 0.
        """
        
        # if pixelSize is not None:
        pixelSize = min(128, max(pixelSize, 16))
        doc = QTextDocument()
        doc.setHtml(text)
        plainText = doc.toPlainText()
        
        self._AdjustSize(plainText, pixelSize)
        text = f'<span style="font-size:{pixelSize}px">{text}</span>'
        self.strText = text
        
        
        
        self.SetPosition(widget, alignment)
        
        if tDuration > 0:
            self.Replay(tDuration)
        else:
            # if self.stackedWidget.currentWidget() == self.pgURSide:
            #     self.lblHintText_URSide.setText(text)
            # elif self.stackedWidget.currentWidget() == self.pgULSide:
            #     self.lblHintText_ULSide.setText(text)
            # elif self.stackedWidget.currentWidget() == self.pgDLSide:
            #     self.lblHintText_DLSide.setText(text)
            # elif self.stackedWidget.currentWidget() == self.pgDRSide:
            #     self.lblHintText_DRSide.setText(text)
            index = self.stackedWidget.currentIndex()
            self.lstLabel[index].setText(text)

    def SetPosition(self, obj, alignment:int = None, pos:QPoint = QPoint(0, 0)):
        
            
        if isinstance(obj, QWidget):
            self.obj = obj
            self.timer.start(500)
            
            # alignment 如果由參數傳入，代表要指定DlgHintBox的定位點，是在元件的哪個位置
            # 否則將按照DlgHintBox圖案的方向(左側、右側)做預設定位
            
            # if alignment == HINT_UP_RIGHT or alignment == HINT_DOWN_RIGHT:
            #     pos = QPoint(0, obj.height())
            # elif alignment == HINT_UP_LEFT or alignment == HINT_DOWN_LEFT:
            #     pos = QPoint(obj.width(), obj.height())
            # else:
            pos = QPoint(obj.width() // 2, obj.height() // 2)
            pos = obj.mapToGlobal(pos)
            
            screen = QApplication.primaryScreen().availableGeometry()
            width  = screen.width()
            height = screen.height()
            
            if alignment is None:
                if pos.x() < width * 0.5 and pos.y() < height * 0.5:
                    alignment = HINT_UP_LEFT
                elif pos.x() < width * 0.5 and pos.y() > height * 0.5:
                    alignment = HINT_DOWN_LEFT
                elif pos.x() >= width * 0.5 and pos.y() > height * 0.5:
                    alignment = HINT_DOWN_RIGHT
                else:
                    alignment = HINT_UP_RIGHT
                
            self.SetSide(alignment)
                
            if self.alignment == HINT_UP_RIGHT:
                pos.setX(pos.x() - self.width() + 10)
                pos.setY(pos.y() - 10)
            elif self.alignment == HINT_UP_LEFT:
                pos.setX(pos.x() - 15)
                pos.setY(pos.y() - 10)
            elif self.alignment == HINT_DOWN_RIGHT:
                pos.setX(pos.x() - self.width() + 10)
                pos.setY(pos.y() - self.height() + 5)
            elif self.alignment == HINT_DOWN_LEFT:
                pos.setX(pos.x() - 15)
                pos.setY(pos.y() - self.height() + 5)
            
            self.move(pos)
            
    def SetSize(self, width:int, height:int):
        width = max(600, width)
        height = max(300, height)
        self.setFixedSize(width, height)
        
    def Clear():
        for dlg in DlgHintBox.stkDialog:
            dlg.close()
            DlgHintBox.stkDialog = []
            DlgHintBox.bShow = True
        
    def IsShow():
        return DlgHintBox.bShow
        
class DlgInstallAdaptor(QDialog, Ui_dlgInstallAdaptor):
    signalRobotStartMoving = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.player = QMediaPlayer()
        self.player.mediaStatusChanged.connect(self.statusChanged)
        
        self.btnConfirm.setEnabled(True)
        self.btnConfirm.clicked.connect(self.OnClicked_btnConfirm)
        self.btnConfirm_needle.clicked.connect(lambda: self.close())
        self.stkWidget.currentChanged.connect(self.onCurrentChanged)
        self.stkWidget.setCurrentWidget(self.pgDriveRobot)
        self.pgRobotMoving.SetText('Robot Moving...')
        
        
    def statusChanged(self, status):
        if status == QMediaPlayer.EndOfMedia:
            sleep(0.5)
            self.player.play()
            
    def closeEvent(self, event: QCloseEvent):
        self.player.stop()
        return super().closeEvent(event)
    
    def onCurrentChanged(self, index):
        currentWidget = self.stkWidget.currentWidget()
        if currentWidget == self.pgNeedle:
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile('video/patient_needle.mp4')))
            
            videoWidget = QVideoWidget()
            videoWidget.setAspectRatioMode(Qt.KeepAspectRatio)
            self.player.setVideoOutput(videoWidget)
            
            layout = QVBoxLayout(self.wdgPutNeedle)
            layout.addWidget(videoWidget)
            layout.setContentsMargins(0, 0, 0, 0)
            self.player.play()
        elif currentWidget == self.pgRobotMoving:
            QTimer.singleShot(3000, lambda:self.stkWidget.setCurrentWidget(self.pgNeedle))
    
    def OnClicked_btnConfirm(self):
        ret = MessageBox.ShowInformation('This action will move robot, do you sure about that?', 'YES', 'NO')
        QTimer.singleShot(1000, lambda: self.stkWidget.setCurrentWidget(self.pgRobotMoving))
        
        if ret == 0:
            logger.info('robot start to move')
            self.signalRobotStartMoving.emit()
            
    def SetState(self, bEnabled:bool):
        self.btnConfirm.setEnabled(bEnabled)
            
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
    signalClose = pyqtSignal()
    
    def __init__(self, nParts = 1):
        """show loading window"""
        ## 顯示 loading 畫面 ############################################################################################
        self.nParts = max(nParts, 1)
        self.nPartSize = 100 // self.nParts
        self.idPart = 0
        super(SystemProcessing, self).__init__()
        self.setupUi(self)
        ############################################################################################
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
    
    def UpdateProgress(self, value:float, content:str):
        progress = int(value * 100 // self.nParts)
        progress += self.idPart * int(self.nPartSize)
        self.pgbLoadDIcom.setValue(progress)
            
        content = content.replace('\\', '/')
        self.lblContent.setText('from ' + content)
        if progress >= 100:
            self.signalClose.emit()
            self.close()
        self.idPart = progress // self.nPartSize
            
class DlgFootPedal(QDialog, FunctionLib_UI.Ui_DlgFootPedal.Ui_DlgFootPedal):
    signalClose = pyqtSignal()
    
    
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        ############################################################################################
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        size = self.size()
        size.setHeight(size.height() + 80)
        self.setFixedSize(size)
        
        self.action = ACTION_NONE
        self.bAutoClose = True
        self.alpha = 255
        self.bPress = False
        self.increment = -20
        self.timer = QTimer()
        self.timer.timeout.connect(self.runContentText)
        self.timer.start(50)
        
        self.btnConfirm.clicked.connect(self.OnClick_btnConfirm)
        self.btnConfirm.setEnabled(False)
        
        self.lblContent.setText('<span style="font-size:64px">...Please press foot pedal...</span>')
    
    def runContentText(self):
        if self.bPress == False:
            self.lblContent.setStyleSheet(f'color:rgba(255, 255, 0, {self.alpha})')
        self.alpha += self.increment
        self.alpha = min(255, max(self.alpha, 0))
        
        if self.alpha == 255 or self.alpha == 0:
            self.increment *= -1
            
    def SetAction(self, idAction:int):
        if idAction in range(NUM_OF_ACTION):            
            self.action = idAction
            
            if idAction == ACTION_POSITION_ROBOT:
                self.SetAutoClose(False)
                self.SetPressImage('entry_mark.jpg')
                self.SetText('Keep pressing pedal and <span style="color:#ff0000">move robot to entry position</span>')
            
    def SetAutoClose(self, bEnabled:bool = True):
        self.bAutoClose = bEnabled
    
    
    def SetPress(self, bPress:bool):
        if self.bAutoClose and bPress == False:
            self.OnClick_btnConfirm()
        else:
            if bPress:
                # self.lblContent.setText('<span style="font-size:48px">...Unlocked, move robot arm by hand...</span>')
                self.wdgPicture.setCurrentWidget(self.pgPedalPress)
                self.btnConfirm.setEnabled(False)
            else:
                # self.lblContent.setText('<span style="font-size:64px">...Please press foot pedal...</span>')
                self.wdgPicture.setCurrentWidget(self.pgPedal)
                self.btnConfirm.setEnabled(True)
            
        self.bPress = bPress
        
    def SetPressImage(self, strImageName:str):
        self.wdgPedalPress.setStyleSheet(f'image:url(image/{strImageName})')
        
    def SetText(self, text:str):
        self.lblDescription.setText(text)
        
    def OnClick_btnConfirm(self):
        self.signalClose.emit()
        self.close()
        
    def GetAction(self):
        return self.action
        
class DlgResumeSupportArm(DlgFootPedal):
    def __init__(self):
        super().__init__()
        
        self.lastValue = None
        
        self.btnConfirm.setHidden(True)
        
        layoutAxis1 = QVBoxLayout(self.wdgIndicatorAxis1)
        layoutAxis1.setContentsMargins(0, 0, 0, 0)
        
        layoutAxis2 = QVBoxLayout(self.wdgIndicatorAxis2)
        layoutAxis2.setContentsMargins(0, 0, 0, 0)
        
        self.indicatorAxis1 = Indicator(TYPE_ROBOTARM)
        self.indicatorAxis2 = Indicator(TYPE_ROBOTARM)
        
        layoutAxis1.addWidget(self.indicatorAxis1)
        layoutAxis2.addWidget(self.indicatorAxis2)
        
    def SetPress(self, bPress:bool):
        
        if bPress:
            self.lblContent.setText('...Unlocked, move robot arm by hand...')
            self.wdgPicture.setCurrentWidget(self.pgSupportArm)
            self.btnConfirm.setEnabled(False)
        else:
            self.lblContent.setText('...Please press foot pedal...')
            self.wdgPicture.setCurrentWidget(self.pgPedal)
            self.btnConfirm.setEnabled(True)
            
        self.bPress = bPress
        
    def SetValue(self, nAxisIndex:int, value, color:QColor):
        if nAxisIndex == 1:
            self.indicatorAxis1.setRawValue(value)
            self.indicatorAxis1.setGreenZone(color)
            
            
            if self.lastValue is not None:
                diff = value - self.lastValue
                # support arm 旋轉方向偏離中心
                if abs(diff) > 50:
                    if value * diff > 0:
                        self.lblHintAxis1.setText('<span style="font-size:48pt">turn another direction</span>')
                    elif value * diff < 0:
                        self.lblHintAxis1.setText('')
                    
                    
        elif nAxisIndex == 2:
            self.indicatorAxis2.setRawValue(value)
            self.indicatorAxis2.setGreenZone(color)
            
            if self.lastValue is not None:
                
                diff = value - self.lastValue
                # support arm 旋轉方向偏離中心
                if abs(diff) > 50:
                    if value * diff > 0:
                        self.lblHintAxis2.setText('<span style="font-size:48pt">turn another direction</font>')
                    elif value * diff < 0:
                        self.lblHintAxis2.setText('')
        
        self.lastValue = value
            
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
        
    def GetStep(self):
        return self.nCurrentStep
        
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
    
class WidgetToolBox(QWidget, Ui_FormToolBar):
    signalSliceUp   = pyqtSignal()
    signalSliceDown = pyqtSignal()
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setupUi(self)
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.btnSliceUp.clicked.connect(lambda:self.signalSliceUp.emit())
        self.btnSliceDown.clicked.connect(lambda:self.signalSliceDown.emit())
        
class widgetFluoroSlider(QWidget, Ui_formSliderFluoroSize):
    signalValueChange = pyqtSignal(int)
    def __init__(self, parent: QWidget):
        super().__init__()
        self.setupUi(self)
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.slider.valueChanged.connect(lambda value:self.signalValueChange.emit(value))
        self.SetPosition(parent)
        
    def SetPosition(self, parent:QWidget):
        width = self.width()
        x = (parent.width() - width) // 2
        pos = QPoint(x, parent.height())
        pos = parent.mapToGlobal(pos)
        
        self.move(pos)
        
    def SetValue(self, value:int):
        self.blockSignals(True)
        self.slider.setValue(value)
        self.blockSignals(False)
        
        
# class CoordinateSystemManual(QWidget, FunctionLib_UI.ui_coordinate_system_manual.Ui_Form, REGISTRATION):
#     def __init__(self, dcmTag, dicom, answer):
#         super(CoordinateSystemManual, self).__init__()
#         self.setupUi(self)
#         self.SetWindow2Center()
        
#         "create VTK"
#         ## 建立 VTK 物件 ############################################################################################
#         self.reader = vtkDICOMImageReader()
        
#         self.actorAxial = vtkImageActor()
        
#         self.windowLevelLookup = vtkWindowLevelLookupTable()
#         self.mapColors = vtkImageMapToColors()
#         self.cameraAxial = vtkCamera()
        
#         self.renderer = vtkRenderer()
        
#         self.actorBallRed = vtkActor()
#         self.actorBallGreen = vtkActor()
#         self.actorBallBlue = vtkActor()
#         ############################################################################################
#         "hint: self.dicomLow = dicomLow = dicom"
#         "hint: self.dcmTagLow = dcmTagLow = dcmTag"
#         self.dcmTag = dcmTag
#         self.dicom = dicom
#         self.answer = answer
        
#         self.Display()
        
#         return
        
#     def Display(self):
#         ## 顯示 ############################################################################################
#         "folderPath"
#         folderDir = self.dcmTag.get("folderDir")
#         "vtk"
#         self.reader.SetDirectoryName(folderDir)
#         self.reader.Update()
        
#         self.iren = self.qvtkWidget_registrtion.GetRenderWindow().GetInteractor()
        
#         self.vtkImage = self.reader.GetOutput()
#         self.vtkImage.SetOrigin(0, 0, 0)
#         self.dicomGrayscaleRange = self.vtkImage.GetScalarRange()
#         self.dicomBoundsRange = self.vtkImage.GetBounds()
#         self.imageDimensions = self.vtkImage.GetDimensions()
#         self.pixel2Mm = self.vtkImage.GetSpacing()
        
#         "ui"
#         self.ScrollBar.setMinimum(1)
#         self.ScrollBar.setMaximum(self.imageDimensions[2]-1)
#         self.ScrollBar.setValue(int((self.imageDimensions[2])/2))
        
#         "vtk"
        
#         self.windowLevelLookup.Build()
#         thresholdValue = int(((self.dicomGrayscaleRange[1] - self.dicomGrayscaleRange[0]) / 6) + self.dicomGrayscaleRange[0])
#         self.windowLevelLookup.SetWindow(abs(thresholdValue*2))
#         self.windowLevelLookup.SetLevel(thresholdValue)
        
#         self.mapColors.SetInputConnection(self.reader.GetOutputPort())
#         self.mapColors.SetLookupTable(self.windowLevelLookup)
#         self.mapColors.Update()
        
#         self.cameraAxial.SetViewUp(0, 1, 0)
#         self.cameraAxial.SetPosition(0, 0, 1)
#         self.cameraAxial.SetFocalPoint(0, 0, 0)
#         self.cameraAxial.ComputeViewPlaneNormal()
#         self.cameraAxial.ParallelProjectionOn()
        
#         self.actorAxial.GetMapper().SetInputConnection(self.mapColors.GetOutputPort())
#         self.actorAxial.SetDisplayExtent(0, self.imageDimensions[0], 0, self.imageDimensions[1], self.ScrollBar.value(), self.ScrollBar.value())
        
#         self.renderer.SetBackground(0, 0, 0)
#         self.renderer.SetBackground(.2, .3, .4)
#         self.renderer.AddActor(self.actorAxial)
#         self.renderer.SetActiveCamera(self.cameraAxial)
#         self.renderer.ResetCamera(self.dicomBoundsRange)
        
#         "show"
#         self.qvtkWidget_registrtion.GetRenderWindow().AddRenderer(self.renderer)
#         self.istyle = CoordinateSystemManualInteractorStyle(self)
#         self.pick_point = self.iren.SetInteractorStyle(self.istyle)
        
#         self.iren.Initialize()
#         self.iren.Start()
#         ############################################################################################
#         return
        
#     def SetWindow2Center(self):
#         ## 視窗置中 ############################################################################################
#         "screen size"
#         screen = QDesktopWidget().screenGeometry()
#         "window size"
#         size = self.geometry()
#         x = (screen.width() - size.width()) // 2
#         y = (screen.height() - size.height()) // 2
#         self.move(x, y)
#         ############################################################################################
#         return
    
#     def ScrollBarChange(self):
#         ## 調整顯示切面 ############################################################################################
#         self.actorAxial.SetDisplayExtent(0, self.imageDimensions[0]-1, 0, self.imageDimensions[1]-1, self.ScrollBar.value(), self.ScrollBar.value())
#             ## 調整是否顯示點 ############################################################################################
#         try:
#             ballRed = self.dcmTag.get("candidateBall")[0]
#             if abs(self.ScrollBar.value()*self.dcmTag.get("pixel2Mm")[2]-ballRed[2]) < self.dicom.radius:
#                 self.renderer.AddActor(self.actorBallRed)
#             else:
#                 self.renderer.RemoveActor(self.actorBallRed)
#             ballGreen = self.dcmTag.get("candidateBall")[0]
#             if abs(self.ScrollBar.value()*self.dcmTag.get("pixel2Mm")[2]-ballGreen[2]) < self.dicom.radius:
#                 self.renderer.AddActor(self.actorBallGreen)
#             else:
#                 self.renderer.RemoveActor(self.actorBallGreen)
#             ballBlue = self.dcmTag.get("candidateBall")[0]
#             if abs(self.ScrollBar.value()*self.dcmTag.get("pixel2Mm")[2]-ballBlue[2]) < self.dicom.radius:
#                 self.renderer.AddActor(self.actorBallBlue)
#             else:
#                 self.renderer.RemoveActor(self.actorBallBlue)
#         except:
#             pass
#             ############################################################################################
#         self.iren.Initialize()
#         self.iren.Start()
#         ############################################################################################
#         return

#     def okAndClose(self):
#         ## 確認後儲存定位球資料 ############################################################################################
#         if np.array(self.dcmTag.get("candidateBall")).shape[0] >= 3:
#             flage, answer = self.GetBallManual(self.dcmTag.get("candidateBall"), self.dcmTag.get("pixel2Mm"), self.answer, self.dcmTag.get("imageTag"))
#             if flage == True:
#                 self.dcmTag.update({"candidateBallVTK": answer})
#                 self.close()
                
#                 "open another ui window to check registration result"
#                 # self.ui_CS = CoordinateSystem(self.dcmTag, self.dicom)
#                 # self.ui_CS.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
#                 # self.ui_CS.show()
#             else:
#                 # QMessageBox.critical(self, "error", "get candidate ball error")
#                 MessageBox.ShowCritical("error", "get candidate ball error")
#                 print('get candidate ball error / SetRegistration_L() error')
                
#             return
#         else:
#             # QMessageBox.information(self, "information", "need to set 3 balls")
#             MessageBox.ShowInformation("information", "need to set 3 balls")
#             return
#         ############################################################################################
#     def Cancel(self):
#         ## 關閉視窗 ############################################################################################
#         self.close()
#         ############################################################################################

# class CoordinateSystemManualInteractorStyle(vtkInteractorStyleTrackballCamera):
#     def __init__(self, setPointWindow):
#         self.setPointWindow = setPointWindow
        
#         self.AddObserver('LeftButtonPressEvent', self.left_button_press_event)
        
#         self.AddObserver('RightButtonPressEvent', self.right_button_press_event)
        
#         return
    
#     def right_button_press_event(self, obj, event):
#         """turn off right button"""
#         ## 關閉右鍵功能 ############################################################################################
#         pass
#         ############################################################################################
#         return
    
    
#     def left_button_press_event(self, obj, event):
#         """Get the location of the click (in window coordinates)"""
#         ## 左鍵點選點 ############################################################################################
#         points = self.GetInteractor().GetEventPosition()
#         picker = vtkCellPicker()
#         picker.Pick(points[0], points[1], 0, self.GetInteractor().FindPokedRenderer(points[0], points[1]))
#         pick_point = picker.GetPickPosition()
#         ############################################################################################
#         ## 儲存點 ############################################################################################
#         if picker.GetCellId() != -1:
#             if np.array(self.setPointWindow.dcmTag.get("candidateBall")).shape[0] >= 3:
#                 # QMessageBox.critical(self.setPointWindow, "error", "there are already selected 3 balls")
#                 MessageBox.ShowCritical(setPointWindow, "error", "there are already selected 3 balls")
#                 return
#             elif np.array(self.setPointWindow.dcmTag.get("candidateBall")).shape[0] == 0:
#                 self.setPointWindow.dcmTag.update({"candidateBall":np.array([np.array(pick_point)])})
#                 flage = 1
#                 print("pick_point - ",flage," : ", pick_point)
#             elif np.array(self.setPointWindow.dcmTag.get("candidateBall")).shape[0] == 1:
#                 tmpPoint = np.insert(self.setPointWindow.dcmTag.get("candidateBall"), 1, pick_point, 0)
#                 self.setPointWindow.dcmTag.update({"candidateBall": tmpPoint})
#                 flage = 2
#                 print("pick_point - ",flage," : ", pick_point)
#             elif np.array(self.setPointWindow.dcmTag.get("candidateBall")).shape[0] == 2:
#                 tmpPoint = np.insert(self.setPointWindow.dcmTag.get("candidateBall"), 2, pick_point, 0)
#                 self.setPointWindow.dcmTag.update({"candidateBall": tmpPoint})
#                 self.setPointWindow.dcmTag.update({"flagecandidateBall": True})
#                 flage = 3
#                 print("pick_point - ",flage," : ", pick_point)
#             else:
#                 print("GetClickedPosition error / Set candidateBall System error / else")
#                 return
#             self.DrawPoint(pick_point, flage)
#         else:
#             print("picker.GetCellId() = -1")
#         ############################################################################################
#         return
    
#     def DrawPoint(self, pick_point, flage):
#         """draw point"""
#         ## 畫點 ############################################################################################
#         radius = 3.5
#         if flage == 1:
#             "red"
#             self.CreateBallRed(pick_point, radius)
#         elif flage == 2:
#             "green"
#             self.CreateBallGreen(pick_point, radius)
#         elif flage == 3:
#             "blue"
#             self.CreateBallBlue(pick_point, radius)
#         ############################################################################################
#         return
    
#     def CreateBallGreen(self, pick_point, radius):
#         ## 建立綠球 ############################################################################################
#         sphereSource = vtkSphereSource()
#         sphereSource.SetCenter(pick_point)
#         sphereSource.SetRadius(radius)
#         sphereSource.SetPhiResolution(100)
#         sphereSource.SetThetaResolution(100)
        
#         mapper = vtkPolyDataMapper()
#         mapper.SetInputConnection(sphereSource.GetOutputPort())
#         self.setPointWindow.actorBallGreen.SetMapper(mapper)
#         self.setPointWindow.actorBallGreen.GetProperty().SetColor(0, 1, 0)
        
#         self.setPointWindow.renderer.AddActor(self.setPointWindow.actorBallGreen)
#         self.setPointWindow.iren.Initialize()
#         self.setPointWindow.iren.Start()
#         ############################################################################################
#         return
    
#     def CreateBallRed(self, pick_point, radius):
#         ## 建立紅球 ############################################################################################
#         sphereSource = vtkSphereSource()
#         sphereSource.SetCenter(pick_point)
#         sphereSource.SetRadius(radius)
#         sphereSource.SetPhiResolution(100)
#         sphereSource.SetThetaResolution(100)
        
#         mapper = vtkPolyDataMapper()
#         mapper.SetInputConnection(sphereSource.GetOutputPort())
#         self.setPointWindow.actorBallRed.SetMapper(mapper)
#         self.setPointWindow.actorBallRed.GetProperty().SetColor(1, 0, 0)
        
#         self.setPointWindow.renderer.AddActor(self.setPointWindow.actorBallRed)
#         self.setPointWindow.iren.Initialize()
#         self.setPointWindow.iren.Start()
#         ############################################################################################
#         return
    
#     def CreateBallBlue(self, pick_point, radius):
#         ## 建立藍球 ############################################################################################
#         sphereSource = vtkSphereSource()
#         sphereSource.SetCenter(pick_point)
#         sphereSource.SetRadius(radius)
#         sphereSource.SetPhiResolution(100)
#         sphereSource.SetThetaResolution(100)
        
#         mapper = vtkPolyDataMapper()
#         mapper.SetInputConnection(sphereSource.GetOutputPort())
#         self.setPointWindow.actorBallBlue.SetMapper(mapper)
#         self.setPointWindow.actorBallBlue.GetProperty().SetColor(0, 0, 1)
        
#         self.setPointWindow.renderer.AddActor(self.setPointWindow.actorBallBlue)
#         self.setPointWindow.iren.Initialize()
#         self.setPointWindow.iren.Start()
#         ############################################################################################
#         return
    
    