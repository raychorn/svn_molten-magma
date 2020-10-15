"""
entity objects to allow the new PE_Checkpoint entity to interact with 
Task and Team Branches.  Using objects in other files but localizing 
all logic and script command in this file.
  Chip Vanek Sept 4, 2006
"""
import sys, time, os
import StringIO, getopt
import copy, re
import traceback
import pprint
from types import ListType, TupleType, DictType, DictionaryType
from optparse import OptionParser, OptionGroup
from SfConstant import *
from Properties import Properties
from SfdcConnection import SfdcConnection
from SObjectClassFactory import SObjectClassFactory
from SfdcApiFault import SfdcApiFaultFactory

from SfConnection import TestCxn
from SFUtil import *
from SfPECheckpoint import *

from Util import booleanize, listify
import PysfdcLogger, logging
log = logging.getLogger('pysfdc.WalkSFUtil')

#import tokenFile

class WalkSFUtil:
    
    cxn = TestCxn().cxn
    sfUtil=SFUtil()
    

    def rejectToDevByPe(self, peId, stream, st=0):
        
        log.info("Actioning Rejected by PE")
        
        """ set status on branch to trigger state change ONLY if all PEs have approved """        
        queryStr="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Checkpoint_Branch__c='%s' and Stream__c ='%s'"%(peId,stream)
        queryList=self.cxn.query(queryStr)      
        staRej="Rejected by PE"      
             
        if queryList in BAD_INFO_LIST:
            log.info('NO Task Existing Branch found')
            return queryList
        else:
            # set all the branch approvals status if it was approved by the PE
            for qr in queryList:
                approv=qr.get('Approve__c')
                baId=qr.get('Id')
                curBASta=self.setBAStatus(baId,approv)
                              
       
        self.setBranchRejStatus(peId,stream,staRej)            
        self.checkTaskBranch(peId,stream)
        self.checkCRsLinked(peId,stream)    
        self.checkBRCRLinks(peId,stream)     
        self.checkTeamLinks(peId,stream)               
        return 
    
    def submitByPe(self, peId, stream, st=0):
        log.info("Actioning Submitted by PE")
        """ set status on branch to trigger state change ONLY if all PEs have approved """
        status = 'Approved, pending Branch'
        queryStr="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Checkpoint_Branch__c='%s' and Stream__c ='%s'"%(peId,stream)
        queryList=self.cxn.query(queryStr)      
        status=None      
        staRej=None
        staApp=None      
        if queryList in BAD_INFO_LIST:
            log.info('NO Task Existing Branch found')
            return queryList
        else:
            # set all the branch approvals status if it was approved by the PE
            for qr in queryList:
                approv=qr.get('Approve__c')
                baId=qr.get('Id')
                baStat=self.setBAStatus(baId,approv)
                if baStat in ['Rejected']:
                    #Atleast one branch was jecteded
                    staRej="Rejected"                
                continue       
        
        self.setBranchAppStatus(peId,stream,staRej)            
        self.checkTaskBranch(peId,stream)
        self.checkCRsLinked(peId,stream)    
        self.checkBRCRLinks(peId,stream)    
        self.checkTeamLinks(peId,stream)                
        return 
    
    def setBranchAppStatus(self,peId,stream,staRej):
        status=None
        if staRej in ['Rejected']:
            status="Rejected by PE"
        else:
            queryStr1="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Checkpoint_Branch__c='%s' and Stream__c ='%s'"%(peId,stream)
            queryList1=self.cxn.query(queryStr1)                 
            status="Approving by PE"
            
            for qr1 in queryList1:                           
                approv=qr1.get('Approve__c')           
                baId=qr1.get('Id')
                if approv in ['Approve','approve']:
                    status = 'Approved, pending Team Branch'                    
                    pass
                else:
                    status="Approving by PE"
                    break  
                continue    
        #print "STATUS..... %s" %status        
        self.setBranchStatus(peId,status)    
        
    def setBranchRejStatus(self,peId,stream,baStatus):
        queryStr1="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Checkpoint_Branch__c='%s' and Stream__c ='%s'"%(peId,stream)
        queryList1=self.cxn.query(queryStr1)                 
        status="Rejected by PE"
        
        for qr1 in queryList1:                           
            approv=qr1.get('Approve__c')           
            baId=qr1.get('Id')
            if approv in ['Reject','reject']:
                status = 'Rejected by PE'                    
                pass            
            break    
        #print "STATUS..... %s" %baStatus        
        self.setBranchStatus(peId,baStatus)   
                
        
    def setBAStatus(self,baId,approve):
        retrievedObj = self.cxn.retrieve('Branch_Approval__c', baId)                
        st=time.time
        staRej=None
        staApp=None        
        if approve in ['Approve','approve']:
            retrievedObj['Status__c'] = "Approved"  
            staApp="Approved"
            #retrievedObj['Date_Time_Actioned__c']=st
            saveResult = retrievedObj.update() 
        if approve in ['Reject','reject']:
            retrievedObj['Status__c'] = "Rejected Back to Developer"  
            #retrievedObj['Date_Time_Actioned__c']=st
            staRej="Rejected"
            saveResult = retrievedObj.update() 
        if approve in ['',None]:
            retrievedObj['Status__c'] = "Approving"                          
            saveResult = retrievedObj.update() 
                        
        return staRej
    
    
    def setBranchStatus(self,peId,status):
        
        retrievedObj = self.cxn.retrieve('Checkpoint_Branch__c', peId)                        
        retrievedObj['Status__c'] = status  
        saveResult = retrievedObj.update()        
        #self.propogateChnages(0)    
           
    def checkPEBranch(self,peBranch,stream):  
        
        queryStr="Select Id, Name, Stream__c from  Checkpoint_Branch__c where Name='%s' and Stream__c ='%s'"%(peBranch,stream)
        queryList=self.cxn.query(queryStr)               
        peId=None
               
        if queryList in BAD_INFO_LIST:
            log.info ("NO PE Branch found with name %s in stream %s"%(peBranch,stream))
            sys.exit()
                        
        else:
            #print "WARNING: Found more than one branch"
            peData=queryList[0] 
            peId=peData.get('Id')
            self.checkBranchStatusById(peId,stream)
        return
    
    def checkBranchStatusById(self,peId,stream):
        #check the current status of the branch and propogate the chnaged to all its linked objects
        #print "Actioning Check on PE Checkpoint branch with Id %s" % peId
        retrievedObj = self.cxn.retrieve('Checkpoint_Branch__c', peId)
        curStatus=retrievedObj.get('Status__c')        
        print "Actioning Check Command on PE Checkpoint branch with Id %s and Status '%s' " %(peId,curStatus)
        log.info("Actioning Check on PE Checkpoint branch with Id %s and Status '%s' " %(peId,curStatus))
        if curStatus in ['PE Submitted', 'Approving by PE','Awaiting Branches']:
            #check for the branch approvals ans trigger the changed to the PE bracnch
            # if the branch approvals are fully approved then trigger the changes to the PE status
            staRej=None
            queryStr1="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Checkpoint_Branch__c='%s' and Stream__c ='%s'"%(peId,stream)
            queryList1=self.cxn.query(queryStr1)                             
            for qr in queryList1:
                approv=qr.get('Approve__c')
                baId=qr.get('Id')
                baStat=self.setBAStatus(baId,approv)
                if baStat in ['Rejected']:
                    #Atleast one branch was jecteded
                    staRej="Rejected"                
                continue   
            
            self.setBranchAppStatus(peId,stream,staRej)  
        elif curStatus in ['Rejected by PE']:
            queryStr="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Checkpoint_Branch__c='%s' "%(peId)
            queryList=self.cxn.query(queryStr)      
                         
            if queryList in BAD_INFO_LIST:
                log.info('NO PE BA barnch found for ID %s' %peId)                
            else:
                for qr in queryList:
                    baId=qr.get('Id')
                    baRetObj = self.cxn.retrieve('Branch_Approval__c', baId)
                    baRetObj['Approve__c']='Reject'
                    baRetObj['Status__c'] = "Rejected Back to Developer"  
                    saveResult = baRetObj.update() 
                    continue                            
        else:
            #all branch approvals have to be have to set to be approved
            queryStr="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Checkpoint_Branch__c='%s' "%(peId)
            queryList=self.cxn.query(queryStr)      
                         
            if queryList in BAD_INFO_LIST:
                log.info('NO PE BA barnch found for ID %s '%peId)                
            else:
                for qr in queryList:
                    baId=qr.get('Id')
                    baRetObj = self.cxn.retrieve('Branch_Approval__c', baId)
                    baRetObj['Status__c'] = "Approved"  
                    baRetObj['Approve__c']='Approve'
                    saveResult = baRetObj.update() 
                    continue    
                
        self.checkTaskBranch(peId,stream)
        self.checkCRsLinked(peId,stream)
        self.checkBRCRLinks(peId,stream)
        self.checkTeamLinks(peId,stream)
        print "Check complete on PE branch with Id %s" % peId
                   
        return
    
    def checkTaskBranch(self,peId,stream):
        
        crtSfPE = SfPECheckpoint()
        crtSfPE.setUp()
               
        retrievedObj = self.cxn.retrieve('Checkpoint_Branch__c', peId)
        status=retrievedObj.get('Status__c')        
        queryStr="Select Branch_Status__c, Code_Stream__c, Id, Name, PE_Checkpoint__c from Task_Branch__c  where PE_Checkpoint__c='%s' and Code_Stream__c ='%s'"%(peId,stream)
        taskId=None        
        queryList=self.cxn.query(queryStr)
        if queryList in BAD_INFO_LIST:
                log.info('NO PE BA barnch found')                
        else:
            for qr in queryList:
                taskId=qr.get('Id')
                taskName=qr.get('Name')
                print "INFO:    Checking Task branch '%s'" % taskName
                taskObj = self.cxn.retrieve('Task_Branch__c', taskId)
                del taskObj['Branch_Status__c']
                #print "TB STATUS  ************************** %s " %status
                taskObj['Branch_Status__c']=status
                saveResult = taskObj.update()
                crtSfPE.linkCrs(taskId,peId)
                crtSfPE.updateBranchApprovals(taskId,peId,stream)
        if status  in ['Awaiting Branches']:
            pass
        elif status in ['Rejected by PE']:
            qStr="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Task_Branch__c='%s' and (Approval_Role__c='%s' or Approval_Role__c='%s' or Approval_Role__c='%s')"%(taskId,'Partition Reviewer','Engineering Manager','Developer')
            qList=self.cxn.query(qStr)
            for qry in qList:
                baId=qry.get('Id')
                baRole=qry.get('Approval_Role__c')
                baObj = self.cxn.retrieve('Branch_Approval__c', baId)
                if baRole in ['Developer']:                    
                    baObj['Status__c'] = "Rejected Back to Developer"
                    del baObj['Approve__c']
                    #baObj['Approve__c']==None
                    saveResult = baObj.update()
                else:                              
                    baObj['Status__c'] = "Pending Submission"
                    del baObj['Approve__c']
                    #baObj['Approve__c']==None
                    saveResult = baObj.update()
        elif status in ['Approving by PE']:
            qStr1="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Task_Branch__c='%s' and (Approval_Role__c='%s' or Approval_Role__c='%s' or Approval_Role__c='%s' )"%(taskId,'Partition Reviewer','Engineering Manager','Developer')
            qList1=self.cxn.query(qStr1)
            for qry in qList1:
                baId=qry.get('Id')
                baRole=qry.get('Approval_Role__c')
                baObj = self.cxn.retrieve('Branch_Approval__c', baId)
                if baRole in ['Developer']:                    
                    baObj['Status__c'] = "Submitted"
                    del baObj['Approve__c']
                    #baObj['Approve__c']==None
                    saveResult = baObj.update()
                else:
                    baObj['Status__c'] = "Approved"
                    baObj['Approve__c']='Approve'
                    saveResult = baObj.update()
                    
        else:
            # Add code to set a flag to call walker on api2            
            baObj = self.cxn.retrieve('Task_Branch__c', taskId)
            if baObj not in [None,'']:
                retrievedObj['Need_Check__c'] = False 
                saveResult = baObj.update()  
            pass
          
        return
    
    def checkBRCRLinks(self,peId,stream):        
        retrievedObj = self.cxn.retrieve('Checkpoint_Branch__c', peId)
        status=retrievedObj.get('Status__c')        
        queryStr="Select Branch_Status__c, Id, Name, PE_Checkpoint__c, Stream__c from Branch_CR_Link__c where PE_Checkpoint__c='%s'"%(peId)
        #print queryStr
        queryList=self.cxn.query(queryStr)
        if queryList in BAD_INFO_LIST:
                log.info('NO PE BA barnch found')                
        else:
            for qr in queryList:
                brcrId=qr.get('Id')
                log.info("Checking BR CR object with Id %s" % brcrId)
                caseBrObj = self.cxn.retrieve('Branch_CR_Link__c', brcrId)
                del caseBrObj['Branch_Status__c']
                caseBrObj['Branch_Status__c']=status
                saveResult = caseBrObj.update()
        
        return

    
    def checkCRsLinked(self,peId,stream):        
        retrievedObj = self.cxn.retrieve('Checkpoint_Branch__c', peId)
        status=retrievedObj.get('Status__c')        
        queryStr="Select CaseNumber, Code_Streams_Priority__c, Id, PE_Checkpoint__c, Status, Status_1_Stream__c from Case  where PE_Checkpoint__c='%s'"%(peId)
        #print queryStr
        queryList=self.cxn.query(queryStr)
        if queryList in BAD_INFO_LIST:
                log.info('NO PE BA barnch found')                
        else:
            for qr in queryList:
                caseId=qr.get('Id')
                log.info("Checking Case object with Id %s" % caseId)
                codeSt=qr.get('Code_Streams_Priority__c')
                stFiled,stStream=self.findCRStreamStatus(codeSt,stream)
                caseObj = self.cxn.retrieve('Case', caseId)
                caseObj[stFiled]=status
                caseObj[stStream]=stream
                saveResult = caseObj.update()
        
        return
    
    def checkTeamLinks(self,peId,stream):
                
        crtSfPE = SfPECheckpoint()
        crtSfPE.setUp()
               
        queryStr="Select Branch_Status__c, Code_Stream__c, Id, Name, PE_Checkpoint__c from Task_Branch__c  where PE_Checkpoint__c='%s' and Code_Stream__c ='%s'"%(peId,stream)
        taskId=None        
        queryList=self.cxn.query(queryStr)
        if queryList in BAD_INFO_LIST:
                log.info('NO PE BA barnch found')                
        else:
            for qr in queryList:
                taskId=qr.get('Id')
                alreadyLinked=crtSfPE.checkTeamBranchLink(peId,taskId)
                #crtSfPE.updateBranchApprovals(taskId,peId,stream)
                continue
            pass
                  
        return
        
    def findCRStreamStatus(self,codeStream,stream):        
        validStreams=[]
        streams=codeStream.split(',')
        for st in streams:
            st=st.strip()
            if st in ACTIVE_STREAMS:
                validStreams.append(st)
        #print "Valid active streams %s" % validStreams
        count =0
        for vs in validStreams:
            if vs==stream:
                break
            else:
                count=count+1
        if count ==0:
            stField='Status_1_Stream__c'              
            stStream='X1st_Stream__c'
        elif count==1:
            stField='Status_2_Stream__c'
            stStream='X2nd_Stream__c'
        else:
            stField='Status_3_Stream__c'  
            stStream='X3rd_Stream__c'              
           
        return stField,stStream
    
    
