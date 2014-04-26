'''
Created on Sep 22, 2010

@author: giulio
'''

from sysObject import Object

class DeadzoneController(Object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self._deadzone = None
        self._setPoint = None
    
    
    def __repr__(self):
        return '<' + self.__class__.__name__ + '(dz=' + str(self._deadzone) + ', sp=' + str(self._setPoint) + ')>'
    
    def getDeadzone(self):
        return self._deadzone
    
    def setDeadzone(self, deadzone):
        assert isinstance(deadzone,tuple)        
        self._deadzone = deadzone
    
    def setPoint(self, setpoint):        
        self._setPoint = setpoint
        
    def action(self, input):
        assert (self._deadzone != None) and (self._setPoint != None)
        if input <= self._deadzone[0] or input >= self._deadzone[1]:
            return input - self._setPoint
        return 0