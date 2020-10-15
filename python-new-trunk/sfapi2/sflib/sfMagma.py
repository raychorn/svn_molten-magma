""" Python API for sForce 3.0 
    - Customizable wrapper around sfBase3.py classes to create entity specific classes
    - SFEntity class should hold only entity global methods
    - SF<EntityName> should hold methods specific to that entity
    
 ToDo:
    - Create Branch specific classes
    - Create Branch/CR workflow methods
    - Create many other cool things that cause useful sForce data perturbations.
    
           Chip Vanek, June 1st, 2004
"""
# Subversion properties
#
# $LastChangedDate: 2007-06-01 13:56:05 -0700 (Fri, 01 Jun 2007) $
# $Author: ramya $
# $Revision: 1528 $
# $HeadURL: http://capps.moltenmagma.com/svn/sfsrc/trunk/sfapi2/sflib/sfMagma.py $
# $Id: sfMagma.py 1528 2007-06-01 20:56:05Z ramya $
import sys, time, os
import urlparse
import StringIO, getopt
import copy, re
import traceback
from types import ListType, TupleType, DictType, DictionaryType, StringType, StringTypes
from optparse import OptionParser
from sfBase3 import *
from sop import sfEntities, SFEntitiesMixin, SFUtilityMixin, SFTestMixin
from sfConstant import *
from mailServer import *
import mail

###########################################################
#  Global constants - will move to util.py and import
###########################################################
version = 3.0
ISO_8601_DATETIME = '%Y-%m-%dT%H:%M:%S'
seqTypes = [ListType, TupleType]
dictTypes = [DictType, DictionaryType]
strTypes = [StringType, StringTypes]
badInfoList = BAD_INFO_LIST

class SFMagmaEntity(SFEntityBase):
    """ Simple base class that is aware of an active sForce connection but
        does not implement all of the connection oriented and data management APIs
        
        Subclass this object to create entity specific data management and business
        logic methods.
    """
    badInfoList = BAD_INFO_LIST
    
    def __init__(self, entity, data=[{}], action=None, sfTool=None, debug=0):
        """  If an active tool object is not passed in then a connection is created.   """
        SFEntityBase.__init__(self, entity, data=data, action=action, sfTool=sfTool, debug=debug)
        
    def setData(self, data, reset=False):
        """ set data with any object specific filtering  
            data is a list of entity-data tuple [('entity', {data})]
            multi-entity objects are expected to be a list of these tuples.
            This overwrite data with the passed in value
        """
        SFEntityBase.setData(self, data, reset)
        
    def getData(self, entity='all', id=''):
        """ get data list, data is a list of entity-data pairs [('entity', {data})]
            multi-entity objects are expected to be a list of these tuples.
            - list of data dictionaries if just entity provided
            - specific data dictionary if id is in entity list
        """
        return SFEntityBase.getData(self, entity, id)

    def setAction(self, action):
        """ set action with any object specific triggered actions  """
        self.action = action
    
    def updateSF(self, data=None, nullEmpty=False):
        """ Update sForce with all the data in this object
            This data may update multiple entities in sForce and may null fields
            ToDo: update all similar entities in the same call
        """
        msg = SFEntityBase.updateSF(self, data=None, nullEmpty=False)
        if msg in ['fail']:
            print self.lastRet
        return msg

            
    def showData(self, data=None, entity='', target='console'):
        """ display data loaded in this object """
        if target in [None, '','console']:
            self.sfb.showDataConsole(data, entity)
        elif target in ['user']:
            self.sfb.showDataUser(data, entity)
        else:
            print 'not implemented yet'

        

class SFMagmaTool(sForceApi3):
    """ This class provides entity global capabilities
        subclass this class and extend or replace methods to suit your needs
    """
    def __init__(self, username=None, upass=None, dlog=None, debug=0, logname='sf3.base', setupLog=True):
        """ Creates the API access object and logs in as admin user
        """
        sForceApi3.__init__(self, username=username, upass=upass, dlog=dlog, debug=debug, logname=logname)
        self.setupBase(setupLog=setupLog)
        self.setupChild()
    

    def setupBase(self, setupLog=True):
        """
        setup the basic structures need to query the SalesForce API
        pass setupLog=False to NOT set up a suite of loggers at this time.
        This allows for manually calling setLogger and passing in the loggers
        to use.
        """
        self.taskRecordTypeMap = {'MOD':'01230000000002v', 'Generic Task':'01230000000002w'}
        self.scm_submissions_root = '/magma/scm-release/submissions'
        self.scm_shadow_root = '/magma/scm-release/submissions'
        self.scm_drop_root = '/home/sfscript/data/drop'

        self.sfdc_base_url = self.sfc.get('main', 'sf_base_url')
        self.from_addr = self.sfc.get('main', 'from_addr')
        self.smtp_server = self.sfc.get('email', 'smtp_server')
        self.domain = self.sfc.get('email', 'domain')

        if setupLog is True:
            self.setLogger()
    ## END setupBase(self, username, upass, logger)

    def mailServer(self):
        if not hasattr(self, 'mailSrvH'):
            self.mailSrvH = MailServer(logger=self.log)

        return self.mailSrvH

    def mailServer2(self):
        if not hasattr(self, 'mailSrvH2'):
            self.mailSrvH2 = mail.MailServer(logger=self.log)

        return self.mailSrvH2

    def setupChild(self):
        """ add methods in child classes"""
        pass

    badInfoList = BAD_INFO_LIST
    trialAddrList = ['rhorn@molten-magma.com']

    ##################################################################################################
    #  Load entity type data structures for use by entity specific calls
    #    Access this info using calls like
    #        all fields  = self.getEntityMap('entityName')['fields']
    #        SOQL filter = self.getEntityMap('entityName')['filters']
    #        field_Info  = self.getEntityMap('entityName')['fieldInfo'].get('ent.fieldName')
    #        type of field = field_Info.get('type')
    #
    ##################################################################################################
    def getEntityMap(self, entity, reset=False):
        """ main accessor for getting entity information
        """
        if self.debug > 2: print 'Information for %s loaded %3d secs ago' %(entity, self.em.getAge(entity))
        if self.em.isStale(entity):
            if self.debug > 2: print 'Updating sop for %s' %entity
            self.setEntityMap(entity)
        return self.em.getEntity(entity, reset)
  
    def getEntities(self):
        """ get the latest entitiy list
        """
        if len(self.entityList) < 10:
            self.entityList = self.describeGlobal()
        return self.entityList
    

    def getDefaults(self, uid='', entity='all'):
        """ return a dictionary of default field values that can be used by any entity
            UserID and entity specific dictionaries is not implemented yet but should be
        """
        allAny = {'OwnerId':'%s' %self.uid
                 ,'Priority': 'Low'
                 }
        return allAny

    def getPicklist(self, etable, efield):
        """ for a given SFDC etable (exists), find efield (exists), 
            check if it is a picklist, extract picklist values (dictionary)
            return picklist keys as a list 
        """
        # Misha
        picklist = []
        em = self.getEntityMap(etable)
        emfi = em.get('fieldInfo')
        emf = emfi.get(efield)
        picklist_dict = emf.get('picklistValues')
        picklist = picklist_dict.keys()
        return picklist

        
    ##################################################################################################
    #         Modifying Data calls: update, create, delete
    ##################################################################################################
    def update(self, entity, data=[{}], nullEmpty=False):
        """ basic wrapper around update, entity and data is required, id must be in data
            ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'', 'req':'', 'result':[]}
        """
        ret = self.updateBase(entity, data=data, nullEmpty=nullEmpty)

        self.lastRet = ret
        if ret['success'] is True:
            if self.debug >1: print ret['msg']
            return ret['result']
        else:
            self.lastResult = ret['result']
            self.lastError  = ret['errMsg']
            if self.debug >0: print ret['errMsg']
            return ret['errCode']


    def create(self, entity, data=[{}], nullEmpty=False):
        """ basic wrapper around create, entity and data is required
            ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'', 'req':'', 'result':[]}
        """
        ret = self.createBase(entity, data=data, nullEmpty=nullEmpty)        
        self.lastRet = ret
        if ret['success'] is True:
            if self.debug >1: print ret['msg']
            return ret['result']
        else:
            self.lastResult = ret['result']
            self.lastError  = ret['errMsg']
            if self.debug >0: print ret['errMsg']
            return ret['errCode']


    def delete(self, ids=[]):
        """ basic wrapper around delete
            ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'', 'req':'', 'result':[]}
        """
        ret = self.deleteBase(ids)
        self.lastRet = ret
        if ret['success'] is True:
            if self.debug >1: print ret['msg']
            return ret['result']
        else:
            self.lastResult = ret['result']
            self.lastError  = ret['errMsg']
            if self.debug >0: print ret['errMsg']
            return ret['errCode']
        

    ######################################################################
    #  SOSL query methods
    #  SELECT [List of Field Names] IN EntityName 
    #     WHERE FieldName = 'value' AND FieldName >= 'value' OR FieldName != ''
    #
    ######################################################################
    def query(self, entity, where=[('LastName','like','vanek',)], sc='', soql=None, limit=200):
        """ search sForce using SOQL with some query building shortcuts  using entity name 
            and a set of shortcut strings for common list of return fields (fewer fields is faster!)
            - If where is a string it will be passed to getSQOLWhereShortcut(where) to return where clause
            - sc will be passed to getSOQLEntityShortcut(sc) to return entity list (and rest of select clause)
                - if sc is empty then all fileds will be returned for entity
            
            ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'', 'req':soql, 'result':[]}
        """
        ret = self.queryBase( entity, where=where, sc=sc, soql=soql, limit=limit)
        self.lastRet = ret                
        if ret['success'] is True:
            if self.debug >1: print ret['msg']            
            return ret['result']
        else:
            self.lastResult = ret['result']
            self.lastError  = ret['errMsg']
            mg=ret['msg']                 
            mgLen=mg.find('No Results')
            if mgLen != -1:                
                return []
            if self.debug >1: print ret
            if self.debug >0: return ret['errMsg']
            return ret['errCode']
            
    def retrieve(self, ids, entity, fieldList='all', allowNulls=False):
        """ return data dictionaries for list of ids, used allowNulls to return empty values
            Provide list of ids along with a list of fields you want back
    
            results are returned as a keys of the returned dictionary (as below)
            ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'', 'req':ids, 'result':[]}
        """
        if fieldList == 'all':
            fieldList = self.getEntityMap(entity)['fields']
        ret = self.retrieveBase(ids, entity, fieldList=fieldList, allowNulls=allowNulls)
        self.lastRet = ret
        if ret['success'] is True:
            if self.debug >1: print ret['msg']
            return ret['result']
        else:
            if self.debug >0: print ret['errMsg']
            return ret['errCode']


    def getUpdated(self, entity, start=None, end=None):
        """ return data dictionaries for all entity items modified between the start and end times
            Provide start and end time as DateTime object or sec since epoch or string as #####
            results are returned as a list in the results key of the returned dictionary (as below)
            ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'', 'req':ids, 'result':[]}
        """
        ret = self.getUpdatedBase(entity, start=start, end=end)
        self.lastRet = ret
        if ret['success'] is True:
            if self.debug >1: print ret['msg']
            return ret['result']
        else:
            if self.debug >0: print ret['errMsg']
            return ret['errCode']

    
    def getSQOLWhereShortcut(self, sc=''):
        """ convert some shortcut strings into valid WHERE clause
             Output is a a list of clause triplets and operators [and, or, not]
        """
        if sc in [None, '']: sc = 't1'
        if sc in ['t1']:
            sc = [['Email','like','ab@yahoo.com'], 'and',['CompanyName','like', 'ab'], 'and',  ['Title', '!=', '']]
        elif sc in ['broadcom']:
            sc = [['Subject','like','%com%']]
        return sc

    ##################################################################################################
    #  Magma sForce data specific methods
    #
    ##################################################################################################
    def getSOQLEntityShortcut(self, sc, entity='Case'):
        """ Convert a shortcut string into a valid SOQL string
          format: SELECT fieldList from objectType 
        """
        allCont = self.getEntityMap('Contact')['filters']
        allUser = self.getEntityMap('User')['filters']
        allCase = self.getEntityMap('Case')['filters']
        allTask = self.getEntityMap('Task')['filters']
        c1  = ('FirstName', 'LastName', 'Email', 'Last_Report__c', 'Mods_Approved_By__c', 'Id')
        u1  = ('Email', 'FirstName', 'LastName', 'Phone', 'Reports_To__c', 'Id')
        user= ('Alias', 'City', 'CompanyName', 'Country', 'Department',
               'Division', 'Email', 'EmployeeNumber', 'Ex_Employee__c',
               'FirstName', 'Id', 'IsActive', 'LastLoginDate', 'LastName',
               'MobilePhone', 'Phone', 'PostalCode', 'Reassign_To__c',
               'Reports_To__c', 'State', 'TimeZoneSidKey', 'Title',
               'Username', 'UserRoleId')
        cont= ('AccountId', 'Business_Unit__c', 'ContactStatus__c',
               'ContactsWithoutEmpNum__c', 'Department', 'Dept__c', 'Email',
               'EmployeeNumber__c', 'FirstName', 'Id', 'LastName',
               'MailingPostalCode', 'MailingState', 'Mods_Approved_By__c',
               'RecordTypeId', 'ReportsToId', 'Title',
               'Branches_Approved_By_User_ID__c')
        mod = ('BranchLabel__c', 'CodeStream__c', 'Developer__c', 'Id',
               'Mod_Owner__c', 'Priority', 'Status', 'WhatId')
        cr1 = ('CaseNumber', 'Code_Streams_Priority__c', 'Status', 'Subject',
               'Id', 'LastModifiedDate', 'ClarifyID__c')
        com = ('Subject', 'Id' )
        min = ('Id', 'OwnerId','LastModifiedDate')
        brcrl = ('Id', 'Case__c', 'Task_Branch__c')

        if type(sc) in [ListType, TupleType]:
            fieldList = []
            fieldList.extend(sc)
            if 'Id' not in fieldList:
                # ensure that we always select 'Id'
                fieldList.append('Id')
            soql = 'SELECT %s from %s' %(','.join(fieldList), entity)
        elif sc in ['contacts','contact']:   
            soql = 'SELECT %s from Contact'%','.join(cont)
        elif sc in ['c1']:   
            soql = 'SELECT %s from Contact'%','.join(c1)
        elif sc in ['call']:   
            soql = 'SELECT %s from Contact'%','.join(allCont)
        elif sc in ['uall']:   
            soql = 'SELECT %s from User'%','.join(allUser)
        elif sc in ['user']:   
            soql = 'SELECT %s from User'%','.join(user)
        elif sc in ['mall']: 
            soql = 'SELECT %s from Task' %','.join(allTask)        
        elif sc in ['mod']: 
            print 'ERROR should not be using this shortcut\n'
            soql = 'SELECT %s from Task' %','.join(mod)
        elif sc in ['cr1']: 
            soql = 'SELECT %s from Case'%','.join(cr1)
        elif sc in ['case']: 
            soql = 'SELECT %s from Case'%','.join(allCase)
        elif sc in ['com']: 
            soql = 'SELECT %s from %s' %(','.join(com), entity)
        elif sc in ['min']:
            soql = 'SELECT %s from %s'%(','.join(min), entity)
        elif sc in ['brcrl']: 
            soql = 'SELECT %s from Branch_CR_Link__c'%','.join(brcrl)
        else:
            print 'Unknown return entity shortcut %s' %sc
            soql = ''
            
        if self.debug >1: print 'SOQL for %s is: %s' %(sc, soql)
        return soql

    ##################################################################################################
    #  SOSL query methods
    #    FIND {searchString} IN 'ALL FIELDS|NAME FIELDS|EMAIL FIELDS|PHONE FIELDS'
    #        RETURNING 'FieldSpec' LIMIT #
    #
    #   NOTE: search is very slow, up to 10 times slower then query.  You have been warned
    ##################################################################################################
    def search(self, sterm, retsc=None, scope='ALL FIELDS', sosl=None, limit=200):
        """ search sForce using SOSL >OR< a search term and a return field shortcut
            - retsc should be a string passed to getSOSLFieldSpec(retsc) to return formatted return fields

            results are returned as a keys of the returned dictionary (as below)
            ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'', 'req':ids, 'result':[]}
        """
        ret = self.searchBase( sterm, retsc=retsc, scope=scope, sosl=sosl, limit=limit)
        self.lastRet = ret
        if ret['success'] is True:
            if self.debug >1: print ret['msg']
            return ret['result']
        else:
            if self.debug >0: print ret['errMsg']
            return ret['errCode']


    def getSOSLFieldSpec(self, shortcut):
        """ Convert a shortcut string into a valid SOSL FieldSpec string
        """
        c1 = {'Contact':['FirstName', 'LastName', 'Email', 'Last_Report__c', 'Mods_Approved_By__c', 'Id', 'Branches_Approved_By_User_ID__c']}
        u1 = {'User':['Email', 'FirstName', 'LastName', 'Phone', 'Reports_To__c', 'Id']}
        a1 = {'Account':['Customer_Support_Alias__c', 'CustomerID__c', 'Name', 'Purch_License_Expire_Date__c'
                        , 'Purchased_License_Start_Date__c', 'Purchased_Licenses__c', 'Id']}
        cr1 = {'Case':['CaseNumber', 'Priority', 'Status', 'Id', 'OwnerId', 'Subject']}
        mod = {'Task':['BranchLabel__c', 'CodeStream__c', 'Developer__c', 'Id', 'Mod_Owner__c', 'Priority', 'Status', 'WhatId']}
        fs = {}
        if shortcut in ['contacts','c1']:  fs = c1
        elif shortcut in ['mod','m1']:     fs = mod
        elif shortcut in ['case','cr']:    fs = cr1
        elif shortcut in ['people','p1']:  
            fs.update(c1)
            fs.update(u1)
        else:
            fs.update(c1)
            fs.update(u1)
            fs.update(a1)
            fs.update(cr1)
            fs.update(mod)
        if self.debug>1: print 'retFields is: %s' %fs
        return fs

    
    ##################################################################################################
    #  Entity access methods with any data validity checks
    ##################################################################################################
    sfAdminIDs  = ['00530000000cBrz','00530000000c9tk','00530000000cNw3',
                   '00530000000c3Va','00530000000cAY7']    
    def getCrById(self, crId):
        """ get all CR Info using the sfId """
        if crId in [None,'']:
            self.setLog('getCrById: called with empty crId','error')
            return {}
        res = self.retrieve([crId], 'Case', fieldList='all',
                            allowNulls=False)
        if res in badInfoList:
            return {}
        return res[0]
        
    def getCrByNum(self, crNum):
        """ get all CR Info using the CR Number
        """
        try:
            crNumInt = int(crNum)
            crPadded = (8 - len(crNum))*'0' + crNum
        except: return {}
        clarify = False

        # No longer assume CR number < 23600 is clarify. 11/5/2004
        where = [['CaseNumber','like',crPadded]]

        res = self.query('Case', where, sc='all') # ToDo limit for performance
        if res in badInfoList:
            msg = 'getCrByNum returned %s for crNum:%s crPadded:%s clarify:%s' %(res,crNum,crPadded,clarify)
            if clarify:
                self.setLog(msg,'warn')
                where = [['CaseNumber','like',crPadded]]
                res = self.query('Case', where, sc='all')
                if res not in badInfoList:
                    self.setLog('getCrByNum: returning < 23600 as crnum:%s'%crNum,'warn')
                    return res[0]
                    
            self.setLog(msg,'error')
            if hasattr(self, 'lastResult'): 
                print 'ERROR:%s\n    Last result:%s'%(msg,self.lastResult)
                if hasattr(self, 'lastError'): print '    Last error:%s'%self.lastError
            return {}
        return res[0]

    def getCrNumByCrId(self, crId):
        """ get crNum from CR Id """
        crInfo = self.getCrById(crId)
        crNum =  crInfo.get('CaseNumber',0)
        return '%s'%int(crNum)

    def getActiveCRs(self, daysAgo=5.0):
        """ get all of the CRs modified since daysAgo """
        result = []
        secsAgo = 60*60*24*daysAgo
        fromSecs = time.time()-secsAgo
        dateStr = self.getAsDateTimeStr(fromSecs)
        where = [['recordTypeID','=','01230000000001Y'],'and',['LastModifiedDate','>',dateStr]]
        queryList = self.query('Case', where=where, sc='cr1')
        if queryList in self.badInfoList:
            print 'getActiveCRs Result: NO CRs Found within the last %s days'%daysAgo
            return result
        result = []
        for info in queryList:
            try:
                print '%5s %5s %11s %22s %s %s'%(int(info.get('CaseNumber')),info.get('ClarifyID__c'),info.get('Code_Streams_Priority__c') \
                                                       ,info.get('Status'), info.get('LastModifiedDate'), info.get('Subject')[:80])
                result.append(info)
            except Exception, e:
                print 'Error %s Skipping the processing of %s'%(e, info   )
        print 'Found %s CRs'%(len(result))
        return result

    def getCrOriginatorByCrNum(self, crNum):
        """ resolve the crInfo, call getCrOriginator, then return Originator UserID """
        crInfo = self.getCrByNum(crNum)
        if crInfo in [None,'',{}]: 
            return ''                   # whaaa
        return self.getCrOriginator(crInfo)

    def getCrOriginatorByCrId(self, crId):
        """ resolve the crInfo, call getCrOriginator, then return Originator UserID """
        crInfo = self.getCrById(crId)
        return self.getCrOriginator(crInfo)

    def getCrOriginator(self, crInfo):
        """ get the right originator ID for a CR 
            - check for admin ID and queues
        """
        if crInfo in [None,'',{}]: return ''
        creatorID = crInfo.get('CreatedById')
        if creatorID not in self.sfAdminIDs and \
               self.getId15(creatorID) not in self.sfAdminIDs:
            ownerID = creatorID
        else:
            ownerID = crInfo.get('OwnerId')
            if ownerID[:3] == '00G':
                ownerID = ''
        
        if self.getId15(ownerID) in self.sfAdminIDs or ownerID in [None,'']:
            # clarify originator
            clarifyOriginatorName = crInfo.get('Originator__c',',')
            first, last = clarifyOriginatorName.split(',')
            where = [['LastName','like',last],'and',['FirstName','like',first]]
            userList = self.query('User', where)

            if userList not in BAD_INFO_LIST:
                user = userList[0]
                ownerID = user.get('Id','')

        if self.getId15(ownerID) in self.sfAdminIDs or ownerID in [None,'']:
            # fall back to contact
            contactId = crInfo.get('ContactId')
            contactInfo = self.getContactById(contactId)
            ownerID = contactInfo.get('Contact_User_Id__c','')

        if self.getId15(ownerID) in self.sfAdminIDs or ownerID in [None,'']:
            # default to soft error default uid and complain to log
            self.setLog('getCrOriginator cr:%s owned/created by sfAdmin or Queue, no originator or contact'%crInfo.get('CaseNumber'),'error')
            ownerID = self.sfc.get('main','default_soft_uid')

        ownerID = self.cascadeToActiveUser(ownerID)

        return ownerID

    ############################################################################################################
    #   CR and Task Branch global methods
    ############################################################################################################
    def getStatusMap(self):
        """ get a ordered list of possible MOD statuses """
        if hasattr(self, 'statMap'): return self.statMap
        from sfTaskBranchStatusMap import SFTaskBranchStatus
        sfMapObj = SFTaskBranchStatus()
        statMap = sfMapObj.getStatusMap()
        self.statMap = statMap
        return self.statMap

    def setCRcsPriority(self, CR, csPriority):
        """ set the csPriority on the CR
        """
        crID = CR.get('id')
        crNum = int(CR.get('CaseNumber'))
        print '    CR:%s -> Setting csPriority to %s' %(crNum, csPriority)
        data = {'id':crID, 'Code_Streams_Priority__c':csPriority}
        sfID = self.update('Case', [data])
        return sfID

    def getCRcsPriority(self, crStreamStr='', CR={}):
        """ get the csPriority from a string or the CR info
        """
        if crStreamStr in [None,'']:
            if CR in [None,'',{}]: return []
            crStreamStr = CR.get('Code_Streams_Priority__c')
        if crStreamStr in [None,'']:
            return []
        crStreamList = []
        streamRE = re.compile(r'\d+(\.\d+)?$') # match a stream number
        for stream in crStreamStr.split(','):
            stream = stream.strip()
            if streamRE.match(stream):
                crStreamList.append(stream)
            else:
                continue
        return crStreamList

    def getCrPriority(self, cr={}):
        """ get the CR Priority which is an amalgam of the Priority and
        Expedited Priority fields
        """
        pri = cr.get('Priority', '3 - Medium')
        expPri = cr.get('ExpeditedPriority__c', '2 - No')

        if pri == "1 - Expedite":
            if expPri == "2 - No":
                return pri
            else:
                return expPri
        else:
            return pri
    ## END getCrPriority
       
    ##################################################################################################
    #  User and Contact access methods
    ##################################################################################################
    magmaEmployeeContactID = '0123000000001tr'
    magmaDeveloperContactID = '0123000000000sj'
    whereMagmaContacts = " and (RecordTypeId = '0123000000000sj' or RecordTypeId = '0123000000001tr')"
    
    def getUserByAlias(self, alias):
        """ return user information using alias or empty dictionary 
            Note aliases are only 8 char long 
        """
        aliasLookup = alias[:8]
        res = self.query('User',['Alias','=',alias])  # use = ?
        if res in badInfoList:
            email = '%s@molten-magma.com'%alias
            res = self.query('User',['Email','=',email])  # use = ?
            if res in badInfoList:
                print 'Cannot find User with alias:%s or email:%s' %(aliasLookup,email)
                return {}
        return res[0]

    def getContactById(self, contactId):
        contactInfo = {}
        if contactId in BAD_INFO_LIST:
            return contactInfo

        res = self.retrieve([contactId], 'Contact')
        if res in BAD_INFO_LIST:
            return contactInfo
        else:
            return res[0]
        
    def getContactByUserId(self, userId):
        """ return contact information using user sfid or empty dictionary """
        result = {}
        if userId in [None,'']: return result        
        userId = self.getId18(userId)
        key = 'Contact:%s' %userId
        info = self.getCache(key)        
        
        if info.get('Id','') != '': 
            self.setLog('getContByUID cached %s %s from %s'%(info.get('FirstName'),info.get('LastName'),userId),'info3')
            return info
            
        res = self.query('Contact',['Contact_User_Id__c','=',userId],'fields')  # userId value is stored as uid18        
        if len(res) > 1:
            msg = 'getContactByUserId: Multiple Contacts found for uid:%s \n%s'%(userId,res)
            self.setLog(msg, 'warn')
            print msg
        elif res in badInfoList:
            pass
        elif not res[0].has_key('Branches_Approved_By_User_ID__c'):
            if res[0].has_key('Reassign_To_User_ID'):
                
                return res[0]
            if type(res[0]) == type({}):
                name = '%s %s'%(res[0].get('FirstName',''),res[0].get('LastName',''))
            msg = 'getContactByUserId: Branches_Approved_By_User_ID__c Not Found in Contact for %s'%(name)
            msg += '\n     uid:%s res:%s, will try uid.empNum -> cont.empNum'%(userId,res)
            self.setLog(msg, 'warn')
        if res not in badInfoList:
            self.setCache(key,res[0])
            return res[0]
        if self.debug>1: print 'WARN:getContactByUserId No Contact found for userID:%s' %userId
        
        res = self.query('User', ['Id','=',userId])
        if res in badInfoList:
            self.setLog('getContactByUserId: no user info for uid:%s err:%s'%(userId,res), 'error')
            return result
        userInfo = res[0]
        userEmpNum = userInfo.get('EmployeeNumber', '')
        if userEmpNum in [None,'']: 
            self.setLog('getContactByUserId: no employee number for uid:%s'%userId,'error')
            return result
        if self.debug >2: print 'Found employee number %s for %s %s' %(userEmpNum,userInfo.get('FirstName'),userInfo.get('LastName'))
        res = self.getContactByEmpNum(userEmpNum)
        if res not in badInfoList:
            self.setCache(key,res)
        return res
        
    def getContactByEmpNum(self, userEmpNum):
        """ Get full contact information using employee number"""
        result = {}
        where = [['EmployeeNumber__c','like',userEmpNum]]
        where.append(self.whereMagmaContacts)
        userContact = self.query('Contact', where, sc='all')
        if userContact in badInfoList:
            self.setLog('getContactByEmpNum: no Contact found for enum:%s'%(userEmpNum),'error')
            return userContact
        if len(userContact) > 1:
            self.setLog('getContactByEmpNum: Found multiple contacts with empnum:%s'%(userEmpNum),'error')
        result = userContact[0]
        return result    
        
    def getUserByEmail(self, email):
        """ get user information using email
            return first of multiple records or {}
        """
        if email in [None,'']: return {}
        key = 'User:%s'%email
        info = self.getCache(key)
        if info.get('Id','') != '': 
            return info
        res = self.query('User',['Email','like',email])
        if res in badInfoList:
            alias = email.split('@')[0]
            res = self.query('User',['Alias','like',alias])
            if res in badInfoList:
                self.setLog('getUserByEmail Cannot find User with alias:%s or email:%s' %(alias,email),'error')
                return {}
        elif len(res) > 1:
            self.setLog('getUserByEmail found multiple users for %s, returning the first'%email,'warn')
        self.setCache(key,res[0])
        return res[0]

    def getUserById(self, uid):
        """ get user information using uid
            return first of multiple records or {}
        """
        if uid in [None,'']: return {}
        key = 'User:%s'%uid
        info = self.getCache(key)
        if info.get('Id','') != '': 
            return info
        res = self.query('User',['Id','=',uid])
        if res in badInfoList:
            self.setLog('getUserById Cannot find User with uid:%s' %(uid),'error')
            return {}
        self.setCache(key,res[0])
        return res[0]

    def cascadeToActiveUser(self, userId):
        """
        If a user is active, return the user ID.

        If inactive, return the user ID from the associated contact record
        Reassign To field.

        If that field is not filled in, return the soft default user ID.
        If some other problem prevents resolution, return the default user ID.
        """
        softDefault = self.sfc.get('main','default_soft_uid')
        activeUserId = softDefault
        
        userFields = ('Id','IsActive','User_Contact_Id__c')
        contactFields = ('Id','Reassign_To_User_ID__c')

        #if userId in BAD_INFO_LIST:
        #    activeUserId = softDefault

        uRes = self.retrieve([userId], 'User', userFields)
        if uRes not in BAD_INFO_LIST:
            # check if the user is active
            userInfo = uRes[0]
            isActive = userInfo.get('IsActive', 'false')

            if isActive == 'true':
                activeUserId = userInfo.get('Id')
            else:
                # not active, check the contact for reassign user
                contactId = userInfo.get('User_Contact_Id__c','')
                cRes = self.retrieve([contactId], 'Contact', contactFields)

                if cRes not in BAD_INFO_LIST:
                    contactInfo = cRes[0]
                    reassignUserId = contactInfo.get('Reassign_To_User_ID__c',
                                                     None)

                    if reassignUserId is not None:
                        activeUserId = self.cascadeToActiveUser(reassignUserId)
                        pass
                    pass
                pass
            pass

        return activeUserId
    
    
    #######################################################################
    #  PE and Engineering Manager Approval Methods
    #######################################################################
    def getPEIdByComp(self, lookup):
        """ get a PE userID from a component lookup string
            return userId string or ''
        """
        result = ''
        if lookup in [None,'']: return result
        origlookup = lookup
        lookup = lookup.lower()
        
        compInfo = self.getComponent(lookup)
        if compInfo in BAD_INFO_LIST:
            print "getPEIdByComp: no component found for lookup >%s< (orig >%s<)" %(lookup, origlookup)
        tid = compInfo.get('Product_Team__c','')
        if tid in badInfoList:
            msg = 'getPEIdByComp No component found for %s' %lookup
            self.setLog(msg,'error')
        userLinks = self.getUserLinksByTeamId(tid,lookup)
        if userLinks in badInfoList:
            msg = 'Error: getPEIdByComp for %s, No UserLinks found for teamID %s' %(lookup, tid)
            self.setLog(msg,'error')
        for userLinkInfo in userLinks:
            linkType = userLinkInfo.get('Link_Type__c','')
            if linkType == 'PE Approver':
                result = userLinkInfo.get('User__c','')
        return result


    def getMgrIdByDevId(self, devId, devContInfo=None):
        """ get a Manager userID from a developer userId
            return userId string or ''    
        """        
        result = self.defaults.get('errorUId')
        if devContInfo == None:
            devContInfo = self.getContactByUserId(devId)            
        if devContInfo in badInfoList:
            self.setLog('getMgrIdByDevId No Contact for uid:%s'%devId,'error')
            return result
        # Change here to use User.IsActive
        if devContInfo.get('ContactStatus__c','Active') in ['Inactive']:
            devId = devContInfo.get('Reassign_To_User_ID__c','')
            devContInfo = self.getContactByUserId(devId)
        
        mgrId = devContInfo.get('Branches_Approved_By_User_ID__c','')
        if mgrId in badInfoList:
            msg = 'getMgrIdByDevId: uid:%s resolved to %s %s %s with no (Branches_Approved_By_User_ID__c)'%(devId,devContInfo.get('FirstName'),devContInfo.get('LastName'),devContInfo.get('Email'))
            self.setLog(msg,'warn')
            print 'WARN: %s'%msg
            mgrId = devContInfo.get('Reassign_To_User_ID')
            if mgrId not in badInfoList:
                msg = 'getMgrIdByDevId: uid:%s resolved to %s %s %s USED: Reassign_To_User_ID'%(devId,devContInfo.get('FirstName'),devContInfo.get('LastName'),devContInfo.get('Email'))
                self.setLog(msg,'error')
                print 'ERROR: %s'%msg
                return mgrId
            mgrEmail = devContInfo.get('Mods_Approved_By__c','')  
            mgrInfo = self.getUserByEmail(mgrEmail)    
            mgrId = mgrInfo.get('Id','')
            if mgrId in badInfoList:
                msg = 'ERROR: getMgrIdByDevId No mgrID found for mgr:%s devId:%s, ' %(mgrEmail,devId)
                self.setLog(msg,'error')
                print 'ERROR: %s'%msg
                return result
        return mgrId
            
    def getMgrByID(self, userId):
        """ Another method to walk up manager tree
            - return whole mgr user info dictionary or {}
        """
        result = {}
        if userId in [None,'']: return result

        userContact = self.getContactByUserId(userId)
        mgrId = userContact.get('Branches_Approved_By_User_ID__c','')
        if mgrId in [None,'']:
            mgrContactId = userContact.get('ReportsToId','')
            # could us a getUserByContactId() method here
            
        if mgrId not in [None,'']:
            res = self.retrieve( [mgrId], 'User', fieldList='all', allowNulls=False)
            if res not in badInfoList:
                return res[0]
        
        mgrEmail = userContact.get('Branches_Approved_By__c','')
        if mgrEmail in [None,'']:
            mgrEmail = userContact.get('Mods_Approved_By__c','')
        if mgrEmail in [None,'']:
            mgrEmail = userContact.get('Reassign_To__c','')
        
        if mgrEmail in [None,'']:
            self.setLog('getMgrById: no Mods approved by found in Contact userId:%s contInfo:%s'%(userId, userContact),'error')
            return result
            
        mgrInfo = self.getUserByEmail(mgrEmail)    
        if mgrInfo in badInfoList:
            self.setLog('getMgrById: no mgr info found for mgrMail:%s '%(mgrEmail),'error')
            return result
        return mgrInfo


    def getVpByUserId(self, userId):
        """ Another method to walk up manager tree
        - return whole VP user info dictionary or {}
        """
        if not hasattr(self, 'vpIdCache'):
            self.vpIdCache = {}
            pass
        
        userFields = ('Id', 'UserRoleId')
        vpRoles = ('00E30000000bwK2EAI')
        
        result = {}
        if userId in [None,'']: return result

        userRoleId = ''
        seenUsers = []
        origUserId = userId

        if self.vpIdCache.get(userId) is not None:
            userId = self.vpIdCache.get(userId)
            pass

        while True:
            if userId in seenUsers:
                break
            seenUsers.append(userId)

            userData = self.getUserById(userId)

            if userData.get('UserRoleId') in vpRoles:
                result = userData
                break
            
            userContact = self.getContactByUserId(userId)
            reportsToContactId = userContact.get('ReportsToId')
            if reportsToContactId is None:
                break

            # look up the reports to contact and get the user Id from it.
            reportsToContact = self.getContactById(reportsToContactId)
            userId = reportsToContact.get('Contact_User_Id__c')
            if userId is None:
                break

            # try again with the new userId
            continue

        if result.get('Id') is not None:
            self.vpIdCache[origUserId] = result.get('Id')
            pass
        
        return result
       

    ##################################################################################################
    #  Product team (Components, User_links) methods 
    ##################################################################################################
    def getComponent(self, lookup):
        """ get all information in a component object or {}"""
        res = self.query('Component__c',['Lookup__c','=',lookup])
        if res in badInfoList:
            res = self.query('Component__c',['Name','=',lookup])
            if res in badInfoList:
                msg = 'getComponent >%s< not found '%lookup
                self.setLog(msg, 'error')
                return {}
        return res[0]

    def getUserLinksByTeamId(self, teamId, teamLookup=''):
        """ get all the userlinks related to a product team lookup 
            Return list of userlinks or []
        """
        res = self.query('User_Link__c',['Product_Team__c','=',teamId])
        if res in badInfoList:
            msg = 'getUserLinksByTeamId: No PE found for %s component:%s'%(teamId,teamLookup)
            self.setLog(msg,'fix')
            return []
        return res
        

    def getProductTeamAll(self, team):
        """ get all the information for a product team object set """
        results = {'Product_Team__c':{}, 'Component__c':[], 'User_Link__c':[],}
        res = self.query('Product_Team__c',['Lookup__c','like',team])
        if res in badInfoList:
            return results
        ptInfo = res[0]
        ptId = ptInfo.get('Id')  
        # now find 'sub-components' that link to this team
        res = self.query('User_Link__c',['Product_Team__c','=',ptId])
        if res not in badInfoList:
            results['User_Link__c'] = res

        res = self.query('Component__c',['Product_Team__c','=',ptId])
        if res not in badInfoList:
            results['Component__c'] = res
        return results
        
    def getProductTeam(self, lookup):
        """ gets the Product team and creates an empty if not found
            returns teamInfo or {'Id':id} or {}
        """
        res = self.query('Product_Team__c',['Lookup__c','=',lookup])
        if res in badInfoList:
            """
            Commenting the code that creates new product team in SF
            ptid = self.setProductTeam(lookup)            
            """
            ptid=''
            if ptid in [None,'','fail',[],{}]: return {}
            try: res['Id'] = ptid
            except:
                print 'Error creating ProductTeam with %s Got %s'%(lookup,res)
                return {}
        else:
            res = res[0]
            ptid = res.get('Id','')
            #print 'Found an Product team id:%s  name:%s '%(ptid, res.get('Name',''))
        return res
        
    def setProductTeam(self, lookup, name='', description=''):
        """ create a Product Team customer object 
            returns Product Team ID or ''
        """
        if name in [None,'']: name = lookup
        data = {'Name':name, 'Lookup__c': lookup}
        res = self.create('Product_Team__c', data)
        print 'Adding an Product Team %s as %s from %s' %(lookup, res, data)
        if res in badInfoList:
            return ''
        return res[0]

    def addComponent(self, lookup, teamId, name='', mail_list=''):
        """ Add a componet object to a Product team with optional email list
            returns component ID or ''
        """
        if name in [None,'']: name = lookup
            
        data = {'Name':name, 'Lookup__c': lookup, 'Product_Team__c':teamId, 'List_Address__c':mail_list}
        res = self.create('Component__c', data)
        print 'Create Component %s for %s res:%s ' %(lookup, teamId ,res)
        if res in badInfoList:
            return ''
        return res[0]

            
    def setUserLink(self, teamId, alias, name='', type='', status=''):
        """ create a Product Team user link object, looking up user and contact for their IDs
            does not check for duplicates, returns User Link ID or '' 
        """
        if name in [None,'']: name = alias
        userInfo = self.getUserByAlias(alias)
        userId = userInfo.get('Id','')
        #contactInfo = self.getContactByUserId(userId)
        #contactId = contactInfo.get('Id','')
        data = {'Name':name, 'Lookup__c': alias, 'Link_Status__c': status, 'Link_Type__c': type
               ,'Product_Team__c': teamId, 'User__c': userId}
        res = self.create('User_Link__c', data)
        print 'Created UserLink %s for %s of type %s as %s res:%s' %(alias,teamId,type,status, res)
        if res in badInfoList:
            return ''
        return res[0]

    def setComponentMap(self, peQueues, peAppMap, comp2EmailMap):
        """ take the old pe dictionaries and create the correct Product Team, componet and UserLink objects
            - Uses maps in the format:
              - peQueues = {'fusion-pes' : {'list' : ['paulg', 'jharper'], 'owner' : 'paulg'}}
              - peAppMap = {'buffering' : {'pe' : 'buffering-pe', 'dev' : 'etienne'},}
                  - value of 'pe' munus the '-pe*' is the lookup label of the Product Team
              - component2QueueEmailMap = {'buffering':'sf_buffering@molten-magma.com',}
              UserLink.Types = ['PE Notify','PE Approver','Developer','Dev Manager'
                               ,'App Engineer','Notify Merged CR','Notify New CR','Interested Party']
              UserLink.Status = ['New','Active','Inactive']
        """
        num = 0
        for component in peAppMap.keys():
            num += 1
            compDict  = peAppMap[component]
            peLabel   = compDict.get('pe')
            teamLookup= peLabel.split('-')[0]
            peAlias  = peQueues.get(peLabel)
            if peAlias in [None,'',[],{}]:
                print 'Error with finding peQue info for %s'%peLabel
                continue
            peAlias   = peAlias['owner']
            ipAliases = peQueues.get(peLabel)['list']   # list of aliases including PE
            devAlias  = compDict.get('dev')
            mail_list = comp2EmailMap.get(component)
            print 'Team:%s  Component:%s Pe:%s List:%s' %(teamLookup, component, peAlias, ipAliases)
            
            ptInfoAll = self.getProductTeamAll(teamLookup)
            #print 'Team %s has %s' %(teamLookup,ptInfoAll)
            # format is {'Product_Team__c':{}, 'Component__c':{}, 'User_Link__c':{},}
            ptInfo   = ptInfoAll.get('Product_Team__c')
            compList = ptInfoAll.get('Component__c')
            ulList   = ptInfoAll.get('User_Link__c')
            
            #teamlInfo = self.getProductTeam(teamLookup)
            teamId = ptInfo.get('Id')
            if teamId is None:
                teamInfo = self.getProductTeam(teamLookup)
                teamId = teamInfo.get('Id','')
                print 'Created Product team %s as %s' %(teamLookup, teamId)
                if teamId in [None,'',[],{}]:
                    print 'Error: Product Team get failed on %s with %s'%(teamLookup,teamInfo)
                    continue
            # should have handle to team Object now 
            exists = False
            for compInfo in compList:
                if compInfo.get('Lookup__c','') == component:
                    exists = True
            if not exists:
                compID = self.addComponent(component, teamId, mail_list=mail_list)
                print 'Added component %s to %s' %(component, teamLookup)
            
            existingULinks = []
            for uLink in ulList:
                ulAlias = uLink.get('Lookup__c','')
                if ulAlias not in existingULinks:
                    existingULinks.append(ulAlias)

            if peAlias not in existingULinks:
                ret = self.setUserLink( teamId, peAlias, name=peAlias, type='PE Approver', status='Active')
                
            for ipAlias in ipAliases:
                if ipAlias not in existingULinks and ipAlias != peAlias:
                    ret = self.setUserLink( teamId, ipAlias, name=ipAlias, type='Interested Party', status='Active')

            if devAlias not in existingULinks and devAlias != ipAlias:
                ret = self.setUserLink( teamId, devAlias, name=devAlias, type='Developer', status='Active')
        return num


    def getMagmaAccountIds(self):
        if not hasattr(self, 'MagmaAccountList'):
            where = [['Name','Like','Magma Design Automation%']]
            fields = ('Id', 'Name')
            res = self.query(ACCOUNT_OBJ, where=where, sc=fields)

            MagmaAccountList = []
            if res not in BAD_INFO_LIST:
                for account in res:
                    if account.get('Id') not in MagmaAccountList:
                        MagmaAccountList.append(account.get('Id'))
                    continue
                pass
            
            self.MagmaAccountList = MagmaAccountList
            
        return self.MagmaAccountList
    ## END getMagmaAccountIds


    def getAllMagmaContacts(self, fields='all'):
        magmaAccountList = self.getMagmaAccountIds()

        seriesSize = 10

        contactList = []
        while len(magmaAccountList) > 0:
            series = magmaAccountList[:seriesSize]
            magmaAccountList = magmaAccountList[seriesSize:]

            where = []
            for acctId in series:
                where.append(['AccountId','=',acctId])
                where.append('or')
                continue

            where.pop()

            res = self.query(CONTACT_OBJ, where, sc=fields)
            if res not in BAD_INFO_LIST:
                contactList.extend(res)
            
            continue

        return contactList
    ## END getAllMagmaContacts

        
            
    ##################################################################################################
    #  utility and setup methods
    ##################################################################################################
    def showDataUser(self, data=None, entity=''):
        """ user console oriented display of data loaded in this object """
        if data is None: data = self.data
        if data in [None,'',[],[()]]: return 
        if type(data) not in seqTypes:
            return self.showDictConsole2(data)
        for dataTuple in data:
            if entity == '':
                entity = dataTuple[0]
                dataDict = dataTuple[1]
            else:
                if entity != dataTuple[0]:
                    continue
                dataDict = dataTuple
            if dataDict in [[],{}]:
                print ' -------- No Data for %s item -------'%entity
            else:
                print ' ------%s Data for the item ---------' %entity
                if type(dataDict) in dictTypes:
                    for k, v in dataDict.items():
                        if v not in [None,'']:
                            print ' %25s: %s' %(k,dataDict[k])
                            #Command_Change_Details__c
                elif type(dataDict) in seqTypes:
                    dataDict = dataDict[0]
                    if type(dataDict) in dictTypes:
                        for k, v in dataDict.items():
                            if v not in [None,'']:
                                print ' %25s: %s' %(k,dataDict[k])
                    else:
                        print ' Wrong format dd:%s '%dataDict
                    
                else:
                    print ' Wrong format dd:%s '%dataDict
        print '---------------------------------------------------'
        return
    

    def getTeamList(self):
        """
        Get a list of tuples with team lookup and description for all
        product teams
        """
        if hasattr(self, 'ptList') is False:
            ptList = self.query('Product_Team__c',['Lookup__c','!=',''])
            if ptList in badInfoList:
                ptList = []
                print 'Could not find any Product Teams, found:%s'%ptList
                pass
            self.ptList = ptList
            pass
        return self.ptList
    ## END getTeamList
    
    def devTeamToScmTeam(self, teamName):
        """ Takes a lookup for a team name and returns the lookup
        for the scm team """
        teamName = teamName.lower()
        ptList = self.getTeamList()

        abbrev = None
        for pt in ptList:
            if teamName == pt.get('Lookup__c'):                
                #abbrev = pt.get('Team_Alias__c')
                abbrev = teamName
                break
            continue
        return abbrev
    ## END devTeamToScmTeam
       


#####################################################################################################
#  Temp data update structures
######################################################################################################
def getPECompMaps():
    """ return the raw dictionaries fro some other method """
    # Define a list of valid PE queues.
    peQueues = {'fusion-pes' :      {'list' : ['paulg', 'grace', 'army', 'jharper','gnana', 'madhu', 'sujay'],
                                                            'owner' : 'paulg'},
                                                            
                'buffering-pe' :    {'list' : ['paulg'],    'owner' : 'paulg'},
                'logicopt-pe' :     {'list' : ['paulg'],    'owner' : 'paulg'},                

                'create-pes' :      {'list' : ['amiri', 'stephenm', 'stevenl','govind'], 
                                                            'owner' : 'amiri'},
                'analysis-pes' :    {'list' : ['emre', 'akash', 'wilson','farokh', 'saby', 'pravins'], 
                                                            'owner' : 'emre'},
                                                            
                'routing-pe' :      {'list' : ['rod'],      'owner' : 'rod'},
                'clock-pe' :        {'list' : ['jharper'],  'owner' : 'jharper'},
            
                'library-pe' :      {'list' : ['sabyasachi'],'owner' : 'sabyasachi'},
                'grace-pe'  :       {'list' : ['grace'],    'owner' : 'grace'},
                'gui-pe'  :         {'list' : ['gnana'],    'owner' : 'gnana'},
                'rlc-qc-pe' :       {'list' : ['akash'],    'owner' : 'akash'},                
                'power_routing-pe':{'list' : ['army'],     'owner' : 'army'},
                'lowpower-pe' :     {'list' : ['andrews'],  'owner' : 'andrews'},
                'floor-pe' :        {'list' : ['paulg'],    'owner' : 'paulg' },
                'sps-pe' :          {'list' : ['sdpaiva'],  'owner' : 'sdpaiva' },
                'techpub-pe' :      {'list' : ['cherry'],   'owner' : 'cherry'},
                'sf-test-pes' :     {'list' : ['kshuk'],    'owner' : 'kshuk'},
                'sf-pes' :          {'list' : ['dbrooks', 'kshuk', 'chip'], 'owner' : 'dbrooks'}
                }
    # Define a Component to PE/Queue mapping to help determine whom to
    # notify for approval purposes.
    peAppMap = {
            
            'clock routing' :   {'pe' : 'clock-pe', 'dev' : 'lippens'},
            'hold buffering':   {'pe' : 'clock-pe', 'dev' : 'lippens'},
            
            'low power issues': {'pe' : 'lowpower-pe', 'dev' : 'ed'},
            'power routing' :   {'pe' : 'power_routing-pe', 'dev' : 'elyu'},
            
            'rlc/quickcap' :    {'pe' : 'rlc_qc-pe', 'dev' : 'emre'},

            'sps backend':      {'pe': 'sps-pe', 'dev' : 'peichen'},
            'sps frontend':     {'pe': 'sps-pe', 'dev' : 'peichen'},

            'congestion' :          {'pe' : 'placement-pe', 'dev' : 'hptseng'},
            'placement' :           {'pe' : 'placement-pe', 'dev' : 'koen'}, 
            'flipchip' :            {'pe' : 'placement-pe', 'dev' : 'henrik'},
            
            'floorplanning' :       {'pe' : 'floor-pe', 'dev' : 'raymond'},
            'prototyping' :         {'pe' : 'floor-pe', 'dev' : 'raymond'},
            
            'buffering' :        {'pe' : 'fusion-pe', 'dev' : 'etienne'},
            'logic optimization':{'pe' : 'fusion-pe', 'dev' : 'michel'},
            'data model' :      {'pe' : 'fusion-pes', 'dev' : 'hong' },
            'flow' :            {'pe' : 'fusion-pes', 'dev' : 'hong' },
            'licensing' :       {'pe' : 'fusion-pes', 'dev' : 'hong' },
            'mtcl' :            {'pe' : 'fusion-pes', 'dev' : 'hong' },
            
            'documentation' :   {'pe': 'techpub-pe', 'dev' : 'cherry'},
            'training' :        {'pe' :'techpub-pe', 'dev' : 'cherry'},
            
            'electromigration' :    {'pe' : 'analysis-pes', 'dev' : 'mustafa'},
            'extraction' :          {'pe' : 'analysis-pes', 'dev' : 'riverson'},
            'crosstalk' :           {'pe' : 'analysis-pes', 'dev' : 'mustafa'},
            'delay calculation' :   {'pe' : 'analysis-pes', 'dev' : 'mustafa'},
            'timing' :              {'pe' : 'analysis-pes',  'dev' : 'swanson'},
            'timing-sdc' :          {'pe' : 'analysis-pes', 'dev' : 'swanson'},
            'power&rail analysis' : {'pe' : 'analysis-pes', 'dev' : 'ed'},
            'extraction/crosstalk' :{'pe' : 'analysis-pes', 'dev' : 'mustafa'}, 
            
            'global routing' :  {'pe' : 'routing-pe', 'dev' : 'hptseng'},
            'detail routing' :  {'pe' : 'routing-pe', 'dev' : 'ksleung'},
            'track routing' :   {'pe' : 'routing-pe', 'dev' : 'hong'},
            
            'rtl qor' :         {'pe' : 'create-pes', 'dev' : 'samit'},
            'rtl verilog' :     {'pe' : 'create-pes', 'dev' : 'samit'},
            'rtl synthesis' :   {'pe' : 'create-pes', 'dev' : 'samit'},
            'rtl vhdl' :        {'pe' : 'create-pes', 'dev' : 'samit'},
            'verilog' :         {'pe' : 'create-pes', 'dev' : 'samit'}, # not in SF Feb 4, 04
            'vhdl' :            {'pe' : 'create-pes', 'dev' : 'samit'}, # not in SF Feb 4, 04
            'scan' :            {'pe' : 'create-pes', 'dev' : 'espark'}, # not in SF Feb 4, 04
            'dft' :             {'pe' : 'create-pes', 'dev' : 'espark'},
            
            'gui' :                             {'pe' : 'gui-pe', 'dev' : 'ryan' },
            'gui - clock tree browser' :        {'pe' : 'gui-pe', 'dev' : 'ryan' },
            'gui - layout / fp : flylines' :    {'pe' : 'gui-pe', 'dev' : 'ryan' },
            'gui - layout / fp : pin menu' :    {'pe' : 'gui-pe', 'dev' : 'ryan' },
            'gui - layout / fp : power menu' :  {'pe' : 'gui-pe', 'dev' : 'ryan' },
            'gui - layout / fp : selection & editing' : {'pe' : 'gui-pe', 'dev' : 'ryan' },
            'gui - layout / fp : viewing' :     {'pe' : 'gui-pe', 'dev' : 'ryan' },
            'gui - schematic' :                 {'pe' : 'gui-pe', 'dev' : 'ryan' },
            'gui - timing viewer' :             {'pe' : 'gui-pe', 'dev' : 'ryan' },
            
            'library' :                         {'pe' : 'library-pe', 'dev' : 'hong' },
            'library liberty' :                 {'pe' : 'library-pe', 'dev' : 'seelen'},
            'library-gdsii' :                   {'pe' : 'library-pe', 'dev' : 'riepe'},
            'library gdsii' :                   {'pe' : 'library-pe', 'dev' : 'riepe'},
            'library-lefdef' :                  {'pe' : 'library-pe', 'dev' : 'hong'},
            
            'magma qualified library':          {'pe': 'sf-pes', 'dev' : 'dbrooks'},             # in sf added Feb 4, 04
            'magma qualified reference flow':   {'pe': 'sf-pes', 'dev' : 'dbrooks'},      # in sf added Feb 4, 04
            'magma qualified rules':            {'pe': 'sf-pes', 'dev' : 'dbrooks'},               # in sf added Feb 4, 04
            'salesforce.com' :                  {'pe': 'sf-pes', 'dev' : 'chip'},
            'salesforce.com workflow test' :    {'pe': 'sf-test-pes', 'dev' : 'kshuk'},
            'snap/enwrap':                      {'pe': 'sf-pes', 'dev' : 'dbrooks'} # in sf added Feb 4, 04
            }

    component2QueueEmailMap = {'buffering':'sf_buffering@molten-magma.com',
                           'clock routing':'sf_clockrouting@molten-magma.com',
                           'congestion':'sf_congestion@molten-magma.com',
                           'crosstalk':'sf_crosstalk@molten-magma.com',
                           'data model':'sf_datamodel@molten-magma.com',
                           'delay calculation':'sf_delaycalculation@molten-magma.com',
                           'detail routing':'sf_detailrouting@molten-magma.com',
                           'dft':'sf_dft@molten-magma.com',
                           'documentation':'sf_documentation@molten-magma.com',
                           'electromigration':'sf_electromigration@molten-magma.com',
                           'extraction':'sf_extraction@molten-magma.com',
                           'flipchip':'sf_flipchip@molten-magma.com',
                           'floorplanning':'sf_floorplanning@molten-magma.com',
                           'global routing':'sf_globalrouting@molten-magma.com',
                           'gui':'sf_gui@molten-magma.com',
                           'hold buffering':'sf_hold_buffering@molten-magma.com',
                           'library':'sf_library@molten-magma.com',
                           'library gdsii':'sf_library-gdsii@molten-magma.com',
                           'library-lefdef':'sf_library-lefdef@molten-magma.com',
                           'library liberty':'sf_library-liberty@molten-magma.com',
                           'logic optimization':'sf_logic-optimization@molten-magma.com',
                           'mtcl':'sf_mtcl@molten-magma.com',
                           'placement':'sf_placement@molten-magma.com',
                           'power&rail analysis':'sf_ir-drop@molten-magma.com',
                           'power routing':'sf_powerrouting@molten-magma.com',
                           'prototyping':'sf_prototyping@molten-magma.com',
                           'rtl qor':'sf_rtl-synthesis@molten-magma.com',
                           'rtl synthesis':'sf_rtl-synthesis@molten-magma.com',
                           'rtl verilog':'sf_verilog@molten-magma.com',
                           'rtl vhdl':'sf_vhdl@molten-magma.com',
                           'support':'salesforce-support@molten-magma.com',
                           'salesforce.com':'salesforce-support@molten-magma.com',
                           'salesforce.com workflow test':'kshuk@molten-magma.com',
                           'timing':'sf_timing@molten-magma.com',
                           'timing-sdc':'sf_timing-sdc@molten-magma.com',
                           'track routing':'sf_trackrouting@molten-magma.com'}
    
    return peQueues, peAppMap, component2QueueEmailMap



##################################################################################################
#  Logic methods called from command line 
##################################################################################################
def doPEMapMigration(options):
    """ called from command line to do the migration """
    sfb = SFMagmaTool(debug=options.debug)
    peQueues, peAppMap, component2QueueEmailMap = getPECompMaps()
    num = sfb.setComponentMap(peQueues, peAppMap, component2QueueEmailMap)
    print 'Added %s Components' %num

def showEntities(query, options):
    sfb = SFMagmaTool(debug=options.debug)
    entityList = sfb.getEntities()
    if query == 'all':
        print 'Returning ALL entities, Use a substring to return on some enetites'
        pprint.pprint( entityList)
        return
    else:
        print 'looking for entities with the string %s\n' %query
        for ent in entityList:
            if ent.lower().find(query.lower()) != -1:
                print '\t%s' %ent
        
def doQuery(entity, where, parm, options):
    print 'Looking for %s items with query %s using parm %s' %(entity, where, parm) 
    sfb = SFMagmaTool(debug=options.debug)
    results = sfb.query( entity, where=where, sc=parm)
    pprint.pprint( results)
    
def doUpdate(entity, where, parm, options):
    print 'Updating the %s items found with query %s using parm %s' %(entity, where, parm) 
    print 'Just kidding, not implemented'

def doDelete(entity, where, parm, options):
    print 'Deleting the %s items found with query %s using parm %s' %(entity, where, parm) 
    print 'Just kidding, not implemented'

def doCreate(entity, where, parm, options):
    print 'Creating the %s items found with query %s using parm %s' %(entity, where, parm) 
    print 'Just kidding, not implemented'

def getEmpTree(names, options):
    """ just a crude leaf to root tree walker to test getMgrById method """
    where = ['LastName','like',names]
    tool = SFMagmaTool(debug=options.debug)
    userInfos = tool.query( 'User', where=where, sc='user')
    indent = '   '
    info = '____________________________\n'
    for ui in userInfos:
        uid = ui.get('Id')
        last = '%s--- Tree for %s %s %s\n' %(indent, ui.get('Email'),ui.get('FirstName'),ui.get('LastName'))
        info += getMgrInfo(uid, last, indent, tool)
    print info
        
def getMgrInfo(uid, last, indent, tool, times=0):
    """ used by getEmpTree """
    indent += indent
    times += 1
    if times > 5: return last
    mgr = tool.getMgrByID(uid)
    if type(mgr) == type(''):
        print last
        return last
    elif mgr.get('Id') == uid:
        print last
        return last
    elif mgr in [None, [], [{}], {}]:
        return last
    last = '%s%s %s %s %s\n' %(last,indent, mgr.get('Email'), mgr.get('FirstName'), mgr.get('LastName'))
    mgrId = mgr.get('Id')
    return getMgrInfo(mgrId, last, indent, tool)

def doSomething(method, term, parm, options):
    """  Command line controlled test of a method """
    print 'You called me with method:%s term:%s parm:%s ' %(method, term, parm)
    print 'Hope it was good for you'

##################################################################################################
#  Commandline management methods.  Minimal logic, just command parm processing
##################################################################################################
def usage(err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to test the basic API calls.\n'
    m += ' '
    m += '    sfEntity  -cq -eCase CaseNumber like 25455  \n'
    m += '      or\n'
    m += '    sfEntity  -cq -eTask BranchLabel__c like %_michel% \n'
    m += '      or\n'
    m += '    sfEntity  -ce  all    (to return list of valid entities)\n'
    return m

def main_CL():
    """ Command line parsing and and defaults methods
    """
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-c", "--cmd",   dest="cmd",   default="query",    help="Command type to use.")
    parser.add_option("-e", "--entity",dest="entity",default="Case",     help="Entity to operate with.")
    parser.add_option("-p", "--parm",  dest="parm",  default="",         help="Command parms.")
    parser.add_option("-f", "--path",  dest="path",  default="",         help="Path to output.")
    parser.add_option("-t", "--trace", dest="trace", default="soap.out", help="SOAP output trace file.")
    parser.add_option("-d", "--debug", dest='debug', action="count",     help="The debug level, use multiple to get more.")
    (options, args) = parser.parse_args()
    if options.debug > 1:
        print ' cmd    %s' %options.cmd
        print ' path   %s' %options.path
        print ' parms  %s' %options.parm
        print ' trace  %s' %options.trace
        print ' debug  %s' %options.debug
        print ' args:  %s' %args
    else:
        options.debug = 0
        
    if len(args) > 0: 
        st = time.time()
        entity = options.entity
        parm = options.parm
        query = args[0:]
        if options.cmd in ['query','q']:
            if parm in ['bc']:
                sc = 'case'
                entity = 'Case'
                query = 'broadcom'
                doQuery(entity, query, sc, options)
            elif parm in ['c','v']:
                sc = 'contact'
                query =[('LastName','vanek',)]
                entity = 'Contact'
                doQuery(entity, query, sc, options)
            else:
                doQuery(entity, query, parm, options)
            
        elif options.cmd in ['update','u']:
            doUpdate(entity, query, parm, options)
            
        elif options.cmd in ['create','c']:
            doCreate(entity, query, parm, options)
            
        elif options.cmd in ['delete','d']:
            doDelete(entity, query, parm, options)

        elif options.cmd in ['entities','e']:
            query = ''.join(query)
            showEntities(query, options)
            
        elif options.cmd in ['tree','t']:
            query = ''.join(query)
            getEmpTree(query, options)

        elif options.cmd in ['pemigrate','pem']:
            query = ''.join(query)
            doPEMapMigration(options)

        else:
            doSomething('search', query, options.parm, options)
            print 'doing nothing yet, I can do it twice if you like'
            
        print '\nTook a total of %3f secs' %(time.time()-st)
    else:
        print '%s' %usage()

if __name__ == "__main__":
    main_CL()
