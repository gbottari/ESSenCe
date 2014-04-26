'''
Created on Oct 13, 2010

@author: Giulio
'''

import sys, os
from system.server import ServerBuilder as SysServerBuilder
sys.path.append(os.path.abspath('..'))

from system.server import Server as SysServer

class Server(SysServer):
    
    POOLING_TIME = 0
    WAKE_UP_TIME = 6
    SUSPEND_TIME = 2

    def __init__(self):
        SysServer.__init__(self)
        self.sleep = lambda time: None
        
    def _getHostname(self):
        return 'SimServer'   
    
    def _heartBeat(self):
        return (self._status in [Server.ON, Server.TURNING_OFF])
    
    def _wakeup(self):
        self.sleep(self.WAKE_UP_TIME)
        self._status = Server.ON
        
    def _suspend(self):
        self.sleep(self.SUSPEND_TIME)
        self._status = Server.OFF
    
    def updateSensors(self):
        pass
    
    def _startApacheServer(self):
        pass
    
    def _setup(self):
        if not self._performedSetup:
            self.dvfsCont.setup() #reset the controller                
            self.dvfsCont.setFreqCap(self.processor.availableFreqs[-1]) #no freqCap
            self.processor.freq = self.processor.availableFreqs[-1]
            self._performedSetup = True


class ServerBuilder(SysServerBuilder):
    
    def __init__(self, sectionName, targetClass=None):
        if not targetClass: targetClass = Server                
        SysServerBuilder.__init__(self, sectionName, targetClass)
    
    
    def readOptions(self, obj, cr):
        '''
        Comparing to SysServer, some attributes aren't really necessary
        '''
        obj.hostname = cr.getValue(self.sectionName, self.HOSTNAME, str, required=False)        
        obj.processor.availableFreqs = cr.getValue(self.sectionName, self.FREQS, eval, required=False)