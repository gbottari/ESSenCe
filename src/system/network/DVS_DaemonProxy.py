'''
Created on Jul 15, 2011

@author: Giulio
'''
from system.network.SocketProxy import SocketProxy, UDP_MODE
from system.network.ShellProxy import ShellProxy


class DVS_DaemonProxy(SocketProxy, ShellProxy):
    '''
    classdocs
    '''

    SHELL_CODE = 7
    SET_FREQ_CODE = 3
    MINIMUM_GRANULARITY = 3 # MHz
        

    def __init__(self, ip, port):
        '''
        Constructor
        '''
        SocketProxy.__init__(self, ip, port, UDP_MODE)
        ShellProxy.__init__(self)
    
    
    def shell(self, cmd, block=True):
        '''
        @warning: block has no effect on this implementation
        '''
        cmd[0] = '%d %s' % (self.SHELL_CODE, cmd[0])
        msg = ' '.join(cmd)
        self.send(msg)
        
        
    def setFreq(self, freq):
        msg = '%d %d' % (self.SET_FREQ_CODE, int(freq / 1000.0))
        self.send(msg)
    
    #TODO: dvs_daemon has other uses like suspend and etc
    #TODO: it would be nice to implement a stop/start command