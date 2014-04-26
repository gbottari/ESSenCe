'''
Created on Sep 22, 2010

@author: giulio
'''

from sysObject import Object
from system.Builder import Builder

class DVFSController(Object):
    '''
    classdocs
    '''


    def __init__(self, server):
        '''
        Constructor
        '''
        self._proc = server.processor
        self._freqCap = server.processor.availableFreqs[-1]
        self._server = server
    
    
    def __str__(self):
        return '<' + self.__class__.__name__ + '(freqCap=' + str(self._freqCap) + ')>'
    
    
    def setup(self):
        '''
        Setup the controller, set governors and initial frequencies
        '''
        pass
    
    
    def setFreqCap(self, freqCap):
        self._freqCap = freqCap
        
        
    def getFreqCap(self):
        return self._freqCap
    

class DVFSControllerBuilder(Builder):
    
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = DVFSController
        Builder.__init__(self, targetClass)