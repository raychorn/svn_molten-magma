""" 
This is the Contacts Walker Process

caveats:

* email address is assumed to be case-insensitive in SalesForce
* some email addresses are duplicates within a single CSV file.

""" 
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

from vyperlogix.misc import _utils
from vyperlogix.daemon.daemon import Log
from vyperlogix.logging import standardLogging
from vyperlogix.hash import lists
from vyperlogix.misc import ObjectTypeName

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

from sfUtil_win32 import *

from vyperlogix.sf import update

csv_fname = ""

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
        logging.error('(%s) soql=%s, Reason: %s' % (_utils.funcName(),soql,info_string))
    return None

def exception_callback(sections):
    _msg = 'EXCEPTION Causing Abend.\n%s' % '\n'.join(sections)
    print >>sys.stdout, _msg
    print >>sys.stderr, _msg
    logging.error('(%s) :: %s' % (_utils.funcName(),_msg))
    sys.stdout.close()
    sys.stderr.close()
    sys.exit(0)

__getRealObjectsFromSOQL = True

def __getObjectsFromSOQL(sfdc,soql):
    try:
	ret = _sf_query(sfdc,soql)
	logging.info('(%s) soql=%s' % (_utils.funcName(),soql))
	if ret in BAD_INFO_LIST:
	    logging.warning("(%s) :: Could not find any Object(s) for SOQL of (%s)." % (_utils.funcName(),soql))
	else: 
	    logging.info("(%s) :: soql=%s." % (_utils.funcName(),soql))
	    objects = []
	    for k in ret.keys():
		v = ret[k]
		val = v if (__getRealObjectsFromSOQL) else lists.copyAsDict(v)
		objects.append(val if (__getRealObjectsFromSOQL) else val.asDict())
	    return objects
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))

    return None

def _getCRLinkByCrId(args):
    try:
	sfdc, id = args
	soql = "Select c.Account__c, c.Description__c, c.Id, c.Name, c.Parent_CR__c from CR_Link__c c where c.Parent_CR__c = '%s'" % (id)
	objs = __getObjectsFromSOQL(sfdc,soql)
	if objs in BAD_INFO_LIST:
	    logging.warning("(%s) :: Could not find any CR_Link__c Object(s) for id of %s." % (_utils.funcName(),id))
	return objs
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))

    return None
    
def getCRLinkByCrId(args): 
    return _getCRLinkByCrId(args)

def _getCrByCaseNumber(args):
    try:
	sfdc, caseNumber = args
	soql = "Select c.CaseNumber, c.CR_Number__c, c.Id from Case c  where c.CaseNumber = '%s'" % (caseNumber)
	objs = __getObjectsFromSOQL(sfdc,soql)
	if objs in BAD_INFO_LIST:
	    logging.warning("(%s) :: Could not find any Case Object(s) for caseNumber of %s." % (_utils.funcName(),caseNumber))
	return objs
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))

    return None
    
def getCrByCaseNumber(args): 
    return _getCrByCaseNumber(args)

def main(args):
    email_from_row = lambda row:row[_analysisColNum].strip().lower()
    
    ioTimeAnalysis.ioBeginTime('%s' % (__name__))
    try:
	sfdc, csv = args
	
	files = []
	
	if (len(csv.rows) > 0):
	    for row in csv.rows:
		caseNum = row[_analysisColNum]
		if (len(caseNum) > 0) and (caseNum != 'MISSING'):
		    crs = getCrByCaseNumber((sfdc,caseNum))
		    if (crs is not None):
			for cr in crs:
			    id = cr['Id']
			    links = getCRLinkByCrId((sfdc,id))
			    if (links is not None):
				for link in links:
				    if (_isVerbose):
					lists.prettyPrint(link,'\t',title='CR_Link__c for %s via %s' % (id,caseNum),fOut=sys.stdout)
				    if (_col2rename is not None) and (len(_col2rename) > 0):
					if (link[_col2rename].find(_oldValue) > -1):
					    if (_isCommit):
						print >>sys.stdout, 'Committed Change :: Rename CRLink with Id of "%s" from "%s" to "%s".' % (link['Id'],link[_col2rename],link[_col2rename].replace(_oldValue,_newValue))
						link[_col2rename] = link[_col2rename].replace(_oldValue,_newValue)
						update.updateSalesForceObject(link)
					    else:
						print >>sys.stdout, 'UnCommitted Change :: Rename CRLink with Id of "%s" from "%s" to "%s".' % (link['Id'],link[_col2rename],link[_col2rename].replace(_oldValue,_newValue))
					    print >>sys.stdout, ''
					    pass
					else:
					    if (_isVerbose):
						print >>sys.stdout, 'No Change :: CRLink with Id of "%s" from "%s" to "%s".' % (link['Id'],link[_col2rename],link[_col2rename].replace(_oldValue,_newValue))
						print >>sys.stdout, ''
				    pass
			    else:
				print >>sys.stderr, 'WARNING: Missing data for Case Id of "%s".' % (id)
		    else:
			print >>sys.stderr, 'WARNING: Missing data for caseNum of "%s".' % (caseNum)
	pass
	
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.error('(%s) :: %s' % (_utils.funcName(),info_string))

    ioTimeAnalysis.ioEndTime('%s' % (__name__))
    logging.info('(%s) :: %s' % (_utils.funcName(),ioTimeAnalysis.ioTimeAnalysisReport()))

if __name__ == "__main__": 
    def ppArgs():
	pArgs = [(k,args[k]) for k in args.keys()]
	pPretty = PrettyPrint.PrettyPrint('',pArgs,True,' ... ')
	pPretty.pprint()

    args = {'--help':'displays this help text.',
	    '--verbose':'output more stuff.',
	    '--csv=?':'name the path to the csv file (must be a simple csv file).',
	    '--xls=?':'name the path to the xls file.',
	    '--headers':'default is False however if this option is used the CSV headers are placed at the top of all output files.',
	    '--colname=?':'name the column in the source file to use, such as "email".',
	    '--old=?':'specify the old value or the value to rename.',
	    '--new=?':'specify the new value or the value the old value is to become.',
	    '--col2rename=?':'name the column in the source file to use for the rename function, such as "Name".',
	    '--commit':'use this option to commit changes to SalesForce.',
	    '--folder=?':'names the folder in which the logs and data will reside.',
	    '--logging=?':'[logging.INFO,logging.WARNING,logging.ERROR,logging.DEBUG]',
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
	    print >>sys.stderr, '(%s) :: %s' % (_utils.funcName(),info_string)
	    _isVerbose = False
	    
	_isCommit = False
	try:
	    if _argsObj.booleans.has_key('isCommit'):
		_isCommit = _argsObj.booleans['isCommit']
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    print >>sys.stderr, '(%s) :: %s' % (_utils.funcName(),info_string)
	    _isCommit = False

	_isHeaders = False
	try:
	    if _argsObj.booleans.has_key('isHeaders'):
		_isHeaders = _argsObj.booleans['isHeaders']
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    print >>sys.stderr, '(%s) :: %s' % (_utils.funcName(),info_string)
	    _isHeaders = False

	__folder = os.path.dirname(sys.argv[0])
	try:
	    __folder = _argsObj.arguments['folder'] if _argsObj.arguments.has_key('folder') else ''
	    if (len(__folder) == 0) or (not os.path.exists(__folder)):
		if (os.environ.has_key('cwd')):
		    __folder = os.environ['cwd']
	except:
	    pass
	_folderPath = __folder
	
	_colname = ''
	try:
	    _colname = _argsObj.arguments['colname'] if _argsObj.arguments.has_key('colname') else ''
	except:
	    pass
	
	_oldValue = ''
	try:
	    _oldValue = _argsObj.arguments['old'] if _argsObj.arguments.has_key('old') else ''
	except:
	    pass
	
	_newValue = ''
	try:
	    _newValue = _argsObj.arguments['new'] if _argsObj.arguments.has_key('new') else ''
	except:
	    pass
	
	_col2rename = ''
	try:
	    _col2rename = _argsObj.arguments['col2rename'] if _argsObj.arguments.has_key('col2rename') else ''
	except:
	    pass
	
	_csvPath = ''
	_analysisData = []
	_analysisColNum = -1
	try:
	    if _argsObj.arguments.has_key('csv'):
		f = _argsObj.arguments['csv']
		if (os.path.exists(f)):
		    if (os.path.isdir(f)):
			_csvPath = f
		    else:
			try:
			    csv = CSV(f)
			    csv_header_toks = [(t.split(),t) for t in csv.header]
			    _target_toks = _colname.split()
			    isFound = None
			    for tt in _target_toks:
				for t in csv_header_toks:
				    if (tt in t[0]):
					isFound = t[-1]
					break
			    if (isFound):
				try:
				    _analysisData = csv.column(isFound)
				    _analysisColNum = csv.header.index(isFound)
				    _csvPath = f
				except ValueError:
				    print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not appear to contain any data in the column(s) in which the tokens %s appears in row 1 although this file appears to be a valid Excel file type.' % (f,_target_toks)
			    else:
				print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not appear to contain any columns in which the tokens %s appears in row 1 although this file appears to be a valid Excel file type.' % (f,_target_toks)
			except ValueError:
			    print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not appear to be a valid Excel file type.' % (f)
		else:
		    print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not exist.' % (f)
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    print >>sys.stderr, '(%s) :: %s' % (_utils.funcName(),info_string)
	    _isAnalysis = False
	    
	try:
	    if _argsObj.arguments.has_key('xls'):
		f = _argsObj.arguments['xls']
		if (os.path.exists(f)):
		    if (os.path.isdir(f)):
			_csvPath = f
		    else:
			try:
			    isFound = None
			    import xlrd
			    book = xlrd.open_workbook(f)
			    l = book.name_obj_list()
			    pass
			    if (isFound):
				try:
				    _analysisData = csv.column(isFound)
				    _csvPath = f
				except ValueError:
				    print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not appear to contain any data in the column(s) in which the tokens %s appears in row 1 although this file appears to be a valid Excel file type.' % (f,_target_toks)
			    else:
				print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not appear to contain any columns in which the tokens %s appears in row 1 although this file appears to be a valid Excel file type.' % (f,_target_toks)
			except ValueError:
			    print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not appear to be a valid Excel file type.' % (f)
		else:
		    print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not exist.' % (f)
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    print >>sys.stderr, '(%s) :: %s' % (_utils.funcName(),info_string)
	    _isAnalysis = False
	    
	try:
	    _logging = eval(_argsObj.arguments['logging']) if _argsObj.arguments.has_key('logging') else False
	except:
	    _logging = logging.WARNING

	d_passwords = lists.HashedLists2()
	
	s = ''.join([chr(ch) for ch in [126,254,192,145,170,209,4,52,159,254,122,198,76,251,246,151]])
	pp = ''.join([ch for ch in decryptData(s).strip() if ord(ch) > 0])
	d_passwords['rhorn@molten-magma.com'] = [pp,'NHZ3awCqrcoLt1MVG4n3on9z']
	
	s = ''.join([chr(ch) for ch in [39,200,142,151,251,164,142,15,45,216,225,201,121,177,89,252]])
	pp = ''.join([ch for ch in decryptData(s).strip() if ord(ch) > 0])
	d_passwords['sfscript@molten-magma.com'] = [pp]
    
	print 'sys.version=[%s]' % sys.version
	v = _utils.getFloatVersionNumber()
	if (v >= 2.51):
	    #print 'sys.path=[%s]' % '\n'.join(sys.path)
	    if (not _isBeingDebugged):
		from vyperlogix.handlers.ExceptionHandler import *
		excp = ExceptionHandler()
		excp.callback = exception_callback
    
	    from vyperlogix.misc._psyco import *
	    importPsycoIfPossible(func=main,isVerbose=True)
    
	    _username = 'rhorn@molten-magma.com'
	    
	    #ep = encryptData('...')
	    #print 'ep=[%s]' % asReadableData(ep)
	    
	    print 'sys.argv=%s' % sys.argv
	    
	    _cwd = _folderPath
	    print '_cwd=%s' % _cwd
	    
	    if (len(_cwd) > 0) and (os.path.exists(_cwd)):
		name = _utils.getProgramName()
		
		if (os.path.exists(_folderPath)):
		    _log_path = _utils.safely_mkdir(fpath=_folderPath)
		else:
		    _log_path = _utils.safely_mkdir(fpath=_cwd)
		
		logFileName = os.sep.join([_log_path,'%s_%s.log' % (_utils.timeStamp().replace(':','-'),name)])
		
		standardLogging.standardLogging(logFileName,_level=_logging,isVerbose=_isVerbose)
		
		logging.info('Logging to "%s" using level of "%s:.' % (logFileName,standardLogging.explainLogging(_logging)))
	
		_stdOut = open(os.sep.join([_log_path,'stdout.txt']),'w')
		_stdErr = open(os.sep.join([_log_path,'stderr.txt']),'w')
		
		sys.stdout = Log(_stdOut)
		sys.stderr = Log(_stdErr)
	
		logging.warning('stdout to "%s".' % (_stdOut.name))
		logging.warning('stderr to "%s".' % (_stdErr.name))
		
		print >>sys.stdout, 'Command Line Arguments=%s' % (_argsObj)
	
		if (d_passwords.has_key(_username)):
		    _password = d_passwords[_username]
		else:
		    _password = []
		if (len(_username) > 0) and (len(_password) > 0):
		    logging.info('username is "%s", password is known and valid.' % (_username))
		    try:
			sfdc = Connection.connect(_username, _password[0])
			logging.info('sfdc=%s' % str(sfdc))
			logging.info('sfdc.endpoint=%s' % str(sfdc.endpoint))
			
			ioTimeAnalysis.initIOTime('%s' % (__name__)) 
			ioTimeAnalysis.initIOTime('SOQL') 

			if (_isBeingDebugged):
			    runWithAnalysis(main,[sfdc,csv])
			else:
			    import cProfile
			    cProfile.run('runWithAnalysis(main,[sfdc,csv])', os.sep.join([_log_path,'profiler.txt']))
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
	_msg = 'Done !'
	logging.warning(_msg)
	print >> sys.stdout, _msg
	sys.stdout.close()
	sys.stderr.close()
	sys.exit(0)
	    

