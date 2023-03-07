from FunctionLib_UI import matplotlib_pyqt as mat
from PyQt5.QtWidgets import *
import sys

app = QApplication(sys.argv)
w = mat.MainWidget()
w.show()
sys.exit(app.exec_())


# pyuic5 -o FunctionLib_UI/ui_matplotlib_pyqt.py FunctionLib_UI/ui_matplotlib_pyqt.ui
# pyuic5 -o FunctionLib_UI/ui_coordinate_system.py FunctionLib_UI/ui_coordinate_system.ui
# pyuic5 -o FunctionLib_UI/ui_set_point_system.py FunctionLib_UI/ui_set_point_system.ui

# from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
# QVTKWidget(self.layoutWidget replace as QVTKRenderWindowInteractor(self.layoutWidget
