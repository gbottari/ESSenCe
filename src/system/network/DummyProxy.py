'''
Created on Jul 16, 2011

@author: Giulio
'''

import logging
from system.network.ServerProxy import ServerProxy

class DummyProxy(ServerProxy):
    '''
    classdocs
    '''

    recognizedFuncs = ['shell','send','receive','close']

    def __init__(self):
        ServerProxy.__init__(self)
        self._logger = logging.getLogger(type(self).__name__)
        self.logCalls = True        
    
    
    def connected(self):
        return True
    
    
    def _dummyCallable(self, *args):
        if self.logCalls:
            self._logger.debug('args %s' % str(args))        
    
        
    def __getattr__(self, name):
        if name in self.recognizedFuncs:            
            if self.logCalls:
                self._logger.debug('Calling %s' % (name))        
            return self._dummyCallable
        
        
if __name__ == '__main__':
    dp = DummyProxy()
    dp.shell(2,'kool')
    