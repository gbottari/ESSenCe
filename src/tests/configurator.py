'''
Created on Sep 30, 2010

@author: giulio
'''
import unittest
from StringIO import StringIO

from system.configReader import ConfigReader
from simulator.cluster import ClusterBuilder
from system.configurator import ConfiguratorBuilder
from system.energyModel import getMaxPerformance
from simulator.server import Server


class ConfiguratorBasicTests(unittest.TestCase):
    def setUp(self):
        config = """
[Cluster]
builder: ('simulator.cluster', 'ClusterBuilder')
servers: ['Ampere']

[Configurator]
builder: ('system.configurator', 'ConfiguratorBuilder')
dependencies: ['Cluster', 'Predictor']
loopPeriod: 20
windowSize: 20
gamma: 1.0

[DVFSController]
builder: ('system.DVFSController', 'DVFSControllerBuilder')

[Ampere]
idlePower: [66.3,70.5,72.7]
busyPower: [81.5,101.8,109.8]
peakPerformance: [170.0,309.9,346.8]
freqs: [1.0,1.8,2.0]
"""
        
        cr = ConfigReader(None)
        sio = StringIO(config)
        cr.readfp(sio)
        
        cluster = ClusterBuilder().build(cr)
        self.configurator = ConfiguratorBuilder().build(cr, cluster, None)
        
    
    def testSmoke(self):
        '''
        Must get a valid configuration for a typical load
        '''
        sl = [self.configurator._efficientServerList[0]]
        config = self.configurator.getConfiguration(100, sl, self.configurator._gamma)
        self.assertTrue(config is not None)
        self.assertTrue(isinstance(config, list))
        self.assertTrue(len(config) > 0) #one server at least
        for server in config: #the members of the list must be servers
            self.assertTrue(isinstance(server,Server))
        
    def testInvalidData(self):
        '''
        Expected results when the functions are called with invalid or incomplete data
        '''
        #Parameters:
        self.assertRaises(AssertionError, self.configurator.getConfiguration, None, None, None)
        self.assertRaises(AssertionError, self.configurator.applyConfiguration, None)
        
        #Malformed Server:
        s = Server()
        self.assertRaises(AttributeError, self.configurator.getConfiguration, 100, [s], self.configurator._gamma)
        
    def testAdjutGamma(self):
        #maintain gamma:
        currGamma = self.configurator._gamma
        newGamma = self.configurator.adjustGamma(0.0)
        self.assertEquals(currGamma,newGamma)
        
        self.configurator._gamma = 0.5
        currGamma = self.configurator._gamma
        
        #increase gamma
        newGamma = self.configurator.adjustGamma(1) #positive number        
        self.assertTrue(newGamma > currGamma)        
        
        #decrease gamma
        newGamma = self.configurator.adjustGamma(-1) #negative number
        self.assertTrue(newGamma < currGamma)
                

class ConfiguratorServerTests(unittest.TestCase):
    def setUp(self):
        config = """
[Cluster]
builder: ('simulator.cluster', 'ClusterBuilder')
servers: ['Ampere', 'Coulomb', 'Hertz', 'Joule', 'Ohm']

[Configurator]
builder: ('system.configurator', 'ConfiguratorBuilder')
dependencies: ['Cluster', 'Predictor']
loopPeriod: 20
windowSize: 20
gamma: 1.0

[DVFSController]
builder: ('system.DVFSController', 'DVFSControllerBuilder')

[Ampere]
hostname: ampere
idlePower: [66.3,70.5,72.7]
busyPower: [81.5,101.8,109.8]
peakPerformance: [170.0,309.9,346.8]
freqs: [1.0,1.8,2.0]

[Coulomb]
hostname: coulomb
idlePower: [67.4,70.9,72.4,73.8,75.2]
busyPower: [75.2,89.0,94.5,100.9,107.7]
peakPerformance: [84.0,152.5,168.6,184.5,199.8]
freqs: [1.0,1.8,2.0,2.2,2.4]

[Hertz]
hostname: hertz
idlePower: [63.9,67.2,68.7,69.9,71.6]
busyPower: [71.6,85.5,90.7,96.5,103.2]
peakPerformance: [82.8,151.3,167.6,183.8,198.5]
freqs: [1.0,1.8,2.0,2.2,2.4]

[Joule]
hostname: joule
idlePower: [66.6,73.8,76.9,80.0]
busyPower: [74.7,95.7,103.1,110.6]
peakPerformance: [82.0,148.3,163.3,179.4]
freqs: [1.0,1.8,2.0,2.2]

[Ohm]
hostname: ohm
idlePower: [65.8,68.5,70.6,72.3,74.3,76.9]
busyPower: [82.5,99.2,107.3,116.6,127.2,140.1]
peakPerformance: [164.8,301.5,337.9,370.9,404.4,439.5]
freqs: [1.0,1.8,2.0,2.2,2.4,2.6]
"""
        
        cr = ConfigReader(None)
        sio = StringIO(config)
        cr.readfp(sio)
        
        cluster = ClusterBuilder().build(cr)
        self.configurator = ConfiguratorBuilder().build(cr, cluster, None)
        
    
    def testExtremes(self):
        sl = self.configurator._efficientServerList[:2]
        
        #Overload
        config = self.configurator.getConfiguration(float('inf'), sl, self.configurator._gamma)
        self.assertTrue(len(config) == len(sl) + 1) #should turn on +1 server
        
        #Underload
        config = self.configurator.getConfiguration(-float('inf'), sl, self.configurator._gamma)
        self.assertTrue(len(config) == len(sl) - 1 and len(config) > 0) #should turn on -1 server, but not everyone
    
    
    def testOneServerRemains(self):
        '''
        One server should be always ON, no matter how low the load is
        '''
        sl = [self.configurator._efficientServerList[0]]
        config = self.configurator.getConfiguration(0.0, sl, self.configurator._gamma)
        self.assertEquals(config,sl)   
    
    
    def testEfficient(self):
        '''
        Tests that the configurator will add/remove the most efficient server available
        '''
        server0 = self.configurator._efficientServerList[0]
        server1 = self.configurator._efficientServerList[1]
        server2 = self.configurator._efficientServerList[2]
        sl = [server0]
        
        #Overload, server[1] will do
        load = server0.energyModel.peakPerf[-1] + 1.0
        config = self.configurator.getConfiguration(load, sl, self.configurator._gamma)
        self.assertEquals(config,[self.configurator._efficientServerList[0],self.configurator._efficientServerList[1]])
        
        #Underload, no change
        sl = [server0, server1]        
        load = server0.energyModel.peakPerf[-1] + server1.energyModel.peakPerf[-1] -5.0
        config = self.configurator.getConfiguration(load, sl, self.configurator._gamma)
        self.assertEquals(config,sl)
        
        #Underload, server[0] will do
        sl = [server0,server1]
        load = server0.energyModel.peakPerf[-1] - 1.0
        config = self.configurator.getConfiguration(load, sl, self.configurator._gamma)
        self.assertEquals(config,[server0])

        #Underload, server[1] and server[0] will do
        sl = [server0,server1,server2]
        load = server0.energyModel.peakPerf[-1] + server1.energyModel.peakPerf[-1] - 1.0
        config = self.configurator.getConfiguration(load, sl, self.configurator._gamma)
        self.assertEquals(config,[server0, server1])


    def testRamp(self):
        '''
        Will build a ramp to test configurations
        All configurations must be able to cope with the load.
        '''
        trace = range(0, int(getMaxPerformance(self.configurator._efficientServerList)))
        reversed = trace[:]
        reversed.reverse()
        trace.extend(reversed)
        
        config = self.configurator._efficientServerList
        for load in trace:
            config = self.configurator.getConfiguration(load, config, self.configurator._gamma)
            perf = getMaxPerformance(config)
            #print 'load =',load,'perf =',perf
            if perf < load:
                self.fail("Configuration can't cope with load")


if __name__ == "__main__":
    unittest.main()