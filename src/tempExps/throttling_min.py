'''
Created on Oct 26, 2010

@author: giulio

Program that records the temperature for each throttling state, on each core.
This one will test only the configuration Pn:Tn, which means minimum frequency
and max throttling state.

Useful info:

On corei7:
time_to_get_hot = 90 #seconds, ~80 degrees
time_to_get_cool = 40 #seconds ~50 degrees
'''
import sys, os
sys.path.append(os.path.abspath('..'))

from subprocess import call
from time import sleep, time
from threading import Thread
from system.userspaceController import UserspaceController
from system.server import Server

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


class Stress(Thread):
    
    def __init__(self):
        Thread.__init__(self)
    
    def cmd(self, cmd):
        self._cmd = cmd
    
    def run(self):
        call(self._cmd)
        

#CONSTS
cooldown_interval = 3 * 60 #seconds ~53 degrees
experiment_interval = 600 #seconds


def main():
    server = Server()
    server.processor.detect()
    freqs = server.processor.availableFreqs()
    uc = UserspaceController(server.processor)
    uc.setup()
    T_states = get_T_States(server.processor.cores[0]) #assume all cores have the same T-states
    
    print 'Starting...'
    
    i = T_states[-1] #max throttling
    output = open('Pn_T%d.txt' % i,'w')
    
    print '-' * 30 
    print 'Setting T%d...' % i
    for j in range(server.processor.coreCount):
        set_T_State(i,j)
    
    print 'Setting Pn...'
    uc.setSpeed(freqs[0])
    
    print 'Executing Stress...'   
    stress = Stress()
    stress.cmd(['stress', '--cpu', '50', '--timeout', '%ss' % experiment_interval])     
    stress.start()
    
    total_time = 0.0
    while stress.isAlive():
        t0 = time()  
        sleep(1)                      
        server.updateSensors()
        elapsed = time() - t0
        total_time += elapsed
        string = ''
        output.write('%d' % int(total_time))
        for core in server.processor.cores:
            string += 'Core%d: %2.1f ' % (core.number,core.temperature)
            output.write(' %f' % core.temperature)
            
        output.write('\n')            
        print string                    
    
    output.close()
    for j in range(server.processor.coreCount):
        set_T_State(0,j)
    
    print 'Cooling down...'
    sleep(cooldown_interval)

if __name__ == '__main__':
    main()