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
    
    
    def getUserChangeObjects(self):
        
        contList=[]
        
        """
        Get all records form the UserChanges object and update contact and user objects
        """
        print "Querying all required data from salesforce...."
        
        soql1 = "Select Id,Email__c,Lookup_User__c,Company_Code__c, Date_Of_Hire__c, Department_Code__c, Department_Name__c, Employee_Number__c, Full_Name__c, Location__c, Preferred_Name__c, Reports_To__c, Title__c from UserChange__c"
        soql2 = "Select Id, FirstName, LastName, Email, Contact_User_Id__c, Title, EmployeeNumber__c from  Contact where ContactStatus__c='Active' and (RecordTypeId  ='0123000000000sjAAA' or RecordTypeId  ='0123000000001trAAA')"
        soql3="Select Id, Account_Type_Code__c from Account  where Type ='Magma'"
        
        
        
        ret = self.query('UserChange__c', soql=soql1)
        ret2 =self.query('Contact', soql=soql2)
        ret3=self.query('Account', soql=soql3)
              
        
        if ret in BAD_INFO_LIST:
            msg = "Couldn't find any records in the object UserChange__c" 
            print msg
            self.setLog(msg, 'warn')
            return 
        print "User Change object length '%s'" %len(ret)
        if ret2 in BAD_INFO_LIST:
            msg = "Couldn't find any records in the object Contact" 
            print msg
            self.setLog(msg, 'warn')
            return 
        
        if ret3 in BAD_INFO_LIST:
            msg = "Couldn't find any records in the object Account" 
            print msg
            self.setLog(msg, 'warn')
            return 
        
        
        for hrRec in ret:                        
            contactExist=False
            usrEmail=hrRec.get('Email__c')
            hrId=hrRec.get('Id')
                       
                        
            for ctRec in ret2: 
                contactId=ctRec.get('Id')                                
                contactEmail=ctRec.get('Email')                                
                #print "Contact email and user email are %s  %s " %(usrEmail,contactEmail)  
                if usrEmail == contactEmail:
                    contactExist=True                                        
                    cUserId=ctRec.get('Contact_User_Id__c')                   
                    contUpdateId=self.updateContactRecord(hrRec,ret2,ret3,contactId)
                    hrObjId=self.updateHrObject(hrId,contUpdateId)
                    
                    """if cUserId is not None:                       
                        userUpdateId=self.updateUserRecord(hrRec,ret2,contactId,cUserId)
                        if userUpdateId is not None:
                            hrUserId=self.updateHrUserID(hrId,userUpdateId)
                            pass
                        pass
                    else:
                        msg= "Contact not a SF user: '%s'"%contactEmail
                        self.setLog(msg,'warn')
                        
                        newUId=self.createUserRecord(hrRec,ret2,contactId)                        
                        cIdUpdates=self.updateContactId(contactId, newUId)
                                              
                        pass 
                    """
                    pass                 
                """End for"""
                continue
                
            if not contactExist:  
                msg="Contact does not exist for email addess: %s"  %usrEmail
                self.setLog(msg)
                print msg
                contList.append(usrEmail)
                """            
                cId=self.createContactRecord(hrRec,ret2,ret3)
                hrObjId=self.updateHrObject(hrId,cId)                               
                uId=self.createUserRecord(hrRec,ret2,cId)
                cIdUpdate=self.updateContactId(cId, uId) 
                hrUserId=self.updateHrUserID(hrId,userUpdateId)   """           
                pass                                                                                                         
            
        print "Full Contact list that does not have a email address in SF: '%s'" %contList
        return 
    
    
    def createContactRecord(self,newRec, contObj,acctObj):
        
        uEmp=newRec.get('Employee_Number__c')
        utitle=newRec.get('Title__c')
        uCompany=newRec.get('Company_Code__c')
        uDateOfHire=newRec.get('Date_Of_Hire__c')
        uDepartmentCode=newRec.get('Department_Code__c')
        uDepartmentName=newRec.get('Department_Name__c')
        uEmp=newRec.get('Employee_Number__c')
        uEmail=newRec.get('Email__c')        
        ufName=newRec.get('Full_Name__c')   
        tempName=ufName.split(',')         
        fName=tempName[1].strip()
        lName=tempName[0]
        ltemp=fName.split(' ')
        fName=ltemp[0]
        uPName=newRec.get('Preferred_Name__c')
        uReportsTo=newRec.get('Reports_To__c')
        tempRepName=uReportsTo.split(',')         
        repfName=tempRepName[1].strip()
        replName=tempRepName[0]
        lrtemp=repfName.split(' ')
        repfName=lrtemp[0]
        repId=None
        cobjInfo=[]
        actId=None
        depCode=None
         
        for actRec in acctObj:
            actTypeCode=actRec.get('Account_Type_Code__c')
           
           
            if actTypeCode==uCompany:                
                actId=actRec.get('Id')               
                pass
            continue
        
        for cRecord in contObj:
            firstNm=cRecord.get('FirstName')
            lastNm=cRecord.get('LastName')
           
            if repfName==firstNm and replName==lastNm :
                repId=cRecord.get('Id')
                pass
            continue
       
          
        contactObject=self.getEntityMap("Contact")
        
        fi=contactObject.get('fieldInfo')        
        deptCd=fi.get('Dept__c')
        pk=deptCd.get('picklistValues')        
        pkey=pk.keys()
        for itr in pkey:
            temp=itr
            temp1=temp.split(' ')
            deptCode=temp1[0]           
            if deptCode==uDepartmentCode:                
                depCode=pk.get(temp)
                #print "Corresponding Dept value %s" %depCode
                pass
            continue
        
        data = [{'ReportsToId':repId, 'RecordTypeId':'0123000000001trAAA','FirstName':fName,'LastName':lName, 'Dept__c': depCode,'AccountId':actId,'Email':uEmail ,'Title':utitle, 'Department': uDepartmentName,'EmployeeNumber__c': uEmp,'ContactStatus__c':'Active'}]
        print" Data to be inserted %s" %data
        contactObjRes = self.create('Contact', data)
       
        if contactObjRes in BAD_INFO_LIST:
           msg = "shutdownUser: Create call of Contact Object  failed. Data follows:\n%s" %(pprint.pformat(contactObjRes))
           print "Reason %s" %contactObjRes
           print msg
           self.setLog(msg, 'error')
           pass
        else:
           cobjInfo = contactObjRes[0]
           msg= "CONTACT OBJECT CREATED WITH ID %s" %cobjInfo
           self.setLog(msg)
        
        return cobjInfo
    
    def updateContactRecord(self,updateRec,contObj,acctObj,contId):
                
        uEmp=updateRec.get('Employee_Number__c')
        utitle=updateRec.get('Title__c')
        uCompany=updateRec.get('Company_Code__c')
        uDateOfHire=updateRec.get('Date_Of_Hire__c')
        uDepartmentCode=updateRec.get('Department_Code__c')
        uDepartmentName=updateRec.get('Department_Name__c')
        #uEmp=updateRec.get('Employee_Number__c')
        uEmail=updateRec.get('Email__c')
        ufName=updateRec.get('Full_Name__c') 
        if ufName != None:
            tempName=ufName.split(',')         
            fName=tempName[1].strip()
            lName=tempName[0]
            ltemp=fName.split(' ')
            fName=ltemp[0]
        #uPName=updateRec.get('Preferred_Name__c')
        uReportsTo=updateRec.get('Reports_To__c')
        tempRepName=None
        repfName=None
        replName=None
        if uReportsTo !=None:
            tempRepName=uReportsTo.split(',')         
            repfName=tempRepName[1].strip()
            replName=tempRepName[0]
            lrtemp=repfName.split(' ')
            repfName=lrtemp[0]
        repId=None
        cUpobjInfo=[]
        depCode=None
        
        for actRec in acctObj:
            actTypeCode=actRec.get('Account_Type_Code__c')
            actId=None
            if actTypeCode==uCompany:
                actId=actRec.get('Id')
                pass
            continue
        
        for cRecord in contObj:
            firstNm=cRecord.get('FirstName')
            lastNm=cRecord.get('LastName')
            
            if repfName==firstNm and replName==lastNm :
                repId=cRecord.get('Id')                
                pass
            continue
        
        contactObject=self.getEntityMap("Contact")
        
        fi=contactObject.get('fieldInfo')        
        deptCd=fi.get('Dept__c')
        pk=deptCd.get('picklistValues')        
        pkey=pk.keys()
        for itr in pkey:
            temp=itr
            temp1=temp.split(' ')
            deptCode=temp1[0]           
            if deptCode==uDepartmentCode:                
                depCode=pk.get(temp)                
                pass
            continue
        
        if repId is None:
            msg="Reports to Id is none for contact with email address: %s" %(uEmail)
            self.setLog(msg)
            print msg
            data = [{'Id':contId, 'Dept__c': depCode,'Title':utitle, 'Department': uDepartmentCode,'EmployeeNumber__c': uEmp,'ContactStatus__c':'Active'}]
            pass
        else:
            data = [{'ReportsToId': repId, 'Id':contId,'Dept__c': depCode,'Title':utitle, 'Department': uDepartmentCode,'EmployeeNumber__c': uEmp,'ContactStatus__c':'Active'}]
        """
        data = [{'ReportsToId': repId, 'Id':contId,'AccountId':actId,'Email':uEmail, 'Dept__c': depCode,'Title':utitle, 'Department': uDepartmentCode,'EmployeeNumber__c': uEmp,'ContactStatus__c':'Active'}]
        data1 = "Reports To: %s, FirstName: %s, LastName: %s, Email :%s" %(repfName+ " "+replName,fName,lName,uEmail) +"Department code: %s,Title: %s, Department:%s ,Employee Number: %s" %(depCode,utitle,uDepartmentCode,uEmp)
        tempData=[{'Id': contId, 'Update_Description__c': data1}]"""
        #print" Data to be Updated is %s" % data
        
        conUpRes = self.update('Contact', data)
        
        if conUpRes in BAD_INFO_LIST:
           msg = "shutdownUser: Update call of Contact Object  failed. Data follows:\n%s" %(pprint.pformat(conUpRes))           
           print msg
           self.setLog(msg, 'error')
           pass
        else:
           cUpobjInfo = conUpRes[0]
        msg ="CONTACT OBJECT UPDATED WITH ID %s" %cUpobjInfo
        self.setLog(msg)
        
        return cUpobjInfo
       
    
    def updateContactId(self,contId, userId):
                
        cUpInfo=[]
            
        data = [{'Contact_User_Id__c': userId, 'Id':contId}]
        #print" Data to be Updated %s" %data
        conUpRes = self.update('Contact', data)
        
        if conUpRes in BAD_INFO_LIST:
           msg = "shutdownUser: Update Id call of Contact Object  failed. Data follows:\n%s" %(pprint.pformat(conUpRes))           
           print msg
           self.setLog(msg, 'error')
           pass
        else:
           cUpInfo = conUpRes[0]
        
        #print "CONTACT OBJECT UPDATED WITH ID %s" %cUpInfo
        
        return cUpInfo
    
    def updateHrObject(self,hrChId, contId):
                
        cUpInfo=[]
        
        data = [{'Contact_Id__c': contId, 'Id':hrChId}]
        #print" Data to be Updated %s" %data
        conUpRes = self.update('UserChange__c', data)
        
        if conUpRes in BAD_INFO_LIST:
           msg = "shutdownUser: Update Id call of user change Object  failed. Data follows:\n%s" %(pprint.pformat(conUpRes))           
           print msg
           self.setLog(msg, 'error')
           pass
        else:
           cUpInfo = conUpRes[0]
        
        msg= "UserObject CONTACT ID UPDATED WITH ID %s" %cUpInfo
        self.setLog(msg)
        
        
        return cUpInfo
    
    def updateHrUserID(self,hrChId, userId):
                
        cUpInfo=[]
        
        data = [{'User_Id__c': userId, 'Id':hrChId}]
        self.setLog(" Data to be Updated %s" %data)
        conUpRes = self.update('UserChange__c', data)
        
        if conUpRes in BAD_INFO_LIST:
           msg = "shutdownUser: Update Id call of user change Object  failed. Data follows:\n%s" %(pprint.pformat(conUpRes))           
           print msg
           self.setLog(msg, 'error')
           pass
        else:
           cUpInfo = conUpRes[0]
        
        self.setLog( "HR User ID UPDATED WITH ID %s" %cUpInfo)
        
        return cUpInfo
       
    
    
    def createUserRecord(self,userChRec,contObj,contId):
                
        profileId=None
        roleId=None
        profileInfo=None
        roleInfo=None
        repId=None
        uobjInfo =[]
        utitle=userChRec.get('Title__c')
        email=userChRec.get('Email__c')
        
        dept=userChRec.get('Department_Name__c')
        
        temp=dept.split("'")
        newDept=""
        count=0        
        for dep in temp:
            count=count+1        
            str=dep
            if count==1:
                newDept=str
                pass
            else:
                newDept=newDept+"\\'"+str            
            continue
        
        
        fullName=userChRec.get('Full_Name__c')
        empNo=userChRec.get('Employee_Number__c')
        uReportsTo=userChRec.get('Reports_To__c')
        name=fullName.split(',')
        firstName=name[1]
        lastname=name[0]
        mail=email.split('@')
        alias=mail[0]
        tempRepName=uReportsTo.split(',')         
        repfName=tempRepName[1].strip()
        replName=tempRepName[0]
        lrtemp=repfName.split(' ')
        repfName=lrtemp[0]
        repEmail=None
        usrEmpNo=None
        
        
        """usrQuery="Select IsActive, ProfileId, Title, UserRoleId from User where IsActive= true and LookupUser__c=true and Title= '%s'" %utitle"""
        usrQuery="Select Employee_Number__c from UserChange__c where Department_Name__c='%s' and Title__c='%s' and Lookup_User__c='y'"  %(newDept,utitle)
        #print "Query to USER Object is %s" %usrQuery
        userChObj=self.query('UserChange__c',soql=usrQuery)
        
        if userChObj in BAD_INFO_LIST:
            msg = "Couldn't find any records in the object User" 
            print msg
            self.setLog(msg, 'warn')
            return
        
        for userChRec in userChObj:
            usrEmpNo=userChRec.get('Employee_Number__c')
            continue
        
        roleQuery="Select IsActive, ProfileId, Title, UserRoleId from User where EmployeeNumber='%s'" %usrEmpNo
        #print "Query to USER Object is %s" %roleQuery
        userObj=self.query('User',soql=roleQuery)
        
        if userObj in BAD_INFO_LIST:
            msg = "Couldn't find any records in the object User" 
            print msg
            self.setLog(msg, 'warn')
            return
        
        for userRec in userObj:
            profileId=userRec.get('ProfileId')
            roleId=userRec.get('UserRoleId')
            pass
       
        for cRecord in contObj:
            firstNm=cRecord.get('FirstName')
            lastNm=cRecord.get('LastName')            
            if repfName==firstNm and replName==lastNm:
                repEmail=cRecord.get('Email')
                pass
            continue
        
        userObject=self.getEntityMap("User")
        
        fi=userObject.get('fieldInfo')  
                          
        eencode=fi.get('EmailEncodingKey')
        epk=eencode.get('picklistValues')
        eKey=epk.get('General US & Western Europe (ISO-8859-1, ISO-LATIN-1)')
        
        lkey=fi.get('LanguageLocaleKey')
        lpk=lkey.get('picklistValues')
        llKey=lpk.get('English')
        
        tkey=fi.get('TimeZoneSidKey')
        tpk=tkey.get('picklistValues')
        timeKey=tpk.get('(GMT-08:00) Pacific Standard Time (America/Los_Angeles)')
        
        lsid=fi.get('LocaleSidKey')
        sidpk=lsid.get('picklistValues')
        sidKey=sidpk.get('English (United States)')
               
        userObjdata = [{'Reports_To__c':repEmail,'EmailEncodingKey':eKey, 'LanguageLocaleKey':llKey,'TimeZoneSidKey':timeKey, 'LocaleSidKey':sidKey,'User_Contact_Id__c': contId,'FirstName': firstName, 'LastName': lastname, 'Alias': alias, 'EmployeeNumber':empNo, 'Department': dept, 'Email':email, 'ProfileId':profileId, 'Title': utitle, 'Username': email, 'UserRoleId': roleId }]
        #print "User obejct to be inserted is %s" %userObjdata
        userObjRes = self.create('User', userObjdata)       
        
            
        if userObjRes in BAD_INFO_LIST:
            msg = "shutdownUser: Create call of User Object  failed. Data follows:\n%s" %(pprint.pformat(userObjdata))
            print msg
            self.setLog(msg, 'error')
            pass
        else:
            uobjInfo = userObjRes[0]
            msg= "USER OBJECT CREATED WITH ID %s" %uobjInfo
            self.setLog(msg)
            
        
        
        return uobjInfo
   
    def updateUserRecord(self,userChObj,contObj,contId,userId):
        
        #print "Inside Update of user"
        profileId=None
        roleId=None
        profileInfo=None
        roleInfo=None
        repId=None
       
        utitle=userChObj.get('Title__c')
        email=userChObj.get('Email__c')
        dept=userChObj.get('Department_Name__c')
        dcode=userChObj.get('Department_Code__c')
        temp=dept.split("'")
        newDept=""
        count=0        
        for dep in temp:
            count=count+1        
            str=dep
            if count==1:
                newDept=str
                pass
            else:
                newDept=newDept+"\\'"+str            
            continue
        
        """fullName=userChObj.get('Full_Name__c')
        empNo=userChObj.get('Employee_Number__c')
        uReportsTo=userChObj.get('Reports_To__c')
        uLookup=userChObj.get('Lookup_User__c') 
        name=fullName.split(',')
        firstName=name[1]
        lastname=name[0]
        mail=email.split('@')
        alias=mail[0]
        uobjInfo=[]  
        tempRepName=None
        repfName=None
        replName=None
        if uReportsTo !=None:   
            tempRepName=uReportsTo.split(',')         
            repfName=tempRepName[1].strip()
            replName=tempRepName[0]
            lrtemp=repfName.split(' ')
            repfName=lrtemp[0]
        repEmail=None"""
        
        userEmail=None
        uobjInfo=[]
        userObj=[]
       
        """usrQuery="Select IsActive, ProfileId, Title, UserRoleId from User where IsActive= true and LookupUser__c=true and Title= '%s'" %utitle
        userObj=self.query('User',soql=usrQuery)"""
        usrQuery="Select Email__c from UserChange__c where Department_Name__c='%s' and Title__c='%s' and Lookup_User__c='y'" %(newDept,utitle)
        #print "Query to USER Object is %s" %usrQuery
        userChObj=self.query('UserChange__c',soql=usrQuery)
        
        if userChObj in BAD_INFO_LIST:
            msg = "Couldn't find any records in the object User. Hence not updating the object" 
            print msg
            self.setLog(msg, 'warn')
            pass
        else:
            if len(userChObj)==1:                
                for userChRec in userChObj:
                    userEmail=userChRec.get('Email__c')                
            
                    if userEmail is not None:
                        roleQuery="Select IsActive, ProfileId, Title, UserRoleId from User where Email ='%s' and IsActive=true" %userEmail
                        print "Query to USER Object is %s" %roleQuery
                        userObj=self.query('User',soql=roleQuery)
                        pass
                    
                        if userObj in BAD_INFO_LIST:
                            msg = "Couldn't find any records in the User object " 
                            print msg
                            self.setLog(msg, 'warn')
                            pass
                        else:
                            for userRec in userObj:
                                profileId=userRec.get('ProfileId')
                                roleId=userRec.get('UserRoleId')
                                pass         
                        
                             
                            """userObjdata = [{'Id': userId,'User_Contact_Id__c': contId, 'Alias': alias, 'EmployeeNumber':empNo, 'Department': dept, 'Email':email, 'ProfileId':profileId, 'Title': utitle, 'Username': email, 'UserRoleId': roleId }]
                             print "Update user object %s" %userObjdata
                            userObjRes = self.update('User', userObjdata) 
                            for cRecord in contObj:
                                firstNm=cRecord.get('FirstName')
                                lastNm=cRecord.get('LastName')            
                                if repfName==firstNm and replName==lastNm:
                                    repEmail=cRecord.get('Email')                 
                                    pass
                                continue
                             """
                        
                            profileInfo = self.getObjInfo('Profile', profileId)
                            profileName = profileInfo.get('Name', None)
                            
                            roleInfo = self.getObjInfo('UserRole', roleId)
                            roleName = roleInfo.get('Name', None)
                            
                            #data1= "Reports To:%s, FirstName: %s, LastName:%s , Alias:%s, Employee Number:%s" %(repEmail,firstName,lastname,alias,empNo)+ "'Department: %s, Email: %s:, ProfileId :%s, Title: %s,  UserRoleId' %s" %(dept,email,profileName,utitle,roleName)
                            
                            data1="Profile Name : %s, Role Name : %s" %(profileName,roleName)
                            
                            #tempdata=[{'Id': userId, 'Description__c': data1}]
                            
                            tempdata=[{'Id': userId, 'ProfileId': profileId,'UserRoleId': roleId}]
                            #print "Update user object %s" %tempdata
                            userObjRes = self.update('User', tempdata)         
                            
                                
                            if userObjRes in BAD_INFO_LIST:
                                msg = "shutdownUser: Update call of User Object  failed. Data follows:\n%s" %(pprint.pformat(userObjdata))
                                print msg
                                self.setLog(msg, 'error')
                                pass
                            else:
                                uobjInfo = userObjRes[0]
                                self.setLog("USER OBJECT UPDATED WITH ID %s" %uobjInfo)
                                pass
                            pass #else
                        pass #if
                    pass #for
                pass#if
            pass#else
                
        return uobjInfo
    
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
    n=NessTool()
    n.getUserChangeObjects()
    

if __name__ == "__main__":
    main()
    