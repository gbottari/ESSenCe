'''
Created on Nov 22, 2010

@author: Giulio
'''

from system.filters import HoltFilter, ExpFilter
from traceScaler import scale
from system.configReader import ConfigReader

'''
def genericGM(data, parCount, filter, step=0.01):
    
    #initialization
    parameters = []
    for i in range(parCount):
        parameters.append(0.0)
        i = i
    
    combination = 0x001
    
    while combination < 2 ** parCount - 1:
        #dissecate the combination binary to know which parameter we must increment or zero-out

        mask = 0x001
        for i in range(parCount):            
            if mask & combination != 0: #equals one
                parameters[i] += step
            else:
                parameters[i] = combination * step
            mask << 1
'''
   
MSE = 0
MAE = 1
MAPE = 2
HIB = 3

errorsDict = {MSE: 'MSE', MAE: 'MAE', MAPE: 'MAPE', HIB: 'HIB'}

def error(x1, x2, method=MSE):
    if method == MSE:
        return (x1 - x2) ** 2
    elif method == MAE:
        return abs(x1 - x2)
    elif method == HIB:
        if x2 > x1:
            return (x1 - x2) ** 2
        else:
            return abs(x1 - x2)
    elif method == MAPE:                                
        if x2 > 0:
            return abs(x1 - x2)/x2


def gridMethod1(data, step=0.01, method=MSE):    
    alpha = 1.0
    result = (1.0, float('inf'))
    
    results = []
    
    while alpha > 0.0:            
        filter = ExpFilter(alpha=alpha)
        SE = 0.0
        for i in range(len(data) - 1):
            prediction = filter.apply(data[i])
            SE += error(prediction, data[i+1], method)
        
        if SE < result[1]:
            result = (alpha, SE)
        
        results.append((alpha, SE))
        
        alpha -= step        
    
    #results.sort(key=lambda x: x[1], reverse=True)
    #for alpha, SE in results:
    #    print 'alpha=%f -> MError=%f' % (alpha,SE / len(data))
    
    return result

def gridMethod2_h1(data, window, step=0.01):
    """
    Data = trace    
    """    
    alpha, beta = 1.0, 1.0
    result = (1.0, 1.0, float('inf'))
    results = []
    
    while alpha > 0.0:
        beta = 1.0
        while beta > 0.0:            
            filter = HoltFilter(alpha=alpha,beta=beta)
            SE = 0.0
            for i in range(len(data)-window):
                filter.apply(data[i])
            
                if (i + 1) % window == 0:
                    pred = filter.S + window * filter.B
                    
                    avg = 0
                    end = min(i + window,len(data))
                    for j in range(i, end):
                        avg += data[j]
                    avg /= (end - i)
                                    
                    SE += (pred - avg) ** 2
            
            if SE < result[2]:
                result = (alpha, beta, SE)
            
            results.append((alpha, beta, SE))            
            beta -= step
        alpha -= step        
    
    results.sort(key=lambda x: x[2], reverse=True)
    for alpha, beta, SE in results:
        print 'alpha=%f, beta=%f -> MError=%f' % (alpha,beta,SE)
    
    return result


def gridMethod2_h2(data, step=0.01, method=MSE):    
    alpha, beta = 1.0, 1.0
    result = (1.0, 1.0, float('inf'))
    
    results = []
    
    while alpha > 0.0:
        beta = 1.0
        while beta > 0.0:            
            filter = HoltFilter(alpha=alpha,beta=beta)
            SE = 0.0
            for i in range(len(data)-1):
                #prediction = max(filter.apply(data[i]),data[i])
                prediction = filter.apply(data[i])                
                SE += error(prediction, data[i+1], method)                       
            
            if SE < result[2]:
                result = (alpha, beta, SE)
            
            results.append((alpha, beta, SE))
            
            beta -= step
        alpha -= step        
    
    #results.sort(key=lambda x: x[2], reverse=True)
    #for alpha, beta, SE in results:
    #    print 'alpha=%f, beta=%f -> MError=%f' % (alpha,beta,SE)
    
    return result

gridOpt = gridMethod2_h2

def gridMethod2_h3(data, window, step=0.01, Yalpha=0.8, method=MSE):
    """
    Data = trace    
    """    
    alpha, beta = 1.0, 1.0
    result = (1.0, 1.0, float('inf'))
    results = []
    
    while alpha > 0.0:
        beta = 1.0
        while beta > 0.0:            
            Y = data[0]
            SE = 0.0
            filter = HoltFilter(alpha=alpha,beta=beta)
            pred = 0.0
            
            for i in range(len(data)):
                Y = Yalpha * data[i] + (1 - Yalpha) * Y 
            
                if (i + 1) > window:
                    SE += error(pred, data[i], method)
            
                if (i + 1) % window == 0:
                    pred = filter.apply(Y)
            
            if SE < result[2]:
                result = (alpha, beta, SE)
            
            results.append((alpha, beta, SE))            
            beta -= step
        alpha -= step        
    
    #results.sort(key=lambda x: x[2], reverse=True)
    #for alpha, beta, SE in results:
    #    print 'alpha=%f, beta=%f -> MError=%f' % (alpha,beta,SE)
    
    return result


def naive(data, method=MSE):    
                      
    SE = 0.0
    for i in range(len(data)-1):
        prediction = data[i]
        SE += error(prediction, data[i+1], method)                      

    return SE


def main():
    filename = '../../tmp/nasa_3.txt'
    step = 20
    f = open(filename)
    lines = f.read()
    f.close()
    raw_data = [float(token) for token in lines.splitlines()]
    
    c = ConfigReader()
    c.parse('../../tmp/config.txt')
    cluster = c.readCluster()
    scale(raw_data,cluster.availableServers,maxUtil=1.0)
    
    data = []
    acc = 0
    for i in range(len(raw_data)):
        acc += raw_data[i]
        if (i + 1) % step == 0:
            data.append(float(acc) / step)
            acc = 0
    rest = len(raw_data) % step
    if rest > 0:
        data.append(float(acc) / rest)
        
    #print gridMethod2_h3(raw_data, window=step, step=0.05, Yalpha=0.8, method=MAPE)
    #print naive(data,MSE)
    print gridMethod2_h2(data, 0.05, MSE)
    #print gridMethod1(data)

if __name__ == '__main__':
    main()