# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Leon\AitherBot\AitherBot_V3.2\FunctionLib_UI\toolBox.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_FormToolBar(object):
    def setupUi(self, FormToolBar):
        FormToolBar.setObjectName("FormToolBar")
        FormToolBar.resize(102, 125)
        FormToolBar.setMouseTracking(True)
        FormToolBar.setStyleSheet("")
        self.gridLayout_2 = QtWidgets.QGridLayout(FormToolBar)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.widget = QtWidgets.QWidget(FormToolBar)
        self.widget.setStyleSheet("QWidget{\n"
"    background-color: rgb(40, 40, 120);\n"
"}\n"
"\n"
"QPushButton{\n"
"    background-color: rgb(105, 105, 255);\n"
"    border-radius:5px;\n"
"    border-left:1px solid #aaa;\n"
"    border-top:1px solid #aaa;\n"
"    border-right:2px solid #777;\n"
"    border-bottom:2px solid #777;\n"
"}\n"
"\n"
"QPushButton:pressed{\n"
"    background-color: rgb(125, 125, 255);\n"
"    border-left:2px solid #777;\n"
"    border-top:2px solid #777;\n"
"    border-right:1px solid #aaa;\n"
"    border-bottom:1px solid #aaa;\n"
"}\n"
"\n"
"QPushButton#btnSliceUp{\n"
"    image:url(image/slice_up.png)\n"
"}\n"
"\n"
"QPushButton#btnSliceDown{\n"
"    image:url(image/slice_down.png)\n"
"}")
        self.widget.setObjectName("widget")
        self.gridLayout = QtWidgets.QGridLayout(self.widget)
        self.gridLayout.setContentsMargins(10, 10, 10, 10)
        self.gridLayout.setHorizontalSpacing(0)
        self.gridLayout.setVerticalSpacing(5)
        self.gridLayout.setObjectName("gridLayout")
        self.btnSliceUp = QtWidgets.QPushButton(self.widget)
        self.btnSliceUp.setMinimumSize(QtCore.QSize(48, 48))
        self.btnSliceUp.setMaximumSize(QtCore.QSize(48, 48))
        self.btnSliceUp.setText("")
        self.btnSliceUp.setObjectName("btnSliceUp")
        self.gridLayout.addWidget(self.btnSliceUp, 0, 0, 1, 1)
        self.btnSliceDown = QtWidgets.QPushButton(self.widget)
        self.btnSliceDown.setMinimumSize(QtCore.QSize(48, 48))
        self.btnSliceDown.setMaximumSize(QtCore.QSize(48, 48))
        self.btnSliceDown.setText("")
        self.btnSliceDown.setObjectName("btnSliceDown")
        self.gridLayout.addWidget(self.btnSliceDown, 1, 0, 1, 1)
        self.gridLayout_2.addWidget(self.widget, 0, 0, 1, 1)

        self.retranslateUi(FormToolBar)
        QtCore.QMetaObject.connectSlotsByName(FormToolBar)

    def retranslateUi(self, FormToolBar):
        _translate = QtCore.QCoreApplication.translate
        FormToolBar.setWindowTitle(_translate("FormToolBar", "Form"))