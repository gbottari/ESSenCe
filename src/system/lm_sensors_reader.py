#coding: utf-8
'''
Created on Oct 29, 2010

@author: Giulio

TODO: detect when sensors command is not found or there are no modules detected. Create Exceptions to handle this.
'''

from tools import readFile
import re 


def readSections(lines):
    sections = []
    
    for line in lines:
        label = '[\w ]+' # accepts alphanumeric characters and white-spaces
        numbers = '[-+]?(\d+(\.\d*)?|\.\d+)' # accepts floats or integers
        match = re.match(r"(?P<name>%s): +(?P<value>%s) ?(?P<quantity>\S+)" % (label, numbers), line)
        if not match:
            print 'No match on line: "%s"' % line
        else:
            gdict = match.groupdict()
            gdict['value'] = float(gdict['value']) 
            sections.append(gdict)
    return sections


def readModule(input):
    '''
    Will read a module and return a dict with the corresponding readings
    The dict is organized as follows:
    {name:'mod_name', sections:[{section1},{section2},...]}
    
    A section is a dict too:
    {name:'section_name', value:'some_value', field1:'value', field2:'value'...}
    'fields' here refers to any information that this specific section contains.
    
    Ex:    
    w83627ehf-isa-0290
    VCore:       +1.49 V  (min =  +0.00 V, max =  +1.74 V)
    CPU Fan:    4440 RPM  (min = 2657 RPM, div = 4)
    Sys Temp:    +34.0°C  (high =  -7.0°C, hyst = -41.0°C)
    
    will output:
    result: {name:'w83627ehf-isa-0290', sections:[<section1>,<section2>,<section3>]}
    section1: {name:'VCore',value:'+1.49 V', min:'+0.00 V', max:'+1.74 V'}
    '''
    
    module = {}
    lines = input.splitlines()
    module['name'] = lines[0]    
    sections = readSections(lines[1:])    
    module['sections'] = sections
    
    return module


def readSensors(proxy):    
    #output = proxy.shell(['sensors','-A'])
    output = readFile('../../tmp/sensors-out.txt')
    blocks = output.split('\n\n') #split in blocks of text
    modules = []
    
    for block in blocks:
        if len(block) > 0:
            module = readModule(block)
            modules.append(module)
    return modules


if __name__ == '__main__':
    modules = readSensors()
    import pprint
    pprint.pprint(modules)