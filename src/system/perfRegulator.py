'''
Created on Sep 22, 2010

@author: giulio

to balance) is not ready yet.
IMPROVEMENTS:
- Make the balancePerformance faster, by using the current distribution.
- Make binary insertion on balancePerformance
'''

from time import sleep
from sysThread import Thread
from service import RequestBuffer
from deadzoneController import DeadzoneController
from ondemandController import OndemandController
from system.energyModel import getMaxPerformance, getPerformance
from server import Server
from system.Builder import Builder


class ServerPerf:
    def __init__(self, server):
        self.server = server
        self.power = server.energyModel.getPower(0) #idle power
        self.perf = 0.0
        self.factor = 0.0 #factor = perf/power
        self.perfIndex = 0 #current frequency index from freq list
        self.loadCapacity = 0.0 #performance quantity without switching the freq up
        
    def __repr__(self): #for debugging
        return self.server.hostname + ': perf = ' + str(self.perf)


class PerfRegulator(Thread):
    '''
    classdocs
    '''

    def __init__(self, cluster):
        Thread.__init__(self)
        self.cluster = cluster
        self._windowSize = 5        
        self._loopPeriod = 3
        self.controller = DeadzoneController()
        self._deltaPerf = 0.05
        self.sleep = sleep
    
    
    def balancePerformanceNaive(self, load, servers):
        '''
        Will balance the performance according to each server max capacity, granting
        proportional throughput among servers.
        '''       
        perfList = []
        maxLoad = getMaxPerformance(servers)
        for server in servers:
            serverPerf = ServerPerf(server)
            serverPerf.perf = load * (server.energyModel.peakPerf[-1] / maxLoad)
            perfList.append(serverPerf)
            
        return perfList
    
        
    def balancePerformance(self, load, servers):
        '''
        Complexity: O(l/c * n) where l = load, c = min performance and n = servers.
        
        Algorithm:
        
        #initialization:
            calculates the base factor (perf/power) for all machines
            zero-out the number of power consumed for the machines
            
        #loop
            search for greatest factor among the infolist
            fill the machine's load capacity, without switching up
            if the required load is balanced, finish 
        '''
        assert servers != None
        assert isinstance(load, int) or isinstance(load, float)
        assert load >= 0.0 
        
        #calculates the base factor (perf/power) for all machines
        perfList = []
        for server in servers:
            serverPerf = ServerPerf(server)
            serverPerf.loadCapacity = server.energyModel.peakPerf[0] 
            serverPerf.factor = (serverPerf.loadCapacity - 0.0) / (server.energyModel.busyPower[0] - server.energyModel.idlePower[0])            
            perfList.append(serverPerf)
        
        resultList = perfList[:]
        
        perfList.sort(key = lambda serverPerf: serverPerf.factor, reverse = True) #sort by factor        
        remainingLoad = load
        
        while remainingLoad > 0 and len(perfList) > 0:
            bestServer = perfList[0]

            machine_load = min(remainingLoad,bestServer.loadCapacity) #either finish the remaining load or fill the server up
            bestServer.perf += machine_load
            remainingLoad -= machine_load
            bestServer.power = bestServer.server.energyModel.getPower(bestServer.perf)
            
            peakPerf = bestServer.server.energyModel.peakPerf

            if bestServer.perfIndex < len(peakPerf) - 1:              
                bestServer.loadCapacity = peakPerf[bestServer.perfIndex + 1] - peakPerf[bestServer.perfIndex]
                bestServer.perfIndex += 1
                bestServer.factor = (peakPerf[bestServer.perfIndex] - peakPerf[bestServer.perfIndex - 1]) / \
                    (bestServer.server.energyModel.busyPower[bestServer.perfIndex] - bestServer.server.energyModel.busyPower[bestServer.perfIndex - 1])
                '''
                #reorders the list:
                #the factor element will always get smaller, because the function is concave.
                index = perfList.index(bestServer)
                for i in range(index,len(perfList) - 1):
                    if perfList[i].factor < perfList[i + 1].factor:
                        perfList[i], perfList[i + 1] = perfList[i + 1], perfList[i] #swap items
                    else: 
                        break #the rest of the list is already sorted
                '''
                perfList.sort(key = lambda serverPerf: serverPerf.factor, reverse = True) #sort by factor
            else: #maximum capacity reached
                del perfList[0] #remove best server
        
        """
        #sanity-check
        sum = 0.0
        for serverPerf in resultList:
            sum += serverPerf.perf
        
        assert (round(sum - load, 5) == 0.0)
        """
        
        return resultList
    
    
    def applyPerfRegulation(self, serverPerfList):
        '''
        Apply the freqCap for each server
        '''
        self._logger.debug('Applying perfReg')
        for serverPerf in serverPerfList:            
            server = serverPerf.server                        
            freqCap = server.energyModel.getFreq(serverPerf.perf)            
            if freqCap != server.dvfsCont.getFreqCap():
                if isinstance(server.dvfsCont,OndemandController):                
                    server.dvfsCont.setFreqCap(freqCap,dest=server._IP)
                else:
                    server.dvfsCont.setFreqCap(freqCap)
                    self._logger.debug('%s frequency cap is now: %4.3fGHz (%3.1f req/s)' % (server, freqCap / 1000000.0, serverPerf.perf))

        #Update the load balancer weights
        self.cluster.loadBalancer.balanceByPerformance()        
        

    def actuate(self, input):
        self._logger.debug('input = %f' % input)
        self.cluster.stateLock.acquire()
        try:            
            currPerf = getPerformance(self.cluster.servers[Server.ON])
            sat = input / currPerf
                    
            if round(sat - self.controller._setPoint, 5) != 0:
                newPerf = input / self.controller._setPoint           
                newPerf = min(getMaxPerformance(self.cluster.servers[Server.ON]), newPerf)
                self._logger.debug('allocation = %f' % newPerf)
                
                output = None
                try:                    
                    output = self.balancePerformance(newPerf, self.cluster.servers[Server.ON])
                    #output = self.balancePerformanceNaive(newPerf, self.cluster.servers[Server.ON])                                    
                except Exception:
                    self._logger.exception('balancePerformance has failed with args: (%s, %s)' % (newPerf, self.cluster.servers[Server.ON]))
                else:
                    try:
                        self.applyPerfRegulation(output)
                    except Exception:
                        self._logger.exception('applyPerfRegulation has failed! Input was: %s' % output)
        finally:
            self.cluster.stateLock.release()


    def run(self):
        '''
        PerfRegulator will arrange performance in a way that QoS = QoS_target
        '''
        try:
            while not self._stop:                
                self.sleep(self._loopPeriod)                
                info = self.cluster.serviceMonitor.services[0].getInfo(self._windowSize)
                incoming = info[RequestBuffer.INCOMING]                
                self.actuate(incoming)                
        except Exception:
            self._logger.exception('%s has failed!' % type(self).__name__)
            raise
        finally:
            self._logger.warning('%s has stopped' % type(self).__name__)
        
        
    @property
    def windowSize(self):
        return self._windowSize
        
    @windowSize.setter
    def windowSize(self, ws):
        self._windowSize = ws
    
    @property
    def loopPeriod(self):
        return self._loopPeriod
    
    @loopPeriod.setter
    def loopPeriod(self, value):
        self._loopPeriod = value
    
    @property
    def deltaPerf(self):
        return self._deltaPerf
    
    @deltaPerf.setter
    def deltaPerf(self, value):
        self._deltaPerf = value


class PerfRegulatorBuilder(Builder):
    
    def __init__(self):
        Builder.__init__(self, PerfRegulator)
        #option strings        
        self.LOOP_PERIOD = 'loopperiod'
        self.QOS_WINDOW_SIZE = 'qoswindowsize'
        self.LOAD_WINDOWSIZE = 'loadwindowsize'
        self.SETPOINT = 'setpoint'
        
    
    def build(self, cr, cluster):
        obj = self.targetClass(cluster)
        
        obj.loopPeriod = cr.getValue(self.sectionName, self.LOOP_PERIOD, int)
        obj.windowSize = cr.getValue(self.sectionName, self.QOS_WINDOW_SIZE, int)
        obj.loadWindowSize = cr.getValue(self.sectionName, self.LOAD_WINDOWSIZE, int)
        obj.controller.setPoint(cr.getValue(self.sectionName, self.SETPOINT, float))
                
        return obj


if __name__ == '__main__':
    cluster = None
    p = PerfRegulator(cluster)
    p.start()