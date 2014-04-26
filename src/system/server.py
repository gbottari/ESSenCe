'''
Created on Sep 9, 2010

@author: giulio
'''

import logging
from processor import Processor
from time import sleep
from tools import execCmd
from lm_sensors_reader import readSensors
from sysObject import Object
from network.SSH import SSH
from system.Builder import Builder
from system.energyModel import EnergyModelBuilder

DVS_DAEMON_NAME = 'dvs_daemon_giulio'

class Server(Object):
    '''
    Represents a worker machine.
    When the 
    '''
    
    OFF = 0
    ON = 1
    TURNING_OFF = 2
    TURNING_ON = 3
    STATUSES = [OFF,ON,TURNING_OFF,TURNING_ON]
    STAT_TO_NAME = {OFF: 'off', ON: 'on', TURNING_OFF: 'turning off', TURNING_ON: 'turning on'}

    POOLING_TIME = 1 #time to send again a switch on/off message
    SWITCH_TIMEOUT = 15 * POOLING_TIME #time to consider either switching on or off as failed
    

    def __init__(self):
        self._hostname = 'server'
        self._IP = None
        self._macAddr = None #MAC address for Wake on LAN
        self._status = Server.OFF #assumes that the server is offline at first
        self.processor = Processor()
        self.processor.server = self
        self.energyModel = None
        self.dvfsCont = None
        self._sensorsInfo = None
        self._cpuFanSpeed = None
        self._wakeupCmd = 'ether-wake'
        self._eth = None #network interface number
        self._performedSetup = False
        self._apachePath = '/usr/local2/apache2/bin/'
        self._logger = logging.getLogger(type(self).__name__)
        self._detectProcessor = True
        self.proxy = None
        self.sleep = sleep
        
    
    def __repr__(self):
        return self._hostname

    
    def updateSensors(self):
        sensors = readSensors(self.proxy)
        for module in sensors:
            for section in module['sections']:
                if section['quantity'] == '\xb0C': # temperature
                    print 'Temperature'
                elif section['quantity'] == 'RPM': # fan speed
                    print 'Fan Speed'
                elif section['quantity'] == 'V': # voltage
                    print 'Voltage'
                else:
                    print 'Unknown'
        """
        for module in self._sensorsInfo:
            if module['name'].startswith('k8temp-pci'):
                accTemp = 0.0               
                for section in module['sections']:
                    number = int(section['name'].split()[0][4:])
                    temp = section['value']
                    self.processor.cores[number].temp = temp
                    accTemp += temp
                self.processor.temp = accTemp / len(self.processor.cores)
            elif module['name'].startswith('coretemp-isa'):
                accTemp = 0.0
                for section in module['sections']:
                    number = int(section['name'].split()[1])
                    temp = section['value']
                    self.processor.cores[number].temp = temp
                    accTemp += temp
                self.processor.temp = accTemp / len(self.processor.cores)
            '''
            elif module['name'].startswith('w83627ehf-isa'):
                for section in module['sections']:
                    if section['name'] == 'CPU Fan':
                        self._cpuFanSpeed = section['value']
            '''
        """
    '''
    def getCaseFanSpeed(self):
        assert self._sensorsInfo is not None
        if not self._sensorsInfo.has_key('Case Fan'): return None
        return self._sensorsInfo['Case Fan']
    '''
    
    def detect(self):
        online = self._heartBeat()
        if not online:
            self._logger.warning('%s is not online, attempting to turn it on...' % self)
            if not self.turnOn():
                self._logger.error('%s is probably turned off' % self)
                raise Exception('Server offline: %s' % self)
        
        self._status = Server.ON #if it was already on, update the status variable
        self._hostname = self._getHostname()
        
        if self._detectProcessor:
            self.processor.detect()
               
    
    def turnOn(self):
        "Turning a server on involves the following steps:\
         1. Issue a wake up command;\
         3. Wait a few seconds;\
         2. Poll the machine for replies;\
         4. If the machine doesn't reply, go back to step 1;"
        #if not (self._status == Server.OFF): return True
        self._status = Server.TURNING_ON
        
        count = 0
        while not self._heartBeat() and (count < Server.SWITCH_TIMEOUT):
            self._wakeup()
            self.sleep(self.POOLING_TIME)
            count += 1
        
        if (count == Server.SWITCH_TIMEOUT):
            self._logger.critical('Could not wake up %s.' % self._hostname)  
            return False
        else:
            self._status = Server.ON            
            self._logger.info('%s is now ready.' % repr(self))

        return True
    
    
    def turnOff(self):
        '''
        Turning a server off involves the following steps:\
        1. Issue a suspend command;\
        3. Wait a few seconds;\
        2. Poll the machine for replies;\
        4. If the machine replies, go back to step 1;
        '''
        self._status = Server.TURNING_OFF
        
        count = 0
        while self._heartBeat() and (count < Server.SWITCH_TIMEOUT):
            self._suspend()
            self.sleep(self.POOLING_TIME)
            count += 1
        
        if (count == Server.SWITCH_TIMEOUT):
            self._logger.critical('Could not suspend %s' % self._hostname)
            return False
        else:
            self._logger.info('%s is now off.' % self._hostname)
            self.processor.util = 0.0
            self._status = Server.OFF
        
        return True
    
    
    def _heartBeat(self):
        '''
        This method will probe the Server for its status, using ping.
        If the server doesn't respond, the function returns FALSE.
        
        Expected output:
        PING 200.20.15.218 (200.20.15.218) 56(84) bytes of data.

        --- 200.20.15.218 ping statistics ---
        # 1       2            3 4         5  6      7     8    9
        1 packets transmitted, 1 received, 0% packet loss, time 0ms
        rtt min/avg/max/mdev = 0.046/0.046/0.046/0.000 ms
        '''
        output = execCmd(['ping','-c','1','-q','-W','1',self._IP]) #send one request
        lines = output.splitlines()
        tokens = lines[3].split()
        replied = int(tokens[3])
        return replied > 0
    
    
    def _wakeup(self):
        '''
        Uses etherwake to wake up the server:
        
        etherwake -i ethX MAC_ADDR
        
        where ethX is the interface which communicates with the server 
        '''
        assert self._macAddr is not None
        output = ''
        try:
            output = execCmd([self._wakeupCmd,'-i', 'eth%d' % self.eth, self._macAddr])
        except:
            self._logger.critical('%s command failed. Output is: %s' % (self._wakeupCmd, output))
            raise               

        
    def _suspend(self):
        '''
        Start the suspend-to-ram process immediately.
        '''
        self._proxy.shell(['echo mem > /sys/power/state'],block=False)
        
        
    def _getHostname(self):
        '''
        An alternative (that takes longer): 'dnsdomainname -A'
        '''
        hostname = self._proxy.shell(['hostname'],block=True)
        if not hostname:
            raise Exception('Could not obtain hostname')
        return hostname[:-1] #last char is a \n        
    
    
    def _setup(self):
        '''
        Setup the server when a fresh boot (restart) is performed.
        Setting up includes:
        * Turn Apache on
        * Setup dvfs controller
        * Start dvs_daemon
        * Mount /cluster partition
        '''
        
        def getRunningProcsCount(name):
            '''
            Returns how many processes with 'name' are currently running
            '''
            output = self._proxy.shell(['ps -C %s' % name], block=True)
            return len(output.splitlines()) - 1
            
        if not self._performedSetup:
            assert self._status == Server.ON
            
            self._logger.info('Setting up %s...' % repr(self))
            
            #Starts cpufreq-stats module
            #ENHANCEMENT: verify that this module is down
            self._logger.info('Starting cpufreq-stats...')
            try:                
                self._proxy.shell(['modprobe','cpufreq-stats'], block=True)
            except:
                self._logger.error('Could not start cpufreq-stats')
                raise
            
            #Mounts /cluster
            #ENHANCEMENT: verify that it's not mounted
            self._logger.info('Mounting /cluster...')
            try:                
                self._proxy.shell(['mount','-a'], block=True)
            except:
                self._logger.error('Could not mount /cluster')
                raise            

            #Starts Apache
            #ENHANCEMENT: verify that Apache is down
            self._logger.info('Starting Apache at %s...' % repr(self))
            dump = ''
            try:
                dump = self._proxy.shell([self._apachePath + 'apachectl', 'start'], block=True)
            except:
                self._logger.exception("Could not start Apache at %s. Command dump: '%s'" % (repr(self), dump))
                raise
            
            #Starts DVS Daemon
            self._logger.info('Starting DVS daemon at %s...' % repr(self))
            output = ''
            try:
                procs = getRunningProcsCount(DVS_DAEMON_NAME)
                if procs > 0:                    
                    self._proxy.shell(['killall',DVS_DAEMON_NAME], block=True)
                    procs = getRunningProcsCount(DVS_DAEMON_NAME)
                    if procs != 0:
                        raise Exception("Can't kill all instances of %s. Detected instances = %d" % (DVS_DAEMON_NAME, procs))
                '''
                22 is a code for: RCV + DVS + SEND threads
                '''
                output = self._proxy.shell(['/cluster/gbottari/dvs_daemon/dvs_daemon_giulio','22','1'], block=True)
                sleep(1) # wait for dvs_daemon to start its threads 
            except:
                self._logger.exception('Could not start DVS daemon at %s. Output was: %s' % (repr(self), output))
                raise
            
            #Setup DVFS Controller     
            if self.dvfsCont is not None:
                self._logger.info('Setting up %s DVFS controller...' % repr(self))
                try:
                    self.dvfsCont.setup() #reset the controller
                    self.dvfsCont.setFreqCap(self.processor.availableFreqs[-1]) #no freqCap on startup
                except:
                    self._logger.error('Error while setting up DVFS Controller in %s' % repr(self))
                    raise
            
            self._performedSetup = True
        else:
            self._logger.warning('Already performed setup on %s' % repr(self))


    def cleanUp(self):
        '''
        Executes clean up actions when the experiment has ended.
        These actions involves turning the servers back on,
        stopping dvs_daemon and stopping Apache
        '''
        self._logger.info('Cleaning up %s...' % self)
        
        if self.status != Server.ON:
            self.turnOn()
        
        #Stop apache
        self._proxy.shell([self._apachePath + 'apachectl', 'stop'], block=True)
        
        #lower the power usage
        self.dvfsCont.setFreqCap(self.processor.availableFreqs[0])
        
        #Stop dvs_daemon        
        self._proxy.shell(['killall', 'dvs_daemon_giulio'], block=True)
    

    @property
    def ip(self):
        return self._IP
    
    @ip.setter
    def ip(self, aIP):
        self._IP = aIP
        self._proxy = SSH(hostname=self._IP)
    
    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, newStatus):        
        self._status = newStatus
    
    @property
    def hostname(self):
        return self._hostname
    
    @hostname.setter
    def hostname(self, aHostname):
        self._hostname = aHostname
    
    @property
    def macAddr(self):
        return self._macAddr
    
    @macAddr.setter
    def macAddr(self, mac):
        self._macAddr = mac
        
    @property
    def cpuFanSpeed(self):
        return self._cpuFanSpeed

    @property
    def eth(self):
        return self._eth
    
    @eth.setter
    def eth(self, interface):
        assert isinstance(interface,int)
        self._eth = interface
        
    def setApachePath(self, path):
        self._apachePath = path


class ServerBuilder(Builder):
    
    def __init__(self, sectionName, targetClass=None):
        if not targetClass: targetClass = Server
        Builder.__init__(self, targetClass)
        self.sectionName = sectionName
        #option strings        
        self.HOSTNAME = 'hostname'
        self.IP = 'ip'  
        self.FREQS = 'freqs'
        self.MAC_ADDR = 'mac'
        self.NETWORK_INTERFACE = 'eth'
        self.APACHE_PATH = 'apachePath'
        self.DVFSCONTROLLER = 'dvfscontroller'
            
    
    def readOptions(self, obj, cr):
        obj.hostname = cr.getValue(self.sectionName, self.HOSTNAME, str, required=False)
        obj.ip = cr.getValue(self.sectionName, self.IP, str, required=True)
        obj.processor.availableFreqs = cr.getValue(self.sectionName, self.FREQS, eval, required=False)
        obj.macAddr = cr.getValue(self.sectionName, self.MAC_ADDR, str, required=True)
        obj.eth = cr.getValue(self.sectionName, self.NETWORK_INTERFACE, int, required=True)
        obj.setApachePath(cr.getValue(self.sectionName, self.APACHE_PATH, str, required=True))
        
    
    def build(self, cr):
        server = Builder.build(self, cr)
        
        energyModel = EnergyModelBuilder(self.sectionName).build(cr, server)      
        server.energyModel = energyModel        
        
        '''
        This section builds a DVFSController.
        Every server must have a different instance of DVFSController, however each section at the
        configuration file usually represents one single instance (that can be shared among many
        objects).
        Therefore, it's the ServerBuilder that must create and link himself with the DVFSController.
        '''
        deps = [server]
        server.dvfsCont = self.buildObject(cr, 'DVFSController', deps)
        
        return server