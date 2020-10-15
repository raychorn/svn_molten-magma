import os
import sys

from ConfigParser import SafeConfigParser
import logging
import base64

import Globals as G

# Our configured logging cannot be used here as it requires Properties
# to configure

class Properties:
    """
    Locate and read properties file.
    """
    __shared_state = {}

    def __init__(self):
        self.props = None

        self.__dict__ = self.__shared_state

        if not hasattr(self, 'props') or self.props is None:
            logging.basicConfig()
            self.__initProps()
            self.__readPropFile()
            
            self.__parseProperties()
            pass
        return
    ## END __init__

    def __initProps(self):
        """ Set up some basic paths """
        if os.environ.has_key(G.HOME_ENV_VAR):
            self.HOME_DIR = os.environ.get(G.HOME_ENV_VAR)
        else:
            logging.critical("Your %s environment variable doesn't seem to be set." %G.HOME_ENV_VAR)
            pass

        self.basePath = os.path.abspath(self.HOME_DIR)
        self.configPath = os.path.join(self.basePath, 'config')
        return
    ## END __initProps

    def __readPropFile(self):
        """ Locate and read the property file """
        propPath = os.path.join(self.configPath, 'pysfdc.conf')
        if not os.path.exists(propPath):
            logging.error("could not locate properties file at %s" %propPath)
            sys.exit(1)
            pass
        
        self.props = SafeConfigParser()
        self.props.read(propPath)
        return
    ## END __readPropFile

    def __parseProperties(self):
        """ read the various sections of properties """
        ## log
        sec = 'log'

        if self.props.has_option(sec, 'logDir'):
            self.logDir = self.props.get(sec, 'logDir')
        else:
            self.logDir = os.path.join(self.basePath, 'log')
            pass
        
        ## soap
        sec = 'sforce'
        wsdlPath = self.props.get(sec, 'wsdlPath')
        if wsdlPath[0] != '/':
            wsdlPath = os.path.join(self.basePath, 'WSDL', wsdlPath)
            pass
        self.wsdlPath = wsdlPath

        self.namespace = self.props.get(sec, 'namespace')

        if self.props.has_option(sec, 'maxRetryCount'):
            self.maxRetryCount = self.props.get(sec, 'maxRetryCount')
        else:
            self.maxRetryCount = 3
            pass


        sec = 'batch'
        baseBatchSize = 200
        
        if self.props.has_option(sec, 'maxCreate'):
            self.maxCreate = self.props.getint(sec, 'maxCreate')
        else:
            self.maxCreate = baseBatchSize
            pass

        if self.props.has_option(sec, 'maxRetrieve'):
            self.maxRetrieve = self.props.getint(sec, 'maxRetrieve')
        else:
            self.maxRetrieve = baseBatchSize
            pass

        if self.props.has_option(sec, 'maxUpdate'):
            self.maxUpdate = self.props.getint(sec, 'maxUpdate')
        else:
            self.maxUpdate = baseBatchSize
            pass

        if self.props.has_option(sec, 'maxDelete'):
            self.maxDelete = self.props.getint(sec, 'maxDelete')
        else:
            self.maxDelete = baseBatchSize
            pass


        sec = "sobject"
        self.describeSObjectStruct = self.__parseStruct(sec)

        sec = "test"
        # FIXME handle case of unset test credentials
        self.testUsername = self.props.get(sec, 'testusername')
        testPwEncode = self.props.get(sec, 'testpwencode')
        self.testPassword = base64.decodestring(testPwEncode)
        return

    def __parseList(self, propStr):
        propList = []
        openBraceIdx = propStr.find('{')
        closeBraceIdx = propStr.find('}')
        if closeBraceIdx <= openBraceIdx:
            closeBraceIdx = len(propStr)
            pass
        for unit in propStr[openBraceIdx+1:closeBraceIdx].split(','):
            propList.append(unit.strip())
            continue

        return propList
    ## END __parseList

    def __parseStruct(self, propSection):
        metaSchema = {}
        metaSchema['type'] = self.props.get(propSection, 'type')

        singleparts = ('key', 'parentfield')
        for part in singleparts:
            if self.props.has_option(propSection, part):
                metaSchema[part] = self.props.get(propSection,
                                                  part)
                pass
            continue
        
        listparts = ('boolean', 'string', 'int', 'list', 'contains')
        for part in listparts:
            if self.props.has_option(propSection, part):
                metaSchema[part] = self.__parseList(self.props.get(propSection,
                                                                   part))
                pass
            continue
        
        for contained in metaSchema.get('contains',[]):
            metaSchema[contained] = self.__parseStruct(contained)
            continue
        return metaSchema
    ## END __parseStruct
    
class NoOptionError(Exception):
    pass

