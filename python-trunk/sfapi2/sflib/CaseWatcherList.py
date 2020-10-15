""" 
Process the creation od Interested partied list (default) and  
add them to the CR. 

See also: CustomMailNotification (sends emails) and CustomCaseEvents (queues emails)
 
""" 
 
#sfUrl = 'https://na1.salesforce.com' 

import pprint 
import sys 
import textwrap 
import datetime 
from optparse import OptionParser 
 
from sfMagma import * 
from sfConstant import * 
from sfUtil import * 

sfUrl = salesForceURL()

class CaseWatcherList(SFMagmaTool): 
     
    logname = 'CaseWatherList' 
     
    def getCheckSince(self): 
        checksince = getLastProcessDate({'diff_hours' : -1})
        self.createNewNotifyObj(checksince) 
        return      
     
    def createNewNotifyObj(self,checksince): 
         
        if checksince not in [None,'',""]:              
            soql=" Select OwnerId, CreatedDate, Id, LastModifiedDate,  Name  from Case_Watcher__c where LastModifiedDate > %s" %checksince 
                         
            ret1 = self.query('Case_Watcher__c', soql=soql)          
             
            if ret1  in BAD_INFO_LIST: 
                msg ="Could not find any records for Case_Watcher__c Object" 
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
            self.setLog(msg) 
                   
        return 
     
    def createUserContact(self,userId,ipId):                 
        idList = [] 
        idList.append(userId)          
        fields = ('Id','Email', 'FirstName','IsActive','LastName','User_Contact_Id__c') 
        ret = self.retrieve(idList, 'User', fieldList=fields) 
                 
        if ret in BAD_INFO_LIST:                         
            msg = "Could not find any records for User Id: %s" %teamId 
            print msg 
            self.setLog(msg, 'warn') 
            pass                 
        else: 
            for cont in ret: 
                contactId = cont.get('User_Contact_Id__c') 
                email = cont.get('Email')
                # BEGIN: Contacts should not be created by the system...
                #self.createCRNotificationObj(email,contactId,ipId,'User Alias','False') 
                # END! Contacts should not be created by the system...
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
        ret = self.query('Case_Watcher_List__c', soql=soql)         
        if ret in BAD_INFO_LIST:                         
            msg ="Could not find any Case_Watcher__c Object"             
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
     
def main():     
    n=CaseWatcherList() 
    n.getCheckSince() 
 
if __name__ == "__main__": 
    main() 
 
