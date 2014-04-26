'''
Created on Nov 15, 2010

@author: Giulio
'''

import sys, os
from simulator.server import ServerBuilder
from system.Builder import Builder
sys.path.append(os.path.abspath('..'))

from system.cluster import Cluster as SysCluster, ClusterBuilder as SysClusterBuilder
from simulator.server import Server


class Cluster(SysCluster):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        SysCluster.__init__(self)
    
    
    def turnOnAll(self):
        self.servers[Server.ON] = self._availableServers[:]
        for server in self.servers[Server.ON]:            
            #server.processor.freq = server.processor.availableFreqs[-1]
            server._status = Server.ON
        del self.servers[Server.OFF][:]
        
        self.loadBalancer.balanceByPerformance()


class ClusterBuilder(SysClusterBuilder):
    
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = Cluster
        SysClusterBuilder.__init__(self, targetClass)
    
    
    def build(self, cr, *args):
        cluster = Builder.build(self, cr, *args)
        
        server_sections = cr.getValue(self.sectionName,self.SERVERS, eval)        
        for section in server_sections:            
            server = ServerBuilder(section).build(cr)            
            #assert isinstance(server, Server)
            cluster.join(server)
            
        return cluster