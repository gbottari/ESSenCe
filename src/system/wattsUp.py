'''
Created on Dec 16, 2010

@author: giulio
'''

from time import sleep
from subprocess import PIPE, Popen
from tools import execCmd
from powerMonitor import PowerMonitor
from system.powerMonitor import PowerMonitorBuilder

class WattsUp(PowerMonitor):
    
    def __init__(self):
        PowerMonitor.__init__(self)
        '''
        The current implementation does not use Proxy.
        '''        
        self._proxy = None        


    def run(self):
        p = Popen(['/usr/local/bin/wattsup', 'ttyUSB0', 'watts'], stdout=PIPE)
        while not self._stop:
            try:
                if p.poll() is None:               
                    output = p.stdout.readline().strip()
                    self._mutex.acquire()
                    self._power = float(output)
                    self._mutex.release()                                        
                else:
                    p = Popen(['/usr/local/bin/wattsup', 'ttyUSB0', 'watts'], stdout=PIPE)
            except:
                self._logger.exception('Problem getting power measurement')
            sleep(self.loopPeriod)
        execCmd(['killall','wattsup'],wait=True)
    
    
    def start(self):
        '''
        @todo: implement this
        
        WattsUp hangs at startup. To fix it, we should wait until the first
        measures are made.
        '''
        PowerMonitor.start(self)


class WattsUpBuilder(PowerMonitorBuilder):
    
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = WattsUp
        PowerMonitorBuilder.__init__(self, targetClass)