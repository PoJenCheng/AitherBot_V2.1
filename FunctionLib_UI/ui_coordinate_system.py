# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'FunctionLib_UI/ui_coordinate_system.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(858, 711)
        self.scrollArea = QtWidgets.QScrollArea(Form)
        self.scrollArea.setGeometry(QtCore.QRect(60, 80, 461, 351))
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 459, 349))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.label_img = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_img.setObjectName("label_img")
        self.gridLayout.addWidget(self.label_img, 0, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 0, 1, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.Button_OK_and_close = QtWidgets.QPushButton(Form)
        self.Button_OK_and_close.setGeometry(QtCore.QRect(170, 490, 93, 28))
        self.Button_OK_and_close.setObjectName("Button_OK_and_close")
        self.label_origin = QtWidgets.QLabel(Form)
        self.label_origin.setGeometry(QtCore.QRect(340, 490, 171, 17))
        self.label_origin.setObjectName("label_origin")
        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(340, 460, 171, 16))
        self.label.setObjectName("label")

        self.retranslateUi(Form)
        self.Button_OK_and_close.clicked.connect(Form.okAndClose)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label_img.setText(_translate("Form", "HI"))
        self.Button_OK_and_close.setText(_translate("Form", "OK and close"))
        self.label_origin.setText(_translate("Form", "(0, 0, 0)"))
        self.label.setText(_translate("Form", "origin -> NO.1 -> NO.2"))
