import copy
import itertools
import math
import os
import shutil
import sys
from datetime import datetime, timedelta
from multiprocessing.sharedctypes import Value

# from keras.models import load_model
import cv2
import matplotlib.pyplot as plt
import numpy as np
import pydicom
import vtkmodules.all as vtk
from numpy._typing import _ArrayLike
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkFiltersCore import vtkTubeFilter
from vtkmodules.vtkFiltersSources import vtkLineSource, vtkSphereSource
from vtkmodules.vtkImagingCore import vtkImageMapToColors, vtkImageReslice
from vtkmodules.vtkIOImage import vtkDICOMImageReader
from vtkmodules.vtkRenderingCore import (
    vtkActor, 
    vtkActor2D, 
    vtkAssembly,
    vtkCamera, 
    vtkCoordinate,
    vtkImageActor, 
    vtkPolyDataMapper,
    vtkPolyDataMapper2D, 
    vtkRenderer,
    vtkVolume, 
    vtkVolumeProperty,
    vtkWindowLevelLookupTable
)
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage

from FunctionLib_Robot.logger import logger
from FunctionLib_Robot.__init__ import *

from ._subFunction import *
from scipy.spatial.transform import Rotation as R
from scipy.spatial.distance import pdist, squareform
from scipy.ndimage import label, zoom
from skimage.measure import regionprops
# import vtk.numpy_interface.dataset_adapter as dsa


VIEW_AXIAL          = 'Axial'
VIEW_CORONAL        = 'Coronal'
VIEW_SAGITTAL       = 'Sagittal'
VIEW_3D             = '3D'
VIEW_CROSS_SECTION  = 'Cross-Section'
SCALAR_TYPE_RANGE = {
            vtk.VTK_UNSIGNED_CHAR:  (0, 255),
            vtk.VTK_CHAR:           (-128, 127),
            vtk.VTK_UNSIGNED_SHORT: (0, 65535),
            vtk.VTK_SHORT:          (-32767, 32767),
            vtk.VTK_UNSIGNED_INT:   (0, sys.maxsize),
            vtk.VTK_INT:            (-sys.maxsize - 1, sys.maxsize),
            vtk.VTK_UNSIGNED_LONG:  (0, sys.maxsize),
            vtk.VTK_LONG:           (-sys.maxsize - 1, sys.maxsize),
            vtk.VTK_FLOAT:          (-sys.float_info.max, sys.float_info.max),
            vtk.VTK_DOUBLE:         (-sys.float_info.max, sys.float_info.max)
}

copy_count = 0

class QSignalObject(QObject):  
    signalRange = pyqtSignal(bool, bool)
    signalUpdateHU = pyqtSignal(int)
    signalGetRenderer = pyqtSignal(vtkRenderer)
    signalOutRenderer = pyqtSignal(vtkRenderer)
    signalUpdateView  = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
    def EmitUpdateHU(self, value):
        if value == '':
            return
        self.signalUpdateHU.emit(int(value))
        
    def EmitRange(self, bRangeBack, bRangeNext):
        self.signalRange.emit(bRangeBack, bRangeNext)
        
    def EmitGetRenderer(self, renderer):
        self.signalGetRenderer.emit(renderer)
        
    def EmitOutRenderer(self, renderer):
        self.signalOutRenderer.emit(renderer)
        
    def EmitUpdateView(self):
        self.signalUpdateView.emit()
        
    def ConnectUpdateHU(self, callbackFunc):
        self.signalUpdateHU.connect(callbackFunc)
        
    def ConnectRange(self, callbackFunc):
        self.signalRange.connect(callbackFunc)
        
    def ConnectGetRenderer(self, callbackFunc):
        self.signalGetRenderer.connect(callbackFunc)
        
    def ConnectOutRenderer(self, callbackFunc):
        self.signalOutRenderer.connect(callbackFunc)
        
    def ConnectUpdateView(self, callbackFunc):
        self.signalUpdateView.connect(callbackFunc)

"DICOM function"
class DICOM(QObject):
    signalProcess = pyqtSignal(float, str)
    
    def __init__(self):
        super().__init__()
        
        
        self.dicPatient = None
        self.windowWidth = None
        self.windowLevel = None
        self.rescaleSlope = None
        self.rescaleIntercept = None
        self.currentSeries = {}
        
    def _RotateImage(self, images:_ArrayLike, spacing:_ArrayLike, axis:str, turns:int):
        if turns == 0:
            return
        
        if axis == 'x':
            # rotate x axis
            images = np.rot90(images, turns, (0, 1))
            if turns % 2 == 1:
                spacing[1:] = spacing[1:][::-1]
            
        elif axis == 'y':
            # rotate y axis
            images = np.rot90(images, turns, (0, 2))
            if turns % 2 == 1:
                spacing[::2] = spacing[::2][::-1]
            
        elif axis == 'z':
            #rotate z axis
            images = np.rot90(images, turns, (1, 2))
            if turns % 2 == 1:
                spacing[:2] = spacing[:2][::-1]
                
        return images, spacing
        
    def GetTotalFiles(self, path:str):
        files = os.listdir(path)
        count = 0
        for f in files:
            fullPath = os.path.join(path, f)
            if os.path.isdir(fullPath):
                count += self.GetTotalFiles(fullPath)
            else:
                count += 1
                
        return count
    
    def CreateDir(self, path:str):
        try:
            os.makedirs(path)
        except FileExistsError:
            logger.error('directory already exists')
        except Exception as e:
            logger.critical(f'create directory error:{e}')
            
    def ClearSelectedSeries(self, index:int):
        if self.currentSeries.get(index):
            del self.currentSeries[index]
        
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
        metadataSeries = []
        metadataStudy = []
        metadataFileList = []
        
        totalFiles = 0
        for dirPath, dirNames, fileNames in os.walk(folderPath):
            dir.append(dirPath)
            for f in fileNames:
                tmpDir = os.path.join(dirPath, f)
                filePathList.append(tmpDir)
                totalFiles += 1
                
        count = 0
        for s in filePathList:
            try:
                # fileData = pydicom.read_file(s)
                fileData = pydicom.dcmread(s)
                metadata.append(fileData)
                # metadataSeries.append(fileData.SeriesInstanceUID)
                # metadataStudy.append(fileData.StudyInstanceUID)
                metadataFileList.append(s)
                count += 1
                self.signalProcess.emit(np.round(count / totalFiles, 2), s)
            except:
                continue
        studyNumber = np.unique(metadataStudy)
        # if studyNumber.shape[0]>1 or len(metadataStudy)==0:
        #     metadata = 0
        #     metadataSeriesNum = 0
        
        totalFiles = len(metadata)
        count = 0
        skipCount = 0
        skipRepeatCount = 0
        dicPatient = {}
        for fileData in metadata:
            if not hasattr(fileData, 'PatientID'):
                skipCount += 1
                continue
            
            
            
            elem = self.FindTag(fileData, (0x18, 0x50))
            if elem is None:
                # (0018, 0050) 和 (0018, 0088)兩個tag都不存在，判斷此檔案應該略過
                # 可能有兩種都不存在但仍然可後判讀的情況
                # 例如透過(0020, 0032) Image Position去計算差值
                # elemSpacingBetweenSlices = self.FindTag(fileData, (0x18, 0x88))
                # elemImagePosition = self.FindTag(fileData, (0x20, 0x32))
                elemSpacingXY = self.FindTag(fileData, (0x28, 0x30))
                if elemSpacingXY is None:
                    skipCount += 1
                    continue
            
            
            pID = fileData.PatientID
            
            if pID not in dicPatient.keys():
                dicPatient[pID] = {}
            
            studyID = fileData.StudyInstanceUID
            if studyID not in dicPatient[pID].keys():
                dicPatient[pID][studyID] = {}
                
            seriesID = fileData.SeriesInstanceUID
            if seriesID not in dicPatient[pID][studyID].keys():
                dicPatient[pID][studyID][seriesID] = {}
                dicPatient[pID][studyID][seriesID]['data'] = []
                dicPatient[pID][studyID][seriesID]['sopID'] = []
            dicSeries = dicPatient[pID][studyID][seriesID]
            
            # 檢查是否有重複的SOP ID
            sopID = self.FindTag(fileData, (0x08, 0x18))
            if sopID:
                listID = dicSeries['sopID']
                if sopID not in listID:
                    listID.append(sopID)
                else:
                    skipRepeatCount += 1
                    continue
            
            dicSeries['path'] = os.path.dirname(fileData.filename)
            # if 'MULTIFRAME' in fileData.ImageType:
            #     print(f'multiframe dicom found!!')
            
            # dicPatient[pID][studyID][seriesID].append(fileData)
            dicSeries['data'].append(fileData)
            count += 1
            self.signalProcess.emit(np.round(count / totalFiles, 2), fileData.filename)
        self.dicPatient = dicPatient
        logger.info(f'skip {skipCount} files')
        logger.info(f'found {skipRepeatCount} files repeated and skip')
        
        #sort series
        # count = 0
        # self.CreateDir('database')
            
        for patient in dicPatient.values():
            for study in patient.values():
                for series in study.values():
                    
                    slices:list = series['data']
                    slice = series['data'][0]
                    
                    # 讀取DTI 試作
                    # DGO = self.FindTag(slices[0], (0x18,0x9089))
                    # if DGO:
                    #     newList = []
                    #     for img in slices:
                    #         elem = self.FindTag(img, (0x18,0x9089))
                    #         if elem and elem == DGO:
                    #             BValue = self.FindTag(img, (0x18, 0x9087))
                    #             if BValue:
                    #                 print(f'B Value = {BValue}')
                    #                 newList.append(img)
                    #             print(f'Diffusion Gradient Orientation = {elem}')
                        
                    #     series['data'] = newList
                    #     # shutil.copy(str(img.filename), destDir)
                    
                        
                    # get image orientation
                    imageOrientation = self.FindTag(slice, (0x20, 0x37))
                    if imageOrientation:
                        imageOrientation = np.array(imageOrientation)
                        series['orientation'] = imageOrientation
                    
                    if hasattr(slice, 'ImagePositionPatient'):
                        imagePosition = slice.ImagePositionPatient
                        # calculate z direction
                        # sort by z direction
                        x = imageOrientation[:3]
                        y = imageOrientation[3:]
                        z = np.cross(x, y)
                        direct_idx = np.argmax(np.abs(z))
                        bReverse = z[direct_idx] < 0
                        slices.sort(key = lambda x:x.ImagePositionPatient[direct_idx], reverse = bReverse)
                    else:
                        logger.warning(f'missing:ImagePositionPatient')
                        elem = self.FindTag(slice, (0x20, 0x32))
                        if elem:
                            logger.info(f'found tag(0x20, 0x32) = {elem} in patient ID = {slice.PatientID}')
                            
                    # 讀取X, Y spacing
                    elem = self.FindTag(slice, (0x28, 0x30))
                    if elem:
                        series['spacingXY'] = list(elem)
                            
                    slicesNum = len(series['data'])
                    if slicesNum > 3:
                        firstImagePosition = self.FindTag(series['data'][0], (0x20, 0x32))
                        lastImagePosition = self.FindTag(series['data'][-1], (0x20, 0x32))
                        
                        if firstImagePosition and lastImagePosition:
                            k = (np.array(lastImagePosition) - np.array(firstImagePosition)) / (slicesNum - 1)
                            thickness = np.linalg.norm(np.array(lastImagePosition) - np.array(firstImagePosition))
                            if not np.isnan(thickness):
                                thickness /= (slicesNum - 1)
                                series['spacingZ'] = thickness
                            else:
                                sopID = series['sopID']
                                logger.warning(f'series[{sopID}] could have wrong spacing between slices')
                                
                            
                            orientationMatrix = np.reshape(imageOrientation, (3, 2), order = 'F')
                            orientationMatrix = orientationMatrix[:, ::-1]
                            
                            #計算dicom affine matrix
                            affine_matrix = np.zeros((4, 4), dtype = np.float32)
                            affine_matrix[:3, 0] = orientationMatrix[:, 0] * series['spacingXY'][0]
                            affine_matrix[:3, 1] = orientationMatrix[:, 1] * series['spacingXY'][1]
                            affine_matrix[:3, 2] = k
                            affine_matrix[:3, 3] = firstImagePosition
                            affine_matrix[3, 3] = 1.0
                            series['affine_matrix'] = affine_matrix
                    
                    # 讀取Z spacing
                    spacingZ = series.get('spacingZ')
                    if spacingZ is None:
                        elem = self.FindTag(slice, (0x18, 0x50))
                        if elem is None:
                            elemSpacingBetweenSlices = self.FindTag(slice, (0x18, 0x88))
                            if elemSpacingBetweenSlices:
                                series['spacingZ'] = elemSpacingBetweenSlices
                                    
                        else:
                            series['spacingZ'] = elem
                                
                        
                    elemPatientPosition = self.FindTag(slice, (0x18, 0x5100))
                    if elemPatientPosition:
                        series['patientPosition'] = elemPatientPosition
                        
                        
                    # 讀取Acquisition dateTime
                    elem = self.FindTag(slice, (0x8, 0x2A))
                    if elem:
                        dateObj = datetime.strptime(elem, '%Y%m%d%H%M%S.%f')
                        series['acquisitionDate'] = dateObj.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        # 讀取Acquisition date
                        elem = self.FindTag(slice, (0x8, 0x22))
                        if elem:
                            dateObj = datetime.strptime(elem, '%Y%m%d')
                            series['acquisitionDate'] = dateObj.strftime('%Y-%m-%d')
                        else:
                            # Series date
                            elem = self.FindTag(slice, (0x8, 0x21))
                            if elem:
                                dateObj = datetime.strptime(elem, '%Y%m%d')
                                series['acquisitionDate'] = dateObj.strftime('%Y-%m-%d')
                            else:
                                series['acquisitionDate'] = 'NONE'
                                
                    # 讀取DimX
                    dimension = np.array([], int)
                    # 讀取multiframe data
                    frames = self.FindTag(slice, (0x28, 0x8))            
                    if frames and frames > 1:
                        logger.info(f'is a multi-frame dicom, {frames} frame in the series')
                        dimension = np.append(dimension, frames)
                        
                    dimY = self.FindTag(slice, (0x28, 0x10))            
                    if dimY:
                        dimension = np.append(dimension, dimY)
                        
                    dimX = self.FindTag(slice, (0x28, 0x11))            
                    if dimX:
                        dimension = np.append(dimension, dimX)
                        
                    series['dimension'] = dimension
                                
        self.signalProcess.emit(1.0, '')
                        
                        # print(f'imagePosition = {slice.ImagePositionPatient}')
                    # for slice in slices:
                    #     if hasattr(slice, 'ImagePositionPatient'):
                    #         print(f'imagePosition = {slice.ImagePositionPatient}')
                        
                        
                        # if hasattr(slice[0x10, 0x10])
                        # print(f'slice thickness = {slice[0x18, 0x50]}')
                    # series = tmpList
                    # series.sort(key = lambda x: float(x.ImagePositionPatient[2]))
        # print(f'total {count} slices has no parameter "ImagePositionPatient"')
            # seriesID = fileData.SeriesInstanceUID
            # if seriesID not in dicSeries.keys():
            #     dicSeries[seriesID] = []
                
            # dicSeries[seriesID].append(fileData)
            
        # dicStudy = {}
        # for seriesID, seriesData in dicSeries.items():
        #     studyID = seriesData[0].StudyInstanceUID
        #     if studyID not in dicStudy.keys():
        #         dicStudy[studyID] = {}
        #     dicStudy[studyID][seriesID] = seriesData
        
        # dicPatient = {}
        # for studyID, studyData in dicStudy.items():
        #     # if len(studyData) > 0:
        #     patientID = list(studyData.values())[0].PatientID
        #     if patientID not in dicPatient.keys():
        #         dicPatient[patientID] = {}
        #     dicPatient[patientID][studyID] = studyData
            
        
        # return metadata, metadataSeriesNum, metadataFileList
        return dicPatient
       
        ############################################################################################
    def SelectDataFromID(self, idPatient:str, idStuy:str, idSeries:str, index:int = 0):
        patient = self.dicPatient.get(idPatient)
        if not patient:
            QMessageBox.critical(None, 'DICOM ERROR', f'not found patient ID = [{idPatient}]')
            return None
        
        study = patient.get(idStuy)
        if not study:
            QMessageBox.critical(None, 'DICOM ERROR', f'not found study ID = [{idStuy}]')
            return None
        
        series = study.get(idSeries)
        if not series:
            QMessageBox.critical(None, 'DICOM ERROR', f'not found series ID = [{idSeries}]')
            return None
        
        index = max(0, min(index, 1))
        # if index >= len(self.currentSeries):
        #     self.currentSeries.append(series)
        # else:
        #     self.currentSeries[index] = series
        self.currentSeries[index] = series
        
    def GetDataFromID(self, idPatient:str, idStuy:str, idSeries:str, index:int = 0):
        self.SelectDataFromID(idPatient, idStuy, idSeries, index)
        return self.GetData(self.currentSeries)
        
        
    def GetDataFromIndex(self,nPatient:int, nStudy:int, nSeries:int):
        patient:dict = list(self.dicPatient.values())[nPatient]
        study:dict = list(patient.values())[nStudy]
        series:dict = list(study.values())[nSeries]
        
        # self.currentSeries = series
        return self.GetData(series)
    
    def GetSlice(self, idPatient:str, idStuy:str, idSeries:str, index:int, nSlice:int):
        patient = self.dicPatient.get(idPatient)
        if not patient:
            QMessageBox.critical(None, 'DICOM ERROR', f'not found patient ID = [{idPatient}]')
            return None
        
        study = patient.get(idStuy)
        if not study:
            QMessageBox.critical(None, 'DICOM ERROR', f'not found study ID = [{idStuy}]')
            return None
        
        series = study.get(idSeries)
        if not series:
            QMessageBox.critical(None, 'DICOM ERROR', f'not found series ID = [{idSeries}]')
            return None
        
        listSeries = series['data']
        
        slice = []
        if nSlice >= len(listSeries):
            dataSet = listSeries[0]
            if nSlice > len(dataSet.pixel_array):
                logger.warning('Invalid nSlice of Dicom')
                return None
            
            if self.rescaleIntercept and self.rescaleSlope:
                slice.append(dataSet.pixel_array[nSlice] * self.rescaleSlope + self.rescaleIntercept)
            else:
                slice.append(dataSet.pixel_array[nSlice])
            slice = slice[0]
        else:
            dataSet = listSeries[nSlice]
            
            rescaleIntercept = None
            rescaleSlope     = None
            elem = self.FindTag(dataSet, (0x28, 0x1052))
            if elem is not None:
                rescaleIntercept = elem
                
            elem = self.FindTag(dataSet, (0x28, 0x1053))
            if elem is not None:
                rescaleSlope = elem
            
            
            if hasattr(dataSet, 'pixel_array'):
                if rescaleIntercept and rescaleSlope:
                    slice = (dataSet.pixel_array * rescaleSlope + rescaleIntercept)
                else:
                    slice = (dataSet.pixel_array)
                
            slice = np.array(slice).astype(np.int16)
        return slice
    
    def GetNumOfSelectedSeries(self):
        return len(self.currentSeries)
        
    def GetData(self, series = None, index:int = 0):
        if self.currentSeries is None and series is None:
            return None
        elif series is None:
            # if index >= len(self.currentSeries):
            #     return None
            series = self.currentSeries.get(index)
            if series is None:
                return None
            
        listSeries:list = series['data']
        
        images = []
        spacing = []
        
        dataSet = listSeries[0]
        # tag = (0x28, 0x30)
        # elem = self.FindTag(dataSet, tag)
        # if elem is not None:
        #     spacing = list(elem)
        
        # tag = (0x18, 0x50)
        # elem = self.FindTag(dataSet, tag)
        # if elem is not None:
        #     spacing.append(elem)
        # else:
        #     tag = (0x18, 0x88)
        #     elem = self.FindTag(dataSet, tag)
        #     if elem is not None:
        #         spacing.append(elem)
        spacingXY = series.get('spacingXY')
        spacingZ  = series.get('spacingZ')
        if not spacingXY or not spacingZ:
            QMessageBox.critical(None, 'DICOM TAG MISSING', 'missing tag [Spacing]')
            return None
        spacing:list = spacingXY[:]
        spacing = np.append(spacing, spacingZ)
        # print(f'spacingXY = {spacingXY}, spacingZ = {spacingZ}')
            
        elem = self.FindTag(dataSet, (0x28, 0x1050))
        if elem is not None:
            self.windowLevel = elem
            
        elem = self.FindTag(dataSet, (0x28, 0x1051))
        if elem is not None:
            self.windowWidth = elem
            
        elem = self.FindTag(dataSet, (0x28, 0x1052))
        if elem is not None:
            self.rescaleIntercept = elem
            
        elem = self.FindTag(dataSet, (0x28, 0x1053))
        if elem is not None:
            self.rescaleSlope = elem
            
        for dataSet in listSeries:
            if hasattr(dataSet, 'pixel_array'):
                if self.rescaleIntercept and self.rescaleSlope:
                    images.append(dataSet.pixel_array * self.rescaleSlope + self.rescaleIntercept)
                else:
                    images.append(dataSet.pixel_array)
            
        images = np.array(images).astype(np.int16)
        
        if len(images.shape) > 3:
            logger.info(f'this is multi-frame dicom')
            images = images[0] 
        
        imageOrientation = series.get('orientation')
        rotate_matrix = np.identity(3)
        if imageOrientation is not None:
            bGantryTilt = False
            for angle in imageOrientation:
                if abs(angle - round(angle)) > 0.001:
                    logger.warning('dicom have a gantry tilt')
                    bGantryTilt = True
                
            if not bGantryTilt:     
                imageOrientation = np.round(imageOrientation)
                row_cosines = np.array(imageOrientation[:3])
                col_cosines = np.array(imageOrientation[3:])
                
                z_axis = np.cross(row_cosines, col_cosines)
                z_axis /= np.linalg.norm(z_axis)
                
                rotate_matrix = np.array([row_cosines, col_cosines, z_axis]).T
                rotate_matrix = np.linalg.inv(rotate_matrix)
                
                r = R.from_matrix(rotate_matrix)
                rot_times = (r.as_euler('zxz', True) / 90).astype(int)
                logger.debug(f'image orientation is {imageOrientation}')
                
                if rot_times[2] != 0:
                    #rotate z axis
                    bChanged = True
                    images, spacing = self._RotateImage(images, spacing, 'z', rot_times[2])
                
                if rot_times[1] != 0:
                    # rotate x axis
                    bChanged = True
                    images, spacing = self._RotateImage(images, spacing, 'x', rot_times[1])
                
                if rot_times[0] != 0:
                    # rotate z axis
                    bChanged = True
                    images, spacing = self._RotateImage(images, spacing, 'z', rot_times[0])
                    
        self.arrImage = images.copy()
        dimension = np.array(images.shape)[::-1] # z,y,x to x,y,z
        
        importer = vtk.vtkImageImport()
        importer.SetDataScalarTypeToShort()
        importer.SetNumberOfScalarComponents(1)
        importer.SetWholeExtent(0, images.shape[2] - 1, 0, images.shape[1] - 1, 0, images.shape[0] - 1)
        importer.SetDataExtentToWholeExtent()
        importer.SetDataSpacing(spacing)
        importer.SetDataOrigin(0, 0, 0)
        images = images.flatten()
        importer.CopyImportVoidPointer(images.data, images.nbytes)
        importer.Update()
        self.importer = importer
        
        imageData:vtk.vtkImageData = importer.GetOutput()
        # spacing_rotated = np.round(spacing_rotated, 6)
        return imageData, spacing, dimension, listSeries
            
    def FindTag(self, dataSet:pydicom.Dataset, tag:tuple, layer = 0):
        if tag in dataSet:
            return dataSet[tag].value
        
        foundElem = None
        for elem in dataSet:
            if elem.VR == 'SQ':
                #Sequence
                for item in elem.value:
                    foundElem = self.FindTag(item, tag, layer + 1)
                    if foundElem is not None:
                        # print(f'found element [{foundElem}] in SQ [{elem.name}]')
                        return foundElem
        
        # if layer == 0 and foundElem is None:
        #     print(f'Tag[{tag}] not found')
        return foundElem
            
    
    def printSequence(self, data, outF, layer = 0):
        prefix = ' ' * 4
        for elem in data:
            # if layer > 0:
            #     outF.writelines(prefix * layer + 'item = ')
                
            if elem.VR == 'SQ':
                # outF.writelines(prefix * layer + f'{len(elem.value)} dataset in SQ\n')
                # outF.writelines('=' * 100 + '\n')
                outF.writelines(prefix * layer + f'{elem.tag} = {elem.name}\n')
                outF.writelines(prefix * layer + '{\n')
                layer += 1
                # for item in elem.value:
                # print(f'elem value type = {type(elem.value)}')
                
                for item in elem.value:
                    # outF.writelines(f'Dataset name = {item.__name__}')
                    outF.writelines(prefix * layer + f'{len(item)} dataElement in dataset\n')
                    # print(f'item type = {type(item)}')
                    self.printSequence(item, outF, layer + 1)
                layer -= 1
                outF.writelines(prefix * layer + '}\n')
            else:
                outF.writelines(prefix * layer + f'{elem}\n')
                        
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
        seriesNumberLabel = np.unique(metadataSeriesNum)
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
        # try:
        totalSlice = len(imageTag)
        for sliceNum in range(totalSlice-1):
            if imageTag[sliceNum].pixel_array.shape==imageTag[sliceNum+1].pixel_array.shape:
                image.append(imageTag[sliceNum].pixel_array)
                self.signalProcess.emit(sliceNum / totalSlice)
            else:
                
                image = 0
                break
        image.append(imageTag[sliceNum+1].pixel_array)
        # except:
        #     image = 0
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
    
"registration function"
class REGISTRATION(QObject):
    signalProgress = pyqtSignal(float, str)
    
    index = 0
    def __init__(self):
        super().__init__()
        self.PlanningPath = []
    
    def TransformationMatrix(self, ballCenterMm):
        """calculate registration transformation matrix

        Args:
            ballCenterMm (_numpy.array_): ball center in mm (candidates matched)

        Returns:
            TransformationMatrix(_numpy.array_): numpy.dot(R_y,R_z) Transformation Matrix
        """
        "ball_center_mm(0,:);   origin"
        "ball_center_mm(1,:);   x axis"
        "ball_center_mm(2,:);   y axis"
        ## 計算球的向量 ############################################################################################
        ball_vector_x = ballCenterMm[1] - ballCenterMm[0]
        ball_vector_y = ballCenterMm[2] - ballCenterMm[0]
        ############################################################################################
        "create new coordinate"
        ## 定義 xyz 軸向量 ############################################################################################
        vectorZ = np.array(np.cross(ball_vector_x, ball_vector_y))
        vectorX = np.array(ball_vector_x)
        vectorY = np.array(np.cross(vectorZ,vectorX))
        new_vector = np.array([vectorX,vectorY,vectorZ])
        ############################################################################################
        ### 公式5
        "calculate unit vector"
        ## 計算 xyz 軸的單位向量, 得出選轉矩陣 ############################################################################################
        unit_new_vector = []
        for vector in new_vector:
            # unit_new_vector.append(vector / self.__GetNorm(vector))
            unit_new_vector.append(vector / np.linalg.norm(vector))
        ############################################################################################

        return np.array(unit_new_vector)
    
    def GetBallSection(self,candidateBall):
        """calculate Transformation Matrix

        Args:
            candidateBall (_dictionary_): candidate ball center 
            same as dictionaryPoint (_dictionary_): point, key(Px,Py,Pz,Pr):numpy.array([[Px,Py,Pz,Pr]...])

        Returns:
            numpy.array([showAxis, showSlice]) (_numpy.array_): show Axis(x=0, y=1, z=2), show Slice/section (slice number)
        
        """
        ## 自動顯示要給使用者選取球的切面 ############################################################################################
        tmpMin = np.min(candidateBall,0)
        tmpMax = np.max(candidateBall,0)
        tmpMean = np.mean(candidateBall,0)
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
        return np.array([showAxis, showSlice])
    
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
        hypotenuse = math.sqrt(np.square(shortSide) + np.square(longSide))
        # error.append(abs(self.__GetNorm(ball[1]-ball[2])-hypotenuse))
        # error.append(abs(self.__GetNorm(ball[0]-ball[1])-shortSide))
        # error.append(abs(self.__GetNorm(ball[0]-ball[2])-longSide))
        error.append(abs(np.linalg.norm(ball[1]-ball[2])-hypotenuse))
        error.append(abs(np.linalg.norm(ball[0]-ball[1])-shortSide))
        error.append(abs(np.linalg.norm(ball[0]-ball[2])-longSide))
        ############################################################################################
        return [np.min(error),np.max(error),np.mean(error)]
    
    def __GetNorm(self, V):
        """get norm

        Args:
            V (_numpy.array_): vector

        Returns:
            d (_number_): (float)
        """
        ## 計算 norm 值, 自動辨識3維向量或是2維向量 ############################################################################################
        if V.shape[0] == 3:
            d = math.sqrt(np.square(V[0])+np.square(V[1])+np.square(V[2]))
        elif V.shape[0] == 2:
            d = math.sqrt(np.square(V[0])+np.square(V[1]))
        else:
            logger.debug("GetNorm() error")
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
        down_ = 100
        up_ = 300      ## 300~ -800變成白色
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
        logger.debug("ThresholdFilter() error")
        ############################################################################################
        return
    def _ClassifyBalls(self, *lstCentroid:list):
        centroids = np.concatenate(lstCentroid, axis = 0)
        
        # 過濾
        groups = []
        visited = set()
        
        # 找出同一顆球的圓心
        # 只提取 xyz 部分
        xyz_points = centroids[:, :3]

        # 計算距離
        distances = pdist(xyz_points)

        # 距離轉方陣
        distance_matrix = squareform(distances)

        # 距離閾值
        distance_threshold = 20

        
        for i in range(distance_matrix.shape[0] - 1):
            if i in visited:
                continue
            group = set([i])
            for j in range(i + 1, distance_matrix.shape[1]):
                if distance_matrix[i, j] < distance_threshold and i != j:
                    group.add(j)
            groups.append(group)
            visited.update(group)
                
        balls = [[centroids[i] for i in group] for group in groups if len(group) > 5]     
        balls = [sorted(ball, key = lambda x:(-x[3], x[0], x[1], x[2])) for ball in balls]
        balls.sort(key = lambda x:(-len(x), x[0][0]))
       
        for i, ball in enumerate(balls):
            balls[i] = np.mean(ball, axis = 0)
        
        return balls
                
    ### 公式7
    def _FindBallXY(self, imageHu):
        """scan XY plane to  find ball centroid,
            May find candidate ball and non-candidates

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)

        Returns:
            result_centroid (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball
        """

        imageHuThr = self.ThresholdFilter(imageHu)
        src_tmp = np.uint8(imageHuThr)
        
        resultCentroid_xy = []
        
        "coefficient"
        param1 = 50
        param2 = 20
        "Radius range: [3mm ~ (21/2)+3mm]"
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
            black_image_2 = np.zeros(shape, np.uint8)
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
            ### 公式12
            ## 用Hough Circles找球心跟半徑 ############################################################################################
            "use Hough Circles to find radius and center of circle"
            circles = cv2.HoughCircles(black_image_2, cv2.HOUGH_GRADIENT, 1, 20,
                                        param1=param1, param2=param2,
                                        minRadius=MIN_RADIUS, maxRadius=maxRadius)
            ############################################################################################
            ## 質心與球心平面距離不超過2的留下當作候選人 ############################################################################################
            if circles is not None and centroid is not None:
                "Intersection"
                "centroid = group of Centroid"
                "circles = group of hough circle"
                for i in centroid:
                    for j in circles[0, :]:
                        distance = math.sqrt((i[0]-j[0])**2+(i[1]-j[1])**2)
                        if distance < IDENTIFY_MARKER_TOLERENCE and j[2] > 6:
                                Px = j[0]
                                Py = j[1]
                                Pz = z
                                Pr = j[2]
                                resultCentroid_xy.append([Px,Py,Pz,Pr])
                            
            
            cv2.destroyAllWindows()
            ############################################################################################
        return np.array(resultCentroid_xy)
    
    def __FindBallXY(self, imageHu):
        """scan XY plane to  find ball centroid,
            May find candidate ball and non-candidates

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)

        Returns:
            result_centroid (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball
        """

        imageHuThr = self.ThresholdFilter(imageHu)
        src_tmp = np.uint8(imageHuThr)
        
        resultCentroid_xy = []
        
        "coefficient"
        param1 = 50
        param2 = 20
        "Radius range: [3mm ~ (21/2)+3mm]"
        maxRadius=int(21/2)+3
        
        "find circle, radius and center of circle in each DICOM image"
        # 輸出輪廓測試
        # path = os.path.join(os.getcwd(), 'output', str(REGISTRATION.index))
        # try:
        #     os.makedirs(path)
        # except FileExistsError:
        #     pass
        # REGISTRATION.index += 1
   
        for z in range(src_tmp.shape[0]):
            ## 找輪廓與質心 ############################################################################################
            ### 公式8
            "draw contours"
            contours, hierarchy = cv2.findContours(src_tmp[z,:,:],
                                                cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)
            "create an all black picture to draw contour"
            shape = (src_tmp.shape[1], src_tmp.shape[2], 1)
            black_image_2 = np.zeros(shape, np.uint8)
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
            
            # filename = f'{z:02}.jpg'
            # filepath = os.path.join(path, filename)
            # cv2.imwrite(filepath, black_image_2, [cv2.IMWRITE_JPEG_QUALITY, 80])
            
            ############################################################################################
            ### 公式12
            ## 用Hough Circles找球心跟半徑 ############################################################################################
            "use Hough Circles to find radius and center of circle"
            circles = cv2.HoughCircles(black_image_2, cv2.HOUGH_GRADIENT, 1, 20,
                                        param1=param1, param2=param2,
                                        minRadius=MIN_RADIUS, maxRadius=maxRadius)
                
            # outputImage = np.stack((black_image_2, ) * 3, axis = -1, dtype = np.uint8)
            # if circles is not None:
            #     circles = np.uint16(np.around(circles))
            #     for c in circles[0]:
            #         cv2.circle(outputImage, (c[0], c[1]), c[2], (0, 255, 0), 2)
                    
            #     filename = f'{z:02}.jpg'
            #     filepath = os.path.join(path, filename)
                
            #     cv2.imwrite(filepath, outputImage, [cv2.IMWRITE_JPEG_QUALITY, 80])
            
            ############################################################################################
            ## 質心與球心平面距離不超過2的留下當作候選人 ############################################################################################
            if circles is not None and centroid is not None:
                "Intersection"
                "centroid = group of Centroid"
                "circles = group of hough circle"
                for i in centroid:
                    for j in circles[0, :]:
                        distance = math.sqrt((i[0]-j[0])**2+(i[1]-j[1])**2)
                        if distance < IDENTIFY_MARKER_TOLERENCE:
                                Px = i[0]
                                Py = i[1]
                                Pz = z
                                Pr = j[2]
                                resultCentroid_xy.append([Px,Py,Pz,Pr])
                            
            
            cv2.destroyAllWindows()
            ############################################################################################
        return np.array(resultCentroid_xy)
  
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
        pointMatrixSorted = np.array(sorted(pointMatrix, key=lambda tmp: (int(tmp[0]), int(tmp[1]), int(tmp[2]))))
        for i in range(len(pointMatrixSorted)-1):
            P1 = pointMatrixSorted[i]
            P2 = pointMatrixSorted[i+1]
            distanceXY = math.sqrt(np.square(P1[0]-P2[0])+np.square(P1[1]-P2[1]))
            distanceXYZ = math.sqrt(np.square(P1[0]-P2[0])+np.square(P1[1]-P2[1])+np.square(P1[2]-P2[2]))
            # distanceXY = np.linalg.norm(P1[:2] - P2[:2])
            # distanceXYZ = np.linalg.norm(P1 - P2)
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
                distanceXY = math.sqrt(np.square(P1[0]-P2[0])+np.square(P1[1]-P2[1]))
                # distanceXY = np.linalg.norm(P1[:2]-P2[:2])
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
            valueSorted = np.array(sorted(value, key=lambda tmp: (tmp[2])))
            
            for row in valueSorted:
                added = False
                for key_i, category in categories.items():
                    "檢查是否與現有組別的第一個元素之距離或震幅不超過 DZ"
                    dz1 = abs(row[2] - category[0][2])
                    dz2 = abs(row[2] - category[-1][2])
                    # distanceXY = math.sqrt(numpy.square(row[0]-category[0][0])+numpy.square(row[1]-category[0][1]))
                    distanceXY = np.linalg.norm(np.array(row[:2]) - category[0][:2])
                    if dz1 <= DZ and dz2 <= DZ and distanceXY < 3:
                        category.append(row)
                        added = True
                        break
                if not added:
                    # categories.update({tuple(row):np.array([row])})
                    categories.update({tuple(row):[row]})
        ############################################################################################
        "把每一組的 key 換成組內的平均點"
        ## 把每一組的 key 換成組內的平均點 ############################################################################################
        dictionary = {}
        for key in categories:
            tmpValue = np.array(categories[key])
            Px = np.mean(tmpValue[:,0])
            Py = np.mean(tmpValue[:,1])
            Pz = np.mean(tmpValue[:,2])
            tmpKey = tuple([Px,Py,Pz])
            dictionary.update({tmpKey:tmpValue})
        ############################################################################################
        return dictionary
    ### 公式7
    def _FindBallYZ(self, imageHu):
        """scan YZ plane to  find ball centroid,
            May find candidate ball and non-candidates

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)

        Returns:
            result_centroid (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball
        """
        imageHuThr = self.ThresholdFilter(imageHu)
        src_tmp = np.uint8(imageHuThr)
        
        resultCentroid_yz = []
        
        "coefficient"
        ratio = 3
        low_threshold = 15
        "Radius range: [3mm ~ (21/2)+3mm]"
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
            black_image_2 = np.zeros(shape, np.uint8)
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
                                        minRadius=MIN_RADIUS, maxRadius=maxRadius)
            ############################################################################################
            ## 質心與球心平面距離不超過2的留下當作候選人 ############################################################################################
            if circles is not None and centroid is not None:
                "Intersection"
                "centroid = group of Centroid"
                "circles = group of hough circle"
                for i in centroid:
                    for j in circles[0, :]:
                        distance = math.sqrt((i[0]-j[0])**2+(i[1]-j[1])**2)
                        if distance < IDENTIFY_MARKER_TOLERENCE and j[2] > 6:
                            Px = x
                            Py = j[0]
                            Pz = j[1]
                            Pr = j[2]
                            resultCentroid_yz.append([Px,Py,Pz,Pr])
            cv2.destroyAllWindows()
            ############################################################################################
        return np.array(resultCentroid_yz)
    
    def __FindBallYZ(self, imageHu):
        """scan YZ plane to  find ball centroid,
            May find candidate ball and non-candidates

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)

        Returns:
            result_centroid (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball
        """
        imageHuThr = self.ThresholdFilter(imageHu)
        src_tmp = np.uint8(imageHuThr)
        
        resultCentroid_yz = []
        
        "coefficient"
        ratio = 3
        low_threshold = 15
        "Radius range: [3mm ~ (21/2)+3mm]"
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
            black_image_2 = np.zeros(shape, np.uint8)
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
                                        minRadius=MIN_RADIUS, maxRadius=maxRadius)
            ############################################################################################
            ## 質心與球心平面距離不超過2的留下當作候選人 ############################################################################################
            if circles is not None and centroid is not None:
                "Intersection"
                "centroid = group of Centroid"
                "circles = group of hough circle"
                for i in centroid:
                    for j in circles[0, :]:
                        distance = math.sqrt((i[0]-j[0])**2+(i[1]-j[1])**2)
                        if distance < IDENTIFY_MARKER_TOLERENCE:
                            Px = x
                            Py = i[0]
                            Pz = i[1]
                            Pr = j[2]
                            resultCentroid_yz.append([Px,Py,Pz,Pr])
            cv2.destroyAllWindows()
            ############################################################################################
        return np.array(resultCentroid_yz)

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
                # distance = np.linalg.norm(np.array(p1[1:]) - np.array(key[1:]))
                # dx = math.sqrt(numpy.square(p1[0]-key[0]))
                dx = abs(p1[0] - key[0])
                if distance < 5 and dx < 31:
                    tmpKey = key
                    tmpValue = np.array([p1])
                    addFlage = True
            if addFlage:
                value = np.append(interestPoint.get(tmpKey), tmpValue, axis=0)
                interestPoint.update({tmpKey:value})
                tmpValue = []
        ############################################################################################
        return interestPoint
    ### 公式7
    def _FindBallXZ(self, imageHu):
        """scan XZ plane to  find ball centroid,
            May find candidate ball and non-candidates

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)

        Returns:
            result_centroid (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball
        """
        imageHuThr = self.ThresholdFilter(imageHu)
        src_tmp = np.uint8(imageHuThr)
        
        resultCentroid_xz = []
        
        "coefficient"
        ratio = 3
        low_threshold = 15
        "Radius range: [3mm ~ (21/2)+3mm]"
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
            black_image_2 = np.zeros(shape, np.uint8)
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
                                        minRadius=MIN_RADIUS, maxRadius=maxRadius)
            ############################################################################################
            ## 質心與球心平面距離不超過2的留下當作候選人 ############################################################################################
            if circles is not None and centroid is not None:
                "Intersection"
                "centroid = group of Centroid"
                "circles = group of hough circle"
                for i in centroid:
                    for j in circles[0, :]:
                        distance = math.sqrt((i[0]-j[0])**2+(i[1]-j[1])**2)
                        if distance < IDENTIFY_MARKER_TOLERENCE and j[2] > 6:
                            Px = j[0]
                            Py = y
                            Pz = j[1]
                            Pr = j[2]
                            resultCentroid_xz.append([Px,Py,Pz,Pr])
            cv2.destroyAllWindows()
            ############################################################################################
        return np.array(resultCentroid_xz)
    
    def __FindBallXZ(self, imageHu):
        """scan XZ plane to  find ball centroid,
            May find candidate ball and non-candidates

        Args:
            imageHu (_numpy.array_): image in Hounsfield Unit (Hu)

        Returns:
            result_centroid (_list_): [Px,Py,Pz,Pr], ball center and radius of candidate ball and non-candidates ball
        """
        imageHuThr = self.ThresholdFilter(imageHu)
        src_tmp = np.uint8(imageHuThr)
        
        resultCentroid_xz = []
        
        "coefficient"
        ratio = 3
        low_threshold = 15
        "Radius range: [3mm ~ (21/2)+3mm]"
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
            black_image_2 = np.zeros(shape, np.uint8)
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
                                        minRadius=MIN_RADIUS, maxRadius=maxRadius)
            ############################################################################################
            ## 質心與球心平面距離不超過2的留下當作候選人 ############################################################################################
            if circles is not None and centroid is not None:
                "Intersection"
                "centroid = group of Centroid"
                "circles = group of hough circle"
                for i in centroid:
                    for j in circles[0, :]:
                        distance = math.sqrt((i[0]-j[0])**2+(i[1]-j[1])**2)
                        if distance < IDENTIFY_MARKER_TOLERENCE:
                            Px = i[0]
                            Py = y
                            Pz = i[1]
                            Pr = j[2]
                            resultCentroid_xz.append([Px,Py,Pz,Pr])
            cv2.destroyAllWindows()
            ############################################################################################
        return np.array(resultCentroid_xz)

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
                # distance = np.linalg.norm(np.array(p1[::2]) - np.array(key[::2]))
                # dy = math.sqrt(numpy.square(p1[1]-key[1]))
                dy = abs(p1[1] - key[1])
                if distance < 5 and dy < 31:
                    tmpKey = key
                    tmpValue = np.array([p1])
                    addFlage = True
            if addFlage:
                value = np.append(interestPoint.get(tmpKey), tmpValue, axis=0)
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
            fNum = tmp - int(tmp)
            strNum = str(fNum)
            
            if fNum > 0 and strNum != '0.5':
                array.append(tmp)
            
        if len(array) > 0:
            return np.mean(array,0)
        else:
            return 0
        ############################################################################################
        # return tmpPoint

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
        return np.array(resultPoint)
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
        hypotenuse = math.sqrt(np.square(shortSide) + np.square(longSide))
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
    def GetBallAuto2(self, imageHu, spacing):
        ## resize imageHu, 變成每個 pixel 相距 1 mm ############################################################################################
        
        interpolation_method = None
        if spacing[0] < 1 and spacing[1] < 1:
            interpolation_method = cv2.INTER_AREA
        elif spacing[0] > 1 and spacing[1] > 1:
            interpolation_method = cv2.INTER_CUBIC
        elif spacing[0] != 1 and spacing[0] != 1:
            interpolation_method = cv2.INTER_LINEAR
            
        if interpolation_method is not None:
            imageHuMm_tmp_xyz = [
                cv2.resize(imageHu[z, :, :], dsize=None, fx=spacing[0], fy=spacing[1], interpolation=interpolation_method)
                for z in range(imageHu.shape[0])
            ]
            
        self.signalProgress.emit(0.05, 'registrator identifying...')

        imageHuMm = np.array(imageHuMm_tmp_xyz)

        if spacing[2] < 1:
            interpolation_method = cv2.INTER_AREA
        elif spacing[2] > 1:
            interpolation_method = cv2.INTER_CUBIC
        else:
            interpolation_method = None
            
            
        new_shape = (imageHuMm.shape[0], imageHuMm.shape[1], int(imageHuMm.shape[2] * spacing[2]))
        imageHuMm_resized = np.zeros(new_shape, dtype=np.int16)
        
        if interpolation_method is not None:
            for y in range(imageHuMm.shape[1]):
                resized_slice = cv2.resize(imageHuMm[:,y,:],dsize=None,fx=1,fy=spacing[2],interpolation = interpolation_method)
                imageHuMm_resized[:, y, :] = resized_slice
            
            imageHuMm = imageHuMm_resized
            
        self.signalProgress.emit(0.1, 'registrator identifying...')
        ############################################################################################
        ## 取得候選人球心 ############################################################################################
        resultCentroid_xy = self._FindBallXY(imageHuMm)
        self.signalProgress.emit(0.34, 'registrator identifying...')
        resultCentroid_yz = self._FindBallYZ(imageHuMm)
        self.signalProgress.emit(0.68, 'registrator identifying...')
        resultCentroid_xz = self._FindBallXZ(imageHuMm)
        self.signalProgress.emit(0.99, 'registrator identify completed')
        
        try:
            balls = self._ClassifyBalls(resultCentroid_xy, resultCentroid_yz, resultCentroid_xz)
            self.signalProgress.emit(0.5, 'classify reference balls')
            reference = self.IdentifyPoint(balls)
        except Exception as msg:
            logger.error(msg)
            
        if not reference:
            return False, None
        else:
            self.signalProgress.emit(1, 'compeleted reference classified')
            refs = np.concatenate(list(reference.values()), axis = 0)
            logger.debug(f'reference = \n{refs}')
            return True, reference
            
        # # 創建一個空白的二值影像數組
        # binary_image = np.zeros_like(image, dtype=np.uint8)

        # # 將範圍內的像素設置為白色
        # binary_image[(image >= -800) & (image <= 300)] = 1
        
        # output_image = np.stack((binary_image, ) * 3, axis = -1, dtype = np.uint8)
        # for i, region in enumerate(output_image):
        #     path = os.path.join(os.getcwd(), 'output', '2', f'{i:03}.jpg')
        #     cv2.imwrite(path, region, [cv2.IMWRITE_JPEG_QUALITY, 80])
        
        # # 標記連通區域
        # labeled_image, num_features = label(binary_image)

        
        
        # # 提取區域特徵
        # regions = regionprops(labeled_image)
        
        # # 篩選球狀物體並找出其球心
        # target_radius = 10
        # radius_tolerance = 2  # 調整容許的半徑誤差
        # target_volume = 4/3 * np.pi * (target_radius ** 3)
        # volume_tolerance = 0.1 * target_volume
        # spherical_objects = []

        # for region in regions:
        #     # 獲取該區域的邊界框
        #     min_point = np.array(region.bbox[:3])
        #     max_point = np.array(region.bbox[3:])
        #     region_radius = (max_point - min_point) / 2
            
        #     if region.area > target_volume and np.abs(region.area - target_volume) <= target_volume:
        #         # 檢查是否近似於球體
        #         logger.debug(region.area)
            
        # # 獲取球心
        # for obj in spherical_objects:
        #     centroid = obj.centroid
        #     print(f"球心坐標: {centroid}")
            
    def GetBallAuto(self, imageHu, spacing, imageTag):
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
        
        pixel2Mm = np.abs(spacing)
        interpolation_method = None
        if pixel2Mm[0] < 1 and pixel2Mm[1] < 1:
            interpolation_method = cv2.INTER_AREA
        elif pixel2Mm[0] > 1 and pixel2Mm[1] > 1:
            interpolation_method = cv2.INTER_CUBIC
        elif pixel2Mm[0] != 1 and pixel2Mm[0] != 1:
            interpolation_method = cv2.INTER_LINEAR
            
        if interpolation_method is not None:
            imageHuMm_tmp_xyz = [
                cv2.resize(imageHu[z, :, :], dsize=None, fx=pixel2Mm[0], fy=pixel2Mm[1], interpolation=interpolation_method)
                for z in range(imageHu.shape[0])
            ]
            
        self.signalProgress.emit(0.05, 'registrator identifying...')
        
        imageHuMm = np.array(imageHuMm_tmp_xyz)
        
        if pixel2Mm[2] < 1:
            interpolation_method = cv2.INTER_AREA
        elif pixel2Mm[2] > 1:
            interpolation_method = cv2.INTER_CUBIC
        else:
            interpolation_method = None
            
            
        new_shape = (imageHuMm.shape[0], imageHuMm.shape[1], int(imageHuMm.shape[2] * pixel2Mm[2]))
        imageHuMm_resized = np.zeros(new_shape, dtype=np.int16)
        
        if interpolation_method is not None:
            for y in range(imageHuMm.shape[1]):
                resized_slice = cv2.resize(imageHuMm[:,y,:],dsize=None,fx=1,fy=pixel2Mm[2],interpolation = interpolation_method)
                imageHuMm_resized[:, y, :] = resized_slice
            
            imageHuMm = imageHuMm_resized
                
        
            
        self.signalProgress.emit(0.1, 'registrator identifying...')
        ############################################################################################
        ## 取得候選人球心 ############################################################################################
        resultCentroid_xy = self.__FindBallXY(imageHuMm)
        self.signalProgress.emit(0.17, 'registrator Classifying...')
        dictionaryPoint = self.__ClassifyPointXY(resultCentroid_xy)
        self.signalProgress.emit(0.34, 'registrator identifying...')
        resultCentroid_yz = self.__FindBallYZ(imageHuMm)
        self.signalProgress.emit(0.51, 'registrator Classifying...')
        dictionaryPoint = self.__ClassifyPointYZ(resultCentroid_yz, dictionaryPoint)
        self.signalProgress.emit(0.68, 'registrator identifying...')
        resultCentroid_xz = self.__FindBallXZ(imageHuMm)
        self.signalProgress.emit(0.85, 'registrator Classifying...')
        dictionaryPoint = self.__ClassifyPointXZ(resultCentroid_xz, dictionaryPoint)
        self.signalProgress.emit(0.99, 'registrator identify completed')
        
        pointMatrixSorted_xy = np.array(sorted(resultCentroid_xy, key=lambda tmp: (int(tmp[0]), int(tmp[1]), int(tmp[2]))))
        pointMatrixSorted_yz = np.array(sorted(resultCentroid_yz, key=lambda tmp: (int(tmp[1]), int(tmp[2]), int(tmp[0]))))
        pointMatrixSorted_xz = np.array(sorted(resultCentroid_xz, key=lambda tmp: (int(tmp[0]), int(tmp[2]), int(tmp[1]))))
        
        averagePoint = self.__AveragePoint(dictionaryPoint)
        ############################################################################################
        ## 計算得出病人坐標系下的球心 ############################################################################################
        resultPoint = []
        
        count = len(averagePoint)
        if count == 0:
            count = 1
        nStep = 1 / count
        nProgress = 0
        self.signalProgress.emit(0, 'calculating registrator position...')
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
                
                nProgress = min(nProgress + nStep, 0.9)
                self.signalProgress.emit(nProgress, 'calculating registrator position...')
            except:
                pass
        
        self.signalProgress.emit(0.9, 'calculating axis...')
        ## 辨識定位球方向 ############################################################################################
        try:
            markers = self.IdentifyPoint(np.array(resultPoint))
            # markers = self.IdentifyPoint(averagePoint)
            self.signalProgress.emit(1, 'registration completed')
        except:
            markers = None
        # print("-------------------------------------------------------------------")
        # print("ball: \n", ball)
        # print("-------------------------------------------------------------------")
        ############################################################################################
        ## 如果 IdentifyPoint 失敗, return 候選人, 為了手動註冊 ############################################################################################
        pointMatrixSorted = np.concatenate((pointMatrixSorted_xy, pointMatrixSorted_yz, pointMatrixSorted_xz), axis = 0)
        if not markers:
            return False, pointMatrixSorted
        # elif ball == []:
        #     return False, pointMatrixSorted
        else:
            logger.info(f'registration balls =')
            for balls in markers.values():
                for ball in balls:
                    logger.info(f'{ball}')
            return True, markers
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
        # ImageOrientationPatient = imageTag[int(point[2])-1].ImageOrientationPatient
        # ImagePositionPatient = imageTag[int(point[2])-1].ImagePositionPatient
        ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        ImagePositionPatient = [0, 0, int(point[2])-1]

        x = point[0]
        y = point[1]
        RowVector = ImageOrientationPatient[0:3]
        ColumnVector = ImageOrientationPatient[3:6]
        X = ImagePositionPatient[0] + x * RowVector[0] + y * ColumnVector[0]
        Y = ImagePositionPatient[1] + x * RowVector[1] + y * ColumnVector[1]
        Z = ImagePositionPatient[2] + x * RowVector[2] + y * ColumnVector[2]
        ############################################################################################
        return np.array([X,Y,Z])
    
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
                P1 = np.array(key)
                P2 = np.array(point)
                # distanceXYZ = math.sqrt(numpy.square(P1[0]-P2[0])+numpy.square(P1[1]-P2[1])+numpy.square(P1[2]-P2[2]))
                distanceXYZ = np.linalg.norm(P1 - P2)
                if distanceXYZ < 15:
                    valueMatrix.append(point)
                    # valueMatrix = np.append(valueMatrix, point)
            dictionaryPoint.update({tuple(key):np.array(valueMatrix)})
        
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
            ball = self.IdentifyPoint(np.array(resultPoint))
        except:
            ball = []
        # print("-------------------------------------------------------------------")
        # print("ball: \n", ball)
        # print("-------------------------------------------------------------------")
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
            planningPath.append(np.dot(regMatrix,(p-originPoint)) + originPoint)
        
        return planningPath
class TracerStyle(vtk.vtkInteractorStyleImage):
    
    def __init__(self):
        self.AddObserver('LeftButtonPressEvent', self.OnLeftButtonPress)
        # self.AddObserver('RightButtonReleaseEvent', self.OnRightButtonRelease)
        # self.AddObserver('LeftButtonReleaseEvent', self.OnLeftButtonRelease)
        
    def OnLeftButtonPress(self, obj, event):
        pass
    
    
    
class ContourInteractorStyle(vtk.vtkInteractorStyle):
    
    def __init__(self, widget:vtk.vtkContourWidget):
        self.contourWidget = widget
        self.AddObserver('LeftButtonPressEvent', self.OnLeftButtonPress)
        # self.AddObserver('RightButtonPressEvent', self.OnRightButtonPress)
        self.AddObserver('RightButtonReleaseEvent', self.OnRightButtonRelease)
        self.AddObserver('LeftButtonReleaseEvent', self.OnLeftButtonRelease)
        self.AddObserver('LeftButtonDoubleClickEvent', self.OnLeftDoubleClickEvent)
        # self.AddObserver('MouseMoveEvent', self.OnMouseMove)
        
        # callback = vtk.vtkImageInteractionCallback()
        # actor = widget.renderer.actorImage
        
        # callback.SetImageReslice()
        
        
    def OnLeftDoubleClickEvent(self, obj, event):
        self.contourWidget.CloseLoop()
    
        
    def OnLeftButtonPress(self, obj, event):
        
        # self.contourWidget.Initialize()
        pass
        # self.contourWidget.SetWidgetState(1)
        
        # self.contourWidget.ProcessEventsOn()
        # self.InvokeEvent(vtk.vtkCommand.LeftButtonReleaseEvent)
        # self.ReleaseFocus()
        # self.InvokeEvent(vtk.vtkWidgetEvent.Select)
        # self.contourWidget.InvokeEvent(vtk.vtkCommand.LeftButtonPressEvent)
        
        
    # def OnRightButtonPress(self, obj, event):
    #     print('R_Press')
    #     # self.contourWidget.InvokeEvent('Reset')
        
    def OnRightButtonRelease(self, obj, event):
        self.contourWidget.CloseLoop()
        # self.contourWidget.Initialize()
        # self.contourWidget.On()
        # iren = self.contourWidget.renderer.GetRenderWindow().GetInteractor()
        # iren.SetInteractorStyle(self.contourWidget.originalIStyle)
        
    def OnLeftButtonRelease(self, obj, event):
        spacing = self.contourWidget.spacing
        dim     = self.contourWidget.dimension
        origin  = self.contourWidget.origin
        
        self.contourWidget.CloseLoop()
        self.contourWidget.rep.GetLinesProperty().SetOpacity(0)
        
        
        polyData = self.contourWidget.GetContourRepresentation().GetContourRepresentationAsPolyData()
        # verts = polyData.GetNumberOfPoints()
        
        cleanFilter = vtk.vtkCleanPolyData()
        cleanFilter.SetInputData(polyData)
        cleanFilter.Update()
        polyDataClean = cleanFilter.GetOutput()
       
        
        extrude = vtk.vtkLinearExtrusionFilter()
        extrude.SetInputData(polyData)
        extrude.SetScaleFactor(2.0)
        extrude.SetVector(0.0, 0.0, 20.0)
        # extrude.SetExtrusionTypeToNormalExtrusion()
        extrude.Update()
        
        polydataCopy = vtk.vtkPolyData()
        polydataCopy.DeepCopy(extrude.GetOutput())
        # self.contourWidget.renderer.polyCopy = polydataCopy
        numOfCopy = polydataCopy.GetNumberOfPoints()
        # extrude.SetInputConnection(fill_holes.GetOutputPort())
        
        
        

        
        mapper = vtk.vtkPolyDataMapper()
        # mapper.SetInputConnection(extrude.GetOutputPort())
        mapper.SetInputData(polydataCopy)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1, 0, 1)
        self.actor = actor

        self.contourWidget.renderer.AddActor(actor)
        # self.contourWidget.renderer.actorImage.VisibilityOff()
        
        # iren = self.contourWidget.iren
        # iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        # iren.Initialize()
        # iren.Start()    
        
        
        
        # center = np.array(dim) * np.array(spacing) * 0.5
        # sphere = vtk.vtkSphereSource()
        # sphere.SetRadius(100)
        # sphere.SetPhiResolution(30)
        # sphere.SetThetaResolution(30)
        # sphere.SetCenter(center)
        # polyData = sphere.GetOutput()
        # sphere.Update()
        
        polyDataToStencil = vtk.vtkPolyDataToImageStencil()
        polyDataToStencil.SetInputData(polydataCopy)
        # polyDataToStencil.SetInputConnection(extrude.GetOutputPort())
        polyDataToStencil.SetOutputOrigin(origin)
        polyDataToStencil.SetOutputSpacing(spacing)
        # polyDataToStencil.SetOutputWholeExtent(whiteImage.GetExtent())
        polyDataToStencil.SetOutputWholeExtent(0, dim[0] - 1, 0, dim[1] - 1, 0, dim[2] - 1)
        polyDataToStencil.Update()
        
        # stencil = vtk.vtkImageStencil()
        # stencil.SetInputData(whiteImage)
        # stencil.SetInputData(self.contourWidget.image)
        # stencil.SetStencilConnection(polyDataToStencil.GetOutputPort())
        # stencil.SetBackgroundValue(0)
        # stencil.Update()
        
        stencilToImage = vtk.vtkImageStencilToImage()
        stencilToImage.SetInputConnection(polyDataToStencil.GetOutputPort())
        stencilToImage.SetInsideValue(255)
        stencilToImage.SetOutsideValue(0)
        stencilToImage.SetOutputScalarTypeToUnsignedChar()
        stencilToImage.Update()
        
        
        source = vtk.vtkImageCanvasSource2D()
        source.SetScalarTypeToUnsignedChar()
        source.SetNumberOfScalarComponents(3)
        source.SetExtent(0, dim[0] - 1, 0, dim[1] - 1, 0, dim[2] - 1)
        # source.SetExtent(0, 512, 0, 512, 0, 0)
        
        source.SetDrawColor(255, 0, 0)
        source.FillBox(0, 512, 0, 512)
        source.Update()
        
        maskSource = vtk.vtkImageCanvasSource2D()
        maskSource.SetScalarTypeToUnsignedChar()
        maskSource.SetNumberOfScalarComponents(1)
        maskSource.SetExtent(0, 512, 0, 512, 0, 0)
               
        maskSource.SetDrawColor(0, 0, 0)
        maskSource.FillBox(0, 512, 0, 512)
        
        maskSource.SetDrawColor(255, 255, 255)
        maskSource.FillBox(100, 120, 100, 120)
        maskSource.Update()
        
        
        
        maskFilter = vtk.vtkImageMask()
        maskFilter.SetInputData(0, self.contourWidget.image)
        # maskFilter.SetInputData(0, source.GetOutput())
        # maskFilter.SetInputData(1, stencilToImage.GetOutput())
        # maskFilter.SetInputConnection(0, source.GetOutputPort())
        maskFilter.SetInputConnection(1, stencilToImage.GetOutputPort())
        # maskFilter.SetInputConnection(1, maskSource.GetOutputPort())
        maskFilter.SetMaskedOutputValue(0, 0, 0)
        maskFilter.Update()
        
        # self.contourWidget.imageView.SetInputData(maskFilter.GetOutput())
        # self.contourWidget.imageView.Render()
        
        ####
        
        actor = vtkImageActor()
        actor.GetMapper().SetInputConnection(maskFilter.GetOutputPort())
        # self.contourWidget.renderer.AddActor(actor)
        
        # mapper = vtk.vtkDataSetMapper()
        # mapper.SetInputConnection(stencil.GetOutputPort())
        # actor = vtkActor()
        # actor.SetMapper(mapper)
        
        
        iren = self.contourWidget.iren
        iren.SetInteractorStyle(self.contourWidget.originalIStyle)
        # iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        # self.contourWidget.renderer.actorImage.GetMapper().SetInputConnection(maskFilter.GetOutputPort())
        self.contourWidget.SetMask(maskFilter.GetOutputPort())
        # self.contourWidget.renderer.actorImage.VisibilityOff()
        self.contourWidget.renderer.SetBackground(0.3, 0.3, 0.3)
        
        
    def OnMouseMove(self, obj, event):
        pass
    

    
    
class ImageAlgorithm():
    image = None
    imageReady = None
    imageBackup = []
    imageOrigin = None
    currentIndex = -1
    currentIndexMask = -1
    extent = None
    spacing = None
    origin = None
    imageOutputPort = None
    scalarType = None
    stencilImage = None
    mask = None
    maskBackup = []
    MAX_BACKUP = 5
    
    def __init__(self):
        self.imageBackup = []
        self.maskBackup = []
        self.currentMask = None
    
    def SetInputData(self, image):
        if isinstance(image, vtk.vtkImageData):
            self.imageBackup = []
            self.maskBackup = []
            self.image = image
            self.saveImage(image)
            self.extent = image.GetExtent()
            self.spacing = image.GetSpacing()
            self.origin = image.GetOrigin()
            self.scalarType = image.GetScalarType()
            
            self.imageOrigin = vtk.vtkImageData()
            self.imageOrigin.DeepCopy(image)
            
            # self.mask = vtk.vtkImageConstant()
            # self.mask.SetOutputScalarType(self.scalarType)
            # self.mask.SetExtent(self.extent)
            # self.mask.SetSpacing(self.spacing)
            
            
        else:
            logger.warning('input data must be vtkImageData type')
                    
    
    
    def ApplyModifiedImage(self):
        
        if self.currentIndex < len(self.imageBackup) - 1:
            self.imageBackup = self.imageBackup[:self.currentIndex + 1]
            
        if self.currentIndexMask < len(self.maskBackup) - 1:
            self.maskBackup = self.maskBackup[:self.currentIndexMask + 1]
        
        self.saveImage(self.imageReady)
        self.image.DeepCopy(self.imageReady)
        self.stencilImage = None
        
    def StepBack(self):
        count = len(self.imageBackup)
        if count > 0:
            bInRange = True
            self.currentIndex -= 1
            self.currentIndexMask -= 1
            if self.currentIndex <= 0:
                self.currentIndex = 0
                bInRange = False
            self.imageReady = self.imageBackup[self.currentIndex]
            self.currentMask = self.maskBackup[self.currentIndexMask]
            self.update()
            return bInRange
        else:
            return False
        
    def StepNext(self):
        count = len(self.imageBackup)
        if count > 0:
            bInRange = True
            self.currentIndex += 1
            self.currentIndexMask += 1
            if self.currentIndex >= count - 1:
                self.currentIndex = count - 1
                bInRange = False
                
            if self.currentIndexMask > len(self.maskBackup) - 1:
                self.currentIndexMask = len(self.maskBackup) - 1
            # print(f'image id = {id(self.imageReady)}')
            # print(f'count = {count}, current index = {self.currentIndex}')
            # for image in self.imageBackup:
            #     print(f'id list = {id(image)}')
            self.imageReady = self.imageBackup[self.currentIndex]
            self.currentMask = self.maskBackup[self.currentIndexMask]
            self.update()
            return bInRange
        else:
            return False
    
    def Inverse(self):
        if not self.imageOrigin or not self.currentMask:
            return
        
        if len(self.imageBackup) == 0:
            return
        
        if len(self.maskBackup) == 0:
            return
        
        # if self.currentIndex < len(self.imageBackup) - 1:
        #     return
        
        imageMath = vtk.vtkImageMathematics()
        # imageMath.SetInput1Data(self.mask)
        imageMath.SetInput1Data(self.currentMask)
        imageMath.SetOperationToMultiplyByK()
        imageMath.SetConstantK(-1)
        imageMath.Update()
        
        self.currentMask = imageMath.GetOutput()
        
        
        
        # scalarType = self.scalarType
        # minValue, maxValue = SCALAR_TYPE_RANGE.get(scalarType, (None, None))
        
        # if minValue is None or maxValue is None:
        #     print('scalarType error')
        #     self.imageOutputPort = None
        #     return False
        
        
        # stencilToImage = vtk.vtkImageStencilToImage()
        # stencilToImage.SetOutputScalarType(scalarType)
        # stencilToImage.SetInputData(self.mask)
        # stencilToImage.SetInsideValue(minValue)
        # stencilToImage.SetOutsideValue(maxValue)
        # stencilToImage.Update()
        
        # 切換cut in / out 只有當current index 指向最新影像時，才有作用
        # 否則需要重畫contour
        # if image is None:
        #     if self.currentIndex == len(self.imageBackup) - 1:
        #         backStep = max(0, self.currentIndex - 1)
        #         image = self.imageBackup[backStep]
        #     else:
        #         return False
        
        imageMath = vtk.vtkImageMathematics()
        imageMath.SetOperationToMin()
        imageMath.SetInput1Data(self.imageOrigin)
        # imageMath.SetInput1Data(self.imageBackup[-1])
        imageMath.SetInput2Data(self.currentMask)
        imageMath.Update()
        
        # self.imageReady = mask
        self.imageReady = imageMath.GetOutput()
        self.update()
        
    def saveImage(self, image):
        if image is None:
            return
        
        if len(self.imageBackup) == 0 or self.imageReady != self.imageBackup[-1]:
            _image = vtk.vtkImageData()
            _image.DeepCopy(image)
            self.imageBackup.append(_image)
            
            if len(self.imageBackup) > self.MAX_BACKUP:
                self.imageBackup.pop(0)
                
        if (len(self.maskBackup) == 0 or self.currentMask != self.maskBackup[-1]) and self.currentMask:
            _mask = vtk.vtkImageData()
            _mask.DeepCopy(self.currentMask)
            self.maskBackup.append(_mask)
                
            if len(self.maskBackup) > self.MAX_BACKUP:
                self.maskBackup.pop(0)
        
                
        self.currentIndex = len(self.imageBackup) - 1
        self.currentIndexMask = len(self.maskBackup) - 1
        self.imageReady = self.imageBackup[-1]
        
        if len(self.maskBackup) > 0:
            self.currentMask = self.maskBackup[-1]
        # print(f'id in saveImage = {id(self.imageReady)}')
    
    def update(self):
        if self.image and self.imageReady:
            self.image.DeepCopy(self.imageReady)
        
class SegmentationFunction(ImageAlgorithm):
    
    def __init__(self):
        super().__init__()
        pass
        
    def CutInside(self, image = None):
        if self.stencilImage is None or len(self.imageBackup) == 0:
            return False
        
        scalarType = self.scalarType
        minValue, maxValue = SCALAR_TYPE_RANGE.get(scalarType, (None, None))
        
        if minValue is None or maxValue is None:
            logger.error('scalarType error')
            self.imageOutputPort = None
            return False
        
        stencilToImage = vtk.vtkImageStencilToImage()
        stencilToImage.SetOutputScalarType(scalarType)
        stencilToImage.SetInputData(self.stencilImage)
        stencilToImage.SetInsideValue(minValue)
        stencilToImage.SetOutsideValue(maxValue)
        stencilToImage.Update()
        
        if not self.currentMask:
            self.currentMask = stencilToImage.GetOutput()
        else:
            imageMath = vtk.vtkImageMathematics()
            imageMath.SetOperationToMin()
            imageMath.SetInput1Data(self.currentMask)
            imageMath.SetInput2Data(stencilToImage.GetOutput())
            imageMath.Update()
            
            self.currentMask = imageMath.GetOutput()
        
        # 切換cut in / out 只有當current index 指向最新影像時，才有作用
        # 否則需要重畫contour
        if image is None:
            image = self.imageReady
            # if self.currentIndex == len(self.imageBackup) - 1:
            #     backStep = max(0, self.currentIndex - 1)
            #     image = self.imageBackup[backStep]
            # else:
            #     return False
        
        imageMath = vtk.vtkImageMathematics()
        imageMath.SetOperationToMin()
        imageMath.SetInput1Data(image)
        imageMath.SetInput2Data(stencilToImage.GetOutput())
        imageMath.Update()
        
        self.imageReady = imageMath.GetOutput()
        return True
    
    def CutOutside(self, image = None):
        if self.stencilImage is None or len(self.imageBackup) == 0:
            return False
        
        scalarType = self.scalarType
        minValue, maxValue = SCALAR_TYPE_RANGE.get(scalarType, (None, None))
        
        if minValue is None or maxValue is None:
            logger.error('scalarType error')
            self.imageOutputPort = None
            return False
        
        
        stencilToImage = vtk.vtkImageStencilToImage()
        stencilToImage.SetOutputScalarType(scalarType)
        stencilToImage.SetInputData(self.stencilImage)
        stencilToImage.SetInsideValue(maxValue)
        stencilToImage.SetOutsideValue(minValue)
        stencilToImage.Update()
        
        if not self.currentMask:
            self.currentMask = stencilToImage.GetOutput()
        else:
            imageMath = vtk.vtkImageMathematics()
            imageMath.SetOperationToMin()
            imageMath.SetInput1Data(self.currentMask)
            imageMath.SetInput2Data(stencilToImage.GetOutput())
            imageMath.Update()
            
            self.currentMask = imageMath.GetOutput()
        
        # 切換cut in / out 只有當current index 指向最新影像時，才有作用
        # 否則需要重畫contour
        if image is None:
            image = self.imageReady
            # if self.currentIndex == len(self.imageBackup) - 1:
            #     backStep = max(0, self.currentIndex - 1)
            #     image = self.imageBackup[backStep]
            # else:
            #     return False
        
        imageMath = vtk.vtkImageMathematics()
        imageMath.SetOperationToMin()
        imageMath.SetInput1Data(image)
        imageMath.SetInput2Data(stencilToImage.GetOutput())
        imageMath.Update()
        
        self.imageReady = imageMath.GetOutput()
        return True
    
    def ComputeCuttingArea(self, polyData, direct, mode, clipRange):
        
        extrudePos = vtk.vtkLinearExtrusionFilter()
        extrudePos.SetInputData(polyData)
        extrudePos.SetScaleFactor(clipRange[0])
        extrudePos.SetVector(direct)
        extrudePos.Update()
        
        extrudeNeg = vtk.vtkLinearExtrusionFilter()
        extrudeNeg.SetInputData(polyData)
        extrudeNeg.SetScaleFactor(clipRange[1])
        extrudeNeg.SetVector(direct)
        extrudeNeg.Update()
        
        extrude = vtk.vtkAppendPolyData()
        extrude.AddInputConnection(extrudePos.GetOutputPort())
        extrude.AddInputConnection(extrudeNeg.GetOutputPort())
        
        polyToStencil = vtk.vtkPolyDataToImageStencil()
        polyToStencil.SetTolerance(0)
        polyToStencil.SetInputConnection(extrude.GetOutputPort())
        polyToStencil.SetOutputOrigin(self.origin)
        polyToStencil.SetOutputSpacing(self.spacing)
        polyToStencil.SetOutputWholeExtent(self.extent)
        polyToStencil.Update()
        self.stencilImage = polyToStencil.GetOutput()
        
        count = len(self.imageBackup)
        if self.currentIndex < count - 1:
            self.imageBackup = self.imageBackup[:self.currentIndex + 1]
            
        if self.currentIndexMask < len(self.maskBackup) - 1:
            self.maskBackup = self.maskBackup[:self.currentIndexMask + 1]
            # self.saveImage(self.imageBackup[self.currentIndex])
            
        bFlag = False
        if mode == 0:
            bFlag = self.CutInside()
            # bFlag = self.CutInside(self.imageReady)
        elif mode == 1:
            bFlag = self.CutOutside()
            # bFlag = self.CutOutside(self.imageReady)
            
        if not bFlag:
            return False
        
        # while count > self.MAX_BACKUP: 
        #     self.imageBackup.pop(0)  
        #     count = len(self.imageBackup)
        # print(f'count after pop = {len(self.imageBackup)}') 
            
        # self.imageBackup.append(self.imageReady)
        # self.currentIndex = len(self.imageBackup) - 1
        self.saveImage(self.imageReady)
        self.update()
        return True
    
class vtkWidgetCall(vtk.vtkPlaneWidget):
    
    plane = vtk.vtkPlane()
    actor = None
    cutActor = None
    def __init__(self, actor, renderer, iren, lookupTable):
        super().__init__()
        self.AddObserver(vtk.vtkCommand.EndInteractionEvent, self.EndInteractor)
        self.AddObserver(vtk.vtkCommand.InteractionEvent, self.Interactor)
        self.actor = actor
        self.renderer = renderer
        
        # shift = vtk.vtkImageShiftScale()
        # range = renderer.image.GetScalarRange()
        # shift.SetShift(-1.0 * range[0])
        # shift.SetScale(255.0 / (range[1] - range[0]))
        # shift.SetOutputScalarTypeToUnsignedChar()
        # shift.SetInputData(renderer.image)
        # shift.ReleaseDataFlagOff()
        # shift.Update()
        
        # self.shiftImage = shift
        self.image = renderer.image
        self.iren = iren
        
        # range = self.renderer.dicomGrayscaleRange
        # lookupTable.SetTableRange(range[0], range[1])
        lookupTable.SetBelowRangeColor(0, 0, 0, 0)
        lookupTable.UseBelowRangeColorOn()
        self.lookupTable = lookupTable
        mapToColor = vtkImageMapToColors()
        mapToColor.SetLookupTable(self.lookupTable)
        
        self.mapColor = mapToColor
        
    def EndInteractor(self, obj, event):
        
        self.GetPlane(self.plane)
        self.plane.SetNormal(np.array(self.plane.GetNormal()) * -1)
        self.actor.GetMapper().AddClippingPlane(self.plane)
        
    def Interactor(self, obj, event):
        
        self.Update()
        
    def Update(self):
        self.GetPlane(self.plane)
        self.plane.SetNormal(np.array(self.plane.GetNormal()) * -1)
        self.actor.GetMapper().AddClippingPlane(self.plane)
        
        self.mapColor.SetInputData(self.image)
        
        sliceMapper = vtk.vtkImageResliceMapper()
        sliceMapper.SetInputConnection(self.mapColor.GetOutputPort())
        sliceMapper.SetSlicePlane(self.plane)
        
        if not self.cutActor:
            imageSlice = vtk.vtkImageSlice()
            imageSlice.SetMapper(sliceMapper)
            # imageSlice.ForceTranslucentOn()
            imageSlice.Update()
            
            self.renderer.AddActor(imageSlice)
            self.cutActor = imageSlice
            
        else:
            self.cutActor.SetMapper(sliceMapper)
    
class InteractorStylePlaneWidget(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self):
        super().__init__()
        self.AddObserver('MouseMoveEvent', self.onMouseMove)
        
    def onMouseMove(self, obj, event):
        super().OnMouseMove()
        
    

    
class InteractorStyleImageAlgorithm(vtkInteractorStyleImage):
    
    signalObj = QSignalObject()
    
    def __init__(self, renderer = None):
        super().__init__()
        
        self.iren        = None
        self.renderer    = None
        self.picker      = None
        self.actor       = None
        self.callback    = None
        self.imageAlgorithm = None
        self.originalStyle = None
        self.bLeftButtonPress = False
        self.statusRange = [False, False]
    
        self.AddObserver('LeftButtonPressEvent', self.onLeftButtonPress)
        self.AddObserver('LeftButtonReleaseEvent', self.onLeftButtonRelease)
        self.AddObserver('MouseMoveEvent', self.onMouseMove)
        self.StartInteractor(renderer)
        
    def StartInteractor(self, renderer:vtkRenderer):
        # if self.originalStyle is not None:
        #     print('already set InteractorStyleImageAlgorithm')
        
        if renderer is not None:
            self.renderer = renderer
            self.iren = renderer.GetRenderWindow().GetInteractor()
            
            # originalStyle保存的是一般的interactorStyle，而不是功能性的
            # 功能性的interactorStyle結束後
            # 會把originalStyle回復給原本的iren
            # 然後originalStyle設為None
            
            
            if self.originalStyle is None:
                self.originalStyle = self.iren.GetInteractorStyle()
            self.iren.SetInteractorStyle(self)
            self.Update()
            
    def SetActor(self, actor):
        if not hasattr(actor, 'GetMapper'):
            logger.error('actor has not GetMapper attribute, please set correct actor or volume')
        else:
            self.actor = actor
            
    def onLeftButtonPress(self, obj, event):
        pass
    
    def onLeftButtonRelease(self, obj, event):
        pass
    
    def onMouseMove(self, obj, event):
        pass
    
    def onChangeCurrentRenderer(self):
        pass
            
    def EndInteractor(self, changeApply = False):
        if self.originalStyle is not None:
            if changeApply:
                self.imageAlgorithm.ApplyModifiedImage()
                self.Update()
            
            self.iren.SetInteractorStyle(self.originalStyle)
            self.originalStyle = None
            
                
    def GetInput(self):
        return self.imageAlgorithm
    
    def ResetImage(self, image = None):
        if image and self.imageAlgorithm:
            self.imageAlgorithm.SetInputData(image)
            
    def SetInput(self, algorithm:ImageAlgorithm):
        self.imageAlgorithm = algorithm
        
    def StepBack(self):
        if self.imageAlgorithm is not None:
            self.statusRange[0] = self.imageAlgorithm.StepBack()
            self.Update()
            # self.signalObj.emit(self.statusRange[0], self.statusRange[1])
            self.signalObj.EmitRange(self.statusRange[0], True)
            
    def StepNext(self):
        if self.imageAlgorithm is not None:
            self.statusRange[1] = self.imageAlgorithm.StepNext()
            self.Update()
            # self.signalObj.emit(self.statusRange[0], self.statusRange[1])
            self.signalObj.EmitRange(True, self.statusRange[1])
    
    def CallbackSetOutRange(self, callbackFunc):
        # self.signalObj.connect(callbackFunc)
        self.signalObj.ConnectRange(callbackFunc)
        
    def CallbackUpdateView(self, callbackFunc):
        self.signalObj.ConnectUpdateView(callbackFunc)
        
    def ResumeRendererStyle(self):
        if self.originalStyle and self.iren:
            self.iren.SetInteractorStyle(self.originalStyle)
            self.originalStyle = None
            self.onChangeCurrentRenderer()
        
    def Update(self, output = None):
        if self.actor is not None and self.imageAlgorithm is not None:
            if output is None:
                output = self.imageAlgorithm.imageReady
                
            # mapper = self.actor.GetMapper()
            # if isinstance(mapper, vtk.vtkImageSliceMapper):
            #     inputConnect = mapper.GetInputConnection(0, 0)
            #     imageMapToColor = vtk.vtkImageMapToColors.SafeDownCast(inputConnect.GetProducer())
            #     imageMapToColor.SetInputData(output)
            # else:
            #     self.actor.GetMapper().SetInputData(output)
            # self.imageAlgorithm.image.DeepCopy(output)
            self.iren.Initialize()
            self.iren.Start()
        
class InteractorStyleSegmentation(InteractorStyleImageAlgorithm):
    
    MODE_CUT_IN  = 0
    MODE_CUT_OUT = 1
    def __init__(self, renderer = None):
        super().__init__(renderer) 

        self.actorLine   = None
        self.drawPlane   = None
        # 0:cut inside 1:cut outside
        self.mode = 0
    # mode 0 : cut inside
    # mode 1 : cut outside
    def SetMode(self, mode):
        if mode < 0 or mode > 1:
            logger.error('mode is not support')
        self.mode = mode
        
    def SetModeCutIn(self):
        self.mode = self.MODE_CUT_IN
        
    def SetModeCutOut(self):
        self.mode = self.MODE_CUT_OUT
    
    def SetInput(self, algorithm:ImageAlgorithm):
        super().SetInput(algorithm)
        self.picker = vtk.vtkWorldPointPicker()
        
    # def StartInteractor(self, renderer:vtkRenderer, mode:int = 0):
    #     super().StartInteractor(renderer)
    #     self.mode = mode
    
            
    def CutInside(self):
        if self.imageAlgorithm is None:
            logger.error('imageAlgorithm not exist at InteractorStyleSegmentation')
            return
        
        if self.iren is None:
            logger.error('iren not exist in at InteractorStyleSegmentation')
            return
        
        self.imageAlgorithm.CutInside()
        self.Update()
        
    def CutOutside(self):
        if self.imageAlgorithm is None:
            logger.error('imageAlgorithm not exist at InteractorStyleSegmentation')
            return
        
        if self.iren is None:
            logger.error('iren not exist in at InteractorStyleSegmentation')
            return
        
        self.imageAlgorithm.CutOutside()
        self.Update()
        
    def Inverse(self):
        if self.imageAlgorithm:
            self.imageAlgorithm.Inverse()
            self.Update()
    
            
    def getCameraPlane(self):
        if self.renderer is None:
            return None
        
        camera = self.renderer.GetActiveCamera()
        
        clipRange = camera.GetClippingRange()
        direct = camera.GetDirectionOfProjection()
        pos = camera.GetFocalPoint()
        
        plane = vtk.vtkPlane()
        plane.SetOrigin(pos)
        plane.SetNormal(direct)
        
        return plane, direct, clipRange
    
    def pickPosition(self):
        if self.iren is None:
            self.iren = self.GetInteractor()
            if self.iren is None:
                logger.error('iren of InteractorStyleSegmentation is None')
                return None
            
            self.renderer = self.iren.GetRenderWindow().GetRenderers().GetFirstRenderer()
            
        points = self.iren.GetEventPosition()
        self.picker.Pick(points[0], points[1], 0, self.renderer)
            
        return self.picker.GetPickPosition()    
    
    def getPickPosition(self):
        if isinstance(self.picker, vtk.vtkWorldPointPicker):
            pos = self.pickPosition()
            if pos is None:
                return None
            
            if self.drawPlane is None:
                return None
                        
            # d = self.drawPlane.EvaluateFunction(pos)

            # if abs(d) < 0.1:
            #     return pos
            # else:
            #     return None
            return pos
    
    def startPickPosition(self):
        pos = self.pickPosition()
        # upVector = np.array(self.renderer.GetActiveCamera().GetViewUp())
        direct = np.array(self.renderer.GetActiveCamera().GetDirectionOfProjection())
        plane = vtk.vtkPlane()
        plane.SetOrigin(pos)
        plane.SetNormal(direct)
        
        # vectorLeft = np.cross(direct, upVector)
        
        # planeObj = vtk.vtkPlaneSource()
        # planeObj.SetOrigin(pos)
        # # planeObj.SetNormal(direct)
        
        # planeObj.SetPoint1(pos + vectorLeft * 100)
        # planeObj.SetPoint2(pos + upVector * 100)
        
        # mapper = vtkPolyDataMapper()
        # mapper.SetInputConnection(planeObj.GetOutputPort())
        
        # planeActor = vtkActor()
        # planeActor.SetMapper(mapper)
        
        # if not hasattr(self, 'planeActor'):
        #     self.planeActor = planeActor
        #     self.renderer.AddActor(planeActor)
        
        self.drawPlane = plane
        
    def onLeftButtonPress(self, obj, event):
        self.bLeftButtonPress = True
        
        self.vtkPts = vtk.vtkPoints()
        self.pts = []
        # if self.actorLine is not None:
        #     self.actorLine.VisibilityOn()
            
        self.startPickPosition()
    
    def onLeftButtonRelease(self, obj, event):
        self.bLeftButtonPress = False
        
        if self.actorLine is not None:
            self.actorLine.VisibilityOff()
            
        camera = self.renderer.GetActiveCamera()
        direct = np.array(camera.GetDirectionOfProjection())
        
        numOfPoints = len(self.pts)
        vertex = np.array([i for i in range(numOfPoints + 1)], dtype = int)
        vertex[numOfPoints] = 0
        
        lines = vtk.vtkCellArray()
        lines.InsertNextCell(numOfPoints + 1, vertex)
        
        polyData = vtk.vtkPolyData()
        polyData.SetPoints(self.vtkPts)
        polyData.SetLines(lines)
        
        clipRange = np.array(camera.GetClippingRange())
        clipRange[0] = -clipRange[1]
        bRet = self.imageAlgorithm.ComputeCuttingArea(polyData, direct, self.mode, clipRange)
        
        self.Update()
        
        self.statusRange[0] = bRet
        self.signalObj.EmitRange(self.statusRange[0], self.statusRange[1])
        self.signalObj.EmitUpdateView()
        
    def onMouseMove(self, obj, event):
        if self.bLeftButtonPress:
            pickPos = self.getPickPosition()
            if pickPos is None:
                return
            
            args = self.getCameraPlane()
            
            if args is None:
                return
            plane = args[0]
            
            projPos = np.zeros(3)
            plane.ProjectPoint(pickPos, projPos)
            self.vtkPts.InsertNextPoint(projPos)
            self.pts.append(projPos)
            
            numOfPoints = self.vtkPts.GetNumberOfPoints()
            
            if numOfPoints < 1: 
                return
            
            polyLine = vtkLineSource()
            pointsTmp = vtk.vtkPoints()
            pointsTmp.DeepCopy(self.vtkPts)
            pointsTmp.InsertNextPoint(self.pts[0])
            
            polyLine.SetPoints(pointsTmp)
            if self.actorLine is None:
                coord = vtkCoordinate()
                coord.SetCoordinateSystemToWorld()
                
                mapperLine = vtkPolyDataMapper2D()
                mapperLine.SetInputConnection(polyLine.GetOutputPort())
                mapperLine.SetTransformCoordinate(coord)
                
                actorLine = vtkActor2D()
                actorLine.SetMapper(mapperLine)
                actorLine.GetProperty().SetColor(1, 1, 0)
                actorLine.GetProperty().SetLineWidth(2)
                self.actorLine = actorLine
                
                self.renderer.AddActor(self.actorLine)
                
            else:
                self.actorLine.GetMapper().SetInputConnection(polyLine.GetOutputPort())
                self.actorLine.VisibilityOn()
            
            self.iren.Initialize()
            self.iren.Start()
            
    def onChangeCurrentRenderer(self):
        self.actorLine = None
    
class InteractorStyleVolume(vtk.vtkInteractorStyleRubberBandPick):
    
    def __init__(self):
        super().__init__()
        
        self.bEnable          = True
        self.bLeftButtonPress = False
        self.renderer         = None
        self.iren             = None
        self.vtkPts           = vtk.vtkPoints()
        self.vtkPtsFar        = vtk.vtkPoints()
        self.pts              = []
        self.picker = vtk.vtkWorldPointPicker()
        
        self.AddObserver('LeftButtonPressEvent', self.OnLeftButtonPress)
        self.AddObserver('LeftButtonReleaseEvent', self.OnLeftButtonRelease)
        self.AddObserver('MouseMoveEvent', self.OnMouseMove)
        self.AddObserver('RightButtonReleaseEvent', self.OnRightButtonRelease)
        
        # self.segmentation = SegmentationFunction()
        # self.segmentation.SetRenderer(self)
        
    def OnRightButtonRelease(self, obj, event):
        self.bEnable = not self.bEnable
        super().OnRightButtonUp()
        
        
    def getCameraPlane(self):
        if self.renderer is None:
            return None
        
        camera = self.renderer.GetActiveCamera()
        
        # pos = camera.GetPosition()
        clipRange = camera.GetClippingRange()
        direct = camera.GetDirectionOfProjection()
        posFar = camera.GetFocalPoint()
        
        # plane = vtk.vtkPlane()
        # plane.SetOrigin(pos)
        # plane.SetNormal(direct)
        
        plane = vtk.vtkPlane()
        plane.SetOrigin(posFar)
        plane.SetNormal(direct)
        
        
        return plane, direct, clipRange
    
    def pickPosition(self):
        if self.iren is None:
            self.iren = self.GetInteractor()
            self.renderer = self.iren.GetRenderWindow().GetRenderers().GetFirstRenderer()
            
            
        points = self.iren.GetEventPosition()
        self.picker.Pick(points[0], points[1], 0, self.renderer)
            
        return self.picker.GetPickPosition()
    def startPickPosition(self):
        pos = self.pickPosition()
        
        direct = self.renderer.GetActiveCamera().GetDirectionOfProjection()
        plane = vtk.vtkPlane()
        plane.SetOrigin(pos)
        plane.SetNormal(direct)
        self.plane = plane
        
    def getPickPosition(self):
        pos = self.pickPosition()
        
        if not hasattr(self, 'plane'):
            return None
        
        d = self.plane.EvaluateFunction(pos)

        if abs(d) < 0.1:
            
            return pos
        else:
            return None
        
    def OnLeftButtonPress(self, obj, event):
        self.bLeftButtonPress = True
        if not self.bEnable:
            super().OnLeftButtonDown()
        else:
            self.vtkPts = vtk.vtkPoints()
            self.vtkPtsFar = vtk.vtkPoints()
            self.pts = []
            if hasattr(self, 'actorLine'):
                self.actorLine.VisibilityOn()
                
            self.startPickPosition()
            
        
                
    def drawCuttingPolygon(self):
        self.actorLine.VisibilityOff()
        
        camera = self.renderer.GetActiveCamera()
        clipRange = camera.GetClippingRange()
        direct = np.array(camera.GetDirectionOfProjection())
        # direct = np.array(camera.GetViewPlaneNormal())
        
        numOfPoints = len(self.pts)
        
        
        vertex = np.zeros(numOfPoints + 1, dtype = int)
        # polyCenter = np.zeros(3)
        
        for i in range(numOfPoints):
            vertex[i] = i
            # polyCenter += np.array(p)
            
        bounds = self.vtkPts.GetBounds()
        polyCenter = np.zeros(3)
        for i in range(3):
            polyCenter[i] = (bounds[i * 2 + 1] + bounds[i * 2]) * 0.5
            
        # polyCenter /= numOfPoints
        # direct = polyCenter - pos
        # direct /= np.linalg.norm(direct)
        
        # sphere = vtkSphereSource()
        # sphere.SetRadius(5)
        # sphere.SetPhiResolution(30)
        # sphere.SetThetaResolution(30)
        # sphere.SetCenter(polyCenter)
        # polyData = sphere.GetOutput()
        # sphere.Update()
        
        # mapper = vtkPolyDataMapper()
        # mapper.SetInputData(sphere.GetOutput())
        
        # actor = vtkActor()
        # actor.SetMapper(mapper)
        # actor.GetProperty().SetColor(1.0, 0.8, 0.3)
        
        # self.renderer.AddActor(actor)
            
        vertex[numOfPoints] = 0
        
        lines = vtk.vtkCellArray()
        lines.InsertNextCell(numOfPoints + 1, vertex)
        
        polyData = vtk.vtkPolyData()
        polyData.SetPoints(self.vtkPts)
        polyData.SetLines(lines)
        
        cleanFilter = vtk.vtkCleanPolyData()
        cleanFilter.SetInputData(polyData)
        # cleanFilter.ConvertLinesToPointsOn()
        # cleanFilter.ConvertPolysToLinesOn()
        # cleanFilter.ConvertStripsToPolysOn()
        cleanFilter.SetTolerance(0.1)
        cleanFilter.Update()
        
        extrudePos = vtk.vtkLinearExtrusionFilter()
        # extrudePos.SetInputConnection(cleanFilter.GetOutputPort())
        extrudePos.SetInputData(polyData)
        extrudePos.SetScaleFactor(clipRange[1])
        extrudePos.SetVector(direct)
        extrudePos.Update()
        
        extrudeNeg = vtk.vtkLinearExtrusionFilter()
        # extrudeNeg.SetInputConnection(cleanFilter.GetOutputPort())
        extrudeNeg.SetInputData(polyData)
        extrudeNeg.SetScaleFactor(clipRange[1])
        extrudeNeg.SetVector(-direct)
        extrudeNeg.Update()
        
        extrude = vtk.vtkAppendPolyData()
        extrude.AddInputConnection(extrudePos.GetOutputPort())
        extrude.AddInputConnection(extrudeNeg.GetOutputPort())
        
        # if not hasattr(self, 'actor'):
        #     mapper = vtkPolyDataMapper()
        #     mapper.SetInputConnection(extrude.GetOutputPort())
        #     # mapper.SetInputData(polyData)
            
        #     self.actor = vtkActor()
        #     self.actor.SetMapper(mapper)
        #     self.actor.GetProperty().SetColor(0, 1, 1)
            
        #     self.renderer.AddActor(self.actor)
        # else:
        #     self.actor.GetMapper().SetInputConnection(extrude.GetOutputPort())
            
        image = self.renderer.image
        
        extent = image.GetExtent()
        spacing = image.GetSpacing()
        origin = image.GetOrigin()
        
        polyToStencil = vtk.vtkPolyDataToImageStencil()
        polyToStencil.SetTolerance(0)
        polyToStencil.SetInputConnection(extrude.GetOutputPort())
        polyToStencil.SetOutputOrigin(origin)
        polyToStencil.SetOutputSpacing(spacing)
        polyToStencil.SetOutputWholeExtent(extent)
        polyToStencil.Update()
        
        
        stencilToImage = vtk.vtkImageStencilToImage()
        stencilToImage.SetOutputScalarType(image.GetScalarType())
        stencilToImage.SetInputConnection(polyToStencil.GetOutputPort())
        stencilToImage.SetInsideValue(-32768)
        stencilToImage.SetOutsideValue(32767)
        stencilToImage.Update()
        
        imageMath = vtk.vtkImageMathematics()
        imageMath.SetOperationToMin()
        imageMath.SetInput1Data(self.renderer.image)
        imageMath.SetInput2Data(stencilToImage.GetOutput())
        imageMath.Update()
        
        self.renderer.volume.GetMapper().SetInputConnection(imageMath.GetOutputPort())
        self.renderer.image = imageMath.GetOutput()
        
            
        self.iren.Initialize()
        self.iren.Start()
        
    def OnLeftButtonRelease(self, obj, event):
        self.bLeftButtonPress = False
        if not self.bEnable:
            super().OnLeftButtonUp()
        else:
            
            self.drawCuttingPolygon()
                
            
            
        
    def OnMouseMove(self, obj, event):
        if self.bLeftButtonPress:
            
            if self.bEnable:
                
                pickPos = self.getPickPosition()
                if pickPos is None:
                    return
                
                args = self.getCameraPlane()
                
                if args is None:
                    return
                plane = args[0]
                
                projPos = np.zeros(3)
                plane.ProjectPoint(pickPos, projPos)
                self.vtkPts.InsertNextPoint(projPos)
                self.pts.append(projPos)
                
                numOfPoints = self.vtkPts.GetNumberOfPoints()
                
                if numOfPoints < 1: 
                    return
                
                
                
                polyLine = vtkLineSource()
                pointsTmp = vtk.vtkPoints()
                pointsTmp.DeepCopy(self.vtkPts)
                pointsTmp.InsertNextPoint(self.pts[0])
                
                polyLine.SetPoints(pointsTmp)
                # for i in range(numOfPoints - 1):
                #     polyLine.SetPoint1(self.pts[i])
                # polyLine.GetPoints().InsertNextPoint(self.pts[0])
                if not hasattr(self, 'actorLine'):
                    coord = vtkCoordinate()
                    coord.SetCoordinateSystemToWorld()
                    
                    mapperLine = vtkPolyDataMapper2D()
                    mapperLine.SetInputConnection(polyLine.GetOutputPort())
                    mapperLine.SetTransformCoordinate(coord)
                    
                    actorLine = vtkActor2D()
                    actorLine.SetMapper(mapperLine)
                    actorLine.GetProperty().SetColor(1, 1, 0)
                    actorLine.GetProperty().SetLineWidth(2)
                    self.actorLine = actorLine
                    
                    self.renderer.AddActor(self.actorLine)
                else:
                    self.actorLine.GetMapper().SetInputConnection(polyLine.GetOutputPort())
                
                self.iren.Initialize()
                self.iren.Start()
                
                
            else:
                super().OnMouseMove()
            
            # self.points.append(projPos)
            
            # newPts = vtk.vtkPoints()
            # for point in self.points:
                
            
        
    
    
class ContourWidget(vtk.vtkContourWidget):
    
    def __init__(self, viewport):
        
        self.AddObserver('EndInteractionEvent', self.OnEndInteraction)
        self.AddObserver('WidgetValueChangedEvent', self.OnWidgetValueChangedEvent)
        self.AddObserver('PlacePointEvent', self.OnPlacePointEvent)
        
        self.rep = vtk.vtkOrientedGlyphContourRepresentation()
        self.rep.GetLinesProperty().SetColor(1, 0, 0)
        self.rep.GetLinesProperty().SetLineWidth(2)
        
        self.rep.GetProperty().SetOpacity(0)
        self.SetRepresentation(self.rep)
        
        self.viewport = viewport
        self.renderer = viewport.renderer
        actorPointPlacer = vtk.vtkImageActorPointPlacer()
        # actorPointPlacer.SetImageActor(self.renderer.volume)
        actorPointPlacer.SetImageActor(self.renderer.actorImage)
        self.rep.SetPointPlacer(actorPointPlacer)
        
        iren = self.renderer.GetRenderWindow().GetInteractor()
        self.originalIStyle = iren.GetInteractorStyle()
        # iren.SetInteractorStyle(None)
        iren.SetInteractorStyle(ContourInteractorStyle(self))
        self.SetInteractor(iren)
        self.iren = iren
        
        
        self.SetEnabled(True)
        # self.ProcessEventsOn()
        self.ContinuousDrawOn()
        
        info = self.renderer.GetImageInfo()
        self.dimension = info[0]
        self.spacing   = info[1]
        self.origin    = info[2]
        
        self.image     = self.renderer.image
        
        # self.initImageView(self.image)
        
        # imageView = vtk.vtkImageViewer2()
        # self.imageView = imageView
        
        # renderer = imageView.GetRenderer()
        # renderer.ResetCamera()
        
        
        
        # imageView.SetupInteractor(iren)
        
        # renderer.SetRenderWindow(renderWindow)
        # self.initImageView(self.image)
        
    def SetMask(self, mask):
        views = self.viewport.parentWidget.viewPortL
        for view in views.values():
            if view.orientation == VIEW_3D:
                view.renderer.volume.GetMapper().SetInputConnection(mask)
            else:
                actor = view.renderer.actorImage
                actor.GetMapper().SetInputConnection(mask)
            view.UpdateView()
            
        
        
    def OnPlacePointEvent(self, obj, event):
        logger.debug('place points')
        
    def OnWidgetValueChangedEvent(self, obj, event):
        logger.debug('value changed')
        
    def OnEndInteraction(self, obj, event):
        spacing = self.spacing
        dim     = self.dimension
        origin  = self.origin
        
        # self.Initalize()
        
        return
        
        polyData = self.GetContourRepresentation().GetContourRepresentationAsPolyData()
        verts = polyData.GetNumberOfPoints()
        logger.debug(f'original verts : {verts}')
        
        # scalarPoly1 = vtk.vtkIntArray()
        # pointData = polyData.GetPointData()
        
        # numOfPoly1 = polyData.GetNumberOfPoints()
        # scalarPoly1.SetNumberOfTuples(numOfPoly1)
        # scalarPoly1.SetNumberOfComponents(1)
        # for i in range(numOfPoly1 - 5):
        #     scalarPoly1.SetTuple1(i, 0)
            
        # pointData.SetScalars(scalarPoly1)
        
        
        
        # scalarPoly2 = vtk.vtkIntArray()
        # pointData = new_poly_data.GetPointData()
        
        # numOfPoly2 = polyData.GetNumberOfPoints()
        # scalarPoly2.SetNumberOfTuples(numOfPoly2)
        # scalarPoly2.SetNumberOfComponents(1)
        # for i in range(numOfPoly2 - 5):
        #     scalarPoly1.SetTuple1(i, 1)
            
        # pointData.SetScalars(scalarPoly2)

 
        
                
        # transform = vtk.vtkTransform()
        # transform.RotateWXYZ(-90, 1, 0, 0)
        
        # transformFilter = vtk.vtkTransformPolyDataFilter()
        # transformFilter.SetInputData(polyData)
        # transformFilter.SetTransform(transform)
        # transformFilter.Update()
        
        # polyData = transformFilter.GetOutput()
        
        # points = polyData.GetPoints()
        # verts = polyData.GetPoints().GetNumberOfPoints()
        
        
        
        # ===============poly測試======================
        # points = vtk.vtkPoints()
        # for i in range(10):
        #     angle = 2 * np.pi * i / 10
        #     points.InsertPoint(i, 150 * np.cos(angle), 150 * np.sin(angle), 0.0)
            
        # vertex = np.zeros(11, dtype = int)
        # for i in range(10):
        #     vertex[i] = i
            
        # vertex[10] = 0
        # lines = vtk.vtkCellArray()
        # lines.InsertNextCell(11, vertex)
        
        # polyData = vtk.vtkPolyData()
        # polyData.SetPoints(points)
        # polyData.SetLines(lines)
        
        # self.contourWidget.Initialize(polyData)
        #==============================================
        # center = np.array(dim) * np.array(spacing) * 0.5
        # sphere = vtk.vtkSphereSource()
        # sphere.SetRadius(100)
        # sphere.SetPhiResolution(30)
        # sphere.SetThetaResolution(30)
        # sphere.SetCenter(center)
        # polyData = sphere.GetOutput()
        # sphere.Update()
        
        extrude = vtk.vtkLinearExtrusionFilter()
        extrude.SetInputData(polyData)
        extrude.SetExtrusionTypeToNormalExtrusion()
        extrude.SetVector(0.0, 30.0, 0.0)
        
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputConnection(extrude.GetOutputPort())
        normals.SetFeatureAngle(60)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())
        # mapper.SetInputData(polyData)
        
        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1, 0, 0)
        
        self.renderer.AddActor(actor)
        
        
        return
        # =============================================
        
        # whiteImage = vtk.vtkImageData()
        # bounds = pd.GetBounds()
        # spacing = np.ones(3)
        # whiteImage.SetSpacing(spacing)
        
        # dim = np.zeros(3, dtype = int)
        # dim[0] = bounds[1] - bounds[0]
        # dim[1] = bounds[3] - bounds[2]
        # dim[2] = bounds[5] - bounds[4]
        # whiteImage.SetDimensions(dim)
        # whiteImage.SetExtent(0, dim[0] - 1, 0, dim[1] - 1, 0, dim[2] - 1)
        
       
        
        # origin = np.zeros(3)
        # origin[0] = bounds[0] + spacing[0] / 2
        # origin[1] = bounds[2] + spacing[1] / 2
        # origin[2] = bounds[4] + spacing[2] / 2
        # whiteImage.SetOrigin(origin)
        # whiteImage.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)
        
        # print('origin', origin)
        
        # count = whiteImage.GetNumberOfPoints()
        # for i in range(count):
        #     whiteImage.GetPointData().GetScalars().SetTuple1(i, 255)
            
        
        
        
        
        polyDataToStencil = vtk.vtkPolyDataToImageStencil()
        # polyDataToStencil.SetInputData(pd)
        polyDataToStencil.SetInputData(polyData)
        polyDataToStencil.SetOutputOrigin(origin)
        polyDataToStencil.SetOutputSpacing(spacing)
        # polyDataToStencil.SetOutputWholeExtent(whiteImage.GetExtent())
        polyDataToStencil.SetOutputWholeExtent(0, dim[0] - 1, 0, dim[1] - 1, 0, dim[2] - 1)
        polyDataToStencil.Update()
        
        # stencil = vtk.vtkImageStencil()
        # stencil.SetInputData(whiteImage)
        # stencil.SetInputData(self.contourWidget.image)
        # stencil.SetStencilConnection(polyDataToStencil.GetOutputPort())
        # stencil.SetBackgroundValue(0)
        # stencil.Update()
        
        stencilToImage = vtk.vtkImageStencilToImage()
        stencilToImage.SetInputConnection(polyDataToStencil.GetOutputPort())
        stencilToImage.SetInsideValue(255)
        stencilToImage.SetOutsideValue(0)
        stencilToImage.SetOutputScalarTypeToUnsignedChar()
        stencilToImage.Update()
        
        
        source = vtk.vtkImageCanvasSource2D()
        source.SetScalarTypeToUnsignedChar()
        source.SetNumberOfScalarComponents(3)
        source.SetExtent(0, dim[0] - 1, 0, dim[1] - 1, 0, dim[2] - 1)
        # source.SetExtent(0, 512, 0, 512, 0, 0)
        
        source.SetDrawColor(255, 0, 0)
        source.FillBox(0, 512, 0, 512)
        source.Update()
        
        maskSource = vtk.vtkImageCanvasSource2D()
        maskSource.SetScalarTypeToUnsignedChar()
        maskSource.SetNumberOfScalarComponents(1)
        maskSource.SetExtent(0, 512, 0, 512, 0, 0)
               
        maskSource.SetDrawColor(0, 0, 0)
        maskSource.FillBox(0, 512, 0, 512)
        
        maskSource.SetDrawColor(255, 255, 255)
        maskSource.FillBox(100, 120, 100, 120)
        maskSource.Update()
        
        
        
        maskFilter = vtk.vtkImageMask()
        maskFilter.SetInputData(0, self.contourWidget.image)
        # maskFilter.SetInputData(0, source.GetOutput())
        # maskFilter.SetInputData(1, stencilToImage.GetOutput())
        # maskFilter.SetInputConnection(0, source.GetOutputPort())
        maskFilter.SetInputConnection(1, stencilToImage.GetOutputPort())
        # maskFilter.SetInputConnection(1, maskSource.GetOutputPort())
        maskFilter.SetMaskedOutputValue(0, 0, 0)
        maskFilter.Update()
        
        # self.contourWidget.imageView.SetInputData(maskFilter.GetOutput())
        # self.contourWidget.imageView.Render()
        
        ####
        
        actor = vtkImageActor()
        actor.GetMapper().SetInputConnection(maskFilter.GetOutputPort())
        # self.contourWidget.renderer.AddActor(actor)
        
        # mapper = vtk.vtkDataSetMapper()
        # mapper.SetInputConnection(stencil.GetOutputPort())
        # actor = vtkActor()
        # actor.SetMapper(mapper)
        
        
        
        self.contourWidget.renderer.actorImage.GetMapper().SetInputConnection(maskFilter.GetOutputPort())
        # self.contourWidget.renderer.actorImage.VisibilityOff()
        self.contourWidget.renderer.SetBackground(0.3, 0.3, 0.3)
        
        # iren = self.contourWidget.renderer.GetRenderWindow().GetInteractor()
        # iren.SetInteractorStyle(self.contourWidget.originalIStyle)
        # iren.Initialize()
        # iren.Start()
        
        # self.contourWidget.renderer.Render()
        
        # iren = self.GetInteractor()
        # iren.Initialize()
        # iren.Start()
        
        
        # self.contourWidget.Initialize()
        # self.contourWidget.Off()
        
    def initImageView(self, image):
        
        if image:
            logger.debug(f'dim = {image.GetDimensions()}')
        
        imageView = vtk.vtkImageViewer2()
        imageView.SetInputData(image)
        
        
        renderer = imageView.GetRenderer()
        renderer.ResetCamera()
        
        renderWindow = self.renderer.GetRenderWindow()
        imageView.SetupInteractor(renderWindow.GetInteractor())
        
        renderer.SetRenderWindow(renderWindow)
        imageView.Render()
        
        style = vtk.vtkInteractorStyleImage()
        renderWindow.GetInteractor().SetInteractorStyle(style)
        
        self.iren.Initialize()
        self.iren.Start() 
        
        self.imageView = imageView
        
   
        
    
class RendererObj(vtkRenderer):
    # signalUpdateView = pyqtSignal()
    # target為全實例共享，故設置為類屬性
    target = [0, 0, 0]
    
    # 之後透過類變數統一管理全部view的target是否顯示
    bShowTarget = False
    
    def __init__(self):
        super(RendererObj, self).__init__()
        
        self.viewPort = None
        self.actorTargetScale = []
        self.actorTargetCenter = []
        self.threshold = None
        self.connectivityFilter = None
        self.imageOrigin = None
        self.image = None
        self.imagePosition = None
        self.border = None
        self.bSelected = False
        self.bFocusMode = True
        self.bTargetVisible = True
        self.bRulerVisible = True
        self.bRulerVisibleTemp = True
        self.textActor = None
            
        self.targetObj = TargetObj(self)
        
        self.actorTarget = [vtkActor2D() for _ in range(2)]
        self.isInitialize = False
        self.imageOutputPort = None
        self.actorImage = vtkImageActor()
        self.windowLevelLookup = None
        self.mapColor = vtkImageMapToColors()
        self.camera = vtkCamera()
        self.orientation = None
        self.textActor = vtk.vtkTextActor()
               
        #reslice image
        self.dicomGrayscaleRange = None
        self.dicomBoundsRange = None
        self.imageDimensions = None
        self.voxelSize = None
        self.imageReslice = None
        self.targetPoint = None
        self.entryPoint = None
        self.actorTargetPoint = [vtkActor2D() for _ in range(2)]
        
    def AddTargetObj(self, *actors):
        self.lstTargetObj = []
        for actor in actors:
            if isinstance(actor, TargetObj):
                self.lstTargetObj.append(actor)
        
    def GetWorldToView(self, pos:_ArrayLike):
        self.SetWorldPoint(np.append(pos, 1))
        self.WorldToView()
        return np.array(self.GetViewPoint())
    
    def GetDisplayToView(self, pos:_ArrayLike):
        self.SetDisplayPoint(pos)
        self.DisplayToView()
        return np.array(self.GetViewPoint())
    
    def GetDisplayToWorld(self, pos:_ArrayLike):
        self.SetDisplayPoint(pos)
        self.DisplayToWorld()
        return np.array(self.GetWorldPoint())[:3]
    
    def GetViewToWorld(self, pos:_ArrayLike):
        self.SetViewPoint(pos)
        self.ViewToWorld()
        return np.array(self.GetWorldPoint())[:3]
        
    def ResetImage(self):
        if self.image and self.imageOrigin:
            self.image.DeepCopy(self.imageOrigin)
            # self.actorImage.GetMapper().SetInputData(self.image)
        
    def SetImageAlgorithm(self, algorithm:ImageAlgorithm):
        algorithm.SetRenderer(self)
        self.algorithm = algorithm
        
    def GetImageInfo(self):
        if self.image:
            origin = self.image.GetOrigin()
            return self.imageDimensions, self.voxelSize, origin
        else:
            return None
        
    def initalBorder(self):
        
        renderWindow = self.GetRenderWindow()
        if not renderWindow:
            return 
           
        border_mapper = vtk.vtkPolyDataMapper2D()
        border_actor = vtk.vtkActor2D()
        
        border_points = vtk.vtkPoints()
        border_points.InsertNextPoint(0, 0, 0)
        border_points.InsertNextPoint(1, 0, 0)
        border_points.InsertNextPoint(1, 1, 0)
        border_points.InsertNextPoint(0, 1, 0)

        border_lines = vtk.vtkCellArray()
        border_lines.InsertNextCell(5)
        border_lines.InsertCellPoint(0)
        border_lines.InsertCellPoint(1)
        border_lines.InsertCellPoint(2)
        border_lines.InsertCellPoint(3)
        border_lines.InsertCellPoint(0)

        border_poly_data = vtk.vtkPolyData()
        border_poly_data.SetPoints(border_points)
        border_poly_data.SetLines(border_lines)
        
        coordinate = vtk.vtkCoordinate()
        coordinate.SetCoordinateSystemToNormalizedViewport()
        coordinate.SetViewport(self)

        border_mapper.SetInputData(border_poly_data)
        border_mapper.SetTransformCoordinate(coordinate)
        border_mapper.TransformCoordinateUseDoubleOn()
        
        border_actor.SetMapper(border_mapper)
        property2D = border_actor.GetProperty()
        property2D.SetColor(0.0, 1.0, 1.0)
        property2D.SetLineWidth(10)
        
        if self.border is None:
            self.AddActor(border_actor)
            self.border = border_actor
            self.border.VisibilityOff()
        
    def updateWL(self, window = None, level = None):
        if not hasattr(self, 'actorSegment'):
            return
        
        if window is not None:
            self.actorSegment.GetProperty().SetColorWindow(window)
            
        if level is not None:
            self.actorSegment.GetProperty().SetColorLevel(level)
            
    def IsRulerVisible(self):
        return self.bRulerVisible
    
    def Segmentation(self, pos:np.ndarray):
        if isinstance(pos, tuple) or isinstance(pos, list):
            pos = np.array(pos)
            
        if self.image is None:
            return
        
        # self.threshold = vtk.vtkImageThreshold()
        # self.threshold.SetInputData(self.image)
        # self.threshold.ThresholdByUpper(100)
        # self.threshold.ReplaceInOn()
        # self.threshold.SetInValue(255)
        # self.threshold.ReplaceOutOn()
        # self.threshold.SetOutValue(0)
        
        # threshold = vtk.vtkImageThreshold()
        # threshold.SetInputData(self.image)
        # threshold.ThresholdByUpper(200)  
        # threshold.SetInValue(255)
        # threshold.SetOutValue(0)  
        # threshold.Update()

        points = vtk.vtkPoints()
        points.InsertNextPoint(pos)
        
        pointsData = vtk.vtkPointSet()
        pointsData.SetPoints(points)
        
        connFilter = vtk.vtkImageConnectivityFilter()
        connFilter.SetInputData(self.image)
        connFilter.GenerateRegionExtentsOn()
        connFilter.SetScalarRange(0, 50)
        connFilter.SetSeedData(pointsData)
        connFilter.Update()
        
        self.connectivityFilter = connFilter
        
        
        
        imageSliceMapper = vtk.vtkImageSliceMapper()
        # imageSliceMapper.SetInputConnection(threshold.GetOutputPort())
        # imageSliceMapper.SetInputConnection(connFilter.GetOutputPort())
        imageSliceMapper.SetInputData(connFilter.GetOutput())
        imageSliceMapper.SliceFacesCameraOn()
        imageSliceMapper.SliceAtFocalPointOn()

        
        imageActor = vtkImageActor()
        imageActor.SetMapper(imageSliceMapper)
        imageActor.GetProperty().SetColorWindow(1)
        imageActor.GetProperty().SetColorLevel(1)
        
        self.actorSegment = imageActor
        
        self.AddActor(self.actorSegment)
        self.actorImage.VisibilityOff()
        
        
                    
        
    
    def ChangeView(self, value):
        """change slice view

        Args:
            value (_int_): location of slice
        """
        ## 改變 slice ############################################################################################
        if isinstance(value, list) or isinstance(value, tuple):
            value = np.array(value)
            
        if isinstance(value, np.ndarray):
            if value.dtype == np.float64:
                if self.orientation == VIEW_AXIAL: 
                    self.target[:] = value
                    self.imagePosition[:] = np.round(value / self.voxelSize)
                    self.actorImage.SetDisplayExtent(0, self.imageDimensions[0] - 1, 0, self.imageDimensions[1] - 1, value, value)
                    self.textActor.SetInput(f'{self.imagePosition[2]}/{self.imageDimensions[2] - 1}')
                elif self.orientation == VIEW_CORONAL: 
                    self.target[:] = value
                    self.imagePosition[:] = np.round(value / self.voxelSize)
                    self.actorImage.SetDisplayExtent(0, self.imageDimensions[0] - 1, value, value, 0, self.imageDimensions[2] - 1)
                    self.textActor.SetInput(f'{self.imagePosition[1]}/{self.imageDimensions[1] - 1}')
                elif self.orientation == VIEW_SAGITTAL: 
                    self.target[:] = value
                    self.imagePosition[:] = np.round(value / self.voxelSize)
                    self.actorImage.SetDisplayExtent(value, value, 0, self.imageDimensions[1] - 1, 0, self.imageDimensions[2] - 1)
                    self.textActor.SetInput(f'{self.imagePosition[0]}/{self.imageDimensions[0] - 1}')
                
            else:
                logger.debug(f'value dtype = {value.dtype}')
                
        else:
            if self.orientation == VIEW_AXIAL: 
                # self.target[2] = value * self.pixel2Mm[2]
                # self.imagePosition[2] = value
                value = max(0, min(self.imageDimensions[2] - 1, value))
                self.actorImage.SetDisplayExtent(0, self.imageDimensions[0] - 1, 0, self.imageDimensions[1] - 1, value, value)
                self.textActor.SetInput(f'{value}/{self.imageDimensions[2] - 1}')
            elif self.orientation == VIEW_CORONAL: 
                value = max(0, min(self.imageDimensions[1] - 1, value))
                self.actorImage.SetDisplayExtent(0, self.imageDimensions[0] - 1, value, value, 0, self.imageDimensions[2] - 1)
                self.textActor.SetInput(f'{value}/{self.imageDimensions[1] - 1}')
            elif self.orientation == VIEW_SAGITTAL: 
                value = max(0, min(self.imageDimensions[0] - 1, value))
                self.actorImage.SetDisplayExtent(value, value, 0, self.imageDimensions[1] - 1, 0, self.imageDimensions[2] - 1)
                self.textActor.SetInput(f'{value}/{self.imageDimensions[0] - 1}')
                
    def GetTarget(self):
        return self.target
    
    def GetViewportInWorld(self):
        renderWindow = self.GetRenderWindow()
        if renderWindow is None:
            return None
        
        viewPort = self.GetViewport()
        renderSize = renderWindow.GetSize()
        viewSize = [viewPort[2] * renderSize[0], viewPort[3] * renderSize[1]]
        
        leftBottom = [0, 0, 0]
        rightTop = [viewSize[0], viewSize[1], 0]
        
        # 将窗口坐标转换为3D坐标
        worldLeftBottom = self.GetDisplayToWorld(leftBottom)
        worldRightTop = self.GetDisplayToWorld(rightTop)
        
        return [worldLeftBottom, worldRightTop]
        
    def SetSelectedOn(self):
        self.bSelected = True
        if self.border:
            self.border.VisibilityOn()
        
    def SetSelectedOff(self):
        self.bSelected = False
        if self.border:
            self.border.VisibilityOff()
        
    def GetSelectedOn(self):
        return self.bSelected
    
    def SetImage(self, image:vtk.vtkImageData, imageOrigin, target, imagePosition):
        self.dicomGrayscaleRange = image.GetScalarRange()
        self.dicomBoundsRange = image.GetBounds()
        self.imageDimensions = image.GetDimensions()
        self.voxelSize = image.GetSpacing()
        self.image = image
        self.imageOrigin = imageOrigin
        self.target = target
        self.imagePosition = imagePosition
        # self.imageOutputPort = imageOutputPort
        
        
    def SetCameraToTarget(self, pos:np.ndarray = None):
        
        if pos is None:
            pos = self.target
            
        # move camera to select point
        camera = self.GetActiveCamera()
        focalPos = np.array(camera.GetFocalPoint())
        cameraPos = np.array(camera.GetPosition())
        viewPlaneNormal = np.array(camera.GetViewPlaneNormal())
        cameraPos = np.array(pos) + viewPlaneNormal * np.linalg.norm(focalPos - cameraPos)
        
        camera.SetFocalPoint(pos)
        camera.SetPosition(cameraPos)
        
    def Update(self):
        if not self.border:
            return
        
        if self.bSelected:
            self.border.VisibilityOn()
        else:
            self.border.VisibilityOff()
        
    
    def InitTarget(self, pos = None):
        
        if self.GetRenderWindow() is None:
            return
        
        if pos is None:
            pos = self.target
        else:
            self.target[:] = np.array(pos)
            
        if not self.bFocusMode:
            self.actorTarget = self.targetObj.InitObj(pos)
            self.isInitialize = True   
            
            # for i in range(len(self.actorTargetScale)):
            #     actor = self.actorTargetScale[i]
            #     self.RemoveActor(actor)
                        
            # self.actorTargetScale = []
            
            # for i in range(len(self.actorTarget)):
            #     p1, p2 = self.targetObj.GetLinePointsByIndex(i)
            #     if p1 is not None and p2 is not None:
            #         self.actorTargetScale.extend(self.drawRuler(pos, p1))
            #         self.actorTargetScale.extend(self.drawRuler(pos, p2))
        
        
    def getProjVector(self, sourceVector:np.ndarray, distVector:np.ndarray):
        if isinstance(sourceVector, list) or isinstance(sourceVector, tuple):
            sourceVector = np.array(sourceVector)
            
        if isinstance(distVector, list) or isinstance(distVector, tuple):
            distVector = np.array(distVector)
            
        distVector = distVector / np.linalg.norm(distVector)
        
        return distVector * np.dot(sourceVector, distVector)

    def drawRuler(self, startPos:np.array, endPos:np.array, scale:float = 10.0):
        if isinstance(startPos, list) or isinstance(startPos, tuple):
            startPos = np.array(startPos)
            
        if isinstance(endPos, list) or isinstance(endPos, tuple):
            endPos = np.array(endPos)
            
        MIN_SCALE = 0.5
        SCALE_LINE_LEN = 10
        SCALE_LINE_LEN_BIG = 30
        
        #計算縮放比例
        p1 = self.GetDisplayToWorld((0, 0, 0))
        p2 = self.GetDisplayToWorld((SCALE_LINE_LEN, 0, 0))
        p3 = self.GetDisplayToWorld((SCALE_LINE_LEN_BIG, 0, 0))
        
        scaleRatio = np.linalg.norm(np.array(p1) - np.array(p2)) * 0.5
        # lengthInWorld = np.linalg.norm(np.array(p1) - np.array(p2)) * 0.5
        # lengthInWorldBig = np.linalg.norm(np.array(p1) - np.array(p3)) * 0.5
        lengthInWorld = SCALE_LINE_LEN * 0.5
        lengthInWorldBig = SCALE_LINE_LEN_BIG * 0.5
        
        if scaleRatio > 10:
            return None
            
        #calculate line scale, minimum is 0.5mm
        scale = max(scale, MIN_SCALE)
        length = np.linalg.norm(endPos - startPos)
        
        if length < scale or np.isnan(length):
            return None
        
        count = 0
        try:
            count = int(length / scale)
            lines = [vtkLineSource() for _ in range(count)]
            actorTargetScale = [vtkActor2D() for _ in range(count)]
        except Exception as msg:
            logger.debug(msg)
            logger.debug(f'length = {length}, scale = {scale}')
        
        unitVector = (endPos - startPos) / length
        viewPlaneVector = self.camera.GetViewPlaneNormal()
        
        crossVector = np.cross(unitVector, viewPlaneVector)
        crossVectorLittle = crossVector * lengthInWorld
        crossVectorBig = crossVector * lengthInWorldBig
        
        coord2D = vtkCoordinate()
        coord2D.SetCoordinateSystemToWorld()
        # coord2D.SetCoordinateSystemToDisplay()
        
        stepPos = startPos.copy()
        for i in range(count):
            stepPos += unitVector * scale
            
            if i % 5 == 4:
                lines[i].SetPoint1(stepPos - crossVectorBig)
                lines[i].SetPoint2(stepPos + crossVectorBig)
            else:
                if scaleRatio < 4:
                    lines[i].SetPoint1(stepPos - crossVectorLittle)
                    lines[i].SetPoint2(stepPos + crossVectorLittle)
                else:
                    continue
            
            mapper = vtkPolyDataMapper2D()
            mapper.SetInputConnection(lines[i].GetOutputPort())
            mapper.SetTransformCoordinate(coord2D) 
        
            actorTargetScale[i].SetMapper(mapper)   
            actorTargetScale[i].GetProperty().SetColor(1, 0, 1)
            actorTargetScale[i].GetProperty().SetLineWidth(1.0)  
            actorTargetScale[i].SetVisibility(self.bTargetVisible) 
            
            self.AddActor(actorTargetScale[i])
            
        return actorTargetScale
    
    def drawRuler2(self, viewStartPos:np.array, viewEndPos:np.array):
        """draw a ruler between two view points
            if not VIEW coordinate, must be transformed to view coordinate point 
        Args:
            viewStartPos (np.array): view coordinate point
            viewEndPos (np.array): view coordinate point

        Returns:
            _type_: list[vtkActor2D]
        """
        if isinstance(viewStartPos, (list, tuple, np.ndarray)):
            startPos = np.array(viewStartPos)
        else:
            return None
            
        if isinstance(viewEndPos, (list, tuple, np.ndarray)):
            endPos = np.array(viewEndPos)
        else:
            return None
            
        MIN_SCALE = 10
        SCALE_LINE_LEN = 10
        SCALE_LINE_LEN_BIG = 30
        
        # view座標系中心點(原點)
        p0 = self.GetDisplayToView((0, 0, 0))
        
        # 尺標的小刻度
        pViewLen = self.GetDisplayToView((SCALE_LINE_LEN, 0, 0))
        
        # 尺標的大刻度
        pViewLenBig = self.GetDisplayToView((SCALE_LINE_LEN_BIG, 0, 0))
        
        # 判斷是世界座標的哪一軸，並乘上對應的voxel size
        worldStartPos = self.GetViewToWorld(startPos)
        worldEndPos = self.GetViewToWorld(endPos)
        diff = np.abs(worldEndPos - worldStartPos)
        voxelSize = self.voxelSize[np.argmax(diff)]
        
        # view座標系中，X Y方向的單位距離不同，要分開計算
        p4 = np.zeros(3)
        if abs(startPos[0] - endPos[0]) < abs(startPos[1] - endPos[1]):
            p4 = self.GetDisplayToView((0, MIN_SCALE / voxelSize, 0))
        else:
            p4 = self.GetDisplayToView((MIN_SCALE / voxelSize, 0, 0))
            
            
        # 換算在view座標系的實際長度
        scaleRatio = np.linalg.norm(p0 - pViewLen) * 0.5
        scaleRatioBig = np.linalg.norm(p0 - pViewLenBig) * 0.5
        scaleMin = np.linalg.norm(p0 - p4)
        
        # zoom in / out時，view座標系的長度會改變，計算實際Zoom in / out 縮放比例
        p5 = self.GetDisplayToWorld((0, 0, 0))
        p6 = self.GetDisplayToWorld((SCALE_LINE_LEN, 0, 0))
        
        ratio = np.linalg.norm(p5 - p6)
        
        if ratio == 0 or np.isnan(ratio):
            ratio = 1
        ratio = SCALE_LINE_LEN / ratio
        
        scaleMin *= ratio
        ratio = min(2.0, ratio)
        scaleRatio *= ratio
        scaleRatioBig *= ratio
        
        # lengthInWorld = np.linalg.norm(np.array(p1) - np.array(p2)) * 0.5
        # lengthInWorldBig = np.linalg.norm(np.array(p1) - np.array(p3)) * 0.5
        # lengthInWorld = scaleRatio
        lengthInWorldBig = scaleRatioBig
            
        #calculate line scale, minimum is 0.5mm
        # worldEndPos = self.GetViewToWorld(endPos)
        # worldStartPos = self.GetViewToWorld(startPos)
        length = np.linalg.norm(endPos - startPos)
        
        if np.isnan(length):
            return None
        
        count = 0
        try:
            count = int(length / scaleMin)
            lines = [vtkLineSource() for _ in range(count)]
            actorTargetScale = [vtkActor2D() for _ in range(count)]
        except Exception as msg:
            logger.debug(msg)
            logger.debug(f'length = {length}, scale = {scaleMin}')
        
        unitVector = (endPos - startPos) / length
        # viewPlaneVector = self.camera.GetViewPlaneNormal()
        viewPlaneVector = np.array([0, 0, 1])
        
        crossVector = np.cross(unitVector, viewPlaneVector)
        crossVectorLittle = crossVector * scaleRatio
        crossVectorBig = crossVector * lengthInWorldBig
        
        coord2D = vtkCoordinate()
        coord2D.SetCoordinateSystemToView()
        # coord2D.SetCoordinateSystemToDisplay()
        
        stepPos = startPos.copy()
        for i in range(count):
            stepPos += unitVector * scaleMin
            
            if i % 5 == 4:
                lines[i].SetPoint1(stepPos - crossVectorBig)
                lines[i].SetPoint2(stepPos + crossVectorBig)
            else:
                if scaleRatio < 4:
                    lines[i].SetPoint1(stepPos - crossVectorLittle)
                    lines[i].SetPoint2(stepPos + crossVectorLittle)
                else:
                    continue
            
            mapper = vtkPolyDataMapper2D()
            mapper.SetInputConnection(lines[i].GetOutputPort())
            mapper.SetTransformCoordinate(coord2D) 
        
            actorTargetScale[i].SetMapper(mapper)   
            actorTargetScale[i].GetProperty().SetColor(1, 0, 1)
            actorTargetScale[i].GetProperty().SetLineWidth(1.0)  
            actorTargetScale[i].SetVisibility(self.bTargetVisible) 
            
            self.AddActor(actorTargetScale[i])
            
        return actorTargetScale
    
    def SetFocusMode(self, bFocus):
        self.bFocusMode = bFocus
        if not bFocus:
            for actorTarget in self.actorTarget:
                actorTarget.VisibilityOn()
                
            for actor in self.actorTargetScale:
                actor.VisibilityOn()
                
            for actor in self.actorTargetCenter:
                actor.VisibilityOff()
        else:
            for actorTarget in self.actorTarget:
                actorTarget.VisibilityOff()
                
            for actor in self.actorTargetScale:
                actor.VisibilityOff()
                
            for actor in self.actorTargetCenter:
                actor.VisibilityOn()
                
    def SetRulerVisible(self, bVisible:bool):
        
        self.bRulerVisible = bVisible
        for actor in self.actorTargetScale:
            actor.SetVisibility(bVisible) 
            
     
    def SetTargetVisible(self, bVisible = True):
        for actor in self.actorTarget:
            actor.SetVisibility(bVisible) 
            
        for actor in self.actorTargetScale:
            actor.SetVisibility(bVisible) 
                      
        for actor in self.actorTargetCenter:
            actor.SetVisibility(bVisible)       
            
        self.bTargetVisible = bVisible    
        
    def SetTarget2D(self):
        self.targetObj.SetInViewportCenter()
        
    
    def SetTarget(self, pos = None):
        
        if pos is None:
                pos = self.target
        else:
            self.target[:] = np.array(pos)
                
        imagePos = np.round(pos / self.voxelSize)
        
        if not self.bFocusMode:
            if self.isInitialize == False:
                self.InitTarget(pos)
                return
            
            if TargetObj.bVisible:
                lines = self.targetObj.SetPosition(pos)
            
                for actor in self.actorTargetScale:
                    self.RemoveActor(actor)
                            
                self.actorTargetScale = []
                
                pos = self.GetWorldToView(pos)
                for i in range(len(self.actorTarget)):
                    p1, p2 = self.targetObj.GetLinePointsByIndex(i) 
                    if p1 is not None and p2 is not None:
                        r1 = self.drawRuler2(pos, p1)
                        r2 = self.drawRuler2(pos, p2)
                        
                        if r1:
                            self.actorTargetScale.extend(r1)
                            
                        if r2:
                            self.actorTargetScale.extend(r2)
                    
                for i in range(len(lines)):
                    mapper = self.actorTarget[i].GetMapper()
                    if mapper is not None:
                        mapper.SetInputConnection(lines[i].GetOutputPort())
            
        else:
            # self.SetCameraToTarget()
            
            self.actorTargetCenter = self.targetObj.SetInViewportCenter()
            viewPos = self.GetWorldToView(pos)
            # draw ruler
            pointsMap = {}
            pointsMap['top']     = [ 0,-1, viewPos[2]]
            pointsMap['bottom']  = [ 0, 1, viewPos[2]]
            pointsMap['left']    = [-1, 0, viewPos[2]]
            pointsMap['right']   = [ 1, 0, viewPos[2]]
            
            # for point in pointsMap.values():
            #     point[:] = self.GetViewToWorld(point)

            if self.bRulerVisible:
                for actor in self.actorTargetScale:
                    self.RemoveActor(actor)
                            
                self.actorTargetScale = []
                
                viewOrigin = [0, 0, viewPos[2]]
                for p in pointsMap.values():
                    ruler = self.drawRuler2(viewOrigin, p)
                    if ruler:
                        self.actorTargetScale.extend(ruler)
    
    
    def SetMapColor(self, windowLevelLookup):
        if self.imageReslice is not None:
            self.mapColor.SetInputConnection(self.imageReslice.GetOutputPort())
        else:
            self.mapColor.SetInputData(self.image)
            # self.mapColor.SetInputConnection(self.imageOutputPort)
            
        self.mapColor.SetLookupTable(windowLevelLookup)
        self.mapColor.Update()
        self.windowLevelLookup = windowLevelLookup
        
    def SetCamera(self, orientation:str):
        if not isinstance(orientation, str):
            logger.debug(f'parameter "orientation" is not str type')
            return
        
        center = np.array(self.imageDimensions).astype(float) * 0.5
        center = center.astype(int)
        # center = np.zeros(3).astype(int)
        
        # orientation = orientation.lower()
        if orientation == VIEW_SAGITTAL:
            
            self.camera.SetViewUp(0, 0, 1)
            self.camera.SetPosition(1, 0, 0)
            self.actorImage.GetMapper().SetInputConnection(self.mapColor.GetOutputPort())
            self.actorImage.SetDisplayExtent(center[0], center[0], 0, self.imageDimensions[1], 0, self.imageDimensions[2])
            self.textActor.SetInput(f'{center[0]}/{self.imageDimensions[0] - 1}')
        elif orientation == VIEW_CORONAL:
            
            self.camera.SetViewUp(0, 0, 1)
            self.camera.SetPosition(0, -1, 0)
            self.actorImage.GetMapper().SetInputConnection(self.mapColor.GetOutputPort())
            self.actorImage.SetDisplayExtent(0, self.imageDimensions[0], center[1], center[1], 0, self.imageDimensions[2])
            self.textActor.SetInput(f'{center[1]}/{self.imageDimensions[1] - 1}')
        elif orientation == VIEW_AXIAL:
            self.camera.SetViewUp(0, -1, 0)
            self.camera.SetPosition(0, 0, -1)
            
            self.actorImage.GetMapper().SetInputConnection(self.mapColor.GetOutputPort())
            self.actorImage.SetDisplayExtent(0, self.imageDimensions[0], 0, self.imageDimensions[1], center[2], center[2])
            self.textActor.SetInput(f'{center[2]}/{self.imageDimensions[2] - 1}')
        elif orientation == VIEW_CROSS_SECTION:
            self.camera.SetViewUp(0, 1, 0)
            self.camera.SetPosition(0, 0, 1)
            self.actorImage.GetMapper().SetInputConnection(self.mapColor.GetOutputPort())
            
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.ComputeViewPlaneNormal()
        self.camera.ParallelProjectionOn()
        self.orientation = orientation

        # self.textActor.SetAlignmentPoint(2)
        self.textActor.SetTextScaleModeToNone()  # 避免文字縮放
        self.textActor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
        self.textActor.SetPosition(0.98, 0.95)  # 設定文字位置 (右上角)
        self.textActor.GetTextProperty().SetJustificationToRight()
        self.textActor.GetTextProperty().SetFontSize(16)
        self.textActor.GetTextProperty().SetColor(1.0, 1.0, 0.0)  # 設定文字顏色
        
        self.AddActor(self.textActor)
        
        "render"
        "Sagittal"
        self.SetBackground(0, 0, 0)
        self.AddActor(self.actorImage)
        self.SetActiveCamera(self.camera)
        self.ResetCamera(self.dicomBoundsRange)
        self.camera.Zoom(1.8)
        
        
    
class RendererObj3D(RendererObj):
    def __init__(self):
        super().__init__()
        self.actorTarget3D = vtkAssembly()
        
        
    def InitTarget(self, pos = None, size = 40):
        prop3Ds = self.actorTarget3D.GetParts()
        prop3Ds.RemoveAllItems()
        
        # if pos is None:
        #     pos = self.target
        # else:
        #     self.target[:] = pos
        
       
        
        #line 1
        line1 = vtkLineSource()
        line1.SetPoint1(0, 0,  - size)
        line1.SetPoint2(0, 0,  + size)
        # line1.SetPoint1(pos[0], pos[1], pos[2] - size)
        # line1.SetPoint2(pos[0], pos[1], pos[2] + size)
        
        mapper1 = vtkPolyDataMapper()
        mapper1.SetInputConnection(line1.GetOutputPort())
        
        actorTarget = [vtkActor() for _ in range(3)]
        actorTarget[0].SetMapper(mapper1)   
        actorTarget[0].GetProperty().SetColor(1, 1, 0)
        actorTarget[0].GetProperty().SetLineWidth(3.0)
        
        #line 2
        line2 = vtkLineSource()
        line2.SetPoint1(0,  - size, 0)
        line2.SetPoint2(0,    size, 0)
        
        mapper2 = vtkPolyDataMapper()
        mapper2.SetInputConnection(line2.GetOutputPort())
        
        actorTarget[1].SetMapper(mapper2)   
        actorTarget[1].GetProperty().SetColor(1, 1, 0)
        actorTarget[1].GetProperty().SetLineWidth(3.0)
        
        #line 3
        line3 = vtkLineSource()
        line3.SetPoint1( - size, 0, 0)
        line3.SetPoint2( + size, 0, 0)
        
        mapper3 = vtkPolyDataMapper()
        mapper3.SetInputConnection(line3.GetOutputPort())
        
        actorTarget[2].SetMapper(mapper3)   
        actorTarget[2].GetProperty().SetColor(1, 1, 0)
        actorTarget[2].GetProperty().SetLineWidth(3.0)
        
        for actor in actorTarget:
            self.actorTarget3D.AddPart(actor)      
        
        self.AddActor(self.actorTarget3D)
        self.isInitialize = True

    
    # function開頭小寫表示將來C++ 是private function
    # 用來另外計算Volume實際上點寫的座標位置
    def getVolumeTarget(self, pos):
        if self.image is None or pos is None:
            return None
        
        if isinstance(pos, tuple) or isinstance(pos, list):
            pos = np.array(pos)
        
        volumePos = pos.copy()
        center = np.array(self.imageDimensions) * np.array(self.voxelSize) * 0.5
        volumePos -= center
        return volumePos
    
    def ResetImage(self):
        if self.image and self.imageOrigin:
            self.image.DeepCopy(self.imageOrigin)
            self.volume.GetMapper().SetInputData(self.image)
        
    
    def SetTarget(self, pos = None):
        
        if pos is None:
            pos = self.target
        else:
            self.target[:] = pos
            
        if self.isInitialize == False:
            self.InitTarget(pos)
            return
        
        # if self.image is not None:
        #     imageIndex = [0] * 3
        #     pcoord = [0] * 3
        #     self.image.ComputeStructuredCoordinates(pos, imageIndex, pcoord)
            
        self.actorTarget3D.SetPosition(pos)
        
    def SetTargetVisible(self, bVisible = True):
        self.actorTarget3D.SetVisibility(bVisible)  
        
    def SetCamera(self, *args):
        self.orientation = args[0]
               
        self.camera.SetViewUp(0, 0, 1)
        self.camera.SetPosition(0.0, 1, 0)
        self.camera.SetFocalPoint(0, 0, 0)
        self.camera.ComputeViewPlaneNormal()
        self.camera.ParallelProjectionOn()
        
        "3D"
        self.SetBackground(0, 0, 0)
        self.SetVolumeRender()
        
        self.SetActiveCamera(self.camera)
        self.ResetCamera(self.dicomBoundsRange)
        
    def SetVolumeRender(self):
        
        volumeMapper = vtk.vtkFixedPointVolumeRayCastMapper()
        # volumeMapper = vtk.vtkOpenGLGPUVolumeRayCastMapper()
        volumeMapper.SetInputData(self.image)
        volumeMapper.SetBlendModeToComposite()
        
        
        volumeProperty = vtkVolumeProperty()
        volumeProperty.SetInterpolationTypeToLinear()
        volumeProperty.ShadeOn()
        volumeProperty.SetAmbient(0.1)
        volumeProperty.SetDiffuse(1.0)
        volumeProperty.SetSpecular(0.2)
        volumeProperty.SetSpecularPower(10)
        volumeProperty.SetScalarOpacityUnitDistance(0.8919)
        # volumeProperty.SetIndependentComponents(True)
        
        windowLevel = self.windowLevelLookup.GetLevel()
        windowWidth = self.windowLevelLookup.GetWindow()
        windowWidth = numpy.fmax(windowWidth, 1.0)
        
        # compositeOpacity = vtk.vtkPiecewiseFunction()
        # compositeOpacity.AddPoint(windowLevel - windowWidth, 0.0)
        # compositeOpacity.AddPoint( windowLevel, 0.8)
        # compositeOpacity.AddPoint( windowLevel + windowWidth, 1.0)
        # volumeProperty.SetScalarOpacity(compositeOpacity)
        
        color = vtk.vtkColorTransferFunction()
        color.AddRGBPoint(-30768,    0,    0,    0,  0.5, 0)
        color.AddRGBPoint( -200, 0.62, 0.36, 0.18,  0.5, 0)
        color.AddRGBPoint( -100, 0.88, 0.60, 0.29, 0.33, 0.45)
        color.AddRGBPoint(  500, 0.90, 0.82, 0.56, 0.50, 0.0)
        color.AddRGBPoint( 3071, 0.83, 0.66, 1.00,  0.5, 0.0)
        
        # color.AddRGBPoint(-3024, 0, 0, 0, 0.5, 0.0)
        # color.AddRGBPoint(-155, .55, .25, .15, 0.5, .92)
        # color.AddRGBPoint(217, .88, .60, .29, 0.33, 0.45)
        # color.AddRGBPoint(420, 1, .94, .95, 0.5, 0.0)
        # color.AddRGBPoint(3071, .83, .66, 1, 0.5, 0.0)
        volumeProperty.SetColor(color)
        
        gradientOpacity = vtk.vtkPiecewiseFunction()
        gradientOpacity.AddPoint(-30768, 0.0, 0.5, 0.0)
        gradientOpacity.AddPoint( -200, 0.0, 0.5, 0.0)
        gradientOpacity.AddPoint( -100, 0.08, 1.0, 1.0)
        gradientOpacity.AddPoint(  500, 1.0, 0.5, 0.0)
        gradientOpacity.AddPoint( 3071, 1.0, 0.5, 0.0)
        
        # gradientOpacity.AddPoint(-3024, 0, 0.5, 0.0)
        # gradientOpacity.AddPoint(-155, 0, 0.5, 0.92)
        # gradientOpacity.AddPoint(217, .68, 0.33, 0.45)
        # gradientOpacity.AddPoint(420, .83, 0.5, 0.0)
        # gradientOpacity.AddPoint(3071, .80, 0.5, 0.0)
        # volumeProperty.SetGradientOpacity(gradientOpacity)
        volumeProperty.SetScalarOpacity(gradientOpacity)
        self.volumeMapper = volumeMapper
        
        self.volume = vtkVolume()
        self.volume.SetMapper(volumeMapper)
        self.volume.SetProperty(volumeProperty)
        
        self.AddActor(self.volume)
    
        
class RendererCrossSectionObj(RendererObj):
    # entryPoint  = None
    # targetPoint = None
    targetCS    = None
    actorCircle = None
    
    def __init__(self):
        super().__init__()
        
    def ChangeView(self, value):
        """change slice view

        Args:
            value (_int_): location of slice
        """
        ## 改變 slice ############################################################################################
        self.SetCrossSectionDelta(value)
        
        
    def FocusTarget(self):
        self.SetCrossSectionDelta(0)
        
    def FocusEntry(self):
        delta = np.linalg.norm(self.entryPoint - self.targetPoint)
        self.SetCrossSectionDelta(delta)
        
    def GetTrajectoryLength(self):
        if self.entryPoint is None or self.targetPoint is None:
            return None
        
        vector = np.array(self.entryPoint) - np.array(self.targetPoint)
        length = np.linalg.norm(vector)
        return length
        
    def GetImageReslice(self):
        if not hasattr(self, 'imageReslice'):
            return None
        else:
            return self.imageReslice.GetOutput()
        
    def GetImageExtent(self):
        if not hasattr(self, 'imageReslice'):
            return None
        else:
            return self.imageReslice.GetOutput().GetDimensions()
        
    # Get normal slice position from cross-section slice position
    def GetPositionFromCrossSection(self, posCS):
        if isinstance(posCS, tuple) or isinstance(posCS, list):
            posCS = np.array(posCS)
            
        if not isinstance(posCS, np.ndarray):
            logger.debug(f'posCS type error')
            return None
        
        if posCS.shape[0] < 3:
            logger.debug(f'dimensions of posCS is little than 3')
            return None
        
        if posCS.shape[0] == 3:
            posCS = np.append(posCS, 1)
        
        
        if self.imageReslice is None:
            logger.debug(f'imageReslice is not exist')
            return None
        
        matrix = self.imageReslice.GetResliceAxes()
        
        pos = np.zeros(4)
        matrix.MultiplyPoint(posCS, pos)
        pos = pos[:3]
        
        return pos
    
    # Get cross-section slice position from normal slice position
    def GetCrossSectionFromPosition(self, pos):
        if isinstance(pos, tuple) or isinstance(pos, list):
            pos = np.array(pos)
            
        if not isinstance(pos, np.ndarray):
            logger.debug(f'pos type error')
            return None
        
        if pos.shape[0] < 3:
            logger.debug(f'dimensions of pos is little than 3')
            return None
        
        
        if self.imageReslice is None:
            logger.debug(f'imageReslice not exist')
            return None
            
        if pos.shape[0] == 3:
            self.imageReslice.SetResliceAxesOrigin(pos)
            pos = np.append(pos, 1)
        else:
            self.imageReslice.SetResliceAxesOrigin(pos[:3])
            pos = np.append(pos[:3], 1)
            
        self.imageReslice.Update()
        
        matrix = vtk.vtkMatrix4x4()
        matrix.DeepCopy(self.imageReslice.GetResliceAxes())
        matrix.Invert()
        
        posCS = np.zeros(4)
        matrix.MultiplyPoint(pos, posCS)
        posCS = posCS[:3]
        
        return posCS
    
    def SetCrossSectionPosition(self, pos:np.ndarray):
        if self.targetPoint is None or self.entryPoint is None:
            return None
        
        if isinstance(pos, tuple) or isinstance(pos, list):
            pos = np.array(pos)
        
        vector = pos - self.targetPoint
        length = np.linalg.norm(vector)
        
        vectorTraj = self.entryPoint - self.targetPoint
        lengthTraj = np.linalg.norm(vectorTraj)
        vectorTraj_norm = vectorTraj / lengthTraj
        
        cos = np.dot(vectorTraj_norm, vector / length)
        
        vectorProject = vectorTraj_norm * (length * cos)
        delta = np.linalg.norm(vectorProject)
        # print(f'delta = {delta}, length of trajectory = {lengthTraj}')
        self.SetCrossSectionDelta(delta)
    
    def SetCrossSectionDelta(self, delta:float):
        if self.targetPoint is None or self.entryPoint is None:
            return None
        
        vector = self.entryPoint - self.targetPoint
        vectorUnit = vector / np.linalg.norm(vector)
        newTarget = self.targetPoint + vectorUnit * delta
        # saveTarget = self.targetPoint
        # print(f'target = {self.targetPoint}, value = {delta}, newTarget = {newTarget}')
        
        self.imageReslice.SetResliceAxesOrigin(newTarget)
        
        
        position = self.GetCrossSectionFromPosition(newTarget)
        self.checkTargetVisible(newTarget)
        
        # distance = np.linalg.norm(newTarget - self.targetPoint)
        # if distance > 0.5:
        #     for actor in self.actorTargetPoint:
        #         actor.VisibilityOff()
        # else:
        #     for actor in self.actorTargetPoint:
        #         actor.VisibilityOn()
        
        if position is None:
            logger.debug('position of Cross-Section is None')
            return None
        
        self.SetCameraToTarget(position)
        self.SetTarget(position, newTarget)
        return newTarget
        
    
    def SetCrossSectionView(self,  target, entry, image = None):
        """change cross section view

        Args:
            position (_np.ndarray_): location of image position
        """
        ## 改變 slice ############################################################################################

        if isinstance(target, (tuple, list, np.ndarray)):
            target = np.asarray(target)
        else:
            logger.error(f'variant "position" type error')
            return
        
        if isinstance(entry, (tuple, list, np.ndarray)):
            entry = np.asarray(entry)
        else:
            logger.error(f'variant "position" type error')
            return
        
        coord2D = vtkCoordinate()
        coord2D.SetCoordinateSystemToWorld()
        
        vector = np.array(entry - target)
        length = np.linalg.norm(vector)
        length = length if length > 0 else 1
        vector = vector / length
        
        viewPlaneVector = np.array([0, 0, 1])
        angle = vtk.vtkMath.AngleBetweenVectors(vector, viewPlaneVector)
        
        axis = np.cross(vector, viewPlaneVector)
        length = np.linalg.norm(axis)
        length = length if length > 0 else 1
        axis = axis / length
                
        transform = vtk.vtkTransform()
        transform.RotateWXYZ(angle * 180.0 / np.pi, axis)
        
        # get image info
        # self.SetImage(image)
        self.image = image if image is not None else self.image
            
        if self.image is None:
            logger.debug(f'imageReslice is NULL')
            return
        
        matrix = transform.GetMatrix()
        
        self.imageReslice = vtkImageReslice()
        self.imageReslice.SetResliceAxes(matrix)
        self.imageReslice.SetResliceAxesOrigin(target)
        
        self.imageReslice.SetInputData(self.image)
        # self.imageReslice.SetInputConnection(self.imageOutputPort)
        self.imageReslice.SetOutputDimensionality(2)
        self.imageReslice.SetInterpolationModeToLinear()
        
        self.imageReslice.SetBackgroundLevel(self.dicomGrayscaleRange[0])
        
        self.mapColor.SetInputConnection(self.imageReslice.GetOutputPort())
        self.mapColor.Update()
        
        #Add 2D target point line
        c = vtkCoordinate()
        c.SetCoordinateSystemToWorld()
        
        posCS = self.GetCrossSectionFromPosition(target)
        
        # self.SetTarget(posCS)
        
        #circle
        # circle = vtk.vtkRegularPolygonSource()
        # circle.SetNumberOfSides(50)  
        # circle.SetRadius(20.0)       
        # circle.SetCenter(pos)
        circleLine = vtkLineSource()
        points = vtk.vtkPoints()
        for i in range(50):
            angle = 2.0 * np.pi * i / 50
            x = 20.0 * np.cos(angle)
            y = 20.0 * np.sin(angle)
            points.InsertNextPoint([posCS[0] + x, posCS[1] +y, posCS[2]])
            
        points.InsertNextPoint(points.GetPoint(0))
        circleLine.SetPoints(points)
        
        mapperCircle = vtk.vtkPolyDataMapper2D()
        mapperCircle.SetInputConnection(circleLine.GetOutputPort())
        mapperCircle.SetTransformCoordinate(coord2D)
        
        if self.actorCircle is None:
            self.actorCircle = vtkActor2D()
            self.actorCircle.SetMapper(mapperCircle)
            self.actorCircle.GetProperty().SetColor(1, 1, 0)
            self.actorCircle.GetProperty().SetLineWidth(2.0)
            self.AddActor(self.actorCircle)
        else:
            self.actorCircle.SetMapper(mapperCircle)
            
        
        # line1 = vtkLineSource()
        # line1.SetPoint1(posCS[0] - 40, posCS[1], posCS[2])
        # line1.SetPoint2(posCS[0] + 40, posCS[1], posCS[2])
        
        # mapper1 = vtkPolyDataMapper2D()
        # mapper1.SetInputConnection(line1.GetOutputPort())
        # mapper1.SetTransformCoordinate(c)
        
        # self.actorTargetPoint[0].SetMapper(mapper1)   
        # self.actorTargetPoint[0].GetProperty().SetColor(1, 1, 0)
        # self.actorTargetPoint[0].GetProperty().SetLineWidth(2.0)
        
        # line2 = vtkLineSource()
        # line2.SetPoint1(posCS[0], posCS[1] - 40, posCS[2])
        # line2.SetPoint2(posCS[0], posCS[1] + 40, posCS[2])
        
        # mapper2 = vtkPolyDataMapper2D()
        # mapper2.SetInputConnection(line2.GetOutputPort())
        # mapper2.SetTransformCoordinate(c)
        
        # self.actorTargetPoint[1].SetMapper(mapper2)   
        # self.actorTargetPoint[1].GetProperty().SetColor(1, 1, 0)
        # self.actorTargetPoint[1].GetProperty().SetLineWidth(2.0)
        
        # for actor in self.actorTargetPoint:
        #     self.AddActor(actor)
        
        
        self.entryPoint = entry
        self.targetPoint = target
        
    def checkTargetVisible(self, pos = None, posCS = None):
        if self.actorCircle is None:
            return None
        
        if posCS is None and pos is None:
            logger.debug(f'function "checkTargetVisible" at least one parameter is required')
            return
        
        elif pos is None:
            currentPos = self.GetPositionFromCrossSection(posCS)
        else:
            currentPos = pos
        
        distance = np.linalg.norm(currentPos - self.targetPoint)
                
        if distance > 0.5:
            self.actorCircle.VisibilityOff()
            # for actor in self.actorTargetPoint:
            #     actor.VisibilityOff()
        else:
            self.actorCircle.VisibilityOn()
            # for actor in self.actorTargetPoint:
            #     actor.VisibilityOn()
        
    def InitTarget(self, pos = None, posOriginal = None):
        
        if self.GetRenderWindow() is None:
            return
        
            
        if pos is None:
            pos = self.GetCrossSectionFromPosition(self.target)
        
        self.actorTarget = self.targetObj.InitObj(pos)
            
        self.isInitialize = True    

    
    
    def SetTarget(self, pos = None, posOriginal = None):
        
        if pos is None and posOriginal is None:
            pos = self.GetCrossSectionFromPosition(self.target)
            if pos is None:
                logger.debug('pos in RendererCrossSectionObj.SetTarget is None')
                return
            
            self.targetCS = pos
            posOriginal = self.target
        else:
            if posOriginal is not None:
                self.target[:] = posOriginal
            else:
                posOriginal = self.GetPositionFromCrossSection(pos)
                if posOriginal is not None:
                    self.target[:] = posOriginal
                else:
                    logger.debug('posOriginal is None')
                    return
                    
            if pos is None:
                pos = self.GetCrossSectionFromPosition(self.target)
                if pos is None:
                    logger.debug('pos in RendererCrossSectionObj.SetTarget is None')
                    return
            self.targetCS = pos
        
        if self.isInitialize == False:
            self.InitTarget(pos, posOriginal)
            return
        
        self.checkTargetVisible(posOriginal)
        
        if not self.bFocusMode:
            lines = self.targetObj.SetPosition(pos)
            
            for i in range(len(self.actorTargetScale)):
                actor = self.actorTargetScale[i]
                self.RemoveActor(actor)
                        
            self.actorTargetScale = []
            
            pos = self.GetWorldToView(pos)
            for i in range(len(self.actorTarget)):
                p1, p2 = self.targetObj.GetLinePointsByIndex(i)
                if p1 is not None and p2 is not None:
                    self.actorTargetScale.extend(self.drawRuler2(pos, p1))
                    self.actorTargetScale.extend(self.drawRuler2(pos, p2))
                
            for i in range(len(lines)):
                mapper = self.actorTarget[i].GetMapper()
                if mapper is not None:
                    mapper.SetInputConnection(lines[i].GetOutputPort())
        else:
           
            self.targetObj.SetInViewportCenter()
            
        self.SetFocusMode(self.bFocusMode)
                
class TargetObj():
    bVisible = True
    
    def __init__(self, renderer:RendererObj):
        self.renderer = renderer
        
        self.actorLineCenter = None
        self.position = None
        self.lines = []
        self.linesPoint = []
        self.bHide = False
        
    def InitObj(self, pos:np.ndarray):
        if isinstance(pos, tuple) or isinstance(pos, list):
            pos = np.array(pos)
        
        viewPort = self.renderer.GetViewport()
        renderSize = self.renderer.GetRenderWindow().GetSize()
        viewSize = [viewPort[2] * renderSize[0], viewPort[3] * renderSize[1]]
        
        leftBottom = [0, 0, 0]
        rightTop = [viewSize[0], viewSize[1], 0]
        
        # 将窗口坐标转换为3D坐标
       
        # self.renderer.SetDisplayPoint(leftBottom[0], leftBottom[1], leftBottom[2])
        # self.renderer.DisplayToWorld()
        # worldLeftBottom = self.renderer.GetWorldPoint()

        # self.renderer.SetDisplayPoint(rightTop[0], rightTop[1], rightTop[2])
        # self.renderer.DisplayToWorld()
        # worldRightTop = self.renderer.GetWorldPoint()
        
        self.renderer.SetWorldPoint(np.append(pos, 1))
        self.renderer.WorldToView()
        viewPos = self.renderer.GetViewPoint()
        

        coord2D = vtkCoordinate()
        coord2D.SetCoordinateSystemToView()
        
        # vectorUp = self.renderer.camera.GetViewUp()
        # vectorViewPlane = self.renderer.camera.GetViewPlaneNormal()
        # vectorLeft = np.cross(vectorViewPlane, vectorUp)
        # vectorViewWidthHalf = (np.array(worldLeftBottom) - np.array(worldRightTop))
           
        self.lines = []
        self.linesPoint = []
        actorTarget = [vtkActor2D() for _ in range(2)]  
        
        #line 1
        line1 = vtkLineSource()
        # vectorProjLeft = self.renderer.getProjVector(vectorViewWidthHalf[:3], vectorLeft)
        # point1 = pos + vectorProjLeft
        # point2 = pos - vectorProjLeft
        point1 = [-1, viewPos[1], viewPos[2]]
        point2 = [ 1, viewPos[1], viewPos[2]]
        line1.SetPoint1(point1)
        line1.SetPoint2(point2)
        self.linesPoint.append([point1, point2])
        
        self.lines.append(line1)
        
        mapper1 = vtkPolyDataMapper2D()
        mapper1.SetInputConnection(line1.GetOutputPort())
        mapper1.SetTransformCoordinate(coord2D) 
        
        actorTarget[0].SetMapper(mapper1)   
        actorTarget[0].GetProperty().SetColor(1, 0, 0)
        actorTarget[0].GetProperty().SetLineWidth(2.0)
        
        #line 2
        line2 = vtkLineSource()
        # vectorProjUp = self.renderer.getProjVector(vectorViewWidthHalf[:3], vectorUp)
        # point1 = pos + vectorProjUp
        # point2 = pos - vectorProjUp
        point1 = [viewPos[0],-1, viewPos[2]]
        point2 = [viewPos[0], 1, viewPos[2]]
        line2.SetPoint1(point1)
        line2.SetPoint2(point2)
        self.linesPoint.append([point1, point2])
        
        self.lines.append(line2)
        
        mapper2 = vtkPolyDataMapper2D()
        mapper2.SetInputConnection(line2.GetOutputPort())
        mapper2.SetTransformCoordinate(coord2D) 
        
        actorTarget[1].SetMapper(mapper2)   
        actorTarget[1].GetProperty().SetColor(1, 0, 0)
        actorTarget[1].GetProperty().SetLineWidth(2.0)
        
        for actor in actorTarget:
            self.renderer.AddActor(actor) 
            actor.SetVisibility(TargetObj.bVisible)
            
        self.position = pos.copy()
        return actorTarget
    
    def SetHide(self, bHide = True):
        self.bHide = bHide
        for obj in self.actorLineCenter:
            obj.SetVisibility(not bHide)
    
    def SetInViewportCenter(self):
        
        if not self.actorLineCenter:
            
            coord2D = vtkCoordinate()
            coord2D.SetCoordinateSystemToView()
            
            line1 = vtkLineSource()
            line1.SetPoint1(-1, 0, 0)
            line1.SetPoint2( 1, 0, 0)
            
            mapper1 = vtkPolyDataMapper2D()
            mapper1.SetInputConnection(line1.GetOutputPort())
            mapper1.SetTransformCoordinate(coord2D) 
            
            self.actorLineCenter = [vtkActor2D() for _ in range(2)]
            self.actorLineCenter[0].SetMapper(mapper1)   
            self.actorLineCenter[0].GetProperty().SetColor(1, 0, 0)
            self.actorLineCenter[0].GetProperty().SetLineWidth(2.0)
            
            line2 = vtkLineSource()
            line2.SetPoint1( 0,-1, 0)
            line2.SetPoint2( 0, 1, 0)
            
            mapper2 = vtkPolyDataMapper2D()
            mapper2.SetInputConnection(line2.GetOutputPort())
            mapper2.SetTransformCoordinate(coord2D) 
            
            self.actorLineCenter[1].SetMapper(mapper2)   
            self.actorLineCenter[1].GetProperty().SetColor(1, 0, 0)
            self.actorLineCenter[1].GetProperty().SetLineWidth(2.0)
            
            self.renderer.AddActor(self.actorLineCenter[0])
            self.renderer.AddActor(self.actorLineCenter[1])
            # self.actorLineCenter[0].VisibilityOn()
            # self.actorLineCenter[1].VisibilityOn()
            self.actorLineCenter[0].SetVisibility(TargetObj.bVisible)
            self.actorLineCenter[1].SetVisibility(TargetObj.bVisible)

        return self.actorLineCenter
            
        
    def SetPosition(self, pos:np.ndarray):
        if self.position is None:
            return
        
        if isinstance(pos, tuple) or isinstance(pos, list):
            pos = np.array(pos)
        
        renderWindow = self.renderer.GetRenderWindow()
        if renderWindow is None:
            return
        
        worldLeftBottom = self.renderer.GetViewToWorld((-1, -1, 0))
        worldRightBottom = self.renderer.GetViewToWorld(( 1, -1, 0))
        worldRightTop = self.renderer.GetViewToWorld((1, 1, 0))
        
        viewPos = self.renderer.GetWorldToView(pos)
        
        # calculate Vector
        vectorUp = np.array(self.renderer.camera.GetViewUp())
        vectorViewPlane = self.renderer.camera.GetViewPlaneNormal()
        
        count = len(self.lines)     
        #line 1
        lines = [vtkLineSource() for i in range(count)]
        
        axisXLength = np.array(worldLeftBottom)[:3] - np.array(worldRightBottom)[:3]
        axisXLength = np.linalg.norm(axisXLength)
        
        point1 = [-1, viewPos[1], viewPos[2]]
        point2 = [ 1, viewPos[1], viewPos[2]]
        lines[0].SetPoint1(point1)
        lines[0].SetPoint2(point2)
        
        self.linesPoint[0] = [point1, point2]
        
        axisYLength = np.array(worldRightTop)[:3] - np.array(worldRightBottom)[:3]
        axisYLength = np.linalg.norm(axisYLength)

        point1 = [viewPos[0], -1, viewPos[2]]
        point2 = [viewPos[0],  1, viewPos[2]]
        lines[1].SetPoint1(point1)
        lines[1].SetPoint2(point2)
        
        self.linesPoint[1] = [point1, point2]
        
        self.position = pos.copy()
        return lines
    
    def GetLinePointsByIndex(self, index:int, bWorldCoordinate:bool = False):
        countOfLines = len(self.lines)
        
        if index >= countOfLines:
            return None, None
        
        p1 = self.linesPoint[index][0]
        p2 = self.linesPoint[index][1]
        
        if bWorldCoordinate:
            p1 = self.renderer.GetViewToWorld(p1)
            p2 = self.renderer.GetViewToWorld(p2)
        
        return p1, p2
    
class StippleLine():
    def __init__(
        self, 
        startPoint:_ArrayLike, 
        endPoint:_ArrayLike, 
        colors:_ArrayLike,
        spacing:float = 10
    ):
        self.startPoint = np.zeros(3)
        self.endPoint = np.zeros(3)
        self.spacing = spacing
        self.colors = colors
        self.renderer = None
        
        self.setPosition(startPoint, endPoint)
        
        # vector = self.endPoint - self.startPoint
        # length = np.linalg.norm(vector)
        # if length > 0:
        #     vector = vector / length
        
        # self.stippeLines = []
        # lineStart = self.startPoint.copy()
        # lineEnd = self.startPoint + vector * spacing
        
        # while np.linalg.norm(lineStart - self.startPoint) < length:
        #     lineSource = vtkLineSource()
        #     lineSource.SetPoint1(lineStart)
        #     lineSource.SetPoint2(lineEnd)

        #     lineMapper2D = vtkPolyDataMapper2D()
        #     lineMapper2D.SetInputConnection(lineSource.GetOutputPort())
            
        #     c = vtkCoordinate()
        #     c.SetCoordinateSystemToWorld()
        #     lineMapper2D.SetTransformCoordinate(c)
            
        #     actorLine = vtkActor2D()
        #     actorLine.SetMapper(lineMapper2D)
        #     actorLine.GetProperty().SetColor(colors)
        #     self.stippeLines.append(actorLine)
            
        #     offset = spacing * 2
        #     lineStart += (vector * offset)
        #     lineEnd += (vector * offset)
            
        #     if np.linalg.norm(lineEnd - self.startPoint) > length:
        #         lineEnd = self.endPoint
                
    def setPosition(self, startPoint:_ArrayLike = None, endPoint:_ArrayLike = None):
        assert(startPoint is not None and endPoint is not None), 'must have startPoint or endPoint'
        
        if startPoint is not None:
            self.startPoint = np.array(startPoint)
            
        if endPoint is not None:
            self.endPoint = np.array(endPoint)
            
            
        vector = self.endPoint - self.startPoint
        length = np.linalg.norm(vector)
        if length > 0:
            vector = vector / length
        
        self.stippeLines = []
        lineStart = self.startPoint.copy()
        lineEnd = self.startPoint + vector * self.spacing
        
        # clear old actor
        if self.renderer is not None:
            for line in self.stippeLines:
                self.renderer.RemoveActor(line)
            self.stippeLines = []
        
        while np.linalg.norm(lineStart - self.startPoint) < length:
            lineSource = vtkLineSource()
            lineSource.SetPoint1(lineStart)
            lineSource.SetPoint2(lineEnd)

            lineMapper2D = vtkPolyDataMapper2D()
            lineMapper2D.SetInputConnection(lineSource.GetOutputPort())
            
            c = vtkCoordinate()
            c.SetCoordinateSystemToWorld()
            lineMapper2D.SetTransformCoordinate(c)
                
            actorLine = vtkActor2D()
            actorLine.SetMapper(lineMapper2D)
            actorLine.GetProperty().SetColor(self.colors)
            self.stippeLines.append(actorLine)
            if self.renderer is not None:
                self.renderer.AddActor(actorLine)
            
            offset = self.spacing * 2
            lineStart += (vector * offset)
            lineEnd += (vector * offset)
            
            if np.linalg.norm(lineEnd - self.startPoint) > length:
                lineEnd = self.endPoint
        
    def setRenderer(self, renderer:vtkRenderer):
        for line in self.stippeLines:
            renderer.AddActor(line)
        self.renderer = renderer
        
    def setVisibility(self, bVisible:bool):
        for line in self.stippeLines:
            line.SetVisibility(bVisible)
    
class TrajectoryVTKObj():
    def __init__(self, entryPoint:_ArrayLike, targetPoint:_ArrayLike, colors:_ArrayLike):
        self.stippleLine = None
        self.actorLine = vtkActor2D()
        self.actorTube = vtkActor()
        self.actorBallGreen = vtkActor()
        self.actorBallRed = vtkActor()
        self.entryPoint = np.asarray(entryPoint)
        self.targetPoint = np.asarray(targetPoint)
        self.bVisible = True
        self.bCurrent = True
        
        self.property = self.actorLine.GetProperty()
        self.property.SetColor(colors)
        
        self.setPosition(entryPoint, targetPoint)
        # self.property.SetLineStipplePattern(1)
        # self.property.SetLineStippleRepeatFactor(1)
        
        # self.originProperty = vtk.vtkProperty2D()
        # self.originProperty.DeepCopy(self.property)
        
    def setCurrent(self, bEnabled:bool = True):
        if self.bVisible:
            self.actorLine.SetVisibility(bEnabled)
            self.stippleLine.setVisibility(not bEnabled)
        self.bCurrent = bEnabled
        
            # self.property.SetLineStipplePattern(0xFFFF)
        # else:
        #     self.property.DeepCopy(self.originProperty)
        #     self.actorLine.SetProperty(self.property)
        
    def setPosition(self, entryPoint:_ArrayLike = None, targetPoint:_ArrayLike = None):
        if entryPoint is None:
            entryPoint = self.entryPoint
        else:
            self.entryPoint = entryPoint
            
        if targetPoint is None:
            targetPoint = self.targetPoint
        else:
            self.targetPoint = targetPoint
        ## 建立線 ############################################################################################
        "Create a line"
        lineSource = vtkLineSource()
        lineSource.SetPoint1(entryPoint)
        lineSource.SetPoint2(targetPoint)

        lineMapper2D = vtkPolyDataMapper2D()
        lineMapper2D.SetInputConnection(lineSource.GetOutputPort())
        
        c = vtkCoordinate()
        c.SetCoordinateSystemToWorld()
        lineMapper2D.SetTransformCoordinate(c)
        
        self.actorLine.SetMapper(lineMapper2D)
        colors = self.actorLine.GetProperty().GetColor()
        
        if self.stippleLine is None:
            self.stippleLine = StippleLine(entryPoint, targetPoint, colors)
        else:
            self.stippleLine.setPosition(entryPoint, targetPoint)
        self.stippleLine.setVisibility(False)
        
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
        self.actorTube.PickableOff()
        
    def setRenderer(self, renderer:vtkRenderer):
        renderer.AddActor(self.actorLine)
        # renderer.AddActor(self.actorTube)
        self.stippleLine.setRenderer(renderer)
        
    def setVisibility(self, bVisible:bool):
        bVisibleAndCurrent = bVisible and self.bCurrent
        bVisbleAndNotCurrent = bVisible and not self.bCurrent
        self.actorLine.SetVisibility(bVisibleAndCurrent)
        self.actorTube.SetVisibility(bVisibleAndCurrent)
        self.stippleLine.setVisibility(bVisbleAndNotCurrent)
        self.bVisible = bVisible
class Trajectory():
    def __init__(self):
        self.nLimitTrajectory = 8
        self.colors = ['#FFFF00',
                       '#FF0000', 
                       '#00FF00',
                       '#9ACD32', 
                       '#EE82EE', 
                       '#FF6347', 
                       '#87CEEB',
                       '#FFFAFA']
        
        self.lstColor = []
        for color in self.colors:
            fColor = (int(color[1:3], 16) / 255, int(color[3:5], 16) / 255, int(color[5:], 16) / 255)
            self.lstColor.append(fColor)
        
        
        self._listTrajectory = []
        self._listVTKObj = []
        # 還沒產生路徑物件時的暫存可視狀態，在物件產生後賦予物件
        self._preVisible = True
        # 紀錄已被設定的點數量，只有0、1、2，來表示一個路徑是否已被完整設定
        self._pointBeenSetNum = 0
        
        self.entryPoint = np.zeros(3)
        self.targetPoint = np.zeros(3)
        self.currentIndex = -1
        
    def __getitem__(self, index):
        num = len(self._listTrajectory)
        if num == 0:
            return None
        else:
            index = min(num - 1, max(-num, index))
            return np.array(self._listTrajectory[index])
        
    def _assertPoint(self, point):
        assert(
            isinstance(point, (tuple, list, np.ndarray)) and len(point) == 3
        ), 'entry or target point type error'
        
    def _checkAddTrajectory(self):
        # 檢查並判斷是否加入新路徑
        if self._pointBeenSetNum == 3 and len(self._listTrajectory) < self.nLimitTrajectory:
            self._pointBeenSetNum = 0
            nCount = len(self._listTrajectory)
            self._listTrajectory.append([self.entryPoint, self.targetPoint])
            self._listVTKObj.append(TrajectoryVTKObj(self.entryPoint, self.targetPoint, self.lstColor[nCount]))
            
            # 賦予物件前置可視屬性，然後重置為預設值(可視)
            self._listVTKObj[-1].setVisibility(self._preVisible)
            self._preVisible = True
            
            self.currentIndex = len(self._listTrajectory) - 1
            self.setCurrentIndex(self.currentIndex)
            
    def addEntry(self, entryPoint):
        self._assertPoint(entryPoint)
        self.entryPoint = np.array(entryPoint)
        
        self._pointBeenSetNum |= 1
        self._checkAddTrajectory()
        
    def addTarget(self, targetPoint):
        self._assertPoint(targetPoint)
        self.targetPoint = np.array(targetPoint)
        
        self._pointBeenSetNum |= 2
        self._checkAddTrajectory()
        
    def count(self):
        return len(self._listTrajectory)
    
    def getCurrentTrajectory(self):
        return self[self.currentIndex]
        
    
    def getEntry(self, index:int = None):
        if index is None:
            if self.currentIndex == -1:
                return self.entryPoint
            else:
                return self._listTrajectory[self.currentIndex][0]
        else:
            return self[index][0]
    
    def getTarget(self, index:int = None):
        if index is None:
            if self.currentIndex == -1:
                return self.targetPoint
            else:
                return self._listTrajectory[self.currentIndex][1]
        else:
            return self[index][1]
        
    def goBackward(self):
        """
        return False if is begin of _listTrajectory

        Returns:
            bool: Is begin of list
        """
        self.currentIndex -= 1
        if self.currentIndex <= 0:
            self.currentIndex = 0
            return self[self.currentIndex], False
        return self[self.currentIndex], True
    
    def goForward(self):
        """
        return False if is end of _listTrajectory

        Returns:
            bool: Is end of list
        """
        self.currentIndex += 1
        count = self.count() - 1
        if self.currentIndex >= count:
            self.currentIndex = count
            return self[self.currentIndex], False
        return self[self.currentIndex], True
    
    def setCurrentIndex(self, index:int):
        self.currentIndex = min(len(self._listTrajectory) - 1, max(0, index))
        for i, obj in enumerate(self._listVTKObj):
            if i == self.currentIndex:
                obj.setCurrent()
            else:
                obj.setCurrent(False)
    
    def setEntry(self, entryPoint:np.ndarray, index:int = None):
        self._assertPoint(entryPoint)
        entryPoint = np.array(entryPoint)
        
        if index is None:
            if self.currentIndex == -1:
                self.addEntry(entryPoint)
            else:
                self.entryPoint = np.array(entryPoint)
                self._listTrajectory[self.currentIndex][0] = self.entryPoint
                self._listVTKObj[self.currentIndex].setPosition(entryPoint = entryPoint)
        elif index < len(self._listTrajectory):
            self.currentIndex = index
            self.entryPoint = np.array(entryPoint)
            self._listTrajectory[index][0] = self.entryPoint
            self._listVTKObj[index].setPosition(entryPoint = entryPoint)
        else:
            self.addEntry(entryPoint)
        
    def setTarget(self, targetPoint:np.ndarray, index:int = None):
        self._assertPoint(targetPoint)
        targetPoint = np.array(targetPoint)
        
        if index is None:
            if self.currentIndex == -1:
                self.addTarget(targetPoint)
            else:
                self.targetPoint = np.array(targetPoint)
                self._listTrajectory[self.currentIndex][1] = self.targetPoint
                self._listVTKObj[self.currentIndex].setPosition(targetPoint = targetPoint)
        elif index < len(self._listTrajectory):
            self.targetPoint = np.array(targetPoint)
            self.currentIndex = index
            self._listTrajectory[index][1] = self.targetPoint
            self._listVTKObj[index].setPosition(targetPoint = targetPoint)
        else:
            self.addTarget(targetPoint)
            
    def setRenderer(self, index:int, *rendererObjs:list):
        if index in range(0, len(self._listVTKObj)):
            for lstRenderer in rendererObjs:
                for renderer in lstRenderer:
                    if isinstance(renderer, RendererObj):
                        self._listVTKObj[index].setRenderer(renderer)
        
            
    def setVisibility(self, index:int, bVisible:bool):
        if index in range(0, len(self._listVTKObj)):
            self._listVTKObj[index].setVisibility(bVisible)
        self._preVisible = bVisible
        
    def toArray(self, index:int = None):
        if index is None or len(self._listTrajectory) == 0:
            return np.asarray(self._listTrajectory)
        else:
            return np.asarray(self[index])

class DISPLAY(QObject):
    
    # signalUpdateView = pyqtSignal()
    
    signalProgress = pyqtSignal(float)
    signalUpdateWW = pyqtSignal(int)
    signalUpdateWL = pyqtSignal(int)
    
    trajectory = Trajectory()
    _lstRendererAxial     = []
    _lstRendererCoronal   = []
    _lstRendererSagittal  = []
    _lstRenderer3D        = []
    _lstRendererCrossSection = []
    
    def __init__(self):
        super().__init__()
        self.targetPoint = np.zeros(3)
        self.entryPoint = np.zeros(3)
        self.currentTrajectory = 0
        self.imageOrigin = None
        
        self.irenList = {}
        self.target = np.zeros(3)
        self.pcoord = np.zeros(3) #image voxel to image index的補正值，0~1
        self.imagePosition = np.zeros(3, dtype = int)
    def Reset(self):
        if hasattr(self, 'rendererList'):
            for renderer in self.rendererList.values():
                renderer.RemoveAllViewProps()
                
                
        self.targetPoint = np.zeros(3)
        self.entryPoint  = np.zeros(3)        
        self.target[:] = np.zeros(3)
        self.pcoord[:] = np.zeros(3)
        self.irenList = {}
        self.rendererList = {}
        
    def CountOfTrajectory(self):
        return DISPLAY.trajectory.count()
            
    def LoadImage(self, image):
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
        # self.reader = vtkDICOMImageReader()
        self.windowLevelLookup = vtkWindowLevelLookupTable()
        self.mapColors = vtkImageMapToColors()
        self.mapColorReslice = vtkImageMapToColors()
        
        self.cameraSagittal = vtkCamera()
        self.cameraCoronal = vtkCamera()
        self.cameraAxial = vtkCamera()
        self.camera3D = vtkCamera()
        
        self.actorSagittal = vtkImageActor()
        self.actorCoronal = vtkImageActor()
        self.actorAxial = vtkImageActor()
        self.actorCrossSection = vtkImageActor()
        
        self.rendererSagittal = RendererObj()
        self.rendererCoronal = RendererObj()
        self.rendererAxial = RendererObj()
        self.renderer3D = RendererObj3D()
        self.rendererCrossSection = RendererCrossSectionObj()
        
        DISPLAY._lstRendererAxial.append(self.rendererAxial)
        DISPLAY._lstRendererCoronal.append(self.rendererCoronal)
        DISPLAY._lstRendererSagittal.append(self.rendererSagittal)
        DISPLAY._lstRenderer3D.append(self.renderer3D)
        DISPLAY._lstRendererCrossSection.append(self.rendererCrossSection)
        
        self.rendererList = {}
        self.rendererList['3D'] = self.renderer3D
        self.rendererList['Sagittal'] = self.rendererSagittal
        self.rendererList['Coronal'] = self.rendererCoronal
        self.rendererList['Axial'] = self.rendererAxial
        self.rendererList['Cross-Section'] = self.rendererCrossSection
        
        
        # self.rendererSagittal = vtkRenderer()
        # self.rendererCoronal = vtkRenderer()
        # self.rendererAxial = vtkRenderer()
        # self.renderer3D = vtkRenderer()
        # self.rendererCrossSection = vtkRenderer()
        "planningPointCenter"
        self.actorPointEntry = vtkActor()
        self.actorPointTarget = vtkActor()
        # self.actorLine = vtkActor()
        self.actorLine = vtkActor2D()
        self.actorTube = vtkActor()
        self.actorBallGreen = vtkActor()
        self.actorBallRed = vtkActor()
        
        # self.actorTarget = [vtkActor2D() for _ in range(3)]
        # self.actorTargetCS = [vtkActor2D() for _ in range(2)]
        # self.actorTarget3D = vtkAssembly()
        
        # self.signalProgress.emit(0.2)
        # self.reader.SetDirectoryName(folderPath)
        # self.reader.Update()
        self.signalProgress.emit(0.5)
        
        
        # self.vtkImage = self.reader.GetOutput()
        # self.vtkImage.SetOrigin(0, 0, 0)
        self.vtkImage = vtk.vtkImageData()
        self.vtkImage.DeepCopy(image)
        self.imageOrigin = vtk.vtkImageData()
        self.imageOrigin.DeepCopy(self.vtkImage)
        
        # 這邊的target和各個renderer中的target是同一個實體
        # 只是建立連結關係
        self.target = np.zeros(3)
        for renderer in self.rendererList.values():
            renderer.SetImage(self.vtkImage, self.imageOrigin, self.target, self.imagePosition)
            
        
        self.dicomGrayscaleRange = self.vtkImage.GetScalarRange()
        self.dicomBoundsRange = self.vtkImage.GetBounds()
        self.imageDimensions = self.vtkImage.GetDimensions()
        self.voxelSize = self.vtkImage.GetSpacing()
        
        # print(f'grayScale = {self.dicomGrayscaleRange}')
        # print(f'bounds = {self.dicomBoundsRange}')
        # print(f'dimensions = {self.imageDimensions}')
        # print(f'pixel = {self.pixel2Mm}')
        
        # self.imageReslice = vtkImageReslice()
        # self.imageReslice.SetInputConnection(self.reader.GetOutputPort())
        # self.imageReslice.SetOutputDimensionality(2)
        # self.imageReslice.SetInterpolationModeToLinear()
        
        # center = np.array(self.imageDimensions) * np.array(self.pixel2Mm) * 0.5
        # self.ChangeCrossSectionView(center, True)
        # self.imageReslice.SetBackgroundLevel(self.dicomGrayscaleRange[0])
        
        # self.SetMapColor()
        self.target[:] = np.array(self.imageDimensions) * np.array(self.voxelSize) * 0.5
        self.imagePosition[:] = np.array(self.imageDimensions, dtype = int) * 0.5
        self.SetMapColor()
        
        self.signalProgress.emit(0.8)
        
        vtkArray = self.vtkImage.GetPointData().GetScalars()
        imageVTK = vtk_to_numpy(vtkArray).reshape(self.imageDimensions[2], self.imageDimensions[1], self.imageDimensions[0])
        
        self.signalProgress.emit(1)
        ############################################################################################
        return imageVTK
    
    
    
    
    def SetCameraToPosition(self, pos = None, renderer = None):
        # move camera to select point
        if renderer is not None:
            renderer.SetCameraToTarget(pos)
        else:
            for key, renderer in self.rendererList.items():
                if key != '3D' and key != 'Cross-Section':
                    renderer.SetCameraToTarget(pos)
                    
    def SetCurrentTrajectory(self, index:int):
        DISPLAY.trajectory.setCurrentIndex(index)
    
    # Get normal slice position from cross-section slice position
    def GetPositionFromCrossSection(self, posCS):
        if isinstance(posCS, tuple) or isinstance(posCS, list):
            posCS = np.array(posCS)
            
        if not isinstance(posCS, np.ndarray):
            return None
        
        if posCS.shape[0] < 3:
            return None
        
        if posCS.shape[0] == 3:
            posCS = np.append(posCS, 1)
        
        imageReslice = self.rendererCrossSection.imageReslice
        if imageReslice is None:
            return None
        
        matrix = imageReslice.GetResliceAxes()
        
        pos = np.zeros(4)
        matrix.MultiplyPoint(posCS, pos)
        pos = pos[:3]
        
        return pos
    
    # Get cross-section slice position from normal slice position
    def GetCrossSectionFromPosition(self, pos):
        if isinstance(pos, tuple) or isinstance(pos, list):
            pos = np.array(pos)
            
        if not isinstance(pos, np.ndarray):
            return None
        
        if pos.shape[0] < 3:
            return None
        
        imageReslice = self.rendererCrossSection.imageReslice
        if imageReslice is None:
            return None
            
        if pos.shape[0] == 3:
            imageReslice.SetResliceAxesOrigin(pos)
            pos = np.append(pos, 1)
        else:
            imageReslice.SetResliceAxesOrigin(pos[:3])
            pos = np.append(pos[:3], 1)
        
        matrix = vtk.vtkMatrix4x4()
        matrix.DeepCopy(imageReslice.GetResliceAxes())
        matrix.Invert()
        
        posCS = np.zeros(4)
        matrix.MultiplyPoint(pos, posCS)
        posCS = posCS[:3]
        
        return posCS
    
    def GetTrajectoryColor(self, index:int):
        nLimit = DISPLAY.trajectory.nLimitTrajectory
        index = min(nLimit - 1, max(-nLimit, index))
        return DISPLAY.trajectory.colors[index]
    
        
    def SetMapColor(self):
        """init window level and window width
        """
        ## 設定 WW/WL ############################################################################################
        self.windowLevelLookup.Build()
        thresholdValue = int(((self.dicomGrayscaleRange[1] - self.dicomGrayscaleRange[0]) / 6) + self.dicomGrayscaleRange[0])
        self.windowLevelLookup.SetWindow(abs(thresholdValue*2))
        self.windowLevelLookup.SetLevel(thresholdValue)
        
        for renderer in self.rendererList.values():
            renderer.SetMapColor(self.windowLevelLookup)

        # self.mapColors.SetInputConnection(self.reader.GetOutputPort())
        # self.mapColors.SetLookupTable(self.windowLevelLookup)
        # self.mapColors.Update()
        
        # self.mapColorReslice.SetInputConnection(self.imageReslice.GetOutputPort())
        # self.mapColorReslice.SetLookupTable(self.windowLevelLookup)
        # self.mapColorReslice.Update()
        ############################################################################################
        self.SetCamera()
        
        return
        
    def SetCamera(self):
        """set VTK camera
        """
        "differen section, differen camera"
        ## 設定 VTK 視窗的攝影機 ############################################################################################
        self.renderer3D.SetCamera(VIEW_3D)
        self.rendererAxial.SetCamera(VIEW_AXIAL)
        self.rendererCoronal.SetCamera(VIEW_CORONAL)
        self.rendererSagittal.SetCamera(VIEW_SAGITTAL)
        self.rendererCrossSection.SetCamera(VIEW_CROSS_SECTION)
        ############################################################################################
        return
    
    def SetTrajectoryVisibility(self, index:int, bVisible:bool):
        DISPLAY.trajectory.setVisibility(index, bVisible)
        
    def CreateActorAndRender(self, value):
        """create actor and render for VTK

        Args:
            value (_int_): location of slice
        """
        ## 設定 VTK 顯示物件 ############################################################################################
        # lineSource = vtkLineSource()
        # lineSource.SetPoint1(0, 0, 0)
        # lineSource.SetPoint2(500, 500, 500)
        # lineMapper2D = vtkPolyDataMapper2D()
        # lineMapper2D.SetInputConnection(lineSource.GetOutputPort())
        
        # c = vtkCoordinate()
        # c.SetCoordinateSystemToWorld()
        # lineMapper2D.SetTransformCoordinate(c)
        
        # actorLine = vtkActor2D()
        # actorLine.SetMapper(lineMapper2D)
        # actorLine.GetProperty().SetColor(1, 1, 0)
        
        # self.renderer3D.AddActor(actorLine)
        
        
        "actor"
        "Sagittal"
        # self.actorSagittal.GetMapper().SetInputConnection(self.mapColors.GetOutputPort())
        # self.actorSagittal.SetDisplayExtent(value, value, 0, self.imageDimensions[1], 0, self.imageDimensions[2])
        # "Coronal"
        # self.actorCoronal.GetMapper().SetInputConnection(self.mapColors.GetOutputPort())
        # self.actorCoronal.SetDisplayExtent(0, self.imageDimensions[0], value, value, 0, self.imageDimensions[2])
        # "Axial"
        # self.actorAxial.GetMapper().SetInputConnection(self.mapColors.GetOutputPort())
        # self.actorAxial.SetDisplayExtent(0, self.imageDimensions[0], 0, self.imageDimensions[1], value, value)
        
        # # self.actorCrossSection.SetInputData(self.mapColorReslice.GetOutput())
        # self.actorCrossSection.GetMapper().SetInputConnection(self.mapColorReslice.GetOutputPort())
        
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
        "Cross Section"
        
        self.rendererCrossSection.SetBackground(0, 0, 0)
        self.rendererCrossSection.AddActor(self.actorCrossSection)
        self.rendererCrossSection.SetActiveCamera(self.cameraAxial)
        self.rendererCrossSection.ResetCamera(self.dicomBoundsRange)
        "3D"
        self.renderer3D.SetBackground(0, 0, 0)
        self.SetVolumeRender()
        # self.InitTargetObject(30)
        
        
        # self.renderer3D.AddActor(self.actorSagittal)
        # self.renderer3D.AddActor(self.actorAxial)
        # self.renderer3D.AddActor(self.actorCoronal)
        self.renderer3D.SetActiveCamera(self.camera3D)
        self.renderer3D.ResetCamera(self.dicomBoundsRange)
        ############################################################################################
        return
    
    def UpdateTarget(self, pos = None, posCS =None, pcoord = None):
        for key, renderer in self.rendererList.items():
            if key != VIEW_CROSS_SECTION:
                renderer.SetTarget(pos)
        
        # if posCS is not None:
        self.rendererCrossSection.SetTarget(posCS)
        
        if pcoord is not None:
            self.pcoord[:] = pcoord
            
        # self.signalUpdateView.emit()
        # for iren in self.irenList.values():
        #     iren.Initialize()
        #     iren.Start()
        
    def ChangeSagittalView(self, value):
        """change sagittal view

        Args:
            value (_int_): location of slice
        """
        ## 改變 slice ############################################################################################
        actorSagittal = self.rendererSagittal.actorImage
        actorSagittal.SetDisplayExtent(value, value, 0, self.imageDimensions[1]-1, 0, self.imageDimensions[2]-1)
        
        # if self.pcoord[0] >= 0.5:
        #     value -= 1
        # self.target[0] = value * self.pixel2Mm[0] + self.pcoord[0]
        
    
    def ChangeCoronalView(self, value):
        """change coronal view

        Args:
            value (_int_): location of slice
        """
        ## 改變 slice ############################################################################################
        actorCoronal = self.rendererCoronal.actorImage
        actorCoronal.SetDisplayExtent(0, self.imageDimensions[0]-1, value, value, 0, self.imageDimensions[2]-1)
        
        # if self.pcoord[1] >= 0.5:
        #     value -= 1
        # self.target[1] = value * self.pixel2Mm[1] + self.pcoord[1]
    
    def ChangeCrossSectionView(self, target:list, entry:list):
        """change axial view

        Args:
            position (_np.ndarray_): location of image position
        """
        ## 改變 slice ############################################################################################

        if hasattr(self.rendererCrossSection, 'imageReslice'):
            self.rendererCrossSection.SetCrossSectionView(target, entry)
        
        # if isinstance(position, tuple) or isinstance(position, list):
        #     position = np.array(position)
            
        # if not isinstance(position, np.ndarray):
        #     print(f'variant "position" type error')
        #     return
        
        # if not hasattr(self, 'imageReslice'):
        #     print(f'please initial imageReslice first')
        #     return
        
        # if center is not None:
        #     vector = np.array([1, 1, 1])
        #     vector = vector / np.linalg.norm(vector)
            
        #     viewPlaneVector = np.array([0, 0, 1])
        #     angle = vtk.vtkMath.AngleBetweenVectors(vector, viewPlaneVector)
            
        #     axis = np.cross(vector, viewPlaneVector)
        #     axis = axis / np.linalg.norm(axis)
                    
        #     transform = vtk.vtkTransform()
            
        #     # transform.PostMultiply()
        #     # transform.Translate(-position)
        #     transform.RotateWXYZ(angle * 180.0 / np.pi, axis)
        #     # transform.Translate( position)
            
            
        #     extent = self.vtkImage.GetExtent()
        #     voxel = self.vtkImage.GetSpacing()
        #     print(f'extent = {extent}')
        #     matrix = transform.GetMatrix()
            
            # self.imageReslice.SetResliceAxes(matrix)
            
            
        # self.imageReslice.SetResliceAxesOrigin(position)
        
    
        ############################################################################################
        return
    
    def ChangeCrossSectionDelta(self, value:int):
        """change axial view

        Args:
            value (_int_): location of image position
        """
        ## 改變 slice ############################################################################################
        transform = self.imageReslice.GetResliceTransform()
        transform.Translate(0, 0, value)
        pos = np.array([0, 0, value])
        inv = vtk.vtkMatrix4x4()
        transform.GetInverse(inv)
        
        new_pos = np.zeros(4)
        inv.MultiplyPoint(np.append(pos, 1), new_pos)
        # self.ChangeCoronalView(pos[1])
        # self.ChangeSagittalView(pos[0])
        # self.ChangeTargetCS(pos, 20)
        ############################################################################################
        return

    def ChangeAxialView(self, value):
        """change axial view

        Args:
            value (_int_): location of slice
        """
        ## 改變 slice ############################################################################################
        actorAxial = self.rendererAxial.actorImage
        actorAxial.SetDisplayExtent(0, self.imageDimensions[0]-1, 0, self.imageDimensions[1]-1, value, value)
        
        # if self.pcoord[2] >= 0.5:
        #     value -= 1
        # self.target[2] = value * self.pixel2Mm[2] + self.pcoord[2]
        
        
        
    
    def ChangeWindowWidthView(self, value):
        """change window width

        Args:
            value (_int_): number of window width
        """
        ## 改變 window width ############################################################################################
        self.windowLevelLookup.SetWindow(value)
        # self.signalUpdateWW.emit(value)
        
        # if hasattr(self.renderer3D, 'volume'):
        #     volumeProperty = self.renderer3D.volume.GetProperty()

        #     windowLevel = self.windowLevelLookup.GetLevel()
        #     windowWidth = np.fmax(value, 1.0)
            
        #     compositeOpacity = vtk.vtkPiecewiseFunction()
        #     compositeOpacity.AddPoint(windowLevel - windowWidth, 0.0)
        #     compositeOpacity.AddPoint( windowLevel, 0.8)
        #     compositeOpacity.AddPoint( windowLevel + windowWidth, 1.0)
        #     volumeProperty.SetScalarOpacity(compositeOpacity)
        
        # gradientOpacity = vtk.vtkPiecewiseFunction()
        # gradientOpacity.AddPoint(-200, 0.0)
        # gradientOpacity.AddPoint( -80, 0.3)
        # gradientOpacity.AddPoint( 200, 1.0)
        # volumeProperty.SetGradientOpacity(gradientOpacity)
        
        # self.volume.SetProperty(volumeProperty)
        ############################################################################################
        return
        
    def ChangeWindowLevelView(self, value):
        """change window level

        Args:
            value (_int_): number of window level
        """
        ## 改變 window level ############################################################################################
        self.windowLevelLookup.SetLevel(value)
        # self.signalUpdateWL.emit(value)
        ## 改變 volume render
        # if hasattr(self.renderer3D, 'volume'):
        #     volumeProperty = self.renderer3D.volume.GetProperty()
        #     # volumeProperty = self.volume.GetProperty()

        #     windowWidth = self.windowLevelLookup.GetWindow()
        #     windowWidth = np.fmax(windowWidth, 1.0)
            
        #     compositeOpacity = vtk.vtkPiecewiseFunction()
        #     compositeOpacity.AddPoint(value - windowWidth, 0.0)
        #     compositeOpacity.AddPoint( value, 0.8)
        #     compositeOpacity.AddPoint( value + windowWidth, 1.0)
        #     volumeProperty.SetScalarOpacity(compositeOpacity)
        
        # gradientOpacity = vtk.vtkPiecewiseFunction()
        # gradientOpacity.AddPoint(-200, 0.0)
        # gradientOpacity.AddPoint( -80, 0.3)
        # gradientOpacity.AddPoint( 200, 1.0)
        # volumeProperty.SetGradientOpacity(gradientOpacity)
        
        # self.volume.SetProperty(volumeProperty)
        ############################################################################################
        return
    
    def IsPositionInImage(self, position):
        imagePos = [0, 0, 0]
        pcoord = [0, 0, 0]
        self.vtkImage.ComputeStructuredCoordinates(position, imagePos, pcoord)
        imagePos += np.round(pcoord)
        
        
        
        ret = 1
        if imagePos[0] < 0 or imagePos[0] >= self.imageDimensions[0]:
            ret = 0
        
        if imagePos[1] < 0 or imagePos[1] >= self.imageDimensions[1]:
            ret = 0
        
        if imagePos[2] < 0 or imagePos[2] >= self.imageDimensions[2]:
            ret = 0
        
        if ret == 0:
            return ret, None
        
        return ret, np.array(imagePos).astype(int)
    
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
       
    def CreateLine(self, index:int):
        """create line between enter point and target point

        Args:
            startPoint (_numpy.array_): enter point
            endPoint (_numpy.array_): target point
        """
        ## 建立線 ############################################################################################
        # colors = vtkNamedColors()

        # "Create a line"
        # lineSource = vtkLineSource()
        # lineSource.SetPoint1(startPoint)
        # lineSource.SetPoint2(endPoint)
        

        # lineMapper2D = vtkPolyDataMapper2D()
        # lineMapper2D.SetInputConnection(lineSource.GetOutputPort())
        
        # c = vtkCoordinate()
        # c.SetCoordinateSystemToWorld()
        # lineMapper2D.SetTransformCoordinate(c)
        
        # self.actorLine.SetMapper(lineMapper2D)
        # self.actorLine.GetProperty().SetColor(colors.GetColor3d('Yellow'))
             
        # # lineMapper = vtkPolyDataMapper()
        # # lineMapper.SetInputConnection(lineSource.GetOutputPort())

        
        # # self.actorLine.SetMapper(lineMapper)
        # # self.actorLine.GetProperty().SetColor(colors.GetColor3d('Red'))
        # # self.actorLine.SetForceTranslucent(True)

        # "Create tube filter"
        # tubeFilter = vtkTubeFilter()
        # tubeFilter.SetInputConnection(lineSource.GetOutputPort())
        # tubeFilter.SetRadius(3)
        # tubeFilter.SetNumberOfSides(50)
        # tubeFilter.Update()

        # tubeMapper = vtkPolyDataMapper()
        # tubeMapper.SetInputConnection(tubeFilter.GetOutputPort())

        # self.actorTube.SetMapper(tubeMapper)
        # "Make the tube have some transparency"
        # self.actorTube.GetProperty().SetOpacity(0.5)
        # self.actorTube.PickableOff()
        
        startPoint, endPoint = DISPLAY.trajectory[index]
        self.rendererCrossSection.SetCrossSectionView(endPoint, startPoint)
        
        DISPLAY.trajectory.setRenderer(
            index,
            DISPLAY._lstRendererAxial,
            DISPLAY._lstRendererCoronal,
            DISPLAY._lstRendererSagittal,
            DISPLAY._lstRenderer3D
        )
        
        # self.rendererSagittal.AddActor(self.actorLine)
        # self.rendererAxial.AddActor(self.actorLine)
        # self.rendererCoronal.AddActor(self.actorLine)
        # self.renderer3D.AddActor(self.actorLine)
        
        # self.rendererSagittal.AddActor(self.actorTube)
        # self.rendererAxial.AddActor(self.actorTube)
        # self.rendererCoronal.AddActor(self.actorTube)
        # self.renderer3D.AddActor(self.actorTube)
        ############################################################################################

     
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
    
    def DrawPoint(self, pick_point, selectedID, radius = 2):
        """draw point"""
        ## 畫點 ############################################################################################
        
        if selectedID == 1:
            "entry point"
            "green"
            self.CreateBallGreen(pick_point, radius)
        elif selectedID == 2:
            "target point"
            "red"
            self.CreateBallRed(pick_point, radius)
        ############################################################################################
        return
    
    def CreateBallGreen(self, pick_point, radius):
        ## 建立 entry point ############################################################################################
        sphereSource = vtkSphereSource()
        sphereSource.SetCenter(pick_point)
        sphereSource.SetRadius(radius)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.actorBallGreen.SetMapper(mapper)
        self.actorBallGreen.GetProperty().SetColor(0, 1, 0)
        self.actorBallGreen.PickableOff()
        
        self.rendererSagittal.AddActor(self.actorBallGreen)
        self.rendererCoronal.AddActor(self.actorBallGreen)
        self.rendererAxial.AddActor(self.actorBallGreen)
        
        # self.irenSagittal.Initialize()
        # self.irenCoronal.Initialize()
        # self.irenAxial.Initialize()
        # self.iren3D.Initialize()
        
        # self.irenSagittal.Start()
        # self.irenCoronal.Start()
        # self.irenAxial.Start()
        # self.iren3D.Start()  
        
        ############################################################################################
        return
    
    def CreateBallRed(self, pick_point, radius):
        ## 建立 target point ############################################################################################
        sphereSource = vtkSphereSource()
        sphereSource.SetCenter(pick_point)
        sphereSource.SetRadius(radius)
        sphereSource.SetPhiResolution(100)
        sphereSource.SetThetaResolution(100)
        
        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(sphereSource.GetOutputPort())
        self.actorBallRed.SetMapper(mapper)
        self.actorBallRed.GetProperty().SetColor(1, 0, 0)
        self.actorBallRed.PickableOff()
        
        self.rendererSagittal.AddActor(self.actorBallRed)
        self.rendererCoronal.AddActor(self.actorBallRed)
        self.rendererAxial.AddActor(self.actorBallRed)
        
        # self.irenSagittal.Initialize()
        # self.irenCoronal.Initialize()
        # self.irenAxial.Initialize()
        # self.iren3D.Initialize()
        
        # self.irenSagittal.Start()
        # self.irenCoronal.Start()
        # self.irenAxial.Start()
        # self.iren3D.Start()  
       
        ############################################################################################
        return
    
    def GetHUValue(self, pick_point):        
        
        # convert from image size to image slices
        returnValue, imagePos = self.IsPositionInImage(pick_point)
        
        if returnValue == 1:
            
            hu_value = self.vtkImage.GetScalarComponentAsDouble(
                imagePos[0], imagePos[1], imagePos[2], 0
            )        
            
            return hu_value
        else:
            return ""
        
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

    # convert from image coordinate To cross section coordinate
    def ConvertPositionToCS(self, position:np.ndarray):
        if isinstance(position, tuple) or isinstance(position, list):
            position = np.array(position)
            
        if position.ndim != 1:
            return None
        
        if position.shape[0] < 3:
            return None
        
        if position.shape[0] == 3:
            position = np.append(position, 1)
        
        position = position[:4]
        
        transform = vtk.vtkMatrix4x4()
        self.imageReslice.GetResliceTransform().GetInverse(transform)
        # print(f'transform Inv = \n{transform}')
        out = np.zeros(4)
        transform.MultiplyPoint(position, out)        
        
        return out[:3]

    # convert from cross section coordinate To image coordinate
    def ConvertCSToPosition(self, position:np.ndarray):
        if isinstance(position, tuple) or isinstance(position, list):
            position = np.array(position)
        
        if position.ndim != 1:
            return None
        
        if position.shape[0] < 3:
            return None
        
        if position.shape[0] == 3:
            position = np.append(position, 1)
        
        position = position[:4]
        
        transform = self.imageReslice.GetResliceTransform()
        # print(f'transform = \n{transform}')
        out = np.zeros(4)
        transform.MultiplyPoint(position, out)        
        
        return out[:3]