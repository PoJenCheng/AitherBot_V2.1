# import pyads
import pyads
import math
import ctypes as ct
import sys
import numpy as np
import keyboard
import winsound
import serial
import cv2
# import random
# import atexit
from pylltLib import pyllt as llt
from time import sleep
from FunctionLib_Robot.__init__ import *
from FunctionLib_Vision._class import REGISTRATION
from FunctionLib_Robot._subFunction import lowPass
from ._globalVar import *
from pyueye import ueye
# from FunctionLib_UI.ui_matplotlib_pyqt import *

import matplotlib
matplotlib.use('QT5Agg')

from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, QObject
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_gt5agg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from time import *
from FunctionLib_Robot.logger import logger

upper_G_length = 0
upper_G_angle = 0
lower_G_length = 0
lower_G_angle = 0


class MOTORCONTROL(QObject):
    signalProgress = pyqtSignal(float)
    signalInitErrMsg = pyqtSignal(str)
    
    def __init__(self, motorAxis):
        super().__init__()
        self.motorAxis = motorAxis
        self.bServoEnableLabel = 'GVL.bServoEnable_' + str(self.motorAxis)
        self.bMotorStopLabel = 'GVL.bMotorStop_' + str(self.motorAxis)
        self.bVelocityLabel = 'GVL.bVelocity_' + str(self.motorAxis)
        self.PowerStatus = 'GVL.PowerStatus_' + str(self.motorAxis)
        self.MoveSpeed = 'GVL.VelocityCommand_' + str(self.motorAxis)
        self.MoveSpeedDir = 'GVL.VelocityDirection_' + str(self.motorAxis)
        self.MoveSpeedDec = 'GVL.VelocityDec_' + str(self.motorAxis)
        self.bMoveSpeed = 'GVL.bVelocity_' + str(self.motorAxis)
        self.bMotorStop = 'GVL.bMotorStop_' + str(self.motorAxis)
        self.StopSatus = 'GVL.StopStatus_' + str(self.motorAxis)
        self.bMoveAbsolute = 'GVL.bMoveAbsolute_' + str(self.motorAxis)
        self.AbsolutePosition = 'GVL.AbsolutePosition_' + str(self.motorAxis)
        self.AbsoluteVelocity = 'GVL.AbsoluteVelocity_' + str(self.motorAxis)
        self.MoveAbsoluteStatus = 'GVL.MoveAbsoluteStatus_' + \
            str(self.motorAxis)
        self.bMoveRelative = 'GVL.bMoveRelative_' + str(self.motorAxis)
        self.RelativePosition = 'GVL.RelativePosition_' + str(self.motorAxis)
        self.RelativeVelocity = 'GVL.RelativeVelocity_' + str(self.motorAxis)
        self.MoveRelativeStatus = 'GVL.MoveRelativeStatus_' + \
            str(self.motorAxis)
        self.bSetPosition = 'GVL.bSetPosition_' + str(self.motorAxis)
        self.SetPositionStatus = 'GVL.SetPositionStatus_' + str(self.motorAxis)
        self.MC_Power_Error = 'GVL.MC_Power_Error_' + str(self.motorAxis)
        self.MC_Power_ErrorID = 'GVL.MC_Power_ErrorID_' + str(self.motorAxis)
        self.MoveVelocity_Error = 'GVL.MoveVelocity_Error_' + \
            str(self.motorAxis)
        self.MoveVelocity_ErrorID = 'GVL.MoveVelocity_ErrorID_' + \
            str(self.motorAxis)
        self.MoveAbsolute_Error = 'GVL.MoveAbsolute_Error_' + \
            str(self.motorAxis)
        self.MoveAbsolute_ErrorID = 'GVL.MoveAbsolute_ErrorID_' + \
            str(self.motorAxis)
        self.MoveRelative_Error = 'GVL.MoveRelative_Error_' + \
            str(self.motorAxis)
        self.MoveRelative_ErrorID = 'GVL.MoveRElative_ErrorID_' + \
            str(self.motorAxis)
        self.bReset = 'GVL.bReset_' + str(self.motorAxis)
        self.Reset_Error = 'GVL.Reset_Error_' + str(self.motorAxis)
        self.Reset_ErrorID = 'GVL.Reset_ErrorID_' + str(self.motorAxis)
        self.SetPosition_Error = 'GVL.SetPosition_Error_' + str(self.motorAxis)
        self.SetPosition_ErrorID = 'GVL.SetPosition_ErrorID_' + \
            str(self.motorAxis)
        self.Stop_Error = 'GVL.Stop_Error_' + str(self.motorAxis)
        self.Stop_ErrorID = 'GVL.Stop_ErrorID_' + str(self.motorAxis)
        self.bDualRotateRelative = 'GVL.bDualRotateRelative'
        self.bDualLinearRelative = 'GVL.bDualLinearRelative'
        self.bMultiMoveRelative = 'GVL.bMultiMoveRelative'
        self.bActualPosition = 'GVL.bActualPosition'
        self.fbActualPosition = 'GVL.Axis' + str(self.motorAxis) + '_Position'
        self.fbStatusPosition = 'GVL.StatusPosition_' + str(self.motorAxis)
        self.bLimitSwitch = 'GVL.LimitSwitch'+str(self.motorAxis)
        self.bDisableLimitSwitch = 'GVL.DisableLimitSwitch'+str(self.motorAxis)
        self.bDualVelocityButton = 'GVL.DualVelocityButton'
        self.bActualVelocity = 'GVL.bActualVelocity'
        self.fbActualVelocity = 'GVL.Axis' + str(self.motorAxis) + '_Velocity'
        self.fbStatusVelocity = 'GVL.StatusVelocity_' + str(self.motorAxis)
        self.fResetStatus = 'GVL.ResetStatus_'+str(self.motorAxis)
        # self.bLimitSwitch5 = 'GVL.LimitSwitch5'
        # self.bLimitSwitch6 = 'GVL.LimitSwitch6'
        self.bDualAbsolute = 'GVL.bDualAbsolute'

        

        try:
            self.plc = pyads.Connection('5.97.65.198.1.1', 851)
            # self.plc = pyads.Connection('5.97.65.198.1.1', pyads.PORT_TC3PLC1)
            # ser = serial.Serial(port='COM5', baudrate=9600, timeout=2)
            self.plc.open()
            print(f'plc open status : {self.plc.is_open}')
        except:
            input("Motor or auduino connect fail. Please check it and press 'Enter'")

    def MotorInitial(self):
        self.plc.write_by_name(self.bMotorStopLabel, False)
        self.plc.write_by_name(self.bServoEnableLabel, False)
        self.plc.write_by_name(self.bVelocityLabel, False)
        self.plc.write_by_name(self.bMoveAbsolute, False)
        self.plc.write_by_name(self.bDualRotateRelative, False)
        self.plc.write_by_name(self.bDualLinearRelative, False)
        self.plc.write_by_name(self.bMoveRelative, False)
        self.plc.write_by_name(self.bReset, False)
        self.plc.write_by_name(self.bSetPosition, False)
        self.plc.write_by_name(self.bMultiMoveRelative, False)
        self.plc.write_by_name(self.bActualPosition, True)
        sleep(0.5)

    
    def TurnOffChecking(self):
        while self.plc.read_by_name(self.bMoveSpeed) == True:
            self.plc.write_by_name(self.bMoveSpeed, False)
            sleep(0.01)
        while self.plc.read_by_name(self.bMoveAbsolute) == True:
            self.plc.write_by_name(self.bMoveAbsolute, False)
            sleep(0.01)
        while self.plc.read_by_name(self.bMoveRelative) == True:
            self.plc.write_by_name(self.bMoveRelative, False)
            sleep(0.01)
        while self.plc.read_by_name(self.bDualVelocityButton) == True:
            self.plc.write_by_name(self.bDualVelocityButton, False)

    def MotorDriverEnable(self):
        ServoEnable = False
        self.plc.write_by_name(self.bServoEnableLabel, ServoEnable)
        sleep(0.1)
        ServoEnable = True
        self.plc.write_by_name(self.bServoEnableLabel, ServoEnable)
        sleep(0.5)
        if self.plc.read_by_name(self.PowerStatus) == True:
            print(f"The servo motor {self.motorAxis} is enabled.")
            return f"The servo motor {self.motorAxis} is enabled."
        else:
            print(f"Fail to enable the servo motor {self.motorAxis}.")
            # self.signalInitErrMsg.emit(f"Fail to enable the servo motor {self.motorAxis}.")
            print(f"Reset servo motor {self.motorAxis}")
            self.ResetMC()
            sleep(1)
            self.MotorDriverEnable()
            
        return ''

    def MC_Stop(self):
        self.plc.write_by_name(self.bMotorStop, True)
        self.plc.write_by_name(self.bDisableLimitSwitch, True)

    def MC_Stop_Disable(self):
        self.plc.write_by_name(self.bMotorStop, False)
        while self.plc.read_by_name(self.StopSatus) == True:
            self.plc.write_by_name(self.bMotorStop, False)

    def MotorDisabled(self):
        while self.plc.read_by_name(self.bServoEnableLabel) == True:
            self.plc.write_by_name(self.bServoEnableLabel, False)
            sleep(0.1)

    def SetPosition(self, progressMaximum:float = None, curProgressValue:float = None):
        while self.plc.read_by_name(self.SetPositionStatus) == False:
            self.plc.write_by_name(self.bSetPosition, True)
            if progressMaximum is not None:
                curProgressValue = min(curProgressValue + 0.0001, progressMaximum)
                self.signalProgress.emit(curProgressValue)
            sleep(0.1)
        if progressMaximum is not None:
            self.signalProgress.emit(progressMaximum)
        self.plc.write_by_name(self.bSetPosition, False)

    def MoveVelocitySetting(self, speed, decceration, dir):
        self.TurnOffChecking()
        # dir = 1 positive, dir = 3 nagative
        self.plc.write_by_name(self.MoveSpeed, speed)
        self.plc.write_by_name(self.MoveSpeedDir, dir)
        self.plc.write_by_name(self.MoveSpeedDec, decceration)
        sleep(0.1)

    def bMoveVelocityEnable(self):
        self.plc.write_by_name(self.bDisableLimitSwitch, False)
        self.plc.write_by_name(self.bMoveSpeed, True)
        sleep(0.1)

    def bDualVelocityEnable(self):
        self.plc.write_by_name(self.bDualVelocityButton, True)

    def MoveAbsoluteSetting(self, Position, Velocity):
        # self.TurnOffChecking()
        self.plc.write_by_name(self.bMoveAbsolute, False)
        self.plc.write_by_name(self.AbsolutePosition, Position)
        self.plc.write_by_name(self.AbsoluteVelocity, Velocity)

    def bMoveAbsoluteEnable(self):
        self.plc.write_by_name(self.bMoveAbsolute, True)
        while self.plc.read_by_name(self.MoveAbsoluteStatus) == False:
            self.plc.write_by_name(self.bMoveAbsolute, True)
            sleep(0.01)

    def bDualMoveAbsolute(self):
        self.plc.write_by_name(self.bDualAbsolute, True)
        while self.plc.read_by_name(self.bDualAbsolute) == False:
            self.plc.write_by_name(self.bDualAbsolute, True)
            sleep(0.01)

    def MoveRelativeSetting(self, Position, Velocity):
        self.TurnOffChecking()
        self.plc.write_by_name(self.RelativePosition, Position)
        self.plc.write_by_name(self.RelativeVelocity, Velocity)

    def bMoveRelativeEnable(self):
        while self.plc.read_by_name(self.bMoveRelative) == True or self.plc.read_by_name(self.bDualRotateRelative) == True\
                or self.plc.read_by_name(self.bDualLinearRelative) == True:
            self.plc.write_by_name(self.bMoveRelative, False)
            self.plc.write_by_name(self.bDualRotateRelative, False)
            self.plc.write_by_name(self.bDualLinearRelative, False)
            sleep(0.1)
        self.plc.write_by_name(self.bMoveRelative, True)

    def fbMoveRelative(self):
        temp = self.plc.read_by_name(self.MoveRelativeStatus)
        return temp

    def bDualRotateRelativeEnable(self):
        while self.plc.read_by_name(self.bDualRotateRelative) == True:
            self.plc.write_by_name(self.bDualRotateRelative, False)
            sleep(0.1)
        self.plc.write_by_name(self.bDualRotateRelative, True)

    def bDualLinearRelativeEnable(self):
        while self.plc.read_by_name(self.bDualLinearRelative) == True:
            self.plc.write_by_name(self.bDualLinearRelative, False)
            sleep(0.1)
        self.plc.write_by_name(self.bDualLinearRelative, True)

    def bMultiMoveRelativeEnable(self):
        while self.plc.read_by_name(self.bMultiMoveRelative) == True:
            self.plc.write_by_name(self.bMultiMoveRelative, False)
            sleep(0.1)
        self.plc.write_by_name(self.bMultiMoveRelative, True)

    def MoveRelativeButtonDisable(self):
        while self.plc.read_by_name(self.bMoveRelative) == True or \
            self.plc.read_by_name(self.bMultiMoveRelative) == True or self.plc.read_by_name(self.bDualRotateRelative) == True\
                or self.plc.read_by_name(self.bDualLinearRelative) == True:
            self.plc.write_by_name(self.bMoveRelative, False)
            self.plc.write_by_name(self.bMultiMoveRelative, False)
            self.plc.write_by_name(self.bDualRotateRelative, False)
            self.plc.write_by_name(self.bDualLinearRelative, False)
            sleep(0.1)

    def ReadActualPosition(self):
        status = self.plc.read_by_name(self.fbStatusPosition)
        while status is False:
            self.plc.write_by_name(self.bActualPosition, True)
            sleep(0.01)
        position = self.plc.read_by_name(self.fbActualPosition)
        return position

    def ReadActualVelocity(self):
        status = self.plc.read_by_name(self.bActualVelocity)
        while status is False:
            self.plc.write_by_name(self.bActualVelocity, True)
            sleep(0.01)
        velocity = self.plc.read_by_name(self.fbActualVelocity)
        return velocity

    def homeValue(self):
        value = self.plc.read_by_name(self.bLimitSwitch)
        return int(value)

    def bMoveRelativeCommandDisable(self):
        moveRelativeStatus = self.plc.read_by_name(self.bMoveRelative)
        if moveRelativeStatus is True:
            self.plc.write_by_name(self.bMoveRelative, False)
            moveRelativeStatus = self.plc.read_by_name(self.bMoveRelative)
            
    def ResetMC(self):
        while self.plc.read_by_name(self.fResetStatus) == False:
            self.plc.write_by_name(self.bReset,True)
        while self.plc.read_by_name(self.fResetStatus) == True:
            self.plc.write_by_name(self.bReset,False)
            

class OperationLight():
    def __init__(self):
        self.bDisplayLight_GR = 'GVL.DisplayLight_GR'
        self.bDisplayLight_OR = 'GVL.DisplayLight_OR'
        self.bDisplayLight_RE = 'GVL.DisplayLight_RE'
        self.DynamicCompensationLight = 'GVL.DynamicCompensation'
        self.EnableCompensation = 'GVL.EnableCompensation'
        
        try:
            self.plc = pyads.Connection('5.97.65.198.1.1', 851)
            self.plc.open()
            print(f'plc open status : {self.plc.is_open}')
            
            self.plc.write_by_name(self.bDisplayLight_GR,False)
            self.plc.write_by_name(self.bDisplayLight_OR,False)
            self.plc.write_by_name(self.bDisplayLight_RE,False)
        except:
            input("Motor or auduino connect fail. Please check it and press 'Enter'")
            self.plc.write_by_name(self.bDisplayLight_GR,False)
            self.plc.write_by_name(self.bDisplayLight_OR,False)
            self.plc.write_by_name(self.bDisplayLight_RE,True)
            
    def DisplayRun(self):
        self.plc.write_by_name(self.bDisplayLight_GR,False)
        self.plc.write_by_name(self.bDisplayLight_OR,True)
        self.plc.write_by_name(self.bDisplayLight_RE,False)
            
    def DisplaySafe(self):
        self.plc.write_by_name(self.bDisplayLight_GR,True)
        self.plc.write_by_name(self.bDisplayLight_OR,False)
        self.plc.write_by_name(self.bDisplayLight_RE,False)
        
    def DisplayError(self):
        self.plc.write_by_name(self.bDisplayLight_GR,False)
        self.plc.write_by_name(self.bDisplayLight_OR,False)
        self.plc.write_by_name(self.bDisplayLight_RE,True)

    def DynamicCompensation(self):
        EnableCompensation = self.plc.read_by_name(self.EnableCompensation)
        while EnableCompensation == False:
            sleep(0.2)
            self.plc.write_by_name(self.DynamicCompensationLight,True)
            sleep(0.2)
            self.plc.write_by_name(self.DynamicCompensationLight,False)
            EnableCompensation = self.plc.read_by_name(self.EnableCompensation)
        self.plc.write_by_name(self.DynamicCompensationLight,False)
    

class RobotSupportArm(QObject):
    signalPedalPress = pyqtSignal(bool)
    signalTargetArrived = pyqtSignal()
    signalAxisDiff = pyqtSignal(int, float)
    
    def __init__(self):
        super().__init__()
        try:
            self.plc = pyads.Connection('5.97.65.198.1.1', 851)
            self.plc.open()
            print(f'plc open status : {self.plc.is_open}')
        except:
            input("Motor or auduino connect fail. Please check it and press 'Enter'")
            
        self.RobotArmEn1 = 'GVL.RobotArmEn1'
        self.RobotArmEn2 = 'GVL.RobotArmEn2'
        self.SupportMove = 'GVL.SupportMove'
        self.EnableSupportEn1 = 'GVL.EnableSupportEn1'
        self.EnableSupportEn2 = 'GVL.EnableSupportEn2'
        self.Tolerance = 100
        self.frequency = 1000
        self.duration = 1000
        self.TargetEn1 = None
        self.TargetEn2 = None
        self.bPedalPressLast = None
        # 是否偏離target
        self.bRobotMoveFromTarget = True
        
        self.plc.write_by_name(self.EnableSupportEn1,False) 
        self.plc.write_by_name(self.EnableSupportEn2,False)
    
    def ReadEncoder(self):
        En1 = self.plc.read_by_name(self.RobotArmEn1)
        En2 = self.plc.read_by_name(self.RobotArmEn2)
        if self.TargetEn1 is not None and self.TargetEn2 is not None:
            diff1 = En1 - self.TargetEn1
            diff2 = En2 - self.TargetEn2
            if abs(diff1) < self.Tolerance + 500 and abs(diff2) < self.Tolerance + 500:
                self.bRobotMoveFromTarget = False
            else:
                self.bRobotMoveFromTarget = True
        return En1, En2
    
    def ReadPedal(self):
        bPress = self.plc.read_by_name(self.SupportMove)
        # 只有狀態改變時才發送訊息
        if self.bPedalPressLast is not None:
            if bPress ^ self.bPedalPressLast == True:
                self.signalPedalPress.emit(bPress)
        self.bPedalPressLast = bPress
        
    
    def ReleaseAllEncoder(self):
        Release = self.plc.read_by_name(self.SupportMove)
        while Release == True:
            self.plc.write_by_name(self.EnableSupportEn1,True) 
            self.plc.write_by_name(self.EnableSupportEn2,True)
            Release = self.plc.read_by_name(self.SupportMove)
            self.signalPedalPress.emit(Release)
        
        self.plc.write_by_name(self.EnableSupportEn1,False) 
        self.plc.write_by_name(self.EnableSupportEn2,False)
        return self.ReadEncoder()
    
    def SetTargetPos(self):
        self.TargetEn1,self.TargetEn2 = self.ReadEncoder()
        self.bRobotMoveFromTarget = False
        return self.TargetEn1, self.TargetEn2
    
    def CaliEncoder1(self):
        caliStatus  = True   # test, 預設False
        while caliStatus is False:
            RealTimePos = self.ReadEncoder()
            footController = self.plc.read_by_name(self.SupportMove)
            self.signalPedalPress.emit(footController)
            if footController == True:
                self.plc.write_by_name(self.EnableSupportEn1,True) #將軸一enable
                diffValue = RealTimePos[0]-self.TargetEn1
                self.signalAxisDiff.emit(1, diffValue)
                if abs(diffValue) <= self.Tolerance:
                    self.plc.write_by_name(self.EnableSupportEn1,False)
                    caliStatus = True
                    winsound.Beep(self.frequency, self.duration)
                    
    def CaliEncoder2(self):
        caliStatus  = True   # test, 預設False
        while caliStatus is False:
            RealTimePos = self.ReadEncoder()
            footController = self.plc.read_by_name(self.SupportMove)
            self.signalPedalPress.emit(footController)
            if footController == True:
                self.plc.write_by_name(self.EnableSupportEn2,True) #將軸二enable
                diffValue = RealTimePos[1]-self.TargetEn2
                self.signalAxisDiff.emit(2, diffValue)
                if abs(diffValue) <= self.Tolerance:
                    self.plc.write_by_name(self.EnableSupportEn2,False)
                    caliStatus = True
                    winsound.Beep(self.frequency, self.duration)
                
    def BackToTargetPos(self):
        self.CaliEncoder1()
        self.CaliEncoder2()
        sleep(0.5)
        self.signalTargetArrived.emit()
        
    def IsMove(self):
        return self.bRobotMoveFromTarget

class imageCalibration():
    def __init__(self,id,exposure_time):        
        # 初始化相機
        self.camera = ueye.HIDS(id)

        # 嘗試初始化相機
        ret = ueye.is_InitCamera(self.camera, None)
        if ret != ueye.IS_SUCCESS:
            print("相機初始化失敗")
            exit(1)

        # 獲取相機感測器的資訊
        self.sensor_info = ueye.SENSORINFO()
        print(self.sensor_info.SensorID)
        ueye.is_GetSensorInfo(self.camera, self.sensor_info)

        # 設置相機的尺寸
        self.original_width = int(self.sensor_info.nMaxWidth)
        self.original_height = int(self.sensor_info.nMaxHeight)

        # 設定像素格式為灰階
        ueye.is_SetColorMode(self.camera, ueye.IS_CM_MONO8)

        # 調整曝光度
        self.exposure_time = exposure_time
        ueye.is_Exposure(self.camera, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE, ueye.DOUBLE(self.exposure_time), ueye.sizeof(ueye.DOUBLE))

        # 分配內存
        self.mem_ptr = ueye.c_mem_p()
        self.mem_id = ueye.int()
        ueye.is_AllocImageMem(self.camera, self.original_width, self.original_height, 8, self.mem_ptr, self.mem_id)
        ueye.is_SetImageMem(self.camera, self.mem_ptr, self.mem_id)

        
    # 繪製紅色虛線
    def draw_dashed_line(self, img, start_point, end_point, color, dash_length=10, space_length=10, thickness=2):
        vector = np.array(end_point) - np.array(start_point)
        vector_length = np.linalg.norm(vector)
        unit_vector = vector / vector_length

        num_segments = int(vector_length // (dash_length + space_length))
        for i in range(num_segments):
            segment_start = np.array(start_point) + unit_vector * (i * (dash_length + space_length))
            segment_end = segment_start + unit_vector * dash_length
            cv2.line(img, tuple(segment_start.astype(int)), tuple(segment_end.astype(int)), color, thickness)


    def CameraCalibration(self,image, CrossP1, CrossP2, CrossP3, CrossP4):
        # 原始梯形的四個頂點
        src_points = np.float32([CrossP1, CrossP2, CrossP3, CrossP4])
        
        # 計算寬度
        width = math.sqrt((CrossP2[0] - CrossP1[0])**2 + (CrossP2[1] - CrossP1[1])**2)
        
        # 計算高度
        height = math.sqrt((CrossP3[0] - CrossP1[0])**2 + (CrossP3[1] - CrossP1[1])**2)

        # 校正後的目標正方形頂點坐標
        dst_points = np.float32([[0, 0], [width, 0], [0, height], [width, height]])

        # 計算透視變換矩陣
        M = cv2.getPerspectiveTransform(src_points, dst_points)

        # 應用透視變換
        corrected_image = cv2.warpPerspective(image, M, (int(width), int(height)))
        
        return corrected_image, width, height
    
    def cameraLogOut(self):
        # 釋放內存並退出相機
        ueye.is_FreeImageMem(self.camera, self.mem_ptr, self.mem_id)
        ueye.is_ExitCamera(self.camera)


    # def FindCrossPoint(self, L1,L2):
    #     # 定義兩條直線的一般方程式
    #     # 第一條直線 Ax + By + C = 0
    #     A1, B1, C1,S1 = L1  # 直線1的係數
    #     # 第二條直線 Ax + By + C = 0
    #     A2, B2, C2,S2 = L2  # 直線2的係數

    #     # 使用 numpy 解決線性方程式
    #     # 建立係數矩陣
    #     coefficients = np.array([[A1, B1], [A2, B2]])
    #     # 建立常數項
    #     constants = np.array([-C1, -C2])
    #     # 求解交點
    #     solution = np.linalg.solve(coefficients, constants)
    #     # 輸出交點
    #     print(solution)
    #     return solution
    
    def FindCrossPoint(self,path):
        imagePic = cv2.imread(path)

        # 將影像轉換為灰度圖像
        gray = cv2.cvtColor(imagePic, cv2.COLOR_BGR2GRAY)

        # 對灰度圖像進行閾值處理
        _, thresh = cv2.threshold(gray, 254, 255, cv2.THRESH_BINARY)

        # 找到輪廓
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 假設白色矩形是最大的輪廓
        contour = max(contours, key=cv2.contourArea)

        # 獲取最小外接矩形
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)

        # 繪製矩形（可選）
        cv2.drawContours(imagePic, [box], 0, (0, 0, 255), 2)

        # 獲取四個頂點座標
        points = [(point[0], point[1]) for point in box]

        # 輸出四個頂點座標
        print("左下角:", points[0])
        print("左上角:", points[1])
        print("右上角:", points[2])
        print("右下角:", points[3])
        
        return points

    def lineEquation(self, x1,y1,x2,y2):
        # 計算斜率
        div = x2-x1
        lineEquationResult = True
        # if abs(div) > 0.5 and div < 1 and abs(div) != 1:
        if abs(div) > 1:
            m = (y2 - y1) / (x2 - x1)  # 斜率
            # 計算截距
            b = y1 - m * x1  # y-截距
            # 一般方程式
            A = -m
            B = 1
            C = -b
        else:
            A = 1
            B = 0
            C = -x1
            
        general_form = f"{A:.2f}x + {B:.2f}y + {C:.2f} = 0"
        print("一般方程式:", general_form)
          
        return A,B,C,lineEquationResult
    
    # def lineEquation(self, x1, y1, x2, y2):
    #     if x1 == x2:
    #         return f"垂直線：x = {x1}"
    #     else:
    #         m = (y2 - y1) / (x2 - x1)
    #         b = y1 - m * x1
    #         return f"直線方程式：y = {m}x + {b}"
        

    def edgeFinder_intercept_X(self,image,X_value1,X_value2,threadValue):
        data1 = []
        data2 = []
        for y in range(image.shape[0]):  # 行
                # 確保像素值為無符號 8 位整數
                pixel_value1 = int(image[y, X_value1])  # 轉換為整數
                pixel_value2 = int(image[y, X_value2])  # 轉換為整數
                if pixel_value1 >= threadValue:
                    pixel_value1 = 1
                    data1.append([X_value1,y])
                if pixel_value2 >= threadValue:
                    pixel_value2 = 1
                    data2.append([X_value2, y])
        upperLine = self.lineEquation(data1[0][0],data1[0][1],data2[0][0],data2[0][1])   
        lowerLine = self.lineEquation(data1[-1][0],data1[-1][1],data2[-1][0],data2[-1][1])
        if upperLine[3] == True and lowerLine[3] == True:
            intercept_X = True
        else:
            intercept_X = False
                
        return upperLine, lowerLine,intercept_X

    def edgeFinder_intercept_Y(self,image,Y_value1,Y_value2,threadValue):
        data1 = []
        data2 = []
        for x in range(image.shape[1]):  # 列
                # 確保像素值為無符號 8 位整數
                pixel_value1 = int(image[Y_value1, x])  # 轉換為整數
                pixel_value2 = int(image[Y_value2, x])  # 轉換為整數
                if pixel_value1 >= threadValue:
                    pixel_value1 = 1
                    data1.append([x,Y_value1])
                if pixel_value2 >= threadValue:
                    pixel_value2 = 1
                    data2.append([x, Y_value2])
        leftLine = self.lineEquation(data1[0][0],data1[0][1],data2[0][0],data2[0][1])   
        rightLine = self.lineEquation(data1[-1][0],data1[-1][1],data2[-1][0],data2[-1][1])
              
        if leftLine[3] == True and rightLine[3] == True:
            intercept_Y = True
        else:
            intercept_Y = False
                      
        return leftLine, rightLine,intercept_Y

    def poleEquation(self, imagePixel,Y_value1,Y_value2):
        data1 = []
        data2 = []
        for x in range(imagePixel.shape[1]):  # 列
                # 確保像素值為無符號 8 位整數
                pixel_value1 = int(imagePixel[Y_value1, x])  # 轉換為整數
                pixel_value2 = int(imagePixel[Y_value2, x])  # 轉換為整數
                if pixel_value1 == 0:
                    # pixel_value1 = 1
                    data1.append([x,Y_value1])
                if pixel_value2 == 0:
                    # pixel_value2 = 1
                    data2.append([x, Y_value2])
        leftLine = self.lineEquation(data1[0][0],data1[0][1],data2[0][0],data2[0][1])   
        rightLine = self.lineEquation(data1[-1][0],data1[-1][1],data2[-1][0],data2[-1][1])
                
        return leftLine, rightLine
    
    def poleEdgeFinder(self, imagePixel, Y_value1, Y_value2, threadValue):
        data1 = []
        data2 = []
        for x in range(imagePixel.shape[1]):
            pixel_value1 = int(imagePixel[Y_value1,x])
            pixel_value2 = int(imagePixel[Y_value2,x])
            if pixel_value1 <= threadValue:
                data1.append([x,Y_value1])
            if pixel_value2 <= threadValue:
                data2.append([x,Y_value2])
        
        return data1, data2
                

    def findAngle(self,slope):
        theta_rad = math.atan(slope)  # 反正切，得到弧度值
        # 轉換為角度
        theta_deg = math.degrees(theta_rad)
        # 直線與垂直線的夾角
        angle_with_vertical = 90 - theta_deg  # 與垂直線的夾角

        return angle_with_vertical
    
    def releaseCamera(self):
        # 釋放內存並退出相機
        ueye.is_FreeImageMem(self.camera, self.mem_ptr, self.mem_id)
        ueye.is_ExitCamera(self.camera)
    
class MOTORSUBFUNCTION(MOTORCONTROL, OperationLight,REGISTRATION, QObject):
    signalInitFailed = pyqtSignal(int)
    signalProgress = pyqtSignal(str, int)
    signalHomingProgress = pyqtSignal(float)
    
    
    def __init__(self):
        QObject.__init__(self)
        OperationLight.__init__(self)
        self.SupportMove = 'GVL.SupportMove'
        
        self.bConnected = False
        self.fHomeProgress = 0.0
        self.initProgress = 0
        self.bStop = False
        
        global entry
        global target
        
        entry = 0
        target = 0
        # print(self.get_camera_list())
        
        # frontCamera_ID = 0
        frontCamera_ID = 0
        sideCamera_ID = 1
        
        self.cameraCali_Front = imageCalibration(frontCamera_ID,3)
        # self.cameraCali_Side = imageCalibration(sideCamera_ID,2)
        
        # cameraCheck = False
        # while cameraCheck == False:
        #     cameraCheck = self.cameraID_check(self.cameraCali_Front)
        #     if cameraCheck == False:
        #         self.cameraCali_Front.cameraLogOut()
        #         self.cameraCali_Side.cameraLogOut()
        #         frontCamera_ID = 1
        #         sideCamera_ID = 0
        #         self.cameraCali_Front = imageCalibration(frontCamera_ID,3)
        #         self.cameraCali_Side = imageCalibration(sideCamera_ID,2)

    # 獲取相機列表並列印序列號
    def get_camera_list(self):
        num_cameras = ueye.int()
        ueye.is_GetNumberOfCameras(num_cameras)
        camera_list = ueye.UEYE_CAMERA_LIST()
        ueye.is_GetCameraList(camera_list)
        cameras = []
        for i in range(camera_list.nCameras):
            serial_number = camera_list.uci[i].SerNo.decode('utf-8')
            cameras.append(serial_number)
        return cameras

    def cameraID_check(self, camera):
        ueye.is_CaptureVideo(camera.camera, ueye.IS_WAIT)
        sleep(1)  # 等待攝影完成

        # 取得影像數據
        image_data = ueye.get_data(camera.mem_ptr, camera.original_width, \
            camera.original_height, 8, camera.original_width, copy=True)

        # 確保無符號 8 位整數
        image = np.array(image_data, dtype=np.uint8).reshape((camera.original_height, camera.original_width))

        # 縮放圖像至原始尺寸的一半
        self.scaled_image = cv2.resize(image, (camera.original_width // 2, camera.original_height // 2))
        self.scaled_width = camera.original_width // 2
        self.scaled_height = camera.original_height // 2
        
        cv2.imwrite("imageFront.jpg",self.scaled_image)
        
        points = camera.FindCrossPoint('imageFront.jpg')

        CalibrationResult = camera.CameraCalibration(self.scaled_image,points[1],points[2],points[0],points[3])
        corrected_image = CalibrationResult[0]
        
        cv2.imwrite("imageFront_cal.jpg",corrected_image)
        
        # 修改成adaptive threshold image
        src = cv2.imread("imageFront_cal.jpg", cv2.IMREAD_GRAYSCALE)
        dst = cv2.adaptiveThreshold(src, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,7,5)
        cv2.imwrite("imageFrontAdaptive.jpg",dst)
        
        src = cv2.imread("imageFrontAdaptive.jpg", cv2.IMREAD_GRAYSCALE)
        imageSize = src.size
        
        if imageSize < 150000:
            return False
        else:
            return True
        
        
    def sti_init(self):
        # for test
        # while count < 5:
        # self.signalProgress.emit('connecting motor [FLDC_Up]...', 0)
        sleep(0.2)
        self.setInitProgress('connecting motor [FLDC_Up]...')
        # self.signalProgress.emit('connecting motor [BLDC_Up]...', 10)
        sleep(0.2)
        self.setInitProgress('connecting motor [BLDC_Up]...', False)
        # self.signalProgress.emit('connecting motor [FLDC_Down]...', 20)
        # sleep(0.5)
        # self.signalProgress.emit('connecting motor [BLDC_Down]...', 30)
        # sleep(0.5)
        # self.signalProgress.emit('connecting motor [Robot System]...', 40)
        # sleep(0.5)
        # self.signalProgress.emit('Initializing motor [FLDC_Up]...', 50)
        # sleep(0.5)
        # self.signalProgress.emit('Initializing motor [BLDC_Up]...', 60)
        # sleep(0.5)
        # self.signalProgress.emit('Initializing motor [FLDC_Down]...', 70)
        # sleep(0.5)
        # self.signalProgress.emit('Initializing motor [BLDC_Down]...', 80)
        # sleep(0.5)
        # self.signalProgress.emit('Enabling motor...', 90)
        # sleep(0.5)
        # self.signalProgress.emit('Homing process Completed', 100)
        # sleep(0.5)
        
    def setInitProgress(self, msg:str, bSucceed:bool = True):
        # countOfSteps 根據總共的setInitProgress指令次數調整, Fail不計算在內
        countOfSteps = 14
        if self.bStop:
            return False
        
        nStep = int(100 / countOfSteps) + 1
        if bSucceed:
            msg = '[SUCCEED]' + msg
            self.initProgress = min(self.initProgress + nStep, 100)
        else:
            msg = '[ERROR]' + msg
            
            
        self.signalProgress.emit(msg, self.initProgress)
        
        return bSucceed
        
    def onSignal_errMsg(self, msg:str):
        self.setInitProgress(msg, False)
        
    def retryFunc(self, func, startTime, motorName:str):
        endTime = time()
        ret = None
        while endTime - startTime < TIMEOVER_ROBOT:
            try:
                ret = func()
                
            except:
                msg = f'Failed on {motorName}, system will re-try after 3 seconds.'
                print(msg)
                self.setInitProgress(msg, False)
                sleep(3)
            else:
                if isinstance(ret, str):
                    return True, ret
                else:
                    return True
            finally:
                endTime = time()
        
        # self.setInitProgress('Fail to link to robot', False)
        # self.bConnected = False
        if isinstance(ret, str):
            return False, ret
        else:
            return False
            
    def Initialize(self):
        robotCheckStatus = False
        nRetry = 0
        funcRetry = None
        self.initProgress = 0
        startTime = time()
        # while robotCheckStatus is False:
        # try:
        "Setting Motor ID"
        # self.signalProgress.emit('connecting motor [FLDC_Up]...', 0)
        self.FLDC_Up = MOTORCONTROL(1)
        if self.setInitProgress('connecting motor [FLDC_Up]...') == False:
            return
        # self.signalProgress.emit('connecting motor [BLDC_Up]...', 10)
        self.BLDC_Up = MOTORCONTROL(2)
        if self.setInitProgress('connecting motor [BLDC_Up]...') == False:
            return
        # self.signalProgress.emit('connecting motor [FLDC_Down]...', 20)
        self.FLDC_Down = MOTORCONTROL(3)
        if self.setInitProgress('connecting motor [FLDC_Down]...') == False:
            return
        # self.signalProgress.emit('connecting motor [BLDC_Down]...', 30)
        self.BLDC_Down = MOTORCONTROL(4)
        if self.setInitProgress('connecting motor [BLDC_Down]...') == False:
            return
        # self.signalProgress.emit('connecting motor [Robot System]...', 40)
        self.RobotSystem = MOTORCONTROL(5)
        if self.setInitProgress('connecting motor [Robot System]...') == False:
            return
        
        keyMotor = ['FLDC_Up', 'BLDC_Up', 'FLDC_Down', 'BLDC_Down']
        lstMotor = [self.FLDC_Up, self.BLDC_Up, self.FLDC_Down, self.BLDC_Down]
        dicMotor = dict(zip(keyMotor, lstMotor))
            
        for key, motor in dicMotor.items():
            motor.signalInitErrMsg.connect(self.onSignal_errMsg)
            
            ret = self.retryFunc(motor.MotorInitial, startTime, key)
            if self.setInitProgress(f'Initializing motor [{key}]...', ret) == False:
                self.signalInitFailed.emit(1)
                return False
            
            ret, msg = self.retryFunc(motor.MotorDriverEnable, startTime, key)
            if self.setInitProgress(msg, ret) == False:
                self.signalInitFailed.emit(DEVICE_ROBOT)
                return False
        self.DisplaySafe()
        self.setInitProgress('Homing process Completed')

        robotCheckStatus = True
        self.bConnected = True
        print("Surgical robot connect success.")

        "Motor Enable"
        motorEnableStatus = False
        
    def OnSignal_progress(self, progress:float):
        self.fHomeProgress = progress
        self.signalHomingProgress.emit(self.fHomeProgress)
        print(f'subProgress = {progress}')

    
    def FLDC_ButtonDisable(self):
        self.FLDC_Up.MoveRelativeButtonDisable()
        self.FLDC_Down.MoveRelativeButtonDisable()

    def BLDC_ButtonDisable(self):
        self.BLDC_Up.MoveRelativeButtonDisable()
        self.BLDC_Down.MoveRelativeButtonDisable()

    def SetZero(self, progressMaximum:float = None):
        if progressMaximum is not None and progressMaximum > self.fHomeProgress:
            fStep = (progressMaximum - self.fHomeProgress) / 4.0
            
            listStep = [self.fHomeProgress + i * fStep for i in range(0,5)]
            print(f'step = {listStep}')
            self.BLDC_Up.SetPosition()
            self.signalHomingProgress.emit(listStep[1])
            self.BLDC_Down.SetPosition()
            self.signalHomingProgress.emit(listStep[2])
            self.FLDC_Up.SetPosition()
            self.signalHomingProgress.emit(listStep[3])
            self.FLDC_Down.SetPosition()
            self.signalHomingProgress.emit(listStep[4])
            self.fHomeProgress = listStep[4]
        else:
            self.BLDC_Up.SetPosition()
            self.BLDC_Down.SetPosition()
            self.FLDC_Up.SetPosition()
            self.FLDC_Down.SetPosition()
        print("Motor position set to zero!")

    def BLDC_Stop(self):
        self.BLDC_Up.MC_Stop()
        self.BLDC_Down.MC_Stop()
        sleep(0.5)
        self.BLDC_Up.MC_Stop_Disable()
        self.BLDC_Down.MC_Stop_Disable()
        self.BLDC_Up.bMoveRelativeCommandDisable()
        self.BLDC_Down.bMoveRelativeCommandDisable()

    def Home(self, BLDC_Up_Speed, BLDC_Down_Speed, Dir, progressMaximum:float):
        homeSwitch = self.BLDC_Up.homeValue() * self.BLDC_Down.homeValue()
        homeStatus_Enable = False
        while homeSwitch == 0:
            homeSwitch = self.BLDC_Up.homeValue() * self.BLDC_Down.homeValue()
            if homeStatus_Enable == False:
                if self.BLDC_Up.homeValue() == 0:
                    self.BLDC_Up.MoveVelocitySetting(BLDC_Up_Speed, 300, Dir)
                    self.BLDC_Up.bMoveVelocityEnable()
                if self.BLDC_Down.homeValue() == 0:
                    self.BLDC_Down.MoveVelocitySetting(
                        BLDC_Down_Speed, 300, Dir)
                    self.BLDC_Down.bMoveVelocityEnable()
                homeStatus_Enable = True
            else:
                self.fHomeProgress = min(self.fHomeProgress + 0.0005, progressMaximum)
                self.signalHomingProgress.emit(self.fHomeProgress)
                if self.BLDC_Up.homeValue() == 1:
                    self.BLDC_Up.MC_Stop()
                if self.BLDC_Down.homeValue() == 1:
                    self.BLDC_Down.MC_Stop()
                    
        self.fHomeProgress = progressMaximum
        self.signalHomingProgress.emit(self.fHomeProgress)
        self.BLDC_Stop()

    def DualLinearPositionMotion(self, Target, Speed):
        while Target != 0:
            self.BLDC_Up.MoveRelativeSetting(Target, Speed)
            self.BLDC_Down.MoveRelativeSetting(Target, Speed)
            self.BLDC_Up.bDualLinearRelativeEnable()
            while self.BLDC_Up.fbMoveRelative() == False or self.BLDC_Down.fbMoveRelative() == False:
                sleep(0.01)
            self.BLDC_Up.MC_Stop()
            self.BLDC_Down.MC_Stop()
            sleep(0.5)
            self.BLDC_ButtonDisable()
            self.BLDC_Up.MC_Stop_Disable()
            self.BLDC_Down.MC_Stop_Disable()
            Target = 0
        self.BLDC_Stop()

    def HomeLinearMotion(self, shifting_Up, Shifting_Down, speed, progressMaximum:float):
        self.BLDC_Stop()
        "move a relative distance in a straight line"
        self.BLDC_Up.MoveRelativeSetting(shifting_Up, speed)
        self.BLDC_Down.MoveRelativeSetting(Shifting_Down, speed)
        sleep(0.5)
        self.BLDC_Up.bMoveRelativeEnable()
        self.BLDC_Down.bMoveRelativeEnable()
        while self.BLDC_Up.fbMoveRelative() == False or self.BLDC_Down.fbMoveRelative() == False:
            self.fHomeProgress = min(self.fHomeProgress + 0.001, progressMaximum)
            self.signalHomingProgress.emit(self.fHomeProgress)
            sleep(0.01)
            
        self.fHomeProgress = progressMaximum
        self.signalHomingProgress.emit(self.fHomeProgress)
        self.BLDC_Stop()

    def FLDC_Stop(self):
        self.FLDC_Up.MC_Stop()
        self.FLDC_Down.MC_Stop()
        sleep(0.5)
        self.FLDC_Up.MC_Stop_Disable()
        self.FLDC_Down.MC_Stop_Disable()

    def DualRotatePositionMotion(self, Target, Speed):
        while Target != 0:
            self.FLDC_Up.MoveRelativeSetting(Target, Speed)
            self.FLDC_Down.MoveRelativeSetting(Target, Speed)
            sleep(0.5)
            self.FLDC_Up.bDualRotateRelativeEnable()
            while self.FLDC_Up.fbMoveRelative() == False or self.FLDC_Down.fbMoveRelative() == False:
                sleep(0.01)
            self.FLDC_Up.MC_Stop()
            self.FLDC_Down.MC_Stop()
            sleep(0.5)
            self.FLDC_ButtonDisable()
            self.FLDC_Up.MC_Stop_Disable()
            self.FLDC_Down.MC_Stop_Disable()
            Target = 0

    def HomeRotation(self, progressMaximum = None):
        "first positioning"
        homeSwitch = self.FLDC_Up.homeValue() * self.FLDC_Down.homeValue()
        homeStatus_Enable = False
        
        if progressMaximum is not None:
            halfMaximum = self.fHomeProgress + (progressMaximum - self.fHomeProgress) * 0.5
            
        while homeSwitch == 0:
            homeSwitch = self.FLDC_Up.homeValue() * self.FLDC_Down.homeValue()
            if homeStatus_Enable == False:
                if self.FLDC_Up.homeValue() == 0:
                    self.FLDC_Up.MoveVelocitySetting(900, 1200, 1)
                    self.FLDC_Up.bMoveVelocityEnable()
                if self.FLDC_Down.homeValue() == 0:
                    self.FLDC_Down.MoveVelocitySetting(1500, 1200, 1)
                    self.FLDC_Down.bMoveVelocityEnable()
                homeStatus_Enable = True
            else:
                if progressMaximum is not None:
                    self.fHomeProgress = min(self.fHomeProgress + 0.0001, halfMaximum)
                    self.signalHomingProgress.emit(self.fHomeProgress)
                if self.FLDC_Up.homeValue == 1:
                    self.FLDC_Up.MC_Stop()
                if self.FLDC_Down.homeValue == 1:
                    self.FLDC_Down.MC_Stop()
                    
        if progressMaximum is not None:
            self.fHomeProgress = halfMaximum
            self.signalHomingProgress.emit(halfMaximum)
        self.FLDC_Stop()

        "Rotate to a specific angle"
        self.DualRotatePositionMotion(-2000, 400)

        "second positioning"
        homeSwitch = self.FLDC_Up.homeValue() * self.FLDC_Down.homeValue()
        while self.FLDC_Up.homeValue() == 1 or self.FLDC_Down.homeValue() == 1:
            homeSwitch = self.FLDC_Up.homeValue() * self.FLDC_Down.homeValue()
            sleep(0.1)
        homeStatus_Enable = False
        while homeSwitch == 0:
            homeSwitch = self.FLDC_Up.homeValue() * self.FLDC_Down.homeValue()
            if homeStatus_Enable == False:
                if self.FLDC_Up.homeValue() == 0:
                    self.FLDC_Up.MoveVelocitySetting(250, 500, 1)
                    self.FLDC_Up.bMoveVelocityEnable()
                if self.FLDC_Down.homeValue() == 0:
                    self.FLDC_Down.MoveVelocitySetting(250, 500, 1)
                    self.FLDC_Down.bMoveVelocityEnable()
                homeStatus_Enable = True
            else:
                if progressMaximum is not None:
                    self.fHomeProgress = min(self.fHomeProgress + 0.0001, progressMaximum)
                    self.signalHomingProgress.emit(self.fHomeProgress)
                if self.FLDC_Up.homeValue() == 1:
                    self.FLDC_Up.MC_Stop()
                if self.FLDC_Down.homeValue() == 1:
                    self.FLDC_Down.MC_Stop()
        self.FLDC_Stop()

        if progressMaximum is not None:
            self.fHomeProgress = min(self.fHomeProgress + 0.0001, progressMaximum)
            self.signalHomingProgress.emit(self.fHomeProgress)
            
        "Rotate to a specific angle"
        self.FLDC_Up.MoveRelativeSetting(shiftingFLDC_up, 1500)
        self.FLDC_Down.MoveRelativeSetting(shiftingFLDC_Down, 1500)
        self.FLDC_Up.bMoveRelativeEnable()
        self.FLDC_Down.bMoveRelativeEnable()
        while self.FLDC_Up.fbMoveRelative() == False or self.FLDC_Down.fbMoveRelative() == False:
            sleep(0.01)
        self.FLDC_Stop()

    def ReSetMotor(self):
        self.BLDC_Up.MotorInitial()
        self.BLDC_Down.MotorInitial()
        self.FLDC_Up.MotorInitial()
        self.FLDC_Down.MotorInitial()
        self.BLDC_Up.MotorDriverEnable()
        self.BLDC_Down.MotorDriverEnable()
        self.FLDC_Up.MotorDriverEnable()
        self.FLDC_Down.MotorDriverEnable()

    def HomeProcessing(self):
        if self.bConnected == False:
            QMessageBox.critical(None, 'error', 'Robot Connection Failure')
            return False
        else:
            self.DisplayRun()
            self.fHomeProgress = 0.0
            print("Home Processing Started.")
            self.Home(1000, 1000,1, 0.125)  #dir = 1 前進 ; dir = 3 後退
            sleep(1)
            self.HomeLinearMotion(-4500,-4500,1000, 0.25)
            sleep(1)
            self.Home(100, 100,1, 0.375)
            sleep(1)
            self.SetZero(0.5)
            self.HomeLinearMotion(shiftingBLDC_Up, shiftingBLDC_Up, 2500, 0.666)
            sleep(0.1)
            self.HomeRotation(0.832)
            self.ReSetMotor()
            self.SetZero(1.0)
            self.signalHomingProgress.emit(1.0)
            self.DisplaySafe()
        return True
    
    def RollCalibration(self,camera,corrected_image,caliStatus):
        leftLine, rightLine= camera.poleEquation(corrected_image,20,180)
        if leftLine[3] == True or rightLine[3] == True:
            try:
                caliAngle = camera.findAngle(((leftLine[0])+(rightLine[0]))/2)
                print(caliAngle)
                
                if caliAngle >= 0.2 and caliAngle < 40:
                    # 根據取得的歪斜角度進行補償
                    RotationCount_axis1 = -1*(float(caliAngle*(RotationMotorCountPerLoop*RotateGearRatio)/360))
                    self.FLDC_Up.MoveRelativeSetting(RotationCount_axis1,200)
                    self.FLDC_Up.bMoveRelativeEnable()
                    while self.FLDC_Up.fbMoveRelative() != True:
                        caliStatus = False
                elif (180-caliAngle) >= 0.2 and caliAngle > 120:
                    # 根據取得的歪斜角度進行補償
                    RotationCount_axis1 = float((180-caliAngle)*(RotationMotorCountPerLoop*RotateGearRatio)/360)
                    self.FLDC_Up.MoveRelativeSetting(RotationCount_axis1,200)
                    self.FLDC_Up.bMoveRelativeEnable()
                    while self.FLDC_Up.fbMoveRelative() != True:
                        caliStatus = False
                else:
                    caliStatus = True
            except:
                pass
        else:
            caliStatus = True
        
        return caliStatus
    
    def YawCalibration(self,camera, corrected_image,imageWidth,caliStatus):
        leftLine, rightLine= camera.poleEdgeFinder(corrected_image,50,100,50)
        poleWidth = abs(leftLine[1][0] - rightLine[-1][0])
        pole_midLine = leftLine[1][0] + poleWidth/2
        diff_distance = (imageWidth/2 - pole_midLine)*(138/605)
        print(diff_distance)
        if abs(diff_distance) >= 0.5 and abs(diff_distance) < 100:
            diff_angle = math.asin(diff_distance/robotInitialLength)
            caliAngle = diff_angle*180/math.pi
            RotationCount_axis3 = float(caliAngle*(RotationMotorCountPerLoop*RotateGearRatio)/360)
            self.FLDC_Down.MoveRelativeSetting(RotationCount_axis3,500)
            self.FLDC_Down.bMoveRelativeEnable()
            while self.FLDC_Down.fbMoveRelative() != True:
                caliStatus = False
        else:
            caliStatus = True   
            
        return caliStatus   
    
    def PitchCalibration(self,camera, corrected_image):
        caliStatus = False
        upperData, lowerData = camera.poleEdgeFinder(corrected_image,30,130,50)
        diff_distance = (upperData[2][0]-lowerData[2][0])*(138/605)
        print(diff_distance)
        if diff_distance > 0.1 :
            LinearCount_axis2 = diff_distance*LinearMotorCountPerLoop
            self.BLDC_Up.MoveRelativeSetting(LinearCount_axis2, 100)
            self.BLDC_Up.bMoveRelativeEnable()
            while self.BLDC_Up.fbMoveRelative() != True:
                caliStatus = False
        elif diff_distance < -0.1:
            LinearCount_axis4 = diff_distance*LinearMotorCountPerLoop
            self.BLDC_Down.MoveRelativeSetting(LinearCount_axis4, 100)
            self.BLDC_Down.bMoveRelativeEnable()
            while self.BLDC_Down.fbMoveRelative() != True:
                caliStatus = False            
        else:
            caliStatus = True
            
        return caliStatus               
    
    def imageCalibraionProcess_front(self,camera):
        caliStatus = False
        caliStatus_rotate_camera1 = False
        caliStatus_movement_camera1 = False
        while caliStatus == False:
            # 開始攝影
            ueye.is_CaptureVideo(camera.camera, ueye.IS_WAIT)
            sleep(1)  # 等待攝影完成

            # 取得影像數據
            image_data = ueye.get_data(camera.mem_ptr, camera.original_width, \
                camera.original_height, 8, camera.original_width, copy=True)

            # 確保無符號 8 位整數
            image = np.array(image_data, dtype=np.uint8).reshape((camera.original_height, camera.original_width))

            # 縮放圖像至原始尺寸的一半
            self.scaled_image = cv2.resize(image, (camera.original_width // 2, camera.original_height // 2))
            self.scaled_width = camera.original_width // 2
            self.scaled_height = camera.original_height // 2
            
            cv2.imwrite("imageFront.jpg",self.scaled_image)
            
            points = camera.FindCrossPoint('imageFront.jpg')

            CalibrationResult = camera.CameraCalibration(self.scaled_image,points[1],points[2],points[0],points[3])
            corrected_image = CalibrationResult[0]
            imageWidth = CalibrationResult[1]
            
            cv2.imwrite("imageFront_cal.jpg",corrected_image)
            
            # 修改成adaptive threshold image
            src = cv2.imread("imageFront_cal.jpg", cv2.IMREAD_GRAYSCALE)
            dst = cv2.adaptiveThreshold(src, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,7,5)
            cv2.imwrite("imageFrontAdaptive.jpg",dst)

            # 計算校正桿的傾斜角度
            # 取得邊界pixel
            if caliStatus_rotate_camera1 == False:
                caliStatus_rotate_camera1 = self.RollCalibration(camera,dst,caliStatus_rotate_camera1)
                print(f"caliStatus_robot_camera1 :{caliStatus_rotate_camera1}")
                cv2.imwrite("imageFront_calAngle.jpg",dst)
            elif caliStatus_movement_camera1 == False:
                src = cv2.imread("imageFront_cal.jpg", cv2.IMREAD_GRAYSCALE)
                ret, dst = cv2.threshold(src,240,255,cv2.THRESH_BINARY)
                cv2.imwrite("imageFrontThreshold.jpg",dst)
                caliStatus_movement_camera1 = self.YawCalibration(camera,dst,imageWidth,caliStatus_movement_camera1)
                print(f"caliStatus_movement_camera1 :{caliStatus_movement_camera1}")
                if caliStatus_movement_camera1 == True:
                    caliStatus = True
                    self.cameraCali_Front.releaseCamera()
        cv2.imwrite("imageFront_done.jpg",corrected_image)
                    
    def imageCalibraionProcess_side(self,camera):
        caliStatus = False
        caliStatus_rotate_camera1 = False
        # caliStatus_movement_camera1 = False
        while caliStatus == False:
            # 開始攝影
            ueye.is_CaptureVideo(camera.camera, ueye.IS_WAIT)
            sleep(1)  # 等待攝影完成

            # 取得影像數據
            image_data = ueye.get_data(camera.mem_ptr, camera.original_width, \
                camera.original_height, 8, camera.original_width, copy=True)

            # 確保無符號 8 位整數
            image = np.array(image_data, dtype=np.uint8).reshape((camera.original_height, camera.original_width))

            # 縮放圖像至原始尺寸的一半
            self.scaled_image = cv2.resize(image, (camera.original_width // 2, camera.original_height // 2))
            self.scaled_width = camera.original_width // 2
            self.scaled_height = camera.original_height // 2
            
            cv2.imwrite("imageSide.jpg",self.scaled_image)
                    
            points = camera.FindCrossPoint("imageSide.jpg")

            CalibrationResult = camera.CameraCalibration(self.scaled_image,points[0],points[1],points[3],points[2])
            corrected_image = CalibrationResult[0]
            # imageWidth = CalibrationResult[1]
            
            cv2.imwrite("imageSide_cal.jpg",corrected_image)
            
            # 修改成adaptive threshold image
            src = cv2.imread("imageSide_cal.jpg", cv2.IMREAD_GRAYSCALE)
            dst = cv2.adaptiveThreshold(src, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,3,5)
            cv2.imwrite("imageSideAdaptive.jpg",dst)

            # 計算校正桿的傾斜角度
            # 取得邊界pixel
            if caliStatus_rotate_camera1 == False:
                caliStatus_rotate_camera1 = self.PitchCalibration(camera,dst)
                print(f"caliStatus_robot_camera1 :{caliStatus_rotate_camera1}")
            else:
                caliStatus = True
        
    def HomeProcessing_image(self):
        #先執行一般HomeProcessing
        self.HomeProcessing()
        self.imageCalibraionProcess_front(self.cameraCali_Front)
        self.imageCalibraionProcess_side(self.cameraCali_Side)     
        
        return True

    def Upper_RobotMovingPoint(self, PointX, PointY):
        global upper_G_length
        global upper_G_angle

        robotTotalLength = (PointX ** 2 + (PointY)**2)**0.5
        "The distance of the robot needs to travel"
        robotMovingLength = robotTotalLength - robotInitialLength

        rotationTheta = math.atan(PointY/(PointX))
        "The angle of the robot needs to rotate"
        rotationAngle = rotationTheta*180/math.pi

        "the difference length and angle of the continuous point"
        diffLength = robotMovingLength - upper_G_length
        diffAngle = rotationAngle - upper_G_angle

        "update global length and angle"
        upper_G_length = robotMovingLength
        upper_G_angle = rotationAngle

        return diffLength, diffAngle

    def Lower_RobotMovingPoint(self, PointX, PointY):
        global lower_G_length
        global lower_G_angle

        robotTotalLength = (PointX ** 2 + (PointY)**2)**0.5
        "The distance of the robot needs to travel"
        robotMovingLength = robotTotalLength - robotInitialLength

        rotationTheta = math.atan(PointY/(PointX))
        "The angle of the robot needs to rotate"
        rotationAngle = rotationTheta*180/math.pi

        "the difference length and angle of the continuous point"
        diffLength = robotMovingLength - lower_G_length
        diffAngle = rotationAngle - lower_G_angle

        "update global length and angle"
        lower_G_length = robotMovingLength
        lower_G_angle = rotationAngle

        return diffLength, diffAngle

    def MultiRelativeMotion(self, target1, target2, target3, target4, Speed1, Speed2, Speed3, Speed4):
        while target1 != 0 or target2 != 0 or target3 != 0 or target4 != 0:
            self.BLDC_Up.MoveRelativeSetting(target2, Speed2)
            self.BLDC_Down.MoveRelativeSetting(target4, Speed4)
            self.FLDC_Up.MoveRelativeSetting(target1, Speed1)
            self.FLDC_Down.MoveRelativeSetting(target3, Speed3)
            self.FLDC_Up.bMultiMoveRelativeEnable()
            while self.BLDC_Up.fbMoveRelative() == False or self.BLDC_Down.fbMoveRelative() == False or \
                    self.FLDC_Up.fbMoveRelative() == False or self.FLDC_Down.fbMoveRelative() == False:
                sleep(0.1)
            self.BLDC_ButtonDisable()
            self.FLDC_ButtonDisable()
            target1 = 0
            target2 = 0
            target3 = 0
            target4 = 0
            
    def CaptureRealTimePoint(self, percentage):
        entry_full = np.array([5,20.93392833,-85.62637816])
        target_full = np.array([ 35,80.55959477,-126.77388984])
        entry_halt = np.array([5,10.93381232,-85.61114631])
        target_halt = np.array([ 20,72.57378253,-127.63668602])
        pointTemp = np.array(
            [entry_full, target_full, entry_halt, target_halt])
        # pointTemp = self.PlanningPath

        "translate base from ball to robot"
        calibration = np.array([baseShift_X, baseShift_Y, baseShift_Z])
        breathingFull_entry = pointTemp[0]
        breathingFull_target = pointTemp[1]
        breathingHalt_entry = pointTemp[2]
        breathingHalt_target = pointTemp[3]

        breathingFull_entry = breathingFull_entry - calibration
        breathingFull_target = breathingFull_target - calibration
        breathingHalt_entry = breathingHalt_entry - calibration
        breathingHalt_target = breathingHalt_target - calibration
        
        realTimeEntry = breathingHalt_entry + (breathingFull_entry - breathingHalt_entry) * (percentage/100)
        realTimeTarget = breathingHalt_target + (breathingFull_target - breathingHalt_target) * (percentage/100)
        
        return realTimeEntry, realTimeTarget

    def CapturePoint(self, entry_full, target_full, entry_halt, target_halt):
        pointTemp = np.array(
            [entry_full, target_full, entry_halt, target_halt])
        # pointTemp = self.PlanningPath

        "translate base from ball to robot"
        calibration = np.array([baseShift_X, baseShift_Y, baseShift_Z])
        breathingFull_entry = pointTemp[0]
        breathingFull_target = pointTemp[1]
        breathingHalt_entry = pointTemp[2]
        breathingHalt_target = pointTemp[3]

        breathingFull_entry = breathingFull_entry - calibration
        breathingFull_target = breathingFull_target - calibration
        breathingHalt_entry = breathingHalt_entry - calibration
        breathingHalt_target = breathingHalt_target - calibration
        
        return breathingFull_entry, breathingFull_target

    def MoveToPoint(self):
        reachTarget = False
        while reachTarget == False:
            Release = self.plc.read_by_name(self.SupportMove)
            Release = True
            if Release == True:
                "obtain upper point"
                # print(f"Entry point is {self.entryPoint}")
                t_upper = (upperHigh - self.entryPoint[2]) / \
                    (self.targetPoint[2]-self.entryPoint[2])
                upperPointX = self.entryPoint[0] + \
                    (self.targetPoint[0]-self.entryPoint[0])*t_upper
                upperPointY = self.entryPoint[1] + \
                    (self.targetPoint[1]-self.entryPoint[1])*t_upper

                "obtain lower point"
                t = (lowerHigh - self.entryPoint[2]) / \
                    (self.targetPoint[2]-self.entryPoint[2])
                lowerPointX = self.entryPoint[0] + \
                    (self.targetPoint[0]-self.entryPoint[0])*t
                lowerPointY = self.entryPoint[1] + \
                    (self.targetPoint[1]-self.entryPoint[1])*t

                "Calculate rotation and movement of upper layer"
                upperMotion = self.Upper_RobotMovingPoint(upperPointX, upperPointY)
                lowerMotion = self.Lower_RobotMovingPoint(lowerPointX, lowerPointY)

                "robot motion"
                "rotation command"
                RotationCount_axis3 = float(
                    lowerMotion[1]*(RotationMotorCountPerLoop*RotateGearRatio)/360)
                RotationCount_axis1 = float(
                    upperMotion[1]*(RotationMotorCountPerLoop*RotateGearRatio)/360) - RotationCount_axis3
                "Linear motion command"
                LinearCount_axis2 = upperMotion[0]*LinearMotorCountPerLoop
                LinearCount_axis4 = lowerMotion[0]*LinearMotorCountPerLoop
                self.DisplayRun()
                self.MultiRelativeMotion(RotationCount_axis1, LinearCount_axis2,
                                        RotationCount_axis3, LinearCount_axis4, 800, 1300, 800, 1300)
                print("Compensation is Done!")
                reachTarget = True
                self.DisplaySafe()
                
    def MoveToPoint_temp(self):
        OperationLight.DynamicCompensation(self)
        # breathingCompensation = self.plc.read_by_name(self.SupportMove)
        "obtain upper point"
        # print(f"Entry point is {self.entryPoint}")
        t_upper = (upperHigh - self.entryPoint[2]) / \
            (self.targetPoint[2]-self.entryPoint[2])
        upperPointX = self.entryPoint[0] + \
            (self.targetPoint[0]-self.entryPoint[0])*t_upper
        upperPointY = self.entryPoint[1] + \
            (self.targetPoint[1]-self.entryPoint[1])*t_upper

        "obtain lower point"
        t = (lowerHigh - self.entryPoint[2]) / \
            (self.targetPoint[2]-self.entryPoint[2])
        lowerPointX = self.entryPoint[0] + \
            (self.targetPoint[0]-self.entryPoint[0])*t
        lowerPointY = self.entryPoint[1] + \
            (self.targetPoint[1]-self.entryPoint[1])*t

        "Calculate rotation and movement of upper layer"
        upperMotion = self.Upper_RobotMovingPoint(upperPointX, upperPointY)
        lowerMotion = self.Lower_RobotMovingPoint(lowerPointX, lowerPointY)

        "robot motion"
        "rotation command"
        RotationCount_axis3 = float(
            lowerMotion[1]*(RotationMotorCountPerLoop*RotateGearRatio)/360)
        RotationCount_axis1 = float(
            upperMotion[1]*(RotationMotorCountPerLoop*RotateGearRatio)/360) - RotationCount_axis3
        "Linear motion command"
        LinearCount_axis2 = upperMotion[0]*LinearMotorCountPerLoop
        LinearCount_axis4 = lowerMotion[0]*LinearMotorCountPerLoop
        self.DisplayRun()
        self.MultiRelativeMotion(RotationCount_axis1, LinearCount_axis2,
                                RotationCount_axis3, LinearCount_axis4, 800, 1300, 800, 1300)
        print("Compensation is Done!")
        self.DisplaySafe()

    def RealTimeTracking(self,percentage):
        "obtain entry point and target point"
        self.movingPoint = self.CaptureRealTimePoint(percentage)
        self.entryPoint = self.movingPoint[0]
        self.targetPoint = self.movingPoint[1]
        print(f"RTentryPoint is {self.entryPoint}")
        print(f"RTtargetPoint is {self.targetPoint}")
        
    
    def reachable_check(self, entry_full, target_full, entry_halt, target_halt):
        movingPoint = self.CapturePoint(entry_full, target_full, entry_halt, target_halt)
        self.entryPoint = movingPoint[0]  # from robot to entry point
        self.targetPoint = movingPoint[1] # from robot to target point
        "obtain upper point"
        # print(f"Entry point is {self.entryPoint}")
        t_upper = (upperHigh - self.entryPoint[2]) / \
            (self.targetPoint[2]-self.entryPoint[2])
        upperPointX = self.entryPoint[0] + \
            (self.targetPoint[0]-self.entryPoint[0])*t_upper
        upperPointY = self.entryPoint[1] + \
            (self.targetPoint[1]-self.entryPoint[1])*t_upper

        "obtain lower point"
        t = (lowerHigh - self.entryPoint[2]) / \
            (self.targetPoint[2]-self.entryPoint[2])
        lowerPointX = self.entryPoint[0] + \
            (self.targetPoint[0]-self.entryPoint[0])*t
        lowerPointY = self.entryPoint[1] + \
            (self.targetPoint[1]-self.entryPoint[1])*t

        "Calculate rotation and movement of upper layer"
        upperMotion = self.Upper_RobotMovingPoint(upperPointX, upperPointY)
        lowerMotion = self.Lower_RobotMovingPoint(lowerPointX, lowerPointY)

        "robot motion"
        "rotation command"
        RotationCount_axis3 = float(
            lowerMotion[1]*(RotationMotorCountPerLoop*RotateGearRatio)/360)
        RotationCount_axis1 = float(
            upperMotion[1]*(RotationMotorCountPerLoop*RotateGearRatio)/360) - RotationCount_axis3
        "Linear motion command"
        LinearCount_axis2 = upperMotion[0]*LinearMotorCountPerLoop
        LinearCount_axis4 = lowerMotion[0]*LinearMotorCountPerLoop
        
        reachable = True
        if abs(RotationCount_axis1 - RotationCount_axis3) >= 9000:
            reachable = False
        if LinearCount_axis2 >= max_linear_count or LinearCount_axis4 >= max_linear_count:
            reachable = False
        if abs(LinearCount_axis2 - LinearCount_axis4) >= max_linearDiffCount_1:
            reachable = False
        if abs(LinearCount_axis4 - LinearCount_axis2) >= max_linearDiffCount_2:
            reachable = False
        
        if reachable is False:
            print("Cannot reach to the target point!")
            
        return reachable
            
               
    def P2P(self,entry_full, target_full, entry_halt, target_halt):
        "obtain entry point and target point"
        self.movingPoint = self.CapturePoint(entry_full, target_full, entry_halt, target_halt)
        self.entryPoint = self.movingPoint[0]  # from robot to entry point
        self.targetPoint = self.movingPoint[1] # from robot to target point
        # self.absolutePosition()
        self.MoveToPoint()
        
    def breathingCompensation(self):
        "obtain entry point and target point"
        self.movingPoint = self.CaptureRealTimePoint(85)
        self.entryPoint = self.movingPoint[0]  # from robot to entry point
        self.targetPoint = self.movingPoint[1] # from robot to target point
        self.MoveToPoint_temp()

    def P2P_Manual(self, entryPoint, targetPoint):
        "get entry and target points manually."
        self.entryPoint = []
        self.targetPoint = []
        for item in entryPoint:
            self.entryPoint.append(float(item))
        for item in targetPoint:
            self.targetPoint.append(float(item))
        self.MoveToPoint()

    def CycleRun(self, P1, P2, P3, P4, cycleTimes):
        "robot executes cycle run in 4 points"
        try:
            point1 = []
            point2 = []
            point3 = []
            point4 = []
            for item in P1:
                point1.append(float(item))
            for item in P2:
                point2.append(float(item))
            for item in P3:
                point3.append(float(item))
            for item in P4:
                point4.append(float(item))

            PointX = [point1[0], point2[0], point3[0], point4[0]]
            PointY = [point1[1], point2[1], point3[1], point4[1]]
            PointZ = [point1[2], point2[2], point3[2], point4[2]]

            times = 0
            while times < cycleTimes:
                times += 1
                print(f"Repeat times {times}.")
                for index in range(4):
                    self.entryPoint = [PointX[index],
                                       PointY[index], PointZ[index]]
                    self.targetPoint = [PointX[index],
                                        PointY[index], PointZ[index]-20]
                    self.MoveToPoint()
            print("Cycle Run Processing is Done!")
        except:
            # self.DisplayError()
            print("Wrong type. Please try it again.")
            
    def EnableDynamicTrack(self):
        self.DynamicCompensation()
        print("Dynamic Tracking Done!")
               
class LineLaser(MOTORCONTROL, QObject):
    signalInitFailed = pyqtSignal(int)
    signalProgress = pyqtSignal(str, int)
    # signalInhaleProgress = pyqtSignal(bool, float, list)
    signalInhaleProgress = pyqtSignal(bool, float)
    signalExhaleProgress = pyqtSignal(bool, float)
    signalModelPassed = pyqtSignal(bool)
    signalBreathingRatio = pyqtSignal(float)
    signalCycleCounter = pyqtSignal(int)
    signalShowHint = pyqtSignal(str)
    
    def __init__(self):
        QObject.__init__(self)
        
        self.initProgress = 0
        self.bStop = False
        self.receiveData             = []
        self.receiveDataTemp         = None
        self.avgValueList            = []
        self.realTimeHeightAvgValue  = []
        self.laserDataBase           = {}
        self.laserDataBase_filter    = {}
        self.laserDataBase_values    = []
        self.percentageBase          = {}
        self.ret = None
        
    def retryFunc(self, func, startTime, *args):
        endTime = time()
        
        retryTimes = 0
        ret = func(*args)
        if ret < 1:
            while (endTime - startTime) < TIMEOVER_LASER:
                sleep(3)
                ret = func(*args)
                if ret > 1:
                    return ret
                retryTimes += 1
                print(f'laser connection retry {retryTimes} times')
                endTime = time()
            
        return ret
        
        
        
    def setProgress(self, msg:str, bSucceed:bool = True):
        # self.initProgress = inc_progress
        if self.bStop:
            raise ValueError('thread stop')
        
        countOfSteps = 6
        nStep = int(100 / countOfSteps) + 1
        
        if bSucceed:
            self.initProgress = min(self.initProgress + nStep, 100)
        else:
            msg = '[ERROR]' + msg
        self.signalProgress.emit(msg, self.initProgress)
        
    def Initialize(self):
        # Parametrize transmission
        self.scanner_type = ct.c_int(0)
        # Init profile buffer and timestamp info
        self.noProfileReceived = True
        self.exposure_time = 100
        self.idle_time = 3900
        self.timestamp = (ct.c_ubyte*16)()
        self.available_resolutions = (ct.c_uint*4)()
        self.available_interfaces = (ct.c_uint*6)()
        self.lost_profiles = ct.c_int()
        self.shutter_opened = ct.c_double(0.0)
        self.shutter_closed = ct.c_double(0.0)
        self.profile_count = ct.c_uint(0)
        
        self.initProgress = 0

        # Null pointer if data not necessary
        self.null_ptr_short = ct.POINTER(ct.c_ushort)()
        self.null_ptr_int = ct.POINTER(ct.c_uint)()

        # Create instance 
        self.hLLT = llt.create_llt_device(llt.TInterfaceType.INTF_TYPE_ETHERNET)
        print(f'LLT = {self.hLLT}')
        
        startTime = time()
        try:
            # Get available interfaces
            args = (self.hLLT, self.available_interfaces, len(self.available_interfaces))
            func = llt.get_device_interfaces_fast 
            # ret = llt.get_device_interfaces_fast(self.hLLT, self.available_interfaces, len(self.available_interfaces))
            ret = self.retryFunc(func, startTime, *args)
            if ret < 1:
                self.setProgress('Laser Device interface setting......failed', False)
                raise ValueError("Error getting interfaces : " + str(ret))

            # Set IP address
            args = (self.hLLT, self.available_interfaces[0], 0)
            func = llt.set_device_interface
            # ret = llt.set_device_interface(self.hLLT, self.available_interfaces[0], 0)
            ret = self.retryFunc(func, startTime, *args)
            if ret < 1:
                self.setProgress('Laser Device interface setting......succeed', False)
                raise ValueError("Error setting device interface: " + str(ret))

            self.setProgress('Laser Device interface setting......succeed')
            # Connect
            # tryTimes = 0
            # while tryTimes < 5:
            #     ret = llt.connect(self.hLLT)
            #     if ret < 1:
            #         tryTimes += 1
            #         print(f'connection retry {tryTimes} times')
            #         if tryTimes >= 5:
            #             self.setProgress('[ERROR]Laser device connection ......failed', False)
            #             raise ConnectionError("Error connect: " + str(ret))
            #     else:
            #         break
            ret = self.retryFunc(llt.connect, startTime, self.hLLT)
            if ret < 1:
                raise ConnectionError("Error connect: " + str(ret))
            
            self.setProgress('Laser device connection ......succeed')
            # Get available resolutions
            args = (self.hLLT, self.available_resolutions, len(self.available_resolutions))
            func = llt.get_resolutions
            # ret = llt.get_resolutions(self.hLLT, self.available_resolutions, len(self.available_resolutions))
            ret = self.retryFunc(func, startTime, *args)
            if ret < 1:
                self.setProgress('[ERROR]Laser device get resolution ......failed', False)
                raise ValueError("Error getting resolutions : " + str(ret))

            # Set max. resolution
            self.resolution = self.available_resolutions[0]
            args = (self.hLLT, self.resolution)
            func = llt.set_resolution
            # ret = llt.set_resolution(self.hLLT, self.resolution)
            ret = self.retryFunc(func, startTime, *args)
            if ret < 1:
                self.setProgress('[ERROR]Laser device set resolution ......failed', False)
                raise ValueError("Error getting resolutions : " + str(ret))

            self.setProgress('Laser device resolution setting ......succeed')
            
            # Declare measuring data arrays
            self.profile_buffer = (ct.c_ubyte*(self.resolution*64))()
            self.x = (ct.c_double * self.resolution)()
            self.z = (ct.c_double * self.resolution)()
            self.intensities = (ct.c_ushort * self.resolution)()
            
            # Scanner type
            ret = self.retryFunc(llt.get_llt_type, startTime, self.hLLT, ct.byref(self.scanner_type))
            # ret = llt.get_llt_type(self.hLLT, ct.byref(self.scanner_type))
            if ret < 1:
                self.setProgress('[ERROR]Laser device get scanner type ......failed', False)
                raise ValueError("Error scanner type: " + str(ret))

            self.setProgress('Laser device get scanner type ......succeed')
            # Set profile config
            # ret = llt.set_profile_config(self.hLLT, llt.TProfileConfig.PROFILE)
            ret = self.retryFunc(llt.set_profile_config, startTime, self.hLLT, llt.TProfileConfig.PROFILE)
            if ret < 1:
                self.setProgress('[ERROR]Laser device set profile config ......failed', False)
                raise ValueError("Error setting profile config: " + str(ret))
        except ValueError as msg:
            print(msg)
            self.signalInitFailed.emit(DEVICE_LASER)
            return
        except ConnectionError as msg:
            print(msg)
            self.signalInitFailed.emit(DEVICE_LASER)
            return

        self.setProgress('Laser device set profile config ......succeed')
        # Set trigger free run
        # ret = llt.set_feature(self.hLLT, llt.FEATURE_FUNCTION_TRIGGER, llt.TRIG_INTERNAL)
        # if ret < 1:
        #     self.setProgress('[ERROR]Laser device set feature ......failed', False)
        #     raise ValueError("Error setting trigger: " + str(ret))

        # self.setProgress('Laser device set feature ......succeed')
        
        # "arduino connection setting"
        # arduinoConnectStatus = False
        # while arduinoConnectStatus == False:
        #     try:
        #         self.ser = serial.Serial(port='COM4', baudrate=115200, timeout=2)
        #         arduinoConnectStatus = True
        #     except:
        #         self.RobotSystem.DisplayError()
        #         input('Auduino connect fail. Please check it and press "Enter".')
                
        # Plot Initial
        # self.fig = plt.figure()
        # self.plot = self.fig.add_subplot()
        # self.lay = QtWidgets.QVBoxLayout()
        
        # self.RobotSystem = MOTORCONTROL(6)
        # self.RobotSystem.TrackNull()
        
        self.TriggerSetting()
        
    # 計算高度均值
    def CalHeightAvg(self, arr):
        try:
            # nonZeroArray = np.nonzero(arr) # 取得非0的個數
            # sum = 0
            # for index in range(len(arr)):
            #     sum += arr[index]**2
            # squareSum = sum**0.5
            # return squareSum/len(nonZeroArray[0])
            nonZeroArray = arr[np.nonzero(arr)] # 取得非0的個數
            if len(nonZeroArray) > 0:
                # sum = np.sum(nonZeroArray ** 2)
                mean = np.mean(nonZeroArray ** 2)
                # return np.sqrt(sum) / len(nonZeroArray)
                return np.sqrt(mean)
            else:
                return 0
            
        except:
            self.RobotSystem.DisplayError()
            print("Calculate height avg error")
            
    def CheckInhale(self):
        arr = self.GetLaserData()
        if arr is not None:
            arr = arr[laserStartPoint:laserEndPoint]
            arrAvg = self.CalHeightAvg(arr)
            items = list(self.percentageBase.values()) # items = (key, item), key = items[0] = avg
            maxAvg =  items[-1][0]
            minAvg =  items[0][0]
            dis = maxAvg - minAvg
            percentage = ((maxAvg-arrAvg)/dis) * 100
            
            bInhale = False
            if percentage >= INHALE_AREA and percentage <= 100:
                bInhale = True
            elif percentage > 100:
                # 取出percentage中的raw data
                self.laserDataBase_values.append(arr)
                self.CalculateHeightAvg(yellowLightCriteria_LowAccuracy, self.laserDataBase_values)
                
            # lstPercent = list(self.percentageBase.keys())
            # lstAvg = [avg for avg, _ in self.percentageBase.values()]
            # for percent, avg in zip(lstPercent, lstAvg):
            #     print(f'percent = {percent}, avg = {avg}')
            # print('=' * 50)    
            
            # self.signalInhaleProgress.emit(bInhale, percentage, lstPercent)
            self.signalInhaleProgress.emit(bInhale, percentage)
            
            # self.receiveData = arr[laserStartPoint:laserEndPoint]
            # self.CalculateRealTimeHeightAvg()
            # # print(self.realTimeHeightAvgValue)
            
            # realTimeAvgValue = self.realTimeHeightAvgValue[0]
            # # 燈號控制
            # self.avgValueList = []
            # # for item in self.percentageBase.items():
            # for item in self.percentageBase.values():
            #     # self.avgValueList.append(list(item)[1])
            #     self.avgValueList.append(list(item)[0])
                
            # # minValue = min(self.avgValueList)
            # # maxValue = max(self.avgValueList)
            # self.avgValueList = sorted(self.avgValueList, reverse=True)
            # percentage = self.PercentagePrediction(realTimeAvgValue)
            # if percentage:
            #     print(f'percentage:{percentage:.1f}')
            #     bInhale = False
            #     if percentage > 90 and percentage <= 100:
            #         bInhale = True
            #     self.signalInhaleProgress.emit(bInhale)
            
    def CheckExhale(self):
        arr = self.GetLaserData()
        if arr is not None:
            arr = arr[laserStartPoint:laserEndPoint]
            arrAvg = self.CalHeightAvg(arr)
            items = list(self.percentageBase.values()) # items = (key, item), key = items[0] = avg
            maxAvg =  items[-1][0]
            minAvg =  items[0][0]
            dis = maxAvg - minAvg
            percentage = ((maxAvg-arrAvg)/dis) * 100
            
            bExhale = False
            if percentage <= EXHALE_AREA and percentage >= 0:
                bExhale = True
            elif percentage < 0:
                # 取出percentage中的raw data
                self.laserDataBase_values.append(arr)
                self.CalculateHeightAvg(yellowLightCriteria_LowAccuracy, self.laserDataBase_values)
            self.signalExhaleProgress.emit(bExhale, percentage)
            
    # private function
    # filter out range data from model
    def filterOutRange(self, indexes):
        if isinstance(indexes, (tuple, list, np.ndarray)):
            if len(indexes) < 2:
                print('too less number parameters in function "filterOutRange"')
            else:
                indexMin = min(indexes)
                indexMax = max(indexes)
                lstDatabase = list(self.percentageBase.items())[indexMin:indexMax + 1]
                self.percentageBase = dict(lstDatabase)
                
                
    # 得到percentageBase中超過90與95%的高度平均值
    def GetAvg(self, arr):
        avgBase = list(arr.values())
        percentage95 = []
        for items in avgBase:
            if items > 95:
                percentage95.append(items)
        value90 = min(avgBase)
        value95 = min(percentage95)
        return  value90, value95
    
    def GetLaserData(self):
        receiveData = None
        
        # profileGetStatus = False
        # while profileGetStatus is False:
        self.ret = llt.get_actual_profile(self.hLLT, self.profile_buffer, len(self.profile_buffer), llt.TProfileConfig.PROFILE,
                                    ct.byref(self.lost_profiles))
        if self.ret != len(self.profile_buffer):
                #當沒有資料顯示NO NEW PROFILE
            if (self.ret == llt.ERROR_PROFTRANS_NO_NEW_PROFILE):
                # print("NO NEW PROFILE")
                sleep((self.idle_time + self.exposure_time)/100000)
                #輸入q跳出迴圈
                if keyboard.is_pressed("q"):
                    self.noProfileReceived = False
                else :
                    pass
            else:
                    raise ValueError("Error get profile buffer data: " + str(self.ret))
                    self.noProfileReceived = False
        else:
        
            #將RawData轉成距離值
            #resolution ln:50
            #scanner_type ln:62
            #每點的距離值抓取z每點位置抓x
            self.ret = llt.convert_profile_2_values(self.hLLT, self.profile_buffer, self.resolution, llt.TProfileConfig.PROFILE, self.scanner_type, 0, 1,
                                    self.null_ptr_short, self.intensities, self.null_ptr_short, self.x, self.z, self.null_ptr_int, self.null_ptr_int)
            #顯示Z軸第一個點
            # for i in range(laserStartPoint,laserEndPoint):
            #     receiveData.append(self.z[i])
            # for i in range(len(self.z)):
            #     receiveData.append(self.z[i])
            receiveData = np.array(self.z)
            #延遲0.1s
            sleep(0.01)
        return receiveData

    def Get_Key(self, val):
        for key, value in self.percentageBase.items():
            if val == value[0]:
                return key
            
    def GetClosestAvg(self, avg):
        if isinstance(avg, (tuple, list, np.ndarray)):
            try:
                if len(avg) >= 2:
                    # avgInhale = min(avg)
                    # avgExhale = max(avg)
                    avg = np.array(avg)
                    
                    idInhale = np.argmin(avg)
                    idExhale = np.argmax(avg)
                    
                    avgInhale = avg[idInhale]
                    avgExhale = avg[idExhale]
            
                    avgList = []
                    for keyAvg, _ in self.percentageBase.values():
                        avgList.append(keyAvg)
                    
                    avgList = np.array(avgList)
                    diffInhale = np.abs(avgList - avgInhale)
                    diffExhale = np.abs(avgList - avgExhale)
                    
                    indexInhale = np.argmin(diffInhale)
                    indexExhale = np.argmin(diffExhale)
                    
                    avgInhale = avgList[indexInhale]
                    avgExhale = avgList[indexExhale]
                    
                    self.filterOutRange((indexInhale, indexExhale))
                    
                    avg[idInhale] = avgInhale
                    avg[idExhale] = avgExhale
                    
                    return avg
            except Exception as msg:
                print(msg)
        
        avgList = []
        for keyAvg, _ in self.percentageBase.values():
            avgList.append(keyAvg)
            
        avgList = np.array(avgList)
        diff = np.abs(avgList - avg)
        
        avgClosest:float = avgList[np.argmin(diff)]
        
        return avgClosest
            
    def GetPercentFromAvg(self, avg, bCutInRange = False):
        avg = np.array(avg).flatten()
        # if bCutInRange and isinstance(avg, tuple) and len(avg) >= 2:
        #     filterFront = []
        #     filterBack = []
        #     for key, (keyAvg, _) in self.percentageBase.items():
        #         if keyAvg < avg[0]:
        #             filterFront.append(key)
        #         elif keyAvg > avg[1]:
        #             filterBack.append(key)
            
        #     if len(filterFront) > 2:
        #         filterFront.pop(-1)
                
        #     if len(filterBack) > 2:
        #         filterBack.pop(0)
                
        #     lstFilter = np.concatenate((filterFront, filterBack))
                
        #     for key in lstFilter:
        #         del self.percentageBase[key]
        
        avgRange = self.GetClosestAvg(avg)
            
        items = list(self.percentageBase.values())
        maxAvg =  items[-1][0]
        minAvg =  items[0][0]
        dis = maxAvg - minAvg
        percentage = 0
        
        if dis > 0:
            
            if isinstance(avgRange, np.ndarray):
                # avgInhale, avgExhale = avgRange
                
                # percentageInhale = ((maxAvg - avgInhale) / dis) * 100
                # lstPercent = [percentageInhale]
                
                lstPercent = []
                for avg in avgRange:
                    percent = ((maxAvg - avg) / dis) * 100
                    lstPercent.append(percent)
                    
                # percentageExhale = ((maxAvg - avgExhale) / dis) * 100
                # lstPercent.append(percentageExhale)
                
                return lstPercent
            else:
                percentage = ((maxAvg - avg) / dis) * 100
        
        return percentage               
    
    def TriggerSetting(self):
        try:
            #Set trigger mod-----------------------------------------------------------------------------------------------
            #Trigger mode
            #llt.TRIG_POLARITY_HIGH = pos.
            #llt.TRIG_POLARITY_LOW = neg.

            #llt.TRIG_INTERNAL
            #llt.TRIG_MODE_EDGE
            #llt.TRIG_MODE_PULSE
            #llt.TRIG_MODE_GATE
            #llt.TRIG_MODE_ENCODER

            #Ex.
            #llt.TRIG_MODE_EDGE | llt.TRIG_POLARITY_HIGH = pos. edge
            #llt.TRIG_MODE_PULSE | llt.TRIG_POLARITY_HIGH = pos. pulse

            #Trigger source
            #llt.TRIG_INPUT_RS422
            #llt.TRIG_INPUT_DIGIN 

            TriggerMode = llt.TRIG_MODE_GATE | llt.TRIG_POLARITY_LOW | llt.TRIG_INPUT_DIGIN | llt.TRIG_EXT_ACTIVE

            ret = llt.set_feature(self.hLLT, llt.FEATURE_FUNCTION_TRIGGER, TriggerMode)
            if ret < 1:
                self.setProgress('[ERROR]Laser device set feature trigger......failed', False)
                raise ValueError("Error setting trigger: " + str(ret))
            
            #Digital input mode
            #llt.MULTI_DIGIN_ENC_INDEX = encoder+reset
            #llt.MULTI_DIGIN_ENC_TRIG = encoder+Trigger
            #llt.MULTI_DIGIN_TRIG_ONLY = Trigger
            #llt.MULTI_DIGIN_TRIG_UM = user modes + trigger
            #llt.MULTI_DIGIN_TS = Time Stamp
            #llt.MULTI_DIGIN_UM = user modes
            #Digital input logic
            #llt.MULTI_LEVEL_24V
            #llt.MULTI_LEVEL_5V

            MultiPort = llt.MULTI_DIGIN_TRIG_ONLY | llt.MULTI_LEVEL_5V

            ret = llt.set_feature(self.hLLT, llt.FEATURE_FUNCTION_DIGITAL_IO, MultiPort)
            if ret < 1:
                self.setProgress('[ERROR]Laser device set feature digital IO......failed', False)
                raise ValueError("Error setting trigger: " + str(ret))
            #--------------------------------------------------------------------------------------------------------------

            # Set exposure time
            ret = llt.set_feature(self.hLLT, llt.FEATURE_FUNCTION_EXPOSURE_TIME, self.exposure_time)
            if ret < 1:
                self.setProgress('[ERROR]Laser device set feature exposure time......failed', False)
                raise ValueError("Error setting exposure time: " + str(ret))

            # Set idle time
            ret = llt.set_feature(self.hLLT, llt.FEATURE_FUNCTION_IDLE_TIME, self.idle_time)
            if ret < 1:
                self.setProgress('[ERROR]Laser device set feature idle time......failed', False)
                raise ValueError("Error idle time: " + str(ret))

            #Wait until all parameters are set before starting the transmission (this can take up to 120ms)
            sleep(0.12)

            # Start transfer
            ret = llt.transfer_profiles(self.hLLT, llt.TTransferProfileType.NORMAL_TRANSFER, 1)

            if ret < 1:
                raise ValueError("Error starting transfer profiles: " + str(ret))
            
            self.setProgress('Laser device set feature ......succeed')
        except:
            print("Laser connect fail.")

    
    def ModelBuilding(self):
        # # self.TriggerSetting()
        if self.receiveDataTemp is None:
            # self.receiveData = []
            # ret = llt.get_actual_profile(self.hLLT, self.profile_buffer, len(self.profile_buffer), llt.TProfileConfig.PROFILE,
            #                             ct.byref(self.lost_profiles))
            # if ret != len(self.profile_buffer):
            #     #當沒有資料顯示NO NEW PROFILE
            #     if (ret == llt.ERROR_PROFTRANS_NO_NEW_PROFILE):
            #         # print("NO NEW PROFILE")
            #         sleep((self.idle_time + self.exposure_time)/100000)
            #         #輸入q跳出迴圈
            #         if keyboard.is_pressed("q"):
            #             self.noProfileReceived = False
            #         else :
            #             pass
            #     else:
            #             raise ValueError("Error get profile buffer data: " + str(ret))
            #             self.noProfileReceived = False
            # else:
            #     #將RawData轉成距離值
            #     #resolution ln:50
            #     #scanner_type ln:62
            #     #每點的距離值抓取z每點位置抓x
            #     self.ret = llt.convert_profile_2_values(self.hLLT, self.profile_buffer, self.resolution, llt.TProfileConfig.PROFILE, self.scanner_type, 0, 1,
            #                             self.null_ptr_short, self.intensities, self.null_ptr_short, self.x, self.z, self.null_ptr_int, self.null_ptr_int)
            #     #顯示Z軸第一個點
            #     dataTemp = []
            
            
            # # dataTemp = self.GetLaserData()
        
            # # for i in range(laserStartPoint,laserEndPoint):
            # #     dataTemp.append(self.z[i])
            self.receiveDataTemp = self.GetLaserData()
            if self.receiveDataTemp is None:
                return []
        
        
        self.receiveData = self.receiveDataTemp[laserStartPoint:laserEndPoint]  
        self.receiveDataTemp = None
        # self.receiveData = dataTemp[laserStartPoint:laserEndPoint + 1]           
        # print(receiveData)
        #延遲0.1s
        sleep(0.01)

        # self.DataBaseChecking()
        return self.receiveData
    
    def ModelAnalyze(self, dicData:dict):
        tStartInhale = list(dicData.keys())[0]
        tEndInhale = tStartInhale
        bInStable = False
        listInhale = []
        listInhaleTemp = []
        for i, (tTime, data) in enumerate(dicData.items()):
            avg = self.CalHeightAvg(data)
            if i == 0:
                avgMean = avg
                continue
            
            if avg:
                # 檢查data的平均是否停留在一個區間內3秒不動，是就紀錄下平均值
                if abs(avg - avgMean) < gVars['toleranceLaserData']:
                    if bInStable == False:
                        tStartInhale = tTime
                        bInStable = True
                    listInhaleTemp.append(avg)
                    self.signalCycleCounter.emit(tTime - tStartInhale)
                elif bInStable:
                    if tTime - tStartInhale > 3000:
                        listInhale.append(listInhaleTemp)
                        listInhaleTemp = []
                    bInStable = False
                    self.signalCycleCounter.emit(0)
                else:
                    listInhaleTemp = []
                avgMean = avg
        
        if len(listInhale) >= 2:
            
            if listInhale[0][0] > listInhale[1][0]:
                valInhale = min(listInhale[1])
                valExhale = max(listInhale[0])
            else:
                valInhale = min(listInhale[0])
                valExhale = max(listInhale[1])
            
            # mean = (np.mean(listInhale[1]), np.mean(listInhale[2]))
           
            return (valInhale, valExhale)
       
        return None
                
    def DataBaseChecking(self,receiveData):  # make sure whether data lost
        try:
            # for item in receiveData:
            #     for j in range(1,(laserEndPoint-laserStartPoint)):
            #         currentTemp = abs(item[j]-item[j-1])
            #         if currentTemp > 10:
            #             error = 10/0
            for item in receiveData.values():
                for j in range(1,(laserEndPoint-laserStartPoint)):
                    currentTemp = abs(item[j]-item[j-1])
                    if currentTemp > 10:
                        error = 10/0
            print("Model Base Checking done!")
            # self.signalModelPassed.emit(True)
            # QMessageBox.information(None, 'Model Building Succeed', 'Model Base Checking done!')
        except:
            print("Model Building Fail")
            print("Please try to build chest model again.")
            self.signalModelPassed.emit(False)
            # QMessageBox.critical(None, 'Model Building Failed', 'Please try to build chest model again.')
            # self.ModelBuilding()
            
    

    # def RealTimeHeightAvg(self,yellowLightCriteria,greenLightCriteria):
    def RealTimeHeightAvg(self):
        # self.triggerSetting()
        # self.receiveData = []
        # meanPercentage = 0
        # ret = llt.get_actual_profile(self.hLLT, self.profile_buffer, len(self.profile_buffer), llt.TProfileConfig.PROFILE,
        #                             ct.byref(self.lost_profiles))
        # if ret != len(self.profile_buffer):
        #     #當沒有資料顯示NO NEW PROFILE
        #     if (ret == llt.ERROR_PROFTRANS_NO_NEW_PROFILE):
        #         # print("NO NEW PROFILE")
        #         sleep((self.idle_time + self.exposure_time)/100000)
        #         #輸入q跳出迴圈
        #         if keyboard.is_pressed("q"):
        #             self.noProfileReceived = False
        #         else :
        #             pass
        #     else:
        #             raise ValueError("Error get profile buffer data: " + str(ret))
        #             self.noProfileReceived = False
        # else:
        #     #將RawData轉成距離值
        #     #resolution ln:50
        #     #scanner_type ln:62
        #     #每點的距離值抓取z每點位置抓x
        #     self.ret = llt.convert_profile_2_values(self.hLLT, self.profile_buffer, self.resolution, llt.TProfileConfig.PROFILE, self.scanner_type, 0, 1,
        #                             self.null_ptr_short, self.intensities, self.null_ptr_short, self.x, self.z, self.null_ptr_int, self.null_ptr_int)
        #     # print(receiveData)
        #     #延遲0.1s
        #     dataTemp = []
        #     for i in range(laserStartPoint,laserEndPoint):
        #         dataTemp.append(self.z[i])
            # self.receiveData.append(dataTemp)
            
        if self.receiveDataTemp is None:
            self.receiveDataTemp = self.GetLaserData()
            if self.receiveDataTemp is None:
                return 0
        
        self.receiveData = self.receiveDataTemp[laserStartPoint : laserEndPoint + 1]
        self.receiveDataTemp = None
        # Rearrange data
        # self.DataRearrange(self.receiveData)
        self.CalculateRealTimeHeightAvg()
        # print(self.realTimeHeightAvgValue)
        
        realTimeAvgValue = self.realTimeHeightAvgValue[0]
        # 燈號控制
        self.avgValueList = []
        # for item in self.percentageBase.items():
        for item in self.percentageBase.values():
            # self.avgValueList.append(list(item)[1][0])
            avg, _ = item
            # self.avgValueList.append(item)
            self.avgValueList.append(avg)
        # minValue = min(self.avgValueList)
        # maxValue = max(self.avgValueList)
        self.avgValueList = sorted(self.avgValueList, reverse=True)
        
        meanPercentage = self.PercentagePrediction(realTimeAvgValue)
        # try:
        #     if meanPercentage >= yellowLightCriteria and  meanPercentage < greenLightCriteria:
        #         # self.RobotSystem.TrackYellow()
        #         print("黃燈")
        #         print(meanPercentage)
        #     elif meanPercentage > greenLightCriteria:
        #         # self.RobotSystem.TrackGreen()
        #         print("綠燈")
        #         print(meanPercentage)
        #     else:
        #         # self.RobotSystem.TrackRed()
        #         # self.ser.write(b'red\n')
        #         pass
        
        sleep(0.01)
        if meanPercentage is not None:
            self.signalBreathingRatio.emit(meanPercentage)
        return meanPercentage
        
        # except:
        #     # self.RobotSystem.DisplayError()
        #     print("Realtime track error")
            
                    
    def PercentagePrediction(self,realTimeAvgValue):
        try:
            # 找出在哪兩條Avg的範圍內
            rangeAvgValue = []
            search = True
            for i in range(1,len(self.avgValueList)):
                if self.avgValueList[i-1] > realTimeAvgValue and self.avgValueList[i] < realTimeAvgValue and search is True:
                    rangeAvgValue.append(self.avgValueList[i-1])
                    rangeAvgValue.append(self.avgValueList[i])
                    search = False
            
            # 取得兩條Avg的raw data
            if len(rangeAvgValue) == 2:
                # for item in self.percentageBase.values():
                #     if item[0] == rangeAvgValue[0]:
                #         lowerLaserRawData = item[1]
                #         lowerTempValue = item
                #     elif item[0] == rangeAvgValue[1]:
                #         upperLaserRawData = item[1]                                                 
                #         upperTempValue = item
                for i, items in enumerate(self.percentageBase.values()):
                    avg, item = items
                    if avg == rangeAvgValue[0]:
                        lowerLaserRawData = item
                        lowerTempValue = items
                    elif avg == rangeAvgValue[1]:
                        upperLaserRawData = item                                                 
                        upperTempValue = items
                    
                # 線性內插，找出各點的比例值
                pointPercentage = []
                # 取得低線與高線的點位比例
            
                lowerPointPercentage = self.Get_Key(lowerTempValue[0])
                upperPointPercentage = self.Get_Key(upperTempValue[0])
                # lowerPointPercentage = rangeAvgValue[0]
                # upperPointPercentage = rangeAvgValue[1]
                diffPointPercentage = upperPointPercentage - lowerPointPercentage # x-y
                # print(f'diff = {diffPointPercentage}')
                try:
                    for i in range(laserEndPoint-laserStartPoint):
                        dis = upperLaserRawData[i] - lowerLaserRawData[i] #a-b
                        if dis != 0:
                            # diff = upperLaserRawData[i] - self.receiveData[0][i] #a-c
                            diff = upperLaserRawData[i] - self.receiveData[i] #a-c
                            if abs(diff) <=2:
                                diffPercentage = diff/dis #(a-c)/(a-b)
                                pointPercentage.append(upperPointPercentage - diffPointPercentage*diffPercentage)
                    if len(pointPercentage) > 0:
                        meanPercentage = np.mean(pointPercentage)
                    else:
                        return 0
                except:
                    print("Predict percentage error")
            
            else:
                meanPercentage = 0
        
            return meanPercentage    
        except:
            pass
        
        
    def CloseLaser(self):
        if hasattr(self, 'ret') and self.ret is not None:
            if self.ret & llt.CONVERT_X == 0 or self.ret & llt.CONVERT_Z == 0 or self.ret & llt.CONVERT_MAXIMUM == 0:
                raise ValueError("Error converting data: " + str(self.ret))

        if hasattr(self, 'profile_buffer'):
            # Output of profile count
            for i in range(16):
                self.timestamp[i] = self.profile_buffer[self.resolution * 64 - 16 + i]

            llt.timestamp_2_time_and_count(self.timestamp, ct.byref(self.shutter_opened), ct.byref(self.shutter_closed), ct.byref(self.profile_count))

            # Stop transmission
            self.ret = llt.transfer_profiles(self.hLLT, llt.TTransferProfileType.NORMAL_TRANSFER, 0)
            if self.ret < 1:
                raise ValueError("Error stopping transfer profiles: " + str(self.ret))

            # Disconnect
            self.ret = llt.disconnect(self.hLLT)
            if self.ret < 1:
                raise ConnectionAbortedError("Error while disconnect: " + str(self.ret))

        # Delete
        self.ret = llt.del_device(self.hLLT)
        if self.ret < 1:
            raise ConnectionAbortedError("Error while delete: " + str(self.ret))
        
    def DataRearrange(self,receiveData:dict, yellowLightCriteria, greenLightCriteria): #如果有重複的數值，則刪除
        self.laserDataBase = {} 
        iterItem = iter(receiveData.items())
        key, item = next(iterItem)
        self.laserDataBase[key] = item
        
        for key, item in iterItem:
            
            lastItem = list(self.laserDataBase.values())[-1]
            listTolerance = np.abs(np.array(item) - np.array(lastItem))
            meanTolerance = np.mean(listTolerance)
            
            if meanTolerance > laserDataRepeatRange:
                self.laserDataBase[key] = item

        if len(self.laserDataBase) > 5:
            self.DataFilter(yellowLightCriteria)
            return True
        
        return False
        
    def DataCheckCycle(self, laserData:dict = None, nInitTolerance:int = None):
        # arrMean = []
        if laserData is None:
            # laserData = self.laserDataBase_filter
            laserData = self.laserDataBase_filter
            
        countCycle = 0
        slopeLast = 0
        timeDelta = 0
        subData = []
        lstSlope = []
        lstTime = []
        lstMax = []
        lstMin = []
        
        for i, (tTime, item) in enumerate(laserData.items()):
            # mean = np.mean(item)
            mean = self.CalHeightAvg(item)
            if i == 0:
                timeDelta = tTime
            else:
                # 計資料段的時間總和，每一秒鐘(1000ms)為一個偵測斜率變化量的區間
                timeDelta = np.diff(lstTime).sum()
                
                # 初始化階段，要計算斜率變化，至少要有兩筆以上的資料，小於兩筆或一秒鐘以內區間直接加入
                if timeDelta < 1000 or len(subData) < 2:
                    # subData.append(arrMean[i])
                    subData.append(mean)
                    lstTime.append(tTime)
                    
                else:
                    # 紀錄累積時間至少達到一秒
                    xAxis = np.arange(len(subData))
                    # 計算多項式逼近的一維參數，分別為斜率和截距
                    slope, intercept = np.polyfit(xAxis, subData, 1)
                    # 計算斜率變化量
                    slopeDiff = slope - slopeLast
                    
                    # 當前斜率與上一次斜率發生正負交錯時，代表有峰值或低波谷
                    if slopeLast * slope < 0:
                        countCycle += 1
                        # 當前斜率為負，前一次為正，代表是波峰，因此找最大值；相反為低谷，找最小值
                        # 並且紀錄當時的斜率變化量，供後面計算過濾
                        if slope < 0:
                            # find maximum value
                            timeInMax = lstTime[np.argmax(subData)]
                            lstMax.append((max(subData), slopeDiff, timeInMax))
                        else:
                            timeInMin = lstTime[np.argmin(subData)]
                            lstMin.append((min(subData), slopeDiff, timeInMin))
                    slopeLast = slope
                    lstSlope.append(slope)
                    
                    # pop掉區間中的最早資料，並加入最新資料，一進一出，並計算當前時間區段是否滿足最少一秒鐘的條件
                    
                    lstTime.pop(0)
                    lstTime.append(tTime)
                    subData.pop(0)
                    subData.append(mean)
            
        self.slopeData = lstSlope
        
        # 每兩個斜率波形變化(波峰/低谷)，代表一個cycle
        cycle = (countCycle / 2)
        bValid = False
        
        # 初始容許值是否設定：初始容許值用於在還沒完成建模時，初步估算使用
        # 因建模完成的cycle有可能比原本的少(部分資料被過濾)
        if nInitTolerance is not None:
            if cycle >= nInitTolerance:
                bValid = True
        elif cycle >= nValidCycle:
            bValid = True
        
        
        lengthMax = len(lstMax)
        lengthMin = len(lstMin)    
        
        if lengthMax == 0 or lengthMin == 0:
            return False, [], []
        
        lstMax = np.array(lstMax)
        lstMin = np.array(lstMin)
        
        # 資料均值的最大 / 最小值數量，必須是成對的，把較多的一邊過濾
        if lengthMax > lengthMin:
            lstMax = lstMax[:lengthMin]
        elif lengthMax < lengthMin:
            lstMin = lstMin[:lengthMax]
        
        # 將最大 / 最小值合併成一個陣列
        mergeAvg = list(zip(lstMin[:, 0], lstMax[:, 0]))
        
        # 分離出對應的斜率變化量為另一個陣列
        lstSlope = np.array(list(zip(lstMin[:, 1], lstMax[:, 1])))
        
        lstTime = list(zip(lstMin[:, 2], lstMax[:, 2]))
        
        # 當斜率變化量小於threshold時，才視為合法的資料
        lstAvg = [[x, y] for i, (x, y) in enumerate(mergeAvg) if (np.abs(lstSlope[i, :]) < BreathingCycle_Slope_Threshold).all()]
        lstTime = [[x, y] for i, (x, y) in enumerate(lstTime) if (np.abs(lstSlope[i, :]) < BreathingCycle_Slope_Threshold).all()]
        
        # 平坦化成一維陣列
        lstAvg = np.array(lstAvg).flatten()
        lstTime = np.array(lstTime).flatten() * 0.001
        lstTime = sorted(lstTime)
        
        return bValid, lstAvg, lstTime
        
                    
    def DataFilter(self,yellowLightCriteria): #將高頻的數值刪除
        self.laserDataBase_filter = {}
        # for lineNum in range(len(self.laserDataBase)):
        #     ignorePointTemp = []
        #     ignorePointTemp = lowPass(self.laserDataBase[lineNum])
        #     self.laserDataBase_filter[lineNum]=ignorePointTemp
        for i, (key, item) in enumerate(self.laserDataBase.items()):
            ignorePointTemp = []
            ignorePointTemp = lowPass(item)
            self.laserDataBase_filter[key]=ignorePointTemp
            
        if len(self.laserDataBase_filter) > 5:
            self.CalculateHeightAvg(yellowLightCriteria)
            
    def CalculateHeightAvg(self, yellowLightCriteria, dataAddition:list = None):  #得到相對應的percentage
        heightAvg = {}
        # for lineNum in range(len(self.laserDataBase_filter)):
        #     X = np.array(self.laserDataBase_filter[lineNum])
        #     heightAvg[self.CalHeightAvg(X)] = X
        #     # heightAvg.append(getChestProfile.calHeightAvg(X))
        try:
            for item in self.laserDataBase_filter.values():
                X = np.array(item)
                avg = self.CalHeightAvg(X)
                if avg > 0:
                    heightAvg[avg] = X
                # heightAvg.append(getChestProfile.calHeightAvg(X))
            if dataAddition is not None:
                for data in dataAddition:
                    data = np.array(data)
                    avg = self.CalHeightAvg(data)
                    if avg > 0:
                        heightAvg[avg] = data

            maxAvg =  max(list(heightAvg.keys()))
            minAvg =  min(list(heightAvg.keys()))
            dis = maxAvg - minAvg
            self.percentageBase = {}
            # for item in list(heightAvg.items()):
            #     avg = list(item)[0]
            #     percentage = ((maxAvg-avg)/dis)*100
            #     # if self.percentage >= yellowLightCriteria:
            #     self.percentageBase[percentage] = item
            for item in heightAvg.items():
                avg, _ = item
                percentage = ((maxAvg-avg)/dis)*100
                # if self.percentage >= yellowLightCriteria:
                self.percentageBase[percentage] = item
            self.percentageBase = dict(sorted(self.percentageBase.items(), key=lambda x:x[0], reverse =True))
        # print(self.percentageBase)
        except Exception as msg:
            print(msg)
        
    def CalculateRealTimeHeightAvg(self):
        self.realTimeHeightAvgValue = []
        valueTemp = self.CalHeightAvg(self.receiveData)
        self.realTimeHeightAvgValue.append(valueTemp)
        
    def FilterDataByAvgRange(self, avgMax, avgMin, yellowLightCriteria = 0):
        filterData = dict(filter(lambda x:x[1][0] <= avgMax and x[1][0] >= avgMin, self.percentageBase.items()))
        self.laserDataBase_filter = dict(((avg, value) for _, (avg, value) in filterData.items()))
        self.CalculateHeightAvg(yellowLightCriteria)
            
    def PlotProfile(self): 
        receiveData = []
        output = []
        profileGetStatus = False
        while profileGetStatus is False:
            self.ret = llt.get_actual_profile(self.hLLT, self.profile_buffer, len(self.profile_buffer), llt.TProfileConfig.PROFILE,
                                        ct.byref(self.lost_profiles))
            if self.ret != len(self.profile_buffer):
                #當沒有資料顯示NO NEW PROFILE
                profileGetStatus = False
            else:
                profileGetStatus = True
        
        #將RawData轉成距離值
        #resolution ln:50
        #scanner_type ln:62
        #每點的距離值抓取z每點位置抓x
        self.ret = llt.convert_profile_2_values(self.hLLT, self.profile_buffer, self.resolution, llt.TProfileConfig.PROFILE, self.scanner_type, 0, 1,
                                self.null_ptr_short, self.intensities, self.null_ptr_short, self.x, self.z, self.null_ptr_int, self.null_ptr_int)
        # print(receiveData)
        #延遲0.1s
        # dataTemp = []
        # for i in range(len(self.z)):
        #     dataTemp.append(self.z[i]*-1)
        # self.receiveDataTemp = np.array(self.GetLaserData())
        self.receiveDataTemp = np.array(self.z)
        dataTemp = self.receiveDataTemp * -1
        # diff = np.abs(np.diff(dataTemp))
        
        # when diff > tolerance, skip this data
        # avg = np.average(diff)
        # if avg < toleranceLaserData:
        #     return None
        
        output = []
        avg = np.average(dataTemp)
        if avg < -120 or avg > -80:
            output.append(dataTemp)
            output.append([])
            
            if avg > -80:
                self.signalShowHint.emit('Laser Sensor too close')
            else:
                self.signalShowHint.emit('Laser Sensor too far')
        else:
            output.append([])
            output.append(dataTemp)
            self.signalShowHint.emit('')
           
        return output     