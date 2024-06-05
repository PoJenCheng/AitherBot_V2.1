import logging
import sys
import os
from datetime import datetime


logger = logging.getLogger('AitherBot')

# 正式版時再改掉level
level = logging.DEBUG

logger.setLevel(level)
logger.propagate = False
formatter = logging.Formatter(
    fmt=f"[%(levelname)1.1s %(asctime)s][%(module)s:%(lineno)d] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

handlerCmd = logging.StreamHandler(sys.stdout)
handlerCmd.setFormatter(formatter)
handlerCmd.setLevel(level)
logger.addHandler(handlerCmd)

filename = datetime.now().strftime('%Y-%m-%d_%H_%M_%S.log')

try:
    os.makedirs('logs')
except FileExistsError:
    pass

try:
    subDir = os.path.join('logs', datetime.now().strftime('%Y-%m-%d'))
    os.makedirs(subDir)
except FileExistsError:
    pass 

    
filename = os.path.join(os.getcwd(), subDir, filename)

tags = ['%(levelname)1.1s',
        '%(asctime)s',
        '%(module)20s',
        '%(lineno)4d',
        '%(message)s']

ff = ','.join(tags)
formatter = logging.Formatter(
    fmt = ff, datefmt = "%Y-%m-%d %H:%M:%S"
)

handlerFile = logging.FileHandler(filename)
handlerFile.setLevel(level)
handlerFile.setFormatter(formatter)
logger.addHandler(handlerFile)