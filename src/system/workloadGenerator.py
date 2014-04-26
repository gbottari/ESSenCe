'''
Created on Oct 16, 2010

@author: Giulio
'''
from time import time
from sysThread import Thread
from server import Server

class WorkloadGenerator(Server, Thread):
    '''
    classdocs
    '''
    
    def __init__(self):
        Server.__init__(self)
        self._detectProcessor = False
        Thread.__init__(self)
        self._startTime = 0
        self._finishTime = 0
        self._wgProgram = ''
        self.initcmd = None
        self._wgParameters = [] #parameters to start the workload generator
        self._minExecTime = 5
        self._wgPath = ''
        self._dump = None #command dump
        self._performedCleanUp = False
   
   
    def _setup(self):
        if not self._performedSetup:
            self._logger.info('Setting up %s...' % self)
            
            self.detect()
                        
            assert self._status == Server.ON #guarantees that the server is online first           
            
            #Mounts /cluster
            self._logger.info('Mounting /cluster...')
            try:
                cmd = ['mount','-a']
                #execCmd(cmd, dest=self._sshLogin, wait=True, mode=SSH_EXEC)
                self._proxy.shell(cmd, block=True)
            except:
                self._logger.error('Could not mount /cluster')
                raise
            
            assert len(self._wgProgram) > 0
            
            if self.initcmd is not None:
                self._logger.info('Sending init command...')
                self._proxy.shell([self.initcmd])
            self._performedSetup = True  
        else:
            self._logger.warning('Already performed setup on %s' % self)


    def cleanUp(self):               
        if self._performedSetup and not self._performedCleanUp:
            self._logger.info('Cleaning up...')            
            #execCmd(['killall',self._wgProgram], dest=self._sshLogin , mode=SSH_EXEC)
            self._proxy.shell(['killall',self._wgProgram])
            self._performedCleanUp = True
    
    
    def run(self):     
        try:
            self._setup()
            
            self._logger.info('Starting workload...')
            
            #cmd = [self._wgPath + self._wgProgram]
            cmd = ['cd','%s' % self._wgPath,'&&', './%s' % self._wgProgram]
            cmd.extend(self._wgParameters)           
            
            self._startTime = time()
                    
            #self._dump = execCmd(cmd, dest=self._sshLogin, mode=SSH_EXEC) #block-waiting
            self._dump = self._proxy.shell(cmd)
            
            self._finishTime = time()        
            elapsed_time = self._finishTime - self._startTime
        
            if elapsed_time < self._minExecTime:
                '''
                Means that the command line failed somehow. Either the remote machine
                couldn't be reached, or the workload program failed. Another possibility
                is that the trace file is bugged or not found.
                '''
                self._logger.critical('Workload Finished too soon: elapsed time = %d < min_time = %d' %\
                                      (elapsed_time, self._minExecTime))
                self._logger.info('Command dump:\n%s' % self._dump)
                raise Exception('Workload Failed!')           
        
        except Exception:
            self._logger.exception('%s has failed!' % type(self).__name__)
            raise
        finally:
            self.cleanUp()
            self._logger.warning('%s has stopped' % type(self).__name__)
       
        
    def stop(self):
        Thread.stop(self)
        self.cleanUp()
            
            
    def getFinishTime(self):
        if self._finishTime != 0:
            return self._finishTime

        return self.getStartTime()
    
    
    def getStartTime(self):
        return self._startTime        
    
        
    def setProgram(self, program):
        self._wgProgram = program
            
        
    def setProgramParameters(self, par):
        self._wgParameters = par       
        
    @property
    def executionDump(self):
        return self._dump