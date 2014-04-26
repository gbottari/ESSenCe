'''
Created on Oct 13, 2010

@author: Giulio
'''

import sys, os
sys.path.append(os.path.abspath('..'))

from system.loadBalancer import LoadBalancer as SysLoadBalancer, LoadBalancerBuilder as SysLoadBalancerBuilder
from server import Server

class LoadBalancer(SysLoadBalancer):
    '''
    classdocs
    '''


    def __init__(self, cluster):
        '''
        Constructor
        '''
        SysLoadBalancer.__init__(self, cluster)
    
    
    def getTotalPerf(self, incoming):
        accPerf = 0.0
        for server, weight in self._weights:
            if server.status in [Server.ON, Server.TURNING_OFF]:
                accPerf += min(server.energyModel.getPerf(server.dvfsCont.getFreqCap()), weight * incoming)
        return accPerf
    
    def enable(self, server):
        pass    
    
    def disable(self, server):
        pass
    
    def _changeWeight(self, server, weight):
        pass


class LoadBalancerBuilder(SysLoadBalancerBuilder):
    
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = LoadBalancer
        SysLoadBalancerBuilder.__init__(self, targetClass)