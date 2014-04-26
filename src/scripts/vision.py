'''
Created on Dec 15, 2010

@author: giulio
'''

import sys, os
sys.path.append(os.path.abspath('..'))

try:
    import Gnuplot
except ImportError:
    Gnuplot = None

from stats import file2data

REPLIED = 3
INCOMING = 4
QOS = 5

POOL = [REPLIED, INCOMING, QOS]

def main():
    filename = 'D:\\Giulio\\My Dropbox\\cluster\\SPACS_v0.6\\exps\\2011-04-23_12h48m00s\\monitor.txt'
    g = Gnuplot.Gnuplot(debug=0)
    window = 20
    
    data = file2data(25, filename)   
       
    avgs = [list() for i in range(len(POOL))]        
    avg = [0.0] * len(POOL)
    for i in range(len(data[0])):        
        for j in range(len(POOL)):        
            avg[j] += data[POOL[j]][i]
            
        if (i + 1) % window == 0:            
            for j in range(len(POOL)):        
                avg[j] /= window            
                avgs[j].append(avg[j])
            avg = [0.0] * len(POOL)
    
    
    #g.plot()  
    g('set grid')
    g('set y2tics')
    
    """
    pi1 = Gnuplot.Data(avgs[0], with_='steps')
    cmd1 = pi1.command()
    pi2 = Gnuplot.Data(avgs[1], with_='steps')
    cmd2 = pi2.command()
    pi3 = Gnuplot.Data(avgs[2], with_='steps')
    cmd3 = pi3.command()    
    g('plot %s, %s, %s axis x1y2' % (cmd1,cmd2,cmd3))
    """
    
    pi1 = Gnuplot.Data([avgs[1][i]/avgs[0][i] for i in range(len(avgs[0]))], with_='steps')
    cmd1 = pi1.command()
    pi2 = Gnuplot.Data(avgs[2], with_='steps')
    cmd2 = pi2.command()        
    g('plot %s, %s axis x1y2' % (cmd1,cmd2))
    
    raw_input()
if __name__ == '__main__':
    main()