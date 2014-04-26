'''
Created on Oct 26, 2010

@author: giulio
'''
import unittest

import sys, os
sys.path.append(os.path.abspath('..'))

from system.processor import Processor, InvalidDataError

class ProcTest(unittest.TestCase):


    def setUp(self):
        self.processor = Processor()
        
    
    def test_readCores_invalidData(self):
        self.assertRaises(InvalidDataError, self.processor._readCores, None)
        self.assertRaises(InvalidDataError, self.processor._readCores, '')
    
    
    def test_readCores(self):
        data = """cpu  2255 34 2290 22625563 6290 127 456
cpu0 1132 34 1441 11311718 3675 127 438
cpu1 1123 0 849 11313845 2614 0 18
intr 114930548 113199788 3 0 5 263 0 4 [... lots more numbers ...]
ctxt 1990473
btime 1062191376
processes 2915
procs_running 1
procs_blocked 0
"""
        self.processor._readCores(data)
        self.assertEquals(len(self.processor.cores), 2)        
        

    def test_readFreqs_invalidData(self):
        self.assertRaises(InvalidDataError, self.processor._readFreqs, None)
        self.assertRaises(InvalidDataError, self.processor._readFreqs, '')
    
    
    def test_readFreqs(self):
        data = """3600000 2089
3400000 136
3200000 34
3000000 67
2800000 172488
"""
        self.processor._readFreqs(data)
        freqs = [2800000, 3000000, 3200000, 3400000, 3600000]
        self.assertEquals(self.processor._availableFreqs, freqs)


if __name__ == "__main__":
    unittest.main()