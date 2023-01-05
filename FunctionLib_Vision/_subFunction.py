#命名example：RunJoystick

import math
import numpy

def GetNorm(V):
    """get norm

    Args:
        V (_numpy.array_): vector

    Returns:
        d (_number_): (float)
    """
    if V.shape[0] == 3:
        d = math.sqrt(numpy.square(V[0])+numpy.square(V[1])+numpy.square(V[2]))
    elif V.shape[0] == 2:
        d = math.sqrt(numpy.square(V[0])+numpy.square(V[1]))
    else:
        print("GetNorm error")
        return 0
    return d
