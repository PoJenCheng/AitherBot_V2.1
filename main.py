from FunctionLib_UI import matplotlib_pyqt as mat
from PyQt5.QtWidgets import *
import sys

app = QApplication(sys.argv)
w = mat.MainWidget()
w.show()
sys.exit(app.exec_())