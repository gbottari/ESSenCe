'''
Created on Jul 19, 2011

@author: Giulio
'''
from system.sysObject import Object

class Builder(Object):
    '''
    classdocs
    '''


    def __init__(self, targetClass):
        '''
        Constructor
        '''
        Object.__init__(self)
        self.targetClass = targetClass
        self.sectionName = self.targetClass.__name__
    
    
    def readOptions(self, obj, cr):
        pass
           
    
    def build(self, cr, *args):
        '''
        Build an instance of some class using args and a ConfigReader object (cr)
        '''
        obj = self.targetClass(*args)
        self.readOptions(obj, cr)
        return obj
    
    
    def buildObject(self, cr, sectionName, deps):        
        builder = cr.getValue(sectionName, 'builder', eval, required=True)       
        
        try:
            exec('from %s import %s' % builder)            
        except ImportError, msg:
            raise Exception('Could not load the requested module. %s' % msg)          
                               
        obj = None        
        exec('obj = %s().build(cr, *deps)' % builder[1])
        
        return obj