'''
Created on Oct 26, 2010

@author: giulio

Program that records the temperature for each throttling state, on each core.

Useful info:

On corei7:
time_to_get_hot = 90 #seconds, ~80 degrees
time_to_get_cool = 40 #seconds ~50 degrees
'''
import sys, os
sys.path.append(os.path.abspath('..'))

from system.processor import Processor
from subprocess import call
from time import sleep, time
from threading import Thread

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


def read_w83627ehf_isa(self, lines):
    '''
    Gets fan information. Returns a dict: {'cpu':<info>,'case':<info>}. 
    <info> is also a dict: {'rpm':<value>,'min':value,'div':value}
    
    #Expected input:
    w83627ehf-isa-<number>
    #0   1      2        3    4    5 6        7    8   9 10         11
    Case Fan:   <number> RPM  (min = <number> RPM, div = <number>)  <[situation]>
    CPU Fan:    <number> RPM  (min = <number> RPM, div = <number>)  <[situation]>
    '''
    result = {}
    for line in lines:
        if line.startswith('Case Fan:'):
            tokens = line.split()
            rpm = int(tokens[2])
            min = int(tokens[6])
            div = int(tokens[10])
            info = {'rpm':rpm,'min':min,'div':div}
            result['cpu'] = info
            
    return result


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
    proc = Processor()
    proc.detect()
    T_states = get_T_States(proc.cores[0]) #assume all cores have the same T-states
    
    print 'Starting...'
    
    for i in T_states:
        output = open('T%d.txt' % i,'w')
        
        print '-' * 30 
        print 'Setting T%d...' % i
        for j in range(proc.getCoreCount()):
            set_T_State(i,j)
            
        print 'Executing Stress...'   
        stress = Stress()
        stress.cmd(['stress', '--cpu', '50', '--timeout', '%ss' % experiment_interval])     
        stress.start()
        
        total_time = 0.0
        while stress.isAlive():
            t0 = time()  
            sleep(1)                      
            proc.updateTemp()
            elapsed = time() - t0
            total_time += elapsed
            string = ''
            output.write('%d' % int(total_time))
            for core in proc.cores:
                string += 'Core%d: %2.1f ' % (core.number,core.temperature)
                output.write(' %f' % core.temperature)
                
            output.write('\n')            
            print string                       
        
        output.close()
        for j in range(proc.getCoreCount()):
            set_T_State(0,j)
        
        print 'Cooling down...'
        sleep(cooldown_interval)

if __name__ == '__main__':
    main()