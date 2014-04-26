'''
Created on May 31, 2011

@author: Giulio
'''

from DVFSController import DVFSController
#from SocketChannel import SocketChannel, UDP_MODE
from network.DVS_DaemonProxy import DVS_DaemonProxy

class ContinuousController(DVFSController):
    '''
    classdocs
    '''
    SET_FREQ_CODE = 3
    ARBITRARY_CMD_CODE = 7
    MINIMUM_GRANULARITY = 3000 #Hz
    SCALING_GOVERNOR = '/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'


    def __init__(self, server):
        '''
        Constructor
        '''
        DVFSController.__init__(self, server)        
        self._proxy = DVS_DaemonProxy(server.ip, 27000)
        self._freqs = server.processor.availableFreqs


    def setup(self):        
        self._proxy.shell(["for f in %s; do echo %s > $f; done" % (self.SCALING_GOVERNOR, 'userspace')])

        
    def roundFreq(self, freq):
        '''
        Some freqs can't be emulated because of the transition overhead
        '''
        i = 0
        while (freq > self._freqs[i]):
            i += 1
        
        if i > 0:    
            diff_high = self._freqs[i] - freq                    
            diff_low = freq - self._freqs[i-1]            
            
            if diff_high < self.MINIMUM_GRANULARITY:
                return self._freqs[i]
            
            if diff_low < self.MINIMUM_GRANULARITY:
                return self._freqs[i-1]
            
        return freq
        
    
    def setFreqCap(self, freqCap):        
        self._proxy.setFreq(self.roundFreq(freqCap))
        DVFSController.setFreqCap(self, freqCap)
    
    
if __name__ == '__main__':
    cont = ContinuousController(None)
    cont._freqs = [1000000, 1800000, 2000000, 2200000]
    assert cont.roundFreq(1000000) == 1000000
    assert cont.roundFreq(1200000) == 1200000
    assert cont.roundFreq(1000001) == 1000000
    assert cont.roundFreq(1002999) == 1000000
    assert cont.roundFreq(2002999) == 2000000
    assert cont.roundFreq(2200000) == 2200000
    assert cont.roundFreq(2190000) == 2190000
    assert cont.roundFreq(2199990) == 2200000