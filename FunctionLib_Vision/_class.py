from multiprocessing.sharedctypes import Value
import pydicom
import matplotlib.pyplot as plt
import numpy
import os
from keras.models import load_model
import cv2
import math
from PyQt5.QtGui import *

"DICOM function"
class DICOM():
    def __init__(self):
        pass
        
    def LoadPath(self, folderPath):
        """identify whether DICOM or not
           identify whether one UID or not

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
        """classify SeriesNumber and metadata in {SeriesNumber : metadata + pixel_array}
           key is SeriesNumber,
           value is metadata + pixel_array
           
           auto recognize DICOM or floder

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
           and then get metadata + pixel_array(image 3D)

        Args:
            seriesNumberLabel (_numpy array_): group of SeriesNumber Label
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
        "sort InstanceNumber"
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
        """_summary_

        Args:
            image (_numpy.array_): DICOM image (voxel array in 3 by 3)
            pixel2Mm (_numpy.array_): Pixel to mm array

        Returns:
            cutImagesHu (_list_): DICOM image in HU value (voxel array in 3 by 3)
        """
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
        """Get Pixel to mm array

        Args:
            imageTag (_list_): DICOM list sort by InstanceNumber (include metadata and pixel_array)

        Returns:
            pixel2Mm (_list_): Pixel to mm array
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
        
"registration function"
class REGISTRATION():
    def __init__(self):
        self.PlanningPath = []
        return
        
    
    def TransformationMatrix(self, ballCenterMm):
        """calculate registration transformation matrix

        Args:
            ballCenterMm (_numpy.array_): ball center in mm (candidates matched)

        Returns:
            TransformationMatrix(_numpy.array_): numpy.dot(R_y,R_z) Transformation Matrix
        """
        "ball_center_mm(1,:);   origin"
        "ball_center_mm(2,:);   x axis"
        "ball_center_mm(3,:);   y axis"  
        ball_vector_x = ballCenterMm[1] - ballCenterMm[0]
        ball_vector_y = ballCenterMm[2] - ballCenterMm[0]
        "create new coordinate"
        vectorZ = numpy.array(numpy.cross(ball_vector_x, ball_vector_y))
        vectorX = numpy.array(ball_vector_x)
        vectorY = numpy.array(numpy.cross(vectorZ,vectorX))
        
        new_vector = numpy.array([vectorX,vectorY,vectorZ])
        "calculate unit vector"
        unit_new_vector = []
        for vector in new_vector:
            unit_new_vector.append(vector / self.GetNorm(vector))
        unit_new_vector = numpy.array(unit_new_vector)
        "calculate radian"
        angle_radian = []
        unit = numpy.eye(3, dtype = 'int')
        for n in range(unit.shape[0]):
            top = numpy.dot(unit_new_vector[n],unit[n])
            down = self.GetNorm(unit_new_vector[n])*self.GetNorm(unit[n])
            angle_radian.append(math.acos(top / down))
        angle_radian = numpy.array(angle_radian)
        "calculate rotation matrix"
        R_z = numpy.array([[math.cos(-angle_radian[1]), -math.sin(-angle_radian[1]), 0],
               [math.sin(-angle_radian[1]), math.cos(-angle_radian[1]), 0],
               [0, 0, 1]])
        
        "calculate new unit vector"
        new_vector = unit_new_vector
        unit_new_vector = []
        for vector in new_vector:
            unit_new_vector.append(numpy.dot(R_z,vector))
        "calculate radian"
        angle_radian = []
        unit = numpy.eye(3, dtype = 'int')
        for n in range(unit.shape[0]):
            top = numpy.dot(unit_new_vector[n],unit[n])
            down = self.GetNorm(unit_new_vector[n])*self.GetNorm(unit[n])
            angle_radian.append(math.acos(top / down))
        angle_radian = numpy.array(angle_radian)
        "calculate rotation matrix"
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
                "display Axis and Slice"
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
        """Threshold is [down_, up_] = [-800, 300]
           image value turn to PIXEL_MAX and 0 whitch is binarization image

        Args:
            imageHu (_list_): image in Hounsfield Unit (Hu)

        Returns:
            imagesHuThr (_list_): _description_
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
        """scan XY plane to  find ball centroid,
           May find candidate ball and non-candidates

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)
            pixel2Mm (_list_): Pixel to mm array

        Returns:
            result_centroid (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball
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
            
        "filter and binarization"
        cutImageHuThr = self.ThresholdFilter(cutImagesHu)
        src_tmp = numpy.uint8(cutImageHuThr)
        resultCentroid_xy = []
        
        "use Hough Circles find radius and circle center"
        "coefficient"
        ratio = 3
        low_threshold = 15
        "Radius range: [4.5mm ~ (21/2)+3mm]"
        minRadius=int((4.5/pixel2Mm[0]))
        maxRadius=int((21/pixel2Mm[0])/2)+3
        
        
        "find circle, radius and center of circle in each DICOM image"
        for z in range(src_tmp.shape[0]):
            "filter"
            src_tmp[z,:,:] = cv2.bilateralFilter(src_tmp[z,:,:],5,100,100)
            "draw contours"
            contours, hierarchy = cv2.findContours(src_tmp[z,:,:],
                                                cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)
            "create an all black picture to draw contour"
            shape = (src_tmp.shape[1], src_tmp.shape[2], 1)
            black_image = numpy.zeros(shape, numpy.uint8)
            cv2.drawContours(black_image,contours,-1,(256/2, 0, 0),1)
            "use contour to find centroid"
            centroid = []
            for c in contours:
                if c.shape[0] > 4 and c.shape[0]<110:
                    M = cv2.moments(c)
                    if M["m00"] != 0:
                        Cx = (M["m10"]/M["m00"])
                        Cy = (M["m01"]/M["m00"])
                        centroid.append((Cx,Cy))
            "use Hough Circles to find radius and center of circle"
            circles = cv2.HoughCircles(black_image, cv2.HOUGH_GRADIENT, 1, 75,
                                        param1=low_threshold*ratio, param2=low_threshold,
                                        minRadius=minRadius, maxRadius=maxRadius)
            if circles is not None and centroid is not None:
                "Intersection"
                "centroid = group of Centroid"
                "circles = group of hough circle"
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
  
    def ClassifyPointXY(self, pointMatrix, pixel2Mm):
        """classify Point Matrix from FindBall() result
           take the first point of each group as the key
           save as numpy.array
           = {point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])}

        Args:
            pointMatrix (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball

        Returns:
            dictionary(_dictionary_): point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])
        """
        dictionaryTmp = {}
        dictionary = {}
        "pointMatrix, "
        "Compare the point with the point in order, "
        "meet the conditions are the same group"
        "conditions: "
        "The XY distance between two points does not exceed 2mm (<= 2 mm)"
        "Z-axis distance does not exceed 20+13mm (< 20+13 mm)"
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
        
        "remove groups which points are repeated"
        "remove small groups which member is less then 15 (< 15)"
        "remove groups that meet the following conditions:"
        "* The number/count/quantity/amount in the group is more than 15mm(> 15 mm), same as Z-axis distance is more than 15mm "
        " & the distance between key[i] and key[i+1] is less than 50mm"
        "* The number/count/quantity/amount in the group is less than 15mm(< 15 mm), same as Z-axis distance is less than 15mm"
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
        "If there is not consecutive numbers in the same group, it will be separated automatically"
        "conditions: "
        "the difference between the [n] number and the [n+1] number (points distance) < -3 mm"
        "After automatic separation, leave the group which is greater than 15 mm"
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
        
        "output 2 result, the radius which has changed (Pr) and temporary results"
        "circle shape trend: small -> big -> small"
        for dic in dictionaryTmp:
            key = dic
            values = dictionaryTmp.get(dic)
            if self.IsRadiusChange(values[:,3]):
                dictionary.update({key:values})
        return dictionary
    
    def FindBallYZ(self, imageHu, pixel2Mm):
        """scan YZ plane to  find ball centroid,
           May find candidate ball and non-candidates

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)
            pixel2Mm (_list_): Pixel to mm array

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
            
        "filter and binarization"
        cutImageHuThr = self.ThresholdFilter(cutImagesHu)
        src_tmp = numpy.uint8(cutImageHuThr)
        resultCentroid_yz = []
        
        "use Hough Circles find radius and circle center"
        "coefficient"
        ratio = 3
        low_threshold = 15
        "in mm"
        minRadius = 4
        "in mm"
        maxRadius = 21
        
        "find circle, radius and center of circle in each DICOM image"
        for x in range(src_tmp.shape[2]):
            "filter"
            src_tmp[:,:,x] = cv2.bilateralFilter(src_tmp[:,:,x],5,100,100)
            "get contour"
            contours, hierarchy = cv2.findContours(src_tmp[:,:,x],
                                                cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)
            "create an all black picture to draw contour"
            shape = (src_tmp[:,:,x].shape[0], src_tmp[:,:,x].shape[1], 1)
            black_image = numpy.zeros(shape, numpy.uint8)
            cv2.drawContours(black_image,contours,-1,(256/2, 0, 0),1)
            "use contour to find centroid"
            centroid = []
            for c in contours:
                if c.shape[0] > 4 and c.shape[0]<110:
                    M = cv2.moments(c)
                    if M["m00"] != 0:
                        Cy = (M["m10"]/M["m00"])
                        Cz = (M["m01"]/M["m00"])+int(imageHu.shape[0]/3)
                        centroid.append((Cy,Cz))
            "use Hough Circles to find radius and center of circle"
            circles = cv2.HoughCircles(black_image, cv2.HOUGH_GRADIENT,1, 25,
                                        param1=low_threshold*ratio, param2=low_threshold,
                                        minRadius=minRadius, maxRadius=maxRadius)

            if circles is not None and centroid is not None:
                "Intersection"
                "centroid = group of Centroid"
                "circles = group of hough circle"
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

    def ClassifyPointYZ(self, pointMatrix, pixel2Mm):
        """classify Point Matrix from FindBall() result
           take the first point of each group as the key
           save as numpy.array
           = {point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])}

        Args:
            pointMatrix (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball

        Returns:
            dictionary(_dictionary_): {point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])}
        """
        dictionaryTmp = {}
        dictionary = {}
        "pointMatrix, "
        "Compare the point with the point in order, "
        "meet the conditions are the same group"
        "conditions: "
        "The YZ distance between two points does not exceed 3mm (< 3 mm)"
        "X-axis distance does not exceed 20+13mm (< 20+13 mm)"
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

        "remove groups which points are repeated"
        "remove small groups which member is less then 15 (< 15)"
        "remove groups that meet the following conditions:"
        "* The number/count/quantity/amount in the group is more than 10mm(> 10 mm), same as Z-axis distance is more than 10mm "
        " & the distance between key[i] and key[i+1] is less than 50mm"
        "* The number/count/quantity/amount in the group is less than 10mm(< 10 mm), same as Z-axis distance is less than 10mm"
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
        "If there is not consecutive numbers in the same group, it will be separated automatically"
        "conditions: "
        "the difference between the [n] number and the [n+1] number (points distance) < -3 mm"
        "After automatic separation, leave the group which is greater than 15 mm"
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
        
        "output 2 result, the radius which has changed (Pr) and temporary results"
        "circle shape change: small -> big -> small"
        for dic in dictionaryTmp:
            key = dic
            values = dictionaryTmp.get(dic)
            if self.IsRadiusChange(values[:,3]):
                dictionary.update({key:values})
        return dictionary
    
    def IsRadiusChange(self, matrix):
        """check the radius is changed (Pr) or not from classify group

        Args:
            matrix (_numpy.array_): the radius of hough circle (Pr)

        Returns:
            _bool_: if Radius is Change = True
        """

        max = numpy.max(matrix)
        min = numpy.min(matrix)
        "remove difference less than 2 mm (< 2 mm)"
        if max-min < 2:
            return False
        "remove difference, -2 < tmp <= 0"
        tmp1 = matrix[0] - matrix[int(len(matrix)/2)]
        if tmp1 <= 0 and tmp1 > -2:
            return False
        tmp2 = matrix[-1] - matrix[int(len(matrix)/2)]
        if tmp2 <= 0 and tmp2 > -2:
            return False
        
        unique, counts = numpy.unique(matrix, return_counts=True)
        if numpy.max(counts) >= 9:
            return False
        
        "leave guoup is greater than (>=) 15 mm and less than (<=) 25 mm"
        if len(matrix)<=25:
            same = 0
            small2big = 0
            for i in range(len(matrix)-1):
                if matrix[i] < matrix[i+1] or matrix[i] < matrix[int(len(matrix)/2)]:
                    "shape change small -> big"
                    small2big+=1
                if matrix[i]>matrix[i+1] and matrix[i] == max:
                    "shape change big -> small"
                    num = i
                    break
                if matrix[i] == matrix[i+1]:
                    same+=1
                    if same == len(matrix)-1:
                        "shape change same, no change"
                        return False
                if i+1 == len(matrix)-1:
                    "when for loop reaches the end, it means that radius (Pr) continues to grow (small to big until the end)"
                    return False
            if num!= len(matrix)-1 and small2big != 0:
                change = num
                for i in range(num,len(matrix)):
                    if matrix[i] >= min:
                        change+=1
                        if change == len(matrix):
                            "shape change: small -> big -> small, means it is ball"
                            return True
            if same > (len(matrix)/2):
                "it's oval/egg"
                return False
        return False

    def AveragePoint(self, dictionaryPoint, axis=[False, False, False]):
        """average ball center of registration result (Px, Py, Pz)

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
                    "remove .5 and integer, get candidate (with centroid)"
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
                    "remove .5 and integer, get candidate (with centroid)"
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
        """get ball center

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)
            pixel2Mm (_list_): Pixel to mm array

        Returns:
            dictionaryPoint (_dictionary_): point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])
        """
        resultCentroid_xy = self.FindBallXY(imageHu, pixel2Mm)
        dictionaryPoint_xy = self.ClassifyPointXY(resultCentroid_xy, pixel2Mm)
        
        resultCentroid_yz = self.FindBallYZ(imageHu, pixel2Mm)
        dictionaryPoint_yz = self.ClassifyPointYZ(resultCentroid_yz, pixel2Mm)
        
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
        
            
    
"example"
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