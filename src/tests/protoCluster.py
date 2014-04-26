'''
Created on Oct 3, 2010

@author: Giulio
'''

from simulator.cluster import Cluster
from system.perfRegulator import PerfRegulator
from system.configurator import Configurator
from simulator.server import Server
from system.energyModel import EnergyModel
from system.DVFSController import DVFSController
from simulator.loadBalancer import LoadBalancer
from system.serviceMonitor import RequestMonitor
from system.service import RequestBuffer
from system.filters import DummyFilter

'''
Auxiliary Functions
'''
def joinServers(servers,cluster):
    for server in servers:
        cluster.joinCluster(server)


def createServer(name):
    server = Server()
    server._hostname = name
    
    energyModel = EnergyModel(server)
    server.energyModel = energyModel
    
    if name == 'ampere':
        server.processor.availableFreqs = [1.0,1.8,2.0]
        server.energyModel._idlePower = [66.3,70.5,72.7]
        server.energyModel._busyPower = [81.5,101.8,109.8]
        server.energyModel._peakPerformance = [99.8,179.6,199.6]
    elif name == 'coulomb':
        server.processor.availableFreqs = [1.0,1.8,2.0,2.2,2.4]
        server.energyModel._idlePower = [67.4,70.9,72.4,73.8,75.2]
        server.energyModel._busyPower = [75.2,89.0,94.5,100.9,107.7]
        server.energyModel._peakPerformance = [53.8,95.4,104.8,113.6,122.3]
    elif name == 'joule':
        server.processor.availableFreqs = [1.0,1.8,2.0,2.2]
        server.energyModel._idlePower = [66.6,73.8,76.9,80.0]
        server.energyModel._busyPower = [74.7,95.7,103.1,110.6]
        server.energyModel._peakPerformance = [51.2,91.2,101.4,111.4]
    elif name == 'ohm':
        server.processor.availableFreqs = [1.0,1.8,2.0,2.2,2.4,2.6]
        server.energyModel._idlePower = [65.8,68.5,70.6,72.3,74.3,76.9]
        server.energyModel._busyPower = [82.5,99.2,107.3,116.6,127.2,140.1]
        server.energyModel._peakPerformance = [99.4,177.4,197.2,218.0,234.6,255.2]
    elif name == 'hertz':
        server.processor.availableFreqs = [1.0,1.8,2.0,2.2,2.4]
        server.energyModel._idlePower = [63.9,67.2,68.7,69.9,71.6]
        server.energyModel._busyPower = [71.6,85.5,90.7,96.5,103.2]
        server.energyModel._peakPerformance = [53.6,92.9,103.4,112.4,122.8]
    else:
        raise Exception('No server with the name "%s" found' % name)
   
    cont = DVFSController(server)
    server.dvfsCont = cont 
        
    return server
        

def createCluster(servers):
    cluster = Cluster()
    lBalancer = LoadBalancer(cluster)
    #service = RequestBuffer()
    #cluster.service = service
    cluster.loadBalancer = lBalancer
    cluster._availableServers = servers
    for server in servers:
        cluster.servers[server.status].append(server)
    
    return cluster


'''
Setup Cluster
'''
cluster = Cluster()

ampere = Server()
coulomb = Server()
hertz = Server()
joule = Server()
ohm = Server()
servers = [ampere,coulomb,hertz,joule,ohm]

ampere._hostname = 'ampere'
coulomb._hostname = 'coulomb'
hertz._hostname = 'hertz'
joule._hostname = 'joule'
ohm._hostname = 'ohm'

joinServers(servers,cluster)

'''
Create Modules
'''
lBalancer = LoadBalancer(cluster)
filter = DummyFilter()
perfReg = PerfRegulator(cluster)
service = RequestBuffer()
serviceMonitor = RequestMonitor([service])
cluster.service = service
cluster.loadBalancer = lBalancer

'''
Setup Processors
'''
ampere.processor.availableFreqs = [1.0,1.8,2.0]
coulomb.processor.availableFreqs = [1.0,1.8,2.0,2.2,2.4]
hertz.processor.availableFreqs = [1.0,1.8,2.0,2.2,2.4]
joule.processor.availableFreqs = [1.0,1.8,2.0,2.2]
ohm.processor.availableFreqs = [1.0,1.8,2.0,2.2,2.4,2.6]

'''
Setup DVFS Controllers
'''
for server in cluster._availableServers:
    cont = DVFSController(server)
    server.dvfsCont = cont

'''
Setup emodels
'''
for server in cluster._availableServers:
    emodel = EnergyModel(server)
    server.energyModel = emodel

ampere.energyModel._idlePower = [66.3,70.5,72.7]
coulomb.energyModel._idlePower = [67.4,70.9,72.4,73.8,75.2]
hertz.energyModel._idlePower = [63.9,67.2,68.7,69.9,71.6]
joule.energyModel._idlePower = [66.6,73.8,76.9,80.0]
ohm.energyModel._idlePower = [65.8,68.5,70.6,72.3,74.3,76.9]

ampere.energyModel._busyPower = [81.5,101.8,109.8]
coulomb.energyModel._busyPower = [75.2,89.0,94.5,100.9,107.7]
hertz.energyModel._busyPower = [71.6,85.5,90.7,96.5,103.2]
joule.energyModel._busyPower = [74.7,95.7,103.1,110.6]
ohm.energyModel._busyPower = [82.5,99.2,107.3,116.6,127.2,140.1]

ampere.energyModel._peakPerformance = [99.8,179.6,199.6]
coulomb.energyModel._peakPerformance = [53.8,95.4,104.8,113.6,122.3]
hertz.energyModel._peakPerformance = [53.6,92.9,103.4,112.4,122.8]
joule.energyModel._peakPerformance = [51.2,91.2,101.4,111.4]
ohm.energyModel._peakPerformance = [99.4,177.4,197.2,218.0,234.6,255.2]


configurator = Configurator(cluster, filter)
configurator.setEfficientServerList(servers[:])
configurator.gamma = 1.0