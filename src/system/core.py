'''
Created on Sep 9, 2010

@author: giulio
'''

from sysObject import Object

class Core(Object):
    '''
    Represents a Processor Core
    '''

    def __init__(self):       
        self.number = None
        self.utilization = 0
        self.frequency = 0
        self.highTemp = 0.0
        self.critTemp = 0.0
        self.temperature = 0.0
        
        self.freq = self.frequency
        self.temp = self.temperature
        self.util = self.utilization
        
    def __repr__(self):
        return '<%s(%d)>' % (self.__class__.__name__, self.number)