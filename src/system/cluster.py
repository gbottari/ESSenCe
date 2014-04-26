'''
Created on Sep 16, 2010

@author: giulio
'''

import logging
from server import Server
from threading import Lock
from time import sleep
from sysObject import Object
from system.Builder import Builder
from system.server import ServerBuilder


class Cluster(Object):
    '''
    classdocs
    '''

    OFF_DELAY = 3 #time to wait from balancing servers to turning them off

    def __init__(self):
        self._switchesCount = []
        self._availableServers = []
        self.servers = []
        self.serviceMonitor = None
        self.loadBalancer = None
        self.stateLock = Lock()
        self._logger = logging.getLogger(type(self).__name__)
        self.sleep = sleep
        for state in Server.STATUSES:
            self.servers.append(list())
            self._switchesCount.append(0.0)
            state = state #remove warning sign
    
            
    def __str__(self):
        self.stateLock.acquire()
        string = '<%s(%s)>' % (self.__class__.__name__, str(self._availableServers))
        self.stateLock.release()

        return string    

    def __iter__(self):
        return self._availableServers.__iter__()
        
        
    def turnOn(self, server):
        assert server in self._availableServers
        
        self.stateLock.acquire()
        try:
            if server in self.servers[Server.OFF]: #don't do anything if server is already ON
                self._logger.info('Turning ON: %s' % server.hostname)    
            
                self.servers[Server.TURNING_ON].append(server)
                self._switchesCount[Server.TURNING_ON] += 1            
                self.servers[Server.OFF].remove(server)
                self.stateLock.release()
                            
                if not server.turnOn():
                    raise Exception('%s refuses to turn ON' % server)
        
                self.stateLock.acquire()
                self.servers[Server.ON].append(server)
                self._switchesCount[Server.ON] += 1            
                self.servers[Server.TURNING_ON].remove(server)           
                
                self.loadBalancer.enable(server)
                self.loadBalancer.balanceByPerformance()
        finally:
            self.stateLock.release()
            
    
    def turnOff(self, server):        
        assert server in self._availableServers
        
        self.stateLock.acquire()
        try:           
            if server in self.servers[Server.ON]: #don't do anything unless server is ON
                '''
                There's a little catch here. We must first redirect requests away
                from the machine we wish to turn off. Thus, we hand over a list of
                the current servers minus the one we wish to turn off to the load
                balancer.
                '''
                s = self.servers[Server.ON][:]
                s.remove(server)
                self.loadBalancer.balanceByPerformance(s)
                     
                self._logger.info('Turning OFF: %s' % server.hostname)      
                
                self.servers[Server.TURNING_OFF].append(server)
                self._switchesCount[Server.TURNING_OFF] += 1            
                self.servers[Server.ON].remove(server)        
                
                self.loadBalancer.disable(server)
                self.stateLock.release()
                
                # make sure that the server is ready to turn off
                self.sleep(Cluster.OFF_DELAY)                
                
                if not server.turnOff():
                    raise Exception('%s refuses to turn OFF' % server)                 
                
                self.stateLock.acquire()
                self.servers[Server.OFF].append(server)
                self._switchesCount[Server.OFF] += 1
                self.servers[Server.TURNING_OFF].remove(server)
        finally:
            self.stateLock.release()      
    
    
    def joinCluster(self, server):
        assert (server not in self._availableServers)
        assert (server is not None)
        
        self._logger.info('Joining the cluster: %s' % server.hostname)
        
        self.stateLock.acquire()
        self._availableServers.append(server) 
        self.servers[server.status].append(server)        
        self.stateLock.release()


    def leaveCluster(self, server):
        assert (server in self._availableServers)
        
        self._logger.info('Leaving the cluster: %s' % server.hostname)
        
        self.stateLock.acquire()
        self._availableServers.remove(server)
        self.servers[server.status].remove(server)        
        self.stateLock.release()
    
    join = joinCluster
    leave = leaveCluster    
    
    def getSwitchCount(self, status):
        self.stateLock.acquire()
        result = self._switchesCount[status]
        self.stateLock.release()
        return result
    
    
    def turnOnAll(self):
        for server in self._availableServers:
            self.turnOn(server)
            
            
    def turnOffAll(self):
        for server in self._availableServers:
            self.turnOff(server)
            
            
    def detect(self):
        '''
        Detects all servers
        '''
        self._logger.info('Detecting servers...')
        for server in self._availableServers:
            server.detect()
    
    def setup(self):
        self._logger.info('Setting up servers...')
        for server in self._availableServers:
            server._setup()
        self.loadBalancer.balanceByPerformance()
    
    def cleanUp(self):
        for server in self._availableServers:
            server.cleanUp()
         
    @property
    def availableServers(self):
        return self._availableServers[:]


class ClusterBuilder(Builder):
    
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = Cluster
        Builder.__init__(self, targetClass)        
        #option strings
        self.SERVERS = 'servers'
       
    
    def build(self, cr, *args):
        cluster = Builder.build(self, cr, *args)
        
        server_sections = cr.getValue(self.sectionName, self.SERVERS, eval)        
        for section in server_sections:
            server = ServerBuilder(section).build(cr)
            cluster.join(server)
            
        return cluster
        