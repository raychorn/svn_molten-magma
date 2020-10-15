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

from Util import booleanize, listify
import PysfdcLogger, logging
log = logging.getLogger('pysfdc.SFUtil')

#import tokenFile

class SFUtil:
    
    modList = []
    loadFromSF = False    
    seqTypes = [ListType, TupleType]

    #######################################################################
    # Team Branch data management methods
    #######################################################################
    cxn = TestCxn().cxn
    #idList = []        
    
    
    def loadPEBranchByName(self, pebranch, stream):
        """ load the TmB object and set branch to team label """
        #print "Branch name: %s" %branch
        branch = pebranch
        stream = stream
        queryStr="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Branch__c='%s' and Stream__c ='%s'"%(branch,stream)
        peData = self.getSFData(queryStr, show=False)
        #print "TB DATA %s" %tbData        
        
        return peData
    
    def loadPEBranchById(self,peId,stream):
        queryStr="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Checkpoint_Branch__c='%s' and Stream__c ='%s'"%(peId,stream)
        
        data = self.getSFData(queryStr, show=False)
        return data
        
        
    def loadTaskBranchById(self,tbId,stream):
        queryStr="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Task_Branch__c='%s' and Stream__c ='%s'"%(tbId,stream)
        data = self.getSFData(queryStr, show=False)
        return data
    
    def loadTaskBranchByName(self,tbName,stream):
        queryStr="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Branch__c='%s' and Stream__c ='%s'"%(tbName,stream)
        data = self.getSFData(queryStr, show=False)
        return data
    
    def loadTeamBranchById(self,teamId,stream):
        queryStr="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Team_Branch__c='%s' and Stream__c ='%s'"%(teamId,stream)
        data = self.getSFData(queryStr, show=False)
        return data
    
    def loadTeamBranchByName(self,teamName,stream):
        queryStr="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Id, Name, OwnerId, Status__c, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where Branch__c='%s' and Stream__c ='%s'"%(teamName,stream)
        data = self.getSFData(queryStr, show=False)
        return data
    
    def getSFData(self, queryStr, show=True):
        """
        Get team branch object given a branch name and code stream
        'The Original!' [TM]
        """
        #where = [['Name','like',branch]
         #       ,'and',['Stream__c','=',stream]]
        #queryList = self.sfb.query('Checkpoint_Branch__c', where=where, sc='all')
        
        #queryStr="Select Id,Name from Checkpoint_Branch__c where Name='%s' and Stream__c ='%s'"%(branch,stream)
        #print queryStr
        queryList=self.cxn.query(queryStr)
               
               
        if queryList in BAD_INFO_LIST:
            log.info('NO Task Existing Branch found')
            return queryList
                        
        if len(queryList) > 1:
            log.info("WARNING:getSFData() Found more than one branch")
                    
        brData=queryList[0]
        
        branch = brData.get('Branch__c')
        stream = brData.get('Stream__c')
        status = brData.get('Status__c')
        self.status = status
        self.branch = branch
        self.stream = stream
        info = [status,branch,stream]
        return info                     
                  
       
     
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
    
    #######################################################################################
    #  Commandline management methods.  Minimal logic, just command parm processing
    #######################################################################################
    
    def loadBranchById(self, id):
        """
        load elements from existing Task Branch Object
        given a task branch Id
        """
        where = [['Id','=', id]]
        tbData = self.getSFDataCommon(where, show=False)        
        # tbData = self.getSFDataById(id, show=False)
        taskBr = tbData.get('Task_Branch__c')
        branch = taskBr.get('Branch__c','')
        stream = taskBr.get('Code_Stream__c','')
        status = taskBr.get('Branch_Status__c','')
        numCLs = len(tbData.get('Branch_CR_Link__c'))
        numBAs = len(tbData.get('Branch_Approval__c'))
        numBTLs = len(tbData.get('Branch_Team_Link__c',[]))

        self.branch = branch
        self.stream = stream
        info = [numCLs,numBAs,status,branch,stream,numBTLs]
        return info    
         
