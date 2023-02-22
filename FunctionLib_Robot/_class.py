import pyads
import math
from time import sleep
from FunctionLib_Robot.__init__ import *
from FunctionLib_Vision._class import REGISTRATION
from ._globalVar import *

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

        try:
            self.plc = pyads.Connection('5.109.167.73.1.1', 851)
            # ser = serial.Serial(port='COM6', baudrate=9600, timeout=2)
            self.plc.open()
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

    def Upper_RobotMovingPoint(self, PointX, PointY):
        global upper_G_length
        global upper_G_angle

        robotTotalLength = (PointX ** 2 + (PointY)**2)**0.5
        "The distance of the robot needs to travel"
        robotMovingLength = robotTotalLength

        rotationTheta = math.atan(PointY/(PointX + 129))
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
        robotMovingLength = robotTotalLength

        rotationTheta = math.atan(PointY/(PointX + 129))
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

    def CapturePoint(self):
        # entry_full = np.array([372.785, 91.31, 20.9])
        # target_full = np.array([372.785, 92.69, -4])
        # entry_halt = np.array([372.785, 92.31, 20.9])
        # target_halt = np.array([372.785, 92.72, -4])
        # pointTest = np.array(
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

        "calculate avg value between full breathing and halt breathing"
        entryPoint_X = (
            (breathingFull_entry[0] + breathingHalt_entry[0])/2)-robotInitialLength
        entryPoint_Y = (breathingFull_entry[1] + breathingHalt_entry[1])/2
        entryPoint_Z = (breathingFull_entry[2] + breathingHalt_entry[2])/2

        targetPoint_X = (
            breathingFull_target[0] + breathingHalt_target[0])/2-robotInitialLength
        targetPoint_Y = (breathingFull_target[1] + breathingHalt_target[1])/2
        targetPoint_Z = (breathingFull_target[2] + breathingHalt_target[2])/2

        entryPoint = np.array([entryPoint_X, entryPoint_Y, entryPoint_Z])
        targetPoint = np.array([targetPoint_X, targetPoint_Y, targetPoint_Z])

        return entryPoint, targetPoint

    # def P2P(self):
    #     # 取得entry point 與 target point
    #     try:
    #         movingPoint = self.CapturePoint()
    #         entryPoint = movingPoint[0]
    #         targetPoint = movingPoint[1]
    #         print(entryPoint[0])
    #     except:
    #         pass

    #     # obtain upper point
    #     t = (upperHigh - entryPoint[2])/(targetPoint[2]-entryPoint[2])
    #     upperPointX = entryPoint[0] + (targetPoint[0]-entryPoint[0])*t
    #     upperPointY = entryPoint[1] + (targetPoint[1]-entryPoint[1])*t

    #     # obtain lower point
    #     t = (lowerHigh - entryPoint[2])/(targetPoint[2]-entryPoint[2])
    #     lowerPointX = entryPoint[0] + (targetPoint[0]-entryPoint[0])*t
    #     lowerPointY = entryPoint[1] + (targetPoint[1]-entryPoint[1])*t

    #     # 計算上層的旋轉與移動
    #     upperMotion = self.Upper_RobotMovingPoint(upperPointX, upperPointY)
    #     lowerMotion = self.Lower_RobotMovingPoint(lowerPointX, lowerPointY)

    #     "robot motion"
    #     "rotation command"
    #     RotationCount_axis3 = float(
    #         lowerMotion[1]*(RotationMotorCountPerLoop*RotateGearRatio)/360)
    #     RotationCount_axis1 = float(
    #         upperMotion[1]*(RotationMotorCountPerLoop*RotateGearRatio)/360) - RotationCount_axis3
    #     # Linear motion command
    #     LinearCount_axis2 = upperMotion[0]*LinearMotorCountPerLoop
    #     LinearCount_axis4 = lowerMotion[0]*LinearMotorCountPerLoop
    #     self.MultiRelativeMotion(RotationCount_axis1, LinearCount_axis2,
    #                              RotationCount_axis3, LinearCount_axis4, 800, 800, 800, 800)

    # def P2P_Manual(self,entryPoint, targetPoint):
    #     # obtain upper point
    #     t = (upperHigh - entryPoint[2])/(targetPoint[2]-entryPoint[2])
    #     upperPointX = entryPoint[0] + (targetPoint[0]-entryPoint[0])*t
    #     upperPointY = entryPoint[1] + (targetPoint[1]-entryPoint[1])*t

    #     # obtain lower point
    #     t = (lowerHigh - entryPoint[2])/(targetPoint[2]-entryPoint[2])
    #     lowerPointX = entryPoint[0] + (targetPoint[0]-entryPoint[0])*t
    #     lowerPointY = entryPoint[1] + (targetPoint[1]-entryPoint[1])*t

    #     # 計算上層的旋轉與移動
    #     upperMotion = self.Upper_RobotMovingPoint(upperPointX, upperPointY)
    #     lowerMotion = self.Lower_RobotMovingPoint(lowerPointX, lowerPointY)

    #     "robot motion"
    #     "rotation command"
    #     RotationCount_axis3 = float(
    #         lowerMotion[1]*(RotationMotorCountPerLoop*RotateGearRatio)/360)
    #     RotationCount_axis1 = float(
    #         upperMotion[1]*(RotationMotorCountPerLoop*RotateGearRatio)/360) - RotationCount_axis3
    #     # Linear motion command
    #     LinearCount_axis2 = upperMotion[0]*LinearMotorCountPerLoop
    #     LinearCount_axis4 = lowerMotion[0]*LinearMotorCountPerLoop
    #     self.MultiRelativeMotion(RotationCount_axis1, LinearCount_axis2,
    #                              RotationCount_axis3, LinearCount_axis4, 800, 800, 800, 800)

    # def CycleRun(self, P1, P2, P3, P4, cycleTimes):
    #     "robot executes cycle run in 4 points"
    #     try:
    #         point1 = []
    #         point2 = []
    #         point3 = []
    #         point4 = []
    #         for item in P1:
    #             point1.append(float(item))
    #         for item in P2:
    #             point2.append(float(item))
    #         for item in P3:
    #             point3.append(float(item))
    #         for item in P4:
    #             point4.append(float(item))

    #         PointX = [point1[0], point2[0], point3[0], point4[0]]
    #         PointY = [point1[1], point2[1], point3[1], point4[1]]
    #         PointZ = [point1[2], point2[2], point3[2], point4[2]]

    #         times = 0
    #         while times < cycleTimes:
    #             times += 1
    #             print(f"Repeat times {times}.")
    #             for index in range(4):
    #                 self.entryPoint = [PointX[index],
    #                                    PointY[index], PointZ[index]]
    #                 self.targetPoint = [PointX[index],
    #                                     PointY[index], PointZ[index]-20]
    #                 self.MoveToPoint()
    #         print("Cycle Run Processing is Done!")
    #     except:
    #         print("Wrong type. Please try it again.")

    def MoveToPoint(self):
        "obtain upper point"
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
        self.MultiRelativeMotion(RotationCount_axis1, LinearCount_axis2,
                                 RotationCount_axis3, LinearCount_axis4, 800, 800, 800, 800)

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
            print("Wrong type. Please try it again.")
