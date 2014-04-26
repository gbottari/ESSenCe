'''
Created on Oct 30, 2010

@author: Giulio
'''

from sysThread import Thread
from time import sleep
from service import RequestBuffer
from system.Builder import Builder
try:
    import fcntl
except ImportError:
    fnctl = None
import os


class RequestMonitor(Thread):
    '''
    classdocs
    '''

    DEADLINE = 120 * 1000 #us = 10^(-6) seconds

    def __init__(self, services):
        '''
        Constructor
        '''
        Thread.__init__(self)
        self.services = services # must be a list of RequestBuffer     
        self.loopPeriod = 1      # in seconds
        '''
        If this variable is set, this class will try to fetch information
        using the apache proxy. If not, will use the log file instead.
        '''
        self.apache = None


    def parse(self, lines):
        """
        Parses a list of strings from Apache's access_log into useful statistics.
        """    
        replied = len(lines)
        avg_delay, lost = 0, 0
        qos = 1.0
        
        if replied != 0:
            for line in lines:
                line.strip() #remove leading and trailing spaces
                """
                Each line has the following fields:
                [status code] [reply time (seconds since epoch)] [source IP] [source url] [source query] [serving delay]
                
                e.g.:
                200 1296756182 192.168.10.2 /home.php ?N=192 11045
                200 1296756183 192.168.10.2 /home.php ?N=192 230036
                200 1296756183 192.168.10.2 /home.php ?N=192 230684
                """
                tokens = line.split()
                
                try:
                    if len(tokens) == 6: #expected lenght
                        status, time, sourceIP, url, query, delay = tokens
                    else:
                        """
                        Sometimes, data is written on the log as follows:
                        
                        200 1297213450 ::1 *  76
                        200 1297213458 ::1 *  126
                        """
                        status = tokens[0]
                        time = tokens[1]
                        delay = tokens[4]
                except:
                    self._logger.exception('Problem parsing data on line. Line contents: %s' % line)
                    status = '200'
                    time = '0'
                    delay = '0'
                                
                time = int(time)
                delay = int(delay) / 1000.0
                
                if delay > self.DEADLINE:
                    lost += 1
                avg_delay += delay
            
            avg_delay /= replied
            qos = float(replied - lost) / replied
            
        result = [0.0] * RequestBuffer.VARIABLES_COUNT
        result[RequestBuffer.QOS] = qos
        result[RequestBuffer.LOST] = lost / self.loopPeriod
        result[RequestBuffer.REPLIED] = replied / self.loopPeriod
        result[RequestBuffer.INCOMING] = result[RequestBuffer.REPLIED]
        result[RequestBuffer.DELAY] = avg_delay
        
        return result
    
    
    def run(self):
        '''
        Will periodically parse the access_log for performance counters.
        '''
        access_log = None
        if not self.apache:
            access_log = open('/usr/local2/apache2/logs/access_log','r') #TODO: hard-coded apache location
            
            # make access_log a non-blocking file
            fd = access_log.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        
        try:            
            while not self._stop:
                '''
                - WARNING -
                Since the implementation supports only one service, we don't need to
                match the URL with the service...
                - WARNING -
                '''                
                data = [0.0] * RequestBuffer.VARIABLES_COUNT
                               
                if self.apache:
                    '''
                    - WARNING -
                    On this mode there's no way to collect QOS and LOST (problem with the apache module).
                    Also, there's no way to differentiate requests (it's hard-coded)
                    - WARNING -
                    '''                    
                    data[RequestBuffer.REPLIED] = self.apache.get_load()[0]
                    data[RequestBuffer.DELAY] = self.apache.get_delay()[0]
                    data[RequestBuffer.INCOMING] = self.apache.get_arrival()[0]
                else:
                    '''
                    - WARNING -
                    On this mode there's no way to collect INCOMING (the log doesn't give this info).
                    Here we may differentiate requests, but it's not implemented currently.
                    - WARNING -
                    '''
                    buffer = [] #keeps the lines read at this iteration
                    while True:                
                        line = None
                        try:
                            line = access_log.readline()
                        except: # an exception may be raised if the stdin isn't ready
                            pass # swallow that exception             
                        if line is None or len(line) == 0: # means that we must have reached the end of the file
                            break
                        buffer.append(line)                        
                    data = self.parse(buffer)
                                
                self.services[0].updateBuffer(data)
                sleep(self.loopPeriod)
                
        except:
            self._logger.exception('%s has failed!' % type(self).__name__)
            raise
        finally:
            if not self.apache: # using the apache log, so we need to close it
                access_log.close()
            self._logger.warning('%s has stopped' % type(self).__name__)


from service import RequestBufferBuilder

class RequestMonitorBuilder(Builder):
    
    def __init__(self):
        Builder.__init__(self, RequestMonitor)
        #option strings
        self.LOOP_PERIOD = 'loopperiod'
        self.SERVICES = 'buffers'
        
    
    def build(self, cr, cluster):
        services = []
        
        obj = self.targetClass(services)        
        
        obj.loopPeriod = cr.getValue(self.sectionName, self.LOOP_PERIOD, int)
        sl = cr.getValue(self.sectionName, self.SERVICES, eval)
        for serviceName in sl:
            service = RequestBufferBuilder().build(cr, serviceName)
            services.append(service)        
        
        return obj