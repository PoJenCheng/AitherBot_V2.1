
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from datetime import date, datetime

from PyQt5.QtWidgets import QStyle, QStyleOption, QWidget
from FunctionLib_Robot.logger import logger

TYPE_INHALE = 0
TYPE_EXHALE = 1
TYPE_ROBOTARM = 2

class QCustomStyle(QProxyStyle):
    def __init__(self, parent:QWidget):
        super().__init__()
        self.setParent(parent)
        
    def drawPrimitive(
        self, element: QStyle.PrimitiveElement, 
        option: QStyleOption, 
        painter: QPainter, 
        widget: QWidget
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
        
        self.layout().setSizeConstraint(QLayout.SetFixedSize)
        self.setLocale(QLocale.Chinese)
        self.setNavigationBarVisible(False)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.SingleLetterDayNames)
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
        # self.clicked.connect(self._OnClicked)
        self.update()
        
    def closeEvent(self, event: QCloseEvent):
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
        
        self._btnLeftYear.setFixedSize(16, 16)
        self._btnLeftMonth.setFixedSize(16, 16)
        self._btnRightYear.setFixedSize(16, 16)
        self._btnRightMonth.setFixedSize(16, 16)
        
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
            self.setSelectedDate(QDate(2024, 6, 5))
            self.showSelectedDate()
            logger.debug(f'selected date = {self.selectedDate()}')
        else:
            self._lastSelectedDate = _date
            
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
    
class WidgetHoming(QWidget):
    count = 0
    percent = 0.0
    signalFinished = pyqtSignal()
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.startTime = datetime.now().timestamp()
        self.mutex = QMutex()
        self.setAutoFillBackground(True)
        
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        # self.mutex.lock()
        # painter.begin(self)
        # painter.setBrush(QBrush(Qt.black))
        # painter.drawRect(self.rect())
        
        painter.setPen(QColor(255, 0, 255))
        
        font = QFont()
        font.setFamily('Arial')
        font.setPointSize(10)
        painter.setFont(font)
        
        fontMetrics = QFontMetrics(font)
        
        fontRect = fontMetrics.boundingRect('Homing...100%')
        
        x = int(self.rect().center().x() - fontRect.width() / 2)
        y = int(self.rect().center().y() - fontRect.height() / 2)
        leftTop = QPoint(x, y)
        
        
        text = f'Homing...{self.percent:.0%}'
        painter.drawText(leftTop.x(), leftTop.y() + fontRect.height(), text)
        super().paintEvent(event)
        # painter.end()
        # self.mutex.unlock()
        if self.percent >= 1:
            QTimer.singleShot(1000, lambda:self.signalFinished.emit())
        
    def OnSignal_Percent(self, percent:float):
        self.percent = percent
        self.update()
        
class WidgetProgressing(QWidget):
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.angle = 0
        self.text = ''
        
        self.idle = QTimer()
        self.idle.timeout.connect(self._onTimer)
        self.idle.start(33)
        
    def paintEvent(self, event: QPaintEvent):
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
        
        return super().paintEvent(event)
    
    def _onTimer(self):
        self.angle = (self.angle + 5) % 360
        self.update()
        
    def SetText(self, text:str):
        self.text = text
            
class NaviButton(QPushButton):
    angle = 0
    angleStep = 3.6
    radius = 100
    circleWidth = 10
    
    def __init__(self, parent:QWidget):
        super().__init__(parent)
        
    def paintEvent(self, event):
        # self.setStyleSheet('font:10pt "Arial"')
        
        
        opt = QStyleOption()
        opt.initFrom(self)
        
        painter = QStylePainter(self)
        # self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
        # self.style().drawControl(QStyle.CE_PushButton, opt, painter, self)
        painter.drawControl(QStyle.CE_PushButton, opt)
        
        super().paintEvent(event)
        
    def CopyPropertyFrom(self, button:QPushButton):
        self.setMaximumSize(button.maximumSize())
        self.setMinimumSize(button.minimumSize())
        self.setText(button.text())
        self.setStyleSheet(button.styleSheet())
        
    def OnSignal_Percent(self, percent:float):
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
                self.greenZoneWidth = 200 / (absValue * 2)
            
        # 此計算出的數值不是 0 就是 100
        if absValue == 0:
            self.value = 0
        else:
            self.value = (((value / absValue) + 1) // 2) * 100
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
        font.setPointSize(24)
        
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
    
    