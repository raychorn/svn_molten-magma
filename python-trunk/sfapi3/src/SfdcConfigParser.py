from ConfigParser import SafeConfigParser
import os

import pysfdcGlobals as pg

config_filename = 'pysfdc.config'


class SfdcConfigParser(SafeConfigParser):

    def __init__(self, configFilePath=None):
        global config_filename

        # provide for the global config file
        globalConfigPath = os.path.join('/etc/pysfdc', config_filename)
        configFileList = [globalConfigPath]

        # Now, capture the instance config - this should be the main config src
        if pg.PYSFDC_HOME is not None:
            instConfigPath = os.path.join(pg.PYSFDC_HOME, 'conf',
                                          config_filename)
            configFileList.append(instConfigPath)
            pass

        # Finally, any user-specified config
        userConfigPath = os.path.join(os.path.expanduser('~'),
                                      '.' + config_filename)
        configFileList.append(userConfigPath)
        
        SafeConfigParser.__init__(self)

        self.read(configFileList)
        return
    
