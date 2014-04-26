'''
Created on Sep 22, 2010

@author: giulio
'''

from server import Server
from energyModel import getMaxPerformance
from sysThread import Thread
from time import sleep
from service import RequestBuffer
from system.Builder import Builder


class Configurator(Thread):
    '''
    classdocs
    '''  

    def __init__(self, cluster, predictor):
        '''
        Constructor
        '''
        Thread.__init__(self)
        self.sectionName = self.__class__.__name__
        
        self._efficientServerList = None
        self.cluster = cluster
        self._loopPeriod = 5 #in seconds
        self._windowSize = 5 #average through windowSize numbers
        self.predictor = predictor
        self._gamma = 1.0 #value that multiply the deadzone
        self.sleep = sleep #sleep function
        self.predicted = 0.0
        
        self.adjustWindow = 5 #put it on configReader
        self.gammaIncrease = 0.01
        self.gammaDecrease = 0.10
        self.dynGamma = False
        self.MAX_GAMMA = 0.90
        self.MIN_GAMMA = 0.00
        
        self.setEfficientServerList(cluster.availableServers[:])
    
    def __repr__(self):
        return '<%s(gamma=%f, loop=%d, window=%d)>' % \
            (self.__class__.__name__, self._gamma, self._loopPeriod, self._windowSize)
    
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
    def loopPeriod(self, lp):
        self._loopPeriod = lp
        
    @property
    def gamma(self):
        return self._gamma

    @gamma.setter
    def gamma(self, value):
        assert value >= 0.0
        self._gamma = value
            
    
    def setEfficientServerList(self, servers):
        '''
        Sort servers by (reversed) performance
        '''
        self._efficientServerList = sorted(servers, key=lambda s: s.energyModel.peakPerf[-1], reverse=True)

 
    def getConfiguration(self, load, config, gamma):
        '''
        Takes a previous configuration (severs that are ON), and gives another configuration, fit for the load.
        This implementation adds/removes the most/least efficient server available that can handle the load.
        Note: this implementation will add or remove one server at most.
        
        ENHANCEMENT: if the load is too low, and there is just one server ON, switch it with the most efficient one.
        ENHANCEMENT: add/remove multiple servers        
        '''
        assert config != None and isinstance(config, list) and len(config) > 0
        assert self._efficientServerList != None
                
        newConfig = config[:]
                
        configPerf = getMaxPerformance(config)

        if load > configPerf * gamma:
            '''
            Will try to find the most efficient server that when added, will make the cluster handle the load.
            If no server can handle the load, the most powerful one is chosen, regardless of efficiency.
            '''            
            candidates = [server for server in self._efficientServerList if server not in config]
            if len(candidates) > 0:
                greatestServer = candidates[0]
                foundServer = False
                
                for server in candidates:
                    if (configPerf + server.energyModel.peakPerf[-1]) * gamma >= load:
                        newConfig.append(server)
                        foundServer = True
                        break                        
                    if server.energyModel.peakPerf[-1] > greatestServer.energyModel.peakPerf[-1]:
                        greatestServer = server #might go back to this one, so we save it                   
                        
                if not foundServer: #then, turn on the mightiest we have
                    newConfig.append(greatestServer)
            else:
                self._logger.info('All machines already ON')
            
        else:
            '''
            Will try to minimize the number of servers ON, starting with the least efficient servers.
            
            Future plans:
            Try to rearrange the cluster for better power efficiency.
            To do this, we will try to find a better configuration, but taking the migration costs
            (i.e. switch up overhead) into account.
            Also, the load must be close to the setPoint in order to do this optimization, meaning
            that we won't be just wasting energy on the process.  
            '''
            inefficientServerList = self._efficientServerList[:]
            inefficientServerList.reverse()
            candidates = [server for server in inefficientServerList if server in config]
            for server in candidates:
                #turning that server off won't kill QoS
                if round((configPerf - server.energyModel.peakPerf[-1]) * gamma - load, 10) >= 0: 
                    if len(newConfig) > 1: #necessary?
                        newConfig.remove(server)
                    break
        
        return newConfig


    def applyConfiguration(self, config):
        '''
        @param config: is list containing servers that should be ON 
        
        First the function will turn ON the servers that are not currently ON. 
        When they are ready, configurator will call the loadBalancer to include the fresh servers into loadBalance and
        exclude those who doesn't belong to the set anymore.
        Then it will turnOff those servers that are not present in serverList.
        Once the configuration is set, applyConfiguration will calculate new values to the controller thresholds.
        
        ENHANCEMENT: parallel turnON()
        '''
        assert config is not None and isinstance(config, list) and len(config) > 0
        
        self._logger.info('Applying configuration: %s' % str(config))
        
        '''
        First, turn servers that are not already ON.        
        While turning servers ON/OFF, the DVFS module can detect the 
        new configuration, and manage it automatically.
        '''        
        
        for server in config:
            if server.status == Server.OFF:
                self.cluster.turnOn(server)

        '''
        Now, turn servers OFF.        
        '''
        serversToTurnOff = [server for server in self.cluster.servers[Server.ON] if server not in config]

        for server in serversToTurnOff:           
            self.cluster.turnOff(server)
        
        self._logger.info('Configuration: %s has been set' % str(config))


    def actuate(self, incoming):        
        pred_incoming = self.predictor.apply(incoming)
        action = max(incoming, pred_incoming)
        self.predicted = action
        
        config = self.cluster.servers[Server.ON]
        try:
            newConfig = self.getConfiguration(action, config, self._gamma)
            if set(newConfig) != set(config): 
                # only apply configurations that are different from the current one
                self.applyConfiguration(newConfig)
        except:
            self._logger.exception('Calling: %s() failed with args: (%s,%s)' % \
                                   (self.getConfiguration.__name__, pred_incoming,config))            
            newConfig = config[:] #don't change configs, then
        

    
    def adjustGamma(self, perfDistance):
        perfDistance = round(perfDistance, 5)
        if perfDistance > 0:
            return min(self._gamma + self.gammaIncrease, self.MAX_GAMMA)
        elif perfDistance < 0:
            return max(self._gamma - self.gammaDecrease, self.MIN_GAMMA)
        return self._gamma
    

    def run(self):
        try:
            #counter = 0
            while not self._stop:
                self.sleep(self._loopPeriod)
                
                info = self.cluster.serviceMonitor.services[0].getInfo(self._windowSize) #workaround
                incoming = info[RequestBuffer.INCOMING]                
                """
                counter += 1
                if self.dynGamma and (counter == self.adjustWindow):
                    #calculate underestimations and overestimations:               
                    self.cluster.stateLock.acquire()
                    #self._logger.debug('incoming = %d, servers=%s, gamma=%f' % \
                                        (incoming, self.cluster.servers[Server.ON], self.MAX_GAMMA))
                    idealConfig = self.getConfiguration(incoming, self.cluster.servers[Server.ON], self.MAX_GAMMA)
                    currentPerf = getMaxPerformance(self.cluster.servers[Server.ON])
                    self.cluster.stateLock.release()
                    
                    idealPerf = getMaxPerformance(idealConfig)
                    perfDistance = currentPerf - idealPerf
                    self._gamma = self.adjustGamma(perfDistance)
                    counter = 0
                """
                self.actuate(incoming)                
                
        except Exception:
            self._logger.exception('%s has failed!' % type(self).__name__)            
            raise
        finally:
            self._logger.warning('%s has stopped' % type(self).__name__)
            

class ConfiguratorBuilder(Builder):
    
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = Configurator
        Builder.__init__(self, targetClass)
        #option strings        
        self.LOOP_PERIOD = 'loopperiod'
        self.WINDOW_SIZE = 'windowsize'
        self.GAMMA = 'gamma'
        self.ADJUST_GAMMA = 'adjustgamma'
        self.GAMMA_INCR = 'gammaincrease'
        self.GAMMA_DECR = 'gammadecrease'
        self.ADJUST_WINDOW = 'adjustwindow'
    
    
    def readOptions(self, obj, cr):
        obj.loopPeriod = cr.getValue(self.sectionName, self.LOOP_PERIOD, int)
        obj.windowSize = cr.getValue(self.sectionName, self.WINDOW_SIZE, int)
        obj.gamma = cr.getValue(self.sectionName, self.GAMMA, float)
        obj.dynGamma = cr.getValue(self.sectionName, self.ADJUST_GAMMA, bool, False)
        if obj.dynGamma:
            obj.gammaIncrease = cr.getValue(self.sectionName, self.GAMMA_INCR, float, True)
            obj.gammaDecrease = cr.getValue(self.sectionName, self.GAMMA_DECR, float, True)
            obj.adjustWindow = cr.getValue(self.sectionName, self.ADJUST_WINDOW, int, True)