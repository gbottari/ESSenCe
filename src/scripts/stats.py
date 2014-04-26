'''
Created on Nov 11, 2010

@author: giulio

Read statistics from a column divided file.
'''

import sys


def file2data(fieldCount, filename, skipLines=0):
    '''
    Returns a list of arrays, one for each column
    '''
    assert filename is not None
    
    result = [list() for i in range(fieldCount)]
    
    with open(filename,'r') as f:
        for line in f.readlines():
            if skipLines > 0:
                skipLines -= 1
            else:
                if line and len(line) > 0 and line[0] != '#': #skip comments
                    tokens = line.split()
                    for i in range(len(tokens)):
                        result[i].append(float(tokens[i]))
    return result


def getColumns(filename):
    with open(filename,'r') as f:
        line = f.readline()
        
        #skip all comments
        while line[0] == '#':
            line = f.readline()
        
        fields = line.split()
        fieldCount = len(fields)   
        
    return fieldCount


def getAvg(data):
    results = []
    for i in range(len(data)):
        results.append(0.0)
    
    #Somar valores
    for i in range(len(data)):
        for j in range(len(data[i])):
            results[i] += float(data[i][j])
    
    #Dividir pelo total
    for i in range(len(data)):
        results[i] /= len(data[i])

    return results


def getSum(data):
    results = []
    for i in range(len(data)):
        results.append(0.0)
    
    #Somar valores
    for i in range(len(data)):
        for j in range(len(data[i])):
            results[i] += float(data[i][j])

    return results


def getLessThan(data, index, reference):
    result = 0
    
    for i in range(len(data[index])):
        if data[index][i] < reference:
            result += 1

    return float(result) / len(data[index])


def getStddev(data, avgs):
    results = []
    for i in range(len(data)):
        results.append(0.0)
    
    #Somar valores
    for i in range(len(data)):
        for j in range(len(data[i])):
            results[i] += (float(data[i][j]) - avgs[i]) ** 2
    
    #Dividir pelo total
    for i in range(len(data)):
        results[i] /= len(data[i])

    return results    


def printResults(results):
    for i in range(len(results)):
        print '%d: %f' % (i+1, results[i])


def print_usage():
    print "%s filename [mode]" % sys.argv[0]


def main():
    #Modes:
    AVG = 0
    STDDEV = 1
    LESS_THAN = 2
    SUM = 3    
    MODES = {'avg': AVG, 'stddev': STDDEV, 'sum': SUM, 'lt': LESS_THAN}

    if len(sys.argv) < 2:
        print_usage()
        return
    filename = sys.argv[1]

    if len(sys.argv) >= 3:
        mode = MODES[sys.argv[2]]
    else:
        mode = AVG
    
    fields = getColumns(filename)
    data = file2data(fields, filename)

    results = None
    if mode == AVG:
        results = getAvg(data)
    elif mode == STDDEV:
        avg = getAvg(data)
        results = getStddev(data,avg)
    elif mode == SUM:
        results = getSum(data)
    elif mode == LESS_THAN:
        index = int(sys.argv[3])
        reference = float(sys.argv[4])        
        print getLessThan(data, index-1, reference)
        return
        
    printResults(results)

if __name__ == '__main__':
    main()