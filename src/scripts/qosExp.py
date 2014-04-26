'''
Created on Nov 4, 2010

@author: giulio

This experiment tries to control the QoS using the following approach:
    replied = lost / (1 - QoS_target)
'''

import sys, os
sys.path.append(os.path.abspath('..'))

from system.configReader import ConfigReader
from system.tools import readFile
from system.continuousController import ContinuousController
from system.deadzoneController import DeadzoneController
from time import sleep

LOST_FILENAME = '/mnt/ram/lost.txt'
REPLIED_FILENAME = '/mnt/ram/replied.txt'
INFO_FILENAME = '/mnt/ram/info.txt'
QOS_TARGET = 0.95
ACTUATE = 1
ALPHA = 0.8
DELTA = 0.03

def main(argv):
    config = ConfigReader()
    config.parse('config.txt')
    cluster = config.readCluster()
    server = cluster._availableServers[0]
    server.processor.detect()
    
    controller = ContinuousController(server.processor)
    controller._setup()
    dz = DeadzoneController()
    dz.setDeadzone((QOS_TARGET - 0.03, QOS_TARGET + 0.03))
    dz.setPoint(QOS_TARGET)
    
    lost_min = server.energyModel.peakPerf[0] / (1 - QOS_TARGET)
    
    time = int(argv[0])
    
    count = 0
    accLost, oldaccLost = 0.0, 0.0
    accReplied, oldaccReplied = 0.0, 0.0
    qos, qos_avg = 1.0, 1.0
    lost_avg = 0.0
    
    print '#1:Time 2:QoS 3:Lost 4:Frequency 5:QoS_Avg 6:Lost_Avg'
    
    while count < time:
        tmp = readFile(LOST_FILENAME)
        if len(tmp) > 0: accLost = int(tmp)
        tmp = readFile(REPLIED_FILENAME)
        if len(tmp) > 0: accReplied = int(tmp)
        
        if count > 0:
            lost = accLost - oldaccLost
            lost_avg = ALPHA * max(lost_min, lost) + (1 - ALPHA) * lost_avg
            
            replied = accReplied - oldaccReplied
            if replied > 0.0:
                qos = float(replied - lost) / replied
                
            qos_avg = ALPHA * qos + (1 - ALPHA) * qos_avg
            
            action = dz.action(qos_avg)
            if action != 0 and (count % ACTUATE == 0):            
                target_replied = lost_avg / (1.0 - QOS_TARGET)            
                freq = server.energyModel.getFreq(target_replied)
                controller.setSpeed(freq)
            
            print '%3d %1.3f %3.0f %1.3f %1.3f %3.0f' % (count, qos, lost, controller.getFreqCap() / 1000000.0, qos_avg, lost_avg)
               
        oldaccReplied = accReplied
        oldaccLost = accLost
        
        sleep(1)
        count += 1  
    controller.stop()
    
if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print 'Exiting...'