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

###########################################################
#  Global constants - will move to util.py and import
###########################################################
version = 3.0
ISO_8601_DATETIME = '%Y-%m-%dT%H:%M:%S'
seqTypes = [ListType, TupleType]
dictTypes = [DictType, DictionaryType]
strTypes = [StringType, StringTypes]
badInfoList = BAD_INFO_LIST

class SFEntity(SFEntityBase):
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

        

class SFEntityTool(sForceApi3):
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

        if setupLog is True:
            self.setLogger()
    ## END setupBase(self, username, upass, logger)

    def mailServer(self):
        if not hasattr(self, 'mailSrvH'):
            self.mailSrvH = MailServer(logger=self.log)

        return self.mailSrvH

    def setupChild(self):
        """ add methods in child classes"""
        pass

    badInfoList = BAD_INFO_LIST
    trialAddrList = ['chip@molten-magma.com']

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
        return self.em.getEntity(entity)
  
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
            if self.debug >0: print ret['errMsg']
            return ret['errCode']
        

    ######################################################################
    #  SOSL query methods
    #  SELECT [List of Field Names] IN EntityName 
    #         WHERE FieldName = 'value' AND FieldName >= 'value' OR FieldName != ''
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
        ret = self.queryBase( entity, where=where, sc=sc, soql=soql,
                              limit=limit)
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
        ret = self.retrieveBase(ids, entity, fieldList=fieldList,
                                allowNulls=allowNulls)
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

    def getSOQLEntityShortcut(self, sc):
        """ Convert a shortcut string into a valid SOQL string
          format: SELECT fieldList from objectType 
        """
        return sForceApi3.getSOQLEntityShortcut(self, sc)





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
        c1 = {'Contact':['FirstName', 'LastName', 'Email', 'Last_Report__c', 'Mods_Approved_By__c', 'Id']}
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
        try:crNumInt = int(crNum)
        except: return {}
        crPadded = (8 - len(crNum))*'0' + crNum
        clarify = False

        # No longer assume CR number < 23600 is clarify. 11/5/2004
##        if int(crNum) < 23600:
##            clarify = True
##            where = [['ClarifyID__c','like',crNum]]
##        else:
##            where = [['CaseNumber','like',crPadded]]
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
               self.getId15(creatorID) not in self.sfAdminIDs and \
               creatorID[:3] != '00G':     # Queue ID start with 00G, right?
            return creatorID
        ownerID = crInfo.get('OwnerId')
        if ownerID not in self.sfAdminIDs and ownerID[:3] != '00G':
            return ownerID
        # clarify originator
        clarifyOriginatorName = crInfo.get('Originator__c',',')
        first, last = clarifyOriginatorName.split(',')
        where = [['LastName','like',last],'and',['FirstName','like',first]]
        userList = self.query('User', where)

        if userList not in BAD_INFO_LIST:
            user = userList[0]
            ownerID = user.get('Id','')
            if ownerID not in self.sfAdminIDs and ownerID not in [None,'']:
                return ownerID
        
        # contact
        contactId = crInfo.get('ContactId')
        user = self.getContactByUserId(contactId)
        ownerID = user.get('Id','')
        if ownerID not in self.sfAdminIDs and ownerID not in [None,'']:
            return ownerID
        # default to chip
        self.setLog('getCrOriginator cr:%s owned/created by sfAdmin or Queue, no originator or contact'%crInfo.get('CaseNumber'),'error')
        return self.sfc.get('main','default_soft_uid')
        

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
        res = self.query('User',['Alias','like',alias])  # use = ?
        if res in badInfoList:
            email = '%s@molten-magma.com'%alias
            res = self.query('User',['Email','like',email])  # use = ?
            if res in badInfoList:
                print 'Cannot find User with alias:%s or email:%s' %(aliasLookup,email)
                return {}
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
        
        res = self.query('Contact',['Contact_User_Id__c','=',userId],'fields')  # userId value is stored as uid15
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
            self.setLog('getUserByEmail Cannot find User with uid:%s' %(uid),'error')
            return {}
        self.setCache(key,res[0])
        return res[0]

    
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
        


##################################################################################################
#  Logic methods called from command line 
##################################################################################################
def showEntities(query, options):
    sfb = SFEntityTool(debug=options.debug)
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
    
def setCRTags(crList, tag, options):
    print ' Setting tag for %s to %s'%(crList,tag)
    sfb = SFEntityTool(debug=options.debug)
    if type(crList) not in [type([]),type(())]:
        crl = [crList]
    else:
        crl = crList
    for crnum in crl:
        crInfo = sfb.getCrByNum(crnum)
        crtag = crInfo.get('Tag__c','')
        newtag = '%s %s'%(crtag,tag)
        data = {'Id':crInfo.get('Id'),'Tag__c':newtag}
        ret = sfb.update('Case',[data])
        print 'Update CR %s as https://na1.salesforce.com/%s'%(crnum,ret[0])
                
                
def doQuery(entity, where, parm, options):
    print 'Looking for %s items with query %s using parm %s' %(entity, where, parm) 
    sfb = SFEntityTool(debug=options.debug)
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
    tool = SFEntityTool(debug=options.debug)
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


def refreshEntityCache():
    """
    Refresh the entire Entity metadata sop cache
    """
    print "Refreshing the entity metadata cache."
    print "This will take several minutes - please be patient."
    tool = SFEntityTool()
    tool.setEntitiesMap()
    print "Done!"
    return

def refreshThisEntityCache(entity, options):
    """
    Refresh a specific Entity metadata sop cache
    """
    db = options.debug
    print "Refreshing the entity metadata cache. with db %s"%db
    print "This will take several minutes - please be patient."
    tool = SFEntityTool(debug=db)
    tool.setEntityMap(entity)
    print "Done!"
    return

    
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
    
def tag_usage(err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to update 1 CR with a tag string:\n'
    m += ' '
    m += '  tagcr  -t <CR>  <tag value>  \n'
    return m
    
def main_CL():
    """ Command line parsing and and defaults methods
    """
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-c", "--cmd",   dest="cmd",   default="query",    help="Command type to use.")
    parser.add_option("-e", "--entity",dest="entity",default="Case",     help="Entity to operate with.")
    parser.add_option("-p", "--parm",  dest="parm",  default="",         help="Command parms.")
    parser.add_option("-f", "--path",  dest="path",  default="",         help="Path to output.")
    parser.add_option("-t", "--tag",   dest="tag",   default="",         help="Category Tag.")
    parser.add_option("-d", "--debug", dest='debug', action="count",     help="The debug level, use multiple to get more.")
    (options, args) = parser.parse_args()
    if options.debug > 1:
        print ' cmd    %s' %options.cmd
        print ' path   %s' %options.path
        print ' parms  %s' %options.parm
        print ' entity  %s' %options.entity
        print ' tag    %s' %options.tag
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

        elif options.cmd in ['refresh']:
            refreshEntityCache()
            
        elif options.cmd in ['reset']:
            refreshThisEntityCache(entity, options)        

        elif options.cmd in ['tree']:
            query = ''.join(query)
            getEmpTree(query, options)

        elif options.cmd in ['tag','t']:
            taglist = query
            tag = ' '.join(taglist)
            crList = options.tag
            if tag in [None,'']:
                print '%s' %tag_usage('Please provide a Tag value')
            setCRTags(crList, tag, options)
            
        else:
            doSomething('search', query, options.parm, options)
            print 'doing nothing yet, I can do it twice if you like'
            
        print '\nTook a total of %3f secs' %(time.time()-st)
    else:
        if options.cmd in ['tag','t']:
            print '%s' %tag_usage()
        else:
            print '%s' %usage()

if __name__ == "__main__":
    main_CL()
