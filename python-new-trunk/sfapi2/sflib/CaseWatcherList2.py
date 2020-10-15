""" 
This is the new CaseWatcherList process - the old one seems dead. 

SalesForce Data: Last Process Time
Notifications ?
""" 
_fromEmailAddress = 'salesforce-support@molten-magma.com'

import pprint 
import os, sys 
import textwrap 
import time
import datetime 
import types

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

# To-Do:
#         (1). Dummy-up some email messages to self via QK SMTP Server
#         (2). Port code from buildNotification and action to format the messages.
#         (3). Ensure emails look as they should compared to the current system and sample some on a random basis.
#         (4). Deploy the code...

import logging

import latestFolder

from vyperlogix.mail import message

from vyperlogix.misc import LazyImport

from pyax.connection import Connection
from pyax.exceptions import ApiFault

from pyax_code.specific import CaseWatcher
from pyax_code import sf_query

from vyperlogix.sf import delete as pyax_delete

from vyperlogix.daemon.daemon import Log
from vyperlogix.daemon.daemon import CustomLog
from vyperlogix.logging import standardLogging
from vyperlogix.hash import lists
from vyperlogix.misc import ObjectTypeName
from vyperlogix.misc import _utils
from vyperlogix.misc.ReportTheList import reportTheList

from vyperlogix.lists.ListWrapper import ListWrapper

from vyperlogix.misc import Args
from vyperlogix.misc import PrettyPrint

from vyperlogix import oodb

from vyperlogix.misc import threadpool

import traceback

sfConstant = LazyImport.LazyImport('sfConstant',locals={},globals={})

from clearDataPathOfFiles import clearDataPathOfFiles

from getLastProcessDate2 import getLastProcessDate2
from Crypto import *

import runWithAnalysis

_case_created_by_window_minutes = 15 # this must be a positive number of minutes.

from vyperlogix.mail import mailServer
import MailEvent

_isBeingDebugged = _utils.isBeingDebugged # When debugger is being used we do not use threads...

_email_blacklist = lists.HashedLists2() # key is the email address that should not get emails.

_email_blacklist['molten-support@molten-magma.com'] = 1
_email_blacklist['sf_prototyping@molten-magma.com'] = 1
_email_blacklist['sf_ops@molten-magma.com'] = 1
_email_blacklist['sf_anaconda@molten-magma.com'] = 1

_count_of_pre_emails_dequeued = 0

_count_of_pre_emails_enqueued = 0
_count_of_pre_emails_blacklisted = 0

import Queue

_proc_queue = threadpool.ThreadQueue(300)

_cases_queue = Queue.Queue()

_pre_email_queue = Queue.Queue()

_email_queue = Queue.Queue()

_use_cases_queue = True # always True whether debugged or not.

_isVerbose = False

_isSerialize = True # this is no longer an option however it is an integral part of this program.

_emailPool = lists.HashedLists()

__isBeingDebugged = _isBeingDebugged
_isBeingDebugged = True

# BEGIN: These booleans control whether or not SalesForce is accessed via OS Threads...
procify_getCasesByComponentName = (not _isBeingDebugged)
procify_getCasesByTeamId = (not _isBeingDebugged)
procify_getCasesByUserId = (not _isBeingDebugged)
procify_getCaseById = (not _isBeingDebugged)
procify_getCasesByAccountId = (not _isBeingDebugged)
procify_crLinks = (not _isBeingDebugged)
procify_cw = (not _isBeingDebugged) # WARNING: this variable CANNOT be made True because the programming model will not support running each CaseWatcher as a separate thread.
# END! These booleans control whether or not SalesForce is accessed via OS Threads...

_isBeingDebugged = __isBeingDebugged

if (0):
    procify_getCasesByComponentName = False
    procify_getCasesByTeamId = False
    procify_getCasesByUserId = False
    procify_getCaseById = False
    procify_getCasesByAccountId = False
    procify_crLinks = False
    procify_cw = False

_cw_queue_slots = 300 if ((procify_getCasesByComponentName) or (procify_getCasesByTeamId) or (procify_getCasesByUserId) or (procify_getCaseById) or (procify_getCasesByAccountId) or (procify_crLinks) or (procify_cw)) else 1

_cw_queue = threadpool.ThreadQueue(_cw_queue_slots)

d_fields = {
    'Status':'Status',
    'Description':'Description',
    'Weekly_Notes__c':'Weekly_Notes__c',
    'Priority':'Priority',
    'Component__c':'Component__c',
    'CustomerPriority__c':'CustomerPriority__c',
    'Requested_End_Date__c':'Requested_End_Date__c',
    'Estimated_Finish_Date__c':'Estimated_Finish_Date__c',
    'R_D_Submission__c':'R_D_Submission__c',
    'OwnerId':'OwnerId',
    'R_D_Commitment_Date__c':'R_D_Commitment_Date__c',
    'ScheduleStatus__c':'ScheduleStatus__c',
    'Status_1_Stream__c':'Status_1_Stream__c',
    'Target_Analysis_Done__c':'Target_Analysis_Done__c',
    'TargetFastTrackBuild__c':'TargetFastTrackBuild__c',
    'Target_Fix_Available__c':'Target_Fix_Available__c',
    'Target_Fix_Merged__c':'Target_Fix_Merged__c',
    'Target_Releases__c':'Target_Releases__c',
    'TimeStampBuild__c':'TimeStampBuild__c',

    'CommentBody':"Select c.CommentBody, c.Id, c.IsDeleted, c.IsPublished, c.LastModifiedDate from CaseComment c where (c.ParentId = '%s') and (c.IsDeleted = False) and (c.IsPublished = True) order by c.LastModifiedDate",
}


d_init_fields = lists.HashedLists2({
    'Case_Fields_Deferred__c':'Case Fields (Immediate notification)',
    'Component__c':'Component',
    'Case_Fields__c':'Case Fields (Immediate notification)',
    'Case_Scope__c':'Case Scope'
})

_stdOut = None
_stdErr = None

_cwd = None

_dbx_name = lambda dbx_path, object_name:os.sep.join([dbx_path,'%s.dbx' % (object_name)])
dbx_name = lambda object_name:_dbx_name(_data_path,object_name)
isStringOptionNotMissing = lambda opt:( (opt is not None) and (len(opt) > 0) )
isStringOptionMissing = lambda opt:(not isStringOptionNotMissing(opt))

asMailEvent = lambda glob:glob if (ObjectTypeName.typeClassName(glob) == 'MailEvent.MailEvent') else MailEvent.MailEvent(glob)
asDict = lambda glob:glob if (type(glob) == types.DictionaryType) else glob.asDict()
asPyaxDict = lambda glob:glob if (type(glob) == types.DictionaryType) else lists.HashedLists2(glob).asDict()
asPyaxDictList = lambda glob:asPyaxDict(glob) if (not isinstance(glob,list)) else [asPyaxDict(item) for item in glob]

isMolten = lambda email:(email.lower().split('@')[-1] != 'molten-magma.com')
isBlacklisted = lambda email:(_email_blacklist[email] != None)

def pretty_up(name):
    s = ' '.join(name.replace('__c','').split('_'))
    t = ''
    for ch in s:
	if (ch.isupper()) and (len(t) > 0):
	    t += ' '
	t += ch
    return t

def is_case_changed():
    '''This function is used only for development and will not be used when in production.'''
    import random
    return ((random.random()*2) > 1.5)

def is_running_locally():
    return _utils.getComputerName().lower() in ['rhorn-lap.ad.moltenmagma.com']

def _handle_to_dbx_key(handle):
    handle = handle if (isinstance(handle,list)) else [handle] if (not isinstance(handle,tuple)) else list(handle)
    return '_'.join([str(item) for item in handle])

def begin_AnalysisDataPoint():
    runWithAnalysis.begin_AnalysisDataPoint('SOQL') 

def end_AnalysisDataPoint():
    runWithAnalysis.end_AnalysisDataPoint('SOQL') 

class CaseWatcherList: 
    def __init__(self,sfdc=None,cwd=os.path.abspath('.')):
        self.__sfdc__ = sfdc
        self.__cwd__ = cwd
	self.mailserver = None
        self.d_caseWatchers = lists.HashedLists()
	self.__chgs__ = []
	self.__base_dicts__ = []
	self.d_isEmailAddressValid = lists.HashedLists2()
	self.api = CaseWatcher.CaseWatcherAPI(self.sfdc,d_fields,begin_AnalysisDataPoint,end_AnalysisDataPoint,runWithAnalysis.count_query)

	#ret = self.getCaseById('5003000000523HjAAI')
	#pass
     
    def _getLastProcessDate(self):
	if (_date_LastProcessDate is not None):
	    t_checksince = _date_LastProcessDate
	else:
	    p = lists.HashedLists2()
	    log_path = os.path.dirname(os.path.dirname(_log_path)) # this has to match the logging policy...
	    p.fromDict({'update' : False, 'cwd': self.cwd, 'data_path': _data_path, 'log_path': log_path, 'time_source':[os.sep.join(['logs', f]) for f in ['stderr.txt','stdout.txt','profiler.txt','end_CaseWatchers_scan.txt']], 'filename' : 'LastCaseWatcherProcessedDate', 'diff_minutes' : -15})
	    checksince = getLastProcessDate2(p)
	    toks = checksince.split('.')
	    checksince = toks[0]+'.000Z'
	    t_checksince = _utils.getFromDateTimeStr(checksince,format=_utils.formatTimeStr())
	    if (p['log_path'] is None): # when log_path is specified then the last runtime is determined from the actual last runtime based on the time the last run concluded...
		_utc_delta = _utils.utcDelta()
		t_checksince -= _utc_delta
        return  t_checksince
    
    def getCaseFieldsById(self,id,fields):
	return self.api.getCaseFieldsById(id,fields)
    
    def getUserByEmail(self, email): 
        return self.api.getUserByEmail(email)

    def setHistoryByEmail(self, email, msg): 
	if (_isSerialize):
	    dbx_db = oodb.PickledFastCompressedHash2(dbx_name('Email_History'))
	    try:
		dbx_db[email] = msg
	    except:
		exc_info = sys.exc_info()
		info_string = '\n'.join(traceback.format_exception(*exc_info))
		info_string = self.api.self_asMessage(self,'Cannot persist email history for "%s" with "%s", Reason: %s' % (email,msg,info_string))
		print >>sys.stderr, info_string
		logging.error(info_string)
	    finally:
		dbx_db.sync()
		dbx_db.close()
    
    def getPeristedDataById(self, name, id): 
	datum = None
	if (_isSerialize):
	    dbx_db = oodb.PickledFastCompressedHash2(dbx_name(name))
	    try:
		o_data = dbx_db[id]
		print >>sys.stdout, '%s :: (%s) o_data=%s' % (ObjectTypeName.objectSignature(self),str(o_data.__class__),str(o_data))
		if (isinstance(o_data,tuple)) and (len(o_data) == 2):
		    ret,_ret = o_data
		    datum = [([lists.HashedLists2(ret_item) for ret_item in ret],[lists.HashedLists2(_ret_item) for _ret_item in _ret])]
		elif (isinstance(o_data,list)):
		    datum = [([lists.HashedLists2(ret_item) for ret_item in ret],[lists.HashedLists2(_ret_item) for _ret_item in _ret]) for ret,_ret in o_data]
	    except:
		exc_info = sys.exc_info()
		info_string = '\n'.join(traceback.format_exception(*exc_info))
		info_string = self.api.self_asMessage(self,'Cannot retrieve persist %s #1, Reason: %s' % (name,info_string))
		print >>sys.stderr, info_string
		logging.error(info_string)
	    finally:
		dbx_db.sync()
		dbx_db.close()
	return datum
    
    def getCaseChangesById(self, id): 
	if (_isUseTrigger):
	    chgs = self.api.getCaseChangesById(id)
	    if (chgs is not None):
		ids,_chgs = chgs
		for c in _chgs:
		    c['CreatedDate'] = _utils.localFromUTC(_utils.getFromDateTimeStr(c['CreatedDate'].isoformat().split('+')[0]))
	else:
	    if (_isSerialize):
		s_name = 'Cases_State'
		previous_folder = None if (len(_latestFolders) < 1) else _latestFolders[-1][0]
		
		if (previous_folder is not None):
		    
		    previous_folder = os.sep.join([previous_folder,_data_path.split(os.sep)[-1]])
		    dbx_cases = oodb.PickledFastCompressedHash2(_dbx_name(previous_folder,s_name))
		    try:
			if (dbx_cases.has_key(id)):
			    data_list = [([lists.HashedLists2(ret_item) for ret_item in ret],[lists.HashedLists2(_ret_item) for _ret_item in _ret]) for ret,_ret in [t for t in dbx_cases[id]]]
			    base_dict = data_list[0][0][0]
			    _base_dict = lists.HashedLists2(base_dict).asDict()
			    for ret,_ret in data_list:
				diff = base_dict.diff(ret[0])
				if (len(diff) > 0):
				    base_dict = ret[0]
			    o_data = self.getPeristedDataById(s_name,id)
			    if (o_data is not None):
				current_dict = o_data[0][0][0]
				diff = base_dict.diff(current_dict)
				if (len(diff) > 0):
				    ids = []
				    _chgs = []
				    for k,v in base_dict.iteritems():
					ids.append(id)
					_chg = {'CaseId__c':id, 'ChangedFieldName__c':v, 'CreatedById':None, 'CreatedDate':_utils.getFromDateTimeStr(_utils.timeStampLocalTime()), 'Id':None, 'IsDeleted':False, 'LastModifiedById':None, 'LastModifiedDate':None, 'Name':None, 'OldFieldValue__c': _base_dict[k]}
					_chgs.append(_chg)
				    chgs = (ids,_chgs)
				self.__base_dicts__.append(base_dict) # debugging only.
			pass
		    except:
			exc_info = sys.exc_info()
			info_string = '\n'.join(traceback.format_exception(*exc_info))
			info_string = self.api.self_asMessage(self,'Cannot read persisted Cases_State for Case Id %s, Reason: %s' % (id,info_string))
			print >>sys.stderr, info_string
			logging.error(info_string)
		    finally:
			dbx_cases.sync()
			dbx_cases.close()
		else:
		    info_string = self.api.self_asMessage(self,'Unable to determine changes in Case Id %s due to failure of all systems to do so, this is normal when CaseWatcher is being run for the first time and the SalesForce Trigger is not functioning or there are simply no changes in Case Id "%s".' % (id,id))
		    print >>sys.stderr, info_string
		    
	self.__chgs__.append(chgs)# debugging only.

        return chgs

    def getCaseWatcherById(self, id): 
        return self.api.getCaseWatcherById(id)

    def getComponentById(self, id): 
        return self.api.getComponentById(id)

    def getAccountById(self, id): 
        return self.api.getAccountById(id)
    
    def getAccountParentByAccountId(self, id): 
        return self.api.getAccountParentByAccountId(id)
    
    def getAccountsByParentId(self, id): 
        return self.api.getAccountsByParentId(id)
    
    def getAccountTreeById(self, id, partial=False):
        return self.api.getAccountTreeById(id,partial)
    
    def getCRLinksById(self, id): 
        return self.api.getCRLinksById(id)

    def getCasesByTeamId(self, team_id, windowIsoDateTime): 
        return self.api.getCasesByTeamId(team_id,windowIsoDateTime)

    def getCasesByUserId(self, user_id, windowIsoDateTime): 
        return self.api.getCasesByUserId(user_id,windowIsoDateTime)

    def getCasesByComponentName(self, cname, windowIsoDateTime): 
        return self.api.getCasesByComponentName(cname,windowIsoDateTime)

    def getCasesByAccountId(self, id, windowIsoDateTime):
        return self.api.getCasesByAccountId(id,windowIsoDateTime)
    
    def getCaseById(self, id, windowIsoDateTime=(None,None)): 
	if (windowIsoDateTime):
	    return self.api.getCaseById(id,windowIsoDateTime)
	return self.api.getCaseById(id)

    def sendMessage(self, toAddress, subj, body, fromAddress=_fromEmailAddress):
	from vyperlogix.misc import decodeUnicode
	
	_message = lambda reason:'Cannot perform email function for fromAddress of "%s", toAddress of "%s", subj of "%s" because %s.' % (fromAddress,toAddress,subj,reason)
	if (self.mailserver):
	    try:
		msg = message.Message(fromAddress, toAddress, decodeUnicode.ensureOnlyPrintableChars(decodeUnicode.decodeUnicode(body),mask='[]'),subject=subj)
		self.mailserver.sendEmail(msg)
	    except:
		exc_info = sys.exc_info()
		info_string = '\n'.join(traceback.format_exception(*exc_info))
		info_string = self.api.self_asMessage(self,_message(info_string))
		print >>sys.stderr, info_string
		logging.error(info_string)
		return False
	else:
	    logging.warning(_message('there is no mailserver'))
	
	return True
    
    def isEmailAddressValid(self,_email):
	bool_tuple = self.d_isEmailAddressValid[_email]
	if (bool_tuple is not None):
	    return bool_tuple
	else:
	    ret = self.getUserByEmail(_email)
	    if (ret not in sfConstant.BAD_INFO_LIST):
		_isAnyActive = False
		_isBlacklisted = False
		for k in ret.keys():
		    _isAnyActive |= ( (ret[k]['ContactStatus__c'] != None) and (ret[k]['ContactStatus__c'] == 'Active') )
		    _isBlacklisted |= (isBlacklisted(ret[k]['Email']))
		bool_tuple = (_isAnyActive, _isBlacklisted)
		if (not _isAnyActive):
		    self.setHistoryByEmail(_email,self.api.asMessage_for_self(self,'ContactStatus__c from User__c is %s.' % (_isAnyActive)))
		if (_isBlacklisted):
		    self.setHistoryByEmail(_email,self.api.asMessage_for_self(self,'Black listed status is %s.' % (_isBlacklisted)))
		self.d_isEmailAddressValid[_email] = bool_tuple
		return bool_tuple
	return (False, True)

    def dropCaseWatchers(self):
	if (_isInitialize):
	    d_caseWatchers = self.api.getCaseWatcherById(None) # get all casewatchers.
	    l_deleted_ids = pyax_delete.deleteSalesForceObjects(self.sfdc,d_caseWatchers.keys())
	    reportTheList(l_deleted_ids,'%s :: Deleted Case Watcher Objects during Initialize function.' % (ObjectTypeName.objectSignature(self)),fOut=sys.stdout)
	    pass
    
    def process(self):
        _baseTime = self._getLastProcessDate()
        windowIsoDateTime = time.strftime(_utils._formatTimeStr(), _baseTime.timetuple())
        _prevHour = _utils.getFromDateTimeStr(windowIsoDateTime,format=_utils._formatTimeStr()) - datetime.timedelta(minutes=_case_created_by_window_minutes)
        _windowIsoDateTime = time.strftime(_utils._formatTimeStr(), _prevHour.timetuple())
        
        windowIsoDateTime = _utils.reformatSalesForceTimeStr(windowIsoDateTime)
        _windowIsoDateTime = _utils.reformatSalesForceTimeStr(_windowIsoDateTime)
        
        print >> sys.stdout, ''
        print >> sys.stdout, '(c.CreatedDate from Case c) must be before _windowIsoDateTime=%s\n' % _windowIsoDateTime
        print >> sys.stdout, '(c.LastModifiedDate from Case c) must be on/after windowIsoDateTime=%s\n' % windowIsoDateTime

	_utils.writeFileFrom(os.sep.join([_log_path,'begin_CaseWatchers_scan.txt']),'begin: %s --> %s' %(windowIsoDateTime,_windowIsoDateTime))
	
	d_emails_by_casewatcher__c = lists.HashedLists()
	
        runWithAnalysis.count_query()
        soql="Select c.Case_Watcher__c, c.Id, c.LastModifiedDate, c.Name, c.Alias_Email__c, c.Email__c from Case_Watcher_List__c c"
	if (isStringOptionNotMissing(_casewatcher)):
	    soql += " where (c.Id = '%s') or (c.Name = '%s')" % (_casewatcher,_casewatcher)
        ret = self.api._sf_query(soql)
        if ret in sfConstant.BAD_INFO_LIST:
	    logging.info("(%s) :: Could not find any Case_Watcher_List__c Object(s)." % (_utils.funcName()))
        else:
            logging.info('(%s) soql=%s' % (_utils.funcName(),soql))
            print >> sys.stdout, '%s :: Collecting my thoughts about Case Watchers...' % (ObjectTypeName.objectSignature(self))
            try:
                for cw_list in ret:
                    _id = cw_list['Case_Watcher__c']
                    if (_id):
			anEmail = cw_list['Email__c']
			d_emails_by_casewatcher__c[_id] = anEmail
                        self.d_caseWatchers[_id] = cw_list
		    if (_limitCaseWatchers > -1) and (len(self.d_caseWatchers) == _limitCaseWatchers):
			print >> sys.stdout, '%s :: Case Watchers limit reached at %s...' % (ObjectTypeName.objectSignature(self),_limitCaseWatchers)
			break
            except:
                exc_info = sys.exc_info()
                info_string = self.api.self_asMessage(self,'\n'.join(traceback.format_exception(*exc_info)))
		print >>sys.stderr, info_string
                logging.warning(info_string)
		
	    if (not _isInitialize):
		for _id,emails in d_emails_by_casewatcher__c.iteritems():
		    results = [test for test in [self.isEmailAddressValid(email) for email in emails] if test[0] and not test[-1]]
		    if (len(results) == 0):
			del self.d_caseWatchers[_id]
			print >> sys.stderr, '%s :: Case_Watcher_List__c with id of "%s" has no valid emails to which a notification could be sent so it has been removed.' % (ObjectTypeName.objectSignature(self),_id)
		    pass
            
            _cases_ = lists.HashedLists2()
            _case_watchers_ = lists.HashedLists2()
            
            _associations_by_case_ = lists.HashedLists()
            _associations_by_cw_ = lists.HashedLists()
            
            def recoverKeyValFrom(d,k):
                from vyperlogix.misc import decodeUnicode
                _id = None
                for key,val in d.iteritems():
                    x = decodeUnicode.decodeUnicode(key)
                    if (x == k):
                        _id = val
                return _id
            
            def track_case_by_id(c):
                _id = c['Id']
                if (not _id):
                    _id = recoverKeyValFrom(c[0],'Id')
                if (_id):
                    _cases_[_id] = c
                else:
                    logging.warning('(%s) :: WARNING: There is no Id "%s" for case: %s' % (_utils.funcName(),_id,c))
            
            def track_case_associations(c,k):
                _id = c['Id']
                if (not _id):
                    _id = recoverKeyValFrom(c[0],'Id')
                if (_id):
                    _associations_by_case_[_id] = k
                    _associations_by_cw_[k] = _id
                else:
                    logging.warning('(%s) :: WARNING: There is no Id "%s" for case: %s' % (_utils.funcName(),_id,c))

            @threadpool.threadify(_proc_queue)
            def deQueue_Cases(q): 
                while True: 
                    c,k = q.get()
                    track_case_by_id(c)
                    track_case_associations(c,k)
                    q.task_done() 
            
            def enQueue_Mail_Events(case_id,cw,cw_list,associations_by_cw):
		logging.info('(%s) :: Case ID: %s (%s)' % (_utils.funcName(),case_id,ObjectTypeName.typeName(case_id)))
                logging.info('(%s) :: BEGIN: Watcher List' % (_utils.funcName()))
                try:
                    case_obj = _cases_[case_id]
                    logging.info('(%s) :: Case: %s' % (_utils.funcName(),case_obj))
                    logging.info('(%s) :: CaseWatcher: %s' % (_utils.funcName(),cw))
                    for d_item in cw_list:
			d_cases = lists.HashedLists2()
			for c in associations_by_cw[cw['Id']]:
			    d_cases[c] = lists.HashedLists2(_cases_[c])
			
                        evt = MailEvent.MailEvent({'cw':cw,'item':d_item,'Case':d_cases})
			evt.case_list = d_cases.keys()
			_emailPool[evt.item_Email__c] = evt
                        logging.info('(%s) :: evt: %s' % (_utils.funcName(),evt))
                except:
                    exc_info = sys.exc_info()
                    info_string = self.api.self_asMessage(self,'\n'.join(traceback.format_exception(*exc_info)))
		    print >>sys.stderr, info_string
                    logging.warning(info_string)
                logging.info('(%s) :: END! Watcher List' % (_utils.funcName()))
            
            @threadpool.threadify(_proc_queue)
            def deQueue_PreEmails(q,associations_by_cw): 
                global _count_of_pre_emails_dequeued
                while True: 
                    case_id, cw, cw_list = q.get()
                    enQueue_Mail_Events(case_id,cw,cw_list,associations_by_cw)
                    _count_of_pre_emails_dequeued += 1
                    q.task_done() 
            
            def queue_PreEmails(packet): 
                global _count_of_pre_emails_enqueued
                global _count_of_pre_emails_blacklisted
                try:
                    sfdc,k_case_id,cw,d_list = packet
                    _d_list_acceptable = []
                    for item in d_list:
                        if (item.has_key('Name')) and (item.has_key('Email__c')):
                            _email = item['Email__c']
			    _isAnyActive, _isBlacklisted = self.isEmailAddressValid(_email)
			    if (_isAnyActive) and (not _isBlacklisted):
				_d_list_acceptable.append(item)
				logging.info('\t(%s) :: Name: %s, Email: %s, (%s) ret=%s' % (_utils.funcName(),item['Name'],item['Email__c'],ObjectTypeName.typeName(ret),ret))
			    if (not _isAnyActive):
				_msg = '(%s) :: Cannot send email address %s a notification because this is not an ACTIVE contact email for SalesForce.' % (_utils.funcName(),_email)
				self.setHistoryByEmail(_email,self.api.asMessage_for_self(self,_msg))
				logging.warning(_msg)
			    if (_isBlacklisted):
				_msg = '(%s) :: Cannot send email address %s a notification because this is a BLACKLISTED contact email.' % (_utils.funcName(),_email)
				self.setHistoryByEmail(_email,self.api.asMessage_for_self(self,_msg))
				logging.warning(_msg)
                            pass
                    if (len(_d_list_acceptable) > 0):
                        _pre_email_queue.put_nowait([k_case_id,cw,_d_list_acceptable])
                        _count_of_pre_emails_enqueued += 1
                    else:
                        _count_of_pre_emails_blacklisted += 1
                        logging.warning('(%s) :: Cannot send any email notification(s) for case id of %s because there are no ACTIVE contact email(s) in SalesForce.' % (_utils.funcName(),k_case_id))
                except:
                    exc_info = sys.exc_info()
                    info_string = self.api.self_asMessage(self,'\n'.join(traceback.format_exception(*exc_info)))
                    print >> sys.stderr, info_string
            
            def do_getCasesByComponentName(k, cname, ts):
                _cases = self.getCasesByComponentName(cname, ts)
                try:
                    for c in _cases:
                        if (_use_cases_queue):
                            _cases_queue.put_nowait([c,k])
                        else:
                            track_case_by_id(c)
                            track_case_associations(c,k)
                except:
                    pass
            
            @threadpool.threadify(_proc_queue)
            def proc_getCasesByComponentName(k, cname, ts):
                do_getCasesByComponentName(k, cname, ts)
                
            def do_getCasesByTeamId(k, teamId,ts):
                _cases = self.getCasesByTeamId(teamId,ts)
                try:
                    for c in _cases:
                        if (_use_cases_queue):
                            _cases_queue.put_nowait([c,k])
                        else:
                            track_case_by_id(c)
                            track_case_associations(c,k)
                except:
                    pass
            
            @threadpool.threadify(_proc_queue)
            def proc_getCasesByTeamId(k, teamId,ts):
                do_getCasesByTeamId(k, teamId,ts)
                
            def do_getCasesByUserId(k, userid,ts):
                _cases = self.getCasesByUserId(userid,ts)
                try:
                    for c in _cases:
                        if (_use_cases_queue):
                            _cases_queue.put_nowait([c,k])
                        else:
                            track_case_by_id(c)
                            track_case_associations(c,k)
                except:
                    pass
                
            @threadpool.threadify(_proc_queue)
            def proc_getCasesByUserId(k, userid,ts):
                do_getCasesByUserId(k, userid,ts)
                
            def do_getCaseById(k, caseNum,ts):
                _cr = self.getCaseById(caseNum,ts)
                if (_cr):
                    if (_use_cases_queue):
                        _cases_queue.put_nowait([_cr,k])
                    else:
                        track_case_by_id(_cr)
                        track_case_associations(_cr,k)
                    logging.info('\tCR: %s' % str(_cr))
                
            @threadpool.threadify(_proc_queue)
            def proc_getCaseById(k, caseNum,ts):
                do_getCaseById(k, caseNum,ts)
                
            def do_getCasesByAccountId(k, acctId, ts):
		cases = self.getCasesByAccountId(acctId, ts)
                for c in cases:
                    if (_use_cases_queue):
                        _cases_queue.put_nowait([c,k])
                    else:
                        track_case_by_id(c)
                        track_case_associations(c,k)
                
            @threadpool.threadify(_proc_queue)
            def proc_getCasesByAccountId(k, acctId, ts):
                do_getCasesByAccountId(k, acctId, ts)
                
            def handle_getCasesByAccountId(k, acctTree,ts):
                for a in acctTree:
                    if (procify_getCasesByAccountId):
                        proc_getCasesByAccountId(k, a['Id'], ts)
                    else:
                        do_getCasesByAccountId(k, a['Id'], ts)
                        
            def do_crLinks(k, cr,ts):
                try:
                    if (cr.has_key('Parent_CR__c')):
                        _cr = self.getCaseById(cr['Parent_CR__c'],ts)
                        if (_cr):
                            if (_use_cases_queue):
                                _cases_queue.put_nowait([_cr,k])
                            else:
                                track_case_by_id(_cr)
                                track_case_associations(_cr,k)
                            logging.info('\tParent_CR: %s' % str(_cr))
                except:
                    pass
            
            @threadpool.threadify(_proc_queue)
            def proc_crLinks(k, cr,ts):
                do_crLinks(k, cr,ts)
                
            def handle_crLinks(k, _crLinks, ts):
                if (_crLinks != None):
                    try:
                        if (_crLinks.keys()[0] != None):
                            try:
                                for cr in _crLinks:
                                    if (procify_crLinks):
                                        proc_crLinks(k, cr,ts)
                                    else:
                                        do_crLinks(k, cr,ts)
                            except:
                                exc_info = sys.exc_info()
                                info_string = self.api.self_asMessage(self,'\n'.join(traceback.format_exception(*exc_info)))
				print >> sys.stderr, info_string
                                logging.warning(info_string)
                    except:
                        pass
                
            def do_cw(cw):
                _case_watchers_[k] = cw
                if (cw.has_key('Name')):
                    logging.info('Case Watcher Name: %s' % cw['Name'])
                if (cw.has_key('Case_Fields__c')):
                    logging.info('Case Fields: %s' % cw['Case_Fields__c'])
                if (cw.has_key('Component__c')):
                    comp_id = cw['Component__c']
                    if (comp_id):
                        comp = self.getComponentById(comp_id)
                        logging.info('Component: %s' % str(comp))
                        if (comp.has_key('Name')):
                            comp_name = comp['Name']
                            if (comp_name):
                                if (procify_getCasesByComponentName):
                                    proc_getCasesByComponentName(k, comp_name, [_windowIsoDateTime,windowIsoDateTime])
                                else:
                                    do_getCasesByComponentName(k, comp_name, [_windowIsoDateTime,windowIsoDateTime])
                if (cw.has_key('Team__c')):
                    team_id = cw['Team__c']
                    if (team_id):
                        if (procify_getCasesByTeamId):
                            proc_getCasesByTeamId(k, team_id, [_windowIsoDateTime,windowIsoDateTime])
                        else:
                            do_getCasesByTeamId(k, team_id, [_windowIsoDateTime,windowIsoDateTime])
                if (cw.has_key('User__c')):
                    user_id = cw['User__c']
                    if (user_id):
                        if (procify_getCasesByUserId):
                            proc_getCasesByUserId(k, user_id, [_windowIsoDateTime,windowIsoDateTime])
                        else:
                            do_getCasesByUserId(k, user_id, [_windowIsoDateTime,windowIsoDateTime])
                if (cw.has_key('Case_Number__c')):
                    caseNum = cw['Case_Number__c']
                    if (caseNum):
                        if (procify_getCaseById):
                            proc_getCaseById(k, caseNum,[_windowIsoDateTime,windowIsoDateTime])
                        else:
                            do_getCaseById(k, caseNum,[_windowIsoDateTime,windowIsoDateTime])
                if (cw.has_key('Case_Scope__c')):
                    caseScope = cw['Case_Scope__c']
                    if (caseScope):
                        logging.info('Case Scope: %s' % caseScope)
                        if (cw.has_key('Account__c')):
                            acct_id = cw['Account__c']
                            if (acct_id):
                                acct = self.getAccountById(acct_id)
                                logging.info('Account: %s' % str(acct))
                                if (caseScope.lower() == 'account only'):
                                    if (acct_id):
                                        if (procify_getCasesByAccountId):
                                            proc_getCasesByAccountId(k, acct_id, [_windowIsoDateTime,windowIsoDateTime])
                                        else:
                                            do_getCasesByAccountId(k, acct_id, [_windowIsoDateTime,windowIsoDateTime])
                                else:
                                    if (caseScope.lower() == 'whole account tree'):
                                        acct_tree = self.getAccountTreeById(acct_id)
                                    elif (caseScope.lower() == 'account and parents'):
                                        acct_tree = self.getAccountTreeById(acct_id,partial=True)
                                        acct_tree.append(acct)
                                    logging.info('Account Tree: %s' % str(acct_tree))
                                    if (acct_tree):
                                        handle_getCasesByAccountId(k, acct_tree,[_windowIsoDateTime,windowIsoDateTime])
                if (cw.has_key('Tech_Campaign__c')):
                    techCampaign = cw['Tech_Campaign__c']
                    if (techCampaign):
                        crLinks = self.getCRLinksById(techCampaign)
                        if (crLinks):
                            logging.info('Tech_Campaign: %s' % techCampaign)
                            handle_crLinks(k, crLinks,[_windowIsoDateTime,windowIsoDateTime])
                        else:
                            logging.warning('No Cr_Link for "%s".' % cw['Tech_Campaign__c'])
                logging.info('Case Watcher: %s' % str(cw))
            
            @threadpool.threadify(_cw_queue)
            def proc_cw(cw):
                do_cw(cw)
                
            def handle_cw(cw):
		if (procify_cw):
		    proc_cw(cw)
		else:
		    do_cw(cw)
                
            def do_init_cw(cw,cwlists):
		_Name = ''
		_Email__c = ''
                if (cw.has_key('Name')):
                    logging.info('Case Watcher Name: %s' % cw['Name'])
		    if (isinstance(cwlists,list)):
			_cw_Name = cw['Name'] # {CaseWatcher Name or Id}
			for cw_list in cwlists:
			    if (cw_list.has_key('Email__c')):
				_Email__c = cw_list['Email__c']
				if (_Email__c is not None):
				    if (not isBlacklisted(_Email__c)):
					aUser = self.getUserByEmail(_Email__c)
					if aUser not in sfConstant.BAD_INFO_LIST:
					    if (len(aUser.keys()) > 0):
						try:
						    _Name = aUser[aUser.keys()[0]]['Name'] # {Name of Contact}
						    msg_buffer = StringIO()
						    self.buildDeadCaseWatcherNotification(_Email__c,cw,_Name,fOut=msg_buffer)
						    self.sendMessage(_Email__c,'CaseWatcher Subscription Removal Notice.',msg_buffer.getvalue())
						except Exception, details:
						    info_string = self.api.self_asMessage(self,'Cannot send email to %s, Reason: %s' % (_Email__c,str(details)))
						    print >>sys.stderr, info_string
						    logging.error(info_string)
					    else:
						info_string = self.api.self_asMessage(self,'Cannot send email to %s, Reason: Dead email address in SalesForce.' % (_Email__c))
						print >>sys.stderr, info_string
						logging.error(info_string)
					    pass
				    else:
					info_string = self.api.self_asMessage(self,'Cannot send email to %s, Reason: Email address is already Blacklisted.' % (_Email__c))
					print >>sys.stderr, info_string
					logging.error(info_string)
				pass
			    pass
			pass
		    pass
		pass
		    
            def init_cw(cw,v):
		do_init_cw(cw,v)
                
	    if (not _isInitialize):
		if (_use_cases_queue):
		    deQueue_Cases(_cases_queue)
	    else:
		if (len(_smtpserver) > 0):
		    self.mailserver = mailServer.AdhocServer(_smtpserver)
		else:
		    print >>sys.stderr, 'Cannot send emails because _smtpserver is "%s".' % (_smtpserver)
            
	    print >> sys.stdout, '\nWaiting for CaseWatchers to %s.' % ('process' if (not _isInitialize) else 'initialize')

	    if (not _isInitialize) and (_isSerialize):
		dbx_cw = oodb.PickledFastCompressedHash2(dbx_name('CaseWatchers'))

	    d_cwlists_to_be_deleted = lists.HashedLists2()
	    d_cw_to_be_deleted = lists.HashedLists2()
	    
	    try:
		for k,v in self.d_caseWatchers.iteritems():
		    logging.info('Case Watcher Id=[%s]' % k)
		    cw = self.getCaseWatcherById(k)
		    if (not _isInitialize) and (_isSerialize):
			dbx_cw[k] = asPyaxDict(cw)
		    if (not _isInitialize):
			handle_cw(cw)
		    else:
			init_cw(cw,v)
			d_cw_to_be_deleted[k] = 1
			for cwlist in v:
			    d_cwlists_to_be_deleted[cwlist['Id']] = 1
	    except:
		exc_info = sys.exc_info()
		info_string = '\n'.join(traceback.format_exception(*exc_info))
		info_string = self.api.self_asMessage(self,'Cannot handle CaseWatchers, Reason: %s' % (info_string))
		print >>sys.stderr, info_string
		logging.error(info_string)
	    finally:
		if (not _isInitialize) and (_isSerialize):
		    dbx_cw.sync()
		    dbx_cw.close()

	    if (_isInitialize):
		if (len(d_cwlists_to_be_deleted) > 0):
		    l_cwlist_deleted_ids = pyax_delete.deleteSalesForceObjects(self.sfdc,d_cwlists_to_be_deleted.keys())
		    reportTheList(l_cwlist_deleted_ids,'%s :: Deleted Case Watcher List Objects during Initialize function.' % (ObjectTypeName.objectSignature(self)),fOut=sys.stdout)
		else:
		    info_string = self.api.self_asMessage(self,'Cannot delete Case Watcher List Objects, Reason: There are none to delete.')
		    print >>sys.stdout, info_string
		    logging.warning(info_string)

		if (len(d_cw_to_be_deleted) > 0):
		    l_cw_deleted_ids = pyax_delete.deleteSalesForceObjects(self.sfdc,d_cw_to_be_deleted.keys())
		    reportTheList(l_cw_deleted_ids,'%s :: Deleted Case Watcher Objects during Initialize function.' % (ObjectTypeName.objectSignature(self)),fOut=sys.stdout)
		else:
		    info_string = self.api.self_asMessage(self,'Cannot delete Case Watcher Objects, Reason: There are none to delete.')
		    print >>sys.stdout, info_string
		    logging.warning(info_string)
		    
	    if (not _isInitialize) and (procify_cw):
		print >> sys.stdout, '\nWaiting for _proc_queue to join().'
		_proc_queue.join()
		print >> sys.stdout, '\nWaiting for _cw_queue to join().'
		_cw_queue.join()
		
	    print >> sys.stdout, '\nCaseWatchers have %s.' % ('processed' if (not _isInitialize) else 'initialized')
	    print >> sys.stdout, '\n'
                        
	    _utils.writeFileFrom(os.sep.join([_log_path,'end_CaseWatchers_scan.txt']),'end: %s --> %s' %(windowIsoDateTime,_windowIsoDateTime))

	    if (not _isInitialize):
		print >> sys.stdout, '\nWaiting for Cases to DeQueue.'
		_cases_queue.join()
		print >> sys.stdout, '\nCases have DeQueued.'
		print >> sys.stdout, '\n'
		
		logging.info('')
		logging.info('BEGIN: (%s) Unique Cases by ID %s' % (len(_cases_),'='*80))
		i = 1
		for k,v in _cases_.iteritems():
		    logging.info('%s :: %s --> %s\n' % (i,k,v))
		    i += 1
		logging.info('END! %s' % ('='*80))
		logging.info('')
		logging.info('BEGIN: (%s) Unique Case Watchers by ID %s' % (len(_case_watchers_),'='*80))
		i = 1
		for k,v in _case_watchers_.iteritems():
		    logging.info('%s :: %s --> %s\n' % (i,k,v))
		    i += 1
		logging.info('END! %s' % ('='*80))
		logging.info('')
		
		deQueue_PreEmails(_pre_email_queue,_associations_by_cw_)
    
		# BEGIN: EnQueue pre-email elements - these get fed into a process that makes MailEvents
		for k_case_id,v_list_of_cw_ids in _associations_by_case_.iteritems():
		    for d_item in v_list_of_cw_ids:
			d_list = self.d_caseWatchers[d_item]
			cw = _case_watchers_[d_item]
			queue_PreEmails([self.sfdc,k_case_id,cw,d_list])
		print 'Placed %d pre-email items on the Queue.' % (_count_of_pre_emails_enqueued)
		print 'Blocked %d pre-email items from the Queue.' % (_count_of_pre_emails_blacklisted)
		# END! EnQueue pre-email elements - these get fed into a process that makes MailEvents
		
		msg = 'Send Notification for this list (%d Cases) resulting in (%d emails) !' % (len(_cases_),_count_of_pre_emails_enqueued)
		print >> sys.stdout, '\n'+msg+'\n'
		
		print >> sys.stdout, '\nWaiting for Pre-Emails to DeQueue.'
		_pre_email_queue.join()
		print >> sys.stdout, '\nPre-Emails have DeQueued.  There are %d objects.' % (_count_of_pre_emails_dequeued)
    
		print >> sys.stdout, 'BEGIN: Case to Watcher Associations %s' % ('='*80)
		i = 0
		for k,v in _associations_by_case_.iteritems():
		    print >> sys.stdout, '%s :: Case: %s --> Watcher: %s' % (i,k,v)
		    print >> sys.stdout, '\tBEGIN: Watcher List'
		    for d_item in v:
			d_list = self.d_caseWatchers[d_item]
			if (len(d_list) == 0):
			    logging.error('Case: %s has no Watcher List Email Addresses.' % (k))
			else:
			    i += 1
			    for item in d_list:
				c_item = lists.HashedLists2(item)
				if (c_item.has_key('Name')) and (c_item.has_key('Email__c')):
				    if (c_item['Case_Watcher__c'] is not None) and (c_item['Case_Watcher__c'] == d_item):
					c_item['__cw__'] = self.getCaseWatcherById(d_item)
				    lists.prettyPrint(c_item,prefix='\t',title='Name: %s, Email: %s' % (c_item['Name'],c_item['Email__c']),fOut=sys.stdout)
		    print >> sys.stdout, '\tEND! Watcher List'
		i -= _count_of_pre_emails_blacklisted
		print >> sys.stdout, 'END! %s' % ('='*80)
		assert _count_of_pre_emails_enqueued == _count_of_pre_emails_dequeued, '\nERROR 1.1: Oops, something went wrong.  There should be %d pre-email objects (EnQueued) but there were %d instead.\n' % (_count_of_pre_emails_enqueued,_count_of_pre_emails_dequeued)
		assert i == _count_of_pre_emails_dequeued, '\nERROR 1.2: Oops, something went wrong.  There should be %d pre-email objects but there were %d instead.\n' % (_count_of_pre_emails_dequeued,i)
		print >> sys.stdout, 'Validated the Pre-Emails EnQueued and DeQueued.'
		
		print >> sys.stdout, ''
		logging.info('BEGIN: Watcher to Case Associations %s' % ('='*80))
		i = 0
		for k,v in _associations_by_cw_.iteritems():
		    logging.info('%s :: Watcher: %s --> Case: %s\n' % (i,k,v))
		    i += 1
    
		if (_isSerialize):
		    dbx_cwc = oodb.PickledFastCompressedHash2(dbx_name('CaseWatcher2Cases'))
		    try:
			for k,v in _associations_by_cw_.iteritems():
			    dbx_cwc[k] = v
		    except:
			exc_info = sys.exc_info()
			info_string = '\n'.join(traceback.format_exception(*exc_info))
			info_string = self.api.self_asMessage(self,'Cannot persist CaseWatcher2Cases, Reason: %s' % (info_string))
			print >>sys.stderr, info_string
			logging.error(info_string)
		    finally:
			dbx_cwc.sync()
			dbx_cwc.close()
		    
		if (len(_smtpserver) > 0):
		    self.mailserver = mailServer.AdhocServer(_smtpserver)
		    print >>sys.stdout, '%s :: len(_emailPool)=%s' % (ObjectTypeName.objectSignature(self),len(_emailPool))
		    if (_isSerialize):
			dbx_evt = oodb.PickledFastCompressedHash2(dbx_name('Mail_Events'))
			for k,evts in _emailPool.iteritems():
			    dbx_evt[k] = [asDict(evt) for evt in evts]
		    try:
			self.handle_emails(_emailPool)
		    except:
			exc_info = sys.exc_info()
			info_string = '\n'.join(traceback.format_exception(*exc_info))
			info_string = self.api.self_asMessage(self,'Cannot Email Case Watcher Notifications, Reason: %s' % (info_string))
			print >>sys.stderr, info_string
			logging.error(info_string)
		    finally:
			if (_isSerialize):
			    dbx_evt.sync()
			    dbx_evt.close()
		else:
		    print >>sys.stderr, 'Cannot send emails because _smtpserver is "%s".' % (_smtpserver)
		
		logging.info('END! %s' % ('='*80))
		logging.info('')
		print
        return 
    
    def buildDeadCaseWatcherNotification(self,toEmail,cw,_name,fOut=sys.stdout):
	from vyperlogix.sf.hostify import hostify
	from vyperlogix.html import myOOHTML as oohtml
	from vyperlogix.misc import decodeUnicode
	
	def doesFolderContainFolder(_path,_name):
	    f_files = [f for f in os.listdir(_path) if (os.path.isdir(os.sep.join([_path,f]))) and (f == _name)]
	    return len(f_files) > 0
	
	fpath = os.path.dirname(sys.argv[0])
	while (os.path.exists(fpath)) and (not doesFolderContainFolder(fpath,'data')):
	    fpath = os.path.dirname(fpath)
	fpath = os.sep.join([fpath,'data'])
	fpath = os.sep.join([fpath,'Dead CaseWatcher List Notification.htm'])
	if (os.path.exists(fpath)):
	    template_contents = decodeUnicode.ensureOnlyPrintableChars(decodeUnicode.decodeUnicode(_utils.readFileFrom(fpath,noCRs=True)),mask='')
	    _cw = lists.HashedLists2(cw)
	    if (_cw['Component__c'] is not None):
		_cw['Component__c'] = self.api.getComponentById(_cw['Component__c'])['Name']
	    if (_cw['Case_Fields_Deferred__c'] is not None) and (len(_cw['Case_Fields_Deferred__c']) > 0):
		_cw['Case_Fields_Deferred__c'] = '<br/>'.join(_cw['Case_Fields_Deferred__c'].split(';'))
	    if (_cw['Case_Fields__c'] is not None) and (len(_cw['Case_Fields__c']) > 0):
		_cw['Case_Fields__c'] = '<ul>%s</ul>' % (''.join(['<li>%s</li>' % (s) for s in _cw['Case_Fields__c'].split(';')]))
	    for k,v in _cw.iteritems():
		if (v is None) or (len(str(v)) == 0) or (d_init_fields[k] is None):
		    del _cw[k]
		if (d_init_fields[k] is not None):
		    _cw[d_init_fields[k]] = _cw[k]
		    del _cw[k]
	    _table = oohtml.renderTable(['<b>Attribute Name</b>','<b>Attribute Value</b>'],_cw,width='50%',border='1')
	    if (isMolten(toEmail)):
		_anchor = oohtml.renderAnchor('https://molten.moltenmagma.com','https://molten.moltenmagma.com')
	    else:
		host = hostify(self.sfdc.endpoint)
		_url = 'a0t/o'
		_anchor = oohtml.renderAnchor('https://%s/%s' % (host,_url),'Case Watchers')
	    template_contents = template_contents.replace('{Name of Contact}',_name).replace('{CaseWatcher Name or Id}','' if (not cw.has_key('Name')) else cw['Name']).replace('{CaseWatcher Object details appear here.}',_table).replace('{Molten&nbsp;or&nbsp;SalesForce}',_anchor)
	    print >>fOut, template_contents
	    pass
	else:
	    _msg = 'Unable to send emails because "%s" is missing or cannot be read.' % (fpath)
	    logging.error(self.api.asMessage_for_self(self,_msg))
	pass
    
    def buildNotification(self,toEmail,unique_cases,fOut=sys.stdout):
	from vyperlogix.sf.hostify import hostify
	from vyperlogix.html import myOOHTML as oohtml
	
	_subj = ''
	
	if (lists.isDict(unique_cases)):
	    _aUser = self.getUserByEmail(toEmail)
	    if (_aUser):
		aUser = _aUser[_aUser.keys()[0]]
		print >>fOut, 'To: %s (%s)' % (aUser['Name'],toEmail)
		num_cases = len(unique_cases)
		plural_cases = 's' if (num_cases > 1) else ''
		print >>fOut, ''
		print >>fOut, 'The following Case Watcher Notification%s are for your information' % (plural_cases)
		print >>fOut, '-'*72
		print >>fOut, ''
		num_events = 1
		for case,evt in unique_cases.iteritems():
		    if (len(evt) == 3):
			_chgs, aCase, aCaseWatcher = evt

			cw_dt = _utils.getFromSalesForceDateStr(str(aCaseWatcher['LastModifiedDate']))
			print >>fOut, '(%d). %s   Case Watcher: %s    CR:%s    Case Subject: %s' % (num_events,_utils.getAsSimpleDateStr(cw_dt,_utils.formatShortDateTimeStr()),aCaseWatcher['Name'],aCase['CaseNumber'],aCase['Subject'])

			for aChg in _chgs:
			    assert aChg['CaseId__c'] == case, '%s :: Something has gone terribly wrong at #1, possibly using the wrong data element for the CaseId__c.' % (ObjectTypeName.objectSignature(self))
			    assert aChg['CaseId__c'] == aCase['Id'], '%s :: Something has gone terribly wrong at #2, possibly using the wrong data element for the CaseId__c.' % (ObjectTypeName.objectSignature(self))

			    try:
				ret,_ret = self.getCaseFieldsById(case,[aChg['ChangedFieldName__c']])
				fCase = ret[ret.keys()[0]]
				try:
				    newValue = fCase[self.api.d_fields_of_interest[aChg['ChangedFieldName__c']]]
				except:
				    if (len(_ret) > 0) and (aChg['ChangedFieldName__c'] == list(self.api.s_non_case_fields_of_interest)[0]):
					_ret_keys = _ret[-1].keys()
					if (len(_ret_keys) > 0):
					    fCaseComment = _ret[-1][_ret_keys[-1]]
					    try:
						newValue = fCaseComment[aChg['ChangedFieldName__c']]
					    except KeyError:
						logging.error('fCaseComment.keys()=%s' % (fCaseComment.keys()))
						logging.error('fCaseComment=%s' % (str(fCaseComment)))
					else:
					    newValue = 'UNDEFINED'
				    else:
					newValue = 'UNDEFINED'
				_is_date = str(aChg['ChangedFieldName__c']).find('Date') > -1
				_msg = "%s: '%s' changed " % (_utils.getAsSimpleDateStr(aChg['LastModifiedDate'],_utils.formatShortDateTimeStr()),pretty_up(aChg['ChangedFieldName__c']))
				print >>fOut, _msg
				s_newValue = newValue if (not _is_date) else _utils.reformatSalesForceDateStrAsMMDDYYYY(newValue)
				print >>fOut, '   FROM "%s"<br/><br/>TO "%s"<hr align="left" width="40%%"/>' % (aChg['OldFieldValue__c'],s_newValue)
				self.setHistoryByEmail(toEmail,self.api.asMessage_for_self(self,_msg))
			    except:
				exc_info = sys.exc_info()
				info_string = '\n'.join(traceback.format_exception(*exc_info))
				info_string = self.api.self_asMessage(self,'Cannot Build Case Watcher Notification, Reason: %s' % (info_string))
				print >>sys.stderr, info_string
				logging.error(info_string)
			num_events += 1
			pass
		    if (isMolten(toEmail)):
			_anchor = oohtml.renderAnchor('https://molten.moltenmagma.com/cases/show/%s' % (case),case)
		    else:
			host = hostify(self.sfdc.endpoint)
			_anchor = oohtml.renderAnchor('https://%s/%s' % (host,case),case)
		    print >>fOut, ' * Case Link: %s' % (_anchor.strip())
		    print >>fOut, '<hr/>'
		_subj = '%s: Magma Case Watcher Notifications (%d Event%s)' % (aUser['Name'],num_cases,plural_cases)
	    else:
		logging.warning('(%s) :: Cannot perform this function because the user for email of "%s" cannot be retrieved, check your code !' % (ObjectTypeName.objectSignature(self),toEmail))
	else:
	    logging.warning('(%s) :: Cannot perform this function because one of the parameters is not correct, check your code !' % (ObjectTypeName.objectSignature(self)))
	return _subj
    
    def handle_emails(self,dbx,debug_limits=-1):
	d_CaseChangesById = lists.HashedLists()
	d_CaseChangesByEmail = lists.HashedLists()
	d_SLAByEmail = lists.HashedLists()
	try:
	    l_to_be_deleted_changes_ids = []
	    i_limits = 1
	    db_name = dbx.fileName
	    logging.warning('BEGIN: %s' % (db_name))
	    for k,v in dbx.iteritems():
		logging.warning('\t%s' % (k))
		io_buffer = StringIO()
		io_buffer2 = StringIO()
		d_unique_case_list = lists.HashedLists2()
		for d in v:
		    if (d is not None):
			evt = asMailEvent(d)
			try:
			    for aCase in evt.case_list:
				d_unique_case_list[aCase] = evt
			except KeyError:
			    exc_info = sys.exc_info()
			    info_string = '\n'.join(traceback.format_exception(*exc_info))
			    info_string = self.api.self_asMessage(self,'Cannot process MailEvent case_list, Reason: %s' % (info_string))
			    print >>sys.stderr, info_string
			    logging.error(info_string)
			    
		if (_isSerialize):
		    dbx_cases = oodb.PickledFastCompressedHash2(dbx_name('Cases_State'))
		    try:
			for case,evt in d_unique_case_list.iteritems():
			    try:
				ret,_ret = self.getCaseFieldsById(case,self.api.d_fields_of_interest.keys())
				_data = ([lists.HashedLists2(ret[rec_key]).asDict() for rec_key in ret.keys()],[lists.HashedLists2(rec).asDict() for rec in _ret])
				#info_string = self.api.self_asMessage(self,'Cases_State :: case is "%s", _data is "%s".' % (case,str(_data)))
				#print >>sys.stderr, info_string
				dbx_cases[case] = _data
			    except:
				exc_info = sys.exc_info()
				info_string = '\n'.join(traceback.format_exception(*exc_info))
				info_string = self.api.self_asMessage(self,'Cannot persist Cases_State #1, Reason: %s' % (info_string))
				print >>sys.stderr, info_string
				logging.error(info_string)
		    except:
			exc_info = sys.exc_info()
			info_string = '\n'.join(traceback.format_exception(*exc_info))
			info_string = self.api.self_asMessage(self,'Cannot persist Cases_State #1, Reason: %s' % (info_string))
			print >>sys.stderr, info_string
			logging.error(info_string)
		    finally:
			dbx_cases.sync()
			dbx_cases.close()
		# Save the d_unique_case_list because this contains all the data we need... current state of the Case.
		# pull list of folders under logs and check the one prior to the one we are in that has data...
		#   for changes...
		d_unique_case_list2 = lists.HashedLists2()
		for kk,evt in d_unique_case_list.iteritems():
		    _chgs = self.getCaseChangesById(kk)
		    if (_chgs is not None) and (isinstance(_chgs,tuple)):
			for aChg in _chgs[-1]:
			    d_CaseChangesById[aChg['CaseId__c']] = asPyaxDict(aChg)
			l_to_be_deleted_changes_ids.append(_chgs[0])
			d_unique_case_list2[kk] = (_chgs[-1],lists.HashedLists2(evt['Case_%s' % kk]),evt.asSubDict('cw_'))
			d_CaseChangesByEmail[evt.item_Email__c] = asPyaxDict(aChg)
		    else:
			_msg = 'User with email address of "%s" has Case # %s with no changes.' % (k,kk)
			self.setHistoryByEmail(evt.item_Email__c,self.api.asMessage_for_self(self,_msg))
			info_string = self.api.self_asMessage(self,_msg)
			logging.warning(info_string)
		if (_isVerbose):
		    try:
			reportTheList(v,'\t\t%s%s for %s' % (ObjectTypeName.typeName(v[0]),'s' if (len(v) > 0) else '',k),fOut=io_buffer)
		    except:
			exc_info = sys.exc_info()
			info_string = '\n'.join(traceback.format_exception(*exc_info))
			info_string = self.api.self_asMessage(self,'Cannot reportTheList for an object of type "%s", Reason: %s' % (ObjectTypeName.typeName(v[0]),info_string))
			print >>sys.stderr, info_string
			logging.error(info_string)
		info_string = self.api.self_asMessage(self,'BEGIN: buildNotification')
		logging.info(info_string)
		if (len(d_unique_case_list2) > 0):
		    _subj = self.buildNotification(k,d_unique_case_list2,fOut=io_buffer2)
		    self.sendMessage(k,_subj,io_buffer2.getvalue())
		    self.setHistoryByEmail(k,self.api.asMessage_for_self(self,'Email sent to "%s" about Case(s) %s.' % (k,str(d_unique_case_list2.keys()))))
		    _chgs = d_CaseChangesByEmail[k]
		    for aChg in _chgs:
			dt = aChg['CreatedDate']
			if (dt is not None):
			    tdiff = _utils.getFromDateTimeStr(_utils.timeStampLocalTime()) - dt
			    d_SLAByEmail[k] = tdiff
		else:
		    info_string = self.api.self_asMessage(self,'User with email address of "%s" had %d Mail Events that resulted in %d emails because of the number of actual changes.' % (k,len(d_unique_case_list),len(d_unique_case_list2)))
		    logging.warning(info_string)
		info_string = self.api.self_asMessage(self,'END! buildNotification')
		logging.warning(info_string)
		print >>sys.stdout, io_buffer.getvalue()
		if (i_limits == debug_limits):
		    logging.warning('Debug Limit reached with %d records.' % (debug_limits))
		    break
		i_limits += 1
	    logging.warning('END! %s' % (db_name))
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    info_string = self.api.self_asMessage(self,'Cannot Email Case Watcher Notifications, Reason: %s' % (info_string))
	    print >>sys.stderr, info_string
	    logging.error(info_string)

	for _id in l_to_be_deleted_changes_ids:
	    l_deleted_ids = pyax_delete.deleteSalesForceObjects(self.sfdc,_id)
	    reportTheList(l_deleted_ids,'%s :: Deleted Case Changes' % (ObjectTypeName.objectSignature(self)),fOut=sys.stdout)

	db_name = dbx_name('Case_Changes')
	dbx_chgs = oodb.PickledFastCompressedHash2(db_name)
	try:
	    for k,v in d_CaseChangesById.iteritems():
		dbx_chgs[k] = v
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    info_string = self.api.self_asMessage(self,'Cannot save Case Changes, Reason: %s' % (info_string))
	    print >>sys.stderr, info_string
	    logging.error(info_string)
	finally:
	    dbx_chgs.close()
    
	db_name = dbx_name('Case_Changes_By_Email')
	dbx_chgs = oodb.PickledFastCompressedHash2(db_name)
	try:
	    for k,v in d_CaseChangesByEmail.iteritems():
		dbx_chgs[k] = v
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    info_string = self.api.self_asMessage(self,'Cannot save Case Changes by Email, Reason: %s' % (info_string))
	    print >>sys.stderr, info_string
	    logging.error(info_string)
	finally:
	    dbx_chgs.close()
    
	db_name = dbx_name('SLA_By_Email')
	dbx_chgs = oodb.PickledFastCompressedHash2(db_name)
	try:
	    for k,v in d_SLAByEmail.iteritems():
		dbx_chgs[k] = v
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    info_string = self.api.self_asMessage(self,'Cannot save SLA by Email, Reason: %s' % (info_string))
	    print >>sys.stderr, info_string
	    logging.error(info_string)
	finally:
	    dbx_chgs.close()
    
    def debug_emails(self,debug_limits):
	if (len(_smtpserver) > 0):
	    self.mailserver = mailServer.AdhocServer(_smtpserver)
	    db_name = dbx_name('Mail_Events')
	    dbx = oodb.PickledFastCompressedHash2(db_name)
	    try:
		self.handle_emails(dbx,debug_limits=debug_limits)
	    except:
		exc_info = sys.exc_info()
		info_string = '\n'.join(traceback.format_exception(*exc_info))
		info_string = self.api.self_asMessage(self,'Cannot Email Case Watcher Notifications, Reason: %s' % (info_string))
		print >>sys.stderr, info_string
		logging.error(info_string)
	    finally:
		dbx.close()
	else:
	    print >>sys.stderr, 'Cannot send emails because _smtpserver is "%s".' % (_smtpserver)
	
	logging.info('END! %s' % ('='*80))
	logging.info('')
	print
    
    def get_sfdc(self):
        return self.__sfdc__
    
    def get_cwd(self):
        return self.__cwd__
    
    sfdc = property(get_sfdc)
    cwd = property(get_cwd)
     
def main(args):
    runWithAnalysis.init_AnalysisDataPoint('SOQL') 
    runWithAnalysis.init_AnalysisDataPoint('EMAIL') 
    sfdc = args if (not isinstance(args,list)) and (not isinstance(args,tuple)) else args[0]
    n = CaseWatcherList(sfdc,cwd=_cwd)

    if (_isDebug) and (_isDebug_limits < 1):
	print >>sys.stderr, '%s :: WARNING: _isDebug_limits is %d and this is a bit of a problem so assuming you wanted to simulate data from SalesForce per the change records rather than debug the email system by specifying some kind of limitation.' % (_utils.funcName(),_isDebug_limits)
	
    if (_isDebug) and (_isDebug_limits > 0):
	n.debug_emails(_isDebug_limits)
    else:
	n.process() 
	if (_isInitialize):
	    n.dropCaseWatchers()
    
def asReadableData(s):
    return ','.join(['%d' % ord(ch) for ch in s])

def exception_callback(sections):
    _msg = 'EXCEPTION Causing Abend.\n%s' % '\n'.join(sections)
    print >>sys.stdout, _msg
    print >>sys.stderr, _msg
    logging.error(_msg)
    from vyperlogix.misc import putStr
    putStr.putStr(_msg)
    sys.exit(1)

#from vyperlogix.decorators import onexit
#@onexit.onexit
#def _onExit():
    #print >>sys.stdout, '(%s) :: _smtpserver_p=%s' % (_utils.funcName(),_smtpserver_p)

if __name__ == "__main__": 
    def ppArgs():
	pArgs = [(k,args[k]) for k in args.keys()]
	pPretty = PrettyPrint.PrettyPrint('',pArgs,True,' ... ')
	pPretty.pprint()

    args = {'--help':'show some help.',
	    '--verbose':'output more stuff.',
	    '--verbose_logging':'output more logging stuff to console.',
	    '--cwd=?':'the path the program runs from, defaults to the path the program runs from.',
	    '--smtpserver=?':'the path for the smtp server process or the address of the smtp server.',
	    '--casewatcher=?':'begin processing with this CaseWatcher Id, if not specified processing begins with all CaseWatchers.',
	    '--date=?':'force this date to be the start date for the CaseWatcher scan, must use the format of %s.' % (_utils._formatTimeStr()),
	    '--debug':'debug some stuff.',
	    '--initialize':'clear-out all CaseWatcher Objects and their CaseWatcher Lists - send emails.',
	    '--notrigger':'do not use the CaseWatcherChangedField__c trigger if this option is specified.',
	    '--nopsyco':'do not load Psyco when this option is used.',
	    '--procify_cw=?':'1 means True and 0 means False.',
	    '--debug=?':'debug some stuff, with limits.',
	    '--staging':'use the staging server rather than production otherwise use production.',
	    '--username=?':'username, use as-needed.',
	    '--password=?':'password, use as-needed.',
	    '--token=?':'login token, use as-needed.',
	    #'--serialize':'serialize some stuff to pass along to debugging step.',
	    '--limit_cw=?':'limit the number of case watchers to this number.',
	    '--logging=?':'[logging.INFO,logging.WARNING,logging.ERROR,logging.DEBUG]',
	    '--console_logging=?':'[logging.INFO,logging.WARNING,logging.ERROR,logging.DEBUG]'}
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
	    info_string = CaseWatcher.asMessage('\n'.join(traceback.format_exception(*exc_info)))
	    print >>sys.stderr, info_string
	    logging.warning(info_string)
	    _isVerbose = False
	    
	_isVerboseLogging = False
	try:
	    if _argsObj.booleans.has_key('isVerbose_logging'):
		_isVerboseLogging = _argsObj.booleans['isVerbose_logging']
	except:
	    exc_info = sys.exc_info()
	    info_string = CaseWatcher.asMessage('\n'.join(traceback.format_exception(*exc_info)))
	    print >>sys.stderr, info_string
	    logging.warning(info_string)
	    _isVerboseLogging = False
	
	_isHelp = False
	try:
	    if _argsObj.booleans.has_key('isHelp'):
		_isHelp = _argsObj.booleans['isHelp']
	except:
	    pass
	
	if (_isHelp):
	    ppArgs()
	
	_isDebug = False
	try:
	    if _argsObj.booleans.has_key('isDebug'):
		_isDebug = _argsObj.booleans['isDebug']
	except:
	    pass
	
	_isStaging = False
	try:
	    if _argsObj.booleans.has_key('isStaging'):
		_isStaging = _argsObj.booleans['isStaging']
	except:
	    pass
	
	_isInitialize = False
	try:
	    if _argsObj.booleans.has_key('isInitialize'):
		_isInitialize = _argsObj.booleans['isInitialize']
	except:
	    pass
	
	_isUseTrigger = True
	try:
	    if _argsObj.booleans.has_key('isNoTrigger'):
		_isUseTrigger = False if (_argsObj.booleans['isNoTrigger']) else _isUseTrigger
	except:
	    _isUseTrigger = True
	
	_isNoPsyco = False
	try:
	    if _argsObj.booleans.has_key('isNopsyco'):
		_isNoPsyco = not _argsObj.booleans['isNopsyco']
	    print >>sys.stderr, "_argsObj.booleans['isNopsyco']=%s" % (_argsObj.booleans['isNopsyco'])
	except:
	    exc_info = sys.exc_info()
	    info_string = CaseWatcher.asMessage('\n'.join(traceback.format_exception(*exc_info)))
	    print >>sys.stderr, info_string
	    logging.warning(info_string)
	    _isNoPsyco = False
	    
	_date_LastProcessDate = __date = None
	try:
	    if _argsObj.arguments.has_key('date'):
		__date = _argsObj.arguments['date']
		if (len(__date) > 0):
		    __date = _utils.getFromDateTimeStr(__date,format=_utils._formatTimeStr())
	except:
	    exc_info = sys.exc_info()
	    info_string = CaseWatcher.asMessage('\n'.join(traceback.format_exception(*exc_info)))
	    print >>sys.stderr, info_string
	    logging.warning(info_string)
	if (__date is not None):
	    _date_LastProcessDate = __date
	
	_isDebug_limits = -1
	try:
	    if _argsObj.arguments.has_key('debug'):
		__isDebug_limits = _argsObj.arguments['debug']
		if (__isDebug_limits.isdigit()):
		    _isDebug_limits = int(__isDebug_limits)
		    if (_isDebug_limits > -1):
			_isDebug = True
	except:
	    pass
	
	_procify_cw = False
	try:
	    if _argsObj.arguments.has_key('procify_cw'):
		__procify_cw = _utils.booleanize(_argsObj.arguments['procify_cw'])
		_procify_cw = __procify_cw
	except:
	    _procify_cw = False
	procify_cw = _procify_cw
	
	if (procify_cw):
	    print >>sys.stderr, 'WARNING: DO NOT attempt to use --procify_cw=1 at this time because this version does not support this option.'
	    procify_cw = False
	
	#_isSerialize = False
	#try:
	    #if _argsObj.booleans.has_key('isSerialize'):
		#_isSerialize = _argsObj.booleans['isSerialize']
	#except:
	    #pass
	
	_isDebug = False if (not _isSerialize) else _isDebug
	_msg = '_isDebug is %s because _isSerialize is %s' % (_isDebug,_isSerialize)
	print _msg
	logging.info('(%s) :: %s' % (_utils.funcName(),_msg))
	
	sf_token = ''
	try:
	    if _argsObj.arguments.has_key('token'):
		sf_token = _argsObj.arguments['token']
	except:
	    sf_token = ''
	
	sf_username = ''
	try:
	    if _argsObj.arguments.has_key('username'):
		sf_username = _argsObj.arguments['username']
	except:
	    sf_username = ''
	
	sf_password = ''
	try:
	    if _argsObj.arguments.has_key('password'):
		sf_password = _argsObj.arguments['password']
	except:
	    sf_password = ''
	
	_limitCaseWatchers = -1
	try:
	    _limitCaseWatchers = eval(_argsObj.arguments['limit_cw']) if _argsObj.arguments.has_key('limit_cw') else False
	except:
	    _limitCaseWatchers = -1
	    
	_logging = logging.WARNING
	try:
	    _logging = eval(_argsObj.arguments['logging']) if _argsObj.arguments.has_key('logging') else False
	except:
	    _logging = logging.WARNING
	    
	_console_logging = logging.WARNING
	try:
	    _console_logging = eval(_argsObj.arguments['console_logging']) if _argsObj.arguments.has_key('console_logging') else False
	except:
	    _console_logging = logging.WARNING

	__cwd__ = os.path.dirname(sys.argv[0])
	try:
	    __cwd = _argsObj.arguments['cwd'] if _argsObj.arguments.has_key('cwd') else __cwd__
	    if (len(__cwd) == 0) or (not os.path.exists(__cwd)):
		if (os.environ.has_key('cwd')):
		    __cwd = os.environ['cwd']
	    __cwd__ = __cwd
	except:
	    pass
	_cwd = __cwd__
	
	__smtpserver = ''
	_smtpserver_p = None
	try:
	    __smtpserver = _argsObj.arguments['smtpserver'] if _argsObj.arguments.has_key('smtpserver') else '-1'
	except:
	    pass
	_smtpserver = __smtpserver
	
	__casewatcher = ''
	try:
	    __casewatcher = _argsObj.arguments['casewatcher'] if _argsObj.arguments.has_key('casewatcher') else ''
	except:
	    pass
	_casewatcher = __casewatcher

	d_passwords = lists.HashedLists2()

	_isUsingAlternateUsername = False
	try:
	    s = ''.join([chr(ch) for ch in [126,254,192,145,170,209,4,52,159,254,122,198,76,251,246,151]])
	    pp = ''.join([ch for ch in decryptData(s).strip() if ord(ch) > 0])
	    d_passwords['rhorn@molten-magma.com'] = pp.replace('@','').replace('$','')
	    
	    s = ''.join([chr(ch) for ch in [39,200,142,151,251,164,142,15,45,216,225,201,121,177,89,252]])
	    pp = ''.join([ch for ch in decryptData(s).strip() if ord(ch) > 0])
	    d_passwords['sfscript@molten-magma.com'] = pp
	except:
	    _isUsingAlternateUsername = True
	    _username = sf_username
	    _password = sf_password
    
	print '_isBeingDebugged=%s' % _isBeingDebugged
	print 'sys.version=[%s]' % sys.version
	v = _utils.getFloatVersionNumber()
	if (v >= 2.51):
	    #print 'sys.path=[%s]' % '\n'.join(sys.path)
	    if (not _isBeingDebugged):
		from vyperlogix.handlers.ExceptionHandler import *
		excp = ExceptionHandler()
		excp.callback = exception_callback
    
	    if (not _isNoPsyco):
		from vyperlogix.misc._psyco import *
		importPsycoIfPossible(func=main,isVerbose=True)
	    else:
		_msg = 'Not loading Psyco due to --nopsyco being used.'
		print >>sys.stdout, _msg
		print >>sys.stderr, _msg
    
	    if (not _isUsingAlternateUsername):
		_username = 'rhorn@molten-magma.com'
	    
	    #ep = encryptData('...')
	    #print 'ep=[%s]' % asReadableData(ep)
	    
	    print '(%s) :: sys.argv=%s' % (_utils.timeStampLocalTime(),sys.argv)
	    
	    print '(%s) :: _cwd=%s' % (_utils.timeStampLocalTime(),_cwd)
	    
	    if (len(_cwd) > 0) and (os.path.exists(_cwd)):
		name = _utils.getProgramName()
		_log_path = _utils.safely_mkdir_logs(fpath=_cwd)
		_log_path = _utils.safely_mkdir(fpath=_log_path,dirname=_utils.timeStampLocalTimeForFileName(delimiters=('_')))
		_data_path = _utils.safely_mkdir(fpath=_log_path,dirname='dbx')
		_log_path = _utils.safely_mkdir(fpath=_log_path,dirname='logs')

		logFileName = os.sep.join([_log_path,'%s.log' % (name)])

		print '(%s) :: logFileName=%s' % (_utils.timeStampLocalTime(),logFileName)
		
		_stdOut = open(os.sep.join([_log_path,'stdout.txt']),'w')
		_stdErr = open(os.sep.join([_log_path,'stderr.txt']),'w')
		_stdLogging = open(logFileName,'w')
		
		sys.stdout = Log(_stdOut)
		sys.stderr = Log(_stdErr)
		_logLogging = CustomLog(_stdLogging)
	
		standardLogging.standardLogging(logFileName,_level=_logging,console_level=_console_logging,isVerbose=_isVerboseLogging)
		
		_logLogging.logging = logging # echos the log back to the standard logging...
		logging = _logLogging # replace the default logging with our own custom logging...
		
		logging.warning('stdout to "%s".' % (_stdOut.name))
		logging.warning('stderr to "%s".' % (_stdErr.name))
	
		_msg = 'Logging to "%s" using level of "%s".' % (logFileName,standardLogging.explainLogging(_logging))
		print >>sys.stdout, _msg
		logging.warning(_msg)
		
		log_file_retention_policy = lambda args: _utils.getFromTimeStampForFileName(args[0].split(os.sep)[-1]) < (datetime.datetime.now() - datetime.timedelta(days=30))
		
		_latestFolders = latestFolder.allFolders(top=os.path.dirname(_log_path),logs=_log_path.split(os.sep)[-1],dbx=_data_path.split(os.sep)[-1],callback=log_file_retention_policy)
		if (len(_latestFolders) > 0):
		    logging.info('BEGIN: Log Retention Policy')
		    for f in _latestFolders:
			try:
			    _utils.removeAllFilesUnder(f[0])
			    if (os.path.exists(f[0])):
				os.remove(f[0])
			    logging.info('Removed "%s" due to age of these logs.' % (f[0]))
			except:
			    exc_info = sys.exc_info()
			    info_string = CaseWatcher.asMessage('\n'.join(traceback.format_exception(*exc_info)))
			    print >>sys.stderr, info_string
			    logging.error(info_string)
		    logging.info('END!   Log Retention Policy')
	
		if (_isInitialize):
		    print '_isInitialize is %s' % (_isInitialize)
		    
		if (_isDebug):
		    print '--debug is %s' % (_isDebug)
		    
		if (_isDebug_limits > -1):
		    print '--debug=%s' % (_isDebug_limits)
		
		if (_isSerialize):
		    print '--serialize is %s' % (_isSerialize)
		    
		print '--usetrigger is %s' % (_isUseTrigger)
		
		if (_limitCaseWatchers):
		    print '--limit_cw=%s' % (_limitCaseWatchers)
		
		if (_casewatcher):
		    print '_casewatcher=%s' % (_casewatcher)
		    
		print '_isVerboseLogging is %s' % (_isVerboseLogging)
		
		print 'procify_cw=%s, _procify_cw=%s' % (procify_cw,_procify_cw)
		
		print 'sf_token is "%s".' % (sf_token)

		if (not _isUsingAlternateUsername):
		    if (d_passwords.has_key(_username)):
			_password = d_passwords[_username]
		    else:
			_password = ''
		if (len(_username) > 0) and (len(_password) > 0):
		    if (not _isStaging):
			logging.warning('username is "%s", password is known and valid.' % (_username))
		    try:
			from pyax_code.context import getSalesForceContext
			
			_ctx = getSalesForceContext()
			if (_isStaging):
			    _srvs = _ctx.get__login_servers()
			    print '_srvs=%s' % str(_srvs)
			    if (_srvs.has_key('production')) and (_srvs.has_key('sandbox')):
				_ctx.login_endpoint = _ctx.login_endpoint.replace(_srvs['production'],_srvs['sandbox'])
			    print '_ctx.login_endpoint=%s' % str(_ctx.login_endpoint)
			sfdc = Connection.connect(sf_username if (len(sf_username) > 0) else _username, sf_password if (len(sf_password) > 0) else _password, token=sf_token if (len(sf_token) > 0) else None, context=_ctx)
			print 'sfdc=%s' % str(sfdc)
			print 'sfdc.endpoint=%s' % str(sfdc.endpoint)
			
			if (not _isDebug):
			    clearDataPathOfFiles(_data_path)
			
			print '(1) _smtpserver is %s' % (_smtpserver)
			if (os.path.exists(_smtpserver)):
			    _smtpserver_p = _utils.spawnProcessWithDetails(_smtpserver,fOut=sys.stdout,pWait=False)
			    _smtpserver = '127.0.0.1:25'
			    print 'SMTP PID is %s, listening on %s' % (_smtpserver_p.pid,_smtpserver)
	
			print '(2) _smtpserver is %s' % (_smtpserver)
			
			#dx = sfdc.describeSObject('Case')
			#products_list = dx.metadata['fields']['Product__c']['picklistValues']
			#print products_list.keys()
			#print '\n'.join(_utils.sort(products_list.keys()))
			
			if (_isBeingDebugged): #  or (not _utils.isUsingWindows)
			    runWithAnalysis.runWithAnalysis(main,[sfdc])
			else:
			    import cProfile
			    cProfile.run('runWithAnalysis.runWithAnalysis(main,[sfdc])', os.sep.join([_log_path,'profiler.txt']))
		    except AttributeError:
			exc_info = sys.exc_info()
			info_string = CaseWatcher.asMessage('\n'.join(traceback.format_exception(*exc_info)))
			print >>sys.stderr, info_string
			logging.warning(info_string)
		    except ApiFault:
			exc_info = sys.exc_info()
			info_string = CaseWatcher.asMessage('\n'.join(traceback.format_exception(*exc_info)))
			print >>sys.stderr, info_string
			logging.warning(info_string)
		else:
		    info_string = CaseWatcher.asMessage('Cannot figure-out what username (%s) and password (%s) to use so cannot continue. Sorry !' % (_username,_password))
		    print >>sys.stderr, info_string
		    logging.error(info_string)
	    else:
		info_string = CaseWatcher.asMessage('ERROR: Missing the cwd parm which is the first parm on the command line.')
		print >>sys.stderr, info_string
    
	else:
	    info_string = CaseWatcher.asMessage('You are using the wrong version of Python, you should be using 2.51 or later but you seem to be using "%s".' % sys.version)
	    print >>sys.stderr, info_string
	    logging.error(info_string)
	    
    _msg = 'Done !'
    logging.warning(_msg)
    print >> sys.stdout, _msg
    _logLogging.close()
    sys.stdout.close()
    sys.stderr.close()
    sys.exit(1)

