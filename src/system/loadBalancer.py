'''
Created on Sep 22, 2010

@author: giulio
'''

import logging
from server import Server
from threading import Lock
from sysObject import Object
from system.Builder import Builder

class LoadBalancer(Object):
    '''
    Controls the load distribution in an Apache server.
    It works by communicating with the apache proxy, sending balancing orders.
    '''

    def __init__(self, cluster):
        '''
        Needs to specify a list of servers that can be handled by the Apache proxy
        '''
        self.apache = None
        self.cluster = cluster
        self._weights = []
        self._mutex = Lock()
        self._logger = logging.getLogger(type(self).__name__)
           
    
    def disable(self, server):
        assert self.apache is not None

        self._mutex.acquire()
        try:
            ret = self.apache.set_worker_info("balancer://mycluster", "http://" + server.hostname + ":81", 0, -1)
            #self._logger.debug('call return: %d' % ret)
            
            if ret == self.apache.WORKER_NOT_FOUND:
                raise Exception("Apache couldn't find worker %s. Check httpd.conf")
        except:
            self._logger.exception('Could not disable %s' % (server))
        finally:
            self._mutex.release()
        
        
    def enable(self, server):
        assert self.apache is not None

        self._mutex.acquire()
        try:
            ret = self.apache.set_worker_info("balancer://mycluster", "http://" + server.hostname + ":81", 1, -1)
            #self._logger.debug('call return: %d' % ret)
            
            if ret == self.apache.WORKER_NOT_FOUND:
                raise Exception("Apache couldn't find worker %s. Check httpd.conf")
        except:
            self._logger.exception('Could not enable %s' % (server))
        finally:
            self._mutex.release()   
    
    
    def _changeWeight(self, server, weight):        
        assert self.apache is not None

        self._mutex.acquire()
        try:            
            ret = self.apache.set_worker_info("balancer://mycluster", "http://" + server.hostname + ":81", -1, int(weight * 100))
            #self._logger.debug('call return: %d' % ret)
            
            if ret == self.apache.WORKER_NOT_FOUND:
                raise Exception("Apache couldn't find worker %s. Check httpd.conf")
        except:
            self._logger.exception('Could not change weight %d to %s' % (int(weight * 100), server))
        finally:
            self._mutex.release()        
        
    
    def getWeights(self):
        '''
        Returns a tuple list: (server, weight)
        '''
        return self._weights[:]
    
    
    def balanceByPerformance(self, serverList=None):
        '''
        Will choose appropriate weights based on the performance given by freqCap.
        '''
        self._logger.info('Balancing by performance')
        perf_sum = 0.0
        weights = []
        
        if serverList is None:
            serverList = self.cluster.servers[Server.ON]
        
        for server in serverList:
            perf = server.energyModel.getPerf(server.dvfsCont.getFreqCap())
            perf_sum += perf
            weights.append((server, perf))        
        
        if perf_sum == 0.0: #shit happens...
            self._logger.warning('The rated performance for all servers is zero. No changes were made. The server list is: %s' % self.cluster.availableServers)
            return False
        
        for i in range(len(weights)):
            weights[i] = (weights[i][0], weights[i][1] / perf_sum)            
            self._changeWeight(weights[i][0] , weights[i][1])
        
        self._weights = weights


class LoadBalancerBuilder(Builder):
    
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = LoadBalancer
        Builder.__init__(self, targetClass)