""" Base Python API for sForce 3.0 
    - wrapper around ZSI 1.2.8 (from version.py), 1.14,  May 25, 2004 CVS checkout with patches
    - wsdl2python patch to generate right format of proxy classes in SforceService_services
    - Subclass and use the classes in sfEntity.py rather then the methods in this base class
    - Uses persistance classes in sop.py to maintain an automatically updated cache of entity metadata
    
 ToDo:
    - Extend old file cache or new sop.py classes to save user based info (username, password, defaults)
    - Add getUpdated & getDeleted support for remote polling of sForce server and local replication
    - Add reset user password support
    - https support to secure login calls and access to sensitive data
    - Add http compression support to improve performance "Accept-Encoding: gzip" & "Content-Encoding:gzip"
    - Add http Persistent Connection to improve performance and response time
    - Add retry support to recove from network or load based errors (rate limit, socket errors, unavailable)

           Chip Vanek, June 1st, 2004
"""
import socket
import sys, time, os
import stat
import pprint
import urlparse
import StringIO, getopt
import copy, re, base64
import traceback
import logging, logging.handlers
from types import ListType, TupleType, DictType, DictionaryType, StringType, UnicodeType, StringTypes, LongType, FloatType
from optparse import OptionParser
import ZSI
import SforceService_services as sfsv
from sfConstant import *
from SforceService_services_types import urn_partner_soap_sforce_com as ns2
from SforceService_services_types import urn_sobject_partner_soap_sforce_com as ns1
# def classes are children of ns1 eg: ns1.sObject_Def

from ZSI import _child_elements, _attrs, FaultException, _children  
# the ZSI/DOM call can be moved here later as full list is developed
from sop import sfCache, sfEntities, SFEntitiesMixin, SFUtilityMixin, SFTestMixin, SFConfig

timeout = 1.0 * 60 * 15 # fifteen minute timeout to try and prevent zombifying
socket.setdefaulttimeout(timeout)

###########################################################
#  Global constants - will move to util.py and import
###########################################################
version = 3.0
ISO_8601_DATETIME = '%Y-%m-%dT%H:%M:%SZ'
#            '%(Y)04d-%(M)02d-%(D)02dT%(h)02d:%(m)02d:%(s)02dZ'
seqTypes = [ListType, TupleType]
dictTypes = [DictType, DictionaryType]
strTypes = [StringType, UnicodeType]
numTypes = (LongType, FloatType)

class SFEntityBase:
    """ Simple base class that is aware of an active sForce connection but
        does not implement all of the connection oriented and data management APIs
        
        Subclass this object to create entity specific data management and business
        logic methods.
    """
    def __init__(self, entity, data={'':{}}, action=None, sfTool=None, debug=0):
        """  If an active tool object is not passed in then a connection is created.
        """
        if sfTool is None:
            sfTool = sForceApi3(debug=debug)
        self.sfb = sfTool
        self.entity = entity
        self.setData(data)
        self.setAction(action)
        self.debug = debug
        if debug == 0:
            self.debug = self.sfb.debug
        
    def setData(self, data, reset=False):
        """ set data with any object specific filtering  
            data is a dictionary of entity-data pairs {'entity': {data}}
            multi-value entities a list of data elements {'entity',[{data}]}
            multi-entity objects are expected to have multiple entity keys.
        """
        if reset or not hasattr(self, 'data'):
            self.data = {}
        if data is None: return self.showDataFormatError(data)
        if type(data) in dictTypes:
            for entity in data.keys():
                if entity not in self.sfb.getEntities():
                    print 'ERROR:setData unknown entity %s will be ignored'%entity
                else:
                    if reset:
                        self.data[entity] = data[entity]
                    else:
                        newData = data[entity]
                        oldData = self.data.get(entity,{})
                        if type(oldData) in dictTypes and type(newData) in dictTypes:   
                            # simple case of one item for this entity
                            oldData.update(newData)
                            self.data[entity] = oldData
                            continue
                        elif type(oldData) in dictTypes and type(newData) in seqTypes:   
                            # typical case of a list of items for the entity
                            oldData = [oldData]
                            
                        elif type(newData) not in seqTypes and type(newData) not in dictTypes:
                            print 'ERROR:setData entity %s has badly formed data'%entity
                            return self.showDataFormatError(newData, entity)
                        if 1:                         
                            if type(newData) not in seqTypes: newData = [newData]
                            checkedData = []
                            checkedIds = []
                            for newd in newData:
                                newId = newd.get('Id','')
                                for old in oldData:
                                    if old.get('Id') == newId:
                                        old.update(newd)            # update old data with new dictionary data
                                        checkedData.append(old)
                                        checkedIds.append(newId)
                                        oldData.remove(old)
                                if newId not in checkedIds and newId != '':  # add brand new data to list
                                    checkedData.append(newd)
                            for old in oldData:
                                if old.get('Id') not in checkedIds and old != {}: # keep old data not updated
                                    checkedData.append(old)
                            msg = 'SetData %s updated:%s now have %s'%(entity,checkedIds,len(checkedData))
                            if self.debug>1:self.sfb.setLog(msg,'info')
                            self.data[entity] = checkedData

        elif type(data) == TupleType: return self.showDataFormatError(data)
        elif type(data) == DictType:  return self.showDataFormatError(data)
        elif type(data) == StringType: return self.showDataFormatError(data)
        else:
            print 'Error setData for:%s' %data
        
    def getData(self, entity='all', id=''):
        """ return the data 
            - list of data dictionaries if just entity provided
            - specific data dictionary if id is in entity list
        """
        if entity == 'all':
            return self.data
        if not self.data.has_key(entity):
            return [{}]
        eData = self.data.get(entity,[{}])
        if id in [None,'']: 
            return eData
        if type(eData) not in seqTypes: eData = [eData]
        if len(id) == 15:
            #id = id[:-3]
            self.sfb.setLog('getData %s NOT Found 15 char id:%s '%(entity,id),'error')
        ids = []
        for ed in eData:
            eid = ed.get('Id','')
            ids.append(eid)
            if eid == id:
                return ed
        self.sfb.setLog('getData %s NOT Found with id:%s in ids:%s'%(entity,id,ids),'error')
        return {}
        

    def showDataFormatError(self, data, entity=''):
        """ echo data format error to console """
        if entity == '': entity =self.entity
        print 'ERROR: Data in this %s object must be stored in the format {\'entity\', {data}}' %entity
        print '       Note that this is a dictionary with an sForce entity string and a data dictionary'
        if data is None: print '       You should provide some data on init, data will be {} now' 
        if type(data) == TupleType:
            print '       You provided a tuple with the first item a %s and the data item a %s' %(type(data[0]),type(data[1]))
        if type(data) == DictType:
            print '       You provided a dictionary item a with no know entity string' 
        if type(data) == StringType:
            print '       You provided a string item a string with no known data dictionary' 
        if self.data >0: print 'DATA: %s' %data
        return 'Error: data format'        
        
    def setAction(self, action):
        """ set action with any object specific triggered actions  """
        self.action = action
    
    def updateSF(self, data=None, nullEmpty=False):
        """ Update sForce with all the data in this object
            This data may update multiple entities in sForce and may null fields
            ToDo: update all similar entities in the same call
        """
        if data is not None: self.setData(data)
        msg = ''
        for entity in self.data.keys():
            dataL = self.data.get(entity)
            if type(dataL) in seqTypes:
                dataList = dataL
            else:
                dataList = [dataL]
            
            ret = self.sfb.update(entity, dataList, nullEmpty=nullEmpty)
            if ret in [None,[],{},'fail']:
                print 'ERROR with %s update %s' %(self.entity, ret)
                return None
            else:
                msg += 'Updated %s ret:%s' %(entity, ret)
        return msg

class sForceApi3(SFEntitiesMixin, SFUtilityMixin, SFTestMixin):
    """ This class provides basic sForce API capabilities 
    """
    entityTS = 0
    data = {}
    entity = ''
    home = os.environ.get('USER')
    em = sfEntities()
    
    
    def __init__(self, username=None, upass=None, dlog=None, debug=0, logname='sf3.base'):
        """ Creates the API access object and logs in as admin user
            ToDo: change this to use the client 'cookie' from first API
        """
        self.debug = int(debug)
        defNS = 'http://partner.soap.sforce.com'
        soapEndpoint = "https://na1.salesforce.com/services/Soap/u/4.0"
        #soapEndpoint = "https://prerelease.salesforce.com/services/Soap/u/4.0"
        kw = {}
        kw['nsdict'] = {"tns":"urn:partner.soap.sforce.com",
                        "ens":"urn:sobject.partner.soap.sforce.com",
                        "fns":"urn:fault.partner.soap.sforce.com",
                        "soap":"http://schemas.xmlsoap.org/wsdl/soap/"}
        self.startTime = time.time()
        self.entityList = []
        self.entityTS = 0
        self.dlog = dlog
        self.logname=logname
        self.action = 'update'

        
        self.sfdc = sfsv.SforceServiceLocator().getSoap(portAddress=soapEndpoint)
        
        self.defaults = {'errorUId':'00530000000cCy5'
                        ,'errorCId':'00330000001Ud4D'
                        ,'userEmpNum':'00002'
                        ,'mgrEmpNum':'00003'
                        }
        self.adminInfo ={'mail': 'salesforce-support@molten-magma.com',
                         'uid': '00530000000c9tkAAA',
                         'cid': '00330000001UZ8QAAW',
                         'name': 'Salesforce Support'
                        }
        self.entityRefreshSecs = 6000
        self.entityRefreshLast = 0
        # get a configuration object handle to ConfigFile based user information
        self.getConfig()
        self.sfc.set('sForce3','debug',2)
        #self.sfc.writeMy()
        self.loginRetry = 0
        self.loginSF()

        home = os.environ.get('USER')
        
        
    def loginSF(self, user=None):
        """ login to the sForce API server """
                
        admUsername = "sfbatch@molten-magma.com"
        admPassword = "sf@magma05"

        self.connectuname = admUsername
        if (sys.platform != 'win32'):
            if os.isatty(sys.stdout.fileno()):
                self.getUserAuth()
    
                self.connectuname = self.username
        
        self.admLoginRequest = sfsv.loginRequestWrapper()

        # process the regular user login
        self.loginRequest = sfsv.loginRequestWrapper()

        # Only log in as admin user now... :-(
#        for umode in ['cookie','admin']:
        for umode in ['admin']:
            if umode == 'cookie':
                username = self.username
                password = self.password
                if self.debug > 1:print 'Connecting as %s' %self.username
            elif umode == 'admin':
                username = admUsername
                password = admPassword
            
            self.username = username
                
            self.loginRequest._username = username
            self.loginRequest._password = password
            if self.debug > 2:
                print 'Connecting to %s' %sfsv.SforceServiceLocator().getSoapAddress()
            print 'self.loginRequest=%s' % self.loginRequest
            try: 
                self.loginResponse = self.sfdc.login(self.loginRequest)
                break
            except Exception,e:
                exc_info = sys.exc_info()
                info_string = '\n'.join(traceback.format_exception(*exc_info))
                print info_string
                es = '%s'%e
                if es.find('INVALID_LOGIN: user not valid') != -1:
                    print 'Login Error: username:%s could not be found err:%s'%(username,es)
                else:
                    print 'Login Error %s e:%s username:%s' %(Exception,es,username)
            
        if not hasattr(self, 'loginResponse'):
            print 'Not connected to SalesForce, Exiting now\n'
            sys.exit(1)

        self.surl = self.loginResponse._result._serverUrl
        self.sid  = self.loginResponse._result._sessionId
        self.connectuid  = self.loginResponse._result._userId

        self.sfdc = sfsv.SforceServiceLocator().getSoap(portAddress=self.surl)

        uid = self.getUserIdByUsername(self.connectuname)
        if uid is None:
            uid = self.connectuid
        self.uid = uid
        
        if self.debug > 3:
            print 'Logged in as %s' %self.uid
            print 'New url is   %s' %self.surl
            print 'SessionID is %s' %self.sid

        if self.debug > 2:
            print 'Connected as %s for %s in %s secs' \
                  %(self.connectuid, self.uid, time.time()-self.startTime)
        
        
        if self.dlog is not None:
            #self.sfdc.binding.trace = self.dlog
            pass
        elif self.debug > 2:
            try: 
                tf = file('soap.trace', 'w+')
                self.sfdc.binding.trace = tf
            except: pass
        # self.sfdc.binding.SetNS(defNS)
        
    def getConnectInfo(self, version='3.0', startTime=None):
        """  return connection information
        """
        if startTime is not None: secs = time.time() - startTime
        else:                     secs = 0
        if self.action == 'update': act = 'u'
        else:                       act = 't'
        apiName = self.username
        uname = self.username
        if apiName == 'sfbatch@molten-magma.com': mode = 'a'
        else:                                 mode = 'u'
        
        if uname != apiName:
            msg = ' Connected to SalesForce as %s script ver %s in %0.1f secs %s%s%s' \
                  %(uname, version, secs, mode, act, self.debug)
        else:
            msg = ' Connected to SalesForce with script ver %s in %0.1f secs %s%s%s' \
                  %(version, secs, mode, act, self.debug)
        self.setLog(msg,'info')
        print msg
        return uname
    
    
    def getConfig(self):
        self.sfc = SFConfig()
        self.sfc.load()       # load all possible configuration file and create initial file for user
        return self.sfc
            
    
    def getUserAuth(self):
        """ get the user authentication credentials from their config file or set them """
        self.sfc = self.getConfig()
        username = self.sfc.get('sForce3', 'username')
        if self.debug>2:print 'getUserAuth for sForce3 username is >%s<'%username
        if username in [None,''] or username[:6] in ['unknow','error:']:
            self.setUserAuth()
        self.username = username
        password = self.sfc.getPrivate('sForce3', 'password')
        if password[:6] in ['unknow','error:']:
            self.setUserAuth()
        self.password = password
        if self.debug >3: print 'From Config Read Username:%s ' %(self.username)
        if self.username in [None, ''] or self.password in [None, '']: 
            self.setUserAuth()
        
        
    
    def setUserAuth(self):
        """ Prompt the user for their password and store it in their configuration file"""
        userPwd = self.getOldPwFile()
        if userPwd != ['','']:
            self.username = userPwd[0]
            self.password = userPwd[1]
            if self.debug>3: print 'Found v1 file cookie as %s username is %s'%(userPwd,self.username)
            self.sfc.set('sForce3','username', self.username)
            self.sfc.setPrivate('sForce3','password', self.password)
            self.sfc.writeMy()
        else:
            print '*******************************************'
            print 'Please enter your username and password for'
            print '\tSalesforce.com below...\n'
            print '*******************************************'
            username = raw_input( "User Name:  ")
            if username.find('@') == -1:
                username = '%s@molten-magma.com' %username
                print 'I assume you mean %s is your SalesForce username' %username
            import getpass
            password = getpass.getpass()
            self.sfc.setPrivate('sForce3','password', password)
            self.sfc.set('sForce3','username', username)
            self.sfc.writeMy()
            self.username = username
            self.password = password

    def getOldPwFile(self):
        """ get the username and password out of the old .sfdcLogin file """
        pwFilePath = os.path.join( os.getenv('HOME'), '.sfdcLogin')
        result = ['','']
        if os.path.isfile( pwFilePath ):
            pwFile = open( pwFilePath, 'r')
            for line in pwFile.readlines():
                lineStr = line.strip()
                lineArray = lineStr.split()
                if lineArray[0] == 'Username':
                    result[0] = lineArray[1]
                if lineArray[0] == 'Password':
                    result[1] = base64.decodestring(lineArray[1])
        return result
    

    def getSessionHeader(self):
         header = '''\
<ns1:SessionHeader SOAP-ENV:mustUnderstand="0" xmlns:ns1="SoapService">
    <ns2:sessionId
xmlns:ns2="urn:partner.soap.sforce.com">%s</ns2:sessionId>
</ns1:SessionHeader>''' %self.sid
         return header
        
    ######################################################################
    #
    #  Basic wrappers around core sForce 3.0 API calls
    #
    ######################################################################
    def getUserInfo(self):
        """ get the information of the current logged in user """


        #print self.sfdc.binding.user_headers
        req = sfsv.getUserInfoRequestWrapper()
        userInfoResult = self.sfdc.getUserInfo(req, auth_header=self.getSessionHeader())
        
        msg =  'Connected as: %s ' %userInfoResult._result._userFullName
        msg += 'At %s ' %userInfoResult._result._userEmail
        msg += 'From %s' %userInfoResult._result._organizationName
        #msg += 'multicurr: %s\n' %userInfoResult._result._organizationMultiCurrency
        return msg

    def getServerTimestamp(self):
        """ get the server timestamp """


        #print self.sfdc.binding.user_headers
        req = sfsv.getServerTimestampRequestWrapper()
        stResult = self.sfdc.getServerTimestamp(req, auth_header=self.getSessionHeader())

        return stResult._result._timestamp

    ######################################################################
    #  Load entity type data structures for use by entity specific calls
    #    Access this info using calls like
    #        all fields  = self.getEntityMap('entityName')['fields']
    #        SOQL filter = self.getEntityMap('entityName')['filters']
    #        field_Info  = self.getEntityMap('entityName')['fieldInfo'].get('ent.fieldName')
    #        type of field = field_Info.get('type')
    #
    ######################################################################
    def getEntityMap(self, entity, reset=False):
        """ main accessor for getting entity information
        """
        if self.debug > 2: print 'Information for %s loaded %3d secs ago' %(entity, self.em.getAge(entity))
        if reset: self.em.reset(True)
        if self.em.isStale(entity):
            if self.debug > 2: print 'Updating sop for %s' %entity
            self.setEntityMap(entity)
            if reset: self.em.reset(False)
        return self.em.getEntity(entity)
  
    def getEntities(self):
        """ get the latest entitiy list
        """
        now = time.time()
        if self.entityRefreshLast + self.entityRefreshSecs < now:
            self.entityList = self.describeGlobal()
            self.entityRefreshLast = now
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
    #     Basic local caching of entiy information for quick access, Non volitile info like User/Contact info
    ##################################################################################################
    def getCache(self, key, data={}, reset=False):
        """ main accessor for getting cache information
        """
        if not hasattr(self, 'cache'):
            home = os.environ.get('USER')
            self.cache = sfCache()
        if self.debug > 2: print 'Load status for %s loaded %3d secs ago' %(key, self.cache.getAge(key))
        if reset: self.cache.reset(True)
        if self.cache.isStale(key):
            if self.debug > 2: print 'Updating SOP Cache for %s' %key
            self.setCache(key, data)
            if reset: self.cache.reset(False)
        return self.cache.getData(key)

    def delCache(self, key):
        """ delete specific cache value
        """
        return self.cache.delData(key)

    def setCache(self, key, data={}):
        """ load the latest data for the key into a simple object persitence dictionary
        """
        st = time.time()
        if data in [None,{},[],'']:
            data = {'loadStatus':'new'}
        
        self.cache.setData(key, data)
        self.cache.commit()
        if self.debug > 0: print '%2d sec Set %s keys and in %s' %(time.time()-self.startTime, len(data.keys()), key)

        
    ##################################################################################################
    #         Modifying Data calls: update, create, delete
    #
    ##################################################################################################
    def updateBase(self, entity, data=[{}], nullEmpty=False):
        """ basic wrapper around update, entity and data is required, id must be in data
        """
        ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'', 'req':'', 'result':[]}
        if type(data) not in seqTypes:
            data = [data]
        if data in [[{}],[]]: 
            ret['errMsg'] = 'Error:Update, you must provide some data'
            return ret

        req = sfsv.updateRequestWrapper()
        ret = self.loadSendObj( req, entity=entity, dataList=data, nullEmpty=nullEmpty, default={})
        if not ret.get('success', False):
            msg = 'Problem with Loading data for Update %s API call, found:%s ' %(entity, ret.get('errMsg'))
            if self.debug >1: print msg
            return ret
        if ret.get('errCode','') in ['warn','data','field']:
            if self.debug >1: print 'Data load Warning in update of %s\n\t %s' %(entity, ret.get('errMsg',''))
            
        req = ret.get('req')
        try: 
            resp = self.sfdc.binding.Send(None, None, req, nsdict=None, auth_header=self.getSessionHeader())  #,_args=obj
# this is likely totally useless,
            if hasattr(resp, '_result'):
                result = resp._result[0]
                success = result._success
                if success in [False,'false']:
                    errors = result._errors
                    errMsg, statCode = errors._message, errors._statusCode
                    return self._showSubmitErrors(entity, errMsg, statCode, data)
        except Exception,e:
            return self._checkSendErrors(ret, Exception, e, data, 'update', entity)

        try:   
            resp = self.sfdc.binding.Receive(sfsv.updateResponseWrapper())
            if hasattr(resp, '_result'):
                result = resp._result[0]
                success = result._success
                if success in [False,'false']:
                    errors = result._errors
                    errMsg, statCode = errors._message, errors._statusCode
                    return self._showSubmitErrors(entity, errMsg, statCode, data)
        except Exception,e:
            return self._checkSendErrors(ret, Exception, e, data, 'update', entity)
        
        return self.checkResults('update', resp, ret, entity, data)
    
    def checkResults(self, method, resp, ret, entity, data):
        """ common parsing of the receive object with error checks """
        results = resp._result
        resultIDs = []
        index = 0
        for result in results:
            success = result._success
            ido = result._id
            id = '%s'%ido            # should we directly extract the id from the object?
            resultIDs.append(id)
            errors = result._errors
            if success in [True,'true']:
                ret['success'] = True
                ret['errCode'] = 'success'
                ret['msg'] = 'Sucessful %s %s with %s fields' %(method, id, len(data[index].keys()))
                ret['errMsg'] = 'Success:Update id:%s Err:%s l:%s' %(id, errors, ret['errMsg'])
            else:
                ret['errCode'] = 'fail'
                if hasattr(errors, '_fields'): 
                    ret['errMsg'] += errors._fields
                if hasattr(errors, '_message'): 
                    ret['errMsg'] += errors._message
                if hasattr(errors, '_statusCode'): 
                    ret['errMsg'] += 'statusCode:%s' %errors._statusCode
                ret['success'] = False
                ret['errMsg'] = 'Error:%s id:%s Err:%s l:%s' %(method, id, errors, ret['errMsg'])
            index += 1
        
        ret['result'] = resultIDs
        return ret


    def createBase(self, entity, data=[{}], nullEmpty=False):
        """
        basic wrapper around create, entity and data is required
        useAdm is a flag which, if true, uses the admin login to execute
        the call.
        """
        ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'',
               'req':'', 'result':[]}
        if type(data) not in seqTypes:
            data = [data]
        if data in [[{}],[]]: 
            ret['errMsg'] = 'Error:Update, you must provide some data'
            return ret

        req = sfsv.createRequestWrapper()
        ret = self.loadSendObj( req, entity=entity, dataList=data, nullEmpty=nullEmpty, default={}, create=True)

        if not ret.get('success', False):
            msg = 'Problem with Loading data for Create %s API call, found:%s ' %(entity, ret.get('errMsg'))
            self.setLog(msg, 'error')
            if self.debug >1:
                print msg
            return ret
        
        if ret.get('errCode','') in ['warn','data','field']:
            msg = 'Data load Warning in create of %s\n\t %s\ndata: %s' \
                  %(entity, ret.get('errMsg',''), data)
            self.setLog(msg, 'warn')

            if self.debug >1:
                print msg
            
        req = ret.get('req')

        try: 
            resp = self.sfdc.binding.Send(None, None, req, nsdict=None, auth_header=self.getSessionHeader())  #,_args=obj
            # pregnant pause
            resp = self.sfdc.binding.Receive(sfsv.createResponseWrapper())
        except Exception,e:
            return self._checkSendErrors(ret, Exception, e, data, 'create', entity)

        results = resp._result
        resultIDs = []
        index = 0
        for result in results:
            success = result._success
            ido = result._id
            id = '%s'%ido            # should we directly extract the id from the object?
            resultIDs.append(id)
            errors = result._errors
            #errFields, errMsg, errCode = errors._fields, errors._message, errors._statusCode
            if success:
                ret['success'] = True
                ret['errCode'] = 'success'
                ret['msg'] = 'Sucessfully created %s with %s fields' %(id, len(data[index].keys()))
                ret['errMsg'] = 'Success:Update id:%s Err:%s l:%s' %(id, errors, ret['errMsg'])
            else:
                ret['success'] = False
                ret['errCode'] = 'fail'
            ret['errMsg'] = 'Error:Create id:%s Err:%s l:%s' %(id, errors, ret['errMsg'])
            index += 1
            
        ret['result'] = resultIDs
        return ret

    def deleteBase(self, ids=[]):
        """ basic wrapper around delete
        """
        ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'',
               'req':ids, 'result':[]}
        
        if type(ids) not in seqTypes:
            ids = [ids]
        if ids in [(),[]]: 
            ret['errMsg'] = 'Error:Delete, you must provide some ids'
            return ret

        req = sfsv.deleteRequestWrapper()
        req._ids = ids
        try:
            #,_args=obj
            resp = self.sfdc.delete(req, auth_header=self.getSessionHeader())  
        except Exception,e:
            return self._checkSendErrors(ret, Exception, e, ids, 'delete')
        results = resp._result
        resultIDs = []
        index = 0
        for result in results:
            success = result._success
            ido = result._id
            id = '%s'%ido            # should we directly extract the id from the object?
            resultIDs.append(id)
            errors = result._errors
            errMsg =''
            if type(errors) in seqTypes:
                for error in errors:
                    if error is None: continue
                    if hasattr(error, '_fields'):
                        errFields, errMsg, errCode = error._fields, error._message, error._statusCode
                        errMsg += 'fields:%s Code:%s Msg:%s' %(errFields, errMsg, errCode)
            if success:
                ret['success'] = True
                ret['errCode'] = 'success'
                ret['msg'] = 'Sucessfully deleted %s' %(id)
                ret['errMsg'] += 'Success:Deleted id:%s Err:%s %s' %(id, errors, errMsg)
            else:
                ret['success'] = False
                ret['errCode'] = 'fail'
                ret['errMsg'] += 'Error:Deleting id:%s Err:%s l:%s' %(id, errors, errMsg)
            index += 1
        ret['result'] = resultIDs
        return ret

    def _showSubmitErrors(self, entity, errMsg, statCode, data):
        """ try to put some logic around how to handle field update driven error """
        ret['success'] = False
        ret['errMsg'] = errMsg
        if statCode.find('INVALID_TYPE_ON_FIELD_IN_RECORD') != -1:      # handle incorrect fields
            ret['errCode'] = 'fieldType'
            return ret
        elif statCode.find('Non-optional string missing') != -1:      
            if self.debug>0: print 'SubmitErrors:Data for %s was:%s' %(entity,data)
            ret['errCode'] = 'data'
            return ret
        else:
            ret['errCode'] = 'data'
            if self.debug>0: print 'SubmitErrors:Data for %s was:%s' %(entity,data)
            return ret
        

    def _checkSendErrors(self, ret, exception, e, data={}, method='', entity=''):
        """ try to make some sense out of the strings coming back from the ZSI exception calls"""
        ret['success'] = False
        es = '%s' %e
        el = es.split(':')        #always three better check!!
        if len(el) > 3:   ftype, fname, fdet, trace = el[0], el[1], el[2], el[3:]
        elif len(el) > 2: ftype, fname, fdet, trace = el[0], el[1], el[2], 'no trace'
        elif len(el) > 1: ftype, fname, fdet, trace = el[0], el[1], es, 'no trace'
        elif len(el) > 0: ftype, fname, fdet, trace = el[0], el[0], es, 'no trace'
        ret['req'] = data
        ret['errMsg'] = 'n:%s t:%s d:%s l:%s' %(fname, ftype, fdet, ret['errMsg'])
        errors = {}
        if self.sfdc.binding.ps:
            errors = _child_elements(self.sfdc.binding.ps.body_root)
        if hasattr(errors, '_fields'): 
            ret['errMsg'] += errors._fields
        if hasattr(errors, '_message'): 
            ret['errMsg'] += errors._message
        if hasattr(errors, '_statusCode'): 
            ret['errMsg'] += 'statusCode:%s'%errors._statusCode
  
        if self.debug >1: print 'Error %s of %s err:%s %s errMsg:%s\n' %(method,entity, e, Exception, ret['errMsg'])
        
        if fdet.find('No such column:') != -1:      # handle incorrect fields
            return ret
        elif fdet.find('Non-optional string missing') != -1:      # handle incorrect fields
            if self.debug>0: print 'SendErrors:Data was:%s' %data
            return ret
        else:
            if self.debug>0: print 'SendErrors:Data was:%s' %data
            return ret
        

    def loadSendObj(self, req, entity, dataList=[{}], nullEmpty=False, default={}, create=False):
        """ basic wrapper around the loading of the ZSI proxy object by updating the ofWhat attribute on the typecode object
            Makes us of the sop entityMap loaded with entity and filed constraints.  A number of basic type constraines are supported
            used by create and update
            Provide:
               req    = default request object for create or update call
               entity = type of sForce entiy to query entityMap, all data MUST be same entity type
               data   = dictionary with all field values (ID is required)
               nullEmpty = True|False to indicate if fields not in data will be deleted on server
               default = dictionary of fields and values that will be used for any matching empty fields in data
                          (still do not know how to handle combo of nullEmpty and default, will return later)
            Returns results dictionary with:
               success = True|False
               errCode = warn|data|field|fail - Fail will not allow object to be used others eliminate offending info from object
               errMsg  = text version of what is not right
               req     = request object with updated sObject list, ofWhat list and field data set on sObjects
        """
        ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'', 'req':req, 'result':[]}
        emap = self.getEntityMap(entity)   # the emap is updates every hour from the sForce server
        fields = emap['fields']            # list of available fields, Note may not be updatable 
        required = emap['required']        # list of field required to have a value during create or save
        fInfo = emap['fieldInfo']          # dictionary of field info, updatable, type, etc..
        if emap.get('updateable',0) == 0:
            msg = 'ERROR: You cannot Update an entity of type %s based on the results of the describesObject call' %entity
            print msg
            ret['errMsg'] = msg
            return ret
        if default == {}:
            default = self.getDefaults()
            
        def setFieldInfo(obj, k, dd):
            fi = fInfo.get(k,'')
            fn = '_%s'%k
            ftype = fi.get('type')                       # type of this field
            #print "ftype is %s" %ftype
            if ftype in ['date','datetime']:             # should I treat date differently or is it silently truncated? have TC.gDate
                fp = ZSI.TCtimes.gDateTime(k, aname=fn)
                setattr(obj, fn, dd.get(k,''))
            elif ftype in ['boolean']:
                fp = ZSI.TC.Boolean(k, aname=fn)                # not tested
                if dd.get(k,'') not in [None,'','false']:
                    setattr(obj, fn, dd.get(k,''))
            elif ftype in ['i4','int']:                  
                digits = fi.get('digits',8)                     # not tested should truncate to number of digits
                fp = ZSI.TC.Integer(k, aname=fn, format='%u')
                setattr(obj, fn, dd.get(k,''))
            elif ftype in ['email']:                            # the api give a weird error if the email is bad format, check here
                fp = ZSI.TC.String(k, aname=fn)
                setattr(obj, fn, dd.get(k,''))
            elif ftype in ['url','string','textarea','phone','id','reference']:  # might want to check on id and references
                fp = ZSI.TC.String(k, aname=fn)
                setattr(obj, fn, dd.get(k,''))
            elif ftype in ['percent','currency']:
                digits = fi.get('digits',8)
                precision = fi.get('precision',8)                  # total width of number without decimal
                scale = fi.get('scale',2)
                format = '%%0.%sf'%scale
                fp = ZSI.TC.Double(k, aname=fn, format=format)     # not tested
                setattr(obj, fn, dd.get(k,''))
            elif ftype in ['double','decimal','float']:
                precision = fi.get('precision',3)                  # total width of number without decimal
                scale = fi.get('scale',2)
                format = '%%0.%sf'%scale
                fp = ZSI.TC.Double(k, aname=fn, format=format)     # simple subclass of ZSI.TC.Decimal with type set to double
                #fp = ZSI.TC.Decimal(k, aname=fn, format=format)   # sForce API does not support decimal only double
                setattr(obj, fn, dd.get(k,''))
            elif ftype in ['combobox','picklist']:
                if self.debug >2: 
                   msg = 'Warning %s type field Information %s in %s of %s ' %(ftype, k, index, entity)
                   ret['errMsg'] += msg
                   print msg
                fp = ZSI.TC.String(k, aname=fn)
                setattr(obj, fn, dd.get(k,''))
            elif ftype in ['base64']:
                fp = ZSI.TC.Base64String(k, aname=fn)
                setattr(obj, fn, dd.get(k,''))
            else:
                fp = ZSI.TC.String(k, aname=fn)
                setattr(obj, fn, dd.get(k,''))
            
            
            return fp, obj
            
        index = 0
        objs = []
        okToSkipFields = ['OwnerId'] # Fields that aren't really required
        
        for data in dataList:
            obj = ns1.sObject_Def(entity)
            if index == 0:
                ow = list(obj.ofwhat)               # get original ofwhat objects
            index +=1

            if not create:
                id = data.get('id','')
                if id in [None, '']:
                    id = data.get('Id','')
                    if id in [None, '']:
                        id = data.get('ID','')
                        if id in [None, '']:
                            ret['errMsg'] += 'Error:loadSendObj Missing id field from %s data %s ' %(entity, data)
                            return ret
                obj._Id = id
            obj._type = entity
            ofwhatList = []
            warnMsg = ''
            for k in data.keys():
                if k in ['id','Id','ID']: continue
                if k not in fields:
                    msg = '\tSkipping unknown field:%s in %s of %s\n' %(k, index, entity)
                    warnMsg += msg
                    ret['errMsg'] += msg
                    if self.debug >1: print msg
                    continue
                else:
                    fi = fInfo.get(k,'')
                    if fi == '':
                        msg = '\tSkipping missing field:%s in %s of %s\n' %(k, index, entity)
                        ret['errMsg'] += msg
                        warnMsg += msg
                        if self.debug >2: print msg
                        continue
                    if k in required:
                        required.remove(k)
                        if self.debug >3: print 'Found required field %s' %k
                        
                    if fi.get('updateable') != 1 and not create:
                        if k not in ['SystemModstamp','LastModifiedDate','CreatedById','CreatedDate','LastModifiedById']:
                            msg = '\tSkipping non-updatable field:%s in %s of %s\n' %(k, index, entity)
                            ret['errMsg'] += msg
                            warnMsg += msg
                            if self.debug >2: print msg
                        continue
                    fp, obj = setFieldInfo(obj, k, data)
                    ofwhatList.append(fp)
            
            for k in required:
                if default.has_key(k):
                    if k in okToSkipFields and create is False:
                        pass
                    else:
                        fp, obj = setFieldInfo(obj, k, default)
                        ofwhatList.append(fp)
                        msg = 'Required field %s is missing! Using %s from defaults' %(k, default.get(k))
                        ret['errMsg'] += msg
                        if self.debug >2: print msg
                else:
                    fi = fInfo.get(k,'')
                    if create:
                        if fi['type'] != 'boolean':
                            msg = 'ERROR:Required field: %s is missing! Also %s, This create will be abandoned\n' %(k, required)
                            ret['errMsg'] += msg
                            ret['errCode'] = 'fail'
                            return ret
                        msg = "non-nillable Boolean field %s missing. This create will be attempted anyway" %(k)
                        ret['errMsg'] += msg
                    elif fi != '' and fi.get('updatable') != 1:
                        ret['errMsg'] += '\tRequired but non-updatable field was skipped\n'
                        pass
                    else:
                        msg = 'Required field: %s is missing! This update will be attempted anyway\n' %(k)
                        ret['errMsg'] += msg
                        if self.debug >2: print msg
                
            if self.debug > 3:print '----------------------------------obj information-----------------------------------------\n'
            if self.debug > 3:print obj.__dict__
            if self.debug > 3:print '------------------------------------------------------------------------------------------\n'
            objs.append(obj)                             # keep the object!!
                
        if warnMsg != '':
            #ret['errMsg'] = ret['errMsg'] + warnMsg
            ret['errCode'] = 'warn'
            
        ow.extend(ofwhatList)
        req.typecode.ofwhat[0].ofwhat = ow  # replace ofwhat list with our new updates list
        if self.debug > 3:print '-------------------------------new request.typecode ofwhat---------------------------------\n'
        if self.debug > 3:print '%s' %req.typecode.ofwhat[0].ofwhat
        req._sObjects = objs                 # add update sObject with new attributes to request object
        ret['success'] = True
        ret['req'] = req
        return ret


    ##################################################################################################
    #   Search and Retrieval calls: query, retrieve, search
    #    -Return a list of results, each result is a dictionary of item data
    #    -empty list inicates no results, errors MAY be returned in first dictionary item
    #
    ##################################################################################################


    ##################################################################################################
    #  SOQL query methods
    #  SELECT [List of Field Names] IN EntityName 
    #         WHERE FieldName = 'value' AND FieldName >= 'value' OR FieldName != ''
    #
    ##################################################################################################
    def queryBase(self, entity, where=[('LastName','like','vanek',)], sc='', soql=None, limit=200):
        """ search sForce using SOQL with some query building shortcuts
            using entity name and a set of shorcut strings for common list of return fields (fewer fields is faster!)
            CV June 1, 2004 Need to review error handling
        """
        ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'',
               'req':soql, 'result':[]}
        if soql is None:
            if entity in [None, '']: entity = 'Contact'
            if entity not in self.getEntities():
                ret['errMsg'] = 'Bad Boy! %s not in valid entity list' %entity
                return ret

            if sc in [None,'']: sc = 'all'
            if sc not in ['all','filters','fields']:    
                query = self.getSOQLEntityShortcut(sc, entity)
                if query in [None,'',{}]:
                    self.setLog('Query: Bad SC:%s using all for %s where:%s'%(sc,entity,where),'error')
                    filter = self.getEntityMap(entity)['fields']
                    query = 'SELECT %s from %s '%(','.join(filter), entity)
                    
            elif sc == 'fields':
                filter = self.getEntityMap(entity)['fields']
                query = 'SELECT %s from %s '%(','.join(filter), entity)
            else:
                filter = self.getEntityMap(entity)['filters']
                query = 'SELECT %s from %s '%(','.join(filter), entity)
                
            if type(where) == type(''):                  
                where = self.getSQOLWhereShortcut(where)  # expand shortcut strings into where lists
                
            whereStr = 'WHERE '
            fInfo = self.getEntityMap(entity)['fieldInfo']
            if type(where) in seqTypes:
                for wexp in where:
                    if type(wexp) in seqTypes:
                        field = wexp[0]
                        oper =  wexp[1]
                        value = wexp[2]
                        fieldInfo = fInfo.get(field,{})
                        ftype = fieldInfo.get('type')
                        if self.debug>2: print 'Where triple %s of type %s value:%s'%(field,ftype,value)
                        if ftype in ['date','datetime','double','boolean']:
                            whereStr += "(%s %s %s)" %(field, oper, value)
                        else:
                            whereStr += "(%s %s '%s')" %(field, oper, value)
                    elif wexp.lower() in ['and', 'or', 'not', '(', ')']:
                        whereStr += " %s " %wexp       # usually just and
                    elif len(where) == 3 and type(wexp) == type(''):
                        # if they just pass in a 3 item list ['CaseNumber','like','24544']
                        if where[1] in ['like']:
                            ss = where[2]
                            if ss in [None,'',[]]:
                                print 'WARNING: badly formed Query WHERE clause of %s'%where
                                ss = ''
                            else:
                                if ss[0] != '%': ss = '%'+ss
                                if ss[-1] != '%': ss = ss+'%'
                            whereStr += "%s %s '%s' " %(where[0], where[1], ss)
                        else:
                            field = where[0]
                            fieldInfo = fInfo.get(field,{})
                            ftype = fieldInfo.get('type')
                            if ftype in ['date','datetime']:
                                if self.debug>2: print 'Where Clause DateTime of %s for %s'%(where[2], field)
                                whereStr += "%s %s %s " %(field, where[1], where[2])
                            else:
                                if self.debug>2: print 'Where element %s of type %s value:%s'%(field,ftype,where[2])
                                whereStr += "%s %s '%s' " %(field, where[1], where[2])
                        break
                    else:
                        if self.debug >0: print 'Adding raw string" %s TO %s' %(wexp, whereStr)
                        whereStr += " %s " %wexp
                        #return ret
            else:
                whereStr += where
                # from command line?
            
            if self.debug >2: print 'Using SOQL WHERE clause of: %s' %whereStr
                                          
            soql = "%s %s" %(query, whereStr)
            if self.debug >2: print 'Using SOQL: %s' %soql
            ret['msg'] = 'Search clause of %s' %whereStr
            ret['req'] = soql

        ret = self._getBySOQL(soql=soql, ret=ret, limit=limit, entity=entity)

        return ret
        
    def getSQOLWhereShortcut(self, sc=''):
        """ convert some shortcut strings into valid WHERE clause
             Output is a a list of clause triplets and operators [and, or, not]
        """
        if sc in [None, '']: sc = 't1'
        if sc in ['t1']:
            sc = [['Email','like','ab@yahoo.com'], 'and',  ['Title', '!=', '']]
        elif sc in ['broadcom']:
            sc = [['Subject','like','%com%']]
        return sc

    def getSOQLEntityShortcut(self, sc, entity='Case'):
        """ Convert a shortcut string into a valid SOQL string
          format: SELECT fieldList from objectType 
        """
        allCont = self.getEntityMap('Contact')['filters']       # should use fields
        allUser = self.getEntityMap('User')['filters']
        allCase = self.getEntityMap('Case')['filters']
        allTask = self.getEntityMap('Task')['filters']
        u1  = ('Email', 'FirstName', 'LastName', 'Phone', 'Reports_To__c',
               'Id')
        user= ('Alias', 'City', 'CompanyName', 'Country', 'Department',
               'Division', 'Email', 'EmployeeNumber', 'Ex_Employee__c',
               'FirstName', 'Id', 'IsActive', 'LastLoginDate', 'LastName',
               'MobilePhone', 'Phone', 'PostalCode', 'Reports_To__c', 'State',
               'TimeZoneSidKey', 'Title', 'Username', 'UserRoleId')
        cont= ('AccountId', 'Business_Unit__c', 'ContactStatus__c',
               'ContactsWithoutEmpNum__c', 'Department' ,'Dept__c', 'Email',
               'EmployeeNumber__c', 'FirstName', 'Id', 'LastName',
               'MailingPostalCode', 'MailingState', 'Mods_Approved_By__c',
               'RecordTypeId', 'ReportsToId', 'Title')
        cr1 = ('CaseNumber', 'Code_Streams_Priority__c', 'Status', 'Subject',
               'Id' )
        com = ('Subject','Id' )

        if type(sc) in [ListType, TupleType]:
            fieldList = []
            fieldList.extend(sc)
            if 'Id' not in fieldList:
                # ensure that we always select 'Id'
                fieldList.append('Id')
            soql = 'SELECT %s from %s' %(','.join(fieldList), entity)
        elif sc in ['contacts','contact']:   
            soql = 'SELECT %s from Contact'%','.join(cont)
        elif sc in ['call']:   
            soql = 'SELECT %s from Contact'%','.join(allCont)
        elif sc in ['uall']:   
            soql = 'SELECT %s from User'%','.join(allUser)
        elif sc in ['user']:   
            soql = 'SELECT %s from User'%','.join(user)
        elif sc in ['mall']: 
            soql = 'SELECT %s from Task' %','.join(allTask)        
        elif sc in ['cr1']: 
            soql = 'SELECT %s from Case'%','.join(cr1)
        elif sc in ['case']: 
            soql = 'SELECT %s from Case'%','.join(allCase)
        elif sc in ['com']: 
            soql = 'SELECT %s from Case' %','.join(com)
        else:
            print 'Unknown return entity shortcut %s' %sc
            soql = ''
            
        if self.debug >3: print 'SOQL for %s is: %s' %(sc, soql)
        return soql




    def _getBySOQL(self, soql=None, ret={}, limit=200, allowNulls=False, entity=''):
        """ search sForce using SOQL return dictionary of data
        """
        req = sfsv.queryRequestWrapper()
        req._queryString = '%s' %soql
        if self.debug>4: print 'Querying using the SOQL %s' %(soql)
        try: 
            #resp = self.sfdc.query(req, auth_header=self.getSessionHeader())
            resp = self.sfdc.binding.Send(None, None, req, soapaction="", auth_header=self.getSessionHeader())
            resp = self.sfdc.binding.Receive(sfsv.queryResponseWrapper())
        except Exception,e:
            msg = '_getBySOQL:Error %s e:%s' %(Exception,e)
            ret['errMsg'] = msg
            e = '%s'%e
            if e.find('INVALID_FIELD: No such column') != -1:
                print '\nThe definition of the fields for %s changed in sForce' %entity
                em = self.getEntityMap(entity, reset=True)
                print 'Error:%s'%e
                print 'Found Problem: Please ask Salesforce-support to:'
                print ' Reset the API cache for %s, this should fix this'%entity
            elif e.find('INVALID_FIELD: value of filter') != -1:
                print 'The format of your Where clause is wrong.  Follow one of the examples below.'
                print '  CaseNumber like \'25455\'                       NOTE \'\' around value are important'
                print '  BranchLabel__c like \'blast4.1_michel_29396\' '
            elif e.find(' malformed query') != -1:
                print 'ERROR: You have provided a bad query string, review the SOQL below and retry your query\n'
                print soql
                print '\nERROR: review the SOQL above and change your command parameters\n'
                
            elif e.find('INVALID_SESSION_ID') != -1:
                print 'This Session TimedOut, doing another login retry:%s'%self.loginRetry
                if self.loginRetry > 20:
                    print 'Too many login retries just exiting now'
                    sys.exit(1)
                else:
                    self.loginSF()
                    print 'Should be logged in again as %s' %self.username
                    print 'Retrying SOQL %s'%soql
                    return self._getBySOQL(soql=soql, ret=ret, limit=limit, allowNulls=allowNulls, entity=entity)
                
                
            
            else:
                print msg
            traceback.print_exc ()
            return ret
        returnList = []
        #print 'QRaw data:%s\n'% sfdc.binding.data
        #print 'QRaw Parsed data ps:%s\n'% self.binding.ps
        #print 'QRaw ps.body_root:%s\n'% self.binding.ps.body_root  # queryResponse
        _result = _child_elements(self.sfdc.binding.ps.body_root)
        #pprint.pprint(_child_elements)
        result = _child_elements(_result[0])
        records = []
        done = result[0].nodeValue
        #queryLocator = _attrs(result[1])[0].nodeValue
        size = result[-1].nodeValue
        for r in result:
            if r.localName.find('records') >=0:
                records.append(r)
        if len(records) > 0:
            ret['msg'] += 'Found (%s) records of type %s ' %(len(records), entity)
            for recNode in records:
                rd = _child_elements(recNode)
                kwDict = {}
                #print 'RecNode is %s has %s' %(recNode, rd)
                for d in rd:
                    v = _children(d)
                    #print 'In Record loop, d:%s v:%s' %(d,v)
                    if hasattr(v, 'childNodes'):
                        v2 = _children(v)                  # this should be recursive to handle more then one level
                        kwDict[v.localName] = v2[0].nodeValue
                        if len(v2) > 1:
                            msg = 'What about me!! other elements found in %s  v:%s v2:%s' %(d,v, v2)
                            if self.debug>1: print msg
                            ret['errMsg'] += msg
                    elif len(v) == 0:
                        if allowNulls:
                            kwDict[d.localName] = ''             # partner wsdl returns empty 
                    else:
                        kwDict[d.localName] = v[0].nodeValue
                returnList.append(kwDict)

            ret['result'] = returnList
            ret['success'] = True
            return ret
        else:
            ret['msg'] += 'No Results found for %s' %soql
            return ret


    def retrieveBase(self, ids, entity, fieldList=[], allowNulls=False,
                     asAdm=False):
        """ return data dictionaries for list of ids, used allowNulls to return empty values
            Provide list of ids along with a list of fields you want back
            results are returned as a list in the results key of the returned dictionary (as below)
        """
        if asAdm is True:
            sfdc = self.admSfdc
        else:
            sfdc = self.sfdc
        
        msg = ''
        ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'', 'req':ids, 'result':[]}
        if entity not in self.getEntities():
            ret['errMsg'] = 'Error:Retrieve %s not in valid entity lists' %entity
            return ret
        emap = self.getEntityMap(entity)   # the emap is updates every X mins from the sForce server, x set in sop.py
        allFields = emap['fields']         # list of available fields, Note may not be updatable  

        if fieldList == []:
            retFieldList = allFields
        else:
            retFieldList = []
            for field in fieldList:
                if field not in allFields:
                    ret['errMsg'] += 'Warn: %s not a valid return field ' %field
                else:
                    retFieldList.append(field)
        rfStr = ','.join(retFieldList)
        
        req = sfsv.retrieveRequestWrapper()
        req._fieldList = rfStr
        req._sObjectType = entity
        req._ids = ids
        ret['msg'] = 'Retrieving %s %s with %s fields for ids %s\n' %(len(ids), entity, len(retFieldList), ids)
        try: 
            #resp = sfdc.retrieve(req, auth_header=self.getSessionHeader())
            resp = sfdc.binding.Send(None, None, req, soapaction="", auth_header=self.getSessionHeader())
            resp = sfdc.binding.Receive(sfsv.retrieveResponseWrapper())
        except Exception,e:
            ret['errMsg'] += 'Retrieving:Error %s %s' %(Exception,e)
            import traceback
            traceback.print_exc ()
            return ret
            
        _result = _child_elements(sfdc.binding.ps.body_root)
        if self.debug>2: print '_result is %s' %_result              # list of result nodes
        results =  _result                          #_child_elements(_result[0])
        ret['msg'] += 'Retrieved (%s) %s records ' %(len(results), entity)
        if self.debug >3: print 'RAW:Retrieve response %s' %(results)
        if len(results) == 0:
            ret['msg'] = 'No %s Results found for %s' %(entity,ids)
            return ret

        returnList = []
        for result in results:
            name = result.nodeValue
            records = _children(result)
            if self.debug >2: print 'Found (%s) records in %s ' %(len(records),result)
            if self.debug >3: print 'RAW:Result records %s' %(records)
            kwDict = {}
            for recNode in records:
                rd = _children(recNode)
                if self.debug >6: print 'RecNode is %s has %s' %(recNode, rd)
                key = recNode.localName
                if len(rd) == 0:
                    # Include null values in dictionary?
                    if key is not None and allowNulls:
                        kwDict[key] = ''
                else:   
                    value = rd[0].nodeValue
                    if self.debug >2: print ' nodeName:%s  nodeValue:%s' %(key,value)
                    kwDict[key] = value
            returnList.append(kwDict)
        ret['result'] = returnList
        ret['success'] = True
        return ret


    def getUpdatedBase(self, entity, start=None, end=None):
        """ return data dictionaries for all entity items modified between the start and end times
            Provide start and end time as DateTime object or sec since epoch or string as #####
            results are returned as a list in the results key of the returned dictionary (as below)
            ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'', 'req':ids, 'result':[]}
        """
        msg = ''
        ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'', 'req':entity, 'result':[]}
        if entity not in self.getEntities():
            ret['errMsg'] = 'Error:getUpdated %s not in valid entity lists' %entity
            return ret

        if start in [None,'','now',0]:
            start = time.time() - 60*60*5     # get for the last hour by default
        if end in [None,'','now',0]:
            end = time.time()
        startTuple = self.getDateTimeTuple(start)
        startStr = self.getAsDateTimeStr(start)
        endTuple = self.getDateTimeTuple(end)
        endStr = self.getAsDateTimeStr(end)
        secAgo = end - start
        print 'getUpdated for %s changed in last %s secs, start:%s, end:%s'%(entity,secAgo,start,end)        
        req = sfsv.getUpdatedRequestWrapper()
        #_endDate: tuple
        #_sObjectType: str
        #_startDate: tuple
        req._startDate = start     #int(start)
        req._endDate =   end       #int(end)
        req._sObjectType = entity
        ret['msg'] = 'Retrieving %s updated last %s secs\n' %(entity, secAgo)
        try: 
            #resp = self.sfdc.getUpdated(req, auth_header=self.getSessionHeader())
            resp = self.sfdc.binding.Send(None, None, req, soapaction="", auth_header=self.getSessionHeader())
            resp = self.sfdc.binding.Receive(sfsv.getUpdatedResponseWrapper())
            print 'RESP:%s' %(resp)
        except Exception,e:
            ret['errMsg'] += 'ERROR:getUpdated %s %s' %(Exception,e)
            import traceback
            traceback.print_exc ()
            return ret
            
        print 'QRaw data:%s\n'% self.sfdc.binding.data
        print 'QRaw Parsed data ps:%s\n'% self.sfdc.binding.ps
        print 'QRaw ps.body_root:%s\n'% self.sfdc.binding.ps.body_root  # queryResponse
        _result = _child_elements(self.sfdc.binding.ps.body_root)
        print 'QRaw _result:%s\n'%_result
        result = _child_elements(_result[0])
        
        if self.debug>1: print '_result is %s' %_result              # list of result nodes
        
        results =  _result                          #_child_elements(_result[0])
        ret['msg'] += 'getUpdated (%s) %s records ' %(len(results), entity)
        if self.debug >3: print 'RAW:getUpdated response %s' %(results)
        if len(results) == 0:
            ret['msg'] = 'No %s Updated since %s' %(entity, startTuple)
            return ret

        returnList = []
        for result in results:
            name = result.nodeValue
            records = _children(result)
            if self.debug >2: print 'Found (%s) records in %s ' %(len(records),result)
            if self.debug >3: print 'RAW:Result records %s' %(records)
            kwDict = {}
            for recNode in records:
                rd = _children(recNode)
                if self.debug >6: print 'RecNode is %s has %s' %(recNode, rd)
                key = recNode.localName
                if len(rd) == 0:
                    # Include null values in dictionary?
                    if key is not None and allowNulls:
                        kwDict[key] = ''
                else:   
                    value = rd[0].nodeValue
                    if self.debug >2: print ' nodeName:%s  nodeValue:%s' %(key,value)
                    kwDict[key] = value
            returnList.append(kwDict)
        ret['result'] = returnList
        ret['success'] = True
        return ret

    ##################################################################################################
    #  SOSL query methods
    #    FIND {searchString} IN 'ALL FIELDS|NAME FIELDS|EMAIL FIELDS|PHONE FIELDS'
    #        RETURNING 'FieldSpec' LIMIT #
    #
    ##################################################################################################

    def searchBase(self, sterm, retsc=None, scope='ALL FIELDS', sosl=None, limit=200):
        """ search sForce using SOSL
            FIND {sterm} IN 'ALL FIELDS|NAME FIELDS|EMAIL FIELDS|PHONE FIELDS'
            RETURNING 'FieldSpec' LIMIT #
            eg: Find {MyProspect} RETURNING CustomObject_c(id, CustomField_c)
            CV June 1, 2004 Need to review error handling
        """
        ret = {'success':False, 'msg':'', 'errCode':'fail', 'errMsg':'', 'req':sterm, 'result':[]}
        if sterm in [None,'']: sterm = 'blast'

        if type(retsc) == type(''):                  
            retsc = self.getSOSLFieldSpec(retsc)  # expand shortcut strings into return fieldSpec lists
            
        if type(retsc) in dictTypes:
            retFieldStr = ''
            for entName in retsc.keys():
                entFields = retsc[entName]
                if entName not in self.getEntities():
                    ret['errMsg'] += 'Error:Search RETURNING entity %s is invalid ' %(entName)
                    ret['errMsg'] += '  Valid formats is: CustomObject_c(id, CustomField_c)'
                    ret['errMsg'] += '  Eg: CR_Link__c(id, Customer_Priority, Promise_Date)'
                    return ret
                if retFieldStr == '':
                    retFieldStr = '%s(%s)' %(entName, ','.join(entFields))
                else:
                    retFieldStr += ',%s(%s)' %(entName, ','.join(entFields))
                    
            sosl = 'FIND {%s} IN %s RETURNING %s' %(sterm, scope, retFieldStr)
        else:
            sosl = 'FIND {%s} IN %s' %(sterm, scope)
            
        return self._getBySOSL(sosl, ret, limit=200, allowNulls=False)

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

    
    def _getBySOSL(self, sosl, ret, limit=200, allowNulls=False):
        """  Assume SOSL is correct and do the call
        """
        req = sfsv.searchRequestWrapper()
        req._searchString = '%s' %sosl
        ret['msg'] += 'Searching using %s; ' %(sosl)
        try: resp = self.sfdc.search(req, auth_header=self.getSessionHeader())
        except Exception,e:
            ret['errMsg'] += 'Error:_getBySOSL %s %s; ' %(Exception,e)
            import traceback
            traceback.print_exc ()
            return ret
        returnList = []
        #print 'QRaw data:%s\n'% self.sfdc.binding.data
        #print 'QRaw Parsed data ps:%s\n'% self.binding.ps
        #print 'QRaw ps.body_root:%s\n'% self.binding.ps.body_root  # queryResponse
        _result = _child_elements(self.sfdc.binding.ps.body_root)
        result = _child_elements(_result[0])
        if len(result) > 0:
            srecords = _child_elements(result[0])
            records = []
            allowNulls = True
            if self.debug>3: print 'RAW:Search records: %s' %srecords
            for r in srecords:
                if r.localName.find('record') >=0:
                    records.append(r)
                else:
                    ret['errMsg'] += 'Upexpected element in search results: %s; ' %r
            ret['msg'] += 'Found (%s) records ' %( len(records))
            for recNode in records:
                rd = _child_elements(recNode)
                kwDict = {}
                #print 'RecNode is %s has %s' %(recNode, rd)
                for d in rd:
                    v = _children(d)
                    #print 'In Record loop, d:%s v:%s' %(d,v)
                    if hasattr(v, 'childNodes'):
                        v2 = _children(v)                  # this should be recursive to handle more then one level
                        kwDict[v.localName] = v2[0].nodeValue
                        if len(v2) > 1:
                            ret['errMsg'] += 'What about me!! other elements found in %s  v:%s v2:%s' %(d,v, v2)
                    elif len(v) == 0:
                        if allowNulls:
                            kwDict[d.localName] = ''             # partner wsdl returns empty 
                    else:
                        kwDict[d.localName] = v[0].nodeValue
                returnList.append(kwDict)

            ret['result'] = returnList
            ret['success'] = True
            return ret
        else:
            ret['errCode'] = 'none'
            ret['success'] = True
            ret['msg'] += 'No Results found for %s' %sosl
            return ret
       

    #######################################################################
    #  utility and setup methods
    #######################################################################
    def checkDate(self, dt, where=''):
        """ check format of date string and return secs or return '' """
        if dt in [None, '']: 
            return ''
        
        if dt in ['now']: 
            return time.mktime(time.localtime())

        if type(dt) == type(1.0): 
            return dt

        if type(dt) not in strTypes:
            dt = '%s'%dt

        if 1:
            try:
                if len( dt.split('T')) != 2:   
                    dt = '%sT12:00:00.000Z'%dt
                dtup = time.strptime(dt, '%Y-%m-%dT%H:%M:%S.000Z')
                dtsec = time.mktime(dtup) - time.timezone
                return dtsec
            except:
                try:
                    if len( dt.split('T')) != 2:
                        dt = '%sT12:00:00:000Z'%dt
                    dtup = time.strptime(dt, '%Y-%m-%dT%H:%M:%S:000Z')
                    dtsec = time.mktime(dtup) - time.timezone
                    return dtsec
                except:    
                    print 'ERROR unknown DateTime string of %s from %s' %(dt, where)
                    # 2003-09-20T12:00.000Z
                    try:
                        dtup = time.strptime(dt, '%Y-%m-%dT%H:%M:%S.000Z')
                        dtsec = time.mktime(dtup) - time.timezone
                        return dtsec
                    except: pass
                    #dtup = time.strptime(dt, '%(Y)04d-%(M)02d-%(D)02dT%(h)02d:%(m)02d:%(s)02dZ')
                    #return time.mktime(time.localtime())
                    return ''
        else:
            print 'Fix checkDate found type %s for %s'%(type(dt),dt) 

    def getTime(self, value=None):
        """ format the time string, used in walkSCM
        """
        if value is None: 
            return time.strftime( "%m/%d %H:%M", time.localtime() )
        if not isinstance(value, (TupleType, time.struct_time)):
            # else assume the timeStr is in the format
            # YYYYMMddTHH:MM:ss as xmlRPC.DateTime class
            value = '%s' %value
            value = time.strptime(value, "%Y-%m-%dT%H:%M:%S")
        tStr   = time.strftime("%a %m/%d %H:%M", value)
        return tStr

    def makeDateTime(self, value):
        """ make into a standard Date Time string from GMT """
        if not isinstance(value, StringType):
            if not isinstance(value, (TupleType, time.struct_time)):
                if value == 0:
                    value = time.time()
                value = time.gmtime(value)
                return time.mktime(value)
            value = time.strftime("%Y%m%dT%H:%M:%S", value)
            return value
        else:
            try:
                if len( date.split('T')) == 2:   dt = value
                else:
                    dt = '%sT12:00:00'%date
                # dtup = time.strptime('2004-04-21T12:30:59', ISO_8601_DATETIME)
                dtup = time.strptime(dt, ISO_8601_DATETIME)
                dtsec = time.mktime(dtup)
                return dtsec
            except:
                print 'ERROR unknown DateTime string of %s' %value
                return time.mktime(time.gmtime())
        
    def getDisplayDateTime(self, value):
        """ return a command line displayable Date Time string 
            typical input -> 2004-01-10T00:13:50.000Z
            output <- June 31, 2004 2:00pm PST
        """
        try:   value = time.strptime(value, '%Y-%m-%dT%H:%M:%S.000Z')
        except:
            print 'ERROR: getDisplayDateTime given %s'%value
            value = time.localtime()
        if not isinstance(value, (TupleType, time.struct_time)):
            print 'ERROR: getDisplayDateTime parse failed for %s'%value
        dt = time.strftime("%b %d %H:%M", value)
        return dt
        
        
    def getDateTimeTuple(self, value, offset=0):
        """ return time tuple for any input, yet right;/ """
        if isinstance(value, (TupleType, time.struct_time)):
            return value
        if isinstance(value, numTypes):
            return time.gmtime(value+offset)
        if isinstance(value, tuple(strTypes)):
            try: 
                value = time.strptime(value, '%Y-%m-%dT%H:%M:%S.000Z')
                return value
            except: 
                print 'ERROR:getDateTimeTuple Could not parse %s'%value
                return time.gmtime(time.time()+offset)


    def getAsDateTimeStr(self, value, offset=0):
        """ return time as 2004-01-10T00:13:50.000Z """
        if isinstance(value, (TupleType, time.struct_time)):
            return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', value)
        if isinstance(value, numTypes):
            secs = time.gmtime(value+offset)
            return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', secs)
            
        if isinstance(value, strTypes):
            try: 
                value = time.strptime(value, '%Y-%m-%dT%H:%M:%S.000Z')
                return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', value)
            except: 
                print 'ERROR:getDateTimeTuple Could not parse %s'%value
                secs = time.gmtime(time.time()+offset)
                return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', secs)

    def getId15(self, id):
        """ Return the 15 char version of the id """
        if len(id) == 15: return id
        return id[:15]
    
    def getId18(self, id):
        """ Return the 18 char version of the id """
        if len(id) == 18: return id
        from sfUtil import convertId15ToId18
        nid = convertId15ToId18(id)
        return nid

    def cmpIds(self, idOne, idTwo):
        """ many but not all sForce ID are returned in the API as 18 character  """
        if len(idOne) == 18: idOne = idOne[:-3]
        if len(idTwo) == 18: idTwo = idTwo[:-3]
        return idOne == idTwo
        
    def setLog(self, msg, type='info'):
        """ log critical errors """
        debugLevel = type[-1:]
        try: 
            debugLevel = int(debugLevel)
            type = type[:-1]
        except: debugLevel = 0
        if debugLevel > self.debug: 
            return  # log based on debug levels appended to type identifier
        if not hasattr(self, 'elog') or self.elog is None:
            self.setLogger()

        try:
            if type.lower() == 'critical': self.clog.critical(msg)
            elif type.lower() == 'error': self.elog.error(msg)
            elif type.lower() == 'warn':  self.elog.warn(msg)
            elif type.lower() == 'note':  self.note.info(msg)
            elif type.lower() == 'fix':  self.note.error(msg)
            elif type.lower() == 'event': self.log.info(msg)
            elif type.lower() == 'owner': self.log.warn(msg)
            elif type.lower() == 'new':   self.log.warn(msg)
            elif type.lower() == 'info':  self.dlog.info(msg)
            elif type.lower() == 'debug': self.dlog.info(msg)
            else:
                self.dlog.info(msg)
        except Exception, e:
            print "setLog failed! Error message: %s" %e 


    def setLogger(self, name=None, note=None, logger=None, dlogger=None, elogger=None, clogger=None):
        """
        setup a reusable logger reference
        """
        if name is None: 
            if hasattr(self, 'logname'):  name = self.logname
            else:                         name = 'sf3'
        if note is not None:    self.note = note
        if logger is not None:  self.log  = logger
        if dlogger is not None: self.dlog = dlogger
        if elogger is not None: self.elog = elogger
        if clogger is not None: self.clog = clogger
        if note is None or logger is None or dlogger is None or \
               elogger is None or clogger is None:
            confPath = 'logger.ini'
            try:
                if os.path.exists(confPath):
                    logging.config.fileConfig(confPath)
                    note    = logging.getLogger('%s' %name)
                    logger  = logging.getLogger('%s.log' %name)
                    dlogger = logging.getLogger('%s.det' %name)
                    elogger = logging.getLogger('%s.err' %name)
                    clogger = logging.getLogger('%s.crit' %name)
                    self.note = note
                    self.log  = logger
                    self.dlog = dlogger
                    self.elog = elogger
                    self.clog = clogger
                else:
                    self.setDefaultLoggers(name)
            except:
                pass
    ## END setLogger


    def setDefaultLoggers(self, name='sf'):
        """
        setup a default reusable logger reference if no logger.ini
        file is found
        """
        note    = logging.getLogger('%s.in' %name)
        logger  = logging.getLogger('%s.log' %name)
        dlogger = logging.getLogger('%s' %name)
        elogger = logging.getLogger('%s.err' %name)
        clogger = logging.getLogger('%s.crit' %name)

        logging.disable(9) # change to see the blather logs 1=most logs 10=DEBUG
        logger.setLevel(logging.INFO)  # set verbosity to show all messages of severity >= DEBUG
        note.setLevel(logging.INFO)
        dlogger.setLevel(logging.DEBUG)
        elogger.setLevel(logging.DEBUG)
        clogger.setLevel(logging.CRITICAL)
        ndir  = os.path.join('/','home','sfscript','log')
        udir  = os.path.join('/','home','sfscript','log','usage')
        edir = os.path.join('/','home','sfscript','log','details')

        if not os.path.exists(udir): os.makedirs(udir)
        if not os.path.exists(edir): os.makedirs(edir)

        # Attempt to set the mode to 666 each time we instantiate a handler
        mode = stat.S_IWUSR + stat.S_IRUSR + stat.S_IWGRP + stat.S_IRGRP + stat.S_IWOTH + stat.S_IROTH
        

        npath = os.path.join(ndir, 'note.log')
        nhdlr = logging.handlers.RotatingFileHandler(npath, "a", 50000000, 20)
        try:
            os.chmod(npath, mode)
        except Exception, e:
            pass

        upath = os.path.join(udir, 'events.log')
        lhdlr = logging.handlers.RotatingFileHandler(upath, "a", 50000000, 20)
        try:
            os.chmod(upath, mode)
        except Exception, e:
            pass

        epath = os.path.join(edir,'debug.log')
        dhdlr = logging.handlers.RotatingFileHandler(epath, "a", 50000000, 15)
        ehdlr = logging.handlers.RotatingFileHandler(epath, "a", 50000000, 9)
        try:
            os.chmod(epath, mode)
        except Exception, e:
            pass

        
        

        recip_str = self.sfc.get('err', 'crit_err_recips')
        recip_list = recip_str.split(',')
        recip_list2 = []
        for recip in recip_list:
            recip_list2.append(recip.strip())
        chdlr = logging.handlers.SMTPHandler(self.sfc.get('email',
                                                          'smtp_server'),
                                             self.sfc.get('main', 'from_addr'),
                                             recip_list2,
                                             self.sfc.get('err',
                                                          'crit_err_subj'))

        nfmt  = logging.Formatter("%(asctime)s %(name)-14s %(message)s", "%x %X")
        lfmt  = logging.Formatter("%(asctime)s %(name)-14s %(levelname)-7s %(message)s", "%x %X")
        efmt  = logging.Formatter("%(asctime)s %(name)-14s %(levelname)-7s %(message)s", "%x %X")
        nhdlr.setFormatter(nfmt)
        lhdlr.setFormatter(lfmt)
        dhdlr.setFormatter(efmt)
        ehdlr.setFormatter(efmt)
        chdlr.setFormatter(efmt)
        note.addHandler(nhdlr)
        logger.addHandler(lhdlr)
        dlogger.addHandler(dhdlr)
        elogger.addHandler(ehdlr)
        clogger.addHandler(chdlr)
        clogger.addHandler(ehdlr) # also want to log critical events to error
        self.note = note
        self.log  = logger
        self.dlog = dlogger
        self.elog = elogger
        self.clog = clogger

    def showData(self, data=None, entity='', target='console'):
        """ display data loaded in this object """
        if target in [None, '','console']:
            self.showDataConsole(data, entity)
        else:
            print 'not implemented yet'


    def showDataConsole(self, data=None, entity=''):
        """ console oriented display of data loaded in this object """
        if data is None: data = self.data
        if data in [None,'',[],[()]]: return 
        if type(data) not in seqTypes:
            return self.showDictConsole2(data)
        for dataTuple in data:
            if entity == '':
                entity = dataTuple[0]
                dataDict = dataTuple[1]
            else:
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

    def showDictConsole2(self, data=None):
        """ console oriented display of data dictionary """
        if data is None: data = self.data
        if data in [None,'',[]]: return 
        for entity, dataDict in data.items():
            if dataDict not in [[],{}]:
                if type(dataDict) in dictTypes:
                    for k, v in dataDict.items():
                        if v not in [None,'']:
                            print ' %25s: %s' %(k,dataDict[k])

                elif type(dataDict) in seqTypes:
                    dataDict = dataDict[0]
                    if type(dataDict) in dictTypes:
                        for k, v in dataDict.items():
                            if v not in [None,'']:
                                print ' %25s: %s' %(k,dataDict[k])
                    else:
                        print ' %25s: %s' %(entity,dataDict)
                else:
                    print ' %25s: %s' %(entity,dataDict)
        print '---------------------------------------------------'


    def showDictConsole(self, data=None):
        """ console oriented display of data dictionary """
        if data is None: data = self.data
        if data in [None,'',[]]: return 
        for entity, dataDict in data.items():
            if dataDict in [[],{}]:
                print '  -------- No Data for %s item -------'%entity
            else:
                print '  ------%s Data for the item ---------' %entity
                if type(dataDict) in dictTypes:
                    for k, v in dataDict.items():
                        if v not in [None,'']:
                            print ' %25s: %s' %(k,dataDict[k])

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

    def setData(self, data, reset=False):
        """ simple set data as a dictionary of entity-data pairs {'entity': [{data}]}
            multi-entity objects are expected to have multiple entity keys.
        """
        if reset or not hasattr(self, 'data'):
            self.data = {}
        if data is None: return self.showDataFormatError(data)
        if type(data) in dictTypes:
            for entity in data.keys():
                if entity not in self.getEntities():
                    print 'ERROR:setData unknown entity %s will be ignored'%entity
                else:
                    if reset:
                        self.data[entity] = data[entity]
                    else:
                        newData = data[entity]
                        oldData = self.data.get(entity,{})
                        if type(oldData) in dictTypes and type(newData) in dictTypes:   # simple case of one item for this entity
                            oldData.update(newData)
                            self.data[entity] = oldData
                            continue
                        elif type(oldData) in dictTypes and type(newData) in seqTypes:   # typical case of a list of items for the entity
                            oldData = [oldData]
                            
                        elif type(newData) not in seqTypes and type(newData) not in dictTypes:
                            print 'ERROR:setData entity %s has badly formed data'%entity
                            return self.showDataFormatError(newData, entity)
                        if 1:                         
                            if type(newData) not in seqTypes: newData = [newData]
                            checkedData = []
                            checkedIds = []
                            for newd in newData:
                                newId = newd.get('Id','')
                                for old in oldData:
                                    if old.get('Id') == newId:
                                        old.update(newd)            # update old data with new dictionary data
                                        checkedData.append(old)
                                        checkedIds.append(newId)
                                        oldData.remove(old)
                                if newId not in checkedIds and newId != '':  # add brand new data to list
                                    checkedData.append(newd)
                            for old in oldData:
                                if old.get('Id') not in checkedIds and old != {}: # keep old data not updated
                                    checkedData.append(old)
                            self.data[entity] = checkedData

        elif type(data) == TupleType: return self.showDataFormatError(data)
        elif type(data) == DictType:  return self.showDataFormatError(data)
        elif type(data) == StringType: return self.showDataFormatError(data)
        else:
            print 'Error setData for:%s' %data
        
    def getDataOFF(self, entity='all', id=''):
        """ return the data 
            - list of data dictionaries if just entity provided
            - specific data dictionary if id is in entity list
        """
        if entity == 'all':
            return self.data
        if not self.data.has_key(entity):
            return [{}]
        eData = self.data.get(entity,[{}])
        if id in [None,'']: 
            return eData
        if type(eData) not in seqTypes: eData = [eData]
        for ed in eData:
            if ed.get('Id','') == id:
                return ed
        return {}
        
    def showDataFormatError(self, data, entity=''):
        """ echo data format error to console """
        if entity == '': entity =self.entity
        print 'ERROR: Data in this %s object must be stored in the format {\'entity\', {data}}' %entity
        print '       Note that this is a dictionary with an sForce entity string and a data dictionary'
        if data is None: print '       You should provide some data on init, data will be {} now' 
        if type(data) == TupleType:
            print '       You provided a tuple with the first item a %s and the data item a %s' %(type(data[0]),type(data[1]))
        if type(data) == DictType:
            print '       You provided a dictionary item a with no know entity string' 
        if type(data) == StringType:
            print '       You provided a string item a string with no known data dictionary' 
        if self.data >0: print 'DATA: %s' %data
        return 'Error: data format'        


    def getUserIdByUsername(self, email):
        soql = "select Id from User where Username = '%s'" %email
        ret = self.queryBase(USER_OBJ, soql=soql)
        if ret.get('success',False) is True:
            queryList = ret.get('result')
        else:
            queryList = []
        
        userId = None
        
        if queryList in BAD_INFO_LIST:
            msg = "getUserIdByUsername Result: NO User found with Username %s" \
                  %email
            self.setLog(msg, 'warn')
            return userId
            
        if len(queryList) > 1:
            # This should never happen - SF shouldn't allow duplicate usernames
            msg = "getUserIdByUsername found more than one User having the Username %s: %s" %(email, queryList)
            self.setLog(msg, 'critical')
        
        userInfo = queryList[0]
        userId = userInfo['Id']
                
        return userId
    ## END getUserIdByUsername



##################################################################################################
#
#  Logic methods called from command line 
#
##################################################################################################
def testMethods(method, term, options):
    """ update SF using passed data"""
    if options.parm != '':  parm = options.parm
    else:                   parm = 'test1'
    if method not in ['update','create','retrieve','delete','search','query']:  method = 'update'
    print '\n--%s TEST with parm %s----------------------------------------------' %(method, parm)
    try:
        ret = doTestMethods(method, term, parm, options)
        if options.debug > 1: print 'Results for %s have a of returned dictionary is %s' %(term, len(ret))
        #pprint.pprint( ret )
        if type(ret) in seqTypes and len(ret) > 0: ret = ret[0]
        if type(ret) != type({}):
            print '--Return format is incorrect for %s %s test' %(method,parm)
            print ret  
        elif ret.get('success','') in [True, 'True']:
            result = ret.get('result',[])
            print '--%s TEST PASSED with %s results----------------------------------'%(method, len(result))
            if options.debug > 0:
                print result
                print '----------return results above--------------------------------------'
        else:
            print '--%s TEST FAILED with parm %s--------------------------------------' %(method,parm)
            print ret
            print '----------return results above--------------------------------------'
    except Exception,e:
        print '--%s TEST FAILED with parm %s--------------------------------------' %(method,parm)
        print '---Error: %s  e:%s--------'%(Exception,e)    
        traceback.print_exc ()
        print '----------return errors above--------------------------------------'



def doTestMethods(method, term, parm, options):
    """ update SF using passed data"""
    tf = file(options.trace, 'w+')
    sfb = sForceApi3(dlog=tf, debug=options.debug)
    ret = ['No test found for %s %s' %(method,parm)]
    dtup = time.strptime('2004-04-21T12:30:59', ISO_8601_DATETIME)
    dtsec = time.mktime(dtup)
    taskdata = {'Description':'This was updated from api3 %s' %term
               ,'Dont_Send_Empty_Report__c':True
               ,'Frequency__c':'weekly'
               ,'Last_Report__c':dtsec               #dataTime
               ,'My_CRs_in_Development__c':True     # ref must be valid ID
               ,'id':'00330000001Ud4D'
               ,'LastName':'Vanek'
               }

    if method == 'update':
        if parm == 'test1':
            ret = sfb.updateTest1(entity='Task', data={}, nullEmpty=False, seed=term)
        elif parm == 'test2':
            ret = sfb.updateTest1(entity='Contact', data=taskdata, nullEmpty=False, seed=term)
    elif method == 'create':
        if parm == 'test1':
            ret = sfb.createTest1(entity='Task', data={}, nullEmpty=False, seed=term)
        elif parm == 'test2':
            ret = sfb.createTest1(entity='Contact', data=taskdata, nullEmpty=False, seed=term)

    elif method == 'query':
        if parm == 'test1':
            soql = "Select Business_Unit__c, Department, Dept__c, Email, EmployeeNumber__c, FirstName, Id, LastName from Contact \
                        where AccountId = '00130000000DWRJ' and EmployeeNumber__c <'10015' and EmployeeNumber__c != '' "
            ret = sfb.queryBase(entity='Contact', soql=soql)
        elif parm == 'test2':                                       # should be same as above
            ret = sfb.queryBase(entity='Contact', where='t1', sc='contacts')  
        else:
            ret = sfb.queryBase(entity='task', where=term, sc=parm)   # sc = mod, case, contacts, 

    elif method == 'search':
        if term.find('@') != -1: scope = 'EMAIL FIELDS'
        else:                    scope = 'ALL FIELDS'
        if parm == 'test1':
            retsc = 'case'
            ret = sfb.searchBase(term, retsc=retsc, scope=scope)
        elif parm == 'test2':
            retsc = 'people'
            ret = sfb.searchBase(term, retsc=retsc, scope=scope)
        else:
            ret = sfb.searchBase(term, retsc=parm, scope=scope)

    elif method == 'retrieve':
        if parm == 'test1':
            ids = ['00T3000000321P8','00T3000000321Nn']
            fieldList = []
            ret = sfb.retrieveBase(ids=ids, entity='Task', fieldList=fieldList )
        elif parm == 'test2':
            ids = ['00330000001Jsyq','00330000001Ud4D']
            fieldList = ['Id','FirstName', 'LastName','Email']
            ret = sfb.retrieveBase(ids=ids, entity='Contact' )
    
    elif method == 'delete':
        if parm == 'test1':
            ids = ['00T300000033cw3']
            ret = sfb.deleteBase(ids=ids)
        else:
            print 'Only a parm of test1 is supported right now'
    
    return ret
    


def genApiFiles(options):
    """ output the API files """
    opath = os.path.normpath(os.path.join('.',options.path))
    if not os.path.isdir(opath):
        try: os.mkdir(opath)
        except: 
            print 'Cannot make directory %s' %opath
            return
    tf = file(options.trace, 'w+')
    st = time.time()
    sfb = sForceApi3(dlog=tf, debug=options.debug)
    try:   print '%s' %sfb.getUserInfo()
    except Exception, e:  print '%s err:%s' %(Exception, e)
    reset = False
    if options.parm in ['reset']: reset = True
    glist = sfb.describeGlobal()
    print 'Now checking access time from sop cache\n'
    for entity in glist:
        emap = sfb.getEntityMap(entity, reset)
        print '%2d sec Got %s map' %(time.time()-st, entity)

    path = os.path.join(opath,'api3.txt')
    of = file(path, 'w')
    of.write('%s'%sfb.em)
    of.close()
    print 'Wrote %s entities to the file %s in %s seconds' %(len(sfb.em), path, time.time()-sfb.startTime)
    st = time.time()
    print 'Now checking access time from sop cache\n'
    for entity in glist:
        emap = sfb.getEntityMap(entity)
        print '%2d sec Got %s map' %(time.time()-st, entity)
        
    
    
##################################################################################################
#
#  Commandline management methods.  Minimal logic, just command parm processing
#
##################################################################################################
def usage(err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to test the basic API calls.\n'
    m += ' '
    m += '    sfBase3  <query string> \n'
    m += '      or\n'
    m += '    sfBase3  -c all -ptest1 \n'
    m += '      or\n'
    m += '    sfBase3 -cs -p p1|c1|cr <search string> \n'
    m += '      or\n'
    m += '    sfBase3  -c api -p reset do (to pull latest entity info NOW)\n'
    return m


def main_CL():
    """ Command line parsing and and defaults methods
    """
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-c", "--cmd",   dest="cmd",   default="query",     help="Command type to use.")
    parser.add_option("-p", "--parm",  dest="parm",  default="test1",     help="Command parms.")
    parser.add_option("-f", "--path",  dest="path",  default="describe",  help="Path to output of sf Walk.")
    parser.add_option("-t", "--trace", dest="trace", default="soap_trace.out",  help="SOAP output trace file.")
    parser.add_option("-d", "--debug", dest='debug', action="count", help="The debug level, use multiple to get more.")
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
        seed = args[0]
        st = time.time()
        if options.cmd in ['query','q']:
            testMethods('query', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)

        elif options.cmd in ['search','s']:
            testMethods('search', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)

        elif options.cmd in ['update','u']:
            testMethods('update', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)

        elif options.cmd in ['create','c']:
            testMethods('create', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)

        elif options.cmd in ['retrieve','r']:
            testMethods('retrieve', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)

        elif options.cmd in ['delete','d']:
            testMethods('delete', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)

        elif options.cmd in ['api']:
            genApiFiles(options)
            print 'Took a total of %2d secs' %(time.time()-st)

        elif options.cmd in ['all']:
            options.parm = 'test1'
            testMethods('query', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)
            testMethods('search', 'brooks', options)
            print 'Took a total of %2d secs' %(time.time()-st)
            testMethods('retrieve', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)
            testMethods('update', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)
            testMethods('create', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)
            options.parm = 'test2'
            testMethods('query', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)
            testMethods('search', 'brooks', options)
            print 'Took a total of %2d secs' %(time.time()-st)
            testMethods('retrieve', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)
            testMethods('update', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)
            testMethods('create', seed, options)
            print 'Took a total of %2d secs' %(time.time()-st)

    else:
        print '%s' %usage()

if __name__ == "__main__":
    main_CL()
