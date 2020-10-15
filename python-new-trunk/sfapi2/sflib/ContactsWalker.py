""" 
This is the Contacts Walker Process

caveats:

* email address is assumed to be case-insensitive in SalesForce
* some email addresses are duplicates within a single CSV file.

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

_suppress_missing_warnings = False

csv_fname = ""

_isVerbose = False
_csvPath = ''
_logging = logging.WARNING

is_platform_not_windows = lambda _sys:(_sys.platform != 'win32')
bool_is_platform_not_windows = is_platform_not_windows(sys)

_isBeingDebugged = (os.environ.has_key('WINGDB_ACTIVE')) # When debugger is being used we do not use threads...

_proc_queue = Queue.Queue(750) if (_isBeingDebugged) else threadpool.ThreadQueue(750)

_isVerbose = False

_demo_filename = 'Z:\\@myMagma\\!Contacts Walker Analysis\\!Research DAC leads combined\\ContactsWalker Analysis\\not_in_salesforce.csv'

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

def _getContactsByEmail(args):
    try:
	fields = []
	if (len(args) == 2):
	    sfdc, email = args
	elif (len(args) == 3):
	    sfdc, email, fields = args
	if (len(fields) > 0):
	    soql = "Select %s from Contact c where c.Email = '%s'" % (', '.join(['c.%s' % (f) for f in fields]),email)
	else:
	    soql = "Select c.Email, c.Id from Contact c where c.Email = '%s'" % (email)
	contacts = __getObjectsFromSOQL(sfdc,soql)
	if contacts in BAD_INFO_LIST:
	    if (not _suppress_missing_warnings):
		logging.warning("(%s) :: Could not find any Contact Object(s) for email of %s." % (misc.funcName(),email))
	return contacts
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (misc.funcName(),info_string))

    return None
    
def getContactsByEmail(args): 
    return _getContactsByEmail(args)
   
def _getLeadsByEmail(args):
    try:
	sfdc, email = args
	soql = "Select l.Email, l.Id, l.ConvertedDate from Lead l where l.Email = '%s'" % (email)
	leads = __getObjectsFromSOQL(sfdc,soql)
	if leads in BAD_INFO_LIST:
	    if (not _suppress_missing_warnings):
		logging.warning("(%s) :: Could not find any Lead Object(s) for email of %s." % (misc.funcName(),email))
	return leads
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (misc.funcName(),info_string))

    return None
    
def getLeadsByEmail(args): 
    return _getLeadsByEmail(args)
   
def _getConvertedContactByLeadId(args):
    try:
	sfdc, id = args
	soql = "Select l.Email, l.Id, l.ConvertedDate, l.ConvertedContactId from Lead l where l.Id = '%s'" % (id)
	leads = __getObjectsFromSOQL(sfdc,soql)
	if leads in BAD_INFO_LIST:
	    if (not _suppress_missing_warnings):
		logging.warning("(%s) :: Could not find any Lead Object(s) for id of %s." % (misc.funcName(),id))
	return leads
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (misc.funcName(),info_string))

    return None
    
def getConvertedContactByLeadId(args): 
    return _getConvertedContactByLeadId(args)
   
def _getAllUsers(args):
    try:
	sfdc = args
	soql = "Select u.Email, u.Name, u.Id, u.Unix_Username__c from User u ORDER BY u.Email"
	users = __getObjectsFromSOQL(sfdc,soql,useRealObjects=True)
	if users in BAD_INFO_LIST:
	    if (not _suppress_missing_warnings):
		logging.warning("(%s) :: Could not find any User Object(s)." % (misc.funcName()))
	return users
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (misc.funcName(),info_string))

    return None
    
def getAllUsers(args): 
    return _getAllUsers(args)

def _getLeadRecordTypes(args):
    try:
	sfdc = args
	soql = "Select r.Id, r.Name, r.SobjectType from RecordType r WHERE r.SobjectType = 'Lead' and r.Name = 'Sales Lead' ORDER BY r.Name"
	_types = __getObjectsFromSOQL(sfdc,soql,useRealObjects=True)
	if _types in BAD_INFO_LIST:
	    if (not _suppress_missing_warnings):
		logging.warning("(%s) :: Could not find any RecordType Object(s)." % (misc.funcName()))
	return _types
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (misc.funcName(),info_string))

    return None
    
def getLeadRecordTypes(args): 
    return _getLeadRecordTypes(args)

def _getLeadSourceTypes(args):
    try:
	sfdc = args
	soql = "Select l.Id, l.Name from LeadSourceType__c l"
	_types = __getObjectsFromSOQL(sfdc,soql,useRealObjects=True)
	if _types in BAD_INFO_LIST:
	    if (not _suppress_missing_warnings):
		logging.warning("(%s) :: Could not find any LeadSourceType__c Object(s)." % (misc.funcName()))
	return _types
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (misc.funcName(),info_string))

    return None
    
def getLeadSourceTypes(args): 
    return _getLeadSourceTypes(args)

def _getLeadSourceDataByLeadId(args):
    try:
	sfdc, id = args
	soql = "Select l.Description__c, l.Id, l.Lead__c, l.Score__c, l.Source__c from LeadSourceData__c l WHERE Lead__c = '%s'" % (id)
	data = __getObjectsFromSOQL(sfdc,soql)
	if data in BAD_INFO_LIST:
	    if (not _suppress_missing_warnings):
		logging.warning("(%s) :: Could not find any LeadSourceData__c Object(s) for Lead Id of %s." % (misc.funcName(),id))
	return data
    except:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.warning('(%s) :: %s' % (misc.funcName(),info_string))

    return None
    
def getLeadSourceDataByLeadId(args): 
    return _getLeadSourceDataByLeadId(args)
   
if (not _isBeingDebugged):
    @threadpool.threadify(_proc_queue)
    def __getContactsByEmail(args):
	getContactsByEmail(args)
    
    @threadpool.threadify(_proc_queue)
    def __getLeadsByEmail(args):
	getLeadsByEmail(args)
    
    def getContactsAndLeadsByEmail(args):
	__getContactsByEmail(args)
	__getLeadsByEmail(args)

def save_data_set_into(d,dname):
    _fname = oodb.dbx_name('%s.dbx' % (dname),_data_path)
    if (not os.path.exists(_fname)):
	logging.info('(%s) :: _fname=%s' % (misc.funcName(),_fname))
	dbx = oodb.PickledFastCompressedHash2(_fname)
	try:
	    for k,v in d.iteritems():
		dbx[k] = v
	except Exception, details:
	    logging.error('(%s) :: ERROR: "%s".' % (misc.funcName(),str(details)))
	finally:
	    dbx.close()
	    
    return oodb.PickledFastCompressedHash2(_fname)
	    
def read_data_set_from(dname):
    _fname = oodb.dbx_name('%s.dbx' % (dname),_data_path)
    return oodb.PickledFastCompressedHash2(_fname)
	    
def main(args):
    global _suppress_missing_warnings
    
    email_from_row = lambda row:row[_analysisColNum].strip().lower()
    
    ioTimeAnalysis.ioBeginTime('%s' % (__name__))
    try:
	sfdc, csv = args
	
	if (not _isRunningLocal_at_work):
	    print '\n\n'
	    print 'This program was designed to run only at Magma Design Automation for security reasons.'
	    print 'Please make sure you run this program only at Magma Design Automation or someone may get an email telling them about all this and you know what that means, right ?!? (Pink Slip... Unemployment...)'
	    print '\n\n'
	elif (_isUnix):
	    users = getAllUsers(sfdc)
	    for u in users:
		if (u['Unix_Username__c'] is None) or (len(u['Unix_Username__c']) == 0):
		    toks = u['Email'].split('@')
		    u['Unix_Username__c'] = toks[0]
		    update.updateSalesForceObject(u)
		    logging.info('%s :: Updated Record # %s, %s --> %s' % (misc.funcName(),u['Id'],u['Email'],u['Unix_Username__c']))
	    logging.info('%s :: DONE' % (misc.funcName()))
	elif (_isDemo):
	    import random
	    from vyperlogix.mail.validateEmail import validateEmail
	    from pyax.sobject.classfactory import ClassFactory
	    
	    sfdc.context.use_default_assignment_rule = True
	    
	    _firstNames = list(set(['_'.join(n.split()) for n in csv.column('firstName') if (len(n) > 1)]))
	    _lastnames = list(set(['_'.join(n.split()) for n in csv.column('lastName') if (len(n) > 1)]))
	    _keyNames = csv.column(_colname)
	    _domains = list(set([k.split('@')[-1].upper() for k in _keyNames if (validateEmail(k))]))

	    _recordTypeIds = []
	    r = getLeadRecordTypes(sfdc)
	    if (r):
		_recordTypeIds = [t['Id'] for t in r if (t.has_key('Id'))]
	    _recordTypeId = random.choice(_recordTypeIds)
	    
	    _leadTypeIds = []
	    r = getLeadSourceTypes(sfdc)
	    if (r):
		_leadTypeIds = [t['Id'] for t in r if (t.has_key('Id'))]
	    
	    d_Lead = sfdc.describeSObject('Lead')
	    flds_Lead = d_Lead.metadata['fields']
	    d_LeadSources = lists.HashedLists2()
	    if (flds_Lead.has_key('LeadSource')):
		d_LeadSources = lists.HashedLists2(flds_Lead['LeadSource']['picklistValues'])
		l_retire = []
		for k,v in d_LeadSources.iteritems():
		    if (v['active'] == False):
			l_retire.append(k)
		for k in l_retire:
		    del d_LeadSources[k]
	    d_Regions = lists.HashedLists2()
	    if (flds_Lead.has_key('Region__c')):
		d_Regions = lists.HashedLists2(flds_Lead['Region__c']['picklistValues'])
		    
	    d_domain_company = csv.associationsBy(_colname,callback=lambda k:k.split('@')[-1].lower())
	    i_company_colNum = csv.column_number_for_name('company')
	    i_country_colNum = csv.column_number_for_name('country')
	    i_city_colNum = csv.column_number_for_name('city')
	    i_address_colNum = csv.column_number_for_name('address1')
	    i_state_colNum = csv.column_number_for_name('state')
	    i_zipPostalCode_colNum = csv.column_number_for_name('zipPostalCode')
	    
	    d_LeadSourceData__c = sfdc.describeSObject('LeadSourceData__c')
	    flds_LeadSourceData__c = d_LeadSourceData__c.metadata['fields']
	    
	    d_LeadSourceData_Descriptions = lists.HashedLists2()
	    if (flds_LeadSourceData__c.has_key('Description__c')):
		d_LeadSourceData_Descriptions = lists.HashedLists2(flds_LeadSourceData__c['Description__c']['picklistValues'])

	    d_LeadSourceData_Types = lists.HashedLists2()
	    if (flds_LeadSourceData__c.has_key('Type__c')):
		d_LeadSourceData_Types = lists.HashedLists2(flds_LeadSourceData__c['Type__c']['picklistValues'])
		l_retire = []
		for k,v in d_LeadSourceData_Types.iteritems():
		    if (v['label'].find(' did not ') > -1) or (v['value'].find(' did not ') > -1):
			l_retire.append(k)
		for k in l_retire:
		    del d_LeadSourceData_Types[k]
	    
	    _suppress_missing_warnings = True

	    print >>sys.stdout, 'Welcome to the Demo.'
	    _fname = oodb.dbx_name('demo.dbx',_data_path)
	    print '(%s) :: _fname=%s' % (misc.funcName(),_fname)
	    dbx = oodb.PickledFastCompressedHash2(_fname)
	    try:
		_max_lead_num = 4
		d_NewLeads = lists.HashedLists2()
		for i_lead_num in xrange(_max_lead_num):
		    while (1):
			_leadSource = d_LeadSources[random.choice(d_LeadSources.keys())]['value']
			_leadSource_description = d_LeadSourceData_Descriptions[random.choice(d_LeadSourceData_Descriptions.keys())]['value']
			_leadSource_type = d_LeadSourceData_Types[random.choice(d_LeadSourceData_Types.keys())]['value']
			_firstName = random.choice(_firstNames).capitalize()
			_lastName = random.choice(_lastnames).capitalize()
			_domainName = random.choice(_domains).lower()
			_companyName = d_domain_company[_domainName][0][i_company_colNum]
			_countryName = d_domain_company[_domainName][0][i_country_colNum]
			_cityName = d_domain_company[_domainName][0][i_city_colNum]
			_addressName = d_domain_company[_domainName][0][i_address_colNum]
			_stateName = d_domain_company[_domainName][0][i_state_colNum]
			_zipPostalCodeName = d_domain_company[_domainName][0][i_zipPostalCode_colNum]
			_leadRegion = d_Regions[random.choice(d_Regions.keys())]['value']
			_emailAddr = '%s.%s@%s' % (_firstName.lower(),_lastName.lower(),_domainName)
			_leadTypeId = random.choice(_leadTypeIds)
			print >>sys.stdout, 'Adding Lead #%d of 4 with some initial scoring.' % (i_lead_num+1)
			print >>sys.stdout, '\t%s %s %s' % (_firstName,_lastName,_emailAddr)
			c = getLeadsByEmail([sfdc,_emailAddr])
			if (c):
			    print 'Picking another Lead to Create...'
			    continue
			else:
			    # Lead does not exist so add it and then score it.
			    aLead = ClassFactory(sfdc, 'Lead')
			    d_lead = {'FirstName':_firstName,'LastName':_lastName,'Email':_emailAddr,'RecordTypeId':_recordTypeId,'LeadSource':_leadSource,'Company':_companyName,'Country':_countryName,'City':_cityName,'Physical_Address__c':_addressName,'State':_stateName,'PostalCode':_zipPostalCodeName,'Region__c':_leadRegion}
			    saveResults = sfdc.create(aLead, [d_lead])
			    if (saveResults[0].has_key('errors')):
				print 'Failed to create Lead from %s!' % (d_lead)
			    else:
				_id = saveResults[0]['id']
				print '(%s) :: Created New Lead from %s!' % (_id,d_lead)
				aLeadSourceData = ClassFactory(sfdc, 'LeadSourceData__c')
				d_data = {'Notes__c':_leadSource,'Date__c':_utils.getFromDateTimeStr(_utils.timeStampSimple(),format=_utils.formatDate_MMDDYYYY_slashes()),'Lead__c':_id,'Source__c':_leadTypeId,'Description__c':_leadSource_description,'Type__c':_leadSource_type}
				saveResults2 = sfdc.create(aLeadSourceData, [d_data])
				if (saveResults2[0].has_key('errors')):
				    print 'Failed to create LeadSourceData__c from %s!' % (d_data)
				dbx[_id] = d_data
				d_NewLeads[_id] = d_data
			    break
		    print '\n'
		print '\n'
		print 'BEGIN:'
		for k,v in dbx.iteritems():
		    if (not d_NewLeads.has_key(k)):
			_lead_id = v['Lead__c']
			c_leads = getConvertedContactByLeadId([sfdc,k])
			if (c_leads):
			    c_leads = c_leads if (not isinstance(c_leads,list)) else c_leads[0]
			    _lead_id = c_leads['ConvertedContactId']
			    print 'Lead %s has been converted to Contact %s!' % (k,_lead_id)
			_leadSource = d_LeadSources[random.choice(d_LeadSources.keys())]['value']
			_leadSource_description = d_LeadSourceData_Descriptions[random.choice(d_LeadSourceData_Descriptions.keys())]['value']
			_leadSource_type = d_LeadSourceData_Types[random.choice(d_LeadSourceData_Types.keys())]['value']
			aLeadSourceData = ClassFactory(sfdc, 'LeadSourceData__c')
			d_data = {'Notes__c':_leadSource,'Date__c':_utils.getFromDateTimeStr(_utils.timeStampSimple(),format=_utils.formatDate_MMDDYYYY_slashes()),'Lead__c':_lead_id,'Source__c':v['Source__c'],'Description__c':_leadSource_description,'Type__c':_leadSource_type}
			saveResults2 = sfdc.create(aLeadSourceData, [d_data])
			if (saveResults2[0].has_key('errors')):
			    print 'Failed to create LeadSourceData__c for %s from %s!' % (k,d_data)
		    scores = getLeadSourceDataByLeadId([sfdc,k])
		    print '\t%s :: %s' % (k,scores)
		print 'END !'
	    finally:
		dbx.close()

	    _suppress_missing_warnings = False
	elif (_isRunningLocal_at_work):
	    files = []
	    
	    fname_d_None = oodb.dbx_name('d_None.dbx',_data_path)
	    fname_d_Contacts = oodb.dbx_name('d_Contacts.dbx',_data_path)
	    fname_d_Both = oodb.dbx_name('d_Both.dbx',_data_path)
	    fname_d_Leads = oodb.dbx_name('d_Leads.dbx',_data_path)
	    
	    is_bypass_processing = False
	    
	    logging.warning('(%s) :: _isCommit is "%s".' % (misc.funcName(),_isCommit))
	    if (_isCommit):
		d_None = read_data_set_from(fname_d_None)
		d_Contacts = read_data_set_from(fname_d_Contacts)
		d_Both = read_data_set_from(fname_d_Both)
		d_Leads = read_data_set_from(fname_d_Leads)
		is_bypass_processing = (len(d_None) > 0) and (len(d_Contacts) > 0) and (len(d_Both) > 0) and (len(d_Leads) > 0)
	    
	    if (not is_bypass_processing):
		fFound_Contacts = open(os.sep.join([_log_path,'contacts.csv']),'w')
		fFound_Leads = open(os.sep.join([_log_path,'leads.csv']),'w')
		fFound_Both = open(os.sep.join([_log_path,'contacts_and_leads.csv']),'w')
		fFound_None = open(os.sep.join([_log_path,'not_in_salesforce.csv']),'w')
		fFound_Report = open(os.sep.join([_log_path,'!report.csv']),'w')
		fFound_Dupes = open(os.sep.join([_log_path,'!dupes.csv']),'w')
		fFound_Blanks = open(os.sep.join([_log_path,'!blanks.csv']),'w')
		fFound_DupeLeads = open(os.sep.join([_log_path,'!dupe-leads.csv']),'w')
		fFound_Problems = open(os.sep.join([_log_path,'!problems.csv']),'w')
		
		lFound_Contacts = []
		lFound_Leads = []
		lFound_Both = []
		lFound_None = []
		lFound_Report = []
		lFound_Dupes = []
		lFound_Blanks = []
		lFound_DupeLeads = []
	
		lFound_Dupes_instances = []
	
		new_csv_fname = os.sep.join([_log_path,'new_%s' % (os.path.basename(csv.filename))])
		new_csv = open(new_csv_fname,'w')
		
		print >>new_csv, ','.join(csv.header)
	
		files.append(fFound_Contacts)
		files.append(fFound_Leads)
		files.append(fFound_Both)
		files.append(fFound_None)
		files.append(fFound_Report)
		files.append(fFound_Dupes)
		files.append(fFound_Blanks)
		files.append(fFound_DupeLeads)
		files.append(new_csv)
		files.append(fFound_Problems)
	
		d_Contacts = lists.HashedLists2()
		d_Leads = lists.HashedLists2()
		d_Both = lists.HashedLists2()
		d_None = lists.HashedLists2()
		
		if (len(csv.rows) > 0):
		    de_duper = lists.HashedLists()
		    for row in csv.rows:
			email = email_from_row(row)
			if (len(email) > 0):
			    de_duper[email] = row
			else:
			    lFound_Blanks.append(asCSV(row))
		    for k,v in de_duper.iteritems():
			if (len(v) > 1):
			    lFound_Dupes.append('%d,%s' % (len(lFound_Dupes)+1,k))
		    print >>fFound_Report, '%s,%s,%s,%s,%s,%s,%s,%s' % ('','Xref','Contact','Lead','Both','Neither','Dupe','Leads')
		    # preload all SOQL here using threads... this did not make things run faster but it was fun to code.
		    if (0):
			for row in csv.rows:
			    email = email_from_row(row)
			    if (len(email) > 0):
				email = email_from_row(row)
				getContactsAndLeadsByEmail([sfdc,email])
			print >>sys.stdout, 'Waiting for all background threads to complete.'
			_proc_queue.join()
			print >>sys.stdout, 'All background threads are complete !'
		    for row in csv.rows:
			_is_in_contacts = False
			_is_in_leads = False
			_num_duplicated_leads = ''
	
			email = email_from_row(row)
			if (len(email) > 0):
			    _count = 0
			    _is_in_contacts = False
			    c = getContactsByEmail([sfdc,email])
			    if (c):
				d_Contacts[email] = row
				_count += 1
				_is_in_contacts = True
			    _is_in_leads = False
			    c = getLeadsByEmail([sfdc,email])
			    if (c):
				try:
				    if (not any([(rec['ConvertedDate'] and len(rec['ConvertedDate']) > 0) and (_utils.isStrDate(rec['ConvertedDate'])) for rec in c])):
					d_Leads[email] = row
					_count += 1
					_is_in_leads = True
				    else:
					print >>sys.stderr, '%s has been converted on %s' % (email,','.join([rec['ConvertedDate'] for rec in c if (rec['ConvertedDate'] and (len(rec['ConvertedDate']) > 0) and (_utils.isStrDate(rec['ConvertedDate'])))]))
				except KeyError:
				    pass
				if (len(c) > 1):
				    _num_duplicated_leads = '%d' % (len(c))
				    lFound_DupeLeads.append(asCSV(row))
			    if (_count == 2):
				d_Both[email] = row
			    elif (_count == 0):
				d_None[email] = row
			    if (len(de_duper[email]) > 1):
				lFound_Dupes_instances.append(row)
			    lFound_Report.append('%s,,%s,%s,%s,%s,%s,%s' % (email,'FOUND (%s)' % (len(d_Contacts)) if (_is_in_contacts) else '','FOUND (%d)' % (len(d_Leads)) if (_is_in_leads) else '','FOUND (%d)' % (len(d_Both)) if (_is_in_contacts and _is_in_leads) else '','FOUND (%d)' % (len(d_None)) if (not _is_in_contacts and not _is_in_leads) else '','DUPE x%d (%d)' % (len(de_duper[email]),len(lFound_Dupes_instances)) if (len(de_duper[email]) > 1) else '',_num_duplicated_leads))
	    
		    for k,v in d_Contacts.iteritems():
			lFound_Contacts.append(asCSV(v))
		    for k,v in d_Leads.iteritems():
			lFound_Leads.append(asCSV(v))
		    for k,v in d_Both.iteritems():
			lFound_Both.append(asCSV(v))
		    for k,v in d_None.iteritems():
			lFound_None.append(asCSV(v))
		else:
		    logging.warning('(%s) :: NOTHING TO DO !' % (misc.funcName()))
		    
		_num_lFound_Contacts = len(lFound_Contacts)
		_num_lFound_Leads = len(lFound_Leads)
		_num_lFound_Both = len(lFound_Both)
		_num_lFound_None = len(lFound_None)
		_num_lFound_Dupes = len(lFound_Dupes)
		_num_lFound_Blanks = len(lFound_Blanks)
		_num_lFound_DupeLeads = len(lFound_DupeLeads)
	
		if (_isHeaders):
		    lFound_Contacts.insert(0,asCSV(csv.header))
		    lFound_Leads.insert(0,asCSV(csv.header))
		    lFound_Both.insert(0,asCSV(csv.header))
		    lFound_None.insert(0,asCSV(csv.header))
		    lFound_Dupes.insert(0,asCSV(['#',_colname]))
		    lFound_Blanks.insert(0,asCSV(csv.header))
		    lFound_DupeLeads.insert(0,asCSV(csv.header))
		    print >>fFound_Problems, '%s\n' % (asCSV(csv.header))
		    
		print >>fFound_Problems, '\n'.join([asCSV(l) for l in csv.problem_rows])
		print >>fFound_Problems, '%s END OF FILE %s' % ('='*30,'='*30)
			
		lFound_Contacts.append('%s END OF FILE %s' % ('='*30,'='*30))
		lFound_Both.append('%s END OF FILE %s' % ('='*30,'='*30))
		lFound_Leads.append('%s END OF FILE %s' % ('='*30,'='*30))
		lFound_None.append('%s END OF FILE %s' % ('='*30,'='*30))
		lFound_Dupes.append('%s END OF FILE %s' % ('='*30,'='*30))
		lFound_Blanks.append('%s END OF FILE %s' % ('='*30,'='*30))
		lFound_DupeLeads.append('%s END OF FILE %s' % ('='*30,'='*30))
		
		print >>fFound_Contacts, '\n'.join(lFound_Contacts)
		print >>fFound_Both, '\n'.join(lFound_Both)
		print >>fFound_Leads, '\n'.join(lFound_Leads)
		print >>fFound_None, '\n'.join(lFound_None)
		print >>fFound_Dupes, '\n'.join(lFound_Dupes)
		print >>fFound_Blanks, '\n'.join(lFound_Blanks)
		print >>fFound_DupeLeads, '\n'.join(lFound_DupeLeads)
	
		lFound_Report.insert(0,'There are %d records in "%s".,Column "C"' % (_num_lFound_Contacts,os.path.basename(fFound_Contacts.name)))
		lFound_Report.insert(1,'There are %d records in "%s".,Column "D"' % (_num_lFound_Leads,os.path.basename(fFound_Leads.name)))
		lFound_Report.insert(2,'There are %d records in "%s".,Column "E"' % (_num_lFound_Both,os.path.basename(fFound_Both.name)))
		lFound_Report.insert(3,'There are %d records in "%s".,Column "F"' % (_num_lFound_None,os.path.basename(fFound_None.name)))
		lFound_Report.insert(4,'There are %d records in "%s".,Column "G"' % (_num_lFound_Dupes,os.path.basename(fFound_Dupes.name)))
		lFound_Report.insert(5,'There are %d records in "%s".' % (_num_lFound_Blanks,os.path.basename(fFound_Blanks.name)))
		lFound_Report.insert(6,'')
		lFound_Report.insert(7,'There are %d records in "%s".,Column "H"' % (_num_lFound_DupeLeads,os.path.basename(fFound_DupeLeads.name)))
		lFound_Report.insert(8,'')
		lFound_Report.insert(9,'There are %d problem records with MISSING data in "%s".' % (len(csv.problem_rows),os.path.basename(fFound_Problems.name)))
		lFound_Report.insert(10,'Problem records are marked with the MISSING keyword usually in the last several columns.')
		lFound_Report.insert(11,'')
		lFound_Report.insert(12,'There are %d records in "%s".' % (len(csv.rows),os.path.basename(csv.filename)))
		_num_balance = _num_lFound_Contacts+_num_lFound_Leads-_num_lFound_Both+_num_lFound_None+_num_lFound_Dupes+_num_lFound_Blanks
		lFound_Report.insert(13,'"There are %d records processed into 6 categories, a deviation of %d records."' % (_num_balance,len(csv.rows)-_num_balance))
		lFound_Report.insert(14,'')
		lFound_Report.insert(15,'Key:')
		lFound_Report.insert(16,'The number that appears between the () is the instance count for that category.')
		lFound_Report.insert(17,'The number that appears after the "x" is the number of instances for that item.')
		lFound_Report.insert(18,'')
		lFound_Report.insert(19,_colname)
	
		lFound_Report.append('')
		lFound_Report.append('The instance count for Column "F" counts all instances of duped %s records.' % (_colname))
		lFound_Report.append('The records for Column "G" do not show-up in the web based GUI however they do appear in the database.')
		lFound_Report.append('')
		lFound_Report.append('Caveats:')
		lFound_Report.append('')
		lFound_Report.append('Email addresses are assumed to be case insensitive in SalesForce however if this proves to be incorrect then the results obtained by the program that produced this report will be in error.')
		lFound_Report.append('No attempt was made to resolve minor spelling errors that may have been present in some of the email addresses supplied to this program as these email addresses may have come from a source other than SalesForce and their validity cannot be determined by the program that produced this report.')
		lFound_Report.append('%s END OF FILE %s' % ('='*30,'='*30))
	
		print >>fFound_Report, '\n'.join(lFound_Report)
		
		for f in files:
		    f.flush()
		    f.close()
		
	    if (_isCommit):
		# contacts.csv ............ Add the scoring data (d_Contacts.iteritems())
		# contacts_and_leads.csv .. Add the scoring data (d_Both.iteritems())
		# leads.csv             ... Add the scoring data (d_Leads.iteritems())
		# not_in_salesforce.csv ... Add the Leads        (d_None.iteritems())
		
		# BEGIN: This may look a bit odd but it works... If files already exist no action is taken other than to read the data...
		d_None = save_data_set_into(d_None,fname_d_None)
		d_Contacts = save_data_set_into(d_Contacts,fname_d_Contacts)
		d_Both = save_data_set_into(d_Both,fname_d_Both)
		d_Leads = save_data_set_into(d_Leads,fname_d_Leads)
		# END! This may look a bit odd but it works... If files already exist no action is taken other than to read the data...

		try:
		    d_None.close()
		except:
		    pass
		try:
		    d_Contacts.close()
		except:
		    pass
		try:
		    d_Both.close()
		except:
		    pass
		try:
		    d_Leads.close()
		except:
		    pass
		
	    if (os.path.exists(new_csv_fname)):
		os.remove(new_csv_fname)
		
	    assert len(csv.rows) == _num_balance, 'ERROR Will Robinson, ERROR !  I mean, DANGER Will Robinson, DANGER !   What ?!?  Never watched the T.V. Show "Lost in Space" ?!?  Well go rent it already !'
	    
	    pass
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
	    '--csv=?':'name the path to the csv file (must be a simple csv file).',
	    '--xls=?':'name the path to the xls file.',
	    '--headers':'default is False however if this option is used the CSV headers are placed at the top of all output files.',
	    '--colname=?':'name the column in the source file to use, such as "email".',
	    '--folder=?':'names the folder in which the logs and data will reside.',
	    '--unix=?':'run the unix email name fix in SalesForce - this option does not use the other options.',
	    '--username=?':'SalesForce username as in --username=sfisher@molten-magma.com.stag.',
	    '--password=?':'SalesForce password as in --password=put-your-password-here.',
	    '--logging=?':'[logging.INFO,logging.WARNING,logging.ERROR,logging.DEBUG]',
	    '--staging':'use the staging server rather than production otherwise use production.',
	    '--customlog':'redirect logging to stdout to facilitate running this from a GUI.',
	    '--demo':'use demo mode when the demo must always work which means existing leads are simply created as-needed in a more of less random fashion (Demo may not work with all input files...).',
	    '--commit':'commit to either --staging or production if --staging is not specified. New Leads are added to SalesForce with a default score, existing Leads and Contacts get an additional score.',
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

	_isUnix = False
	try:
	    if _argsObj.booleans.has_key('isUnix'):
		_isUnix = _argsObj.booleans['isUnix']
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    print >>sys.stderr, '(%s) :: %s' % (misc.funcName(),info_string)
	    _isUnix = False

	_isHeaders = False
	try:
	    if _argsObj.booleans.has_key('isHeaders'):
		_isHeaders = _argsObj.booleans['isHeaders']
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    print >>sys.stderr, '(%s) :: %s' % (misc.funcName(),info_string)
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
	
	_isStaging = False
	try:
	    if _argsObj.booleans.has_key('isStaging'):
		_isStaging = _argsObj.booleans['isStaging']
	except:
	    pass
	
	_isDemo = False
	try:
	    if _argsObj.booleans.has_key('isDemo'):
		_isDemo = _argsObj.booleans['isDemo']
	except:
	    pass
	
	_isCommit = False
	try:
	    if _argsObj.booleans.has_key('isCommit'):
		_isCommit = _argsObj.booleans['isCommit']
	except:
	    pass
	
	_isCustomlog = False
	try:
	    if _argsObj.booleans.has_key('isCustomlog'):
		_isCustomlog = _argsObj.booleans['isCustomlog']
	except:
	    pass
	
	csv = None
	
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
				    if (not _isDemo):
					print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not appear to contain any data in the column(s) in which the tokens %s appears in row 1 although this file appears to be a valid Excel file type.' % (f,_target_toks)
			    else:
				if (not _isDemo):
				    print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not appear to contain any columns in which the tokens %s appears in row 1 although this file appears to be a valid Excel file type.' % (f,_target_toks)
			except ValueError:
			    if (not _isDemo):
				print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not appear to be a valid Excel file type.' % (f)
		else:
		    if (not _isDemo):
			print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not exist.' % (f)
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    print >>sys.stderr, '(%s) :: %s' % (misc.funcName(),info_string)
	    
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
				    if (not _isDemo):
					print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not appear to contain any data in the column(s) in which the tokens %s appears in row 1 although this file appears to be a valid Excel file type.' % (f,_target_toks)
			    else:
				if (not _isDemo):
				    print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not appear to contain any columns in which the tokens %s appears in row 1 although this file appears to be a valid Excel file type.' % (f,_target_toks)
			except ValueError:
			    if (not _isDemo):
				print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not appear to be a valid Excel file type.' % (f)
		else:
		    if (not _isDemo):
			print >>sys.stderr, 'Cannot use the --analysis argument because "%s" does not exist.' % (f)
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    print >>sys.stderr, '(%s) :: %s' % (misc.funcName(),info_string)
	    
	try:
	    _logging = eval(_argsObj.arguments['logging']) if _argsObj.arguments.has_key('logging') else False
	except:
	    _logging = logging.WARNING

	#_iv = XTEAEncryption.iv(os.path.splitext(os.path.basename(sys.argv[0]))[0])
	#if (_iv == 'Contacts'):
	    ##c_username = XTEAEncryption._encryptode('rhorn@molten-magma.com.stag',_iv)
	    #if (_isRunningLocal_at_work):
		#print '_iv=%s' % (_iv)
		#print '_isRunningLocal_at_work=%s' % (_isRunningLocal_at_work)
		#_username = XTEAEncryption._decryptode('4FD749C59E3EB7D61C8E2047B404E53889817A5C149AFF',_iv)
		#_password = XTEAEncryption._decryptode('4ED655DC9F49EC814B812E05',_iv)
	    #else:
		#_username = ''
		#_password = ''
	#else:
	    #print >>sys.stderr, 'WARNING: This program may not know how to connect to SalesForce at this time.  PLS contact the original developer for some support.'
	    #sys.exit(1)
	    
	#if (not _isRunningLocal_at_work):
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
	
		if (not _isDemo):
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
			    
			    _isError = False
			    if (_isDemo) and (_demo_filename.find(csv.filename) == -1):
				_isError = True
				logging.error('Cannot run this demo with any input file other than "%s", sorry.' % (_demo_filename))
    
			    if (not _isError):
				if (_isBeingDebugged):
				    runWithAnalysis(main,[sfdc,csv])
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
	    

