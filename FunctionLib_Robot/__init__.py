import numpy as np

PTM_OutputPath = 'c://PTM/Output.txt'
Target_path = "C://MTP/TargetPoint.txt"
Entry_Path = "C://MTP/EntryPoint.txt"
MTP_path = 'c://MTP/Command.txt'
InterpolateMatrix = 'c://MTP/InterpolateMatrix.txt'
Inform_path = 'c://PTM/inform.txt'
jogControlPath = 'c://MTP/jogControl_Z.txt'
jogPositionPath = 'c://PTM/jogPosition_XY.txt'
SlideZ_Path = 'c://MTP/jogControl.txt'
pointAB_Path = 'C://PTM/jogPosition_XY.txt'
dynamicTrackingDisabled = 'c://MTP/dynamicTrackingDisabled.txt'
SlideZ_Path = 'c://MTP/jogControl.txt'
pointAB_Path = 'C://PTM/jogPosition_XY.txt'
point_Path = 'C://MTP/point.txt'


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
shiftingFLDC_up = -5.3613 - 1283.5547
shiftingBLDC_Up = 1187.1387
shiftingFLDC_Down = -7.8662 - 1777.6318
shiftingBLDC_Down = -406.6699 - (-1356.5918)
robotShifting = np.array([70, -11.5, 205])

robotInitialLength = 129
upperHigh = 16.3
lowerHigh = -8.7
global data
data = ''
test = 10
