'''
Created on Oct 13, 2010

@author: Giulio
'''

import logging
from ConfigParser import SafeConfigParser, NoOptionError

class ConfigReader(SafeConfigParser):

    def __init__(self, filename):
        SafeConfigParser.__init__(self)
        self._logger = logging.getLogger(type(self).__name__)   
        self.filename = filename
    
    
    def getValue(self, section, option, conv=str, required=True):
        item = None
        try:
            if conv == bool:
                item = self.getboolean(section, option)
            else:
                item = self._get(section, conv, option)
        except NoOptionError:
            if required: 
                raise Exception('Required option "%s" not found in section "%s"' % (option, section))
                
        return item
    
    
    def parse(self):
        if len(self.read(self.filename)) == 0:
            raise Exception('Couldn\'t open: \'%s\'' % self.filename)        