'''
Created on Oct 13, 2010

@author: Giulio
'''
import unittest

import sys, os
sys.path.append(os.path.abspath('..'))

from system.service import RequestBuffer

LINEAR_TRACE = '../tmp/linearTrace.txt' 

class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.buffSize = 5
        self.service = RequestBuffer()
        self.service.setBufferSize(self.buffSize)        

    def testZeroBufferSize(self):
        self.service.setBufferSize(0)
        self.service.updateBuffer([0.0] * self.service.VARIABLES_COUNT)
    
    def testSetBufferSize(self):        
        self.assertEquals(len(self.service._buffer),self.buffSize)

    def testUpdateBuffer(self):
        #no overlay:
        oracle = []
        size = self.buffSize
        for i in range(size):
            data = [float(i)] * self.service.VARIABLES_COUNT
            oracle.append(data)
            self.service.updateBuffer(data)
        self.assertEquals(oracle,self.service._buffer)
        
        #overlay:
        oracle = []
        size = self.buffSize + 2
        for i in range(size):
            data = [float(i)] * self.service.VARIABLES_COUNT
            oracle.append(data)
            self.service.updateBuffer(data)
        self.assertEquals(oracle[2:],self.service._buffer)

    def testNotEnoughItems(self):
        #no overlay:
        oracle = float(1 + 2 + 3) / 3
        for i in [1, 2, 3]:
            data = [float(i)] * self.service.VARIABLES_COUNT            
            self.service.updateBuffer(data)
        output = self.service.getInfo(10)
        self.assertEquals(oracle,output[0])
if __name__ == "__main__":
    unittest.main()