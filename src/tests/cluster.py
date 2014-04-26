'''
Created on Sep 23, 2010

@author: giulio
'''
import unittest

import sys, os
from system.energyModel import EnergyModel
sys.path.append(os.path.abspath('..'))

from simulator.cluster import Cluster
from simulator.server import Server
from system.DVFSController import DVFSController
from simulator.loadBalancer import LoadBalancer

class ClusterTest(unittest.TestCase):

    def setUp(self):        
        self.cluster = Cluster()        
        lb = LoadBalancer(self.cluster)
        self.cluster.loadBalancer = lb
        
        self.s1 = Server()        
        self.s2 = Server()
        
        self.s1.WAKE_UP_TIME = 0
        self.s2.WAKE_UP_TIME = 0
        
        emodel1 = EnergyModel(self.s1)
        emodel2 = EnergyModel(self.s1)
        
        peakPerf = [1,2,3]
        busy = [3,4,5]
        idle = [1,1,1]
        
        emodel1.assignSamples(busy, idle, peakPerf)
        emodel2.assignSamples(busy, idle, peakPerf)
        
        self.s1.energyModel = emodel1
        self.s2.energyModel = emodel2
        
        freqs = [1.0,2.0]
        self.s1.processor.availableFreqs = freqs
        self.s2.processor.availableFreqs = freqs
        cont1 = DVFSController(self.s1)
        cont2 = DVFSController(self.s2)
        self.s1.dvfsCont = cont1
        self.s2.dvfsCont = cont2

    def test_turnOnInvalidServer(self):
        self.assertRaises(AssertionError,self.cluster.turnOn,None)
        #not joined yet:
        self.assertRaises(AssertionError,self.cluster.turnOn, self.s1)

    def test_joinCluster(self):
        self.cluster.joinCluster(self.s1)
        self.assertTrue(self.s1 in self.cluster._availableServers)
        self.assertTrue(self.s1 in self.cluster.servers[Server.OFF])
        
        #invalid join:
        self.assertRaises(AssertionError, self.cluster.joinCluster, None)
        #multiple joining:
        self.assertRaises(AssertionError, self.cluster.joinCluster, self.s1)
    
    def test_leaveCluster(self):
        self.cluster.joinCluster(self.s1)
        self.cluster.leaveCluster(self.s1)
        self.assertTrue(self.s1 not in self.cluster._availableServers)
        
        #invalid leaving:
        self.assertRaises(AssertionError, self.cluster.leaveCluster, None)
        #multiple leaving:
        self.assertRaises(AssertionError, self.cluster.leaveCluster, self.s1)
        
    def test_turnOn(self):
        self.s1._status = Server.OFF
        self.cluster.joinCluster(self.s1)
        self.assertTrue(self.s1 in self.cluster.servers[Server.OFF])
        self.cluster.turnOn(self.s1)
        self.assertTrue(self.s1 in self.cluster.servers[Server.ON])
        
        #invalid turnOn:
        self.assertRaises(AssertionError, self.cluster.turnOn, None)
        self.assertRaises(AssertionError, self.cluster.turnOn, self.s2)
    
    def test_turnOff(self):
        self.s1._status = Server.ON
        self.cluster.joinCluster(self.s1)
        self.cluster.turnOff(self.s1)
        
        #invalid turnOn:
        self.assertRaises(AssertionError, self.cluster.turnOff, None)
        self.assertRaises(AssertionError, self.cluster.turnOff, self.s2)
        

if __name__ == "__main__":
    unittest.main()