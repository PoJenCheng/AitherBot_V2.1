# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Leon\AitherBot\AitherBot_V3.2\FunctionLib_UI\formFluoroSlider.ui'
#
# Created by: PyQt5 UI code generator 5.15.10
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_formSliderFluoroSize(object):
    def setupUi(self, formSliderFluoroSize):
        formSliderFluoroSize.setObjectName("formSliderFluoroSize")
        formSliderFluoroSize.resize(247, 40)
        formSliderFluoroSize.setStyleSheet("QWidget{\n"
"    background-color: rgb(156, 156, 255);\n"
"}\n"
"\n"
"QPushButton,  #wdg_fusionTool  QPushButton{\n"
"    background-color: rgb(48, 42, 107);\n"
"}")
        self.horizontalLayout = QtWidgets.QHBoxLayout(formSliderFluoroSize)
        self.horizontalLayout.setContentsMargins(10, 0, 10, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.slider = QtWidgets.QSlider(formSliderFluoroSize)
        self.slider.setMinimum(50)
        self.slider.setMaximum(512)
        self.slider.setProperty("value", 100)
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        self.slider.setObjectName("slider")
        self.horizontalLayout.addWidget(self.slider)

        self.retranslateUi(formSliderFluoroSize)
        QtCore.QMetaObject.connectSlotsByName(formSliderFluoroSize)

    def retranslateUi(self, formSliderFluoroSize):
        _translate = QtCore.QCoreApplication.translate
        formSliderFluoroSize.setWindowTitle(_translate("formSliderFluoroSize", "Form"))
