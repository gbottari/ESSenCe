'''
Created on Dec 24, 2010

@author: Giulio
'''

from system.configReader import ConfigReader
from system.energyModel import getMaxPerformance

perfIndex = 0
perfList = [0.8, 0.5, 0.6, 0.8, 0.4, 0.5, 0.6, 0.9, 0.7]

def actuate(self, qos):
    assert self._policyServers is not None
                           
    self._policyMutex.acquire()
    
    newPerf = self.perfList[self.perfIndex % len(self.perfList)] * getMaxPerformance(self._policyServers)
    self.perfIndex += 1
     
    try:
        output = None
        try:
            self._logger.debug('balancing: ' + str(newPerf))                
            output = self.balancePerformanceNaive(newPerf, self._policyServers)
        except Exception:
            self._logger.exception('balancePerformance has failed with args: (%s, %s)' % (newPerf, self._policyServers))
        else:
            try:
                self.applyPerfRegulation(output)
            except Exception:
                self._logger.exception('applyPerfRegulation has failed! Input was: %s' % output)
    finally:   
        self._policyMutex.release()
        

def main():   
    reader = ConfigReader('../tmp/config.txt')
    exp = reader.readExperiment()
    exp._perfRegulator.actuate = actuate
    exp.startExperiment()
    print 'end!'
    
if __name__ == '__main__':
    main()