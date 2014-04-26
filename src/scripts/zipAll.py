'''
Created on Mar 15, 2011

@author: giulio
'''

import sys, os
#from tools import execCmd

def findMatchingFiles(dir, match):
    results = []
    
    for data in os.walk(dir):        
        for file in data[2]:   
            if file == match >= 0:
                results.append(os.path.join(data[0],file))  
        
    return results
    

def main():
    
    if len(sys.argv) < 3:
        print 'Usage:'
        print 'python %s {dir} {file}' % (sys.argv[0])
        return
    
    dir = sys.argv[1]
    match = sys.argv[2]
    
    for file in findMatchingFiles(dir, match):
        os.system('gzip %s' % file)

if __name__ == '__main__':
    main()