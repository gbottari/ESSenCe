'''
Created on Nov 8, 2010

@author: Giulio

Runs a thorough analysis of temperature and performance for every combination of P-State and T-State.
To do this, it communicates with a workload server.
'''
import sys, os
sys.path.append(os.path.abspath('..'))

from system.server import Server
from time import sleep, time
from threading import Thread
from system.userspaceController import UserspaceController
import xmlrpclib

#SERVER_IP = '200.20.15.226'
SERVER_IP = 'localhost'

def get_T_States(core):
    '''
    Returns the number of throttling states for that core.
    Assumes that starts from T0
    '''
    f = open('/proc/acpi/processor/CPU%d/throttling' % core.number)
    count = int(f.readline().split()[-1])
    f.close()
    return range(count)


def set_T_State(t, coreNumber):
    f = open('/proc/acpi/processor/CPU%d/throttling' % coreNumber, 'w')
    f.write(str(t))
    f.close()
       

#CONSTS
cooldown_interval = 5 * 60 #seconds ~53 degrees
experiment_interval = 600 #seconds


def main():
    workloadServer = xmlrpclib.ServerProxy('http://%s:8568' % SERVER_IP)
    server = Server()
    server.processor.detect()
    P_States = server.processor.availableFreqs().reverse()
    T_States = get_T_States(server.processor.cores[0]) #assume all cores have the same T-states
    uc = UserspaceController(server.processor)
    uc.setup()
    
    print 'Starting...'
    
    for P in range(P_States):
        for T in range(T_States):
            output = open('P%d:T%d.txt' % (P,T),'w')
            
            print '-' * 30 
            print 'Setting P%d:T%d...' % (P,T)
            uc.setSpeed(P_States[P])
            for core in server.processor.cores:
                set_T_State(T_States[T], core.number)
                
            print 'Executing Workload Generator...'   
            output = workloadServer.run_workgen()
            
            thread = Thread(target=workloadServer.run_workgen, args=())
            
            total_time = 0.0
            while thread.isAlive():
                t0 = time()  
                sleep(1)                      
                server.updateSensors()
                elapsed = time() - t0
                total_time += elapsed
                string = '%d ' % int(total_time)
                output.write(string)
                for core in server.processor.cores:
                    string += 'Core%d: %2.1f ' % (core.number,core.temperature)
                    output.write('%f ' % core.temperature)
                    
                output.write('\n')            
                print string                       
            
            output.close()
            
            print 'Cooling down...'
            uc.setSpeed(P_States[0])
            for core in server.processor.cores:
                set_T_State(T_States[0], core.number)            
            
            sleep(cooldown_interval)

if __name__ == '__main__':
    main()