"""
entity objects to list all CRs that are lisked with a Team Branch, Task Branch
or a PE Checkpoint. Displays the result in a heirachical way
Ramya Subramani 01/09/2006
"""
import sys, time, os
import StringIO, getopt
import copy, re
import traceback
import pprint
from types import ListType, TupleType, DictType, DictionaryType
from optparse import OptionParser, OptionGroup
from SfConstant import *
from SFUtil import *
from WalkSFUtil import *
from Properties import Properties
from SfdcConnection import SfdcConnection
from SObjectClassFactory import SObjectClassFactory
from SfdcApiFault import SfdcApiFaultFactory

from SfConnection import TestCxn

from Util import booleanize, listify
import PysfdcLogger, logging
log = logging.getLogger('pysfdc.listCRs')

#import tokenFile

class ListCRs:
    
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
    
    
    def loadBranch(self, branch, stream):
        """ load the TmB object and set branch to team label """
        #print "Branch name: %s" %branch
        branch = branch
        stream = stream
        brType,Id = self.getSFData(branch, stream, show=False)
        #print "TB DATA %s" %tbData        
        return brType,Id
    
    def getSFData(self, branch, stream, show=True):
        """
        Get team branch object given a branch name and code stream
        'The Original!' [TM]
        """
        brId=None;
        queryStr1="Select Id,Name from Team_Branch__c where Name='%s' and Stream__c ='%s'"%(branch,stream)
        queryList1=self.cxn.query(queryStr1)      
        queryStr2="Select Id,Name from Task_Branch__c where Name='%s' and Code_Stream__c  ='%s'"%(branch,stream)
        queryList2=self.cxn.query(queryStr2) 
        queryStr3="Select Id,Name from Checkpoint_Branch__c where Name='%s' and Stream__c ='%s'"%(branch,stream)
        queryList3=self.cxn.query(queryStr3)          
        queryStr4="Select Id,CaseNumber from Case where CaseNumber like '%%%s%%' "%(branch)
        queryList4=self.cxn.query(queryStr4)
               
        if queryList1 not in BAD_INFO_LIST:
            log.info('Branch is a Team branch')
            for qr1 in queryList1:
                brId=qr1.get('Id')
            return 'team',brId
        elif queryList2 not in BAD_INFO_LIST:
            log.info('Branch is a Task branch')
            for qr2 in queryList2:
                brId=qr2.get('Id')
            return 'task',brId
        elif queryList3 not in BAD_INFO_LIST:
            log.info('Branch is a PE Checkpoint branch')
            for qr3 in queryList3:
                brId=qr3.get('Id')
            return 'pe',brId
        elif queryList4 not in BAD_INFO_LIST:
            log.info('File Contains a CR number')
            for qr4 in queryList4:
                brId=qr4.get('Id')
            return 'cr',brId        
        else:
            print "BRANCH NAME '%s' cannot be found in Salesforce" %branch
            return '',''       
        
     
    def listCRsUsage(self,err=''):
        """  Prints the Usage() statement for this method    """
        m = ''
        
        if len(err):
            m += '%s\n\n' %err
    
        m += 'List all the CRs that are linked to a branch (Team branch, Task Branch , PE checkpoint ).\n'
        m += '\n'
        m += 'Usage:\n'
        m += '    listcrs [OPTIONS] -s <stream> -b <branch name/CR Number> -l <file path>\n'       
        m += '\n'
        m += 'Options include:\n'
        m += '  *  -s <Stream name> Valid stream name (blast5, talus1.0)'
        m += '    \n'         
        m += '    -b < Branch Name/CR Number> CR Number or Task Branch or Team branch or PE checkpoint branch'
        m += '    \n'
        m += '  *        OR use the option below to add a list of  Branches\n'
        m += '    -l  <file path>  List of branches/CR Numbers one name per line\n'
        m += '    \n'
        m += '       Commands marked with a * are required\n'
        return m
    
    def listCRsCL(self, branch,stream, options, st, teamTool=None,
                        checkTmb=True, scmFlag=False):
        """ command line logic for listCRs
        set checkTmb to false to allow fast linking. Must run check manually
        on the team branch if used.
        """
                         
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
            
            if type(branch) is not self.seqTypes:
                if branch in [None,'']:
                    print 'Please provide a branch name to find the CR linked to it'
                    sys.exit()
                brList = [branch]
            else:
                brList = branch
            db=options.debug
        
          
            # load the PE Checkpoint branch if present other wise craete it
            brType,Id = self.loadBranch(branch, stream)
            #print "TYPE %s" %brType
            ae=options.ae
            ae=ae.lower()
            if ae in ['yes']:
                self.ListAECRS(Id,stream)
                
            else:                
                print "================================================================================"
                self.listAllBrCrs(brType,Id,stream,branch)  
                         
                             
        return
    
    def listAllBrCrs(self,brType,Id,stream,branch):
        if brType in ['team']:   
            tmStatus=self.findTeamStatus(stream,branch)
            #print "Team Branch: %s"%branch         
            print "Team Branch:%s     Status:%s"%(branch,tmStatus)
            self.findPELinks(Id,stream)
            self.findTeamTaskLinks(Id,stream)            
            #self.formatDisplay(peBrs,taskBrs)
            pass
        elif brType in ['task']:
            self.findTeamName(Id,stream)                        
            self.findPeName(Id,stream)
            #print "      Task Branch: %s" %(branch)
            tmStatus=self.findTaskStatus(stream,branch)            
            print "      Task Branch:%s     Status:%s"%(branch,tmStatus)
            self.findBRCRs(Id,stream)            
            pass
        elif brType in ['pe']:
            self.findPETaskLiks(Id,stream)
            pass
        elif brType in ['cr']:
            self.findByCRs(Id,stream)
            pass
        
        return
    
    
    def ListAECRS(self,crid,stream):
        queryStr="Select CaseNumber, Id, PE_Checkpoint__c, Status from Case where Id='%s' "%crid       
        queryStr2="Select Id,Case__c, Task_Branch__c,PE_Checkpoint__c  from Branch_CR_Link__c where Case__c='%s' "%(crid)            
        
        queryList=self.cxn.query(queryStr) 
        queryList2=self.cxn.query(queryStr2)        
        
        if queryList not in BAD_INFO_LIST:
            for qr in queryList:
                #peid=qr.get("PE_Checkpoint__c")
                #retrievedObj = self.cxn.retrieve('Checkpoint_Branch__c', peid)                                             
                status=qr.get("Status")
                cno=qr.get("CaseNumber")
                print "============================================================================="
                               
                                 
                if queryList2 not in BAD_INFO_LIST:
                    for qr2 in queryList2:                        
                        
                        tbId=qr2.get('Task_Branch__c')
                        retrievedObj1 = self.cxn.retrieve('Task_Branch__c', tbId)   
                        tbStatus=retrievedObj1.get('Branch_Status__c')            
                        tbName=retrievedObj1.get('Name')     
                        rPath=retrievedObj1.get('Patch_Release_Path__c')
                        patchVer=retrievedObj1.get('Patch_Version__c')
                        tbStream=retrievedObj1.get('Code_Stream__c')
                        if(tbStatus=='Merged'):                            
                            print "Case Number:%s   Stream:%s   RELEASE PATH:%s" %(cno,tbStream,rPath)           
                        else:                           
                            print "Case Number:%s   Stream:%s" %(cno,tbStream)           
                
        else:
            print "CR Number:%s     not found in Salesforce" %(cno)
            
            
    
    def findByCRs(self,crid,stream):
        queryStr="Select CaseNumber, Id, PE_Checkpoint__c, Status from Case where Id='%s' "%crid
        queryStr2="Select Id,Case__c, Task_Branch__c,PE_Checkpoint__c  from Branch_CR_Link__c where Case__c='%s' "%(crid)            
        
        queryList=self.cxn.query(queryStr) 
        queryList2=self.cxn.query(queryStr2)
        
        if queryList not in BAD_INFO_LIST:
            for qr in queryList:
                #peid=qr.get("PE_Checkpoint__c")
                #retrievedObj = self.cxn.retrieve('Checkpoint_Branch__c', peid)                                             
                status=qr.get("Status")
                cno=qr.get("CaseNumber")
                rdDate=self.findCRStatus(cno)
                tc=self.findTechCamp(cno)
                print "         CR Number:%s    Status:%s     R&D Submission:%s     Linked TechCamp:%s"   %(cno,status,rdDate,tc)
                #if retrievedObj not in BAD_INFO_LIST:
                #    print "   PE Checkpoint: %s          %s"%(retrievedObj.get('Name'),retrievedObj.get('Status__c'))
                #else:
                #    print "   PE Checkpoint: None"                    
                if queryList2 not in BAD_INFO_LIST:
                    for qr2 in queryList2:
                        peid=qr.get("PE_Checkpoint__c")
                        retrievedObj = self.cxn.retrieve('Checkpoint_Branch__c', peid) 
                        if retrievedObj not in BAD_INFO_LIST:
                            print "   PE Checkpoint:%s     Status:%s"%(retrievedObj.get('Name'),retrievedObj.get('Status__c'))
                        else:
                            print "   PE Checkpoint: None"  
                        
                        tbId=qr2.get('Task_Branch__c')
                        retrievedObj1 = self.cxn.retrieve('Task_Branch__c', tbId)   
                        tbStatus=retrievedObj1.get('Branch_Status__c')            
                        tbName=retrievedObj1.get('Name')     
                        rPath=retrievedObj1.get('Patch_Release_Path__c')
                        patchVer=retrievedObj1.get('Patch_Version__c')
                        tbStream=retrievedObj1.get('Code_Stream__c')
                        if(tbStatus=='Merged'):
                            print "      Task Branch:%s     Stream:%s     Status:%s     Release Path:%s" %(tbName,tbStream,tbStatus,rPath)           
                        else:
                            print "      Task Branch:%s     Stream:%s     Status:%s" %(tbName,tbStream,tbStatus)           
                
        else:
            print "CR Number:%s        not found in Salesforce" %(cno)
                    
    
    def findPELinks(self,Id,stream):
        queryStr="Select Id,Name,Status__c from Checkpoint_Branch__c where Team_Branch__c='%s' and Stream__c ='%s'"%(Id,stream)
        queryList=self.cxn.query(queryStr) 
        if queryList not in BAD_INFO_LIST:
            for qr in queryList:
                print "   PE Checkpoint:%s     Status:%s"%(qr.get('Name'),qr.get('Status__c'))
        else:
            print "   PE Checkpoint: None"
        return
    
    def findTeamTaskLinks(self,Id,stream):
        queryStr="Select Id, Name,Task_Branch__c from Branch_Team_Link__c where Team_Branch__c='%s' "%(Id)
        queryList=self.cxn.query(queryStr)        
        if queryList not in BAD_INFO_LIST:
            for qr in queryList:
                tbId=qr.get('Task_Branch__c')
                retrievedObj = self.cxn.retrieve('Task_Branch__c', tbId)   
                tbStatus=retrievedObj.get('Branch_Status__c')            
                tbName=retrievedObj.get('Name')     
                print "      Task Branch:%s     Status:%s" %(tbName,tbStatus)
                self.findBRCRs(tbId,stream)                
        else:
            print "      Task Branch: None" 
        return
    
    def findBRCRs(self,tbId,stream):
        queryStr2="Select Id,Case__c, CR_Status__c,CR_Num__c,Task_Branch__c from Branch_CR_Link__c where Task_Branch__c='%s' and Stream__c ='%s'"%(tbId,stream)                       
        crList=self.cxn.query(queryStr2)                 
        if crList not in BAD_INFO_LIST:                    
            for qr2 in crList:
                crNum=qr2.get('CR_Num__c')
                crStatus=qr2.get('CR_Status__c')
                rdDate=self.findCRStatus(crNum)
                tc=self.findTechCamp(crNum)
                print "         CR Number:%s     Status:%s     R&D Submission:%s     Linked TechCamp:%s" %(crNum,crStatus,rdDate,tc)
        else:
            print "         CR Number: None"
        return
    
    def findTeamName(self,Id,stream):
        queryStr="Select Id, Name,Task_Branch__c,Team_Branch__c,Branch_Status__c from Branch_Team_Link__c where Task_Branch__c='%s' "%(Id)                
        queryList=self.cxn.query(queryStr)           
        if queryList not in BAD_INFO_LIST:
            for qr in queryList:
                tmId=qr.get('Team_Branch__c')
                retrievedObj = self.cxn.retrieve('Team_Branch__c', tmId)                               
                tmName=retrievedObj.get('Name')    
                tmStatus=retrievedObj.get('Status__c')                
                print "Team Branch:%s     Status:%s"%(tmName,tmStatus)
        else:
            print "Team Branch: None"
        return
    
    def findPeName(self,Id,stream):
        retrievedObj = self.cxn.retrieve('Task_Branch__c', Id)                               
        peId=retrievedObj.get('PE_Checkpoint__c')  
        if peId not in BAD_INFO_LIST:
            retrievedObj1 = self.cxn.retrieve('Checkpoint_Branch__c', peId)                               
            peName=retrievedObj1.get('Name')    
            peStatus=retrievedObj1.get('Status__c')        
            print "   PE Checkpoint:%s     Status:%s"%(peName,peStatus)
        else:
            print "   PE Checkpoint: None"
        return
    
    def findPETaskLiks(self,Id,stream):
        retrievedObj = self.cxn.retrieve('Checkpoint_Branch__c', Id)   
        tmId=retrievedObj.get('Team_Branch__c') 
        if tmId not in BAD_INFO_LIST:
            retrievedObj1 = self.cxn.retrieve('Team_Branch__c', tmId)                               
            tmName=retrievedObj1.get('Name')              
            tmStatus=retrievedObj1.get('Status__c')
            print "Team Branch:%s     Status:%s"%(tmName,tmStatus)
            print "   PE Checkpoint:%s     Status:%s"%(retrievedObj.get('Name'),retrievedObj.get('Status__c'))
            queryStr="Select Id, Name, PE_Checkpoint__c,Branch_Status__c from Task_Branch__c where PE_Checkpoint__c='%s'"%(Id)
            queryList=self.cxn.query(queryStr) 
            if queryList not in BAD_INFO_LIST:
                for qr in queryList:
                    tbName=qr.get('Name')
                    tbStatus=qr.get('Branch_Status__c')
                    tbId=qr.get('Id')
                    print "      Task Branch:%s     Status:%s" %(tbName,tbStatus)
                    self.findBRCRs(tbId,stream)
            else:
                print "      Task Branch: None"
            
        else:
            print "Team Branch: None"   
         
        return
    
    def findTeamStatus(self,stream,branch):
        tmStatus=''
        queryStr="Select Id,Name, Status__c, Stream__c from Team_Branch__c where Name='%s' and Stream__c='%s' "%(branch,stream)                
        queryList=self.cxn.query(queryStr)              
        if queryList not in BAD_INFO_LIST:
            for qr in queryList:
                tmStatus=qr.get('Status__c')                           
        return tmStatus
    
    def findTaskStatus(self,stream,branch):
        tmStatus=''
        queryStr="Select Id,Branch_Status__c, Code_Stream__c, Name from Task_Branch__c where Name='%s' and Code_Stream__c='%s' "%(branch,stream)        
        queryList=self.cxn.query(queryStr)           
        if queryList not in BAD_INFO_LIST:
            for qr in queryList:
                tmStatus=qr.get('Branch_Status__c')                
                   
        return tmStatus
    
    def findCRStatus(self,crNo):        
        crStatus=''
        crNo='%'+crNo        
        queryStr="Select Id,CaseNumber, R_D_Submission__c, Status from Case where CaseNumber like '%s'"%(crNo)                
        queryList=self.cxn.query(queryStr)           
        if queryList not in BAD_INFO_LIST:
            for qr in queryList:
                crRd=qr.get('R_D_Submission__c')                      
                    
        return crRd
    
    def findTechCamp(self,crNo):
        techCamp=''
        crNo='%'+crNo
        queryStr="Select Id,CaseNumber, R_D_Submission__c, Status from Case where CaseNumber like '%s'"%(crNo)                
        queryList=self.cxn.query(queryStr)           
        if queryList not in BAD_INFO_LIST:
            for qr in queryList:
                crId=qr.get('Id')                                      
                queryStr2="Select Id,Parent_CR__c, Tech_Campaign__c from CR_Link__c where Parent_CR__c='%s'"%(crId)                              
                queryList2=self.cxn.query(queryStr2)           
                if queryList2 not in BAD_INFO_LIST:                                                            
                    for qr2 in queryList2:                                                
                        techId=qr2.get('Tech_Campaign__c')  
                        retrievedObj = self.cxn.retrieve('Tech_Campaign__c', techId) 
                        if retrievedObj not in BAD_INFO_LIST:
                            techName=retrievedObj.get('Name')
                            techCamp=techCamp+techName                   
        return techCamp
        
    
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
            
        
            

def mainTeamUsage():
    """ Prints the shell-script wrapped command line usage """

    m =  'CR LIST SUMMARY\n\n'
    m += 'Issue any of these commands with no arguments to\n'
    m += 'see help for that specific command.\n\n'
    m += 'Process Flow Commands:\n'
    m += ' * listcrs -s<stream> -n <branch name/Cr Number> -l <branch/CR list>\n'
    m += '   Prints the command summary for task branch operations.\n'
    m += '\n'
    return m
    
def usage(cmd='', err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to list CRs linked to a branch(es).\n'
    m += ' '
    m += ' listcrs -s<stream> -n <branch name/CR Number> -l <branch/CR list>   \n'       # addTeamBranch    
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
    #parser.add_option("-t", "--tbr",   dest="tbr",   default="",         help="Team Branch Label")
    #parser.add_option("-n", "--team",   dest="team", default="",       help="Team Name")
    #parser.add_option("-p", "--petbr",  dest="petbr", default="",    help="PE Checkpoint name")
    parser.add_option("-a", "--ae",  dest="ae", default="no",    help="AE Report")
    
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
        
        obj=ListCRs()
        obj.setUp()
        branch = options.br      
        branchlist=options.listBranchPath
        st = time.time()
               
        
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

        
        if options.cmd in ['listcrs']:
            if (branch in [None,''] and branchlist in [None,'']) or stream in [None,'']: 
                print '%s' %obj.listCRsUsage('You must provide at least a valid stream, a branch name or a list of branches')
                sys.exit()                                                   
            obj.listCRsCL(branch,stream, options, st)                        
        
        
        elif options.cmd in ['teamhelp']:
            print mainTeamUsage()
            sys.exit()
       
       
        
        print '\nTook a total of %3.2f secs -^' %(time.time()-st)
    else:
        print '%s' %usage(options.cmd)
        
        
        
if __name__ == "__main__":
    main_CL()