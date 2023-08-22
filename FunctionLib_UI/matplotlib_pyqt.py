from fileinput import filename
from turtle import update
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
# from PyQt5.QtGui import QMovie
from FunctionLib_Robot._class import *
from FunctionLib_Robot._subFunction import *
from FunctionLib_Robot.__init__ import *
from FunctionLib_Robot._globalVar import *
# from FunctionLib_Vision._class import SAT
from time import sleep
from datetime import datetime
import sys
import numpy
import math
import cv2
import logging
import threading
import os
import FunctionLib_UI.ui_coordinate_system
import FunctionLib_UI.ui_coordinate_system_manual
import FunctionLib_UI.ui_set_point_system
import FunctionLib_UI.ui_processing
from FunctionLib_UI.ui_matplotlib_pyqt import *
from FunctionLib_Vision._class import *
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
from vtkmodules.vtkRenderingCore import vtkCellPicker
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg


class MainWidget(QMainWindow,Ui_MainWindow, MOTORSUBFUNCTION, LineLaser, SAT):
    def __init__(self, parent = None):
        try:
            """initial main ui
            """       
            super(MainWidget, self).__init__()
            QMainWindow.__init__(self)
            SAT.__init__(self)

            self.setupUi(self)
            self._init_log()
            self._init_ui()
            self.logUI.info('initial UI')

            self.ui = Ui_MainWindow()

            self.dcmFn = DICOM()
            self.regFn = REGISTRATION()
            self.satFn = SAT()
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
            self.dcmTagLow.update({"selectedBall": []})
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
            self.dcmTagHigh.update({"selectedBall": []})
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

            "initialize dcm system accuracy test (SAT)"
            self.dcmTagSAT = {}
            self.dcmTagSAT.update({"ww": 1})
            self.dcmTagSAT.update({"wl": 1})
            "registration ball"
            self.dcmTagSAT.update({"selectedBall": []})
            self.dcmTagSAT.update({"regBall": []})
            self.dcmTagSAT.update({"flageSelectedBall": False})
            "set test point"
            self.dcmTagSAT.update({"selectedTestPoint": []})
            self.dcmTagSAT.update({"flageselectedTestPoint": False})

            self.Slider_WW_L.setMinimum(1)
            self.Slider_WW_L.setMaximum(3071)
            self.Slider_WW_L.setValue(0)
            self.Slider_WW_H.setMinimum(1)
            self.Slider_WW_H.setMaximum(3071)
            self.Slider_WW_H.setValue(0)
            self.Slider_WW_SAT.setMinimum(1)
            self.Slider_WW_SAT.setMaximum(3071)
            self.Slider_WW_SAT.setValue(0)

            self.Slider_WL_L.setMinimum(-1024)
            self.Slider_WL_L.setMaximum(3071)
            self.Slider_WL_L.setValue(0)
            self.Slider_WL_H.setMinimum(-1024)
            self.Slider_WL_H.setMaximum(3071)
            self.Slider_WL_H.setValue(0)
            self.Slider_WL_SAT.setMinimum(-1024)
            self.Slider_WL_SAT.setMaximum(3071)
            self.Slider_WL_SAT.setValue(0)

            self.Slider_WW_L.valueChanged.connect(self.SetWidth_L)
            self.Slider_WL_L.valueChanged.connect(self.SetLevel_L)
            self.Slider_WW_H.valueChanged.connect(self.SetWidth_H)
            self.Slider_WL_H.valueChanged.connect(self.SetLevel_H)
            self.Slider_WW_SAT.valueChanged.connect(self.SetWidth_SAT)
            self.Slider_WL_SAT.valueChanged.connect(self.SetLevel_SAT)

            self.Action_ImportDicom_L.triggered.connect(self.ImportDicom_L)
            self.Action_ImportDicom_H.triggered.connect(self.ImportDicom_H)
            self.Action_ImportDicom_SAT.triggered.connect(self.ImportDicom_SAT)
            self.logUI.debug('initial main UI')
            print('initial main UI')
        except Exception as e:
            print("Initial System Error - UI")
            print(repr(e))
        """"""
        try:
            "robot control initial"
            MOTORSUBFUNCTION.__init__(self)
            global g_homeStatus
            g_homeStatus = False
            self.homeStatus = g_homeStatus
            print('initial main robot control')
        except:
            print("Initial System Error - robot control")
        try:
            "Line Laser initial"
            LineLaser.__init__(self)
            LineLaser.TriggerSetting(self)
            # self.recordBreathingBase = False        
            
            "Laser Button Color Initialization"
            # self.Button_StartLaserDisplay.setStyleSheet("background-color:#DCDCDC")
            # self.Button_StopLaserDisplay.setStyleSheet("background-color:#DCDCDC")
            # self.Button_RecordCycle.setStyleSheet("background-color:#DCDCDC")
            # self.Button_StopRecording.setStyleSheet("background-color:#DCDCDC")
            # self.Button_StartTracking.setStyleSheet("background-color:#DCDCDC")
            # self.Button_StopLaserTracking.setStyleSheet("background-color:#DCDCDC")
            
            "Laser Button Disable Setting"
            self.Button_StartLaserDisplay.setEnabled(True)
            self.Button_StopLaserDisplay.setEnabled(False)
            self.Button_RecordCycle.setEnabled(False)
            self.Button_StopRecording.setEnabled(False)
            self.Button_StartTracking.setEnabled(False)
            self.Button_StopLaserTracking.setEnabled(False)
            self.Button_Accuracy.setEnabled(False)
            
            self.yellowLightCriteria = yellowLightCriteria_LowAccuracy
            self.greenLightCriteria = greenLightCriteria_LowAccuracy
            
            "LCD setting"
            self.breathingRatio.setDecMode()
            print('initial main Line Laser')
        except:
            print("Initial System Error - Line Laser")
        """"""

    def closeEvent(self, event):
        print("close~~~~~~~~")
        try:
            # 移除VTK道具
            # self.irenSagittal_L.RemoveAllViewProps() 
            self.dicomLow.rendererSagittal.RemoveAllViewProps()
            self.dicomLow.rendererCoronal.RemoveAllViewProps()
            self.dicomLow.rendererAxial.RemoveAllViewProps()
            self.dicomLow.renderer3D.RemoveAllViewProps()
            # 關閉VTK交互器
            # self.irenSagittal_L.close()
            self.qvtkWidget_Sagittal_L.close()
            self.qvtkWidget_Coronal_L.close()
            self.qvtkWidget_Axial_L.close()
            self.qvtkWidget_3D_L.close()
            print("remove dicomLow VTk success")
        except Exception as e:
            print(e)
            print("remove dicomLow VTk error")
        try:
            # 移除VTK道具
            self.dicomHigh.rendererSagittal.RemoveAllViewProps()
            self.dicomHigh.rendererCoronal.RemoveAllViewProps()
            self.dicomHigh.rendererAxial.RemoveAllViewProps()
            self.dicomHigh.renderer3D.RemoveAllViewProps()
            # 關閉VTK交互器
            self.qvtkWidget_Sagittal_H.close()
            self.qvtkWidget_Coronal_H.close()
            self.qvtkWidget_Axial_H.close()
            self.qvtkWidget_3D_H.close()
            print("remove dicomHigh VTk success")
        except Exception as e:
            print(e)
            print("remove dicomHigh VTk error")
        try:
            # 接受關閉事件
            event.accept()
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
        print("Stop Breathing Recording")
        
    def Fun_LaserTracking(self):
        while self.trackingBreathingCommand is True:
            breathingPercentageTemp = self.RealTimeHeightAvg(self.yellowLightCriteria, self.greenLightCriteria) #透過計算出即時的HeightAvg, 顯示燈號
            self.breathingRatio.display(breathingPercentageTemp)
            if breathingPercentageTemp >= self.greenLightCriteria:  #綠燈
                self.breathingRatio.setStyleSheet("border: 2px solid black; color: green; background: silver;")
            elif breathingPercentageTemp >= self.yellowLightCriteria and breathingPercentageTemp < self.greenLightCriteria: #黃燈
                self.breathingRatio.setStyleSheet("border: 2px solid black; color: yellow; background: silver;")
            else:
                self.breathingRatio.setStyleSheet("border: 2px solid black; color: red; background: silver;")
            self.laserProfileFigure.update_figure(self.PlotProfile())
            if type(breathingPercentageTemp) is np.float64:
                self.breathingPercentage = breathingPercentageTemp                
                print(self.breathingPercentage)
                
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

    def RobotStepRun(self):
        testBallPosition = self.satFn.TestBall
        testBallSelect = int(self.lineEdit_EnterNumber_SAT.text())-1
        if testBallSelect >= 0 and testBallSelect <= 5:
            selectBallPosition = testBallPosition[testBallSelect]
            calibration = np.array([baseShift_X, baseShift_Y, baseShift_Z])
            entryTestBall = selectBallPosition - calibration
            targetTestBall = selectBallPosition - \
                calibration - np.array([0, 0, -20])
            MOTORSUBFUNCTION.P2P_Manual(
                self, entryTestBall, targetTestBall)
        else:
            print("select target ball is wrong")
            
    def CloseRobotSystem(self):
        MOTORSUBFUNCTION.HomeProcessing(self)
        print("Home processing is done!")
        QMessageBox.information(self, "information", "AitherBot will be closed!")
        os.system("shutdown -s -t 0 ")


    def _init_log(self):
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

    def _init_ui(self):
        "DICOM planning ui disable"
        self.Button_Planning.setEnabled(False)

        "DICOM Low ui disable (turn on after the function is enabled)"
        self.Button_Registration_L.setEnabled(False)
        self.Button_ShowRegistration_L.setEnabled(False)
        self.comboBox_L.setEnabled(False)
        self.Button_SetPoint_L.setEnabled(False)
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
        self.Button_SetPoint_H.setEnabled(False)
        self.Button_ShowPoint_H.setEnabled(False)

        self.Slider_WW_H.setEnabled(False)
        self.Slider_WL_H.setEnabled(False)
        self.SliceSelect_Axial_H.setEnabled(False)
        self.SliceSelect_Sagittal_H.setEnabled(False)
        self.SliceSelect_Coronal_H.setEnabled(False)

        "Navigation Robot ui disable (turn on after the function is enabled)"
        # self.Button_RobotHome.setEnabled(False)
        # self.Button_RobotAutoRun.setEnabled(False)

        "System Accuracy Test ui disable (turn on after the function is enabled)"
        self.Button_Registration_SAT.setEnabled(False)
        self.Button_ShowRegistration_SAT.setEnabled(False)
        self.Button_ShowTestPoint_SAT.setEnabled(False)
        self.Button_Robot2TestPoint.setEnabled(False)

        self.Slider_WW_SAT.setEnabled(False)
        self.Slider_WL_SAT.setEnabled(False)
        self.SliceSelect_Axial_SAT.setEnabled(False)
        self.SliceSelect_Sagittal_SAT.setEnabled(False)
        self.SliceSelect_Coronal_SAT.setEnabled(False)

    def ImportDicom_L(self):
        """load inhale (Low breath) DICOM to get image array and metadata
        """
        self.logUI.info('Import Dicom inhale/_Low')
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
        
        "pydicom stage"
        metadata, metadataSeriesNum, filePathList = self.dcmFn.LoadPath(filePath)
        if metadata == 0 or metadataSeriesNum == 0:
            self.ui_SP.close()
            QMessageBox.critical(self, "error", "please load one DICOM")
            self.logUI.info('not loading one DICOM')
            return
        print("-------------------------------------------------------------------")
        print("load inhale/Low DICOM path:")
        print(filePath)
        print("-------------------------------------------------------------------")
        logStr = 'Load inhale/Low Dicom: ' + filePath
        self.logUI.info(logStr)
        
        "reset VTK"
        if self.dcmTagLow.get("imageTag") != []:
            "render"
            "Sagittal"
            self.dicomLow.rendererSagittal.RemoveActor(self.dicomLow.actorSagittal)
            "Coronal"
            self.dicomLow.rendererCoronal.RemoveActor(self.dicomLow.actorCoronal)
            "Axial"
            self.dicomLow.rendererAxial.RemoveActor(self.dicomLow.actorAxial)
            "3D"
            self.dicomLow.renderer3D.RemoveActor(self.dicomLow.actorSagittal)
            self.dicomLow.renderer3D.RemoveActor(self.dicomLow.actorAxial)
            self.dicomLow.renderer3D.RemoveActor(self.dicomLow.actorCoronal)
            
            self.dicomLow.rendererSagittal.RemoveActor(self.dicomLow.actorPointEntry)
            
            self.irenSagittal_L.Initialize()
            self.irenCoronal_L.Initialize()
            self.irenAxial_L.Initialize()
            self.iren3D_L.Initialize()
            
            self.irenSagittal_L.Start()
            self.irenCoronal_L.Start()
            self.irenAxial_L.Start()
            self.iren3D_L.Start()

        "reset dcm"
        self.dcmTagLow = {}
        self.dcmTagLow.update({"ww": 1})
        self.dcmTagLow.update({"wl": 1})
        self.dcmTagLow.update({"imageTag": []})
        "registration ball"
        self.dcmTagLow.update({"selectedBall": []})
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
        self.Button_SetPoint_L.setEnabled(False)
        self.Button_ShowPoint_L.setEnabled(False)
        # self.Button_RobotHome.setEnabled(False)
        # self.Button_RobotAutoRun.setEnabled(False)

        seriesNumberLabel, dicDICOM, dirDICOM = self.dcmFn.SeriesSort(metadata, metadataSeriesNum, filePathList)
        imageTag, folderDir = self.dcmFn.ReadDicom(seriesNumberLabel, dicDICOM, dirDICOM)
        self.dcmTagLow.update({"imageTag": imageTag})
        image = self.dcmFn.GetImage(self.dcmTagLow.get("imageTag"))
        if image != 0:
            self.dcmTagLow.update({"image": numpy.array(image)})
        else:
            self.ui_SP.close()
            QMessageBox.critical(self, "error", "please load one DICOM")
            self.logUI.warning('fail to get image')
            return

        rescaleSlope = self.dcmTagLow.get("imageTag")[0].RescaleSlope
        rescaleIntercept = self.dcmTagLow.get("imageTag")[0].RescaleIntercept
        self.dcmTagLow.update({"imageHu": numpy.array(self.dcmFn.Transfer2Hu(self.dcmTagLow.get("image"), rescaleSlope, rescaleIntercept))})
        self.dcmTagLow.update({"pixel2Mm": self.dcmFn.GetPixel2Mm(self.dcmTagLow.get("imageTag")[0])})
        self.dcmTagLow.update({"imageHuMm": numpy.array(self.dcmFn.ImgTransfer2Mm(self.dcmTagLow.get("imageHu"), self.dcmTagLow.get("pixel2Mm")))})
        patientPosition = self.dcmTagLow.get("imageTag")[0].PatientPosition
        # if patientPosition == 'HFS':
        #     self.label_dcmL_L_side.setText("Left")
        #     self.label_dcmL_R_side.setText("Right")
        # elif patientPosition == 'HFP':
        #     self.label_dcmL_L_side.setText("Right")
        #     self.label_dcmL_R_side.setText("Left")
        # else:
        #     self.label_dcmL_L_side.setText("error")
        #     self.label_dcmL_R_side.setText("error")

        "VTK stage"
        self.dcmTagLow.update({"folderDir":folderDir})
        imageVTKHu = self.dicomLow.LoadImage(folderDir)
        self.dcmTagLow.update({"imageVTKHu":imageVTKHu})
        self.dicomLow.CreateActorAndRender(128)
        self.irenSagittal_L = self.qvtkWidget_Sagittal_L.GetRenderWindow().GetInteractor()
        self.irenCoronal_L = self.qvtkWidget_Coronal_L.GetRenderWindow().GetInteractor()
        self.irenAxial_L = self.qvtkWidget_Axial_L.GetRenderWindow().GetInteractor()
        self.iren3D_L = self.qvtkWidget_3D_L.GetRenderWindow().GetInteractor()
        
        self.SliceSelect_Sagittal_L.setMinimum(1)
        self.SliceSelect_Sagittal_L.setMaximum(self.dicomLow.imageDimensions[0]-1)
        self.SliceSelect_Sagittal_L.setValue(int((self.dicomLow.imageDimensions[0])/2))
        self.SliceSelect_Coronal_L.setMinimum(1)
        self.SliceSelect_Coronal_L.setMaximum(self.dicomLow.imageDimensions[1]-1)
        self.SliceSelect_Coronal_L.setValue(int((self.dicomLow.imageDimensions[1])/2))
        self.SliceSelect_Axial_L.setMinimum(1)
        self.SliceSelect_Axial_L.setMaximum(self.dicomLow.imageDimensions[2]-1)
        self.SliceSelect_Axial_L.setValue(int((self.dicomLow.imageDimensions[2])/2))

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

        self.logUI.debug('Loaded inhale/Low Dicom')
        self.ShowDicom_L()
        
        "Enable ui"
        self.Slider_WW_L.setEnabled(True)
        self.Slider_WL_L.setEnabled(True)
        self.SliceSelect_Axial_L.setEnabled(True)
        self.SliceSelect_Sagittal_L.setEnabled(True)
        self.SliceSelect_Coronal_L.setEnabled(True)
        self.Button_Registration_L.setEnabled(True)
        self.tabWidget.setCurrentWidget(self.tabWidget_Low)
        
        self.ui_SP.close()
        return

    def ShowDicom_L(self):
        """show low dicom to ui
        """
        self.qvtkWidget_Sagittal_L.GetRenderWindow().AddRenderer(self.dicomLow.rendererSagittal)
        
        self.irenSagittal_L.SetInteractorStyle(MyInteractorStyle(self.dicomLow.rendererSagittal))
        
        self.qvtkWidget_Coronal_L.GetRenderWindow().AddRenderer(self.dicomLow.rendererCoronal)
        self.irenCoronal_L.SetInteractorStyle(MyInteractorStyle(self.dicomLow.rendererCoronal))
        
        self.qvtkWidget_Axial_L.GetRenderWindow().AddRenderer(self.dicomLow.rendererAxial)
        self.irenAxial_L.SetInteractorStyle(MyInteractorStyle(self.dicomLow.rendererAxial))
        
        self.qvtkWidget_3D_L.GetRenderWindow().AddRenderer(self.dicomLow.renderer3D)
        self.iren3D_L.SetInteractorStyle(MyInteractorStyle3D(self.dicomLow.renderer3D))
        
        self.irenSagittal_L.Initialize()
        self.irenCoronal_L.Initialize()
        self.irenAxial_L.Initialize()
        self.iren3D_L.Initialize()
        
        self.irenSagittal_L.Start()
        self.irenCoronal_L.Start()
        self.irenAxial_L.Start()
        self.iren3D_L.Start()

        return
    
    def ScrollBarChangeSagittal_L(self):
        """while ScrollBar Change (Sagittal), update ui plot
        """
        self.dicomLow.ChangeSagittalView(self.SliceSelect_Sagittal_L.value())
        
        if numpy.array(self.dcmTagLow.get("selectedPoint")).shape[0] == 2:
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
        
        self.irenSagittal_L.Initialize()
        self.iren3D_L.Initialize()
        
        self.irenSagittal_L.Start()
        self.iren3D_L.Start()
        
        self.logUI.debug('Show Low Dicom Sagittal')
        
    def ScrollBarChangeCoronal_L(self):
        """while ScrollBar Change (Coronal), update ui plot
        """
        self.dicomLow.ChangeCoronalView(self.SliceSelect_Coronal_L.value())
        
        if numpy.array(self.dcmTagLow.get("selectedPoint")).shape[0] == 2:
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
        
        self.irenCoronal_L.Initialize()
        self.iren3D_L.Initialize()
        
        self.irenCoronal_L.Start()
        self.iren3D_L.Start()
        
        self.logUI.debug('Show Low Dicom Coronal')

    def ScrollBarChangeAxial_L(self):
        """while ScrollBar Change (Axial), update ui plot
        """
        self.dicomLow.ChangeAxialView(self.SliceSelect_Axial_L.value())
        
        if numpy.array(self.dcmTagLow.get("selectedPoint")).shape[0] == 2:
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
        
        self.irenAxial_L.Initialize()
        self.iren3D_L.Initialize()
        
        self.irenAxial_L.Start()
        self.iren3D_L.Start()
        
        self.logUI.debug('Show Low Dicom Axial')

    def SetWidth_L(self):
        """set window width and show changed DICOM to ui
        """
        self.dcmTagLow.update({"ww": int(self.Slider_WW_L.value())})
        
        self.dicomLow.ChangeWindowWidthView(self.Slider_WW_L.value())
        self.irenSagittal_L.Initialize()
        self.irenCoronal_L.Initialize()
        self.irenAxial_L.Initialize()
        self.iren3D_L.Initialize()
        
        self.irenSagittal_L.Start()
        self.irenCoronal_L.Start()
        self.irenAxial_L.Start()
        self.iren3D_L.Start()
        
        self.logUI.debug('Set Low Dicom Window Width')

    def SetLevel_L(self):
        """set window center/level and show changed DICOM to ui
        """
        self.dcmTagLow.update({"wl": int(self.Slider_WL_L.value())})
        
        self.dicomLow.ChangeWindowLevelView(self.Slider_WL_L.value())
        self.irenSagittal_L.Initialize()
        self.irenCoronal_L.Initialize()
        self.irenAxial_L.Initialize()
        self.iren3D_L.Initialize()
        
        self.irenSagittal_L.Start()
        self.irenCoronal_L.Start()
        self.irenAxial_L.Start()
        self.iren3D_L.Start()
        
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
            "render"
            "Sagittal"
            self.dicomHigh.rendererSagittal.RemoveActor(self.dicomHigh.actorSagittal)
            "Coronal"
            self.dicomHigh.rendererCoronal.RemoveActor(self.dicomHigh.actorCoronal)
            "Axial"
            self.dicomHigh.rendererAxial.RemoveActor(self.dicomHigh.actorAxial)
            "3D"
            self.dicomHigh.renderer3D.RemoveActor(self.dicomHigh.actorSagittal)
            self.dicomHigh.renderer3D.RemoveActor(self.dicomHigh.actorAxial)
            self.dicomHigh.renderer3D.RemoveActor(self.dicomHigh.actorCoronal)
            
            self.dicomHigh.rendererSagittal.RemoveActor(self.dicomHigh.actorPointEntry)
            
            self.irenSagittal_H.Initialize()
            self.irenCoronal_H.Initialize()
            self.irenAxial_H.Initialize()
            self.iren3D_H.Initialize()
            
            self.irenSagittal_H.Start()
            self.irenCoronal_H.Start()
            self.irenAxial_H.Start()
            self.iren3D_H.Start()
        
        "reset dcm"
        self.dcmTagHigh = {}
        self.dcmTagHigh.update({"ww": 1})
        self.dcmTagHigh.update({"wl": 1})
        self.dcmTagHigh.update({"imageTag": []})
        "registration ball"
        self.dcmTagHigh.update({"selectedBall": []})
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
        self.Button_SetPoint_H.setEnabled(False)
        self.Button_ShowPoint_H.setEnabled(False)
        # self.Button_RobotHome.setEnabled(False)
        # self.Button_RobotAutoRun.setEnabled(False)

        seriesNumberLabel, dicDICOM, dirDICOM = self.dcmFn.SeriesSort(metadata, metadataSeriesNum, filePathList)
        imageTag, folderDir = self.dcmFn.ReadDicom(seriesNumberLabel, dicDICOM, dirDICOM)
        self.dcmTagHigh.update({"imageTag": imageTag})
        image = self.dcmFn.GetImage(self.dcmTagHigh.get("imageTag"))
        if image != 0:
            self.dcmTagHigh.update({"image": numpy.array(image)})
        else:
            self.ui_SP.close()
            QMessageBox.critical(self, "error", "please load one DICOM")
            self.logUI.warning('fail to get image')
            return

        rescaleSlope = self.dcmTagHigh.get("imageTag")[0].RescaleSlope
        rescaleIntercept = self.dcmTagHigh.get("imageTag")[0].RescaleIntercept
        self.dcmTagHigh.update({"imageHu": numpy.asarray(self.dcmFn.Transfer2Hu(self.dcmTagHigh.get("image"), rescaleSlope, rescaleIntercept))})
        self.dcmTagHigh.update({"pixel2Mm": self.dcmFn.GetPixel2Mm(self.dcmTagHigh.get("imageTag")[0])})
        self.dcmTagHigh.update({"imageHuMm": numpy.array(self.dcmFn.ImgTransfer2Mm(self.dcmTagHigh.get("imageHu"), self.dcmTagHigh.get("pixel2Mm")))})
        patientPosition = self.dcmTagHigh.get("imageTag")[0].PatientPosition
        # if patientPosition == 'HFS':
        #     self.label_dcmH_L_side.setText("Left")
        #     self.label_dcmH_R_side.setText("Right")
        # elif patientPosition == 'HFP':
        #     self.label_dcmH_L_side.setText("Right")
        #     self.label_dcmH_R_side.setText("Left")
        # else:
        #     self.label_dcmH_L_side.setText("error")
        #     self.label_dcmH_R_side.setText("error")

        "VTK stage"
        self.dcmTagHigh.update({"folderDir":folderDir})
        imageVTKHu = self.dicomHigh.LoadImage(folderDir)
        self.dcmTagHigh.update({"imageVTKHu":imageVTKHu})
        self.dicomHigh.CreateActorAndRender(128)
        self.irenSagittal_H = self.qvtkWidget_Sagittal_H.GetRenderWindow().GetInteractor()
        self.irenCoronal_H = self.qvtkWidget_Coronal_H.GetRenderWindow().GetInteractor()
        self.irenAxial_H = self.qvtkWidget_Axial_H.GetRenderWindow().GetInteractor()
        self.iren3D_H = self.qvtkWidget_3D_H.GetRenderWindow().GetInteractor()
        
        self.SliceSelect_Sagittal_H.setMinimum(1)
        self.SliceSelect_Sagittal_H.setMaximum(self.dicomHigh.imageDimensions[0]-1)
        self.SliceSelect_Sagittal_H.setValue(int((self.dicomHigh.imageDimensions[0])/2))
        self.SliceSelect_Coronal_H.setMinimum(1)
        self.SliceSelect_Coronal_H.setMaximum(self.dicomHigh.imageDimensions[1]-1)
        self.SliceSelect_Coronal_H.setValue(int((self.dicomHigh.imageDimensions[1])/2))
        self.SliceSelect_Axial_H.setMinimum(1)
        self.SliceSelect_Axial_H.setMaximum(self.dicomHigh.imageDimensions[2]-1)
        self.SliceSelect_Axial_H.setValue(int((self.dicomHigh.imageDimensions[2])/2))

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
        self.qvtkWidget_Sagittal_H.GetRenderWindow().AddRenderer(self.dicomHigh.rendererSagittal)
        
        self.irenSagittal_H.SetInteractorStyle(MyInteractorStyle(self.dicomHigh.rendererSagittal))
        
        self.qvtkWidget_Coronal_H.GetRenderWindow().AddRenderer(self.dicomHigh.rendererCoronal)
        self.irenCoronal_H.SetInteractorStyle(MyInteractorStyle(self.dicomHigh.rendererCoronal))
        
        self.qvtkWidget_Axial_H.GetRenderWindow().AddRenderer(self.dicomHigh.rendererAxial)
        self.irenAxial_H.SetInteractorStyle(MyInteractorStyle(self.dicomHigh.rendererAxial))
        
        self.qvtkWidget_3D_H.GetRenderWindow().AddRenderer(self.dicomHigh.renderer3D)
        self.iren3D_H.SetInteractorStyle(MyInteractorStyle3D(self.dicomHigh.renderer3D))
        
        self.irenSagittal_H.Initialize()
        self.irenCoronal_H.Initialize()
        self.irenAxial_H.Initialize()
        self.iren3D_H.Initialize()
        
        self.irenSagittal_H.Start()
        self.irenCoronal_H.Start()
        self.irenAxial_H.Start()
        self.iren3D_H.Start()

        return

    def ScrollBarChangeSagittal_H(self):
        """while ScrollBar Change (Sagittal), update ui plot
        """
        self.dicomHigh.ChangeSagittalView(self.SliceSelect_Sagittal_H.value())
        
        if numpy.array(self.dcmTagHigh.get("selectedPoint")).shape[0] == 2:
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
        
        self.irenSagittal_H.Initialize()
        self.iren3D_H.Initialize()
        
        self.irenSagittal_H.Start()
        self.iren3D_H.Start()
        
        self.logUI.debug('Show High Dicom Sagittal')
    
    def ScrollBarChangeCoronal_H(self):
        """while ScrollBar Change (Coronal), update ui plot
        """
        self.dicomHigh.ChangeCoronalView(self.SliceSelect_Coronal_H.value())
        
        if numpy.array(self.dcmTagHigh.get("selectedPoint")).shape[0] == 2:
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
        
        self.irenCoronal_H.Initialize()
        self.iren3D_H.Initialize()
        
        self.irenCoronal_H.Start()
        self.iren3D_H.Start()
        
        self.logUI.debug('Show High Dicom Coronal')
    
    def ScrollBarChangeAxial_H(self):
        """while ScrollBar Change (Axial), update ui plot
        """
        self.dicomHigh.ChangeAxialView(self.SliceSelect_Axial_H.value())
        
        if numpy.array(self.dcmTagHigh.get("selectedPoint")).shape[0] == 2:
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
        
        self.irenAxial_H.Initialize()
        self.iren3D_H.Initialize()
        
        self.irenAxial_H.Start()
        self.iren3D_H.Start()
        
        self.logUI.debug('Show High Dicom Axial')

    def SetWidth_H(self):
        """set window width and show changed DICOM to ui
        """
        self.dcmTagHigh.update({"ww": int(self.Slider_WW_H.value())})
        
        self.dicomHigh.ChangeWindowWidthView(self.Slider_WW_H.value())
        self.irenSagittal_H.Initialize()
        self.irenCoronal_H.Initialize()
        self.irenAxial_H.Initialize()
        self.iren3D_H.Initialize()
        
        self.irenSagittal_H.Start()
        self.irenCoronal_H.Start()
        self.irenAxial_H.Start()
        self.iren3D_H.Start()
        
        self.logUI.debug('Set High Dicom Window Width')

    def SetLevel_H(self):
        """set window center/level and show changed DICOM to ui
        """
        self.dcmTagHigh.update({"wl": int(self.Slider_WL_H.value())})
        
        self.dicomHigh.ChangeWindowLevelView(self.Slider_WL_H.value())
        self.irenSagittal_H.Initialize()
        self.irenCoronal_H.Initialize()
        self.irenAxial_H.Initialize()
        self.iren3D_H.Initialize()
        
        self.irenSagittal_H.Start()
        self.irenCoronal_H.Start()
        self.irenAxial_H.Start()
        self.iren3D_H.Start()
        
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
            if reply == QMessageBox.Yes:
                self.dcmTagLow.update({"selectedBall": []})
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
                self.Button_SetPoint_L.setEnabled(False)
                self.Button_ShowPoint_L.setEnabled(False)
                
                "VTK"
                try:
                    self.dicomLow.RemovePoint()
                    self.irenSagittal_L.Initialize()
                    self.irenCoronal_L.Initialize()
                    self.irenAxial_L.Initialize()
                    self.iren3D_L.Initialize()
                    
                    self.irenSagittal_L.Start()
                    self.irenCoronal_L.Start()
                    self.irenAxial_L.Start()
                    self.iren3D_L.Start()
                except:
                    pass
                
                self.logUI.info('reset selected ball (Low)')
                print("reset selected ball (Low)")
                
                return
            else:
                self.ui_SP.close()
                return
        "automatic find registration ball center"
        try:
            candidateBallVTK = self.regFn.GetBallAuto(self.dcmTagLow.get("imageVTKHu"), self.dcmTagLow.get("pixel2Mm"), self.dcmTagLow.get("imageTag"))
        except:
            self.ui_SP.close()
            self.logUI.warning('get candidate ball error / SetRegistration_L() error')
            QMessageBox.critical(self, "error", "get candidate ball error / SetRegistration_L() error")
            print('get candidate ball error / SetRegistration_L() error')
            return
        if candidateBallVTK != False:
            self.logUI.info('get candidate ball of inhale/Low DICOM in VTK:')
            i = 0
            for key, value in candidateBallVTK.items():
                tmp = str(i) + ": " + str(key) + str(value)
                self.logUI.info(tmp)
                i += 1
            self.dcmTagLow.update({"candidateBallVTK": candidateBallVTK})
            
            "open another ui window to check registration result"
            self.ui_CS = CoordinateSystem(self.dcmTagLow, self.dicomLow)
            self.ui_SP.close()
            self.ui_CS.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.ui_CS.show()
            self.Button_ShowRegistration_L.setEnabled(True)
        else:
            self.ui_SP.close()
            self.logUI.warning('get candidate ball error')
            QMessageBox.critical(self, "error", "get candidate ball error")
            print('get candidate ball error / SetRegistration_L() error')
            
            "Set up the coordinate system manually"
            self.ui_CS = CoordinateSystemManual(self.dcmTagLow, self.dicomLow)
            # self.ui_CS.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.ui_CS.show()
            
            
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
            selectedBallAll = numpy.array(candidateBallVTK.get(tuple(selectedBallKey)))
            selectedBall = selectedBallAll[:,0:3]
            self.dcmTagLow.update({"regBall": selectedBall})
            self.logUI.info('get registration balls of inhale/Low DICOM:')
            for tmp in self.dcmTagLow.get("regBall"):
                self.logUI.info(tmp)
            "calculate error/difference of relative distance"
            error = self.regFn.GetError(self.dcmTagLow.get("regBall"))
            logStr = 'registration error of inhale/Low DICOM (min, max, mean): ' + str(error)
            self.logUI.info(logStr)
            self.label_Error_L.setText('Registration difference: {:.2f} mm'.format(error[2]))
            "calculate transformation matrix"
            regMatrix = self.regFn.TransformationMatrix(self.dcmTagLow.get("regBall"))
            self.logUI.info('get registration matrix of inhale/Low DICOM: ')
            for tmp in regMatrix:
                self.logUI.info(tmp)
            self.dcmTagLow.update({"regMatrix": regMatrix})
            self.Button_SetPoint_L.setEnabled(True)
            self.comboBox_L.setEnabled(True)
        return

    def SetPoint_L(self):
        """set/select entry and target points
        """
        if self.dcmTagLow.get("flageSelectedPoint") == False:
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
        elif self.dcmTagLow.get("flageSelectedPoint") == True:
            reply = QMessageBox.information(self, "information", "already selected points, reset now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
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
            print("-------------------------------------------------------------------")
            
            self.dcmTagLow.update({"flageShowPointButton": True})
            if self.dcmTagLow.get("flageShowPointButton") is True and self.dcmTagHigh.get("flageShowPointButton") is True:
                self.Button_Planning.setEnabled(True)
            
            "VTK"
            pointEntry = self.dcmTagLow.get("selectedPoint")[0]
            pointTarget = self.dcmTagLow.get("selectedPoint")[1]
            
            self.dicomLow.CreatePath(numpy.array([pointEntry, pointTarget]))
            
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
                
            self.irenSagittal_L.Initialize()
            self.irenCoronal_L.Initialize()
            self.irenAxial_L.Initialize()
            self.iren3D_L.Initialize()
            
            self.irenSagittal_L.Start()
            self.irenCoronal_L.Start()
            self.irenAxial_L.Start()
            self.iren3D_L.Start()
            
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
                self.dcmTagHigh.update({"selectedBall": []})
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
                self.Button_SetPoint_H.setEnabled(False)
                self.Button_ShowPoint_H.setEnabled(False)
                
                "VTK"
                try:
                    self.dicomHigh.RemovePoint()
                    self.irenSagittal_L.Initialize()
                    self.irenCoronal_L.Initialize()
                    self.irenAxial_L.Initialize()
                    self.iren3D_L.Initialize()
                    
                    self.irenSagittal_L.Start()
                    self.irenCoronal_L.Start()
                    self.irenAxial_L.Start()
                    self.iren3D_L.Start()
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
            candidateBallVTK = self.regFn.GetBallAuto(self.dcmTagHigh.get("imageVTKHu"), self.dcmTagHigh.get("pixel2Mm"), self.dcmTagHigh.get("imageTag"))
        except:
            self.ui_SP.close()
            self.logUI.warning('get candidate ball error / SetRegistration_H() error')
            QMessageBox.critical(self, "error", "get candidate ball error")
            print('get candidate ball error / SetRegistration_H() error')
            return
        if candidateBallVTK != False:
            self.logUI.info('get candidate ball of exhale/High DICOM in VTK:')
            i = 0
            for key, value in candidateBallVTK.items():
                tmp = str(i) + ": " + str(key) + str(value)
                self.logUI.info(tmp)
                i += 1
            self.dcmTagHigh.update({"candidateBallVTK": candidateBallVTK})
            
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
            selectedBallAll = numpy.array(candidateBallVTK.get(tuple(selectedBallKey)))
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
            self.Button_SetPoint_H.setEnabled(True)
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
            
            self.dicomHigh.CreatePath(numpy.array([pointEntry, pointTarget]))
            
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
        tmpPointLow = numpy.array([[0.0, 0.0, 0.0],[0.0, 0.0, 0.0]])
        tmpPointHigh = numpy.array([[0.0, 0.0, 0.0],[0.0, 0.0, 0.0]])
        tmpPointLow[0] = self.regFn.TransformPointVTK(self.dcmTagLow.get("imageTag"), self.dcmTagLow.get("selectedPoint")[0])
        tmpPointLow[1] = self.regFn.TransformPointVTK(self.dcmTagLow.get("imageTag"), self.dcmTagLow.get("selectedPoint")[1])
        tmpPointHigh[0] = self.regFn.TransformPointVTK(self.dcmTagHigh.get("imageTag"), self.dcmTagHigh.get("selectedPoint")[0])
        tmpPointHigh[1] = self.regFn.TransformPointVTK(self.dcmTagHigh.get("imageTag"), self.dcmTagHigh.get("selectedPoint")[1])
        self.dcmTagLow.update({"PlanningPath":self.regFn.GetPlanningPath(self.dcmTagLow.get("regBall")[0], tmpPointLow, self.dcmTagLow.get("regMatrix"))})
        self.dcmTagHigh.update({"PlanningPath":self.regFn.GetPlanningPath(self.dcmTagHigh.get("regBall")[0], tmpPointHigh, self.dcmTagHigh.get("regMatrix"))})
        try:
            "把兩組PlanningPath合在一起"
            self.PlanningPath = []
            for tmpPoint in self.dcmTagHigh.get("PlanningPath"):
                # self.PlanningPath.append(tmpPoint)
                self.PlanningPath.append(tmpPoint*[1, 1, -1])
            for tmpPoint in self.dcmTagLow.get("PlanningPath"):
                # self.PlanningPath.append(tmpPoint)
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
            
            "VTK"
            self.irenSagittal_L.Initialize()
            self.irenCoronal_L.Initialize()
            self.irenAxial_L.Initialize()
            self.iren3D_L.Initialize()
            
            self.irenSagittal_L.Start()
            self.irenCoronal_L.Start()
            self.irenAxial_L.Start()
            self.iren3D_L.Start()
            
            self.irenSagittal_H.Initialize()
            self.irenCoronal_H.Initialize()
            self.irenAxial_H.Initialize()
            self.iren3D_H.Initialize()
            
            self.irenSagittal_H.Start()
            self.irenCoronal_H.Start()
            self.irenAxial_H.Start()
            self.iren3D_H.Start()
            
        except:
            self.logUI.warning('fail to Set Planning Path / SetPlanningPath() error')
            print("fail to Set Planning Path / SetPlanningPath() error")
            QMessageBox.critical(self, "error", "fail to Set Planning Path")

        return

    def ImportDicom_SAT(self):
        """load system accuracy test (SAT) DICOM to get image array and metadata
        """
        self.logUI.info('Import Dicom system accuracy test (SAT)')
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setFilter(QDir.Files)

        if dlg.exec_():
            filePath = dlg.selectedFiles()[0] + '/'
        else:
            return

        "pydicom stage"
        metadata, metadataSeriesNum, filePathList = self.dcmFn.LoadPath(filePath)
        if metadata == 0 or metadataSeriesNum == 0:
            QMessageBox.critical(self, "error", "please load one DICOM")
            self.logUI.info('not loading one DICOM')
            return
        print("-------------------------------------------------------------------")
        print("load system accuracy test (SAT) DICOM path:")
        print(filePath)
        print("-------------------------------------------------------------------")
        logStr = 'Load system accuracy test (SAT) Dicom: ' + filePath
        self.logUI.info(logStr)

        "reset dcm"
        self.dcmTagSAT = {}
        self.dcmTagSAT.update({"ww": 1})
        self.dcmTagSAT.update({"wl": 1})
        "registration ball"
        self.dcmTagSAT.update({"selectedBall": []})
        self.dcmTagSAT.update({"regBall": []})
        self.dcmTagSAT.update({"flageSelectedBall": False})
        "set test point"
        self.dcmTagSAT.update({"selectedTestPoint": []})
        self.dcmTagSAT.update({"flageselectedTestPoint": False})
        "ui disable"
        self.Button_Registration_SAT.setEnabled(False)
        self.Button_ShowRegistration_SAT.setEnabled(False)
        self.Button_ShowTestPoint_SAT.setEnabled(False)
        self.Button_Robot2TestPoint.setEnabled(False)

        seriesNumberLabel, dicDICOM, dirDICOM = self.dcmFn.SeriesSort(metadata, metadataSeriesNum, filePathList)
        # self.dcmSAT.update({"imageTag": self.dcmFn.ReadDicom(seriesNumberLabel, dicDICOM)})
        imageTag, folderDir = self.dcmFn.ReadDicom(seriesNumberLabel, dicDICOM, dirDICOM)
        self.dcmTagSAT.update({"imageTag": imageTag})
        image = self.dcmFn.GetImage(self.dcmTagSAT.get("imageTag"))
        if image != 0:
            self.dcmTagSAT.update({"image": numpy.array(image)})
        else:
            QMessageBox.critical(self, "error", "please load one DICOM")
            self.logUI.warning('fail to get image')
            return

        rescaleSlope = self.dcmTagSAT.get("imageTag")[0].RescaleSlope
        rescaleIntercept = self.dcmTagSAT.get("imageTag")[0].RescaleIntercept
        self.dcmTagSAT.update({"imageHu": numpy.array(self.dcmFn.Transfer2Hu(self.dcmTagSAT.get("image"), rescaleSlope, rescaleIntercept))})
        self.dcmTagSAT.update({"pixel2Mm": self.dcmFn.GetPixel2Mm(self.dcmTagSAT.get("imageTag")[0])})
        self.dcmTagSAT.update({"imageHuMm": numpy.array(self.dcmFn.ImgTransfer2Mm(self.dcmTagSAT.get("imageHu"), self.dcmTagSAT.get("pixel2Mm")))})
        patientPosition = self.dcmTagSAT.get("imageTag")[0].PatientPosition
        if patientPosition == 'HFS':
            self.label_dcmSAT_L_side.setText("Left")
            self.label_dcmSAT_R_side.setText("Right")
        elif patientPosition == 'HFP':
            self.label_dcmSAT_L_side.setText("Right")
            self.label_dcmSAT_R_side.setText("Left")
        else:
            self.label_dcmSAT_L_side.setText("error")
            self.label_dcmSAT_R_side.setText("error")

        self.SliceSelect_Axial_SAT.setMinimum(0)
        self.SliceSelect_Axial_SAT.setMaximum(self.dcmTagSAT.get("imageHuMm").shape[0]-1)
        self.SliceSelect_Axial_SAT.setValue(int((self.dcmTagSAT.get("imageHuMm").shape[0])/2))
        self.SliceSelect_Sagittal_SAT.setMinimum(0)
        self.SliceSelect_Sagittal_SAT.setMaximum(self.dcmTagSAT.get("imageHuMm").shape[1]-1)
        self.SliceSelect_Sagittal_SAT.setValue(int((self.dcmTagSAT.get("imageHuMm").shape[1])/2))
        self.SliceSelect_Coronal_SAT.setMinimum(0)
        self.SliceSelect_Coronal_SAT.setMaximum(self.dcmTagSAT.get("imageHuMm").shape[2]-1)
        self.SliceSelect_Coronal_SAT.setValue(int((self.dcmTagSAT.get("imageHuMm").shape[2])/2))

        max = int(numpy.max(self.dcmTagSAT.get("imageHuMm")))
        min = int(numpy.min(self.dcmTagSAT.get("imageHuMm")))
        "WindowWidth"
        self.Slider_WW_SAT.setMinimum(1)
        self.Slider_WW_SAT.setMaximum(max)
        "WindowCenter / WindowLevel"
        self.Slider_WL_SAT.setMinimum(min)
        self.Slider_WL_SAT.setMaximum(max)
        self.dcmTagSAT.update({"ww": int(self.dcmTagSAT.get("imageTag")[0].WindowWidth[0])})
        self.dcmTagSAT.update({"wl": int(self.dcmTagSAT.get("imageTag")[0].WindowCenter[0])})
        self.Slider_WW_SAT.setValue(self.dcmTagSAT.get("ww"))
        self.Slider_WL_SAT.setValue(self.dcmTagSAT.get("wl"))

        self.logUI.debug('Loaded system accuracy test (SAT) Dicom')
        self.ShowDicom_SAT()

        "enable ui"
        self.Slider_WW_SAT.setEnabled(True)
        self.Slider_WL_SAT.setEnabled(True)
        self.SliceSelect_Axial_SAT.setEnabled(True)
        self.SliceSelect_Sagittal_SAT.setEnabled(True)
        self.SliceSelect_Coronal_SAT.setEnabled(True)
        self.Button_Registration_SAT.setEnabled(True)
        self.tabWidget.setCurrentWidget(self.tabWidget_SystemAccuracy)

        return

    def ShowDicom_SAT(self):
        """show SAT dicom to ui
        """
        imageHu2DAxial = self.dcmTagSAT.get("imageHuMm")[self.SliceSelect_Axial_SAT.value(), :, :]
        imageHu2DAxial_ = self.dcmFn.GetGrayImg(imageHu2DAxial, self.dcmTagSAT.get("ww"), self.dcmTagSAT.get("wl"))
        qimgAxial = self.dcmFn.ReadyQimg(imageHu2DAxial_)
        self.label_Axial_SAT.setPixmap(QPixmap.fromImage(qimgAxial))
        self.logUI.debug('Show Low Dicom Axial')

        imageHu2DSagittal = self.dcmTagSAT.get("imageHuMm")[:, :, self.SliceSelect_Sagittal_SAT.value()]
        imageHu2DSagittal_ = self.dcmFn.GetGrayImg(imageHu2DSagittal, self.dcmTagSAT.get("ww"), self.dcmTagSAT.get("wl"))
        qimgSagittal = self.dcmFn.ReadyQimg(imageHu2DSagittal_)
        self.label_Sagittal_SAT.setPixmap(QPixmap.fromImage(qimgSagittal))
        self.logUI.debug('Show Low Dicom Sagittal')

        imageHu2DCoronal = self.dcmTagSAT.get("imageHuMm")[:, self.SliceSelect_Coronal_SAT.value(), :]
        imageHu2DCoronal_ = self.dcmFn.GetGrayImg(imageHu2DCoronal, self.dcmTagSAT.get("ww"), self.dcmTagSAT.get("wl"))
        qimgCoronal = self.dcmFn.ReadyQimg(imageHu2DCoronal_)
        self.label_Coronal_SAT.setPixmap(QPixmap.fromImage(qimgCoronal))
        self.logUI.debug('Show Low Dicom Coronal')

        return

    def ScrollBarChangeAxial_SAT(self):
        """while ScrollBar Change (Axial), update ui plot
        """
        imageHu2DAxial = self.dcmTagSAT.get("imageHuMm")[self.SliceSelect_Axial_SAT.value(), :, :]
        imageHu2DAxial_ = self.dcmFn.GetGrayImg(imageHu2DAxial, self.dcmTagSAT.get("ww"), self.dcmTagSAT.get("wl"))
        qimgAxial = self.dcmFn.ReadyQimg(imageHu2DAxial_)
        self.label_Axial_SAT.setPixmap(QPixmap.fromImage(qimgAxial))
        self.logUI.debug('Show Low Dicom Axial')

    def ScrollBarChangeSagittal_SAT(self):
        """while ScrollBar Change (Sagittal), update ui plot
        """
        imageHu2DSagittal = self.dcmTagSAT.get("imageHuMm")[:, :, self.SliceSelect_Sagittal_SAT.value()]
        imageHu2DSagittal_ = self.dcmFn.GetGrayImg(imageHu2DSagittal, self.dcmTagSAT.get("ww"), self.dcmTagSAT.get("wl"))
        qimgSagittal = self.dcmFn.ReadyQimg(imageHu2DSagittal_)
        self.label_Sagittal_SAT.setPixmap(QPixmap.fromImage(qimgSagittal))
        self.logUI.debug('Show Low Dicom Sagittal')

    def ScrollBarChangeCoronal_SAT(self):
        """while ScrollBar Change (Coronal), update ui plot
        """
        imageHu2DCoronal = self.dcmTagSAT.get("imageHuMm")[:, self.SliceSelect_Coronal_SAT.value(), :]
        imageHu2DCoronal_ = self.dcmFn.GetGrayImg(imageHu2DCoronal, self.dcmTagSAT.get("ww"), self.dcmTagSAT.get("wl"))
        qimgCoronal = self.dcmFn.ReadyQimg(imageHu2DCoronal_)
        self.label_Coronal_SAT.setPixmap(QPixmap.fromImage(qimgCoronal))
        self.logUI.debug('Show Low Dicom Coronal')

    def SetWidth_SAT(self):
        """set window width and show changed DICOM to ui
        """
        self.dcmTagSAT.update({"ww": int(self.Slider_WW_SAT.value())})
        self.ShowDicom_SAT()
        self.logUI.debug('Set Low Dicom Window Width')

    def SetLevel_SAT(self):
        """set window center/level and show changed DICOM to ui
        """
        self.dcmTagSAT.update({"wl": int(self.Slider_WL_SAT.value())})
        self.ShowDicom_SAT()
        self.logUI.debug('Set Low Dicom Window Level')

    def SetRegistration_SAT(self):
        """automatic find registration ball center and test ball center
           + open another ui window to let user selects ball in order (origin -> x axis -> y axis)
        """
        if self.dcmTagSAT.get("regBall") != []:
            reply = QMessageBox.information(self, "information", "already registration, reset now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.dcmTagSAT.update({"selectedBall": []})
                self.dcmTagSAT.update({"regBall": []})
                self.dcmTagSAT.update({"flageSelectedBall": False})
                self.logUI.info('reset selected ball (SAT)')
                print("reset selected ball (SAT)")
                return
            else:
                return

        "automatic find registration ball center"
        try:
            "get/find the center of each ball"
            tmpCandidateBall = self.satFn.GetBall(self.dcmTagSAT.get("imageHuMm"))

            "Group regBalls and test balls"
            groupCandidateBall = self.satFn.GroupBall(tmpCandidateBall)
            for key in groupCandidateBall:
                if groupCandidateBall.get(key).shape[0] == 4:
                    "regBall"
                    candidateBall = groupCandidateBall.get(key)
                elif groupCandidateBall.get(key).shape[0] == 6:
                    "test ball"
                    candidateTestBall = groupCandidateBall.get(key)
        except:
            self.logUI.warning('get candidate ball error')
            QMessageBox.critical(self, "error", "get candidate ball error")
            print('get candidate ball error / SetRegistration_SAT() error')
            return
        self.logUI.info('get candidate ball of SAT DICOM:')
        for tmp in candidateBall:
            self.logUI.info(tmp)
        self.logUI.info('get test ball:')
        for tmp in candidateTestBall:
            self.logUI.info(tmp)
        self.dcmTagSAT.update({"candidateBall": candidateBall})
        self.dcmTagSAT.update({"candidateTestBall": candidateTestBall})

        "open another ui window to let user selects ball in order (origin -> x axis -> y axis)"
        try:
            tmp = self.regFn.GetBallSection(self.dcmTagSAT.get("candidateBall"))
            self.dcmTagSAT.update({"showAxis": tmp[0]})
            self.dcmTagSAT.update({"showSlice": tmp[1]})
            self.ui_CS = CoordinateSystem(self.dcmTagSAT)
            self.ui_CS.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self.ui_CS.show()
            self.Button_ShowRegistration_SAT.setEnabled(True)
        except:
            self.logUI.warning('get candidate ball error / SetRegistration_L() error / candidateBall could be []')
            QMessageBox.critical(self, "error", "get candidate ball error")
            print('get candidate ball error / SetRegistration_L() error / candidateBall could be []')

        return

    def ShowRegistrationDifference_SAT(self):
        """map/pair/match ball center between auto(candidateBall) and manual(selectedBall)
           calculate error/difference of relative distance
        """
        "map/pair/match ball center between auto(candidateBall) and manual(selectedBall)"
        candidateBall = self.dcmTagSAT.get("candidateBall")
        selectedBall = self.dcmTagSAT.get("selectedBall")
        if selectedBall != []:
            flagePair = False
            ball = []
            if self.dcmTagSAT.get("flageSelectedBall") == True:
                self.logUI.info('get selected balls')
                for P1 in selectedBall:
                    for P2 in candidateBall:
                        distance = math.sqrt(numpy.square(P1[0]-P2[0])+numpy.square(P1[1]-P2[1])+numpy.square(P1[2]-P2[2]))
                        if distance < 10:
                            ball.append(P2)
                            break
                if len(ball) == 3:
                    flagePair = True
                else:
                    QMessageBox.critical(self, "error", "please redo registration")
                    self.logUI.warning('find seleted balls error / ShowRegistrationDifference_SAT error')
                    print("find seleted balls error / ShowRegistrationDifference_SAT() error")
                    return
            else:
                QMessageBox.critical(self, "error", "please redo registration")
                print("Choose Point error / ShowRegistrationDifference_SAT() error")
                self.logUI.warning('Choose Point error / ShowRegistrationDifference_SAT() error')
                return

            "calculate error/difference of relative distance"
            if flagePair == True:
                "The ball positions are paired"
                self.dcmTagSAT.update({"regBall": (numpy.array(ball)*[1, 1, -1])})
                self.logUI.info('get registration balls of SAT DICOM:')
                for tmp in self.dcmTagSAT.get("regBall"):
                    self.logUI.info(tmp)
                "calculate error/difference of relative distance"
                error = self.regFn.GetError(self.dcmTagSAT.get("regBall"))
                logStr = 'registration error of SAT DICOM (min, max, mean): ' + str(error)
                self.logUI.info(logStr)
                self.label_RegistrtionError_SAT.setText('Registration difference: {:.2f} mm'.format(error[2]))
                "calculate transformation matrix"
                regMatrix = self.regFn.TransformationMatrix(self.dcmTagSAT.get("regBall"))
                self.logUI.info('get registration matrix of SAT DICOM: ')
                for tmp in regMatrix:
                    self.logUI.info(tmp)
                self.dcmTagSAT.update({"regMatrix": regMatrix})

            else:
                QMessageBox.critical(self, "error", "please redo registration")
                print("pair error / ShowRegistrationDifference_SAT() error")
                self.logUI.warning('pair error / ShowRegistrationDifference_SAT() error')
                return
            self.Button_ShowTestPoint_SAT.setEnabled(True)
            self.Button_Robot2TestPoint.setEnabled(True)
        else:
            QMessageBox.critical(self, "error", "there are not selected 3 balls")
        return

    def ShowTestPoint_SAT(self):
        """show test ball position and save as .jpg and .txt files name with date and time
        """
        tmpBall = self.satFn.SortCandidateTestBall(self.dcmTagSAT.get("candidateTestBall"))
        testBall = self.satFn.GetTestBall(tmpBall, self.dcmTagSAT.get("regBall")[0], self.dcmTagSAT.get("regMatrix"))

        "test ball image result"
        tmpSection = self.regFn.GetBallSection(tmpBall)
        showSlice = tmpSection[1]
        imageHu2DMm = self.dcmTagSAT.get("imageHuMm")[:, showSlice, :]
        gray = numpy.uint8(imageHu2DMm)
        gray3Channel = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        "teat balls position save as .txt"
        fileName = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        with open(str(fileName)+'.txt', 'w') as f:
            f.write("test ball (x,y,z) in the image coordinate system:\n")
        for i in range(tmpBall.shape[0]):
            org = (int(tmpBall[i, 0]), int(tmpBall[i, 2]))
            cv2.putText(gray3Channel, str(i+1), org, cv2.FONT_HERSHEY_COMPLEX, 1, (0, 100, 255), 1)

            with open(str(fileName)+'.txt', 'a') as f:
                f.write(str(tmpBall[i]))
                f.write('\n')

        with open(str(fileName)+'.txt', 'a') as f:
            f.write("\ntest ball (x,y,z) in the regBall coordinate system:\n")
        for p in testBall:
            with open(str(fileName)+'.txt', 'a') as f:
                f.write(str(p))
                f.write("\n")

        "show test ball position in ui"
        cv2.imshow("ball", gray3Channel)

        "teat balls image save as .jpg"
        cv2.imwrite(str(fileName)+'.jpg', gray3Channel)
        return

class CoordinateSystem(QWidget, FunctionLib_UI.ui_coordinate_system.Ui_Form):
    def __init__(self, dcmTag, dicomVTK):
        super(CoordinateSystem, self).__init__()
        self.setupUi(self)
        self.SetWindow2Center()
        
        "create VTK"
        self.reader = vtkDICOMImageReader()
        
        self.windowLevelLookup = vtkWindowLevelLookupTable()
        self.mapColors = vtkImageMapToColors()
        self.camera3D = vtkCamera()
        
        self.renderer3D = vtkRenderer()
        
        self.actorBallRed = vtkActor()
        self.actorBallGreen = vtkActor()
        self.actorBallBlue = vtkActor()

        "hint: self.dcmLow = dcmLow = dcm"
        self.dcmTag = dcmTag
        self.dicomVTK = dicomVTK
        
        "addComboBox"
        tmpKey = []
        
        self.candidateBallVTK = self.dcmTag.get("candidateBallVTK")
        for k in self.candidateBallVTK.keys():
            tmpKey.append(k)
        self.keys = numpy.array(tmpKey)
        
        for i in range(len(self.keys)):
            self.comboBox_label.addItem(str(i+1))
        
        self.comboBox_label.setCurrentIndex(0)
        self.comboBox_label.currentIndexChanged.connect(self.SelectionChange)
        self.SelectionChange(0)
        
        return
    
    def SetWindow2Center(self):
        screen = QDesktopWidget().screenGeometry()  # 螢幕大小
        size = self.geometry()  # 視窗大小
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
        
        return
    
    def SelectionChange(self,i):
        currentKey = self.keys[i,:]
        
        currentValue = numpy.array(self.candidateBallVTK.get(tuple(currentKey)))
        
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
        
        return
    
    def CreateBallRed(self, center, radius):
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
        return
    
    def CreateBallGreen(self, center, radius):
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
        return
    
    def CreateBallBlue(self, center, radius):
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
        return
    
    def DisplayImage(self, value):
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
        
        return
        
    # def UpdateImage(self):
    #     "update and display ui"
    #     bytesPerline = 3 * self.imgWidth
    #     self.qimg = QImage(self.gray3Channel, self.imgWidth, self.imgHeight, bytesPerline, QImage.Format_RGB888).rgbSwapped()
    #     self.label_img.setPixmap(QPixmap.fromImage(self.qimg))
    #     "GetClickedPosition don't +()), it could create error below: "
    #     "TypeError: GetClickedPosition() missing 1 required positional argument: 'event'"
    #     self.label_img.mousePressEvent = self.GetClickedPosition
    #     return

    # def GetClickedPosition(self, event):
    #     showAxis = self.dcm.get("showAxis")
    #     showSlice = self.dcm.get("showSlice")
    #     x = event.pos().x()
    #     y = event.pos().y()
    #     self.flage = self.flage + 1
    #     if self.flage > 3:
    #         QMessageBox.critical(self, "error", "there are already selected 3 balls")
    #         return
    #     else:
    #         if showAxis == 0:
    #             "x axis"
    #             self.point.append([showSlice, x, y])
    #             self.label_origin.setText(f"(x, y, z) = ({showSlice}, {x}, {y})")
    #         elif showAxis == 1:
    #             "y axis"
    #             self.point.append([x, showSlice, y])
    #             self.label_origin.setText(f"(x, y, z) = ({x}, {showSlice}, {y})")
    #         elif showAxis == 2:
    #             "z axis"
    #             self.point.append([x, y, showSlice])
    #             self.label_origin.setText(f"(x, y, z) = ({x}, {y}, {showSlice})")
    #         else:
    #             print("Coordinate System error")
    #     self.drawPoint(x, y)
    #     self.UpdateImage()
    #     return

    # def drawPoint(self, x, y):
    #     "red"
    #     color = (0, 0, 255)
    #     point = (int(x), int(y))
    #     point_size = 1
    #     thickness = 4
    #     cv2.circle(self.gray3Channel, point, point_size, color, thickness)
    #     return

    def okAndClose(self):
        selectLabel = self.comboBox_label.currentText()
        selectKey = self.keys[int(selectLabel)-1,:]
        # selectValue = self.candidateBall.get(tuple(selectKey))
        selectValue = self.candidateBallVTK.get(tuple(selectKey))
        print("-------------------------------------------------------------------")
        print("selectLabel = ", selectLabel, ", \nkey = ", selectKey, ", \nvalue = ", selectValue)
        print("-------------------------------------------------------------------")
        self.dcmTag.update({"selectedBallKey":selectKey})
        
        self.close()
        return

    def Cancel(self):
        self.close()

class CoordinateSystemManual(QWidget, FunctionLib_UI.ui_coordinate_system_manual.Ui_Form, REGISTRATION):
    def __init__(self, dcmTag, dicomVTK):
        super(CoordinateSystemManual, self).__init__()
        self.setupUi(self)
        self.SetWindow2Center()
        
        "create VTK"
        self.reader = vtkDICOMImageReader()
        
        self.actorAxial = vtkImageActor()
        
        self.windowLevelLookup = vtkWindowLevelLookupTable()
        self.mapColors = vtkImageMapToColors()
        self.cameraAxial = vtkCamera()
        
        self.renderer = vtkRenderer()
        
        
        
        

        "hint: self.dcmLow = dcmLow = dcm"
        self.dcmTag = dcmTag
        self.dicomVTK = dicomVTK
        
        self.Display()
        
        return
        
    def Display(self):
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
        # self.iren.SetInteractorStyle(CoordinateSystemManualInteractorStyle(self))
        # self.istyle = CoordinateSystemManualInteractorStyle(self)
        # self.iren.SetInteractorStyle(self.istyle)
        self.istyle = CoordinateSystemManualInteractorStyle(self)
        self.pick_point = self.iren.SetInteractorStyle(self.istyle)
        
        
        self.iren.Initialize()
        self.iren.Start()
        
        return
        
    def SetWindow2Center(self):
        screen = QDesktopWidget().screenGeometry()  # 螢幕大小
        size = self.geometry()  # 視窗大小
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
        
        return
    
    def ScrollBarChange(self):
        
        self.actorAxial.SetDisplayExtent(0, self.imageDimensions[0]-1, 0, self.imageDimensions[1]-1, self.ScrollBar.value(), self.ScrollBar.value())
        
        self.iren.Initialize()
        self.iren.Start()

    def okAndClose(self):
        
        if numpy.array(self.dcmTag.get("candidateBall")).shape[0] >= 3:
            # print("666666666666")
            # print(self.dcmTag.get("candidateBall"))
            
            self.GetBallManual(self.dcmTag.get("candidateBall"), self.dcmTag.get("imageVTKHu"), self.dcmTag.get("pixel2Mm"), self.reader)
            
            
            self.close()
            return
        else:
            QMessageBox.information(self, "information", "need to set 3 balls")
            return
    
    def Cancel(self):
        self.close()

class CoordinateSystemManualInteractorStyle(vtkInteractorStyleTrackballCamera):
    def __init__(self, setPointWindow):
        self.setPointWindow = setPointWindow
        
        self.actorBallRed = vtkActor()
        self.actorBallGreen = vtkActor()
        self.actorBallBlue = vtkActor()
        
        self.AddObserver('LeftButtonPressEvent', self.left_button_press_event)
        self.AddObserver('RightButtonPressEvent', self.right_button_press_event)
        
        return
    
    def right_button_press_event(self, obj, event):
        """turn off right button"""
        pass
        return
    
    def left_button_press_event(self, obj, event):
        """Get the location of the click (in window coordinates)"""
        points = self.GetInteractor().GetEventPosition()
        
        picker = vtkCellPicker()
        picker.Pick(points[0], points[1], 0, self.GetInteractor().FindPokedRenderer(points[0], points[1]))
        pick_point = picker.GetPickPosition()
        
        if picker.GetCellId() != -1:
            if numpy.array(self.setPointWindow.dcmTag.get("candidateBall")).shape[0] >= 3:
                QMessageBox.critical(self.setPointWindow, "error", "there are already selected 3 balls")
                return
            elif numpy.array(self.setPointWindow.dcmTag.get("candidateBall")).shape[0] == 0:
                self.setPointWindow.dcmTag.update({"candidateBall":numpy.array([numpy.array(pick_point)])})
                flage = 1
                print("pick_point - ",flage," : ", pick_point)
            elif numpy.array(self.setPointWindow.dcmTag.get("candidateBall")).shape[0] == 1:
                tmpPoint = numpy.insert(self.setPointWindow.dcmTag.get("candidateBall"), 1, pick_point, 0)
                self.setPointWindow.dcmTag.update({"candidateBall": tmpPoint})
                flage = 2
                print("pick_point - ",flage," : ", pick_point)
            elif numpy.array(self.setPointWindow.dcmTag.get("candidateBall")).shape[0] == 2:
                tmpPoint = numpy.insert(self.setPointWindow.dcmTag.get("candidateBall"), 2, pick_point, 0)
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
        return
    
    def DrawPoint(self, pick_point, flage):
        """draw point"""
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
            
        return
    
    def CreateBallGreen(self, pick_point, radius):
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
        return
    
    def CreateBallRed(self, pick_point, radius):
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
        return
    
    def CreateBallBlue(self, pick_point, radius):
        sphereSource = vtkSphereSource()
        sphereSource.SetCenter(pick_point)
        sphereSource.SetRadius(radius)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.actorBallBlue.SetMapper(mapper)
        self.actorBallBlue.GetProperty().SetColor(0, 0, 1)
        
        self.setPointWindow.renderer.AddActor(self.actorBallBlue)
        self.setPointWindow.iren.Initialize()
        self.setPointWindow.iren.Start()
        return

class SetPointSystem(QWidget, FunctionLib_UI.ui_set_point_system.Ui_Form):# , DICOM):
    def __init__(self, dcmTag, comboBox, scrollBar):
        super(SetPointSystem, self).__init__()
        self.setupUi(self)

        "hint: self.dcmTagLow = dcmTagLow"
        self.dcmTag = dcmTag
        self.comboBox = comboBox
        if scrollBar < 1:
           self.scrollBar = 1
        else:
            self.scrollBar = scrollBar
        self.DisplayImage()
        self.flage = 0

    def DisplayImage(self):
        self.pixel2Mm = self.dcmTag.get("pixel2Mm")
        showSection = self.comboBox
        ww = self.dcmTag.get("ww")
        wl = self.dcmTag.get("wl")

        self.dicom_dir = self.dcmTag.get("folderDir")
        self.reader = vtkDICOMImageReader()
        self.reader.SetDirectoryName(self.dicom_dir)
        self.reader.Update()
        
        self.vtkImage = self.reader.GetOutput()
        self.vtkImage.SetOrigin(0, 0, 0)
        self.imageDimensions = self.vtkImage.GetDimensions()
        
        windowLevelLookup = vtkWindowLevelLookupTable()
        windowLevelLookup.Build()
        windowLevelLookup.SetWindow(ww)
        windowLevelLookup.SetLevel(wl)

        self.mapColors = vtkImageMapToColors()
        self.mapColors.SetInputConnection(self.reader.GetOutputPort())
        self.mapColors.SetLookupTable(windowLevelLookup)
        self.mapColors.Update()
        
        self.actor = vtkImageActor()
        self.actor.GetMapper().SetInputConnection(self.mapColors.GetOutputPort())
        
        self.renderer = vtkRenderer()
        # self.renderer.SetBackground(.2, .3, .4)
        
        if showSection == "Axial":
            self.cameraAxial = vtkCamera()
            self.cameraAxial.SetViewUp(0, 1, 0)
            self.cameraAxial.SetPosition(0, 0, 1)
            self.cameraAxial.SetFocalPoint(0, 0, 0)
            self.cameraAxial.ComputeViewPlaneNormal()
            self.cameraAxial.ParallelProjectionOn()
            
            self.actor.SetDisplayExtent(0, self.imageDimensions[0], 0, self.imageDimensions[1], int(self.scrollBar), int(self.scrollBar))
            
            self.renderer.AddActor(self.actor)
            self.renderer.SetActiveCamera(self.cameraAxial)
        elif showSection == "Coronal":
            self.cameraCoronal = vtkCamera()
            self.cameraCoronal.SetViewUp(0, 0, -1)
            self.cameraCoronal.SetPosition(0, 1, 0)
            self.cameraCoronal.SetFocalPoint(0, 0, 0)
            self.cameraCoronal.ComputeViewPlaneNormal()
            self.cameraCoronal.ParallelProjectionOn()
            
            self.actor.SetDisplayExtent(0, self.imageDimensions[0], int(self.scrollBar), int(self.scrollBar), 0, self.imageDimensions[2])
            
            self.renderer.AddActor(self.actor)
            self.renderer.SetActiveCamera(self.cameraCoronal)
        elif showSection == "Sagittal":
            self.cameraSagittal = vtkCamera()
            self.cameraSagittal.SetViewUp(0, 0, -1)
            self.cameraSagittal.SetPosition(1, 0, 0)
            self.cameraSagittal.SetFocalPoint(0, 0, 0)
            self.cameraSagittal.ComputeViewPlaneNormal()
            self.cameraSagittal.ParallelProjectionOn()
            
            self.actor.SetDisplayExtent(int(self.scrollBar), int(self.scrollBar), 0, self.imageDimensions[1], 0, self.imageDimensions[2])
            
            self.renderer.AddActor(self.actor)
            self.renderer.SetActiveCamera(self.cameraSagittal)
        else:
            print("DisplayImage error / Set Point System error")
            return
            
        self.renderer.ResetCamera()
        self.qvtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.iren = self.qvtkWidget.GetRenderWindow().GetInteractor()
        self.istyle = SetPointInteractorStyle(self)
        self.pick_point = self.iren.SetInteractorStyle(self.istyle)

        self.iren.Initialize()
        self.iren.Start()
        
        "save point"
        
        return

    # def UpdateImage(self):
    #     "update and display ui"
    #     bytesPerline = 3 * self.imgWidth
    #     self.qimg = QImage(self.gray3Channel, self.imgWidth, self.imgHeight, bytesPerline, QImage.Format_RGB888).rgbSwapped()
    #     self.label_img.setPixmap(QPixmap.fromImage(self.qimg))
    #     "GetClickedPosition don't + ()), it could create error below: "
    #     "TypeError: GetClickedPosition() missing 1 required positional argument: 'event'"
    #     self.label_img.mousePressEvent = self.GetClickedPosition
    #     return

    # def GetClickedPosition(self, event):
    #     x = event.pos().x()
    #     y = event.pos().y()
    #     showSection = self.comboBox

        # self.flage = self.SavePoints(x, y, showSection, self.scrollBar)
        # if self.flage == 1:
        #     "green"
        #     color = (0, 255, 0)
        #     # self.drawPoint(x, y, color)
        #     # self.UpdateImage()
        # elif self.flage == 2:
        #     "red"
        #     color = (0, 0, 255)
    #         self.drawPoint(x, y, color)
    #         self.UpdateImage()

    # def drawPoint(self, x, y, color):
    #     point = (int(x), int(y))
    #     point_size = 1
    #     thickness = 4
    #     cv2.circle(self.gray3Channel, point, point_size, color, thickness)
    #     return

    # def SavePoints(self, x, y, showSection, showSlice):
    #     if numpy.array(self.dcmTag.get("selectedPoint")).shape[0] >= 2:
    #         QMessageBox.critical(self, "error", "there are already selected 2 points")
    #         return 3
    #     elif numpy.array(self.dcmTag.get("selectedPoint")).shape[0] == 0:
    #         if showSection == "Axial":
    #             self.dcmTag.update({"selectedPoint": numpy.array([numpy.array([x, y, showSlice])])}) #*[1, 1, -1]])})
    #             self.dcmTag.update({"sectionTag":numpy.array([self.comboBox])})
    #             self.label_origin.setText(f"(x, y, z) = ({x}, {y}, {showSlice})")
    #         elif showSection == "Coronal":
    #             self.dcmTag.update({"selectedPoint": numpy.array([numpy.array([x, showSlice, y])])}) #*[1, 1, -1]])})
    #             self.dcmTag.update({"sectionTag":numpy.array([self.comboBox])})
    #             self.label_origin.setText(f"(x, y, z) = ({x}, {showSlice}, {y})")
    #         elif showSection == "Sagittal":
    #             self.dcmTag.update({"selectedPoint": numpy.array([numpy.array([showSlice, x, y])])}) #*[1, 1, -1]])})
    #             self.dcmTag.update({"sectionTag":numpy.array([self.comboBox])})
    #             self.label_origin.setText(f"(x, y, z) = ({showSlice}, {x}, {y})")
    #         else:
    #             print("GetClickedPosition error / Set Point System error / self.dcm.get(\"selectedPoint\").shape[0] == 0")
    #         return 1
    #     elif numpy.array(self.dcmTag.get("selectedPoint")).shape[0] == 1:
    #         if showSection == "Axial":
    #             tmp = numpy.insert(self.dcmTag.get("selectedPoint"), 1, numpy.array([x, y, showSlice]), 0) #*[1, 1, -1], 0)
    #             self.dcmTag.update({"selectedPoint": tmp})
    #             tmpTag = numpy.insert(self.dcmTag.get("sectionTag"),1,self.comboBox)
    #             self.dcmTag.update({"sectionTag":tmpTag})
    #             self.label_origin.setText(f"(x, y, z) = ({x}, {y}, {showSlice})")
    #         elif showSection == "Coronal":
    #             tmp = numpy.insert(self.dcmTag.get("selectedPoint"), 1, numpy.array([x, showSlice, y]), 0) #*[1, 1, -1], 0)
    #             self.dcmTag.update({"selectedPoint": tmp})
    #             tmpTag = numpy.insert(self.dcmTag.get("sectionTag"),1,self.comboBox)
    #             self.dcmTag.update({"sectionTag":tmpTag})
    #             self.label_origin.setText(f"(x, y, z) = ({x}, {showSlice}, {y})")
    #         elif showSection == "Sagittal":
    #             tmp = numpy.insert(self.dcmTag.get("selectedPoint"), 1, numpy.array([showSlice, x, y]), 0) #*[1, 1, -1], 0)
    #             self.dcmTag.update({"selectedPoint": tmp})
    #             tmpTag = numpy.insert(self.dcmTag.get("sectionTag"),1,self.comboBox)
    #             self.dcmTag.update({"sectionTag":tmpTag})
    #             self.label_origin.setText(f"(x, y, z) = ({showSlice}, {x}, {y})")
    #         else:
    #             print("GetClickedPosition error / Set Point System error / self.dcm.get(\"selectedPoint\").shape[0] == 1")
    #         self.dcmTag.update({"flageSelectedPoint": True})
    #         return 2
    #     else:
    #         print("GetClickedPosition error / Set Point System error / else")
    #         return 0

    def okAndClose(self):
        self.close()

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
        points = self.GetInteractor().GetEventPosition()
        
        picker = vtkCellPicker()
        picker.Pick(points[0], points[1], 0, self.GetInteractor().FindPokedRenderer(points[0], points[1]))
        pick_point = picker.GetPickPosition()
        
        if picker.GetCellId() != -1:
            if numpy.array(self.setPointWindow.dcmTag.get("selectedPoint")).shape[0] >= 2:
                QMessageBox.critical(self.setPointWindow, "error", "there are already selected 2 points")
                return
            elif numpy.array(self.setPointWindow.dcmTag.get("selectedPoint")).shape[0] == 0:
                self.setPointWindow.dcmTag.update({"selectedPoint":numpy.array([numpy.array(pick_point)])})
                flage = 1
            elif numpy.array(self.setPointWindow.dcmTag.get("selectedPoint")).shape[0] == 1:
                tmpPoint = numpy.insert(self.setPointWindow.dcmTag.get("selectedPoint"), 1, pick_point, 0)
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
        return pick_point
            
    def DrawPoint(self, pick_point, flage):
        """draw point"""
        radius = 2
        if flage == 1:
            "entry point"
            "green"
            self.CreateBallGreen(pick_point, radius)
        elif flage == 2:
            "target point"
            "red"
            self.CreateBallRed(pick_point, radius)
            
        return
    
    def CreateBallGreen(self, pick_point, radius):
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
        return
    
    def CreateBallRed(self, pick_point, radius):
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
        return
    
class SystemProcessing(QWidget, FunctionLib_UI.ui_processing.Ui_Form):
    def __init__(self):
        """show loading window"""
        super(SystemProcessing, self).__init__()
        self.setupUi(self)
        return

class MyInteractorStyle(vtkInteractorStyleTrackballCamera):
    def __init__(self, renderer = None):
        self.AddObserver('LeftButtonPressEvent', self.left_button_press_event)
        self.AddObserver('RightButtonPressEvent', self.right_button_press_event)
        self.renderer = renderer
        return

    def left_button_press_event(self, obj, event):
        """turn off left button"""
        pass
        return
    
    def right_button_press_event(self, obj, event):
        """turn off right button"""
        pass
        return

class MyInteractorStyle3D(vtkInteractorStyleTrackballCamera):
    def __init__(self, renderer = None):
        self.AddObserver('RightButtonPressEvent', self.right_button_press_event)
        
    def right_button_press_event(self, obj, event):
        """turn off right button"""
        return

#画布控件继承自 matplotlib.backends.backend_qt5agg.FigureCanvasQTAgg 类
class Canvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi) #创建画布,设置宽高，每英寸像素点数
        self.axes = fig.add_subplot(111)#
        FigureCanvasQTAgg.__init__(self, fig)#调用基类的初始化函数
        self.setParent(parent)
        FigureCanvasQTAgg.updateGeometry(self)
        
    def update_figure(self,receiveData):
        self.axes.cla()#清除已绘的图形
        self.axes.set_xlim([1,640])
        self.axes.set_ylim([-125,-65])
        self.axes.set_xticks([])
        self.axes.set_yticks([])
        self.axes.plot(receiveData[0])
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWidget()
    w.show()
    sys.exit(app.exec_())
