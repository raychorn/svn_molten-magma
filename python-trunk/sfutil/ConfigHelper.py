#!/usr/bin/python
'''
Just a few helper functions for config files. Does not deal with config files
directly.

Maybe someday create a full subclass of ConfigParser for tighter integration.
'''

import ConfigParser, os, sys, re, string


def buildConfigPaths(configFileName, configDirPath=None):
    '''
    Looks for the config file in a number of places depending on the
    arguments provided.
     
    The following search hierarchy is followed:

    1a. in the configDirPath relative to the script being run (no leading /)
    1b. in the dir specified by configDirPath (if absolute - leading /)
    2.  in the same dir as the script being run
    3.  in the current working directory
    '''

    (scriptDir, scriptName) = os.path.split(sys.argv[0])

    configPathList = []
    if configDirPath is not None:
        if re.match('/', configDirPath) is None:
            # relative to script loc
            configPathList.append(os.path.join(scriptDir, configDirPath,
                                          configFileName))
        else:
            # absolute path
            configPathList.append(os.path.join(configDirPath, configFileName))


    configPathList.append(os.path.join(scriptDir, configFileName))
    configPathList.append(os.path.join(os.getcwd(), configFileName))
        
    return configPathList
## END def buildConfigPaths(configFileName, configDirPath)


def fetchConfig(configFile):
    configPaths = buildConfigPaths(configFile)
    props = ConfigParser.SafeConfigParser()
    props.read(configPaths)
    return props
## END def fetchConfig(configFile)


def parseConfigList(rawConfigItem, splitTok=None):
    '''
    Splits a config item into a list object.

    Default is to split on whitespace, but arbitrary token to split upon
    may optionally be provided.
    '''

    if splitTok is None:
        return string.split(rawConfigItem)
    else:
        splitList = string.split(rawConfigItem, splitTok)
        newList = []
        for splitItem in splitList:
            newList.append(splitItem.strip())
        return newList
## END def parseConfigList(rawConfigItem, splitTok)
