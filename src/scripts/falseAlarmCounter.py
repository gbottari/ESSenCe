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

from Gnuplot import Gnuplot, Data

def main():
    traceFilename = '../../tmp/wc98_1.txt'
    configFilename = '../../tmp/dynGamma.txt'
    cReader = ConfigReader()
    cReader.parse(configFilename)
    cluster = cReader.readCluster()
    predictor = cReader.readPredictor()
    lb = cReader.readLoadBalancer(cluster)
    cluster.loadBalancer = lb
    
    config = cluster._availableServers[:]
    bestConfig = config[:]
    predConfig = config[:]
    reactiveConfig = config[:]    
    
    bestConfigurator = cReader.readConfigurator(cluster, DummyFilter())
    bestConfigurator.setEfficientServerList(cluster._availableServers)
    bestConfigurator.gamma = 1.0 #do not change!!
    
    predConfigurator = cReader.readConfigurator(cluster, predictor)
    predConfigurator.setEfficientServerList(cluster._availableServers)
    predConfigurator._gamma = 1.0
    
    reactiveConfigurator = cReader.readConfigurator(cluster, DummyFilter())
    reactiveConfigurator.setEfficientServerList(cluster._availableServers)
    #reactiveConfigurator._gamma = 0.55
    
    step = predConfigurator.windowSize
    
    #reads the trace file
    data = file2data(1, traceFilename)[0]
    scale(data, cluster.availableServers)

    predCounter, reactiveCounter, bestCounter = 0, 0, 0 #configuration counter
    pred_upCounter, pred_downCounter = 0, 0
    best_upCounter, best_downCounter = 0, 0
    reactive_upCounter, reactive_downCounter = 0, 0
    bestPerf = getMaxPerformance(bestConfig)
    reactivePerf = getMaxPerformance(bestConfig)
    predPerf = getMaxPerformance(bestConfig)
    
    avgs = []
    reactivePerfs = []
    predPerfs = []
    bestPerfs = []
    gammas = []
    for i in range(len(data) / step):
        avgData = 0.0
        for j in range(step):
            avgData += data[i * step + j]
        avgData /= step
        avgs.append(avgData)
        
        reactivePerfs.append(reactivePerf)
        predPerfs.append(predPerf)
        
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
            bestPerfs.append(bestPerf)
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
                
            if avgData > predPerf:                
                pred_downCounter += 1
            elif getMaxPerformance(predConfig) > getMaxPerformance(optimumConfig):
                pred_upCounter += 1
                
            elif len(bestConfig) < len(predConfig):
                pred_upCounter += 1
        
        prediction = predictor.apply(avgData)
        #actuation = prediction
        actuation = max(prediction, avgData)
        
        tmp = predConfigurator.getConfiguration(actuation, predConfig, predConfigurator._gamma)
        if set(tmp) != set(predConfig):
            predCounter += 1
            predConfig = tmp
            predPerf = getMaxPerformance(predConfig)        

        if reactiveConfigurator.dynGamma:
            idealConfig = bestConfigurator.getConfiguration(avgData, reactiveConfig, reactiveConfigurator.MAX_GAMMA)
            idealPerf = round(getMaxPerformance(idealConfig),5)
            currPerf = round(getMaxPerformance(reactiveConfig),5)
            
            reactiveConfigurator._gamma = reactiveConfigurator.adjustGamma(currPerf - idealPerf)
            gammas.append(reactiveConfigurator._gamma)
            
        tmp = reactiveConfigurator.getConfiguration(avgData, reactiveConfig, reactiveConfigurator._gamma)        
        if set(tmp) != set(reactiveConfig):
            reactiveCounter += 1
            reactiveConfig = tmp
            reactivePerf = getMaxPerformance(reactiveConfig)
        
        
                
    print 'Best       - False alarms: up = %d, down = %d' % (best_upCounter, best_downCounter)
    print 'Predictive - False alarms: up = %d, down = %d' % (pred_upCounter, pred_downCounter)
    print 'Reactive   - False alarms: up = %d, down = %d' % (reactive_upCounter, reactive_downCounter)
    print 'Best Configs = %d, Predictive Configs = %d, Reactive Configs = %d' %\
          (bestCounter, predCounter, reactiveCounter)
    
    
    g = Gnuplot(debug=0)
    g('reset')
    #g('set size 0.65,0.65')
    g('set encoding iso_8859_1')
    g('set terminal postscript eps enhanced monochrome')    
    g('set output "carlos2.ps"')
    g('set key top left')
    g('set xlabel "Tempo (s)"')
    g('set xrange [0:%d]' % (len(data) / step))
    spacing = 15
    tics = ','.join(['"%d" %d' % (x * step * spacing, x * spacing) for x in range(1, len(data) / (step * spacing) + 1)])
    g('set xtics (%s)' % tics)
    g('set ylabel "Requisições"'.encode('iso_8859_1'))
    g('set grid')
    
    #plot incoming requests avg
    with_plot = 'steps'    
    
    #plot configurations
    pi1 = Data(avgs, with_=with_plot,title='Carga')
    pi2 = Data(reactivePerfs, with_=with_plot,title='Reativo')
    pi_gamma = Data(gammas, with_=with_plot,title='Gamma')
    #pi3 = Data(predPerfs, with_=with_plot,title='Preditivo')    
    #pi4 = Data(bestPerfs, with_=with_plot,title='Perfect')
    #g.plot(pi1,pi2)
    #g.plot(pi_gamma)
    
    #raw_input()
        
    print 'Done'

if __name__ == '__main__':
    main()