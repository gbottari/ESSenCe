#coding: utf-8
'''
Created on Sep 9, 2010

@author: giulio
'''

import logging
from core import Core
from sysObject import Object

class InvalidDataError(Exception): pass

class Processor(Object):
    '''
    Represents a Server Processor.
    It assumes that a processor consist of many cores, which may operate at different
    frequencies at a time. However, it is assumed that every core has the same set of 
    operational frequencies.
    '''
    
    STAT_FILENAME = '/proc/stat'
    TIME_IN_STATE_FILENAME = '/sys/devices/system/cpu/cpu0/cpufreq/stats/time_in_state'
    
    
    def __init__(self):
        self.cores = []                # list of cores, ordered by core number
        self._avgFreq = 0              # average frequency among all cores
        self._avgUtil = 0              # average utilization among all cores
        self._temperature = 0.0        # max temperature among all cores
        self._availableFreqs = []      # frequencies present on each core
        self._logger = logging.getLogger(type(self).__name__)


    def __repr__(self):
        return '<' + self.__class__.__name__ + '(' + str(self.cores) + ')>'

    
    def _readFreqs(self, time_in_state_text):
        '''
        Reads the available frequencies from the "time_in_state" file dump. 
        '''
        if time_in_state_text is None or len(time_in_state_text) == 0:
            raise InvalidDataError("Couldn't retrieve available freqs")
        
        lines = time_in_state_text.splitlines()
        
        del self._availableFreqs[:]
        for line in lines:
            if len(line) > 0:
                self._availableFreqs.append(int(line.split()[0]))
        self._availableFreqs.reverse()
        
        self._avgFreq = self._availableFreqs[0] # initialize freq field with some valid frequency
    
    
    def _readCores(self, proc_stat_dump):
        '''
        Reads the available cores from /proc/stat, and then
        creates Core objects associated with this Processor.
        '''        
        if proc_stat_dump is None or len(proc_stat_dump) == 0:
            raise InvalidDataError("Couldn't read: %s" % Processor.STAT_FILENAME)
        
        lines = proc_stat_dump.splitlines()
        
        del self.cores[:] # remove any cores that previously existed
        i = 0        
        while lines[i+1].startswith('cpu'): # skip first line, because it contains the average of all cpus                        
            core = Core()
            core.number = i
            self.cores.append(core)
            i += 1
            

    def detect(self):
        '''
        Detects system information to build the processor object
        '''
        if not self._availableFreqs:       
            dump = self.server.proxy.shell(['cat', self.TIME_IN_STATE_FILENAME], block=True)                                                     
            self._readFreqs(dump)
        else:
            self._logger.warning('Skipping freq detection')
            
        if not self._availableFreqs:
            dump = self.server.proxy.shell(['cat', Processor.STAT_FILENAME], block=True)  
            self._readCores(dump)
        else:
            self._logger.warning('Skipping core detection')        
        

    @property
    def temperature(self):
        return self._temperature
    
    @temperature.setter
    def temperature(self, temp):
        self._temperature = temp
    
    temp = temperature
    
    @property
    def utilization(self):
        return self._avgUtil

    @utilization.setter
    def utilization(self, util):
        self._avgUtil = util

    util = utilization

    @property
    def frequency(self):
        return self._avgFreq

    @frequency.setter
    def frequency(self, freq):
        if len(self.cores) > 0 and len(self._availableFreqs) >= 2:
            """
            Verify given frequency, if possible
            """
            if self._availableFreqs[0] <= freq <= self._availableFreqs[-1]:
                self._avgFreq = freq
            else:
                raise Exception("Given frequency out of bounds: %f" % freq)
        self._avgFreq = freq

    freq = frequency
    
    @property
    def availableFreqs(self):
        return self._availableFreqs
    
    @availableFreqs.setter
    def availableFreqs(self, freqs):
        '''
        Detects if the values are in GHz or MHz and then convert it to Hz
        '''
        if freqs[-1] < 10000.0:
            if freqs[-1] < 100.0: #Mhz
                mult = 1000000.0
            else:
                mult = 1000.0
            for i in range(len(freqs)):
                freqs[i] *= mult
        self._availableFreqs = freqs
