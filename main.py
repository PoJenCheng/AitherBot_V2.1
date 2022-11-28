from FunctionLib_UI import matplotlib_pyqt as mat
from PyQt5.QtWidgets import *
import sys

# import logging
# log_SYSTEM: logging.Logger = logging.getLogger(name='SYSTEM')
# log_SYSTEM.setLevel(logging.DEBUG)
# handler: logging.StreamHandler = logging.StreamHandler()
# handler: logging.StreamHandler = logging.FileHandler('my.log','w','utf-8')
# formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y/%m/%d %H:%M:%s')
# handler.setFormatter(formatter)
# log_SYSTEM.addHandler(handler)
# log_SYSTEM.info('start software')


app = QApplication(sys.argv)
w = mat.MainWidget()
w.show()
sys.exit(app.exec_())


# pyuic5 -o FunctionLib_UI/ui_matplotlib_pyqt.py FunctionLib_UI/ui_matplotlib_pyqt.ui
# pyuic5 -o FunctionLib_UI/ui_coordinate_system.py FunctionLib_UI/ui_coordinate_system.ui
# pyuic5 -o FunctionLib_UI/ui_set_point_system.py FunctionLib_UI/ui_set_point_system.ui
