
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
TYPE_ROBOTARM = 2

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
        if not isinstance(indicatorType, int):
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
        elif self.uidType == TYPE_ROBOTARM:     
            # 繪製背景矩形
            rect_width = self.width() - self.pointer_width
            rect_height = self.height() - self.pointer_height
            
            # 計算左側紅區範圍
            rtRedZoneLeft_x = self.pointer_width * 0.5
            rtRedZoneLeft_Width = rect_width * 0.45
            rect = QRectF(rtRedZoneLeft_x, 0, rtRedZoneLeft_Width, rect_height)
            
            # 設定左側紅區漸層色
            linearLeft = QLinearGradient(rtRedZoneLeft_x, 0, rtRedZoneLeft_x + rtRedZoneLeft_Width, 0)
            linearLeft.setColorAt(0, QColor(255, 0, 0))
            linearLeft.setColorAt(1, QColor(0, 255, 0))
            
            # 繪製左側紅區
            painter.setBrush(linearLeft)
            painter.drawRect(rect)
            
            # 計算中間綠區範圍
            rtGreenZone_x = rtRedZoneLeft_x + rtRedZoneLeft_Width
            rtGreenZone_Width = rect_width * 0.1
            rect = QRectF(rtGreenZone_x, 0, rtGreenZone_Width, rect_height)
            
            # 設定綠區顏色(單一色:綠色)並綠製
            painter.setBrush(QColor(0, 255, 0))
            painter.drawRect(rect)
            
            # 計算右側紅區範圍
            rtRedZoneRight_x = rtGreenZone_x + rtGreenZone_Width
            rtRedZoneRight_Width = rect_width * 0.45
            rect = QRectF(rtRedZoneRight_x, 0, rtRedZoneRight_Width, rect_height)
            
            # 設定右側紅區漸層色
            linearRight = QLinearGradient(rtRedZoneRight_x, 0, rtRedZoneRight_x + rtRedZoneRight_Width, 0)
            linearRight.setColorAt(0, QColor(0, 255, 0))
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

            painter.setBrush(QColor(255, 255, 255))  
            painter.drawPolygon(pointer) 
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
    
    