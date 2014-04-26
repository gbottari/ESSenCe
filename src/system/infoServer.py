'''
Created on Dec 3, 2010

@author: giulio
'''

from sysThread import Thread
from network.SocketProxy import SocketProxy, UDP_MODE
from system.Builder import Builder

class ResourceMonitor(Thread):
    '''
    classdocs
    '''

    RCV_BUFFER_SIZE = 512
    

    def __init__(self, ip, port, cluster):
        '''
        Constructor
        '''
        Thread.__init__(self)
        self.cluster = cluster
        self._proxy = SocketProxy(ip, port, UDP_MODE)
   

    def run(self):
        try:
            while not self._stop:
                data = self._proxy.receive()
                tokens = data.split()
                
                '''
                Message Format:
                0    1        2         3    4                 5
                TYPE HOSTNAME FREQ(MHZ) UTIL RUNNING_PROCESSES OTHER
                '''
                machine_name = tokens[1]
                freq = float(tokens[2]) * 1000.0 #converts from Mhz to Hz
                util = float(tokens[3])
                #running_processes = int(tokens[4])
                
                #search for server in cluster
                server = None
                for s in self.cluster.availableServers:
                    if s.hostname == machine_name:
                        server = s
                        break
                
                if server is not None:
                    server.processor.util = util
                    if round(freq, 3) > 0.0:
                        server.processor.freq = freq
                    else:
                        self._logger.debug("Frequency received is invalid: %f" % freq)
                else:
                    self._logger.critical('Could not find server named "%s" on cluster' % machine_name)
        except:
            self._logger.exception('%s has failed!' % type(self).__name__)
            raise
        finally:
            self._proxy.close()
            self._logger.warning('%s has stopped' % type(self).__name__)


class ResourceMonitorBuilder(Builder):
    
    def __init__(self):
        Builder.__init__(self, ResourceMonitor)
        self.PORT = 'port'
        self.HOST = 'host'   
    
    
    def build(self, cr, cluster):
        addr = cr.getValue(self.sectionName, self.HOST)
        port = cr.getValue(self.sectionName, self.PORT, int) 
        
        obj = self.targetClass(addr, port, cluster)
                        
        return obj    