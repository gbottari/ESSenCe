'''
Created on Sep 23, 2010

atauthor: giulio
'''
import unittest

import sys, os
from system.perfRegulator import PerfRegulator
sys.path.append(os.path.abspath('..'))

from protoCluster import createServer, createCluster


class PerfRegTest(unittest.TestCase):   
    def setUp(self):
        self.servers = [createServer('ampere'), \
                        createServer('coulomb'), \
                        createServer('joule'), \
                        createServer('hertz'), \
                        createServer('ohm')]
        cluster = createCluster(self.servers)
        self.perfReg = PerfRegulator(cluster)
    
    
    def verifyBalanceOutput(self, oracle, output):
        '''
        Uses the assertAlmostEquals function to compare the value of two lists,
        otherwise it would use assertEquals.
        '''
        for i in range(len(output)):
            for j in range (len(output[i])):
                self.assertAlmostEquals(oracle[i][j],output[i][j].perf)


    def test_balancePerformance_invalid(self):
        self.assertRaises(AssertionError,self.perfReg.balancePerformance,100,None)
        self.assertRaises(AssertionError,self.perfReg.balancePerformance,None,None)
        self.assertRaises(AssertionError,self.perfReg.balancePerformance,None,self.servers)
        self.assertRaises(AssertionError,self.perfReg.balancePerformance,-1,self.servers)
        self.assertRaises(AssertionError,self.perfReg.balancePerformance,-1,None)


    def test_balancePerfomance_1server(self):
        output = []
        oracle = []        
        s0 = self.servers[0]

        # no load
        load = 0.0
        oracle.append([0])        
        output.append(self.perfReg.balancePerformance(load, [s0]))
        
        # maximum load on server
        load = s0.energyModel._peakPerformance[-1] 
        oracle.append([load])
        output.append(self.perfReg.balancePerformance(load, [s0]))
        
        # average load on server
        load = s0.energyModel._peakPerformance[-1] / 2
        oracle.append([load])
        output.append(self.perfReg.balancePerformance(load, [s0]))
        
        # overload on server
        load = s0.energyModel._peakPerformance[-1] * 10
        oracle.append([s0.energyModel._peakPerformance[-1]])
        output.append(self.perfReg.balancePerformance(load, [s0]))
        
        self.verifyBalanceOutput(oracle,output)
    
    
    def test_applyPerf(self):
        s0 = self.servers[0]

        perf = 0.0
        out = self.perfReg.balancePerformance(perf, [s0])
        self.perfReg.applyPerfRegulation(out)
        
    
    def test_balancePerfomance_2servers_homogeneous(self):
        output = []
        oracle = []
        s0 = self.servers[0]
        sl = [s0,s0]
        
        # no load
        perf = 0
        oracle.append([0,0])
        output.append(self.perfReg.balancePerformance(perf, sl))        
        
        # maximum load at freq 0
        perf = 2 * s0.energyModel.peakPerf[0]
        oracle.append([s0.energyModel.peakPerf[0],s0.energyModel.peakPerf[0]])
        output.append(self.perfReg.balancePerformance(perf, sl))
        
        # average load at freq 0
        perf = s0.energyModel.peakPerf[0]
        '''
        The oracle here is any combination of load distribution, since
        servers are homogeneous. Thus, we must verify that the frequency 
        of both servers is not overrated, since the input only occupies 
        one freq at most.
        '''
        out = self.perfReg.balancePerformance(perf, sl)
        self.assertTrue((out[0].perfIndex == 1 and out[1].perfIndex == 0) or \
                        (out[0].perfIndex == 0 and out[1].perfIndex == 1))
        
        self.verifyBalanceOutput(oracle,output)
        
        
    def test_balancePerfomance_2servers_heterogeneous(self):
        output = []
        oracle = []
        s0 = self.servers[0]
        s1 = self.servers[1]
        sl = [s0,s1]
        
        # no load
        perf = 0
        oracle.append([0,0])
        output.append(self.perfReg.balancePerformance(perf, sl))        
        
        # maximum load at freq 0
        perf = s0.energyModel.peakPerf[0] + s1.energyModel.peakPerf[0]
        oracle.append([s0.energyModel.peakPerf[0],s1.energyModel.peakPerf[0]])
        output.append(self.perfReg.balancePerformance(perf, sl))
                
                
        self.verifyBalanceOutput(oracle,output)
        
if __name__ == "__main__":
    unittest.main()