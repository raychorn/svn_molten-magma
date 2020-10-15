""" 
This is the Free Email Walker Process - handles all aspects of the Free Email List.

""" 

__version__ = 0.1

import pprint 
import os, sys 
import textwrap 
import time
import datetime 

import re

import logging

import cStringIO
 
from pyax.connection import Connection
from pyax.exceptions import ApiFault

from vyperlogix import misc
from vyperlogix.misc import _utils
from vyperlogix.daemon.daemon import Log
from vyperlogix.daemon.daemon import CustomLog
from vyperlogix.logging import standardLogging
from vyperlogix.hash import lists
from vyperlogix.misc import ObjectTypeName

from vyperlogix.lists.ListWrapper import ListWrapper

from vyperlogix.sf import update

from vyperlogix.misc import ask

from vyperlogix.misc import Args
from vyperlogix.misc import PrettyPrint

from vyperlogix.aima import utils

from vyperlogix import oodb

from vyperlogix.misc import threadpool

from vyperlogix.parsers.CSV import CSV
from vyperlogix.parsers.CSV import asCSV

import traceback
import Queue
from stat import *

from sfConstant import BAD_INFO_LIST

from crypto import *
from runWithAnalysis import *

from vyperlogix.crypto import XTEAEncryption
from vyperlogix.products import keys as products_keys

from sfUtil_win32 import *

_isRunningLocal_at_work = _utils.getComputerName().lower().find('.moltenmagma.com') > -1

_isVerbose = False
_csvPath = ''
_logging = logging.WARNING

is_platform_not_windows = lambda _sys:(_sys.platform != 'win32')
bool_is_platform_not_windows = is_platform_not_windows(sys)

_isBeingDebugged = (os.environ.has_key('WINGDB_ACTIVE')) # When debugger is being used we do not use threads...

_proc_queue = Queue.Queue(750) if (_isBeingDebugged) else threadpool.ThreadQueue(750)

_isVerbose = False

def _sf_query(sfdc,soql):
    try:
	ioTimeAnalysis.ioBeginTime('SOQL') 
	ret = sfdc.query(soql)
	ioTimeAnalysis.ioEndTime('SOQL') 
	sf_stats.count_query()
        return ret
    except ApiFault:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.error('(%s) soql=%s, Reason: %s' % (misc.funcName(),soql,info_string))
    return None

def exception_callback(sections):
    _msg = 'EXCEPTION Causing Abend.\n%s' % '\n'.join(sections)
    print >>sys.stdout, _msg
    print >>sys.stderr, _msg
    logging.error('(%s) :: %s' % (misc.funcName(),_msg))
    _logLogging.close()
    sys.stdout.close()
    sys.stderr.close()
    sys.exit()

def __getObjectsFromSOQL(sfdc,soql,useRealObjects=False):
    try:
	ret = _sf_query(sfdc,soql)
	logging.info('(%s) soql=%s' % (misc.funcName(),soql))
	if ret in BAD_INFO_LIST:
	    if (not _suppress_missing_warnings):
		logging.warning("(%s) :: Could not find any Object(s) for SOQL of (%s)." % (misc.funcName(),soql))
	else: 
	    logging.info("(%s) :: soql=%s." % (misc.funcName(),soql))
	    objects = []
	    for k in ret.keys():
		v = ret[k]
		if (not useRealObjects):
		    val = lists.copyAsDict(v)
		    objects.append(val.asDict())
		else:
		    objects.append(v)
	    return objects
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (misc.funcName(),info_string))

    return None

def _getFreeEmailHost(args):
    try:
	sfdc = args if (not isinstance(args,list)) else args[0]
	soql = "Select f.CreatedById, f.CreatedDate, f.Domain__c, f.Id, f.IsActive__c, f.LastModifiedById, f.LastModifiedDate, f.OwnerId from FreeEmailHost__c f ORDER BY f.Domain__c"
	data = __getObjectsFromSOQL(sfdc,soql)
	return data
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (misc.funcName(),info_string))

    return None
    
def getFreeEmailHost(args): 
    return _getFreeEmailHost(args)

def makeFreeEmailHost(sfdc,item):
    from pyax.sobject.classfactory import ClassFactory
    try:
	aHost = ClassFactory(sfdc, 'FreeEmailHost__c')
	d = {'Domain__c':item,'IsActive__c':True}
	saveResults = sfdc.create(aHost, [d])
	if (saveResults[0].has_key('errors')):
	    print >>sys.stderr, 'Failed to create FreeEmailHost__c from %s!' % (d)
	else:
	    print >>sys.stdout, '%s --> "%s".' % (item,str(saveResults))
    except Exception, details:
	print >>sys.stderr, _utils.formattedException(details)
    
def main(args):
    ioTimeAnalysis.ioBeginTime('%s' % (__name__))
    try:
	sfdc = args if (not isinstance(args,list)) else args[0]
	
	if (not _isRunningLocal_at_work):
	    print '\n\n'
	    print 'This program was designed to run only at Magma Design Automation for security reasons.'
	    print 'Please make sure you run this program only at Magma Design Automation or someone may get an email telling them about all this and you know what that means, right ?!? (Pink Slip... Unemployment...)'
	    print '\n\n'
	elif (_isRunningLocal_at_work):
	    if (os.path.exists(_input)):
		items = [item.strip() for item in _utils._readFileFrom(_input,mode='r')]
		for item in items:
		    makeFreeEmailHost(sfdc,item)
		pass
	    else:
		info_string = 'Cannot find "%s".' % (_input)
		logging.warning('(%s) :: %s' % (misc.funcName(),info_string))
	    
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.error('(%s) :: %s' % (misc.funcName(),info_string))

    ioTimeAnalysis.ioEndTime('%s' % (__name__))
    logging.info('(%s) :: %s' % (misc.funcName(),ioTimeAnalysis.ioTimeAnalysisReport()))

if __name__ == "__main__": 
    def ppArgs():
	pArgs = [(k,args[k]) for k in args.keys()]
	pPretty = PrettyPrint.PrettyPrint('',pArgs,True,' ... ')
	pPretty.pprint()

    args = {'--help':'displays this help text.',
	    '--verbose':'output more stuff.',
	    '--input=?':'name the path to the source file (must be a simple ascii text file).',
	    '--folder=?':'names the folder in which the logs and data will reside.',
	    '--username=?':'SalesForce username as in --username=sfisher@molten-magma.com.stag.',
	    '--password=?':'SalesForce password as in --password=put-your-password-here.',
	    '--logging=?':'[logging.INFO,logging.WARNING,logging.ERROR,logging.DEBUG]',
	    '--staging':'use the staging server rather than production otherwise use production.',
	    '--customlog':'redirect logging to stdout to facilitate running this from a GUI.',
	    }
    _argsObj = Args.Args(args)
    if (_isVerbose):
	print '_argsObj=(%s)' % str(_argsObj)

    if (len(sys.argv) == 1):
	ppArgs()
    else:
	_progName = _argsObj.programName
	_isVerbose = False
	try:
	    if _argsObj.booleans.has_key('isVerbose'):
		_isVerbose = _argsObj.booleans['isVerbose']
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    print >>sys.stderr, '(%s) :: %s' % (misc.funcName(),info_string)
	    _isVerbose = False

	_isStaging = False
	try:
	    if _argsObj.booleans.has_key('isStaging'):
		_isStaging = _argsObj.booleans['isStaging']
	except:
	    pass
	
	_isCustomlog = False
	try:
	    if _argsObj.booleans.has_key('isCustomlog'):
		_isCustomlog = _argsObj.booleans['isCustomlog']
	except:
	    pass
	
	try:
	    _logging = eval(_argsObj.arguments['logging']) if _argsObj.arguments.has_key('logging') else False
	except:
	    _logging = logging.WARNING

	__username = ''
	try:
	    __username = _argsObj.arguments['username'] if _argsObj.arguments.has_key('username') else __username
	except:
	    pass
	_username = __username
	
	__password = ''
	try:
	    __password = _argsObj.arguments['password'] if _argsObj.arguments.has_key('password') else __password
	except:
	    pass
	_password = __password
	
	__input = ''
	try:
	    __input = _argsObj.arguments['input'] if _argsObj.arguments.has_key('input') else __input
	except:
	    pass
	_input = __input
	
	__folder = os.path.dirname(sys.argv[0])
	try:
	    __folder = _argsObj.arguments['folder'] if _argsObj.arguments.has_key('folder') else ''
	    if (len(__folder) == 0) or (not os.path.exists(__folder)):
		if (os.environ.has_key('cwd')):
		    __folder = os.environ['cwd']
	except:
	    pass
	_folderPath = __folder
	
	print 'sys.version=[%s]' % sys.version
	v = _utils.getFloatVersionNumber()
	if (v >= 2.51):
	    if (not _isBeingDebugged):
		from vyperlogix.handlers.ExceptionHandler import *
		excp = ExceptionHandler()
		excp.callback = exception_callback
    
	    from vyperlogix.misc._psyco import *
	    importPsycoIfPossible(func=main,isVerbose=True)
    
	    print 'sys.argv=%s' % sys.argv
	    
	    _cwd = _folderPath
	    print '_cwd=%s' % _cwd
	    
	    if (len(_cwd) > 0) and (os.path.exists(_cwd)):
		name = _utils.getProgramName()
		
		if (os.path.exists(_folderPath)):
		    _log_path = _utils.safely_mkdir(fpath=_folderPath)
		else:
		    _log_path = _utils.safely_mkdir(fpath=_cwd)
		_data_path = _utils.safely_mkdir(fpath=os.path.dirname(_log_path),dirname='data')
		
		print '_data_path=%s' % (_data_path)
		
		logFileName = os.sep.join([_log_path,'%s_%s.log' % (_utils.timeStamp().replace(':','-'),name)])

		_logLogging = CustomLog(sys.stdout)
		
		standardLogging.standardLogging(logFileName,_level=_logging,console_level=logging.INFO,isVerbose=_isVerbose)

		if (_isCustomlog):
		    _logLogging.logging = logging # echos the log back to the standard logging...
		    logging = _logLogging # replace the default logging with our own custom logging...
		
		logging.info('Logging to "%s" using level of "%s:.' % (logFileName,standardLogging.explainLogging(_logging)))
	
		_stdOut = open(os.sep.join([_log_path,'stdout.txt']),'w')
		_stdErr = open(os.sep.join([_log_path,'stderr.txt']),'w')
		
		sys.stdout = Log(_stdOut)
		sys.stderr = Log(_stdErr)
	
		logging.warning('stdout to "%s".' % (_stdOut.name))
		logging.warning('stderr to "%s".' % (_stdErr.name))
		
		print >>sys.stdout, 'Command Line Arguments=%s' % (_argsObj)
	
		if (len(_username) > 0) and (len(_password) > 0):
		    logging.info('username is "%s", password is (%s) known and assumed to be valid.' % (_username,'*'*len(_password)))
		    try:
			from pyax_code.context import getSalesForceContext
			
			_ctx = getSalesForceContext()
			if (_isStaging):
			    _srvs = _ctx.get__login_servers()
			    print '_srvs=%s' % str(_srvs)
			    if (_srvs.has_key('production')) and (_srvs.has_key('sandbox')):
				_ctx.login_endpoint = _ctx.login_endpoint.replace(_srvs['production'],_srvs['sandbox'])
			    print '_ctx.login_endpoint=%s' % str(_ctx.login_endpoint)
			    if (not _username.endswith('.stag')):
				_username += '.stag'
				print '_username is "%s".' % (_username)
			elif (_isDemo) and (not _isStaging):
			    logging.error('Are you sure you really want to run this Demo in Production SalesForce ?  The developer did not think you would so try again...')
			    sys.exit(1)
			try:
			    sfdc = Connection.connect(_username, _password, context=_ctx)
			except Exception, details:
			    exc_info = sys.exc_info()
			    info_string = '\n'.join(traceback.format_exception(*exc_info))
			    print >>sys.stderr, '(%s) :: "%s". %s' % (misc.funcName(),str(details),info_string)
			    sfdc = None
			logging.info('sfdc=%s' % str(sfdc))
			if (sfdc is not None):
			    logging.info('sfdc.endpoint=%s' % str(sfdc.endpoint))
			    
			    ioTimeAnalysis.initIOTime('%s' % (__name__)) 
			    ioTimeAnalysis.initIOTime('SOQL') 
			    
			    if (_isBeingDebugged):
				runWithAnalysis(main,[sfdc])
			    else:
				import cProfile
				cProfile.run('runWithAnalysis(main,[sfdc,csv])', os.sep.join([_log_path,'profiler.txt']))
			else:
			    logging.error('Cannot login so cannot run demo. Sorry.')
			    sys.exit(1)
		    except NameError:
			exc_info = sys.exc_info()
			info_string = '\n'.join(traceback.format_exception(*exc_info))
			logging.error(info_string)
		    except AttributeError:
			exc_info = sys.exc_info()
			info_string = '\n'.join(traceback.format_exception(*exc_info))
			logging.error(info_string)
		    except ApiFault:
			exc_info = sys.exc_info()
			info_string = '\n'.join(traceback.format_exception(*exc_info))
			logging.error(info_string)
		else:
		    logging.error('Cannot figure-out what username (%s) and password (%s) to use so cannot continue. Sorry !' % (_username,_password))
	    else:
		print >> sys.stderr, 'ERROR: Missing the cwd parm which is the first parm on the command line.'
    
	else:
	    logging.error('You are using the wrong version of Python, you should be using 2.51 or later but you seem to be using "%s".' % sys.version)
	_msg = 'Done !!!!'
	logging.warning(_msg)
	print >> sys.stdout, _msg
	try:
	    _logLogging.close()
	    sys.stdout.close()
	    sys.stderr.close()
	except:
	    pass
	try:
	    sys.exit()
	except:
	    pass
	    

