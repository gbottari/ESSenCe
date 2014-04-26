'''
Created on May 31, 2011

@author: Giulio
'''

from time import sleep
from powerMonitor import PowerMonitor
from server import Server
from system.powerMonitor import PowerMonitorBuilder

class PowerEmulator(PowerMonitor):
    
    SUSPENDED_POWER = 6 #Watts
    
    
    def __init__(self, cluster):
        PowerMonitor.__init__(self)
        self.sleep = sleep
        self.cluster = cluster
        
        
    def calcPower(self):
        power = self.SUSPENDED_POWER * len(self.cluster.servers[Server.OFF])
        
        notOffServers = self.cluster.servers[Server.ON] + \
            self.cluster.servers[Server.TURNING_OFF] + self.cluster.servers[Server.TURNING_ON]
        
        for server in notOffServers:
            try:
                #self._logger.debug('server %s, freq %f, util %f' % (server, server.processor.freq, server.processor.util))
                power += server.energyModel.getPowerInFreq(server.processor.freq, server.processor.util)
            except:
                self._logger.exception('Problem while calculating power on %s with current freq = %f' %\
                                       (server, server.processor.freq / 1000000.0))
        return power
    
    
    def run(self):
        while not self._stop:
            self.sleep(self.loopPeriod)
            try:                                
                self._mutex.acquire()
                self._power = self.calcPower()                
                self._mutex.release()    
            except:
                self._logger.exception('Problem getting power measurement')


class PowerEmulatorBuilder(PowerMonitorBuilder):
    
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = PowerEmulator
        PowerMonitorBuilder.__init__(self, targetClass)