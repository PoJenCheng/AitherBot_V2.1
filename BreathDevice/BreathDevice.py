import serial
import time
import threading
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from PyQt5.QtCore import *
from filterpy.kalman import KalmanFilter
from FunctionLib_Robot.logger import logger

class BreathingDetect(QObject):
    signalUpdateData = pyqtSignal(object, object, object, object)
    signalUpdatePercent = pyqtSignal(float, float, float, float)
    signalUpdatePercentLine = pyqtSignal(float, float, float, float)
    # Low-pass filter parameters
    alpha = 0.3  # Smoothing factor for the filter (0 < alpha < 1)

    # Serial port and baud rate configuration
    serial_port = 'COM5'  # Adjust to your serial port
    baud_rate = 9600
        
    def __init__(self):
        super().__init__()
        
        # Data lists
        self.pitch_data = []
        self.roll_data = []
        self.time_data = []
        self.percentPitch = {}
        self.kf_pitch = None
        self.kf_roll = None
        self.filtered_pitch = None
        self.filtered_roll = None
        self.mergeData = None
        
        # Open the serial connection
        time.sleep(2)  # Allow time for the Arduino to initialize
        
    def __CalculatePercent(self, pitchValue, rollValue):
        if len(self.detectPitch) == 0:
            self.detectPitch = [pitchValue]
        else:
            self.detectPitch.append(self.alpha * pitchValue + (1 - self.alpha) * self.detectPitch[-1])
            
        if len(self.detectRoll) == 0:
            self.detectRoll = [rollValue]
        else:
            self.detectRoll.append(self.alpha * rollValue + (1 - self.alpha) * self.detectRoll[-1])
            
        maxPitch = np.max(self.filtered_pitch)
        minPitch = np.min(self.filtered_pitch)
        
        maxRoll = np.max(self.filtered_roll)
        minRoll = np.min(self.filtered_roll)
        
        maxMerge = np.max(self.mergeData)
        minMerge = np.min(self.mergeData)
        
        maxMerge2 = np.max(self.mergeData2)
        minMerge2 = np.min(self.mergeData2)
        
        try:
            percentPitch = (self.detectPitch[-1] - minPitch) / (maxPitch - minPitch)
            percentRoll = (self.detectRoll[-1] - minRoll) / (maxRoll - minRoll)
            
            detectMerge = self.CombindAngles(self.detectPitch[-1], self.detectRoll[-1])
            detectMerge2 = self.CombindAngles2(self.detectPitch[-1], self.detectRoll[-1])
            
            percentMerge = (detectMerge - minMerge) / (maxMerge - minMerge)
            percentMerge2 = (detectMerge2 - minMerge2) / (maxMerge2 - minMerge2)
            
            # self.signalUpdatePercentLine.emit(self.detectPitch[-1], self.detectRoll[-1], detectMerge, detectMerge2)
            # self.signalUpdatePercent.emit(percentPitch, percentRoll, percentMerge, percentMerge2)
            self.signalUpdatePercentLine.emit(self.detectPitch[-1], self.detectRoll[-1], detectMerge, 0.0)
            self.signalUpdatePercent.emit(percentPitch, percentRoll, percentMerge, 0.0)
            return percentPitch, percentRoll
        
        except Exception as msg:
            print(msg)
    
    def __Detect(self):
        if self.ser.in_waiting > 0:
            line = self.ser.readline().decode('utf-8').strip()
            data = line.split(",")

            if len(data) == 3:
                try:
                    x, y, z = map(float, data)

                    # Calculate pitch and roll angles
                    pitch = np.arctan2(x, np.sqrt(y**2 + z**2)) * (180.0 / np.pi)
                    roll = np.arctan2(y, np.sqrt(x**2 + z**2)) * (180.0 / np.pi)
                    
                    # self.kf_pitch.predict()
                    # self.kf_pitch.update(pitch)
                    
                    # self.kf_roll.predict()
                    # self.kf_roll.update(roll)
                    
                    # self.__CalculatePercent(self.kf_pitch.x[0][0], self.kf_roll.x[0][0])
                    self.__CalculatePercent(pitch, -roll)
                    

                except Exception as msg:
                    print(msg)
                    
    def __FilterMinMax(self, timeData, data):
        timeData = np.asarray(timeData)
        data = np.asarray(data)
        
        slopeLast = 0
        lstMax = []
        lstMin = []
        idxStart = 0
        for i in range(len(timeData)):
            if timeData[i] - timeData[idxStart] > 1:
                # 紀錄累積時間至少達到一秒
                xAxis = np.arange(len(data[idxStart:i]))
                # 計算多項式逼近的一維參數，分別為斜率和截距
                slope, intercept = np.polyfit(xAxis, data[idxStart:i], 1)
                # 計算斜率變化量
                slopeDiff = slope - slopeLast
                
                if abs(slopeDiff) > 0.001 and slopeLast * slope < 0:
                    # 當前斜率與上一次斜率發生正負交錯時，代表有峰值或低波谷
                    # 當前斜率為負，前一次為正，代表是波峰，因此找最大值；相反為低谷，找最小值
                    # 並且紀錄當時的斜率變化量，供後面計算過濾
                    if slope < 0:
                        # find maximum value
                        # timeInMax = lstTime[np.argmax(subData)]
                        idxMax = idxStart + np.argmax(data[idxStart:i])
                        lstMax.append([data[idxMax], idxMax])
                        idxStart = i
                    elif slope > 0:
                        # timeInMin = lstTime[np.argmin(subData)]
                        idxMin = idxStart + np.argmin(data[idxStart:i])
                        lstMin.append([data[idxMin], idxMin])
                        idxStart = i
                slopeLast = slope
        
        
        dataMapper = np.ones_like(data, dtype = bool)
        
        if len(lstMin) <= 1 or len(lstMax) <= 1:
            return dataMapper
        
        lstMin = np.asarray(lstMin)
        lstMax = np.asarray(lstMax)
        minArg = np.argsort(lstMin[:, 0])
        maxArg = np.argsort(lstMax[:, 0])
        
        value2ndMin = lstMin[minArg[1]][0]
        dataMapper[data < value2ndMin] = False
        
        value2ndMax = lstMax[maxArg[-2]][0]
        dataMapper[data > value2ndMax] = False
        
        # idxMin = int(lstMin[minArg[1]][1])
        
        # if idxMin < len(data) / 2:
        #     dataMapper[:idxMin] = False
        #     print(f'0 - {idxMin} gone')
        # else:
        #     dataMapper[idxMin:] = False
        #     print(f'{idxMin} ~  gone')
            
        # idxMax = int(lstMax[maxArg[-2]][1])
        
        # if idxMax > len(data) / 2:
        #     dataMapper[idxMax:] = False
        #     print(f'{idxMax} ~  gone')
        # else:
        #     dataMapper[:idxMax] = False
        #     print(f'0 - {idxMax} gone')
        
        # argRange = np.where(dataMapper)
        return dataMapper
    
    def CombindAngles2(self, *angles):
        merge_angles = []
        
        angles = np.asarray(angles)
        if len(angles.shape) == 1:
            angles = angles.reshape(-1, 1)
            
        for pitch_deg, roll_deg in zip(*angles):
            # pitch_deg, roll_deg = angles
            
            # Convert degrees to radians
            pitch = np.radians(pitch_deg)
            roll = np.radians(roll_deg)
            
            # Calculate normal vector components
            nx = np.sin(pitch)
            ny = -np.sin(roll) * np.cos(pitch)
            nz = np.cos(roll) * np.cos(pitch)
            v =  np.array([nx, ny, nz]).flatten()
            
            # 計算與 z 軸的合成角
            norm = np.linalg.norm(v)
            deg = np.degrees(np.arccos(nz / norm))  # 注意法向量的方向
            
            # 計算向量的大小
            # n = np.array([0, 0, 1])
            # v_norm = np.linalg.norm(v)
            # n_norm = np.linalg.norm(n)
            
            # # 檢查向量是否為零
            # if v_norm == 0 or n_norm == 0:
            #     raise ValueError("向量或法向量不能為零")
            
            # # 計算內積
            # dot_product = np.dot(v, n)
            
            # # 計算向量與平面的夾角
            # angle_rad = np.arcsin(np.abs(dot_product) / (v_norm * n_norm))
            
            # # 將弧度轉換為度數
            # deg = np.degrees(angle_rad)
            
            merge_angles.append(deg)
        
        return np.array(merge_angles)
        
    def CombindAngles(self, *angles):
        if not all(isinstance(x, type(angles[0])) for x in angles):
            logger.error('inputs are not the same type')
            return None
        
        if all(isinstance(x, (tuple, list, np.ndarray)) for x in angles):
            if not all(len(x) == len(angles[0]) for x in angles):
                logger.error('inputs have different length')
                return None
        
        mergeData = np.degrees(np.arctan(np.sqrt(np.sum(np.tan(np.radians(x)) ** 2 for x in angles))))
        return mergeData
    
    def StartDetect(self):
        # self.idle = QTimer()
        # self.idle.timeout.connect(self.__Detect)
        # self.idle.start(100)
        self.ser = serial.Serial(self.serial_port, self.baud_rate)
        self.detectPitch = []
        self.detectRoll = []
        while True:
            self.__Detect()
            # QCoreApplication.processEvents()
    
    def StartRecord(self):
        
        self.ser = serial.Serial(self.serial_port, self.baud_rate)
        # Sampling duration in seconds
        duration = 25
        start_time = time.time()
        end_time = start_time + 25

        print("Start to measure")

        # Apply low-pass filter using exponential moving average
        filtered_pitch = None
        filtered_roll = None
        
        # Data collection loop
        while time.time() < end_time:
            timeDelta = time.time() - start_time
            
            
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8').strip()
                data = line.split(",")

                if timeDelta < 5:
                    continue
            
                if len(data) == 3:
                    try:
                        x, y, z = map(float, data)

                        # Calculate pitch and roll angles
                        pitch = np.arctan2(x, np.sqrt(y**2 + z**2)) * (180.0 / np.pi)
                        roll = np.arctan2(y, np.sqrt(x**2 + z**2)) * (180.0 / np.pi)

                        # Append data
                        self.pitch_data.append(pitch)
                        self.roll_data.append(-roll)
                        self.time_data.append(timeDelta)

                        if filtered_pitch is None:
                            filtered_pitch = [self.pitch_data[0]]
                        else:
                            filtered_pitch.append(self.alpha * self.pitch_data[-1] + (1 - self.alpha) * filtered_pitch[-1])
                            
                        if filtered_roll is None:
                            filtered_roll = [self.roll_data[0]]
                        else:
                            filtered_roll.append(self.alpha * self.roll_data[-1] + (1 - self.alpha) * filtered_roll[-1])
                            
                        mergeData = self.CombindAngles(filtered_pitch, filtered_roll)
                        mergeData2 = self.CombindAngles2(filtered_pitch, filtered_roll)
                        
                        logger.debug(f'{mergeData[-1]}, {mergeData2[-1]}')
                        # self.signalUpdateData.emit(filtered_pitch, filtered_roll, list(mergeData), list(mergeData2))
                        self.signalUpdateData.emit(filtered_pitch, filtered_roll, list(mergeData), None)
                            
                    except Exception as msg:
                        print(msg)
                        
                        
                # QCoreApplication.processEvents()

        # Close the serial port
        self.ser.close()
        
        # idxStart = 0
        # slopeLast = 0
        # lstWave = []
        # for i in range(len(self.time_data)):
        #     if self.time_data[i] - self.time_data[idxStart] > 1:
        #         # 紀錄累積時間至少達到一秒
        #         xAxis = np.arange(len(filtered_pitch[idxStart:i]))
        #         # 計算多項式逼近的一維參數，分別為斜率和截距
        #         slope, intercept = np.polyfit(xAxis, filtered_pitch[idxStart:i], 1)
        #         # 計算斜率變化量
        #         slopeDiff = slope - slopeLast
                
        #         if abs(slopeDiff) > 0.001 and slopeLast * slope < 0:
        #             # 當前斜率與上一次斜率發生正負交錯時，代表有峰值或低波谷
        #             # 當前斜率為負，前一次為正，代表是波峰，因此找最大值；相反為低谷，找最小值
        #             # 並且紀錄當時的斜率變化量，供後面計算過濾
        #             if slope < 0:
        #                 # find maximum value
        #                 # timeInMax = lstTime[np.argmax(subData)]
        #                 idxMax = np.argmax(filtered_pitch[idxStart:i])
        #                 lstWave.append([filtered_pitch[idxStart + idxMax], idxStart + idxMax])
        #                 idxStart = i
                        
        #             elif slope > 0:
        #                 # timeInMin = lstTime[np.argmin(subData)]
        #                 idxMin = np.argmin(filtered_pitch[idxStart:i])
        #                 lstWave.append([filtered_pitch[idxStart + idxMin], idxStart + idxMin])
        #                 idxStart = i
                      
        #             if len(lstWave) > 2:
                        
        #                 xStart1 = lstWave[0][1]
                        
        #                 xStart2 = (lstWave[-2][1] + lstWave[-1][1]) // 2
        #                 # lastPoint = lstWave[-1]
        #                 lstWave.clear()  
        #                 lstWave.append([filtered_pitch[xStart2], xStart2])
        #                 # lstWave.append(lastPoint)

        #                 x = np.arange(xStart2 - xStart1)
        #                 p = np.polyfit(x, filtered_pitch[xStart1:xStart2], 3)
        #                 y = np.polyval(p, x)
        #                 filtered_pitch[xStart1:xStart2] = y
                    
                
        #         slopeLast = slope
        
        if not all(len(filtered_pitch) == len(x) for x in [mergeData, mergeData2]):
            logger.debug(f'length = {len(filtered_pitch)}, merge 2 = {len(mergeData2)}')
        
        argRange1 = self.__FilterMinMax(self.time_data, filtered_pitch)
        
        argRange2 = self.__FilterMinMax(self.time_data, filtered_roll)
        mapper = argRange1 & argRange2
        filtered_pitch = np.asarray(filtered_pitch)[mapper]
        filtered_roll = np.asarray(filtered_roll)[mapper]
        mergeData = np.asarray(mergeData)[mapper]
        mergeData2 = np.asarray(mergeData2)[mapper]
        self.time_data = np.asarray(self.time_data)[mapper]

        if not all(len(filtered_pitch) == len(x) for x in [mergeData, mergeData2]):
            logger.debug(f'length = {len(filtered_pitch)}, merge 2 = {len(mergeData2)}')
            
        # self.signalUpdateData.emit(filtered_pitch, filtered_roll, list(mergeData))
        
        # filtered_pitch = np.asarray(filtered_pitch)
        # filtered_roll = np.asarray(filtered_roll)
        # mergeData = np.asarray(mergeData)
        # self.time_data = np.asarray(self.time_data)

        # self.signalUpdateData.emit(filtered_pitch, filtered_roll, list(mergeData), list(mergeData2))
        self.signalUpdateData.emit(filtered_pitch, filtered_roll, list(mergeData), None)
        

        # for i in range(1, len(self.pitch_data)):
        #     # Update pitch and roll with EMA
        #     filtered_pitch_data.append(self.alpha * self.pitch_data[i] + (1 - self.alpha) * filtered_pitch_data[i - 1])
        #     filtered_roll_data.append(self.alpha * self.roll_data[i] + (1 - self.alpha) * filtered_roll_data[i - 1])
        
        self.filtered_pitch = filtered_pitch
        self.filtered_roll = filtered_roll
        self.mergeData = mergeData
        self.mergeData2 = mergeData2
        # df = pd.DataFrame(self.pitch_data, columns = ['times'])
        # pitch_std = df['times'].rolling(window = 10).std()
        # print(pitch_std)
        
        # df = pd.DataFrame(self.roll_data, columns = ['times'])
        # roll_std = df['times'].rolling(window = 10).std()
        # print(roll_std)
        
        # filtered_pitch_data = [self.pitch_data[0]]
        # for i in range(11, len(self.pitch_data)):
        #     data_slice = np.array(self.pitch_data[i - 10:i])
        #     mean = np.mean(data_slice)
        #     std = np.std(data_slice)
            
        #     score = np.abs(data_slice - mean) / std
        #     sortedData = data_slice[np.argsort(score)]
            
        #     pitch = np.sum(sortedData[:2] * 0.2) + filtered_pitch_data[-1] * 0.6
        #     filtered_pitch_data.append(pitch)
            
        # filtered_roll_data = [self.roll_data[0]]
        # for i in range(11, len(self.roll_data)):
        #     data_slice = np.array(self.roll_data[i - 10:i])
        #     mean = np.mean(data_slice)
        #     std = np.std(data_slice)
            
        #     score = np.abs(data_slice - mean) / std
        #     sortedData = data_slice[np.argsort(score)]
            
        #     roll = np.sum(sortedData[:2] * 0.2) + filtered_roll_data[-1] * 0.6
        #     filtered_roll_data.append(roll)
        
        # kf = KalmanFilter(dim_x = 1, dim_z = 1)
        # kf.x = np.array([[0.]])
        # kf.F = np.array([[1.]])       # 狀態轉換矩陣
        # timeDelta = self.time_data[1] - self.time_data[0]
        # kf.H = np.array([[1.0]])       # 測量矩陣
        # kf.P *= 10.                 # 初始不確定性
        # kf.R = 1.0                    # 測量不確定性
        # kf.Q = 1e-7 
        
        # filtered_pitch_data = []  # Start with the first data point
        # filtered_roll_data = []

        # for pitch in self.pitch_data:
        #     kf.predict()
        #     kf.update(pitch)
        #     filtered_pitch_data.append(kf.x[0][0])
            
        # self.kf_pitch = kf
            
            
        # kf = KalmanFilter(dim_x = 1, dim_z = 1)
        # kf.x = np.array([[0.]])
        # kf.F = np.array([[1.]])       # 狀態轉換矩陣
        # kf.H = np.array([[1.]])       # 測量矩陣
        # kf.P *= 10.                 # 初始不確定性
        # kf.R = 1.0                    # 測量不確定性
        # kf.Q = 1e-7 
            
        # for roll in self.roll_data:
        #     kf.predict()
        #     kf.update(roll)
        #     filtered_roll_data.append(kf.x[0][0])
        
        # self.kf_roll = kf
        
        # Save raw data plot
        # plt.figure(figsize=(12, 6))

        # # Plot for raw pitch
        # plt.subplot(2, 1, 1).set_ylim(-10, 10)
        # # plt.subplot(2, 1, 1)
        # plt.plot(self.time_data, self.pitch_data, color='blue')
        # plt.title("Raw Pitch Angle Over Time")
        # plt.xlabel("Time (s)")
        # plt.ylabel("Pitch (degrees)")
        

        # # Plot for raw roll
        # plt.subplot(2, 1, 2).set_ylim(-10, 10)
        # # plt.subplot(2, 1, 2)
        # plt.plot(self.time_data, self.roll_data, color='orange')
        # plt.title("Raw Roll Angle Over Time")
        # plt.xlabel("Time (s)")
        # plt.ylabel("Roll (degrees)")

        # # Adjust layout and save raw data plot as PNG
        # plt.tight_layout()
        # plt.savefig("raw_pitch_roll_angles.png")

        # # Save filtered data plot
        # plt.figure(figsize=(12, 6))

        # # Plot for filtered pitch
        # plt.subplot(2, 1, 1).set_ylim(-10, 10)
        # # plt.subplot(2, 1, 1)
        # # plt.plot(self.time_data[10:], filtered_pitch_data, color='blue')
        # plt.plot(self.time_data, filtered_pitch, color='blue')
        # plt.title("Filtered Pitch Angle Over Time")
        # plt.xlabel("Time (s)")
        # plt.ylabel("Pitch (degrees)")

        # # Plot for filtered roll
        # plt.subplot(2, 1, 2).set_ylim(-10, 10)
        # # plt.subplot(2, 1, 2)
        # # plt.plot(self.time_data[10:], filtered_roll_data, color='orange')
        # plt.plot(self.time_data, filtered_roll, color='orange')
        # plt.title("Filtered Roll Angle Over Time")
        # plt.xlabel("Time (s)")
        # plt.ylabel("Roll (degrees)")

        # # Adjust layout and save filtered data plot as PNG
        # plt.tight_layout()
        # plt.savefig("filtered_pitch_roll_angles.png")
        
    def RunDetector(detector:'BreathingDetect'):
        time.sleep(1)
        detector.StartRecord()
        print('ready to detect')
        time.sleep(3)
        detector.StartDetect()
