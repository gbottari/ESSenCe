'''
Created on Jul 15, 2011

@author: Giulio
'''

import logging
from system.network.ServerProxy import ServerProxy

from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, timeout

UDP_MODE = SOCK_DGRAM
TCP_MODE = SOCK_STREAM


class SocketProxy(ServerProxy):
    # TODO: the way this class works is somewhat confusing
    
    RCV_BUFFER_SIZE = 512

    def __init__(self, ip, port, mode=UDP_MODE):
        super(SocketProxy, self).__init__()
        self._socket = None #keep it here
        self._ip = ip
        self._port = port
        self._mode = mode
        self._socket = socket(AF_INET, mode)
        #self._socket.settimeout(3)
        self._setup = False
        self._logger = logging.getLogger(type(self).__name__)
       
    
    def send(self, msg):
        try:
            #logging.debug('Sending: %s to %s' % (msg, host))
            self._socket.connect((self._ip, self._port))
            self._socket.send(msg)
        except:
            self._logger.exception('Could not send message: %s to host: %s' % (msg, self._ip))
    
    
    def receive(self):
        if not self._setup:     
            if self._mode == UDP_MODE:
                self._socket.bind((self._ip, self._port))                
            else:
                self._socket.connect((self._ip, self._port))
            self._setup = True
        data = None
        try:
            data = self._socket.recv(self.RCV_BUFFER_SIZE)
        except timeout:
            self._logger.exception('Receive timed out!')
            raise
        return data


    def __del__(self):
        self.close()
 
            
    def close(self):
        if self._socket:
            self._socket.close()