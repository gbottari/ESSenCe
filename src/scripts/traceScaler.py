'''
Created on Nov 18, 2010

@author: giulio
'''

import sys, os
sys.path.append(os.path.abspath('..'))

from system.energyModel import getMaxPerformance


def scale(data, servers, maxUtil=0.90, minPerf=0):
    '''
    Scales a trace based on the maximum load for the cluster
    '''    
    trace_min, trace_max = min(data), max(data)
    maxPerf = getMaxPerformance(servers) * 0.90
    
    #scales the trace file
    for i in range(len(data)):
        data[i] = (data[i] - trace_min) / (trace_max - trace_min) * (maxPerf - minPerf) + minPerf
        

def get_min_max(filename):
    min = float('inf')
    max = -float('inf')
    with open(filename) as f:
        for line in f.readlines():
            value = float(line)
            if value < min:
                min = value
            if value > max:
                max = value
    return (min,max)


def main():
    if len(sys.argv) < 4:
        print 'python %s filename target_min target_max [-int]' % sys.argv[0]
        return
    
    filename = sys.argv[1]
    convert_to_int = False
    if len(sys.argv) >= 5:
        convert_to_int = sys.argv[4] == '-int'
    
    min, max = get_min_max(filename)
    target_min, target_max = float(sys.argv[2]), float(sys.argv[3])
    assert target_max > target_min
    
    with open(filename,'r') as f:
        for line in f.readlines():
            value = float(line)
            scaled_value = (value - min) / (max - min) * (target_max - target_min) + target_min
            if convert_to_int:
                scaled_value = int(scaled_value)
            print str(scaled_value)
    

if __name__ == '__main__':
    main()