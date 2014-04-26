# -*- coding: utf-8 -*-
'''
Created on Dec 6, 2010

@author: Giulio
'''

#from system.filters import HoltFilter, DummyFilter
from stats import file2data
from traceScaler import scale
from system.configReader import ConfigReader
from system.energyModel import getMaxPerformance
from system.filters import DummyFilter

GAMMA_INCREMENT = 0.01
MAX_GAMMA = 2.0

def main():
    traceFilename = '../../tmp/nasa_3.txt'
    configFilename = '../../tmp/probSub.txt'
    cReader = ConfigReader()
    cReader.parse(configFilename)
    cluster = cReader.readCluster()
    lb = cReader.readLoadBalancer(cluster)
    cluster.loadBalancer = lb
    
    bestConfigurator = cReader.readConfigurator(cluster, DummyFilter())
    bestConfigurator.setEfficientServerList(cluster._availableServers)
    bestConfigurator.gamma = 1.0 #do not change!!
    
    reactiveConfigurator = cReader.readConfigurator(cluster, DummyFilter())
    reactiveConfigurator.setEfficientServerList(cluster._availableServers)
    
    step = bestConfigurator.windowSize
    
    #reads the trace file
    data = file2data(1, traceFilename)[0]
    scale(data, cluster.availableServers)
    
    gamma = 0.0
    while round(gamma,5) <= MAX_GAMMA:
        config = cluster._availableServers[:]
        bestConfig = config[:]
        reactiveConfig = config[:] 
        reactiveConfigurator._gamma = gamma        
                            
        reactiveCounter, bestCounter = 0, 0 #configuration counter
        best_upCounter, best_downCounter = 0, 0
        reactive_upCounter, reactive_downCounter = 0, 0
        bestPerf = getMaxPerformance(bestConfig)
        reactivePerf = getMaxPerformance(bestConfig)
        
        subestimated = 0.0
        for i in range(len(data) / step):
            avgData = 0.0
            for j in range(step):
                avgData += data[i * step + j]
            avgData /= step
                        
            optimumConfig = None
            '''
            Will use the efficient list to create the optimumConfig
            '''
            optimumConfig = [bestConfigurator._efficientServerList[0]]
            k = 1
            while getMaxPerformance(optimumConfig) < avgData:
                optimumConfig.append(bestConfigurator._efficientServerList[k])
                k += 1        
            
            '''
            Calculates the appropriate configuration, 'knowing' that avgData is true
            '''     
            if i > 0: #calculates false alarms                           
                tmp = bestConfigurator.getConfiguration(avgData, bestConfig, bestConfigurator._gamma)
                if tmp != bestConfig:                
                    bestCounter += 1                
                    bestConfig = tmp                
                    bestPerf = getMaxPerformance(bestConfig)
                '''
                Compares the chosen configuration with a least powerful one
                '''
                if avgData > bestPerf:                
                    best_downCounter += 1
                elif getMaxPerformance(bestConfig) > getMaxPerformance(optimumConfig):
                    best_upCounter += 1
                
                if avgData > reactivePerf:                
                    reactive_downCounter += 1                    
                elif getMaxPerformance(reactiveConfig) > getMaxPerformance(optimumConfig):
                    reactive_upCounter += 1
                
                for j in range(step):
                    subestimated += max(data[i * step + j] - reactivePerf, 0)
               
            if reactiveConfigurator.dynGamma:
                idealConfig = bestConfigurator.getConfiguration(avgData, reactiveConfig, reactiveConfigurator.MAX_GAMMA)
                idealPerf = round(getMaxPerformance(idealConfig),5)
                currPerf = round(getMaxPerformance(reactiveConfig),5)
                
                reactiveConfigurator._gamma = reactiveConfigurator.adjustGamma(currPerf - idealPerf)
                
            tmp = reactiveConfigurator.getConfiguration(avgData, reactiveConfig, reactiveConfigurator._gamma)        
            if set(tmp) != set(reactiveConfig):
                reactiveCounter += 1
                reactiveConfig = tmp
                reactivePerf = getMaxPerformance(reactiveConfig)
        
        #print 'Gamma = %f' % gamma
        #print 'Best       - super = %d, sub = %d' % (best_upCounter, best_downCounter)
        #print 'Reactive   - super = %d, sub = %d' % (reactive_upCounter, reactive_downCounter)
        #print 'Best Configs = %d, Reactive Configs = %d' %\
        #     (bestCounter, reactiveCounter)
        
        print gamma, 1.0 - reactive_downCounter / (float(len(data) - step) / step), reactiveCounter
        gamma += GAMMA_INCREMENT

if __name__ == '__main__':
    main()