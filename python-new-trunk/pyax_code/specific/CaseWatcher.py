import types
from vyperlogix.classes.CooperativeClass import Cooperative

from vyperlogix.misc import ObjectTypeName

from vyperlogix.hash import lists
from vyperlogix.lists.ListWrapper import ListWrapper

from vyperlogix.misc import LazyImport

from pyax_code.sf_query import asMessage

sfConstant = LazyImport.LazyImport('sfConstant',locals={},globals={})

def dummy():
    pass

class CaseWatcherAPI(Cooperative):
    def __init__(self,sfdc,d_fields,begin_Analysis_callback=dummy,end_Analysis_callback=dummy,count_query_callback=dummy):
	self.__sfdc__ = sfdc
	self.__d_fields__ = d_fields
	self.__begin_Analysis_callback__ = begin_Analysis_callback
	self.__end_Analysis_callback__ = end_Analysis_callback
	self.__count_query_callback__ = count_query_callback

	self.__d_fields_of_interest__ = lists.HashedLists2(self.d_fields)

	self.__s_non_case_fields_of_interest__ = set([k for k,v in self.d_fields.iteritems() if (v.find('Select ') > -1) and (v.find(' where ') > -1)])
	self.__s_case_fields_of_interest__ = set(self.d_fields.keys()) - self.s_non_case_fields_of_interest

	self.self_asMessage = lambda cls, reason:'(%s) %s.' % (ObjectTypeName.objectSignature(cls),reason)
	self.asMessage_for_self = self.self_asMessage
	self.asMessage = asMessage
	
    def _sf_query(self,soql):
	from pyax_code.sf_query import _sf_query
	return _sf_query(self.sfdc,soql,self.begin_Analysis_callback,self.end_Analysis_callback)
    
    def count_query(self):
	cb = self.count_query_callback
	if (type(cb) == types.FunctionType):
	    try:
		cb()
	    except:
		pass

    def getCaseChangesById(self,id):
	self.count_query()
	soql="Select c.CaseId__c, c.ChangedFieldName__c, c.CreatedById, c.CreatedDate, c.Id, c.IsDeleted, c.LastModifiedById, c.LastModifiedDate, c.Name, c.OldFieldValue__c from CaseWatcherChangedField__c c where c.CaseId__c='%s'" % id
	ret = self._sf_query(soql)
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else: 
	    _chg = []
	    for k,v in ret.iteritems():
		_chg.append(v)
	    return (ret.keys(),_chg)
	return None
    
    def getCaseWatcherById(self,id):
	from pyax_code.specific import getCaseWatcherById as soql_getCaseWatcherById
	
	self.count_query()
	d_args = lists.HashedLists2({'sfdc':self.sfdc})
	if (id is not None) and (len(str(id)) > 0):
	    d_args['Id'] = id
	ret = soql_getCaseWatcherById._getCaseWatcherById(d_args,self.begin_Analysis_callback,self.end_Analysis_callback)
	if ret not in sfConstant.BAD_INFO_LIST:
	    if (id is not None) and (len(str(id)) > 0):
		k = ret.keys()[0]
		if (k):
		    v = ret[k]
		    return v
	    else:
		return ret
	return None

    def getComponentById(self,id): 
	self.count_query()
	soql="Select c.Id, c.Name from Component__c c where c.Id='%s'" % id
	ret = self._sf_query(soql)
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else: 
	    k = ret.keys()[0]
	    if (k):
		v = ret[k]
		return v
	return None

    def getAccountById(self,id): 
	self.count_query()
	soql="Select a.Id, a.Name from Account a where a.Id='%s'" % id
	ret = self._sf_query(soql)
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else: 
	    k = ret.keys()[0]
	    if (k):
		v = ret[k]
		return v
	return None
	
    def getAccountParentByAccountId(self,id): 
	self.count_query()
	soql="Select a.Id, a.ParentId from Account a where a.Id='%s'" % id
	ret = self._sf_query(soql)
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else: 
	    k = ret.keys()[0]
	    if (k):
		v = ret[k]
		return v
	return None
    
    def getAccountsByParentId(self,id): 
	self.count_query()
	soql="Select a.Id, a.ParentId from Account a where a.ParentId='%s'" % id
	ret = self._sf_query(soql)
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else: 
	    return ret
	return []
    
    def getAccountTreeById(self,id,partial):
	accts = []
	self.count_query()
	_soql = " or (a.ParentId = '%s')" % (id) if (not partial) else ''
	soql="Select a.Id, a.Name, a.ParentId from Account a where a.Id = '%s'%s" % (id,_soql)
	ret = self._sf_query(soql)
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else: 
	    for item in ret:
		accts.append(item)
	    return accts
	return None

    def getCRLinksById(self,id): 
	self.count_query()
	soql="Select c.Parent_CR__c from CR_Link__c c where c.Tech_Campaign__c='%s'" % id
	ret = self._sf_query(soql)
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else: 
	    return ret
	return None

    def getUserByEmail(self,email):
	self.count_query()
	soql="Select c.ContactStatus__c, c.Email, c.HasOptedOutOfEmail, c.Id, c.Name, c.Portal_Privilege__c, c.Portal_Username__c, c.User__c from Contact c where C.Email='%s'" % email
	ret = self._sf_query(soql)
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else: 
	    d = lists.HashedLists2(ret)
	    return d
	return lists.HashedLists2()

    def _getCaseFieldsList(self):
	fields = [self.d_fields_of_interest[f] for f in list(self.s_case_fields_of_interest)]
	return fields
    
    def csv_getCaseFieldsList(self,prefix,fields):
	csv = ','.join(['%s.%s' % (prefix.replace('.',''),f) for f in fields])
	return csv

    def getCasesByTeamId(self,team_id, time_list): 
	_windowIsoDateTime, windowIsoDateTime = time_list
	self.count_query()
	soql="Select c.Id, c.CaseNumber, c.LastModifiedDate, c.CreatedDate, c.Subject, c.Component_Link__r.Product_Team__c%s from Case c where c.Component_Link__r.Product_Team__c = %s and c.Status != 'Closed' and c.LastModifiedDate >= %s and c.CreatedDate < %s" % (', '+self.csv_getCaseFieldsList('c.',self._getCaseFieldsList()),team_id,windowIsoDateTime,_windowIsoDateTime)
	ret = self._sf_query(soql)
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else:
	    d = lists.HashedLists2(ret)
	    return ret
	return []

    def getCasesByUserId(self,user_id, time_list): 
	_windowIsoDateTime, windowIsoDateTime = time_list
	self.count_query()
	soql="Select c.Id, c.CaseNumber, c.LastModifiedDate, c.CreatedDate, c.Subject%s from Case c where c.OwnerId = '%s' and c.Status != 'Closed' and c.LastModifiedDate >= %s and c.CreatedDate < %s" % (', '+self.csv_getCaseFieldsList('c.',self._getCaseFieldsList()),user_id,windowIsoDateTime,_windowIsoDateTime)
	ret = self._sf_query(soql)
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else:
	    d = lists.HashedLists2(ret)
	    return ret
	return []

    def getCasesByComponentName(self,cname,time_list): 
	_windowIsoDateTime, windowIsoDateTime = time_list
	self.count_query()
	soql="Select c.Id, c.CaseNumber, c.LastModifiedDate, c.CreatedDate, c.Subject%s from Case c where c.Component__c = '%s' and c.Status != 'Closed' and c.LastModifiedDate >= %s and c.CreatedDate < %s" % (', '+self.csv_getCaseFieldsList('c.',self._getCaseFieldsList()),cname,windowIsoDateTime,_windowIsoDateTime)
	ret = self._sf_query(soql)
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else:
	    d = lists.HashedLists2(ret)
	    return ret
	return []

    def getCasesByAccountId(self,id,time_list):
	_windowIsoDateTime, windowIsoDateTime = time_list
	self.count_query()
	soql="Select c.AccountId, c.Id, c.CaseNumber, c.LastModifiedDate, c.CreatedDate, c.Subject%s from Case c where c.Status != 'Closed' and c.LastModifiedDate >= %s and c.CreatedDate < %s and c.AccountId = '%s'" % (', '+self.csv_getCaseFieldsList('c.',self._getCaseFieldsList()),windowIsoDateTime,_windowIsoDateTime,id)
	ret = self._sf_query(soql)
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else:
	    _list = []
	    for rec in ret:
		_list.append(rec)
	    return _list
	return []
    
    def getCaseById(self,id,time_list=(None,None)): 
	_windowIsoDateTime, windowIsoDateTime = time_list
	self.count_query()
	soql="Select c.Id, c.CaseNumber, c.LastModifiedDate, c.CreatedDate, c.Subject%s from Case c where c.Id = '%s' and c.Status != 'Closed'" % (', '+self.csv_getCaseFieldsList('c.',self._getCaseFieldsList()),id)
	if (windowIsoDateTime is not None) and (_windowIsoDateTime is not None):
	    soql += " and c.LastModifiedDate >= %s and c.CreatedDate < %s" % (windowIsoDateTime,_windowIsoDateTime)
	ret = self._sf_query(soql)
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else:
	    return ret
	return None

    def getCaseFieldsById(self,id,fields): 
	self.count_query()
	soql_fields = ', '.join(['c.%s' % (self.d_fields_of_interest[aField]) for aField in fields if (aField in self.s_case_fields_of_interest)])
	if (len(soql_fields) > 0):
	    soql_fields = ', %s' % soql_fields
	soql="Select c.Id, c.CaseNumber%s from Case c where c.Id = '%s'" % (soql_fields,id)
	ret = self._sf_query(soql)
	other_fields = [aField for aField in fields if (aField in self.s_non_case_fields_of_interest)]
	_ret = []
	for other in other_fields:
	    other_soql = self.d_fields_of_interest[other]
	    if (other_soql):
		other_toks = ListWrapper(other_soql.split())
		i_from = other_toks.find('from')
		i_where = other_toks.find('where')
		other_prefix = ''
		if (i_where > i_from) and ((i_where - i_from - 1) > 1):
		    other_prefix = other_toks[i_from+2]
		    if (not any([t.find('%s.' % (other_prefix)) > -1 for t in other_toks])):
			other_prefix = '' # sanity check to make sure we have the right token
		_soql=other_soql % (id)
		_ret.append(self._sf_query(_soql))
	if ret in sfConstant.BAD_INFO_LIST:
	    pass
	else:
	    return (ret,_ret)
	return None

    def sfdc():
        doc = "sfdc"
        def fget(self):
            return self.__sfdc__
        return locals()
    sfdc = property(**sfdc())
    
    def d_fields():
        doc = "d_fields"
        def fget(self):
            return self.__d_fields__
        return locals()
    d_fields = property(**d_fields())
    
    def d_fields_of_interest():
        doc = "d_fields_of_interest"
        def fget(self):
            return self.__d_fields_of_interest__
        return locals()
    d_fields_of_interest = property(**d_fields_of_interest())
    
    def s_non_case_fields_of_interest():
        doc = "s_non_case_fields_of_interest"
        def fget(self):
            return self.__s_non_case_fields_of_interest__
        return locals()
    s_non_case_fields_of_interest = property(**s_non_case_fields_of_interest())
    
    def s_case_fields_of_interest():
        doc = "s_case_fields_of_interest"
        def fget(self):
            return self.__s_case_fields_of_interest__
        return locals()
    s_case_fields_of_interest = property(**s_case_fields_of_interest())

    def count_query_callback():
        doc = "count_query_callback"
        def fget(self):
            return self.__count_query_callback__
        return locals()
    count_query_callback = property(**count_query_callback())

    def begin_Analysis_callback():
        doc = "begin_Analysis_callback"
        def fget(self):
            return self.__begin_Analysis_callback__
        return locals()
    begin_Analysis_callback = property(**begin_Analysis_callback())

    def end_Analysis_callback():
        doc = "end_Analysis_callback"
        def fget(self):
            return self.__end_Analysis_callback__
        return locals()
    end_Analysis_callback = property(**end_Analysis_callback())

