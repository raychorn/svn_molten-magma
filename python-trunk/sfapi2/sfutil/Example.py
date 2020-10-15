"""
Process the creation of new contact and user.

Update existing contact or User record/

Actions to take:

Identify if the record exist in salesforce if so do an update on the contact record otherwise do an insert. 

Based on the job title update the Role and profile in the user table.

Send notifications once the record are created or if the role has changed.


"""

sfUrl = 'https://na1.salesforce.com'

import pprint
import sys
import textwrap
from optparse import OptionParser

from sfMagma import *
from sfConstant import *
from sfUtil import *

class NessTool(SFMagmaTool):
    logname = 'NESSTool'
    trial = False
    debug = False
    
    def getUserChangeObjects(self):
        """
        Get all records form the UserChanges object and 
        """
        print "Inside getuserChangeObject"
        """data1 =[{'EmailEncodingKey':'Big5', 'LanguageLocaleKey':'English','TimeZoneSidKey':'Asia/Calcutta', 'LocaleSidKey':'French','Alias': 'sukanyasubramani_15',   'Email': 'sukanyasubramani_15@yahoo.com',  'FirstName': 'San', 'LastName': 'Ab', 'ProfileId': '00e30000000bnodAAA', 'Reports_To__c': '0033000000CqtnNAAR', 'UserRoleId': '00E30000000c0vCEAQ','Username': 'sukanyasubramani_15@yahoo.com'}]"""
        data1= [{'Username': 'test_sf@test.com', 'TimeZoneSidKey': 'America/Los_Angeles', 'LanguageLocaleKey': 'en_US', 'LastName': 'Test2', 'Alias': 'test2', 'LocaleSidKey': 'en_US', 'EmailEncodingKey': 'ISO-8859-1', 'ProfileId': '00e30000000bnodAAA', 'UserRoleId': '00E30000000c0vCEAQ', 'Email': 'test_sf@test.com'}]
        
        """data1 =[{'EmailEncodingKey':'Big5', 'LanguageLocaleKey':'en_US','TimeZoneSidKey':'Asia/Calcutta', 'LocaleSidKey':'en_US','Alias':'sukanyasubramani_15',   'Email': 'sukanyasubramani_15@yahoo.com',  'FirstName': 'San', 'LastName': 'Ab', 'ProfileId': '00e30000000bnodAAA',  'UserRoleId': '00E30000000c0vCEAQ','Username': 'sukanyasubramani_15@yahoo.com'}]"""
        
        """ data1= [{'ReportsToId': '0033000000CqtnNAAR', 'RecordTypeId': '0123000000001trAAA', 'FirstName': 'San', 'Title': 'Member of Technical Staff', 'LastName': 'Ab', 'EmployeeNumber__c': 'xxx',  'Department': '1100', 'ContactStatus__c': 'Active', 'Email': 'sukanyasubramani_15@yahoo.com', 'AccountId': '00130000003NhNOAA0'}]"""
        
        #testData=" Test Description"
        #tempRec=[{'Id': '00330000000MDjWAAW', 'Update_Description__c': 'Test Description', 'Dry-Run__c': 'Contact Test Run','LastName':'Rzymianowicz'}]
       # print" Data to be Updated is %s" %tempRec
        #contactObjRes = self.update('Contact', tempRec)
       
        """contactObjRes = self.create('Contact', tempRec)"""
        """ contactObjRes = self.create('User', data1)"""
        
        """getEnity Comment
        
        dept="2125"
        userObject=self.getEntityMap("Contact")
        id=userObject.get('fields')
        lb=userObject.get('label')
        fi=userObject.get('fieldInfo')
        print "Label is %s" %lb
        print "Fields is %s" %id
        print "Field Info is %s" %fi
        for fio in fi:
            finfo=fio
            print "Field INFO object %s" %finfo
        tk=fi.get('Dept__c')
        pk=tk.get('picklistValues')
        print "Email value %s" %pk.get('Unicode (UTF-8)')
        pkey=pk.keys()
        for itr in pkey:
            temp=itr
            temp1=temp.split(' ')
            deptCode=temp1[0]
            print "Department code value after extraction %s" %deptCode
            if deptCode==dept:
                print "Department code matched %s" %deptCode
                val=pk.get(temp)
                print "Corresponding Dept value %s" %val
                pass
            continue
        
                
            
        for pke in pkey:
            print " Picklist Keys are %s" %pke
            print "PickList Values are %s" %pk.get(pke)
        for plv in pk:
            pkv=plv
            print "PICKLIST VALUS IS %s" %pkv
            
        print "TimeZoneSidKey  picklist value is %s" %pk
        
        for ur in userObject:
            nm=ur
            print "LABELLLLLL is %s" %nm
        time=userObject.get('label')       
        print " META DATA of USER OBJECT %s" %userObject
        
        print " TimeZoneSidKey %s"  %time
        
        End of comment
        
        
        if contactObjRes in BAD_INFO_LIST:
           msg = "shutdownUser: Create call of Contact Object  failed. Data follows:\n%s" %(pprint.pformat(contactObjRes))
           print "Reason %s" %contactObjRes
           print msg
           self.setLog(msg, 'error')
           pass
        else:
           cobjInfo = contactObjRes[0]
           print "Contact object cretaed successfully with ID %s" % cobjInfo
           """
       
        #soql = "Select FirstName from Contact  where FirstName like 'za%'"
        
        soql="Select Case__c, CR__c, CR_Fields__c, Email__c, Id, LastModifiedDate, Name, SCM_Build__c, Task_Branch__c, Task_Branch_Fields__c, Team_Branch__c, Team_Branch_Fields__c from Interested_Party__c where Id='a0t3000000000wwAAA'"

        ret = self.query('Interested_Party__c', soql=soql)
        
        objInfo = {}
        if ret in BAD_INFO_LIST:
            msg = "Couldn't find any record types for Interested_Party enity"
            print msg
            self.setLog(msg, 'error')
            pass
        
        for nt in ret:
            cr=nt.get('CR__c')
            if cr=='true':
                print "Value of CR is %s" %cr
            val=nt.get('CR_Fields__c')
            print "CR fields are %s" %val
            pass
        
        
        return ret
  
                    
        
    
def main():
    print "Inside Main function of NESS class"
    n=NessTool()
    uList=n.getUserChangeObjects()
    for dt in uList:
        name=dt.get('FirstName')
        print "Full Name from Salesforce %s" %name

if __name__ == "__main__":
    main()
    