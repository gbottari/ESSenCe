# -*- coding: utf-8 -*-
'''
Created on Mar 14, 2011

@author: giulio
'''

from system.filters import HoltFilter, ExpFilter
from bestParameters import error, MSE, MAE, MAPE, HIB, errorsDict, gridMethod2_h3
from traceScaler import scale
from system.configReader import ConfigReader


def main():
    filename = '../../tmp/nasa_3.txt'
    step = 20
    method = MSE
    
    f = open(filename)
    lines = f.read()
    f.close()
    raw_data = [float(token) for token in lines.splitlines()]
    
    c = ConfigReader()
    c.parse('../../tmp/config.txt')
    cluster = c.readCluster()
    scale(raw_data, cluster.availableServers, maxUtil=1.0)
    
    #holt1 = HoltFilter(alpha=0.50, beta=0.10) #jeito ruim
    holt2 = HoltFilter(alpha=0.65, beta=0.05) #com média
    '''
    # apply holt1
    pred = 0
    error1 = 0.0
    for i in range(len(raw_data)):
        if (i + 1) > step:        
            error1 += error(pred, raw_data[i], method)
        holt1.apply(raw_data[i]) # update holt
        if (i + 1) % step == 0:  # every 'step' apply holt
            pred = holt1.S + step * holt1.B
    error1 /= len(raw_data) - step
    '''
    # apply holt2
    acc = 0.0
    pred = 0
    error2 = 0.0
    for i in range(len(raw_data)):
        if (i + 1) > step:        
            error2 += error(pred, raw_data[i], method)
        acc += raw_data[i]
        if (i + 1) % step == 0: # every 'step' apply holt
            pred = holt2.apply(float(acc) / step)            
            acc = 0.0
    error2 /= len(raw_data) - step
    
    print '#step: %f' % step
    print '#error: %s' % errorsDict[method]
    #print '#holt1_error: %f' % error1
    print '#holt2_error: %f' % error2
    print '#1-alpha #2-error'
    
    alpha = 1.0
    dec = 0.01
    while alpha > 0.0:
        # apply holt3
        acc = 0
        pred = 0.0
        error3 = 0.0
        
        holt3_pars = gridMethod2_h3(raw_data, window=step, step=0.05, Yalpha=alpha, method=method)        
        holt3 = HoltFilter(alpha=holt3_pars[0], beta=holt3_pars[1]) #com exp avg
        #holt3 = HoltFilter(alpha=0.55, beta=0.05) #com exp avg
        
        Y = raw_data[0] # initialization of exponential average
        for i in range(len(raw_data)):
            Y = alpha * raw_data[i] + (1 - alpha) * Y # smooth the data
            
            if (i + 1) > step:        
                error3 += error(pred, raw_data[i], method)            
            
            if (i + 1) % step == 0: # every 'step' apply holt
                pred = holt3.apply(Y)
                acc = 0
        
        print alpha, error3 / (len(raw_data) - step)

        alpha -= dec


if __name__ == '__main__':
    main()