'''
Created on Jun 13, 2011

@author: Giulio
'''

from system.powerEmulator import PowerEmulator
from stats import file2data
from system.configReader import ConfigReader
from system.energyModel import getMaxPerformance
from system.server import Server

def main():
    monitorFilename = '2011-06-07_11h44m46s/monitor.txt'
    data = file2data(27, monitorFilename, 0)
        
    configFilename = '2011-06-07_11h44m46s/wc98_1_freqs.txt'
    cReader = ConfigReader()
    cReader.parse(configFilename)
    cluster = cReader.readCluster()
    cluster.servers[Server.ON] = cluster.availableServers
    del cluster.servers[Server.OFF][:]
    pe = PowerEmulator(cluster)
    
    map = {'ampere': 12, 'coulomb': 15, 'hertz': 18, 'joule': 21, 'ohm': 24}
    
    #offsets
    FREQ = 0
    FCAP = 1
    UTIL = 2
    
    #absolute
    POWER = 2 - 1
       
    
    for i in range(len(data[0])):
        # take utilization and freqs        
        for server in cluster:
            hostname = server.hostname
            server.processor.util = data[map[hostname] + UTIL][i] / 100.0
            server.processor.freq = data[map[hostname] + FREQ][i] * 1000000.0    
        
        if i < len(data[0]) - 1:
            print data[POWER][i+1], pe.calcPower()

if __name__ == '__main__':
    main()