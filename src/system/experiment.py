'''
Created on Oct 14, 2010

@author: Giulio
'''

import logging, os
from network.SH import SH
from time import ctime, sleep
from datetime import datetime
from shutil import copy
from shared import LOG_NAME, MONITOR_NAME
from workloadGenerator import WorkloadGenerator
from server import Server
from sysObject import Object

from scripts.stats import file2data, getColumns, getAvg, getStddev, getSum, getLessThan
from system.Builder import Builder

try:
    import Gnuplot
except ImportError:
    logging.warning("Gnuplot.py not detected.")
    Gnuplot = None

try:
    import pylab
except ImportError:
    logging.warning("You must install pylab if you intend to plot stuff")
    pylab = None


class Experiment(Object):
    '''
    This class represents and executes a experiment, from creating the environment to collecting the results. 
    '''

    #Status:
    NOT_RUNNING = 0
    RUNNING = 1          
    FAILED = 2           
    SUCCESS = 3 
    ABORTED = 4
    
    STATUS_DICT = {NOT_RUNNING:'not running', RUNNING:'running', FAILED: 'failed', SUCCESS: 'success', ABORTED: 'aborted'}

    APACHE_PATH = '/usr/local2/apache2/'

    def __init__(self):
        self._label = 'Some Experiment'
        self._description = 'no description'
        self._configFilename = None
        self._status = Experiment.NOT_RUNNING
        self.workGen = WorkloadGenerator()
        self._stopTimeout = 30 #time to wait since a stop() is called (seconds)
        self._saveDir = '../exps/'
        self.plot = True
        self._logger = logging.getLogger(type(self).__name__)
        self.sh = SH()
        
        #System Modules
        self._cluster = None
        self._configurator = None
        self._loadBalancer = None
        self._perfRegulator = None
        self._serviceMonitor = None
        self._monitor = None
        self._infoServer = None
        self._powerMonitor = None
        
    
    def __str__(self):
        return '<%s(label=%s)>' % (self.__class__.__name__, self._label)
    
    
    def getStatus(self):
        return self._status
              
        
    def resetLog(self):
        '''
        Shutdown and destroys the current log.
        '''
        logging.shutdown()
        if os.path.isfile(LOG_NAME):
            open(LOG_NAME,'w')
    
    
    def __plotResults(self, path):
        g = Gnuplot.Gnuplot()
        #common setup
        g('reset')
        g('set terminal postscript enhanced solid color eps')
        g('file = "%s"' % MONITOR_NAME)
        g('set y2tics')
        g('set ytics nomirror')
        g('set key top left')
        g('set xlabel "Time(s)"')
        g('set grid')
               
        '''
        Power vs Incoming
        '''
        g('set grid')
        g('set ylabel \"Power (W)\"')
        g('set y2label \"Incoming\"')
        g('set autoscale y2')
        g('set y2tics')
        g('set ytics 0,100,600')
        g('set yrange [-300:600]')
        plot_args2 = 'file u 1:2 w l t \"Power\", file u 1:5 w l axis x1y2 t "Incoming"'
        g.plot(plot_args2)
        
        filename = 'power_incoming'
        g.save(path + filename + '.plt') #save gnuplot file
        g.hardcopy(path + filename + '.ps')
        
        '''
        Sat vs Incoming
        '''
        g('set grid')
        g('set ylabel "Saturation"')
        g('set y2label "Incoming"')        
        g('set ytics 0, 0.20, 2.0 nomirror')
        g('set yrange [-2.5:2.0]')
        g('set autoscale y2')
        g('set y2tics')
        qos_target = -1.0
        if self._perfRegulator:
            qos_target = self._perfRegulator.controller._setPoint
        plot_args3 = 'file u 1:5 w l axis x1y2 t "Incoming", file u 1:11 w l t "Sat", %f w l t "Sat Target (%3.2f)"' % (qos_target, qos_target)
        g.plot(plot_args3)
        
        filename = 'sat_incoming'
        g.save(path + filename + '.plt') #save gnuplot file
        g.hardcopy(path + filename + '.ps')
        
        '''
        Machines vs Incoming Requests
        '''
        filename = 'machines_incoming'
        g('set title "%s"' % 'Machines vs Trace')
        g('set autoscale y')
        g('set ylabel "Requests (req/s)"')
        g('set y2label "Frequencies (GHz)"')
        
        #set correct y2tics:
        tics_override = '('
        
        accFreq = 0.0
        for server in self._cluster.availableServers:
            peakFreq = server.processor.availableFreqs[-1] / 1000000.0
            accFreq += peakFreq
            tics_override += '\"%3.1f\" %f, ' % (peakFreq, accFreq)
        tics_override = tics_override[:-2] + ')'
        g('set y2tics 0,0.2 %s' % tics_override)        
        g('set y2range [0:%f]' % accFreq)
        
        plot_args1 = 'file u 1:5 w l t "requests"'
        counter = len(self._monitor.varPool) #magic number
        peakFreq = 0.0
        for server in self._cluster.availableServers: #this may bring some problems...
            plot_args1 += ', file u 1:($%d+%f) w steps axis x1y2 t "%s"' % (counter, peakFreq, server.hostname)
            peakFreq += server.processor.availableFreqs[-1] / 1000000.0
            counter += 1
        
        g.plot(plot_args1)
        
        g.save(path + filename + '.plt') #save gnuplot file
        g.hardcopy(path + filename + '.ps')
        
        """
        '''
        Incoming & Predicted vs QoS
        '''
        g('unset grid')
        g('set title \"%s\"' % 'Incoming and Predicted vs QoS')
        g('set ylabel \"Requests/s\"')
        g('set y2label \"QoS\"')
        g('set y2tics 0, 0.20, 1.0')
        g('set y2range [-2.5:1.1]')
        plot_args3 = 'file u 1:4 w l t \"Incoming\", file u 1:7 w l lw 2 t \"Predicted\", file u 1:5 w l axis x1y2 t \"QoS\", %f w l axis x1y2 t \"QoS Target (%3.2f)\"' % (qos_target,qos_target)
        g.plot(plot_args3)
        
        filename = 'incoming_pred_qos'
        g.save(path + filename + '.plt') #save gnuplot file
        g.hardcopy(path + filename + '.ps')
        """
    
    
    def _plotResults(self, path):
        '''
        Power and Incoming
        '''        
        fig = pylab.figure()
        fields = getColumns(MONITOR_NAME)
        data = file2data(fields, MONITOR_NAME)
        pylab.grid(True)
        ax1 = pylab.subplot(111)        
        l1 = pylab.plot(data[4], color='red')
        ax2 = pylab.twinx()        
        l2 = pylab.plot(data[1], color='blue')
       
        ax2.legend((l1,l2), ('Incoming', 'Power'), 'best')
        ax1.set_ylabel("Incoming (req/s)")
        ax2.set_ylabel("Power (W)")
        ax1.set_xlabel("Time (s)")
        ax2.set_yticks(range(0, 600, 100))
        pylab.ylim(-300, 600)
        
        fig.savefig(path + 'power.eps')
        
        '''
        Sat and Incoming
        '''
        fig = pylab.figure()
        fields = getColumns(MONITOR_NAME)
        data = file2data(fields, MONITOR_NAME)
        pylab.grid(True)
        ax1 = pylab.subplot(111)        
        l1 = pylab.plot(data[4], color='blue')
        ax2 = pylab.twinx()        
        l2 = pylab.plot(data[10], color='red')
        qos_target = self._perfRegulator.controller._setPoint        
        pylab.axhline(qos_target, color='orange')        
        
        ax2.legend((l1,l2), ('Incoming', 'Saturation'), 'best')
        ax1.set_ylabel("Incoming (req/s)")
        ax2.set_ylabel("Saturation")
        ax1.set_xlabel("Time (s)")
        ax2.set_yticks([x/10.0 for x in range(0, 20, 2)])
        pylab.ylim(-2.5, 2)
        
        fig.savefig(path + 'sat.eps')
        
    
    def startExperiment(self):
        
        def isRunning(processName):
            result = self.sh.shell(['ps aux | grep %s' % processName], shell=True, block=True) #this one must be shell executed            
            return (result is not None) and (len(result.splitlines()) > 2)
        
        '''
        First, it will read a config and create the appropriate system environment.
        Then, the usual setup is provided in preparation for the experiment start.
        Lastly, the workgenerator and system threads are started.
        This function will finish when the work generator has stopped. 
        '''
        assert self._status == Experiment.NOT_RUNNING
        self._status = Experiment.RUNNING
        
        self.resetLog() #clear log
        try:
            apache_online = isRunning('local2')
            
            if apache_online:                
                self._logger.info('Detected Apache online, shutting it down...')
                self.sh.shell([self.APACHE_PATH + 'bin/apachectl','stop'], block=True)    
                sleep(0.5) # a small delay is necessary here 
                apache_online = isRunning('local2')
                if apache_online:
                    self._logger.warning('Could not stop apache or there is another Apache process running (httpd).')
                    
            self._logger.info('Clearing access_log...')
            f = open(self.APACHE_PATH + 'logs/access_log', 'w')
            f.close()
            
            self._logger.info('Starting Apache...')
            self.sh.shell([self.APACHE_PATH + 'bin/apachectl','start'], block=True)
            sleep(0.5) # a small delay is necessary here
            apache_online = isRunning('local2')
            if not apache_online:
                raise Exception("Apache couldn't be turned on!")
            
            self._cluster.turnOnAll()
            self._cluster.detect()            
            self._cluster.setup()
            self._monitor.openMonitorFile(MONITOR_NAME)                        
            
            self._logger.info('Starting experiment...')
            self._infoServer.start()
            self._serviceMonitor.start()
            self._powerMonitor.start()                
            self._monitor.start()
            if self._perfRegulator:
                self._perfRegulator.start()
            if self._configurator:
                self._configurator.start()
            self.workGen.start()
            
            self._logger.info('Experiment started')
            
            self.workGen.join() #wait for experiment to finish
            
        except:
            self._logger.exception('Experiment Failed!')
            self._status = Experiment.FAILED
        finally:
            self.stopExperiment()
        
        if self._status == Experiment.RUNNING:
            self._status = Experiment.SUCCESS 


    def abortExperiment(self):
        '''
        User abort experiment command issued.
        '''
        if self._status != Experiment.RUNNING:
            self._logger.warning('Experiment can\'t be aborted because it is: %s' % Experiment.STATUS_DICT[self._status])
            return
        
        self._status = Experiment.ABORTED
        
        self._logger.warning('Aborting experiment...')        
        self.stopExperiment()
            
    
    def getReport(self):
        '''
        Generate a experiment report.
        The report consists of the experiment description, configuration and some statistics.
        '''      
        fields = getColumns(MONITOR_NAME)
        
        #this code will trim the first moments of the monitor
        skipLines = 5 # the very first measures are usually bogus
        if self._configurator:
            skipLines = max(skipLines, 4 * self._configurator.loopPeriod)
        if self._perfRegulator:
            skipLines = max(skipLines, self._perfRegulator.loopPeriod)
        data = file2data(fields, MONITOR_NAME, skipLines=skipLines)
        avgs = getAvg(data)
        stddevs = getStddev(data,avgs)
        
        power = avgs[1]
        power_stddev = stddevs[1]
        #qos = avgs[5]
        qos = getLessThan(data, 8, 100)
        qos_stddev = stddevs[5]
        saturation = avgs[10]
        mse = avgs[7]
        sat_stddev = stddevs[10]
        delay = avgs[8]
        delay_stddev = stddevs[8]
        dyn_power = avgs[11]
        
        sums = getSum(data)
        
        lost = sums[2]
        
        report = '''\
%(separator)s
%(experiment)s
%(separator)s
%(description)s

Status         : %(status)s
Start time     : %(start_time)s
Finish time    : %(finish_time)s
Elapsed time   : %(elapsed_time)1.0f seconds
Workgen command: %(wg_cmd)s
Power          : avg: %(power)5.2f, stddev: %(power_stddev)5.2f
Dynamic Power  : avg: %(dyn_power)5.2f
Saturation     : avg: %(saturation)6.5f, stddev: %(sat_stddev)6.5f
Delay          : avg: %(delay)7.3f, stddev: %(delay_stddev)7.3f
QoS            : avg: %(qos)6.5f, stddev: %(qos_stddev)6.5f
Lost           : total: %(lost)5.1f
MSE            : %(mse)6.5f
Switches ON    : %(switch_on)d
Switches OFF   : %(switch_off)d''' \
        % { \
        'separator'   : '-' * 20, \
        'experiment'  : self._label, \
        'description' : self._description, \
        'status'      : Experiment.STATUS_DICT[self._status], \
        'start_time'  : ctime(self.workGen.getStartTime()), \
        'finish_time' : ctime(self.workGen.getFinishTime()), \
        'elapsed_time': self.workGen.getFinishTime() - self.workGen.getStartTime(), \
        'wg_cmd'      : ' '.join([self.workGen._wgProgram] + self.workGen._wgParameters), \
        'mse'         : mse, \
        'switch_on'   : self._cluster.getSwitchCount(Server.ON), \
        'switch_off'  : self._cluster.getSwitchCount(Server.OFF), \
        'qos'         : qos, \
        'qos_stddev'  : qos_stddev, \
        'power'       : power, \
        'power_stddev': power_stddev, \
        'lost'        : lost, \
        'saturation'  : saturation, \
        'sat_stddev'  : sat_stddev, \
        'delay'       : delay, \
        'delay_stddev': delay_stddev, \
        'dyn_power'   : dyn_power
        }
        
        return report
    
    
    def saveExperiment(self): #incomplete
        '''
        This function will create a experiment folder and save results, configuration and log there.
        Results consists of the real workload sent by the workloadGenerator and captured at the FE,
        QoS per second, replied requests per second, and servers states per second (one column per
        server).
        Configuration is the experiment config file, and the log is, of course, the system log.
        '''
        self._logger.info('Saving experiment...')
    
        now = datetime.now()
        path = self._saveDir + now.strftime("%Y-%m-%d_%Hh%Mm%Ss") + '/'
        os.mkdir(path)
        
        copy(MONITOR_NAME, path) #save monitor info        
        copy(self._configFilename, path) #save config file for the server
        
        #write report
        with open(path + 'report.txt', 'w') as f:
            report = 'Could not generate a proper report. See the log for details.'
            try:
                report = self.getReport()
            except:
                self._logger.exception('Problem while generating report.')
            f.write(report)
        
        self._logger.info('Bye!')
        
        copy(LOG_NAME,path) #save log 
        if self.plot and Gnuplot != None: self._plotResults(path)        
        self.resetLog()    
    
    
    def _wait(self, thread):
        if thread.isAlive():
            thread.join(self._stopTimeout)
            if thread.isAlive(): #zombie: hmmm... braaaains!
                self._logger.warning('Thread timed out: %s' % type(thread).__name__)
    
    def _stopThread(self, thread):
        if not thread.isAlive():
            self._logger.error('Thread %s was already dead when tried to kill it.' % thread)
            self._status = Experiment.FAILED
                    
        thread.stop()
    
    
    def stopExperiment(self):
        '''
        Will stop system threads and stop the workload generator if it is still active.
        '''
        if self._status == Experiment.ABORTED:
            '''
            Means that the experiment has already been aborted/failed and therefore
            there's nothing else to do.
            '''
            self._logger.warning('Attempted to stop a %s experiment' % self.STATUS_DICT[self._status])
            return
        
        self._logger.warning('Stopping Experiment...')
                
        self._stopThread(self._monitor)        
                
        if self._configurator:
            self._stopThread(self._configurator)
        if self._perfRegulator:
            self._stopThread(self._perfRegulator)
        
        if self._configurator:
            self._wait(self._configurator)
        if self._perfRegulator:
            self._wait(self._perfRegulator)
        
        #Stops Apache:
        self._logger.info('Stopping Apache...')
        self.sh.shell([self.APACHE_PATH + 'bin/apachectl','stop'], block=True)
        
        if self.workGen.isAlive():
            self.workGen.stop()
            self._wait(self.workGen)
        
        self._finishTime = self.workGen.getFinishTime()
                
        self._stopThread(self._serviceMonitor)
        self._stopThread(self._infoServer)        
        self._stopThread(self._powerMonitor)
        
        self._wait(self._serviceMonitor)
        self._wait(self._infoServer)        
        self._wait(self._powerMonitor)       
        self._wait(self._monitor)
        
        self._cluster.cleanUp()


    def setDescription(self, description):
        self._description = description
        
    
    def setConfigFilename(self, config):
        self._configFilename = config
        
        
    def setLabel(self, label):
        self._label = label


class BaseExperimentBuilder(Builder):

    def __init__(self, targetClass=None):        
        Builder.__init__(self, Experiment)

    
    def build(self, cr, *args):
        exp = Builder.buildObject(self, cr, 'Experiment', [])
        return exp


class ExperimentBuilder(Builder):
    
    def __init__(self, targetClass=None):
        if not targetClass: targetClass = Experiment
        Builder.__init__(self, targetClass)
        
        #sections
        self.EXPERIMENT = 'Experiment'
        self.SERVICE_MONITOR = 'RequestMonitor'
        self.CLUSTER = 'Cluster'
        self.PREDICTOR = 'Predictor'
        self.PERFREGULATOR = 'PerfRegulator'
        self.POWERMONITOR = 'PowerMonitor'       
        self.APACHE = 'XMLRPCProxy'
        self.CONFIGURATOR = 'Configurator'
        
        #options
        self.TRACE = 'trace'
        self.USE_CONFIGURATOR = 'useconfigurator'
        self.USE_PERFREGULATOR = 'useperfregulator'        
        self.DESCRIPTION = 'description'
        self.PLOT = 'plot'
        self.IP = 'ip'
        self.MAC_ADDR = 'mac'
        self.NETWORK_INTERFACE = 'eth'
        self.WORKGEN_PROGRAM = 'workgenprogram'
        self.WORKGEN_PARAMETERS = 'workgenparameters'
        self.WORKGEN_MIN_EXECUTION_TIME = 'workgenminexectime'
        self.WORKGEN_PATH = 'workgenpath'
        self.WORKGEN_MACHINE = 'workgenmachine'
        self.WORKGEN_INITCMD = 'workgeninitcmd'
    
    
    def readWorkGen(self, obj, cr):
        workgenSection = cr.getValue(self.EXPERIMENT, self.WORKGEN_MACHINE)
        
        obj.workGen.ip = cr.getValue(workgenSection, self.IP)
        obj.workGen.macAddr = cr.getValue(workgenSection, self.MAC_ADDR)
        obj.workGen.eth = cr.getValue(workgenSection, self.NETWORK_INTERFACE, int)
        
        obj.workGen.setProgram(cr.getValue(self.EXPERIMENT, self.WORKGEN_PROGRAM, str))
        obj.workGen.setProgramParameters(cr.getValue(self.EXPERIMENT, self.WORKGEN_PARAMETERS, eval))            
        
        obj.workGen.initcmd = cr.getValue(self.EXPERIMENT, self.WORKGEN_INITCMD, required=False)            
        obj.workGen._minExecTime = cr.getValue(self.EXPERIMENT, self.WORKGEN_MIN_EXECUTION_TIME, int, False)
        obj.workGen._wgPath = cr.getValue(self.EXPERIMENT, self.WORKGEN_PATH, required=False)     
            
    
    def readResourceMonitor(self, obj, cr):        
        from infoServer import ResourceMonitorBuilder #TODO: use a Builder on that one
        
        obj._infoServer = ResourceMonitorBuilder().build(cr, obj._cluster)
        obj._infoServer.cluster = obj._cluster
        
    
    def readApache(self, obj, cr):        
        obj._apache = self.buildObject(cr, self.APACHE, obj)                
        obj._serviceMonitor.apache = obj._apache
        obj._loadBalancer.apache = obj._apache
        
    
    def readOptions(self, obj, cr):        
        from filters import DummyFilter
        from monitor import SystemMonitor              
               
        # common
        obj._serviceMonitor = self.buildObject(cr, self.SERVICE_MONITOR, obj)
        obj._cluster = self.buildObject(cr, self.CLUSTER, obj)
        obj._loadBalancer = self.buildObject(cr, 'LoadBalancer', obj) # needs Cluster
        
        # specific
        self.readWorkGen(obj, cr)
        
        # specific
        self.readResourceMonitor(obj, cr) # needs Cluster
        
        # specific
        self.readApache(obj, cr)
        
        '''
        Common
        '''               
        obj.setConfigFilename(cr.filename)
        obj.setDescription(cr.getValue(self.EXPERIMENT, self.DESCRIPTION, str, False))
        obj.plot = cr.getValue(self.EXPERIMENT, self.PLOT, bool)     
        
        obj._monitor = SystemMonitor()
         
        if not cr.has_section(self.PREDICTOR):
            filter = DummyFilter()
        else:
            filter = self.buildObject(cr, self.PREDICTOR, obj)
        obj._predictor = filter
        
        usePerfRegulator = cr.getValue(self.EXPERIMENT, self.USE_PERFREGULATOR, bool)
        if usePerfRegulator: 
            obj._perfRegulator = self.buildObject(cr, self.PERFREGULATOR, obj)
        useConfigurator = cr.getValue(self.EXPERIMENT, self.USE_CONFIGURATOR, bool) 
        if useConfigurator:
            obj._configurator = self.buildObject(cr, self.CONFIGURATOR, obj)
                                       
        obj._powerMonitor = self.buildObject(cr, self.POWERMONITOR, obj)
        
        #link objects:
        if useConfigurator:
            obj._configurator.perfRegulator = obj._perfRegulator
        obj._cluster.loadBalancer = obj._loadBalancer        
        obj._monitor.experiment = obj        
        obj._cluster.serviceMonitor = obj._serviceMonitor
        
        '''
        Set the buffer size for the RequestBuffer according to the window requirements from
        the active policies.
        '''        
        buffSize = 0
        
        if obj._configurator:
            buffSize = max(buffSize, obj._configurator.windowSize)
        
        if obj._perfRegulator:
            buffSize = max(buffSize, obj._perfRegulator.loadWindowSize, obj._perfRegulator.windowSize)
        
        obj._serviceMonitor.services[0].setBufferSize(buffSize)
                    
    
    def buildObject(self, cr, sectionName, exp):
        '''
        Automatically fetches the dependencies from the Experiment instance and hands them to the
        conventional method.
        '''
        sections = cr.getValue(sectionName, 'dependencies', eval, required=False)
        
        '''
        Transforms the string list of dependencies into a list of objects that
        represents those dependencies
        '''
        deps = []
        if sections:
            for section in sections:
                attr = '_' + section.lower()
                if hasattr(exp, attr):
                    deps.append(eval('exp.' + attr))        
        
        return Builder.buildObject(self, cr, sectionName, deps)