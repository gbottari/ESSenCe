'''
Created on May 31, 2011

@author: Giulio
'''

from time import sleep
from powerMonitor import PowerMonitor
#from SocketChannel import SocketChannel, TCP_MODE
from network.SocketProxy import SocketProxy, TCP_MODE
from system.powerMonitor import PowerMonitorBuilder


class LabView(PowerMonitor):
    
    def __init__(self, ip, port):
        PowerMonitor.__init__(self)
        self._proxy = SocketProxy(ip, port, TCP_MODE)
        
        
    def run(self):
        try:
            while not self._stop:
                try:
                    msg = self._proxy.receive()
                    #msg = msg.replace(',','.')
                    self._mutex.acquire()
                    try:
                        self._power = float(msg)
                    except:
                        self._power = float(msg[:8]) #power measurements are doubled...
                        #self._logger.debug('Power is doubled!')
                    finally:
                        self._mutex.release()
                except:
                    self._logger.exception('Problem getting power measurement')                    
                sleep(self.loopPeriod)
            self._proxy.close()
        except:
            self._logger.exception('%s has failed!' % type(self).__name__)
            raise
        finally:
            self._logger.warning('%s has stopped' % type(self).__name__)


class LabViewBuilder(PowerMonitorBuilder):
    
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = LabView
        PowerMonitorBuilder.__init__(self, targetClass)
        self.IP = 'ip'
        self.PORT = 'port'
    
            
    def build(self, cr):        
        ip = cr.getValue(self.sectionName, self.IP)
        port = cr.getValue(self.sectionName, self.PORT, int)        
        
        return PowerMonitorBuilder.build(self, cr, ip, port)