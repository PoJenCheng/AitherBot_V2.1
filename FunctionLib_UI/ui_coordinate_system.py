# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'FunctionLib_UI/ui_coordinate_system.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtWidgets
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1850, 950)
        self.Button_OK_and_close = QtWidgets.QPushButton(Form)
        self.Button_OK_and_close.setGeometry(QtCore.QRect(110, 910, 93, 28))
        self.Button_OK_and_close.setObjectName("Button_OK_and_close")
        self.qvtkWidget_registrtion = QVTKRenderWindowInteractor(Form)
        self.qvtkWidget_registrtion.setGeometry(QtCore.QRect(20, 20, 1761, 871))
        self.qvtkWidget_registrtion.setObjectName("qvtkWidget_registrtion")
        self.comboBox_label = QtWidgets.QComboBox(Form)
        self.comboBox_label.setGeometry(QtCore.QRect(20, 910, 69, 22))
        self.comboBox_label.setObjectName("comboBox_label")
        self.Button_cancel = QtWidgets.QPushButton(Form)
        self.Button_cancel.setGeometry(QtCore.QRect(220, 910, 93, 28))
        self.Button_cancel.setObjectName("Button_cancel")

        self.retranslateUi(Form)
        self.Button_OK_and_close.clicked.connect(Form.okAndClose)
        self.Button_cancel.clicked.connect(Form.Cancel)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.Button_OK_and_close.setText(_translate("Form", "OK and close"))
        self.Button_cancel.setText(_translate("Form", "Cancel"))
