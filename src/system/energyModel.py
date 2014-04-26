'''
Created on Sep 9, 2010

@author: giulio
'''

from tools import linearInterpolation
from sysObject import Object
import logging
from system.Builder import Builder
from system.shared import SCALING_FACTOR

def getMaxPerformance(serverList):
    result = 0.0
    for server in serverList:
        result += server.energyModel._peakPerformance[-1]
    return result


def getPerformance(servers):
    perf = 0.0
    for server in servers:
        perf += server.energyModel.getPerf(server.dvfsCont.getFreqCap())
    return perf


class EnergyModel(Object):
    '''
    Represents a Server energy model
    '''


    def __init__(self, server):
        '''
        Constructor
        '''
        self._idlePower = None
        self._busyPower = None
        self._peakPerformance = None
        self.server = server
        self._logger = logging.getLogger(type(self).__name__)


    def getPowerInFreq(self, freq, utilization):
        try:
            assert 0.0 <= round(utilization,8) <= 1.0
        except AssertionError:
            self._logger.exception('Invalid utilization: %f' % utilization)
            raise
        
        freqs = self.server.processor.availableFreqs
        assert freqs[0] <= freq <= freqs[-1]
        
        #find the surronding freqs
        index = 0
        while freq > freqs[index]:
            index += 1
        
        upperFreq = None
        lowerFreq = None
        lowerFreq_idlePower = None
        upperFreq_idlePower = None
        lowerFreq_busyPower = None
        upperFreq_busyPower = None
        if index == 0:
            lowerFreq = upperFreq = freqs[0]
            lowerFreq_idlePower = upperFreq_idlePower = self._idlePower[0]
            lowerFreq_busyPower = upperFreq_busyPower = self._busyPower[0]
        else:
            lowerFreq = freqs[index - 1]
            lowerFreq_idlePower = self._idlePower[index - 1]
            lowerFreq_busyPower = self._busyPower[index - 1]
            upperFreq = freqs[index]
            upperFreq_idlePower = self._idlePower[index]
            upperFreq_busyPower = self._busyPower[index]
                          
        idlePower = linearInterpolation([lowerFreq, upperFreq], \
                                        [lowerFreq_idlePower, upperFreq_idlePower], freq)
        
        busyPower = linearInterpolation([lowerFreq, upperFreq], \
                                        [lowerFreq_busyPower, upperFreq_busyPower], freq)
        
        return idlePower + (busyPower - idlePower) * utilization
    

    def getPower(self, perf):
        '''
        Returns the power spent to achieve a certain amount of performance, at the minimum frequency
        possible that will set the processor at ~95% CPU utilization.
        If not enough performance is required to keep the processor busy, a linear relation is
        assumed between idle and busy power.
        '''
        
        if perf <= self._peakPerformance[0]:
            return float(perf) / self._peakPerformance[0] * (self._busyPower[0] - self._idlePower[0]) + self._idlePower[0]
        
        return linearInterpolation(self._peakPerformance, self._busyPower, perf)


    def getPerf(self, freq):
        '''
        Returns the peakPerformance for the given frequency. Analogous to getPower().
        '''
        return linearInterpolation(self.server.processor.availableFreqs, self._peakPerformance, freq)


    def getFreq(self, perf):
        if perf >= self._peakPerformance[-1]:
            return  self.server.processor.availableFreqs[-1]
        return linearInterpolation(self._peakPerformance, self.server.processor.availableFreqs, perf)


    def assignSamples(self, busy, idle, peakPerf):
        assert len(busy) == len(idle) == len(peakPerf)        
        self._idlePower = idle
        self._busyPower = busy
        self._peakPerformance = peakPerf


    @property
    def peakPerf(self):
        return self._peakPerformance
    
    @property
    def busyPower(self):
        return self._busyPower
    
    @property
    def idlePower(self):
        return self._idlePower


class EnergyModelBuilder(Builder):
    
    def __init__(self, sectionName, targetClass=None):
        if not targetClass: targetClass = EnergyModel
        Builder.__init__(self, targetClass)
        self.sectionName = sectionName
        #option strings
        self.BUSY_POWER = 'busypower'
        self.IDLE_POWER = 'idlepower'
        self.PEAK_PERFORMANCE = 'peakperformance'
            
    
    def readOptions(self, obj, cr):
        busy = cr.getValue(self.sectionName, self.BUSY_POWER, eval, required=True)
        idle = cr.getValue(self.sectionName, self.IDLE_POWER, eval, required=True)
        peak = cr.getValue(self.sectionName, self.PEAK_PERFORMANCE, eval, required=True)
        
        peak = [perf * SCALING_FACTOR for perf in peak]
        
        obj.assignSamples(busy, idle, peak)
    '''
    def build(self, cr, server):
        return Builder.build(self, cr, server)
    '''