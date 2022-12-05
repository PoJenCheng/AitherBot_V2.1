from multiprocessing.sharedctypes import Value
import pydicom
import matplotlib.pyplot as plt
import numpy
import os
from keras.models import load_model
import cv2
import math
from PyQt5.QtGui import *

"跟DICOM有關的, 會要建立很多組DICOM"
class DICOM():
    def __init__(self):
        pass
        
    def LoadPath(self, folderPath):
        """分辨是不是DICOM. 分辨是否一組UID

        Args:
            folderPath (_string_): DICOM folder path
            
        Returns:
            metadata (_list_):
            metadataSeriesNum (_list_):
        """
        filePath = []
        metadata = []
        metadataSeriesNum = []
        metadataStudy = []
        for dirPath, dirNames, fileNames in os.walk(folderPath):
            for f in fileNames:
                dir = os.path.join(dirPath, f)
                filePath.append(dir)
        n=0
        for s in filePath:
            try:
                metadata.append(pydicom.read_file(s))
                metadataSeriesNum.append(metadata[n].SeriesInstanceUID)
                metadataStudy.append(metadata[n].StudyInstanceUID)
                n+=1
            except:
                continue
        seriesNumber = numpy.unique(metadataStudy)
        if seriesNumber.shape[0]>1 or len(metadataStudy)==0:
            metadata = 0
            metadataSeriesNum = 0
        return metadata, metadataSeriesNum
        
    def SeriesSort(self, metadata, metadataSeriesNum):
        """依照SeriesNumber為key, 分類/分組metadata + pixel_array
           分類/分組/SeriesNumber, 自動辨別是不是資料夾及DICOM

        Args:
            metadata (_list_):
            metadataSeriesNum (_list_):
            
        Returns:
            seriesNumberLabel (_numpy array_): 有幾組的SeriesNumber的Label
            dicDICOM (_dictionary_): {SeriesNumber : metadata + pixel_array}
        """
        seriesNumberLabel = numpy.unique(metadataSeriesNum)
        matrix=[]
        dicDICOM = {}
        for n in seriesNumberLabel:
            for i in range(len(metadata)):
                if metadata[i].SeriesInstanceUID == n:
                    matrix.append(metadata[i])
            dicDICOM.update({n:matrix})
            matrix=[]
        return seriesNumberLabel, dicDICOM
    
    def ReadDicom(self, seriesNumberLabel, dicDICOM):
        """read DICOM
           把分類好的dicDICOM, 找到要的metadata + pixel_array
           return pixel_array(_list_)

        Args:
            seriesNumberLabel (_numpy array_): 有幾組的SeriesNumber的Label
            dicDICOM (_dictionary_): {SeriesNumber : metadata + pixel_array}
            
        Returns:
            imageTag (_list_): DICOM list sort by InstanceNumber (include metadata and pixel_array)
        """
        seriesN=[]
        for s in seriesNumberLabel:
            seriesN.append(len(dicDICOM.get(s)))
        tmp = max(seriesN)
        index = seriesN.index(tmp)
        
        imageInfo = dicDICOM.get(seriesNumberLabel[index])
        imageTag = [0]*tmp
        "照InstanceNumber排序"
        for i in range(len(imageInfo)):
            tmp = imageInfo[i]
            imageTag[tmp.InstanceNumber-1] = tmp
        return imageTag
    
    def GetImage(self, imageTag):
        """get image from image DICOM

        Args:
            imageTag (_list_): DICOM list sort by InstanceNumber (include metadata and pixel_array)

        Returns:
            image (_list_): image (only pixel array)
        """
        image = []
        try:
            for sliceNum in range(len(imageTag)-1):
                if imageTag[sliceNum].pixel_array.shape==imageTag[sliceNum+1].pixel_array.shape:
                    image.append(imageTag[sliceNum].pixel_array)
                else:
                    image = 0
                    break
        except:
            image = 0
        return image
    
    def Transfer2Hu(self, image, rescaleSlope, rescaleIntercept):
        """transfer pixel value to Hounsfield Unit (Hu)
           Hounsfield Unit (Hu) = pixel value * rescale slope + rescale intercept

        Args:
            image (_list_): image (only pixel array)
            rescaleSlope (_number_): from tag (0028,1053) rescaleSlope
            rescaleIntercept (_number_): from tag (0028,1052) rescaleIntercept

        Returns:
            imageHu (_list_): image in Hounsfield Unit (Hu)
        """
        imageHu = []
        for sliceNum in range(len(image)):
            imageHu.append(image[sliceNum] * rescaleSlope + rescaleIntercept)
        return imageHu

    def ImgTransfer2Mm(self, image, pixel2Mm):
        cutImagesHu=[]
        for z in range(image.shape[0]):
            "resize, 會變成mm"
            if pixel2Mm[0]<1 and abs(pixel2Mm[1])<1 and abs(pixel2Mm[2])==1:
                src_tmp = cv2.resize(image[z,:,:],dsize=None,fx=pixel2Mm[0],fy=pixel2Mm[1],interpolation=cv2.INTER_AREA)
                cutImagesHu.append(src_tmp)
            elif pixel2Mm[0]>1 and abs(pixel2Mm[1])>1 and abs(pixel2Mm[2])==1:
                src_tmp = cv2.resize(image[z,:,:],dsize=None,fx=pixel2Mm[0],fy=pixel2Mm[1],interpolation=cv2.INTER_CUBIC)
                cutImagesHu.append(src_tmp)
            elif pixel2Mm[0]==1 and abs(pixel2Mm[1])==1 and abs(pixel2Mm[2])==1:
                cutImagesHu.append(image[z,:,:])
            else:
                cutImagesHu.append(image[z,:,:])
        return cutImagesHu
    
    def GetPixel2Mm(self, imageTag):
        """Get Pixel to Mm array

        Args:
            imageTag (_list_): DICOM list sort by InstanceNumber (include metadata and pixel_array)

        Returns:
            pixel2Mm (_list_): Pixel to Mm array
        """
        pixel2Mm = []
        pixel2Mm.append(imageTag.PixelSpacing[0])
        pixel2Mm.append(imageTag.PixelSpacing[1])
        pixel2Mm.append(imageTag.SpacingBetweenSlices)
        return pixel2Mm
    
    def GetGrayImg(self, imageHu2D, ww, wl):
        """transfer image from 4096 to 256 for plot

        Args:
            imageHu2D (_numpy.array_): image 2D in Hounsfield Unit (Hu)
            ww (_number_): from tag (0028,1051)	Window Width
            wl (_number_): from tag (0028,1050)	Window Center

        Returns:
            imageHu2D_ (_array_): image 2D in HU and 256
        """
        imageHu2D_ = numpy.ones((imageHu2D.shape[0],imageHu2D.shape[1]))
        
        for i in range(imageHu2D.shape[0]):
            for j in range(imageHu2D.shape[1]):
                imageHu2D_[i,j] = (255/ww)*imageHu2D[i,j]+128-((255*wl)/ww)
                if imageHu2D_[i,j] >= 255:
                        imageHu2D_[i,j] = 255
                elif imageHu2D_[i,j] <= 0:
                        imageHu2D_[i,j] = 0
        return imageHu2D_

    def Ready2Qimg(self, imageHu2D):
        """ready image to show on label

        Args:
            imageHu2D (_numpy.array_): 2D image

        Returns:
            qimg (_QImage_): image, to show on label
        """
        imgHeight, imgWidth = imageHu2D.shape
        gray = numpy.uint8(imageHu2D)
        gray3Channel = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        bytesPerline = 3 * imgWidth
        qimg = QImage(gray3Channel, imgWidth, imgHeight, bytesPerline, QImage.Format_RGB888).rgbSwapped()
        return qimg
        
"跟對位有關"
class REGISTRATION():
    def __init__(self):
        self.PlanningPath = []
        return
        
    
    def TransformationMatrix(self, ballCenterMm):
        """算轉換矩陣

        Args:
            ballCenterMm (_numpy.array_): 已配對定位球中心點

        Returns:
            TransformationMatrix(_numpy.array_): numpy.dot(R_y,R_z) Transformation Matrix
        """
        "ball_center_mm(1,:);   原點"
        "ball_center_mm(2,:);   x 軸"
        "ball_center_mm(3,:);   y 軸"  
        ball_vector_x = ballCenterMm[1] - ballCenterMm[0]
        ball_vector_y = ballCenterMm[2] - ballCenterMm[0]
        "建立新座標(向量兩兩垂直)"
        vectorZ = numpy.array(numpy.cross(ball_vector_x, ball_vector_y))
        vectorX = numpy.array(ball_vector_x)
        vectorY = numpy.array(numpy.cross(vectorZ,vectorX))
        
        new_vector = numpy.array([vectorX,vectorY,vectorZ])
        
        "計算單位向量"
        unit_new_vector = []
        for vector in new_vector:
            unit_new_vector.append(vector / self.GetNorm(vector))
        unit_new_vector = numpy.array(unit_new_vector)
        "計算選轉角度"
        angle_radian = []
        unit = numpy.eye(3, dtype = 'int')
        for n in range(unit.shape[0]):
            top = numpy.dot(unit_new_vector[n],unit[n])
            down = self.GetNorm(unit_new_vector[n])*self.GetNorm(unit[n])
            angle_radian.append(math.acos(top / down))
        angle_radian = numpy.array(angle_radian)
        "轉動矩陣"
        R_z = numpy.array([[math.cos(-angle_radian[1]), -math.sin(-angle_radian[1]), 0],
               [math.sin(-angle_radian[1]), math.cos(-angle_radian[1]), 0],
               [0, 0, 1]])
        
        "算出轉後的單位向量 + 建立新座標(向量兩兩垂直)"
        new_vector = unit_new_vector
        unit_new_vector = []
        for vector in new_vector:
            unit_new_vector.append(numpy.dot(R_z,vector))
        "計算選轉角度"
        angle_radian = []
        unit = numpy.eye(3, dtype = 'int')
        for n in range(unit.shape[0]):
            top = numpy.dot(unit_new_vector[n],unit[n])
            down = self.GetNorm(unit_new_vector[n])*self.GetNorm(unit[n])
            angle_radian.append(math.acos(top / down))
        angle_radian = numpy.array(angle_radian)
        "轉動矩陣"
        R_y = numpy.array([[math.cos(angle_radian[0]), 0, math.sin(angle_radian[0])],
        [0, 1, 0],
        [-math.sin(angle_radian[0]), 0, math.cos(angle_radian[0])]])
        
        return numpy.dot(R_y,R_z)
    
    def GetBallSection(self,candidateBall):
        """calculate Transformation Matrix

        Args:
            candidateBall (_dictionary_): candidate ball center 
            same as dictionaryPoint (_dictionary_): point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])

        Returns:
            numpy.array([showAxis, showSlice]) (_numpy.array_): show Axis(x=0, y=1, z=2), show Slice/section (slice number)
        
        """
        tmpMin = numpy.min(candidateBall,0)
        tmpMax = numpy.max(candidateBall,0)
        tmpMean = numpy.mean(candidateBall,0)
        for i in range(tmpMean.shape[0]):
            if abs(tmpMax[i]-tmpMean[i]) < 2 and abs(tmpMin[i]-tmpMean[i]) < 2:
                """showAxis
                0 = x axis
                1 = y axis
                2 = z axis
                """
                "要顯示的Axis跟Slice"
                showAxis = i
                showSlice = int(tmpMean[i])
                break
        return numpy.array([showAxis, showSlice])
    
    def GetError(self,ball):
        """get rigistration error/difference

        Args:
            ball (_numpy.array_): registration ball center

        Returns:
            [numpy.min(error),numpy.max(error),numpy.mean(error)] (_list_): [min error, max error, mean error]
        """
        error = []
        legsA = 140
        legsB = 150
        hypotenuse = self.GetNorm(numpy.array([legsA,legsB]))
        error.append(abs(self.GetNorm(ball[0]-ball[1])-hypotenuse))
        error.append(abs(self.GetNorm(ball[0]-ball[2])-legsB))
        error.append(abs(self.GetNorm(ball[1]-ball[2])-legsA))
        return [numpy.min(error),numpy.max(error),numpy.mean(error)]
    
    def GetNorm(self, V):
        """get norm

        Args:
            V (_numpy.array_): vector

        Returns:
            d (_number_): (float)
        """
        if V.shape[0] == 3:
            d = math.sqrt(numpy.square(V[0])+numpy.square(V[1])+numpy.square(V[2]))
        elif V.shape[0] == 2:
            d = math.sqrt(numpy.square(V[0])+numpy.square(V[1]))
        else:
            print("GetNorm error")
            return 0
        return d
        
    def ThresholdFilter(self, imageHu):
        """只保留[down_, up_]之間的圖, 並且為PIXEL_MAX, 其他為0

        Args:
            imageHu (_list_): input

        Returns:
            imagesHuThr (_list_): output
        """ 
        imagesHuThr = []
        PIXEL_MAX = 4096-1
        down_ = -800
        up_ = 300
        for z in range(len(imageHu)):
            ret, th4 = cv2.threshold(imageHu[z], up_, PIXEL_MAX, cv2.THRESH_TOZERO_INV)
            ret, th5 = cv2.threshold(th4, down_, PIXEL_MAX, cv2.THRESH_BINARY)
            imagesHuThr.append(th5)
        return imagesHuThr
    
    def FindBallXY(self, imageHu, pixel2Mm):
        """找2D(XY平面)圓心, 所以會有不是球的圓心被找到

        Args:
            imageHu (_numpy.array_): _description_
            pixel2Mm (_list_): Pixel to Mm array

        Returns:
            result_centroid (_type_): _description_
        """
        y = 200
        x = 512
        NORMALIZE=4096-1
        "cut image"
        cutImagesHu=[]
        if pixel2Mm[0]!=pixel2Mm[1]:
            print("xy plot resize is fail")
            return
        for z in range(int(imageHu.shape[0]/3),imageHu.shape[0]):
            cutImagesHu.append(imageHu[z,:y,:x])
            
        "filter & 二值化"
        cutImageHuThr = self.ThresholdFilter(cutImagesHu)
        src_tmp = numpy.uint8(cutImageHuThr)
        resultCentroid_xy = []
        
        "係數"
        "Hough Circles找半徑跟圓心"
        ratio = 3
        low_threshold = 15
        "Radius範圍 [4.5mm ~ (21/2)+3mm]"
        minRadius=int((4.5/pixel2Mm[0]))
        maxRadius=int((21/pixel2Mm[0])/2)+3
        
        
        "每一張DICOM找圓, 圓心, 半徑"
        for z in range(src_tmp.shape[0]):
            "filter"
            src_tmp[z,:,:] = cv2.bilateralFilter(src_tmp[z,:,:],5,100,100)
            "畫輪廓"
            contours, hierarchy = cv2.findContours(src_tmp[z,:,:],
                                                cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)
            "建立全黑的圖片畫輪廓"
            shape = (src_tmp.shape[1], src_tmp.shape[2], 1)
            black_image = numpy.zeros(shape, numpy.uint8)
            cv2.drawContours(black_image,contours,-1,(256/2, 0, 0),1)
            "用輪廓找質心"
            centroid = []
            for c in contours:
                if c.shape[0] > 4 and c.shape[0]<110:
                    M = cv2.moments(c)
                    if M["m00"] != 0:
                        Cx = (M["m10"]/M["m00"])
                        Cy = (M["m01"]/M["m00"])
                        centroid.append((Cx,Cy))
            "Hough Circles找半徑跟圓心"
            circles = cv2.HoughCircles(black_image, cv2.HOUGH_GRADIENT, 1, 75,
                                        param1=low_threshold*ratio, param2=low_threshold,
                                        minRadius=minRadius, maxRadius=maxRadius)
            if circles is not None and centroid is not None:
                "交集"
                "centroid = 這張圖有幾個質心"
                "circles = 這張圖有幾個hough circle"
                for i in centroid:
                    for j in circles[0, :]:
                        distance = math.sqrt((i[0]-j[0])**2+(i[1]-j[1])**2)
                        if distance<2:
                            Px = i[0]*pixel2Mm[0]
                            Py = i[1]*pixel2Mm[1]
                            Pz = (z+int(imageHu.shape[0]/3))*abs(pixel2Mm[2])
                            Pr = j[2]*pixel2Mm[0]
                            
                            resultCentroid_xy.append([Px,Py,Pz,Pr])
        return resultCentroid_xy
  
    def SortPointXY(self, pointMatrix, pixel2Mm):
        """Sort Point Matrix for FindBall() result
           分類/分組所有2D圓心, 以第一點為key, 存成numpy.array

        Args:
            pointMatrix (_list_): _description_

        Returns:
            dictionary(_dictionary_): point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])
        """
        dictionaryTmp = {}
        dictionary = {}
        "pointMatrix 點跟點依序倆倆比較，符合條件的為同一組"
        "條件: "
        "兩點XY距離不超過2mm"
        "Z軸距離不超過20+13mm"
        for num1 in range(len(pointMatrix)-1):
            tmp=[]
            value = []
            for num2 in range(num1+1,len(pointMatrix)):
                P1 = pointMatrix[num1]
                P2 = pointMatrix[num2]
                distance = math.sqrt(numpy.square(P1[0]-P2[0])+numpy.square(P1[1]-P2[1]))
                dz = abs(P1[2]-P2[2])
                if distance <= 2 and dz < 20+13:
                    tmp.append(pointMatrix[num2])
            value.append(pointMatrix[num1])
            value.extend(tmp)
            dictionaryTmp.update({tuple(pointMatrix[num1]):numpy.array(value)})

        "刪除重複的組別 & 組別太小的"
        "符合以下條件都刪除: "
        "組別裡元素個數(=Z軸距離)大於15mm & key[i]與key[i+1]距離小於50mm"
        "組別裡元素個數(=Z軸距離)小於15mm"
        key_ = list(dictionaryTmp.keys())
        delete_label = []
        for num1 in range(len(key_)-1):
            key = key_[num1]
            values = dictionaryTmp.get(key)
            if values.shape[0] >= 15:
                for num2 in range(num1+1,len(key_)):
                    P1 = key_[num1]
                    P2 = key_[num2]
                    distance = math.sqrt(numpy.square(P1[0]-P2[0])+numpy.square(P1[1]-P2[1])+numpy.square(P1[2]-P2[2]))
                    if distance <= 50:
                        delete_label.append(tuple(P2))
            else:
                delete_label.append(tuple(key))
        values = dictionaryTmp.get(key_[-1])
        if values.shape[0] < 15:
            delete_label.append(tuple(key_[-1]))
        for dic1 in delete_label:
            try:
                del dictionaryTmp[dic1]
            except:
                pass
        "同組裡面若有斷層(不連貫), 自動分開"
        "條件: "
        "前-後(不連貫距離) < -3mm"
        "自動分開以後留下組別裡元素個數大於15mm的"
        key_ = list(dictionaryTmp.keys())
        delete_label = []
        for dic_num in range(len(key_)):
            key = key_[dic_num]
            values = dictionaryTmp.get(key)
            tmp1=[]
            tmp2=[]
            for num in range(values.shape[0]-1):
                if values[num,2]-values[num+1,2] < (-3):
                    tmp1 = values[:num,:]
                    tmp2 = values[num+1:,:]
                    if tmp1.shape[0]>=15:
                        dictionaryTmp.update({tuple(tmp1[0,:]):tmp1})
                    else:
                        delete_label.append(tuple(key))
                    if tmp2.shape[0]>=15:
                        dictionaryTmp.update({tuple(tmp2[0,:]):tmp2})
                    
                    break
        for dic in delete_label:
            try:
                del dictionaryTmp[dic]
            except:
                pass
        
        "將暫時的結果及Pr有改變的output"
        "小 -> 大 -> 小"
        for dic in dictionaryTmp:
            key = dic
            values = dictionaryTmp.get(dic)
            if self.IsRadiusChange(values[:,3]):
                dictionary.update({key:values})
        return dictionary
    
    def FindBallYZ(self, imageHu, pixel2Mm):
        """找2D(XZ平面)圓心, 所以會有不是球的圓心被找到

        Args:
            imageHu (_numpy.array_): _description_
            pixel2Mm (_list_): Pixel to Mm array

        Returns:
            result_centroid (_type_): _description_
        """
        y = 200
        x = 512
        NORMALIZE=4096-1
        "cut image"
        cutImagesHu=[]
        if pixel2Mm[0]<1 and abs(pixel2Mm[2])<=1:
            for z in range(int(imageHu.shape[0]/3),imageHu.shape[0]):
                src_tmp = cv2.resize(imageHu[z,:y,:x],dsize=None,fx=pixel2Mm[0],fy=pixel2Mm[1],interpolation=cv2.INTER_AREA)
                cutImagesHu.append(src_tmp)
        elif pixel2Mm[0]>1 and abs(pixel2Mm[2])>=1:
            for z in range(int(imageHu.shape[0]/3),imageHu.shape[0]):
                src_tmp = cv2.resize(imageHu[z,:y,:x],dsize=None,fx=pixel2Mm[0],fy=pixel2Mm[1],interpolation=cv2.INTER_CUBIC)
                cutImagesHu.append(src_tmp)
        else:
            for z in range(int(imageHu.shape[0]/3),imageHu.shape[0]):
                cutImagesHu.append(imageHu[z,:y,:x])
            
        "filter"
        cutImageHuThr = self.ThresholdFilter(cutImagesHu)
        src_tmp = numpy.uint8(cutImageHuThr)
        resultCentroid_yz = []
        
        "係數"
        "Hough Circles找半徑跟圓心"
        ratio = 3
        low_threshold = 15
        "in mm"
        minRadius = 4
        "in mm"
        maxRadius = 21
        
        "每一張DICOM找圓, 圓心, 半徑"
        for x in range(src_tmp.shape[2]):
            "filter"
            src_tmp[:,:,x] = cv2.bilateralFilter(src_tmp[:,:,x],5,100,100)
            "畫輪廓"
            contours, hierarchy = cv2.findContours(src_tmp[:,:,x],
                                                cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)
            "建立全黑的圖片畫輪廓"
            shape = (src_tmp[:,:,x].shape[0], src_tmp[:,:,x].shape[1], 1)
            black_image = numpy.zeros(shape, numpy.uint8)
            cv2.drawContours(black_image,contours,-1,(256/2, 0, 0),1)
            "用輪廓找質心"
            centroid = []
            for c in contours:
                if c.shape[0] > 4 and c.shape[0]<110:
                    M = cv2.moments(c)
                    if M["m00"] != 0:
                        Cy = (M["m10"]/M["m00"])
                        Cz = (M["m01"]/M["m00"])+int(imageHu.shape[0]/3)
                        centroid.append((Cy,Cz))
            "Hough Circles找半徑跟圓心"
            circles = cv2.HoughCircles(black_image, cv2.HOUGH_GRADIENT,1, 25,
                                        param1=low_threshold*ratio, param2=low_threshold,
                                        minRadius=minRadius, maxRadius=maxRadius)

            if circles is not None and centroid is not None:
                "交集"
                "centroid = 這張圖有幾個質心"
                "circles = 這張圖有幾個hough circle"
                for i in centroid:
                    for j in circles[0, :]:
                        distance = math.sqrt((i[0]-j[0])**2+(i[1]-(j[1]+int(imageHu.shape[0]/3)))**2)
                        if distance <= 2:
                            Py = i[0]
                            Pz = i[1]
                            Px = x
                            Pr = j[2]
                            resultCentroid_yz.append([Px,Py,Pz,Pr])
                        if distance > j[2]-2 and distance < j[2]+2:
                            Py = j[0]
                            Pz = (j[1]+int(imageHu.shape[0]/3))
                            Px = x
                            Pr = j[2]
                            resultCentroid_yz.append([Px,Py,Pz,Pr])
            cv2.destroyAllWindows()
        return resultCentroid_yz

    def SortPointYZ(self, pointMatrix, pixel2Mm):
        """Sort Point Matrix for FindBall() result
           分類/分組所有2D圓心, 以第一點為key, 存成numpy.array

        Args:
            pointMatrix (_list_): _description_

        Returns:
            dictionary(_dictionary_): point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])
        """
        dictionaryTmp = {}
        dictionary = {}
        "pointMatrix 點跟點依序倆倆比較，符合條件的為同一組"
        "條件: "
        "兩點YZ距離不超過3mm"
        "X軸距離不超過20+13mm"
        for num1 in range(len(pointMatrix)-1):
            tmp=[]
            value = []
            for num2 in range(num1+1,len(pointMatrix)):
                P1 = pointMatrix[num1]
                P2 = pointMatrix[num2]
                distance = math.sqrt(numpy.square(P1[1]-P2[1])+numpy.square(P1[2]-P2[2]))
                dx = abs(P1[0]-P2[0])
                if distance < 3 and dx < 20+13:
                    tmp.append(pointMatrix[num2])
            value.append(pointMatrix[num1])
            value.extend(tmp)
            dictionaryTmp.update({tuple(pointMatrix[num1]):numpy.array(value)})

        "刪除重複的組別 & 組別太小的"
        "符合以下條件都刪除: "
        "組別裡元素個數(=X軸距離)大於10mm & key[i]與key[i+1]距離小於50mm"
        "組別裡元素個數(=X軸距離)小於10mm"
        key_ = list(dictionaryTmp.keys())
        delete_label = []
        for num1 in range(len(key_)-1):
            key = key_[num1]
            values = dictionaryTmp.get(key)
            if values.shape[0] >= 10:
                for num2 in range(num1+1,len(key_)):
                    P1 = key_[num1]
                    P2 = key_[num2]
                    distance = math.sqrt(numpy.square(P1[0]-P2[0])+numpy.square(P1[1]-P2[1])+numpy.square(P1[2]-P2[2]))
                    if distance <= 50:
                        delete_label.append(tuple(P2))
            else:
                delete_label.append(tuple(key))
        if values.shape[0] < 15:
            delete_label.append(tuple(key_[-1]))
        for dic1 in delete_label:
            try:
                del dictionaryTmp[dic1]
            except:
                pass
        "同組裡面若有斷層(不連貫), 自動分開"
        "條件: "
        "前-後(不連貫距離)<-3"
        "自動分開以後留下組別裡元素個數大於15mm的"
        key_ = list(dictionaryTmp.keys())
        delete_label = []
        for dic_num in range(len(key_)):
            key = key_[dic_num]
            values = dictionaryTmp.get(key)
            tmp1=[]
            tmp2=[]
            for num in range(values.shape[0]-1):
                if values[num,2]-values[num+1,2] < (-3):
                    tmp1 = values[:num,:]
                    tmp2 = values[num+1:,:]
                    if tmp1.shape[0]>=15:
                        dictionaryTmp.update({tuple(tmp1[0,:]):tmp1})
                    else:
                        delete_label.append(tuple(key))
                    if tmp2.shape[0]>=15:
                        dictionaryTmp.update({tuple(tmp2[0,:]):tmp2})
                    break
        for dic in delete_label:
            try:
                del dictionaryTmp[dic]
            except:
                pass
        
        "將暫時的結果及Pr有改變的output"
        "小 -> 大 -> 小"
        for dic in dictionaryTmp:
            key = dic
            values = dictionaryTmp.get(dic)
            if self.IsRadiusChange(values[:,3]):
                dictionary.update({key:values})
        return dictionary
    
    def IsRadiusChange(self, matrix):
        """檢查分類/分組完的圓心中, Pr 有沒有改變

        Args:
            matrix (_numpy.array_): 半徑(Pr)

        Returns:
            _bool_: if Radius is Change = True
        """

        max = numpy.max(matrix)
        min = numpy.min(matrix)
        "去除差異小於2mm的"
        if max-min < 2:
            return False
        "去除差異 -2 < tmp <= 0"
        tmp1 = matrix[0] - matrix[int(len(matrix)/2)]
        if tmp1 <= 0 and tmp1 > -2:
            return False
        tmp2 = matrix[-1] - matrix[int(len(matrix)/2)]
        if tmp2 <= 0 and tmp2 > -2:
            return False
        
        unique, counts = numpy.unique(matrix, return_counts=True)
        if numpy.max(counts) >= 9:
            return False
        
        "組別裡元素個數大於15mm且小於25mm"
        if len(matrix)<=25:
            same = 0
            small2big = 0
            for i in range(len(matrix)-1):
                if matrix[i] < matrix[i+1] or matrix[i] < matrix[int(len(matrix)/2)]:
                    "代表由小變到大"
                    small2big+=1
                if matrix[i]>matrix[i+1] and matrix[i] == max:
                    num = i
                    "代表由小變到大"
                    break
                if matrix[i] == matrix[i+1]:
                    same+=1
                    if same == len(matrix)-1:
                        "代表全部一樣"
                        return False
                if i+1 == len(matrix)-1:
                    "迴圈到底了，代表持續變大"
                    return False
            if num!= len(matrix)-1 and small2big != 0:
                change = num
                for i in range(num,len(matrix)):
                    if matrix[i] >= min:
                        change+=1
                        if change == len(matrix):
                            "小->大->小，圓形"
                            return True
            if same > (len(matrix)/2):
                "橢圓形"
                return False
        return False

    def AveragePoint(self, dictionaryPoint, axis=[False, False, False]):
        """得出最後的四球影像坐標 (平均)

        Args:
            dictionaryPoint (_dictionary_): point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])

        Returns:
            point (_numpy.array_): point, (Px,Py,Pz)
        """
        point = []
        if axis == [False,False,False]:
            print("AveragePoint error")
            return
        elif axis == [True,True,True]:
            print("AveragePoint error")
            return
        elif axis==[False,True,True]:
            for key in dictionaryPoint:
                value = dictionaryPoint.get(key)
                array = []
                Px = value[int(value.shape[0]/2),0]
                for tmp in value:
                    tmp_str1 = str(tmp[1])
                    tmp_str2 = str(tmp[2])
                    "去除.5及整數，留下看起來是質心候選的"
                    if int(tmp[1]) != tmp[1] and len(tmp_str1)-(tmp_str1.find(".")+1) == 1 and tmp_str1[tmp_str1.find(".")+1] == "5":
                        if int(tmp[2]) != tmp[2] and len(tmp_str2)-(tmp_str2.find(".")+1) == 1 and tmp_str2[tmp_str2.find(".")+1] == "5":
                            pass
                        else:
                            array.append([Px,tmp[1],tmp[2]])
                    elif int(tmp[2]) != tmp[2] and len(tmp_str2)-(tmp_str2.find(".")+1) == 1 and tmp_str2[tmp_str2.find(".")+1] == "5":
                        if int(tmp[1]) != tmp[1] and len(tmp_str1)-(tmp_str1.find(".")+1) == 1 and tmp_str1[tmp_str1.find(".")+1] == "5":
                            pass
                        else:
                            array.append([Px,tmp[1],tmp[2]])
                    else:
                        array.append([Px,tmp[1],tmp[2]])
                point.append(numpy.mean(array,0))
        elif axis==[True,True,False]:
            for key in dictionaryPoint:
                value = dictionaryPoint.get(key)
                array = []
                Pz = value[int(value.shape[0]/2),2]
                for tmp in value:
                    tmp_str0 = str(tmp[0])
                    tmp_str1 = str(tmp[1])
                    "去除.5及整數，留下看起來是質心候選的"
                    if int(tmp[0]) != tmp[0] and len(tmp_str0)-(tmp_str0.find(".")+1) == 1 and tmp_str0[tmp_str0.find(".")+1] == "5":
                        if int(tmp[1]) != tmp[1] and len(tmp_str1)-(tmp_str1.find(".")+1) == 1 and tmp_str1[tmp_str1.find(".")+1] == "5":
                            pass
                        else:
                            array.append([tmp[0],tmp[1],Pz])
                    elif int(tmp[1]) != tmp[1] and len(tmp_str1)-(tmp_str1.find(".")+1) == 1 and tmp_str1[tmp_str1.find(".")+1] == "5":
                        if int(tmp[0]) != tmp[0] and len(tmp_str0)-(tmp_str0.find(".")+1) == 1 and tmp_str1[tmp_str0.find(".")+1] == "5":
                            pass
                        else:
                            array.append([tmp[0],tmp[1],Pz])
                    else:
                        array.append([tmp[0],tmp[1],Pz])
                point.append(numpy.mean(array,0))
        return point

    def GetBall(self, imageHu, pixel2Mm):
        """目前目標先找到圓心
           找到圓心之後要換成轉換矩陣, 再之後得出robot座標下的目標點

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)
            pixel2Mm (_list_): Pixel to mm array

        Returns:
            dictionaryPoint (_dictionary_): point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])
        """
        resultCentroid_xy = self.FindBallXY(imageHu, pixel2Mm)
        dictionaryPoint_xy = self.SortPointXY(resultCentroid_xy, pixel2Mm)
        
        resultCentroid_yz = self.FindBallYZ(imageHu, pixel2Mm)
        dictionaryPoint_yz = self.SortPointYZ(resultCentroid_yz, pixel2Mm)
        
        point_xy = self.AveragePoint(dictionaryPoint_xy,axis = [True, True, False])
        point_yz = self.AveragePoint(dictionaryPoint_yz,axis = [False, True, True])
        
        point = []
        if len(point_xy)==len(point_yz):
            for P1 in point_xy:
                for P2 in point_yz:
                    distance = math.sqrt((P1[0]-P2[0])**2+(P1[1]-P2[1])**2+(P1[2]-P2[2])**2)
                    if distance <= 5:
                        point.append([P1[0],P1[1],P2[2]])
        else:
            print("get point error")
        return numpy.array(point)
    
    def GetPlanningPath(self, originPoint_H, selectedPoint_H, regMatrix_H,
                        originPoint_L, selectedPoint_L, regMatrix_L):
        PlanningPath = []
        
        for p in selectedPoint_H:
            PlanningPath.append(numpy.dot(regMatrix_H,(p-originPoint_H)))
        for p in selectedPoint_L:
            PlanningPath.append(numpy.dot(regMatrix_L,(p-originPoint_L)))
        
        self.PlanningPath = PlanningPath
        
        return PlanningPath
        
            
    
"使用範例"
if __name__ == "__main__":
    path_dicom_only = "C:\\Users\\tinac\\OneDrive\\Tina on OneDrive\\brain navi\\LCGS\\CT\\20220615\\S43320\\S2010\\"
    path_dicom = "C:\\Users\\tinac\\OneDrive\\Tina on OneDrive\\brain navi\\LCGS\\CT\\20220615\\S43320\\"
    g_dicom = DICOM()
    g_metadata, g_metadataSeriesNum = g_dicom.LoadPath(path_dicom_only)
    g_seriesNumberLabel, g_dicDICOM = g_dicom.SeriesSort(g_metadata, g_metadataSeriesNum)
    g_imageTag = g_dicom.ReadDicom(g_seriesNumberLabel, g_dicDICOM)
    g_rescaleSlope = g_imageTag[0].RescaleSlope
    g_rescaleIntercept = g_imageTag[0].RescaleIntercept
    g_image = g_dicom.GetImage(g_imageTag)
    g_imageHu = g_dicom.Transfer2Hu(g_image, g_rescaleSlope, g_rescaleIntercept)
    g_pixel2Mm = g_dicom.GetPixel2Mm(g_imageTag[0])
    sliceNum = 100-1
    wl = g_imageTag[0].WindowCenter[0]
    ww = g_imageTag[0].WindowWidth[0]
    g_image = numpy.array(g_image)
    g_imageHu2D_ = g_dicom.GetGrayImg(g_image[sliceNum-1,:,:], ww, wl)
    plt.figure()
    plt.imshow(g_imageHu2D_, cmap='gray')
    plt.title("slice number: " + str(sliceNum))
    plt.show()