"""
Entity object companion for walkSF. This class split out to break
circular dependency cause by sfTeamBranch needing SFTaskBranchWalk and
SFTaskBranchWalk needing 
"""
import sys, time, os
import pprint
import StringIO, getopt
import copy, re
import traceback
from types import ListType, TupleType, DictType, DictionaryType
from optparse import OptionParser, OptionGroup
from sfMagma import *
from sfTaskBranch import *   # get SFTaskBranch & SFTaskBranchTool
from sfUtil import *
from sop import sfEntities, SFEntitiesMixin, SFUtilityMixin, SFTestMixin
from MudflowWrap import MudflowWrap

class SFTaskBranchWalk(SFTaskBranch):
    """ This is a composite object that represents a TaskBranch sForce object
        and related Branch Approval & Branch CR objects as one entity
    """
    tb_obj = 'Task_Branch__c'
    tb_appr = 'Branch_Approval__c'
    cr_link = 'Branch_CR_Link__c'
    modList = []
    loadFromSF = False

    def __init__(self, entity=None, data={}, action=None, sfTool=None, debug=0):
        """  If an active tool object is not passed in then a connection is created.   """
        if entity is None: entity = 'Task_Branch__c'
        SFMagmaEntity.__init__(self, entity, data=data, action=action, sfTool=sfTool, debug=debug)


    ##################################################################################################
    #   Status oriented methods
    ##################################################################################################
    def submitByDev(self, branch, stream, st=0, partData=None):
        """ set status on branch to trigger state change """
        if partData is None or len(partData) == 0:
            status = 'Approving by Manager'
        else:
            status = 'Approving by Partition Reviewer'
            pass
        ld = self.checkLoad(branch, stream, cl=True)
	# ld = [0, 3, u'Fixing', 'blast5_fduru_005', 'blast5', 0]
	# ld = [numCLs,numBAs,status,branch,stream,numBTLs]
	if self.debug>0: print 'Load Status ',ld
	if ld[0] in [None,0,-1]:
	    print '  Please use lncr first'
	    print '  Without a CR there is no documentation of what this fix is about'
	    return -2
        if -1 in ld[:2]: return -1

        num, notify = self.submitAndNotify(status, st, partData=partData)
        if num > 0:
            for baId, info in notify.items():       #notify = {baId:info}
                # info = {'status':status, 'role':role, 'actor':ownerId, 'tbId':tbId}
                if info.get('role','') == 'mgr':
                    msg = 'submitByDev: Changed status to %s and notified %s for role %s'%(status,info.get('actor'),info.get('role'))
                    if self.debug>1:print msg
                    self.sfb.setLog(msg,'info')
                else:
                    msg = 'submitByDev: Expected role "mgr", but changed status to %s and notified %s for role %s'%(status,info.get('actor'),info.get('role'))
                    if self.debug>1:print msg
                    self.sfb.setLog(msg,'error')
                    pass

                continue
            pass
        
        # if we have partition data, we need to see if we can bypass the
        # partition reviewer state if the part BAs were already approved
        if partData is not None:
            num = self.submitByPart(branch, stream)
            pass

        return num
   
    def rejectToDev(self, branch, stream, st=None):
        """ set status on branch to trigger state change """
        status = 'Rejecting'
        ld = self.checkLoad(branch, stream, cl=0)
        if -1 in ld[:2]: return -1
        num, notify = self.submitAndNotify(status, st)
        return num


    def rejectToDevByPart(self, branch, stream, st=None):
        """ set status on branch to trigger state change """
        status = 'Rejected by Partition Reviewer'
        ld = self.checkLoad(branch, stream, cl=0)
        if -1 in ld[:2]: return -1
        num, notify = self.submitAndNotify(status, st)
        return num

    def rejectToDevByMgr(self, branch, stream, st=None):
        """ set status on branch to trigger state change """
        status = 'Rejected by Mgr'
        ld = self.checkLoad(branch, stream, cl=0)
        if -1 in ld[:2]: return -1
        num, notify = self.submitAndNotify(status, st)
        return num

    def rejectToDevByPe(self, branch, stream, st=None):
        """ set status on branch to trigger state change """
        status = 'Rejected by PE'
        ld = self.checkLoad(branch, stream, cl=0)
        if -1 in ld[:2]: return -1
        num, notify = self.submitAndNotify(status, st)
        return num

    def submitByPart(self, branch, stream, st=0):
        """ set status on branch to trigger state change ONLY if all Partition Reviewers
        have approved """
        status = 'Approving by Manager'
        ld = self.checkLoad(branch, stream, cl=True)
        if -1 in ld[:2]: return -1

        # get the BAs on this branch
        baList = self.getData('Branch_Approval__c')
        myBaList = copy.deepcopy(baList)

        ## Find the Part BA owned by script runner (if any) and approve it
        scriptRunnerUid = self.sfb.uid
        scriptConnectUid = self.sfb.connectuid

        for ba in myBaList:
            if ba.get('Approval_Role__c','') == 'Partition Reviewer' and \
                   ba.get('OwnerId') == scriptRunnerUid:
                # Mark this BA as approved.
                baId = ba.get('Id')
                tbId = ba.get('Task_Branch__c')
                data = {'Approve__c':'Approve'}
                self.setBranchApproval(baId, tbId, data=data, date='now',
                                       status='Approved')
                pass
            continue
        
        # now, snap the branch
        self.setBranchStatus()

        ## Check to see if we have all the part approvals necessary

        # get the BAs on this branch (again)
        baList = self.getData('Branch_Approval__c')

        # check that all part BAs are Approved.
        # find just the part BAs
        partBaCount = 0
        partApprovedBaCount = 0
        for ba in baList:
            if ba.get('Approval_Role__c','') == 'Partition Reviewer':
                partBaCount += 1

                if ba.get('Status__c','') == 'Approved':
                    partApprovedBaCount += 1
                    pass
                pass
            continue
        
        num = 0            
        if partBaCount > 0 and partBaCount == partApprovedBaCount:
            # update the tb status now that we're approved
            self.setBranchStatus(status)
            num, notify = self.submitAndNotify(status, st)
            pass

        return num


    def submitByMgr(self, branch, stream, st=None):
        """ set status on branch to trigger state change """
        num = 0
        nextStatus = 'Approving by PE'
        ld = self.checkLoad(branch, stream, cl=True)
        if -1 in ld[:2]: return -1

        # get the BAs on this branch
        baList = self.getData('Branch_Approval__c')
        myBaList = copy.deepcopy(baList)
        
        ## Find the Mgr BA owned by script runner (if any) and approve it
        scriptRunnerUid = self.sfb.uid
        scriptConnectUid = self.sfb.connectuid

        for ba in myBaList:
            if ba.get('Approval_Role__c','') == 'Engineering Manager' and \
                   (ba.get('OwnerId') == scriptRunnerUid or \
                    scriptRunnerUid == scriptConnectUid):
                num, notify = self.submitAndNotify(nextStatus, st)
                pass
            continue

        return num

    def submitByPe(self, branch, stream, st=0):
        """ set status on branch to trigger state change ONLY if all PEs have approved """
        status = 'Approved, pending Branch'
        ld = self.checkLoad(branch, stream, cl=True)
        if -1 in ld[:2]: return -1

        # get the BAs on this branch
        baList = self.getData('Branch_Approval__c')
        myBaList = copy.deepcopy(baList)

        ## Find the PE BA owned by script runner (if any) and approve it
        scriptRunnerUid = self.sfb.uid
        scriptConnectUid = self.sfb.connectuid

        for ba in myBaList:
            if ba.get('Approval_Role__c','') == 'Product Engineer' and \
                   ba.get('OwnerId') == scriptRunnerUid:
                # Mark this BA as approved.
                baId = ba.get('Id')
                tbId = ba.get('Task_Branch__c')
                data = {'Approve__c':'Approve'}                
                self.setBranchApproval(baId, tbId, data=data, date='now', status='Approved')
                
            elif ba.get('Approval_Role__c','') == 'Team Manager':
                # If we notice a Team Mgr BA, the destination status of this
                # branch is as follows.
                status = 'Approved, pending Team Branch'
                
        # now, snap the branch       
        self.setBranchStatus()
       
               

        ## Check to see if we have all the PE approvals necessary

        # get the BAs on this branch (again)
        baList = self.getData('Branch_Approval__c')

        # check that all PE BAs are Approved.
        # find just the PE BAs
        peBaCount = 0
        peApprovedBaCount = 0
        for ba in baList:
            if ba.get('Approval_Role__c','') == 'Product Engineer':
                peBaCount += 1

                if ba.get('Status__c','') == 'Approved':
                    peApprovedBaCount += 1
                    pass
                pass
            continue
        
        num = 0            
        if peBaCount > 0 and peBaCount == peApprovedBaCount:
            # check the submission date against mudflow
            # to see if branch has been changed since then
            try:
                sdt = self.getSubmittedDatetime()
                if sdt is not None:
                    sdtfmt = sdt.strftime('%d-%b-%y.%H:%M')
                    mudflowObj = MudflowWrap.remoteMudflow(branch)
                    if mudflowObj.hasDelta() is True:
                        # mark the field
                        tbData = self.getData('Task_Branch__c')
                        tbUpd = {'Id': tbData.get('Id'),
                                 'Changed_After_Submit__c': True}
                        self.sfb.update('Task_Branch__c', tbUpd)
                        pass
                    pass
            except Exception, e:
                # note failure in log and continue on
                msg = 'Failed to mark branch for changes after submission: %s' \
                      %e
                self.sfb.setLog(msg, 'error')
                pass
                        
                
            # update the tb status now that we're approved
            self.setBranchStatus(status)
            
            if scriptRunnerUid == scriptConnectUid:
                # if we're running as sfscript (unix user), also
                # submit the token
                num, notify = self.submitAndNotify(status, st)
            pass

        return num


    def approveBranch(self, branch, stream, st=0):
        """ decide what approval role the user needs for this 
            branch and do it.
        """
        ld = self.checkLoad(branch, stream, cl=True)
        if -1 in ld[:2]: return -1
        num = 0
        role = self.getNextApprovalRole()   # dev, mgr, pe, scm, ae
        if role == 'dev':   num = self.submitByDev(branch, stream, st)
        elif role == 'part': num = self.submitByPart(branch, stream, st)
        elif role == 'mgr': num = self.submitByMgr(branch, stream, st)
        elif role == 'pe':  num = self.submitByPe(branch, stream, st)
        elif role == 'scm': num = self.submitToSCM(branch, stream, st)
        elif role == 'ae':  num = self.submitToAE(branch, stream, st)
        else: print 'ERROR: approveBranch, getNextApprovalRole returned %s'\
              %role
        return num, role
            

    def submitToSCM(self, branch, stream, st=0):
        """ set status on branch to trigger state change 
             not used, August 6th, 2004
        """
        status = 'Submitted to SCM'
        ld = self.checkLoad(branch, stream, cl=True)
        if -1 in ld[:2]: return -1
        updated = self.postSCMTokenAndNotify()
        num, notify = self.submitAndNotify(status, st)
        return num


    def submitToAE(self, branch, stream, st=0):
        """ set status on branch to trigger state change """
        status = 'Merged'
        ld = self.checkLoad(branch, stream, cl=True)
        if -1 in ld[:2]: return -1
        num, notify = self.submitAndNotify(status, st)
        return num
