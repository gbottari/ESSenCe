#@PydevCodeAnalysisIgnore
'''
Created on Sep 23, 2010

@author: giulio
'''
import unittest

import sys, os
sys.path.append(os.path.abspath('..'))

from system.energyModel import EnergyModel
from system.server import Server


class EnergyModelTest(unittest.TestCase):
    def setUp(self):
        ampere = Server()
        ampere._hostname = 'ampere'
        ampere.processor.availableFreqs = [1.0,1.8,2.0]
        ampere.energyModel = EnergyModel(ampere)
        ampere.energyModel._idlePower = [66.3,70.5,72.7]
        ampere.energyModel._busyPower = [81.5,101.8,109.8]
        ampere.energyModel._peakPerformance = [99.8,179.6,199.6]
        self.server1 = ampere
    
        
    def test_getFreq(self):
        oracle = self.server1.processor.availableFreqs[0]
        output = self.server1.energyModel.getFreq(0.0)
        self.assertEquals(oracle,output)
    
    def test_getPower(self):
        output = []
        oracle = []        
        
        #tests known values
        for i in range(len(self.server1.energyModel._busyPower)):
            output.append(self.server1.energyModel.getPower(self.server1.energyModel._peakPerformance[i]))
            oracle.append(self.server1.energyModel._busyPower[i])

        #tests intermediate perf values
        for i in range(1,len(self.server1.energyModel._busyPower)):
            perf = float(self.server1.energyModel._peakPerformance[i-1] + self.server1.energyModel._peakPerformance[i]) / 2
            output.append(self.server1.energyModel.getPower(perf))
            power = float(self.server1.energyModel._busyPower[i-1] + self.server1.energyModel._busyPower[i]) / 2
            oracle.append(power)

        #tests below peakPerformance values
        output.append(self.server1.energyModel.getPower(0))
        oracle.append(self.server1.energyModel._idlePower[0])
        output.append(self.server1.energyModel.getPower( float(self.server1.energyModel._peakPerformance[0]) / 2) )
        oracle.append(float(self.server1.energyModel._idlePower[0] + self.server1.energyModel._busyPower[0]) / 2)
        
        for out,ora in zip(output,oracle):
            self.assertAlmostEquals(out,ora)
        
            
    def test_getPowerInFreq(self):        
        #test busy utilization:
        output = []
        oracle = []
        i = 0
        for freq in self.server1.processor.availableFreqs:
            power = self.server1.energyModel.getPowerInFreq(freq, 1.0)
            output.append(power)
            oracle.append(self.server1.energyModel._busyPower[i])
            i += 1
        self.assertEquals(output,oracle)

        #test idle utilization:
        output = []
        oracle = []
        i = 0
        for freq in self.server1.processor.availableFreqs:
            power = self.server1.energyModel.getPowerInFreq(freq, 0.0)
            output.append(power)
            oracle.append(self.server1.energyModel._idlePower[i])
            i += 1
        self.assertEquals(output,oracle)
        
        #test 50% utilization:
        output = []
        oracle = []
        i = 0
        for freq in self.server1.processor.availableFreqs:
            power = self.server1.energyModel.getPowerInFreq(freq, 0.5)
            output.append(power)
            oracle.append((self.server1.energyModel._idlePower[i] + self.server1.energyModel._busyPower[i]) / 2)
            i += 1
        self.assertEquals(output,oracle)
        
        freqs = self.server1.processor.availableFreqs
        
        #test intermediate freqs (idle):        
        for i in range(len(freqs)-1):
            output = self.server1.energyModel.getPowerInFreq((freqs[i] + freqs[i+1]) / 2, 0.0)
            oracle = (self.server1.energyModel._idlePower[i] + self.server1.energyModel._idlePower[i+1]) / 2
            self.assertAlmostEquals(output,oracle)
        
        #test intermediate freqs (busy):
        for i in range(len(freqs)-1):
            output = self.server1.energyModel.getPowerInFreq((freqs[i] + freqs[i+1]) / 2, 1.0)
            oracle = (self.server1.energyModel._busyPower[i] + self.server1.energyModel._busyPower[i+1]) / 2
            self.assertAlmostEquals(output,oracle)
            
        #test intermediate freqs (50%):
        for i in range(len(freqs)-1):
            output = self.server1.energyModel.getPowerInFreq((freqs[i] + freqs[i+1]) / 2, 0.5)
            oracle = (self.server1.energyModel._busyPower[i] + self.server1.energyModel._busyPower[i+1]) / 2
            oracle = (oracle + (self.server1.energyModel._idlePower[i] + self.server1.energyModel._idlePower[i+1]) / 2) / 2
            self.assertAlmostEquals(output,oracle)
    
        #print 'idle at 1.0 Ghz: %s' % ampere.energyModel.getPowerInFreq(freqs[0], 0.0)
        #print 'idle at 2.0 Ghz: %s' % ampere.energyModel.getPowerInFreq(freqs[-1], 0.0)
    

if __name__ == "__main__":
    unittest.main()