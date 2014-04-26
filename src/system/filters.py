'''
Created on Sep 22, 2010

@author: giulio
@original author: Vinicius Petrucci [http://www.ic.uff.br/~vpetrucci/master.html]
'''
from system.Builder import Builder

class Filter(object):
    def apply(self, x):
        raise NotImplementedError, "Must provide .apply()"
    

class DummyFilter(Filter):
    def apply(self, x):
        return x

Naive = Reactive = DummyFilter


class ExpFilter(Filter):
    def __init__(self, alpha=0.5):
        self.alpha = alpha
        self.S = 0.0
        self._inited = False

    def apply(self, x):
        if not self._inited:
            self.S = x
            self._inited = True
        self.S = self.alpha*x + (1-self.alpha)*self.S 
        return self.S

ExpAvg = ExpFilter


class ExpFilterARRSES(Filter):
    def __init__(self, alpha=0.5):
        ExpFilter.__init__(self, alpha)
        self.A = 0.0
        self.M = 0.0
        self.F = 0.0
        self.alpha = 0.5
        self.beta = 0.0

    def apply(self, x):        
        self.F = self.alpha * x + (1.0 - self.alpha) * self.F
        
        E = x - self.F
        self.A = self.beta * E + (1.0 - self.beta) * self.A
        self.M = self.beta * abs(E) + (1.0 - self.beta) * self.M
        
        self.alpha = abs(self.A / self.M)
        
        return self.F


class HoltFilter(Filter):
    def __init__(self, alpha=0.5, beta=0.5, k=1):
        self.alpha = alpha
        self.beta = beta  
        self.k = k
        self._inited = 0
        self.S = 0.0
        self.B = 0.0


    def apply(self, x):
        fore = x
        if self._inited <= 1:
            if self._inited == 0:
                self.S = x
                self.B = x
            else: #self._inited == 1:
                self.B = x - self.B
            self._inited += 1
        else:             
            old_S = self.S
            self.S = self.alpha * x + (1-self.alpha) * (self.S + self.B)
            self.B = self.beta * (self.S - old_S) + (1-self.beta) * self.B
            
            fore = self.S + (self.B * self.k)
            
        if fore < 0:
            fore = 0.0
        return fore


MSE = 0
MAE = 1
MAPE = 2
HIB = 3

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


class AdaptableHoltFilter(HoltFilter):
    def __init__(self, alpha=0.5, beta=0.5, k=1, windowSize=10, optMethod=MSE):
        HoltFilter.__init__(self, alpha, beta, k)
        self.buffer = []
        self.windowSize = windowSize
        self.method = optMethod
        self.applyCount = 0
        self.precision = 0.01
    
    
    def optimizePars(self, precision=0.01, method=MSE):    
        alpha = 1.0
        result = (1.0, 1.0, float('inf'))
        while alpha >= 0.0:
            beta = 1.0
            while beta >= 0.0:
                holt = HoltFilter(alpha=alpha,beta=beta,k=1)
                SE = 0.0
                for i in range(len(self.buffer)-1):
                    prediction = max(holt.apply(self.buffer[i]), self.buffer[i])                
                    SE += error(prediction, self.buffer[i+1], method)                       
                
                if SE < result[2]:
                    result = (alpha, beta, SE)
                
                beta -= precision
                beta = round(beta,5)
            alpha -= precision
            alpha = round(alpha,5)    
        return result
    
    
    def apply(self, x):
        self.buffer.append(x)
        if len(self.buffer) > self.windowSize:
            self.buffer.pop(0)
        
        result = HoltFilter.apply(self, x)
        
        self.applyCount += 1
        
        if self.applyCount % self.windowSize == 0:
            pars = self.optimizePars(self.precision, self.method)
            self.alpha = pars[0]
            self.beta = pars[1]
            
        return result


class KalmanFilter(Filter):
    '''
    Code based on: http://www.scipy.org/Cookbook/KalmanFiltering
    '''
    
    def __init__(self, *args, **kwds):
        super(KalmanFilter, self).__init__(*args, **kwds)        
        self.Pminus = 0.0
        self.xhat = 0.0
        self.xhatminus = 0.0
        self.K = None
        self.P = 1.0
        self.Q = 1e-5 #process noise covariance
        self.R = 0.1**2 #measurement noise covariance
        self.pred = HoltFilter(alpha=0.9,beta=0.4)
        self.alpha = 0.8

    def apply(self, z):
        # time update
        self.xhatminus = self.xhat
        #self.xhatminus = self.pred.apply(self.xhat)
        self.Pminus = self.P + self.Q
    
        # measurement update
        self.K = self.Pminus /(self.Pminus + self.R)
        #self.xhat = self.xhatminus + self.K * (z - self.xhatminus)
        self.xhat = self.xhatminus + self.K * (z - self.xhatminus)
        if self.xhat < 0: self.xhat = 0
        self.P = (1.0 - self.K) * self.Pminus
        return self.xhatminus
          
    
    def __repr__(self):
        return 'K = %f, P = %f' % (self.K,self.P)


class Bote(Filter):
    def __init__(self):        
        self.S = None

    def apply(self, x):
        if not self.S:
            self.S = x
            return x
        
        #self.S = x + (x - self.S)
        result = 2 * x - self.S
        self.S = x
        return result
    

class ExpAvgBuilder(Builder):
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = ExpAvg
        Builder.__init__(self, targetClass)
        self.sectionName = 'Predictor'
        #option strings
        self.ALPHA = 'alpha'
        
        
    def readOptions(self, obj, cr):
        obj.alpha = cr.getValue(self.sectionName, self.ALPHA, float)


class HoltBuilder(ExpAvgBuilder):
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = HoltFilter
        ExpAvgBuilder.__init__(self, targetClass)        
        #option strings        
        self.BETA = 'beta'
        
        
    def readOptions(self, obj, cr):
        ExpAvgBuilder.readOptions(self, obj, cr)
        obj.beta = cr.getValue(self.sectionName, self.BETA, float)
    

class AdaptableHoltBuilder(HoltBuilder):
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = AdaptableHoltFilter
        HoltBuilder.__init__(self, targetClass)        
        #option strings
        self.WINDOW_SIZE = 'windowSize'
        
        
    def readOptions(self, obj, cr):
        HoltBuilder.readOptions(self, obj, cr)
        obj.windowSize = cr.getValue(self.sectionName, self.WINDOW_SIZE, int)
    

class DummyFilterBuilder(Builder):
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = DummyFilter
        Builder.__init__(self, targetClass)
        self.sectionName = 'Predictor'        
    

class KalmanFilterBuilder(Builder):
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = KalmanFilter
        Builder.__init__(self, targetClass)
        self.sectionName = 'Predictor'        
        
        
    def readOptions(self, obj, cr):
        obj.Q = cr.getValue(self.sectionName,'Q', float)
        obj.R = cr.getValue(self.sectionName,'R', float)


if __name__ == '__main__':
    import timeit
    iteractions = 1000
    
    print 'AdaptableHolt Benchmark'
    method1 = """
    import random
    from __main__ import HoltFilter, error
    
    step = 20   
    data = [i for i in range(2400)]
    alpha, beta = 1.0, 1.0
    result = (1.0, 1.0, float('inf'))
    
    while alpha > 0.0:
        beta = 1.0
        while beta > 0.0:            
            filter = HoltFilter(alpha=alpha,beta=beta)
            SE = 0.0
            for i in range(len(data) - 1):
                prediction = max(filter.apply(data[i]), data[i])                
                SE += error(prediction, data[i+1])                       
            
            if SE < result[2]:
                result = (alpha, beta, SE)
            
            beta -= step
        alpha -= step
    """
    t = timeit.Timer(stmt=method1)
    print "method 1: %.2f usec/pass" % (1000000 * t.timeit(number=iteractions)/iteractions)
    
    method2 = """
    import random
    from __main__ import HoltFilter, error
    
    step = 20   
    data = [i for i in range(2400)]
    alpha, beta = 1.0, 1.0
    result = (1.0, 1.0, float('inf'))
    
    while alpha > 0.0:
        beta = 1.0
        while beta > 0.0:            
            filter = HoltFilter(alpha=alpha,beta=beta)
            SE = 0.0
            for i in range(len(data) - 1):
                prediction = max(filter.apply(data[i]), data[i])                
                SE += error(prediction, data[i+1])                       
                if SE > result[2]:
                    break
                
            if SE < result[2]:
                result = (alpha, beta, SE)
            
            beta -= step
        alpha -= step
    """
    t = timeit.Timer(stmt=method2)
    print "method 2: %.2f usec/pass" % (1000000 * t.timeit(number=iteractions)/iteractions)
    