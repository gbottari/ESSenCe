'''
Created on Jul 23, 2011

@author: Giulio
'''
import sys, os
sys.path.append(os.path.abspath('..'))


from system.configReader import ConfigReader
from system.configurator import ConfiguratorBuilder
from system.energyModel import getMaxPerformance
import cProfile


def main():    
    c = ConfigReader()
    c.parse('../../tmp/config.txt')
    cluster = c.readCluster()
    
    configurator = ConfiguratorBuilder().build(c, cluster, None)
    
    servers = cluster.availableServers * 100000
    maxPerf = getMaxPerformance(servers)
    cProfile.runctx('configurator.getConfiguration(maxPerf, servers,  1.0)',globals=globals(),locals=locals())
    
if __name__ == '__main__':
    main()