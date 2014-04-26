'''
Created on Nov 12, 2010

@author: giulio
'''

import logging
from system.configReader import ConfigReader
from time import sleep
from system.experiment import Experiment, BaseExperimentBuilder

EXPS_PATH = '../tmp/new_exps.txt'
#EXPS_PATH = '../tmp/pred_config/tests.txt'

def main():    
    try:
        with open(EXPS_PATH,'r') as f:
            for line in f:
                if len(line) > 0 and line[0] not in ['#','\n']: # ignore blank lines (\n) and comments                    
                    config = ConfigReader(line.rstrip(' \n')) # remove the trailing spaces and '\n' on the line                
                    config.parse()
                    exp = BaseExperimentBuilder().build(config)
                    logging.info('Starting: %s' % exp)
                    exp.startExperiment()
                    exp.saveExperiment()
                    if exp.getStatus() != Experiment.SUCCESS:
                        break
                    sleep(3) # delay between experiments
    except KeyboardInterrupt:
        logging.warning('User aborted...')
        exp.abortExperiment()
        return
    logging.info('Finished!')

if __name__ == '__main__':
    main()