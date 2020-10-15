""" 
Process the creation od Interested partied list (default) and  
 
add them to the CR. 
 
""" 
 
import pprint 
import os, sys 
import textwrap 
import datetime 

from vyperlogix.misc import _utils
from vyperlogix.logging import standardLogging
from vyperlogix.hash import lists

import logging
 
from pyax.connection import Connection
from pyax.exceptions import ApiFault

from sfConstant import BAD_INFO_LIST

from getLastProcessDate2 import getLastProcessDate2
from crypto import *

_cwd = None

_isBeingDebugged = _utils.isBeingDebugged # When debugger is being used we do not use threads...

class CaseWatcherList: 
     
    def __init__(self, sfdc=None,cwd=os.path.abspath('.')):
        self.__sfdc__ = sfdc
        self.__cwd__ = cwd
        self.__logname__ = 'CaseWatherList' 
     
    def _getLastProcessDate(self):
        p = lists.HashedLists2()
        p.fromDict({'update' : False, 'cwd': self.cwd, 'filename' : 'LastCaseWatcherProcessedDate', 'diff_minutes' : -15})
        checksince = getLastProcessDate2(p)
        return  checksince
    
    def getCheckSince(self): 
        checksince = self._getLastProcessDate()
        self.createNewNotifyObj(checksince) 
        return
    
    def query(self,objName,soql):
        return self.sfdc.query(soql)
     
    def createNewNotifyObj(self,checksince): 
        if checksince not in [None,'',""]:              
            soql="Select OwnerId, CreatedDate, Id, LastModifiedDate,  Name  from Case_Watcher__c where LastModifiedDate > %s" %checksince 
            logging.warning('soql=[%s]' % soql) 
                         
            ret1 = self.query('Case_Watcher__c', soql=soql)          
            logging.warning('ret1=[%s]' % ret1) 
             
            if ret1  in BAD_INFO_LIST: 
                msg ="Could not find any records for Case_Watcher__c Object" 
                logging.warning('msg=[%s]' % msg) 
                print msg 
                self.setLog(msg, 'warn') 
            else:                           
                for buildLink in ret1:    
                    userId = buildLink.get('OwnerId')                                                         
                    ipId = buildLink.get('Id')                                         
                    if userId not in BAD_INFO_LIST: 
                        self.createUserContact(userId,ipId) 
                    continue 
                pass     
        else: 
            msg = "No query need to be performed" 
            logging.warning('msg=[%s]' % msg) 
            self.setLog(msg) 
                   
        return 
     
    def createUserContact(self,userId,ipId):                 
        idList = [] 
        idList.append(userId)          
        fields = ('Id','Email', 'FirstName','IsActive','LastName','User_Contact_Id__c') 
        ret = self.retrieve(idList, 'User', fieldList=fields) 
                 
        if ret in BAD_INFO_LIST:                         
            msg = "Could not find any records for User Id: %s" %teamId 
            logging.warning('msg=[%s]' % msg) 
            print msg 
            self.setLog(msg, 'warn') 
            pass                 
        else: 
            for cont in ret: 
                contactId = cont.get('User_Contact_Id__c') 
                email = cont.get('Email')                  
                self.createCRNotificationObj(email,contactId,ipId,'User Alias','False') 
            pass 
        return  
     
    def getContactEmail(self, contactId):        
        email=None 
        idList = [] 
        idList.append(contactId)          
        fields = ('Id','Email') 
        ret = self.retrieve(idList, 'Contact', fieldList=fields) 
                 
        if ret in BAD_INFO_LIST:                         
            msg = "Could not find any records for Product team Id: %s" %teamId 
            logging.warning('msg=[%s]' % msg) 
            print msg 
            self.setLog(msg, 'warn') 
            pass                 
        else: 
            for cont in ret: 
                email=cont.get('Email')                                                  
            pass 
         
        return email 
     
    def createCRNotificationObj(self,email,contactId,ipId, name,isEmailAlias):         
        newEmail=email 
        soql="Select Email__c, Id, Case_Watcher__c, Name from Case_Watcher_List__c   where Case_Watcher__c= '%s'" %ipId                 
        logging.warning('soql=[%s]' % soql) 
        ret = self.query('Case_Watcher_List__c', soql=soql)         
        logging.warning('ret=[%s]' % ret) 
        if ret in BAD_INFO_LIST:                         
            msg ="Could not find any Case_Watcher__c Object"             
            logging.warning('msg=[%s]' % msg) 
            print msg 
            self.setLog(msg, 'warn')                         
            data = [{'Email__c':newEmail,'Contact__c':contactId,'Case_Watcher__c':ipId,'Name':name,'Alias_Email__c':isEmailAlias}]                         
            contactObjRes = self.create('Case_Watcher_List__c', data)               
        else: 
            emailExist=False 
            for ip in ret:                 
                existEmail=ip.get('Email__c')                 
                if newEmail==existEmail: 
                    msg= "Record with the same email Id alraedy exist:  %s" %existEmail 
                    logging.warning('msg=[%s]' % msg) 
                    self.setLog(msg) 
                    emailExist=True 
                    self.setLog(msg) 
                    break 
                continue 
             
            if not emailExist:                 
                data = [{'Email__c':newEmail, 'Contact__c':contactId,'Case_Watcher__c':ipId,'Name':name}]                 
                contactObjRes = self.create('Case_Watcher_List__c', data)    
                pass         
            pass 
                 
        return 
     
    def getContactId(self,userId): 
        contId=None         
        idList = [] 
        idList.append(userId) 
         
        if userId is not None: 
            fields = ('Id', 'User_Contact_Id__c', 'Email', 'IsActive') 
            res = self.retrieve(idList, 'User', fieldList=fields) 
 
            if res not in BAD_INFO_LIST: 
                for user in res: 
                    contId = user.get('User_Contact_Id__c')                     
                    continue 
                pass 
            pass 
        return contId     

    def get_sfdc(self):
        return self.__sfdc__
    
    def get_cwd(self):
        return self.__cwd__
    
    sfdc = property(get_sfdc)
    cwd = property(get_cwd)
    
def main(sfdc):     
    n=CaseWatcherList(sfdc,cwd=_cwd) 
    n.getCheckSince() 
 
if __name__ == "__main__": 
    d_passwords = lists.HashedLists2()
    
    s = ''.join([chr(ch) for ch in [126,254,192,145,170,209,4,52,159,254,122,198,76,251,246,151]])
    pp = ''.join([ch for ch in decryptData(s).strip() if ord(ch) > 0])
    d_passwords['rhorn@molten-magma.com'] = pp
    
    s = ''.join([chr(ch) for ch in [39,200,142,151,251,164,142,15,45,216,225,201,121,177,89,252]])
    pp = ''.join([ch for ch in decryptData(s).strip() if ord(ch) > 0])
    d_passwords['sfscript@molten-magma.com'] = pp

    print 'sys.version=[%s]' % sys.version
    v = _utils.getFloatVersionNumber()
    if (v >= 2.51):
        from vyperlogix.handlers.ExceptionHandler import *
        from vyperlogix.misc._psyco import *
        excp = ExceptionHandler()
        importPsycoIfPossible(func=main,isVerbose=True)

        _username = 'rhorn@molten-magma.com'

        if (os.environ.has_key('cwd')):
            _cwd = os.environ['cwd']
        elif (len(sys.argv) >= 1):
            try:
                _cwd = sys.argv[1]
            except:
                _cwd = ''
        else:
            _cwd = ''
        
        print '_cwd=%s' % _cwd
            
        if (len(_cwd) > 0) and (os.path.exists(_cwd)):
            name = _utils.getProgramName()
            _log_path = _utils.safely_mkdir_logs(_cwd)
            logFileName = os.sep.join([_log_path,'%s.log' % (name)])
            
            _logging = logging.WARNING
            
            standardLogging.standardLogging(logFileName,_level=_logging)
            
            logging.warning('Logging to "%s" using level of "%s:.' % (logFileName,standardLogging.explainLogging(_logging)))
        
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
			main(sfdc)
		    else:
			import cProfile
			cProfile.run('main(sfdc)', os.sep.join([_log_path,'profiler.txt']))
                    
                except ApiFault, details:
                    exc_info = sys.exc_info()
                    info_string = '\n'.join(traceback.format_exception(*exc_info))
                    logging.warning(info_string)
            else:
                logging.error('Cannot figure-out what username (%s) and password (%s) to use so cannot continue. Sorry !' % (_username,_password))
    else:
        logging.error('You are using the wrong version of Python, you should be using 2.51 or later but you seem to be using "%s".' % sys.version)
    logging.warning('Done !')
             
 
