'''
Created on Dec 3, 2010

@author: giulio
'''

import socket

def main():

    HOST = '192.168.1.9'    # The remote host
    PORT = 27000              # The same port as used by the server
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((HOST, PORT))
    print 'Sending'
    s.send('Hello, world')
    s.close()
    print 'Done'

if __name__ == '__main__':
    main()