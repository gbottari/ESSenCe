'''
Created on Nov 1, 2010

@author: Giulio
'''
import logging
from threading import Thread as DefaultThread
from sysObject import Object

class Thread(Object, DefaultThread):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        DefaultThread.__init__(self)
        self._stop = False
        self._logger = logging.getLogger(type(self).__name__)
       
        
    def start(self):
        self._logger.warning('Starting %s...' % type(self).__name__)
        DefaultThread.start(self)
       
        
    def stop(self):
        self._logger.warning('Stopping %s...' % type(self).__name__)
        self._stop = True