""" Business Logic specific to polling the sForce server for changes in the Task Branch object
    - Task Branch (TB) is a sForce representation of a code branch in Clearcase
    - TB is displayed as a container object with a list of:
       - Branch Approvals - Developer Accept, Manager Approve, PE Approve, AE accept, Closed
       - Branch CR Links - link objects to customer oriented CRs with mirroroed CR Status
 ToDo:
    - Create methods to support each specific action to call from command line
    
           Chip Vanek, July 26th, 2004
"""
import sys, time, os
import datetime
import StringIO
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
from sfTaskBranchStatusMap import *
from sfUser2 import SFUser
import mail


class SFTaskBranchWalkTool(SFTaskBranchTool):
    """ This is a subclass of the SFEntityTool to hold any Branch specific
        SOQL query methods and entity linking action methods
    """
    logname = 'sf.walkSFt'
 
    ########################################################################
    #  Branch Approval methods
    ########################################################################
    def taskOrTeam(self, brId):
        """ given a task branch ID, resolve the branch.

        If it's part of a team branch and it's status is
        Approved, pending Team Branch or later, return record to cause
        eval as a Team Branch, otherwise eval as a task branch.
        """
        dividingStat = 'Approved, pending Team Branch'
        evalInfo = {}

        if brId[:3] == TASK_BRANCH_SIG:
            tbObj = SFTaskBranchWalk(sfTool=self, debug=self.debug)
            brInfo = tbObj.loadBranchById(brId)
            tbBranch = brInfo[3]
            tbStream = brInfo[4]
            tbStatus = brInfo[2]

            evalInfo = self.assembleTbInfo(tbObj)
        
            if brInfo[5] > 0:
                if brInfo[5] > 1:
                    # Ack - task branch is linked to more than one team branch!
                    msg = 'Task branch %s in %s (%s) is linked to multiple team branches. Please investigate!' %(tbBranch, tbStream, brId)
                    self.setLog(msg, 'critical')
                    pass
            
                # check if status is late enough to force team branch treatment
                sm = self.getStatMap(tbStatus,{})
                order = sm.get('order')

                if order >= self.getStatMap(dividingStat,{}).get('order'): 
                    # treat as team branch
                    tbBTL = tbObj.getData('Branch_Team_Link__c')[0]
                    tmbId = tbBTL.get('Team_Branch__c')
                    brId = tmbId
                    pass
                pass
            pass
        # we'll run this if brId was passed in as a team branch ID or
        # if we determined we needed to eval the linked team branch
        # for a passed task branch
        
        if brId[:3] == TEAM_BRANCH_SIG:
            
            tmbObj = SFTeamBranch(sfTool=self, debug=self.debug)
            brInfo = tmbObj.loadTeamBranchById(brId)

            evalInfo = self.assembleTmbInfo(tmbObj)
            pass

        return brId, evalInfo


    def assembleTbInfo(self, tbObj):
        tbInfo = tbObj.getData('Task_Branch__c')
        tbBaList = tbObj.getData('Branch_Approval__c')

        if tbInfo in BAD_INFO_LIST:
            tbInfo = {}
            evalInfo = ''
        else:
            tbStatus = tbInfo.get('Branch_Status__c','')
            tbBranch = tbInfo.get('Branch__c','')
            tbStream = tbInfo.get('Code_Stream__c','')

            evalInfo = {'branch': tbBranch,
                        'stream': tbStream,
                        'status': tbStatus,
                        'type'  : 'task',
                        'baList': tbBaList}
            pass

        return evalInfo

        
    def assembleTmbInfo(self, tmbObj):
        tmbInfo = tmbObj.getData('Team_Branch__c')
        tmbBaList = tmbObj.getData('Branch_Approval__c')
        
        if tmbInfo in BAD_INFO_LIST:
            tmbInfo = {}
            evalInfo = ''
        else:
            tmbStatus = tmbInfo.get('Status__c','')
            tmbBranch = tmbInfo.get('Branch__c','')
            tmbStream = tmbInfo.get('Stream__c','')
            evalInfo = {'branch': tmbBranch,
                        'stream': tmbStream,
                        'status': tmbStatus,
                        'type'  : 'team',
                        'baList': tmbBaList}
            pass

        return evalInfo

        
    
    def getLatestBAwithActionNeeded(self, secsAgo=60*60*24, st=0):
        """ get the Branch Approvals modified in the since secsAgo
            This is the main entry methos from the cron job
            Returns: 
                branches     = {taskBranchID:{'branch':branch, 'stream':stream}}
                actionNeeded = {taskBranchID:{'role':'dev|mgr|..', 'action':'approve|reject', 'baId':baid}
                actionNeeded was create with the method checkBAForAction(info, status) were info is EACH BA in loop
                actionNeeded & branches is used next by actionBApprovals(br,act) to do the action (submit|appr|scm)
        """
        fromSecs = time.time()-secsAgo
        dateStr = self.getAsDateTimeStr(fromSecs)
        where = [['OwnerId','!=',''],'and',
                 ['LastModifiedDate','>',dateStr],'and',
                 ['Order__c','<',4.4]]

        queryList = self.query('Branch_Approval__c', where=where, sc='all')

        if queryList in self.badInfoList:
            if self.debug > 0:
                print 'getLatestBA Result: NO Branch Approvals Found within the last %s min'%(secsAgo/60)
            return {}, {}
        total = len(queryList)
        print '%.4s found %s Branch Approvals modified in the last %s min' \
              %((time.time()-st), total, secsAgo/60)    
        num = 0
        actionNeeded = {}    # key as tbId value of action required
        branches = {}

        for info in queryList:
            num += 1
            baId = info.get('Id')
            tbId = info.get('Task_Branch__c','')
            branch = info.get('Branch__c','')
            stream = info.get('Stream__c','')
            role = info.get('Approval_Role__c','')

            print "branch: %s, stream: %s, role: %s" %(branch, stream, role)

            if tbId in [None,'']:
                self.setLog('getLatestBAWAN: %s found BA NOT LINKED to a TB, baId:%s'%(branch,baId),'error')
                continue

            if branches.has_key(tbId):
                # already evaluated this task branch ID and it's on the docket
                continue

            branchId, branchInfo = self.taskOrTeam(tbId)
            branches[branchId] = branchInfo
            continue
        
        #print "Fetching recently modified task branches"
        
        # grab the Task Branches that have been modified 
        where = [['LastModifiedDate','>',dateStr],'and',['Branch_Status__c','!=','Open']]
        queryList = self.query('Task_Branch__c', where=where, sc='all')
        if queryList in self.badInfoList:
            if self.debug>0:
                print 'getLatestTB Result: NO Task Branches modified within the last %s min'%(secsAgo/60)
        else:
            for info in queryList:
                tbId = info.get('Id')
                branch = info.get('Branch__c','')
                stream = info.get('Code_Stream__c','')
                status = info.get('Branch_Status__c','')
                print "branch: %s, stream: %s, status: %s" %(branch, stream, status)
                if tbId in [None,'']:
                    self.setLog('getLatestBAWAN: %s found Empty TB %s'\
                                %(tbId, info),'error')
                    continue

                if branches.has_key(tbId):
                    # already evaluated this task branch ID and it's
                    # on the docket
                    continue
                
                branchId, branchInfo = self.taskOrTeam(tbId)
                branches[branchId] = branchInfo
                continue
            pass

        # grab Team Branches that have been modified
        where = [['LastModifiedDate','>',dateStr]]
        queryList = self.query('Team_Branch__c', where=where, sc='all')
        if queryList in self.badInfoList:
            if self.debug>0:
                print 'getLatestTmB Result: NO Team Branches modified within the last %s min'%(secsAgo/60)
        else:
            for info in queryList:
                tmbId = info.get('Id')
                branch = info.get('Branch__c','')
                stream = info.get('Stream__c','')
                status = info.get('Status__c','')
                print "branch: %s, stream: %s, status: %s" %(branch, stream, status)
                if tmbId in [None,'']:
                    self.setLog('getLatestBAWAN: %s found Empty TmB %s' \
                                %(tmbId, info),'error')
                    continue

                if branches.has_key(tmbId):
                    # already seen this team branch ID and it's on the docket
                    continue

                branchId, branchInfo = self.taskOrTeam(tmbId)
                branches[tmbId] = branchInfo
                continue
            pass
        total = len(branches)
        print '%.4s found %s unique Team and/or Task Branches'%((time.time()-st), total)    

        num = 0
        for brId, brInfo in branches.items():
            num += 1
            branch = brInfo.get('branch')
            stream = brInfo.get('stream')
            status = brInfo.get('status')
            type = brInfo.get('type','')
            baList = brInfo.get('baList',[])
            if branch == '' or stream == '': 
                print 'getLatestBAWAN: Skipping empty BAInfo:%s '%(brInfo)
                continue
            
            msg = '%3s/%s %2s BAs IN%32s AS %-30s'\
                  %(num,total,len(baList),branch,status)
            self.setLog(msg, 'info')
            print msg
            
            for info in baList:
                action = self.checkBAForAction(info, status)        
		#{'role':'', 'action':''} action = approve|reject

                if action not in [None,'',{'role':'', 'action':''}]: 
                    baId = info.get('Id')
                    action['baId'] = baId
                    action['stream'] = stream
                    action['branch'] = branch
                    appr = action.get('action')
                    role = action.get('role')
                    if actionNeeded.has_key(brId):          # multiple actions for one Task Branch
                        priorAct = actionNeeded[brId]
                        priorAction = priorAct.get('role')
                        #print "appr: %s" %appr
                        if priorAction == 'team':
                            msg = 'getLatestBAAction: %s Skipping %s action, Team Action pending for %s'\
                                   %(branch, appr, baId)
                            
                        elif appr == 'team':
                            actionNeeded[brId] = action
                            msg = 'getLatestBAAction: %s overwriting %s action with %s action for %s'\
                                   %(branch, priorAction, appr, baId)
                        else:
                            msg = 'getLatestBAAction: %s WhatToDO? %s action AFTER %s action for %s'\
                                   %(branch, priorAction, appr, baId)
                        self.setLog(msg,'warn')
                    else:        
                        actionNeeded[brId] = action
                        pass
                    msg ='%.4s FOUND ACTION %4s %8s action %31s AS %s'\
                         %((time.time()-st), role, appr, branch, status )    
                    print msg
                    self.setLog(msg,'info')
                pass
            continue
        return branches, actionNeeded

    def findBranchByName(self, branch, team=False, noAutocreate=False):
        branches = {}

        entity = 'Task_Branch__c'
        if team is True:
            entity = 'Team_Branch__c'
            noAutocreate = False # doesn't apply to team branch. ever.
            pass

        where = [['Branch__c','like',branch]]

        if noAutocreate is True:
            where.extend(['and',['Autocreated__c','=',False]])
            pass

        queryList = self.query(entity, where=where, sc='all')
        if queryList in self.badInfoList:
            print 'findBranchByName: NO Branches found for %s'%(branch)
            print ' results are %s'%queryList
            return {}

        if team is True:
            print ' Found %s TEam Branch(es) with %s'%(len(queryList),branch)
        else:
            print ' Found %s Task Branch(es) with %s'%(len(queryList),branch)
            pass

        for info in queryList:
            tbId = info.get('Id')
            if tbId in [None,'']:
                self.setLog('findBranchByName: Found empty Branch %s' \
                            %(tbId, info),'error')
                continue
            branchId, info = self.taskOrTeam(tbId)
            branches[branchId] = info
            continue

        return branches
    ## END findBranchByName
        

    def checkBranch(self, branch, stream, team=False):
        """ Just check this one branch on demand
            Called by users using 'walk' and from sForce WIL
        """        
        results = {}
        actionNeeded = {}

        branches = self.findBranchByName(branch, team)
        if len(branches) == 0:
            print 'checkBranch: Cannot build TB for %s'%(branch)
            return results, actionNeeded

        for id, info in branches.items():
            if stream == info.get('stream',''):
                results[id] = info
        if len(results) == 0:  # no branch found with passed stream, so...
                results = branches

        for brId, info in results.items():
            status = info.get('status')
            baList = info.get('baList')
            stream = info.get('stream')
            print '  Checking the %s approval records for %s'%(len(baList),branch)
            for info in baList:
                action = self.checkBAForAction(info, status)
                #{'role':'', 'action':''} action = approve|reject
                if action not in [None,'',{'role':'', 'action':''}]:
                    baId = info.get('Id')
                    action['baId'] = baId
                    action['stream'] = stream
                    action['branch'] = branch
                    appr = action.get('action')
                    role = action.get('role')
                    if actionNeeded.has_key(brId):          # multiple actions for one Task Branch
                        priorAct = actionNeeded[brId]
                        priorAction = priorAct.get('role')
                        msg = 'checkBranch: %s BAOverwrite %s action AFTER %s action for %s'\
                                           %(branch, priorAction, appr, baId)
                        if appr == 'team':
                            actionNeeded[brId] = action
                            msg = 'checkBranch: %s overwriting %s action with %s action for %s'\
                                                %(branch, priorAction, appr, baId)
                        self.setLog(msg,'warn')
                    else:
                        actionNeeded[brId] = action
        
        return results, actionNeeded

    def actionBApprovals(self, collect, actionNeeded, st=0):       
        """ main entry method for walkSF cron approvals """
        if st == 0: st= time.time()
        result = {}
        tbObj = SFTaskBranchWalk(sfTool=self, debug=self.debug)
        teamObj = SFTeamBranch(sfTool=self, debug=self.debug)        
        for tbId, action in actionNeeded.items():
            baId = action.get('Id')
            braId=action.get('baId')
            role = action.get('role')
            branch = action.get('branch')
            stream = action.get('stream')
            approv = action.get('action')
            isTeam = action.get('isTeam', False)
            # action = {'Id':baId, 'role':role, 'branch':branch, 'stream':cs, 'action',"approved|rejected", isTeam:True|False}
            #msg = 'ACTIONING: %s %s for %s in %s tbId:%s based on BA: %s'%(role,approv,branch,stream, tbId, baId)
            msg = 'ACTIONING: %s %s for %s in %s tbId:%s  based on BA: %s %s'%(role,approv,branch,stream, tbId, baId,braId)
            #msg = '%.4s %s'%((time.time()-st),msg)
            self.setLog(msg,'info')
            print msg
            if role == 'dev':
                num = tbObj.submitByDev(branch, stream, st)
                result[branch] = {'num':num, 'role':role, 'approve':approv, 'stream':stream}
                
            elif role == 'part':
                if approv == 'rejected':
                    num = tbObj.rejectToDevByPart(branch, stream, st)
                else:
                    num = tbObj.submitByPart(branch, stream, st)
                result[branch] = {'num':num, 'role':role, 'approve':approv, 'stream':stream}
                
            elif role == 'mgr':
                if approv == 'rejected':
                    num = tbObj.rejectToDevByMgr(branch, stream, st)
                else:
                    num = tbObj.submitByMgr(branch, stream, st)
                result[branch] = {'num':num, 'role':role, 'approve':approv, 'stream':stream}
                
            elif role == 'pe':
                if approv == 'rejected':
                    num = tbObj.rejectToDevByPe(branch, stream, st)
                else:
                    num = tbObj.submitByPe(branch, stream, st)
                result[branch] = {'num':num, 'role':role, 'approve':approv, 'stream':stream}

            elif role == 'team':
                num = teamObj.submitByTeam(branch, stream, st)
                result[branch] = {'num':num, 'role':role, 'approve':approv, 'stream':stream}
                
            elif role == 'scm':
                if isTeam is True:
                    num = teamObj.submitToSCM(branch, stream, st)
                else:
                    num = tbObj.submitToSCM(branch, stream, st)
                result[branch] = {'num':num, 'role':role, 'approve':approv, 'stream':stream}
                
            elif role == 'ae':
                num = tbObj.submitToAE(branch, stream, st)
                result[branch] = {'num':num, 'role':role, 'approve':approv, 'stream':stream}
            else:
                print 'Role value error >%s< is not recognized'%role
        
        for branch, info in result.items():
            msg = '%32s IN %s was %s by %s and sent %s msgs'\
              %(branch, info.get('stream'),info.get('approve'),info.get('role'),info.get('num'))
            print msg
        if len(result) >0:
            #print 'ACTIONED %s branches'%len(result)
            pass
               
        return result
        
        
    def fixBranches(self, collect, st=0):
        """ main entry method for walkSF cron approvals """
        if st == 0: st= time.time()
        total = len(collect)
        num = 0
        cnum = 0
        tbObj = SFTaskBranchWalk(sfTool=self, debug=self.debug)
        teamObj = SFTeamBranch(sfTool=self, debug=self.debug)

        for brId, info in collect.items():
            num +=1
            branch = info.get('branch')
            stream = info.get('stream')
            status = info.get('status','')
            brtype = info.get('type','')
            msg = 'Checking: %s in %s type:%s status:%s'%(branch,stream,brtype,status)
            msg = '%s/%s %s'%(num,total,msg)
            self.setLog(msg,'info')
            print msg

            if brtype in ['team']:
                teamObj.loadTeamBranchById(brId)
                # just check if all is consistant with existing status
                changes = teamObj.setBranchStatus() 
            else:
                tbObj.loadBranchById(brId)
                # just check if all is consistant with existing status
                changes = tbObj.setBranchStatus() 

            if changes:
                msg = 'FIXES APPLIED to %s in %s'%(branch,stream)
                print msg
                self.setLog(msg,'info')
                cnum +=1
        msg = 'fixBranches fixed %s of %s in %s sec'%(cnum,total,(time.time()-st))
        print msg
        self.setLog(msg,'info')
        return cnum

    
    def checkBAForAction(self, baInfo, status, actionList=[]):
        """ check the fields in the Branch Approval object and decide if action is required
            return action key or ''
        """
        if baInfo in [None,{},'']:
            return ''
        
        sm = self.getStatMap(status,{})
        # sm = {'order':34.0, 'role':'mgr', 'crStatus':'Approving', 'crStatusFirst':'First-Approving'}
        statOrder = sm.get('order')
        activeRole = sm.get('role','')
        role    = baInfo.get('Approval_Role__c','')
        approve = baInfo.get('Approve__c','')
        actor   = baInfo.get('OwnerId','')
        baId    = baInfo.get('Id','')
        tbId    = baInfo.get('Task_Branch__c','')
        baStat  = baInfo.get('Status__c','')
        #actDate = baInfo.get('Date_Time_Actioned','')
        noteDate= baInfo.get('Date_Time_Notified','')
        action = {'role':'', 'action':''}
        
        if status in ['Fixing','Submitting']:
            if role == 'Developer': # and activeRole in ['dev']:
                validStatsBA = ['Fixing','Submitting','Submitted','Closed']
                if status in ['Submitting'] and approve in ['Approve']:
                    action = {'role':'dev', 'action':'approved'}
        
        elif status in ['Approving by Partition Reviewer']:
            if role == 'Partition Reviewer': # and activeRole in ['part']:
                validStatsBA = ['Pending Submission','Requires Approval','Approving','Approved','Rejecting','Rejected']
                if baStat in ['Requires Approval','Approving'] and approve in ['Approve']:
                    action = {'role':'part', 'action':'approved'}
                if baStat in ['Requires Approval','Approving'] and approve in ['Reject']:
                    action = {'role':'part', 'action':'rejected'}
                    
        elif status in ['Approving by Manager']:
            if role == 'Engineering Manager': # and activeRole in ['mgr']:
                validStatsBA = ['Pending Submission','Requires Approval','Approving','Approved','Rejecting','Rejected']
                if baStat in ['Requires Approval','Approving'] and approve in ['Approve']:
                    action = {'role':'mgr', 'action':'approved'}
                if baStat in ['Requires Approval','Approving'] and approve in ['Reject']:
                    action = {'role':'mgr', 'action':'rejected'}
        
        elif status in ['Approved by Manager','Approving by PE']:
            if role == 'Product Engineer': # and activeRole in ['pe']:
                validStatsBA = ['Pending Submission','Requires Approval','Approving','Approved','Rejecting','Rejected']
                # added Approved to the list below to catch the case where the PE BA is marked
                # Approved/Approve, but the task branch status hasn't moved forward.
                if baStat in ['Requires Approval','Approving','Approved'] and approve in ['Approve']:
                    action = {'role':'pe', 'action':'approved'}
                if baStat in ['Requires Approval','Approving'] and approve in ['Reject']:
                    action = {'role':'pe', 'action':'rejected'}
        
        elif status in ['Approved by PE', 'Approved, pending Branch']:
            if role == 'Team Manager': # 
                #validStatsBA = ['Awaiting Branches','Team Branch Hold','Submitted to Team Testing','Team-Approving','Team-Approved']
                if (baStat in ['Team Approving'] and approve in ['Approve']) or\
                       baStat in ['Team Approved']:
                    action = {'role':'team', 'action':'approved'}
        
            elif role == 'SCM': # and activeRole in ['scm']:
                action = {'role':'scm', 'action':'approved'}
        
        elif status in ['Team Branch Hold']:
            if role == 'Team Manager':
                if baStat in ['Team Approving','Team Approved'] \
                       and approve in ['Approve']:
                    action = {'role':'team', 'action':'approved',
                              'isTeam': True}
            
        elif status in ['Team-Approved','Approved, pending Team Branch']:
            if role == 'Team Manager': # 
                #validStatsBA = ['Awaiting Branches','Team Branch Hold','Submitted to Team Testing','Team-Approving','Team-Approved']
                if baStat in ['Team Approved'] or \
                       (baStat in ['Team Approving'] and approve in ['Approve']):
                    action = {'role':'scm', 'action':'approved',
                              'isTeam': True}
        
        elif status in ['Merged - Notifying Originator']:
            if role == 'CR Originator' and activeRole in ['ae']:
                action = {'role':'ae', 'action':'approved'}
                
        return action





    ##################################################################################################
    #   Overall Status control mapping for Branch Approvals
    ##################################################################################################
    def getStatMap(self, status, default=None):
        """ wrapper to handle status not in self.statMap 
        """
        sm = self.getStatusMap().get(status,{})
        if sm in [None,{}]:
            print 'ERROR %s not found in statusMap'%status
            if default is not None:
                return default
            sm = self.getStatusMap().get('Fixing',{})
        return sm
    

    ##################################################################################################
    #  utility and setup methods
    ##################################################################################################


##################################################################################################
version = 2.0  # version number shown to users at command line
##################################################################################################
#  Logic methods called from command line 
##################################################################################################
def getLatestTBCL(options, secsAgo=None):
    entity = 'Branch_Approval__c'
    print 'Checking on the %s modified in the last %s secs'%(entity, secsAgo)
    sfb = SFTaskBranchWalkTool(debug=options.debug,logname='sf.walkSFt')
    if secsAgo not in [None,0,'']:
        latestList, actionNeeded = sfb.getLatestTBA(secsAgo)   #secAgo is only parm
    else:
        latestList, actionNeeded = sfb.getLatestTBA()          #secAgo is only parm
    total = len(latestList)
    print 'FOUND %s %s items modified in the last %s mins'%(total, entity, secsAgo/60)
    tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
    # latestList is [{'Task_Branch__c':tbInfo, 'Branch_Approval__c':bal}] bal is a list of BAs
    for info in latestList:
        tbInfo = info.get('Task_Branch__c')
        baList = info.get('Branch_Approval__c')
        # now do something interesting....
        

def fixTBCL(options, parm=None):
    entity = 'Task_Branch__c'
    sfb = SFTaskBranchWalkTool(debug=options.debug,logname='walkFix')
    if parm in ['all']:
        parm = [['OwnerId','!=','']]
    if parm in ['nomts']:
        dateStr = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.localtime(0))
        parm = [['Branch_Status__c','like','Merged%']
                ,'and',['Merged_Date_Time__c','=','']
               ]
    print 'Checking on the %s using fix where %s '%(entity, parm)
    if parm not in [None,0,'']:
        latestList = sfb.getTBWith(parm)   #parm is ??
    else:
        latestList = sfb.getTBWith()       # get Task Branch Approval owned by chip
    total = len(latestList)
    print 'FOUND %s %s items using parm %s'%(total, entity, parm)
    tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
    for tbInfo in latestList:
        #print 'Info returned by getTBAWith is: tbId:%s baList:%s'%(tbId, baList)
        if tbInfo in [None,'','fail']:
            print 'fixTBCL: Could not find ID for TaskBranch %s'%tbInfo
            continue
        if type(tbInfo) != type({}):
            continue
        tbId = tbInfo.get('Id')
        tokens = tbObj.loadBranchById(tbId)
        # tokens = [numCLs,numBAs,status,branch,stream]
        status = tokens[2]
        print 'Updating info for %s using same status of %s'%(tokens[3],status)
        updated = False
        if status not in [None,'']:
            updated = tbObj.setBranchStatus(status)
        if updated:
            print 'Updated %s'%(tokens)

def setTBFixStamp(branch, stream, status, ts='now', db=0):
    entity = 'Task_Branch__c'
    if ts in [None,'']: ts = time.time()
    if status in [None,'',[]]: 
        print 'Please provide a status as next step'
	sys.exit(1)
    if type(status) == type([]):
        status = ' '.join(status)
    sfb = SFTaskBranchWalkTool(debug=db,logname='setTBStamp')
    updated = sfb.setTBFixStamp(branch, stream, status, ts=ts)
    if updated:
        print 'Updated TimeStamp %s for %s %s stat:%s'\
                           %(ts,branch, stream, status)

	    
def fixTBACL(options, parm=None):
    entity = 'Branch_Approval__c'
    if parm in ['all']:
        parm = [['OwnerId','!=','']]
    if parm in ['nomts']:
        parm = [['OwnerId','!=','']
                ,'and',['Branch_Status__c','like','Merged,Closed']
                ,'and',['Merged_Date_Time__c','like','']
               ]

    print 'Checking on the %s using fix parm %s '%(entity, parm)
    sfb = SFTaskBranchWalkTool(debug=options.debug,logname='walkFix')
    if parm not in [None,0,'']:
        latestList, actionNeeded = sfb.getTBAWith(parm)   #parm is ??
    else:
        latestList, actionNeeded = sfb.getTBAWith()       # get Task Branch Approval owned by chip
    total = len(latestList)
    print 'FOUND %s %s items using parm %s'%(total, entity, parm)
    tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
    for tbId, baList in latestList.items():
        #print 'Info returned by getTBAWith is: tbId:%s baList:%s'%(tbId, baList)
        if tbId in [None,'']:
            print 'fixTBACL: Could not find ID for TaskBranch %s'%baList
            continue
        tokens = tbObj.loadBranchById(tbId)
        # tokens = [numCLs,numBAs,status,branch,stream]
        status = tokens[2]
        print 'Updating info for %s using same status of %s'%(tokens[3],status)
        updated = False
        if status not in [None,'']:
            updated = tbObj.setBranchStatus(status)
        if updated:
            print 'Updated %s'%(tokens)
        
        

def checkCL(branch, stream, db=0, st=0):
    """ Main entry point to just check, action on branch  """
    
    sfb = SFTaskBranchWalkTool(debug=db,logname='sf.checkTB')
    print 'Checking for the Branch %s'%(branch)
    sfb.getConnectInfo('2.1.0',st)
    if 1:
        collect, actionNeeded = sfb.checkBranch(branch, stream, team=False)
        if len(collect) == 0:
	    print 'Checking if this is a Team Branch'
 	    collect, actionNeeded = sfb.checkBranch(branch, stream, team=True)
    try: pass
    except Exception,e:
	print 'Error: checkBranch getting branches %s'%e
    
    actioned = sfb.actionBApprovals(collect, actionNeeded, st)
    if len(actioned) > 0:
        print 'Actioned this branch %s'%actioned
        

    try:	
        actioned = sfb.actionBApprovals(collect, actionNeeded, st)
        if len(actioned) > 0:
            print 'Actioned this branch %s'%actioned
    except Exception,e:
	print 'Error: checkBranch actioning approvals %s'%e
    
    """changed  = sfb.fixBranches(collect,st)
    print ' Checked status and got: %s'%changed"""

    try: 
        changed  = sfb.fixBranches(collect,st)
        print ' Checked status and got: %s'%changed
    except Exception, e:
	print 'Error: checkBranch fixing branch %s'%e
    

def walkSFQueryCL(role, options, st=0):
    """
    Wrapper to check for both approvals and rejections on a role's BAs.
    """
    logname = 'walk%s'%role
    sfb = SFTaskBranchWalkTool(debug=options.debug,logname=logname)

    if role in ['part','mgr','pe','team','ae']:
        doneApp = walkSFQueryFlow(sfb, role, options, st, act='Approve')
        doneRej = walkSFQueryFlow(sfb, role, options, st, act='Reject')
        done = doneApp + doneRej
        pass
    elif role in ['scm']:
        done = walkSFToSCMFlow(sfb, options, st)
    elif role in ['autoae']:
        done = walkAEAutoApproveFlow(sfb, options, st)
    else:
        print 'Unknown role of %s'%role
        sys.exit(0)

    sys.exit(done)

def walkSFQueryFlow(sfb, role, options, st=0, act='Approve'):
    """ new main poll method using targeted queries 
        This queries Branch approvals for 'approve'
    """
    if act not in ['Approve','approve','reject','Reject']:
        act = 'approve'
    action = {'action':'approved','isTeam':False}
    if act in ['Reject','reject']:
        action = {'action':'rejected','isTeam':False}

    where  = [['OwnerId','!=','']]
    where += ['and','(',['Status__c','=','Approving'],'or',
              ['Status__c','=','Team Approving'],'or',
              ['Status__c','=','Merged - Testing by Originator'],')']
    where += ['and',['Approve__c','=','%s'%act]]
    
    tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
    if role in ['part']:
        where += ['and',['Approval_Role__c','=','Partition Reviewer']]
        action['role'] = 'part'
    elif role in ['mgr']:
        where += ['and',['Approval_Role__c','=','Engineering Manager']]
        action['role'] = 'mgr'
    elif role in ['pe']:
        where += ['and',['Approval_Role__c','=','Product Engineer']]
        action['role'] = 'pe'
    elif role in ['team']:
        where += ['and',['Approval_Role__c','=','Team Manager']]
        action['role'] = 'team'
        action['isTeam'] = True
        tbObj = SFTeamBranch(sfTool=sfb,debug=options.debug)
    elif role in ['ae']:
        where += ['and',['Approval_Role__c','=','CR Originator']]
        action['role'] = 'ae'
    #logname = 'walk%s'%role
    #sfb = SFTaskBranchWalkTool(debug=options.debug,logname=logname)
    collect, empty = sfb.getTBAWith(where, isTeam=action['isTeam'])
    # collect = {tbId:[list of BAs]}
    total = len(collect)
    print '%s FOUND %s BAs items with %s for role %s ' \
          %(time.ctime(),total, act, role)
    # actionNeeded = {tbId:action}
    #action = {'Id':baId, 'role':role, 'branch':branch
    #         ,'stream':cs, 'action',"approved|rejected", isTeam:True|False}
    #actionNeeded = {tbId:action}
    actionNeeded = {}
    done = 0
    
    for tbId, baList in collect.items():
        if tbId in [None,'']:
            #print 'walkSFQueryFlow: Could not find ID for TaskBranch %s'%baList
            continue
        # now can load the (Task|Team)Branch and approve away        
        if role in ['team']:
            tokens = tbObj.loadTeamBranchById(tbId)
        else:
            tokens = tbObj.loadBranchById(tbId)
            pass
        # tokens = [numCLs,numBAs,status,branch,stream]
        status = tokens[2]
        branch = tokens[3]
        stream = tokens[4]
        print 'Actioning %s for %s %s %s'%(status,branch,stream,tokens[0])
        action['branch'] = branch
        action['stream'] = stream
        actionNeeded = {tbId: action}
        actioned = sfb.actionBApprovals(collect, actionNeeded, st)
        if len(actioned) == 0:
            print 'Failed Action %s %s for %s %s'%(status,act,branch,stream)
        else:
            print 'Actioned %s %s for %s %s\n'%(status,act,branch,stream)
            done += 1
            pass
    
    #print 'Actioned %s TaskBranches'%(done)
    #print actionNeeded
    return done


def walkSFToSCMFlow(sfb, options, st=0):
    """ new main poll method using targeted queries 
        This queries Branch approvals for 'approve'
    """
    tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
    tmbObj = SFTeamBranch(sfTool=sfb,debug=options.debug)

    action = {'role': 'scm', 'action':'approved'}

    # query for task branches ready for submission
    brList = []
    where  = [['Branch_Status__c','=','Approved, pending Branch']]
    res = sfb.query(TASK_BRANCH_OBJ, where, sc='all')
    if res in BAD_INFO_LIST:
        pass
    else:
        brList.extend(res)

    # query for team branches ready for submission
    where  = [['Status__c','=','Team-Approved']]
    res = sfb.query(TEAM_BRANCH_OBJ, where, sc='all')
    if res in BAD_INFO_LIST:
        pass
    else:
        brList.extend(res)
        
    print '%s FOUND %s items ready for SCM' \
          %(time.ctime(), len(brList))

    done = 0
    for br in brList:
        tbId = br.get('Id')
        if tbId[:3] == TASK_BRANCH_SIG:
            tokens = tbObj.loadBranchById(tbId)
            action['isTeam'] = False
        else:
            tokens = tmbObj.loadTeamBranchById(tbId)
            action['isTeam'] = True
            
        # tokens = [numCLs,numBAs,status,branch,stream]
        status = tokens[2]
        branch = tokens[3]
        stream = tokens[4]
        print 'Actioning %s for %s %s %s'%(status,branch,stream,tokens[0])
        action['branch'] = branch
        action['stream'] = stream
        actionNeeded = {tbId: action}
        
        actioned = sfb.actionBApprovals({}, actionNeeded, st)
        if len(actioned) == 0:
            print 'Failed Action %s for %s %s'%(status,branch,stream)
        else:
            print 'Actioned %s for %s %s\n'%(status,branch,stream)
            done += 1
            pass
        continue
    
    return done

def walkAEAutoApproveFlow(sfb, options, st=0):
    """ This flow looks for AE BAs that have been 'ripe' (Merged - Testing,
    but unapproved and last modified date > 15 days ago. Flow simply sets
    Approve__c field to Approve on these BAs and sends a notification
    to the approver.
    """
    done = 0
    daysPast = 15
    limit = 2 # max number to auto-approve per run
    mailServer = sfb.mailServer2()

    # determine the  date 15 days ago
    now = datetime.datetime.utcnow()
    delta = datetime.timedelta(days=daysPast, hours=12)
    dateline = now - delta
    datelineFmt = '%s.000Z' %dateline.isoformat()[:19]

    where =  [['Approval_Role__c', '=', 'CR Originator']]
    where += ['and', ['Status__c', '=', 'Merged - Testing by Originator']]
    where += ['and', ['LastModifiedDate', '<', datelineFmt]]
    where += ['and', ['Approve__c', '!=', 'Approve']]
    where += ['and', ['Approve__c', '!=', 'Reject']]

    fields = ('Id', 'OwnerId', 'Approve__c', 'Case__c', 'Stream__c',
              'Task_Branch__c', 'Team_Branch__c', 'comments__c')
    res = sfb.query('Branch_Approval__c', where, sc=fields)

    if res in BAD_INFO_LIST:
        res = []
        pass

    msg = "Found %s AE BAs to auto-approve." %(len(res))
    sfb.setLog(msg, 'info')
    print msg

    # collect the CR IDs
    crIdList = []
    for ba in res:
        crId = ba.get('Case__c',None)
        if crId is not None:
            crIdList.append(crId)
            pass
        continue

    # fetch CR subject and number info for the list of CRs
    fields = ('Id','CaseNumber','Subject')
    crRes = sfb.retrieve(crIdList, CASE_OBJ, fields)
    crLookup = {}
    for cr in crRes:
        crLookup[cr.get('Id')] = cr
        continue

    # now, process and auto-approve each BA
    for ba in res:
        # add a note to the comments
        dateNoteFmt = datetime.datetime.now().isoformat()[:10]
        comment = "Autoapproved on %s after %s days\n--\n%s" \
                  %(dateNoteFmt, daysPast, ba.get('comments__c',''))
        
        # for each found, set: Approve__c = 'Approve'
        baUpdMap = {'Id': ba.get('Id'),
                    'Approve__c': 'Approve',
                    'Auto_Action_Timestamp__c': time.mktime(now.timetuple()),
                    'comments__c': comment}

        res = sfb.update('Branch_Approval__c', data=baUpdMap)
        done += 1
        
        if res[0] == ba.get('Id'):
            # send notification to BA owner

            # get the CR info:
            crInfo = crLookup.get(ba.get('Case__c'))
            crId = crInfo.get('Id')
            crNum = crInfo.get('CaseNumber').lstrip('0')
            crSubj = crInfo.get('Subject')

            stream = ba.get('Stream__c')
            if stream in LEGACY_STREAMS:
                stream = "blast%s" %stream
                pass

            # log the autoapproval
            msg = "Autoapproved AE BA on CR %s in stream %s (BA: %s)" \
                  %(crNum, stream, ba.get('Id'))
            sfb.setLog(msg, 'info')
            print msg


            # look up owner's user record.
            baOwner = SFUser.retrieve(sfb, ba.get('OwnerId'))
            baOwnerData = baOwner.getDataMap()
            baOwnerEmail = baOwnerData.get('Email')
            baOwnerName = "%s %s" %(baOwnerData.get('FirstName',''),
                                    baOwnerData.get('LastName'))
            baOwnerName.strip()
            
            subj = "Fix for CR %s in stream %s automatically approved for you" %(crNum, stream)

            body =  "%s,\n\n" %baOwnerName
            body += "The approval record for a fix of the following CR which has been merged into\n"
            body += "the %s code stream has been automatically approved on your behalf.\n\n" %(stream)
            body += "%s: %s\n" %(crNum, crSubj)
            body += "%s/%s\n\n" %(sfb.sfdc_base_url, crId)
            body += "Task Branch: %s/%s\n" %(sfb.sfdc_base_url,
                                             ba.get('Task_Branch__c'))
            body += "Branch Approval: %s/%s\n" %(sfb.sfdc_base_url,
                                                   ba.get('Id'))
            body += "\n"
            body += "Merged fixes are available for testing for %s days before\n" %daysPast
            body += "they are automatically approved.\n"

            message = mail.Message(sfb.from_addr, baOwnerEmail, body, subj)

            mailServer.sendEmail(message)

    return done
## END walkAEAutoApproveFlow

    
def walkSFCL(secsAgo, options):
    """ main polling method run from cron  """
    if secsAgo in [None,0,'']:
        print 'Please provide a valid secs integer'
        return 0
    start = time.time()
    maxTime = 60*15
    #maxTime = 60*3 # shorter run time for testing
    waitTime= 180 # wait 3 min between loop iterations
    times = 0
    totalTimes = maxTime/waitTime
    sfb = SFTaskBranchWalkTool(debug=options.debug,logname='sf.walkSFt')
    try:
        lockHandle = cronLock('sfWalkSF.lock')
    except Exception, e:
        msg = 'Could not acquire exclusive lock for cron run. Assume another instance is being run. EXITING.'
        sfb.setLog(msg, 'warn')
        sfb.setLog('Information from locking operation was: %s' %e,'warn')
        print '%s %s'%(time.ctime(),msg)
        sys.exit()
    
    elapes = (time.time()-start)
    while elapes < maxTime:
        st = time.time()
        times +=1
        secs = int(secsAgo)
        togo = (maxTime -elapes)/60
        print 'Checking for Branch Approves modified in the last %s min %s/%s max loops %.1s min to go'%((secs/60),times,totalTimes,togo)
        sfb.getConnectInfo('2.02',st)
        collect, actionNeeded = sfb.getLatestBAwithActionNeeded(secsAgo, st)

        #print "walkSFCL: collect = %s" %pprint.pformat(collect)
        #print "walkSFCL: actionNeeded = %s" %pprint.pformat(actionNeeded)
        
        actioned = sfb.actionBApprovals(collect, actionNeeded, st)
        #changed  = sfb.fixBranches(collect,st)
        if len(actioned) == 0:
            secsAgo = secs + 60*10
        
        print '%s %.5s secs to action %s out of %s branches, waiting %s secs then checking back %s min'%(time.ctime(), (time.time()-st), len(actioned), len(collect),waitTime, secsAgo/60)
        time.sleep(waitTime)
        elapes = time.time() - start
        #print actioned

	
def walkSFCheckCL(secsAgo, options):
    """ aux polling method run from cron, only fixes up modified Task Branches  """
    if secsAgo in [None,0,'']:
        print 'Please provide a valid secs integer'
        return 0
    start = time.time()
    maxTime = 60*50
    waitTime= 60 # wait 1 min between loop iterations
    times = 0
    totalTimes = maxTime/waitTime
    sfb = SFTaskBranchWalkTool(debug=options.debug,logname='sf.walkSFx')
    try:
        lockHandle = cronLock('sfWalkSFx.lock')
    except Exception, e:
        msg = 'Could not acquire exclusive lock for Branch Fix cron run. %s'%e
        sfb.setLog(msg, 'warn')
        print '%s %s'%(time.ctime(),msg)
        sys.exit()
    
    elapes = (time.time()-start)
    while elapes < maxTime:
        st = time.time()
        times +=1
        secs = int(secsAgo)
        togo = (maxTime -elapes)/60
        print 'Checking for Branch Approves modified in the last %s min %s/%s max loops %.1s min to go'%((secs/60),times,totalTimes,togo)
        sfb.getConnectInfo('2.01',st)
        collect, actionNeeded = sfb.getLatestBAwithActionNeeded(secsAgo, st)

        #actioned = sfb.actionBApprovals(collect, actionNeeded, st)
        changed  = sfb.fixBranches(collect,st)
        if changed == 0:
            secsAgo = secs + 60*10
        
        print '%s %.5s secs to change %s out of %s branches, waiting %s secs then checking back %s min'%(time.ctime(), (time.time()-st), changed, len(collect),waitTime, secsAgo/60)
        time.sleep(waitTime)
        elapes = time.time() - start



        
        
def getALLBranchApprovals(num, options):
    if num in ['all']: num = 10000
    else:              num = int(num)
    print 'Checking on %s of the Branch approval objects'%num
    sfb = SFTaskBranchWalkTool(debug=options.debug)
    allBAUsers = sfb.getBAUsers()
    total = len(allBAUsers)
    num = 0
    numWarn = 0
    print 'FOUND %s Owners of Branch Approvals'%total
    print 'Now will display the status of all approvals'
    tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
    for uid in allBAUsers:
        num += 1
        res = sfb.getMyApprovals(uid=uid, stream=None, branch=None, show=False, getTB=False)
        print ' \n'
    

def getMyBranchApprovals(options):
    sfb = SFTaskBranchWalkTool(debug=options.debug)
    myBAList = sfb.getMyApprovals(uid=None, user='chip@molten-magma.com')
    total = len(myBAList)
    num = 0
    baIds = []
    print 'FOUND %s Branch Approvals'%total
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


def getLatestBA(options, secsAgo=None):
    #entity = 'Task_Branch__c'
    entity = 'Branch_Approval__c'
    print 'Checking on latest %s '%entity
    sfb = SFTaskBranchWalkTool(debug=options.debug,logname='getBA')
    if secsAgo not in [None,0,'']:
        latestList, actionNeeded = sfb.getLatestTBA(secsAgo)   #secAgo is only parm
    else:
        latestList, actionNeeded = sfb.getLatestTBA()          #secAgo is only parm
    total = len(latestList)
    print 'FOUND %s %s items'%(total, entity)
    #tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)


def doSomething(method, term, parm, options):
    """  Command line controlled test of a method """
    print 'You called me with method:%s term:%s parm:%s ' %(method, term, parm)
    print 'Hope it was good for you'

def teambranchset(branch, stream, db, st, newstatus, setcyclecount='False'):
#    print 'Entering teambranchset'
#    print 'Stream: %s, Branch: %s, new status: %s, Cycle count set: %s' %(stream, branch, newstatus, setcyclecount)
#
    sfb = SFTaskBranchWalkTool(debug=db,logname='sf.checkTB')
    print 'Checking for the Branch %s'%(branch)
    sfb.getConnectInfo('2.1.0',st)
#    find the branch, make sure it exists in a given stream
    branches = sfb.findBranchByName(branch, team=True)
    if len(branches) == 0:
        print 'Cannot find branch by label: %s'%(branch)
        return
    results = {}
    for id, info in branches.items(): 
        if stream == info.get('stream',''): 
            results[id] = info
            my_branch = info
    if len(results) == 0:
        print 'Cannot find branch %s in stream: %s'%(branch, stream)
        return
    if len(results) > 1:
        print 'Found more then one branch %s in stream: %s'%(branch, stream)
        return
    
    print "Found branch %s in stream %s" % (my_branch.get('branch',''), my_branch.get('stream',''))
#    set branch to new status

#   Check all Team Branches for given branch label and stream
    try:
        collect, actionNeeded = sfb.checkBranch(branch, stream, team=True)
    except Exception,e:
        print 'Error: checkBranch getting branches %s'%e


    try:
        actioned = sfb.actionBApprovals(collect, actionNeeded, st)
        if len(actioned) > 0:
            print '  Updated Branch Approvals for branch %s' % branch
        else:
            print '  No change to Branch Approvals for branch %s' % branch
    except Exception,e:
        print 'Error: checkBranch actioning approvals %s'%e

#    try:
#        changed  = sfb.fixBranches(collect,st)
#        print ' Checked status and got: %s'%changed
#        update = incrementCRV_SCM_QOR_Recycle_Count(pass task branch)
#    except Exception, e:
#        print 'Error: checkBranch fixing branch %s'%e

    return

##################################################################################################
#  Commandline management methods.  Minimal logic, just command parm processing
##################################################################################################
def usage(cmd='', err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to scan latest Task Branch (TB) on SalesForce.\n'
    m += ' '
    m += '    walkSF -c walk -s4.1 \n  (walk sForce and enforce approval workflow)'      
    m += '      or\n'
    m += '    walkSF -c toscm -s4.1 -b<branch_Name> (create new SCM token)\n'       # make new token
    m += '      or\n'
    m += '    walkSF -c lsba -s4.1     (list all approvals) \n'       # make new token
    m += '      or\n'
    m += '    walkSF -cteambranchset -stalus1.0 -bsome_task_branch -xnew_status \n'       # make new token
    return m

def main_CL():
    """ Command line parsing and and defaults methods
    """
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-c", "--cmd",   dest="cmd",   default="walk",     help="Command type to use.")
    parser.add_option("-p", "--parm",  dest="parm",  default="",         help="Command parms.")
    parser.add_option("-x", "--parm2", dest="parm2", default="",         help="Command parms 2.")
    parser.add_option("-s", "--cs",    dest="cs",    default="",        help="Code Stream of Branch")
    parser.add_option("-b", "--br",    dest="br",    default="",         help="Branch Label")
    parser.add_option("-f", "--path",  dest="path",  default="./details.txt", help="Path to details file.")
    parser.add_option("-z", "--trace", dest="trace", default="soap.out", help="SOAP output trace file.")
    parser.add_option("-d", "--debug", dest='debug', action="count",     help="The debug level, use multiple to get more.")
    parser.add_option("-i", "--cycle", dest='cycle', default="",     help="Cycle counter flag (optional). Set to True or False")

    (options, args) = parser.parse_args()
#    print options
#    print args

    if options.debug > 1:
        print ' cmd  %s, parms  %s, stream %s' %(options.cmd, options.parm, options.cs)
        print ' path   %s, trace  %s, debug  %s' %(options.path,options.trace ,options.debug)
        print ' args:  %s' %args
    else:
        options.debug = 0

    if len(args) > 0: 
        db = options.debug
        st = time.time()
        parm = options.parm
        query = args[1:]
        if options.cs in [None,'']: stream = None
        else: stream = options.cs

        if options.cmd in ['check']:
            if options.br in [None,'']: 
                print '%s' %('\tYou must provide a least a branch label!')
                sys.exit()
            else: branch = options.br
            if options.cs in [None,'']: stream = None
            else: stream = options.cs
            checkCL(branch, stream, db, st)
            
        elif options.cmd in ['teambranchset']:
            if options.br in [None,'']: 
                print 'teambranchset:\tYou must provide a valid branch label!'
                sys.exit()
            branch = options.br
            if options.cs in [None,'']:
                print 'teambranchset:\tYou must provide a valid stream!'
                sys.exit()
            else: stream = options.cs
            if options.parm2 in [None,'']:
                print 'teambranchset:\tYou must provide a valid new status!'
                sys.exit()
            else: newstatus = options.parm2
            if options.cycle in [None,'']:
                setcyclecount = 'False'
            else: setcyclecount = 'True'
            teambranchset(branch, stream, db, st, newstatus, setcyclecount)

        elif options.cmd in ['walk','sfwalk']:
            if options.parm in [None,'',0]:
                secsAgo = 60*60*2
            else:
                secsAgo = int(options.parm)
            walkSFCL(secsAgo, options)

        elif options.cmd in ['walkact','walkactions']:
            act = 'approve'
            if options.br in ['Reject','reject']:
                act = 'reject'
            role = 'mgr'
            if options.parm2 in ['part','mgr','pe','team','ae','scm','autoae']:
                role = options.parm2
                
            walkSFQueryCL(role, options, st)

        #Cv production run every 15 min to find secsago branches and fix
        elif options.cmd in ['walkfix']:
            if options.parm in [None,'',0]:
                secsAgo = 60*60*4
            else:
                secsAgo = int(options.parm)
            walkSFCheckCL(secsAgo, options)

        elif options.cmd in ['toscm','submitscm']:
            if options.br in [None,'']: 
                print '%s' %('\tYou must provide a least a branch label!')
                sys.exit()
            branch = options.br
            submitToSCMCL(branch, stream, query, options)
    
        elif options.cmd in ['lsba','listapprovals']:
            try: num = int(query)
            except: num = 2000
            getALLBranchApprovals(num, options)
        
        #CV for testing Branch Timestamps, not for production
        elif options.cmd in ['setStamp']:
            branch = options.br
	    db = options.debug
	    status = query = args[:5]
	    ts = options.parm
	    setTBFixStamp(branch, stream, status, ts, db)
	    
        #CV  not used as of Nov, 2004 
        elif options.cmd in ['fix']:
            fixCL(branch, stream, query, options, st)
            
        elif options.cmd in ['fix']:
            parm = options.parm
            fixTBCL(options, parm)
            
        else:
            doSomething('search', query, options.parm, options)
            print 'doing nothing yet, I can do it twice if you like'
        print '\nTook a total of %3.2f secs -^' %(time.time()-st)
    else:
        print '%s' %usage(options.cmd)

if __name__ == "__main__":
    main_CL()
