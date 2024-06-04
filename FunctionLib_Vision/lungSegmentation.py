from skimage import measure, morphology, exposure
from skimage.draw import disk
from scipy.ndimage import label, generate_binary_structure, binary_opening, binary_closing
from lungmask import LMInferer
from lungmask.utils import simple_bodymask
from PyQt5.QtCore import QTimer
import SimpleITK as sitk
import scipy.ndimage as ndimage
import numpy as np
import matplotlib.pyplot as plt

class LungSegmentation():
    def __init__(self, dicomPath:str):
        
        self.label_colors = [[255, 255, 0, 100], [255, 0, 255, 100], [0, 255, 255, 100], [0, 255, 100, 100]]
        
        self.image, self.spacing = self._readDicomSeries(dicomPath)
        self.spacing *= 0.1
        
        self.image_array = sitk.GetArrayFromImage(self.image)
        
    def apply(self, bUseAI:bool = False, threshold:int = -500):
        if bUseAI:
            bodymask, volumeSize = self._segmentationByModel(self.image)
        else:
            bodymask, volumeSize = self._segmentation(self.image_array, threshold)
        
        max_value = min(np.max(self.image_array), 600)
        expose_image = exposure.rescale_intensity(self.image_array, in_range=(threshold, max_value), out_range=(0, 255)).astype(np.uint8)
        # 擴展成RGBA
        image = np.stack((expose_image, ) * 4, axis = -1, dtype = np.uint8)
        image[..., 3] = 255
        
        labels = np.unique(bodymask)
        idx = 0
        for label in labels:
            if label > 0:
                image[bodymask == label] =  np.array(self.label_colors[idx], dtype = np.uint8)
                idx = (idx + 1) % 4
            
        return image, volumeSize
        
    def _calculateCenterHU(self, image:np.ndarray):
        # centerX, centerY = np.array(image.shape[1:]) // 2
        center = np.array(image.shape) // 2
        
        mask = self._createSphericalMask(image.shape, center, 10)
        
        # mask = mask1 & mask2
        center_pixels = image[mask]
        center_mean = np.mean(center_pixels)
        expose_image = exposure.rescale_intensity(image, in_range=(np.min(image), np.max(image)), out_range=(0, 255)).astype(np.uint8)
        mask_inv = np.invert(mask)
        expose_image[mask_inv] = 0
        
        return center_mean
    
    def _createSphericalMask(self, shape, center, radius):
        """
        创建一个球形掩码
        :param shape: 图像的形状 (depth, height, width)
        :param center: 球心的坐标 (z, y, x)
        :param radius: 球的半径
        :return: 球形掩码
        """
        
        Z, Y, X = np.ogrid[:shape[0], :shape[1], :shape[2]]
        dist_from_center = np.sqrt((X - center[2])**2 + (Y - center[1])**2 + (Z - center[0])**2)
        
        mask = dist_from_center <= radius
        return mask 
        
    # 读取DICOM图像 by simpleSITK
    def _readDicomSeries(self, directory):
        reader = sitk.ImageSeriesReader()
        reader.MetaDataDictionaryArrayUpdateOn()
        reader.LoadPrivateTagsOn()
        series_IDs = reader.GetGDCMSeriesIDs(directory)
        
        for i, index in enumerate(series_IDs):
            dicom_files = reader.GetGDCMSeriesFileNames(directory, index)
            reader.SetFileNames(dicom_files)
            
            image = reader.Execute()
            spacing = np.asarray(image.GetSpacing())
        return image, spacing
    
    def _segmentationByModel(self, image):
        inferer = LMInferer('LTRCLobes', fillmodel = 'R231')
        # inferer = LMInferer()
            
        segmentation = inferer.apply(image)
        volumeSize = np.count_nonzero(segmentation) * np.prod(self.spacing)
        
        return segmentation, volumeSize
    
    def _segmentation(self, image, threshold:int = -500, down_sample:int = 128):
        down_scale = np.append(1, down_sample / np.asarray(image.shape[1:]))
        img_down = ndimage.zoom(image, down_scale, order = 0)
        
        bodymask = img_down < threshold
        bodymask = measure.label(bodymask.astype(int), connectivity=1)
        regions = measure.regionprops(bodymask.astype(int))
        area = 0
        if len(regions) > 1:
            lstArea = np.zeros_like(regions)
            for i, region in enumerate(regions):
                # 略過在圖像邊緣的區域
                if np.any(region.coords[:, 1:] <= 5) or np.any(region.coords[:, 1:] >= bodymask.shape[1] - 6):
                    lstArea[i] = 0
                else:
                    lstArea[i] = region.area
            
            area = np.max(lstArea)
            max_region = np.argmax(lstArea) + 1
            bodymask = bodymask == max_region
            
            mask_new = []
            for mask_slice in bodymask:
                mask_slice = ndimage.binary_closing(mask_slice)
                mask_slice = ndimage.binary_fill_holes(mask_slice, structure=np.ones((3, 3))).astype(int)
                mask_slice = ndimage.binary_erosion(mask_slice, iterations=2)
                mask_slice = ndimage.binary_dilation(mask_slice, iterations=2)
                mask_new.append(mask_slice)
                
            bodymask = np.asarray(mask_new)
        realScale = np.append(1, np.asarray(image.shape[1:]) / down_sample)
        bodymask = ndimage.zoom(bodymask, realScale, order=0)
        
        area = area * np.prod(self.spacing * realScale)
        return bodymask, area
    
    
g_image = None
g_nSlice = 0
g_axesImage = None
g_timer = None
    
def ShowImage(dicomPath:str):
    # lungSegment = LungSegmentation('C:/Leon/CT/20220615/S43320/S2010')
    lungSegment = LungSegmentation(dicomPath)
    
    global g_image, g_nSlice
    g_image, volumeSize = lungSegment.apply()
    g_nSlice = 0
    
    plt.ion()
    fig, ax = plt.subplots(figsize = (10, 6))
    fig.subplots_adjust(0, 0, 1, 0.9, 0, 0)
    ax.axis('off')
    
    ax.set_title(f'Volume area1 = {volumeSize:,.3f} cm³', {'fontsize' : 24, 'color' : 'red'})
    
    global g_axesImage
    g_axesImage = ax.imshow(g_image[0])
    
    global g_timer
    g_timer = QTimer()
    g_timer.timeout.connect(IdleShowSlice)
    g_timer.start(20)

def IdleShowSlice():
    global g_nSlice
    sliceImage = g_image[g_nSlice]
    
    g_axesImage.set_data(sliceImage)
    g_nSlice = (g_nSlice + 1) % g_image.shape[0]