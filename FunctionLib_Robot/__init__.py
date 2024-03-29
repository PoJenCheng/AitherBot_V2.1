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
shiftingFLDC_up = -7407.9492-11.0742
shiftingBLDC_Up = -37126.9336-0.0879
shiftingFLDC_Down = -8178.5742-6828.7500
shiftingBLDC_Down = -37000.0195+0.1758
robotShifting = np.array([70, -11.5, 205])

robotInitialLength = 129
upperHigh = 16.3
lowerHigh = -8.7
global data
data = ''

"distance between point ball and robot base"
baseShift_X = -178
baseShift_Y = 32.5 #70 - 2.5
baseShift_Z = -21.4 #15.5


"Laser setting parameter"
nValidCycle = 5
laserDataRepeatRange = 0.05
filterTolerance = 1
toleranceLaserData = 0.01
yellowLightCriteria_LowAccuracy = 75
greenLightCriteria_LowAccuracy = 85
yellowLightCriteria_HighAccuracy = 80
greenLightCriteria_HighAccuracy = 95
INHALE_AREA = 80
EXHALE_AREA = 20
laserStartPoint = 100 # the start point to measure
laserEndPoint = 550 # measure laser point to the end point

gVars = {}
gVars['toleranceLaserData'] = 0.01

TIMEOVER = 20
DEVICE_ROBOT = 1
DEVICE_LASER = 2
