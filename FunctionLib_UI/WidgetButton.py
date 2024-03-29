
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
        
class messageBox(QMessageBox):
    
    def __init__(self, icon:int, text:str):
        super().__init__()
        
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        if icon:
            self.setIcon(icon)
            
        self.setText(text)
        
        layout = self.layout()
        widget = QWidget()
        widget.setObjectName('msgWidget')
        layout.addWidget(widget)
        
        # self.addButton('Reborn', 3)
        # self.addButton('exit', 3)
        
        subLayout = QGridLayout(widget)
        col = 0
        
        self.hLayout = QHBoxLayout()
        self.hLayout.setContentsMargins(0, 0, 0, 0)
        self.hLayout.setSpacing(0)
        for item in self.children():
            
            if isinstance(item, QLabel):
                subLayout.addWidget(item, 0, col)
                col += 1
                
            # if isinstance(item, QDialogButtonBox):
            #     self.hLayout.addWidget(item)
                
        subLayout.addLayout(self.hLayout, 1, 0, 1, 2)
        widget.setStyleSheet("""
                             
                                #msgWidget{
                                    background-color:rgba(93, 161, 209, 180);
                                    border-radius:10px;
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
                                }
                                
                                QPushButton:pressed{
                                    border-top:2px solid #444;
                                    border-left:2px solid #444;
                                    border-bottom:1px solid #ddd;
                                    border-right:1px solid #ddd;
                                }
                                
                             """)
        
        
    def addButtons(self, *buttonName):
        
        for button in buttonName:
            self.addButton(button, 3)
        
        # for button in buttonName:
        #     self.hLayout.addWidget(QPushButton(button))
            
        for item in self.children():
            if isinstance(item, QDialogButtonBox):
                # item.layout().setSpacing(0)
                self.hLayout.addWidget(item)
                
                lstButton = [button for button in item.children() if isinstance(button, QPushButton)]
                
                if len(lstButton) > 1:
                    lstButton[0].setStyleSheet("""
                                                border-top-left-radius:20px;
                                                border-bottom-left-radius:20px;
                                                """)
                    
                    lstButton[-1].setStyleSheet("""
                                                border-top-right-radius:20px;
                                                border-bottom-right-radius:20px;
                                                """)
        