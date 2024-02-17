
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent, QPaintEvent
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QWidget
from datetime import datetime

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
        
        
        
        