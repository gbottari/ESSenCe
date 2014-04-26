'''
Created on Nov 8, 2010

@author: giulio

Server that provides a httperf service
'''

import sys, os
sys.path.append(os.path.abspath('..'))

from system.workloadGenerator import WorkloadGenerator
from SimpleXMLRPCServer import SimpleXMLRPCServer

RATE = 1000
CONNECTIONS = 99999999

# Create server
server = SimpleXMLRPCServer(("localhost", 8568))

# Registers the XML-RPC introspection functions system.listMethods, system.methodHelp and system.methodSignature
server.register_introspection_functions()

def run_workgen():
    wg = WorkloadGenerator()
    wg.setProgram('ping')
    wg.setProgramParameters(['www.google.com','-n','10'])
    wg._minExecTime = 0
    wg.start()
    return 0
    
# register
server.register_function(run_workgen)

# Run the server's main loop
try:
    print 'Use Control-C to exit'
    server.serve_forever()
except KeyboardInterrupt:
    print 'Exiting'