'''
Created on Sep 23, 2010

@author: giulio
'''
import unittest

import sys, os
sys.path.append(os.path.abspath('..'))

from simulator.server import Server
from system.core import Core
from system.DVFSController import DVFSController
from system.processor import Processor

class ServerTest(unittest.TestCase):

    core = Core()
    proc = Processor()
    proc.cores = [core]
    server = Server()
    server.processor = proc
    server.processor.availableFreqs = [1.0]
    cont = DVFSController(server)
    server.dvfsCont = cont    
    server._status = Server.OFF
    server.WAKE_UP_TIME = 0
    
    def testTurnOn(self):                    
        self.server.turnOn()
        #if the server is already on, nothing should happen:
        self.server.turnOn()
    
    def testTurnOff(self):
        self.server._status = Server.ON
        self.server.turnOff()
        #if the server is already off, nothing should happen:
        self.server.turnOff()
        
    def testSwitching(self):
        '''
        Switching a server ON, then OFF then ON again
        '''
        self.server.turnOn()
        self.server.turnOff()
        self.server.turnOn()
        
    def testReadSensors(self):
        s = Server()
        core = Core()
        s.processor.cores.append(core)        
        core = Core()
        s.processor.cores.append(core)        
        s.updateSensors()
        '''
        self.assertEquals(s.cpuFanSpeed, 4440)
        self.assertEquals(s.processor.temperature, (42.0 + 43.0) / 2)
        self.assertEquals(s.processor.cores[0].temperature, 42.0)
        self.assertEquals(s.processor.cores[1].temperature, 43.0)
        '''

if __name__ == "__main__":
    unittest.main()