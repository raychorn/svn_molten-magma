import logging, logging.config
import os.path

from Properties import Properties

isConfigured = False

DEBUG2 = 9
DEBUG3 = 8

defaultConfig = """\
[formatters]
keys: basic,email

[handlers]
keys: console,rotating,criticalconsole

[loggers]
keys: root,pysfdc

[formatter_basic]
format: %(asctime)s %(name)s:%(levelname)s %(module)s:%(lineno)d:  %(message)s

[formatter_email]
format: %(asctime)s %(name)s:%(levelname)s
 %(module)s:%(lineno)d:
 %(message)s

[handler_criticalconsole]
class: StreamHandler
args: ()
level: CRITICAL
formatter: basic

[handler_console]
class: StreamHandler
args: ()
formatter: basic

[handler_rotating]
; append to a 100MB file, keep 3 versions
; default file location is PYSFDC_HOME/log/pysfdc.log
class: handlers.RotatingFileHandler
args: ['%(logfile)s', 'a', 104857600, 3]
formatter: basic

#[handler_criticalemail]
#; send mail using SMTP server at mailhost.addr from fromaddr@domain to
#; a list of addresses (without domains) having the specified subject
#class: handlers.SMTPHandler
#args: ['mail.host.com', 'fromaddr@host.com', ('toaddr@host.com',), 'email subject line']
#formatter: email
#level: CRITICAL

; Log anything else to the rotating file log
[logger_root]
level: WARNING
handlers: rotating

[logger_pysfdc]
level: INFO
qualname: pysfdc
handlers: rotating,criticalconsole
;handlers: rotating,criticalconsole,criticalemail
propagate: 0
"""



class PysfdcLogger(logging.Logger):

    def __init__(self, name, level=logging.NOTSET):
        logging.Logger.__init__(self, name, level)
        return
    ## END __init__

    # methods to support custom logging levels
    debug1 = logging.Logger.debug # just for completeness' sake
    
    def debug2(self, msg, *args, **kw):
        global DEBUG2
        self.log(DEBUG2, msg, *args, **kw)
        return
    ##  END debug2

    def debug3(self, msg, *args, **kw):
        global DEBUG3
        self.log(DEBUG3, msg, *args, **kw)
        return
    ## END debug3
    
    pass
## END PysfdcLogger

# configure the logger upon import of this module
#configLogger()
#logging.setLoggerClass(PysfdcLogger)


def __configPysfdcLogger():
    global isConfigured
    global defaultConfig
    global DEBUG2
    global DEBUG3

    # configure only once
    if isConfigured is True:
        return

    # add custom levels we want
    logging.addLevelName(DEBUG2, 'DEBUG2')
    logging.addLevelName(DEBUG3, 'DEBUG3')

    props = Properties()
    logConfigPath = os.path.join(props.configPath, 'pysfdc_log.conf')

    logPath = os.path.join(props.logDir, '/home/sfscript/log/details/sfapi3.log')
    presets = {'logfile': logPath}

    try:
        if not os.path.exists(logConfigPath):
            logConfigFile = file(logConfigPath, 'w+')
            logConfigFile.write(defaultConfig)
            logConfigFile.close()
            pass

        logging.config.fileConfig(logConfigPath, presets)

        log = logging.getLogger('pysfdc.PysfdcLogger')
        log.debug2('Log config read from %s' %logConfigPath)
    except Exception, e:
        # accept the basic configuration instead
        #logging.setLoggerClass(logging.Logger)
        logging.basicConfig()

        # log the config error
        logging.error('Could not configure logger - falling back to logging.basicConfig:\n%s' %e)
        pass

    isConfigured = True
    return
## END __configPysfdcLogger

logging.setLoggerClass(PysfdcLogger)
__configPysfdcLogger()
