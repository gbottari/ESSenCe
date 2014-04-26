'''
Created on Feb 3, 2011

@author: giulio
'''

from sys import stdin
from time import sleep
import os
import fcntl

# make stdin a non-blocking file
fd = stdin.fileno()
fl = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

LOOP_PERIOD = 5
DEADLINE = 1000 * 1000 * 1000 #us


def parse(lines):
    """
    Parses a list of strings from Apache's access_log into useful statistics.
    """    
    replied = len(lines)
    avg_delay, lost = 0, 0
    qos = 1.0
    
    if replied != 0:
        for line in lines:
            line.strip() #remove leading and trailing spaces
            """
            Each line has the following fields:
            [status code] [reply time (seconds since epoch)] [source IP] [source url] [source query] [serving delay]
            
            e.g.:
            200 1296756182 192.168.10.2 /home.php ?N=192 11045
            200 1296756183 192.168.10.2 /home.php ?N=192 230036
            200 1296756183 192.168.10.2 /home.php ?N=192 230684
            """
            status, time, sourceIP, url, query, delay = line.split()
            
            time = int(time)
            delay = int(delay)
            
            if delay > DEADLINE:
                lost += 1
            avg_delay += delay
        avg_delay /= replied
        qos = (replied - lost) / replied

    return {'replied': replied, 'delay' : avg_delay, 'qos' : qos, 'lost': lost}


def main():
    try:
        while True:            
            print 'Reading...' * 5
            buffer = []
            while True:                
                line = None
                try:
                    line = stdin.readline()
                except: #an exception may be raised if the stdin isn't ready
                    pass #swallow the exception             
                if line is None: #if couldn't read a line, break and wait for the buffer to fill
                    break
                buffer.append(line)
            sleep(LOOP_PERIOD)
            
            info = parse(buffer)
            print 'replied=%d, delay=%f, qos=%f' % \
            (info['replied'], info['delay'], info['qos'])
    except KeyboardInterrupt:
        print 'Leaving...'        


if __name__ == '__main__':
    main()