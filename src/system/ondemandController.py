'''
Created on Sep 22, 2010

@author: giulio
'''

from DVFSController import DVFSController
#from DVSDaemonChannel import DVSDaemonChannel
from network.DVS_DaemonProxy import DVS_DaemonProxy

class OndemandController(DVFSController):
    '''
    classdocs
    '''
    
    GOVERNOR_FILENAME = '/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'
    POWERSAVE_BIAS_FILENAME = '/sys/devices/system/cpu/cpu*/cpufreq/ondemand/powersave_bias'
    UP_THRESHOLD_FILENAME = '/sys/devices/system/cpu/cpu*/cpufreq/ondemand/up_threshold'

    def __init__(self, server):
        '''
        Constructor
        '''
        DVFSController.__init__(self, server)
        self._powersave_bias = 0
        self._up_threshold = 80
        self._proxy = DVS_DaemonProxy(server.ip, 27000)   
    
            
    def setPowersaveBias(self, powersave_bias):
        assert 0 <= powersave_bias <= 1000
        
        self._powersave_bias = powersave_bias
        self._proxy.shell(["for f in %s; do echo %d > $f; done" % (self.POWERSAVE_BIAS_FILENAME, powersave_bias)])
            
        
    def setUpThreshold(self, up_threshold):
        assert 0 <= up_threshold <= 100
        
        self._up_threshold = up_threshold
        self._proxy.shell(["for f in %s; do echo %d > $f; done" % (self.UP_THRESHOLD_FILENAME, up_threshold)])        
        
    
    def setOndemandGovernor(self):
        self._proxy.shell(["for f in %s; do echo %s > $f; done" % (self.GOVERNOR_FILENAME, 'ondemand')])
        
    
    def setup(self):      
        self.setOndemandGovernor()
        self.setPowersaveBias(0)
    
    
    def setFreqCap(self, freqCap):
        #assumption: cores with same freqs
        hi_freq = self._server.processor.availableFreqs[-1]
        
        powersave_bias = int((1.0 - float(freqCap) / hi_freq) * 1000)
        
        if powersave_bias > 1000: powersave_bias = 1000
        elif powersave_bias < 0: powersave_bias = 0
        
        self.setPowersaveBias(powersave_bias)
        
        DVFSController.setFreqCap(self, freqCap) #call super