# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Leon\AitherBot_V2.1\FunctionLib_UI\step.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(217, 32)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QtCore.QSize(0, 0))
        Form.setMaximumSize(QtCore.QSize(16777215, 32))
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.wdgArrow1 = QtWidgets.QWidget(Form)
        self.wdgArrow1.setMinimumSize(QtCore.QSize(32, 32))
        self.wdgArrow1.setMaximumSize(QtCore.QSize(32, 32))
        self.wdgArrow1.setStyleSheet("image:url(image/arrow-black.png);")
        self.wdgArrow1.setObjectName("wdgArrow1")
        self.horizontalLayout.addWidget(self.wdgArrow1)
        self.wdgArrow2 = QtWidgets.QWidget(Form)
        self.wdgArrow2.setMinimumSize(QtCore.QSize(32, 32))
        self.wdgArrow2.setMaximumSize(QtCore.QSize(32, 32))
        self.wdgArrow2.setStyleSheet("image:url(image/arrow-black.png);")
        self.wdgArrow2.setObjectName("wdgArrow2")
        self.horizontalLayout.addWidget(self.wdgArrow2)
        self.wdgArrow3 = QtWidgets.QWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgArrow3.sizePolicy().hasHeightForWidth())
        self.wdgArrow3.setSizePolicy(sizePolicy)
        self.wdgArrow3.setMinimumSize(QtCore.QSize(32, 32))
        self.wdgArrow3.setMaximumSize(QtCore.QSize(32, 32))
        self.wdgArrow3.setStyleSheet("image:url(image/arrow-black.png);")
        self.wdgArrow3.setObjectName("wdgArrow3")
        self.horizontalLayout.addWidget(self.wdgArrow3)
        self.lblStepName = QtWidgets.QLabel(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblStepName.sizePolicy().hasHeightForWidth())
        self.lblStepName.setSizePolicy(sizePolicy)
        self.lblStepName.setMinimumSize(QtCore.QSize(100, 0))
        self.lblStepName.setText("")
        self.lblStepName.setObjectName("lblStepName")
        self.horizontalLayout.addWidget(self.lblStepName)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))