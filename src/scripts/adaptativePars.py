'''
Created on Mar 18, 2011

@author: giulio

This script will output the mean error (such as MSE or MAE) for various
adaptation windows. The goal is to find an optimal window to make adaptations
in various traces.
'''

'''
We consider the errors after the first adaption. Moreover, the global 
predictor uses the same window to make predictions, thus rendering 
the comparison more fairly.
'''


from system.filters import HoltFilter
from traceScaler import scale
from bestParameters import error, MSE, HIB, MAPE, MAE, gridOpt, errorsDict
from system.configReader import ConfigReader


def main():
    filename = '../../tmp/nasa_3.txt'
    method = MAE
    pred_step = 10                 # applies predictions every given seconds
    precision = 0.05
    
    f = open(filename)
    lines = f.read()
    f.close()
    raw_data = [float(token) for token in lines.splitlines()]
    
    c = ConfigReader()
    c.parse('../../tmp/config.txt')
    cluster = c.readCluster()
    scale(raw_data,cluster.availableServers,maxUtil=1.0)
    
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
        
    """
    Calculate the optimum pars
    """
    opt_pars = gridOpt(data, precision, method)
    
    """
    Print header
    """
    print "#trace: " + filename
    print "#pred_step: %d" % pred_step
    print "#precision: %f" % precision
    print '#error: %s' % errorsDict[method]
    print '#opt-alpha: %f, opt-beta: %f' % (opt_pars[0],opt_pars[1])
    print '#1-adapt_step #2-adapt_error #3-opt_error'
    
    """
    Calculate the adaptive error
    """   
    for adapt_step in range(pred_step, 500):
        adapt_window_size = adapt_step # adapt parameters using a window of the given size
        opt_holt = HoltFilter(alpha=opt_pars[0],beta=opt_pars[0])
        opt_pred = 0.0
        opt_error = 0.0
        adapt_window = []
        
        '''
        Holt's initialization doesn't matter, because we'll consider
        the error only after the first adaption
        '''
        adapt_holt = HoltFilter()   
        adapt_pred = 0.0
        adapt_error = 0.0        
        acc = 0.0
        for i in range(len(raw_data)):
            acc += raw_data[i]
            
            if (i + 1) > adapt_step: # calculate error according to method, skipping the first window         
                adapt_error += error(adapt_pred, raw_data[i], method)
                opt_error += error(opt_pred, raw_data[i], method)
            
            if (i + 1) % pred_step == 0: # got a data point
                adapt_window.append(acc / pred_step)
                if len(adapt_window) > adapt_window_size:
                    adapt_window.pop(0)
                
            if (i + 1) % adapt_step == 0: # do adaption
                adapt_pars = gridOpt(adapt_window, precision, MSE)
                adapt_holt.alpha = adapt_pars[0]
                adapt_holt.beta = adapt_pars[1] 
    
            if (i + 1) % pred_step == 0: # do prediction after adaptation
                avg = acc / pred_step
                adapt_pred = adapt_holt.apply(avg)
                opt_pred = opt_holt.apply(avg)
                acc = 0.0

        print adapt_step, adapt_error / (len(raw_data) - adapt_step), opt_error / (len(raw_data) - adapt_step)

if __name__ == '__main__':
    main()