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
from SFUtil import *
from WalkSFUtil import *
from Properties import Properties
from SfdcConnection import SfdcConnection
from SObjectClassFactory import SObjectClassFactory
from SfdcApiFault import SfdcApiFaultFactory

from SfConnection import TestCxn

from Util import booleanize, listify
import PysfdcLogger, logging
log = logging.getLogger('pysfdc.walkPE')

#import tokenFile

class WalkPE:
    
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
            msg ='WARNING: There should be only ONE PE barnch for %s' %pprint.pformat(where)   
            print msg
            log.info(msg)
        return queryList
     
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
    
    def checkPE(self,branch, stream):
        log.info("Calling checkpe command for PE cehckpoint name %s" %branch)
        walkUtil = WalkSFUtil()  
        walkUtil.checkPEBranch(branch,stream)
        return
    
    def syncPEBranches(self):        
        queryStr="Select Id, Name, Need_Check__c, Status__c, Stream__c,Team_Branch__c from Checkpoint_Branch__c where Need_Check__c=True"
        queryList=self.cxn.query(queryStr)
        
        if queryList in BAD_INFO_LIST:
            log.info('No PE checkpoints to be checked')
            sys.exit(1)
        else:
            for qr in queryList:
                pename=qr.get('Name')
                stream=qr.get('Stream__c')
                peId=qr.get('Id')                
                msg="Checking PE branch %s in code stream %s "%(pename,stream)                
                log.info(msg)                
                self.checkPE(pename,stream)
                retrievedObj = self.cxn.retrieve('Checkpoint_Branch__c', peId)        
                retrievedObj['Need_Check__c'] = False                  
                saveResult = retrievedObj.update() 
        return        
     
      
    def walkSFQueryCL(self,role, options, st=0):
        """
        Wrapper to check for both approvals and rejections on a role's BAs.
        """
        logname = 'walk%s'%role
        
        if role in ['pe']:
            doneApp = self.walkSFQueryFlow(role, options, st, act='Approve')
            doneRej = self.walkSFQueryFlow(role, options, st, act='Reject')
            done = doneApp + doneRej
            pass    
        else:
            print 'Unknown role of %s'%role
            sys.exit(0)
    
        sys.exit(done)
    
    def walkSFQueryFlow(self, role, options, st=0, act='Approve'):
        """ new main poll method using targeted queries 
            This queries Branch approvals for 'approve'
        """
        if act not in ['Approve','approve','reject','Reject']:
            act = 'approve'
        action = {'action':'approved','isTeam':False}
        if act in ['Reject','reject']:
            action = {'action':'rejected','isTeam':False}
    
        where  = "OwnerId !='' "
        where += "and Status__c = 'Approving' "
        where += "and Approve__c ='%s'"%act
        where += "and Checkpoint_Branch__c !=''"
            
        if role in ['pe']:
            where += " and Approval_Role__c ='Product Engineer'"
            action['role'] = 'pe'
        
        #logname = 'walk%s'%role
        #sfb = SFTaskBranchWalkTool(debug=options.debug,logname=logname)
        peUtil = SFUtil()
        collect, empty = self.getTBAWith(where)
        
        # collect = {tbId:[list of BAs]}
        total = len(collect)
        msg= '%s FOUND %s BAs items with %s for role %s ' \
              %(time.ctime(),total, act, role)
        print msg
        log.info(msg)
        # actionNeeded = {tbId:action}
        #action = {'Id':baId, 'role':role, 'branch':branch
        #         ,'stream':cs, 'action',"approved|rejected", isTeam:True|False}
        #actionNeeded = {tbId:action}
        actionNeeded = {}
        done = 0
        
        #tbObj = SFUtil(debug=options.debug)
        for tbId, baList in collect.items():
            if tbId in [None,'']:
                #print 'walkSFQueryFlow: Could not find ID for TaskBranch %s'%baList
                continue
            
            brObject=(collect.get(tbId))
            brObj=brObject[0]
            #print "BRANCH OBJECT is  .................%s" %brObj
            # now can load the (Task|Team)Branch and approve away  
            #print "ID ............... %s"%tbId
            baId=brObj.get('Id')
            stream=brObj.get('Stream__c')
            tmId=brObj.get('Team_Branch__c')
            tbrId=brObj.get('Task_Branch__c')
            peId=brObj.get('Checkpoint_Branch__c')
            
            #print "VALUES  %s... %s... %s ..."%(tmId,tbrId,peId)
            #print "BRANCH TYPE..................%s" %branchType
              
            """if tmId not in [None,'']:
                print "TEAM QUERY"
                tokens = peUtil.loadTeamBranchById(tbId,stream)"""
            if peId not in [None,'']:                
                tokens=peUtil.loadPEBranchById(tbId,stream)
            else:                                          
                tokens = peUtil.loadTaskBranchById(tbId,stream)
                pass
            # tokens = [numCLs,numBAs,status,branch,stream]
            status = tokens[0]
            branch = tokens[1]
            stream = tokens[2]
            print 'Actioning %s for %s %s'%(status,branch,stream)
            action['branch'] = branch
            action['stream'] = stream
            action['Id']=baId
            actionNeeded = {tbId: action}
            #print "Collect %s and Action Needed data %s" %(collect, actionNeeded)
            actioned = self.actionBApprovals(collect, actionNeeded, st)
            if len(actioned) == 0:
                print 'Failed Action %s %s for %s %s'%(status,act,branch,stream)
            else:
                print 'Actioned %s %s for %s %s\n'%(status,act,branch,stream)
                done += 1
                pass
        
        #print 'Actioned %s TaskBranches'%(done)
        #print actionNeeded
        return done
    
    def getTBAWith(self, where=None, show=False):
            """ get the Branch Approvals using passed where clause"""
            collect = {}
            actionNeeded = {}    # key as tbId value of action required
            stream=None
            branchType=None
            if where is None:
                uid = '00530000000cCy5'  #Chip Vanek
                where = "OwnerId = '%s'"%uid
            #print "Query %s" %where
            querystr="Select Approval_Role__c, Approve__c, Branch__c, Checkpoint_Branch__c, Component__c, Id, Name, OwnerId, Stream__c, Task_Branch__c, Team_Branch__c from Branch_Approval__c where %s" %where
            #print "............."
            #print querystr
            queryList=self.cxn.query(querystr)
        
            if queryList in BAD_INFO_LIST:
                #if self.debug>1:print 'getTBAWith Result: NO Branch Approvals Found using %s'%where
                return collect, actionNeeded
            for info in queryList:
                stream=info.get('Stream__c')
                tbId=info.get('Checkpoint_Branch__c')
                branchType="peChpnt"
                if tbId in [None,'']:
                    tbId = info.get('Team_Branch__c','')
                    branchType="team"
                    if tbId in [None,'']:
                        branchType="task"
                        tbId = info.get('Task_Branch__c','')
                bal = collect.get(tbId,[])
                bal.append(info)
                collect[tbId] = bal
                
            #print (role,stream)
            #data={}
            #data['brType']=branchType
            #data['stream']=stream
           
            #print "--------------------Collect %s and Action %s" %(collect,actionNeeded)
            return collect, actionNeeded
    
    def actionBApprovals(self, collect, actionNeeded, st=0):
            """ main entry method for walkSF cron approvals """
            if st == 0: st= time.time()
            result = {}
            walkUtil = WalkSFUtil()        
            for tbId, action in actionNeeded.items():
                                
                baId = action.get('Id')
                #braId=action.get('baId')
                role = action.get('role')
                branch = action.get('branch')
                stream = action.get('stream')
                approv = action.get('action')
                isTeam = action.get('isTeam', False)
                # action = {'Id':baId, 'role':role, 'branch':branch, 'stream':cs, 'action',"approved|rejected", isTeam:True|False}
                #msg = 'ACTIONING: %s %s for %s in %s tbId:%s based on BA: %s'%(role,approv,branch,stream, tbId, baId)
                msg = 'ACTIONING: %s %s for %s in %s tbId:%s  based on BA: %s'%(role,approv,branch,stream, tbId,baId)
                #msg = '%.4s %s'%((time.time()-st),msg)
                print msg
                #self.setLog(msg,'info')                
                if role == 'pe':
                    if approv == 'rejected':
                        walkUtil.rejectToDevByPe(tbId, stream, st)
                        pass
                    else:
                         walkUtil.submitByPe(tbId, stream, st)
                                                
                
                else:
                    print 'Role value error >%s< is not recognized'%role
                    log.info('Role value error >%s< is not recognized'%role)
            
            for branch, info in result.items():
                msg = '%32s IN %s was %s by %s and sent %s msgs'\
                  %(branch, info.get('stream'),info.get('approve'),info.get('role'),info.get('num'))
                print msg
                log.info(msg)
            if len(result) >0:
                #print 'ACTIONED %s branches'%len(result)
                pass
            
            return result
            
        
            

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
    m += '  Default usage is to reevaluate the PE checkpoint barnch.\n'
    m += ' '
    m += '    checkpe -s<stream name> -p<PE Checkpoint branch_Name>   \n'       # addTeamBranch    
    return m

def main_CL():
    """ Command line parsing and and defaults methods    """
    version=3.0
        
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-c", "--cmd",   dest="cmd",   default="walk",     help="Command type to use.")
    #parser.add_option("-p", "--parm",  dest="parm",  default="",         help="Command parms.")
    parser.add_option("-x", "--parm2", dest="parm2", default="",         help="Command parms 2.")
    parser.add_option("-s", "--cs",    dest="cs",    default="",        help="Code Stream of Branch")
    parser.add_option("-p", "--br",    dest="br",    default="",         help="Branch Label")
    parser.add_option("-f", "--path",  dest="path",  default="./details.txt", help="Path to details file.")
    parser.add_option("-z", "--trace", dest="trace", default="soap.out", help="SOAP output trace file.")
    parser.add_option("-d", "--debug", dest='debug', action="count",     help="The debug level, use multiple to get more.")
    parser.add_option("-i", "--cycle", dest='cycle', default="",     help="Cycle counter flag (optional). Set to True or False")

    (options, args) = parser.parse_args()
#    print options
#    print args

    if options.debug > 1:
        print ' cmd  %s, parms  %s, stream %s' %(options.cmd,  options.cs)
        print ' path   %s, trace  %s, debug  %s' %(options.path,options.trace ,options.debug)
        print ' args:  %s' %args
    else:
        options.debug = 0

    if len(options.cmd) > 0: 
        obj=WalkPE()
        obj.setUp()
        db = options.debug
        st = time.time()
        #parm = options.parm
        query = args[1:]
        if options.cs in [None,'']: stream = None
        else: stream = options.cs

        
        if options.cmd in ['walkact','walkactions']:
            act = 'approve'
            if options.br in ['Reject','reject']:
                act = 'reject'
            role = 'pe'
            if options.parm2 in ['part','mgr','pe','team','ae','scm','autoae']:
                role = options.parm2
                
            obj.walkSFQueryCL(role, options, st)
            
        if options.cmd in ['checkpe']:            
            if options.br in [None,''] and options.cs in [None,''] : 
                print '\tYou must provide a least a branch label and a stream!'
                print '%s' %usage(options.cmd)
                sys.exit()
            branch = options.br
            stream = options.cs
            if stream not in ACTIVE_STREAMS:
                print " %s is not a valid stream, please try again using a valid code stream" %stream
                print '%s' %usage(options.cmd)
                sys.exit()
            obj.checkPE(branch, stream)
            
        if options.cmd in ['syncpe']:             
            obj.syncPEBranches()
  
       
        
        print '\nTook a total of %3.2f secs -^' %(time.time()-st)
    else:
        print '%s' %usage(options.cmd)
        
        
if __name__ == "__main__":
    main_CL()