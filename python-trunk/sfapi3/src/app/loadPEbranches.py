#=========================================================================
#
# Python Source File -- Created with SAPIEN Technologies PrimalScript 3.1
#
# NAME: Create pe_checkpoint load file
#
# AUTHOR: Chip Vanek , Upvia
# DATE  : 10/4/2006
#
# COMMENT: Usees the directory structure create by Alexa
#  ~/done/<PE_Masking_task_Branch_Name> (contains list of actual task branch names)
#  ~/cr_maps/<task_branch_name> (contains list of CRs linked to task branch)
#
#
#=========================================================================
import os, re, sys, string, time, stat
import glob, pprint
import getopt, copy
from optparse import OptionParser, OptionGroup
from SFUtil import *
from Properties import Properties
from SfdcConnection import SfdcConnection
from SObjectClassFactory import SObjectClassFactory
from SfdcApiFault import SfdcApiFaultFactory

from SfConnection import TestCxn

from Util import booleanize, listify
from WalkSFUtil import *

class FileNode:
    """   get information from the file
    """
    meta_type = 'FileNode'
    filelines = []
    filedata = []
    filename = ''
    branchRE   = re.compile("\.(?P<brString>[a-zA-Z0-9_\.]+)-?")
    
    
    def __init__(self, name, path='.', data=None, crListPath=None, tool=None):
        """ pass filename as a minimum """
        self.name = name   # should be name of file at a min
        if path in ['.',None]:
            path = os.getcwd()
        if crListPath in [None,'']:
            crListPath = '../cr_maps/'
        self.crListPath = crListPath 
        self.path = path
        self.data = data
        if tool in [None]:
            tool = BranchNode()
            tool.setUp()
        self.tool = tool
        
    def log(self, msg):
        print msg   
        
    def load(self, p=None):
        """ For default directory implementation load directory list into data
        """
        if p is None: p = self.path
        self.data = []
        if os.path.isdir(p): 
            self.log('Load called with a directory: %s'%p)
            self.data = os.listdir(p)
            msg = 'Loaded %s filenames from %s mdate:%s' %(len(self.data),npath, self.mdate)
            #self.log(msg)
            return self.data
        f_stat = os.stat(p)
        self.adate = f_stat[7]
        self.mdate = f_stat[8]
        self.cdate = f_stat[9]
        self.name = os.path.basename(p)
        fp = open(p)
        self.data = fp.readlines()
        fp.close()
        msg = 'Loaded %s from %s mdate:%s' %(self.name, p, self.data)
        #self.log(msg)
        
    def getBRInfo(self, version=None):
        """ parse filename and get a list of CRs 
        """
        fileName = self.name
        self.branch = self.name
        self.version = self.name.split('_')[0]
        if self.version in [None,'',self.branch]: self.version = 'Talus1.0'
        pebr = self.tool.loadBranch(self.branch,self.version,type='pe')
        pebrId = self.tool.id
        #self.log('Result of loadBranchPE:%s'%pebr)
        tsbr = self.tool.loadBranch(self.branch,self.version,type='br')
        tsbrId = self.tool.id
        tmId = self.tool.getTeamBranchLink(tsbrId)
        #self.log('Result of loadBranchTask:%s'%tsbr)
        if len(pebr) == 0:
            self.log('WARN: No PE checkpoint found for %s '%(self.name))
            info = {'Name':self.branch, 'Stream__c':self.version}
            if len(tsbr) ==0:
                self.log('ERROR: No Task Branch found for %s '%(self.name))
                peStatus = 'Approving by PE'
            else:
                peStatus = tsbr.get('Status__c','Not found')
                info['Task_Branch__c'] = tsbrId
                info['Team_Branch__c'] = tmId
            info['Status__c'] = peStatus
            self.log('Creating a PE with info of:'%info)
            pebrId = self.tool.createPEBR(self.branch,info)
            petmId = tmId
        else:
            peStatus = pebr.get('Status__c')
            petmId = pebr.get('Team_Branch__c')
            self.log('Found PE CKHPONT:%s  %s %s tmId:%s'%(pebrId,pebr.get('Name'),peStatus,petmId))
            
        if len(tsbr) != 0:
            status = tsbr.get('Branch_Status__c')
            #self.log('Found TaskBranch:%s  %s %s'%(tsbrId,tsbr.get('Name'),status))
            if tsbr.get('PE_Checkpoint__c','') == pebrId:
                self.log('OK:   TaskBranch:%s  %s %s Linked TO PE CKHPONT:%s tmId:%s'%(tsbrId,tsbr.get('Name'),status,pebrId,tmId))
            else:
                self.log('FIXING: TaskBranch:%s Linking TO PE Checkpoint: %s  %s'%(tsbrId,pebrId,status))
                #self.log('TASK%s'%tsbr)
                #self.log('PE%s'%pebr)
                # link Task Branch to PE branch
                data = {'Id':tsbrId, 'PE_Checkpoint__c':pebrId }
                tsId = self.tool.setSFData('Task_Branch__c', data)
                # Update PE branch to link to Team Branch
                # update PE status with mask PE (TB)status
                data = {'Id':pebrId, 'Status__c':status,'Team_Branch__c':tmId }
                tsId = self.tool.setSFData('Checkpoint_Branch__c', data)
                
            
        self.log('---------------------------------')
        self.crList = []
        runCheck = False
        crPath = os.path.join(self.path,self.crListPath)
        for line in self.data:
            tbranch = line.split('\n')[0]
            version = tbranch.split('_')[0]
            crMapFile = os.path.normpath(os.path.join(crPath,tbranch))
            self.crList = []
            if os.path.isdir(crMapFile): 
                self.log('WARN: crMapFile file NOT found path:%s using: %s'%(crMapFile,crPath))
            elif os.path.isfile(crMapFile):
                fp = open(crMapFile)
                crList = fp.readlines()
                fp.close()
                for cr in crList:
                    self.crList.append(cr.split('\n')[0])
                #self.log('FOUND CRs: %s'%(self.crList))
            else:
                pass
                #self.log('NO CRs for tb:%s pe:%s '%(tbranch,self.name))
            brInfo = self.tool.loadBranch(tbranch,version,type='br')
            if len(brInfo) == 0:
                self.log('ERROR: No Task Branch found for %s got:%s'%(tbranch,brInfo))
            else:
                brId = brInfo.get('Id')
                status = brInfo.get('Branch_Status__c')
                if peStatus != status: 
                    runCheck = True
                    self.log('  Statuses are different PE:%s  TB:%s'%(peStatus,status))
                #self.log('Found TaskBranch:%s %s'%(brId,brInfo.get('Name')))
                # now check if this task branch is linked to main PE Checkpoint
                if brInfo.get('PE_Checkpoint__c','') == pebrId:
                    self.log('OK:   TaskBranch:%s  %s %s Checkpoint: %s'%(brId,status,brInfo.get('Name'), pebrId))
                else:
                    # link Task Branch to PE branch
                    data = {'Id':brId, 'PE_Checkpoint__c':pebrId }
                    self.log('FIXING: Linking Task Branch to PE Checkpoint :%s TO %s'%(brId,pebrId))
                    #self.log('TASK%s'%brInfo)
                    #self.log('PE%s'%pebr)
                    tsId = self.tool.setSFData('Task_Branch__c', data)
                # now create BRCR Links for CR is file list
                self.tool.setBRCRs(brId,self.crList)
        self.log('_______________end of %s _______________________'%(self.branch))
        if runCheck:
            walkUtil = WalkSFUtil()  
            walkUtil.checkPEBranch(self.branch,self.version)
            self.log('_______________Checked %s _______________________'%(self.branch))
        

            
            


class BranchNode:
    """ manage the Branch information in Salesforce 
    """
    modList = []
    loadFromSF = False
    branchType = 'pe'
    seqTypes = [ListType, TupleType]

    #######################################################################
    # Branch data management methods
    #######################################################################
    def setUp(self):
        self.cxn = TestCxn().cxn
        self.idList = []
        return

    def log(self, msg):
        print msg   
        
    def loadBranch(self, branch, stream, type='pe'):
        """ load the branch object and set branch and stream """
        self.branch = branch
        self.stream = stream
        self.id = None
        self.data = self.getSFData(branch, stream, type=type, show=False)
        if self.data in [None,'',{},[]]:
            self.data = {}
        else:
            self.data = self.data[0]
            self.id = self.data.get('Id')
        #self.log('Query returns:%s '%(self.data))
        return self.data
    
    def getSFData(self, branch, stream, type='br', show=True):
        """ Get branch object given a branch name and code stream and type
        """
        if type in ['br']:
            fields = 'Id,Name,Branch_Status__c,PE_Checkpoint__c'
            queryStr="Select %s from Task_Branch__c where Name='%s' and Code_Stream__c ='%s'"%(fields,branch,stream)
            errStr = 'No Task Branch found: %s'%branch
        elif type in ['pe']:
            fields = 'Id,Name,Status__c,Team_Branch__c'
            queryStr="Select %s from Checkpoint_Branch__c where Name='%s' and Stream__c ='%s'"%(fields,branch,stream)
            errStr = 'No PE CHpnt Branch found: %s'%branch
        elif type in ['tb']:
            fields = 'Id,Name,Status__c'
            queryStr="Select %s from Team_Branch__c where Name='%s' and Stream__c ='%s'"%(fields,branch,stream)
            errStr = 'No Team Branch found: %s'%branch
        else:
            return {}
            
        result=self.cxn.query(queryStr)
        if result in BAD_INFO_LIST:
            self.log(errStr)
            return []
        elif len(result) > 1:
            msg ='WARNING: There should be only ONE branch for %s' %pprint.pformat(queryStr)   
            self.log(msg)
            result
        return result

    def setSFData(self, entity, data):
        """ Set some data in Salesforce with basic validation  """
        id = data.get('Id')
        if id:  
            obj = self.cxn.retrieve(entity, id)
            for k,v in data.items():
                obj[k] = v
            saveResult = obj.update()    
        else:   
            newObj = SObjectClassFactory(self.cxn, entity)
            saveResult = self.cxn.create(newObj, data)
        if saveResult in BAD_INFO_LIST:
            log.info('ERROR: could not set %s with %s got: %s'%(entity,data,saveResult))
        else:
            log.info('Set %s with %s got: %s'%(entity,data,saveResult))
        return saveResult.get('Id','')
    
    def setBRCRs(self,brId,crList=[]):
        """ Check or set the linkage of CRs to BRs"""
        BRCRInfoMaster = {}
        fields ="Id,Case__c, Component__c, Component_Link__c, CR_Num__c, CR_Status__c, CR_Subject__c, PE_Checkpoint__c, Task_Branch__c" 
        sql = "Select %s from Branch_CR_Link__c where Task_Branch__c = '%s'" %(fields,brId)
        BRCRList=self.cxn.query(sql)
        if BRCRList in BAD_INFO_LIST:
            pass
            #self.log("NO BRCRs found on %s"%brId)
        else:
            #self.log('CHECKING: %s'%BRCRList)
            for BRCRInfo in BRCRList:
                brcrId = BRCRInfo.get('Id')
                BRCRInfoMaster[brcrId] = BRCRInfo
            
        for crNum in crList:
            pad = '00000000'+crNum
            crNum = pad[len(crNum):]
            fields = "CaseNumber, Component__c, Id, Status, Subject"
            where = "where CaseNumber = '%s'"%crNum
            sql ="Select %s from Case %s"%(fields,where)
            CRList=self.cxn.query(sql)
            if CRList in BAD_INFO_LIST:
                self.log('NO CASE found using %s'%sql)
            else:
                CRInfo = CRList[0]
                crId = CRInfo.get('Id')
                foundBRCRId = ''
                for brcrId, BRCRInfo in BRCRInfoMaster.items():
                    if BRCRInfo.get('Case__c') == crId:
                        foundBRCRId = brcrId
                if foundBRCRId in [None,'']:
                    self.log('Could not find a linkage from %s to %s'%(crNum,brId))
                    brcrId = self.createBRCR(brId,CRInfo)
                else:
                    del BRCRInfoMaster[brcrId]
                    self.log('Found a linkage from %s to %s'%(crNum,brId))
        if len(BRCRInfoMaster) > 0:
            self.log('INFO: BRCRs onTB:%s %s'%(brId,BRCRInfoMaster.keys()))
            
                    
    def createBRCR(self,brId,CRInfo):
        """ create a new Branch CR Link """
        data={}
        data['Component__c']= CRInfo.get('Component__c','')
        data['CR_Subject__c']= CRInfo.get('Subject','')
        data['CR_Status__c']= CRInfo.get('Status','')
        data['Task_Branch__c']= brId
        newBRCR = SObjectClassFactory(self.cxn, 'Branch_CR_Link__c')
        self.log('Ready to create BRCRList with %s'%data)
        res = self.cxn.create(newBRCR, data)
        if res in BAD_INFO_LIST:
            self.log('Warning: BRCRLink with for %s with %s was not created'%(brId,CRInfo))
        else:
            self.log('NEW BRCRLink created for %s with %s'%(brId,data))
        return res.get('id','')
     
    def getTeamBranchLink(self, tbid):
        """ Get team branch using Team Branch Link
        """
        if tbid in [None,'']: return {}
        fields = 'Id,Branch_Status__c, Task_Branch__c, Team_Branch__c'
        queryStr="Select %s from Branch_Team_Link__c where Task_Branch__c ='%s'"%(fields,tbid)
        result=self.cxn.query(queryStr)
        if result in BAD_INFO_LIST:
            self.log('Team branch not found with %s'%queryStr)
            return ''
        return result[0].get('Team_Branch__c','')

    def createPEBR(self,br,Info):
        """ create a new PE Branch  Name, Need_Check__c, Status__c, Stream__c, Team_Branch__c
        """
        data={}
        data['Name']= Info.get('Name',br)
        data['Status__c']= Info.get('Status','')
        data['Stream__c']= Info.get('Stream__c','')
        data['Need_Check__c']= 'true'
        data['Team_Branch__c'] = self.getTeamBranchLink(Info.get('Task_Branch__c',''))
        newBR = SObjectClassFactory(self.cxn, 'Checkpoint_Branch__c')
        res = self.cxn.create(newBR, data)
        if res in BAD_INFO_LIST:
            self.log('Warning: PEBR with for %s with %s was not created res:%s '%(br,data,res))
        else:
            self.log('NEW PEBR created for %s with %s res:%s'%(br,data,res))
        return res.get('id','')

    
    
            
def parseDone(options):
    """ run inside the done dir """    
    path =  options.path   
    if path in ['.',None,'']:
        path = os.getcwd()
    print 'Working in %s'%path
    os.chdir(path)
    fileList = glob.glob('*')
    #print 'Found files ',fileList
    bo = BranchNode()
    bo.setUp()
    n = FileNode(path,tool=bo)
    num = 0
    for fn in fileList:
       n.load(fn)
       pe = n.name
       n.log('\n looking at %s as %s'%(fn,pe))
       n.getBRInfo()
       num = num +1
       if num > 200: break
       n.log('>>>>>>>> %s <<<<<<<<<<<'%num)

def usage(err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to seach the Scan the currect directory for PE checkpoints.\n'
    m += '   It will look for linked CRs in a peer directory'
    m += '  create_pe_load  \n'
    return m


def main_CL():
    """ Command line parsing and and defaults method for walk
    """
    parser = OptionParser(usage=usage(), version='0.5')
    parser.add_option("-p", "--path",  dest="path", default="",      help="path in the directory.")
    parser.add_option("-s", "--cs",    dest="code", default="blast5", help="The Code version <4|4.0|4.1|4.2|all> to use.")
    parser.add_option("-x", "--parm",  dest="parm", default="",     help="Parms used by a method")
    parser.add_option("-l", "--list",  dest="list", default="junk", help="List the branch status in the tree")
    parser.add_option("-q", "--quiet", dest='quiet',default="1",    help="Show less info in output")
    parser.add_option("-d", "--debug", dest='debug',action="count", help="The debug level, use multiple to get more.")
    (options, args) = parser.parse_args()
    options.debug = 0
    if options.debug > 1:
        print ' verbose %s\tdebug %s' %(options.quiet, options.debug)
        print ' path    %s' %options.path
        print ' version  %s' %options.code
        print ' list    %s' %options.list
        print ' args:   %s' %args
    version = str(options.code)
    
    if args not in ['',None]:
        parseDone(options)
    else:
        print '%s' %usage()

if __name__ == '__main__':
    """ go juice """
    main_CL()       