'''
Created on Oct 10, 2010

@author: Giulio
'''
import unittest

import sys, os, random
sys.path.append(os.path.abspath('..'))

from system.filters import HoltFilter, AdaptableHoltFilter

class HoltTests(unittest.TestCase):
    
    def setUp(self):
        self.h = HoltFilter()
        self.testRange = 10
    
    def testInitialization(self):
        """
        Test Holt's initialization routine
        """
        
        self.h.alpha = 1.0
        self.h.beta = 0.0        
        data = 3        
        pred = self.h.apply(data)      
        """
        While not initialized, Holt should output the
        given data
        """
        self.assertAlmostEquals(data, pred)
        
        data += 1
        pred = self.h.apply(data)        
        self.assertAlmostEquals(data, pred)
    
    
    def testLinear(self):
        """
        Test a linear trace
        """
        self.h.alpha = 1.0
        self.h.beta = 0.0
        for i in range(self.testRange):
            pred = self.h.apply(i)
            if i > 1:
                self.assertAlmostEquals(i + 1, pred)


    def testLongForecasting(self):
        """
        Test a linear trace with long forecasting
        """
        self.h.alpha = 1.0
        self.h.beta = 0.0
        self.h.k = 3
        for i in range(self.testRange):            
            pred = self.h.apply(i)
            if i > 1:
                self.assertAlmostEquals(i + self.h.k, pred)


class AdaptableHoltTests(HoltTests):
    """
    Adaptable Holt should work just as regular Holt, 
    but with interval based adaptations.
    """

    def setUp(self):
        HoltTests.setUp(self)
        self.h = AdaptableHoltFilter()        
        self.h.windowSize = self.testRange * 2 # must be greater than Holt's original test range


    def testOptimization(self):
        """
        Will use adaptation on a linear trace.
        Expected output should be alpha = 1.0, and beta = 0.0
        """
        for i in range(self.h.windowSize):
            self.h.apply(i)        
        
        self.assertAlmostEquals(self.h.alpha,1.0)
        self.assertAlmostEquals(self.h.beta,0.0)
        
        
    def testAdaption(self):
        """
        Will test the ability to change Holt's parameters at given intervals
        """
        for i in range(self.h.windowSize):
            self.h.apply(random.random() * 2)        
        pars = (self.h.alpha, self.h.beta)
        
        for i in range(self.h.windowSize):
            self.h.apply(i ** 2 + i * 2 + 5 * random.random())            
        new_pars = (self.h.alpha, self.h.beta)
        
        self.assertNotEquals(pars, new_pars)


if __name__ == "__main__":
    unittest.main()