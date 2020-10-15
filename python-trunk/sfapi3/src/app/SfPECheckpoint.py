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
import datetime
import time
from types import ListType, TupleType, DictType, DictionaryType
from optparse import OptionParser, OptionGroup
from SfConstant import *
from WalkSFUtil import *
from SFUtil import *
from Properties import Properties
from SfdcConnection import SfdcConnection
from SObjectClassFactory import SObjectClassFactory
from SfdcApiFault import SfdcApiFaultFactory
from TaskBranchStatusMap import *

from SfConnection import TestCxn

from Util import booleanize, listify
import PysfdcLogger, logging
log = logging.getLogger('pysfdc.lnPEchpnt')

#import tokenFile

class SfPECheckpoint:
    
    modList = []
    loadFromSF = False
    branchType = 'team'
    seqTypes = [ListType, TupleType]

    #######################################################################
    # Team Branch data management methods
    #######################################################################
    def setUp(self):
        self.cxn = TestCxn().cxn
        self.idList = []
        return
    
    
    def loadPEBranch(self, pebranch, stream):
        """ load the TmB object and set branch to team label """
        #print "Branch name: %s" %branch
        branch = pebranch
        stream = stream
        peData = self.getSFData(branch, stream, show=False)
        #print "TB DATA %s" %tbData
        
        return peData
    
    def getSFData(self, branch, stream, show=True):
        """
        Get team branch object given a branch name and code stream
        'The Original!' [TM]
        """
        #where = [['Name','like',branch]
         #       ,'and',['Stream__c','=',stream]]
        #queryList = self.sfb.query('Checkpoint_Branch__c', where=where, sc='all')
        
        queryStr="Select Id,Name from Checkpoint_Branch__c where Name='%s' and Stream__c ='%s'"%(branch,stream)
        queryList=self.cxn.query(queryStr)
               
               
        if queryList in BAD_INFO_LIST:
            log.info('NO Task Existing PE checkpoint found')
            return queryList
        
        if len(queryList) > 1:
            print 'WARNING: There should be only ONE PE barnch for %s'\
                  %pprint.pformat(where)   
        return queryList
     
   

    def addPEBranchUsage(self,err=''):
        """  Prints the Usage() statement for this method    """
        m = ''
        
        if len(err):
            m += '%s\n\n' %err
    
        m += 'Link a PE Checkpoint to a Task Branch(es) (TB) with a Team Branch (TmB) on Salesforce.\n'
        m += '\n'
        m += 'Usage:\n'
        m += '    lnpechpnt [OPTIONS] -s <stream> -p <PE Checkpoint name> -t <team name> -b <task branch> -l <file path>\n'       
        m += '\n'
        m += 'Options include:\n'
        m += '  *  -s <Stream name> Valid stream name (blast5, talus1.0)'
        m += '    \n'
        m += '  *  -p <PE Checkpoint name>  PE Checkpoint which task branches must be linked'
        m += '    \n'
        m += '  *  -t <team Branch>  Team branch to which PE Checkpoint should br be linked\n'
        m += '        Use the command teams to find an active team \n'
        m += '        Use the command teamls -stalus -n<team name> to find active team branches\n'
        m += '    \n'
        m += '    -b <Task Branch> Task Branch which has be to linked to the PE Checkpoint'
        m += '    \n'
        m += '  *        OR use the option below to add a list of Task Branches\n'
        m += '    -l  <file path>  List of task branches one branch name per line\n'
        m += '    \n'
        m += '       Commands marked with a * are required\n'
        return m
    
    def addPEBranchCL(self,team,  branch, pebr,stream, options, st, teamTool=None,
                        checkTmb=True, scmFlag=False):
        """ command line logic for addPECheckPointBranch
        set checkTmb to false to allow fast linking. Must run check manually
        on the team branch if used.
        """
        
        walkUtil = WalkSFUtil() 
         
        listBranchPath = None
        
        if options is not None:
            debug = options.debug
            if  options.listBranchPath:       
                listBranchPath = options.listBranchPath
            pass
    
        branchList = None
        # process listBranchPath to result in a list of branch names
        if branchList is None:
            # no list passed in, check options for file to parse
            
            branchList = self.parseBranchListFile(listBranchPath)      
            log.info("Branch List provided %s" %branchList)          
                 
        elif branchList not in [ListType, TupleType]:
            # brachList passed in, but not a list. Try making it a list
            branchList = list([branchList])        
            pass
        if branchList is None:        
            branchList=list([branch])
            pass
        #print "BRANCH LIST %s" %branchList
        
        for branch in branchList:                
            team = team.lower()
            if type(branch) is not self.seqTypes:
                if branch in [None,'']:
                    print 'Please provide a branch name to link to the PE Checkpoint %s'%(pebr)
                    sys.exit()
                brList = [branch]
            else:
                brList = branch
            db=options.debug
        
          
            # load the PE Checkpoint branch if present other wise craete it
            peres = self.loadPEBranch(pebr, stream)
            pebrId=None
            if peres in BAD_INFO_LIST:
                print "Creating new PE checkpoint with name: %s"%pebr
                log.info("Creating new PE checkpoint with name: %s"%pebr)
                pebrId=self.createPEBranch(pebr, stream,team)
                pass
            else:                
                peData=peres[0]
                pebrId=peData.get('Id')
                pass
                    
            #print "PE Checkpoint ID is %s" %pebrId 
            
            self.linkTaskBranches(pebrId,pebr,brList,stream)  
        
        walkUtil.checkPEBranch(branch,stream)      
                             
        return
    
    def linkTaskBranches(self,pebrId,pebr,brList,stream):
          
        branchList=brList
        stream=stream
        if branchList in [None,'']:
            print 'Please provide a valid branch to link to %s '%(pebr)
            sys.exit()
        for branch in branchList:
            #print "Linking branch name '%s' to PE Chepoint '%s'"%(branch,pebr)
            brId=self.loadTaskBranch(branch,stream)            
            
            #where = [['PE_Checkpoint__c ','=',pebrId],'and',['Id','=',brId]]   
            #queryList = sfb.query('Task_Branch__c', where=where, sc='all')
            queryStr="Select Id,Name,PE_Checkpoint__c from Task_Branch__c where Id ='%s'"%(brId)                      
            queryList=self.cxn.query(queryStr)
                        
            if queryList in BAD_INFO_LIST:            
                pass                    
            else:
                #data = [{'PE_Checkpoint__c':pebrId,'Id':brId}]                       
                #buildLinkObjRes = sfb.update('Task_Branch__c', data)  
                for qr in queryList:
                    pebr=qr.get('PE_Checkpoint__c')                     
                    tbrId=qr.get('Id')               
                    if pebr in [None,'']:
                        retrievedObj = self.cxn.retrieve('Task_Branch__c', tbrId)   
                        curTbSta=retrievedObj.get('Branch_Status__c')
                        #if curTbSta not in ['Fixing','Rejected by Mgr','Rejected by PE','Rejected by Partition Reviewer','Rejected by SCM','Approving by Partition Reviewer','Approving by Manager']:
                        if curTbSta not in ['Fixing','Rejected by Mgr','Rejected by PE','Rejected by Partition Reviewer','Rejected by SCM','Approving by Partition Reviewer']:
                                                        
                            retrievedObj['PE_Checkpoint__c'] = pebrId
                            retrievedObj['Linked_Objects__c']='PE Checkpoint'
                            saveResult = retrievedObj.update()
                                             
                            self.linkCrs(brId,pebrId)
                            print "INFO: Linking branch name '%s' to PE Checkpoint "%(branch)
                            log.info("Linking branch name '%s' to PE Checkpoint "%(branch))
                            self.updateBranchApprovals(brId,pebrId,stream)
                            alreadyLinked=self.checkTeamBranchLink(pebrId,brId)
                            pass                            
                           
                        else:
                            #print "Current sta        tus of the task branch %s" %curTbSta
                            print "WARNING:   Not linking Task Branch '%s' since its in status '%s'" %(branch,curTbSta)
                            log.info("WARNING:   Task Branch '%s' is in the status '%s'" %(branch,curTbSta))
                            pass
                    else:
                        print "WARNING:    Not linking Task branch '%s' its already linked to a PE checkpoint" %branch 
                        if (pebr ==pebrId):
                            alreadyLinked=self.checkTeamBranchLink(brId,pebrId)
                            self.linkCrs(brId,pebrId)
                            self.updateBranchApprovals(brId,pebrId,stream)
                        else:
                            #print "CR has been already linked to a different PE CHECHPOINT"
                            log.info("CR has been already linked to a different PE CHECHPOINT")
                        pass
                
            pass
        
        return
    
    def checkTeamBranchLink(self,pebrId,tbId):
        alreadyLinked=False
        data={}
        retrievedObj = self.cxn.retrieve('Checkpoint_Branch__c', pebrId)
        teamBrId=retrievedObj.get('Team_Branch__c')
        peStatus=retrievedObj.get('Status__c')
                                        
        if teamBrId not in BAD_INFO_LIST:    
            retrievedTeamObj = self.cxn.retrieve('Team_Branch__c', teamBrId)   
            tmId=retrievedTeamObj.get('Team__c')      
            
            queryStr="Select Id, Name, Task_Branch__c,Team__c, Team_Branch__c from Branch_Team_Link__c where Task_Branch__c='%s'"%(tbId)                      
            queryList=self.cxn.query(queryStr)
            if queryList in BAD_INFO_LIST:   
                brTeamLnId=''             
                log.info("The task branch %s is not linked to a team barnch %s, hence linking it "%(tbId,teamBrId))
                self.setTeamBranchLink(brTeamLnId,teamBrId,tmId,tbId,peStatus)
            elif len(queryList) >1:
                log.info("Error the task branch has more than one team links")
                pass
            else:
                tmBrLnk=queryList[0]
                brTeamLnId=tmBrLnk.get('Id')                                
                log.info("Skipping ....Team Branch Linkage, task barnch is already linked to a team branch")
                self.setTeamBranchLink(brTeamLnId,teamBrId,tmId,tbId,peStatus)
                alreadyLinked=True                
        else:
            print "Team object should be first created before trying to link to it"     
        
        return alreadyLinked
    
    
    def setTeamBranchLink(self, brTeamLnId, teamBrId, tmId, brId, status):
        """ update or create a Team Branch Link object """
        data={}
        
        if brTeamLnId != '':            
            retrievedTeamObj = self.cxn.retrieve('Branch_Team_Link__c', brTeamLnId)            
            curTeamBrlink=retrievedTeamObj.get('Team_Branch__c')            
            if curTeamBrlink!=teamBrId:
                log.info("TEAM BRANCH LINKAGE IS NOT EQUAL HENCE UPDATING TO %s "%teamBrId)
                self.cxn.delete(brTeamLnId)                         
                data['Team__c'] = tmId
                data['Task_Branch__c']=brId
                data['Branch_Status__c']=status
                data['Team_Branch__c']=teamBrId
                newBrTeamLink = SObjectClassFactory(self.cxn, 'Branch_Team_Link__c')
                res = self.cxn.create(newBrTeamLink, data)
                self.setTeamBranchApprovals(data)
                if res in BAD_INFO_LIST:                
                    print "ERROR: In Updating or linking the Team Branch"                
                pass  
            
                     
            #if self.debug >1:
                #print 'Updated TeamBRLink with data:%s\n res:%s'%(data,res)
        else:
            data['Team__c'] = tmId
            data['Task_Branch__c']=brId
            data['Branch_Status__c']=status
            data['Team_Branch__c']=teamBrId
            newBrTeamLink = SObjectClassFactory(self.cxn, 'Branch_Team_Link__c')
            res = self.cxn.create(newBrTeamLink, data)
            self.setTeamBranchApprovals(data)
            #mode = 'Created'
            #if self.debug >1:
                #print 'Create TeamBRLink with data:%s\n res:%s'%(data,res)
            if res in BAD_INFO_LIST:                
                print "ERROR: In Updating or linking the Team Branch"
                return ''
                
        return 
    
    def setTeamBranchApprovals(self,data):
        
        status=''
        approve=''
        order = 4.1        
        tmId=data.get('Team_Branch__c')
        appInst='No additional approval instructions'
        appRole='Team Manager'
        tbId=data.get('Task_Branch__c')
        
        retrievedTbObj = self.cxn.retrieve('Task_Branch__c', tbId)
        
        tbStatus=retrievedTbObj.get('Branch_Status__c')
        stream=retrievedTbObj.get('Code_Stream__c')
        branch=retrievedTbObj.get('Name')        
        subject = 'Team Approval %s in %s '%(branch, stream)
        statMap = TaskBranchStatusMap().getStatusMap()
        tbStatMap = statMap.get(tbStatus,())
        statOrder = tbStatMap.get('order', 0.0)
        team=data.get('Team__c')
        instuct = 'Since you are the Team Manager for %s you are asked to review that the branches in this Team branch'%team
        
        if statOrder >= 42.0:
            status='Team Approved'
            approve='Approve'
        else:
            status='Team Approving'
            approve=''
        
               
        
        queryStr="Select Id, Name, OwnerId,Lookup__c from Product_Team__c where Lookup__c  ='%s'"%(team)                      
        queryList=self.cxn.query(queryStr)   
        pdObj=queryList[0]
        ownerId=pdObj.get('OwnerId')        
        
        baData={}
        baData['Name']=subject
        baData['Order__c']=order
        baData['Approval_Role__c']=appRole
        baData['OwnerId']=ownerId
        baData['Instructions__c']=instuct
        baData['Stream__c']=stream
        baData['Branch__c']=branch
        baData['Status__c']=status
        baData['Approve__c']=approve
        baData['Task_Branch__c']=tbId
        baData['Approval_Instructions__c']=appInst
        baData['Team_Branch__c']=tmId
         
        queryStr2="Select Approval_Role__c, Id, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Task_Branch__c ='%s' and Approval_Role__c='Team Manager'"%(tbId)                      
        queryList2=self.cxn.query(queryStr2) 
        if queryList2  in BAD_INFO_LIST:          
        
            newBALink = SObjectClassFactory(self.cxn, 'Branch_Approval__c')
            res = self.cxn.create(newBALink, baData)                
            if res in BAD_INFO_LIST:            
                print "ERROR: In Creating BA approval team link record"
                return ''    
        else:
            oldBaObj=queryList2[0]
            baId=oldBaObj.get('Id')
            baUpObj = self.cxn.retrieve('Branch_Approval__c', baId)
            baUpObj['Team_Branch__c']=tmId
            baUpres = baUpObj.update()
                
        
        queryStr3="Select Approval_Role__c, Id, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Task_Branch__c ='%s' and Approval_Role__c='CR Originator'"%(tbId)                      
        queryList3=self.cxn.query(queryStr3)
        if queryList3 not in BAD_INFO_LIST:
            for  br in queryList3:
                baId=br.get('Id')
                baObj = self.cxn.retrieve('Branch_Approval__c', baId)
                baObj['Team_Branch__c']=tmId
                bares = baObj.update()                    
        
        return
    
    
    def updateBranchApprovals(self,brId,pebrId,stream):
        #print "BR id .....%s " %brId
        pename=None
        #res=sfb.retrieve([pebrId], 'Checkpoint_Branch__c')
        retrievedObj = self.cxn.retrieve('Checkpoint_Branch__c', pebrId)
        if retrievedObj not in BAD_INFO_LIST:
            pename= retrievedObj.get('Name')            
            pass
        #where = [['Task_Branch__c ','=',brId],'and',['Approval_Role__c','=','Product Engineer']]
        #queryList = sfb.query('Branch_Approval__c', where=where, sc='all')
        queryStr="Select Approval_Role__c, Id, OwnerId, Task_Branch__c,Checkpoint_Branch__c  from Branch_Approval__c where Task_Branch__c='%s' and Approval_Role__c='%s'"%(brId,'Product Engineer')
        #print "QUERY 1=======%s" %queryStr
        queryList=self.cxn.query(queryStr)
        #print "queryLis: %s" %queryList
                
        #print "queryList2: %s"%queryList2
        
        if queryList in BAD_INFO_LIST:            
            log.info("No PE Branch approval found in Task Branch record, hence creating new BA")
            #Create new BA        
            pass
        else: 
            for qr in queryList:
                queryStr2="Select Approval_Role__c, Id, OwnerId, Task_Branch__c,Checkpoint_Branch__c  from Branch_Approval__c where Checkpoint_Branch__c='%s' and Approval_Role__c='%s'"%(pebrId,'Product Engineer')
                #print "Query 2:============= %s"%queryStr2
                queryList2=self.cxn.query(queryStr2)
                baId=qr.get('Id')
                if len(queryList2)==0:
                    log.info("No existing branch approval for the PE checkpoint,hence creating new one")
                    #print "brID.... %s" %brId
                    baObj = self.cxn.retrieve('Branch_Approval__c', baId)    
                    peObj = self.cxn.retrieve('Checkpoint_Branch__c', pebrId) 
                    #print  "baObj %s" %baObj
                    #print "peObj %s" %peObj
                    
                    pebrName=peObj.get('Name')          
                    baObj['Checkpoint_Branch__c'] = pebrId
                    del baObj['Branch__c']
                    del baObj['Task_Branch__c']
                    #del baObj['Approve__c']
                    del baObj['Status__c']
                    baObj['Branch__c'] = pebrName
                    baObj['Status__c'] = "Approving"
                    del baObj['Approve__c']
                    del baObj['Approval_Action__c']
                    #baObj['Task_Branch__c'] = None
                    baObj['Name'] = "Approval %s in %s" %(pebrName,stream)                                            
                    saveResult = baObj.update() 
                    pass
                else:   
                    ownerList=[]                 
                    for qr2 in queryList2:
                        ownerPE=qr2.get('OwnerId')
                        ownerList.append(ownerPE)
                        continue
                    
                    ownerTB=qr.get('OwnerId')
                    #ownerPE=qr2.get('OwnerId')
                    #print "ownerTB %s" %ownerTB
                    #print "ownerList %s" %ownerList
                    if (ownerTB) in ownerList:
                        log.info("A branch approval with the same Id already exist, hence removing the team branch link")
                        self.cxn.delete(baId)
                        pass
                    else:                   
                        print "Creating branch approval Record for the task branch"  
                        log.info("Creating branch approval Record for the task branch")
                        baObj = self.cxn.retrieve('Branch_Approval__c', baId)    
                        peObj = self.cxn.retrieve('Checkpoint_Branch__c', pebrId)  
                        pebrName=peObj.get('Name')          
                        baObj['Checkpoint_Branch__c'] = pebrId
                        del baObj['Branch__c']
                        del baObj['Task_Branch__c']
                        del baObj['Status__c']
                        baObj['Branch__c'] = pebrName
                        baObj['Status__c'] = "Approving"
                        del baObj['Approve__c']
                        del baObj['Approval_Action__c']
                        #baObj['Task_Branch__c'] = None
                        baObj['Name'] = "Approval %s in %s" %(pebrName,stream)                                            
                        saveResult = baObj.update()      
                pass
            
        return
    
    def linkCrs(self,brId,pebrId):
        
        #where = [['Task_Branch__c','=',brId]]
        #queryList = sfb.query('Branch_CR_Link__c', where=where, sc='all')
        queryStr="Select Id,Case__c from Branch_CR_Link__c where Task_Branch__c='%s'"%(brId)
        queryList=self.cxn.query(queryStr)
        if queryList in BAD_INFO_LIST:            
            log.info('CRs do not have to be linked') 
            pass
        else:
            log.info('Linking CRs to PE Checkpoint')
            for qr in queryList:               
                
                caseId=qr.get('Case__c') 
                brcrId=qr.get('Id')          
                
                retrievedBrCrObj = self.cxn.retrieve('Branch_CR_Link__c', brcrId) 
                #print "retrievedObj %s" %retrievedObj
                #print "Length of retrived object %s" %len(retrievedObj)
                if retrievedBrCrObj not in  BAD_INFO_LIST:
                    pebr=retrievedBrCrObj.get('PE_Checkpoint__c')                      
                    #print "pebr %s" %pebr       
                    if pebr in [None,'']:                        
                        retrievedBrCrObj['PE_Checkpoint__c'] = pebrId
                        saveResult = retrievedBrCrObj.update()     
                        log.info('CR BR Link is updated with the PE checkpoint %s '%pebrId)
                        #print "Linking CR Br Link '%s' to the PE checkpoint "   %cNo    
                        log.info("INFO:     Linking CR BR Link '%s' to the PE checkpoint " %pebrId)        
                    else:
                        #print "WARNING:    CR BR Link with Id %s is already is linked to a PE checkpoint" %brcrId
                        log.info("Skipping... CR BR Link with Id %s is already is linked to a PE checkpoint" %brcrId)                
                
                pass         
                
                retrievedObj = self.cxn.retrieve('Case', caseId) 
                #print "retrievedObj %s" %retrievedObj
                #print "Length of retrived object %s" %len(retrievedObj)
                if retrievedObj not in  BAD_INFO_LIST:
                    pebr=retrievedObj.get('PE_Checkpoint__c')  
                    cNo=retrievedObj.get('CaseNumber')
                    #print "pebr %s" %pebr       
                    if pebr in [None,'']:                        
                        retrievedObj['PE_Checkpoint__c'] = pebrId
                        saveResult = retrievedObj.update()     
                        log.info('CR is updated with the PE checkpoint %s '%pebrId)
                        #print "Linking CR '%s' to the PE checkpoint "   %cNo    
                        log.info("Linking CR '%s' to the PE checkpoint " %cNo)        
                    else:
                        #print "Skipping... CR %s is already is linked to a PE checkpoint" %cNo
                        log.info("Skipping... CR %s is already is linked to a PE checkpoint" %cNo)                
                
                pass    
                  
                
            pass
             
        return
    
    
    
    def loadTaskBranch(self,branch,stream):
        
        log.info('Finding TaskBranch Id for branch name %s'%branch)
        
        #where = [['Name','=',branch]
        #            ,'and',['Code_Stream__c','=',stream]]                
        #queryList = sfb.query('Task_Branch__c', where=where, sc='all')
        queryStr="Select Id,Name from Task_Branch__c where Name='%s' and Code_Stream__c ='%s'"%(branch,stream)
        queryList=self.cxn.query(queryStr)
        if queryList in BAD_INFO_LIST:
               print "WARNING:    NO Task Branch Found with name %s in stream %s" %(branch,stream)
               log.info('Skipping ...  NO Task Branch Found with name %s in stream %s' %(branch,stream))
               return queryList
            
        if len(queryList) > 1:
            log.info('WARNING: There were more than one Task Branch for %s in stream %s' %(branch,stream))
            pass
        
        brData=queryList[0]
        brId=brData.get('Id')       
    
        return brId
    
    
    def createPEBranch(self,pebr,stream,team):
        
        data={}
        teamId=self.getTeamId(team,stream)
        data['Name']=pebr
        data['Stream__c']=stream
        data['Team_Branch__c']=teamId
        data['Status__c']='Approving By PE'    
        data['CRV_Created_Date__c']=self.makeDateTime()
        #res = sfb.create('Checkpoint_Branch__c',data)
        newPEchpnt = SObjectClassFactory(self.cxn, 'Checkpoint_Branch__c')
        res = self.cxn.create(newPEchpnt, data)
        if res in BAD_INFO_LIST:
            print "Warning:    PE Checkpoint with name %s was not created" %pebr
            log.info('Warning: PE Checkpoint with name %s was not created'%pebr)
            pass
        else:
            log.info('PE checkpoint was created sucessfully with name %s'%(pebr))
            print "INFO:    PE checkpoint was created sucessfully with name %s"%(pebr)
            #print "RESULT %s" %res
            pass
        return res['id']
    
    def getTeamId(self,teamName,stream):
        
        teamName = teamName.lower()
        teamId=None
        #where = [['Name','=',teamName]
        #            ,'and',['Stream__c','=',stream]]                
        #queryList = sfb.query('Team_Branch__c', where=where, sc='all')
        
        queryStr="Select Id,Name from Team_Branch__c where Name='%s' and Stream__c ='%s'"%(teamName,stream)
        queryList=self.cxn.query(queryStr)
        
        if queryList in BAD_INFO_LIST:
            log.info('Warning Team name %s is not a valid team, please specify a correct team name and resubmit the branch' %teamName)
            sys.exit(1)
        if len(queryList) > 0:
            brData=queryList[0]
            teamId=brData.get('Id')          
            return teamId    
        
    
    def parseBranchListFile(self,path):
        """ parse a file to extract the branch names and return a list of
        the branch names """
            
        branchList = []    
        if path not in [None,''] and os.path.exists(path):
            fh = file(path)
    
            for line in fh.readlines():               
                line = line.strip()            
                splitline = line.split()
                if len(splitline) == 1:
                    # ADD lower() HERE TO MAKE CASE INSENS.                
                    branchList.append(splitline[0])
                    pass
                continue
            
            fh.close()
            pass
        
        if len(branchList) == 0:
            branchList = None
            pass    
        return branchList
    
    def makeDateTime(self):
            
        """ make into a standard Date Time string from GMT """
        value = time.time()
        value = time.gmtime(value)
        #return time.mktime(value)
        value = time.strftime("%Y%m%dT%H:%M:%S", value)
        dt = datetime.datetime.utcfromtimestamp(time.time())
        
        delinquentIsoDateTime = "%sZ" %dt.isoformat()
        return delinquentIsoDateTime
    
    #######################################################################################
    #  Commandline management methods.  Minimal logic, just command parm processing
    #######################################################################################
def mainTeamUsage():
    """ Prints the shell-script wrapped command line usage """

    m =  'TEAM PE CHECKPOINT COMMAND SUMMARY\n\n'
    m += 'Issue any of these commands with no arguments to\n'
    m += 'see help for that specific command.\n\n'
    m += 'Process Flow Commands:\n'
    m += ' * lnpechpnt -s<stream> -p <pe checkpoint> -b <branch name> -t <team name> -l <branch list>\n'
    m += '   Prints the command summary for task branch operations.\n'
    m += '\n'
    return m
    
def usage(cmd='', err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to link a CR with a Task Branch (TB) on SalesForce.\n'
    m += ' '
    m += '    teamBranch -c lntb -s4.1 -t<Team_branch> -b<branch_Name>   \n'       # addTeamBranch    
    return m

def main_CL():
    """ Command line parsing and and defaults methods    """
    version=3.0
        
    parser = OptionParser(usage=mainTeamUsage(), version='%s'%version)
    parser.add_option("-l", "--lb", dest="listBranchPath", default=None,
                      help="Path to file listing branches to allow forward."
                      "If used, branches not listed in the file will not be"
                      "moved forward. Format is one branch name per line")
    parser.add_option("-c", "--cmd",   dest="cmd",   default="add",      help="Command type to use.")    
    parser.add_option("-s", "--cs",    dest="cs",    default=DEFAULT_STREAM,        help="Code Stream of Branch")
    parser.add_option("-b", "--br",    dest="br",    default="",         help="Branch Label")
    parser.add_option("-t", "--tbr",   dest="tbr",   default="",         help="Team Branch Label")
    #parser.add_option("-n", "--team",   dest="team", default="",       help="Team Name")
    parser.add_option("-p", "--petbr",  dest="petbr", default="",    help="PE Checkpoint name")
    
    textgr = OptionGroup(parser, "Description Options","Add text description using the options below ")
    textgr.add_option("-d", "--desc",  dest="desc",  default=False, action="store_true", help="General description details")
    textgr.add_option("-m", "--mdesc", dest="mdesc", default=False, action="store_true", help="Merge description details")
    textgr.add_option("-f", "--path",  dest="path",  default="./details.txt", help="Path to details file.")
    parser.add_option_group(textgr)
    parser.add_option("-z", "--trace", dest="trace", default="soap.out", help="SOAP output trace file.")
    parser.add_option("-v", "--debug", dest='debug', action="count",     help="The debug level, use multiple to get more.")
       
    
    (options, args) = parser.parse_args()

    if options.debug > 1:
        print ' cmd  %s, pechpnt  %s' %(options.cmd, options.petbr)
        print ' stream %s, branch %s, team %s' %(options.cs, options.br, options.tbr)
        print ' path   %s, trace  %s, debug  %s' %(options.path, options.trace ,options.debug)
        print ' args:  %s' %args
    else:
        options.debug = 0

    if len(options.cmd) > 0: 
        
        obj=SfPECheckpoint()
        obj.setUp()
        #team = options.tbr
        teamBR = options.tbr
        branch = options.br
        pebr = options.petbr       
        branchlist=options.listBranchPath
        st = time.time()
        #parm = options.parm
        #query = args[1:]

        
        # check if user types -tb instead of --tb
        
        
        # parse the stream
        if options.cs in [None,'']: stream = DEFAULT_STREAM
        else: stream = options.cs
        stream = str(stream).strip()
        stream = stream.lower()


        if stream[:5] == "blast" and \
           stream not in ACTIVE_STREAMS and \
           stream[5:] in LEGACY_STREAMS:
            stream = stream[5:]
        elif stream in LEGACY_STREAMS:
            # honor legacy "number only" streams for 4 and lower.
            if stream == '5':
                stream = 'blast%s' %stream
                #print "Error: '%s' is not a valid stream." %(stream)
                #sys.exit(1)
                pass
        elif "blast%s" %stream in ACTIVE_STREAMS:
            print "Error: '%s' is not a valid stream. You must use the full name, 'blast%s'." %(stream, stream)
            sys.exit(1)
        elif stream not in ACTIVE_STREAMS and stream != '':
            print "Error: '%s' is not a valid stream." %(stream)
            sys.exit(1)
            pass

        
        if options.cmd in ['lnpechpnt']:
            if (branch in [None,''] and branchlist in [None,'']) or stream in [None,''] or pebr in [None,''] or teamBR in [None,'']: 
                print '%s' %obj.addPEBranchUsage('You must provide at least a valid stream, a PE Checkpoint, a task barnch name and a team name')
                sys.exit()
                                                   
            obj.addPEBranchCL(teamBR, branch, pebr,stream, options, st)
                            

        elif options.cmd in ['unlnpechpnt']:
            if team in [None,''] or stream in [None,'']: 
                print '%s' %obj.remTeamBranchUsage('You must provide at least a valid stream a PE Checkpoint name and a team name')
                sys.exit()
            if teamBR in [None,'']:
                teamBR = team
            obj.unlinkTeamBranchCL(teamBR, stream, branch, options, st)                            
        
        
        elif options.cmd in ['teamhelp']:
            print mainTeamUsage()
            sys.exit()
       
       
        
        print '\nTook a total of %3.2f secs -^' %(time.time()-st)
    else:
        print '%s' %usage(options.cmd)
        
        
if __name__ == "__main__":
    main_CL()