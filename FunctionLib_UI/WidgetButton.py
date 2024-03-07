
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent, QPaintEvent
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget
from datetime import datetime

TYPE_INHALE = 0
TYPE_EXHALE = 1

class WidgetButton(QWidget):
    clicked = pyqtSignal()
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)

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
        if not isinstance(indicatorType, int) or indicatorType not in [TYPE_INHALE, TYPE_EXHALE]:
            raise ValueError('indicator type error')
        
        self.value = 0  
        self.uidType = indicatorType
        self.setStyleSheet('border:none')

    def setValue(self, value):
        # 設定值，更新畫面
        self.value = value
        self.update()
        
    def move(self, value):
        self.value = max(0, min(self.value + value, 100))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.value > 100 or self.value < 0:
            font = painter.font()
            font.setFamily('Arial')
            font.setPointSize(24)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(1, self.height() - 4, 'OUT OF RANGE')
            painter.setPen(QColor(255, 0, 0))
            painter.drawText(0, self.height() - 5, 'OUT OF RANGE')
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

            painter.setBrush(QColor(255, 255, 255))  
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

            painter.setBrush(QColor(255, 255, 255))  
            painter.drawPolygon(pointer)        
        
        