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

def main():
    filename = '/home/giulio/Dropbox/labtempo_not_shared/traces/wc98_100.txt'
    g = Gnuplot.Gnuplot(debug=0)
    window = 20
    x_range = 2400
    x_start = 0  
    
    data = file2data(1, filename)[0]
    print 'Starting'
    
    
    try:
        g('set grid')
        while True:
            g('set xrange[%d:%d]' % (x_start, x_start + x_range))
                        
            avgs = [0.0] * (x_range / window)
            for i in range(x_start, min(x_start + x_range, len(data)), 1):
                avgs[(i - x_start) / window] += data[i]
            
            for i in range(x_range / window):
                avgs[i] = float(avgs[i]) / window
            
            plot_args = '"%s" w l' % (filename)
            #g.plot()  
            pi = Gnuplot.Data(zip(range(x_start, x_start + x_range, window), avgs), with_='steps')
            cmd = pi.command()
            #g.plot(pi)
            g('plot %s, %s lw 2' % (plot_args, cmd))
            input = raw_input()
            #if input == 'a':
            #    print 'left'
            
            x_start += window
    except KeyboardInterrupt:
        print 'Leaving...'

if __name__ == '__main__':
    main()