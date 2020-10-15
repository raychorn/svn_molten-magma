""" Business Logic specific to MOD management with  migration
    to the new Task Branch customer object
    - Task Branch (TB) is a sForce representation of a code branch in Clearcase
    - TB is displayed as a contaiber object with a list of:
       - Branch Approvals - Developer Accept, Manager Approve, PE Approve, AE accept, Closed
       - Branch CR Links - link objects to customer oriented CRs with mirroroed CR Status

           Chip Vanek, Sept 7th, 2004
"""
import sys, time, os
import grp, pprint
import StringIO, getopt
import copy, re
import pprint
import traceback
from types import ListType, TupleType, DictType, DictionaryType
from optparse import OptionParser
from sfMagma import *
from sfTaskBranch import *   # get SFTaskBranch & SFTaskBranchTool
from sfUtil import *
from sfTeamBranch import SFTeamBranch   # get SFTeamBranch
from sop import sfEntities, SFEntitiesMixin, SFUtilityMixin, SFTestMixin
from sop import ccBranches, opBranches, sfBranches, sfEntities, SFEntitiesMixin, SFUtilityMixin, SFTestMixin, BasicCacheMixin

from walkSFEntity import SFTaskBranchWalk

from sfUser import SFUserTool
from sfNote import *
from sfConstant import *
import tokenFile
from emailTransMap import emailTransMap


class SFMOD2TaskBranch(SFTaskBranch):
    """ This is a composite object that represents the MOD oriented methods
        in a TaskBranch sForce object and related Branch Approval & Branch 
        CR objects as one entity
    """
    branchType = 'task'
    modList = []
    loadFromSF = False


    def setModMigration(self, modId, tbId, data={}, id=''):
        """ update (or create) the temporary Mod Migration object """
        if data in [None,'',{}]:
            data = self.getData('Mod_Migration__c',modId)
        #print 'setMODMigration:%s\n'%data
        
        data['MOD_URL__c'] = 'https://na1.salesforce.com/%s'%modId
        if id == '':
            data['Task_Branch__c'] = tbId
            res = self.sfb.create('Mod_Migration__c',data)
            mode = 'Created'
        else:
            data['Id'] = id
            res = self.sfb.update('Mod_Migration__c',data)
            mode = 'Updated'
        if res in self.badInfoList:
            return ''
        id = res[0]
        data['Id'] = id
        self.setData({'Mod_Migration__c':data})
        if self.debug >0: self.sfb.setLog('%s Mod_Migration, %s Status:%s  branch:%s'%(mode,data.get('Name'), data.get('MOD_Status__c'),data.get('Developer__c')),'info')
        return id

        
    ######################################################################
    #  MOD specific Methods, analogous methods are includes above what
    #  do not rely on MODs
    ######################################################################

    def getModData(self, branchLabel, stream='4', overwrite=True, show=True):
        """ Load data from all (branchlabel/codestream) MODs into object data """
        modList = self.sfb.getMODs(branchLabel, stream)
        if show: self.showData(modList, 'Task')
        self.modList = modList
        return modList

    def getRightPriority(self, modPrior, priority):
        """ use passed modPriority to potentially updated
            final priority"""
        modPrior = modPrior.lower()
        if modPrior.find('expedite') != -1: 
            priority = 'expedite'
        elif modPrior.find('high') != -1:     
            if priority not in ['expedite']:
                priority = 'high'
        elif modPrior.find('normal') != -1:   
            if priority not in ['expedite','high']:
                priority = 'medium'
        elif modPrior.find('medium') != -1:   
            if priority not in ['expedite','high']:
                priority = 'medium'
        elif modPrior.find('low') != -1:      
            if priority not in ['expedite','high','medium']:
                priority = 'low'
        return priority
            

    def loadBranchFromMODs(self, branch, stream, team='', label=''):
        """ update or create a Task Branch object and load elements from old MOD
            - MOD.developer    -> TB.Appr(approver, status=accepted, role=developer, data=MOD.create)
        """
        self.branch = branch
        self.stream = stream
        tbData = self.getSFData(branch, stream, show=False)
        modList = self.getModData(branch, stream, show=False)
        if len(modList) == 0:
            self.sfb.setLog('%s %s No MODs found, skipping load'%(branch,stream),'info')
            return 
        tbInfo = tbData.get('Task_Branch__c',{})       # dictionary of SF info or {} # change to self.getData(entity)
        if tbInfo in [None,{}]:
            tbId = self.setTaskBranch(id='', branch=branch, stream=stream)
            tbOwnerId = ''
        else:
            tbId = tbInfo.get('Id','')
            tbOwnerId = tbInfo.get('OwnerId','')
        mmList = tbData.get('Mod_Migration__c',[])   # change to self.getData(entity)
        
        self.baRoleMap = self.setBaRoleMap()
        numCRs = []
        modNum = 0
        total_char_lost = 0
        modDescMap = {}
        print '    ->Loading %s MODs into TB %s'%(len(modList),branch)
        self.sfb.setLog('%s %s Loading %s MODs '%(branch,stream,len(modList)),'info')
        priority = 'low'

        for MOD in modList:
            modNum += 1
            if modNum == 1:
                self.setTBFromMod(MOD)
            modId   = self.sfb.getId18(MOD.get('Id'))
            contId  = MOD.get('WhoId')           # populated from CR and not reliable
            ownerId = MOD.get('OwnerId')         # could be dev, mgr, pe, or ae
            crId    = MOD.get('WhatId')          # The CR sfId
            modStatus = MOD.get('Status')        # used to determine role of ownerId
            modRisk   = MOD.get('Risk__c')
            modSubject = MOD.get('Subject')
            modPrior   = MOD.get('Priority','')
            priority = self.getRightPriority(modPrior, priority)
            
            devEmail = MOD.get('Developer__c')
            msg = ' %s Status: %s dev:%s'%(modSubject, modStatus, devEmail)
            self.sfb.setLog(' %s:MOD %s %s %s'%(modNum,stream,branch,msg),'info')
            
            crInfo = self.sfb.getCrById(crId)
            component = crInfo.get('Component__c','')
            crNum = '%s'%int(crInfo.get('CaseNumber',0))
            crStatus = crInfo.get('Status')
            if crNum not in numCRs: numCRs.append(crNum)
            msg = 'cr: %s comp:%s status:%s'%(crNum, component, crStatus)
            self.sfb.setLog(' %s:MOD %s %s %s'%(modNum,stream,branch,msg),'info')

            aeId = self.sfb.getCrOriginator(crInfo)       #
            devInfo  = self.sfb.getUserByEmail(devEmail)  #could be {}
            devId    = devInfo.get('Id','')
            if devId == '':
                # can't get valid devId from the MOD, use the owner of the TB (may be '')
                devId = tbOwnerId
            
            mgrInfo  = self.sfb.getMgrByID(devId)
            mgrId    = mgrInfo.get('Id','')
            peId = self.sfb.getPEIdByComp(component)
            devName = '%s %s id:%s'%(devInfo.get('FirstName',''),devInfo.get('LastName',''), devId)
            mgrName = '%s %s id:%s'%(mgrInfo.get('FirstName'),mgrInfo.get('LastName'), mgrId)
            msg = 'dev:%s mgr:%s pe:%s ae:%s'%(devName, mgrName, peId, aeId)
            self.sfb.setLog(' %s:MOD %s %s %s'%(modNum,stream,branch,msg),'info')
            
            actionIds = [devId, mgrId, peId, aeId]
            done = self.setTBApprovalsFromMOD(tbId, crNum, component, MOD, actionIds, branch, stream)
            
            modDesc = MOD.get('Description','')
            modDescMap[crNum] = modDesc
            len_desc = len(modDesc)
            total_char_lost += len_desc
            
            foundClId = ''
            clDataList = self.getData('Branch_CR_Link__c')
            for clInfo in clDataList:
                if clInfo.get('Case__c','') == crId: 
                    foundClId = clInfo.get('Id')
            name = 'CR Link for stream %s'%(stream)
            data = {'Name': name,'Case__c': crId,'CR_Status__c': crStatus, 'Branch_Status__c':modStatus, 'CR_Num__c':crNum
                   ,'Component__c': component, 'Details__c':modDesc[:255], 'attNum__c':len_desc, 'Stream__c':stream}
            clId = self.setBranchCRLink(tbId, id=foundClId, data=data)
            if foundClId == '': msg = 'cr:%s ADDED crid:%s'%(crNum, crId)
            else:               msg = 'cr:%s Updated crid:%s'%(crNum, crId)
            self.sfb.setLog(' %s:MOD %s %s %s'%(modNum,stream,branch,msg),'info')
            
            foundId = ''
            for mmInfo in mmList:
                if mmInfo.get('MOD_Id__c','') == modId: 
                    foundId = mmInfo.get('Id')
            data = {'Name': modSubject,'CR__c': crId,'MOD_Id__c': modId,'Developer__c': devEmail
                   ,'Mgr_Approval__c':MOD.get('EngMgrApproval__c',''), 'PE_Approval__c':MOD.get('PEApproval__c','')
                   ,'MOD_Status__c': modStatus, 'MOD_Risk__c': modRisk  ,'Owner__c': ownerId
                   , 'Desc__c': modDesc, 'attNum__c':len_desc
                   ,'Status__c': 'Trial Load', 'MOD_Priority__c':MOD.get('Priority','') }
            done = self.setModMigration( modId, tbId, data, id=foundId)

        branchDescr = buildBranchDescr(modDescMap)

        msg = 'Finished update of %s in %s with data from %s MODs'%(branch,stream,len(modList))
        self.sfb.setLog('%s'%(msg),'info')
        baList = self.getData('Branch_Approval__c')

        tbUpdate = {}
        tbUpdate['Team_Branch__c'] = team
        tbUpdate['Num_CRs__c'] = len(numCRs)
        tbUpdate['Att_Chars__c'] = total_char_lost
        tbUpdate['Branch_Priority__c'] = priority

        if len(branchDescr):
            tbUpdate['Details__c'] = branchDescr[:255]
            if len(branchDescr) > 255:
                # insert a note.
                noteTitle = "Branch Details"
                nt = SFNoteTool()
                note = nt.findNote(tbId, noteTitle)
                if note is None:
                    # create new Branch Details note
                    noteId = nt.createNote(tbId, noteTitle, branchDescr)
                else:
                    # update existing Branch Details note
                    noteInfo = note.getData(NOTE_OBJ)
                    noteInfo['Body'] = branchDescr
                    note.updateSF()
                    pass
                pass
            pass
            
        #self.setData({'Task_Branch__c': tbUpdate})  # not needed with change to taskBranch as passedOnly
        tbId = self.setTaskBranch(tbId, branch=branch, stream=stream, data=tbUpdate)
        self.loadFromSF = True
            

    def getTBStatusFromMODs(self):
        """ Get the percentage map of MOD status
            This involved a complete query of prior MOD information
        """
        if self.loadFromSF: tbData = self.getData()
        else:               tbData = self.getSFData( self.branch, self.stream, show=False)
        mmList = tbData.get('Mod_Migration__c')
        stat = {}
        numMulti = 0
        if len(mmList) >0:
            # load map of existing ModMigrations as {'status_name':{'order':24, 'num':3}}
            for mm in mmList:
                mmStatus = mm.get('MOD_Status__c','')
                mmStatMap = self.sfb.getStatMap(mmStatus)
                order = mmStatMap.get('order',100.0)
                num = mmStatMap.get('num',0.0) + 1.0
                #print 'MOD Status %s order:%s num:%s' %(mmStatus,order,num)
                stat[mmStatus] = {'order':order, 'num':num}
            if len(stat.keys()) == 1:           # simple case of only one status
                status = stat.keys()[0]
                return True, status
            else:
                min = 100           # smallest order number
                max = 0             # largest order number
                major = 0.0
                minor = 1.0
                statRatio = {}
                for s, info in stat.items():
                    order = info['order']
                    if order > max: max = order
                    if order < min: min = order
                    ratio = info['num']/len(mmList)
                    if ratio > major: major = ratio
                    if ratio < minor: minor = ratio
                    statRatio[s] = {'ratio':ratio, 'order':order}
                maxStatus = ''
                minStatus = ''
                for s, info in statRatio.items():
                    if info['ratio'] == minor:
                        if info['order'] <= 53.9: minStatus = s
                        else:   minStatus = 'Merged - Testing by Originator'
                    if info['ratio'] == major: 
                        if info['order'] <= 53.9: maxStatus = s
                        else:   maxStatus = 'Merged - Testing by Originator'
                if minStatus == maxStatus:
                    return True, maxStatus                            # majority of the MODs are in minimal status
                
                # need to use a better combination of major percentage, ordinal, and     
                if minStatus != maxStatus and statRatio[maxStatus]['ratio'] > 70:    
                    msg = 'getTBStatusFromMODs: %25s max percent %3.2d status was %s, minor status was %s' %(self.branch, max, maxStatus, minStatus)
                    self.sfb.setLog(msg,'warn')
                    return False, minStatus                            # should never happen
                if minStatus != maxStatus:    
                    msg = 'getTBStatusFromMODs: %25s max percent %3.2d status was %s, minor status was %s' %(self.branch, max, maxStatus, minStatus)
                    self.sfb.setLog(msg,'warn')
                    return False, minStatus                            # Warn and prefeer earliest status 
                msg = 'getTBStatusFromMODs: %25s max percent %3.2d status was %s, minor status was %s' %(self.branch, max, maxStatus, minStatus)
                self.sfb.setLog(msg,'error')
        else:
            msg =  'getTBStatusFromMODs: %25s no MODs found'%self.branch
            self.sfb.setLog(msg,'warn')
            #print 'Debug mmList not found tbData:%s'%tbData
        return False, ''



    def setTBApprovalsFromMOD(self, tbId, crNum, component, MOD, actionIds, branch='', stream=''):
        """ update existing or create new Branch Approval objects using MOD info 
            need tbId, crNum, MOD, list of actionIDs (dev, mgr, pe, ae), branch, stream, and
            baRoleMap = {'dev':{'ids':[],'sf:''},'mgr':{'ids':[],'sf:''}, 'pe':{'ids':[],'sf:''}, 'ae':{'ids':[],'sf:''}}
                baRoleMap used to see what branch approvals to add/update
        """
        if branch in [None,'']: branch = self.branch
        if stream in [None,'']: stream = self.stream
        devDate = MOD.get('CreatedDate')
        date = MOD.get('LastModifiedDate')
        devId, mgrId, peId, aeId = actionIds
        modStatus = MOD.get('Status','')
        if self.debug > 1: print '  MOD last:%s %s'%(date,modStatus)
        
        statOrder = self.sfb.getStatMap(modStatus).get('order',0)

        for role in ['dev','mgr','pe','ae','scm']:    # extend for scm ??
            rolePick = self.baRoleMap.get(role).get('sf')
            comp = ''
            action = ''
            stat = 'Action Pending'
            if role == 'dev':
                apprId = devId
                order = 3.0
                date = devDate
                if statOrder > 32.9: stat = 'Submitted'
                else:              stat = 'Fixing'
            elif role == 'mgr':
                apprId = mgrId
                order = 3.4
                action = MOD.get('EngMgrApproval__c','')
                stat = action
                if action not in ['Approved','Rejected']:    # wipe out ,'Not Applicable','Not Required'
                    action = ''
                    stat = 'Pending Submission'
                if action in ['Approved']:    action = 'Approve'
                if action in ['Rejected']:    action = 'Reject'
            elif role == 'pe':
                apprId = peId
                order = 3.5
                action = MOD.get('PEApproval__c','Pending Submission')
                stat = action
                if action not in ['Approved','Rejected']:    # wipe out ,'Not Applicable','Not Required'
                    action = ''
                    stat = 'Pending Submission'
                if action in ['Approved']:    action = 'Approve'
                if action in ['Rejected']:    action = 'Reject'
                comp = component
            elif role == 'scm':
                if statOrder > 37.9 and statOrder < 53.9:
                    apprId = devId
                    order = statOrder/10
                    stat = modStatus
                else:
                    continue
            elif role == 'ae':
                apprId = aeId
                order = 6.0
                if statOrder < 54:
                    stat = 'Pending Merged Fix'
                elif statOrder < 69:
                    stat = 'Merged - Testing by Originator'
                else:
                    stat = 'Merged - Tested by Originator'
                    if statOrder == 71.0:
                        action = 'Approved'
                    elif statOrder >= 73.0:
                        action = 'Rejected'
                        
                comp = component
                crNums = [crNum]
            else:
                continue

            if self.debug>2: print 'Checking for %s approver id:%s with status:%s' %(rolePick,apprId,stat)
            baId = ''
            crNums = []
            
            if apprId in self.baRoleMap.get(role).get('ids') and role != 'ae':       
                # Check to see if there is an approval with this role already
                baId = self.getBaId(apprId, role)       # get the ID of the approval record
                crNums = uniq(self.getBranchApprovalCRList(baId))
                if self.debug>0: print 'Found Existing %s approver with status:%s crs:%s id:%s ' %(rolePick,stat,crNums,apprId)

            # Gotta check for ae (cr originator) role as well
            elif apprId in self.baRoleMap.get(role).get('ids') and role == 'ae' and \
                     self.baRoleMap.get(role).get('crInfo').has_key(crNum):
                baId = self.baRoleMap.get(role).get('crInfo').get(crNum)
                crNums = uniq(self.getBranchApprovalCRList(baId))
                if self.debug>0: print 'Found Existing %s approver with status:%s crs:%s id:%s ' %(rolePick,stat,crNums,apprId)
                print 'Found Existing %s approver with status:%s crs:%s id:%s ' %(rolePick,stat,crNums,apprId)
                
            if not crNum in crNums:
                crNums.append(crNum)

            crStr = ','.join(crNums)
            if role == 'dev':
                tbaSubject = '%s %s in %s for %s CRs'%(stat, branch, stream, len(crNums))
                instuct = 'Please use the shell script submitbranch rather than changing the Approve Field above.'
                if baId in ['',None] and len(crStr) == 0:
                    # skip creation of a dev ba having no crs.
                    continue
                
            elif role == 'mgr':
                tbaSubject = 'Approval for %s in %s'%(branch, stream)
                instuct = 'Please edit this item and choose Approve or Reject from the Approve Field above.'
            elif role == 'pe':
                tbaSubject = 'Approval %s in %s for %s CRs'%(branch, stream, len(crNums))
                instuct = 'Since you are the PE for %s you are asked to review that the CRs below are fixed in this branch, then choose Approve or Reject from the Approve Field above.'%component
            elif role == 'ae':
                tbaSubject = 'Accept Fix for %s in %s in %s '%(branch, stream, crStr )
                instuct = 'Please test that this branch fixes the problem detailed in the CRs below and approve this item by changing the Approve Field above to Approve'
            
            if len(tbaSubject) > 80:
                print 'WARN: truncating Branch approval subject to 80 char was\n  %s'%tbaSubject
                tbaSubject = tbaSubject[:80]
            
            data ={'Name':tbaSubject,
                   'Order__c': order,
                   'Approval_Role__c': rolePick,
                   'OwnerId': apprId,
                   'Approve__c': action,
                   'Component__c':comp,
                   'Instructions__c': instuct,
                   'Stream__c':stream,
                   'Branch__c':branch}
            
            if branch in [None,'']:
                print 'ERROR: Updating BranchApproval with no Branch value using %s'%data
            sfId = self.setBranchApproval( baId, tbId=tbId, status=stat, date=date, data=data, crNums=crNums)
            if sfId in badInfoList:
                self.sfb.setLog('setBA:%s Updating From MOD %s to %s ret:%s in %s'%(self.branch, rolePick, stat, sfId, crNums),'error')
                continue
            self.baRoleMap[role]['ids'].append(apprId)
            self.baRoleMap[role]['sfids'].append(sfId)
            

    def getOwnerRoleByModStatus(self, status, ownerId, devId, mgrId, peId, aeId):
        """ get the Owner role based on the MOD status 
            return one of ['dev','mgr','pe','ae','admin']
        """
        if status in ['Fixing']:
            role = 'dev'
        elif status in ['Approving by Manager']:
            role = 'mgr'
        elif status in ['Approving by PE']:
            role = 'pe'
        elif status in ['Merged - Testing by Originator']:
            role = 'ae'
        elif status[:6] == 'Closed':
            role = 'dev'
        else:
            role = 'dev'

        if role == 'mgr' and ownerId != mgrId:
            print 'WARN: existing owner NOT as expected mgrId:%s ownerId:%s'%(mgrId,ownerId)
        elif role == 'pe' and ownerId != peId:
            print 'WARN: existing owner NOT as expected peId:%s ownerId:%s'%(peId,ownerId)
        elif role == 'ae' and ownerId != aeId:
            print 'WARN: existing owner NOT as expected aeId:%s ownerId:%s'%(aeId,ownerId)
        elif role == 'dev' and ownerId != devId:
            print 'WARN: existing owner NOT as expected devId:%s ownerId:%s'%(devId,ownerId)
        elif ownerId not in [devId,mgrId,peId,aeId]:
            idL = 'd:%s m:%s p:%s a:%s' %(devId,mgrId,peId,aeId)
            print 'WARN: could not find owner in valid owner list, ownerID:%s list:%s'%(ownerId,idL)
        return role
        

    def setTBFromMod(self, MOD, flags={'overwriteStatus':'yes'}):
        """  Update the TaskBranch data in this object with information from the passed in MOD
             - MOD.status       -> TB.status       ( use MOD.status to determin approvals to create)
             - MOD.owner        -> TB.owner ??? this needs to be triple checked
             - MOD.branch_label -> TB.branch_label TB.branch
             - MOD.teambranch   -> TB.team_branch
             - MOD.priority     -> TB.priority
             - MOD.codestream   -> TB.codestream
             - MOD.Mantle time  -> TB.Merge Data/time
             - MOD.risk         -> TB.risk & TB.command_change
             - MOD.comments     -> TB.Detail/detail2/detail3 + bit bucket for 2635 chars
        """
        
        tbInfo = self.getData('Task_Branch__c')
        if type(tbInfo) in seqTypes: tbInfo = tbInfo[0]
        
        #print 'setTBFromMod: %s MOD is:%s'%(type(MOD),MOD)
        subject = MOD.get('Subject')
        status = MOD.get('Status','')
        if status != '' and tbInfo.get('Status','') != status:
            if flags.get('overwriteStatus','') != '':
                tbInfo['Branch_Status__c'] = status
            else:
                print 'WARN: found new status: %s for MOD:%s' %(status,subject)
        
        # only set OwnerId if it's not already set.
        if tbInfo.get('OwnerId', None) in BAD_INFO_LIST:
            ownerId = MOD.get('OwnerId','')
            if self.debug >1: print 'MOD.Status of %s for %s' %(status, subject)

            devEmail = MOD.get('Developer__c')
            ownerInfo = self.sfb.getUserByEmail(devEmail)
            ownerId = ownerInfo.get('Id') 
            if self.debug >0: print 'TB Owner, %s %s from %s as %s MOD:%s'%(ownerInfo.get('FirstName'),ownerInfo.get('LastName'),devEmail,ownerId,subject)
            tbInfo['OwnerId'] = ownerId
        
        value = MOD.get('BranchLabel__c','')
        if value != '' and tbInfo.get('Branch__c','') != value:
            tbInfo['Branch__c'] = value
        
        value = MOD.get('TeamBranch__c','')
        if value != '' and tbInfo.get('Team_Branch__c','') != value:
            tbInfo['Team_Branch__c'] = value

        value = MOD.get('Priority','')
        if value != '' and tbInfo.get('Branch_Priority__c','') != value:
            tbInfo['Branch_Priority__c'] = value

        value = MOD.get('CodeStream__c','')
        if value != '' and tbInfo.get('Code_Stream__c','') != value:
            tbInfo['Code_Stream__c'] = value
        
        value = MOD.get('MantleTimeStamp__c','')
        if value != '':
            mts = self.sfb.checkDate(value, 'setTBFromMod')
            tbmts = tbInfo.get('Merged_Date_Time__c','')
            print 'FOUND MTS or %s converted to %s TB:%s'%(value,mts, tbmts)
            if mts != '' and tbmts != mts:
                tbInfo['Merged_Date_Time__c'] = mts

        risk = MOD.get('Risk__c','')
        cmdChg = False
        highRisk = False
        if risk in ['Med with Command Change']:    cmdChg = True
        elif risk in ['High (No Command Change)']: highRisk = True
        elif risk in ['High with Command Change']:
            highRisk = True
            cmdChg = True
        elif risk in ['Low']: pass
        else:
            print 'Risk not set for %s, setting to Low'%subject
            
        if self.debug>1: print 'RISK MOD:%s cmdChg:%s highRisk:%s'%(risk,cmdChg,highRisk)
            
        if tbInfo.get('Command_Change__c','') != cmdChg:
            tbInfo['Command_Change__c'] = cmdChg
        if tbInfo.get('High_Risk__c','') != highRisk:
            tbInfo['High_Risk__c'] = highRisk
        
        self.setData({'Task_Branch__c':tbInfo})  # why?

    ##################################################################################################
    #  Utilities ?
    ##################################################################################################

        
            

class SFMOD2TaskBranchTool(SFTaskBranchTool):
    """ This is a subclass of the SFEntityTool to hold any Branch specific
        SOQL query methods and entity linking action methods
    """
    csNextGeneric = '4'
    logname = 'sf.walkMOD'
    debug = 3   # CV Sept 7th, 2004 remove this??

    ##################################################################################################
    #  MOD migration methods
    ##################################################################################################
    def getMODs(self, branch, stream):
        """ get a list of MODs for the given branch and code stream
            return list of MODInfo or []
        """
        result = []
        
        where = [['BranchLabel__c','=',branch]
                ,'and',['CodeStream__c','=',stream]
                ,'and',['RecordTypeId','=','01230000000002vAAA']]
        #where = self.getSQOLWhereShortcut('br_mod', branch)         # NOTE this does not limit by Stream!!!
        res = self.query('Task', where, sc='fields')
        if res in badInfoList:
            # what to do?  munge branch string, eliminate stream?  Log erro for now
            self.setLog('getMODs: None found for %s in %s '%(branch, stream),'error')
            return result
        print '    Found %s MOD for %s in %s'%(len(res), branch, stream)
        return res
    
    def getUpdatedMODs(self, secsAgo=60*60*24, show=False):
        """ get the MODs modified in the last secsAgo"""
        collect = {}
        fromSecs = time.time()-secsAgo
        dateStr = self.getAsDateTimeStr(fromSecs)
        where = [['LastModifiedDate','>',dateStr]
                 ,'and',['RecordTypeId','=','01230000000002vAAA']
                ]
        queryList = self.query('Task', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'getUpdatedMODs Result: NO Tasks Found within the last %s secs'%secsAgo
            return collect
        for info in queryList:
            modId = info.get('Id','')
            branch = info.get('BranchLabel__c','')
            if show:
                print '%30s at %s'%(branch,modId)
            bal = collect.get(branch,[])
            bal.append(info)
            collect[branch] = bal
        # now collect is a dictionary with key of tbId and list of baInfo
        msg = 'getUpdatedMODs: found %s branches in %s MODs'%(len(collect),len(queryList))
        self.setLog(msg,'info')
        print msg
        return collect
        
    

    def getMODsByCR(self, CR, filterCS=['all']):        
        """ get MOD in a CR filtering by filterCS   
            Called from walkSCM
        """
        crID = CR.get('Id')
        crNum = CR.get('CaseNumber')
        where = [['whatID','=',crID],'and',['RecordTypeId','=','01230000000002vAAA']]
        MODs = self.query('Task', where)
        if MODs in badInfoList:
            self.setLog('getMODsByCR No MODs found for cr:%s'%(crNum),'info')
            return []
        self.setLog('getMODsByCR found %s MODS cr:%s'%(len(MODs), crNum),'info')
        results = []
        branches = []
        streams = []

        for MOD in MODs:
            brMOD  = MOD.get('BranchLabel__c')
            tbrMOD = MOD.get('TeamBranch__c')
            brs = []
            if brMOD is not None:
                if brMOD.find(',') != -1: # we have a psuedo list of branches
                    brList = brMOD.split(',')
                    if brList[0] not in [None,'']:
                        brs = brList
                    else:
                        brs = brList[1:]
                    branches.extend(brs)
                else:
                    brs.append(brMOD)
                    branches.append(brMOD)
            if tbrMOD is not None:
                branches.append(tbrMOD)
                brs.append(tbrMOD)
                
            csMOD = MOD.get('CodeStream__c')
            streams.append(csMOD)
            if csMOD in filterCS:
                results.append(MOD)
            elif 'all' in filterCS:
                results.append(MOD)
            elif csMOD == self.csNextGeneric:
                if genericInBuild == True:
                    msg = 'Found %s MOD to potentially include into %s, cr:%s %s' %(self.csNextGeneric, filterCS, crNum, branches )
                        
        if len(results) == 0:
            self.setLog('No MODs in cs:%s CR:%s cs:%s brs:%s'%(filterCS, crNum, streams, branches),'warn')
        return results

    

##################################################################################################
#  Logic methods called from command line 
##################################################################################################
def loadBranch(branch, stream, parm, options):
    print 'Loading Task Branch from MOD for the branch %s in code stream %s' %(branch, stream) 
    tf = file(options.trace, 'w+')
    sfb = SFTaskBranchTool(dlog=tf, debug=options.debug,logname='loadBR')
    brObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
    info = brObj.loadBranchFromMODs(branch, stream)
    print '%s CRs, %s BAs, %s, %s, %s'%info
    results = brObj.data
    #pprint.pprint( results)


def updateBranchFromMODs(secsAgo, options, max='all', skip=0):
    if max in ['all']: max = 10000
    else:              max = int(max)
    try: skip = int(skip)
    except: skip = 0

    sfb = SFMOD2TaskBranchTool(debug=options.debug,logname='sf.walkMOD')
    
    try:
        lockHandle = cronLock('walkMOD.lock')
    except Exception, e:
        msg = "Could not acquire reentrancy lock. Assume another instance is running. EXITING."
        sfb.setLog(msg, 'warn')
        print msg
        sys.exit()

    print 'Updating %s branches skipping first %s changes in the last %s min' %(max,skip,secsAgo/60)
    collect = sfb.getUpdatedMODs(secsAgo=secsAgo, show=True)
    if len(collect) < 1:
        print 'No MODs were found to have changed in the last %s min'%(secsAgo/60)
    else:
        start = 0
        num = 0
        print 'Skipping the first %s rows, then processing %s rows'%(skip,max)
        for branch, MODs in collect.items():
            for MOD in MODs:
               stream = MOD.get('CodeStream__c')
               team   = MOD.get('TeamBranch__c')
            if stream not in ['4','4.0','4.1','4.2']:
                print 'Skipping Branch %s, stream was %s' %(branch,stream)
                continue
            num += 1
            if num < skip: continue
            if num > max+skip: break
            msg = '%s:TB Found branch %s in %s  %s'%(num, branch,stream, team)
            sfb.setLog(msg,'info')
            brObj = SFMOD2TaskBranch(sfTool=sfb,debug=options.debug)
            
            brObj.loadBranchFromMODs(branch, stream, team)
            #inf = brObj.loadBranch(branch, stream, team=team)             
            #foundOK, status = brObj.getTBStatusFromMODs()          # turn off
            foundOK, status = False, 'Unknown'
            if foundOK:
                updated = brObj.setBranchStatus(status)
                if updated: msg = ' %s:TB %s Updated Status of %s %s' %(num, branch,stream, status)
                else:       msg = ' %s:TB %s Skipped Status Update of %s %s' %(num, branch, stream,status)
                sfb.setLog(msg,'info')
            else:
                msg = ' %s:TB %s Skipping the updating of the status %s' %(num, branch,status)
                sfb.setLog(msg,'info')
            msg = '%s:TB Done updating branch %s in %s from MOD'%(num, branch,stream)
            print msg
            sfb.setLog(msg,'info')
            


def doSomething(method, term, parm, options):
    """  Command line controlled test of a method """
    print 'You called me with method:%s term:%s parm:%s ' %(method, term, parm)
    print 'Hope it was good for you'

##################################################################################################
#  Commandline management methods.  Minimal logic, just command parm processing
##################################################################################################
def usage(err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to get changed MODs and update sForce.\n'
    m += ' '
    m += '    sfMODmanage -cl do         (sync TBs from MODs)\n'
    m += '      or\n'
    m += '    sfTaskBranch -cl -p3600 do (sync MODs update last 3600 secs) \n'
    return m

def main_CL():
    """ Command line parsing and and defaults methods
    """
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-c", "--cmd",   dest="cmd",   default="load",     help="Command type to use.")
    parser.add_option("-p", "--parm",  dest="parm",  default="",         help="Command parms.")
    parser.add_option("-s", "--cs",    dest="cs", default="4",           help="Code Stream of Branch")
    parser.add_option("-t", "--trace", dest="trace", default="soap.out", help="SOAP output trace file.")
    parser.add_option("-d", "--debug", dest='debug', action="count",     help="The debug level, use multiple to get more.")
    (options, args) = parser.parse_args()
    if options.debug > 1:
        print ' cmd    %s' %options.cmd
        print ' parms  %s' %options.parm
        print ' trace  %s' %options.trace
        print ' debug  %s' %options.debug
        print ' args:  %s' %args
    else:
        options.debug = 0
        
    if len(args) > 0: 
        st = time.time()
        parm = options.parm
        query = args[0:]
        branch = args[0]
        if options.cmd in ['get','g']:
            doSomething('get', query, options.parm, options)
            
        elif options.cmd in ['load','l']:
            secsAgo = options.parm
            if secsAgo in [None,'',0]: secsAgo = 60*60*24
            else: secsAgo = int(secsAgo)
            skip = 0
            max = 'all' # change to 'all'
            updateBranchFromMODs(secsAgo=secsAgo, options=options, max=max, skip=skip)

        else:
            doSomething('search', query, options.parm, options)
            print 'doing nothing yet, I can do it twice if you like'
            
        print '\nTook a total of %3f secs' %(time.time()-st)
    else:
        print '%s' %usage()

if __name__ == "__main__":
    main_CL()
