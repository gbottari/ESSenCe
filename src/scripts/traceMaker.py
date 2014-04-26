'''
Created on Nov 12, 2010

@author: giulio
'''
import sys

def main():
    if len(sys.argv) < 3:
        print 'Usage:\n\
               python %s [f(x)] /*range*/[lower]:[upper] [-r]' % sys.argv[0]
        exit()
    
    #parsing
    formula = sys.argv[1]
    lower, upper = sys.argv[2].split(':') 
    lower = int(lower)
    upper = int(upper)
    
    values = range(lower,upper+1)
    for arg in sys.argv[1:]:    
        if arg == '-r':
            values.reverse()
    
    for x in values:
        print eval(formula)

if __name__ == '__main__':
    main()