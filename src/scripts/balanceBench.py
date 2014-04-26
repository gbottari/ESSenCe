'''
Created on Jun 16, 2011

@author: Giulio
'''
import sys, os
sys.path.append(os.path.abspath('..'))


from system.configReader import ConfigReader
from system.configurator import ConfiguratorBuilder
from system.energyModel import getMaxPerformance
import time


def main():    
    c = ConfigReader()
    c.parse('../../tmp/config.txt')
    cluster = c.readCluster()
    
    configurator = ConfiguratorBuilder().build(c, cluster, None)
    
    tests = 1000
    maxMultiplier = 200
    step = 20
        
    for mult in xrange(1,maxMultiplier,step):
        servers = cluster.availableServers * mult
        maxPerf = getMaxPerformance(servers)
           
        ti = time.time()
        for i in xrange(tests):    
            configurator.getConfiguration(maxPerf, servers,  1.0)            
        tf = time.time()
        
        print len(servers), (tf-ti) * 1000.0 / tests 
    
    
if __name__ == '__main__':
    main()