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

from vyperlogix.classes.CooperativeClass import Cooperative

from vyperlogix.sf import update

from vyperlogix.misc import Args
from vyperlogix.misc import PrettyPrint

from vyperlogix.aima import utils

from vyperlogix import oodb

import traceback
import Queue
from stat import *

from sfConstant import BAD_INFO_LIST

from crypto import *
from runWithAnalysis import *

from sfUtil_win32 import *

csv_fname = ""

_isVerbose = False
_csvPath = ''
_logging = logging.WARNING

is_platform_not_windows = lambda _sys:(_sys.platform != 'win32')
bool_is_platform_not_windows = is_platform_not_windows(sys)

_isBeingDebugged = (os.environ.has_key('WINGDB_ACTIVE')) # When debugger is being used we do not use threads...

_isVerbose = False

def exception_callback(sections):
    _msg = 'EXCEPTION Causing Abend.\n%s' % '\n'.join(sections)
    print >>sys.stdout, _msg
    print >>sys.stderr, _msg
    logging.error('(%s) :: %s' % (_utils.funcName(),_msg))
    sys.stdout.close()
    sys.stderr.close()
    sys.exit(0)
    
class Bitset(Cooperative):
    def __init__(self,data):
	self.__data__ = data
	
    def testBit(self,n):
	i = n >> 3
	ch = self.__data__[i]
	v = ord(ch)
	t = (0x80 >> n % 8)
	x = v & t
	return (x != 0)
    
    def __str__(self):
	s = ''
	b = []
	for i in xrange(0,len(self)):
	    _n = self.testBit(i)
	    b.append('1' if (_n) else '0')
	    if (len(b) == 8):
		s += ''.join(b)
		s += ' '
		b = []
	return s

    def __len__(self):
	return len(self.__data__) * 8

def main(args):
    ioTimeAnalysis.ioBeginTime('%s' % (__name__))
    try:
	sfdc = args[0]
	
	d = sfdc.describeSObject('Case')
	flds = d.metadata['fields']
	for k,f in flds.iteritems():
	    if (k != 'Component__c'):
		continue
	    _hasValues = False
	    if (f.has_key('dependentPicklist')) and (f['dependentPicklist'] == True):
		controller_name = '' if (not f.has_key('controllerName')) else f['controllerName']
		if (flds.has_key(controller_name)):
		    f_controller = flds[controller_name]
		    controller_picklistValues = f_controller['picklistValues'].keys()
		    values = [] if (not f.has_key('picklistValues')) else f['picklistValues']
		    f_type = '' if (not f.has_key('type')) else f['type']
		    print '%s:' % (controller_name)
		    if (f_type == 'picklist'):
			_keys = values.keys()
			_keys.sort()
			for _k in _keys:
			    v = values[_k]
			    if (v):
				v_validFor = '' if (not v.has_key('validFor')) else v['validFor']
				if (v_validFor) and (len(v_validFor) > 0):
				    bset = Bitset(v_validFor)
				    if (v['active']):
					print '%s, %s, "%s", %s, %s' % (_k,'Active' if (v['active']) else 'Not Active',v_validFor,len(bset),str(bset))
					d_mapping = lists.HashedLists()
					for i in xrange(0,len(bset)):
					    _n = bset.testBit(i)
					    if (_n):
						try:
						    _value = f_controller['picklistValues'][controller_picklistValues[i]]['value']
						    _label = f_controller['picklistValues'][controller_picklistValues[i]]['label']
						    d_mapping[_label] = _value
						    #print '%s at %s is "%s" has ("%s","%s").' % (k,i,_k,_label,_value)
						    _hasValues = True
						except IndexError, details:
						    #print 'ERROR: %s is out of range (%s) and (%s).' % (i,len(controller_picklistValues),len(values))
						    pass
					d_keys = d_mapping.keys()
					d_keys.sort()
					print '%s' % (_k)
					for d_k in d_keys:
					    print '\t%s' % (d_k)
				    pass
			    print '-'*30
			    print ''
			    pass
			pass
		    else:
			print '+++ f_type is "%s".' % (f_type)
		else:
		    print 'Cannot determine mappings for controller named "%s".' % (controller_name)
	    if (_hasValues):
		print '='*80
		print ''
	    pass
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
	    }
    _argsObj = Args.Args(args)
    if (_isVerbose):
	print '_argsObj=(%s)' % str(_argsObj)

    if (len(sys.argv) == 1):
	ppArgs()

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

    d_passwords = lists.HashedLists2()
    
    s = ''.join([chr(ch) for ch in [126,254,192,145,170,209,4,52,159,254,122,198,76,251,246,151]])
    pp = ''.join([ch for ch in decryptData(s).strip() if ord(ch) > 0])
    d_passwords['rhorn@molten-magma.com'] = [pp.replace('@','').replace('$',''),None]
    
    s = ''.join([chr(ch) for ch in [39,200,142,151,251,164,142,15,45,216,225,201,121,177,89,252]])
    pp = ''.join([ch for ch in decryptData(s).strip() if ord(ch) > 0])
    d_passwords['sfscript@molten-magma.com'] = [pp, None]

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
	
	print 'sys.argv=%s' % sys.argv
	
	_cwd = os.path.dirname(sys.argv[0])
	print '_cwd=%s' % _cwd
	
	if (len(_cwd) > 0) and (os.path.exists(_cwd)):
	    name = _utils.getProgramName()
	    
	    _log_path = _utils.safely_mkdir(fpath=_cwd,dirname='logs')
	    
	    if (d_passwords.has_key(_username)):
		_password = d_passwords[_username]
	    else:
		_password = []
	    if (len(_username) > 0) and (len(_password) > 0):
		logging.info('username is "%s", password is known and valid.' % (_username))
		try:
		    if (len(_password) == 1) or (_password[-1] is None):
			sfdc = Connection.connect(_username, _password[0])
		    else:
			sfdc = Connection.connect(_username, _password[0], _password[-1])
		    logging.info('sfdc=%s' % str(sfdc))
		    logging.info('sfdc.endpoint=%s' % str(sfdc.endpoint))
		    
		    ioTimeAnalysis.initIOTime('%s' % (__name__)) 
		    ioTimeAnalysis.initIOTime('SOQL') 

		    if (_isBeingDebugged):
			runWithAnalysis(main,[sfdc])
		    else:
			import cProfile
			cProfile.run('runWithAnalysis(main,[sfdc])', os.sep.join([_log_path,'profiler.txt']))
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
	

