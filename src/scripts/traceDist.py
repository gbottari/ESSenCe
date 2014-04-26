'''
Created on Dec 15, 2010

@author: giulio
'''

from system.configReader import ConfigReader
from system.energyModel import getMaxPerformance

try:
    from Gnuplot import Gnuplot, Data
except ImportError:
    Gnuplot = None
from random import gauss

def readOutlineFile(filename):
    traceOutline = []        
    file = open(filename,'r')
    try:
        for line in file:
            x, y = line.split()
            traceOutline.append((int(x),float(y)))
    except:
        print 'Error reading file'
    finally:
        file.close()

    return traceOutline


def generateTrace(outline, maxRequests, stddev=10.00):
    trace = []
    for x, y in outline:
        for i in range(x):
            value = gauss(y * maxRequests, y * stddev)
            trace.append(value)
    return trace


def main():
    filename = '../tmp/config.txt'
    
    c = ConfigReader()
    c.parse(filename)
    cluster = c.readCluster()

    maxPerf = getMaxPerformance(cluster.availableServers)    
    
    outline = readOutlineFile('../tmp/outline.txt')
    trace = generateTrace(outline, maxPerf, 20)
        
    if Gnuplot is not None:
        data = Data(trace, with_='l')
        g = Gnuplot()
        g('set ytics 0, 100')
        g('set xtics 0, 20')
        g('set grid')
        g.plot(data)
        raw_input()
    
    file = open('../tmp/trace_gen.txt','w')
    for value in trace:
        file.write('%f\n' % value)
    file.close()

if __name__ == '__main__':
    main()