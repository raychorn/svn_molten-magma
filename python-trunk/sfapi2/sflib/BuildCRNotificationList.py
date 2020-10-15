"""
Scan newly created Interested patry object and make sure the CR, component and team 

email addresses are added to the CR Notification object 

"""

sfUrl = 'https://na1.salesforce.com'

import pprint
import sys
import textwrap
from optparse import OptionParser

from sfMagma import *
from sfConstant import *
from sfUtil import *

class BuildCRNotificationList(SFMagmaTool):
    
    logname = 'BuildCRNotification'
    
    
    def getInterestedPartiesObjects(self):
        """
        Get all Cases where recordType ID's are related to a CR
        """  
                
        soql1 = "Select CaseNumber, Id, OwnerId, RecordTypeId from Case  where RecordTypeId ='012300000000XXgAAM'"
               
        
        ret = self.query('Case', soql=soql1)
       
        print "After complteing the quries"
        
        if ret in BAD_INFO_LIST:
            msg = "Couldn't find any records in the object UserChange__c" 
            print msg
            self.setLog(msg, 'warn')
            pass
        else:
            print" Could not find any new CR's" 
                
        
        for hrRec in ret:  
            groupOwner=True 
            user=False                     
            ownerId=hrRec.get('OwnerId')
            caseId=hrRec.get('Id')
            
            soql2="Select Email, Id, Name, OwnerId, RelatedId, Type from Group  where Id='%s' and Type='Case'" %ownerId
            print "SQL: %s" %soql2      
            ret2 = self.query('Case', soql=soql2)      
            
            if ret2 in BAD_INFO_LIST:
                groupOwner=False
                msg = "Couldn't find any records in the Group Object" 
                print msg
                self.setLog(msg, 'warn')
                pass     
             
            else:  
                print "Owner belongs to group object"
                pass
            
            if groupOwner is not True:
                
                user=True              
                soql3="Select Email, FirstName, LastName, Id, IsActive from User  where Id='%s' and IsActive=True" %ownerId
                print "SQL: %s" %soql2  
                ret2 = self.query('User', soql=soql3)   
                   
            
                if ret2 in BAD_INFO_LIST:                    
                    msg = "Couldn't find any records in the User Object" 
                    print msg
                    self.setLog(msg, 'warn')
                    pass
                else:
                    print "user query has records"
                    pass
                pass # outer else
            
            
            for hrRec2 in ret2:
                print "Inside for to retrieve values"
                email=hrRec2.get('Email') 
                name=None
                if groupOwner is True:  
                    print "Group owner is true"                                 
                    name=hrRec2.get('Name')
                    pass
                if user is True:
                    print "user is true"
                    fName=hrRec2.get('FirstName')
                    lName=hrRec2.get('LastName')
                    name= fName +" "+lName
                    pass 
                
                pass
            
            if email is not None:
                 notifyId=self.createInterestedParties(email, name, caseId) 
            
            continue #for
                                
                                                                          
             
   
    
    def createInterestedParties(self,email,name,caseId):
        
        print "Inside Create new Interested Party"    
        intInfo =[]
        
        existQuery="Select Case__c, Email__c, Name from Interested_Party__c  where Case__c='%s' and Email__c='%s'" %(caseId,email)
        
        ret2 = self.query('Interested_Party__c', soql=existQuery)                     
            
        if ret2 in BAD_INFO_LIST:                    
            msg = "The notifier object does not exist for the case. Hence adding the new Interested party to the case" 
            data = [{'Name': name,'Email__c': email,'Case__c':caseId}]
            print" Data to be inserted %s" %data
            interestedObjRes = self.create('Interested_Party__c', data)
           
            if interestedObjRes in BAD_INFO_LIST:
               msg = "shutdownUser: Create call of Interested parties Object  failed. Data follows:\n%s" %(pprint.pformat(interestedObjRes))
               print "Reason %s" %interestedObjRes
               print msg
               self.setLog(msg, 'error')
               pass
            else:
               intInfo = interestedObjRes[0]
               print "Interested party OBJECT CREATED WITH ID %s" %intInfo 
               pass           
           
            pass #outer if
       
        else:
            print "The notifier already exist, hence not adding the new record"
            pass     
        
        return intInfo    
    
    
    def getObjInfo(self, entity, objId):
        """
        Wrapper to fetch an entire record
        """
        objInfo = {}
        ret = self.retrieve([objId], entity)
        if ret in BAD_INFO_LIST:
            msg = "Retrieve of %s %s failed" %(entity, objId)
            print msg
            self.setLog(msg, 'error')
        else:
            objInfo = ret[0]

        return objInfo
          
        
    
def main():
    print "Inside Main function of Main class"
    n=CRNotificationList()
    n.getInterestedPartiesObjects()
    

if __name__ == "__main__":
    main()
    