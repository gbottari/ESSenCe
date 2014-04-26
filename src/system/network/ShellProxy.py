'''
Created on Jul 15, 2011

@author: Giulio
'''
from system.network.ServerProxy import ServerProxy

class ShellProxy(ServerProxy):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
    
    def shell(self, cmd, block=True):
        '''
        Execute a shell command.
        @param cmd: a shell command list; e.g. ['echo', 'hello']
        @param block: block waits until the command is finished. On this case
        shell returns None
        '''
        raise NotImplementedError #must be overloaded