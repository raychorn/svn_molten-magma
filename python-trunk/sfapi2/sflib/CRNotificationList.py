"""
Process the creation od Interested partied list (default) and 

add them to the CR.

"""

sfUrl = 'https://na1.salesforce.com'

import pprint
import sys
import textwrap
import datetime
from optparse import OptionParser

from sfMagma import *
from sfConstant import *
from sfUtil import *

class CRNotificationList(SFMagmaTool):
    
    logname = 'CRNotification'
    
    
    def getCheckSince(self):
        #tmp_root = '/home/sfbeta/tmp/processDates'
        tmp_root = '/home/sfscript/tmp/processDates'
        #tmp_root ='/home/ramya/sfsrc/sfapi2/tmp'
        filename='LastCheckedCRNotificationDate'  
        checksince=None
                      
        curDirPath = os.getcwd()
        tmpDirPath = tmp_root    
        os.chdir(tmpDirPath)       
        
        #os.system('umask 000')
        tmpPath = os.path.join(tmp_root,filename)
        if os.path.isfile(tmpPath):
            #ph = os.popen(filename)
            curFile=open(tmpPath, "rb", 0)
            for line in curFile.readlines():
                #print "Lines read from  file: %s" %line
                checksince=line                
                continue
            curFile.close()
            #os.system('umask %s' %saveUmask)                  
            os.remove(filename)            
        
        #os.cat(filename)    
        try:
            #open file stream
            #secsAgo=60*60*24
            newfilename=os.path.join(tmp_root,filename)
            file = open(newfilename, 'a')
            #fromSecs = time.time()-secsAgo       
            fromSecs = time.time()                     
            fromSecs = datetime.datetime.fromtimestamp(fromSecs)
            #diff = datetime.timedelta(days=-1)
            #previousDay=fromSecs + diff            
            currentDay=time.mktime(fromSecs.timetuple())                 
            dateStr = self.getAsDateTimeStr(currentDay)                       

            file.write(dateStr)
            #file.write("\n")
            file.close()
        except IOError:
            msg= "There was an error writing to %s" %filename
            self.setLog(msg, 'warn')
            pass
        
        if checksince in [None,'',""]:
            fromSecs = time.time()
            fromSecs = datetime.datetime.fromtimestamp(fromSecs)
            diff = datetime.timedelta(hours=-1)
            previousHour=fromSecs + diff            
            previousHour=time.mktime(previousHour.timetuple())                    
            preHourStr = self.getAsDateTimeStr(previousHour)            
            checksince=preHourStr
            
        os.chdir(curDirPath)
        self.createNewNotifyObj(checksince)
                              
        return     
    
    def createNewNotifyObj(self,checksince):              
                   
        
        if checksince not in [None,'',""]:             
            soql=" Select Case_Number__c, Component__c, CreatedDate, Id, LastModifiedDate, Tech_Campaign__c,User__c, Name, Team__c from Case_Watcher__c where LastModifiedDate > %s" %checksince                                    
            ret1 = self.query('Case_Watcher__c', soql=soql)         
            
            if ret1  in BAD_INFO_LIST:
                msg ="Could not find any records for Case_Watcher__c Object"
                print msg
                self.setLog(msg, 'warn')
                pass
            else:                          
                for buildLink in ret1:                                       
                    caseNo= buildLink.get('Case_Number__c')
                    comp=buildLink.get('Component__c')
                    team=buildLink.get('Team__c')
                    techCamp=buildLink.get('Tech_Campaign__c')
                    userId=buildLink.get('User__c')
                    ipId=buildLink.get('Id')                    
                    if caseNo not in BAD_INFO_LIST:
                        self.createCRContact(caseNo,ipId)
                        pass
                    if comp not in BAD_INFO_LIST:
                        self.createCompContact(comp,ipId)
                        pass
                    if team not in BAD_INFO_LIST:
                        self.createTeamContact(team,ipId)
                        pass 
                    if techCamp not in BAD_INFO_LIST:
                        self.createTechCampContact(techCamp,ipId)
                        pass
                    if userId not in BAD_INFO_LIST:
                        self.createUserContact(userId,ipId)
                        pass                
                    continue
                pass    
            
        else:
            self.setLog("No query need to be performed")            
                  
        return
    
    
    """def getPreviousDate(self,date):  
        checksince=None  
        date=date    
        if date is None:
            secsAgo=60*60*24
            #get a date 1 day before
            fromSecs = time.time()-secsAgo
            print" Current day: %s" %fromSecs
            fromSecs = datetime.datetime.fromtimestamp(fromSecs)
            diff = datetime.timedelta(days=-1)
            previousDay=fromSecs + diff
            print "Previous date: %s" %previousDay  
            previousDay=time.mktime(previousDay.timetuple())  
            print "Previous day: %s"%previousDay      
            dateStr = self.getAsDateTimeStr(previousDay)
            print "Previous formated date: %s"%dateStr
            checksince=dateStr
            pass
        else: 
            checksince=date            
        return checksince"""
    
    def createCRContact(self,caseId,ipId):        
        idList = []
        idList.append(caseId) 
        fields = ('Id','CaseNumber', 'ContactId', 'OwnerId')
        ret = self.retrieve(idList, 'Case', fieldList=fields)
        
        if ret in BAD_INFO_LIST:                        
            msg ="Could not find any records for the case Id: %s" %caseId
            print msg
            self.setLog(msg, 'warn')
            pass                
        else:
            for cont in ret:
                contactId=cont.get('ContactId')                
                if contactId not in BAD_INFO_LIST:
                    email=self.getContactEmail(contactId)                                  
                    self.createCRNotificationObj(email,contactId,ipId, 'CR Alias','False')
                    pass
            pass
        return 
    
    
    def createCompContact(self,compId,ipId):        
        idList = []
        idList.append(compId) 
        fields = ('Id','List_Address__c', 'List_Alias__c', 'Name','OwnerId')
        ret = self.retrieve(idList, 'Component__c', fieldList=fields)
                
        if ret in BAD_INFO_LIST:                        
            msg ="Could not find any records for the Component Id: %s" %compId
            print msg
            self.setLog(msg, 'warn')
            pass                
        else:
            for cont in ret:
                email=cont.get('List_Address__c') 
                ownerId=cont.get('OwnerId')
                contId=self.getContactId(ownerId)                 
                if email not in BAD_INFO_LIST:
                    self.createCRNotificationObj(email,contId,ipId,'Component Alias','True')
            pass
        return 
     
    
    
    def createTeamContact(self,teamId,ipId):        
        
        idList = []
        idList.append(teamId) 
        fields = ('Id','Build_Account_Contact__c', 'Name','OwnerId')
        ret = self.retrieve(idList, 'Product_Team__c', fieldList=fields)
                
        if ret in BAD_INFO_LIST:                        
            msg ="Could not find any records for Product team Id: %s" %teamId
            print msg
            self.setLog(msg, 'warn')
            pass                
        else:
            for cont in ret:
                contactId=cont.get('Build_Account_Contact__c')
                if contactId is not None:
                    email=self.getContactEmail(contactId)
                    ownerId=cont.get('OwnerId')
                    contId=self.getContactId(ownerId)                     
                    self.createCRNotificationObj(email,contId,ipId,'ProductTeam Alias','True')
            pass
        return 
    
    def createUserContact(self,userId,ipId):                
        idList = []
        idList.append(userId)         
        fields = ('Id','Email', 'FirstName','IsActive','LastName','User_Contact_Id__c')
        ret = self.retrieve(idList, 'User', fieldList=fields)
                
        if ret in BAD_INFO_LIST:                        
            msg ="Could not find any records for User Id: %s" %teamId
            print msg
            self.setLog(msg, 'warn')
            pass                
        else:
            for cont in ret:
                contactId=cont.get('User_Contact_Id__c')
                email=cont.get('Email')                 
                self.createCRNotificationObj(email,contactId,ipId,'User Alias','False')
            pass
        return 
    
    def createTechCampContact(self,techId,ipId):        
        idList = []
        idList.append(techId) 
        fields = ('Id','Name','OwnerId')
        ret = self.retrieve(idList, 'Tech_Campaign__c', fieldList=fields)
                
        if ret in BAD_INFO_LIST:                        
            msg ="Could not find any records for Tech Camp team Id: %s" %teamId
            print msg
            self.setLog(msg, 'warn')
            pass                
        else:
            for cont in ret:
                ownerId=cont.get('OwnerId')                
                contId=self.getContactId(ownerId)
                email=self.getContactEmail(contId)                
                self.createCRNotificationObj(email,contId,ipId,'TechCampaign Alias','True')
            pass
        return 
     
    def getContactEmail(self, contactId):       
        email=None
        idList = []
        idList.append(contactId)         
        fields = ('Id','Email')
        ret = self.retrieve(idList, 'Contact', fieldList=fields)
                
        if ret in BAD_INFO_LIST:                        
            msg ="Could not find any records for Product team Id: %s" %teamId
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
            pass  
                      
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
    n=CRNotificationList()
    n.getCheckSince()
    
    

if __name__ == "__main__":
    main()
    