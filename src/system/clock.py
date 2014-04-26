'''
Created on Dec 13, 2010

@author: giulio
'''

from threading import Semaphore, Condition, currentThread
from sysObject import Object
import logging

class Clock(Object):
    '''
    This class emulates _time in order to the system work in simulation mode.
    It keeps track of the threads that call 'sleep', with Record objects.
    Once the thread calls 'sleep', the corresponding Record semaphore is acquired
    a number of times specified with the '_time' parameter.
    When the tick function is called, _time passes, and all the semaphores are released once. 
    '''

    class Record(object):        
        def __init__(self, thread):
            self.sem = Semaphore(0)  # locks the thread until enough ticks are placed
            self.counter = 0         # times to call acquire()
            self.thread = thread     # thread identifier


    def __init__(self):
        '''
        Constructor
        '''
        self._records = []
        self._time = 0
        self._syncCondition = Condition()
        self._bypass = False  # bypass flag
        self._logger = logging.getLogger(type(self).__name__)
    
    
    def __str__(self):
        return '<%s(time=%d)>' % (self.__class__.__name__, self._time)
    
    
    def sleep(self, time):
        '''
        Blocks the calling thread until 'time' ticks has passed or bypass() has been called.
        '''        
               
        self._syncCondition.acquire()
        
        thread = currentThread()
        
        if time == 0 or self._bypass:
            #self._logger.debug('Bypassing: time = %d, condition = %s, culprit: %s' % (time,str(self._bypass),thread))
            self._syncCondition.release()
            return       
        
        # verifies if the thread is already registered
        rec = None
        
        for record in self._records:
            if record.thread is thread:
                rec = record
        
        # creates a record for it, if one is not found
        if rec is None:
            rec = self.Record(thread)    
            self._records.append(rec)
        
        rec.counter = time
        
        # signals that some record thread has been "trapped"
        self._syncCondition.notifyAll()
           
        self._syncCondition.release()
        
        # blocks the thread until a certain amount of ticks have passed        
        while rec.counter > 0:                        
            rec.sem.acquire()
 
    
    def tick(self):
        '''
        Makes time advance by one unit. All threads that have been blocked by sleep
        will be released if enough ticks has passed.
        '''
                
        for rec in self._records:
            self._syncCondition.acquire()
            if rec.counter > 0:
                rec.counter -= 1
                rec.sem.release()
                if rec.counter == 0:
                    self._syncCondition.wait()
                else:
                    self._syncCondition.release()
            else:
                self._syncCondition.release()
        
        self._syncCondition.acquire()
        self._time += 1
        self._syncCondition.release()
        
            
    def sync(self, threads):
        '''
        When tick is called, the threads that were blocked may be freed and start working again.
        Before continuing, we may want to wait for the threads to be blocked once again (when they
        call sleep, we assume they're done). 
        This method will wait until the specified threads are blocked again.
        '''
        
        stop = False
        while not stop:
            self._syncCondition.acquire()
            stop = True # assume the threads are blocked  
            for rec in self._records:
                for t in threads:
                    if rec.thread is t and rec.counter == 0:
                        # if we find at least one thread that is not blocked, 
                        # the assumption is false.
                        self._logger.debug('thread %s, recCounter %d' % (rec.thread , rec.counter))
                        stop = False
                        break
            if not stop:
                self._logger.debug('waiting')      
                self._syncCondition.wait() # wait also releases the lock
            else:
                self._syncCondition.release()
                
    
    def bypass(self):
        '''
        This method is useful when one wishes to terminates running threads.
        Bypass will make calls to sleep uneffective and also release all blocked threads.
        '''
        self._syncCondition.acquire()
        self._bypass = True
        for rec in self._records:
            rec.counter = 0
            #self._logger.debug('releasing %s' % rec.thread)
            rec.sem.release()      
        self._syncCondition.release()