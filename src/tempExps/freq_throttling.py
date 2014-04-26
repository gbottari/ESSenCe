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
from system.userspaceController import UserspaceController


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
    freqs = proc.availableFreqs()
    uc = UserspaceController(proc)
    uc.setup()
    
    print 'Starting...'
    
    for i in freqs:
        output = open('freq%d.txt' % i,'w')
        
        print '-' * 30 
        print 'Setting Frequency %d...' % i
        uc.setSpeed(i)
            
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
        uc.setSpeed(0)
        
        print 'Cooling down...'
        sleep(cooldown_interval)

if __name__ == '__main__':
    main()