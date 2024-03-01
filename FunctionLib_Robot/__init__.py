import numpy as np

LinearMotorCountPerLoop = 360  # 8192 count per loop in encoder
LinearGearRatio = 1  # screw pitch is 1
RotationMotorCountPerLoop = 360
RotateGearRatio = 50  # H.D. gear ratio
PointShift = 10  # Distance between ball coordination and robot center
L_OrginalToRobot = 47.5  # Length from original point to robot point
# Length from ball original point to rotation motor center
L_OriginalToRotationCenter = 120
L_RobotToTCP = 82  # Length from TCP to robot point
Distance_Lower = 7  # Distance from entry point to lower actuator plane
Distance_Higher = -15  # Distance from lower actuator to higher one
distanceY_P1ToP2 = 22  # Distance from control Point 1 to control Point 2
L_OriginalToEffector = 68
Button_X = 2
Button_A = 0
Button_B = 1
Button_Y = 3
Button_L = 4
Button_R = 5
Button_Back = 6
Button_Start = 7
BallStick_LX = 0
BallStick_LY = 1
BallStick_RX = 2
BallStick_RY = 3
maxManualLinearSpeed = 1000
maxManualRotateSpeed = 200
jogResolution = 1
differential_time = 2
normalSpeed = 1000
shiftingFLDC_up = -335.5664 - 8486.0156
shiftingBLDC_Up = -37846.5820 + 1.6699
shiftingFLDC_Down = -769.5703 - 14868.9844
shiftingBLDC_Down = -37612.4414 + 2.5488
robotShifting = np.array([70, -11.5, 205])

robotInitialLength = 129
upperHigh = 16.3
lowerHigh = -8.7
global data
data = ''

"distance between point ball and robot base"
baseShift_X = -174  #205
baseShift_Y = 32.5 #70 - 2.5
baseShift_Z = -26.7 #15.5


"Laser setting parameter"
nValidCycle = 5
laserDataRepeatRange = 0.05
filterTolerance = 1
toleranceLaserData = 5
yellowLightCriteria_LowAccuracy = 75
greenLightCriteria_LowAccuracy = 85
yellowLightCriteria_HighAccuracy = 80
greenLightCriteria_HighAccuracy = 95
laserStartPoint = 100 # the start point to measure
laserEndPoint = 550 # measure laser point to the end point
