""" 
This is the SCM Walker Process

--branch=talus1.0

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
from vyperlogix.misc.ReportTheList import reportTheList
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

import traceback
from stat import *

from sfConstant import BAD_INFO_LIST

from getLastProcessDate2 import getLastProcessDate2
from crypto import *
from runWithAnalysis import *

from sfUtil_win32 import *

csv_fname = "Z:\\@myMagma\\!Research WalkSCMTalus1.0\\branches in set33 24jun2008 IST for TAT estimate.csv"

_isVerbose = False
_branchName = None
_isReload = False
_isAnalysis = False
_isBrowse = False
_folderPath = ''
_analysisFolder = ''
_analysisData = []
_isTaskBranch__c = False
_task_branch__c = ''
_logging = logging.WARNING

dbx_Cases_fname = None
dbx_Team_Branch__c_fname = None
dbx_Task_Branch__c_fname = None
dbx_TaskBranches_fname = None
dbx_Checkpoint_Branch__c_fname = None
dbx_Task_Branches_by_Team_Branch_fname = None
dbx_Cases_for_Task_Branch__c_fname = None
dbx_Cases_by_Id_fname = None

is_platform_not_windows = lambda _sys:(_sys.platform != 'win32')
bool_is_platform_not_windows = is_platform_not_windows(sys)

path_conversion_matrix = lists.HashedLists2({'L:\\':'/magma/scm-release/submissions', 'R:\\':'/local/sfscript/SCM2/submissions'})

_left_path = 'L:\\' if (not bool_is_platform_not_windows) else path_conversion_matrix['L:\\']
_right_path = 'R:\\' if (not bool_is_platform_not_windows) else path_conversion_matrix['R:\\']

_isBeingDebugged = (os.environ.has_key('WINGDB_ACTIVE')) # When debugger is being used we do not use threads...

_isVerbose = False

_zeroPadCrNum = lambda foo:'%08d' % int(foo)

is_nocr = lambda s:str(s).find('nocr.') > -1

convert_windows_to_linux_path = lambda fpath:fpath.replace(_left_path,path_conversion_matrix[_left_path]).replace(_right_path,path_conversion_matrix[_right_path]).replace(os.sep,ros.os_sep)

def ros_stat(fpath):
    if (bool_is_platform_not_windows):
        return os.stat(fpath)
    fpath = convert_windows_to_linux_path(fpath)
    s = ros.os_stat(fpath)
    return s

def ros_lstat(fpath):
    if (bool_is_platform_not_windows):
        return os.lstat(fpath)
    fpath = convert_windows_to_linux_path(fpath)
    s = ros.os_lstat(fpath)
    return s

def zeroPadCrNum(cr):
    cr = str(cr)
    if (cr.isdigit()):
	return _zeroPadCrNum(cr)
    return cr

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

def collect_files_from_path(fpath,branch=''):
    d_files = lists.HashedLists2()
    if (os.path.exists(fpath)):
	for root, dirs, files in _utils.walk(fpath, topdown=True, rejecting_re=None):
	    for f in files:
		_fnameIn = os.sep.join([root,f])
		if (len(branch) > 0):
		    _name = [branch,_fnameIn.split(branch)[-1]]
		    _key = '%s%s' % (os.sep,''.join(_name))
		else:
		    _name = os.path.basename(_fnameIn)
		    _key = '%s' % (_name)
		d_files[_key] = _fnameIn
    else:
	logging.warning('(%s) :: The directory identified by "%s" cannot be found.' % (_utils.funcName(),fpath))
    return d_files

def _getTaskBranchesFromTeamBranchId(args):
    dbx = oodb.PickledHash2(dbx_Task_Branches_by_Team_Branch_fname,oodb.PickleMethods.useSafeSerializer)
    try:
	sfdc, team_branch_id = args
	dbx_key = '_'.join([team_branch_id])
	if (dbx.has_key(dbx_key)):
	    v = dbx[dbx_key]
	    dbx.close()
	    logging.info("(%s) :: Retrieved for key of %s the data object %s from cached dbx." % (_utils.funcName(),dbx_key,v))
	    return v
	soql = "Select b.Branch_Status__c, b.Id, b.Name, b.Task_Branch__c, b.Team__c, b.Team_Branch__c, b.User__c from Branch_Team_Link__c b WHERE (b.Team_Branch__c = '%s')" % (team_branch_id)
	ret = _sf_query(sfdc,soql)
	logging.info('(%s) soql=%s' % (_utils.funcName(),soql))
	if ret in BAD_INFO_LIST:
	    logging.warning("(%s) :: Could not find any Branch_Team_Link__c Object(s) for name of %s." % (_utils.funcName(),team_branch_id))
	else: 
	    logging.info("(%s) :: soql=%s." % (_utils.funcName(),soql))
	    _keys = ret.keys()
	    if (_keys):
		vals = []
		for k in _keys:
		    v = ret[k]
		    val = lists.copyAsDict(v)
		    vals.append(val.asDict())
		dbx[dbx_key] = vals
		dbx.sync()
		dbx.close()
		return v
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))

    dbx.close()
    return None
    
def getTaskBranchesFromTeamBranchId(args): 
    return _getTaskBranchesFromTeamBranchId(args)
   
def _getCheckpointByTeamBranchId(args):
    dbx = oodb.PickledHash2(dbx_Checkpoint_Branch__c_fname,oodb.PickleMethods.useSafeSerializer)
    try:
	sfdc, team_branch_id, stream_name = args
	dbx_key = '_'.join([team_branch_id, stream_name])
	if (dbx.has_key(dbx_key)):
	    v = dbx[dbx_key]
	    dbx.close()
	    logging.info("(%s) :: Retrieved for key of %s the data object %s from cached dbx." % (_utils.funcName(),dbx_key,v))
	    return v
	soql = "Select c.Id, c.Name, c.Status__c, c.Stream__c, c.Team_Branch__c from Checkpoint_Branch__c c where (c.Stream__c = '%s') and (c.Team_Branch__c = '%s')" % (stream_name,team_branch_id)
	ret = _sf_query(sfdc,soql)
	logging.info('(%s) soql=%s' % (_utils.funcName(),soql))
	if ret in BAD_INFO_LIST:
	    logging.warning("(%s) :: Could not find any Checkpoint_Branch__c Object(s) for team_branch_id of %s and stream_name of %s." % (_utils.funcName(),team_branch_id,stream_name))
	else: 
	    logging.info("(%s) :: soql=%s." % (_utils.funcName(),soql))
	    k = ret.keys()[0]
	    if (k):
		v = ret[k]
		val = lists.copyAsDict(v)
		dbx[dbx_key] = val.asDict()
		dbx.sync()
		dbx.close()
		return v
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))

    dbx.close()
    return None
    
def getCheckpointByTeamBranchId(args): 
    return _getCheckpointByTeamBranchId(args)
   
def _getTaskBranchByName(args):
    dbx = oodb.PickledHash2(dbx_Task_Branch__c_fname,oodb.PickleMethods.useSafeSerializer)
    try:
	sfdc, branch_name, stream_name = args
	dbx_key = '_'.join([branch_name, stream_name])
	if (dbx.has_key(dbx_key)):
	    v = dbx[dbx_key]
	    dbx.close()
	    logging.info("(%s) :: Retrieved for key of %s the data object %s from cached dbx." % (_utils.funcName(),dbx_key,v))
	    return v
	soql="Select t.Branch__c, t.Id, t.Merge_Details__c, t.Merged_Date_Time__c, t.Branch_Status__c, t.Name, t.Code_Stream__c from Task_Branch__c t where t.Branch__c = '%s'" % (branch_name)
	ret = _sf_query(sfdc,soql)
	logging.info('(%s) soql=%s' % (_utils.funcName(),soql))
	if ret in BAD_INFO_LIST:
	    logging.warning("(%s) :: Could not find any Task_Branch__c Object(s) for branch_name of %s and stream_name of %s." % (_utils.funcName(),branch_name, stream_name))
	else: 
	    logging.info("(%s) :: soql=%s." % (_utils.funcName(),soql))
	    k = ret.keys()[0]
	    if (k):
		v = ret[k]
		val = lists.copyAsDict(v)
		dbx[dbx_key] = val.asDict()
		dbx.sync()
		dbx.close()
		return v
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))

    dbx.close()
    return None
    
def getTaskBranchByName(args): 
    return _getTaskBranchByName(args)
   
def _getCasesByTaskBranchId(args):
    dbx = oodb.PickledHash2(dbx_Cases_for_Task_Branch__c_fname,oodb.PickleMethods.useSafeSerializer)
    try:
	sfdc, id = args
	dbx_key = '%s' % (id)
	if (dbx.has_key(dbx_key)):
	    v = dbx[dbx_key]
	    dbx.close()
	    logging.info("(%s) :: Retrieved for key of %s the data object %s from cached dbx." % (_utils.funcName(),dbx_key,v))
	    return v
	soql="Select c.Account__c, c.Branch__c, c.branchUrl__c, c.Build__c, c.Case__c, c.Checkpoint_Branch__c, c.Comment__c, c.Component__c, c.Id, c.Name, c.Priority__c, c.Task_Branch__c, c.Type__c from CR_List__c c where c.Task_Branch__c = '%s'" % (id)
	ret = _sf_query(sfdc,soql)
	logging.info('(%s) soql=%s' % (_utils.funcName(),soql))
	if ret in BAD_INFO_LIST:
	    logging.warning("(%s) :: Could not find any CR_List__c Object(s) for branch_name of %s and stream_name of %s." % (_utils.funcName(),branch_name, stream_name))
	else: 
	    logging.info("(%s) :: soql=%s." % (_utils.funcName(),soql))
	    for k in ret.keys():
		v = ret[k]
		val = lists.copyAsDict(v)
		dbx[dbx_key] = val.asDict()
	    v = dbx[dbx_key]
	    dbx.sync()
	    dbx.close()
	    return v
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))

    dbx.close()
    return None
    
def getCasesByTaskBranchId(args): 
    return _getCasesByTaskBranchId(args)

def _getCaseById(args):
    dbx = oodb.PickledHash2(dbx_Cases_by_Id_fname,oodb.PickleMethods.useSafeSerializer)
    try:
	sfdc, id = args
	dbx_key = '%s' % (id)
	if (dbx.has_key(dbx_key)):
	    v = dbx[dbx_key]
	    dbx.close()
	    logging.info("(%s) :: Retrieved for key of %s the data object %s from cached dbx." % (_utils.funcName(),dbx_key,v))
	    return v
	soql="Select c.CaseNumber, c.Id, c.ClosedDate, c.CR_Status__c, c.Status, c.Tag__c from Case c where c.Id = '%s'" % (id)
	ret = _sf_query(sfdc,soql)
	logging.info('(%s) soql=%s' % (_utils.funcName(),soql))
	if ret in BAD_INFO_LIST:
	    logging.warning("(%s) :: Could not find any CR_List__c Object(s) for branch_name of %s and stream_name of %s." % (_utils.funcName(),branch_name, stream_name))
	else: 
	    logging.info("(%s) :: soql=%s." % (_utils.funcName(),soql))
	    k = ret.keys()[0]
	    if (k):
		v = ret[k]
		val = lists.copyAsDict(v)
		dbx[dbx_key] = val.asDict()
		dbx.sync()
		dbx.close()
		return v
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))

    dbx.close()
    return None
    
def getCaseById(args): 
    return _getCaseById(args)

# +++

def _getTeamBranchByName(args):
    dbx = oodb.PickledHash2(dbx_Team_Branch__c_fname,oodb.PickleMethods.useSafeSerializer)
    try:
	sfdc, branch_name, stream_name = args
	dbx_key = '_'.join([branch_name, stream_name])
	if (dbx.has_key(dbx_key)):
	    v = dbx[dbx_key]
	    dbx.close()
	    logging.info("(%s) :: Retrieved for key of %s the data object %s from cached dbx." % (_utils.funcName(),dbx_key,v))
	    return v
	soql="Select t.Branch__c, t.Id, t.Merge_Details__c, t.Merged_Date_Time__c, t.Status__c, t.Stream__c from Team_Branch__c t where t.Branch__c = '%s'" % (branch_name)
	ret = _sf_query(sfdc,soql)
	logging.info('(%s) soql=%s' % (_utils.funcName(),soql))
	if ret in BAD_INFO_LIST:
	    logging.warning("(%s) :: Could not find any Team_Branch__c Object(s) for branch name of %s and stream name of %s." % (_utils.funcName(),branch_name,stream_name))
	else: 
	    logging.info("(%s) :: soql=%s." % (_utils.funcName(),soql))
	    k = ret.keys()[0]
	    if (k):
		v = ret[k]
		val = lists.copyAsDict(v)
		dbx[dbx_key] = val.asDict()
		dbx.sync()
		dbx.close()
		return v
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))

    dbx.close()
    return None
    
def getTeamBranchByName(args): 
    return _getTeamBranchByName(args)
   
def _getCaseByNumber(args):
    dbx = oodb.PickledHash2(dbx_Cases_fname,oodb.PickleMethods.useSafeSerializer)
    try:
	sfdc, num = args
	dbx_key = '%d' % int(num)
	if (dbx.has_key(dbx_key)):
	    v = dbx[dbx_key]
	    dbx.close()
	    logging.info("(%s) :: Retrieved for key of %s the data object %s from cached dbx." % (_utils.funcName(),dbx_key,v))
	    return v
	soql="Select c.CaseNumber, c.Id, c.ClosedDate, c.CR_Status__c, c.Status, c.Tag__c from Case c where c.CaseNumber = '%s'" % num
	ret = _sf_query(sfdc,soql)
	logging.info('(%s) soql=%s' % (_utils.funcName(),soql))
	if ret in BAD_INFO_LIST:
	    logging.warning("(%s) :: Could not find any Case Object(s) for number of %s." % (_utils.funcName(),num))
	else: 
	    logging.info("(%s) :: soql=%s." % (_utils.funcName(),soql))
	    k = ret.keys()[0]
	    if (k):
		v = ret[k]
		val = lists.copyAsDict(v)
		dbx[dbx_key] = val.asDict()
		dbx.sync()
		dbx.close()
		return v
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))

    dbx.close()
    return None
    
def getCaseByNumber(args): 
    return _getCaseByNumber(args)
  
def _getTaskBranches(args):
    dbx = oodb.PickledHash2(dbx_TaskBranches_fname,oodb.PickleMethods.useSafeSerializer)
    try:
	sfdc = args[0]
	soql="Select t.Branch__c, t.Id, t.Name, t.Num_CRs__c, t.Merge_Details__c, t.Merged_Date_Time__c, t.Branch_Status__c from Task_Branch__c t"
	ret = _sf_query(sfdc,soql)
	logging.info('(%s) soql=%s' % (_utils.funcName(),soql))
	if ret in BAD_INFO_LIST:
	    logging.warning("(%s) :: Could not find any Task_Branch__c Object(s)." % (_utils.funcName()))
	else: 
	    logging.info("(%s) :: soql=%s." % (_utils.funcName(),soql))
	    k = ret.keys()[0]
	    if (k):
		v = ret[k]
		for k,v in v.iteritems():
		    dbx[str(k)] = str(v)
		dbx.sync()
		dbx.close()
		return v
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))

    dbx.close()
    return None
    
def getTaskBranches(args): 
    return _getTaskBranches(args)
  
def parseCrNum(s):
    match = re.search("(?:[0-9]{8})|(?:[0-9]{7})|(?:[0-9]{6})|(?:[0-9]{5})|(?:[0-9]{4})", s)
    if match:
	return match.group()
    return s

def reportDict(fname,d):
    repOut = open(fname, 'w')
    try:
	_keys = _utils.sort(d.keys())
	for k in _keys:
	    v = d[k]
	    print >>repOut, '%s (%d)' % (k,len(v))
	    for n in v:
		print >>repOut, '\t%s' % (str(n))
    except:
	pass
    repOut.flush()
    repOut.close()

def indexOfFirstNonNumericChar(s):
    i = 0
    for ch in s:
	if (not ch.isdigit()):
	    return i
	i += 1
    return i

def parseCrListFromToken(raw_token):
    _re = re.compile(r"(?:[0-9]{8}(_|\.))|(?:[0-9]{7}(_|\.))|(?:[0-9]{6}(_|\.))|(?:[0-9]{5}(_|\.))|(?:[0-9]{4}(_|\.))")
    cr_list = [n.group() for n in _re.finditer(raw_token)]
    cr_list_x = [(n.start(),n.end()) for n in _re.finditer(raw_token)]
    n = len(cr_list_x)
    i_d = indexOfFirstNonNumericChar(raw_token)
    if (n > 0):
	if (cr_list_x[0][0] > i_d):
	    cr_list = []
	    n = 0
	logging.info('(%s) :: n=%s' % (_utils.funcName(),n))
	for i in xrange(0,n):
	    logging.info('(%s) :: i=%s' % (_utils.funcName(),i))
	    if (i < (n-1)):
		if ((cr_list_x[i+1][0] - cr_list_x[i][-1]) > 1):
		    logging.info('(%s) :: prune "%s"' % (_utils.funcName(),str(cr_list[i+1:])))
		    del cr_list[i+1:]
		    logging.info('(%s) :: break !' % (_utils.funcName()))
		    break
	    else:
		logging.info('(%s) :: break !' % (_utils.funcName()))
		break
    task_branch = raw_token.replace(''.join(cr_list),'')
    logging.info('(%s) :: task_branch=%s from raw_token=%s' % (_utils.funcName(),task_branch,raw_token))
    cr_list = [parseCrNum(n) for n in cr_list]
    return (task_branch,cr_list)

def performAnalysis(sfdc,analysis_name,_left_path,_stream_name,d):
    _count_found_task_branches = _count_task_branches = _count_crs = _count_found_crs = _count_ignore_crs = 0
    
    _found_task_branch_classifications = lists.HashedLists()
    _found_task_branch_classifications_by_date = lists.HashedLists()
    _found_task_branch_classifications_by_date_specific = lists.HashedLists()
    
    _begin_date = _utils.getFromSimpleDateStr('06-26-2008').toordinal()
    _end_date = datetime.date.today().toordinal()
	
    logging.info('(%s) :: BEGIN: %s' % (_utils.funcName(),analysis_name))
    for k,v in d.iteritems():
	_is_task_branch_rejected = False
	base_k = os.path.basename(k)
	if (is_nocr(base_k)):
	    logging.info('(%s) :: No reason to process NoCr Tokens. (%s)' % (_utils.funcName(),k))
	else:
	    date_k = None
	    _msg = 'Token :: "%s" in "%s".' % (base_k,os.path.dirname(k))
	    
	    if (len(_analysisData) == 0):
		full_k = os.sep.join([_left_path,base_k])
		_stat_k = ros_stat(full_k)
		if (_stat_k):
		    _date_k_secs_a = _stat_k.st_atime
		    _date_k_secs_m = _stat_k.st_mtime
		    _date_k_a = _utils.getAsDateTimeStr(_date_k_secs_a,fmt=_utils.formatDate_MMDDYYYY_dashes())
		    _date_k_m = _utils.getAsDateTimeStr(_date_k_secs_m,fmt=_utils.formatDate_MMDDYYYY_dashes())
	    
		    date_k_secs = _date_k_secs_m
	    
		    date_k = _utils.getAsDateTimeStr(date_k_secs)
		    _date_k = _utils.getAsDateTimeStr(date_k_secs,fmt=_utils.formatDate_MMDDYYYY_dashes())
		    _date_k_ord = _utils.getFromSimpleDateStr(_date_k).toordinal()
		    _msg = 'Token :: "%s" in "%s" on %s.' % (base_k,os.path.dirname(k),date_k)
		else:
		    logging.warning('(%s) :: Cannot get the temporal data from "%s".' % (_utils.funcName(),full_k))

	    task_branch, cr_list = parseCrListFromToken(base_k)
	    ret_cp = None
	    _found_object_type = 'Task_Branch__c'
	    ret = getTaskBranchByName([sfdc,task_branch,_stream_name])
	    if (not ret):
		if (_isTeamBranches):
		    _found_object_type = 'Team_Branch__c'
		    ret = getTeamBranchByName([sfdc,task_branch,_stream_name])
		    if (ret) and (ret.has_key('Id')):
			ret_cp = getCheckpointByTeamBranchId([sfdc,ret['Id'],_stream_name])
			ret_tb = getTaskBranchesFromTeamBranchId([sfdc,ret['Id']])
		else:
		    logging.warning('(%s) :: Task Branch of "%s" has not been found and --team_branches option was not used therefore no analysis can be performed on this task branch since it is not in SalesForce at this time.' % (_utils.funcName(),task_branch))
	    else:
		if (len(_analysisData) > 0):
		    v_cases = getCasesByTaskBranchId([sfdc,ret['Id']])
		    if (v_cases):
			v_cases = v_cases if (isinstance(v_cases,list)) else [v_cases]
			for v_case in v_cases:
			    if (v_case):
				ret_case = getCaseById([sfdc,v_case['Case__c']])
				if (ret_case):
				    cr_list.append(ret_case['CaseNumber'])
	    for cr in cr_list:
		logging.info('(%s) :: CR=%s' % (_utils.funcName(),cr))
	    if (ret):
		_found_branch_name = ''
		_isStream_Correct = False
		if (ret.has_key('Stream__c')):
		    _found_branch_name = ret['Stream__c']
		elif (ret.has_key('Code_Stream__c')):
		    _found_branch_name = ret['Code_Stream__c']
		if (len(_found_branch_name) > 0):
		    if (_found_branch_name != _stream_name):
			logging.warning('(%s) :: The actual Branch Name "%s" does not match the expected Stream Name "%s"' % (_utils.funcName(),_found_branch_name,_stream_name))
		    else:
			_isStream_Correct = True
		fOut = sys.stdout if (_isStream_Correct) else sys.stderr
		_count_found_task_branches += 1
		print >>fOut, _msg
		print >>fOut, '%s%sFound %s in "%s" :: "%s" in "%s".' % ('(+++) ' if (_isStream_Correct) else '','' if (_isStream_Correct) else 'Not ',_found_object_type,_found_branch_name,task_branch,_stream_name)
		print >>fOut, 'ret=%s' % (ret)
		for rk,rv in ret.iteritems():
		    print >>fOut, '\t %s=%s' % (rk,rv)
		_found_key = 'UNCLASSIFIED'
		if (ret.has_key('Status__c')):
		    _found_key = ret['Status__c']
		elif (ret.has_key('Branch_Status__c')):
		    _found_key = ret['Branch_Status__c']
		print >>fOut, '_found_task_branch_classifications[%s]' % (_found_key)
		_found_task_branch_classifications[_found_key] = [base_k,lists.HashedLists2(ret)]
		if (len(_analysisData) == 0):
		    _found_task_branch_classifications_by_date[_date_k] = [base_k,lists.HashedLists2(ret)]
		    logging.info('(%s) :: _begin_date=%s, _date_k_ord=%s, _end_date=%s' % (_utils.funcName(),_begin_date,_date_k_ord,_end_date))
		    if (_date_k_ord >= _begin_date) and (_date_k_ord <= _end_date):
			_found_task_branch_classifications_by_date_specific[_date_k] = [base_k,lists.HashedLists2(ret)]
			logging.info('+++ (%s) :: _found_task_branch_classifications_by_date_specific=%s' % (_utils.funcName(),_date_k))
	    else:
		_is_task_branch_rejected = True
		print >>sys.stderr, _msg
		print >>sys.stderr, 'Rejected Token - Not Found in Team Branch or Task Branch :: "%s" in "%s".' % (task_branch,_stream_name)
		_found_task_branch_classifications['NOT IN SALESFORCE'] = (base_k,task_branch,_stream_name)
		_found_task_branch_classifications_by_date[date_k] = (base_k,task_branch,_stream_name)
	    _count_task_branches += 1
	    logging.info('(%s) :: task_branch=%s' % (_utils.funcName(),task_branch))
	    logging.info('(%s) :: ret=%s' % (_utils.funcName(),str(ret)))
	    fOut = sys.stdout if (not _is_task_branch_rejected) else sys.stderr
	    for cr in cr_list:
		if (cr.isdigit()):
		    _count_crs += 1
		    cr = zeroPadCrNum(cr)
		    logging.info('(%s) :: cr=%s' % (_utils.funcName(),cr))
		    ret = getCaseByNumber([sfdc,cr])
		    logging.info('(%s) :: ret=%s' % (_utils.funcName(),str(ret)))
		    if (ret):
			_count_found_crs += 1
			print >>fOut, 'Found CR :: "%s" in "%s".' % (cr,_stream_name)
		    else:
			print >>fOut, 'Rejected CR :: "%s" in "%s".' % (cr,_stream_name)
		else:
		    _count_ignore_crs += 1
		    logging.info('(%s) :: IGNORE cr=%s' % (_utils.funcName(),cr))
	    logging.info('')
	    _msg = '%s\n\n' % ('='*80)
	    print >>fOut, _msg
		
    logging.info('(%s) :: _count_found_task_branches=%d of _count_task_branches=%d' % (_utils.funcName(),_count_found_task_branches,_count_task_branches))
    logging.info('(%s) :: _count_found_crs=%d of _count_crs=%d' % (_utils.funcName(),_count_found_crs,_count_crs))
    logging.info('(%s) :: _count_ignore_crs=%d' % (_utils.funcName(),_count_ignore_crs))
    logging.info('(%s) :: END! %s' % (_utils.funcName(),analysis_name))
    
    reportDict(os.sep.join([os.path.dirname(sys.stdout.f.name),'%s_found_task_branch_classifications.txt' % (analysis_name)]),_found_task_branch_classifications)
    reportDict(os.sep.join([os.path.dirname(sys.stdout.f.name),'%s_found_task_branch_classifications_by_date.txt' % (analysis_name)]),_found_task_branch_classifications_by_date)
    reportDict(os.sep.join([os.path.dirname(sys.stdout.f.name),'%s_found_task_branch_classifications_by_date_specific.txt' % (analysis_name)]),_found_task_branch_classifications_by_date_specific)

def storeDataInto(dpath, fname, d_source):
    full_fname = os.sep.join([dpath,fname])
    if (os.path.exists(full_fname)):
	os.remove(full_fname)
    dbx = oodb.PickledHash2(full_fname,oodb.PickleMethods.useSafeSerializer)
    for k,v in d_source.iteritems():
	dbx[k] = v
    dbx.sync()
    dbx.close()
    return full_fname

def areDbxFilesReadable(_data_path,fnames):
    _keys = fnames.keys()
    _found_names = [not os.path.exists(f[0]) for f in fnames.values()]
    n = len(fnames) # Assume all are accessible unless otherwise notes...
    if (any(_found_names)):
	i = 0
	n = 1
	for b in _found_names:
	    if (b):
		logging.warning('(%s) :: Cannot locate "%s".' % (_utils.funcName(),_keys[i]))
	    else:
		n += 1
	    i += 1
    assert n == len(fnames), 'Oops, something went wrong with the Dbx file names. Some of them are not readable.'
    return n == len(fnames)

def performBrowse(_data_path,fnames):
    areDbxFilesReadable(_data_path,fnames)

def searchDbxForKey(fname,key):
    if (os.path.exists(fname)):
	dbx = oodb.PickledHash2(fname,oodb.PickleMethods.useSafeSerializer)
	val = None if (not dbx.has_key(key)) else dbx[key]
	if (val == None):
	    _found_key = [k for k in dbx.keys() if (k.find(key) > -1)]
	    if (len(_found_key) > 0):
		val = dbx[_found_key[0]]
	dbx.close()
	return val
    elif (len(_analysisData) == 0):
	logging.warning('(%s) :: Cannot locate the file named "%s".' % (_utils.funcName(),fname))

def performSpecificAnalysis(sfdc,_data_path,fnames):
    global _analysisFolder
    global _analysisData
    global dbx_Task_Branch__c_fname
    global dbx_Checkpoint_Branch__c_fname
    global dbx_Task_Branches_by_Team_Branch_fname

    if (os.path.exists(_analysisFolder)):
	if (areDbxFilesReadable(_data_path,fnames)):
	    d_analysis = lists.HashedLists()
	    d_analysis2 = lists.HashedLists()
	    d_analysis3 = lists.HashedLists()

	    l_tokens = []
	    l_nocr = []
	    d_specific_files = lists.HashedLists()
	    
	    def considerDbxForKey(tb_name):
		isFound = []
		for kk,vv in fnames.iteritems():
		    val = searchDbxForKey(vv,tb_name)
		    if (val):
			isFound.append(True)
			d_analysis[tb_name] = vv
			if (isinstance(val,list)):
			    d_analysis2[tb_name] = (vv,[d for d in val if (lists.isDict(d))])
			else:
			    d_analysis2[tb_name] = (vv,val)
		    else:
			isFound.append(False)
		if (not any(isFound)):
		    _msg = '(%s) :: Cannot locate Task Branch named "%s" in any of the following files: %s.' % (_utils.funcName(),tb_name,fnames.keys())
		    logging.warning(_msg)
		    print >>sys.stderr, _msg
	    
	    if (len(_analysisData) == 0):
		d_specific_files = collect_files_from_path(_analysisFolder)
		for k,v in d_specific_files.iteritems():
		    if (not is_nocr(k)):
			task_branch, cr_list = parseCrListFromToken(k)
			l_tokens.append(task_branch)
			d_analysis3[task_branch] = k
			considerDbxForKey(task_branch)
		    else:
			l_nocr.append(k)
			logging.info('(%s) :: is_nocr(%s)=True.' % (_utils.funcName(),k))
	    else:
		for task_branch in [t.strip() for t in _analysisData if (len(t.strip()) > 0)]:
		    d_analysis3[task_branch] = task_branch
		    l_tokens.append(task_branch)
		    considerDbxForKey(task_branch)
    
	    const_Missing_Task_Branch = 'Missing Task Branch'
	    
	    d_stats = lists.HashedLists()
	    
	    logging.info('(%s) :: BEGIN: %d items of %d.' % (_utils.funcName(),len(d_analysis),len(l_tokens)))
	    d_counts = lists.HashedLists()
	    for k,v in d_analysis.iteritems():
		fOut_suspense = cStringIO.StringIO() # holds output until all the analysis has been completed.

		d = lists.HashedLists2()
		for item in v:
		    d[os.path.basename(item)] = item
		d_copy = lists.HashedLists2(d.asDict())
		_is_both = False if (d['both_left_and_right.dbx'] == None) else True
		_is_left = False if (d['left_files.dbx'] == None) else True
		_is_right = False if (d['right_files.dbx'] == None) else True
		_is_left_only = (not _is_both) and (_is_left)
		_is_right_only = (not _is_both) and (_is_right)
		d_copy['both_left_and_right.dbx'] = None
		d_copy['left_files.dbx'] = None
		d_copy['left_only.dbx'] = None
		d_copy['right_files.dbx'] = None
		_reasons = []
		_val = d_analysis2[k]
		l_missing_task_branch = []
		if (_val):
		    l_missing_task_branch = [os.path.basename(vv) for vv,item in _val if os.path.basename(vv).find(os.path.basename(dbx_Task_Branch__c_fname)) > -1]
		    _reasons.append('' if (len(l_missing_task_branch) > 0) else const_Missing_Task_Branch)
		_is_in_salesforce = len(d_copy) > 0
		#_is_corrective_actions_required = (not _is_both) or (not _is_in_salesforce) or (len(l_missing_task_branch) == 0)
		_is_corrective_actions_required = (_is_both) and (len(l_missing_task_branch) == 0)
		_msg = 'Token "%s", _is_both=%s, %sIN SALESFORCE%s.' % (k,_is_both,'IS ' if (_is_in_salesforce) else 'NOT ',', CORRECTIVE_ACTIONS_REQUIRED !' if (_is_corrective_actions_required) else '')
		logging.info(_msg)
		print >>fOut_suspense, _msg
		if (len(d_copy) > 0):
		    logging.info('(%s) :: BEGIN: d_copy' % (_utils.funcName()))
		    for kk,vv in d_copy.iteritems():
			logging.info('(%s) :: %s' % (_utils.funcName(),(kk)))
		    logging.info('(%s) :: END! d_copy' % (_utils.funcName()))
		if (_val):
		    for vv,item in _val:
			if (lists.isDict(item)):
			    _is_merged = (item['Branch_Status__c'] == 'Merged')
			    d_stats[item['Branch_Status__c']] = (k,item.asDict())
			    if (_is_merged):
				print >>fOut_suspense, '\t%s --> MERGED !' % (os.path.basename(vv))
			    else:
				print >>fOut_suspense, '\t%s --> %s !' % (os.path.basename(vv),item['Branch_Status__c'])
				print >>fOut_suspense, ''
			    lists.prettyPrint(item,title='Team_Branch__c' if (_is_corrective_actions_required) else 'Task_Branch__c',tab_width=4,fOut=fOut_suspense)
			    if (_is_corrective_actions_required) and (item['Id'] != None):
				cp_val = searchDbxForKey(dbx_Checkpoint_Branch__c_fname,item['Id'])
				if (cp_val):
				    lists.prettyPrint(cp_val,title='Checkpoint_Branch__c by %s' % (item['Id']),tab_width=4,fOut=fOut_suspense)
				
				tb_val = searchDbxForKey(dbx_Task_Branches_by_Team_Branch_fname,item['Id'])
				if (tb_val):
				    tb_val = tb_val if (isinstance(tb_val,list)) else [tb_val]
				    tb_val_count = 1
				    for tb_item in tb_val:
					l_end_msg = lists.prettyPrint(tb_item,title='Task_Branches_by_Team_Branch by %s (%d of %d)' % (item['Id'],tb_val_count,len(tb_val)),tab_width=4,delay_end=True,fOut=fOut_suspense)
					if (tb_item.has_key('Team_Branch__c')):
					    _Team_Branch__c = tb_item['Team_Branch__c']
					    ret_tb = getTaskBranchesFromTeamBranchId([sfdc,_Team_Branch__c])
					    if (ret_tb):
						ret_tb = ret_tb if (isinstance(ret_tb,list)) else [ret_tb]
						ret_tb_count = 1
						for ret_tb_item in ret_tb:
						    d_stats[ret_tb_item['Branch_Status__c']] = (k,lists.HashedLists2(ret_tb_item).asDict())
						    lists.prettyPrint(ret_tb_item,prefix='\t',title='Task_Branch for %s (%d of %d)' % (_Team_Branch__c,ret_tb_count,len(ret_tb)),tab_width=4,fOut=fOut_suspense)
						    ret_tb_count += 1
						    
						_is_corrective_actions_required = False
						i_found = _utils.findInListSafely(_reasons,const_Missing_Task_Branch)
						if (i_found > -1):
						    del _reasons[i_found]
					    else:
						print >>fOut_suspense, 'Cannot query SalesForce for Task_Branch__c of "%s".' % (_Team_Branch__c)
					else:
					    print >>fOut_suspense, 'Missing Team_Branch__c for object of type "%s" from "%s".' % (ObjectTypeName.typeName(tb_item),ObjectTypeName.typeName(tb_val))
					print >>fOut_suspense, '\n'.join(l_end_msg)
					tb_val_count += 1
		if (len(_reasons) > 0) and (any([len(r.strip()) > 0 for r in _reasons])):
		    print >>fOut_suspense, 'Reason: %s' % (', '.join(_reasons))
		print >>fOut_suspense, '='*80
		print >>fOut_suspense, ''
		
		d_counts[str(_is_corrective_actions_required)] = (k,_reasons)

		fOut = sys.stderr if (_is_corrective_actions_required) else sys.stdout
		print >>fOut, fOut_suspense.getvalue()
		fOut_suspense.close()
		
	    _total = 0
	    if (d_counts[str(False)]):
		_total += len(d_counts[str(False)])
	    if (d_counts[str(True)]):
		_total += len(d_counts[str(True)])
	    _total += len(l_nocr)
	    
	    _set = set(l_tokens)
	    
	    d_tokens = lists.HashedLists()
	    for item in l_tokens:
		d_tokens[item] = item
	    
	    repeated_tokens = []
	    for item in d_tokens.values():
		if (len(item) > 1):
		    repeated_tokens.append(item[0])
		    
	    repeated_tokens_with_analysis = []
	    for item in d_tokens.values():
		if (len(item) > 1):
		    repeated_tokens_with_analysis.append([item[0],d_analysis3[item[0]]])
		    
	    d_found_task_branches = lists.HashedLists2()
	    for k,v in d_stats.iteritems():
		for item in v:
		    d_found_task_branches[item[0]] = (item[-1],k)
    
	    _tokens_debug_txt = 'tokens-debug.txt'

	    if (len(d_specific_files) > 0):
		fOut_set = open(os.sep.join([os.path.dirname(sys.stdout.f.name),_tokens_debug_txt]),'w')
		print >>fOut_set, ''
		reportTheList(d_specific_files.keys(),'1.0 Raw Tokens',fOut_set)
		fOut_set.flush()
		fOut_set.close()
    
	    fOut_set = open(os.sep.join([os.path.dirname(sys.stdout.f.name),_tokens_debug_txt]),'a')
	    print >>fOut_set, ''
	    reportTheList(list(_set),'1.0 Unique Tokens set(l_tokens)',fOut_set)
	    fOut_set.flush()
	    fOut_set.close()
    
	    fOut_set = open(os.sep.join([os.path.dirname(sys.stdout.f.name),_tokens_debug_txt]),'a')
	    print >>fOut_set, ''
	    reportTheList(l_tokens,'1.0 Unique Tokens (with repeated Tokens, if any) l_tokens',fOut_set)
	    fOut_set.flush()
	    fOut_set.close()
    
	    fOut_set = open(os.sep.join([os.path.dirname(sys.stdout.f.name),_tokens_debug_txt]),'a')
	    print >>fOut_set, ''
	    reportTheList(repeated_tokens,'1.0 Repeated Tokens (if any)',fOut_set)
	    fOut_set.flush()
	    fOut_set.close()
    
	    fOut_set = open(os.sep.join([os.path.dirname(sys.stdout.f.name),_tokens_debug_txt]),'a')
	    print >>fOut_set, ''
	    reportTheList(repeated_tokens_with_analysis,'1.0 Repeated Tokens With Analysis',fOut_set)
	    fOut_set.flush()
	    fOut_set.close()
	    
	    fOut_set = open(os.sep.join([os.path.dirname(sys.stdout.f.name),_tokens_debug_txt]),'a')
	    print >>fOut_set, ''
	    if (d_counts[str(False)]):
		reportTheList(list(d_counts[str(False)]),'1.1 Tokens that do not require Corrective Actions (if any)',fOut_set)
	    fOut_set.flush()
	    fOut_set.close()
    
	    if (d_counts[str(False)]):
		_set -= set([x[0] for x in d_counts[str(False)]])
	    
	    fOut_set = open(os.sep.join([os.path.dirname(sys.stdout.f.name),_tokens_debug_txt]),'a')
	    print >>fOut_set, ''
	    reportTheList(list(_set),'1.1 Unaccounted Tokens (Tokens that fall thru the cracks)',fOut_set)
	    fOut_set.flush()
	    fOut_set.close()
    
	    fOut_set = open(os.sep.join([os.path.dirname(sys.stdout.f.name),_tokens_debug_txt]),'a')
	    print >>fOut_set, ''
	    if (d_counts[str(True)]):
		reportTheList(list(d_counts[str(True)]),'1.2 Tokens that do require Corrective Actions (if any)',fOut_set)
	    fOut_set.flush()
	    fOut_set.close()
    
	    if (d_counts[str(True)]):
		_set -= set([x[0] for x in d_counts[str(True)]])
    
	    fOut_set = open(os.sep.join([os.path.dirname(sys.stdout.f.name),_tokens_debug_txt]),'a')
	    print >>fOut_set, ''
	    reportTheList(list(_set),'1.2 Unaccounted Tokens (Tokens that fall thru the cracks, before removing nocr.Tokens)',fOut_set)
	    fOut_set.flush()
	    fOut_set.close()
    
	    fOut_set = open(os.sep.join([os.path.dirname(sys.stdout.f.name),_tokens_debug_txt]),'a')
	    print >>fOut_set, ''
	    reportTheList(l_nocr,'1.3 lnocr.Tokens',fOut_set)
	    fOut_set.flush()
	    fOut_set.close()
    
	    _set -= set(l_nocr)
    
	    fOut_set = open(os.sep.join([os.path.dirname(sys.stdout.f.name),_tokens_debug_txt]),'a')
	    print >>fOut_set, ''
	    reportTheList(list(_set),'1.3 Unaccounted Tokens (Tokens that fall thru the cracks, after removing nocr.Tokens and all other Tokens with known classifications)',fOut_set)
	    fOut_set.flush()
	    fOut_set.close()

	    foutReport = cStringIO.StringIO()
	    foutReportCSV = cStringIO.StringIO()
	    
	    print >>foutReport, '-'*80
	    print >>foutReport, ''
	    print >>foutReport, 'There are %d items of %d in this file.' % (0 if (not d_counts[str(False)]) else len(d_counts[str(False)]),len(l_tokens))
	    print >>foutReport, 'BEGIN:'
	    if (d_counts[str(False)]):
		i = 1
		for item in d_counts[str(False)]:
		    print >>foutReport, '\t%d :: %s' % (i,str(item))
		    print >>foutReportCSV, '"%d",%s' % (i,_utils.asCSV(item))
		    i += 1
	    print >>foutReport, 'END!'
	    
	    _utils.writeFileFrom(os.sep.join([_log_path,'NO_corrective_actions_required.txt']),foutReport.getvalue())
	    _utils.writeFileFrom(os.sep.join([_log_path,'NO_corrective_actions_required.csv']),foutReportCSV.getvalue())
	    
	    #print >>sys.stdout, foutReport.getvalue()
	    
	    foutReport.close()
	    foutReportCSV.close()

	    foutReport = cStringIO.StringIO()
	    foutReportCSV = cStringIO.StringIO()
	    
	    print >>foutReport, ''
	    print >>foutReport, 'Accounted for %d of %d items.' % (_total,len(l_tokens))
	    print >>foutReport, ''
	    print >>foutReport, 'Unaccounted for %d of %d items.' % (len(_set),len(l_tokens))
	    print >>foutReport, ''

	    reportTheList(_set,'Unaccounted',foutReportCSV)
	    
	    _utils.writeFileFrom(os.sep.join([_log_path,'Accounted_versus_Unaccounted.txt']),foutReport.getvalue())
	    _utils.writeFileFrom(os.sep.join([_log_path,'Accounted_versus_Unaccounted.csv']),foutReportCSV.getvalue())

	    foutReport.close()
	    foutReportCSV.close()

	    foutReport = cStringIO.StringIO()
	    foutReportCSV = cStringIO.StringIO()
	    
	    print >>foutReport, ''
	    print >>foutReport, '='*80
	    print >>foutReport, ''
	    _num_tb = sum([len(v) for k,v in d_stats.iteritems()])
	    _num_unique_tb = len(d_found_task_branches.keys())
	    print >>foutReport, 'BEGIN: Reporting a total of %d Task Branches of %d uniques.' % (_num_tb,_num_unique_tb)
	    for k,v in d_stats.iteritems():
		print >>foutReportCSV, '"There are ","%d","with Branch Status of ","%s"' % (len(v),str(k).upper())
		print >>foutReport, '\tThere are %d with Branch Status of %s.' % (len(v),str(k).upper())
	    print >>foutReport, 'END!'
	    print >>foutReport, ''
	    print >>foutReport, '-'*80
	    print >>foutReport, ''
	    for k,v in d_stats.iteritems():
		print >>foutReportCSV, '"%s"' % (str(k).upper())
		print >>foutReport, '\tBranch Status of %s.' % (str(k).upper())
		i = 1
		for item in v:
		    d_item = item[-1]
		    lists.prettyPrint(d_item,prefix='',title='(%d of %d) :: Task Branch(es) with Status of %s' % (i,len(v),k),tab_width=4,fOut=foutReport)
		    lists.prettyPrint(d_item,prefix='\t',title='(%d of %d) :: Task Branch(es) with Status of %s' % (i,len(v),k),tab_width=4,asCSV=True,fOut=foutReportCSV)
		    v_cases = getCasesByTaskBranchId([sfdc,d_item['Id']])
		    if (v_cases):
			v_caseLinks = v_cases if (isinstance(v_cases,list)) else [v_cases]
			for v_caseLink in v_caseLinks:
			    if (v_caseLink):
				ret_case = getCaseById([sfdc,v_caseLink['Case__c']])
				if (ret_case):
				    lists.prettyPrint(ret_case,prefix='\t\t',title='\t\tCR For Task Branch of %s' % (d_item['Name']),asCSV=False,fOut=foutReport)
				    lists.prettyPrint(ret_case,title='CR For Task Branch of %s' % (d_item['Name']),asCSV=True,fOut=foutReportCSV)
			print >>foutReport, ''
		    else:
			print >>foutReport, '\t\tNO CASES FOR THIS TASK BRANCH.'
		    print >>foutReport, '-'*80
		    print >>foutReport, ''
		    i += 1
		print >>foutReport, '='*80
		print >>foutReport, ''
	    
	    _utils.writeFileFrom(os.sep.join([_log_path,'Task_Branches_by_Branch_Status.txt']),foutReport.getvalue())
	    _utils.writeFileFrom(os.sep.join([_log_path,'Task_Branches_by_Branch_Status.csv']),foutReportCSV.getvalue())

	    foutReport.close()
	    foutReportCSV.close()

	    foutReport = cStringIO.StringIO()
	    foutReportCSV = cStringIO.StringIO()
	    
	    csv = CSV(csv_fname)
	    
	    l_expected_task_branches = [n for n in csv.column(1) if (len(n.strip()) > 0)]
	    
	    d_expected_task_branches = lists.HashedLists2()
	    d_expected_task_branches.caseless = True
	    for l in l_expected_task_branches:
		d_expected_task_branches[l] = 'NOT FOUND'
	    
	    d_not_expected_task_branches = lists.HashedLists2()
	    d_not_expected_task_branches.caseless = True

	    print >>foutReport, ''
	    print >>foutReport, '-'*80
	    print >>foutReport, ''
	    print >>foutReport, 'BEGIN: Reporting a total of %d unique Task Branches.' % (_num_unique_tb)
	    i = 1
	    for k,v in d_found_task_branches.iteritems():
		ex = d_expected_task_branches[k]
		s_ex = 'FOUND' if (ex) else 'NOT FOUND'
		if (ex):
		    d_expected_task_branches[k] = s_ex
		else:
		    d_not_expected_task_branches[k] = s_ex
		lists.prettyPrint(v[0],prefix='\t',title='(%d) (%s) Task Branch(es) for %s with Status of %s' % (i,s_ex,k,v[-1]),tab_width=4,fOut=foutReport)
		lists.prettyPrint(v[0],prefix='\t',title='(%d) (%s) Task Branch(es) for %s with Status of %s' % (i,s_ex,k,v[-1]),tab_width=4,asCSV=True,fOut=foutReportCSV)
		i += 1
	    print >>foutReport, 'END!'
	    print >>foutReport, ''
	    print >>foutReport, '='*80
	    print >>foutReport, ''

	    _utils.writeFileFrom(os.sep.join([_log_path,'Unique_Task_Branches_Report.txt']),foutReport.getvalue())
	    #_utils.writeFileFrom(os.sep.join([_log_path,'Unique_Task_Branches_Report.csv']),foutReportCSV.getvalue())

	    foutReport.close()
	    foutReportCSV.close()

	    foutReport = cStringIO.StringIO()
	    foutReportCSV = cStringIO.StringIO()
	    
	    print >>foutReport, 'BEGIN: The Expected Task Branches, all %d of them.' % (len(l_expected_task_branches))
	    reportTheList(l_expected_task_branches,'The Data from "%s" for column #2 which is named "%s".' % (csv.filename,csv.header[1]),fOut=foutReport)
	    reportTheList(l_expected_task_branches,'The Data from "%s" for column #2 which is named "%s".' % (csv.filename,csv.header[1]),asCSV=True,fOut=foutReportCSV)
	    print >>foutReport, 'END!'
	    print >>foutReport, ''

	    _utils.writeFileFrom(os.sep.join([_log_path,'Expected_Task_Branches.txt']),foutReport.getvalue())
	    _utils.writeFileFrom(os.sep.join([_log_path,'Expected_Task_Branches.csv']),foutReportCSV.getvalue())

	    foutReport.close()
	    foutReportCSV.close()

	    foutReport = cStringIO.StringIO()
	    foutReportCSV = cStringIO.StringIO()
	    
	    def _adjustExpectedVersusFoundCSVValues(l):
		if (l[-1] == 'NOT FOUND'):
		    l.insert(len(l)-1,'')
		return l

	    print >>foutReport, 'BEGIN: The Expected versus Found Task Branches, all %d of them.' % (len(d_expected_task_branches))
	    _found_meaning = 'Expected Task Branch has a Token' if (len(_analysisData) == 0) else 'Task Branch was FOUND and also appears on the Expected List'
	    _not_found_meaning = 'Expected Task Branch has NO Token' if (len(_analysisData) == 0) else 'Task Branch was FOUND but does not appear on the Expected List'
	    _title = 'Task Branch(es) FOUND or NOT from the expected list. FOUND means %s and NOT FOUND means %s.' % (_found_meaning,_not_found_meaning)
	    lists.prettyPrint(d_expected_task_branches,prefix='\t',title=_title,tab_width=4,fOut=foutReport)
	    lists.prettyPrint(d_expected_task_branches,prefix='\t',title=_title,tab_width=4,asCSV=True,csv_callback=_adjustExpectedVersusFoundCSVValues,fOut=foutReportCSV)
	    print >>foutReport, 'END!'
	    print >>foutReport, ''
	    
	    _utils.writeFileFrom(os.sep.join([_log_path,'Expected_versus_Found_Task_Branches.txt']),foutReport.getvalue())
	    _utils.writeFileFrom(os.sep.join([_log_path,'Expected_versus_Found_Task_Branches.csv']),foutReportCSV.getvalue())

	    foutReport.close()
	    foutReportCSV.close()

	    foutReport = cStringIO.StringIO()
	    foutReportCSV = cStringIO.StringIO()
	    
	    print >>foutReport, 'BEGIN: The Expected Task Branches Not Found, all %d of them.' % (len(d_not_expected_task_branches))
	    lists.prettyPrint(d_not_expected_task_branches,prefix='\t',title='Task Branch(es) FOUND or NOT from the expected list.',tab_width=4,fOut=foutReport)
	    lists.prettyPrint(d_not_expected_task_branches,prefix='\t',title='Task Branch(es) FOUND or NOT from the expected list.',tab_width=4,asCSV=True,csv_callback=_adjustExpectedVersusFoundCSVValues,fOut=foutReportCSV)
	    print >>foutReport, 'END!'
	    print >>foutReport, ''

	    _utils.writeFileFrom(os.sep.join([_log_path,'Found_Task_Branches_Not_Expected.txt']),foutReport.getvalue())
	    _utils.writeFileFrom(os.sep.join([_log_path,'Found_Task_Branches_Not_Expected.csv']),foutReportCSV.getvalue())

	    foutReport.close()
	    foutReportCSV.close()

	    print >>sys.stdout, ''
	    print >>sys.stderr, '-'*80
	    print >>sys.stderr, ''
	    print >>sys.stderr, 'There are %d items of %d in this file.' % (0 if (not d_counts[str(True)]) else len(d_counts[str(True)]),len(l_tokens))
	    print >>sys.stderr, 'BEGIN:'
	    if (d_counts[str(True)]):
		i = 1
		for item in d_counts[str(True)]:
		    print >>sys.stdout, '\t%d :: %s' % (i,str(item))
		    i += 1
	    print >>sys.stderr, 'END!'
	    print >>sys.stderr, ''
	    print >>sys.stderr, 'Accounted for %d of %d items.' % (_total,len(l_tokens))
	    print >>sys.stderr, ''
	    print >>sys.stderr, 'Unaccounted for %d of %d items.' % (len(_set),len(l_tokens))
	    print >>sys.stderr, ''
	    reportTheList(_set,'Unaccounted',sys.stderr)
    
	    fOut_nocr = open(os.sep.join([os.path.dirname(sys.stdout.f.name),'nocr.txt']),'w')
	    print >>fOut_nocr, 'There are %d of %d items in this file.' % (len(l_nocr),len(l_tokens))
	    print >>fOut_nocr, '\n'.join(l_nocr)
	    print >>fOut_nocr, ''
	    print >>fOut_nocr, 'Accounted for %d of %d items.' % (_total,len(l_tokens))
	    print >>fOut_nocr, ''
	    print >>fOut_nocr, 'Unaccounted for %d of %d items.' % (len(_set),len(l_tokens))
	    print >>fOut_nocr, ''
	    reportTheList(_set,'Unaccounted',fOut_nocr)
	    fOut_nocr.flush()
	    fOut_nocr.close()
	    
	    logging.info('(%s) :: END!' % (_utils.funcName()))
	    pass
	pass
    else:
	logging.warjning('(%s) :: Unable to perform processing due to failure to locate the "%s" directory.' % (_utils.funcName(),_analysisFolder))
	    
def performTaskBranchAnalysis(args):
    ret = getTaskBranches(args)
    pass

def main(args):
    global _isAnalysis
    global _analysisFolder
    global _analysisData
    global dbx_Cases_fname
    global dbx_Team_Branch__c_fname
    global dbx_Task_Branch__c_fname
    global dbx_TaskBranches_fname
    global dbx_Checkpoint_Branch__c_fname
    global dbx_Task_Branches_by_Team_Branch_fname
    global dbx_Cases_for_Task_Branch__c_fname
    global dbx_Cases_by_Id_fname
    global _data_path
    
    ioTimeAnalysis.ioBeginTime('%s' % (__name__))
    try:
	sfdc,left_path,right_path,branch_name = args
	
	_stream_name = branch_name.split(os.sep)[0]

	dbx_left_files = lists.HashedLists()
	dbx_right_files = lists.HashedLists()
	dbx_both_left_and_right = lists.HashedLists()
	dbx_left_only = lists.HashedLists()
	dbx_right_only = lists.HashedLists()

	dbx_files = []
	
	dbx_Cases_fname = os.sep.join([_data_path, 'Cases.dbx'])
	dbx_Team_Branch__c_fname = os.sep.join([_data_path, 'Team_Branch__c.dbx'])
	dbx_Task_Branch__c_fname = os.sep.join([_data_path, 'Task_Branch__c.dbx'])
	dbx_TaskBranches_fname = os.sep.join([_data_path, 'Task_Branches__c.dbx'])
	dbx_Checkpoint_Branch__c_fname = os.sep.join([_data_path, 'Checkpoint_Branch__c.dbx'])
	dbx_Task_Branches_by_Team_Branch_fname = os.sep.join([_data_path, 'Task_Branches_by_Team_Branch.dbx'])
	dbx_Cases_for_Task_Branch__c_fname = os.sep.join([_data_path, 'Cases_for_Task_Branch__c.dbx'])
	dbx_Cases_by_Id_fname = os.sep.join([_data_path, 'Cases_by_Id.dbx'])
	
	dbx_files.append(dbx_Cases_fname)
	dbx_files.append(dbx_Team_Branch__c_fname)
	dbx_files.append(dbx_Task_Branch__c_fname)
	dbx_files.append(dbx_TaskBranches_fname)
	dbx_files.append(dbx_Checkpoint_Branch__c_fname)
	dbx_files.append(dbx_Task_Branches_by_Team_Branch_fname)
	dbx_files.append(dbx_Cases_for_Task_Branch__c_fname)
	dbx_files.append(dbx_Cases_by_Id_fname)
	
	_left_path = os.sep.join([left_path,branch_name])
	logging.info('(%s) :: _left_path=%s' % (_utils.funcName(),_left_path))

	_isAnalysis_using_CSV_data = (len(_analysisData) > 0)
	
	if (_isReload):
	    _isAnalysis = _isAnalysis_using_CSV_data # force the analysis True if reloading from a CSV file.
	    
	    for fname in [fname for fname in os.listdir(_data_path) if (fname.endswith('.dbx') > -1)]:
		_fname = os.sep.join([_data_path, fname])
		if (os.path.exists(_fname)):
		    os.remove(_fname)
	    
	    if (not _isAnalysis):
		d_left_files = collect_files_from_path(_left_path,branch_name)
	    else:
		d_left_files = lists.HashedLists2(dict([(tb_name.strip(),tb_name.strip()) for tb_name in _analysisData if (len(tb_name.strip()) > 0)]))
	    
	    dbx_left_files_name = storeDataInto(_data_path, 'left_files.dbx', d_left_files)
	    
	    num_left_files = len(d_left_files)
	    logging.info('(%s) :: num_left_files=%s' % (_utils.funcName(),num_left_files))
	    
	    dbx = oodb.PickledHash2(dbx_left_files_name,oodb.PickleMethods.useSafeSerializer)
	    
	    dbx_num_left_files = len(dbx)
	    logging.info('(%s) :: dbx_num_left_files=%s' % (_utils.funcName(),dbx_num_left_files))
	    
	    dbx.close()
	    
	    assert dbx_num_left_files == num_left_files, 'Oops, something went wrong with the data reload process for "%s", expected to get %d records but got %d instead..' % (dbx_left_files_name,num_left_files,dbx_num_left_files)
	    
	    _right_path = os.sep.join([right_path,branch_name])
	    logging.info('(%s) :: _right_path=%s' % (_utils.funcName(),_right_path))

	    if (not _isAnalysis):
		d_right_files = collect_files_from_path(_right_path,branch_name)
	    else:
		d_right_files = lists.HashedLists2(d_left_files.asDict())
	
	    dbx_right_files_name = storeDataInto(_data_path, 'right_files.dbx', d_right_files)

	    num_right_files = len(d_right_files)
	    logging.info('(%s) :: num_right_files=%s' % (_utils.funcName(),num_right_files))
	    
	    dbx = oodb.PickledHash2(dbx_right_files_name,oodb.PickleMethods.useSafeSerializer)
	    
	    dbx_num_right_files = len(dbx)
	    logging.info('(%s) :: dbx_num_right_files=%s' % (_utils.funcName(),dbx_num_right_files))
	    
	    dbx.close()
	    
	    assert dbx_num_right_files == num_right_files, 'Oops, something went wrong with the data reload process for "%s", expected to get %d records but got %d instead..' % (dbx_right_files_name,num_right_files,dbx_num_right_files)
	    
	    d_both_left_and_right = lists.HashedLists()
	    
	    d_left_only = lists.HashedLists2(d_left_files.asDict())
	    d_right_only = lists.HashedLists2(d_right_files.asDict())
	    
	    for k,v in d_left_files.iteritems():
		d_both_left_and_right[k] = v
		if (d_right_only[k]):
		    d_right_only[k] = None
	    
	    for k,v in d_right_files.iteritems():
		d_both_left_and_right[k] = v
		if (d_left_only[k]):
		    d_left_only[k] = None
		
	    for k,v in d_both_left_and_right.iteritems():
		if (len(v) == 1):
		    d_both_left_and_right[k] = None
	
	    dbx_both_left_and_right_name = storeDataInto(_data_path, 'both_left_and_right.dbx', d_both_left_and_right)
	    dbx_left_only_name = storeDataInto(_data_path, 'left_only.dbx', d_left_only)
	    dbx_right_only_name = storeDataInto(_data_path, 'right_only.dbx', d_right_only)

	    num_both_left_and_right = len(d_both_left_and_right)
	    logging.info('(%s) :: num_both_left_and_right=%s' % (_utils.funcName(),num_both_left_and_right))
	    
	    num_left_only = len(d_left_only)
	    logging.info('(%s) :: num_left_only=%s' % (_utils.funcName(),num_left_only))
		    
	    num_right_only = len(d_right_only)
	    logging.info('(%s) :: num_right_only=%s' % (_utils.funcName(),num_right_only))
	    
	    dbx = oodb.PickledHash2(dbx_both_left_and_right_name,oodb.PickleMethods.useSafeSerializer)
	    
	    dbx_num_both_left_and_right_files = len(dbx)
	    logging.info('(%s) :: dbx_num_both_left_and_right_files=%s' % (_utils.funcName(),dbx_num_both_left_and_right_files))
	    
	    dbx.close()
	    
	    assert dbx_num_both_left_and_right_files == num_both_left_and_right, 'Oops, something went wrong with the data reload process for "%s", expected to get %d records but got %d instead..' % (dbx_both_left_and_right_name,num_both_left_and_right,dbx_num_both_left_and_right_files)
	    
	    dbx = oodb.PickledHash2(dbx_left_only_name,oodb.PickleMethods.useSafeSerializer)
	    
	    dbx_num_left_only_files = len(dbx)
	    logging.info('(%s) :: dbx_num_left_only_files=%s' % (_utils.funcName(),dbx_num_left_only_files))
	    
	    dbx.close()
	    
	    assert dbx_num_left_only_files == num_left_only, 'Oops, something went wrong with the data reload process for "%s", expected to get %d records but got %d instead..' % (dbx_left_only_name,num_left_only,dbx_num_left_only_files)
	    
	    dbx = oodb.PickledHash2(dbx_right_only_name,oodb.PickleMethods.useSafeSerializer)
	    
	    dbx_num_right_only_files = len(dbx)
	    logging.info('(%s) :: dbx_num_right_only_files=%s' % (_utils.funcName(),dbx_num_right_only_files))
	    
	    dbx.close()
	    
	    assert dbx_num_right_only_files == num_right_only, 'Oops, something went wrong with the data reload process for "%s", expected to get %d records but got %d instead..' % (dbx_right_only_name,num_right_only,dbx_num_right_only_files)
	else:
	    #_isAnalysis = False
	    #logging.warning('(%s) :: Loading from cached data has not yet been implemented.' % (_utils.funcName()))
	    pass

	dbx_left_files_name = os.sep.join([_data_path, 'left_files.dbx'])
	dbx_left_files = oodb.PickledHash2(dbx_left_files_name,oodb.PickleMethods.useSafeSerializer)
	
	dbx_num_left_files = len(dbx_left_files)
	logging.info('(%s) :: dbx_num_left_files=%s' % (_utils.funcName(),dbx_num_left_files))
	
	dbx_right_files_name = os.sep.join([_data_path, 'right_files.dbx'])
	dbx_right_files = oodb.PickledHash2(dbx_right_files_name,oodb.PickleMethods.useSafeSerializer)
	
	dbx_num_right_files = len(dbx_right_files)
	logging.info('(%s) :: dbx_num_right_files=%s' % (_utils.funcName(),dbx_num_right_files))
	
	dbx_both_left_and_right_name = os.sep.join([_data_path, 'both_left_and_right.dbx'])
	dbx_both_left_and_right = oodb.PickledHash2(dbx_both_left_and_right_name,oodb.PickleMethods.useSafeSerializer)
	
	dbx_num_both_left_and_right_files = len(dbx_both_left_and_right)
	logging.info('(%s) :: dbx_num_both_left_and_right_files=%s' % (_utils.funcName(),dbx_num_both_left_and_right_files))
	
	dbx_left_only_name = os.sep.join([_data_path, 'left_only.dbx'])
	dbx_left_only = oodb.PickledHash2(dbx_left_only_name,oodb.PickleMethods.useSafeSerializer)
	
	dbx_num_left_only_files = len(dbx_left_only)
	logging.info('(%s) :: dbx_num_left_only_files=%s' % (_utils.funcName(),dbx_num_left_only_files))
	
	dbx_right_only_name = os.sep.join([_data_path, 'right_only.dbx'])
	dbx_right_only = oodb.PickledHash2(dbx_right_only_name,oodb.PickleMethods.useSafeSerializer)
	
	dbx_num_right_only_files = len(dbx_right_only)
	logging.info('(%s) :: dbx_num_right_only_files=%s' % (_utils.funcName(),dbx_num_right_only_files))
	
	d_fnames = lists.HashedLists2({'dbx_left_files_name':dbx_left_files_name,'dbx_right_files_name':dbx_right_files_name,'dbx_both_left_and_right_name':dbx_both_left_and_right_name,'dbx_left_only_name':dbx_left_only_name,'dbx_right_only_name':dbx_right_only_name,'dbx_Cases_fname':dbx_Cases_fname,'dbx_Team_Branch__c_fname':dbx_Team_Branch__c_fname,'dbx_Task_Branch__c_fname':dbx_Task_Branch__c_fname})

	if (_isAnalysis):
	    performAnalysis(sfdc,'d_both_left_and_right',_left_path,_stream_name,dbx_both_left_and_right)
	elif (_isBrowse):
	    performBrowse(_data_path,d_fnames)
	elif (os.path.exists(_analysisFolder)):
	    performSpecificAnalysis(sfdc,_data_path,d_fnames)
	elif (_isTaskBranch__c):
	    performTaskBranchAnalysis([sfdc])
	else:
	    logging.warning('(%s) :: Analysis was not performed because it was not requested.' % (_utils.funcName()))
	
	if (not _isReload):
	    if (dbx_num_right_only_files == 0):
		assert dbx_num_both_left_and_right_files + dbx_num_left_only_files == dbx_num_left_files, '(%s) :: Oops, Something went wrong, number of files on both left and right (%d) plus number of files of left only (%d) does jnot equal number of files on left (%d).' % (_utils.funcName(),dbx_num_both_left_and_right_files,dbx_num_left_only_files,dbx_num_left_files)
    
	    dbx_left_files.close()
	    dbx_right_files.close()
	    dbx_both_left_and_right.close()
	    dbx_left_only.close()
	    dbx_right_only.close()
	
	ioTimeAnalysis.ioEndTime('%s' % (__name__))
	
	logging.info('+++ (%s) :: %s' % (_utils.funcName(),ioTimeAnalysis.ioTimeAnalysisReport()))

    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))
    pass

if __name__ == "__main__": 
    def ppArgs():
	pArgs = [(k,args[k]) for k in args.keys()]
	pPretty = PrettyPrint.PrettyPrint('',pArgs,True,' ... ')
	pPretty.pprint()

    args = {'--help':'displays this help text.','--verbose':'output more stuff.','--reload':'reload the local data from the remote host.','--analysis':'perform analysis.','--analysis=?':'perform analysis based on a folder that contains Tokens.','--browse':'browse dbx files.','--folder=?':'names the folder in which the logs and data will reside.','--branch=?':'name of branch (talus1.0, etc).','--team_branches':'allow task branches to be the same as team branches in case task branch is not found.','--task_branch__c=?':'name of Branch__c from Task_Branch__c.','--logging=?':'[logging.INFO,logging.WARNING,logging.ERROR,logging.DEBUG]'}
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
	    logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))
	    _isVerbose = False

	_branchName = None
	try:
	    if _argsObj.arguments.has_key('branch'):
		_branchName = _argsObj.arguments['branch']
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))
	    _branchName = None
	    
	_isReload = False
	try:
	    if _argsObj.booleans.has_key('isReload'):
		_isReload = _argsObj.booleans['isReload']
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))
	    _isReload = False
	    
	_isTeamBranches = False
	try:
	    if _argsObj.booleans.has_key('isTeam_branches'):
		_isTeamBranches = _argsObj.booleans['isTeam_branches']
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))
	    _isTeamBranches = False

	_isAnalysis = False
	try:
	    if _argsObj.booleans.has_key('isAnalysis'):
		_isAnalysis = _argsObj.booleans['isAnalysis']
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))
	    _isAnalysis = False

	try:
	    if _argsObj.arguments.has_key('analysis'):
		f = _argsObj.arguments['analysis']
		if (os.path.exists(f)):
		    if (os.path.isdir(f)):
			_analysisFolder = f
		    else:
			try:
			    csv = CSV(f)
			    csv_header_toks = [(t.split(),t) for t in csv.header]
			    _target_toks = 'Task Branch'.split()
			    isFound = None
			    for tt in _target_toks:
				for t in csv_header_toks:
				    if (tt in t[0]):
					isFound = t[-1]
					break
			    if (isFound):
				try:
				    _analysisData = csv.column(isFound)
				    _analysisFolder = f
				except ValueError:
				    logging.warning('Cannot use the --analysis argument because "%s" does not appear to contain any data in the column(s) in which the tokens %s appears in row 1 although this file appears to be a valid Excel file type.' % (f,_target_toks))
			    else:
				logging.warning('Cannot use the --analysis argument because "%s" does not appear to contain any columns in which the tokens %s appears in row 1 although this file appears to be a valid Excel file type.' % (f,_target_toks))
			except ValueError:
			    logging.warning('Cannot use the --analysis argument because "%s" does not appear to be a valid Excel file type.' % (f))
		else:
		    logging.warning('Cannot use the --analysis argument because "%s" does not exist.' % (f))
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))
	    _isAnalysis = False
	    
	_isBrowse = False
	try:
	    if _argsObj.booleans.has_key('isBrowse'):
		_isBrowse = _argsObj.booleans['isBrowse']
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))
	    _isBrowse = False
	    
	try:
	    if _argsObj.arguments.has_key('folder'):
		f = _argsObj.arguments['folder']
		if (os.path.exists(f)):
		    _folderPath = f
		else:
		    logging.warning('Cannot use the --folder argument because "%s" does not exist.' % (f))
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))
	    
	_isTaskBranch__c = False
	try:
	    if _argsObj.arguments.has_key('task_branch__c'):
		_task_branch__c = _argsObj.arguments['task_branch__c']
		_isTaskBranch__c = len(_task_branch__c) > 0
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    logging.warning('(%s) :: %s' % (_utils.funcName(),info_string))
	    _isTaskBranch__c = False
	
	try:
	    _logging = eval(_argsObj.arguments['logging']) if _argsObj.arguments.has_key('logging') else False
	except:
	    _logging = logging.WARNING

	if (os.path.exists(_analysisFolder)):
	    _isBrowse = False
	    
	if (_isTaskBranch__c):
	    _isAnalysis = False
	    _isBrowse = False

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
	    
	    _cwd = os.path.dirname(sys.argv[0])
	    if (os.environ.has_key('cwd')):
		_cwd = os.environ['cwd']
	    
	    print '_cwd=%s' % _cwd
	    
	    if (len(_cwd) > 0) and (os.path.exists(_cwd)):
		name = _utils.getProgramName()
		
		if (os.path.exists(_folderPath)):
		    _log_path = _utils.safely_mkdir(fpath=_folderPath)
		    _data_path = _utils.safely_mkdir(fpath=_folderPath,dirname='dbx')
		else:
		    _log_path = _utils.safely_mkdir(fpath=_cwd)
		    _data_path = _utils.safely_mkdir(fpath=_cwd,dirname='dbx')
		
		logFileName = os.sep.join([_log_path,'%s_%s.log' % (_utils.timeStamp().replace(':','-'),name)])
		
		standardLogging.standardLogging(logFileName,_level=_logging,isVerbose=_isVerbose)
		
		logging.info('Logging to "%s" using level of "%s:.' % (logFileName,standardLogging.explainLogging(_logging)))
	
		_stdOut = open(os.sep.join([_log_path,'stdout.txt']),'w')
		_stdErr = open(os.sep.join([_log_path,'stderr.txt']),'w')
		
		sys.stdout = Log(_stdOut)
		sys.stderr = Log(_stdErr)
	
		logging.warning('stdout to "%s".' % (_stdOut.name))
		logging.warning('stderr to "%s".' % (_stdErr.name))
		
		lists.prettyPrint(_argsObj,title='Command Line Arguments',fOut=sys.stdout)
	
		if (d_passwords.has_key(_username)):
		    _password = d_passwords[_username]
		else:
		    _password = []
		if (len(_username) > 0) and (len(_password) > 0):
		    logging.info('username is "%s", password is known and valid.' % (_username))
		    try:
			sfdc = Connection.connect(_username, _password[0], _password[-1])
			logging.info('sfdc=%s' % str(sfdc))
			logging.info('sfdc.endpoint=%s' % str(sfdc.endpoint))
			
			ioTimeAnalysis.initIOTime('%s' % (__name__)) 
			ioTimeAnalysis.initIOTime('SOQL') 

			ros = connectToRiver()
			    
			if (not _branchName):
			    _branchName = ''
			_full_branch_name = os.sep.join([_branchName,'done'])
			if (_isBeingDebugged):
			    runWithAnalysis(main,[sfdc,_left_path,_right_path,_full_branch_name])
			else:
			    import cProfile
			    cProfile.run('runWithAnalysis(main,[sfdc,_left_path,_right_path,_full_branch_name])', os.sep.join([_log_path,'profiler.txt']))
			
			if (ros):
			    ros.close()
		    except AttributeError:
			exc_info = sys.exc_info()
			info_string = '\n'.join(traceback.format_exception(*exc_info))
			logging.warning(info_string)
		    except ApiFault:
			exc_info = sys.exc_info()
			info_string = '\n'.join(traceback.format_exception(*exc_info))
			logging.warning(info_string)
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
	    

