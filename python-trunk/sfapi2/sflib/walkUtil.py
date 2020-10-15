""" Business Logic specific to polling the sForce server for changes in the Task Branch object
    along with polling of changes in a local directory structure.  THis is a multi use admin tool
    
           Chip Vanek, September 17th, 2004
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
from sfUtil import *
from sfTeamBranch import SFTeamBranch   # get SFTeamBranch
from sop import sfEntities, SFEntitiesMixin, SFUtilityMixin, SFTestMixin
from walkSFEntity import SFTaskBranchWalk

        

class SFUtilWalkTool(SFTaskBranchTool):
    """ This is a subclass of the SFTaskBranchTool to hold any Branch specific
    """
    logname = 'sf.walkUtil'

    ##################################################################################################
    ##################################################################################################
    def getLatestTBA(self, secsAgo=60*60*24, show=False):
        """ get the Branch Approvals modified in the since secsAgo"""
        collect = {}
        actionNeeded = {}    # key as tbId value of action required
        fromSecs = time.time()-secsAgo
        dateStr = self.getAsDateTimeStr(fromSecs)
        where = [['OwnerId','!=',''],'and',['LastModifiedDate','>',dateStr]]
        print '%s getLatestTBA using query of %s'%(time.ctime(),where)
        queryList = self.query('Branch_Approval__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'getLatestBA Result: NO Branch Approvals Found within the last %s secs'%secsAgo
            return collect
        print '%s Found %s BA changed in teh last %s secs'%(time.ctime(),len(queryList),secsAgo)
        for info in queryList:
            tbId = info.get('Task_Branch__c','')
            action = self.checkBAForAction(info)
            if action not in [None,'']: 
                actionNeeded[tbId] = action
            bal = collect.get(tbId,[])
            bal.append(info)
            collect[tbId] = bal
        # now collect is a dictionary with key of tbId and list of baInfo
        
        result = []
        for tbId, bal in collect.items():
            if tbId in [None,'',[]]:
                self.setLog('getLatestTBA: tbId:%s bal:%s'%(tbId,bal),'error')
                continue
            tbInfo = self.retrieve([tbId], 'Task_Branch__c', fieldList='all', allowNulls=False)[0]
            print 'Task Branch: %s'%tbInfo.get('Name')
            if show: self.showData(tbInfo)
            for baInfo in bal:
                baRole = baInfo.get('Approval_Role__c')
                status = baInfo.get('Status__c')
                name   = baInfo.get('Name')
                msg = '    BA:%19s %-30s %s'%(baRole,status,name)
                print msg
                if show: self.showData(baInfo)
            result.append({'Task_Branch__c':tbInfo, 'Branch_Approval__c':bal})
        print 'Found %s Task_Branchs with %s Branch Approvals'%(len(result),len(queryList))
        return result, actionNeeded

    def delOrphanBAs(self):
        """ delete all the BAs that are no longer linked to a Task Branch"""
        where = [['Task_Branch__c','=','']]
        queryList = self.query('Branch_Approval__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'delOrphanBAs Result: NO Branch Approvals Orphans Found using %s'%where
            return []
        delList = []
        for info in queryList:
            baId = info.get('Id')
            if baId not in [None,'']:
                delList.append(baId)
            
        if len(delList) > 0:
            res = self.delete(delList)
            print 'deleted %s BA items'%(len(delList))
        
        

    def getTBAWith(self, where=None, show=False):
        """ get the Branch Approvals using passed where clause"""
        collect = {}
        actionNeeded = {}    # key as tbId value of action required
        if where is None:
            uid = '00530000000cCy5'  #Chip Vanek
            where = [['OwnerId','=',uid]]
        queryList = self.query('Branch_Approval__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'getTBAWith Result: NO Branch Approvals Found using %s'%where
            return collect
        for info in queryList:
            tbId = info.get('Task_Branch__c','')
            bal = collect.get(tbId,[])
            bal.append(info)
            collect[tbId] = bal
        return collect, actionNeeded

    ##################################################################################################
    ##################################################################################################

    ##################################################################################################
    #  utility and setup methods
    ##################################################################################################


##################################################################################################
version = 2.0  # version number shown to users at command line
##################################################################################################
#  Logic methods called from command line 
##################################################################################################
def getLatestCL(options, secsAgo=None, parm=None):
    entity = 'Branch_Approval__c'
    print 'Checking on the %s modified in the last %s secs'%(entity, secsAgo)
    sfb = SFUtilWalkTool(debug=options.debug,logname='sf.walkSFt')
    
    if secsAgo not in [None,'']:
        latestList, actionNeeded = sfb.getLatestTBA(secsAgo)   #secAgo is only parm
    elif parm not in [None,'']:
        latestList, actionNeeded = sfb.getTBAWith(parm)   #parm is ??
    else:
        print 'Call getLatestTBCL with secsAgo, or some query parms'
        sys.exit()
    total = len(latestList)
    print 'FOUND %s %s items modified in the last %s secs'%(total, entity, secsAgo)
    tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
    # latestList is [{'Task_Branch__c':tbInfo, 'Branch_Approval__c':bal}] bal is a list of BAs
    for info in latestList:
        if type(info) == type({}):
            tbInfo = info.get('Task_Branch__c')
            status = tbInfo.get('Branch_Status__c')
            branch = tbInfo.get('Branch__c')
            stream = tbInfo.get('Code_Stream__c')
            baList = info.get('Branch_Approval__c')
            tbObj.loadBranch(branch, stream)
        else:
            tbId = info[0]
            baList = info[1]
            tokens = tbObj.loadBranchById(tbId)
            status = tokens[2]
            branch = tbObj.branch
            stream = tbObj.stream
        # now do something interesting....
        #tbObj is now loaded with the sForce information
        if status not in [None,'']:
            updated = tbObj.setBranchStatus(status)
        if updated:
            print 'Updated %s'%(tokens)

        
def getALLBranchApprovals(num, options):
    if num in ['all']: num = 10000
    else:              num = int(num)
    print 'Checking on %s of the Branch approval objects'%num
    sfb = SFUtilWalkTool(debug=options.debug)
    allBAUsers = sfb.getBAUsers()
    total = len(allBAUsers)
    num = 0
    numWarn = 0
    print 'FOUND %s Owners of Branch Approvals'%total
    print 'Now will display the status of all approvals'
    tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
    for uid in allBAUsers:
        num += 1
        myBAList = sfb.getMyApprovals(uid=uid, stream=None, branch=None, show=False, getTB=False)
        total = len(myBAList)
        num = 0
        baIds = []
        print 'FOUND %s Branch Approvals for %s'%(total,uid)
        for info in myBAList:
            num += 1
            baId = info.get('Id')
            name = info.get('Name')
            role = info.get('Approval_Role__c')
            if role in ['Engineering Manager']:
                baIds.append(baId)
            print '%15s %s'%(role,name)
            #ret = sfb.delete(baIds)
            #print 'Deleted %s'%ret
        
        print ' \n'
    

def doSomething(method, term, parm, options):
    """  Command line controlled test of a method """
    print 'You called me with method:%s term:%s parm:%s ' %(method, term, parm)
    print 'Hope it was good for you'

##################################################################################################
#  Commandline management methods.  Minimal logic, just command parm processing
##################################################################################################
def usage(cmd='', err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is ??\n'
    m += ' '
    m += '    walkutil -c walk -s4.1 \n '      
    m += '      or\n'
    return m

def main_CL():
    """ Command line parsing and and defaults methods
    """
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-c", "--cmd",   dest="cmd",   default="walk",     help="Command type to use.")
    parser.add_option("-p", "--parm",  dest="parm",  default="",         help="Command parms.")
    parser.add_option("-x", "--parm2", dest="parm2", default=60,         help="Command parms2.")
    parser.add_option("-s", "--cs",    dest="cs",    default="4",        help="Code Stream of Branch")
    parser.add_option("-b", "--br",    dest="br",    default="",         help="Branch Label")
    parser.add_option("-f", "--path",  dest="path",  default="./details.txt", help="Path to details file.")
    parser.add_option("-z", "--trace", dest="trace", default="soap.out", help="SOAP output trace file.")
    parser.add_option("-d", "--debug", dest='debug', action="count",     help="The debug level, use multiple to get more.")
    (options, args) = parser.parse_args()
    if options.debug > 1:
        print ' cmd  %s, parms  %s, stream %s' %(options.cmd, options.parm, options.cs)
        print ' path   %s, trace  %s, debug  %s' %(options.path, options.trace ,options.debug)
        print ' args:  %s' %args
    else:
        options.debug = 0
    if len(args) > 0: 
        st = time.time()
        parm = options.parm
        query = args[1:]
        if options.cs in [None,'']: stream = '4'
        else: stream = options.cs

        if options.cmd in ['check']:
            checkCL(branch, stream, query, options, st)
            
        elif options.cmd in ['lsba']:
            try: num = int(query)
            except: num = 2000
            getALLBranchApprovals(num, options)

        elif options.cmd in ['walk']:
            secsAgo = int(options.parm2)
            if secsAgo in [None,'',0]: secsAgo = 60*1
            parm = options.parm
            getLatestCL(options, secsAgo, parm)

        else:
            doSomething('search', query, options.parm, options)
            print 'doing nothing yet, I can do it twice if you like'
        print '\nTook a total of %3.2f secs -^' %(time.time()-st)
    else:
        print '%s' %usage(options.cmd)

if __name__ == "__main__":
    main_CL()
