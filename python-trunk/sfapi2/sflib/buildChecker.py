""" 
Process to create reconile build objects link records with build object and task branches using 

the patch version number.

"""
import sys, time, os, datetime
import grp, pprint
import StringIO, getopt
import copy, re
import pprint
import traceback
from sfMagma import *
from sfConstant import *
from sfUtil import *
from types import ListType, TupleType, DictType, DictionaryType
from optparse import OptionParser
from sfMagma import *
from sfUser import SFUserTool
from sfNote import *
from sfCr import *
from sfConstant import *
from sfUtil import cronLock, uniq
from sop import ccBranches, opBranches, sfBranches, sfEntities, SFEntitiesMixin, SFUtilityMixin, SFTestMixin, BasicCacheMixin
import tokenFile
from emailTransMap import emailTransMap


class buildChecker(SFMagmaTool):
    logname = 'BuildChecker'
    
    
    def getNewBuildObjects(self):
        
        """
        Get all records from the build object that has the Needs_Check_Flag set to true.
        """
               
        soql1="Select Access_Path__c, Build_Date__c, Build_ID__c, Build_Path__c, Build_Type__c, Id, Name, Needs_Check__c from Build__c where Needs_Check__c =true"
        
        ret = self.query('Build__c', soql=soql1)
                
        if ret in BAD_INFO_LIST:
            msg = "Couldn't find any records in the Build object that needs to be checked" 
            print msg
            self.setLog(msg, 'warn')
            return 
        
        else:                   
            for bldRec in ret:     
                task={}
                bldLink={}
                new={}
                cur={}
                buildVersion=bldRec.get('Build_ID__c')
                buildObjId=bldRec.get('Id')
                
                soql2="Select Id, Name, Patch_Version__c, Code_Stream__c, CreatedDate, OwnerId from Task_Branch__c where Patch_Version__c ='%s'" %(buildVersion)
                soql3="Select Build__c, Id, Name, Task_Branch__c from Build_Branch_Link__c where Build__c ='%s'" %(buildObjId)
                
                ret1 = self.query('Task_Branch__c', soql=soql2)       
                ret2=self.query('Build_Branch_Link__c',soql=soql3)               
                
            
                if ret1 in BAD_INFO_LIST:
                    msg = "Couldn't find any records in the Task Branch for the given version number" 
                    print msg
                    self.setLog(msg, 'warn')                
                    pass  
                
                else:
                    taskObj=[]
                    for tskRec in ret1:
                        id=tskRec.get('Id')                                                                                    
                        task[id]=tskRec
                        continue
                    pass
                
                if ret2 in BAD_INFO_LIST:
                    msg ="Could not find any records for the Build Branch Link Object"
                    print msg
                    self.setLog(msg, 'warn')
                    pass
                
                else:
                    for buildLink in ret2:
                        id= buildLink.get('Id')
                        taskId=buildLink.get('Task_Branch__c')
                        bldLink[taskId]=id
                        continue
                    pass      
                
                new=task.keys()
                current=bldLink.keys()
        
                toBeDeleted=[]
                toBeCreated=[]
        
                for td in new:
                    if (td not in current):
                        toBeCreated.append(td)
                        pass
                    continue
        
                for tc in current:
                    if (tc not in new):
                        toBeDeleted.append(tc)
                        pass
                    continue
                
                #print "To be created %s" %toBeCreated
                #print "To Be deleted %s" %toBeDeleted
                
                #Delete the records
                if toBeDeleted is not None:
                    self.tobeDeletd(toBeDeleted,bldLink,buildObjId)
                                          
                
                if toBeCreated is not None:  
                    self.tobeCreated(toBeCreated,task,buildObjId)                
                    
                
                #Set the need_Check to false
                
                upData=[{'Id':buildObjId, 'Needs_Check__c':False}]                
                buildUpdate=self.update('Build__c', upData)   
                if buildUpdate in BAD_INFO_LIST:                    
                    msg = "shutdownUser: Upadet call of Contact Object  failed. Data follows:\n%s" %(pprint.pformat(buildUpdate))                    
                    print msg
                    self.setLog(msg, 'error')
                    pass 
                else:
                    msg="Upadted the build object with unmarking the Needs_to_check flag"
                    self.setLog(msg, 'INFO')
                    pass                                   
                continue #for
            pass #else      
            
                    
                        
    def tobeDeletd(self,tbd,bldLink,buildObjId): 
        for dt in tbd:
            bId=[]
            buildLnId=bldLink.get(dt) 
            self.deleteCRList(dt,buildObjId)  
            bId.append(buildLnId)    
            msg="Build branch link with Id %s is deleted" %(bId)  
            print msg
            self.log.info(msg)                              
            delBiuldLink=self.delete(bId)  
         
            if delBiuldLink in BAD_INFO_LIST:                    
                msg = "shutdownUser: delete call  failed. Data follows:\n%s" %(pprint.pformat(delBiuldLink))
                print "Reason %s" %delBiuldLink
                print msg
                self.setLog(msg, 'error')
                pass  
            continue             
        pass
    
      
    def tobeCreated(self,tbc,task,buildObjId):
        for cr in tbc:
            taskObj=task.get(cr)
            taskId=cr
            ownerId=taskObj.get('OwnerId')
            stream=taskObj.get('Code_Stream__c')
            date=taskObj.get('CreatedDate')            
            newdate=self.checkDate(date)            
            #cdate=taskObj.get('CreatedDate')            
            name="BldLink"                                  
            
            data = [{'Build__c':buildObjId, 'Name':name,'Task_Branch__c':taskId,'Created_Date__c':newdate,'Owner__c':ownerId,'Stream__c':stream}]           
            buildLinkObjRes = self.create('Build_Branch_Link__c', data)   
            if buildLinkObjRes in BAD_INFO_LIST:
                msg = "shutdownUser: Create call of Contact Object  failed. Data follows:\n%s" %(pprint.pformat(buildLinkObjRes))
                print "Reason %s" %buildLinkObjRes
                print msg
                self.setLog(msg, 'error')
                pass
            else:
                bobjInfo = buildLinkObjRes[0]
                msg= "Build Link Object CREATED WITH ID %s" %bobjInfo
                print msg
                self.log.info(msg)
                self.createCRList(taskId,buildObjId)
                pass
            continue            
        return   
    
    def createCRList(self, taskId,buildObjId):
        comp=None
        type=None
        priority=None
        fields=('Component__c', 'Priority', 'Type')
        soql1="Select Case__c, CR_Num__c, Stream__c, Task_Branch__c from Branch_CR_Link__c where Task_Branch__c ='%s'" %(taskId)        
        ret = self.query('Branch_CR_Link__c', soql=soql1)         
        if ret not in BAD_INFO_LIST:            
            for cr in ret:
                caseId=cr.get('Case__c')
                stream=cr.get('Stream__c')
                """soql2="Select Approval_Role__c, Approve__c, Case__c, Id, Status__c from Branch_Approval__c where Case__c='%s'  and  Stream__c ='%s' and Approval_Role__c='CR Originator' and (Approve__c !='Reject' or Status__c!='Merged - Rejected')" %(caseId,stream)                
                ret2=self.query('Branch_Approval__c', soql=soql2) 
                if ret2 not in BAD_INFO_LIST:
                    for br in ret2: """
                cId=[]                       
                #caseId=br.get('Case__c') 
                cId.append(caseId)
                caseRes = self.retrieve(cId, 'Case', fields)
                for cres in caseRes:
                    comp=cres.get('Component__c')
                    priority=cres.get('Priority')
                    type=cres.get('Type')
                    continue
                name="CRLink" 
                data = [{'Build__c':buildObjId,'Name':name,'Component__c':comp,'Priority__c':priority,'Type__c':type,'Task_Branch__c':taskId,'Case__c':caseId}]
                msg=" Data to be inserted %s" %data
                self.log.info(msg)
                crObjRes = self.create('CR_List__c', data)   
                if crObjRes in BAD_INFO_LIST:
                    msg = "shutdownUser: Create call of Contact Object  failed. Data follows:\n%s" %(pprint.pformat(crObjRes))
                    print "Reason %s" %crObjRes
                    print msg
                    self.setLog(msg, 'error')
                    pass
                else:
                    crobjInfo = crObjRes[0]
                    msg= "CR Link Object CREATED WITH ID %s" %crobjInfo   
                    print msg                         
                    self.log.info(msg)
                    pass                       
                continue
                    #pass #if               
               # continue #for
            pass     #if   
        else:
            msg = "No Task branch found for Id %s" %(taskId)                    
            print msg
            self.setLog(msg, 'error')
            pass
        pass
    
    def deleteCRList(self,taskId,buildObjId):
        soql1="Select Id, Task_Branch__c from CR_List__c where Task_Branch__c='%s' and Build__c='%s'" %(taskId,buildObjId)
        ret = self.query('Task_Branch__c', soql=soql1) 
        if ret not in BAD_INFO_LIST: 
            for cr in ret:                
                crlink=[] 
                crLinkId=cr.get('Id')
                crlink.append(crLinkId)  
                msg= "CR ID to be delted %s" % crlink  
                print msg                          
                self.log.info(msg)
                delCRLink=self.delete(crlink)  
             
                if delCRLink in BAD_INFO_LIST:                    
                    msg = "shutdownUser: delete call  failed. Data follows:\n%s" %(pprint.pformat(delCRLink))
                    print "Reason %s" %delCRLink
                    print msg
                    self.setLog(msg, 'error')
                    pass  
                continue   
            pass                        
            
                
    
def main():    
    n=buildChecker()
    n.getNewBuildObjects()
    

if __name__ == "__main__":
    main()
