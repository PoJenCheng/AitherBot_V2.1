# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Leon\AitherBot\AitherBot_V3.2\FunctionLib_UI\DlgHintBox.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_DlgHintBox(object):
    def setupUi(self, DlgHintBox):
        DlgHintBox.setObjectName("DlgHintBox")
        DlgHintBox.resize(600, 300)
        DlgHintBox.setMinimumSize(QtCore.QSize(600, 300))
        self.gridLayout = QtWidgets.QGridLayout(DlgHintBox)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.stackedWidget = QtWidgets.QStackedWidget(DlgHintBox)
        self.stackedWidget.setStyleSheet("QPushButton{\n"
"    font: 24px \"Arial\";\n"
"    color:rgb(241, 231, 255);\n"
"    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgb(170, 170, 255), stop:0.2 rgb(200, 200, 255), stop:0.3 rgb(210, 210, 255), stop:0.5 rgb(200, 200, 255),  stop:1 rgb(170, 170, 255));\n"
"    border-radius: 5px;\n"
"    border-top:1px solid #ddd;\n"
"    border-left:1px solid #ddd;\n"
"    border-bottom:2px solid #999;\n"
"    border-right:2px solid #999;\n"
"}\n"
"\n"
"QPushButton:pressed{\n"
"    border-top:2px solid #999;\n"
"    border-left:2px solid #999;\n"
"    border-bottom:1px solid #ddd;\n"
"    border-right:1px solid #ddd;\n"
"}")
        self.stackedWidget.setObjectName("stackedWidget")
        self.pgURSide = QtWidgets.QWidget()
        self.pgURSide.setObjectName("pgURSide")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.pgURSide)
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_3.setSpacing(0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.wdgL_URSide = QtWidgets.QWidget(self.pgURSide)
        self.wdgL_URSide.setStyleSheet("background-image:url(image/msgbox/up_right_side/dark/msg_l.png)")
        self.wdgL_URSide.setObjectName("wdgL_URSide")
        self.gridLayout_3.addWidget(self.wdgL_URSide, 1, 0, 1, 1)
        self.wdgMain_URSide = QtWidgets.QWidget(self.pgURSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgMain_URSide.sizePolicy().hasHeightForWidth())
        self.wdgMain_URSide.setSizePolicy(sizePolicy)
        self.wdgMain_URSide.setMinimumSize(QtCore.QSize(0, 0))
        self.wdgMain_URSide.setStyleSheet("#wdgMain_URSide{\n"
"    border-image:url(image/msgbox/up_right_side/dark/msg_center.png);\n"
"}\n"
"\n"
"QWidget{\n"
"    font:24px \"Arial\";\n"
"    color:rgb(207, 255, 255);\n"
"}\n"
"\n"
"\n"
"QCheckBox{\n"
"    font:12px \"Arial\";\n"
"    color:rgb(240, 240, 0);\n"
"}\n"
"")
        self.wdgMain_URSide.setObjectName("wdgMain_URSide")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.wdgMain_URSide)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.lblHintText_URSide = QtWidgets.QLabel(self.wdgMain_URSide)
        self.lblHintText_URSide.setStyleSheet("font:48px;")
        self.lblHintText_URSide.setText("")
        self.lblHintText_URSide.setWordWrap(True)
        self.lblHintText_URSide.setObjectName("lblHintText_URSide")
        self.gridLayout_2.addWidget(self.lblHintText_URSide, 0, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnConfirm_URSide = QtWidgets.QPushButton(self.wdgMain_URSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnConfirm_URSide.sizePolicy().hasHeightForWidth())
        self.btnConfirm_URSide.setSizePolicy(sizePolicy)
        self.btnConfirm_URSide.setMinimumSize(QtCore.QSize(100, 40))
        self.btnConfirm_URSide.setObjectName("btnConfirm_URSide")
        self.horizontalLayout.addWidget(self.btnConfirm_URSide)
        self.chbKnown_URSide = QtWidgets.QCheckBox(self.wdgMain_URSide)
        self.chbKnown_URSide.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.chbKnown_URSide.setObjectName("chbKnown_URSide")
        self.horizontalLayout.addWidget(self.chbKnown_URSide)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(3, 1)
        self.gridLayout_2.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.gridLayout_2.setRowStretch(0, 1)
        self.gridLayout_3.addWidget(self.wdgMain_URSide, 1, 1, 1, 1)
        self.wdgR_URSide = QtWidgets.QWidget(self.pgURSide)
        self.wdgR_URSide.setStyleSheet("background-image:url(image/msgbox/up_right_side/dark/msg_r.png)")
        self.wdgR_URSide.setObjectName("wdgR_URSide")
        self.gridLayout_3.addWidget(self.wdgR_URSide, 1, 2, 1, 2)
        self.wdgBL_URSide = QtWidgets.QWidget(self.pgURSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgBL_URSide.sizePolicy().hasHeightForWidth())
        self.wdgBL_URSide.setSizePolicy(sizePolicy)
        self.wdgBL_URSide.setMinimumSize(QtCore.QSize(50, 50))
        self.wdgBL_URSide.setStyleSheet("background-image:url(image/msgbox/up_right_side/dark/msg_bl.png)")
        self.wdgBL_URSide.setObjectName("wdgBL_URSide")
        self.gridLayout_3.addWidget(self.wdgBL_URSide, 2, 0, 1, 1)
        self.wdgB_URSide = QtWidgets.QWidget(self.pgURSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgB_URSide.sizePolicy().hasHeightForWidth())
        self.wdgB_URSide.setSizePolicy(sizePolicy)
        self.wdgB_URSide.setMinimumSize(QtCore.QSize(0, 50))
        self.wdgB_URSide.setStyleSheet("background-image:url(image/msgbox/up_right_side/dark/msg_b.png)")
        self.wdgB_URSide.setObjectName("wdgB_URSide")
        self.gridLayout_3.addWidget(self.wdgB_URSide, 2, 1, 1, 1)
        self.wdgBR_URSide = QtWidgets.QWidget(self.pgURSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgBR_URSide.sizePolicy().hasHeightForWidth())
        self.wdgBR_URSide.setSizePolicy(sizePolicy)
        self.wdgBR_URSide.setMinimumSize(QtCore.QSize(50, 50))
        self.wdgBR_URSide.setStyleSheet("background-image:url(image/msgbox/up_right_side/dark/msg_br.png)")
        self.wdgBR_URSide.setObjectName("wdgBR_URSide")
        self.gridLayout_3.addWidget(self.wdgBR_URSide, 2, 3, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.wdgTL_URSide = QtWidgets.QWidget(self.pgURSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgTL_URSide.sizePolicy().hasHeightForWidth())
        self.wdgTL_URSide.setSizePolicy(sizePolicy)
        self.wdgTL_URSide.setMinimumSize(QtCore.QSize(50, 128))
        self.wdgTL_URSide.setStyleSheet("background-image:url(image/msgbox/up_right_side/dark/msg_tl.png)")
        self.wdgTL_URSide.setObjectName("wdgTL_URSide")
        self.horizontalLayout_2.addWidget(self.wdgTL_URSide)
        self.wdgT_URSide = QtWidgets.QWidget(self.pgURSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgT_URSide.sizePolicy().hasHeightForWidth())
        self.wdgT_URSide.setSizePolicy(sizePolicy)
        self.wdgT_URSide.setMinimumSize(QtCore.QSize(0, 128))
        self.wdgT_URSide.setStyleSheet("background-image:url(image/msgbox/up_right_side/dark/msg_t.png)")
        self.wdgT_URSide.setObjectName("wdgT_URSide")
        self.horizontalLayout_2.addWidget(self.wdgT_URSide)
        self.wdgTR_URSide = QtWidgets.QWidget(self.pgURSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgTR_URSide.sizePolicy().hasHeightForWidth())
        self.wdgTR_URSide.setSizePolicy(sizePolicy)
        self.wdgTR_URSide.setMinimumSize(QtCore.QSize(110, 128))
        self.wdgTR_URSide.setStyleSheet("background-image:url(image/msgbox/up_right_side/dark/msg_tr.png)")
        self.wdgTR_URSide.setObjectName("wdgTR_URSide")
        self.horizontalLayout_2.addWidget(self.wdgTR_URSide)
        self.gridLayout_3.addLayout(self.horizontalLayout_2, 0, 0, 1, 4)
        self.stackedWidget.addWidget(self.pgURSide)
        self.pgULSide = QtWidgets.QWidget()
        self.pgULSide.setObjectName("pgULSide")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.pgULSide)
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_5.setSpacing(0)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.wdgTL_ULSide = QtWidgets.QWidget(self.pgULSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgTL_ULSide.sizePolicy().hasHeightForWidth())
        self.wdgTL_ULSide.setSizePolicy(sizePolicy)
        self.wdgTL_ULSide.setMinimumSize(QtCore.QSize(110, 128))
        self.wdgTL_ULSide.setStyleSheet("background-image:url(image/msgbox/up_left_side/dark/msg_tl.png)")
        self.wdgTL_ULSide.setObjectName("wdgTL_ULSide")
        self.horizontalLayout_3.addWidget(self.wdgTL_ULSide)
        self.wdgT_ULSide = QtWidgets.QWidget(self.pgULSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgT_ULSide.sizePolicy().hasHeightForWidth())
        self.wdgT_ULSide.setSizePolicy(sizePolicy)
        self.wdgT_ULSide.setMinimumSize(QtCore.QSize(0, 128))
        self.wdgT_ULSide.setStyleSheet("background-image:url(image/msgbox/up_left_side/dark/msg_t.png)")
        self.wdgT_ULSide.setObjectName("wdgT_ULSide")
        self.horizontalLayout_3.addWidget(self.wdgT_ULSide)
        self.wdgTR_ULSide = QtWidgets.QWidget(self.pgULSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgTR_ULSide.sizePolicy().hasHeightForWidth())
        self.wdgTR_ULSide.setSizePolicy(sizePolicy)
        self.wdgTR_ULSide.setMinimumSize(QtCore.QSize(50, 128))
        self.wdgTR_ULSide.setStyleSheet("background-image:url(image/msgbox/up_left_side/dark/msg_tr.png)")
        self.wdgTR_ULSide.setObjectName("wdgTR_ULSide")
        self.horizontalLayout_3.addWidget(self.wdgTR_ULSide)
        self.gridLayout_5.addLayout(self.horizontalLayout_3, 0, 0, 1, 3)
        self.wdgL_ULSide = QtWidgets.QWidget(self.pgULSide)
        self.wdgL_ULSide.setStyleSheet("background-image:url(image/msgbox/up_left_side/dark/msg_l.png)")
        self.wdgL_ULSide.setObjectName("wdgL_ULSide")
        self.gridLayout_5.addWidget(self.wdgL_ULSide, 1, 0, 1, 1)
        self.wdgMain_ULSide = QtWidgets.QWidget(self.pgULSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgMain_ULSide.sizePolicy().hasHeightForWidth())
        self.wdgMain_ULSide.setSizePolicy(sizePolicy)
        self.wdgMain_ULSide.setMinimumSize(QtCore.QSize(0, 0))
        self.wdgMain_ULSide.setStyleSheet("#wdgMain_ULSide{\n"
"    border-image:url(image/msgbox/up_left_side/dark/msg_center.png);\n"
"}\n"
"\n"
"QWidget{\n"
"    font:24px \"Arial\";\n"
"    color:rgb(207, 255, 255);\n"
"}\n"
"\n"
"QCheckBox{\n"
"    font:12px \"Arial\";\n"
"    color:rgb(240, 240, 0);\n"
"}\n"
"")
        self.wdgMain_ULSide.setObjectName("wdgMain_ULSide")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.wdgMain_ULSide)
        self.gridLayout_4.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_4.setSpacing(0)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.lblHintText_ULSide = QtWidgets.QLabel(self.wdgMain_ULSide)
        self.lblHintText_ULSide.setStyleSheet("font:48px;")
        self.lblHintText_ULSide.setText("")
        self.lblHintText_ULSide.setWordWrap(True)
        self.lblHintText_ULSide.setObjectName("lblHintText_ULSide")
        self.gridLayout_4.addWidget(self.lblHintText_ULSide, 0, 0, 1, 1)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem2)
        self.btnConfirm_ULSide = QtWidgets.QPushButton(self.wdgMain_ULSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnConfirm_ULSide.sizePolicy().hasHeightForWidth())
        self.btnConfirm_ULSide.setSizePolicy(sizePolicy)
        self.btnConfirm_ULSide.setMinimumSize(QtCore.QSize(100, 40))
        self.btnConfirm_ULSide.setObjectName("btnConfirm_ULSide")
        self.horizontalLayout_4.addWidget(self.btnConfirm_ULSide)
        self.chbKnown_ULSide = QtWidgets.QCheckBox(self.wdgMain_ULSide)
        self.chbKnown_ULSide.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.chbKnown_ULSide.setObjectName("chbKnown_ULSide")
        self.horizontalLayout_4.addWidget(self.chbKnown_ULSide)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem3)
        self.horizontalLayout_4.setStretch(0, 2)
        self.horizontalLayout_4.setStretch(3, 1)
        self.gridLayout_4.addLayout(self.horizontalLayout_4, 1, 0, 1, 1)
        self.gridLayout_4.setRowStretch(0, 1)
        self.gridLayout_5.addWidget(self.wdgMain_ULSide, 1, 1, 1, 1)
        self.wdgR_ULSide = QtWidgets.QWidget(self.pgULSide)
        self.wdgR_ULSide.setStyleSheet("background-image:url(image/msgbox/up_left_side/dark/msg_r.png)")
        self.wdgR_ULSide.setObjectName("wdgR_ULSide")
        self.gridLayout_5.addWidget(self.wdgR_ULSide, 1, 2, 1, 1)
        self.wdgBL_ULSide = QtWidgets.QWidget(self.pgULSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgBL_ULSide.sizePolicy().hasHeightForWidth())
        self.wdgBL_ULSide.setSizePolicy(sizePolicy)
        self.wdgBL_ULSide.setMinimumSize(QtCore.QSize(50, 50))
        self.wdgBL_ULSide.setStyleSheet("background-image:url(image/msgbox/up_left_side/dark/msg_bl.png)")
        self.wdgBL_ULSide.setObjectName("wdgBL_ULSide")
        self.gridLayout_5.addWidget(self.wdgBL_ULSide, 2, 0, 1, 1)
        self.wdgB_ULSide = QtWidgets.QWidget(self.pgULSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgB_ULSide.sizePolicy().hasHeightForWidth())
        self.wdgB_ULSide.setSizePolicy(sizePolicy)
        self.wdgB_ULSide.setMinimumSize(QtCore.QSize(0, 50))
        self.wdgB_ULSide.setStyleSheet("background-image:url(image/msgbox/up_left_side/dark/msg_b.png)")
        self.wdgB_ULSide.setObjectName("wdgB_ULSide")
        self.gridLayout_5.addWidget(self.wdgB_ULSide, 2, 1, 1, 1)
        self.wdgBR_ULSide = QtWidgets.QWidget(self.pgULSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgBR_ULSide.sizePolicy().hasHeightForWidth())
        self.wdgBR_ULSide.setSizePolicy(sizePolicy)
        self.wdgBR_ULSide.setMinimumSize(QtCore.QSize(50, 50))
        self.wdgBR_ULSide.setStyleSheet("background-image:url(image/msgbox/up_left_side/dark/msg_br.png)")
        self.wdgBR_ULSide.setObjectName("wdgBR_ULSide")
        self.gridLayout_5.addWidget(self.wdgBR_ULSide, 2, 2, 1, 1)
        self.stackedWidget.addWidget(self.pgULSide)
        self.pgDRSide = QtWidgets.QWidget()
        self.pgDRSide.setObjectName("pgDRSide")
        self.gridLayout_7 = QtWidgets.QGridLayout(self.pgDRSide)
        self.gridLayout_7.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_7.setSpacing(0)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.wdgTL_DRSide = QtWidgets.QWidget(self.pgDRSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgTL_DRSide.sizePolicy().hasHeightForWidth())
        self.wdgTL_DRSide.setSizePolicy(sizePolicy)
        self.wdgTL_DRSide.setMinimumSize(QtCore.QSize(50, 50))
        self.wdgTL_DRSide.setStyleSheet("background-image:url(image/msgbox/down_right_side/dark/msg_tl.png)")
        self.wdgTL_DRSide.setObjectName("wdgTL_DRSide")
        self.gridLayout_7.addWidget(self.wdgTL_DRSide, 0, 0, 1, 1)
        self.wdgT_DRSide = QtWidgets.QWidget(self.pgDRSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgT_DRSide.sizePolicy().hasHeightForWidth())
        self.wdgT_DRSide.setSizePolicy(sizePolicy)
        self.wdgT_DRSide.setMinimumSize(QtCore.QSize(0, 50))
        self.wdgT_DRSide.setStyleSheet("background-image:url(image/msgbox/down_right_side/dark/msg_t.png)")
        self.wdgT_DRSide.setObjectName("wdgT_DRSide")
        self.gridLayout_7.addWidget(self.wdgT_DRSide, 0, 1, 1, 1)
        self.wdgTR_DRSide = QtWidgets.QWidget(self.pgDRSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgTR_DRSide.sizePolicy().hasHeightForWidth())
        self.wdgTR_DRSide.setSizePolicy(sizePolicy)
        self.wdgTR_DRSide.setMinimumSize(QtCore.QSize(50, 50))
        self.wdgTR_DRSide.setStyleSheet("background-image:url(image/msgbox/down_right_side/dark/msg_tr.png)")
        self.wdgTR_DRSide.setObjectName("wdgTR_DRSide")
        self.gridLayout_7.addWidget(self.wdgTR_DRSide, 0, 2, 1, 1)
        self.wdgL_DRSide = QtWidgets.QWidget(self.pgDRSide)
        self.wdgL_DRSide.setStyleSheet("background-image:url(image/msgbox/down_right_side/dark/msg_l.png)")
        self.wdgL_DRSide.setObjectName("wdgL_DRSide")
        self.gridLayout_7.addWidget(self.wdgL_DRSide, 1, 0, 1, 1)
        self.wdgMain_DRSide = QtWidgets.QWidget(self.pgDRSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgMain_DRSide.sizePolicy().hasHeightForWidth())
        self.wdgMain_DRSide.setSizePolicy(sizePolicy)
        self.wdgMain_DRSide.setMinimumSize(QtCore.QSize(0, 0))
        self.wdgMain_DRSide.setStyleSheet("#wdgMain_DRSide{\n"
"    border-image:url(image/msgbox/down_right_side/dark/msg_center.png);\n"
"}\n"
"\n"
"QWidget{\n"
"    font:24px \"Arial\";\n"
"    color:rgb(207, 255, 255);\n"
"}\n"
"\n"
"QCheckBox{\n"
"    font:12px \"Arial\";\n"
"    color:rgb(240, 240, 0);\n"
"}\n"
"")
        self.wdgMain_DRSide.setObjectName("wdgMain_DRSide")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.wdgMain_DRSide)
        self.gridLayout_6.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_6.setSpacing(0)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.lblHintText_DRSide = QtWidgets.QLabel(self.wdgMain_DRSide)
        self.lblHintText_DRSide.setStyleSheet("font:48px;")
        self.lblHintText_DRSide.setText("")
        self.lblHintText_DRSide.setWordWrap(True)
        self.lblHintText_DRSide.setObjectName("lblHintText_DRSide")
        self.gridLayout_6.addWidget(self.lblHintText_DRSide, 0, 0, 1, 1)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem4)
        self.btnConfirm_DRSide = QtWidgets.QPushButton(self.wdgMain_DRSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnConfirm_DRSide.sizePolicy().hasHeightForWidth())
        self.btnConfirm_DRSide.setSizePolicy(sizePolicy)
        self.btnConfirm_DRSide.setMinimumSize(QtCore.QSize(100, 40))
        self.btnConfirm_DRSide.setObjectName("btnConfirm_DRSide")
        self.horizontalLayout_6.addWidget(self.btnConfirm_DRSide)
        self.chbKnown_DRSide = QtWidgets.QCheckBox(self.wdgMain_DRSide)
        self.chbKnown_DRSide.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.chbKnown_DRSide.setObjectName("chbKnown_DRSide")
        self.horizontalLayout_6.addWidget(self.chbKnown_DRSide)
        spacerItem5 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem5)
        self.horizontalLayout_6.setStretch(0, 2)
        self.horizontalLayout_6.setStretch(3, 1)
        self.gridLayout_6.addLayout(self.horizontalLayout_6, 1, 0, 1, 1)
        self.gridLayout_6.setRowStretch(0, 1)
        self.gridLayout_7.addWidget(self.wdgMain_DRSide, 1, 1, 1, 1)
        self.wdgR_DRSide = QtWidgets.QWidget(self.pgDRSide)
        self.wdgR_DRSide.setStyleSheet("background-image:url(image/msgbox/down_right_side/dark/msg_r.png)")
        self.wdgR_DRSide.setObjectName("wdgR_DRSide")
        self.gridLayout_7.addWidget(self.wdgR_DRSide, 1, 2, 1, 1)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.wdgBL_DRSide = QtWidgets.QWidget(self.pgDRSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgBL_DRSide.sizePolicy().hasHeightForWidth())
        self.wdgBL_DRSide.setSizePolicy(sizePolicy)
        self.wdgBL_DRSide.setMinimumSize(QtCore.QSize(50, 128))
        self.wdgBL_DRSide.setStyleSheet("background-image:url(image/msgbox/down_right_side/dark/msg_bl.png);\n"
"background-repeat:no-repeat;\n"
"background-position:top;")
        self.wdgBL_DRSide.setObjectName("wdgBL_DRSide")
        self.horizontalLayout_5.addWidget(self.wdgBL_DRSide)
        self.wdgB_DRSide = QtWidgets.QWidget(self.pgDRSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgB_DRSide.sizePolicy().hasHeightForWidth())
        self.wdgB_DRSide.setSizePolicy(sizePolicy)
        self.wdgB_DRSide.setMinimumSize(QtCore.QSize(0, 128))
        self.wdgB_DRSide.setStyleSheet("background-image:url(image/msgbox/down_right_side/dark/msg_b.png);\n"
"background-repeat:repeat-x;\n"
"background-position:top;")
        self.wdgB_DRSide.setObjectName("wdgB_DRSide")
        self.horizontalLayout_5.addWidget(self.wdgB_DRSide)
        self.wdgBR_DRSide = QtWidgets.QWidget(self.pgDRSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgBR_DRSide.sizePolicy().hasHeightForWidth())
        self.wdgBR_DRSide.setSizePolicy(sizePolicy)
        self.wdgBR_DRSide.setMinimumSize(QtCore.QSize(110, 128))
        self.wdgBR_DRSide.setStyleSheet("background-image:url(image/msgbox/down_right_side/dark/msg_br.png)")
        self.wdgBR_DRSide.setObjectName("wdgBR_DRSide")
        self.horizontalLayout_5.addWidget(self.wdgBR_DRSide)
        self.gridLayout_7.addLayout(self.horizontalLayout_5, 2, 0, 1, 3)
        self.stackedWidget.addWidget(self.pgDRSide)
        self.pgDLSide = QtWidgets.QWidget()
        self.pgDLSide.setObjectName("pgDLSide")
        self.gridLayout_9 = QtWidgets.QGridLayout(self.pgDLSide)
        self.gridLayout_9.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_9.setSpacing(0)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.wdgTL_DLSide = QtWidgets.QWidget(self.pgDLSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgTL_DLSide.sizePolicy().hasHeightForWidth())
        self.wdgTL_DLSide.setSizePolicy(sizePolicy)
        self.wdgTL_DLSide.setMinimumSize(QtCore.QSize(50, 50))
        self.wdgTL_DLSide.setStyleSheet("background-image:url(image/msgbox/down_left_side/dark/msg_tl.png)")
        self.wdgTL_DLSide.setObjectName("wdgTL_DLSide")
        self.gridLayout_9.addWidget(self.wdgTL_DLSide, 0, 0, 1, 1)
        self.wdgT_DLSide = QtWidgets.QWidget(self.pgDLSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgT_DLSide.sizePolicy().hasHeightForWidth())
        self.wdgT_DLSide.setSizePolicy(sizePolicy)
        self.wdgT_DLSide.setMinimumSize(QtCore.QSize(0, 50))
        self.wdgT_DLSide.setStyleSheet("background-image:url(image/msgbox/down_left_side/dark/msg_t.png)")
        self.wdgT_DLSide.setObjectName("wdgT_DLSide")
        self.gridLayout_9.addWidget(self.wdgT_DLSide, 0, 1, 1, 1)
        self.wdgTR_DLSide = QtWidgets.QWidget(self.pgDLSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgTR_DLSide.sizePolicy().hasHeightForWidth())
        self.wdgTR_DLSide.setSizePolicy(sizePolicy)
        self.wdgTR_DLSide.setMinimumSize(QtCore.QSize(50, 50))
        self.wdgTR_DLSide.setStyleSheet("background-image:url(image/msgbox/down_left_side/dark/msg_tr.png)")
        self.wdgTR_DLSide.setObjectName("wdgTR_DLSide")
        self.gridLayout_9.addWidget(self.wdgTR_DLSide, 0, 2, 1, 1)
        self.wdgL_DLSide = QtWidgets.QWidget(self.pgDLSide)
        self.wdgL_DLSide.setStyleSheet("background-image:url(image/msgbox/down_left_side/dark/msg_l.png)")
        self.wdgL_DLSide.setObjectName("wdgL_DLSide")
        self.gridLayout_9.addWidget(self.wdgL_DLSide, 1, 0, 1, 1)
        self.wdgMain_DLSide = QtWidgets.QWidget(self.pgDLSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgMain_DLSide.sizePolicy().hasHeightForWidth())
        self.wdgMain_DLSide.setSizePolicy(sizePolicy)
        self.wdgMain_DLSide.setMinimumSize(QtCore.QSize(0, 0))
        self.wdgMain_DLSide.setStyleSheet("#wdgMain_DLSide{\n"
"    border-image:url(image/msgbox/up_left_side/dark/msg_center.png);\n"
"}\n"
"\n"
"QWidget{\n"
"    font:24px \"Arial\";\n"
"    color:rgb(207, 255, 255);\n"
"}\n"
"\n"
"QCheckBox{\n"
"    font:12px \"Arial\";\n"
"    color:rgb(240, 240, 0);\n"
"}\n"
"")
        self.wdgMain_DLSide.setObjectName("wdgMain_DLSide")
        self.gridLayout_8 = QtWidgets.QGridLayout(self.wdgMain_DLSide)
        self.gridLayout_8.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_8.setSpacing(0)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.lblHintText_DLSide = QtWidgets.QLabel(self.wdgMain_DLSide)
        self.lblHintText_DLSide.setStyleSheet("font:48px;")
        self.lblHintText_DLSide.setText("")
        self.lblHintText_DLSide.setWordWrap(True)
        self.lblHintText_DLSide.setObjectName("lblHintText_DLSide")
        self.gridLayout_8.addWidget(self.lblHintText_DLSide, 0, 0, 1, 1)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        spacerItem6 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem6)
        self.btnConfirm_DLSide = QtWidgets.QPushButton(self.wdgMain_DLSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnConfirm_DLSide.sizePolicy().hasHeightForWidth())
        self.btnConfirm_DLSide.setSizePolicy(sizePolicy)
        self.btnConfirm_DLSide.setMinimumSize(QtCore.QSize(100, 40))
        self.btnConfirm_DLSide.setObjectName("btnConfirm_DLSide")
        self.horizontalLayout_8.addWidget(self.btnConfirm_DLSide)
        self.chbKnown_DLSide = QtWidgets.QCheckBox(self.wdgMain_DLSide)
        self.chbKnown_DLSide.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.chbKnown_DLSide.setObjectName("chbKnown_DLSide")
        self.horizontalLayout_8.addWidget(self.chbKnown_DLSide)
        spacerItem7 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_8.addItem(spacerItem7)
        self.horizontalLayout_8.setStretch(0, 2)
        self.horizontalLayout_8.setStretch(3, 1)
        self.gridLayout_8.addLayout(self.horizontalLayout_8, 1, 0, 1, 1)
        self.gridLayout_8.setRowStretch(0, 1)
        self.gridLayout_9.addWidget(self.wdgMain_DLSide, 1, 1, 1, 1)
        self.wdgR_DLSide = QtWidgets.QWidget(self.pgDLSide)
        self.wdgR_DLSide.setStyleSheet("background-image:url(image/msgbox/down_left_side/dark/msg_r.png)")
        self.wdgR_DLSide.setObjectName("wdgR_DLSide")
        self.gridLayout_9.addWidget(self.wdgR_DLSide, 1, 2, 1, 1)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setSpacing(0)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.wdgBL_DLSide = QtWidgets.QWidget(self.pgDLSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgBL_DLSide.sizePolicy().hasHeightForWidth())
        self.wdgBL_DLSide.setSizePolicy(sizePolicy)
        self.wdgBL_DLSide.setMinimumSize(QtCore.QSize(110, 128))
        self.wdgBL_DLSide.setStyleSheet("background-image:url(image/msgbox/down_left_side/dark/msg_bl.png);")
        self.wdgBL_DLSide.setObjectName("wdgBL_DLSide")
        self.horizontalLayout_7.addWidget(self.wdgBL_DLSide)
        self.wdgB_DLSide = QtWidgets.QWidget(self.pgDLSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgB_DLSide.sizePolicy().hasHeightForWidth())
        self.wdgB_DLSide.setSizePolicy(sizePolicy)
        self.wdgB_DLSide.setMinimumSize(QtCore.QSize(0, 128))
        self.wdgB_DLSide.setStyleSheet("background-image:url(image/msgbox/down_left_side/dark/msg_b.png);\n"
"background-repeat:repeat-x;\n"
"background-position:top;")
        self.wdgB_DLSide.setObjectName("wdgB_DLSide")
        self.horizontalLayout_7.addWidget(self.wdgB_DLSide)
        self.wdgBR_DLSide = QtWidgets.QWidget(self.pgDLSide)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wdgBR_DLSide.sizePolicy().hasHeightForWidth())
        self.wdgBR_DLSide.setSizePolicy(sizePolicy)
        self.wdgBR_DLSide.setMinimumSize(QtCore.QSize(50, 128))
        self.wdgBR_DLSide.setStyleSheet("background-image:url(image/msgbox/down_left_side/dark/msg_br.png);\n"
"background-repeat:no-repeat;\n"
"background-position:top;")
        self.wdgBR_DLSide.setObjectName("wdgBR_DLSide")
        self.horizontalLayout_7.addWidget(self.wdgBR_DLSide)
        self.gridLayout_9.addLayout(self.horizontalLayout_7, 2, 0, 1, 3)
        self.stackedWidget.addWidget(self.pgDLSide)
        self.gridLayout.addWidget(self.stackedWidget, 0, 0, 1, 1)

        self.retranslateUi(DlgHintBox)
        self.stackedWidget.setCurrentIndex(3)
        QtCore.QMetaObject.connectSlotsByName(DlgHintBox)

    def retranslateUi(self, DlgHintBox):
        _translate = QtCore.QCoreApplication.translate
        DlgHintBox.setWindowTitle(_translate("DlgHintBox", "Dialog"))
        self.btnConfirm_URSide.setText(_translate("DlgHintBox", "OK"))
        self.chbKnown_URSide.setText(_translate("DlgHintBox", "don\'t show this again"))
        self.btnConfirm_ULSide.setText(_translate("DlgHintBox", "OK"))
        self.chbKnown_ULSide.setText(_translate("DlgHintBox", "don\'t show this again"))
        self.btnConfirm_DRSide.setText(_translate("DlgHintBox", "OK"))
        self.chbKnown_DRSide.setText(_translate("DlgHintBox", "don\'t show this again"))
        self.btnConfirm_DLSide.setText(_translate("DlgHintBox", "OK"))
        self.chbKnown_DLSide.setText(_translate("DlgHintBox", "don\'t show this again"))
