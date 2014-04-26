'''
Created on May 31, 2011

@author: Giulio
'''

from sysThread import Thread
from threading import Lock
from system.Builder import Builder


class PowerMonitor(Thread):    

    def __init__(self):
        '''
        Constructor
        '''
        Thread.__init__(self)
        self._proxy = None
        self._power = 0.0
        self._mutex = Lock()
        self.loopPeriod = 1
        
        
    def getPower(self):
        self._mutex.acquire()
        result = self._power
        self._mutex.release()
        return result


class PowerMonitorBuilder(Builder):
    
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = PowerMonitor
        Builder.__init__(self, targetClass)
        self.sectionName = PowerMonitor.__name__
        # options:
        self.LOOP_PERIOD = 'loopperiod'
    
    
    def readOptions(self, obj, cr):
        lp = cr.getValue(self.sectionName, self.LOOP_PERIOD, int, required=False)
        if lp:
            obj.loopPeriod = lp