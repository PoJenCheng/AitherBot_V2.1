from multiprocessing.sharedctypes import Value
import pydicom
import matplotlib.pyplot as plt
import numpy
import os
from keras.models import load_model
import cv2
import math
import itertools
from PyQt5.QtGui import *
from ._subFunction import *
import copy

from vtkmodules.vtkImagingCore import vtkImageReslice
import vtk.numpy_interface.dataset_adapter as dsa

from vtkmodules.vtkIOImage import vtkDICOMImageReader
from vtkmodules.vtkImagingCore import vtkImageMapToColors
from vtkmodules.vtkFiltersSources import vtkSphereSource
from vtkmodules.vtkFiltersCore import vtkTubeFilter
from vtkmodules.vtkFiltersSources import vtkLineSource
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtk.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkRenderingCore import (
    vtkCamera,
    vtkImageActor,
    vtkActor,
    vtkPolyDataMapper,
    vtkRenderer,
    vtkWindowLevelLookupTable
)

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
        ## 讀取資料夾, 讀取 dicom 檔案 ############################################################################################
        filePathList = []
        dir = []
        metadata = []
        metadataSeriesNum = []
        metadataStudy = []
        metadataFileList = []
        for dirPath, dirNames, fileNames in os.walk(folderPath):
            dir.append(dirPath)
            for f in fileNames:
                tmpDir = os.path.join(dirPath, f)
                filePathList.append(tmpDir)
        n=0
        for s in filePathList:
            try:
                metadata.append(pydicom.read_file(s))
                metadataSeriesNum.append(metadata[n].SeriesInstanceUID)
                metadataStudy.append(metadata[n].StudyInstanceUID)
                metadataFileList.append(s)
                n+=1
            except:
                continue
        seriesNumber = numpy.unique(metadataStudy)
        if seriesNumber.shape[0]>1 or len(metadataStudy)==0:
            metadata = 0
            metadataSeriesNum = 0
                
        return metadata, metadataSeriesNum, metadataFileList
        ############################################################################################
        
    def SeriesSort(self, metadata, metadataSeriesNum, metadataFileList):
        """classify SeriesNumber and metadata in metadata({SeriesNumber : metadata + pixel_array})
            key is SeriesNumber,
            value is metadata + pixel_array
            
            auto recognize DICOM or floder

        Args:
            metadata (_list_): metadata for each slice ({SeriesNumber : metadata + pixel_array})
            metadataSeriesNum (_list_): Series Number for each slice
            metadataFileList (_list_): dir + File name for each slice
            
        Returns:
            seriesNumberLabel (_numpy.array_): 有幾組的SeriesNumber的Label
            dicDICOM (_dictionary_): {SeriesNumber : metadata + pixel_array}
            dirDICOM (_dictionary_): {SeriesNumber : dir + File name}
        """
        ##分類 DICOM series, 取得 DICOM 影像路徑 ##########################################################################################
        seriesNumberLabel = numpy.unique(metadataSeriesNum)
        matrix=[]
        matrixFile = []
        dicDICOM = {}
        dirDICOM = {}
        for n in seriesNumberLabel:
            for i in range(len(metadata)):
                if metadata[i].SeriesInstanceUID == n:
                    matrix.append(metadata[i])
                    matrixFile.append(metadataFileList[i])
            dicDICOM.update({n:matrix})
            dirDICOM.update({n:matrixFile})
            matrix=[]
            matrixFile = []
        return seriesNumberLabel, dicDICOM, dirDICOM
        ############################################################################################
    
    def ReadDicom(self, seriesNumberLabel, dicDICOM, dirDICOM):
        """read DICOM
            and then get metadata + pixel_array(image 3D)

        Args:
            seriesNumberLabel (_numpy array_): group of SeriesNumber Label
            dicDICOM (_dictionary_): {SeriesNumber : metadata + pixel_array}
            dirDICOM (_dictionary_): {SeriesNumber : dir + File name}
        Returns:
            imageTag (_list_): DICOM list sort by InstanceNumber (include metadata and pixel_array)
            folderDir (_string_): dir + folder name
        """
        ## 自動偵測影像是哪個 series number, 產生影像路徑 ############################################################################################
        seriesN=[]
        for s in seriesNumberLabel:
            seriesN.append(len(dicDICOM.get(s)))
        tmpSeries = max(seriesN)
        index = seriesN.index(tmpSeries)
        
        imageInfo = dicDICOM.get(seriesNumberLabel[index])
        imageDir = dirDICOM.get(seriesNumberLabel[index])
        
        tmpDir = imageDir[0].rfind('\\')
        if tmpDir == -1:
            tmpDir_ = imageDir[0].rfind('/')
            folderDir = imageDir[0][0:tmpDir_]
        else:
            folderDir = imageDir[0][0:tmpDir]
        ############################################################################################
        ## 依照 instance number 排列影像 ############################################################################################
        "sort InstanceNumber"
        imageTag = [0]*tmpSeries
        for i in range(len(imageInfo)):
            tmpSeries = imageInfo[i]
            imageTag[tmpSeries.InstanceNumber-1] = tmpSeries
        ############################################################################################
        return imageTag, folderDir
    
    def GetImage(self, imageTag):
        """get image from image DICOM

        Args:
            imageTag (_list_): DICOM list sort by InstanceNumber (include metadata and pixel_array)

        Returns:
            image (_list_): image (only pixel array)
        """
        ## 取得影像陣列 ############################################################################################
        image = []
        try:
            for sliceNum in range(len(imageTag)-1):
                if imageTag[sliceNum].pixel_array.shape==imageTag[sliceNum+1].pixel_array.shape:
                    image.append(imageTag[sliceNum].pixel_array)
                else:
                    image = 0
                    break
            image.append(imageTag[sliceNum+1].pixel_array)
        except:
            image = 0
        ############################################################################################
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
        ## 轉換影像, 從原始值到hu值 ############################################################################################
        imageHu = []
        for sliceNum in range(len(image)):
            ### 公式2
            imageHu.append(image[sliceNum] * rescaleSlope + rescaleIntercept)
        ############################################################################################
        return imageHu

    def ImgTransfer2Mm(self, image, pixel2Mm):
        """transfer voxel to HU value in mm unit

        Args:
            image (_numpy.array_): DICOM image (voxel array in 3 by 3)
            pixel2Mm (_numpy.array_): Pixel to mm array

        Returns:
            cutImagesHu (_list_): DICOM image in HU value (voxel array in 3 by 3)
        """
        ## 轉換影像, 讓每個 pixel 間距變成 1mm ############################################################################################
        cutImagesHu=[]
        for z in range(image.shape[0]):
            "resize to mm"
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
        ############################################################################################
        return cutImagesHu
    
    def GetPixel2Mm(self, imageTag):
        """Get Pixel to mm array

        Args:
            imageTag (_list_): DICOM list sort by InstanceNumber (include metadata and pixel_array)

        Returns:
            pixel2Mm (_list_): Pixel to mm array
        """
        ## 取得三軸方向 pixel 轉換成 mm 的比例陣列 ############################################################################################
        pixel2Mm = []
        pixel2Mm.append(imageTag.PixelSpacing[0])
        pixel2Mm.append(imageTag.PixelSpacing[1])
        # pixel2Mm.append(imageTag.SpacingBetweenSlices)
        pixel2Mm.append(abs(imageTag.SpacingBetweenSlices))
        ############################################################################################
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
        ## 依照使用者設定的 Window Width 跟 Window Center / level 轉換影像灰值, 用於顯示 ############################################################################################
        imageHu2D_ = numpy.ones((imageHu2D.shape[0],imageHu2D.shape[1]))
        
        for i in range(imageHu2D.shape[0]):
            for j in range(imageHu2D.shape[1]):
                ### 公式3
                imageHu2D_[i,j] = (255/ww)*imageHu2D[i,j]+128-((255*wl)/ww)
                if imageHu2D_[i,j] >= 255:
                        imageHu2D_[i,j] = 255
                elif imageHu2D_[i,j] <= 0:
                        imageHu2D_[i,j] = 0
        ############################################################################################
        return imageHu2D_

    def ReadyQimg(self, imageHu2D):
        """ready image to show on label

        Args:
            imageHu2D (_numpy.array_): 2D image

        Returns:
            qimg (_QImage_): image, to show on label
        """
        ## 顯示 dicom 到 ui, 用 Qlabel ############################################################################################
        ### 公式4
        imgHeight, imgWidth = imageHu2D.shape
        gray = numpy.uint8(imageHu2D)
        gray3Channel = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        bytesPerline = 3 * imgWidth
        qimg = QImage(gray3Channel, imgWidth, imgHeight, bytesPerline, QImage.Format_RGB888).rgbSwapped()
        ############################################################################################
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
        ## 計算球的向量 ############################################################################################
        ball_vector_x = ballCenterMm[1] - ballCenterMm[0]
        ball_vector_y = ballCenterMm[2] - ballCenterMm[0]
        ############################################################################################
        "create new coordinate"
        ## 定義 xyz 軸向量 ############################################################################################
        vectorZ = numpy.array(numpy.cross(ball_vector_x, ball_vector_y))
        vectorX = numpy.array(ball_vector_x)
        vectorY = numpy.array(numpy.cross(vectorZ,vectorX))
        new_vector = numpy.array([vectorX,vectorY,vectorZ])
        ############################################################################################
        ### 公式5
        "calculate unit vector"
        ## 計算 xyz 軸的單位向量, 得出選轉矩陣 ############################################################################################
        unit_new_vector = []
        for vector in new_vector:
            unit_new_vector.append(vector / self.__GetNorm(vector))
        ############################################################################################

        return numpy.array(unit_new_vector)
    
    def GetBallSection(self,candidateBall):
        """calculate Transformation Matrix

        Args:
            candidateBall (_dictionary_): candidate ball center 
            same as dictionaryPoint (_dictionary_): point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])

        Returns:
            numpy.array([showAxis, showSlice]) (_numpy.array_): show Axis(x=0, y=1, z=2), show Slice/section (slice number)
        
        """
        ## 自動顯示要給使用者選取球的切面 ############################################################################################
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
        ############################################################################################
        return numpy.array([showAxis, showSlice])
    
    def GetError(self,ball):
        """get rigistration error/difference

        Args:
            ball (_numpy.array_): registration ball center

        Returns:
            [numpy.min(error),numpy.max(error),numpy.mean(error)] (_list_): [min error, max error, mean error]
        """
        ## 計算球心距離與設計值距離的誤差 ############################################################################################
        error = []
        shortSide = 30
        longSide = 65
        hypotenuse = math.sqrt(numpy.square(shortSide) + numpy.square(longSide))
        error.append(abs(self.__GetNorm(ball[1]-ball[2])-hypotenuse))
        error.append(abs(self.__GetNorm(ball[0]-ball[1])-shortSide))
        error.append(abs(self.__GetNorm(ball[0]-ball[2])-longSide))
        ############################################################################################
        return [numpy.min(error),numpy.max(error),numpy.mean(error)]
    
    def __GetNorm(self, V):
        """get norm

        Args:
            V (_numpy.array_): vector

        Returns:
            d (_number_): (float)
        """
        ## 計算 norm 值, 自動辨識3維向量或是2維向量 ############################################################################################
        if V.shape[0] == 3:
            d = math.sqrt(numpy.square(V[0])+numpy.square(V[1])+numpy.square(V[2]))
        elif V.shape[0] == 2:
            d = math.sqrt(numpy.square(V[0])+numpy.square(V[1]))
        else:
            print("GetNorm() error")
            return 0
        ############################################################################################
        return d
        
    def ThresholdFilter(self, imageHu):
        """Threshold is [down_, up_] = [-800, 300]
           image value turn to PIXEL_MAX and 0 whitch is binarization image

        Args:
            imageHu (_list_ or _numpy.array_): image in Hounsfield Unit (Hu)

        Returns:
            imagesHuThr (_list_): _description_
        """
        ## 影像濾波 + 自動辨識 input 是 list 或 numpy.array ############################################################################################
        ### 公式6
        imagesHuThr = []
        PIXEL_MAX = 4096-1
        down_ = -800
        up_ = 300
        "numpy.array type"
        try:
            for z in range(imageHu.shape[0]):
                ret, th4 = cv2.threshold(imageHu[z,:,:], up_, PIXEL_MAX, cv2.THRESH_TOZERO_INV)
                ret, th5 = cv2.threshold(th4, down_, PIXEL_MAX, cv2.THRESH_BINARY)
                imagesHuThr.append(th5)
            return imagesHuThr
        except:
            pass
        "list type"
        try:
            for z in range(len(imageHu)):
                ret, th4 = cv2.threshold(imageHu[z], up_, PIXEL_MAX, cv2.THRESH_TOZERO_INV)
                ret, th5 = cv2.threshold(th4, down_, PIXEL_MAX, cv2.THRESH_BINARY)
                imagesHuThr.append(th5)
            return imagesHuThr
        except:
            pass
        print("ThresholdFilter() error")
        ############################################################################################
        return
    ### 公式7
    def __FindBallXY(self, imageHu):
        """scan XY plane to  find ball centroid,
            May find candidate ball and non-candidates

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)

        Returns:
            result_centroid (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball
        """

        imageHuThr = self.ThresholdFilter(imageHu)
        src_tmp = numpy.uint8(imageHuThr)
        
        resultCentroid_xy = []
        
        "coefficient"
        ratio = 3
        low_threshold = 15
        "Radius range: [3mm ~ (21/2)+3mm]"
        minRadius=int(3)
        maxRadius=int(21/2)+3
        
        "find circle, radius and center of circle in each DICOM image"
        for z in range(src_tmp.shape[0]):
            ## 找輪廓與質心 ############################################################################################
            ### 公式8
            "draw contours"
            contours, hierarchy = cv2.findContours(src_tmp[z,:,:],
                                                cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)
            "create an all black picture to draw contour"
            shape = (src_tmp.shape[1], src_tmp.shape[2], 1)
            black_image_2 = numpy.zeros(shape, numpy.uint8)
            "use contour to find centroid"
            centroid = []
            tmpContours = []
            for c in contours:
                if c.shape[0] > 5:
                    M = cv2.moments(c)
                    if M["m00"] != 0:
                        Cx = (M["m10"]/M["m00"])
                        Cy = (M["m01"]/M["m00"])
                        centroid.append((Cx,Cy))
                        tmpContours.append(c)
            cv2.drawContours(black_image_2,tmpContours,-1,(256/2, 0, 0),1)
            ############################################################################################
            ## 用Hough Circles找球心跟半徑 ############################################################################################
            "use Hough Circles to find radius and center of circle"
            circles = cv2.HoughCircles(black_image_2, cv2.HOUGH_GRADIENT, 1, 10,
                                        param1=low_threshold*ratio, param2=low_threshold,
                                        minRadius=minRadius, maxRadius=maxRadius)
            ############################################################################################
            ## 質心與球心平面距離不超過2的留下當作候選人 ############################################################################################
            if circles is not None and centroid is not None:
                "Intersection"
                "centroid = group of Centroid"
                "circles = group of hough circle"
                for i in centroid:
                    for j in circles[0, :]:
                        distance = math.sqrt((i[0]-j[0])**2+(i[1]-j[1])**2)
                        if distance < 2:
                            Px = i[0]
                            Py = i[1]
                            Pz = z
                            Pr = j[2]
                            resultCentroid_xy.append([Px,Py,Pz,Pr])
            
            cv2.destroyAllWindows()
            ############################################################################################
        return resultCentroid_xy
  
    def __ClassifyPointXY(self, pointMatrix):
        """classify Point Matrix from FindBall..() result
           take the first point of each group as the key
           save as numpy.array
           = {point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])}

        Args:
            pointMatrix (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball

        Returns:
            dictionary(_dictionary_): point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])
        """
        dictionaryTmp = {}
        keyMatrix = []
        tmp = []
        
        "sorted and get key"
        ## 排序候選人(pointMatrix), 找出邊界, 視為key ############################################################################################
        pointMatrixSorted = numpy.array(sorted(pointMatrix, key=lambda tmp: (int(tmp[0]), int(tmp[1]), int(tmp[2]))))
        for i in range(len(pointMatrixSorted)-1):
            P1 = pointMatrixSorted[i]
            P2 = pointMatrixSorted[i+1]
            distanceXY = math.sqrt(numpy.square(P1[0]-P2[0])+numpy.square(P1[1]-P2[1]))
            distanceXYZ = math.sqrt(numpy.square(P1[0]-P2[0])+numpy.square(P1[1]-P2[1])+numpy.square(P1[2]-P2[2]))
            dx = abs(P1[0]-P2[0])
            dy = abs(P1[1]-P2[1])
            dz = abs(P1[2]-P2[2])
            
            if  dx > 2 and dy > 2 and dz > 2:
                keyMatrix.append(P2)
            elif distanceXYZ > 5:
                keyMatrix.append(P2)
        keyMatrix.insert(0, pointMatrixSorted[0])
        for key in keyMatrix:
            dictionaryTmp.update({tuple(key):[]})
        ############################################################################################
        ## 依照 key 分類候選人, 同個組裡面, 平面距離 < 5, 第三個軸 < 31 ############################################################################################
        for tmp in pointMatrixSorted:
            for key in dictionaryTmp.keys():
                P1 = tmp
                P2 = key
                distanceXY = math.sqrt(numpy.square(P1[0]-P2[0])+numpy.square(P1[1]-P2[1]))
                dz = abs(P1[2]-P2[2])
                if distanceXY < 5 and dz < 31:
                    value = dictionaryTmp.get(key)
                    value.append(P1)
                    dictionaryTmp.update({key:value})
                    break
        ############################################################################################
        "size <= 5, delete"
        ## 組內候選人數量 <= 5, 刪除 ############################################################################################
        delete_label = []
        for key in dictionaryTmp.keys():
            if len(dictionaryTmp.get(key)) <= 5:
                delete_label.append(key)
        for dic1 in delete_label:
                try:
                    del dictionaryTmp[dic1]
                except:
                    pass
        ############################################################################################
        ## 檢查候選人與組內的第一個元素之距離不超過 DZ, 平面距離 < 3 ############################################################################################
        DZ = 20 + 10
        valueSorted = []
        categories = {}
        for key in dictionaryTmp.keys():
            value = dictionaryTmp.get(key)
            valueSorted = numpy.array(sorted(value, key=lambda tmp: (tmp[2])))
            
            for row in valueSorted:
                added = False
                for key_i, category in categories.items():
                    "檢查是否與現有組別的第一個元素之距離或震幅不超過 DZ"
                    dz1 = abs(row[2] - category[0][2])
                    dz2 = abs(row[2] - category[-1][2])
                    distanceXY = math.sqrt(numpy.square(row[0]-category[0][0])+numpy.square(row[1]-category[0][1]))
                    if dz1 <= DZ and dz2 <= DZ and distanceXY < 3:
                        category.append(row)
                        added = True
                        break
                if not added:
                    categories.update({tuple(row):[row]})
        ############################################################################################
        "把每一組的 key 換成組內的平均點"
        ## 把每一組的 key 換成組內的平均點 ############################################################################################
        dictionary = {}
        for key in categories:
            tmpValue = numpy.array(categories[key])
            Px = numpy.mean(tmpValue[:,0])
            Py = numpy.mean(tmpValue[:,1])
            Pz = numpy.mean(tmpValue[:,2])
            tmpKey = tuple([Px,Py,Pz])
            dictionary.update({tmpKey:tmpValue})
        ############################################################################################
        return dictionary
    ### 公式7
    def __FindBallYZ(self, imageHu):
        """scan YZ plane to  find ball centroid,
            May find candidate ball and non-candidates

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)

        Returns:
            result_centroid (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball
        """
        imageHuThr = self.ThresholdFilter(imageHu)
        src_tmp = numpy.uint8(imageHuThr)
        
        resultCentroid_yz = []
        
        "coefficient"
        ratio = 3
        low_threshold = 15
        "Radius range: [3mm ~ (21/2)+3mm]"
        minRadius=int(3)
        maxRadius=int(21/2)+3
        
        "find circle, radius and center of circle in each DICOM image"
        for x in range(src_tmp.shape[2]):
            ## 找輪廓與質心 ############################################################################################
            ### 公式8
            "draw contours"
            contours, hierarchy = cv2.findContours(src_tmp[:,:,x],
                                                cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)
            "create an all black picture to draw contour"
            shape = (src_tmp.shape[0], src_tmp.shape[1], 1)
            black_image_2 = numpy.zeros(shape, numpy.uint8)
            "use contour to find centroid"
            centroid = []
            tmpContours = []
            for c in contours:
                if c.shape[0] > 5:
                    M = cv2.moments(c)
                    if M["m00"] != 0:
                        Cy = (M["m10"]/M["m00"])
                        Cz = (M["m01"]/M["m00"])
                        centroid.append((Cy,Cz))
                        tmpContours.append(c)
            cv2.drawContours(black_image_2,tmpContours,-1,(256/2, 0, 0),1)
            ############################################################################################
            ## 用Hough Circles找球心跟半徑 ############################################################################################
            "use Hough Circles to find radius and center of circle"
            circles = cv2.HoughCircles(black_image_2, cv2.HOUGH_GRADIENT, 1, 10,
                                        param1=low_threshold*ratio, param2=low_threshold,
                                        minRadius=minRadius, maxRadius=maxRadius)
            ############################################################################################
            ## 質心與球心平面距離不超過2的留下當作候選人 ############################################################################################
            if circles is not None and centroid is not None:
                "Intersection"
                "centroid = group of Centroid"
                "circles = group of hough circle"
                for i in centroid:
                    for j in circles[0, :]:
                        distance = math.sqrt((i[0]-j[0])**2+(i[1]-j[1])**2)
                        if distance < 2:
                            Px = x
                            Py = i[0]
                            Pz = i[1]
                            Pr = j[2]
                            resultCentroid_yz.append([Px,Py,Pz,Pr])
            cv2.destroyAllWindows()
            ############################################################################################
        return resultCentroid_yz

    def __ClassifyPointYZ(self, pointMatrix, interestPoint):
        """classify Point Matrix from FindBall..() result
           save as numpy.array
           = {point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])}

        Args:
            pointMatrix (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball
            interestPoint(_dictionary_): {point, key(Px,Py,Pz):numpy.array([[Px,Py,Pz,Pr]...])}

        Returns:
            interestPoint(_dictionary_): {point, key(Px,Py,Pz):numpy.array([[Px,Py,Pz,Pr]...])}
        """
        tmpValue = []
        
        "sorted and classify"
        ## 依照 key 分類候選人, 同個組裡面, 平面距離 < 5, 第三個軸 < 31 ############################################################################################
        pointMatrixSorted = sorted(pointMatrix, key=lambda tmp: (int(tmp[1]), int(tmp[2]), int(tmp[0])))
        for p1 in pointMatrixSorted:
            addFlage = False
            for key in interestPoint.keys():
                distance = math.sqrt(numpy.square(p1[1]-key[1])+numpy.square(p1[2]-key[2]))
                dx = math.sqrt(numpy.square(p1[0]-key[0]))
                if distance < 5 and dx < 31:
                    tmpKey = key
                    tmpValue = numpy.array([p1])
                    addFlage = True
            if addFlage:
                value = numpy.append(interestPoint.get(tmpKey), tmpValue, axis=0)
                interestPoint.update({tmpKey:value})
                tmpValue = []
        ############################################################################################
        return interestPoint
    ### 公式7
    def __FindBallXZ(self, imageHu):
        """scan XZ plane to  find ball centroid,
            May find candidate ball and non-candidates

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)

        Returns:
            result_centroid (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball
        """
        imageHuThr = self.ThresholdFilter(imageHu)
        src_tmp = numpy.uint8(imageHuThr)
        
        resultCentroid_xz = []
        
        "coefficient"
        ratio = 3
        low_threshold = 15
        "Radius range: [3mm ~ (21/2)+3mm]"
        minRadius=int(3)
        maxRadius=int(21/2)+3
        
        "find circle, radius and center of circle in each DICOM image"
        for y in range(src_tmp.shape[1]):
            ## 找輪廓與質心 ############################################################################################
            ### 公式8
            "draw contours"
            contours, hierarchy = cv2.findContours(src_tmp[:,y,:],
                                                cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)
            "create an all black picture to draw contour"
            shape = (src_tmp.shape[0], src_tmp.shape[2], 1)
            black_image_2 = numpy.zeros(shape, numpy.uint8)
            "use contour to find centroid"
            centroid = []
            tmpContours = []
            for c in contours:
                if c.shape[0] > 5:
                    M = cv2.moments(c)
                    if M["m00"] != 0:
                        Cx = (M["m10"]/M["m00"])
                        Cz = (M["m01"]/M["m00"])
                        centroid.append((Cx,Cz))
                        tmpContours.append(c)
            cv2.drawContours(black_image_2,tmpContours,-1,(256/2, 0, 0),1)
            ############################################################################################
            ## 用Hough Circles找球心跟半徑 ############################################################################################
            "use Hough Circles to find radius and center of circle"
            circles = cv2.HoughCircles(black_image_2, cv2.HOUGH_GRADIENT, 1, 10,
                                        param1=low_threshold*ratio, param2=low_threshold,
                                        minRadius=minRadius, maxRadius=maxRadius)
            ############################################################################################
            ## 質心與球心平面距離不超過2的留下當作候選人 ############################################################################################
            if circles is not None and centroid is not None:
                "Intersection"
                "centroid = group of Centroid"
                "circles = group of hough circle"
                for i in centroid:
                    for j in circles[0, :]:
                        distance = math.sqrt((i[0]-j[0])**2+(i[1]-j[1])**2)
                        if distance < 2:
                            Px = i[0]
                            Py = y
                            Pz = i[1]
                            Pr = j[2]
                            resultCentroid_xz.append([Px,Py,Pz,Pr])
            cv2.destroyAllWindows()
            ############################################################################################
        return resultCentroid_xz

    def __ClassifyPointXZ(self, pointMatrix, interestPoint):
        """classify Point Matrix from FindBall..() result
            save as numpy.array
            = {point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])}

        Args:
            pointMatrix (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball
            interestPoint(_dictionary_): {point, key(Px,Py,Pz):numpy.array([[Px,Py,Pz,Pr]...])}

        Returns:
            interestPoint(_dictionary_): {point, key(Px,Py,Pz):numpy.array([[Px,Py,Pz,Pr]...])}
        """
        # dictionaryTmp = {}
        # keyMatrix = []
        # tmp = []
        tmpValue = []
        
        "sorted and classify"
        ## 依照 key 分類候選人, 同個組裡面, 平面距離 < 5, 第三個軸 < 31 ############################################################################################
        pointMatrixSorted = sorted(pointMatrix, key=lambda tmp: (int(tmp[0]), int(tmp[2]), int(tmp[1])))
        for p1 in pointMatrixSorted:
            addFlage = False
            for key in interestPoint.keys():
                distance = math.sqrt(numpy.square(p1[0]-key[0])+numpy.square(p1[2]-key[2]))
                dy = math.sqrt(numpy.square(p1[1]-key[1]))
                if distance < 5 and dy < 31:
                    tmpKey = key
                    tmpValue = numpy.array([p1])
                    addFlage = True
            if addFlage:
                value = numpy.append(interestPoint.get(tmpKey), tmpValue, axis=0)
                interestPoint.update({tmpKey:value})
                tmpValue = []
        ############################################################################################
        return interestPoint
    
    def __AverageValue(self, interestPoint):
        """remove .5 and integer, get candidate (with centroid)
           average value of point array

        Args:
            interestPoint (_numpy.array_): interest Point array

        Returns:
            tmpPoint (_number_): mean of interestPoint, whitch is remove .5 and integer
        """
        ## 計算平均 ############################################################################################
        array = []
        for tmp in interestPoint:
            "remove .5 and integer, get candidate (with centroid)"
            tmp_str0 = str(tmp)
            if int(tmp) != tmp and len(tmp_str0)-(tmp_str0.find(".")+1) == 1 and tmp_str0[tmp_str0.find(".")+1] == "5":
                pass
            elif int(tmp) == tmp:
                pass
            else:
                    array.append(tmp)
            
        tmpPoint = numpy.mean(array,0)
        ############################################################################################
        return tmpPoint

    def __AveragePoint(self, dictionaryPoint):
        """average points for find ball center

        Args:
            dictionaryPoint (_dictionary_): matrix points of ball center

        Returns:
            _numpy.array_: result of average
        """
        ## 計算候選人平均 ############################################################################################
        resultPoint = []
        for key, value in dictionaryPoint.items():
            point = [0, 0, 0]
            for n in range(3):
                point[n] = self.__AverageValue(value[:, n])
            resultPoint.append(point)
        ############################################################################################
        return numpy.array(resultPoint)
    ### 公式9
    def IdentifyPoint(self, point):
        """identify first ball, second ball, and third ball

        Args:
            point (_numpy.array_): matrix of ball center
            
        Returns:
            ball (_dictionary_): result
        """
        ## 辨識+定義定位球方向 ############################################################################################
        result = []
        tmpDic = {}
        shortSide = 30
        longSide = 65
        hypotenuse = math.sqrt(numpy.square(shortSide) + numpy.square(longSide))
        error = 1.5
        "計算三個點之間的距離"
        for p1, p2, p3 in itertools.combinations(point, 3):
            result = []
            d12 = ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2) ** 0.5
            d23 = ((p2[0] - p3[0]) ** 2 + (p2[1] - p3[1]) ** 2 + (p2[2] - p3[2]) ** 2) ** 0.5
            d31 = ((p3[0] - p1[0]) ** 2 + (p3[1] - p1[1]) ** 2 + (p3[2] - p1[2]) ** 2) ** 0.5
            "檢查邊長是否符合條件"
            if d12 > shortSide-error and d12 < shortSide+error:
                if d23 > longSide-error and d23 < longSide+error:
                    if d31 > hypotenuse-error and d31 < hypotenuse+error:
                        result.append(p2)
                        result.append(p1)
                        result.append(p3)
                        tmpDic.update({tuple(p2):result})
                elif d31 > longSide-error and d31 < longSide+error:
                    if d23 > hypotenuse-error and d23 < hypotenuse+error:
                        result.append(p1)
                        result.append(p2)
                        result.append(p3)
                        tmpDic.update({tuple(p1):result})
            elif d23 > shortSide-error and d23 < shortSide+error:
                if d31 > longSide-error and d31 < longSide+error:
                    if d12 > hypotenuse-error and d12 < hypotenuse+error:
                        result.append(p3)
                        result.append(p2)
                        result.append(p1)
                        tmpDic.update({tuple(p3):result})
                elif d12 > longSide-error and d12 < longSide+error:
                    if d31 > hypotenuse-error and d31 < hypotenuse+error:
                        result.append(p2)
                        result.append(p3)
                        result.append(p1)
                        tmpDic.update({tuple(p2):result})
            elif d31 > shortSide-error and d31 < shortSide+error:
                if d12 > longSide-error and d12 < longSide+error:
                    if d23 > hypotenuse-error and d23 < hypotenuse+error:
                        result.append(p1)
                        result.append(p3)
                        result.append(p2)
                        tmpDic.update({tuple(p1):result})
                elif d23 > longSide-error and d23 < longSide+error:
                    if d12 > hypotenuse-error and d12 < hypotenuse+error:
                        result.append(p3)
                        result.append(p1)
                        result.append(p2)
                        tmpDic.update({tuple(p3):result})
        ############################################################################################
        return tmpDic
            
    def GetBallAuto(self, imageHu, pixel2Mm, imageTag):
        """auto get ball center

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)
            pixel2Mm (_list_): Pixel to mm array
            imageTag (_list_): DICOM list sort by InstanceNumber (include metadata and pixel_array)

        Returns:
            (_bool_): true -> get ball success, false -> get ball fail
            ball (_dictionary_): ball center, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])
        """
        ## resize imageHu, 變成每個 pixel 相距 1 mm ############################################################################################
        imageHuMm_tmp_xyz = []
        if pixel2Mm[0] < 1 and pixel2Mm[1] < 1:
            for z in range(imageHu.shape[0]):
                src_tmp = cv2.resize(imageHu[z,:,:],dsize=None,fx=pixel2Mm[0],fy=pixel2Mm[1],interpolation=cv2.INTER_AREA)
                imageHuMm_tmp_xyz.append(src_tmp)
        elif pixel2Mm[0] > 1 and pixel2Mm[1] > 1:
            for z in range(imageHu.shape[0]):
                src_tmp = cv2.resize(imageHu[z,:,:],dsize=None,fx=pixel2Mm[0],fy=pixel2Mm[1],interpolation=cv2.INTER_CUBIC)
                imageHuMm_tmp_xyz.append(src_tmp)
        else:
            pass
        imageHuMm_tmp_xyz = numpy.array(imageHuMm_tmp_xyz)
        imageHuMm_tmp = []
        if pixel2Mm[2] < 1:
            for y in range(imageHuMm_tmp_xyz.shape[1]):
                src_tmp = cv2.resize(imageHuMm_tmp_xyz[:,y,:],dsize=None,fx=1,fy=pixel2Mm[2],interpolation=cv2.INTER_AREA)
                imageHuMm_tmp.append(src_tmp)
            imageHuMm_tmp = numpy.array(imageHuMm_tmp)
            imageHuMm = []
            for z in range(imageHuMm_tmp.shape[1]):
                imageHuMm.append(imageHuMm_tmp[:,z,:])
            imageHuMm = numpy.array(imageHuMm)
        elif pixel2Mm[2] > 1:
            for y in range(imageHuMm_tmp_xyz.shape[2]):
                src_tmp = cv2.resize(imageHuMm_tmp_xyz[:,y,:],dsize=None,fx=1,fy=pixel2Mm[2],interpolation=cv2.INTER_CUBIC)
                imageHuMm_tmp.append(src_tmp)
            imageHuMm_tmp = numpy.array(imageHuMm_tmp)
            imageHuMm = []
            for z in range(imageHuMm_tmp.shape[1]):
                imageHuMm.append(imageHuMm_tmp[:,z,:])
            imageHuMm = numpy.array(imageHuMm)
        else:
            imageHuMm = imageHuMm_tmp_xyz
            imageHuMm = numpy.array(imageHuMm)
        ############################################################################################
        ## 取得候選人球心 ############################################################################################
        resultCentroid_xy = self.__FindBallXY(imageHuMm)
        dictionaryPoint = self.__ClassifyPointXY(resultCentroid_xy)
        resultCentroid_yz = self.__FindBallYZ(imageHuMm)
        dictionaryPoint = self.__ClassifyPointYZ(resultCentroid_yz, dictionaryPoint)
        resultCentroid_xz = self.__FindBallXZ(imageHuMm)
        dictionaryPoint = self.__ClassifyPointXZ(resultCentroid_xz, dictionaryPoint)
        
        pointMatrixSorted_xy = numpy.array(sorted(resultCentroid_xy, key=lambda tmp: (int(tmp[0]), int(tmp[1]), int(tmp[2]))))
        pointMatrixSorted_yz = numpy.array(sorted(resultCentroid_yz, key=lambda tmp: (int(tmp[1]), int(tmp[2]), int(tmp[0]))))
        pointMatrixSorted_xz = numpy.array(sorted(resultCentroid_xz, key=lambda tmp: (int(tmp[0]), int(tmp[2]), int(tmp[1]))))
        
        averagePoint = self.__AveragePoint(dictionaryPoint)
        ############################################################################################
        ## 計算得出病人坐標系下的球心 ############################################################################################
        resultPoint = []
        for p in averagePoint:
            try:
                pTmp1 = [(p[0]),(p[1]),int(p[2])]
                tmpPoint1 = self.TransformPointVTK(imageTag, pTmp1)
                
                pTmp2 = [(p[0]),(p[1]),int(p[2])+1]
                tmpPoint2 = self.TransformPointVTK(imageTag, pTmp2)
                
                X1 = int(p[2])
                X2 = int(p[2])+1
                Y1 = tmpPoint1[2]
                Y2 = tmpPoint2[2]
                X = p[2]
                Pz = (Y1 + (Y2 - Y1) * ((X - X1) / (X2 - X1)))/pixel2Mm[2]
                resultPoint.append([tmpPoint1[0],tmpPoint1[1],Pz, p[0], p[1], p[2]])
            except:
                pass
        ## 辨識定位球方向 ############################################################################################
        try:
            ball = self.IdentifyPoint(numpy.array(resultPoint))
        except:
            ball = []
        print("-------------------------------------------------------------------")
        print("ball: \n", ball)
        print("-------------------------------------------------------------------")
        ############################################################################################
        ## 如果 IdentifyPoint 失敗, return 候選人, 為了手動註冊 ############################################################################################
        pointMatrixSorted = numpy.concatenate((pointMatrixSorted_xy, pointMatrixSorted_yz, pointMatrixSorted_xz), axis = 0)
        if ball == {}:
            return False, pointMatrixSorted
        elif ball == []:
            return False, pointMatrixSorted
        else:
            return True, ball
        ############################################################################################
    ### 公式10
    def TransformPointVTK(self, imageTag, point):
        """Transform pixel point (in VTK image unit) to mm point in patient coordinates

        Args:
            imageTag (_list_): DICOM list sort by InstanceNumber (include metadata and pixel_array)
            point (_numpy.array, dtype=int_): pixel point (in CT image coordinates)

        Returns:
            point (_numpy.array_): Transformed Point (in patient coordinates)
        """
        ## 把 VTK image 轉換成病人坐標系 ############################################################################################
        ImageOrientationPatient = imageTag[int(point[2])-1].ImageOrientationPatient
        ImagePositionPatient = imageTag[int(point[2])-1].ImagePositionPatient

        x = point[0]
        y = point[1]
        RowVector = ImageOrientationPatient[0:3]
        ColumnVector = ImageOrientationPatient[3:6]
        X = ImagePositionPatient[0] + x * RowVector[0] + y * ColumnVector[0]
        Y = ImagePositionPatient[1] + x * RowVector[1] + y * ColumnVector[1]
        Z = ImagePositionPatient[2] + x * RowVector[2] + y * ColumnVector[2]
        ############################################################################################
        return numpy.array([X,Y,Z])
    
    def GetBallManual(self, candidateBall, pixel2Mm, answer, imageTag):
        """manually get ball center

        Args:
            candidateBall (_numpy.array_): array of user selected ball center
            pixel2Mm (_list_): Pixel to mm array
            answer (_numpy.array_):  array of ball center, which is from auto get ball center in VTK image unit
            imageTag (_list_): DICOM list sort by InstanceNumber (include metadata and pixel_array)

        Returns:
            (_bool_): true -> get ball success, false -> get ball fail
            ball (_dictionary_): get ball center result, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])
        """
        ## 找出與手動點選的點接近的候選人 ############################################################################################
        dictionaryPoint = {}
        for point in candidateBall:
            dictionaryPoint.update({tuple(point):numpy.array([[]])})
        for key, value in dictionaryPoint.items():
            valueMatrix = []
            for point in answer:
                P1 = key
                P2 = point
                distanceXYZ = math.sqrt(numpy.square(P1[0]-P2[0])+numpy.square(P1[1]-P2[1])+numpy.square(P1[2]-P2[2]))
                if distanceXYZ < 15:
                    valueMatrix.append(point)
            dictionaryPoint.update({tuple(key):numpy.array(valueMatrix)})
        
        averagePoint = self.__AveragePoint(dictionaryPoint)
        ############################################################################################
        ## 計算得出病人坐標系下的球心 ############################################################################################
        resultPoint = []
        for p in averagePoint:
            try:
                pTmp1 = [(p[0]),(p[1]),int(p[2])]
                tmpPoint1 = self.TransformPointVTK(imageTag, pTmp1)
                
                pTmp2 = [(p[0]),(p[1]),int(p[2])+1]
                tmpPoint2 = self.TransformPointVTK(imageTag, pTmp2)
                
                X1 = int(p[2])
                X2 = int(p[2])+1
                Y1 = tmpPoint1[2]
                Y2 = tmpPoint2[2]
                X = p[2]
                Pz = (Y1 + (Y2 - Y1) * ((X - X1) / (X2 - X1)))/pixel2Mm[2]
                resultPoint.append([tmpPoint1[0],tmpPoint1[1],Pz, p[0], p[1], p[2]])
                
            except:
                pass
        ############################################################################################
        ## 辨識定位球方向 ############################################################################################
        try:
            ball = self.IdentifyPoint(numpy.array(resultPoint))
        except:
            ball = []
        print("-------------------------------------------------------------------")
        print("ball: \n", ball)
        print("-------------------------------------------------------------------")
        ############################################################################################
        
        if ball == []:
            return False, ball
        else:
            return True, ball
    ### 公式11
    def GetPlanningPath(self, originPoint, selectedPoint, regMatrix):
        """get planning path

        Args:
            originPoint (_numpy.array_): origin point of coordinate system
            selectedPoint (_numpy.array_): selected points of planning path
            regMatrix (_numpy.array_): registration matrix

        Returns:
            planningPath (_list_): planning path result
        """
        planningPath = []
        
        for p in selectedPoint:
            planningPath.append(numpy.dot(regMatrix,(p-originPoint)))
        
        return planningPath

class DISPLAY():
    def __init__(self):
        pass
    
    def LoadImage(self, folderPath):
        """load image
           use VTK
           for diocm display
           and image array in VTK

        Args:
            folderPath (_string_): dir + folder name (==folderDir)

        Returns:
            imageVTK (_numpy.array_): image array in VTK
        """
        "init"
        self.radius = 3.5
        ## 建立好load dicom 所需的 VTK 物件 ############################################################################################
        self.reader = vtkDICOMImageReader()
        self.windowLevelLookup = vtkWindowLevelLookupTable()
        self.mapColors = vtkImageMapToColors()
        
        self.cameraSagittal = vtkCamera()
        self.cameraCoronal = vtkCamera()
        self.cameraAxial = vtkCamera()
        self.camera3D = vtkCamera()
        
        self.actorSagittal = vtkImageActor()
        self.actorCoronal = vtkImageActor()
        self.actorAxial = vtkImageActor()
        
        self.rendererSagittal = vtkRenderer()
        self.rendererCoronal = vtkRenderer()
        self.rendererAxial = vtkRenderer()
        self.renderer3D = vtkRenderer()
        
        "planningPointCenter"
        self.actorPointEntry = vtkActor()
        self.actorPointTarget = vtkActor()
        self.actorLine = vtkActor()
        self.actorTube = vtkActor()
        
        self.reader.SetDirectoryName(folderPath)
        self.reader.Update()
        
        self.vtkImage = self.reader.GetOutput()
        self.vtkImage.SetOrigin(0, 0, 0)
        self.dicomGrayscaleRange = self.vtkImage.GetScalarRange()
        self.dicomBoundsRange = self.vtkImage.GetBounds()
        self.imageDimensions = self.vtkImage.GetDimensions()
        self.pixel2Mm = self.vtkImage.GetSpacing()
        
        self.SetMapColor()
        
        vtkArray = self.vtkImage.GetPointData().GetScalars()
        imageVTK = vtk_to_numpy(vtkArray).reshape(self.imageDimensions[2], self.imageDimensions[1], self.imageDimensions[0])
        ############################################################################################
        return imageVTK
        
    def SetMapColor(self):
        """init window level and window width
        """
        ## 設定 WW/WL ############################################################################################
        self.windowLevelLookup.Build()
        thresholdValue = int(((self.dicomGrayscaleRange[1] - self.dicomGrayscaleRange[0]) / 6) + self.dicomGrayscaleRange[0])
        self.windowLevelLookup.SetWindow(abs(thresholdValue*2))
        self.windowLevelLookup.SetLevel(thresholdValue)

        self.mapColors.SetInputConnection(self.reader.GetOutputPort())
        self.mapColors.SetLookupTable(self.windowLevelLookup)
        self.mapColors.Update()
        ############################################################################################
        self.SetCamera()
        
        return
        
    def SetCamera(self):
        """set VTK camera
        """
        "differen section, differen camera"
        ## 設定 VTK 視窗的攝影機 ############################################################################################
        self.cameraSagittal.SetViewUp(0, 0, -1)
        self.cameraSagittal.SetPosition(1, 0, 0)
        self.cameraSagittal.SetFocalPoint(0, 0, 0)
        self.cameraSagittal.ComputeViewPlaneNormal()
        self.cameraSagittal.ParallelProjectionOn()
        
        self.cameraCoronal.SetViewUp(0, 0, -1)
        self.cameraCoronal.SetPosition(0, 1, 0)
        self.cameraCoronal.SetFocalPoint(0, 0, 0)
        self.cameraCoronal.ComputeViewPlaneNormal()
        self.cameraCoronal.ParallelProjectionOn()
        
        self.cameraAxial.SetViewUp(0, 1, 0)
        self.cameraAxial.SetPosition(0, 0, 1)
        self.cameraAxial.SetFocalPoint(0, 0, 0)
        self.cameraAxial.ComputeViewPlaneNormal()
        self.cameraAxial.ParallelProjectionOn()
        
        self.camera3D.SetViewUp(0, 1, 0)
        self.camera3D.SetPosition(0.8, 0.3, 1)
        self.camera3D.SetFocalPoint(0, 0, 0)
        self.camera3D.ComputeViewPlaneNormal()
        ############################################################################################
        return
        
    def CreateActorAndRender(self, value):
        """create actor and render for VTK

        Args:
            value (_int_): location of slice
        """
        ## 設定 VTK 顯示物件 ############################################################################################
        "actor"
        "Sagittal"
        self.actorSagittal.GetMapper().SetInputConnection(self.mapColors.GetOutputPort())
        self.actorSagittal.SetDisplayExtent(value, value, 0, self.imageDimensions[1], 0, self.imageDimensions[2])
        "Coronal"
        self.actorCoronal.GetMapper().SetInputConnection(self.mapColors.GetOutputPort())
        self.actorCoronal.SetDisplayExtent(0, self.imageDimensions[0], value, value, 0, self.imageDimensions[2])
        "Axial"
        self.actorAxial.GetMapper().SetInputConnection(self.mapColors.GetOutputPort())
        self.actorAxial.SetDisplayExtent(0, self.imageDimensions[0], 0, self.imageDimensions[1], value, value)
        
        "render"
        "Sagittal"
        self.rendererSagittal.SetBackground(0, 0, 0)
        self.rendererSagittal.AddActor(self.actorSagittal)
        self.rendererSagittal.SetActiveCamera(self.cameraSagittal)
        self.rendererSagittal.ResetCamera(self.dicomBoundsRange)
        "Coronal"
        self.rendererCoronal.SetBackground(0, 0, 0)
        self.rendererCoronal.AddActor(self.actorCoronal)
        self.rendererCoronal.SetActiveCamera(self.cameraCoronal)
        self.rendererCoronal.ResetCamera(self.dicomBoundsRange)
        "Axial"
        self.rendererAxial.SetBackground(0, 0, 0)
        self.rendererAxial.AddActor(self.actorAxial)
        self.rendererAxial.SetActiveCamera(self.cameraAxial)
        self.rendererAxial.ResetCamera(self.dicomBoundsRange)
        "3D"
        self.renderer3D.SetBackground(0, 0, 0)
        self.renderer3D.AddActor(self.actorSagittal)
        self.renderer3D.AddActor(self.actorAxial)
        self.renderer3D.AddActor(self.actorCoronal)
        self.renderer3D.SetActiveCamera(self.camera3D)
        self.renderer3D.ResetCamera(self.dicomBoundsRange)
        ############################################################################################
        return
        
    def ChangeSagittalView(self, value):
        """change sagittal view

        Args:
            value (_int_): location of slice
        """
        ## 改變 slice ############################################################################################
        self.actorSagittal.SetDisplayExtent(value, value, 0, self.imageDimensions[1], 0, self.imageDimensions[2])
        ############################################################################################
        return
    
    def ChangeCoronalView(self, value):
        """change coronal view

        Args:
            value (_int_): location of slice
        """
        ## 改變 slice ############################################################################################
        self.actorCoronal.SetDisplayExtent(0, self.imageDimensions[0]-1, value, value, 0, self.imageDimensions[2]-1)
        ############################################################################################
        return

    def ChangeAxialView(self, value):
        """change axial view

        Args:
            value (_int_): location of slice
        """
        ## 改變 slice ############################################################################################
        self.actorAxial.SetDisplayExtent(0, self.imageDimensions[0]-1, 0, self.imageDimensions[1]-1, value, value)
        ############################################################################################
        return
    
    def ChangeWindowWidthView(self, value):
        """change window width

        Args:
            value (_int_): number of window width
        """
        ## 改變 window width ############################################################################################
        self.windowLevelLookup.SetWindow(value)
        self.mapColors.Update()
        ############################################################################################
        return
        
    def ChangeWindowLevelView(self, value):
        """change window level

        Args:
            value (_int_): number of window level
        """
        ## 改變 window level ############################################################################################
        self.windowLevelLookup.SetLevel(value)
        self.mapColors.Update()
        ############################################################################################
        return
    
    def CreateEntry(self, center):
        """create entry point

        Args:
            center (_numpy.array_): point center
        """
        ## 建立 entry point 物件 ############################################################################################
        sphereSource = vtkSphereSource()
        sphereSource.SetCenter(center)
        sphereSource.SetRadius(self.radius)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.actorPointEntry.SetMapper(mapper)
        self.actorPointEntry.GetProperty().SetColor(0, 1, 0)
        
        self.rendererSagittal.AddActor(self.actorPointEntry)
        self.rendererAxial.AddActor(self.actorPointEntry)
        self.rendererCoronal.AddActor(self.actorPointEntry)
        self.renderer3D.AddActor(self.actorPointEntry)
        ############################################################################################
        return
    
    def CreateTarget(self, center):
        """create target point

        Args:
            center (_numpy.array_): point center
        """
        ## 建立 target point 物件 ############################################################################################
        sphereSource = vtkSphereSource()
        sphereSource.SetCenter(center)
        sphereSource.SetRadius(self.radius)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.actorPointTarget.SetMapper(mapper)
        self.actorPointTarget.GetProperty().SetColor(1, 0, 0)
        
        self.rendererSagittal.AddActor(self.actorPointTarget)
        self.rendererAxial.AddActor(self.actorPointTarget)
        self.rendererCoronal.AddActor(self.actorPointTarget)
        self.renderer3D.AddActor(self.actorPointTarget)
        ############################################################################################
        return
       
    def CreateLine(self, startPoint, endPoint):
        """create line between enter point and target point

        Args:
            startPoint (_numpy.array_): enter point
            endPoint (_numpy.array_): target point
        """
        ## 建立線 ############################################################################################
        colors = vtkNamedColors()

        "Create a line"
        lineSource = vtkLineSource()
        lineSource.SetPoint1(startPoint)
        lineSource.SetPoint2(endPoint)

        lineMapper = vtkPolyDataMapper()
        lineMapper.SetInputConnection(lineSource.GetOutputPort())

        
        self.actorLine.SetMapper(lineMapper)
        self.actorLine.GetProperty().SetColor(colors.GetColor3d('Red'))

        "Create tube filter"
        tubeFilter = vtkTubeFilter()
        tubeFilter.SetInputConnection(lineSource.GetOutputPort())
        tubeFilter.SetRadius(3)
        tubeFilter.SetNumberOfSides(50)
        tubeFilter.Update()

        tubeMapper = vtkPolyDataMapper()
        tubeMapper.SetInputConnection(tubeFilter.GetOutputPort())

        self.actorTube.SetMapper(tubeMapper)
        "Make the tube have some transparency"
        self.actorTube.GetProperty().SetOpacity(0.5)
        
        self.rendererSagittal.AddActor(self.actorLine)
        self.rendererAxial.AddActor(self.actorLine)
        self.rendererCoronal.AddActor(self.actorLine)
        self.renderer3D.AddActor(self.actorLine)
        
        self.rendererSagittal.AddActor(self.actorTube)
        self.rendererAxial.AddActor(self.actorTube)
        self.rendererCoronal.AddActor(self.actorTube)
        self.renderer3D.AddActor(self.actorTube)
        ############################################################################################
        return

     
    def CreatePath(self, planningPointCenter):
        """create planning path between enter point and target point

        Args:
            planningPointCenter (_type_): point center of enter point and target point
        """
        ## 建立手術路徑 ############################################################################################
        self.CreateEntry(planningPointCenter[0])
        self.CreateTarget(planningPointCenter[1])
        self.CreateLine(planningPointCenter[0], planningPointCenter[1])
        ############################################################################################
        return
        
    def RemovePoint(self):
        """remove actor of point
        """
        ## 移除點物件 ############################################################################################
        self.rendererSagittal.RemoveActor(self.actorPointEntry)
        self.rendererAxial.RemoveActor(self.actorPointEntry)
        self.rendererCoronal.RemoveActor(self.actorPointEntry)
        self.renderer3D.RemoveActor(self.actorPointEntry)
        
        self.rendererSagittal.RemoveActor(self.actorPointTarget)
        self.rendererAxial.RemoveActor(self.actorPointTarget)
        self.rendererCoronal.RemoveActor(self.actorPointTarget)
        self.renderer3D.RemoveActor(self.actorPointTarget)
        
        self.rendererSagittal.RemoveActor(self.actorLine)
        self.rendererAxial.RemoveActor(self.actorLine)
        self.rendererCoronal.RemoveActor(self.actorLine)
        self.renderer3D.RemoveActor(self.actorLine)
        
        self.rendererSagittal.RemoveActor(self.actorTube)
        self.rendererAxial.RemoveActor(self.actorTube)
        self.rendererCoronal.RemoveActor(self.actorTube)
        self.renderer3D.RemoveActor(self.actorTube)
        ############################################################################################
        return

