from FunctionLib_Robot.__init__ import *

# 過濾掉高頻雜訊
def lowPass(filterData):
    ignorePoint = []
    dataTemp = []
    k = 1
    for point in range(len(filterData)):
        if point == 0 and filterData[point] != 0:
            dataTemp.append(filterData[point])
        else:
            diff = abs(filterData[point] - filterData[point-k])
            if diff <= filterTolerance*k:
                dataTemp.append(filterData[point])
                k = 1
            elif diff > filterTolerance:
                k += 1
                ignorePoint.append(point)
    
    mask = np.ones_like(filterData, dtype=bool)
    mask[ignorePoint] = False
    
    ndFilterData = np.array(filterData)
    filterData = ndFilterData[mask]
    # for i in range(len(ignorePoint)):
    #     filterData[ignorePoint[i]] = 0
    
    return filterData