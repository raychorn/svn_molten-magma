""" 
This is the Magma Users Walker Process - handles those files that look like this "Headcount Report - November 2008 120108 LA.XLS".

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
from vyperlogix.misc import ObjectTypeName

from vyperlogix.hash.lists import HashedLists2

from vyperlogix.hash.lists import HashedFuzzyLists2

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

summary_report_log = None
summary_rollup_report_log = None
summary_rollup_detailed_report_log = None

cname = _utils.getComputerName().lower()
_isRunningLocal_at_work = (cname.find('.moltenmagma.com') > -1) or (cname in ['undefined3', 'sql2005'])

_isVerbose = False
_csvPath = ''
_logging = logging.WARNING

is_platform_not_windows = lambda _sys:(_sys.platform != 'win32')
bool_is_platform_not_windows = is_platform_not_windows(sys)

_isBeingDebugged = (os.environ.has_key('WINGDB_ACTIVE')) # When debugger is being used we do not use threads...

_proc_queue = Queue.Queue(750) if (_isBeingDebugged) else threadpool.ThreadQueue(750)

_isVerbose = False

_csv_model = CSV()

_email_col_name = 'email'

def exception_callback(sections):
    _msg = 'EXCEPTION Causing Abend.\n%s' % '\n'.join(sections)
    print >>sys.stdout, _msg
    print >>sys.stderr, _msg
    logging.error('(%s) :: %s' % (misc.funcName(),_msg))
    _logLogging.close()
    sys.stdout.close()
    sys.stderr.close()
    sys.exit()

def process_data(sfdc,csv_model,iCol):
    '''
    Not on the list but in SF - make inactive, flag in log file and email Stan.
        Grab list of all users and determine if the user is on the list.
    (x) On list but not in SF - flag in log and email stan.
    (x) On list but not Active - make active but email Stan.
    '''
    from vyperlogix.classes.SmartObject import SmartFuzzyObject
    records = csv_model.rowsAsRecords(dict2_factory=SmartFuzzyObject)

    from vyperlogix.sf.sf import SalesForceQuery
    sfQuery = SalesForceQuery(sfdc)
    
    from vyperlogix.sf.users import SalesForceUsers
    users = SalesForceUsers(sfQuery)
    
    from vyperlogix.sf.contacts import SalesForceContacts
    contacts = SalesForceContacts(sfQuery)
    
    from vyperlogix.sf.accounts import SalesForceAccounts
    accounts = SalesForceAccounts(sfQuery)
    
    account_name_tokens = list(set('Magma Design Automation'.split()))
    
    logging.info('(%s) :: BEGIN :: Get All Active Users.' % (misc.funcName()))
    all_users = users.getAllActiveUsers()
    d_users_by_id = HashedFuzzyLists2()
    d_users_by_email = HashedFuzzyLists2()
    if (users.contains_sf_objects(all_users)):
	for aUser in all_users:
	    d_users_by_id[aUser['Id']] = aUser
	    d_users_by_email[aUser['Email']] = aUser
    logging.info('(%s) :: END! :: Get All Active Users.' % (misc.funcName()))
    
    logging.info('(%s) :: BEGIN :: Get All Magma Users.' % (misc.funcName()))
    all_magma_users = users.getAllMagmaUsers()
    d_magma_users_by_id = HashedFuzzyLists2()
    d_magma_users_by_email = HashedFuzzyLists2()
    if (users.contains_sf_objects(all_magma_users)):
	for aUser in all_magma_users:
	    d_magma_users_by_id[aUser['Id']] = aUser
	    d_magma_users_by_email[aUser['Email']] = aUser
    logging.info('(%s) :: END! :: Get All Magma Users.' % (misc.funcName()))
    
    users_keys = d_users_by_id.keys()
    magma_users_keys = d_magma_users_by_id.keys()
    errant_users = []
    if (len(users_keys) > len(magma_users_keys)):
	errant_users = list(set(users_keys) - set(magma_users_keys))
    else:
	errant_users = list(set(magma_users_keys) - set(users_keys))

    d_errant_users_by_id = HashedFuzzyLists2()
    d_errant_users_by_email = HashedFuzzyLists2()
    for aUserId in errant_users:
	if (len(users_keys) > len(magma_users_keys)):
	    aUser = d_users_by_id[aUserId]
	    d_errant_users_by_id[aUserId] = aUser
	    d_errant_users_by_email[aUser['Email']] = aUser
	else:
	    aUser = d_magma_users_by_id[aUserId]
	    d_errant_users_by_id[aUserId] = aUser
	    d_errant_users_by_email[aUser['Email']] = aUser
	
    d_bad_Account_spec = {}
    d_bad_Account_Name = {}
    d_missing_Account = {}
    d_is_in_SalesForce_but_not_Active = {}
    d_not_in_SalesForce_but_on_Employee_List = {}
    d_in_SalesForce_but_not_on_Employee_List = {}
    
    try:
	for record in records:
	    logging.info('(%s) :: Considering "%s".' % (misc.funcName(),record.email))
	    if (len(record.email) > 0):
		aUser = d_users_by_email[record.email]
		logging.info('(%s) :: Email is "%s" --> User is "%s".' % (misc.funcName(),record.email, aUser))
		if (aUser is not None):
		    try:
			aContact = contacts.getContactsByEmail(record.email)
			logging.info('(%s) :: Contact is "%s".' % (misc.funcName(),aContact))
			if (contacts.contains_sf_objects(aContact)):
			    anAccount = accounts.getAccountById(aContact[0]['AccountId'])
			    logging.info('(%s) :: Account is "%s".' % (misc.funcName(),anAccount))
			    if (accounts.contains_sf_objects(anAccount)):
				# Make sure the account is in the Magma Account Tree.
				tree = accounts.m_getAccountTree(anAccount[0])
				aNode = tree.findForwards(Id=anAccount[0]['Id'])
				if (aNode is None):
				    if (not d_bad_Account_spec.has_key(record.email)):
					d_bad_Account_spec[record.email] = aUser
				    info_string = 'User "%s" has a bad Account specification.  Kindly update SalesForce to correct this problem.' % (record.email)
				    logging.warning('(%s) :: %s' % (misc.funcName(),info_string))
				    print >>summary_report_log, info_string
				else:
				    name_tokens = list(set(aNode.Name.split()))
				    if (not all([t in account_name_tokens for t in name_tokens])):
					if (not d_bad_Account_Name.has_key(record.email)):
					    d_bad_Account_Name[record.email] = aUser
					info_string = 'User "%s" has a bad Account Name because it does not contain all the tokens from "%s" because it is composed of "%s".  Kindly update SalesForce to correct this problem.' % (record.email,account_name_tokens,name_tokens)
					logging.warning('(%s) :: %s' % (misc.funcName(),info_string))
					print >>summary_report_log, info_string
			    else:
				if (not d_missing_Account.has_key(record.email)):
				    d_missing_Account[record.email] = aUser
				info_string = 'User "%s" has no Account Name at-all.  Kindly update SalesForce to correct this problem.' % (record.email)
				logging.warning('(%s) :: %s' % (misc.funcName(),info_string))
				print >>summary_report_log, info_string
			if (not aUser['IsActive']):
			    if (not d_is_in_SalesForce_but_not_Active.has_key(record.email)):
				d_is_in_SalesForce_but_not_Active[record.email] = aUser
			    info_string = 'User "%s" is in SalesForce but is not Active. Kindly update this User in SalesForce.' % (record.email)
			    logging.warning('(%s) :: %s' % (misc.funcName(),info_string))
			    print >>summary_report_log, info_string
		    except Exception, details:
			info_string = _utils.formattedException(details=details)
			logging.warning('(%s) :: %s' % (misc.funcName(),info_string))
		else:
		    if (not d_not_in_SalesForce_but_on_Employee_List.has_key(record.email)):
			d_not_in_SalesForce_but_on_Employee_List[record.email] = aUser
		    info_string = 'Cannot locate a User record in SalesForce for "%s" for a User that is on the Magma Employee List. Kindly update your Magma Employee List.' % (record.email)
		    logging.warning('(%s) :: %s' % (misc.funcName(),info_string))
		    print >>summary_report_log, info_string
	retired = []
	for record in records:
	    if (len(record.email) > 0):
		aUser = d_users_by_email[record.email]
		if (aUser is not None):
		    retired.append(record.email)
	for item in retired:
	    print 'Removing "%s" from the users by email list because this user is on the Roster.' % (record.email)
	    del d_users_by_id[d_users_by_email[item]['Id']]
	    del d_users_by_email[item]
	for k,v in d_users_by_email.iteritems():
	    if (not d_in_SalesForce_but_not_on_Employee_List.has_key(k)):
		d_in_SalesForce_but_not_on_Employee_List[k] = aUser
	    info_string = 'Cannot locate an Active User that is in SalesForce and not on the Magma Employee List for "%s".  Kindly update your Magma Employee List or make this user Inactive.' % (k)
	    logging.warning('(%s) :: %s' % (misc.funcName(),info_string))
	    print >>summary_report_log, info_string
    except Exception, details:
	info_string = _utils.formattedException(details=details)
	logging.warning('(%s) :: %s' % (misc.funcName(),info_string))

    def report_rollup(d,name,detailed=False,fOut=sys.stdout):
	try:
	    print >>fOut, 'BEGIN: %s' % (name)
	    for k,v in d.iteritems():
		print >>fOut, '\t%s%s' % (k,'' if (not detailed) else ' --> %s' % (str(v)))
	    print >>fOut, 'END:   %s' % (name)
	    print >>fOut, '\n\n'
	except Exception, details:
	    info_string = _utils.formattedException(details=details)
	    logging.warning('(%s) :: %s' % (misc.funcName(),info_string))
    
    report_rollup(d_bad_Account_spec,'Bad Account Spec',fOut=summary_rollup_report_log)
    report_rollup(d_bad_Account_Name,'Bad Account Name',fOut=summary_rollup_report_log)
    report_rollup(d_missing_Account,'Missing Account in User',fOut=summary_rollup_report_log)
    report_rollup(d_is_in_SalesForce_but_not_Active,'User is not Active in SalesForce',fOut=summary_rollup_report_log)
    report_rollup(d_not_in_SalesForce_but_on_Employee_List,'User not in SalesForce but on Employee List',fOut=summary_rollup_report_log)
    report_rollup(d_in_SalesForce_but_not_on_Employee_List,'User in SalesForce but not on Employee List',fOut=summary_rollup_report_log)

    report_rollup(d_bad_Account_spec,'Bad Account Spec',fOut=summary_rollup_detailed_report_log,detailed=True)
    report_rollup(d_bad_Account_Name,'Bad Account Name',fOut=summary_rollup_detailed_report_log,detailed=True)
    report_rollup(d_missing_Account,'Missing Account in User',fOut=summary_rollup_detailed_report_log,detailed=True)
    report_rollup(d_is_in_SalesForce_but_not_Active,'User is not Active in SalesForce',fOut=summary_rollup_detailed_report_log,detailed=True)
    report_rollup(d_not_in_SalesForce_but_on_Employee_List,'User not in SalesForce but on Employee List',fOut=summary_rollup_detailed_report_log,detailed=True)
    report_rollup(d_in_SalesForce_but_not_on_Employee_List,'User in SalesForce but not on Employee List',fOut=summary_rollup_detailed_report_log,detailed=True)
    
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
		_csv_model.filename = _input
		headers = ListWrapper([name.lower() for name in _csv_model.header])
		i = headers.findFirstContaining(_email_col_name.lower())
		if (i > -1):
		    process_data(sfdc,_csv_model,i)
		else:
		    info_string = 'Cannot find a header named "%s".' % (_email_col_name)
		    logging.error('(%s) :: %s' % (misc.funcName(),info_string))
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
		
		_summary_report_log = open(os.sep.join([_log_path,'summary_report.txt']),'w')
		summary_report_log = Log(_summary_report_log)
		
		_summary_rollup_report_log = open(os.sep.join([_log_path,'summary_rollup_report.txt']),'w')
		summary_rollup_report_log = Log(_summary_rollup_report_log)
		
		_summary_rollup_detailed_report_log = open(os.sep.join([_log_path,'summary_rollup_detailed_report.txt']),'w')
		summary_rollup_detailed_report_log = Log(_summary_rollup_detailed_report_log)
	
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
				cProfile.run('runWithAnalysis(main,[sfdc])', os.sep.join([_log_path,'profiler.txt']))
			else:
			    logging.error('Cannot login so cannot process Headcount. Sorry.')
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
	    

