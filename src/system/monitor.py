'''
Created on Nov 13, 2010

@author: Giulio
'''

from sysThread import Thread
from time import sleep
from service import RequestBuffer
from threading import Lock
from server import Server
from system.energyModel import getPerformance


class MonitorVariable(object):
    def __init__(self, header=None, format=None, func=None):
        self.header = header # header name
        self.format = format # string format for the monitor file
        self.func = func     # function to call when reading the variable
        self.value = 0.0     # last read value
        
    def update(self): #calls func to update value
        if self.func:
            self.value = self.func()
            

class SystemMonitor(Thread):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        Thread.__init__(self)
        self.HEADER_FORMAT = '%02d-'
        
        self.loopPeriod = 1
        self.time = MonitorVariable(header='%sTime' % self.HEADER_FORMAT, format="%5d", func=None)
        self.time.value = 0
        self.power = MonitorVariable(header='%sPower' % self.HEADER_FORMAT, format="%5.1f", func=None)
        self.varPool = [self.time, self.power]
        
        #temporary hard-coded variables:
        self.lost = MonitorVariable(header='%sLost' % self.HEADER_FORMAT, format="%6.1f", func=None)
        self.replied = MonitorVariable(header='%sReplied' % self.HEADER_FORMAT, format="%6.1f", func=None)
        self.incoming = MonitorVariable(header='%sIncoming' % self.HEADER_FORMAT, format="%6.1f", func=None)
        self.qos = MonitorVariable(header='%sQoS' % self.HEADER_FORMAT, format="%6.4f", func=None)
        self.predicted = MonitorVariable(header='%sPredicted' % self.HEADER_FORMAT, format="%5.1f", func=None)
        self.mse = MonitorVariable(header='%sMSE' % self.HEADER_FORMAT, format="%11.1f", func=None)        
        self.delay = MonitorVariable(header='%sDelay' % self.HEADER_FORMAT, format="%7.3f", func=None)
        self.gamma = MonitorVariable(header='%sGamma' % self.HEADER_FORMAT, format="%3.3f", func=None)
        self.saturation = MonitorVariable(header='%sSaturation' % self.HEADER_FORMAT, format="%3.3f", func=None)
        self.dyn_power = MonitorVariable(header='%sDynPower' % self.HEADER_FORMAT, format="%5.1f", func=None)
        
        self.varPool.append(self.lost)
        self.varPool.append(self.replied)
        self.varPool.append(self.incoming)
        self.varPool.append(self.qos)
        self.varPool.append(self.predicted)
        self.varPool.append(self.mse)
        self.varPool.append(self.delay)
        self.varPool.append(self.gamma)
        self.varPool.append(self.saturation)
        self.varPool.append(self.dyn_power)
        
        self.HEADER_PERIOD = 40 # period to repeat the header on the monitor file 
        
        self._monFile = None   
        self._mutex = Lock()
        self.emulatePower = True
        self.experiment = None
    
    
    def addVariable(self, header, format, func):
        assert isinstance(func, callable)
        var = MonitorVariable(header,format,func)
        self.varPool.append(var)
        
    
    def _buildHeader(self):
        result = '#' #makes the header line ignored on gnuplot 
        counter = 1
        for var in self.varPool:            
            #result += item['header'] % (counter) + ' '
            result += var.header % (counter) + ' '
            counter += 1
        
        for server in self.experiment._cluster:
            result += self.HEADER_FORMAT % counter + server.hostname + ' '
            counter += 3 # util, freq and freqCap 
        
        result.strip() #remove trailing space
        
        return result


    def openMonitorFile(self, filename):
        '''
        Opens the monitor file and write the header on it
        '''
        self._monFile = open(filename,'w')
        self._header = self._buildHeader()
        self._monFile.write(self._header + '\n')
        
    
    def closeMonitorFile(self):
        if self._monFile is not None:
            self._monFile.close()
    
    
    def record(self):
        '''
        Record one line of data to the monitor's file
        
        WARNING: the information of the servers could be updated at the same time as
        the execution here is taking place.
        '''         
                
        if self.experiment._configurator:
            self.predicted.value = self.experiment._configurator.predicted
        
        info = self.experiment._serviceMonitor.services[0].getInfo(self.loopPeriod)
        
        self.qos.value = info[RequestBuffer.QOS]
        self.replied.value = info[RequestBuffer.REPLIED]
        self.lost.value = info[RequestBuffer.LOST]
        self.incoming.value = info[RequestBuffer.INCOMING]
        self.delay.value = info[RequestBuffer.DELAY]        
        
        self.power.value = self.experiment._powerMonitor.getPower()
        '''
        Calculate Dynamic Power
        '''
        staticPower = 0.0
        for server in self.experiment._cluster:
            if server.status != Server.OFF:
                staticPower += server.energyModel.idlePower[0]
        self.dyn_power.value = self.power.value - staticPower    
                 
        self.mse.value = (self.incoming.value - self.predicted.value) ** 2
        if self.experiment._configurator:
            self.gamma.value = self.experiment._configurator.gamma
        self.time.value += self.loopPeriod
        
        for var in self.varPool:
            var.update()
            
        self.saturation.value = self.incoming.value / getPerformance(self.experiment._cluster.servers[Server.ON])
        
        line = ''
        if self.time.value % self.HEADER_PERIOD == 0:
            line = self._header + '\n'
               
        for var in self.varPool:            
            line += ' ' + var.format % var.value 
             
        for server in self.experiment._cluster:
            freq = server.processor.freq
            util = server.processor.utilization
            freqCap = server.dvfsCont.getFreqCap()

            if server.status == Server.OFF:
                freq = 0.0
                freqCap = 0.0
                util = 0.0
            
            line += '  %5.4f %5.4f %05.1f' % (freq / 1000000.0, freqCap / 1000000.0, util * 100)
        self._monFile.write(line + '\n')       
        
        
    def run(self):
        try:
            while not self._stop:
                self._mutex.acquire()
                self.record()
                self._mutex.release()
                sleep(self.loopPeriod)
        finally:
            self.closeMonitorFile()