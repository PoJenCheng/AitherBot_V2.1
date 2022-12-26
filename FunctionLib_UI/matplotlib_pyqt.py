from fileinput import filename
from turtle import update
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from FunctionLib_Robot._class import *
from FunctionLib_Robot._subFunction import *
from FunctionLib_Robot.__init__ import *
from FunctionLib_Robot._globalVar import *
from time import sleep
import sys
import numpy
import math
import cv2
import logging
import FunctionLib_UI.ui_matplotlib_pyqt
import FunctionLib_UI.ui_coordinate_system
import FunctionLib_UI.ui_set_point_system
import FunctionLib_Vision._class



class MainWidget(QMainWindow, FunctionLib_UI.ui_matplotlib_pyqt.Ui_MainWindow, MOTORSUBFUNCTION):
    def __init__(self):
        """initial main ui
        """
        super(MainWidget, self).__init__()

        self.setupUi(self)
        self._init_log()
        self._init_ui()
        self.logUI.info('initial UI')

        self.ui = FunctionLib_UI.ui_matplotlib_pyqt.Ui_MainWindow()

        self.dcmFn = FunctionLib_Vision._class.DICOM()
        self.regFn = FunctionLib_Vision._class.REGISTRATION()
        self.satFn = FunctionLib_Vision._class.SAT()
        

        self.tabWidget.setCurrentWidget(self.tabWidget_Low)

        "initialize dcm Low"
        self.dcmLow = {}
        self.dcmLow.update({"ww": 1})
        self.dcmLow.update({"wl": 1})
        "registration ball"
        self.dcmLow.update({"selectedBall": []})
        self.dcmLow.update({"regBall": []})
        self.dcmLow.update({"flageSelectedBall": False})
        "set point"
        self.dcmLow.update({"selectedPoint": []})
        self.dcmLow.update({"flageSelectedPoint": False})
        self.dcmLow.update({"flageShowPointButton": False})

        "initialize dcm High"
        self.dcmHigh = {}
        self.dcmHigh.update({"ww": 1})
        self.dcmHigh.update({"wl": 1})
        "registration ball"
        self.dcmHigh.update({"selectedBall": []})
        self.dcmHigh.update({"regBall": []})
        self.dcmHigh.update({"flageSelectedBall": False})
        "set point"
        self.dcmHigh.update({"selectedPoint": []})
        self.dcmHigh.update({"flageSelectedPoint": False})
        self.dcmHigh.update({"flageShowPointButton": False})
        
        "initialize dcm system accuracy test (SAT)"
        self.dcmSAT = {}
        self.dcmSAT.update({"ww": 1})
        self.dcmSAT.update({"wl": 1})
        "registration ball"
        self.dcmSAT.update({"selectedBall": []})
        self.dcmSAT.update({"regBall": []})
        self.dcmSAT.update({"flageSelectedBall": False})
        "set test point"
        self.dcmSAT.update({"selectedTestPoint": []})
        self.dcmSAT.update({"flageselectedTestPoint": False})

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

        self.SliceSelect_Axial_L.valueChanged.connect(self.ScrollBarChangeAxial_L)
        self.SliceSelect_Sagittal_L.valueChanged.connect(self.ScrollBarChangeSagittal_L)
        self.SliceSelect_Coronal_L.valueChanged.connect(self.ScrollBarChangeCoronal_L)
        self.SliceSelect_Axial_H.valueChanged.connect(self.ScrollBarChangeAxial_H)
        self.SliceSelect_Sagittal_H.valueChanged.connect(self.ScrollBarChangeSagittal_H)
        self.SliceSelect_Coronal_H.valueChanged.connect(self.ScrollBarChangeCoronal_H)
        self.SliceSelect_Axial_SAT.valueChanged.connect(self.ScrollBarChangeAxial_SAT)
        self.SliceSelect_Sagittal_SAT.valueChanged.connect(self.ScrollBarChangeSagittal_SAT)
        self.SliceSelect_Coronal_SAT.valueChanged.connect(self.ScrollBarChangeCoronal_SAT)

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

        "robot control initial"
        MOTORSUBFUNCTION.__init__(self)
        global g_homeStatus
        g_homeStatus = False
        self.homeStatus = g_homeStatus

    def HomeProcessing(self):
        MOTORSUBFUNCTION.HomeProcessing(self)
        print("Home processing is done!")
        self.homeStatus = True

    def RobotRun(self):
        if self.homeStatus is True:
            MOTORSUBFUNCTION.P2P(self)
        else:
            print("Please execute home processing first.")

    def _init_log(self):
        self.logUI: logging.Logger = logging.getLogger(name='UI')
        self.logUI.setLevel(logging.DEBUG)
        "set log level"
        # self.log_INFO: logging.Logger = logging.getLogger(name='INFO')
        # self.log_INFO.setLevel(logging.DEBUG)

        handler: logging.StreamHandler = logging.StreamHandler()
        handler: logging.StreamHandler = logging.FileHandler(
            'my.log', 'w', 'utf-8')

        formatter: logging.Formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        self.Button_RobotHome.setEnabled(True)
        self.Button_RobotAutoRun.setEnabled(True)
        # **************** 要記得改成False
        
        "System Accuracy Test ui disable (turn on after the function is enabled)"
        self.Button_Registration_SAT.setEnabled(False)
        self.Button_ShowRegistration_SAT.setEnabled(False)
        self.Button_SelectTestPoint_SAT.setEnabled(False)
        self.lineEdit_CmmTestPoint_SAT.setEnabled(False)
        self.Button_EnterTestPoint_SAT.setEnabled(False)
        self.Button_Robot2TestPoint.setEnabled(False)
        self.lineEdit_CmmStylus_SAT.setEnabled(False)
        self.Button_EnterStylus_SAT.setEnabled(False)
        
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

        metadata, metadataSeriesNum = self.dcmFn.LoadPath(filePath)
        if metadata == 0 or metadataSeriesNum == 0:
            QMessageBox.critical(self, "error", "please load one DICOM")
            self.logUI.info('not loading one DICOM')
            return
        print("-------------------------------------------------------------------")
        print("load inhale/Low DICOM path:")
        print(filePath)
        print("-------------------------------------------------------------------")
        logStr = 'Load inhale/Low Dicom: ' + filePath
        self.logUI.info(logStr)

        "reset dcm"
        self.dcmLow = {}
        self.dcmLow.update({"ww": 1})
        self.dcmLow.update({"wl": 1})
        "registration ball"
        self.dcmLow.update({"selectedBall": []})
        self.dcmLow.update({"regBall": []})
        self.dcmLow.update({"flageSelectedBall": False})
        "set point"
        self.dcmLow.update({"selectedPoint": []})
        self.dcmLow.update({"flageSelectedPoint": False})
        self.dcmLow.update({"flageShowPointButton": False})
        "ui disable"
        self.Button_Planning.setEnabled(False)
        self.Button_Registration_L.setEnabled(False)
        self.Button_ShowRegistration_L.setEnabled(False)
        self.comboBox_L.setEnabled(False)
        self.Button_SetPoint_L.setEnabled(False)
        self.Button_ShowPoint_L.setEnabled(False)
        self.Button_RobotHome.setEnabled(False)
        self.Button_RobotAutoRun.setEnabled(False)

        seriesNumberLabel, dicDICOM = self.dcmFn.SeriesSort(
            metadata, metadataSeriesNum)
        self.dcmLow.update(
            {"imageTag": self.dcmFn.ReadDicom(seriesNumberLabel, dicDICOM)})
        image = self.dcmFn.GetImage(self.dcmLow.get("imageTag"))
        if image != 0:
            self.dcmLow.update({"image": numpy.array(image)})
        else:
            QMessageBox.critical(self, "error", "please load one DICOM")
            self.logUI.warning('fail to get image')
            return

        rescaleSlope = self.dcmLow.get("imageTag")[0].RescaleSlope
        rescaleIntercept = self.dcmLow.get("imageTag")[0].RescaleIntercept
        self.dcmLow.update({"imageHu": numpy.array(self.dcmFn.Transfer2Hu(
            self.dcmLow.get("image"), rescaleSlope, rescaleIntercept))})
        self.dcmLow.update(
            {"pixel2Mm": self.dcmFn.GetPixel2Mm(self.dcmLow.get("imageTag")[0])})
        self.dcmLow.update({"imageHuMm": numpy.array(self.dcmFn.ImgTransfer2Mm(
            self.dcmLow.get("imageHu"), self.dcmLow.get("pixel2Mm")))})
        patientPosition = self.dcmLow.get("imageTag")[0].PatientPosition
        if patientPosition == 'HFS':
            self.label_dcmL_L_side.setText("Left")
            self.label_dcmL_R_side.setText("Right")
        elif patientPosition == 'HFP':
            self.label_dcmL_L_side.setText("Right")
            self.label_dcmL_R_side.setText("Left")
        else:
            self.label_dcmL_L_side.setText("error")
            self.label_dcmL_R_side.setText("error")

        self.SliceSelect_Axial_L.setMinimum(0)
        self.SliceSelect_Axial_L.setMaximum(
            self.dcmLow.get("imageHuMm").shape[0]-1)
        self.SliceSelect_Axial_L.setValue(
            int((self.dcmLow.get("imageHuMm").shape[0])/2))
        self.SliceSelect_Sagittal_L.setMinimum(0)
        self.SliceSelect_Sagittal_L.setMaximum(
            self.dcmLow.get("imageHuMm").shape[1]-1)
        self.SliceSelect_Sagittal_L.setValue(
            int((self.dcmLow.get("imageHuMm").shape[1])/2))
        self.SliceSelect_Coronal_L.setMinimum(0)
        self.SliceSelect_Coronal_L.setMaximum(
            self.dcmLow.get("imageHuMm").shape[2]-1)
        self.SliceSelect_Coronal_L.setValue(
            int((self.dcmLow.get("imageHuMm").shape[2])/2))

        max = int(numpy.max(self.dcmLow.get("imageHuMm")))
        min = int(numpy.min(self.dcmLow.get("imageHuMm")))
        "WindowWidth"
        self.Slider_WW_L.setMinimum(1)
        self.Slider_WW_L.setMaximum(max)
        "WindowCenter / WindowLevel"
        self.Slider_WL_L.setMinimum(min)
        self.Slider_WL_L.setMaximum(max)
        self.dcmLow.update(
            {"ww": int(self.dcmLow.get("imageTag")[0].WindowWidth[0])})
        self.dcmLow.update(
            {"wl": int(self.dcmLow.get("imageTag")[0].WindowCenter[0])})
        self.Slider_WW_L.setValue(self.dcmLow.get("ww"))
        self.Slider_WL_L.setValue(self.dcmLow.get("wl"))

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

    def ShowDicom_L(self):
        """show low dicom to ui
        """
        imageHu2DAxial = self.dcmLow.get(
            "imageHuMm")[self.SliceSelect_Axial_L.value(), :, :]
        imageHu2DAxial_ = self.dcmFn.GetGrayImg(
            imageHu2DAxial, self.dcmLow.get("ww"), self.dcmLow.get("wl"))
        qimgAxial = self.dcmFn.Ready2Qimg(imageHu2DAxial_)
        self.label_Axial_L.setPixmap(QPixmap.fromImage(qimgAxial))
        self.logUI.debug('Show Low Dicom Axial')

        imageHu2DSagittal = self.dcmLow.get(
            "imageHuMm")[:, :, self.SliceSelect_Sagittal_L.value()]
        imageHu2DSagittal_ = self.dcmFn.GetGrayImg(
            imageHu2DSagittal, self.dcmLow.get("ww"), self.dcmLow.get("wl"))
        qimgSagittal = self.dcmFn.Ready2Qimg(imageHu2DSagittal_)
        self.label_Sagittal_L.setPixmap(QPixmap.fromImage(qimgSagittal))
        self.logUI.debug('Show Low Dicom Sagittal')

        imageHu2DCoronal = self.dcmLow.get(
            "imageHuMm")[:, self.SliceSelect_Coronal_L.value(), :]
        imageHu2DCoronal_ = self.dcmFn.GetGrayImg(
            imageHu2DCoronal, self.dcmLow.get("ww"), self.dcmLow.get("wl"))
        qimgCoronal = self.dcmFn.Ready2Qimg(imageHu2DCoronal_)
        self.label_Coronal_L.setPixmap(QPixmap.fromImage(qimgCoronal))
        self.logUI.debug('Show Low Dicom Coronal')

        return

    def ScrollBarChangeAxial_L(self):
        """while ScrollBar Change (Axial), update ui plot
        """
        imageHu2DAxial = self.dcmLow.get(
            "imageHuMm")[self.SliceSelect_Axial_L.value(), :, :]
        imageHu2DAxial_ = self.dcmFn.GetGrayImg(
            imageHu2DAxial, self.dcmLow.get("ww"), self.dcmLow.get("wl"))
        qimgAxial = self.dcmFn.Ready2Qimg(imageHu2DAxial_)
        self.label_Axial_L.setPixmap(QPixmap.fromImage(qimgAxial))
        self.logUI.debug('Show Low Dicom Axial')

    def ScrollBarChangeSagittal_L(self):
        """while ScrollBar Change (Sagittal), update ui plot
        """
        imageHu2DSagittal = self.dcmLow.get(
            "imageHuMm")[:, :, self.SliceSelect_Sagittal_L.value()]
        imageHu2DSagittal_ = self.dcmFn.GetGrayImg(
            imageHu2DSagittal, self.dcmLow.get("ww"), self.dcmLow.get("wl"))
        qimgSagittal = self.dcmFn.Ready2Qimg(imageHu2DSagittal_)
        self.label_Sagittal_L.setPixmap(QPixmap.fromImage(qimgSagittal))
        self.logUI.debug('Show Low Dicom Sagittal')

    def ScrollBarChangeCoronal_L(self):
        """while ScrollBar Change (Coronal), update ui plot
        """
        imageHu2DCoronal = self.dcmLow.get(
            "imageHuMm")[:, self.SliceSelect_Coronal_L.value(), :]
        imageHu2DCoronal_ = self.dcmFn.GetGrayImg(
            imageHu2DCoronal, self.dcmLow.get("ww"), self.dcmLow.get("wl"))
        qimgCoronal = self.dcmFn.Ready2Qimg(imageHu2DCoronal_)
        self.label_Coronal_L.setPixmap(QPixmap.fromImage(qimgCoronal))
        self.logUI.debug('Show Low Dicom Coronal')

    def SetWidth_L(self):
        """set window width and show changed DICOM to ui
        """
        self.dcmLow.update({"ww": int(self.Slider_WW_L.value())})
        self.ShowDicom_L()
        self.logUI.debug('Set Low Dicom Window Width')

    def SetLevel_L(self):
        """set window center/level and show changed DICOM to ui
        """
        self.dcmLow.update({"wl": int(self.Slider_WL_L.value())})
        self.ShowDicom_L()
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

        metadata, metadataSeriesNum = self.dcmFn.LoadPath(filePath)
        if metadata == 0 or metadataSeriesNum == 0:
            QMessageBox.critical(self, "error", "please load one DICOM")
            self.logUI.info('not loading one DICOM')
            return
        print("-------------------------------------------------------------------")
        print("load exhale/High DICOM path:")
        print(filePath)
        print("-------------------------------------------------------------------")
        logStr = 'Load exhale/High Dicom: ' + filePath
        self.logUI.info(logStr)
        
        "reset dcm"
        self.dcmHigh = {}
        self.dcmHigh.update({"ww": 1})
        self.dcmHigh.update({"wl": 1})
        "registration ball"
        self.dcmHigh.update({"selectedBall": []})
        self.dcmHigh.update({"regBall": []})
        self.dcmHigh.update({"flageSelectedBall": False})
        "set point"
        self.dcmHigh.update({"selectedPoint": []})
        self.dcmHigh.update({"flageSelectedPoint": False})
        self.dcmHigh.update({"flageShowPointButton": False})
        "ui disable"
        self.Button_Planning.setEnabled(False)
        self.Button_Registration_H.setEnabled(False)
        self.Button_ShowRegistration_H.setEnabled(False)
        self.comboBox_H.setEnabled(False)
        self.Button_SetPoint_H.setEnabled(False)
        self.Button_ShowPoint_H.setEnabled(False)
        self.Button_RobotHome.setEnabled(False)
        self.Button_RobotAutoRun.setEnabled(False)
        

        seriesNumberLabel, dicDICOM = self.dcmFn.SeriesSort(
            metadata, metadataSeriesNum)
        self.dcmHigh.update(
            {"imageTag": self.dcmFn.ReadDicom(seriesNumberLabel, dicDICOM)})
        image = self.dcmFn.GetImage(self.dcmHigh.get("imageTag"))
        if image != 0:
            self.dcmHigh.update({"image": numpy.array(image)})
        else:
            QMessageBox.critical(self, "error", "please load one DICOM")
            self.logUI.warning('fail to get image')
            return

        rescaleSlope = self.dcmHigh.get("imageTag")[0].RescaleSlope
        rescaleIntercept = self.dcmHigh.get("imageTag")[0].RescaleIntercept
        self.dcmHigh.update({"imageHu": numpy.asarray(self.dcmFn.Transfer2Hu(
            self.dcmHigh.get("image"), rescaleSlope, rescaleIntercept))})
        self.dcmHigh.update(
            {"pixel2Mm": self.dcmFn.GetPixel2Mm(self.dcmHigh.get("imageTag")[0])})
        self.dcmHigh.update({"imageHuMm": numpy.array(self.dcmFn.ImgTransfer2Mm(
            self.dcmHigh.get("imageHu"), self.dcmHigh.get("pixel2Mm")))})
        patientPosition = self.dcmHigh.get("imageTag")[0].PatientPosition
        if patientPosition == 'HFS':
            self.label_dcmH_L_side.setText("Left")
            self.label_dcmH_R_side.setText("Right")
        elif patientPosition == 'HFP':
            self.label_dcmH_L_side.setText("Right")
            self.label_dcmH_R_side.setText("Left")
        else:
            self.label_dcmH_L_side.setText("error")
            self.label_dcmH_R_side.setText("error")

        self.SliceSelect_Axial_H.setMinimum(0)
        self.SliceSelect_Axial_H.setMaximum(
            self.dcmHigh.get("imageHuMm").shape[0]-1)
        self.SliceSelect_Axial_H.setValue(
            int((self.dcmHigh.get("imageHuMm").shape[0])/2))
        self.SliceSelect_Sagittal_H.setMinimum(0)
        self.SliceSelect_Sagittal_H.setMaximum(
            self.dcmHigh.get("imageHuMm").shape[1]-1)
        self.SliceSelect_Sagittal_H.setValue(
            int((self.dcmHigh.get("imageHuMm").shape[1])/2))
        self.SliceSelect_Coronal_H.setMinimum(0)
        self.SliceSelect_Coronal_H.setMaximum(
            self.dcmHigh.get("imageHuMm").shape[2]-1)
        self.SliceSelect_Coronal_H.setValue(
            int((self.dcmHigh.get("imageHuMm").shape[2])/2))

        max = int(numpy.max(self.dcmHigh.get("imageHuMm")))
        min = int(numpy.min(self.dcmHigh.get("imageHuMm")))
        "WindowWidth"
        self.Slider_WW_H.setMinimum(1)
        self.Slider_WW_H.setMaximum(max)
        "WindowCenter / WindowLevel"
        self.Slider_WL_H.setMinimum(min)
        self.Slider_WL_H.setMaximum(max)
        self.dcmHigh.update(
            {"ww": int(self.dcmHigh.get("imageTag")[0].WindowWidth[0])})
        self.dcmHigh.update(
            {"wl": int(self.dcmHigh.get("imageTag")[0].WindowCenter[0])})
        self.Slider_WW_H.setValue(self.dcmHigh.get("ww"))
        self.Slider_WL_H.setValue(self.dcmHigh.get("wl"))

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

    def ShowDicom_H(self):
        """show high dicom to ui
        """
        imageHu2DAxial = self.dcmHigh.get(
            "imageHuMm")[self.SliceSelect_Axial_H.value(), :, :]
        imageHu2DAxial_ = self.dcmFn.GetGrayImg(
            imageHu2DAxial, self.dcmHigh.get("ww"), self.dcmHigh.get("wl"))
        qimgAxial = self.dcmFn.Ready2Qimg(imageHu2DAxial_)
        self.label_Axial_H.setPixmap(QPixmap.fromImage(qimgAxial))
        self.logUI.debug('Show High Dicom Axial')

        imageHu2DSagittal = self.dcmHigh.get(
            "imageHuMm")[:, :, self.SliceSelect_Sagittal_H.value()]
        imageHu2DSagittal_ = self.dcmFn.GetGrayImg(
            imageHu2DSagittal, self.dcmHigh.get("ww"), self.dcmHigh.get("wl"))
        qimgSagittal = self.dcmFn.Ready2Qimg(imageHu2DSagittal_)
        self.label_Sagittal_H.setPixmap(QPixmap.fromImage(qimgSagittal))
        self.logUI.debug('Show High Dicom Sagittal')

        imageHu2DCoronal = self.dcmHigh.get(
            "imageHuMm")[:, self.SliceSelect_Coronal_H.value(), :]
        imageHu2DCoronal_ = self.dcmFn.GetGrayImg(
            imageHu2DCoronal, self.dcmHigh.get("ww"), self.dcmHigh.get("wl"))
        qimgCoronal = self.dcmFn.Ready2Qimg(imageHu2DCoronal_)
        self.label_Coronal_H.setPixmap(QPixmap.fromImage(qimgCoronal))
        self.logUI.debug('Show High Dicom Coronal')

        return

    def ScrollBarChangeAxial_H(self):
        """while ScrollBar Change (Axial), update ui plot
        """
        imageHu2DAxial = self.dcmHigh.get(
            "imageHuMm")[self.SliceSelect_Axial_H.value(), :, :]
        imageHu2DAxial_ = self.dcmFn.GetGrayImg(
            imageHu2DAxial, self.dcmHigh.get("ww"), self.dcmHigh.get("wl"))
        qimgAxial = self.dcmFn.Ready2Qimg(imageHu2DAxial_)
        self.label_Axial_H.setPixmap(QPixmap.fromImage(qimgAxial))
        self.logUI.debug('Show High Dicom Axial')

    def ScrollBarChangeSagittal_H(self):
        """while ScrollBar Change (Sagittal), update ui plot
        """
        imageHu2DSagittal = self.dcmHigh.get(
            "imageHuMm")[:, :, self.SliceSelect_Sagittal_H.value()]
        imageHu2DSagittal_ = self.dcmFn.GetGrayImg(
            imageHu2DSagittal, self.dcmHigh.get("ww"), self.dcmHigh.get("wl"))
        qimgSagittal = self.dcmFn.Ready2Qimg(imageHu2DSagittal_)
        self.label_Sagittal_H.setPixmap(QPixmap.fromImage(qimgSagittal))
        self.logUI.debug('Show High Dicom Sagittal')

    def ScrollBarChangeCoronal_H(self):
        """while ScrollBar Change (Coronal), update ui plot
        """
        imageHu2DCoronal = self.dcmHigh.get(
            "imageHuMm")[:, self.SliceSelect_Coronal_H.value(), :]
        imageHu2DCoronal_ = self.dcmFn.GetGrayImg(
            imageHu2DCoronal, self.dcmHigh.get("ww"), self.dcmHigh.get("wl"))
        qimgCoronal = self.dcmFn.Ready2Qimg(imageHu2DCoronal_)
        self.label_Coronal_H.setPixmap(QPixmap.fromImage(qimgCoronal))
        self.logUI.debug('Show High Dicom Coronal')

    def SetWidth_H(self):
        """set window width and show changed DICOM to ui
        """
        self.dcmHigh.update({"ww": int(self.Slider_WW_H.value())})
        self.ShowDicom_H()
        self.logUI.debug('Set High Dicom Window Width')

    def SetLevel_H(self):
        """set window center/level and show changed DICOM to ui
        """
        self.dcmHigh.update({"wl": int(self.Slider_WL_H.value())})
        self.ShowDicom_H()
        self.logUI.debug('Set High Dicom Window Level')

    def SetRegistration_L(self):
        """automatic find registration ball center + open another ui window to let user selects ball in order (origin -> x axis -> y axis)
        """
        "automatic find registration ball center"
        if self.dcmLow.get("regBall") != []:
            reply = QMessageBox.information(
                self, "information", "already registration, reset now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.dcmLow.update({"selectedBall": []})
                self.dcmLow.update({"regBall": []})
                self.dcmLow.update({"flageSelectedBall": False})
                self.logUI.info('reset selected ball (Low)')
                print("reset selected ball (Low)")
                return
            else:
                return

        try:
            candidateBall = self.regFn.GetBall(
                self.dcmLow.get("imageHu"), self.dcmLow.get("pixel2Mm"))
        except:
            self.logUI.warning('get candidate ball error')
            QMessageBox.critical(self, "error", "get candidate ball error")
            print('get candidate ball error / SetRegistration_L() error')
            return
        self.logUI.info('get candidate ball:')
        for tmp in candidateBall:
            self.logUI.info(tmp)
        self.dcmLow.update({"candidateBall": candidateBall})
        "open another ui window to let user selects ball in order (origin -> x axis -> y axis)"
        try:
            tmp = self.regFn.GetBallSection(self.dcmLow.get("candidateBall"))
            self.dcmLow.update({"showAxis": tmp[0]})
            self.dcmLow.update({"showSlice": tmp[1]})
            self.ui_CS = CoordinateSystem(self.dcmLow)
            self.ui_CS.show()
            self.Button_ShowRegistration_L.setEnabled(True)
        except:
            self.logUI.warning(
                'get candidate ball error / SetRegistration_L() error / candidateBall could be []')
            QMessageBox.critical(self, "error", "get candidate ball error")
            print(
                'get candidate ball error / SetRegistration_L() error / candidateBall could be []')
        return

    def ShowRegistrationDifference_L(self):
        """map/pair/match ball center between auto(candidateBall) and manual(selectedBall)
           calculate error/difference of relative distance
        """
        "map/pair/match ball center between auto(candidateBall) and manual(selectedBall)"
        candidateBall = self.dcmLow.get("candidateBall")
        selectedBall = self.dcmLow.get("selectedBall")
        if selectedBall != []:
            flagePair = False
            ball = []
            if self.dcmLow.get("flageSelectedBall") == True:
                self.logUI.info('get selected balls')
                for P1 in selectedBall:
                    for P2 in candidateBall:
                        distance = math.sqrt(numpy.square(
                            P1[0]-P2[0])+numpy.square(P1[1]-P2[1])+numpy.square(P1[2]-P2[2]))
                        if distance < 10:
                            ball.append(P2)
                        else:
                            pass
                if len(ball) == 3:
                    flagePair = True
                else:
                    self.logUI.warning(
                        'find seleted balls error / ShowRegistrationDifference error')
                    print("find seleted balls error / ShowRegistrationDifference() error")
            else:
                print("Choose Point error / ShowRegistrationDifference() error")
                self.logUI.warning(
                    'Choose Point error / ShowRegistrationDifference() error')

            if flagePair == True:
                "The ball positions are paired"
                self.dcmLow.update({"regBall": (numpy.array(ball)*[1, 1, -1])})
                self.logUI.info('get registration balls:')
                for tmp in self.dcmLow.get("regBall"):
                    self.logUI.info(tmp)
                "calculate error/difference of relative distance"
                error = self.regFn.GetError(self.dcmLow.get("regBall"))
                logStr = 'registration error (min, max, mean): ' + str(error)
                self.logUI.info(logStr)
                self.label_Error_L.setText(
                    'Error / Difference: {:.2f} mm'.format(error[2]))
                "calculate transformation matrix"
                regMatrix = self.regFn.TransformationMatrix(
                    self.dcmLow.get("regBall"))
                self.logUI.info('get registration matrix: ')
                for tmp in regMatrix:
                    self.logUI.info(tmp)
                self.dcmLow.update({"regMatrix": regMatrix})

            else:
                print("pair error / ShowRegistrationDifference() error")
                self.logUI.warning(
                    'pair error / ShowRegistrationDifference() error')
            self.Button_SetPoint_L.setEnabled(True)
            self.comboBox_L.setEnabled(True)
        else:
            QMessageBox.critical(
                self, "error", "there are not selected 3 balls")
        return

    def SetPoint_L(self):
        if self.dcmLow.get("flageSelectedPoint") == False:
            if self.comboBox_L.currentText() == "Axial":
                self.ui_SPS = SetPointSystem(
                    self.dcmLow, self.comboBox_L.currentText(), self.SliceSelect_Axial_L.value())
                self.ui_SPS.show()
            elif self.comboBox_L.currentText() == "Coronal":
                self.ui_SPS = SetPointSystem(
                    self.dcmLow, self.comboBox_L.currentText(), self.SliceSelect_Coronal_L.value())
                self.ui_SPS.show()
            elif self.comboBox_L.currentText() == "Sagittal":
                self.ui_SPS = SetPointSystem(
                    self.dcmLow, self.comboBox_L.currentText(), self.SliceSelect_Sagittal_L.value())
                self.ui_SPS.show()
            else:
                print("comboBox_L error / SetPoint_L() error")
                self.logUI.warning('comboBox_L error / SetPoint_L() error')

            self.Button_ShowPoint_L.setEnabled(True)
            return
        elif self.dcmLow.get("flageSelectedPoint") == True:
            reply = QMessageBox.information(
                self, "information", "already selected points, reset now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.dcmLow.update({"selectedPoint": []})
                self.dcmLow.update({"flageSelectedPoint": False})
                self.Button_Planning.setEnabled(False)
                self.dcmLow.update({"flageShowPointButton": False})
                self.logUI.info('reset selected point (Low)')
                print("reset selected point (LoW)")
                self.Button_ShowPoint_L.setEnabled(False)
                return
            else:
                return

        return

    def ShowPoint_L(self):
        try:
            print("inhale/Low DICOM entry / target point position (in image coodinate)")
            "in this case"
            point = self.dcmLow.get("selectedPoint")
            self.dcmLow.update({"selectedPoint": (point*[1, 1, -1])})
            for tmp in self.dcmLow.get("selectedPoint"):
                print(tmp)
            print("-------------------------------------------------------------------")

            self.dcmLow.update({"flageShowPointButton": True})
            if self.dcmLow.get("flageShowPointButton") is True and self.dcmHigh.get("flageShowPointButton") is True:
                self.Button_Planning.setEnabled(True)
            return
        except:
            self.logUI.warning('show points error / SetPoint_L() error')
            QMessageBox.critical(self, "error", "show points error")
            print('show points error / SetPoint_L() error')
            return

    def SetRegistration_H(self):
        """automatic find registration ball center + open another ui window to let user selects ball in order (origin -> x axis -> y axis)
        """
        "automatic find registration ball center"
        if self.dcmHigh.get("regBall") != []:
            reply = QMessageBox.information(
                self, "information", "already registration, reset now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.dcmHigh.update({"selectedBall": []})
                self.dcmHigh.update({"regBall": []})
                self.dcmHigh.update({"flageSelectedBall": False})
                self.logUI.info('reset selected ball (High)')
                print("reset selected ball (High)")
                return
            else:
                return

        try:
            candidateBall = self.regFn.GetBall(
                self.dcmHigh.get("imageHu"), self.dcmHigh.get("pixel2Mm"))
        except:
            self.logUI.warning('get candidate ball error / SetRegistration_H() error')
            QMessageBox.critical(self, "error", "get candidate ball error")
            print('get candidate ball error / SetRegistration_H() error')
            return
        self.logUI.info('get candidate ball:')
        for tmp in candidateBall:
            self.logUI.info(tmp)
        self.dcmHigh.update({"candidateBall": candidateBall})
        "open another ui window to let user selects ball in order (origin -> x axis -> y axis)"
        try:
            tmp = self.regFn.GetBallSection(self.dcmHigh.get("candidateBall"))
            self.dcmHigh.update({"showAxis": tmp[0]})
            self.dcmHigh.update({"showSlice": tmp[1]})

            self.ui_CS = CoordinateSystem(self.dcmHigh)
            self.ui_CS.show()
            self.Button_ShowRegistration_H.setEnabled(True)
        except:
            self.logUI.warning(
                'get candidate ball error / SetRegistration_H() error / candidateBall could be []')
            QMessageBox.critical(self, "error", "get candidate ball error")
            print(
                'get candidate ball error / SetRegistration_H() error / candidateBall could be []')
        return

    def ShowRegistrationDifference_H(self):
        """map/pair/match ball center between auto(candidateBall) and manual(selectedBall)
           calculate error/difference of relative distance
        """
        "map/pair/match ball center between auto(candidateBall) and manual(selectedBall)"
        candidateBall = self.dcmHigh.get("candidateBall")
        selectedBall = self.dcmHigh.get("selectedBall")
        if selectedBall != []:
            flagePair = False
            ball = []
            if self.dcmHigh.get("flageSelectedBall") == True:
                self.logUI.info('get selected balls')
                for P1 in selectedBall:
                    for P2 in candidateBall:
                        distance = math.sqrt(numpy.square(
                            P1[0]-P2[0])+numpy.square(P1[1]-P2[1])+numpy.square(P1[2]-P2[2]))
                        if distance < 10:
                            ball.append(P2)
                        else:
                            pass
                if len(ball) == 3:
                    flagePair = True
                else:
                    self.logUI.warning(
                        'find seleted balls error / ShowRegistrationDifference_H() error')
                    print("find seleted balls error / ShowRegistrationDifference_H() error")
            else:
                print("Choose Point error / ShowRegistrationDifference_H() error")
                self.logUI.warning(
                    'Choose Point error / ShowRegistrationDifference_H() error')

            if flagePair == True:
                "The ball positions are paired"
                self.dcmHigh.update(
                    {"regBall": (numpy.array(ball)*[1, 1, -1])})
                self.logUI.info('get registration balls:')
                for tmp in self.dcmHigh.get("regBall"):
                    self.logUI.info(tmp)
                "calculate error/difference of relative distance"
                error = self.regFn.GetError(self.dcmHigh.get("regBall"))
                logStr = 'registration error (min, max, mean): ' + str(error)
                self.logUI.info(logStr)
                self.label_Error_H.setText(
                    'Error / Difference: {:.2f} mm'.format(error[2]))
                "calculate transformation matrix"
                regMatrix = self.regFn.TransformationMatrix(
                    self.dcmHigh.get("regBall"))
                self.logUI.info('get registration matrix: ')
                for tmp in regMatrix:
                    self.logUI.info(tmp)
                self.dcmHigh.update({"regMatrix": regMatrix})

            else:
                print("pair error / ShowRegistrationDifference_H() error")
                self.logUI.warning(
                    'pair error / ShowRegistrationDifference_H() error')
            self.Button_SetPoint_H.setEnabled(True)
            self.comboBox_H.setEnabled(True)
        else:
            QMessageBox.critical(
                self, "error", "there are not selected 3 balls")
        return

    def SetPoint_H(self):
        if self.dcmHigh.get("flageSelectedPoint") == False:
            if self.comboBox_H.currentText() == "Axial":
                self.ui_SPS = SetPointSystem(
                    self.dcmHigh, self.comboBox_H.currentText(), self.SliceSelect_Axial_H.value())
                self.ui_SPS.show()
            elif self.comboBox_H.currentText() == "Coronal":
                self.ui_SPS = SetPointSystem(
                    self.dcmHigh, self.comboBox_H.currentText(), self.SliceSelect_Coronal_H.value())
                self.ui_SPS.show()
            elif self.comboBox_H.currentText() == "Sagittal":
                self.ui_SPS = SetPointSystem(
                    self.dcmHigh, self.comboBox_H.currentText(), self.SliceSelect_Sagittal_H.value())
                self.ui_SPS.show()
            else:
                print("comboBox_H error / SetPoint_H() error")
                self.logUI.warning('comboBox_H error / SetPoint_H() error')
            
            self.Button_ShowPoint_H.setEnabled(True)
            return
        elif self.dcmHigh.get("flageSelectedPoint") == True:
            reply = QMessageBox.information(
                self, "information", "already selected points, reset now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.dcmHigh.update({"selectedPoint": []})
                self.dcmHigh.update({"flageSelectedPoint": False})
                self.Button_Planning.setEnabled(False)
                self.dcmHigh.update({"flageShowPointButton": False})
                self.logUI.info('reset selected point (High)')
                print("reset selected point (High)")
                self.Button_ShowPoint_H.setEnabled(False)
                return
            else:
                return

        return

    def ShowPoint_H(self):
        try:
            print("exhale/High DICOM entry / target point position (in image coodinate)")
            point = self.dcmHigh.get("selectedPoint")
            self.dcmHigh.update({"selectedPoint": (point*[1, 1, -1])})
            for tmp in self.dcmHigh.get("selectedPoint"):
                print(tmp)
            print("-------------------------------------------------------------------")

            self.dcmHigh.update({"flageShowPointButton": True})
            if self.dcmLow.get("flageShowPointButton") is True and self.dcmHigh.get("flageShowPointButton") is True:
                self.Button_Planning.setEnabled(True)
            return
        except:
            self.logUI.warning('show points error / ShowPoint_H() error')
            QMessageBox.critical(self, "error", "show points error")
            print('show points error / ShowPoint_H() error')
            return

    def ShowPlanningPath(self):
        try:
            self.PlanningPath = self.regFn.GetPlanningPath(self.dcmHigh.get("regBall")[0], self.dcmHigh.get("selectedPoint"), self.dcmHigh.get("regMatrix"),
                                                           self.dcmLow.get("regBall")[0], self.dcmLow.get("selectedPoint"), self.dcmLow.get("regMatrix"))

            print("PlanningPath: (in mm unit)")
            for p in self.PlanningPath:
                print(p)
            print("-------------------------------------------------------------------")
            self.Button_RobotHome.setEnabled(True)
            self.Button_RobotAutoRun.setEnabled(True)
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

        metadata, metadataSeriesNum = self.dcmFn.LoadPath(filePath)
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
        self.dcmSAT = {}
        self.dcmSAT.update({"ww": 1})
        self.dcmSAT.update({"wl": 1})
        "registration ball"
        self.dcmSAT.update({"selectedBall": []})
        self.dcmSAT.update({"regBall": []})
        self.dcmSAT.update({"flageSelectedBall": False})
        "set test point"
        self.dcmSAT.update({"selectedTestPoint": []})
        self.dcmSAT.update({"flageselectedTestPoint": False})
        "ui disable"
        self.Button_Registration_SAT.setEnabled(False)
        self.Button_ShowRegistration_SAT.setEnabled(False)
        self.Button_SelectTestPoint_SAT.setEnabled(False)
        self.lineEdit_CmmTestPoint_SAT.setEnabled(False)
        self.Button_EnterTestPoint_SAT.setEnabled(False)
        self.Button_Robot2TestPoint.setEnabled(False)
        self.lineEdit_CmmStylus_SAT.setEnabled(False)
        self.Button_EnterStylus_SAT.setEnabled(False)

        seriesNumberLabel, dicDICOM = self.dcmFn.SeriesSort(metadata, metadataSeriesNum)
        self.dcmSAT.update({"imageTag": self.dcmFn.ReadDicom(seriesNumberLabel, dicDICOM)})
        image = self.dcmFn.GetImage(self.dcmSAT.get("imageTag"))
        if image != 0:
            self.dcmSAT.update({"image": numpy.array(image)})
        else:
            QMessageBox.critical(self, "error", "please load one DICOM")
            self.logUI.warning('fail to get image')
            return

        rescaleSlope = self.dcmSAT.get("imageTag")[0].RescaleSlope
        rescaleIntercept = self.dcmSAT.get("imageTag")[0].RescaleIntercept
        self.dcmSAT.update({"imageHu": numpy.array(self.dcmFn.Transfer2Hu(self.dcmSAT.get("image"), rescaleSlope, rescaleIntercept))})
        self.dcmSAT.update({"pixel2Mm": self.dcmFn.GetPixel2Mm(self.dcmSAT.get("imageTag")[0])})
        self.dcmSAT.update({"imageHuMm": numpy.array(self.dcmFn.ImgTransfer2Mm(self.dcmSAT.get("imageHu"), self.dcmSAT.get("pixel2Mm")))})
        patientPosition = self.dcmSAT.get("imageTag")[0].PatientPosition
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
        self.SliceSelect_Axial_SAT.setMaximum(self.dcmSAT.get("imageHuMm").shape[0]-1)
        self.SliceSelect_Axial_SAT.setValue(int((self.dcmSAT.get("imageHuMm").shape[0])/2))
        self.SliceSelect_Sagittal_SAT.setMinimum(0)
        self.SliceSelect_Sagittal_SAT.setMaximum(self.dcmSAT.get("imageHuMm").shape[1]-1)
        self.SliceSelect_Sagittal_SAT.setValue(int((self.dcmSAT.get("imageHuMm").shape[1])/2))
        self.SliceSelect_Coronal_SAT.setMinimum(0)
        self.SliceSelect_Coronal_SAT.setMaximum(self.dcmSAT.get("imageHuMm").shape[2]-1)
        self.SliceSelect_Coronal_SAT.setValue(int((self.dcmSAT.get("imageHuMm").shape[2])/2))

        max = int(numpy.max(self.dcmSAT.get("imageHuMm")))
        min = int(numpy.min(self.dcmSAT.get("imageHuMm")))
        "WindowWidth"
        self.Slider_WW_SAT.setMinimum(1)
        self.Slider_WW_SAT.setMaximum(max)
        "WindowCenter / WindowLevel"
        self.Slider_WL_SAT.setMinimum(min)
        self.Slider_WL_SAT.setMaximum(max)
        self.dcmSAT.update({"ww": int(self.dcmSAT.get("imageTag")[0].WindowWidth[0])})
        self.dcmSAT.update({"wl": int(self.dcmSAT.get("imageTag")[0].WindowCenter[0])})
        self.Slider_WW_SAT.setValue(self.dcmSAT.get("ww"))
        self.Slider_WL_SAT.setValue(self.dcmSAT.get("wl"))

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
        """show low dicom to ui
        """
        imageHu2DAxial = self.dcmSAT.get("imageHuMm")[self.SliceSelect_Axial_SAT.value(), :, :]
        imageHu2DAxial_ = self.dcmFn.GetGrayImg(imageHu2DAxial, self.dcmSAT.get("ww"), self.dcmSAT.get("wl"))
        qimgAxial = self.dcmFn.Ready2Qimg(imageHu2DAxial_)
        self.label_Axial_SAT.setPixmap(QPixmap.fromImage(qimgAxial))
        self.logUI.debug('Show Low Dicom Axial')

        imageHu2DSagittal = self.dcmSAT.get("imageHuMm")[:, :, self.SliceSelect_Sagittal_SAT.value()]
        imageHu2DSagittal_ = self.dcmFn.GetGrayImg(imageHu2DSagittal, self.dcmSAT.get("ww"), self.dcmSAT.get("wl"))
        qimgSagittal = self.dcmFn.Ready2Qimg(imageHu2DSagittal_)
        self.label_Sagittal_SAT.setPixmap(QPixmap.fromImage(qimgSagittal))
        self.logUI.debug('Show Low Dicom Sagittal')

        imageHu2DCoronal = self.dcmSAT.get("imageHuMm")[:, self.SliceSelect_Coronal_SAT.value(), :]
        imageHu2DCoronal_ = self.dcmFn.GetGrayImg(imageHu2DCoronal, self.dcmSAT.get("ww"), self.dcmSAT.get("wl"))
        qimgCoronal = self.dcmFn.Ready2Qimg(imageHu2DCoronal_)
        self.label_Coronal_SAT.setPixmap(QPixmap.fromImage(qimgCoronal))
        self.logUI.debug('Show Low Dicom Coronal')

        return

    def ScrollBarChangeAxial_SAT(self):
        """while ScrollBar Change (Axial), update ui plot
        """
        imageHu2DAxial = self.dcmSAT.get("imageHuMm")[self.SliceSelect_Axial_SAT.value(), :, :]
        imageHu2DAxial_ = self.dcmFn.GetGrayImg(imageHu2DAxial, self.dcmSAT.get("ww"), self.dcmSAT.get("wl"))
        qimgAxial = self.dcmFn.Ready2Qimg(imageHu2DAxial_)
        self.label_Axial_SAT.setPixmap(QPixmap.fromImage(qimgAxial))
        self.logUI.debug('Show Low Dicom Axial')

    def ScrollBarChangeSagittal_SAT(self):
        """while ScrollBar Change (Sagittal), update ui plot
        """
        imageHu2DSagittal = self.dcmSAT.get("imageHuMm")[:, :, self.SliceSelect_Sagittal_SAT.value()]
        imageHu2DSagittal_ = self.dcmFn.GetGrayImg(imageHu2DSagittal, self.dcmSAT.get("ww"), self.dcmSAT.get("wl"))
        qimgSagittal = self.dcmFn.Ready2Qimg(imageHu2DSagittal_)
        self.label_Sagittal_SAT.setPixmap(QPixmap.fromImage(qimgSagittal))
        self.logUI.debug('Show Low Dicom Sagittal')

    def ScrollBarChangeCoronal_SAT(self):
        """while ScrollBar Change (Coronal), update ui plot
        """
        imageHu2DCoronal = self.dcmSAT.get("imageHuMm")[:, self.SliceSelect_Coronal_SAT.value(), :]
        imageHu2DCoronal_ = self.dcmFn.GetGrayImg(imageHu2DCoronal, self.dcmSAT.get("ww"), self.dcmSAT.get("wl"))
        qimgCoronal = self.dcmFn.Ready2Qimg(imageHu2DCoronal_)
        self.label_Coronal_SAT.setPixmap(QPixmap.fromImage(qimgCoronal))
        self.logUI.debug('Show Low Dicom Coronal')

    def SetWidth_SAT(self):
        """set window width and show changed DICOM to ui
        """
        self.dcmSAT.update({"ww": int(self.Slider_WW_SAT.value())})
        self.ShowDicom_SAT()
        self.logUI.debug('Set Low Dicom Window Width')

    def SetLevel_SAT(self):
        """set window center/level and show changed DICOM to ui
        """
        self.dcmSAT.update({"wl": int(self.Slider_WL_SAT.value())})
        self.ShowDicom_SAT()
        self.logUI.debug('Set Low Dicom Window Level')
    
    def SetRegistration_SAT(self):
        
        "automatic find registration ball center"
        # if self.dcmSAT.get("regBall") != []:
        #     reply = QMessageBox.information(self, "information", "already registration, reset now?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # if reply == QMessageBox.Yes:
        #     self.dcmSAT.update({"selectedBall": []})
        #     self.dcmSAT.update({"regBall": []})
        #     self.dcmSAT.update({"flageSelectedBall": False})
        #     self.logUI.info('reset selected ball (SAT)')
        #     print("reset selected ball (SAT)")
        #     return
        # else:
        #     return
        
        ""
        # 變成找到所有的球
        candidateBall = self.satFn.GetBall(self.dcmSAT.get("imageHuMm"))
        
        tmp = self.satFn.GetBallSection(candidateBall)
        
        
        
        "set test point"
        # self.dcmSAT.update({"selectedTestPoint": []})
        # self.dcmSAT.update({"flageselectedTestPoint": False})
        
        return
        
        

class CoordinateSystem(QWidget, FunctionLib_UI.ui_coordinate_system.Ui_Form):
    def __init__(self, dcm):
        super(CoordinateSystem, self).__init__()
        self.setupUi(self)

        "hint: self.dcmLow = dcmLow = dcm"
        self.dcm = dcm
        self.dcmFn = FunctionLib_Vision._class.DICOM()
        self.DisplayImage()
        self.flage = 0
        self.point = []

    def DisplayImage(self):
        imageHu2D = numpy.array([])
        showAxis = self.dcm.get("showAxis")
        showSlice = self.dcm.get("showSlice")
        pixel2Mm = self.dcm.get("pixel2Mm")
        ww = self.dcm.get("ww")
        wl = self.dcm.get("wl")
        if showAxis == 0:
            "x axis"
            imageHu2D = self.dcm.get("imageHu")[
                :, :, int(showSlice/pixel2Mm[0])]
            """Didn't consider when one of pixel2Mm > 1 and one of pixel2Mm < 1,"""
            """(which is pixel2Mm[n] != pixel2Mm[n+1])"""
            if pixel2Mm[0] < 1 and abs(pixel2Mm[2]) <= 1:
                imageHu2D = cv2.resize(
                    imageHu2D, dsize=None, fx=pixel2Mm[0], fy=pixel2Mm[2], interpolation=cv2.INTER_AREA)
            elif pixel2Mm[0] > 1 and abs(pixel2Mm[2]) >= 1:
                imageHu2D = cv2.resize(
                    imageHu2D, dsize=None, fx=pixel2Mm[0], fy=pixel2Mm[2], interpolation=cv2.INTER_CUBIC)
            else:
                pass
        elif showAxis == 1:
            "y axis"
            imageHu2D = self.dcm.get("imageHu")[
                :, int(showSlice/pixel2Mm[1]), :]
            """Didn't consider when one of pixel2Mm > 1 and one of pixel2Mm < 1,"""
            """(which is pixel2Mm[n] != pixel2Mm[n+1])"""
            if pixel2Mm[1] < 1 and abs(pixel2Mm[2]) <= 1:
                imageHu2D = cv2.resize(
                    imageHu2D, dsize=None, fx=pixel2Mm[1], fy=pixel2Mm[2], interpolation=cv2.INTER_AREA)
            elif pixel2Mm[1] > 1 and abs(pixel2Mm[2]) >= 1:
                imageHu2D = cv2.resize(
                    imageHu2D, dsize=None, fx=pixel2Mm[1], fy=pixel2Mm[2], interpolation=cv2.INTER_CUBIC)
            else:
                pass
        elif showAxis == 2:
            "z axis"
            """Didn't consider when one of pixel2Mm > 1 and one of pixel2Mm < 1,"""
            """(which is pixel2Mm[n] != pixel2Mm[n+1])"""
            imageHu2D = self.dcm.get("imageHu")[
                int(showSlice/pixel2Mm[2]), :, :]
        else:
            print("Coordinate System error")
            return
        if imageHu2D.shape[0] != 0:
            imageHu2D_ = self.dcmFn.GetGrayImg(imageHu2D, ww, wl)
            self.imgHeight, self.imgWidth = imageHu2D_.shape
            gray = numpy.uint8(imageHu2D_)
            self.gray3Channel = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            "mark out candidateBall"
            if showAxis == 0:
                "x axis"
                for C in self.dcm.get("candidateBall"):
                    Cx = C[1]
                    Cy = C[2]
                    cv2.circle(self.gray3Channel, (int(Cx), int(Cy)),
                               20, (256/2, 200, 100), 2)
            elif showAxis == 1:
                "y axis"
                for C in self.dcm.get("candidateBall"):
                    Cx = C[0]
                    Cy = C[2]
                    cv2.circle(self.gray3Channel, (int(Cx), int(Cy)),
                               20, (256/2, 200, 100), 2)
            elif showAxis == 2:
                "z axis"
                for C in self.dcm.get("candidateBall"):
                    Cx = C[0]
                    Cy = C[1]
                    cv2.circle(self.gray3Channel, (int(Cx), int(Cy)),
                               20, (256/2, 200, 100), 2)
            else:
                print("Coordinate System error")
                return
            "update and display ui"
            self.UpdateImage()
        else:
            print("Coordinate System show img error")

    def UpdateImage(self):
        "update and display ui"
        bytesPerline = 3 * self.imgWidth
        self.qimg = QImage(self.gray3Channel, self.imgWidth, self.imgHeight,
                           bytesPerline, QImage.Format_RGB888).rgbSwapped()
        self.label_img.setPixmap(QPixmap.fromImage(self.qimg))
        "GetClickedPosition don't +()), it could create error below: "
        "TypeError: GetClickedPosition() missing 1 required positional argument: 'event'"
        self.label_img.mousePressEvent = self.GetClickedPosition
        return

    def GetClickedPosition(self, event):
        showAxis = self.dcm.get("showAxis")
        showSlice = self.dcm.get("showSlice")
        x = event.pos().x()
        y = event.pos().y()
        self.flage = self.flage + 1
        if self.flage > 3:
            QMessageBox.critical(
                self, "error", "there are already selected 3 balls")
            return
        else:
            if showAxis == 0:
                "x axis"
                self.point.append([showSlice, x, y])
                self.label_origin.setText(
                    f"(x, y, z) = ({showSlice}, {x}, {y})")
            elif showAxis == 1:
                "y axis"
                self.point.append([x, showSlice, y])
                self.label_origin.setText(
                    f"(x, y, z) = ({x}, {showSlice}, {y})")
            elif showAxis == 2:
                "z axis"
                self.point.append([x, y, showSlice])
                self.label_origin.setText(
                    f"(x, y, z) = ({x}, {y}, {showSlice})")
            else:
                print("Coordinate System error")
        self.drawPoint(x, y)
        self.UpdateImage()
        return

    def drawPoint(self, x, y):
        "red"
        color = (0, 0, 255)
        point = (int(x), int(y))
        point_size = 1
        thickness = 4
        cv2.circle(self.gray3Channel, point, point_size, color, thickness)
        return

    def okAndClose(self):
        if len(self.point) == 3:
            self.dcm.update({"flageSelectedBall": True})
            self.dcm.update({"selectedBall": numpy.array(self.point)})
            self.close()
        else:
            QMessageBox.critical(
                self, "error", "there are not selected 3 balls")
            return


class SetPointSystem(QWidget, FunctionLib_UI.ui_set_point_system.Ui_Form):
    def __init__(self, dcm, comboBox, scrollBar):
        super(SetPointSystem, self).__init__()
        self.setupUi(self)

        "hint: self.dcmLow = dcmLow"
        self.dcm = dcm
        self.dcmFn = FunctionLib_Vision._class.DICOM()
        self.comboBox = comboBox
        self.scrollBar = scrollBar
        self.DisplayImage()
        self.flage = 0

    def DisplayImage(self):
        pixel2Mm = self.dcm.get("pixel2Mm")
        showSection = self.comboBox
        showSlice = self.scrollBar
        ww = self.dcm.get("ww")
        wl = self.dcm.get("wl")

        if showSection == "Axial":
            imageHu2D = self.dcm.get("imageHuMm")[int(showSlice), :, :]
        elif showSection == "Coronal":
            imageHu2D = self.dcm.get("imageHuMm")[:, int(showSlice), :]
        elif showSection == "Sagittal":
            imageHu2D = self.dcm.get("imageHuMm")[:, :, int(showSlice)]
        else:
            print("DisplayImage error / Set Point System error")
            return
        if imageHu2D.shape[0] != 0:
            imageHu2D_ = self.dcmFn.GetGrayImg(imageHu2D, ww, wl)
            self.imgHeight, self.imgWidth = imageHu2D_.shape
            gray = numpy.uint8(imageHu2D_)
            self.gray3Channel = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            "update and display ui"
            self.UpdateImage()
        else:
            print("DisplayImage error / Set Point System show img error")

    def UpdateImage(self):
        "update and display ui"
        bytesPerline = 3 * self.imgWidth
        self.qimg = QImage(self.gray3Channel, self.imgWidth, self.imgHeight,
                           bytesPerline, QImage.Format_RGB888).rgbSwapped()
        self.label_img.setPixmap(QPixmap.fromImage(self.qimg))
        "GetClickedPosition don't + ()), it could create error below: "
        "TypeError: GetClickedPosition() missing 1 required positional argument: 'event'"
        self.label_img.mousePressEvent = self.GetClickedPosition
        return

    def GetClickedPosition(self, event):
        x = event.pos().x()
        y = event.pos().y()
        showSection = self.comboBox
        showSlice = self.scrollBar

        self.flage = self.SavePoints(x, y, showSection, showSlice)
        if self.flage == 1 or self.flage == 2:
            self.drawPoint(x, y)
            self.UpdateImage()

    def drawPoint(self, x, y):
        "red"
        color = (0, 0, 255)
        point = (int(x), int(y))
        point_size = 1
        thickness = 4
        cv2.circle(self.gray3Channel, point, point_size, color, thickness)
        return

    def SavePoints(self, x, y, showSection, showSlice):
        if numpy.array(self.dcm.get("selectedPoint")).shape[0] >= 2:
            QMessageBox.critical(
                self, "error", "there are already selected 2 points")
            return 3
        elif numpy.array(self.dcm.get("selectedPoint")).shape[0] == 0:
            if showSection == "Axial":
                self.dcm.update(
                    {"selectedPoint": numpy.array([[x, y, showSlice]])})
                self.label_origin.setText(
                    f"(x, y, z) = ({x}, {y}, {showSlice})")
            elif showSection == "Coronal":
                self.dcm.update(
                    {"selectedPoint": numpy.array([[x, showSlice, y]])})
                self.label_origin.setText(
                    f"(x, y, z) = ({x}, {showSlice}, {y})")
            elif showSection == "Sagittal":
                self.dcm.update(
                    {"selectedPoint": numpy.array([[showSlice, x, y]])})
                self.label_origin.setText(
                    f"(x, y, z) = ({showSlice}, {x}, {y})")
            else:
                print(
                    "GetClickedPosition error / Set Point System error / self.dcm.get(\"selectedPoint\").shape[0] == 0")
            return 1
        elif numpy.array(self.dcm.get("selectedPoint")).shape[0] == 1:
            if showSection == "Axial":
                tmp = numpy.insert(self.dcm.get(
                    "selectedPoint"), 1, numpy.array([x, y, showSlice]), 0)
                self.dcm.update({"selectedPoint": tmp})
                self.label_origin.setText(
                    f"(x, y, z) = ({x}, {y}, {showSlice})")
            elif showSection == "Coronal":
                tmp = numpy.insert(self.dcm.get(
                    "selectedPoint"), 1, numpy.array([x, showSlice, y]), 0)
                self.dcm.update({"selectedPoint": tmp})
                self.label_origin.setText(
                    f"(x, y, z) = ({x}, {showSlice}, {y})")
            elif showSection == "Sagittal":
                tmp = numpy.insert(self.dcm.get(
                    "selectedPoint"), 1, numpy.array([showSlice, x, y]), 0)
                self.dcm.update({"selectedPoint": tmp})
                self.label_origin.setText(
                    f"(x, y, z) = ({showSlice}, {x}, {y})")
            else:
                print(
                    "GetClickedPosition error / Set Point System error / self.dcm.get(\"selectedPoint\").shape[0] == 1")
            self.dcm.update({"flageSelectedPoint": True})
            return 2
        else:
            print("GetClickedPosition error / Set Point System error / else")
            return 0

    def okAndClose(self):
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWidget()
    w.show()
    sys.exit(app.exec_())
