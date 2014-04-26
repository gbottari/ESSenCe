'''
Created on Nov 12, 2010

@author: giulio
'''

import sys, os
from system.experiment import ExperimentBuilder as SysExperimentBuilder
sys.path.append(os.path.abspath('..'))
from system.experiment import Experiment as SysExperiment
from system.server import Server
from system.service import RequestBuffer
from system.shared import MONITOR_NAME
from scripts.traceScaler import scale
from scripts.stats import file2data
from system.clock import Clock


class Experiment(SysExperiment):
    '''
    Simulated experiments
    '''
        
    MAX_CLUSTER_UTILIZATION = 1250.0/1357.3
    

    def __init__(self):
        '''
        Constructor
        '''
        SysExperiment.__init__(self)
        self._traceFilename = None
        self._clock = Clock()
    
    
    def startExperiment(self):
        '''
        The experiment is simulated through a trace file which contains the incoming requests.
        
        The following variables are emulated: qos, enqueued, replied and lost.
        '''
        assert self._status == Experiment.NOT_RUNNING
        self._status = Experiment.RUNNING

        self.resetLog() #clear log
                
        try:
            self._cluster.turnOnAll() #all machines starts ON
        except:
            self._logger.critical('Turning Servers ON error!')
            raise
        
        self._monitor.openMonitorFile(MONITOR_NAME)        
        
        enqueued = 0.0
        qos = 1.0
        
        data = file2data(1, self._traceFilename)[0]
        scale(data, self._cluster.availableServers, maxUtil=self.MAX_CLUSTER_UTILIZATION)

        #substitution of sleep functions
        for server in self._cluster:
            server.sleep = self._clock.sleep
        self._cluster.sleep = self._clock.sleep
        self._powerMonitor.sleep = self._clock.sleep
                
        tracking_threads = [self._powerMonitor]
        
        if self._perfRegulator:
            self._perfRegulator.sleep = self._clock.sleep
            tracking_threads.append(self._perfRegulator)
            self._perfRegulator.start()           
        
        if self._configurator:
            self._configurator.sleep = self._clock.sleep
            tracking_threads.append(self._configurator)
            self._configurator.start()             
        
        self._powerMonitor.start()
        
        for incoming in data:            
            replied = self._loadBalancer.getTotalPerf(incoming + enqueued)
            replied = round(replied,10)

            lost = min(enqueued, replied)
            lost = round(lost,10)
            enqueued += incoming - replied
            if enqueued < 0.0: #overprovisioning
                enqueued = 0.0
            
            if replied > 0.0:
                qos = (replied - lost) / replied
            
            info = [0.0] * RequestBuffer.VARIABLES_COUNT
            info[RequestBuffer.INCOMING] = incoming
            info[RequestBuffer.REPLIED] = replied
            info[RequestBuffer.LOST] = lost
            info[RequestBuffer.QOS] = qos
            
            #calculate Utilization
            for server, weight in self._loadBalancer.getWeights():                    
                if server.status in [Server.ON, Server.TURNING_OFF]:
                    freqCap = server.dvfsCont.getFreqCap()
                    perf = weight * replied
                    server.processor.util = perf / server.energyModel.getPerf(freqCap)
                    if server.processor.util > 1.0:
                        server.processor.util = 1.0
                else:
                    server.processor.util = 0.0
                        
            #make freq = freqCap
            for server in self._cluster:
                server.processor.freq = server.dvfsCont.getFreqCap()
            self._serviceMonitor.services[0].updateBuffer(info)
            
            
            self._monitor.record()        
            self._clock.tick() #release threads and advance time            
            #self._clock.sync(tracking_threads) #block until the threads are done
            
        self.stopExperiment()


    def stopExperiment(self):
        if self._status == self.RUNNING:        
            self._monitor.closeMonitorFile()
            if self._configurator:
                self._configurator.stop()
            if self._perfRegulator:
                self._perfRegulator.stop()
            self._powerMonitor.stop()
            self._clock.bypass()
            
            self._status = self.SUCCESS
        else:
            self._logger.warning('Experiment already stopped!')

    @property
    def traceFilename(self):
        return self._traceFilename
    
    @traceFilename.setter
    def traceFilename(self, name):
        self._traceFilename = name
        

class ExperimentBuilder(SysExperimentBuilder):
    
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = Experiment
        SysExperimentBuilder.__init__(self, targetClass)
    
    
    def readWorkGen(self, obj, cr):
        pass
    
    
    def readResourceMonitor(self, obj, cr):
        pass
    
    
    def readApache(self, obj, cr):
        pass
    
        
    def readOptions(self, obj, cr):
        SysExperimentBuilder.readOptions(self, obj, cr)        
        obj.traceFilename = cr.getValue(self.EXPERIMENT, self.TRACE)        