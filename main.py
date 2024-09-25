from FunctionLib_UI import MainInterface as mi
from PyQt5.QtCore import QTranslator, QLocale, QCoreApplication
from PyQt5.QtWidgets import *

import sys

app = QApplication(sys.argv)

lang = mi.LAN_EN
if len(sys.argv) > 1: 
    strLang = ''
    if int(sys.argv[-1]) == mi.LAN_CN:
        
        strLang = 'language/Aitherbot_tw.qm'
        lang = int(sys.argv[-1])
        
    if strLang != '':
        translator = QTranslator()
        translator.load(strLang) 
        app.installTranslator(translator)

w = mi.MainInterface(lang)
# w.show()
w.showFullScreen()
sys.exit(app.exec_()) 