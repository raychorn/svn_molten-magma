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
from sfMagma import *
from sfTaskBranch import *   # get SFTaskBranch & SFTaskBranchTool
#from sfTaskBranchStatusMap import *
from sfConstant import *
from walkSFEntity import SFTaskBranchWalk
from sfUtil import *
from sop import sfEntities, SFEntitiesMixin, SFUtilityMixin, SFTestMixin
import tokenFile
##################################################################################################
version = 2.0  # version number shown to users at command line
##################################################################################################

class SFPEBranch(SFTaskBranchWalk):
    """ This is a composite object that represents a TeamBranch sForce object
        and related Branch Approval & Branch CR objects as one entity
    """
    modList = []
    loadFromSF = False
    branchType = 'pe_checkpoint'

    #######################################################################
    # Team Branch data management methods
    #######################################################################
    def loadBranch(self, branch, stream):
        return self.loadPEBranch(branch, stream)
    
    def loadPEBranch(self, branch, stream):
        """ load the TmB object and set branch to team label """
        #print "Branch name: %s" %branch
        self.branch = branch
        self.stream = stream
        tbData = self.getSFData( branch, stream, show=False)
        #print "TB DATA %s" %tbData
        status = tbData.get('Checkpoint_Branch__c').get('Status','')
        numTBs = len(tbData.get('Task_Branch__c'))
        numBAs = len(tbData.get('Branch_Approval__c'))
        info = [numTBs,numBAs,status,branch,stream]
        if self.debug > 1: print "PEBranch Data: %s" %tbData        
        return info
        
    def getSFData(self, branch, stream, show=True):
        """
        Get PE Checkpoint branch object given a branch name and code stream
        Select c.Id, c.Name, c.Status__c, c.Stream__c, c.Team_Branch__c from Checkpoint_Branch__c c
        """
        where = [['Name','like',branch]
                ,'and',['Stream__c','=',stream]]
        res = self.getSFDataCommon(where, show=show)
        return res

    def getSFDataCommon(self, where, show=True):
        """
        Common code to support the getSFData methods.
        one call to get all new PE branch object related to a
        ClearCase branch will set data as a list of entity-data pairs
        [('entity', {data})] return this data structure or {}
        """
        res = {'Checkpoint_Branch__c':{},
               'Case':[],
               'Branch_Approval__c':[],
               'Task_Branch__c':[]}
        self.setData(res, reset=True)        

        queryList = self.sfb.query('Checkpoint_Branch__c', where=where, sc='all')
        if queryList in self.badInfoList:
            if self.debug > 0:
                print '   NO Task Existing PE checkpoint found for %s'%pprint.pformat(where)
            return queryList
        if len(queryList) > 1:
            print 'WARNING: There should be only ONE PE branch for %s'%pprint.pformat(where)       
        
        numBR = 0
        numBA = 0
        peData= queryList[0]
        if self.debug > 0:print '  PE Checkpoint Branch Data has %s '%pprint.pformat(peData)
        if type(peData) not in dictTypes:
            return 'Error: getSFTeamData for %s Query returned %s'%(pprint.pformat(where), peData)
        
        pebId = peData.get('Id','')
        res['Checkpoint_Branch__c'] = peData

        if pebId not in [None,'']:
            branch = peData.get('Name','')

            where = [['PE_Checkpoint__c','=',pebId]]
            tbList = self.sfb.query('Task_Branch__c', where=where)
            if tbList in self.badInfoList:
                if self.debug > 0:  
                    print '  NO TaskBranch  found with %s'%where
                    print '  Found: %s'%pprint.pformat(tbList)
            res['Task_Branch__c'] = tbList
            numBR = len(tbList)
            
            where = [['Checkpoint_Branch__c','=',pebId]]
            baList = self.sfb.query('Branch_Approval__c', where=where)
            if baList in self.badInfoList:
                if self.debug > 0:  
                    print '  NO Branch Approvals found with %s'%where
                    print '  Found: %s'%pprint.pformat(baList)
            res['Branch_Approval__c'] = baList
            numBA = len(baList)

            #where = [['PE_Checkpoint__c','=',pebId]]
            #crList = self.sfb.query('Case', where=where)
            #if crList in self.badInfoList:
            #    if self.debug > 0:  
            #        print '  NO Branch Approvals found with %s'%where
            #        print '  Found: %s'%pprint.pformat(crList)
            #res['Case'] = crList
            #numCR = len(crList)
            numCR = 0

            self.sfb.setLog('getPEData %25s br:%s ba:%s cr:%s'%(branch,numBR,numBA,numCR),'info2')
            if self.debug > 0:
                self.sfb.setLog('->%25s ba:%s'%(branch,approvals),'info')
        else:
            if self.debug>1:
                print '   NO PE Checkpoint Branch Found for %s '%pprint.pformat(where)
            return res
        self.setData(res)
        self.loadFromSF = True
        if show: self.showData(res)
        return res
    

class SFPEBranchTool(SFTaskBranchTool):
    """ This is a subclass of the SFEntityTool to hold any Branch specific
        SOQL query methods and entity linking  methods
    """
    logname = 'lnPEchpnt'

    
##################################################################################################
#  Logic methods called from command line 
##################################################################################################

def addPEBranchUsage(err=''):
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

def addPEBranchCL(team,  branch, pebr,stream, options, st, teamTool=None,
                    checkTmb=True, scmFlag=False):
    """ command line logic for addPECheckPointBranch
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
        
        branchList = parseBranchListFile(listBranchPath)                
             
    elif branchList not in [ListType, TupleType]:
        # brachList passed in, but not a list. Try making it a list
        branchList = list([branchList])        
        pass
    if branchList is None:        
        branchList=list([branch])
        pass
    #print "BRANCH LIST %s" %branchList
    
    for branch in branchList:        
        statMap = SFTaskBranchStatus().getStatusMap()
        team = team.lower()
        if type(branch) is not seqTypes:
            if branch in [None,'']:
                print 'Please provide a branch name to link to the PE Checkpoint %s'%(pebr)
                sys.exit()
            brList = [branch]
        else:
            brList = branch
        db=options.debug
    
        # if we were passed a team tool, use it
        if teamTool is None:
            #print 'Connecting to SalesForce for the %s team branch in code stream %s' %(team,stream)
            sfb = SFTeamBranchTool(debug=db, logname='lnPEchpnt')
            #sfb.getConnectInfo(version,st)
        else:
            sfb = teamTool
            pass
    
            
        # default to the "Generic" branch for the specified team if a team branch name
        # isn't provided. The generic team branch has the same name as the team.
        
    
        #taskBrTool = SFTaskBranchTool(debug=db, logname='addTmB')
        tbrObj = SFPEBranch(sfTool=sfb)
        
        # load the PE Checkpoint branch if present other wise craete it
        peres = tbrObj.loadPEBranch(pebr, stream)
        pebrId=None
        if peres in sfb.badInfoList:
            print "Creating new PE checkpoint with name: %s"%pebr
            pebrId=createPEBranch(pebr, stream,team,teamTool=sfb)
            pass
        else:
            
            peData=peres[0]
            pebrId=peData.get('Id')
            pass
                
        #print "PE Checkpoint ID is %s" %pebrId 
        
        linkTaskBranches(pebrId,pebr,brList,stream,teamTool=sfb)        
                         
    return

def linkTaskBranches(pebrId,pebr,brList,stream,teamTool):
    sfb=teamTool  
    branchList=brList
    stream=stream
    if branchList in [None,'']:
        print 'Please provide a valid branch to link to %s '%(pebr)
        sys.exit()
    for branch in branchList:
        #print "Linking branch name '%s' to PE Chepoint '%s'"%(branch,pebr)
        brId=loadTaskBranch(branch,stream,teamTool)
        
        
        #where = [['PE_Checkpoint__c ','=',pebrId],'and',['Id','=',brId]]   
        where = [['Code_Stream__c','=',stream] ,'and',['Id','=',brId]]   
        queryList = sfb.query('Task_Branch__c', where=where, sc='all')
        
        if queryList in badInfoList:            
            pass
        else:
            for qr in queryList:
                pebr=qr.get('PE_Checkpoint__c')
                
                if pebr in [None,'']:
                    data = [{'PE_Checkpoint__c':pebrId,'Id':brId}]                       
                    buildLinkObjRes = sfb.update('Task_Branch__c', data)             
                    linkCrs(brId,pebrId,teamTool)
                    print "Linking branch name '%s' to PE Chepoint '%s'"%(branch,pebr)
                    #updateBranchApprovals(brId,pebrId,stream,teamTool
                    
                else:
                    print "Skipping... Task branch '%s' has been already linked to a PE checkpoint" %branch 
                    #linkCrs(brId,pebrId,teamTool)
                    #updateBranchApprovals(brId,pebrId,stream,teamTool)
                    pass      
                           
       
        pass
    
    return

def updateBranchApprovals(brId,pebrId,stream,teamTool):
    sfb=teamTool
    pename=None
    res=sfb.retrieve([pebrId], 'Checkpoint_Branch__c')
    if res not in badInfoList:
        for pe in res:
            pename= pe.get('Name')
            continue
        pass
    where = [['Task_Branch__c ','=',brId],'and',['Approval_Role__c','=','Product Engineer']]
    queryList = sfb.query('Branch_Approval__c', where=where, sc='all')
    if queryList in badInfoList:            
        print "No PE Branch approval found in Task Branch record, hence creating new BA"
        #Create new BA        
        pass
    else: 
        for qr in queryList:
            baid=rq.get('Id')
            name="Approval for %s in %s" %(pename,stream)  
            data = [{'PE_Checkpoint__c':pebrId,'Id':baid,'Branch__c':'','CR_List__c':'','Task_Branch__c':'','Name':name}]                       
            buildLinkObjRes = sfb.update('Branch_Approval__c', data) 
            
            pass
        
    return

def linkCrs(brId,pebrId,teamTool):
    sfb=teamTool
    where = [['Task_Branch__c ','=',brId]]
    queryList = sfb.query('Branch_CR_Link__c', where=where, sc='all')
    if queryList in badInfoList:            
        sfb.setLog('CRs do not have to be linked','info') 
        pass
    else:
        sfb.setLog('Linking CRs to PE Checkpoint','info')
        for qr in queryList:
            
            """eObj=sfb.describeSObject('Case') 
            data={}
            for f in eObj._fields:                      
                label=  f._label       
                name = f._name                                  
                print "CASE  %s ... %s "%(name,f._type)
                pass"""
            
            #caseId=qr.get('Case__c')
            brcrId=qr.get('Id')           
            where = [['Id','=',brcrId]]
            #fields=('PE_Checkpoint__c','Id')
                                              
            data = [{'PE_Checkpoint__c':pebrId,'Id':brcrId}]                       
            buildLinkObjRes = sfb.update('Branch_CR_Link__c', data) 
            sfb.setLog('CR Branch Link Updated %s '%buildLinkObjRes,'info')
            pass          
            
        pass
         
    return


def loadTaskBranch(branch,stream,teamTool):
    sfb=teamTool
    sfb.setLog('Finding TaskBranch Id for branch name %s'%branch,'info')
    
    where = [['Name','=',branch]
                ,'and',['Code_Stream__c','=',stream]]                
    queryList = sfb.query('Task_Branch__c', where=where, sc='all')
    
    if queryList in badInfoList:
           print "Skipping ...  NO Task Branch Found with name %s in stream %s" %(branch,stream)
           sfb.setLog('Skipping ...  NO Task Branch Found with name %s in stream %s' %(branch,stream),'info')
           return queryList
        
    if len(queryList) > 1:
        sfb.setLog('WARNING: There were more than one be only ONE Task Branch for %s in stream %s'%(branch,stream),'warn')
        pass
    
    brData=queryList[0]
    brId=brData.get('Id')       

    return brId


def createPEBranch(pebr,stream,team,teamTool):
    sfb=teamTool
    data={}
    teamId=getTeamId(team,stream,teamTool)
    data['Name']=pebr
    data['Stream__c']=stream
    data['Team_Branch__c']=teamId
    data['Status__c']='Approving By PE'    
    res = sfb.create('Checkpoint_Branch__c',data)
    if res in badInfoList:
        sfb.setLog('Warning: PE Chepoint with name %s was not created'%pebr,'warn')
        pass
    else:
        sfb.setLog('PE checkpoint was created sucessfully with name %s'%(pebr),'info')
        print "PE checkpoint was created sucessfully with name %s"%(pebr)
        pass
    return res[0]

def getTeamId(teamName,stream,teamTool):
    sfb=teamTool
    teamName = teamName.lower()
    teamId=None
    where = [['Name','=',teamName]
                ,'and',['Stream__c','=',stream]]                
    queryList = sfb.query('Team_Branch__c', where=where, sc='all')
    
    if queryList in badInfoList:
        sfb.setLog('Warning Team name %s is not a valid team, please specify a correct team name and resubmit the branch' %teamName,'info')
        sys.exit(1)
    if len(queryList) > 0:
        brData=queryList[0]
        teamId=brData.get('Id')          
        return teamId    

        
        
def parseBranchListFile(path):
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
            if (branch in [None,''] and branchlist in [None,'']) or stream in [None,''] or pebr in [None,'']: 
                print '%s' %addPEBranchUsage('You must provide at least a valid stream, a PE Checkpoint, a task barnch name and a team name')
                sys.exit()
                                                   
            addPEBranchCL(teamBR, branch, pebr,stream, options, st)
                            

        elif options.cmd in ['unlnpechpnt']:
            if team in [None,''] or stream in [None,'']: 
                print '%s' %remTeamBranchUsage('You must provide at least a valid stream a PE Checkpoint name and a team name')
                sys.exit()
            if teamBR in [None,'']:
                teamBR = team
            unlinkTeamBranchCL(teamBR, stream, branch, options, st)                            
        
        
        elif options.cmd in ['teamhelp']:
            print mainTeamUsage()
            sys.exit()
       
       
        
        print '\nTook a total of %3.2f secs -^' %(time.time()-st)
    else:
        print '%s' %usage(options.cmd)
if __name__ == "__main__":
    main_CL()