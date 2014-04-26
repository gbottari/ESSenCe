'''
Created on Nov 8, 2010

@author: giulio
'''
import xmlrpclib

#SERVER_IP = '200.20.15.226'
SERVER_IP = 'localhost'

def main():
    s = xmlrpclib.ServerProxy(uri='http://%s:8568' % SERVER_IP,allow_none=True)
    print 'Running'
    s.run_workgen()
    print 'Stopped'
    
if __name__ == '__main__':
    main()