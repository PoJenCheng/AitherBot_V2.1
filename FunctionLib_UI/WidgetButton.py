
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import *
from PyQt5.QtGui import QCloseEvent, QDragEnterEvent, QDragLeaveEvent, QDragMoveEvent, QDropEvent, QMouseEvent
from PyQt5.QtWidgets import *
from datetime import date, datetime

from PyQt5.QtWidgets import QStyle, QStyleOption, QWidget
from FunctionLib_Robot.logger import logger
from FunctionLib_Robot.__init__ import *
from typing import *
import numpy as np

TYPE_INHALE = 0
TYPE_EXHALE = 1
TYPE_ROBOTARM = 2

def message_handler(mode, context, message):
    if "QDrag:" not in message:
        print(message)

# 安装自定义的日志处理器
qInstallMessageHandler(message_handler)

class CustomGroupBox(QGroupBox):
    def __init__(self, title:str, parent:QWidget = None):
        super().__init__(title)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        pixmap = QPixmap('image/joystick.png')
        
        painter.drawPixmap(5, -10, pixmap.scaled(60, 60))
        rect = QRectF(60, 0, 130, 48)
        
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(93, 161, 209))
        painter.drawRect(rect)
        painter.restore()
        rect.moveLeft(70)
        painter.drawText(rect, 'Joystick')

class MimeData(QMimeData):
    def __init__(self, item:QTreeWidgetItem):
        super().__init__()
        self._item = item

class TreeWidget(QTreeWidget):
    signalButtonClicked = pyqtSignal(int, str)
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._dragItem = None
        self._preSelectedItem = None
        self._groupTable = []
        self._hasDrived = []
        self._groupNumberTable = np.array([], dtype = int)
        self._groupNumber = 0
        self.bFoundGroup = False # 上一個路徑的狀態
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.MoveAction)
        
    def startDrag(self, supportedActions: Qt.DropActions):
        item = self.currentItem()
        if item:
            drag = QDrag(self)
            # 如不設置mimeData，底下的自定義圖像不會在拖曳時出現
            # 這邊自定的圖像只是把拖曳的item變成半透明
            # 原本預設是不透明
            mimeData = MimeData(item)
            drag.setMimeData(mimeData)

            # 暫時隱藏header，後續繪製圖像時就不會有header
            self.setHeaderHidden(True)
            # 自定義拖曳圖像尺寸
            itemRect = self.visualItemRect(item)
            pixmap = QPixmap(itemRect.size())
            pixmap.fill(Qt.transparent)
            
            painter = QPainter(pixmap)
            # 計算偏移量
            offset = (self.indexOfTopLevelItem(item)) * itemRect.height()
            itemRect.moveTop(offset)
            # 繪出至pixmap
            self.render(painter, QPoint(0, 0), QRegion(itemRect))
            painter.end()
            self.setHeaderHidden(False)
            
            # 設置透明度
            dragImage = QPixmap(pixmap.size())
            dragImage.fill(Qt.transparent)
            painter = QPainter(dragImage)
            painter.setOpacity(0.5)  
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

            drag.setPixmap(dragImage)
            drag.setHotSpot(dragImage.rect().center())
            drag.exec_(Qt.MoveAction)
            
        super().startDrag(supportedActions)
        
    def dragEnterEvent(self, event: QDragEnterEvent = None):
        if self.currentColumn() == 0:
            event.ignore()
        else:
            event.setDropAction(Qt.MoveAction)
            event.accept()
            # super().dragEnterEvent(event)
            
        
    def dragMoveEvent(self, event: QDragMoveEvent = None):
        for i in range(self.topLevelItemCount()):
            self.topLevelItem(i).setData(1, ROLE_DROPITEM, False)
                
        itemSrc = self.currentItem()
        itemDst = self.itemAt(event.pos())
        if self.currentColumn() == 0:
            event.ignore()
        elif self._HasSameDicom(itemSrc, itemDst):
            event.ignore()
        else:
            itemDst.setData(1, ROLE_DROPITEM, True)
            event.setDropAction(Qt.MoveAction)
            event.accept()
        self.update()
        
    def dropEvent(self, event: QDropEvent = None):
        
        if event.source() == self:
            for i in range(self.topLevelItemCount()):
                self.topLevelItem(i).setData(1, ROLE_DROPITEM, False)
                
            drop_pos = event.pos()
            dropIndex = self.indexAt(drop_pos)
            itemDrag = self.currentItem()
            
            itemTarget = self.itemAt(drop_pos)
            
            # 因為加了mimeData，event會執行兩次
            # 判斷mimeData是自訂的繼承類別，才是我們要的那一次
            mimeData = event.mimeData()
            if itemDrag and itemTarget != itemDrag and isinstance(mimeData, MimeData):
                item = itemDrag.clone()
                rect = self.visualItemRect(itemTarget)
                
                # 檢查拖放的位置，是在item的上半部或下半部
                # 上半部會將item移到該項上方，反之，下半部就是移到下方
                dropRow = dropIndex.row()
                if drop_pos.y() > rect.top() + rect.height() / 2:
                    dropRow += 1
                    
                if not self._HasSameDicom(itemDrag, itemTarget):
                    self.insertTopLevelItem(dropRow, item)
                    self.setItemWidget(item, 2, self.itemWidget(itemDrag, 2))
                    # self.setItemWidget(itemDrag, 2, QWidget())
                    # 確保在完成拖曳事件後，才設定拖曳項為current，如果不這麼做，會影響拖曳事件，造成不正常的結果
                    QTimer.singleShot(0, lambda:self._ReAssembleItemWidget(item, itemTarget))
                    
                    self.takeTopLevelItem(self.indexOfTopLevelItem(itemDrag))
                    event.setDropAction(Qt.MoveAction)
                    event.accept()
                    
                else:
                    logger.debug('ignore')
                    event.ignore()
            else:
                event.ignore()
                
    def AddItemToGroup(self, item:QTreeWidgetItem):
        bFoundGroup = False
        idx = self.topLevelItemCount()
        owner = item.data(0, ROLE_DICOM)
        for i in range(idx):
            if i != self._groupTable[i]:
                continue
            
            if self.topLevelItem(i).data(0, ROLE_DICOM) != owner:
                bFoundGroup = True
                self._groupTable[i] = idx
                self._groupTable.append(i)
                self._groupNumberTable = np.append(self._groupNumberTable, self._groupNumberTable[i])
                break
                
        if not bFoundGroup:
            self._groupNumber += 1
            self._groupTable.append(idx)
            self._groupNumberTable = np.append(self._groupNumberTable, self._groupNumber)
            
        self.addTopLevelItem(item)
        
        self._hasDrived.append(False)
        
        wdgMark = QWidget()
        wdgMark.setObjectName(f'group{idx}')
        layout = QHBoxLayout(wdgMark)
        layout.setContentsMargins(2, 0, 0, 0)
        layout.setSpacing(2)
        
        button = QPushButton()
        button.setObjectName(f'btnT{idx}')
        button.setText(owner)
        button.setFixedSize(24, 24)
        button.clicked.connect(self._OnClicked_btnTrajectory)
        
        lblGroup = QLabel(str(self._groupNumberTable[-1]))
        lblGroup.setFixedSize(24, 24)
        lblGroup.setAlignment(Qt.AlignCenter)
        layout.addWidget(lblGroup)
        layout.addWidget(button)
        layout.addStretch(1)
        
        wdgMark.setStyleSheet(f"""
                                #group{idx}{{
                                background-color:none
                                }}
                                """)
        
        self.setItemWidget(item, 2, wdgMark)
            
        self.bFoundGroup = bFoundGroup
        return bFoundGroup
    
    def UpdateItemGroup(self, idxParner:int, idx:int):
        if idx in self._groupTable and idxParner in self._groupTable:
            table = self._groupTable
            # change old parner
            idxParnerOfParner = table.index(idxParner)
            numberOfParner = self._groupNumberTable[idxParner]
            
            idxParnerOfIdx = table.index(idx)
            numberOfIdx = self._groupNumberTable[idx]
            
            # new group
            table[idxParner], table[idx] = idx, idxParner
            self._groupNumberTable[idx] = numberOfParner
            
            if idxParner == idxParnerOfParner:
                if idx != idxParnerOfIdx:
                    table[idxParnerOfIdx] = idxParnerOfIdx
            elif idx == idxParnerOfIdx:
                if idxParner != idxParnerOfParner:
                    table[idxParnerOfParner] = idxParnerOfParner
                    self._groupNumberTable[idxParnerOfParner] = numberOfIdx
            else:
                table[idxParnerOfIdx], table[idxParnerOfParner] = idxParnerOfParner, idxParnerOfIdx
                self._groupNumberTable[idxParnerOfParner] = numberOfIdx
        else:
            try:
                self._groupTable.index(idx)
                self._groupTable.index(idxParner)
            except Exception as msg:
                logger.error(msg)
                
    def GetItemByIndex(self, idx:int):
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, ROLE_TRAJECTORY) == idx:
                return item
            
    def GetCurrentTrajectory(self, nPattern:int = TRAJECTORY_ALL):
        """
        get current trajectory and it corresponded one

        Returns:
            dict: {'I':inhale, 'E':exhale}
        """
        item = self.currentItem()
        if not item:
            return None
        
        idx = item.data(0, ROLE_TRAJECTORY)
        idxParner = self._groupTable[idx]
        dicomLabel = item.data(0, ROLE_DICOM)
        
        if not dicomLabel:
            logger.error('missing dicom label:[inhale / exhale]')
            return None
        
        if nPattern == TRAJECTORY_CURRENT:
            return {dicomLabel:idx}
        
        # output order: [inhale, exhale]
        dicOutput = {'I':idx, 'E':idxParner}
        
        if dicomLabel == 'E':
            dicOutput = {'E':idx, 'I':idxParner}
            
            
        if idx == idxParner: 
            # 只有一條路徑(缺少inhale或exhale)，只取第一條作為current
            return dict([list(dicOutput.items())[0]])
        
        if nPattern == TRAJECTORY_PARTNER:
            return dict([list(dicOutput.items())[1]])
        
        return dicOutput    
    
    # def GetNextTrajectory(self, bOnlyCurrent = False):
    #     """
    #     get current trajectory and it corresponded one

    #     Returns:
    #         dict: {'I':inhale, 'E':exhale}
    #     """
    #     item = self.currentItem()
    #     if not item:
    #         return None
        
    #     idx = item.data(0, ROLE_TRAJECTORY) + 1
    #     bFoundNext = False
    #     for i in range(self.topLevelItemCount()):
    #         item = self.topLevelItem(i)
    #         if item.data(0, ROLE_TRAJECTORY) == idx:
    #             self.setCurrentItem(item)
    #             bFoundNext = True
    #             break
        
    #     if not bFoundNext:
    #         return None
        
    #     return self.GetCurrentTrajectory(bOnlyCurrent)
    
    def GetGroupNumber(self, idx:int = -1):
        if idx not in range(len(self._groupNumberTable)):
            return self._groupNumber
        else:
            return self._groupNumberTable[idx]
        
    def GetLock(self):
        item = self.currentItem()
        if item:
            bLocked = item.data(0, ROLE_LOCK)
            return bLocked
        return False
        
    def LockItem(self):
        item = self.currentItem()
        if item:
            bLocked = item.data(0, ROLE_LOCK)
            item.setData(0, ROLE_LOCK, not bLocked)
            widget = self.itemWidget(item, 2)
            
            if isinstance(widget, QWidget):
                lstChildren = widget.children()
                if len(lstChildren) < 4:
                    btnLock = QPushButton()
                    btnLock.setFixedSize(24, 24)
                    btnLock.setStyleSheet("""
                                        image:url(image/lock.png)
                                        """)
                    widget.layout().insertWidget(2, btnLock)
                else:
                    widget.layout().removeWidget(lstChildren[-1])
        
    def RemoveItem(self, idx:int):
        if idx >= self.topLevelItemCount():
            return
        
        itemList = []
        for i in range(self.topLevelItemCount()):
            itemList.append(self.topLevelItem(i))
            
        itemList.sort(key = lambda item:item.data(0, ROLE_TRAJECTORY))
        for i in range(len(itemList)):
            if i > idx:
                itemList[i].setData(0, ROLE_TRAJECTORY, itemList[i].data(0, ROLE_TRAJECTORY) - 1)
                # widget = self.itemWidget(itemList[i])
                # if isinstance(widget, QWidget):
                #     itemList[i].setData(2, ROLE_COLOR, DISPLAY.GetTrajectoryColor(index))
                    
        itemIndex = self.indexOfTopLevelItem(itemList[idx])
        
        self._groupNumberTable = np.delete(self._groupNumberTable, idx)
        idxParner = self._groupTable[idx]
        # 如果刪除目標有配對路徑，將其配對路徑索引指向其自身
        if idxParner != idx:
            self._groupTable[idxParner] = idxParner
        
        # 將刪除目標的索引值之後的索引，全部遞減 1
        self._groupTable = np.array(self._groupTable)
        self._groupTable[self._groupTable > idx] -= 1
        
        # 從group table中刪除要移除的對象索引
        self._groupTable = np.delete(self._groupTable, idx).tolist()
        
        # 將current item設為目標索引值的後一個item
        if idx < self.topLevelItemCount() - 1:
            idx += 1
        # 否則為前一個item
        elif idx > 0:
            idx -= 1
        self.setCurrentItem(self.topLevelItem(idx), 1)
        
        self.blockSignals(True)
        self.takeTopLevelItem(itemIndex)
        self.blockSignals(False)
        
    def SortItems(self):
        # 按照群組號碼重新排序index
        sortedIndex = np.argsort(self._groupNumberTable)
        sortedTable = self._groupNumberTable[sortedIndex]
        
        sortedTable[sortedTable == np.min(sortedTable)] = 1
        result = [sortedTable[0]]
        num = 1
        for i in range(1, sortedTable.shape[0]):
            if sortedTable[i] != sortedTable[i - 1]:
                num += 1
            result.append(num)
        
        sortedTable = result
        self._groupNumberTable[sortedIndex] = sortedTable
        
        itemList = []
        
        # 將item和itemWidget儲存
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            widget = self.itemWidget(item, 2)
            itemList.append([item, widget])
        
        # number table是按造實際路徑index排序，所以item需要根據路徑索引排列才會一致
        itemList.sort(key = lambda item:item[0].data(0, ROLE_TRAJECTORY))
        # 使用排列後的number table indexes來排列item list
        itemList = np.array(itemList)[sortedIndex]
        
        count = self.topLevelItemCount()
        # 暫存的item將itemWidget保存起來，不然一旦item從treeWidget中移除
        # 這些item會被C++移除而造成錯誤
        # 這裡存的是已經經過排列的itemWidget，與item的排序一致
        for i in range(count):
            itemTmp = QTreeWidgetItem(self)
            self.setItemWidget(itemTmp, 2, itemList[i, 1])
            
        # 要重新排列item順序，一定要先移除
        # 已在treeWidget中的item會無視insert指令
        self.blockSignals(True)
        for i in range(count):
            self.takeTopLevelItem(0)
        
        # 將排列後的item加回treeWidget，並移除暫存的item
        for i, (item, widget) in enumerate(itemList):
            widget = self.itemWidget(self.topLevelItem(0), 2)
            widget.findChild(QLabel).setText(str(sortedTable[i]))
            self.addTopLevelItem(item)
            self.setItemWidget(item, 2, widget)
            self.takeTopLevelItem(0)
            
        self.blockSignals(False)
            
        
                
    def _GetItemWidget(self, *items:QTreeWidgetItem, childType:Optional[Type[QObject]] = None):
        itemWidgets = [self.itemWidget(item, 2) for item in items]
            
        if childType is None or not issubclass(childType, QObject):
            return itemWidgets
                
        return [widget.findChild(childType) if isinstance(widget, QWidget) else None for widget in itemWidgets]
        
    def _HasSameDicom(self, itemSrc:QTreeWidgetItem, itemDst:QTreeWidgetItem):
        buttonSrc, buttonDst = self._GetItemWidget(itemSrc, itemDst, childType = QPushButton)
        if isinstance(buttonDst, QPushButton) and isinstance(buttonSrc, QPushButton):
            return buttonDst.text() == buttonSrc.text()
        return False
    
    def _OnClicked_btnTrajectory(self):
        button = self.sender()
        if isinstance(button, QPushButton):
            # 切換Inhale / Exhale標識
            owners = np.array(['I', 'E'])
            objName = button.objectName()
            if objName:
                owner, = owners[owners != button.text()]
                idx = int(objName[4:])
                
                itemList = [self.topLevelItem(i) for i in range(self.topLevelItemCount())]
                itemList.sort(key = lambda item:item.data(0, ROLE_TRAJECTORY))
                itemList[idx].setData(0, ROLE_DICOM, owner)
                
                button.setText(owner)
                # 如果切換後，造成與parner item的owner相同，則解除群組
                idxParner = self._groupTable[idx]
                if idx != idxParner and owner == itemList[idxParner].data(0, ROLE_DICOM):
                    self._groupTable[idx] = idx
                    self._groupTable[idxParner] = idxParner
                    
                    groupNumber = self._groupNumberTable[idx]
                    
                    sortedIndex = np.argsort(self._groupNumberTable)
                    sortedGroupNumber = np.sort(self._groupNumberTable)
                    
                    startIndex = np.argwhere(sortedGroupNumber == groupNumber).flatten()
                    
                    result = sortedGroupNumber.copy()
                    for i in range(startIndex[1], sortedGroupNumber.shape[0]):
                        result[i] = sortedGroupNumber[i] + 1
                    
                    del sortedGroupNumber
                    self._groupNumberTable[sortedIndex] = result
                    
                    for i in range(len(itemList)):
                        strNum = str(self._groupNumberTable[i])
                        self.itemWidget(itemList[i], 2).findChild(QLabel).setText(strNum)
                
                self.signalButtonClicked.emit(idx, owner)
                
    def _ReAssembleItemWidget(self, itemSrc:QTreeWidgetItem, itemDst:QTreeWidgetItem):
        ## 將itemSrc與itemDst組成群組
        labelSrc, labelDst = self._GetItemWidget(itemSrc, itemDst, childType = QLabel)
        if isinstance(labelSrc, QLabel) and isinstance(labelDst, QLabel):
            # 對應DISPLAY.trajectory的index
            idxItemSrc = itemSrc.data(0, ROLE_TRAJECTORY)
            idxItemDst = itemDst.data(0, ROLE_TRAJECTORY)
            
            self.UpdateItemGroup(idxItemDst, idxItemSrc)
            self.SortItems()
            
        self.setCurrentItem(itemSrc, 1)
        
    def _RestoreItemWidget(self, widgets:list):
        for i in range(self.topLevelItemCount()):
            self.setItemWidget(self.topLevelItem(i), 2, widgets[i])
        
        # self.setCurrentItem(itemSrc, 1)
class QCustomStyle(QProxyStyle):
    def __init__(self, parent:QWidget):
        super().__init__()
        self.setParent(parent)
        
    def drawPrimitive(
        self, 
        element: QStyle.PrimitiveElement, 
        option: QStyleOption = None, 
        painter: QPainter = None, 
        widget: QWidget = None
    ):
        if element == QStyle.PE_FrameFocusRect:
            return
        super().drawPrimitive(element, option, painter, widget)

class QCustomCalendarWidget(QCalendarWidget):
    signalSetCalendarTime = pyqtSignal(QDate)
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        
        self._bConfirm = False
        self._exceptDate = []
        self._lastSelectedDate = None
        
        # self.layout().setSizeConstraint(QLayout.SetFixedSize)
        # self.setLocale(QLocale.Chinese)
        self.setNavigationBarVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.ShortDayNames)
        self.setStyle(QCustomStyle(self))
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(80, 80, 80))
        fmt.setBackground(QColor(255, 255, 255))
        fmt.setFontFamily('Arial')
        
        self.setHeaderTextFormat(fmt)
        self.setWeekdayTextFormat(Qt.Monday, fmt)
        self.setWeekdayTextFormat(Qt.Tuesday, fmt)
        self.setWeekdayTextFormat(Qt.Wednesday, fmt)
        self.setWeekdayTextFormat(Qt.Thursday, fmt)
        self.setWeekdayTextFormat(Qt.Friday, fmt)
        
        fmt.setForeground(QColor(255, 0, 0))
        fmt.setBackground(QColor(255, 255, 255))
        self.setWeekdayTextFormat(Qt.Saturday, fmt)
        self.setWeekdayTextFormat(Qt.Sunday, fmt)
        
        self._InitTopWidget()
        self._InitBottomWidget()
        
        self.currentPageChanged.connect(self._SetDataLabelTimeText)
        self.clicked.connect(self._OnClicked)
        self.update()
        
    def closeEvent(self, event: QCloseEvent = None):
        if not self._bConfirm:
            return
        super().closeEvent(event)
        
    def paintCell(self, painter: QPainter, rect: QRect, date: QDate):
        if date == self.selectedDate():
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 145, 255))
            
            painter.drawRoundedRect(rect.x(), rect.y() + 3, rect.width(), rect.height() - 6, 3, 3)
            painter.setPen(QColor(255, 255, 255))
            
            painter.drawText(rect, Qt.AlignCenter, str(date.day()))
            painter.restore()
        elif date == QDate.currentDate():
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 161, 255))
            
            painter.drawRoundedRect(rect.x(), rect.y() + 3, rect.width(), rect.height() - 6, 3, 3)
            painter.setBrush(QColor(255, 255, 255))
            painter.drawRoundedRect(rect.x() + 1, rect.y() + 4, rect.width() - 2, rect.height() - 8, 2, 2)
            
            painter.setPen(QColor(0, 161, 255))
            painter.drawText(rect, Qt.AlignCenter, str(date.day()))
            painter.restore()
        elif date < self.minimumDate() or date > self.maximumDate() or date in self._exceptDate:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(249, 249, 249))
            
            painter.drawRoundedRect(rect.x(), rect.y() + 3, rect.width(), rect.height() - 6, 3, 3)
            painter.setPen(QColor(220, 220, 220))
            
            painter.drawText(rect, Qt.AlignCenter, str(date.day()))
            painter.restore()
        else:
            super().paintCell(painter, rect, date)
        
        
    def _InitTopWidget(self):
        topWidget = QWidget(self)
        topWidget.setObjectName('wdgCalendarTop')
        topWidget.setFixedHeight(40)
        topWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        hBoxLayout = QHBoxLayout()
        hBoxLayout.setContentsMargins(12, 0, 12, 0)
        hBoxLayout.setSpacing(4)
        
        self._btnLeftYear = QPushButton(self)
        self._btnLeftMonth = QPushButton(self)
        self._btnRightYear = QPushButton(self)
        self._btnRightMonth = QPushButton(self)
        self._dataLabel = QLabel(self)
        
        self._btnLeftYear.setObjectName('btnLeftYear')
        self._btnLeftMonth.setObjectName('btnLeftMonth')
        self._btnRightYear.setObjectName('btnRightYear')
        self._btnRightMonth.setObjectName('btnRightMonth')
        self._dataLabel.setObjectName('dataLabel')
        
        # self._btnLeftYear.setFixedSize(24, 24)
        # self._btnLeftMonth.setFixedSize(24, 24)
        # self._btnRightYear.setFixedSize(24, 24)
        # self._btnRightMonth.setFixedSize(24, 24)
        self._btnLeftYear.setFixedSize(32, 32)
        self._btnLeftMonth.setFixedSize(32, 32)
        self._btnRightYear.setFixedSize(32, 32)
        self._btnRightMonth.setFixedSize(32, 32)
        
        topWidget.setStyleSheet('QPushButton{border-radius:5px;}')
        
        self._btnLeftYear.setStyleSheet('image:url(image/calendar_last_year.png)')
        self._btnLeftMonth.setStyleSheet('image:url(image/calendar_last_month.png)')
        self._btnRightYear.setStyleSheet('image:url(image/calendar_next_year.png)')
        self._btnRightMonth.setStyleSheet('image:url(image/calendar_next_month.png)')
        
        hBoxLayout.addWidget(self._btnLeftYear)
        hBoxLayout.addWidget(self._btnLeftMonth)
        hBoxLayout.addStretch()
        hBoxLayout.addWidget(self._dataLabel)
        hBoxLayout.addStretch()
        hBoxLayout.addWidget(self._btnRightMonth)
        hBoxLayout.addWidget(self._btnRightYear)
        topWidget.setLayout(hBoxLayout)
        
        vBodyLayout = self.layout()
        vBodyLayout.insertWidget(0, topWidget)
        
        self._btnLeftYear.clicked.connect(self._OnBtnClicked)
        self._btnLeftMonth.clicked.connect(self._OnBtnClicked)
        self._btnRightYear.clicked.connect(self._OnBtnClicked)
        self._btnRightMonth.clicked.connect(self._OnBtnClicked)
        
        self._SetDataLabelTimeText(self.selectedDate().year(), self.selectedDate().month())
    
    def _InitBottomWidget(self):
        bottomWidget = QWidget(self)
        bottomWidget.setObjectName('wdgCalendarBottom')
        bottomWidget.setFixedHeight(52)
        bottomWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        hBoxLayout = QHBoxLayout()
        hBoxLayout.setContentsMargins(12, 12, 12, 0)
        hBoxLayout.setSpacing(6)
        
        self._btnEnsure = QPushButton(self)
        self._btnEnsure.setObjectName('btnCalendarEnsure')
        self._btnEnsure.setFixedSize(100, 40)
        self._btnEnsure.setText('Confirm')
        
        self._btnToday = QPushButton(self)
        self._btnToday.setObjectName('btnCalendarToday')
        self._btnToday.setFixedSize(100, 40)
        self._btnToday.setText('Today')
        
        hBoxLayout.addStretch()
        hBoxLayout.addWidget(self._btnToday)
        hBoxLayout.addWidget(self._btnEnsure)
        bottomWidget.setLayout(hBoxLayout)
        
        vBodyLayout = self.layout()
        vBodyLayout.addWidget(bottomWidget)
        
        self._btnEnsure.clicked.connect(lambda:self.signalSetCalendarTime.emit(self.selectedDate()))
        
        self._btnToday.clicked.connect(lambda:self.showToday())
        
        
    
    def _SetDataLabelTimeText(self, year, month):
        self._dataLabel.setText(f'{year}年{month:02}月')
        
    def _OnBtnClicked(self):
        btnSender = self.sender()
        if btnSender == self._btnLeftYear:
            self.showPreviousYear()
        elif btnSender == self._btnRightYear:
            self.showNextYear()
        elif btnSender == self._btnLeftMonth:
            self.showPreviousMonth()
        elif btnSender == self._btnRightMonth:
            self.showNextMonth()
            
    def _OnClicked(self, _date:QDate):
        if _date in self._exceptDate:
            dayOffset = 1
            dateL = QDate(_date)
            dateR = QDate(_date)
            
            while all(_date in self._exceptDate for _date in [dateL, dateR]):
                dateL = dateL.addDays(-dayOffset)
                dateR = dateR.addDays( dayOffset)
            
            if dateL not in self._exceptDate:
                self.setSelectedDate(dateL)
                self._lastSelectedDate = dateL
            else:
                self.setSelectedDate(dateR)
                self._lastSelectedDate = dateR
                
            self.showSelectedDate()
        else:
            self._lastSelectedDate = _date
            
        self.signalSetCalendarTime.emit(self._lastSelectedDate)
            
    def SetExceptDate(self, dates:list):
        self._exceptDate = dates
        

class WidgetButton(QWidget):
    clicked = pyqtSignal()
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        
        
    def copyFrom(self, widget:QWidget):
        meta_widget = widget.metaObject()
        meta_button = self.metaObject()
        
        # 获取widget的属性数量
        prop_count = meta_widget.propertyCount()
        for i in range(prop_count):
            prop = meta_widget.property(i)
            prop_name = prop.name()
            
            # 检查属性是否可写
            if prop.isWritable():
                value = prop.read(widget)
                prop_button = meta_button.property(meta_button.indexOfProperty(prop_name))
                
                # 检查button是否有对应的属性
                if prop_button.isValid() and prop_button.isWritable():
                    prop_button.write(self, value)

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)
        super().paintEvent(event)
        
    def mousePressEvent(self, event):
        self.clicked.emit()
        return super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        return super().mouseReleaseEvent(event)
class WidgetProgressing(QWidget):
    signalClose = pyqtSignal()
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.angle = 0
        self.text = ''
        
        self.idle = QTimer()
        self.idle.timeout.connect(self._onTimer)
        self.painter = None
        
    def closeEvent(self, event: QCloseEvent = None):
        self.idle.stop()
        super().closeEvent(event)
    
    def paintEvent(self, event: QPaintEvent):
        try:
            
            center = self.rect().center()
            painter = QPainter(self)
            
            painter.translate(center)
            
            font = painter.font()
            font.setFamily('Arial')
            font.setPointSize(36)
            
            fm = QFontMetrics(font)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            
            posX = int(fm.width(self.text) * 0.5)
            posY = int(fm.height() * 0.5) - 3
            painter.drawText(-posX, posY, self.text)
            
            painter.setPen(Qt.NoPen)
            painter.rotate(self.angle)
            radius = min(self.width(), self.height()) // 2 - 50
            stepColor = 255 // 72
            for i in range(72):
                painter.setBrush(QColor(255, 255, 255, 255 - i * stepColor))
                painter.drawEllipse(QPoint(radius, 0), 10, 10)
                painter.rotate(-5)
            
            painter.end()
            self.painter = painter
            super().paintEvent(event)
        except Exception as msg:
            logger.error(msg)
    
    def _onTimer(self):
        self.angle = (self.angle + 5) % 360
        self.update()
        
    def SetText(self, text:str):
        self.text = text
        
    def Start(self):
        if not self.idle.isActive():
            self.idle.start(33)
            
class NaviButton(QPushButton):
    angle = 0
    angleStep = 3.6
    radius = 100
    circleWidth = 10
    
    def __init__(self, parent:QWidget):
        super().__init__(parent)
        self.rectWidth = 0.0
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        opt = QStyleOption()
        opt.initFrom(self)
        
        path = QPainterPath()
        rect = QRectF(self.rect())
        path.addRoundedRect(rect, 24.0, 24.0)
        
        pathSub = QPainterPath()
        rectSub = QRectF(self.rect())
        rectSub.moveLeft(self.rectWidth)
        pathSub.addRect(rectSub)
        path = path.subtracted(pathSub)
        
        painter = QStylePainter(self)
        painter.drawControl(QStyle.CE_PushButton, opt)
        
        painter.setPen(Qt.black)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())
        
        painter.setClipPath(path)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(QColor(0, 0, 255, 50))
        painter.drawRect(rect)
        
        painter.setPen(Qt.white)
        painter.drawText(self.rect(), Qt.AlignCenter, self.text())
        
        
    def OnSignal_Percent(self, percent:float):
        self.rectWidth = self.width() * percent
        self.setText(f'Homing...{percent:.1%}')
        self.update()
        
class Indicator(QWidget):
    pointer_height = 20
    pointer_width  = 30
    
    
    def __init__(self, indicatorType:int, parent=None):
        super().__init__(parent)
        if not isinstance(indicatorType, int):
            raise ValueError('indicator type error')
        
        self.value = 0  
        self.uidType = indicatorType
        self.greenZoneColor = QColor(0, 255, 0)
        self.greenZoneWidth = 0.01
        self.setStyleSheet('border:none')

    def setValue(self, value):
        # 設定值，更新畫面
        self.value = value
        self.update()
        
    # 輸入原始數值而不是輸入百分比，計算綠區的寬度
    # 最大值 / 最小值為 5000 ~ -5000, 超過範圍 greenZoneWidth = 0.01
    # support arm tolerence +-100, total width = 200
    def setRawValue(self, value):
            
        absValue = abs(value)
        if absValue < 5000:
            if absValue <= 1000:
                self.greenZoneWidth = 0.2
                self.value = (value + 1000) * 0.05
                self.update()
                return
            else:
                self.greenZoneWidth = (SUPPORT_ARM_TORLERANCE * 0.5) / (absValue * 2)
            
        # 此計算出的數值不是 0 就是 100
        if absValue == 0:
            self.value = 0
        else:
            self.value = (((value / absValue) + 1) // 2) * SUPPORT_ARM_TORLERANCE
        self.update()
        
    def setGreenZone(self, color:QColor):
        self.greenZoneColor = color
        
    def move(self, value):
        self.value = max(0, min(self.value + value, 100))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen()
        pen.setWidth(3)
        pen.setColor(QColor(255, 255, 255))
        painter.setPen(pen)
        
        if self.uidType == TYPE_ROBOTARM:
            self.value = min(100, max(self.value, 0))     
            # 繪製背景矩形
            rect_width = self.width() - self.pointer_width
            rect_height = self.height() - self.pointer_height
            
            # 計算左側紅區範圍
            rtRedZoneLeft_x = self.pointer_width * 0.5
            rtRedZoneLeft_Width = rect_width * (0.5 - self.greenZoneWidth * 0.5)
            rect = QRectF(rtRedZoneLeft_x, 0, rtRedZoneLeft_Width, rect_height)
            
            # 設定左側紅區漸層色
            linearLeft = QLinearGradient(rtRedZoneLeft_x, 0, rtRedZoneLeft_x + rtRedZoneLeft_Width, 0)
            linearLeft.setColorAt(0, QColor(255, 0, 0))
            linearLeft.setColorAt(1, self.greenZoneColor)
            
            # 繪製左側紅區
            painter.setBrush(linearLeft)
            painter.drawRect(rect)
            
            # 計算中間綠區範圍
            rtGreenZone_x = rtRedZoneLeft_x + rtRedZoneLeft_Width
            rtGreenZone_Width = rect_width * self.greenZoneWidth
            rect = QRectF(rtGreenZone_x, 0, rtGreenZone_Width, rect_height)
            
            # 設定綠區顏色(單一色:綠色)並綠製
            painter.setBrush(self.greenZoneColor)
            painter.drawRect(rect)
            
            # 計算右側紅區範圍
            rtRedZoneRight_x = rtGreenZone_x + rtGreenZone_Width
            rtRedZoneRight_Width = rect_width * (0.5 - self.greenZoneWidth * 0.5)
            rect = QRectF(rtRedZoneRight_x, 0, rtRedZoneRight_Width, rect_height)
            
            # 設定右側紅區漸層色
            linearRight = QLinearGradient(rtRedZoneRight_x, 0, rtRedZoneRight_x + rtRedZoneRight_Width, 0)
            linearRight.setColorAt(0, self.greenZoneColor)
            linearRight.setColorAt(1, QColor(255, 0, 0))
            
            # 繪製右側紅區
            painter.setBrush(linearRight)
            painter.drawRect(rect)

            # 計算指針位置
            scale = rect_width * 0.01
            pointer_x = self.value * scale + self.pointer_width * 0.5
            pointer_y = rect_height

            # 繪製指針三角形
            pointer = QPolygon([
                QPoint(int(pointer_x), int(pointer_y)),
                QPoint(int(pointer_x + self.pointer_width * 0.5), self.height()),
                QPoint(int(pointer_x - self.pointer_width * 0.5), self.height())
            ])
            
            # 指針色彩
            linearPointer = QLinearGradient(pointer_x - self.pointer_width * 0.5, 0, pointer_x + self.pointer_width * 0.5, 0)
            linearPointer.setColorAt(0, QColor(180, 180, 0))
            linearPointer.setColorAt(0.3, QColor(255, 255, 0))
            linearPointer.setColorAt(0.4, QColor(255, 255, 255))
            linearPointer.setColorAt(0.5, QColor(255, 255, 0))
            linearPointer.setColorAt(1, QColor(180, 180, 0))

            # painter.setBrush(QColor(255, 255, 255))  
            painter.setPen(Qt.NoPen)
            painter.setBrush(linearPointer)  
            painter.drawPolygon(pointer) 
        elif self.value > 100 or self.value < 0:
            font = painter.font()
            font.setFamily('Arial')
            font.setPointSize(36)
            
            fm = QFontMetrics(font)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            
            strText = 'OUT OF RANGE'
            posX = int((self.width() - fm.width(strText)) * 0.5)
            posY = int((self.height() + fm.height()) * 0.5) - 3
            # painter.drawText(posX + 1, self.height() - 4, strText)
            painter.drawText(posX + 1, posY + 1, strText)
            painter.setPen(QColor(255, 0, 0))
            # painter.drawText(posX, self.height() - 5, strText)
            painter.drawText(posX, posY, strText)
        elif self.uidType == TYPE_INHALE:
            # 繪製背景矩形
            rect_width = self.width() - self.pointer_width
            rect_height = self.height() - self.pointer_height
            
            rectXRed = self.pointer_width * 0.5
            rectWidthRed = rect_width * 0.8
            rect = QRectF(rectXRed, 0, rectWidthRed, rect_height)
            
            linear = QLinearGradient(rectXRed, 0, rectXRed + rectWidthRed, 0)
            linear.setColorAt(0, Qt.red)
            linear.setColorAt(1, QColor(0, 255, 0))
            
            painter.setBrush(linear)
            painter.drawRect(rect)
            
            rectXGreen = rectXRed + rectWidthRed
            rectWidthGreen = rect_width * 0.2
            
            rect = QRectF(rectXGreen, 0, rectWidthGreen,  rect_height)
            painter.setBrush(QColor(0, 255, 0)) 
            painter.drawRect(rect)

            # 計算指針位置
            scale = rect_width * 0.01
            pointer_x = self.value * scale + self.pointer_width * 0.5
            pointer_y = rect_height

            # 繪製指針三角形
            pointer = QPolygon([
                QPoint(int(pointer_x), int(pointer_y)),
                QPoint(int(pointer_x + self.pointer_width * 0.5), self.height()),
                QPoint(int(pointer_x - self.pointer_width * 0.5), self.height())
            ])
            # 指針色彩
            linearPointer = QLinearGradient(pointer_x - self.pointer_width * 0.5, 0, pointer_x + self.pointer_width * 0.5, 0)
            linearPointer.setColorAt(0, QColor(180, 180, 0))
            linearPointer.setColorAt(0.3, QColor(255, 255, 0))
            linearPointer.setColorAt(0.4, QColor(255, 255, 255))
            linearPointer.setColorAt(0.5, QColor(255, 255, 0))
            linearPointer.setColorAt(1, QColor(180, 180, 0))

            # painter.setBrush(QColor(255, 255, 255))  
            painter.setPen(Qt.NoPen)
            painter.setBrush(linearPointer) 
            painter.drawPolygon(pointer)        
        elif self.uidType == TYPE_EXHALE:
            # 繪製背景矩形
            rect_width = self.width() - self.pointer_width
            rect_height = self.height() - self.pointer_height
            
            rectXRed = self.pointer_width * 0.5
            rectWidthRed = rect_width * 0.2
            rect = QRectF(rectXRed, 0, rectWidthRed, rect_height)
            
            painter.setBrush(QColor(0, 255, 0))
            painter.drawRect(rect)
            
            rectXGreen = rectXRed + rectWidthRed
            rectWidthGreen = rect_width * 0.8
            
            linear = QLinearGradient(rectXGreen, 0, rectXGreen + rectWidthGreen, 0)
            linear.setColorAt(0, QColor(0, 255, 0))
            linear.setColorAt(1, QColor(255, 0, 0))
            
            rect = QRectF(rectXGreen, 0, rectWidthGreen,  rect_height)
            painter.setBrush(linear) 
            painter.drawRect(rect)

            # 計算指針位置
            scale = rect_width * 0.01
            pointer_x = self.value * scale + self.pointer_width * 0.5
            pointer_y = rect_height

            # 繪製指針三角形
            pointer = QPolygon([
                QPoint(int(pointer_x), int(pointer_y)),
                QPoint(int(pointer_x + self.pointer_width * 0.5), self.height()),
                QPoint(int(pointer_x - self.pointer_width * 0.5), self.height())
            ])
            # 指針色彩
            linearPointer = QLinearGradient(pointer_x - self.pointer_width * 0.5, 0, pointer_x + self.pointer_width * 0.5, 0)
            linearPointer.setColorAt(0, QColor(180, 180, 0))
            linearPointer.setColorAt(0.3, QColor(255, 255, 0))
            linearPointer.setColorAt(0.4, QColor(255, 255, 255))
            linearPointer.setColorAt(0.5, QColor(255, 255, 0))
            linearPointer.setColorAt(1, QColor(180, 180, 0))

            # painter.setBrush(QColor(255, 255, 255))  
            painter.setPen(Qt.NoPen)
            painter.setBrush(linearPointer) 
            painter.drawPolygon(pointer)  
        
class AnimationWidget(QWidget):
    timePool = []
    signalIdle = pyqtSignal()
    def __init__(self, imagePath:str, parent = None):
        super().__init__(parent)
        
        self.image = QImage(imagePath)
        self.opacity = 0
        self.opacityStep = 1
        
        self.setMinimumHeight(150)
        
        self.bPause = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.startAnimation)
        self.timePool.append(self.timer)
        # self.timer.start(50)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(self.opacity * 0.1)
        
        width = self.width()
        rcImage = self.image.rect()
        shift = int((width - rcImage.width()) * 0.5)
        rcImage.moveLeft(shift)
        painter.drawImage(QRectF(rcImage), self.image)
        super().paintEvent(event)
        
    def startAnimation(self):
        self.opacity = max(0, min(10, self.opacity + self.opacityStep))
        if self.opacity == 0 or self.opacity == 10:
            self.opacityStep *= -1
            
        self.update()
        self.signalIdle.emit()
        
    def IsActive(self):
        return self.timer.isActive()
        
    def Start(self):
        for timer in self.timePool:
            if timer.isActive():
                timer.stop()
                
        for item in self.children():
            if isinstance(item, QWidget):
                item.setHidden(True)
                
        self.timer.start(50)
        
    def Stop(self):
        self.timer.stop()
        for item in self.children():
            if isinstance(item, QWidget):
                item.setHidden(False)
                
        self.opacity = 0
        self.opacityStep = 1
        
    def SetPause(self, bPause = True):
        if self.bPause == True and bPause == False:
            self.Start()
        elif bPause == True:
            self.Stop()
        self.bPause = bPause
        
class AnimationJoystickWidget(QWidget):
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.imageUpper = QImage('image/robot_upper.png')
        self.imageDown = QImage('image/robot_down.png')
        self.lstImage = [self.imageUpper, self.imageDown]
        self.idx = -1
        
        self.opacity = 0
        self.opacityStep = 0.1
        
    def paintEvent(self, event):
        
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)
        
        if self.idx not in range(2):
            return
        
        painter = QPainter(self)
        painter.setOpacity(self.opacity)
        
        rcImage = self.rect()
        painter.drawImage(QRectF(rcImage), self.lstImage[self.idx])
        
        super().paintEvent(event)  
        
    def Idle(self): 
        if self.idx in range(2):
            if self.opacity < 0 or self.opacity > 1:
                self.opacityStep *= -1
            self.opacity += self.opacityStep
        self.update()
            
    def SetHighlight(self, part:int):
        self.idx = part
        if part not in range(2):
            self.opacity = 0
class MessageBox(QMessageBox):
    
    def __init__(self, icon:int, text:str):
        super().__init__()
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        if icon:
            self.setIcon(icon)
            
        self.setText(text)
        self.context = text
        
        layout = self.layout()
        layout.setContentsMargins(10, 10, 10, 10)
        widget = QWidget()
        widget.setObjectName('msgWidget')
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(widget)
        
        # self.addButton('Reborn', 3)
        # self.addButton('exit', 3)
        
        subLayout = QGridLayout(widget)
        subLayout.setContentsMargins(10, 10, 10, 10)
        col = 0
        
        self.subWidget = QWidget()
        self.subWidget.setObjectName('subWidget')
        self.subWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # self.subWidget.setMinimumSize(200, 100)
        
        self.hLayout = QGridLayout(self.subWidget)
        # self.hLayout = QGridLayout()
        self.hLayout.setContentsMargins(0, 5, 0, 5)
        self.hLayout.setSpacing(0)
        for item in self.children():
            
            if isinstance(item, QLabel):
                subLayout.addWidget(item, 0, col)
                col += 1
                
        # subLayout.addLayout(self.hLayout, 1, 0, 1, 2)
        subLayout.addWidget(self.subWidget, 1, 0, 1, 2)
        widget.setStyleSheet("""
                             
                                #msgWidget{
                                    background-color:rgba(93, 161, 209, 180);
                                    border-radius:20px;
                                }
                                
                                QWidget{
                                    font:24pt "Arial";
                                    color:rgb(255, 255, 208);
                                }
                                
                                QPushButton{
                                    background-color:rgb(109, 190, 247);
                                    border-top:1px solid #ddd;
                                    border-left:1px solid #ddd;
                                    border-bottom:2px solid #444;
                                    border-right:2px solid #444;
                                    padding:10px;
                                    min-width:200px;
                                    font:16pt "Arial";
                                }
                                
                                QPushButton:pressed{
                                    border-top:2px solid #444;
                                    border-left:2px solid #444;
                                    border-bottom:1px solid #ddd;
                                    border-right:1px solid #ddd;
                                }
                                
                                QDialogButtonBox{
                                    alignment:left;
                                }
                                
                                
                             """)
        self.mainWidget = widget
        
        
    def addButtons(self, *buttonName, **kwButtonName):
        
       
        for button in buttonName:
            self.addButton(button, 3)
        
        for name, action in kwButtonName.items():
            self.addButton(name, action)
            
        for item in self.children():
            if isinstance(item, QDialogButtonBox):
                self.hLayout.addWidget(item, 0, 0, alignment = Qt.AlignCenter)
                # item.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
                
                lstButton = [button for button in item.children() if isinstance(button, QPushButton)]
                
                miniWidth = 200
                for button in lstButton:
                    
                    font = QFont()
                    font.setFamily('Arial')
                    font.setPointSize(16)
                    
                    fontMetrics = QFontMetrics(font)
                    # fontRect = fontMetrics.boundingRect(button.text())
                    
                    # miniWidth += fontRect.width()
                    miniWidth += fontMetrics.width(button.text())
                
                # if item.width() - 200 < miniWidth:
                #     item.setMinimumWidth(miniWidth)
                
                if len(lstButton) > 1:
                    lstButton[0].setStyleSheet("""
                                                border-top-left-radius:20px;
                                                border-bottom-left-radius:20px;
                                                """)
                    
                    lstButton[-1].setStyleSheet("""
                                                border-top-right-radius:20px;
                                                border-bottom-right-radius:20px;
                                                """)
                layout = item.layout()
                
                if layout:
                    tempWidget = QWidget()
                    tempWidget.setLayout(layout)
                    
                    gridLayout = QGridLayout()
                    gridLayout.setContentsMargins(0, 0, 0, 0)
                    # gridLayout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding))
                    for i, button in enumerate(lstButton):
                        gridLayout.addWidget(button, 0, i, Qt.AlignCenter)
                    gridLayout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding), 0, len(lstButton) + 1)
                    item.setLayout(gridLayout)
                    
                    
                # item.setCenterButtons(True)
        font = QFont()
        font.setFamily('Arial')
        font.setPointSize(36)
        
        fontMetrics = QFontMetrics(font)
        widthWidget = min(fontMetrics.width(self.context) + 50, 900)
        self.mainWidget.setMinimumWidth(widthWidget)
        
    def showMsg(msg:str, icon:int = 0, *args, **kwargs):
        # if len(args) == 0 and len(kwargs) == 0:
        #     QMessageBox.warning(None, 'messagebox error', 'at least one button ')
        msgbox = MessageBox(icon, msg)
        if len(args) == 0 and len(kwargs) == 0:
            msgbox.addButtons('OK')
        else:
            msgbox.addButtons(*args, **kwargs)
            
        ret = msgbox.exec_()  
        return ret
    
    def ShowCritical(msg:str, *buttons, **kwButtons):
        return MessageBox.showMsg(msg, QMessageBox.Critical, *buttons, **kwButtons)
    
    def ShowInformation(msg:str, *buttons, **kwButtons):
        return MessageBox.showMsg(msg, QMessageBox.Information, *buttons, **kwButtons)
    
    def ShowWarning(msg:str, *buttons, **kwButtons):
        return MessageBox.showMsg(msg, QMessageBox.Warning, *buttons, **kwButtons)
    
    def ShowQuestion(msg:str, *buttons, **kwButtons):
        return MessageBox.showMsg(msg, QMessageBox.Question, *buttons, **kwButtons)
    
    