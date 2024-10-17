import numpy as np
from PyQt5.QtCore import Qt

# LinearMotorCountPerLoop = 360  # 8192 count per loop in encoder
# LinearGearRatio = 1  # screw pitch is 1
# RotationMotorCountPerLoop = 2048
# RotateGearRatio = 100  # H.D. gear ratio
PointShift = 10  # Distance between ball coordination and robot center
L_OrginalToRobot = 47.5  # Length from original point to robot point
# Length from ball original point to rotation motor center
L_OriginalToRotationCenter = 120
L_RobotToTCP = 82  # Length from TCP to robot point
Distance_Lower = 7  # Distance from entry point to lower actuator plane
Distance_Higher = -15  # Distance from lower actuator to higher one
distanceY_P1ToP2 = 22  # Distance from control Point 1 to control Point 2
L_OriginalToEffector = 68
Button_X = 0
Button_A = 1
Button_B = 2
Button_Y = 3
Button_L = 4
Button_R = 5
Button_Back = 6
Button_Start = 7
BallStick_LX = 0
BallStick_LY = 1
BallStick_RX = 2
BallStick_RY = 3
DPad = 0
maxManualLinearSpeed = 1000
maxManualRotateSpeed = 200
jogResolution_movement = 5
differential_time = 2
normalSpeed = 1000
shiftingFLDC_up = -20.5893
shiftingBLDC_Up = -52.85
shiftingFLDC_Down = -26.0881
shiftingBLDC_Down = -52.85
# robotShifting = np.array([70, -11.5, 205])

robotInitialLength = 132.253 #132.93 #110.38  #128.38
upperHigh = 6.798 #6.6 #6.1
lowerHigh = -14.93 #-18.671 #-14.171 #-15.6
global data
data = ''

"distance between point ball and robot base"
baseShift_X = -182.5
baseShift_Y = 32.5 #32.48 #70 - 2.5
baseShift_Z = -22.24 #-21.04 #15.5

diff_Pole_lightBoard = 66.24 #67.24


"Laser setting parameter"
laserDataRepeatRange = 0.05
filterTolerance = 1
toleranceLaserData = 0.01
yellowLightCriteria_LowAccuracy = 75
greenLightCriteria_LowAccuracy = 85
yellowLightCriteria_HighAccuracy = 80
greenLightCriteria_HighAccuracy = 95

laserStartPoint = 100 # the start point to measure
laserEndPoint = 550 # measure laser point to the end point

gVars = {}
gVars['toleranceLaserData'] = 0.004

# model building parameters
nValidCycle = 3
MODEL_SCORE = 60
VALID_CYCLE_NUM = 10
INHALE_AREA = 80
EXHALE_AREA = 20
BreathingCycle_Slope_Threshold = 0.5

# devices retry time
TIMEOVER_ROBOT = 60
TIMEOVER_LASER = 5

# enabled device setting, default is DEVICE_ALL
DEVICE_NONE = 0
DEVICE_ROBOT = 1
DEVICE_LASER = 2
DEVICE_ALL = 3

# 設定啟動的設備，正常是DEVICE_ALL，要個別測試就選擇robot或是laser
DEVICE_ENABLED = DEVICE_NONE

# entry or target
POINT_ENTRY = 1
POINT_TARGET = 2

TRAJECTORY_ALL = 0
TRAJECTORY_CURRENT = 1
TRAJECTORY_PARTNER = 2

SUPPORT_ARM_TORLERANCE = 20

# foot pedal action
NUM_OF_ACTION = 4
ACTION_NONE = 0
ACTION_NEXT_SCENE = 1
ACTION_DRIVE_CONFIRM = 2
ACTION_POSITION_ROBOT = 3

#Dialog Hint Box direction
HINT_UP_RIGHT   = 0
HINT_UP_LEFT    = 1
HINT_DOWN_RIGHT = 2
HINT_DOWN_LEFT  = 3

# trajectory item data
ROLE_VISIBLE    = Qt.UserRole + 1
ROLE_COLOR      = Qt.UserRole + 2
ROLE_DICOM      = Qt.UserRole + 3
ROLE_GROUP      = Qt.UserRole + 4
ROLE_TRAJECTORY = Qt.UserRole + 5
ROLE_DROPITEM   = Qt.UserRole + 6
ROLE_LOCK       = Qt.UserRole + 7


IMG_VISIBLE = 'image/eye2.png'
IMG_HIDDEN = 'image/eye-off2.png'
IMG_PARTIAL = 'image/eye-close-line2.png'

# 選擇是否略過註冊，for測試使用，以免每次都要跑registration shpere註冊
ENABLE_REGISTRATION = False
ENABLE_LUNG_VOLUME_DETECT = True

ROBOT_ACTION_P2P = 0
ROBOT_ACTION_TRACKING = 1

JOYSTICK_UP_FORWARD = 1
JOYSTICK_UP_BACKWARD = 2
JOYSTICK_UP_LEFT = 3
JOYSTICK_UP_RIGHT = 4
JOYSTICK_DOWN_FORWARD = 5
JOYSTICK_DOWN_BACKWARD = 6
JOYSTICK_DOWN_LEFT = 7
JOYSTICK_DOWN_RIGHT = 8

entry_full_1 = np.array([5,20.93392833,-85.62637816])
target_full_1 = np.array([ 35,80.55959477,-126.77388984])
entry_halt_1 = np.array([5,10.93381232,-85.61114631])
target_halt_1 = np.array([ 20,72.57378253,-127.63668602])

entry_full_2 = np.array([8,25.93392833,-90.62637816])
target_full_2 = np.array([ 32,75.55959477,-123.77388984])
entry_halt_2 = np.array([8,13.93381232,-90.61114631])
target_halt_2 = np.array([ 18,70.57378253,-130.63668602])

max_linear_count = 36000
max_linearDiffCount_1 = 5000 # motor axis 2 - motor axis 4
max_linearDiffCount_2 = 10000 # motor axis 4 - motor axis 2
max_rotateDiffCount = 9000 # motor axis 1 -motor axis 3
# Registration parameter
IDENTIFY_MARKER_TOLERENCE = 5
MIN_RADIUS = 3