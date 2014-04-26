'''
Created on Feb 3, 2011

@author: giulio
'''

class Object(object):
    '''
    classdocs
    '''

    def __repr__(self):
        return '<%s>' % (self.__class__.__name__)