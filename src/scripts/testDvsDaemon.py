'''
Created on Dec 4, 2010

@author: Giulio
'''

import socket

def main():
    HOST = '192.168.1.9'    # The remote host
    PORT = 27000              # The same port as used by the server
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((HOST, PORT))
    print 'Sending'
    s.send('7 echo "ROAR!!!" > mighty_test.txt')
    s.close()
    print 'Done'


if __name__ == '__main__':
    main()