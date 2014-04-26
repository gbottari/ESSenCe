'''
Created on Nov 3, 2010

@author: giulio
'''
import sys, os
sys.path.append(os.path.abspath('..'))

from system.lm_sensors_reader import readSensors
from time import sleep

TIME = 5 * 60

def main():
    modules = readSensors()
    header = ''
    i = 0
    for module in modules:        
        for section in module['sections']:
            i += 1
            header += '#%d-%s ' % (i, section['name'])
    print header
    
    count = 0
    while count < TIME:
        modules = readSensors()
        line = ''        
        for module in modules:
            for section in module['sections']:
                line += str(section['value']) + ' '
        print line            
        sleep(1)
        count += 1
    

if __name__ == '__main__':
    main()