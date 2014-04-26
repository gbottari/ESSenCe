'''
Created on Jul 15, 2011

@author: Giulio
'''
from system.network.ServerProxy import ServerProxy
from xmlrpclib import ServerProxy as ServerProxy_xmlrpclib
from threading import Lock
from system.Builder import Builder

class XMLRPCProxy(ServerProxy):
    '''
    classdocs
    '''


    def __init__(self, addr, port):        
        ServerProxy.__init__(self)
        self._proxy = ServerProxy_xmlrpclib("http://%s:%d" % (addr,port))
        self._mutex = Lock()
        
        
    def __getattr__(self, name):
        '''
        Forwards attribute look-up to the proxy, making it possible to call methods directly,
        like: xmlrpc.remoteFunc().
        Also, uses a mutex to prevent concurrent access to the proxy.
        '''
        if hasattr(self._proxy, name):
            attr = getattr(self._proxy, name)
            
            def wrapped(*args, **kwargs):
                self._mutex.acquire()
                try:                    
                    retval = attr(*args, **kwargs)
                finally:
                    self._mutex.release()                            
                return retval
            
            return wrapped
        
        return super(XMLRPCProxy, self).__getattr__(name)


class XMLRPCProxyBuilder(Builder):
    
    def __init__(self):
        Builder.__init__(self, XMLRPCProxy)
        #option strings
        self.HOST = 'host'
        self.PORT = 'port'
    
    def build(self, cr):
        addr = cr.getValue(self.sectionName, self.HOST)
        port = cr.getValue(self.sectionName, self.PORT, int)        
        obj = self.targetClass(addr, port)

        return obj