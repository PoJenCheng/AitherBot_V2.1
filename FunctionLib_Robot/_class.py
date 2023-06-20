import pyads
import math
import ctypes as ct
import sys
import numpy as np
import keyboard
import serial
import random
from pylltLib import pyllt as llt
from time import sleep
from FunctionLib_Robot.__init__ import *
from FunctionLib_Vision._class import REGISTRATION
from FunctionLib_Robot._subFunction import lowPass
from ._globalVar import *
from FunctionLib_UI.ui_matplotlib_pyqt import *


import matplotlib
matplotlib.use('QT5Agg')

from PyQt5.QtWidgets import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_gt5agg import FigureCanvasGTKAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar


upper_G_length = 0
upper_G_angle = 0
lower_G_length = 0
lower_G_angle = 0


class MOTORCONTROL():
    def __init__(self, motorAxis):
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
        self.bLimitSwitch5 = 'GVL.LimitSwitch5'
        self.bLimitSwitch6 = 'GVL.LimitSwitch6'
        self.bDualAbsolute = 'GVL.bDualAbsolute'
        self.bDisplayLight_GY = 'GVL.DisplayLight_GY'
        self.bDisplayLight_RE = 'GVL.DisplayLight_RE'
        self.bTrackLight_GY = 'GVL.LaserTrack_GY'
        self.bTrackLight_RE = 'GVL.LaserTrack_RE'

        try:
            self.plc = pyads.Connection('5.109.167.73.1.1', 851)
            # ser = serial.Serial(port='COM6', baudrate=9600, timeout=2)
            self.plc.open()
        except:
            input("Motor or auduino connect fail. Please check it and press 'Enter'")

    def MotorInitial(self):
        try:
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
        except:
            self.plc.write_by_name(self.bDisplayLight_GY,True)
            self.plc.write_by_name(self.bDisplayLight_RE,True)

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
        else:
            print(f"Fail to enable the servo motor {self.motorAxis}.")
            sleep(1)
            self.MotorDriverEnable()

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

    def SetPosition(self):
        while self.plc.read_by_name(self.SetPositionStatus) == False:
            self.plc.write_by_name(self.bSetPosition, True)
            sleep(0.1)
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
        value = int(self.plc.read_by_name(self.bLimitSwitch))
        return value

    def bMoveRelativeCommandDisable(self):
        moveRelativeStatus = self.plc.read_by_name(self.bMoveRelative)
        if moveRelativeStatus is True:
            self.plc.write_by_name(self.bMoveRelative, False)
            moveRelativeStatus = self.plc.read_by_name(self.bMoveRelative)
            
    def DisplayRun(self):
        self.plc.write_by_name(self.bDisplayLight_GY,True)
        self.plc.write_by_name(self.bDisplayLight_RE,False)
            
    def DisplaySafe(self):
        self.plc.write_by_name(self.bDisplayLight_GY,False)
        self.plc.write_by_name(self.bDisplayLight_RE,False)
        
    def DisplayError(self):
        self.plc.write_by_name(self.bDisplayLight_GY,True)
        self.plc.write_by_name(self.bDisplayLight_RE,True)
        
    def TrackGreen(self):
        self.plc.write_by_name(self.bTrackLight_GY,True)
        self.plc.write_by_name(self.bTrackLight_RE,False)
    
    def TrackYellow(self):
        self.plc.write_by_name(self.bTrackLight_GY,True)
        self.plc.write_by_name(self.bTrackLight_RE,True)
        
    def TrackRed(self):
        self.plc.write_by_name(self.bTrackLight_GY,False)
        self.plc.write_by_name(self.bTrackLight_RE,True)
        
    def TrackNull(self):
        self.plc.write_by_name(self.bTrackLight_GY,False)
        self.plc.write_by_name(self.bTrackLight_RE,False)


class MOTORSUBFUNCTION(MOTORCONTROL, REGISTRATION):
    def __init__(self):
        robotCheckStatus = False
        while robotCheckStatus is False:
            try:
                "Setting Motor ID"
                self.FLDC_Up = MOTORCONTROL(1)
                self.BLDC_Up = MOTORCONTROL(2)
                self.FLDC_Down = MOTORCONTROL(3)
                self.BLDC_Down = MOTORCONTROL(4)
                self.RobotSystem = MOTORCONTROL(5)

                "Motor Initial"
                self.FLDC_Up.MotorInitial()
                self.BLDC_Up.MotorInitial()
                self.FLDC_Down.MotorInitial()
                self.BLDC_Down.MotorInitial()

                robotCheckStatus = True
                print("Surgical robot connect success.")
            except:
                print("Fail to link to robot, system will re-try after 3 seconds.")
                sleep(3)

        "Motor Enable"
        motorEnableStatus = False
        while motorEnableStatus is False:
            try:
                "Motor Enable"
                self.BLDC_Up.MotorDriverEnable()
                self.BLDC_Down.MotorDriverEnable()
                self.FLDC_Up.MotorDriverEnable()
                self.FLDC_Down.MotorDriverEnable()
                motorEnableStatus = True
                self.SetZero()
                print("Motor are enabled.")
            except:
                print("Robot control system connect fail.")
        
        self.LightSafe()

    
    def LightSafe(self):
        self.RobotSystem.DisplaySafe()
    
    def FLDC_ButtonDisable(self):
        self.FLDC_Up.MoveRelativeButtonDisable()
        self.FLDC_Down.MoveRelativeButtonDisable()

    def BLDC_ButtonDisable(self):
        self.BLDC_Up.MoveRelativeButtonDisable()
        self.BLDC_Down.MoveRelativeButtonDisable()

    def SetZero(self):
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

    def Home(self, BLDC_Up_Speed, BLDC_Down_Speed):
        homeSwitch = self.BLDC_Up.homeValue() * self.BLDC_Down.homeValue()
        homeStatus_Enable = False
        while homeSwitch == 0:
            homeSwitch = self.BLDC_Up.homeValue() * self.BLDC_Down.homeValue()
            if homeStatus_Enable == False:
                if self.BLDC_Up.homeValue() == 0:
                    self.BLDC_Up.MoveVelocitySetting(BLDC_Up_Speed, 3000, 3)
                    self.BLDC_Up.bMoveVelocityEnable()
                if self.BLDC_Down.homeValue() == 0:
                    self.BLDC_Down.MoveVelocitySetting(
                        BLDC_Down_Speed, 3000, 3)
                    self.BLDC_Down.bMoveVelocityEnable()
                homeStatus_Enable = True
            else:
                if self.BLDC_Up.homeValue() == 1:
                    self.BLDC_Up.MC_Stop()
                if self.BLDC_Down.homeValue() == 1:
                    self.BLDC_Down.MC_Stop()
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

    def HomeLinearMotion(self, shifting_Up, Shifting_Down, speed):
        self.BLDC_Stop()
        "move a relative distance in a straight line"
        self.BLDC_Up.MoveRelativeSetting(shifting_Up, speed)
        self.BLDC_Down.MoveRelativeSetting(Shifting_Down, speed)
        self.BLDC_Up.bMoveRelativeEnable()
        self.BLDC_Down.bMoveRelativeEnable()
        while self.BLDC_Up.fbMoveRelative() == False or self.BLDC_Down.fbMoveRelative() == False:
            sleep(0.01)
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

    def HomeRotation(self):
        "first positioning"
        homeSwitch = self.FLDC_Up.homeValue() * self.FLDC_Down.homeValue()
        homeStatus_Enable = False
        while homeSwitch == 0:
            homeSwitch = self.FLDC_Up.homeValue() * self.FLDC_Down.homeValue()
            if homeStatus_Enable == False:
                if self.FLDC_Up.homeValue() == 0:
                    self.FLDC_Up.MoveVelocitySetting(300, 1200, 1)
                    self.FLDC_Up.bMoveVelocityEnable()
                if self.FLDC_Down.homeValue() == 0:
                    self.FLDC_Down.MoveVelocitySetting(400, 2000, 1)
                    self.FLDC_Down.bMoveVelocityEnable()
                homeStatus_Enable = True
            else:
                if self.FLDC_Up.homeValue == 1:
                    self.FLDC_Up.MC_Stop()
                if self.FLDC_Down.homeValue == 1:
                    self.FLDC_Down.MC_Stop()
        self.FLDC_Stop()

        "Rotate to a specific angle"
        self.DualRotatePositionMotion(-350, 400)

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
                    self.FLDC_Up.MoveVelocitySetting(50, 500, 1)
                    self.FLDC_Up.bMoveVelocityEnable()
                if self.FLDC_Down.homeValue() == 0:
                    self.FLDC_Down.MoveVelocitySetting(50, 500, 1)
                    self.FLDC_Down.bMoveVelocityEnable()
                homeStatus_Enable = True
            else:
                if self.FLDC_Up.homeValue() == 1:
                    self.FLDC_Up.MC_Stop()
                if self.FLDC_Down.homeValue() == 1:
                    self.FLDC_Down.MC_Stop()
        self.FLDC_Stop()

        "Rotate to a specific angle"
        self.FLDC_Up.MoveRelativeSetting(shiftingFLDC_up, 200)
        self.FLDC_Down.MoveRelativeSetting(shiftingFLDC_Down, 200)
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
        self.RobotSystem.DisplayRun()
        print("Home Processing Started.")
        self.Home(1000, 1000)
        sleep(0.1)
        self.Home(1000, 500)
        sleep(0.1)
        self.Home(100, 100)
        sleep(0.1)
        self.HomeLinearMotion(shiftingBLDC_Up, shiftingBLDC_Down, 100)
        sleep(0.1)
        self.HomeRotation()
        self.ReSetMotor()
        self.SetZero()
        self.RobotSystem.DisplaySafe()
 

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
        # entry_full = np.array([354.61890598,54.93392833,-85.62637816])
        # target_full = np.array([ 354.55446918,45.55959477,-126.77388984])
        # entry_halt = np.array([354.61892983,55.93381232,-85.61114631])
        # target_halt = np.array([ 354.55311805,54.57378253,-127.63668602])
        # pointTemp = np.array(
        #     [entry_full, target_full, entry_halt, target_halt])
        pointTemp = self.PlanningPath

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

    def CapturePoint(self):
        # entry_full = np.array([354.61890598,54.93392833,-85.62637816])
        # target_full = np.array([ 354.55446918,45.55959477,-126.77388984])
        # entry_halt = np.array([354.61892983,55.93381232,-85.61114631])
        # target_halt = np.array([ 354.55311805,54.57378253,-127.63668602])
        # pointTemp = np.array(
        #     [entry_full, target_full, entry_halt, target_halt])
        pointTemp = self.PlanningPath

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
        "obtain upper point"
        # print(f"Entry point is {self.entryPoint}")
        t = (upperHigh - self.entryPoint[2]) / \
            (self.targetPoint[2]-self.entryPoint[2])
        upperPointX = self.entryPoint[0] + \
            (self.targetPoint[0]-self.entryPoint[0])*t
        upperPointY = self.entryPoint[1] + \
            (self.targetPoint[1]-self.entryPoint[1])*t

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
        self.RobotSystem.DisplayRun()
        self.MultiRelativeMotion(RotationCount_axis1, LinearCount_axis2,
                                 RotationCount_axis3, LinearCount_axis4, 800, 800, 800, 800)
        print("Compensation is Done!")
        self.RobotSystem.DisplaySafe()

    def RealTimeTracking(self,percentage):
        "obtain entry point and target point"
        self.movingPoint = self.CaptureRealTimePoint(percentage)
        self.entryPoint = self.movingPoint[0]
        self.targetPoint = self.movingPoint[1]
        print(f"RTentryPoint is {self.entryPoint}")
        print(f"RTtargetPoint is {self.targetPoint}")


    def P2P(self):
        "obtain entry point and target point"
        self.movingPoint = self.CapturePoint()
        self.entryPoint = self.movingPoint[0]
        self.targetPoint = self.movingPoint[1]
        self.MoveToPoint()

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
            self.RobotSystem.DisplayError()
            print("Wrong type. Please try it again.")
               
class LineLaser(MOTORCONTROL):
    def __init__(self):
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

        # Null pointer if data not necessary
        self.null_ptr_short = ct.POINTER(ct.c_ushort)()
        self.null_ptr_int = ct.POINTER(ct.c_uint)()

        # Create instance 
        self.hLLT = llt.create_llt_device(llt.TInterfaceType.INTF_TYPE_ETHERNET)

        # Get available interfaces
        ret = llt.get_device_interfaces_fast(self.hLLT, self.available_interfaces, len(self.available_interfaces))
        if ret < 1:
            raise ValueError("Error getting interfaces : " + str(ret))

        # Set IP address
        ret = llt.set_device_interface(self.hLLT, self.available_interfaces[0], 0)
        if ret < 1:
            raise ValueError("Error setting device interface: " + str(ret))

        # Connect
        tryTimes = 0
        while tryTimes < 5:
            ret = llt.connect(self.hLLT)
            if ret < 1:
                tryTimes += 1
                raise ConnectionError("Error connect: " + str(ret))
            else:
                tryTimes = 5

        # Get available resolutions
        ret = llt.get_resolutions(self.hLLT, self.available_resolutions, len(self.available_resolutions))
        if ret < 1:
            raise ValueError("Error getting resolutions : " + str(ret))

        # Set max. resolution
        self.resolution = self.available_resolutions[0]
        ret = llt.set_resolution(self.hLLT, self.resolution)
        if ret < 1:
            raise ValueError("Error getting resolutions : " + str(ret))

        # Declare measuring data arrays
        self.profile_buffer = (ct.c_ubyte*(self.resolution*64))()
        self.x = (ct.c_double * self.resolution)()
        self.z = (ct.c_double * self.resolution)()
        self.intensities = (ct.c_ushort * self.resolution)()

        # Scanner type
        ret = llt.get_llt_type(self.hLLT, ct.byref(self.scanner_type))
        if ret < 1:
            raise ValueError("Error scanner type: " + str(ret))

        # Set profile config
        ret = llt.set_profile_config(self.hLLT, llt.TProfileConfig.PROFILE)
        if ret < 1:
            raise ValueError("Error setting profile config: " + str(ret))

        # Set trigger free run
        ret = llt.set_feature(self.hLLT, llt.FEATURE_FUNCTION_TRIGGER, llt.TRIG_INTERNAL)
        if ret < 1:
            raise ValueError("Error setting trigger: " + str(ret))

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
        self.fig = plt.figure()
        self.plot = self.fig.add_subplot()
        self.lay = QtWidgets.QVBoxLayout()
        
        self.RobotSystem = MOTORCONTROL(6)
        self.RobotSystem.TrackNull()
    
    # 計算高度均值
    def CalHeightAvg(self, arr):
        try:
            nonZeroArray = np.nonzero(arr) # 取得非0的個數
            sum = 0
            for index in range(len(arr)):
                sum += arr[index]**2
            squareSum = sum**0.5
            return squareSum/len(nonZeroArray[0])
        except:
            self.RobotSystem.DisplayError()
            print("Calculate height avg error")

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

    def Get_Key(self, val):
        for key, value in self.percentageBase.items():
            if val == value[0]:
                return key
    
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
                raise ValueError("Error setting trigger: " + str(ret))
            #--------------------------------------------------------------------------------------------------------------

            # Set exposure time
            ret = llt.set_feature(self.hLLT, llt.FEATURE_FUNCTION_EXPOSURE_TIME, self.exposure_time)
            if ret < 1:
                raise ValueError("Error setting exposure time: " + str(ret))

            # Set idle time
            ret = llt.set_feature(self.hLLT, llt.FEATURE_FUNCTION_IDLE_TIME, self.idle_time)
            if ret < 1:
                raise ValueError("Error idle time: " + str(ret))

            #Wait until all parameters are set before starting the transmission (this can take up to 120ms)
            sleep(0.12)

            # Start transfer
            ret = llt.transfer_profiles(self.hLLT, llt.TTransferProfileType.NORMAL_TRANSFER, 1)
            if ret < 1:
                raise ValueError("Error starting transfer profiles: " + str(ret))
        except:
            self.RobotSystem.DisplayError()
            print("Laser connect fail.")

               
    def ModelBuilding(self):
        # self.TriggerSetting()
        self.receiveData = []
        ret = llt.get_actual_profile(self.hLLT, self.profile_buffer, len(self.profile_buffer), llt.TProfileConfig.PROFILE,
                                    ct.byref(self.lost_profiles))
        if ret != len(self.profile_buffer):
            #當沒有資料顯示NO NEW PROFILE
            if (ret == llt.ERROR_PROFTRANS_NO_NEW_PROFILE):
                # print("NO NEW PROFILE")
                sleep((self.idle_time + self.exposure_time)/100000)
                #輸入q跳出迴圈
                if keyboard.is_pressed("q"):
                    self.noProfileReceived = False
                else :
                    pass
            else:
                    raise ValueError("Error get profile buffer data: " + str(ret))
                    self.noProfileReceived = False
        else:
            #將RawData轉成距離值
            #resolution ln:50
            #scanner_type ln:62
            #每點的距離值抓取z每點位置抓x
            self.ret = llt.convert_profile_2_values(self.hLLT, self.profile_buffer, self.resolution, llt.TProfileConfig.PROFILE, self.scanner_type, 0, 1,
                                    self.null_ptr_short, self.intensities, self.null_ptr_short, self.x, self.z, self.null_ptr_int, self.null_ptr_int)
            #顯示Z軸第一個點
            dataTemp = []
            for i in range(laserStartPoint,laserEndPoint):
                dataTemp.append(self.z[i])
            self.receiveData.append(dataTemp)                
            # print(receiveData)
            #延遲0.1s
            sleep(0.01)

            # self.DataBaseChecking()
        return self.receiveData
                
    def DataBaseChecking(self,receiveData):  # make sure whether data lost
        try:
            for item in receiveData:
                for j in range(1,(laserEndPoint-laserStartPoint)):
                    currentTemp = abs(item[j]-item[j-1])
                    if currentTemp > 10:
                        error = 10/0
            print("Model Base Checking done!")
        except:
            self.RobotSystem.DisplayError()
            print("Model Building Fail")
            print("Please try to build chest model again.")
            # self.ModelBuilding()

    def RealTimeHeightAvg(self,yellowLightCriteria,greenLightCriteria):
        # self.triggerSetting()
        self.receiveData = []
        meanPercentage = 0
        ret = llt.get_actual_profile(self.hLLT, self.profile_buffer, len(self.profile_buffer), llt.TProfileConfig.PROFILE,
                                    ct.byref(self.lost_profiles))
        if ret != len(self.profile_buffer):
            #當沒有資料顯示NO NEW PROFILE
            if (ret == llt.ERROR_PROFTRANS_NO_NEW_PROFILE):
                # print("NO NEW PROFILE")
                sleep((self.idle_time + self.exposure_time)/100000)
                #輸入q跳出迴圈
                if keyboard.is_pressed("q"):
                    self.noProfileReceived = False
                else :
                    pass
            else:
                    raise ValueError("Error get profile buffer data: " + str(ret))
                    self.noProfileReceived = False
        else:
            #將RawData轉成距離值
            #resolution ln:50
            #scanner_type ln:62
            #每點的距離值抓取z每點位置抓x
            self.ret = llt.convert_profile_2_values(self.hLLT, self.profile_buffer, self.resolution, llt.TProfileConfig.PROFILE, self.scanner_type, 0, 1,
                                    self.null_ptr_short, self.intensities, self.null_ptr_short, self.x, self.z, self.null_ptr_int, self.null_ptr_int)
            # print(receiveData)
            #延遲0.1s
            dataTemp = []
            for i in range(laserStartPoint,laserEndPoint):
                dataTemp.append(self.z[i])
            self.receiveData.append(dataTemp)
            
            # Rearrange data
            # self.DataRearrange(self.receiveData)
            self.CalculateRealTimeHeightAvg()
            # print(self.realTimeHeightAvgValue)
            
            realTimeAvgValue = self.realTimeHeightAvgValue[0]
            # 燈號控制
            self.avgValueList = []
            for item in self.percentageBase.items():
                self.avgValueList.append(list(item)[1][0])
            # minValue = min(self.avgValueList)
            # maxValue = max(self.avgValueList)
            self.avgValueList = sorted(self.avgValueList, reverse=True)
            
            meanPercentage = self.PercentagePrediction(realTimeAvgValue)
            try:
                if meanPercentage >= yellowLightCriteria and  meanPercentage < greenLightCriteria:
                    self.RobotSystem.TrackYellow()
                    print("黃燈")
                    print(meanPercentage)
                elif meanPercentage > greenLightCriteria:
                    self.RobotSystem.TrackGreen()
                    print("綠燈")
                    print(meanPercentage)
                else:
                    self.RobotSystem.TrackRed()
                    # self.ser.write(b'red\n')
            
                sleep(0.01)
                return meanPercentage
            
            except:
                self.RobotSystem.DisplayError()
                print("Realtime track error")
            
                    
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
                for item in self.percentageBase.values():
                    if item[0] == rangeAvgValue[0]:
                        lowerLaserRawData = item[1]
                        lowerTempValue = item
                    elif item[0] == rangeAvgValue[1]:
                        upperLaserRawData = item[1]                                                 
                        upperTempValue = item
                    
                # 線性內插，找出各點的比例值
                pointPercentage = []
                # 取得低線與高線的點位比例
            
                lowerPointPercentage = self.Get_Key(lowerTempValue[0])
                upperPointPercentage = self.Get_Key(upperTempValue[0])
                diffPointPercentage = upperPointPercentage - lowerPointPercentage # x-y
                try:
                    for i in range(laserEndPoint-laserStartPoint):
                        dis = upperLaserRawData[i] - lowerLaserRawData[i] #a-b
                        if dis != 0:
                            diff = upperLaserRawData[i] - self.receiveData[0][i] #a-c
                            if abs(diff) <=2:
                                diffPercentage = diff/dis #(a-c)/(a-b)
                                pointPercentage.append(upperPointPercentage - diffPointPercentage*diffPercentage)
                    meanPercentage = np.mean(pointPercentage)
                except:
                    self.RobotSystem.DisplayError()
                    print("Predict percentage error")
            
            else:
                meanPercentage = 0
        
            return meanPercentage    
        except:
            pass
        
    def CloseLaser(self):
        if self.ret & llt.CONVERT_X is 0 or self.ret & llt.CONVERT_Z is 0 or self.ret & llt.CONVERT_MAXIMUM is 0:
            raise ValueError("Error converting data: " + str(self.ret))

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
        
    def DataRearrange(self,receiveData, yellowLightCriteria, greenLightCriteria): #如果有重複的數值，則刪除
        self.laserDataBase = []
        self.laserDataBase.append(receiveData[0])
        k = 0
        index = 0
        for line in range(len(receiveData)):
            k += 1
            tolerance = 0
            if k < len(receiveData):
                for point in range(len(receiveData[line])):
                    skip = False
                    if skip is False:
                        if receiveData[k][point] != 0:
                            tolerance += abs(receiveData[k][point] - receiveData[index][point])
                        else:
                            skip = True                
                if tolerance > laserDataRepeatRange:
                    self.laserDataBase.append(receiveData[k])
                    index = k
        
        self.DataFilter(yellowLightCriteria)
                    
    def DataFilter(self,yellowLightCriteria): #將高頻的數值刪除
        self.laserDataBase_filter = {}
        for lineNum in range(len(self.laserDataBase)):
            ignorePointTemp = []
            ignorePointTemp = lowPass(self.laserDataBase[lineNum])
            self.laserDataBase_filter[lineNum]=ignorePointTemp
        self.CalculateHeightAvg(yellowLightCriteria)
            
    def CalculateHeightAvg(self,yellowLightCriteria):  #得到相對應的percentage
        heightAvg = {}
        for lineNum in range(len(self.laserDataBase_filter)):
            X = np.array(self.laserDataBase_filter[lineNum])
            heightAvg[self.CalHeightAvg(X)] = X
            # heightAvg.append(getChestProfile.calHeightAvg(X))

        maxAvg =  max(list(list(heightAvg.keys())))
        minAvg =  min(list(list(heightAvg.keys())))
        dis = maxAvg - minAvg
        self.percentageBase = {}
        for item in list(heightAvg.items()):
            avg = list(item)[0]
            self.percentage = ((maxAvg-avg)/dis)*100
            # if self.percentage >= yellowLightCriteria:
            self.percentageBase[self.percentage] = item
        self.percentageBase = dict(sorted(self.percentageBase.items(), key=lambda x:x[0], reverse =True))
        # print(self.percentageBase)
        
    def CalculateRealTimeHeightAvg(self):
        self.realTimeHeightAvgValue = []
        valueTemp = np.array(self.CalHeightAvg(self.receiveData[0]))
        self.realTimeHeightAvgValue.append(valueTemp)
            
    def PlotProfile(self): 
        receiveData = []
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
        dataTemp = []
        for i in range(len(self.z)):
            dataTemp.append(self.z[i]*-1)
        receiveData.append(dataTemp)
           
        return receiveData     