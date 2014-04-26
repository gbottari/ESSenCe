'''
Created on Jul 15, 2011

@author: Giulio
'''
from system.network.ShellProxy import ShellProxy
from system.tools import execCmd, LOCAL_EXEC

class SH(ShellProxy):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        ShellProxy.__init__(self)
                
        
    def shell(self, cmd, shell= False, block=True):
        '''
        Execute a shell command.
        @param cmd: a shell command string
        @param block: block waits until the command is finished. On this case
        shell returns None       
        '''
        # TODO: what about shell=True?        
        return execCmd(cmd, dest=None, wait=block, shell=shell, mode=LOCAL_EXEC)
    
    
    def connected(self):
        return True # no reason to fail, ever