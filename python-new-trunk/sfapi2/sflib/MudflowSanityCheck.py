import os, sys, traceback
import logging

from pyax.connection import Connection
from pyax.exceptions import ApiFault

from vyperlogix.daemon.daemon import Log
from vyperlogix.logging import standardLogging
from vyperlogix.hash import lists
from vyperlogix.misc import ObjectTypeName
from vyperlogix.misc import _utils
from vyperlogix.misc.ReportTheList import reportTheList

from vyperlogix.lists.ListWrapper import ListWrapper

from vyperlogix.misc import Args
from vyperlogix.misc import PrettyPrint

from vyperlogix.misc import LazyImport
sfConstant = LazyImport.LazyImport('sfConstant',locals={},globals={})

from vyperlogix.xml import xml_utils

from crypto import *

import runWithAnalysis

_isVerbose = False

_isBeingDebugged = _utils.isBeingDebugged # When debugger is being used we do not use threads...

def _sf_query(sfdc,soql):
    try:
	runWithAnalysis.begin_AnalysisDataPoint('SOQL') 
	ret = sfdc.query(soql)
	runWithAnalysis.end_AnalysisDataPoint('SOQL') 
        return ret
    except ApiFault:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
	info_string = asMessage('soql=%s, Reason: %s' % (soql,info_string))
	print >>sys.stderr, info_string
        logging.error(info_string)
        return None

def _getTaskBranchByName(args):
    name, sfdc = args
    runWithAnalysis.count_query()
    soql="Select t.Branch__c, t.Id, t.Name from Task_Branch__c t where t.Name = '%s'" % name
    ret = _sf_query(sfdc,soql)
    if ret in sfConstant.BAD_INFO_LIST:
	logging.info("(%s) :: Could not find any Task_Branch__c Object(s) for name of %s." % (_utils.funcName(),name))
    else: 
        logging.info('(%s) soql=%s' % (_utils.funcName(),soql))
	return ret
    return None

def getTaskBranchByName(args):
    return _getTaskBranchByName(args)

def _getBranchApprovalsForTaskBranchId(args):
    id, sfdc = args
    runWithAnalysis.count_query()
    soql="Select b.Approval_Role__c, b.Approval_Action__c, b.Branch__c, b.Component__c, b.Id, b.OwnerId, b.Name, b.Task_Branch__c, b.Team_Branch__c from Branch_Approval__c b where b.Task_Branch__c = '%s'" % id
    ret = _sf_query(sfdc,soql)
    if ret in sfConstant.BAD_INFO_LIST:
	logging.info("(%s) :: Could not find any Branch_Approval__c Object(s) for name of %s." % (_utils.funcName(),id))
    else: 
        logging.info('(%s) soql=%s' % (_utils.funcName(),soql))
	return ret
    return None

def getBranchApprovalsForTaskBranchId(args):
    return _getBranchApprovalsForTaskBranchId(args)

def exception_callback(sections):
    _msg = 'EXCEPTION Causing Abend.\n%s' % '\n'.join(sections)
    print >>sys.stdout, _msg
    print >>sys.stderr, _msg
    sys.exit(1)

from vyperlogix.decorators import onexit
@onexit.onexit
def _onExit():
    print >>sys.stdout, '(%s) :: Exiting...' % (_utils.funcName())

def main(args):
    from xml.dom.minidom import parse, parseString
    
    sfdc, fname = args
    fIn = open(fname, 'r')
    try:
	xml = fIn.readlines()
    finally:
	fIn.close()
    d_required_approvals = lists.HashedLists()
    dom = parseString(''.join(xml))
    for child in dom.childNodes:
	name = xml_utils.decodeUnicode(child.nodeName)
	attrs = xml_utils.getAttrsFromNode(child)
	brName = attrs['branch']
	print 'name=%s, attrs=%s' % (name,attrs)
	print '\tbrName=%s' % (brName)
	task_branches = getTaskBranchByName([brName,sfdc])
	if (task_branches not in sfConstant.BAD_INFO_LIST):
	    for brId in task_branches.keys():
		# get the branch approvals for this branch.
		approvals = getBranchApprovalsForTaskBranchId([brId,sfdc])
		if (approvals not in sfConstant.BAD_INFO_LIST):
		    for approval in approvals:
			if (approval['Approval_Role__c'] == 'Partition Reviewer'):
			    toks = approval['Name'].split(':')
			    d_required_approvals[toks[-1].strip()] = approval
			    pass
			pass
		    pass
		pass
	    pass
	print ''
	d_missing_approvals = lists.HashedLists()
	for _child in child.childNodes:
	    _name = xml_utils.decodeUnicode(_child.nodeName)
	    #print '\t_name=%s' % (_name)
	    if (_name == 'partition_violation'):
		_attrs = xml_utils.getAttrsFromNode(_child)
		#print '\t\t_name=%s, _attrs=%s' % (_name,_attrs)
		d_nodes = lists.HashedLists2()
		for __child in _child.childNodes:
		    __name = xml_utils.decodeUnicode(__child.nodeName)
		    __text = xml_utils.getAllNodeText(__child.childNodes)
		    if (len(__text) > 0):
			d_nodes[__name] = __text
		    pass
		#print '\t\t\td_nodes=%s' % (d_nodes)
		partitionName = d_nodes['partition']
		_isMissing = True
		if (d_required_approvals[partitionName]):
		    pass
		if (_isMissing):
		    d_missing_approvals[partitionName] = lists.HashedLists2(d_nodes.asDict())
		pass
	    pass
	print 'Required Partitions:'
	print '%s' % '\n\t'.join(d_required_approvals.keys())
	print
	print 'Missing Partitions:'
	print '%s' % '\n\t'.join(d_missing_approvals.keys())
	pass
    pass
    
if __name__ == "__main__": 
    def ppArgs():
	pArgs = [(k,args[k]) for k in args.keys()]
	pPretty = PrettyPrint.PrettyPrint('',pArgs,True,' ... ')
	pPretty.pprint()

    args = {'--help':'show some help.',
	    '--verbose':'output more stuff.',
	    '--xml=?':'name the xml input file.',
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
	    info_string = asMessage('\n'.join(traceback.format_exception(*exc_info)))
	    print >>sys.stderr, info_string
	    _isVerbose = False
	    
	_isHelp = False
	try:
	    if _argsObj.booleans.has_key('isHelp'):
		_isHelp = _argsObj.booleans['isHelp']
	except:
	    pass
	
	if (_isHelp):
	    ppArgs()
	
	_xmlIn = ''
	try:
	    if _argsObj.arguments.has_key('xml'):
		__xmlIn = _argsObj.arguments['xml']
		if (os.path.exists(__xmlIn)):
		    _xmlIn = __xmlIn
	except:
	    pass
	
	__cwd__ = os.path.dirname(sys.argv[0])
	_cwd = __cwd__
	
	d_passwords = lists.HashedLists2()
	
	s = ''.join([chr(ch) for ch in [126,254,192,145,170,209,4,52,159,254,122,198,76,251,246,151]])
	pp = ''.join([ch for ch in decryptData(s).strip() if ord(ch) > 0])
	d_passwords['rhorn@molten-magma.com'] = pp
	
	s = ''.join([chr(ch) for ch in [39,200,142,151,251,164,142,15,45,216,225,201,121,177,89,252]])
	pp = ''.join([ch for ch in decryptData(s).strip() if ord(ch) > 0])
	d_passwords['sfscript@molten-magma.com'] = pp
    
	print '_isBeingDebugged=%s' % _isBeingDebugged
	print 'sys.version=[%s]' % sys.version
	v = _utils.getFloatVersionNumber()
	if (v >= 2.51):
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
	    
	    print '_cwd=%s' % _cwd
	    
	    if (len(_cwd) > 0) and (os.path.exists(_cwd)):
		name = _utils.getProgramName()
		_log_path = _utils.safely_mkdir_logs(fpath=_cwd)
		_log_path = _utils.safely_mkdir(fpath=_log_path,dirname=_utils.timeStampLocalTimeForFileName(delimiters=('_')))
		# code a retention policy for _log_path
		_log_path = _utils.safely_mkdir(fpath=_log_path,dirname='logs')

		logFileName = os.sep.join([_log_path,'%s.log' % (name)])
		
		standardLogging.standardLogging(logFileName,_level=logging.INFO,console_level=logging.INFO,isVerbose=True)

		if (d_passwords.has_key(_username)):
		    _password = d_passwords[_username]
		else:
		    _password = ''
		if (len(_username) > 0) and (len(_password) > 0):
		    logging.warning('username is "%s", password is known and valid.' % (_username))
		    try:
			sfdc = Connection.connect(_username, _password)
			print 'sfdc=%s' % str(sfdc)
			print 'sfdc.endpoint=%s' % str(sfdc.endpoint)
			
			if (_isBeingDebugged):
			    runWithAnalysis.runWithAnalysis(main,[sfdc,_xmlIn])
			else:
			    import cProfile
			    cProfile.run('runWithAnalysis.runWithAnalysis(main,[sfdc,_xmlIn])', os.sep.join([_log_path,'profiler.txt']))
		    except AttributeError:
			exc_info = sys.exc_info()
			info_string = asMessage('\n'.join(traceback.format_exception(*exc_info)))
			print >>sys.stderr, info_string
			logging.warning(info_string)
		    except ApiFault:
			exc_info = sys.exc_info()
			info_string = asMessage('\n'.join(traceback.format_exception(*exc_info)))
			print >>sys.stderr, info_string
			logging.warning(info_string)
		else:
		    info_string = asMessage('Cannot figure-out what username (%s) and password (%s) to use so cannot continue. Sorry !' % (_username,_password))
		    print >>sys.stderr, info_string
		    logging.error(info_string)
	    else:
		info_string = asMessage('ERROR: Missing the cwd parm which is the first parm on the command line.')
		print >>sys.stderr, info_string
    
	else:
	    info_string = asMessage('You are using the wrong version of Python, you should be using 2.51 or later but you seem to be using "%s".' % sys.version)
	    print >>sys.stderr, info_string
	    logging.error(info_string)
    _msg = 'Done !'
    print >> sys.stdout, _msg
    sys.exit(1)

