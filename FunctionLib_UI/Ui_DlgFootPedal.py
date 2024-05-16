# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Leon\AitherBot\AitherBot_V3.2\FunctionLib_UI\DlgFootPedal.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_DlgFootPedal(object):
    def setupUi(self, DlgFootPedal):
        DlgFootPedal.setObjectName("DlgFootPedal")
        DlgFootPedal.setWindowModality(QtCore.Qt.ApplicationModal)
        DlgFootPedal.resize(942, 819)
        DlgFootPedal.setStyleSheet("QDialog{\n"
"background-color: #74d3ff;\n"
"}\n"
"")
        DlgFootPedal.setModal(True)
        self.gridLayout_6 = QtWidgets.QGridLayout(DlgFootPedal)
        self.gridLayout_6.setContentsMargins(5, 5, 5, 5)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.mainWidget = QtWidgets.QWidget(DlgFootPedal)
        self.mainWidget.setStyleSheet("\n"
"QWidget{\n"
"    font: 24pt \"Arial\";\n"
"    background-color:rgb(77, 140, 187);\n"
"}\n"
"\n"
"QPushButton{\n"
"font: 48pt \"Arial\";\n"
"color:#666666;\n"
"border-radius:24px;\n"
"background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0, 155, 155, 255), stop:0.2 rgba(88, 239, 255, 255), stop:0.5 rgba(88, 239, 255, 255), stop:0.75 rgba(0, 200, 200, 255),  stop:1 rgba(0, 155, 155, 255));\n"
"padding: 0px 20px;\n"
"margin-bottom:5px;\n"
"margin-right:3px;\n"
"}\n"
"\n"
"QPushButton:hover{\n"
"color:#aa3333;\n"
"background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(50, 155, 155, 255), stop:0.2 rgba(150, 239, 255, 255), stop:0.5 rgba(150, 239, 255, 255), stop:0.75 rgba(50, 200, 200, 255),  stop:1 rgba(50, 155, 155, 255));\n"
"}\n"
"\n"
"QPushButton:pressed{\n"
"margin-top:5px;\n"
"margin-bottom:0px;\n"
"margin-left:3px;\n"
"margin-right:0px;\n"
"}\n"
"\n"
"QPushButton:disabled{\n"
"    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(155, 155, 155, 255), stop:0.2 rgba(239, 239, 239, 255), stop:0.5 rgba(239, 239, 239, 255), stop:0.75 rgba(200, 200, 200, 255),  stop:1 rgba(155, 155, 155, 255));\n"
"}\n"
"\n"
"#lblContent{\n"
"    color:rgb(255, 255, 0);\n"
"    font: 64px \"Arial\";\n"
"}\n"
"\n"
"#lblContentPress{\n"
"    color:rgb(255, 200, 255);\n"
"    font: 48px \"Arial\";\n"
"}\n"
"\n"
"#lblDescription{\n"
"    color:rgb(255, 255, 255);\n"
"    font: 24pt \"Arial\";\n"
"}")
        self.mainWidget.setObjectName("mainWidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.mainWidget)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setHorizontalSpacing(0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.btnConfirm = QtWidgets.QPushButton(self.mainWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnConfirm.sizePolicy().hasHeightForWidth())
        self.btnConfirm.setSizePolicy(sizePolicy)
        self.btnConfirm.setMinimumSize(QtCore.QSize(300, 150))
        self.btnConfirm.setObjectName("btnConfirm")
        self.gridLayout.addWidget(self.btnConfirm, 0, 0, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 1, 0, 1, 1)
        self.wdgPicture = QtWidgets.QStackedWidget(self.mainWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgPicture.sizePolicy().hasHeightForWidth())
        self.wdgPicture.setSizePolicy(sizePolicy)
        self.wdgPicture.setMinimumSize(QtCore.QSize(825, 563))
        self.wdgPicture.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.wdgPicture.setStyleSheet("background-color: rgb(77, 140, 187);")
        self.wdgPicture.setObjectName("wdgPicture")
        self.pgPedal = QtWidgets.QWidget()
        self.pgPedal.setStyleSheet("")
        self.pgPedal.setObjectName("pgPedal")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.pgPedal)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lblContent = QtWidgets.QLabel(self.pgPedal)
        self.lblContent.setAlignment(QtCore.Qt.AlignCenter)
        self.lblContent.setObjectName("lblContent")
        self.verticalLayout.addWidget(self.lblContent)
        self.wdgPedal = QtWidgets.QWidget(self.pgPedal)
        self.wdgPedal.setMinimumSize(QtCore.QSize(0, 285))
        self.wdgPedal.setMaximumSize(QtCore.QSize(16777215, 285))
        self.wdgPedal.setStyleSheet("image:url(image/foot_pedal_and_drag.png)")
        self.wdgPedal.setObjectName("wdgPedal")
        self.verticalLayout.addWidget(self.wdgPedal)
        self.lblDescription = QtWidgets.QLabel(self.pgPedal)
        self.lblDescription.setText("")
        self.lblDescription.setAlignment(QtCore.Qt.AlignCenter)
        self.lblDescription.setObjectName("lblDescription")
        self.verticalLayout.addWidget(self.lblDescription)
        self.verticalLayout.setStretch(1, 1)
        self.wdgPicture.addWidget(self.pgPedal)
        self.pgPedalPress = QtWidgets.QWidget()
        self.pgPedalPress.setStyleSheet("")
        self.pgPedalPress.setObjectName("pgPedalPress")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.pgPedalPress)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.lblContentPress = QtWidgets.QLabel(self.pgPedalPress)
        self.lblContentPress.setAlignment(QtCore.Qt.AlignCenter)
        self.lblContentPress.setObjectName("lblContentPress")
        self.verticalLayout_2.addWidget(self.lblContentPress)
        self.wdgPedalPress = QtWidgets.QWidget(self.pgPedalPress)
        self.wdgPedalPress.setStyleSheet("image:url(image/foot_pedal_press.png)")
        self.wdgPedalPress.setObjectName("wdgPedalPress")
        self.verticalLayout_2.addWidget(self.wdgPedalPress)
        self.verticalLayout_2.setStretch(1, 1)
        self.wdgPicture.addWidget(self.pgPedalPress)
        self.pgSupportArm = QtWidgets.QWidget()
        self.pgSupportArm.setStyleSheet("color:#ffee88")
        self.pgSupportArm.setObjectName("pgSupportArm")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.pgSupportArm)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.wdgAxis1 = QtWidgets.QWidget(self.pgSupportArm)
        self.wdgAxis1.setStyleSheet("background-color: rgb(93, 171, 227);")
        self.wdgAxis1.setObjectName("wdgAxis1")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.wdgAxis1)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.lblAxis1 = QtWidgets.QLabel(self.wdgAxis1)
        self.lblAxis1.setStyleSheet("color:#ff00aa")
        self.lblAxis1.setObjectName("lblAxis1")
        self.gridLayout_3.addWidget(self.lblAxis1, 0, 0, 1, 1)
        self.wdgIndicatorAxis1 = QtWidgets.QWidget(self.wdgAxis1)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgIndicatorAxis1.sizePolicy().hasHeightForWidth())
        self.wdgIndicatorAxis1.setSizePolicy(sizePolicy)
        self.wdgIndicatorAxis1.setMinimumSize(QtCore.QSize(0, 60))
        self.wdgIndicatorAxis1.setMaximumSize(QtCore.QSize(16777215, 60))
        self.wdgIndicatorAxis1.setObjectName("wdgIndicatorAxis1")
        self.gridLayout_3.addWidget(self.wdgIndicatorAxis1, 0, 1, 1, 1)
        self.lblHintAxis1 = QtWidgets.QLabel(self.wdgAxis1)
        self.lblHintAxis1.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.lblHintAxis1.setStyleSheet("color:rgb(255, 0, 0)")
        self.lblHintAxis1.setText("")
        self.lblHintAxis1.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.lblHintAxis1.setObjectName("lblHintAxis1")
        self.gridLayout_3.addWidget(self.lblHintAxis1, 1, 1, 1, 1)
        self.gridLayout_3.setColumnStretch(1, 1)
        self.gridLayout_5.addWidget(self.wdgAxis1, 0, 0, 1, 1)
        self.wdgAxis2 = QtWidgets.QWidget(self.pgSupportArm)
        self.wdgAxis2.setStyleSheet("background-color: rgb(93, 171, 227);")
        self.wdgAxis2.setObjectName("wdgAxis2")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.wdgAxis2)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.lblAxis2 = QtWidgets.QLabel(self.wdgAxis2)
        self.lblAxis2.setStyleSheet("color:#00ff90")
        self.lblAxis2.setObjectName("lblAxis2")
        self.gridLayout_4.addWidget(self.lblAxis2, 0, 0, 1, 1)
        self.wdgIndicatorAxis2 = QtWidgets.QWidget(self.wdgAxis2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgIndicatorAxis2.sizePolicy().hasHeightForWidth())
        self.wdgIndicatorAxis2.setSizePolicy(sizePolicy)
        self.wdgIndicatorAxis2.setMinimumSize(QtCore.QSize(0, 60))
        self.wdgIndicatorAxis2.setMaximumSize(QtCore.QSize(16777215, 60))
        self.wdgIndicatorAxis2.setObjectName("wdgIndicatorAxis2")
        self.gridLayout_4.addWidget(self.wdgIndicatorAxis2, 0, 1, 1, 1)
        self.lblHintAxis2 = QtWidgets.QLabel(self.wdgAxis2)
        self.lblHintAxis2.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.lblHintAxis2.setStyleSheet("color:rgb(255, 0, 0)")
        self.lblHintAxis2.setText("")
        self.lblHintAxis2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.lblHintAxis2.setObjectName("lblHintAxis2")
        self.gridLayout_4.addWidget(self.lblHintAxis2, 1, 1, 1, 1)
        self.gridLayout_4.setColumnStretch(1, 1)
        self.gridLayout_5.addWidget(self.wdgAxis2, 1, 0, 1, 1)
        self.wdgPicture.addWidget(self.pgSupportArm)
        self.gridLayout_2.addWidget(self.wdgPicture, 0, 0, 1, 1)
        self.gridLayout_2.setRowStretch(0, 1)
        self.gridLayout_6.addWidget(self.mainWidget, 1, 0, 1, 1)
        self.wdgTitle = QtWidgets.QWidget(DlgFootPedal)
        self.wdgTitle.setMinimumSize(QtCore.QSize(0, 80))
        self.wdgTitle.setStyleSheet("border-image:url(image/aitherbot_background_s50.png);\n"
"border-top:80px;\n"
"border-left:900px;")
        self.wdgTitle.setObjectName("wdgTitle")
        self.gridLayout_6.addWidget(self.wdgTitle, 0, 0, 1, 1)

        self.retranslateUi(DlgFootPedal)
        QtCore.QMetaObject.connectSlotsByName(DlgFootPedal)

    def retranslateUi(self, DlgFootPedal):
        _translate = QtCore.QCoreApplication.translate
        DlgFootPedal.setWindowTitle(_translate("DlgFootPedal", "Dialog"))
        self.btnConfirm.setText(_translate("DlgFootPedal", "Position Confirm"))
        self.lblContent.setText(_translate("DlgFootPedal", "...Please press foot pedal..."))
        self.lblContentPress.setText(_translate("DlgFootPedal", "...Unlocked, move robot arm by hand..."))
        self.lblAxis1.setText(_translate("DlgFootPedal", "Axis 1"))
        self.lblAxis2.setText(_translate("DlgFootPedal", "Axis 2"))
