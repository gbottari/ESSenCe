'''
Created on Sep 9, 2010

@author: giulio

TODO: separate the functions here in 'tools', into more specific files
'''
import subprocess
import socket
import logging

#Execution modes for execCmd()
LOCAL_EXEC = 0
SSH_EXEC = 1
REMOTE_DAEMON_EXEC = 2
KNOWN_EXEC_MODES = [LOCAL_EXEC, SSH_EXEC, REMOTE_DAEMON_EXEC]

REMOTE_DAEMON_MSG_CODE = 7
REMOTE_DAEMON_PORT = 27000

def linearInterpolation(x_list, y_list, x):
    """Gives the linear interpolated result of funtion f(x), where (x,y) is given by two lists."""
    if x > x_list[-1]:
        raise Exception("required (%f) is higher than maximum (%f)" % (x,x_list[-1]))
    
    index = 0
    for element in x_list:
        if element >= x:
            break
        index += 1
    
    if index < 1:
        return float(y_list[index])
    
    loX = x_list[index-1]
    hiX = x_list[index]
    loY = y_list[index-1]
    hiY = y_list[index]
    
    return float(loY - hiY) / (loX - hiX) * (x - loX) + loY


def diffLists(list1, list2):
    """Returns a list with the subtraction of two lists."""
    assert len(list1) == len(list2)
    return [list1[i] - list2[i] for i in range(len(list1))]


def diffDicts(dict1, dict2):
    """Returns a dict with the subtraction of two dicts."""
    return dict([ (key, dict1[key] - dict2[key]) for key in dict2.keys() ])


def sendMsg(host, msg, port):
    '''
    Sends a UDP message to dvs_daemon
    '''
    sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        #logging.debug('Sending: %s to %s' % (msg, host))
        sendSocket.connect((host, port))
        sendSocket.send(msg)
    except:
        logging.error('Could not send message: %s to host: %s' % (msg, host))
    finally:
        sendSocket.close()


def execCmd(cmd, dest=None, wait=True, shell=False, mode=LOCAL_EXEC):
    '''
    Executes a command, waits for it to finish and returns a string output.
    'cmd' is a list with the first element being the program, and the others its arguments.
    Set 'wait' to false if you don't want to wait for the process to finish. Note that the
    output produced by the process won't be returned if 'wait' is False.
    
    If a login is given, shell is forced False. 
    '''
    assert isinstance(cmd,list) #can't execute a None command
    assert mode in KNOWN_EXEC_MODES #needs to specify the correct mode
    
    if mode != LOCAL_EXEC:
        assert dest is not None #must know the destination
    
    if mode == SSH_EXEC:
        cmd[:0] = ['ssh', dest] #appends ssh to the command
        shell = False #forces shell to be false
    elif mode == REMOTE_DAEMON_EXEC:
        cmd[0] = '%d %s' % (REMOTE_DAEMON_MSG_CODE, cmd[0])
       
    if mode == REMOTE_DAEMON_EXEC:
        if wait: raise Exception('Cannot wait on daemon')
        sendMsg(dest, ' '.join(cmd), REMOTE_DAEMON_PORT)
    else: #both SSH and LOCAL
        if wait:
            p = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=shell)
            return p.communicate()[0]
        else:
            subprocess.Popen(cmd,shell=shell)
        

def readFile(filename):
    '''
    Returns the contents of a local file.
    '''
    assert filename is not None
    with open(filename,'r') as f:
        contents = f.read()
    return contents


if __name__ == '__main__':
    #test diffDicts
    d1 = {}
    d2 = {'la': [1.0,1.0,1.0]}
    print diffDicts(d1, d2)