'''
Created on Sep 22, 2010

@author: giulio

TODO: Add service name
TODO: Use another data structure for the buffer. A list is kind of problem-prone.
'''

import threading
import logging
from sysObject import Object
from system.Builder import Builder

class RequestBuffer(Object):
    '''
    classdocs
    '''
    QOS = 0
    LOST = 1
    REPLIED = 2
    INCOMING = 3
    DELAY = 4
    VARIABLES_COUNT = 5
    DEFAULT_BUFFER_SIZE = 10


    def __init__(self):        
        self._urls = [] #list of URLs that belongs to this service
        self._buffer = None #[ [QOS,LOST,REPLIED,INCOMING], ...]
        self._bufferMutex = threading.Lock()
        self._bufferReady = threading.Condition()
        self._bufferCount = 0 #number of elements on the buffer
        self._bufferSize = 0  #maximum elements on the buffer
        self.setBufferSize(self.DEFAULT_BUFFER_SIZE)
        self._logger = logging.getLogger(type(self).__name__)
    
    
    def setBufferSize(self, size):
        '''
        Note: this process will erase data on the buffers when called.
        Note: this shouldn't be called after the thread has started running.
        '''
        self._bufferMutex.acquire()
        self._bufferSize = size
        self._buffer = [[0.0] * self.VARIABLES_COUNT] * self._bufferSize        
        self._bufferMutex.release()
        
        
    def getInfo(self, samples):
        '''
        Will return the average 'info' through 'samples'.
        Note: fresh values are in the back of the queue.
        '''
        result = [0.0] * self.VARIABLES_COUNT
        
        if self._bufferSize == 0:
            # the buffer hasn't been properly initialized by calling setBufferSize
            self.setBufferSize(1)
        
        '''
        E.g.
        buffer = [10, 20, 30, 40]
        size = 4
        samples = 3
        result = (20 + 30 + 40) / 3 = 45
        '''
        self._bufferMutex.acquire()
        itemsCounter = min(samples, self._bufferCount) # fetch samples or the maximum available
        
        for i in range(self._bufferSize - itemsCounter, self._bufferSize):
            for j in range(len(result)):
                result[j] += self._buffer[i][j]
        self._bufferMutex.release()
        
        if itemsCounter > 0:
            # average from the items
            for i in range(len(result)):
                result[i] /= itemsCounter
        
        return result

    
    def updateBuffer(self, data):
        assert data is not None
        
        self._bufferMutex.acquire()
        self._buffer.append(data)
        self._buffer.pop(0)
        self._bufferCount += 1  
            
        #if self.monitor is not None:
        #    self.monitor.setServiceInfo(data)
        self._bufferMutex.release()
   
    @property
    def urls(self):
        return self._urls    
    
    @urls.setter
    def urls(self, urlList):
        self._urls = urlList


class RequestBufferBuilder(Builder):
    
    def __init__(self):
        Builder.__init__(self, RequestBuffer)
        #option strings        
        self.URLS = 'urls'
    
        
    def build(self, cr, section):
        obj = self.targetClass()      
        obj.name = section
        obj.urls = cr.getValue(section, self.URLS, eval)
                
        return obj