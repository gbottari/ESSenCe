'''
Created on Mar 19, 2011

@author: Giulio

This script will output an error (like MSE or MAE) for various
prediction periods. This will be done with a predictor and the
Naive method.
'''

from system.filters import HoltFilter, ExpFilter, AdaptableHoltFilter
from traceScaler import scale
from bestParameters import error, MSE, HIB, MAPE, MAE, gridOpt
from system.configReader import ConfigReader


def main():
    filename = '../../tmp/wc98_1.txt'
    method = MSE
    
    precision = 0.05
    
    f = open(filename)
    lines = f.read()
    f.close()
    raw_data = [float(token) for token in lines.splitlines()]
    
    c = ConfigReader()
    c.parse('../../tmp/config.txt')
    cluster = c.readCluster()
    scale(raw_data,cluster.availableServers,maxUtil=1.0)
    
    
    for pred_step in range(1, 500):
        """
        Take the averages at pred_step windows
        """
        data = []
        acc = 0.0
        for i in range(len(raw_data)):
            acc += raw_data[i]
            if (i + 1) % pred_step == 0:
                data.append(acc / pred_step)
                acc = 0
        rest = len(raw_data) % pred_step
        if rest > 0:
            data.append(acc / rest)
    
        #take the optimized Holt parameters:
        """
        pars = gridOpt(data, precision, method)
        holt = HoltFilter(alpha=pars[0], beta=pars[1])
        """
        holt = AdaptableHoltFilter(alpha=1.0, beta=0.05, windowSize=10, optMethod=method)
        
        #apply Holt and Naive to the real data
        holtError = 0.0
        naiveError = 0.0
        acc = 0.0
        avg = 0.0
        pred = 0.0
        for i in range(len(raw_data)):
            if (i + 1) > pred_step: #don't count the first error
                naiveError += error(avg, raw_data[i], method)
                holtError += error(pred, raw_data[i], method)
            
            acc += raw_data[i]
            if (i + 1) % pred_step == 0:
                avg = acc / pred_step                
                pred = holt.apply(avg)
                acc = 0.0            
            
        holtError /= len(raw_data) - pred_step
        naiveError /= len(raw_data) - pred_step

        print pred_step, naiveError, holtError

if __name__ == '__main__':
    main()