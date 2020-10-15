"""
Structure for reading and providing access to properties, read from a
file, throughout a project.

Properties class is a singleton-type class that will read the properties file
the first time the class is instantiated, parsing the file and populating
data members in the class for use by all future instantiations.

Author:		Kevin Shuk <surf@surfous.com>
Date:		Sep 17, 2005
Copyright: 	(c) 2005, Kevin Shuk
                All Rights Reserved
"""
ident = "$ID: $"

import os
import sys
import types

from ConfigParser import SafeConfigParser
import logging

# Our configured logging cannot be used here as it requires Properties
# to configure

class Properties:
    """
    Locate and read properties file.
    """
    __shared_state = {}

    def __init__(self, basePath=None):
        self.props = None

        self.__dict__ = self.__shared_state

        if not hasattr(self, 'props') or self.props is None:
            logging.basicConfig()
            self.__initProps(basePath)
            self.__readPropFile()
            
            self.__parseProperties()
            pass
        return
    ## END __init__

    def __initProps(self, basePath):
        """ Set up some basic paths """
        self.HOME_DIR = None
        if basePath is not None:
            self.HOME_DIR = basePath
        elif os.environ.has_key('SFDCEXPORT_HOME'):
            self.HOME_DIR = os.environ.get('SFDCEXPORT_HOME')
        else:
            logging.critical("Unable to determine script home. Do you need to set SFDCEXPORT_HOME environment var?")
            pass

        self.basePath = os.path.abspath(self.HOME_DIR)
        self.configDir = os.path.join(self.basePath, 'config')
        self.libDir = os.path.join(self.basePath, 'lib')
        self.binDir = os.path.join(self.basePath, 'bin')
        return
    ## END __initProps

    def __readPropFile(self):
        """ Locate and read the property file """
        propPath = os.path.join(self.configDir, 'export.conf')
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
        sec = "url"
        if self.props.has_option(sec, "baseUrl"):
            self.baseUrl = self.props.get(sec, "baseUrl")
        else:
            raise MissingPropertyError("config property baseUrl must be set")

        
        if self.props.has_option(sec, "loginUrl"):
            self.loginUrl = self.props.get(sec, "loginUrl")
        else:
            raise MissingPropertyError("config property loginUrl must be set")

        
        if self.props.has_option(sec, "exportUrl"):
            self.exportUrl = self.props.get(sec, "exportUrl")
        else:
            raise MissingPropertyError("config property exportUrl must be set")


        ## login
        sec = "login"

        self.uname = None
        if self.props.has_option(sec, 'uname'):
            self.uname = self.props.get(sec, 'uname')
            pass

        self.encpw = None
        if self.props.has_option(sec, 'encpw'):
            self.encpw = self.props.get(sec, 'encpw')
            pass


        ## email
        sec = "email"
        self.sendMail=False
        if self.props.has_option(sec, "sendMail"):
            self.sendMail = self.props.getboolean(sec, "sendMail")
            pass

        self.smtpHost = None
        if self.props.has_option(sec, "smtpHost"):
            self.smtpHost = self.props.get(sec, "smtpHost")
            pass

        self.smtpPort = 25
        if self.props.has_option(sec, "smtpPort"):
            self.smtpPort = self.props.get(sec, "smtpPort")
            pass

        self.smtpUser = None
        if self.props.has_option(sec, "smtpUser"):
            self.smtpUser = self.props.get(sec, "smtpUser")
            pass

        self.smtpEncpw = None
        if self.props.has_option(sec, "smtpEncpw"):
            self.smtpEncpw = self.props.get(sec, "smtpEncpw")
            pass

        self.fromEmail = None
        if self.props.has_option(sec, "fromEmail"):
            self.fromEmail = self.props.get(sec, "fromEmail")
            pass

        self.toEmailList = None
        if self.props.has_option(sec, "toEmailList"):
            propStr = self.props.get(sec, "toEmailList")
            toEmailList = self.__parseList(propStr)
            if type(toEmailList) != types.ListType:
                toEmailList = [toEmailList,]
                pass
            self.toEmailList = toEmailList
            pass

        if self.sendMail is True and (self.smtpHost is None or \
                                      self.fromEmail is None or \
                                      self.toEmailList is None):
            msg = "if sendMail is set to true, all of smtpHose, fromEmail and toEmailList must be present"
            raise MissingPropertyError(msg)
        

        ## storage
        sec = "storage"
        if self.props.has_option(sec, "exportFileDir"):
            self.exportFileDir = self.props.get(sec, "exportFileDir")
        else:
            raise NoPropertyError("config property exportFileDir must be set")

        self.exportFileBasename = "default"
        if self.props.has_option(sec, "exportFileBasename"):
            self.exportFileBasename = self.props.get(sec, "exportFileBasename")
            pass

        # we will always use the zip file extension
        self.exportFileExtension = "zip"
##        if self.props.has_option(sec, "exportFileExtension"):
##            self.exportFileExtension = self.props.get(sec,
##                                                      "exportFileExtension")
##            pass

        self.exportArchiveDir = os.path.join(self.exportFileDir, 'archive')
        if self.props.has_option(sec, "exportArchiveDir"):
            self.exportArchiveDir = self.props.get(sec, "exportArchiveDir")
            pass

        ## retention
        sec = "retention"
        self.retainCount = 1
        if self.props.has_option(sec, "retainCount"):
            self.retainCount = self.props.get(sec, "retainCount")
            pass

        self.frequencyDays = 7
        if self.props.has_option(sec, "frequencyDays"):
            self.frequencyDays = self.props.get(sec, "frequencyDays")
            pass


        ## options
        sec = "options"
        self.pollIntervalMins = 10
        if self.props.has_option(sec, "pollintervalMins"):
            self.pollIntervalMins = self.props.getint(sec,
                                                          "pollIntervalMins")
            pass

        self.incAttach = True
        if self.props.has_option(sec, "includeAttachments"):
            self.incAttach = self.props.getboolean(sec, "includeAttachments")
            pass
        
        self.replaceCRs = False
        if self.props.has_option(sec, "replaceCarriageReturnsWithSpaces"):
            self.replaceCRs = self.props.getboolean(sec, "replaceCarriageReturnsWithSpaces")
            pass

        self.exportTypes = ["allEntities",]
        if self.props.has_option(sec, "exportTypesList"):
            propStr = self.props.get(sec, "exportTypesList")
            exportTypes = self.__parseList(propStr)
            if type(exportTypes) != types.ListType:
                exportTypes = [exportTypes,]
                pass
            
            if "allEntities" in exportTypes:
                exportTypes = ["allEntities",]
                pass
            
            self.exportTypes = exportTypes
            pass


        validEncodings = ["ISO-8859-1",
                          "Unicode",
                          "UTF-8",
                          "MS932",
                          "Shift_JIS",
                          "GB2312",
                          "Big5",
                          "EUC_KR",
                          "UTF-16"]
        self.encoding = "ISO-8859-1"
        if self.props.has_option(sec, "encoding"):
            encoding = self.props.get(sec, "encoding")
            if encoding in validEncodings:
                self.encoding = encoding
                pass
            pass

        
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
    
class PropertyError(Exception):
    pass

class NoPropertyError(PropertyError):
    pass

class MissingPropertyError(PropertyError):
    """ A property that is manditory or is depended upon by another property
    is missing.
    """
    pass

