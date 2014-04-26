'''
Created on Nov 10, 2010

@author: giulio
'''

import sys, os
sys.path.append(os.path.abspath('..'))

from SimpleXMLRPCServer import SimpleXMLRPCServer
from system.processor import Processor

# Create server
server = SimpleXMLRPCServer(("", 8568))

# Registers the XML-RPC introspection functions system.listMethods, system.methodHelp and system.methodSignature
server.register_introspection_functions()

myProc = Processor()
def getInfo():
    myProc.detect()
    print myProc
    return myProc



server.register_function(getInfo,'getInfo') 

try:
    print 'Use Control-C to exit'
    server.serve_forever()
except KeyboardInterrupt:
    print 'Exiting'