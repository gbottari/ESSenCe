'''
Created on Apr 6, 2011

@author: Giulio
'''

from system.configReader import ConfigReader

def main():    
    c = ConfigReader()
    c.parse('../../tmp/config.txt')
    cluster = c.readCluster()
    
    print 'Frequency Pick Efficiency','*' * 10
    
    pickList = []
    for server in cluster:        
        dynPot = [busy - idle for busy, idle in zip(server.energyModel.busyPower,server.energyModel.idlePower)]
        deltaPerf = [server.energyModel.peakPerf[0]]
        deltaPerf += [server.energyModel.peakPerf[i+1] for i in range(len(server.energyModel.peakPerf)-1)]
        #deltaPerf = server.energyModel.peakPerf[:]
        eff = [deltaPerf[i] / dynPot[i] for i in range(len(dynPot))]
        pickList += [(server.hostname, eff[i], i) for i in range(len(eff))]        
        print server.hostname, eff
    
    pickList = sorted(pickList, key=lambda element: element[1], reverse=True)
    for element in pickList:
        print element
    """
    print 'Server Pick Efficiency Integral','*' * 10
    #calculates the integral power * load for each server
    pickList = []
    for server in cluster:        
        a = 0.0
        b = server.energyModel.idlePower[0]
        d = 0.0
        integral = 0.0
        for i in range(len(server.energyModel.peakPerf)):
            d = server.energyModel.busyPower[i]
            a = server.energyModel.peakPerf[i] - a
            integral += a / 2.0 * (b + d)
            b = d
        pickList.append((server.hostname, integral))
    
    pickList = sorted(pickList, key=lambda element: element[1])
    for element in pickList:
        print element

    print 'Server Pick Efficiency peak/power','*' * 10
    #calculates the integral power * load for each server
    pickList = []
    for server in cluster:
        pickList.append((server.hostname,server.energyModel.peakPerf[-1]/server.energyModel.busyPower[-1] ))
    
    pickList = sorted(pickList, key=lambda element: element[1], reverse=True)
    for element in pickList:
        print element
    """

            
if __name__ == '__main__':
    main()