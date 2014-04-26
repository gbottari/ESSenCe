'''
Created on Oct 19, 2011

@author: giulio
'''

import system.filters as filters
from stats import file2data



def testPredictor(pred, data, start=1, mode=filters.MAE):
    debug = False
    
    assert len(data) > start
    
    prediction =  pred.apply(data[0])
    accError = 0.0
    
    for i in range(1, len(data)):
        if debug:
            print 'i = %03d, predicted = %f, actual = %f' % (i, prediction, data[i])
        if i > start - 1:
            accError += filters.error(prediction, data[i], mode)
        prediction = pred.apply(data[i])
        

    return accError / (len(data) - start)


def printStats(name, error, parameters=None):
    print "%-7s: Error = %-15f; Pars = %s" % (name, error, parameters)


def main():
    trace = '../../tmp/wc98_1.txt'
    window = 1
    mode = filters.MAE
    step = 20
    
    data = file2data(1, trace)[0]
    
    newData = []
    x = 0.0
    for i in range(len(data)):
        x += data[i]
        
        if (i + 1) % step == 0:
            x /= step
            newData.append(x)
            x = 0.0
    data = newData
    
    bote = filters.Bote()    
    AHOLT = filters.AdaptableHoltFilter(alpha=0.5, beta=0.5, k=1, windowSize=window, optMethod=mode)
    HOLT = filters.HoltFilter(alpha=0.8, beta=0.9, k=1)
    dummy = filters.DummyFilter()
    expAvg = filters.ExpAvg(alpha=0.7)

    error = testPredictor(bote, data, window, mode=mode)
    printStats('Bote', error)
    
    #error = testPredictor(AHOLT, data, window)
    #printStats('Adaptable Holt', error)
    
    error = testPredictor(HOLT, data, window)
    printStats('Holt', error, {'alpha': HOLT.alpha, 'beta': HOLT.beta})
    
    error = testPredictor(expAvg, data, window)
    printStats('ExpAvg', error, {'alpha': expAvg.alpha})
    
    error = testPredictor(dummy, data, window)
    printStats('Dummy', error)


if __name__ == '__main__':
    main()