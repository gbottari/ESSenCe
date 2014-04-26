'''
Created on Sep 23, 2010

@author: giulio
'''
import unittest

import sys, os
sys.path.append(os.path.abspath('..'))

from system.DVFSController import DVFSController
from system.server import Server
from system.processor import Processor


class DVFSControllerTest(unittest.TestCase):

    def setUp(self):
        s = Server()        
        self.proc = Processor()
        s.processor = self.proc
        s.processor.availableFreqs = [1.0]
        self.controller = DVFSController(s)

    def testName(self):
        pass


if __name__ == "__main__":
    unittest.main()