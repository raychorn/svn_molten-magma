import wx
from wx.lib.wordwrap import wordwrap

import string

import os, sys
import time
import traceback

import Queue

from vyperlogix import oodb

from vyperlogix.hash import lists

from vyperlogix.iterators import iterutils

from vyperlogix.daemon.daemon import Log

from vyperlogix import misc
from vyperlogix.misc import _utils
from vyperlogix.lists.ListWrapper import ListWrapper
from vyperlogix.misc import threadpool

from vyperlogix.misc import ObjectTypeName

from vyperlogix.sf.hostify import hostify

from vyperlogix.wx.pyax import SalesForceLoginModel

from vyperlogix.parsers.CSV import CSV2
from vyperlogix.parsers.CSV import XLS2

from vyperlogix.wx.Error_Handlers import WxStderr

from vyperlogix.wx.PopUpDialog import wx_PopUp_Dialog

from vyperlogix.wx import CustomStatusBar

from vyperlogix.wx import wx_utils

_info_Copyright = "(c). Copyright %s, Magma Design Automation" % (_utils.timeStampLocalTime(format=_utils.formatDate_YYYY()))

_info_site_address = 'www.moltenmagma.com'

_use_validation_QC = False

__copyright__ = """[**], All Rights Reserved.

THE AUTHOR MAGMA DESIGN AUTOMATION DISCLAIMS ALL WARRANTIES WITH REGARD TO
THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !

USE AT YOUR OWN RISK."""

__copyright__ = __copyright__.replace('[**]',_info_Copyright)

_developers = ["Ray C Horn", "Stan Fisher", "Michael Shahamatdoust"]
_writers = []
_artists = []
_translators = []

__ChangeLog__ = """
[*2a*]
(**) Version 1.0.0.0:
Reworking the data handling functions to work with Unicode, or so the desire goes.
[*2b*]
"""

s = [l for l in __ChangeLog__.split('\n') if (l.find('(**) ') > -1)]
if (len(s) > 0):
    __version__ = s[0].split(':')[0].split()[-1]
else:
    __version__ = 'UNKNOWN'

s_productName = 'Current Users'
assert __version__ != 'UNKNOWN', 'Oops, cannot determine the current version number for "%s".' % (s_productName)
__productName__ = '%s v%s' % (s_productName,__version__)

__ChangeLog__ = __ChangeLog__.replace('[*2a*]','%s %s %s' % ('='*5,'Begin','='*5)).replace('[*2b*]','%s %s   %s' % ('='*5,'End','='*5))

_smtp_server_address = 'mailhost.moltenmagma.com:25'

has_ContactsWalker_exe = False

_symbol_csv_filetype = '.csv'
_symbol_xls_filetype = '.xls'

_info_root_folder = 'c:\\'
wildcard_csv = "CSV File (*%s)|*%s|XLS files (*%s)|*%s" % (_symbol_csv_filetype,_symbol_csv_filetype,_symbol_xls_filetype,_symbol_xls_filetype)

l_allowed_computers = ['UNDEFINED3', 'SQL2005']

l_domain_names = ['.moltenmagma.com']
l_domains = ['magma']
l_domain_users = [r'magma\rhorn']

from vyperlogix.products import data as products_data
_data_path_prefix = products_data._data_path_prefix

dbx_name = lambda name:oodb.dbx_name(name,_data_path)

_csv_model = CSV2()

_symbol_import_leads_button_face = 'Import Leads'
_symbol_load_csv_button_face = 'Choose File'
_symbol_import_csv_button_face = 'Import File'

_symbol_d_None = 'd_None'
_symbol_d_Both = 'd_Both'
_symbol_d_Contacts = 'd_Contacts'
_symbol_d_Leads = 'd_Leads'

_symbol_LeadsImporter_Leads = 'LeadsImporter_Leads'

_dp_files_symbols = [_symbol_d_None,_symbol_d_Both,_symbol_d_Contacts,_symbol_d_Leads,_symbol_LeadsImporter_Leads]

_lp_files_symbols = ['!blanks.csv','!dupe-leads.csv','!dupes.csv','!problems.csv','!report.csv','contacts.csv','contacts_and_leads.csv','leads.csv','not_in_salesforce.csv','stderr.txt','stdout.txt']

_symbol_before = 'before'
_symbol_after = 'after'

_symbol_csv_path = 'csv_path'

_symbol_cbRecordTypes = 'cbRecordTypes'
_symbol_cbLeadTypes = 'cbLeadTypes'
_symbol_cbLeadSource = 'cbLeadSource'
_symbol_cbLeadSourceDescr = 'cbLeadSourceDescr'
_symbol_cbLeadSourceDataTypes = 'cbLeadSourceDataTypes'

_symbol_username = 'username'
_symbol_endpoint_name = ''
_symbol_endpoint_url = ''

_symbol_btnProcess1_button = 'btnProcess1'
_symbol_btnProcess2_button = 'btnProcess2'
_symbol_btnProcess3_button = 'btnProcess3'

d_button_enable_map = lists.HashedLists2({_symbol_btnProcess1_button:True,
					  _symbol_btnProcess2_button:False,
					  _symbol_btnProcess3_button:False
					  })

_data_files = lists.HashedLists2({_symbol_d_Both:'d_Both_PFCH2.dbx',_symbol_d_Contacts:'d_Contacts_PFCH2.dbx',_symbol_d_Leads:'d_Leads_PFCH2.dbx',_symbol_d_None:'d_None_PFCH2.dbx'})

_symbol_title = 'title'
_symbol_firstName = 'firstName'
_symbol_lastName = 'lastName'
_symbol_company = 'company'
_symbol_country = 'country'
_symbol_city = 'city'
_symbol_address1 = 'address1'
_symbol_address2 = 'address2'
_symbol_address3 = 'address3'
_symbol_state = 'state'
_symbol_zipPostalCode = 'zipPostalCode'
_symbol_notes = 'notes'
_symbol_product = 'product'
_symbol_phone = 'phoneOffice'
_symbol_phone_mobile = 'phoneMobile'
_symbol_email = 'eMail'

_symbol_name = 'name'

# BEGIN: The list of all possible column names...
_symbol_table = lists.HashedFuzzyLists2({_symbol_title:'title',
				    _symbol_firstName:'firstName',
				    _symbol_lastName:'lastName',
				    _symbol_company:'company',
				    _symbol_country:'country',
				    _symbol_city:'city',
				    _symbol_address1:'address1',
				    _symbol_address2:'address2',
				    _symbol_address3:'address3',
				    _symbol_state:'state',
				    _symbol_zipPostalCode:'zipPostalCode',
				    _symbol_notes:'notes',
				    _symbol_product:'product',
				    _symbol_phone:'phoneOffice',
				    _symbol_phone_mobile:'phoneMobile',
				    _symbol_email:'eMail'
				})
# END!  The list of all possible column names...

# BEGIN: The list of all transformations to be performed on each data element before the data goes into SalesForce...
_transformation_table = lists.HashedFuzzyLists2({_symbol_title:lambda title:str(title).strip(),
						 _symbol_firstName:lambda firstName:str(firstName).strip(),
						 _symbol_lastName:lambda lastName:str(lastName).strip(),
						 _symbol_company:lambda company:str(company).strip(),
						 _symbol_country:lambda country:str(country).strip(),
						 _symbol_city:lambda city:str(city).strip(),
						 _symbol_address1:lambda address1:str(address1).strip(),
						 _symbol_address2:lambda address2:str(address2).strip(),
						 _symbol_address3:lambda address3:str(address3).strip(),
						 _symbol_state:lambda state:str(state).strip(),
						 _symbol_zipPostalCode:lambda zipPostalCode:filter_floating_point_zip_code(str(zipPostalCode).strip()),
						 _symbol_notes:lambda notes:str(notes).strip(),
						 _symbol_product:lambda product:str(product).strip(),
						 _symbol_phone:lambda phoneOffice:str(phoneOffice).strip(),
						 _symbol_phone_mobile:lambda phoneMobile:str(phoneMobile).strip(),
						 _symbol_email:lambda eMail:str(eMail).strip()
				})
# END!  The list of all transformations to be performed on each data element before the data goes into SalesForce...

# BEGIN: The minimally acceptable list of columns that MUST appear in every input file...
_symbol_minimal_table = lists.HashedLists2({_symbol_title:'title',
				    _symbol_firstName:'firstName',
				    _symbol_lastName:'lastName',
				    _symbol_phone:'phoneOffice',
				    _symbol_email:'eMail'
				})
# END!  The minimally acceptable list of columns that MUST appear in every input file...

# BEGIN: The exception functions list...
_symbol_exception_functions_table = lists.HashedLists2({_symbol_name:lambda name:name.split()
				})
# END!  The exception functions list...

# BEGIN: The exception columns list...
_symbol_exception_headers_table = lists.HashedLists()
_symbol_exception_headers_table[_symbol_name] = _symbol_firstName
_symbol_exception_headers_table[_symbol_name] = _symbol_lastName
# END!  The exception columns list...

reverse_symbol_exception_functions_table = _symbol_exception_functions_table.insideOut()
reverse_symbol_exception_headers_table = _symbol_exception_functions_table.insideOut()

_isRunning = True

_thread_Q = threadpool.ThreadQueue(500)

ID_ICON_TIMER = wx.NewId()

def filter_floating_point_zip_code(zip_code):
    chars = ['.']
    tests = [str(ch).isdigit() or (ch in chars) for ch in zip_code]
    if (all(tests)):
	toks = zip_code.split('.')
	if (len(toks) == 2):
	    zip_code = toks[0]
	return zip_code
    return zip_code

def prep_data_for_salesforce(_dict,_key):
    value = ''
    if (lists.isDict(_dict)):
	value = _dict[_symbol_table[_key]]
	if (callable(_transformation_table[_key])):
	    try:
		value = _transformation_table[_key](value)
	    except Exception, details:
		info_string = _utils.formattedException(details=details)
		print >>sys.stderr, info_string
    else:
	print >>sys.stderr, '%s :: Invalid data for params.  Check to make sure you know what you are doing...' % (misc.funcName())
    return value

def is_running_at_home():
    comp_name = _utils.getComputerName()
    return (comp_name in l_allowed_computers)

def is_running_locally():
    comp_name = _utils.getComputerName()
    return (comp_name.lower() in ['rhorn-lap.ad.moltenmagma.com']) or (comp_name in l_allowed_computers)

def is_running_securely():
    from vyperlogix.win import computerSystem
    s = computerSystem.getComputerSystemSmartly()
    return s.UserName.lower().split('\\')[0] in l_domains

def is_running_securely_for_developers():
    from vyperlogix.win import computerSystem
    s = computerSystem.getComputerSystemSmartly()
    return s.UserName.lower() in l_domain_users

_sf_login_model = SalesForceLoginModel.SalesForceLoginModel(callback_developers_check=is_running_securely_for_developers)

class IconBar:
    def __init__(self,l_off=[128,0,0],l_on=[255,0,0],r_off=[0,128,0],r_on=[0,255,0]):
        self.s_line = "\xff\xff\xff"+"\0"*45
        self.s_border = "\xff\xff\xff\0\0\0"
        self.s_point = "\0"*3
        self.__num_bars = threshold_failures_count
        self.sl_off = string.join(map(chr,l_off),'')*(self.num_bars+1)
        self.sl_on = string.join(map(chr,l_on),'')*(self.num_bars+1)
        self.sr_off = string.join(map(chr,r_off),'')*(self.num_bars+1)
        self.sr_on = string.join(map(chr,r_on),'')*(self.num_bars+1)

    def num_bars():
        doc = "number of bars"
        def fget(self):
            return self.__num_bars
        def fset(self, value):
            self.__num_bars = value
        return locals()
    num_bars = property(**num_bars())
    
    def Get(self,l,r):
        s=""+self.s_line
        for i in range(self.num_bars):
            if i<(self.num_bars-l):
                sl = self.sl_off
            else:
                sl = self.sl_on

            if i<(self.num_bars-r):
                sr = self.sr_off
            else:
                sr = self.sr_on

            s+=self.s_border+sl+self.s_point+sr+self.s_point
            s+=self.s_border+sl+self.s_point+sr+self.s_point
            s+=self.s_line

        image = wx.EmptyImage(16,16)
        image.SetData(s)

        bmp = image.ConvertToBitmap()
        bmp.SetMask(wx.Mask(bmp, wx.WHITE)) #sets the transparency colour to white 

        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(bmp)

        return icon

class MyTaskBarIcon(wx.TaskBarIcon):
    def __init__(self, frame):
        wx.TaskBarIcon.__init__(self)
        self.frame = frame
        self.SetIconBar()

        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=4)
	
    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(4, 'Exit')
        return menu

    def OnTaskBarClose(self, event):
        self.frame.Close()

    def SetIconBar(self):
        '''Sets the icon bar hover text...'''
	import salesforce_icon2
	self.SetIcon(wx.IconFromBitmap(salesforce_icon2.getsalesforce_icon2Bitmap()))

_processing_list = []

_child_process_pid = -1

@threadpool.threadify(_thread_Q)
def notifyLeadOwner(leads,email,isSendingEmailsToLeadOwners,log=None):
    print >>sys.stdout, '(%s).2 :: isSendingEmailsToLeadOwners is "%s".' % (misc.funcName(),isSendingEmailsToLeadOwners)
    if (isSendingEmailsToLeadOwners):
	from vyperlogix.mail import message
	from vyperlogix.mail import mailServer
	
	rr = leads.getLeadsByEmail(email)
	print >>sys.stdout, '(%s).3 :: leads.getLeadsByEmail(%s) is "%s".' % (misc.funcName(),email,str(rr))
	if (rr is not None) and (len(rr) > 0):
	    ro = leads.getLeadOwnerById(rr[0]['OwnerId'])
	    print >>sys.stdout, '(%s).4 :: leads.getLeadOwnerById(%s) is "%s".' % (misc.funcName(),rr[0]['OwnerId'],str(ro))
	    if (ro is not None) and (len(ro) > 0):
		ro_email = ro[0]['Email']
		print >>sys.stdout, '(%s).5 :: ro_email is "%s".' % (misc.funcName(),ro_email)
		try:
		    _host = hostify(_sf_login_model.sfContext.endpoint_base)
		    io_buf = _utils.stringIO()
		    print >>io_buf, '''

%s

A new lead has been assigned to you. 

Lead Email: %s
Lead Name: %s
Lead Company : %s 

Lead Address: 
%s
%s, %s %s
USA 

You can review new lead at <a href="https://%s/%s" target="_blank">%s</a>.
				    ''' % ('Force.com Sandbox: ' if (_sf_login_model.isStaging) else '',email,'%s %s' % (rr[0]['FirstName'],rr[0]['LastName']),rr[0]['Company'],rr[0]['Street'],rr[0]['City'],rr[0]['State'],rr[0]['PostalCode'],_host,rr[0]['Id'],rr[0]['Id'])
		    msg = message.HTMLMessage('salesforce-support@molten-magma.COM', 'rhorn@molten-magma.com' if (_sf_login_model.isStaging) else ro_email, io_buf.getvalue(), subject='%sA new lead has been assigned to you%s.' % ('Force.com Sandbox: ' if (_sf_login_model.isStaging) else '',' (%s)' % (ro_email) if (_sf_login_model.isStaging) else ''))
		    smtp = mailServer.GMailServer('','',_smtp_server_address.split(':')[0],int(_smtp_server_address.split(':')[-1]))
		    smtp.sendEmail(msg)
		    if (not _sf_login_model.isStaging):
			msg = message.HTMLMessage(ro_email, 'rhorn@molten-magma.com', io_buf.getvalue(), subject='%sA new lead has been assigned to you%s.' % ('Force.com Sandbox: ' if (_sf_login_model.isStaging) else '',' (%s)' % (ro_email)))
			smtp.sendEmail(msg)
		except Exception, details:
		    info_string = _utils.formattedException(details=details)
		    appendText(log,info_string)
		    print >>sys.stderr, info_string

def importLeadIntoSalesForce(emailColName,email,aCandidate,isSendingEmailsToLeadOwners,log=None):
    from pyax.sobject.classfactory import ClassFactory
    
    from vyperlogix.sf.sf import SalesForceQuery
    sfQuery = SalesForceQuery(_sf_login_model)

    from vyperlogix.sf.leads import SalesForceLeads
    leads = SalesForceLeads(sfQuery)

    from vyperlogix.sf.contacts import SalesForceContacts
    contacts = SalesForceContacts(sfQuery)

    from vyperlogix.sf.magma.leadSourceHistory import SalesForceLeadSourceHistory
    histories = SalesForceLeadSourceHistory(sfQuery)
    
    isLead = False
    isContact = False
    isNone = False

    aLead = None
    aContact = None
    
    print >>sys.stdout, '(%s).1.0 :: isSendingEmailsToLeadOwners is "%s" of type "%s".' % (misc.funcName(),isSendingEmailsToLeadOwners,type(isSendingEmailsToLeadOwners))
    isSendingEmailsToLeadOwners = isSendingEmailsToLeadOwners if (isinstance(isSendingEmailsToLeadOwners,bool)) else False
    
    print >>sys.stdout, '(%s).1.1 :: isSendingEmailsToLeadOwners is "%s".' % (misc.funcName(),isSendingEmailsToLeadOwners)
    
    lw_header = ListWrapper(_csv_model.header)
    d = lists.HashedLists2()
    header = lw_header.copy()
    if (isinstance(aCandidate,list)):
	for i in xrange(len(aCandidate)):
	    d[header[i]] = aCandidate[i]
    else:
	d = aCandidate
    if (email is not None) and (len(email) > 0):
	_contact_id = None
	r = leads.getLeadsByEmail(email)
	isLead = (r is not None) and (len(r) > 0) and (not str(r[-1]).isdigit())
	if (isLead):
	    aLead = r[0]
	    r = [l for l in r if (l['ConvertedDate'])]
	    if (len(r) > 0):
		for aLead in r:
		    appendText(log,'(%s) :: aLead=%s' % (misc.funcName(),aLead))
		    isContact = (aLead['ConvertedContactId'] is not None) and (aLead['ConvertedDate'] is not None)
		    if (isContact):
			_contact_id = aLead['ConvertedContactId']
			break
	if (not isContact):
	    r = contacts.getContactsByEmail(email)
	    isContact = (r is not None) and (len(r) > 0) and (not str(r[-1]).isdigit())
	    if (isContact):
		aContact = r[0]
		_contact_id = aContact['Id']
	isNone = (not isLead) and (not isContact)
	if (isNone):
	    try:
		aStreet = []
		aStreet.append(prep_data_for_salesforce(d,_symbol_address1))
		if (d.has_key(_symbol_table[_symbol_address2])):
		    val = prep_data_for_salesforce(d,_symbol_address2)
		    if (val is not None):
			aStreet.append(val)
		if (d.has_key(_symbol_table[_symbol_address3])):
		    val = prep_data_for_salesforce(d,_symbol_address3)
		    if (val is not None):
			aStreet.append(val)
		aStreet = [street for street in aStreet if (street is not None)]
		aLead = ClassFactory(leads.sfQuery.sfdc, 'Lead')
		try:
		    d_lead = {'Title':prep_data_for_salesforce(d,_symbol_title),
			      'FirstName':prep_data_for_salesforce(d,_symbol_firstName),
			      'LastName':prep_data_for_salesforce(d,_symbol_lastName),
			      'Email':email,
			      'RecordTypeId':d_recTypes[_cbRecordTypes],
			      'LeadSource':_cbLeadSource,
			      'Company':prep_data_for_salesforce(d,_symbol_company),
			      'Country':prep_data_for_salesforce(d,_symbol_country),
			      'City':prep_data_for_salesforce(d,_symbol_city),
			      'Street':','.join(aStreet),
			      'State':prep_data_for_salesforce(d,_symbol_state),
			      'PostalCode':prep_data_for_salesforce(d,_symbol_zipPostalCode),
			      'Phone':prep_data_for_salesforce(d,_symbol_phone),
			      'MobilePhone':prep_data_for_salesforce(d,_symbol_phone_mobile),
			      }
		except Exception, details:
		    info_string = misc.formattedException(details=details)
		    print >>sys.stderr, info_string
		saveResults = leads.sfQuery.sfdc.create(aLead, [d_lead])
		if (saveResults[0].has_key('errors')):
		    info_string = 'Failed to create Lead from %s!' % (d_lead)
		    print >>sys.stdout, info_string
		    appendText(log,info_string)
		else:
		    notifyLeadOwner(leads,email,isSendingEmailsToLeadOwners,log=log)
		    d_leadTypes = leads.leadTypes().insideOut()
		    aLeadSourceData = ClassFactory(leads.sfQuery.sfdc, 'LeadSourceData__c')
		    d_data = {'Notes__c':prep_data_for_salesforce(d,_symbol_notes),
			      'Date__c':_utils.getFromDateTimeStr(_utils.timeStampSimple(),format=_utils.formatDate_MMDDYYYY_slashes()),
			      'Lead__c':saveResults[0]['id'],
			      'Source__c':d_leadTypes[_cbLeadTypes],
			      'Description__c':_cbLeadSourceDescr,
			      'Type__c':_cbLeadSourceDataTypes,
			      'Applications__c':prep_data_for_salesforce(d,_symbol_product)
			      }
		    io_buf = _utils.stringIO()
		    lists.prettyPrint(d_data,title='LeadSourceData__c for Lead #%s' % (saveResults[0]['id']),fOut=io_buf)
		    appendText(log,io_buf.getvalue())
		    saveResults2 = leads.sfQuery.sfdc.create(aLeadSourceData, [d_data])
		    if (saveResults2[0].has_key('errors')):
			info_string = '1. Failed to create LeadSourceData__c from %s!' % (d_data)
			appendText(log,info_string)
			
		    _status = 'New Lead+Scored'
		    appendText(log,'%s: %s :: %s, %s' % (_status,email,str(saveResults),str(saveResults2)))
		    return _status
	    except Exception, details:
		_details = _utils.formattedException(details)
		appendText(log,_details)
	elif (isContact):
	    try:
		d_leadTypes = leads.leadTypes().insideOut()
		
		schemas = []
		schemas.append(histories.new_schema(aLead['LeadSource'],aLead['RecordTypeId'],Contact__c=_contact_id))
		histories.createBatch(schemas)
		
		aLeadSourceData = ClassFactory(leads.sfQuery.sfdc, 'LeadSourceData__c')
		d_data = {'Notes__c':prep_data_for_salesforce(d,_symbol_notes),
			  'Date__c':_utils.getFromDateTimeStr(_utils.timeStampSimple(),format=_utils.formatDate_MMDDYYYY_slashes()),
			  'Contact__c':_contact_id,
			  'Source__c':d_leadTypes[_cbLeadTypes],
			  'Description__c':_cbLeadSourceDescr,
			  'Type__c':_cbLeadSourceDataTypes,
			  'Applications__c':prep_data_for_salesforce(d,_symbol_product)
			  }
		saveResults2 = leads.sfQuery.sfdc.create(aLeadSourceData, [d_data])
		if (saveResults2[0].has_key('errors')):
		    info_string = '2. Failed to create LeadSourceData__c from %s!' % (d_data)
		    appendText(log,info_string)
		    _status = 'Contact-Not_Scored'
		else:
		    _status = 'Contact+Scored'
		    appendText(log,'%s: %s :: %s' % (_status,email,str(saveResults2)))
		    
		aLead['ConvertedContact']['RecordTypeId'] = d_recTypes[_cbRecordTypes]
		aLead['ConvertedContact']['LeadSource'] = _cbLeadSource
		leads.update(aLead)
		
		return _status
	    except Exception, details:
		_details = _utils.formattedException(details)
		appendText(log,_details)
	elif (isLead):
	    try:
		d_leadTypes = leads.leadTypes().insideOut()
		
		schemas = []
		schemas.append(histories.new_schema(aLead['LeadSource'],aLead['RecordTypeId'],Lead__c=aLead['Id']))
		histories.createBatch(schemas)
		
		aLeadSourceData = ClassFactory(leads.sfQuery.sfdc, 'LeadSourceData__c')
		d_data = {'Notes__c':prep_data_for_salesforce(d,_symbol_notes),
			  'Date__c':_utils.getFromDateTimeStr(_utils.timeStampSimple(),format=_utils.formatDate_MMDDYYYY_slashes()),
			  'Lead__c':aLead['Id'],
			  'Source__c':d_leadTypes[_cbLeadTypes],
			  'Description__c':_cbLeadSourceDescr,
			  'Type__c':_cbLeadSourceDataTypes,
			  'Applications__c':prep_data_for_salesforce(d,_symbol_product)
			  }
		if (_contact_id is not None):
		    d_data['Contact__c'] = _contact_id
		saveResults2 = leads.sfQuery.sfdc.create(aLeadSourceData, [d_data])
		if (saveResults2[0].has_key('errors')):
		    info_string = '3. Failed to create LeadSourceData__c from %s!' % (d_data)
		    appendText(log,info_string)
		    _status = 'Lead-Not_Scored'
		else:
		    _status = 'Lead+Scored'
		    appendText(log,'%s: %s :: %s' % (_status,email,str(saveResults2)))
		    
		aLead['RecordTypeId'] = d_recTypes[_cbRecordTypes]
		aLead['LeadSource'] = _cbLeadSource
		leads.update(aLead)
		
		return _status
	    except Exception, details:
		_details = _utils.formattedException(details)
		appendText(log,_details)
    return ''

def handle_importLeadIntoSalesForce(self,emailColName,email,aCandidate,isSendingEmailsToLeadOwners,log=None):
    _status = importLeadIntoSalesForce(emailColName,email,aCandidate,isSendingEmailsToLeadOwners,log=log)
    _scored = 'YES' if (_status.find('+Scored') > -1) else 'NO'
    print '"%s", status is "%s",scored is "%s".' % (email,_status,_scored)
    self.track_qa_for_email(email,status=_status,scored=_scored,validated='Pending')
    appendText(log,'(%s).2.1 :: _use_validation_QC is %s.' % (misc.funcName(),_use_validation_QC))
    if (not _use_validation_QC):
	self.count += 1
    else:
	self.track_qa_for_validation(email,status=_status,scored=_scored,validated='Pending')

def handle_preloadLeadIntoSalesForceSandbox(self,emailColName,email,aCandidate,isSendingEmailsToLeadOwners,log=None):
    from vyperlogix.sf.sf import SalesForceQuery
    sfQuery = SalesForceQuery(_sf_login_model)

    from vyperlogix.sf.magma.temp_object import SalesForceTempObject
    temps = SalesForceTempObject(sfQuery)

    if (len(self.__schemas) == 0):
	temporaries = temps.getTempObjects()
	pass
    
    self.__schemas.append(temps.new_schema(aCandidate['address1__c'],aCandidate['address2__c'], aCandidate['address3__c'], aCandidate['city__c'], aCandidate['company__c'], aCandidate['country__c'], aCandidate['eMail__c'], aCandidate['firstName__c'], aCandidate['lastName__c'], aCandidate['notes__c'], aCandidate['phoneMobile__c'], aCandidate['phoneOffice__c'], aCandidate['Product__c'], aCandidate['state__c'], aCandidate['title__c'], aCandidate['zipPostalCode__c']))
    _status = 'Preloaded'
    print '"%s", status is "%s".' % (k,_status)
    self.track_qa_for_email(k,status=_status,scored=_scored,validated='Pending')
    appendText(log,'(%s).2.1 :: _use_validation_QC is %s.' % (misc.funcName(),_use_validation_QC))
    if (not _use_validation_QC):
	self.count += 1
    else:
	self.track_qa_for_validation(k,status=_status,scored=_scored,validated='Pending')

@threadpool.threadify(_thread_Q)
def importLeadsIntoSalesForce(self,d,_email,isSendingEmailsToLeadOwners,callback_func=handle_importLeadIntoSalesForce,log=None):
    '''List of leads is not being de-duped to allow for legitimate multiple instances of Leads for those who participate in more than one activity at a time.'''
    global _isRunning
    n = d.length()
    appendText(log,'(%s).1 :: n is "%d".' % (misc.funcName(),n))
    try:
	if (n > 0):
	    self.count = 0
	    self.number = n
	    print >>sys.stdout, '(%s).2 :: isSendingEmailsToLeadOwners is "%s".' % (misc.funcName(),isSendingEmailsToLeadOwners)
	    for k,v in d.iteritems():
		if (_isRunning):
		    if (len(k) > 0):
			for _v in v:
			    #_v.encode('utf-8') # _csv_model.reader.__book__.encoding
			    if (callable(callback_func)):
				try:
				    _status = callback_func(self,_email,k,_v,isSendingEmailsToLeadOwners,log=log)
				except Exception, details:
				    info_string = _utils.formattedException(details=details)
				    print >>sys.stderr, info_string
		    else:
			self.number -= 1
		else:
		    appendText(log,'(%s).3 :: Process TERMINATED at user request.' % (misc.funcName()))
		    break
    except Exception, details:
	_details = _utils.formattedException(details)
	print >>sys.stderr, _details

def _appendText(log,x):
    try:
	log.AppendText(x+'\n')
	print >>sys.stdout, x
    except Exception, details:
	_details = _utils.formattedException(details)
	print >>sys.stderr, _details

def appendText(log,x):
    wx.CallAfter(_appendText,log,x)

def show_to_user(p):
    print 'Searching: "%s".' % (p)

    
def similarity_suggestions(l_left,l_right):
    from vyperlogix.hash import lists
    from vyperlogix.lists.ListWrapper import ListWrapper
    d = lists.HashedLists2()
    if (isinstance(l_left,list)) and (isinstance(l_right,list)):
	from vyperlogix.misc import SequenceMatcher
	_d_left = lists.HashedLists2()
	for item in l_left:
	    _d_left[str(item).lower()] = item
	_l_left = _d_left.keys()
	_d_right = lists.HashedLists2()
	for item in l_right:
	    _d_right[str(item).lower()] = item
	_l_right = _d_right.keys()
	for item in l_left:
	    toks = item.split()
	    if (len(toks) > 1):
		s = str(''.join(toks)).lower()
		_l_left.append(s)
		_d_left[s] = item
		_f = misc.findInListSafely(_l_left,str(item).lower())
		if (_f > -1):
		    del _l_left[_f]
	    elif ( (item.lower().startswith('zip')) and (item.lower().endswith('code')) ) or (item.lower() == 'zip'):
		_l_left.append(_symbol_zipPostalCode)
		_d_left[_symbol_zipPostalCode.lower()] = item
		_f = misc.findInListSafely(_l_left,str(item).lower())
		if (_f > -1):
		    del _l_left[_f]
	a = [(l_item,r_item,SequenceMatcher.computeQuickRatio(l_item,r_item)) for l_item in _l_left for r_item in _l_right]
	a1 = [(list(x)[0],list(x)[1:]) for x in a] #  if (list(x)[-1] != 1.0)
	d1 = lists.HashedLists()
	for t in a1:
	    _t = list(t)
	    d1[_t[0]] = _t[1:]
	d2 = lists.HashedLists2()
	for k,v in d1.iteritems(): # k comes from the l_left list.
	    vv = [tuple(_v[0]) for _v in v]
	    vd = lists.HashedLists(dict(vv))
	    _vd = lists.HashedLists()
	    for k1,v1 in vd.insideOut().iteritems():
		_vd[k1] = v1
	    _vd_keys = misc.reverse(misc.sort(_vd.keys()))
	    _vd_result = None
	    for item in _vd_keys:
		_vd_v = ListWrapper()
		for x in _vd[item]:
		    if (isinstance(x,list)):
			_vd_v += x
		    else:
			_vd_v.append(x)
		for n in xrange(len(k),3,-1):
		    s_k = k[0:n]
		    _vd_f = _vd_v.findFirstContaining(s_k.lower())
		    if (_vd_f > -1):
			_vd_result = _vd_v[_vd_f]
			break
	    d2[_d_left[k] if (_d_left.has_key(k)) else _d_left[k.lower()]] = _d_right[_vd_result]
    return d2

def perform_header_analysis(csv_model):
    '''Splits the contents of those columns that should be split.
    This function has not been tested and will not handle a split that results in more than two items per split.
    It is recommended the user split the data manually.
    '''
    h = [t.lower() for t in csv_model.header]
    for k,v in _symbol_exception_headers_table.iteritems():
	_k = k.lower()
	if (_k in h):
	    print 'Split header "%s" into "%s".' % (k,','.join(v if (isinstance(v,list)) else [v]))
	    csv_model.split_column(k,v[0],v[-1],split_callback=_symbol_exception_functions_table[_k])
	    pass
    pass

def redirectStdIO(fpath,do_close=False):
    prefix = ''
    if (os.path.isfile(fpath)):
	prefix = os.path.basename(fpath).split('.')[0]
	
	fpath = os.path.dirname(fpath)
    
    if (os.path.isdir(fpath)) and (os.path.exists(fpath)):
	if (do_close):
	    try:
		sys.stdout.flush()
		sys.stdout.close()
	    except:
		pass
	
	_stdOut = open(os.sep.join([fpath,'%sstdout.txt' % (prefix+'_')]),'w')
	sys.stdout = Log(_stdOut)
    
	if (do_close):
	    try:
		sys.stderr.flush()
		sys.stderr.close()
	    except:
		pass

	_stdErr = open(os.sep.join([fpath,'%sstderr.txt' % (prefix+'_')]),'w')
	sys.stderr = Log(_stdErr)

class MainFrame(wx.App):
    def OnInit(self):
	import CurrentUsers_Dialog
	self.__login_dialog__ = None
	self.__child_frame = CurrentUsers_Dialog.Dialog(None, title=__productName__, onProcess_callback=self.onProcess, onReset_callback=None, onToggleLog_callback=self.onToggleLog)
        self.__child_frame.Center(wx.BOTH)
        self.__child_frame.Show(True)
        self.SetTopWindow(self.__child_frame)
	
        self.__child_frame.__taskbar_icon = MyTaskBarIcon(self)
        self.__child_frame.Centre()
	
	self.__qa_dialog__ = None
	
	self.__leads = None
	self.__schemas = []
	self.__qa_Q__ = Queue.Queue(100)

	self.__validation_Q__ = Queue.Queue(100)
	
	import salesforce_icon2
	self.__child_frame.SetIcon(wx.IconFromBitmap(salesforce_icon2.getsalesforce_icon2Bitmap()))
	
        self.statusBar = CustomStatusBar.CustomStatusBar(self.__child_frame, None)
        self.__child_frame.SetStatusBar(self.statusBar)
        self.statusBar.SetFieldsCount(2)
        self.statusBar.SetStatusWidths([-4, -2])
	
        # Menu Bar
        self.top_frame_menubar = wx.MenuBar()
        self.file_menu_item = wx.Menu()
        self.exit_menu_item = wx.MenuItem(self.file_menu_item, wx.NewId(), "Exit", "", wx.ITEM_NORMAL)
	
        self.file_menu_item.AppendItem(self.exit_menu_item)
        self.top_frame_menubar.Append(self.file_menu_item, "File")
	
        self.help_menu_item = wx.Menu()
        self.about_menu_item = wx.MenuItem(self.help_menu_item, wx.NewId(), "About", "", wx.ITEM_NORMAL)
        self.help_menu_item.AppendItem(self.about_menu_item)
        self.changelog_menu_item = wx.MenuItem(self.help_menu_item, wx.NewId(), "Change Log", "", wx.ITEM_NORMAL)
        self.help_menu_item.AppendItem(self.changelog_menu_item)
        self.top_frame_menubar.Append(self.help_menu_item, "Help")

        self.__child_frame.SetMenuBar(self.top_frame_menubar)
        # Menu Bar end

        self.Bind(wx.EVT_MENU, self.OnClose, self.exit_menu_item)
        self.Bind(wx.EVT_MENU, self.onAbout, self.about_menu_item)
        self.Bind(wx.EVT_MENU, self.onChangeLog, self.changelog_menu_item)

	self.__child_frame.Bind(wx.EVT_CLOSE, self.OnClose)
	
	self.__d_recordTypes = lists.HashedLists2()
	self.__d_leadTypes = lists.HashedLists2()
	self.__d_leadSources = lists.HashedLists2()
	self.__d_leadSourceDescriptions = lists.HashedLists2()
	self.__d_leadSourceTypes = lists.HashedLists2()

	self.__number = 0
	self.__count = 0
	self.__isDialogClosed = False
	self.__onProcessingDone = None
	self.__isAppClosed = False
	
        self.__timer = None

	self.__callback_TimerHandler = None
	
	self.__child_frame.Bind(wx.EVT_TIMER, self.TimerHandler)
	
	if (not _utils.isBeingDebugged) and ( (not _utils._isComputerAllowed) or (not _is_running_securely) ):
	    wx_PopUp_Dialog(parent=self.__child_frame,msg='Sorry but you cannot use this program at this time due to Security Concerns.\nPlease try back later from safely behind the Magma Firewall as a user on the Magma domain.',title='USER ERROR',styles=wx.ICON_ERROR)
	    self._OnClose()
	else:
	    self.__child_frame.btnProcess2.Hide()
	    self.init_salesforce()
	    self.enable_ifPossible()
	    self.__child_frame.Disable()
	
	return True
    
    def log(self, msg):
	appendText(self.__child_frame.textboxLog,str(msg))
    
    def number():
        doc = "number"
        def fget(self):
            return self.__number
        def fset(self, number):
            self.__number = number
	    appendText(self.__child_frame.textboxLog,'%s :: number is "%d".' % (ObjectTypeName.objectSignature(self),number))
        return locals()
    number = property(**number())
    
    def count():
        doc = "count"
        def fget(self):
            return self.__count
        def fset(self, count):
            self.__count = count
	    appendText(self.__child_frame.textboxLog,'%s :: count is "%d".' % (ObjectTypeName.objectSignature(self),count))
        return locals()
    count = property(**count())
    
    def isDialogClosed():
        doc = "isDialogClosed"
        def fget(self):
            return self.__isDialogClosed
        return locals()
    isDialogClosed = property(**isDialogClosed())
    
    def progressTimerHandler(self):
	b = True
	if (self.__qa_dialog__ is not None):
	    try:
		_b_ = (self.__qa_dialog__.percentage_completed() >= 100.0)
		b = _b_
	    except:
		pass
	if (b) and (self.count == self.number):
	    self.callback_ProgressDialogDone()
	    self.__isDialogClosed = True
	else:
	    count = (float(self.count)/float(self.number))*100.0
	    self.gauge_panel.count = count
	    self.gauge_panel.update()
	    self.process_qa_data()
	    self.process_qa_validation()
	
    def progressTimerHandlerWaitForThreads(self):
	b = True
	if (self.__qa_dialog__ is not None):
	    try:
		p = self.__qa_dialog__.percentage_completed()
		_b_ = (p >= 100.0)
		b = _b_
		appendText(self.__child_frame.textboxLog,'%s :: p is "%3.0f" (%s), b is "%s".' % (ObjectTypeName.objectSignature(self),p,p,b))
	    except:
		pass
	appendText(self.__child_frame.textboxLog,'%s :: self.count is "%d", self.number is "%d".' % (ObjectTypeName.objectSignature(self),self.count,self.number))
	if (b) and (self.count == self.number):
	    print >>sys.stdout, '_thread_Q.join()'
	    _thread_Q.join()
	    self.callback_ProgressDialogDone()
	    self.__isDialogClosed = True
	else:
	    try:
		count = (float(self.count)/float(self.number))*100.0
	    except ZeroDivisionError:
		count = 0
	    self.gauge_panel.count = count
	    self.gauge_panel.update()
	    self.process_qa_data()
	    self.process_qa_validation()

    def process_qa_data(self):
	try:
	    if (not self.__qa_Q__.empty()):
		data = self.__qa_Q__.get_nowait()
		appendText(self.__child_frame.textboxLog,'(**) %s' % (ObjectTypeName.objectSignature(self)))
		self.__qa_dialog__.update_lbMonitor_item(data)
	except Exception, details:
	    info_string = _utils.formattedException(details)
	    print >>sys.stderr, info_string
	    appendText(self.__child_frame.textboxLog,info_string)
	    
    def process_qa_validation(self):
	try:
	    info_string = '%s.1 :: Q-Size is %d and count is %d.' % (ObjectTypeName.objectSignature(self),self.__validation_Q__.qsize(),self.count)
	    appendText(self.__child_frame.textboxLog,info_string)
	    if (not self.__validation_Q__.empty()):
		data = self.__validation_Q__.get_nowait()
		try:
		    appendText(self.__child_frame.textboxLog,'(**) %s.2' % (ObjectTypeName.objectSignature(self)))
		    email,status,scored,validated = data
		    
		    from vyperlogix.sf.sf import SalesForceQuery
		    sfQuery = SalesForceQuery(_sf_login_model)
		    from vyperlogix.sf.leads import SalesForceLeads
		    leads = SalesForceLeads(sfQuery)
		    aLead = leads.getLeadsByEmail(email)
		    if (isinstance(aLead,list)) and (len(aLead) > 0):
			aLead = aLead[0]

			isContact = (aLead['ConvertedContactId'] is not None) and (aLead['ConvertedDate'] is not None)
			_id = aLead['Id'] if (not isContact) else aLead['ConvertedContactId']
			
			from vyperlogix.sf.users import SalesForceUsers
			users = SalesForceUsers(sfQuery)
			aUser = users.getUserById(aLead['OwnerId'])
			if (users.contains_sf_objects(aUser)):
			    aUser = aUser[0]
			    validated = 'VALID' if (aUser['Name'].lower().find('Salesforce Support'.lower()) == -1) and (aUser['Name'].lower().find('Lead-Catchall'.lower()) == -1) else validated
			    appendText(self.__child_frame.textboxLog,'%s.3 :: User Name "%s" is %s.' % (ObjectTypeName.objectSignature(self),aUser['Name'],validated))

			from vyperlogix.sf.magma.leadSourceData import SalesForceLeadSourceData
			lead_source_data = SalesForceLeadSourceData(sfQuery)
			activities = lead_source_data.getTodaysActivityByLeadOrContactId(_id)
			has_activities = lead_source_data.contains_sf_objects(activities)
			    
			# bump the count only if the validation was successful.
			if (_use_validation_QC) and (has_activities):
			    validated = 'VALID+ACTIVITIES (%d)' % (len(activities))
			    self.count += 1
			appendText(self.__child_frame.textboxLog,'%s.4 :: %s for count of %d.' % (ObjectTypeName.objectSignature(self),validated,self.count))
		
		    data = (email,status,scored,validated)
		    self.__qa_dialog__.update_lbMonitor_item(data)
		except Exception, details:
		    info_string = _utils.formattedException(details)
		    appendText(self.__child_frame.textboxLog,info_string)
	except Exception, details:
	    info_string = _utils.formattedException(details)
	    print >>sys.stderr, info_string
	    appendText(self.__child_frame.textboxLog,info_string)
	    
    def TimerHandler(self, event):
	if (callable(self.__callback_TimerHandler)):
	    self.__callback_TimerHandler()
	
    def startTimer(self):
	self.__timer = wx.Timer(self.__child_frame)
	self.__timer.Start(250)
    
    def stopTimer(self):
        if (self.__timer):
            self.__timer.Stop()
	    self.__timer = None
    
    def callback_ProgressDialogError(self):
	self.stopTimer()
	wx_PopUp_Dialog(parent=self.__child_frame,msg='There is nothing to do because there are "%d" keys in this file.' % (len(dbx)),title='WARNING',styles=wx.ICON_WARNING)
    
    def callback_ProgressDialogDone(self):
	self.stopTimer()
	if (not self.isDialogClosed):
	    self.gauge_panel.closeDialog()
	    self.__isDialogClosed = True
	    if (callable(self.__onProcessingDone)):
		try:
		    self.__onProcessingDone()
		finally:
		    self.__onProcessingDone = None
	    
    def handle_an_item(self,k,v,log):
	from vyperlogix.sf.sf import SalesForceQuery
	sfQuery = SalesForceQuery(_sf_login_model)
	from vyperlogix.sf.leads import SalesForceLeads
	leads = SalesForceLeads(sfQuery)
	
	appendText(log,'%s=%s' % (k,v))
	d_v = lists.HashedLists2(v)
	d_saveResults2 = d_v['saveResults2']
	if (d_saveResults2):
	    _id = d_saveResults2['id']
	    if (_id):
		from vyperlogix.sf.delete import deleteSalesForceObjects
		r = deleteSalesForceObjects(sfQuery.sfdc,[_id])
		appendText(log,'Deleted LeadSourceData %s' % (r))
	d_saveResults = d_v['saveResults']
	if (d_saveResults):
	    _id = d_saveResults['id']
	    if (_id):
		from vyperlogix.sf.delete import deleteSalesForceObjects
		r = deleteSalesForceObjects(sfQuery.sfdc,[_id])
		appendText(log,'Deleted Lead %s' % (r))
    
    def refreshButtonsAfterLeadsImported(self):
	self.__child_frame.btnProcess3.Disable()
	d_button_enable_map[_symbol_btnProcess3_button] = False

	val_cbProcessMode = self.__child_frame.cbProcessMode.GetValue()
	if (val_cbProcessMode == self.__child_frame.cbProcessMode_preload_leads):
	    appendText(self.__child_frame.textboxLog,'Creating a batch of %d TEMP_OBJECT__c objects.' % (self.__schemas))
	    pass

	try:
	    self.__qa_dialog__._OnClose()
	finally:
	    self.__qa_dialog__ = None
	appendText(self.__child_frame.textboxLog,'DONE !!!')
    
    def onChangeLog(self, event):
	from CurrentUsers_Dialog import ChangeLogDialog
	self.__changeLog_dialog__ = ChangeLogDialog(None, 'ChangeLog for %s' % (s_productName))
	self.__changeLog_dialog__.tbChangeLog.SetValue(__ChangeLog__)
	self.__changeLog_dialog__.Show()
	self.__changeLog_dialog__.CenterOnParent()
	
    def onAbout(self, event):
	import salesforce_icon2

        info = wx.AboutDialogInfo()
        info.Name = s_productName
        info.Version = __version__
        info.Copyright = _info_Copyright
        info.Description = wordwrap(
            "\"%s\" is a software program that Imports Leads with Leads Scoring into SalesForce using the Apex API and must be executed from behind the Firewall using a specific domain for security purposes. " % (__productName__),
            350, wx.ClientDC(self.__child_frame))
        info.WebSite = ("http://%s" % (_info_site_address), "%s Home Page" % (__productName__))

        info.License = wordwrap(__copyright__, 700, wx.ClientDC(self.__child_frame))

	info.SetIcon(wx.IconFromBitmap(salesforce_icon2.getsalesforce_icon2Bitmap()))
	
	for n in _developers:
	    info.AddDeveloper(n)
	for n in _writers:
	    info.AddDocWriter(n)
	for n in _artists:
	    info.AddArtist(n)
	for n in _translators:
	    info.AddTranslator(n)
        
        wx.AboutBox(info)

    def hideLog(self):
	self.__child_frame.textboxLog.Hide()
	self.__child_frame.btnToggleLog.SetLabel('Show %s' % (self.__child_frame.btnToggleLog.GetLabel().split()[-1]))
	    
    def showLog(self):
	self.__child_frame.textboxLog.Show()
	self.__child_frame.btnToggleLog.SetLabel('Hide %s' % (self.__child_frame.btnToggleLog.GetLabel().split()[-1]))

    def onToggleLog(self):
	if (self.__child_frame.textboxLog.IsShown()):
	    self.hideLog()
	else:
	    self.showLog()
    
    def onProcess(self):
	global _csv_model
	try:
	    print '\n%s' % (ObjectTypeName.objectSignature(self))
	    print 'cbRecordTypes is "%s"' % (self.__child_frame.cbRecordTypes.GetValue())
	    print 'cbLeadTypes is "%s"' % (self.__child_frame.cbLeadTypes.GetValue())
	    print 'cbLeadSource is "%s"' % (self.__child_frame.cbLeadSource.GetValue())
	    print 'cbLeadSourceDescr is "%s"' % (self.__child_frame.cbLeadSourceDescr.GetValue())
	    print 'cbLeadSourceDataTypes is "%s"' % (self.__child_frame.cbLeadSourceDataTypes.GetValue())
    
	    fn = oodb.dbx_name('%s.dbx' % (_utils.getProgramName()),_data_path)
	    oodb.put_data(fn,_symbol_cbRecordTypes,self.__child_frame.cbRecordTypes.GetValue(),fOut=sys.stderr)
	    oodb.put_data(fn,_symbol_cbLeadTypes,self.__child_frame.cbLeadTypes.GetValue(),fOut=sys.stderr)
	    oodb.put_data(fn,_symbol_cbLeadSource,self.__child_frame.cbLeadSource.GetValue(),fOut=sys.stderr)
	    oodb.put_data(fn,_symbol_cbLeadSourceDescr,self.__child_frame.cbLeadSourceDescr.GetValue(),fOut=sys.stderr)
	    oodb.put_data(fn,_symbol_cbLeadSourceDataTypes,self.__child_frame.cbLeadSourceDataTypes.GetValue(),fOut=sys.stderr)
	except Exception, details:
	    _details = _utils.formattedException(details)
	    wx_PopUp_Dialog(parent=self.__child_frame,msg=_details,title='ERROR',styles=wx.ICON_INFORMATION | wx.CANCEL)
	
	try:
	    if (_csv_model.num_headers < 1):
		if (len(self.__child_frame.cbRecordTypes.GetValue()) > 0) and (len(self.__child_frame.cbLeadTypes.GetValue()) > 0) and (len(self.__child_frame.cbLeadSource.GetValue()) > 0) and (len(self.__child_frame.cbLeadSourceDescr.GetValue()) > 0) and (len(self.__child_frame.cbLeadSourceDataTypes.GetValue()) > 0):
		    try:
			self.disable_ifPossible()
			fn = oodb.dbx_name('%s.dbx' % (_utils.getProgramName()),_data_path)
			_root_ = oodb.get_data(fn,_symbol_csv_path,fOut=None)
			if (_root_ is None):
			    _root_ = _info_root_folder
			else:
			    _root_ = _root_ if (not isinstance(_root_,list)) else _root_[0]
			file_types = []
			toks = wildcard_csv.split('|')
			for t in iterutils.iterstep(toks,2):
			    file_types.append(t)
			dlg = wx.FileDialog(
			    self.__child_frame, message="Choose a %s file that contains the data you wish to use when Importing Leads." % (' or '.join(file_types)),
			    defaultDir=_root_, 
			    defaultFile="",
			    wildcard=wildcard_csv,
			    style=wx.FD_OPEN | wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST
			    )
	
			if (dlg.ShowModal() == wx.ID_OK):
			    paths = dlg.GetPaths()
			    paths = paths if (not isinstance(paths,list)) else paths[0]
			    redirectStdIO(paths)
			    if (paths.endswith(_symbol_xls_filetype)):
				_csv_model = XLS2(dict2_factory=lists.HashedFuzzyLists2)
			    else:
				_csv_model = CSV2(dict2_factory=lists.HashedFuzzyLists2)
			    CustomStatusBar._status_bar_notification.append(('Reading "%s".' % (paths),1))
			    _csv_model.filename = paths
			    fn = oodb.dbx_name('%s.dbx' % (_utils.getProgramName()),_data_path)
			    oodb.put_data(fn,_symbol_csv_path,os.path.dirname(_csv_model.filename) if (os.path.isfile(_csv_model.filename)) else _csv_model.filename,fOut=sys.stderr)
			    CustomStatusBar._status_bar_notification.append(('Analyzing "%s".' % (str(paths)),1))
			    _tests = []
			    _missing = []
			    _header = [h.lower() for h in _csv_model.header]
			    for h in _header:
				aTest = _symbol_minimal_table.has_key(h) or _symbol_table.has_key(h)
				_tests.append(aTest)
				if (not aTest):
				    _missing.append(h)
			    _csv_model.isValid = all(_tests) and (len(_tests) > 0)
			    CustomStatusBar._status_bar_notification.append(('Is "%s" Valid %s.' % (str(paths),_csv_model.isValid),1))
			    if (not _csv_model.isValid) and (len(_missing) > 0):
				resp = wx_PopUp_Dialog(parent=self.__child_frame,msg='Cannot Process unless your %s has all of the required column headers, yours has these ("%s") that don\'t seem to make any sense and must be corrected so they do make sense before you can proceed.  You may need to rename some of your existing column headers to allow the required column headers to be present.\n\nFeel free to edit the headers as-needed to satisfy this pop-up or simply click the OK button to by-pass this warning.' % (ObjectTypeName.typeClassName(_csv_model).split('.')[-1],', '.join(_missing)),title='Okay to Process anyway ?!?',styles=wx.ICON_INFORMATION | wx.YES_NO)
				if (resp == wx.ID_YES):
				    _csv_model.isValid = True
			    if (_csv_model.isValid):
				self.refreshEmailColWidgetFrom(_csv_model.header)
				    
				self.__child_frame.btnProcess.SetLabel(_symbol_import_csv_button_face)
				self.__child_frame.btnProcess1.Disable()
				d_button_enable_map[_symbol_btnProcess1_button] = False
				d_button_enable_map[_symbol_btnProcess2_button] = False
				self.__child_frame.btnProcess2.SetLabel(_symbol_import_csv_button_face)
				self.__child_frame.labelCSVEmailAddressCol.Show()
				
				pname = os.path.basename(_csv_model.filename).split('.')[0]
				
				self.__child_frame.SetLabel('%s %s' % (self.__child_frame.GetLabel(),pname))
			if (_csv_model.isValid):
			    CustomStatusBar._status_bar_notification.append(('OnProcess_MapperDialog',1))
			    self.OnProcess_MapperDialog()
			elif (len(_missing) > 0):
			    wx_PopUp_Dialog(parent=self.__child_frame,msg='Cannot Process unless your %s has all of the required column headers, yours has these ("%s") that don\'t seem to make any sense and must be corrected so they do make sense before you can proceed.  You may need to rename some of your existing column headers to allow the required column headers to be present.\n\nFeel free to edit the headers as-needed to satisfy this pop-up.' % (ObjectTypeName.typeClassName(_csv_model).split('.')[-1],', '.join(_missing)),title='WARNING',styles=wx.ICON_WARNING)
			else:
			    wx_PopUp_Dialog(parent=self.__child_frame,msg='Cannot Process unless your %s due to some other kind of error that should NEVER happen.  At this point the only thing you can do is drop an email to I.T. and tell them what happened. Sorry.' % (ObjectTypeName.typeClassName(_csv_model).split('.')[-1]),title='ERROR',styles=wx.ICON_ERROR)
		    except Exception, details:
			_details = _utils.formattedException(details)
			wx_PopUp_Dialog(parent=self.__child_frame,msg=_details,title='ERROR',styles=wx.ICON_INFORMATION | wx.CANCEL)
		else:
		    wx_PopUp_Dialog(parent=self.__child_frame,msg='Cannot Process unless you choose something for each list displayed.',title='WARNING',styles=wx.ICON_WARNING)
	    else:
		try:
		    resp = wx.ID_YES # fake it so the process will proceed...
		    print 'resp is "%s" but is this wx.ID_YES ? "%s".' % (resp,(resp == wx.ID_YES))
		    if (resp == wx.ID_YES):
			val_cbProcessMode = self.__child_frame.cbProcessMode.GetValue()
			if (val_cbProcessMode != self.__child_frame.cbProcessMode_default):
			    self.__child_frame.btnProcess3.Disable()
			    email_col_name = self.__child_frame.cbCSVEmailAddressCol.GetValue()
			    
			    d = lists.HashedLists()
			    for rec in _csv_model.rowsAsRecords():
				rec_key = _symbol_table[email_col_name]
				try:
				    _rec = str(rec[rec_key])
				    if (len(_rec) > 0):
					d[_rec] = rec
				except Exception, details:
				    info_string = misc.formattedException(details=details)
				    print >>sys.stderr, info_string
				    
			    if (val_cbProcessMode == self.__child_frame.cbProcessMode_preload_leads):
				from vyperlogix.wx.ProgressDialogPanel import ProgressDialogPanel
				self.gauge_panel = ProgressDialogPanel(self.__child_frame,title='Processing Leads Preload')
				self.gauge_panel.Centre(wx.BOTH)
				self.__isDialogClosed = False
				lists.prettyPrint(d,title='Leads',fOut=sys.stdout)
				self.__callback_TimerHandler = self.progressTimerHandlerWaitForThreads
				self.__onProcessingDone = self.refreshButtonsAfterLeadsImported
				self.startTimer()
				self.__child_frame.btnToggleLog.Show()
				self.hideLog()
				self.showLog()
				
				from CurrentUsers_Dialog import QAMonitorDialog
				self.__qa_dialog__ = QAMonitorDialog(None, title='QA Monitor', logger=self.log)
				self.__qa_dialog__.Show(True)
				self.__qa_dialog__.CenterOnParent()
				
				try:
				    recs = [(rec[_symbol_table[_symbol_email]],'Pending','','') for rec in _csv_model.rowsAsRecords() if (len(rec[_symbol_table[_symbol_email]]) > 0)]
				except Exception, details:
				    recs = []
				    info_string = _utils.formattedException(details=details)
				    print >>sys.stderr, info_string
				self.__qa_dialog__.append_all_to_lbMonitor(recs)
				
				d.prettyPrint(title='_csv_model.rowsAsRecords')
				importLeadsIntoSalesForce(self,d,email_col_name,False,callback_func=handle_preloadLeadIntoSalesForceSandbox,log=self.__child_frame.textboxLog)
			    elif (val_cbProcessMode == self.__child_frame.cbProcessMode_import_leads):
				from vyperlogix.wx.ProgressDialogPanel import ProgressDialogPanel
				self.gauge_panel = ProgressDialogPanel(self.__child_frame,title='Processing Leads Importer')
				self.gauge_panel.Centre(wx.BOTH)
				self.__isDialogClosed = False
				lists.prettyPrint(d,title='Leads',fOut=sys.stdout)
				self.__callback_TimerHandler = self.progressTimerHandlerWaitForThreads
				self.__onProcessingDone = self.refreshButtonsAfterLeadsImported
				self.startTimer()
				isSendEmailsForSalesForce = is_checkbox_value_true(self.__child_frame.cbSendEmailsForSalesForce.GetValue())
				print >>sys.stdout, '%s :: isSendEmailsForSalesForce is "%s".' % (ObjectTypeName.objectSignature(self),isSendEmailsForSalesForce)
				self.__child_frame.btnToggleLog.Show()
				self.hideLog()
				self.showLog()
				
				from CurrentUsers_Dialog import QAMonitorDialog
				self.__qa_dialog__ = QAMonitorDialog(None, title='QA Monitor', logger=self.log)
				self.__qa_dialog__.Show(True)
				self.__qa_dialog__.CenterOnParent()
				
				try:
				    recs = [(rec[_symbol_table[_symbol_email]],'Pending','','') for rec in _csv_model.rowsAsRecords() if (len(rec[_symbol_table[_symbol_email]]) > 0)]
				except Exception, details:
				    recs = []
				    info_string = _utils.formattedException(details=details)
				    print >>sys.stderr, info_string
				self.__qa_dialog__.append_all_to_lbMonitor(recs)
				
				self.__qa_dialog__.report_email_to_indexes()
				
				d.prettyPrint(title='_csv_model.rowsAsRecords')
				importLeadsIntoSalesForce(self,d,email_col_name,isSendEmailsForSalesForce,callback_func=handle_importLeadIntoSalesForce,log=self.__child_frame.textboxLog)
			    else:
				wx_PopUp_Dialog(parent=self.__child_frame,msg='Cannot Process unless you choose something other than the Processing Mode of "%s".' % (self.__child_frame.cbProcessMode_default),title='ERROR',styles=wx.ICON_ERROR)
			else:
			    wx_PopUp_Dialog(parent=self.__child_frame,msg='Cannot Process unless you choose something other than the Processing Mode of "%s".' % (self.__child_frame.cbProcessMode_default),title='ERROR',styles=wx.ICON_ERROR)
		    else:
			resp = wx_PopUp_Dialog(parent=self.__child_frame,msg='No actions have been taken due to your previous responses.  You may try again if you feel some actions should have been taken.',title='INFORMATION',styles=wx.ICON_INFORMATION | wx.CANCEL)
		except Exception, details:
		    _details = _utils.formattedException(details)
		    wx_PopUp_Dialog(parent=self.__child_frame,msg=_details,title='ERROR',styles=wx.ICON_INFORMATION | wx.CANCEL)
	except Exception, details:
	    _details = _utils.formattedException(details)
	    wx_PopUp_Dialog(parent=self.__child_frame,msg=_details,title='ERROR',styles=wx.ICON_INFORMATION | wx.CANCEL)
    
    @threadpool.threadify(_thread_Q)
    def track_qa_for_email(self,email,status='',scored='',validated=''):
	try:
	    appendText(self.__child_frame.textboxLog,'(**) %s' % (ObjectTypeName.objectSignature(self)))
	    data = (email,status,scored,validated)
	    self.__qa_Q__.put_nowait(data)
	except Exception, details:
	    info_string = _utils.formattedException(details)
	    appendText(self.__child_frame.textboxLog,info_string)
    
    @threadpool.threadify(_thread_Q)
    def track_qa_for_validation(self,email,status='',scored='',validated=''):
	try:
	    appendText(self.__child_frame.textboxLog,'(**) %s' % (ObjectTypeName.objectSignature(self)))
	    data = (email,status,scored,validated)
	    self.__validation_Q__.put_nowait(data)
	except Exception, details:
	    info_string = _utils.formattedException(details)
	    appendText(self.__child_frame.textboxLog,info_string)
    
    def _onProcessCompleted(self):
	self.enable_ifPossible()
	self.__child_frame.btnProcess.SetLabel(_symbol_import_leads_button_face)
	self.__child_frame.btnProcess2.Disable()
	d_button_enable_map[_symbol_btnProcess2_button] = False
	self.__child_frame.btnProcess3.SetLabel(_symbol_import_leads_button_face)
	
    def onProcessCompleted(self, runtime):
	self._onProcessCompleted()
	
    def _OnClose(self):
	global _isRunning
	_isRunning = False
	try:
	    if (self.__login_dialog__):
		self.__login_dialog__.Destroy()
		del self.__login_dialog__
	except AttributeError:
	    pass
	self.__child_frame.__taskbar_icon.RemoveIcon()
        self.__child_frame.__taskbar_icon.Destroy()
	self.__child_frame.Destroy()
	del self.__child_frame
	if (_child_process_pid > -1):
	    from vyperlogix.process.killProcByPID import killProcByPID
	    try:
		print 'Killing _child_process_pid of "%s".' % (_child_process_pid)
		killProcByPID(_child_process_pid)
	    except Exception, details:
		print >>sys.stderr, _utils.formattedException(details=details)
	self.__isAppClosed = True
	
    def OnClose(self, event):
	self._OnClose()
	
    def OnExit(self):
	if (not self.__isAppClosed):
	    self._OnClose()
	del self
	_thread_Q.join()
	if (not _isBeingDebugged):
	    sys.stdout.close()
	sys.stderr.close()
	sys.exit()
	
    def Close(self):
	self.OnExit()
	
    def IsShown(self):
	return self.__child_frame.IsShown()
    
    def Show(self):
	self.__child_frame.Show()
    
    def Hide(self):
	self.__child_frame.Hide()
    
    def _close_LoginDialog(self):
	if (self.__login_dialog__ is not None):
	    self.__login_dialog__.Destroy()
	    #self.__child_frame.Enable(True)
	    del self.__login_dialog__
	    print '_sf_login_model.isLoggedIn is "%s".' % (_sf_login_model.isLoggedIn)
	    if (not _sf_login_model.isLoggedIn):
		self._OnClose()
	    
    def OnClose_LoginDialog(self):
	self._close_LoginDialog()
	    
    def _close_MapperDialog(self):
	if (self.__mapper_dialog__ is not None):
	    self.__mapper_dialog__.Destroy()
	    del self.__mapper_dialog__
	    
    def OnClose_MapperDialog(self):
	resp = wx_PopUp_Dialog(parent=self.__child_frame,msg='The .CSV you selected does not have column headers that match the standard processing model therefore you MUST map those unknown .CSV Column Headers (from the Left) to the standard model (on the Right) using the pop-up dialog otherwise there is nothing to do and this program will close.\n\nIf you are sure you want to close this program without taking any actions then click the YES button otherwise click the NO button to return to the dialog from whence you came when you saw this pop-up.',title='YES/NO PROMPT',styles=wx.ICON_INFORMATION | wx.YES_NO)
	if (resp == wx.ID_YES):
	    self._close_MapperDialog()
	    self.enable_ifPossible()
	    self._OnClose()
	    
    def refreshEmailColWidgetFrom(self,l_items):
	self.__child_frame.cbCSVEmailAddressCol.SetItems(l_items)
	if (len(l_items) == 1):
	    self.__child_frame.cbRecordTypes.SetSelection(0)
	else:
	    l = ListWrapper([h.lower() for h in self.__child_frame.cbCSVEmailAddressCol.GetItems()])
	    try:
		i = l.findFirstContaining('email')
	    except UnicodeDecodeError, details:
		info_string = _utils.formattedException(details=details)
		print >>sys.stderr, info_string
	    if (i > -1):
		self.__child_frame.cbCSVEmailAddressCol.SetSelection(i)
	self.__child_frame.cbCSVEmailAddressCol.Show()
	    
    def OnProcess_MapperDialog(self):
	#global _symbol_table
	#try:
	    #d = self.__mapper_dialog__.get_suggestions()
	    #_symbol_table = d.insideOut()
	    #self._close_MapperDialog()
	    #self.refreshEmailColWidgetFrom(_symbol_table.keys())
	#except:
	    #pass
	self._onProcessCompleted()
	d_button_enable_map[_symbol_btnProcess1_button] = False
	d_button_enable_map[_symbol_btnProcess2_button] = False
	d_button_enable_map[_symbol_btnProcess3_button] = True
	self.enable_ifPossible()
	    
    #def onRadio_Staging(self):
	#_sf_login_model.isStaging = True
	    
    #def onRadio_Production(self):
	#_sf_login_model.isStaging = False
	
    def enable_ifPossible(self):
	self.__child_frame.btnProcess.Enable()
	if (d_button_enable_map[_symbol_btnProcess1_button]):
	    self.__child_frame.btnProcess1.Enable()
	else:
	    self.__child_frame.btnProcess1.Disable()
	if (d_button_enable_map[_symbol_btnProcess2_button]):
	    self.__child_frame.btnProcess2.Enable()
	else:
	    self.__child_frame.btnProcess2.Disable()
	if (d_button_enable_map[_symbol_btnProcess3_button]):
	    self.__child_frame.btnProcess3.Enable()
	else:
	    self.__child_frame.btnProcess3.Disable()
	
    def disable_ifPossible(self):
	self.__child_frame.btnProcess.Disable()
	self.__child_frame.btnProcess1.Disable()
	self.__child_frame.btnProcess2.Disable()
	self.__child_frame.btnProcess3.Disable()
	
    def waitForExecutableToBeFound(self):
	if (has_ContactsWalker_exe):
	    self.stopTimer()
	    self.enable_ifPossible()
	    
    def onProcess_LoginDialog(self):
	try:
	    self.__login_dialog__.DisableChildren()
	    _sf_login_model.username = self.__login_dialog__.textUsername.GetValue()
	    _sf_login_model.password = self.__login_dialog__.textPassword.GetValue()
	    _sf_login_model.perform_login(end_point=self.__login_dialog__.textEndPoint.GetValue())
	    if (len(_sf_login_model.lastError) > 0) or (_sf_login_model.sfdc is None):
		self.__login_dialog__.EnableChildren()
		CustomStatusBar._status_bar_notification.append(('SalesForce Login FAILED !',15))
		wx_PopUp_Dialog(parent=self.__child_frame,msg=_sf_login_model.lastError,title='ERROR',styles=wx.ICON_ERROR)
	    else:
		_sf_login_model.use_default_assignment_rule = True
		CustomStatusBar._status_bar_notification.append(('%s' % (_sf_login_model.current_endpoint),15))
		
		fn = oodb.dbx_name('%s.dbx' % (_utils.getProgramName()),_data_path)
		oodb.put_data(fn,_symbol_username,self.__login_dialog__.textUsername.GetValue(),fOut=sys.stderr)
		oodb.put_data(fn,_symbol_endpoint_name,self.__login_dialog__.cbServerEndPoints.GetValue(),fOut=sys.stderr)
		oodb.put_data(fn,_symbol_endpoint_url,self.__login_dialog__.textEndPoint.GetValue(),fOut=sys.stderr)
    
		self._close_LoginDialog()

		from vyperlogix.sf.sf import SalesForceQuery
		sfQuery = SalesForceQuery(_sf_login_model)

		from vyperlogix.sf.leads import SalesForceLeads
		self.__leads = SalesForceLeads(sfQuery)
		
		self.__child_frame.__leads__ = self.__leads
		
		self.__d_recordTypes = self.__leads.recordTypes().insideOut()
		l = self.__d_recordTypes.keys()
		self.__child_frame.cbRecordTypes.SetItems(l)
		if (len(l) == 1):
		    self.__child_frame.cbRecordTypes.SetSelection(0)
		    
		self.__d_leadTypes = self.__leads.leadTypes().insideOut()
		l = self.__d_leadTypes.keys()
		self.__child_frame.cbLeadTypes.SetItems(l)
		if (len(l) == 1):
		    self.__child_frame.cbLeadTypes.SetSelection(0)
		    
		self.__d_leadSources = self.__leads.leadSources()
		l = self.__d_leadSources.keys()
		self.__child_frame.cbLeadSource.SetItems(l)
		if (len(l) == 1):
		    self.__child_frame.cbLeadSource.SetSelection(0)
		    
		self.__d_leadSourceDescriptions = self.__leads.leadSourceDescriptions()
		l = self.__d_leadSourceDescriptions.keys()
		self.__child_frame.cbLeadSourceDescr.SetItems(l)
		if (len(l) == 1):
		    self.__child_frame.cbLeadSourceDescr.SetSelection(0)
		    
		self.__d_leadSourceTypes = self.__leads.leadSourceTypes()
		l = self.__d_leadSourceTypes.keys()
		l = [item for item in l if (item.find('did not') == -1)]
		self.__child_frame.cbLeadSourceDataTypes.SetItems(l)
		if (len(l) == 1):
		    self.__child_frame.cbLeadSourceDataTypes.SetSelection(0)
		    self.__child_frame.cbLeadSourceDataTypes.Disable()
		    self.__child_frame.cbLeadSourceDataTypes.SetToolTipString('Ignore this for now, per Michael on 12-03-2008, "We can revisit this later on..."')
    
		fn = oodb.dbx_name('%s.dbx' % (_utils.getProgramName()),_data_path)
		try:
		    v = oodb.get_data(fn,_symbol_cbRecordTypes,fOut=None)
		    v = v if (not isinstance(v,list)) else v[0]
		    if (v is not None):
			self.__child_frame.cbRecordTypes.SetValue(v)
		except:
		    pass
		try:
		    v = oodb.get_data(fn,_symbol_cbLeadTypes,fOut=None)
		    v = v if (not isinstance(v,list)) else v[0]
		    if (v is not None):
			self.__child_frame.cbLeadTypes.SetValue(v)
		except:
		    pass
		try:
		    v = oodb.get_data(fn,_symbol_cbLeadSource,fOut=None)
		    v = v if (not isinstance(v,list)) else v[0]
		    if (v is not None):
			self.__child_frame.cbLeadSource.SetValue(v)
		except:
		    pass
		try:
		    v = oodb.get_data(fn,_symbol_cbLeadSourceDescr,fOut=None)
		    v = v if (not isinstance(v,list)) else v[0]
		    if (v is not None):
			self.__child_frame.cbLeadSourceDescr.SetValue(v)
		except:
		    pass
		try:
		    v = oodb.get_data(fn,_symbol_cbLeadSourceDataTypes,fOut=None)
		    v = v if (not isinstance(v,list)) else v[0]
		    if (v is not None):
			self.__child_frame.cbLeadSourceDataTypes.SetValue(v)
		except:
		    pass
	    
		self.__child_frame.cbSendEmailsForSalesForce.SetLabel(self.__child_frame.cbSendEmailsForSalesForce.GetLabel().replace('Lead Owners','Developers' if (_sf_login_model.isStaging) else 'Lead Owners'))

		self.__child_frame.Enable()
		self.enable_ifPossible()
		# get the data from SalesForce...
	except Exception, details:
	    _details = _utils.formattedException(details)
	    wx_PopUp_Dialog(parent=self.__child_frame,msg=_details,title='ERROR',styles=wx.ICON_INFORMATION | wx.CANCEL)
	
    def init_salesforce(self):
	try:
	    if (not _sf_login_model.isLoggedIn):
		self.__child_frame.btnToggleLog.Hide()
		self.__child_frame.btnProcess.SetLabel(_symbol_load_csv_button_face)
		self.__child_frame.btnProcess.Hide()
		self.__child_frame.btnProcess1.SetLabel(_symbol_load_csv_button_face)
		self.__child_frame.labelCSVEmailAddressCol.Hide()
		self.__child_frame.cbCSVEmailAddressCol.Hide()
		self.hideLog()

		from vyperlogix.wx.SalesForceLogin import SalesForceLogin
		self.__login_dialog__ = SalesForceLogin(None, 'Login to SalesForce', onProcess_callback=self.onProcess_LoginDialog, onClose_callback=self.OnClose_LoginDialog)

		self.__login_dialog__.Show()
		self.__login_dialog__.CenterOnParent()
		self.disable_ifPossible()
    
		fn = oodb.dbx_name('%s.dbx' % (_utils.getProgramName()),_data_path)
		_username = oodb.get_data(fn,_symbol_username,fOut=None)
		_endpoint_name = oodb.get_data(fn,_symbol_endpoint_name,fOut=None)
		_endpoint_url = oodb.get_data(fn,_symbol_endpoint_url,fOut=None)

		if (_username is not None):
		    self.__login_dialog__.textUsername.SetValue(_username)
		if (_endpoint_name is not None):
		    choices = self.__login_dialog__.cbServerEndPoints.GetStrings()
		    i = misc.findInListSafely(choices,_endpoint_name)
		    if (i > -1):
			self.__login_dialog__.cbServerEndPoints.SetSelection(i)
		if (_endpoint_url is not None):
		    self.__login_dialog__.textEndPoint.SetValue(_endpoint_url)
		
		self.__login_dialog__.Bind(wx.EVT_CLOSE, self.OnClose_LoginDialog)
	except Exception, details:
	    _details = _utils.formattedException(details)
	    wx_PopUp_Dialog(parent=self.__child_frame,msg=_details,title='ERROR',styles=wx.ICON_INFORMATION | wx.CANCEL)
	
    def on_cbRecordTypes_list_callback(self):
	return ['']
	
def main(argv=None):
    global _data_path
    
    if argv is None:
        argv = sys.argv

    _data_path = _utils.appDataFolder(prefix=_utils.getProgramName())
    _utils._makeDirs(_data_path)
    
    _log_path = os.path.dirname(sys.argv[0])

    if (not _isBeingDebugged):
	_stdOut = open(os.sep.join([_log_path,'stdout.txt']),'w')
	sys.stdout = Log(_stdOut)

    _stdErr = open(os.sep.join([_log_path,'stderr.txt']),'w')
    sys.stderr = Log(_stdErr)

    try:
	app = MainFrame(0)
	app.MainLoop()
    except Exception, exception:
	type, value, stack = sys.exc_info()
	formattedBacktrace = ''.join(traceback.format_exception(type, value, stack, 5))
	wx_PopUp_Dialog(parent=None,msg='An unexpected problem occurred:\n%s' % (formattedBacktrace),title='FATAL ERROR',styles=wx.ICON_ERROR)

def exception_callback(sections):
    _msg = 'EXCEPTION Causing Abend.\n%s' % '\n'.join(sections)
    print >>sys.stdout, _msg
    print >>sys.stderr, _msg
    sys.exit(1)

if __name__ == '__main__':
    _isBeingDebugged = _utils.isBeingDebugged
    
    if (not _isBeingDebugged):
	from vyperlogix.handlers.ExceptionHandler import *
	excp = ExceptionHandler()
	excp.callback = exception_callback

    from vyperlogix.misc._psyco import *
    importPsycoIfPossible(func=main,isVerbose=True)

    if (_utils.getComputerName() in l_allowed_computers):
	_utils._isComputerAllowed = _is_running_securely = True # allow the security measures to be b-passed because we are really running in a secure mode...
    else:
	_is_running_securely = is_running_securely()
	_utils.isComputerAllowed(l_domain_names)

    #sys.setappdefaultencoding('ascii')
    main()
