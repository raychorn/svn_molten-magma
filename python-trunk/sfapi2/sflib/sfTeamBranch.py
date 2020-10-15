""" Business Logic specific to the Team Branch customer object
    - Team Branch (TmB) is a sForce representation of a collection of Clearcase branches
    - TmB is displayed as a container object with a list of:
       - Branch Approvals - Team Manager Approve, Closed
       - Branch Team Link - link objects to Task Branches with mirrored Task Branch Status
 ToDo:
    - Create methods to support each specific action to call for command line
        - linkTeamBranch    - create a new Branch Team Link in a TmB
        - approveTeamBranch - change status of Team manager Branch Approval from pending -> approved
        - submitTeamBranch  - Submit Team Branch as token to SCM
        
    - Create walkSF methods to move TmB to next step in workflow
    
           Chip Vanek, August 4th, 2004
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
from sfPECheckpoint import SFPEBranch 
from sfTaskBranchStatusMap import *
from sfConstant import *
from walkSFEntity import SFTaskBranchWalk
from sfUtil import *
from sop import sfEntities, SFEntitiesMixin, SFUtilityMixin, SFTestMixin
import tokenFile


class SFTeamBranch(SFTaskBranchWalk):
    """ This is a composite object that represents a TeamBranch sForce object
        and related Branch Approval & Branch CR objects as one entity
    """
    modList = []
    loadFromSF = False
    branchType = 'team'

    #######################################################################
    # Team Branch data management methods
    #######################################################################
    def loadBranch(self, branch, stream):
        return self.loadTeamBranch(branch, stream)
    
    def loadTeamBranch(self, branch, stream):
        """ load the TmB object and set branch to team label """
        #print "Branch name: %s" %branch
        self.branch = branch
        self.stream = stream
        tbData = self.getSFData( branch, stream, show=False)
        #print "TB DATA %s" %tbData
        status = tbData.get('Team_Branch__c').get('Status','')
        numTBs = len(tbData.get('Branch_Team_Link__c'))
        numBAs = len(tbData.get('Branch_Approval__c'))
        info = [numTBs,numBAs,status,branch,stream]
        #print "Task Data: %s" %tbData        
        return info

    def loadBranchById(self, id):
        return self.loadTeamBranchById(id)

    def loadTeamBranchById(self, id):
        """ load the TmB object for given id and set branch to team label """
        tbData = self.getSFDataById(id, show=False)        
        teamBr = tbData.get('Team_Branch__c')
        branch = teamBr.get('Branch__c','')
        stream = teamBr.get('Stream__c')
        status = teamBr.get('Status','')
        numTBs = len(tbData.get('Branch_Team_Link__c'))
        numBAs = len(tbData.get('Branch_Approval__c'))
        self.branch = branch
        self.stream = stream
        info = [numTBs,numBAs,status,branch,stream]
        return info

    def refresh(self):
        """ Refresh the current team branch object """
        info = self.loadBranch(self.branch, self.stream)
        return info
    ## END refresh

    def getSFDataById(self, id, show=True):
        """
        Get team branch object by team branch ID
        """
        where = [['Id', '=', id]]
        res = self.getSFDataCommon(where, show=show)
        return res
    
    def getSFData(self, branch, stream, show=True):
        """
        Get team branch object given a branch name and code stream
        'The Original!' [TM]
        """
        where = [['Branch__c','like',branch]
                ,'and',['Stream__c','=',stream]]
        res = self.getSFDataCommon(where, show=show)
        return res

    def getSFDataCommon(self, where, show=True):
        """
        Common code to support the getSFData methods.

        one call to get all new Team branch object related to a
        ClearCase branch will set data as a list of entity-data pairs
        [('entity', {data})] return this data structure or {}
        """
        res = {'Team_Branch__c':{},
               'Branch_Approval__c':[],
               'Branch_Team_Link__c':[]}
        self.setData(res, reset=True)

        #print 'getSFData with query %s'%where
        queryList = self.sfb.query('Team_Branch__c', where=where, sc='all')
        if queryList in self.badInfoList:
            if self.debug > 0:
                print '    NO Task Branch Found for %s' \
                      %pprint.pformat(where)
            return res
        
        if len(queryList) > 1:
            print 'WARNING: There should be only ONE TmB object for %s'\
                  %pprint.pformat(where)
        numBR = 0
        numBA = 0
        tbData= queryList[0]
        #rint '  Team Branch Data has %s items'%len(tbData)
        if type(tbData) not in dictTypes:
            return 'Error: getSFTeamData for %s Query returned %s' \
                   %(pprint.pformat(where), tbData)
        
        tbId = tbData.get('Id','')
        res['Team_Branch__c'] = tbData

        if tbId not in [None,'']:
            branch = tbData.get('Branch__c','')

            where = [['Team_Branch__c','=',tbId]]

            approvals = self.sfb.query('Branch_Approval__c', where=where)   # should limit field with sc='Branch_Approval'

            if approvals not in badInfoList:
                res['Branch_Approval__c'] = approvals

                if self.debug > 0:
                    self.sfb.setLog('->%25s ba:%s'%(branch,approvals),'info')

                numBA = len(approvals)
            cr_links  = self.sfb.query('Branch_Team_Link__c', where=where)    # should limit for performance with , sc='Branch_CR_Link'
            if cr_links not in self.badInfoList:
                res['Branch_Team_Link__c'] = cr_links

                if self.debug > 0:
                    self.sfb.setLog('->%25s br:%s'%(branch,cr_links),'info')
                    
                numBR = len(cr_links)
        else:
            if self.debug>1:
                print '    NO Team Branch Found for %s ' \
                      %pprint.pformat(where)
            return res
        #print 'getSFTeamData with results %s'%res
        self.setData(res)
        self.sfb.setLog('getSFData %25s br:%s ba:%s'%(branch,numBR,numBA),'info2')
        self.loadFromSF = True
        if show: self.showData(res)
        
        return res

    def delete(self):
        """ as advertised, deletes this team branch """
        tmbData = self.getData('Team_Branch__c')
        baList = self.getData('Branch_Approval__c')
        btlList = self.getData('Branch_Team_Link__c')

        # delete branch approvals
        baIdList = []
        for ba in baList:
            baIdList.append(ba.get('Id'))
            continue
        if len(baIdList):
            self.sfb.delete(baIdList)
            pass

        # delete branch-team links approvals
        btlIdList = []
        for btl in btlList:
            btlIdList.append(btl.get('Id'))
            continue
        if len(btlIdList):
            self.sfb.delete(btlIdList)
            pass

        # delete the team branch
        tmbId = tmbData.get('Id')
        if tmbId not in [None,'']:
            self.sfb.delete([tmbId,])
            pass

        return


    def setBranchStatus(self, status='', st=None, scmTS=None, qorrespin=False):
        """ Set the status fields for the Team Branch and Branch Link entities 
            This involved a complete query of prior information
            REQUIRED: All Branch Link objects must already be created
        """
        from walkSCM import findReleasePath, findVersionNum
        
        #print "INSIDE setBranchStatus ......."

        branch = self.branch
        stream = self.stream

        if self.loadFromSF:
            tbData = self.getData()
        else:
            tbData = self.getSFData( branch, stream, show=False)

        tbInfo = tbData.get('Team_Branch__c',{})
        tbId = tbInfo.get('Id')
        tbStatus = tbInfo.get('Status__c')
        
        msg = "passed status: %s, current tbStatus %s" %(status, tbStatus)
        self.sfb.setLog(msg, 'info2')
        
        if status in [None,'']:
            status = tbStatus

        # Quick map of the various team branch states to the state the 
        # approvals should take
        
        #branchStatMap = SFTaskBranchStatus().getStatusMap()
        data = {}

        statMap = self.sfb.getStatMap(status,{})
        statOrder = statMap.get('order', 0.0)
        
        if statOrder >= 54.0 and scmTS is not None:
            # set the patch release path and version if we're merged
            data['Merged_Date_Time__c'] = self.sfb.checkDate(scmTS)
            
            # find release path candidate for stream + merge date/time
            releasePath = None
            versionNum = None
            
            try:
                releasePath = findReleasePath(stream, scmTS)
                
                # find the version number in the releasePath
                if releasePath is not None:
                    data['Patch_Release_Path__c'] = releasePath
                    versionNum = findVersionNum(releasePath)
                    pass
            except Exception, e:
                pass

            if versionNum is not None:
                data['Patch_Version__c'] = versionNum
                pass
            pass
            

        if len(statMap) and status != tbStatus:
            # update the team branch's status if it's a known status
            # and the passed status differs from the current status
            data['Status__c'] = status
            pass

        

        if len(data) > 0:
            self.setTeamBranch(tbId=tbId, data=data)
            pass

        notify = self.setBranchApprovalStatus(status, st, scmTS=scmTS)
        if len(notify) == 0: 
            nt = ' no changes'
            update = False
        else:     
            nt = ' notify for %s user'%len(notify)
            update = True
        if st is not None: ts = '%.7s'%((time.time()-st))
        else:              ts = ' ' 
        brlList = tbData.get('Branch_Team_Link__c',[])
        baList = tbData.get('Branch_Approval__c',[])
        msg = '%s->>setTmBStat-> %25s BR:%s BA:%s %s status:%s ' \
              %(ts,branch,len(brlList),len(baList),nt,status)
        self.sfb.setLog(msg,'info')

        # not surewhy this is commented out...
        self.setBranchStatusCL(status, qorrespin=qorrespin)
        self.setPEBranchStatusCL(status, qorrespin=qorrespin)
        
        return update 

    def incrementCRV_SCM_QOR_Recycle_Count(self, st=None, scmTS=None):
        """ For given Task Branch (self):
              Read CRV_SCM_QOR_Recycle_Count__c (double) field from Task_Branch__c table 
              if number: increment by one
              else: set to 1
            Misha
        """



        update = True
        return update
        
    def getOwnerIdFromTeamLabel(self, team):
        """
        Look up team in Product Teams table, then find active Team Manager
        """
        # Find the Id of the specified Product Team
        prTeamId = self.getTeamIdFromTeamLabel(team)

        # Now, find a team manager user Id for the product team
        teamMgrId = self.getTeamMgrUserId(prTeamId)
        return teamMgrId

    def getTeamIdFromTeamLabel(self, team):
        msg = "getTeamIdFromTeamLabel: Looking up team name %s" %team
        self.sfb.setLog(msg, 'debug3')
        
        defaultPrTeamId = 'a0N300000000012EAA' # 'sf' team
        
        where = [['Lookup__c', '=', team]]
        res = self.sfb.query('Product_Team__c', where=where, sc='all')

        if res in BAD_INFO_LIST:
            msg = 'Couldn\'t find product team named "%s". Will resort to default' %team
            self.sfb.setLog(msg, 'error')
            prTeamData = {}
            return defaultPrTeamId
        else:
            prTeamData = res[0]
            
        if len(res) > 1:
            msg = 'getTeamIdFromTeamLabel: More than one product team found with the name "%s"! The first of the two below were used.\nres:%s' %(team, res)
            self.sfb.setLog(msg, 'warn')

        prTeamId = prTeamData.get('Id', defaultPrTeamId)
        return prTeamId
    ## END getTeamIdFromTeamLabel
        
    def getTeamMgrUserId(self, prTeamId):
        """
        Given a Product Team Id, return the User Id of the Product Team Manager
        """
        defaultTeamMgrId = '00530000000cCy5AAE' # Chip Vanek

        where = [['Product_Team__c','=',prTeamId],'and',
                 ['Link_Type__c','=','Team Manager'],'and',
                 ['Link_Status__c','=','Active']]
        res = self.sfb.query('User_Link__c', where=where, sc='all')

        if res in BAD_INFO_LIST:
            msg = 'Couldn\'t get Team Manager user link for product team %s. Will resort to default' %prTeamId
            self.sfb.setLog(msg, 'error')
            userLinkData = {}
            return defaultTeamMgrId
        else:
            userLinkData = res[0]

        if len(res) > 1:
            msg = 'getTeamMgrUserId: More than one active Team Manager user link found for "%s"! We already defaulted to the first found in the structure below.\n%s' \
                  %(prTeamId, pprint.pformat(res))
            self.sfb.setLog(msg, 'critical')

        # default to Chip Vanek if User__c element not found
        teamMgrId = userLinkData.get('User__c', defaultTeamMgrId)
                 
        # Ensure we hand back an Id18
        return self.sfb.getId18(teamMgrId)
    ## END getTeamMgrUserId


    
    def setBranchApprovalStatus(self, status=None, st=None, scmTS=None, partData=None):
        """ Called on every change of a Team Branch to ensure the 'right' Branch Approval 
            relationships still exist.  Can be called at anytime after initial 'addTeam'
            -  checks/created following BA sub-object with correct related status
                - TeamMgr BA owner by TB owner, subject and status wrt status parm
                - Loop over BR Links and create BAs
                    - BA owned by Team Branch Owner

            REQUIRED:   self.getData must be fully loaded
                        All BR Links must be present
        """
        
        
        teamInfo = self.getData('Team_Branch__c')
        btLinkList = self.getData('Branch_Team_Link__c')
        if type(teamInfo) == type([]): 
            teamInfo = teamInfo[0]
        if teamInfo in [None,'',{},[]]:
            self.sfb.setLog('setTBAStat: NO TEam Branch info found for %s'%(self.branch),'warn')
            return {}
        teamId = teamInfo.get('Id','')
        tbOwner= teamInfo.get('OwnerId')
        tbTeam = teamInfo.get('Team__c')
        teamBr = teamInfo.get('Branch__c')
        
        tbOwner = self.getOwnerIdFromTeamLabel(tbTeam)

        if status in [None,'']:
            status = tbInfo.get('Status__c','Awaiting Branches')

        msg = "SFTeamBranch.setBAStatus: BA Status is to be %s" %status
        
        self.sfb.setLog(msg, 'info2')
        statMap = self.sfb.getStatMap(status)   # statMap = {'order':36.0, 'role':'dev', 'crStatus':'Approved', 'crStatusFirst':'First-Approved'}
        statOrder = statMap.get('order')
        if statOrder in [None,'']:
            print 'ERROR getStatMap returned wrong value for -> %s <-'%status


        # get a crlink map for crs links to each constituent branch (clMap)...
        clList = self.getData('Branch_CR_Link__c')
        crNums = []
        clMap = {}

        brObj = SFTaskBranch(sfTool=self.sfb, debug=self.debug)
        for btLink in btLinkList:
            brId = btLink.get('Task_Branch__c')
            brInfo = brObj.loadBranchById(brId)
            brClList = brObj.getData('Branch_CR_Link__c')
            for clInfo in brClList:
                crId = clInfo.get('Case__c')
                #crNum = self.sfb.getCrNumByCrId(crId)
                #comp = clInfo.get('Component__c')       
                crInfo = self.sfb.getCrById(crId)
                crNum =  crInfo.get('CaseNumber',0)   
                #print "CR NUMBER  %s ....... " %crNum   
                comp =  crInfo.get('Component__c','')  # get component string directly from the CR
                #clMap[crNum] = comp
                clMap[crNum] = crInfo       # CV 10/27/04 Need more CR info in BAs
                
                if crNum not in crNums:
                    crNums.append(crNum)
            
        self.sfb.setLog('team setBAStatus:%s numCRs:%s \tBranchStatus:%s teamId:%s'%(self.branch, len(crNums), status, teamId),'info')

        if st is not None:
            ts = '%.7s'%((time.time()-st))
        else:
            ts = '  ' 
        msg = '%s %30s got Mgr, baRoleMap & statMap found %s CRs' \
              %(ts, self.branch, len(crNums))

        if self.debug>0:
                print msg


        self.baRoleMap = self.setBaRoleMap()

        #pprint.pprint(self.baRoleMap)
       

        # Here's where we loop o'er the roles

        for role in ['team','scm','ae']:  
                      
            roleMap = self.baRoleMap.get(role)
            validActions = ['Approved','Rejected','Approve','Reject']
            date = 'now'        # fix this ?!
            
            #print "ROLE .....%s ....." %role

            # OK, for each role, here's what we're gonna do:
            # specify a default status for the BA's of that role.
            # specify rules to modify the BA status based upon the TB status
            # Call the setBA method for the role with pertinent information.
            if role == 'team':
                validStats = ['Awaiting Task Branch',
                              'Task Branch Ready',
                              'Team Approving',
                              'Team Approved']
                stat = None
                if statOrder >= 38.0: stat = 'Team Approving'
                if statOrder >= 42.0: stat = 'Team Approved'

                notify = self.setBranchApprovalForTeamMgr(teamId, roleMap, stat,
                                                          tbOwner, tbTeam)
            elif role == 'scm':
                # NOTE: Be sure to sync this stanza with counterpart
                # in sfTaskBranch.py
                scmBaOwner = '00530000000cBrzAAE'
                validStats = ['Pending Fix',
                              'Requires Receipt',
                              'Received',
                              'Accepted',
                              'Testing',
                              'Patch Build Available',
                              'Merged']
                order = 4.40
                stat = 'Pending Submission'
                if statOrder > 43.9 and statOrder < 54:
                    order = statOrder/10
                    stat = '%s' %(status)
                notify = self.setBranchApprovalStatusForSCM(teamId, scmBaOwner,
                                                            roleMap, clMap,
                                                            stat, order, scmTS=scmTS)
                             
            elif role == 'ae':
                # NOTE: Be sure to sync this stanza with counterpart
                # in sfTaskBranch.py
                validStats = ['Pending Merged Fix',
                              'Merged - Notifying Originator',
                              'Merged - Testing by Originator',
                              'Merged - Approved',
                              'Merged - Rejected'] 
                if statOrder < 53.9:
                    #Merged - Notifying Originator = 54.0
                    stat = 'Pending Merged Fix'
                else:
                    stat = '%s'%(status)

                notify = self.setBranchApprovalStatusForOriginator(None,
                                                                   roleMap,
                                                                   clMap,
                                                                   stat,
                                                                   validStats,
                                                                   validActions,
                                                                   teamId)
                
        if len(notify) > 0:
            self.sfb.setLog('setTBAStat:Found actors to notify in %s  %s'%(self.branch,notify),'info')
        return notify
            

    def setBranchApprovalForTeamMgr(self, teamId, roleMap, status, ownerId, team):
        """ Check for and set/create Branch Approval for Team Manager (teamMgr)
            Return/change:
        """
        order = 4.1
        role = 'team'
        rolePick = roleMap.get('sf')
        baIds = roleMap.get('sfids')
        baMap = {}                                  # branch={baId,status}
        baList = self.getData('Branch_Approval__c')

        if self.sfb.debug > 1:
            msg = "setBranchApprovalForTeamMgr: branch approval list of %s BAs\n%s" \
                  %(len(baList), pprint.pformat(baList))
            self.sfb.setLog(msg, 'info')
            print msg
        
##        for baInfo in baList:
##            baId = baInfo.get('Id')
##            branch = baInfo.get('Branch__c')        # text branch label
##            baStatus = baInfo.get('Status__c')
##            action = baInfo.get('Approve__c')
##            if branch not in [None,'']:
##                baMap[branch] = {'baId':baId, 'status':baStatus, 'action':action}
##            baIds.append(baId)
        for baId in baIds:
            baInfo = self.getData('Branch_Approval__c', baId)
            branch = baInfo.get('Branch__c')
            baStatus = baInfo.get('Status__c')
            action = baInfo.get('Approve__c')
            if branch not in [None,'']:
                baMap[branch] = {'baId':baId,
                                 'status':baStatus,
                                 'action':action}
                
        if self.sfb.debug > 1:
            msg = "baMap now contains:\n%s" %pprint.pformat(baMap)
            self.sfb.setLog(msg, 'info')
            print msg
        
        extraBAs = copy.deepcopy(baIds)
        brlIds = []
        notify = {}
        brListRef = self.getData('Branch_Team_Link__c')
        brList = copy.deepcopy(brListRef) # need a copy so that we don't nuke it

        if self.sfb.debug > 1:
            msg = "setBranchApprovalForTeamMgr: number of task branch team links in brList is %s\n%s" %(len(brList), pprint.pformat(brList))
            self.sfb.setLog(msg, 'info')
            print msg

        for btLinkInfo in brList:           # Get Task Branch info and create/update Approval & Link Objects

            tblId = btLinkInfo.get('Id')
            tblStat = btLinkInfo.get('Status__c')
            brId    = btLinkInfo.get('Task_Branch__c')
            brInfo = self.sfb.getTBInfoById(brId)       # the TaskBranch info
            branch = brInfo.get('Branch__c')        # text branch label
            brStat = brInfo.get('Branch_Status__c') # need to update?

            if self.sfb.debug > 1:
                msg = "Processing branch-team link ID %s which links branch %s (%s)" \
                      %(tblId, branch, brId)
                self.sfb.setLog(msg, 'info')
                print(msg)

                msg = "tblStat: %s, brStat %s, tblId: %s" \
                      %(tblStat, brStat, tblId)
                self.sfb.setLog(msg, 'info')
                print(msg)


            # Here's where we actually update the branch-team link's status
            if tblStat != brStat and tblId not in [None,'']:
                sfId = self.setTeamBranchLink(tbId=tblId, teamId=teamId, brId=brId,
                                              data={'Branch_Status__c':brStat})

            brlIds.append(tblId)

            # promoted from block below
            subject = 'Team Approval %s in %s '%(branch, self.stream)
            instuct = 'Since you are the Team Manager for %s you are asked to review that the branches in this Team branch'%team
            
            data ={'Name':subject,
                   'Order__c': order,
                   'Approval_Role__c': rolePick,
                   'OwnerId': ownerId, 
                   'Instructions__c': instuct,
                   'Stream__c':self.stream,
                   'Branch__c':branch}

            if branch not in baMap.keys(): # need a new teamBA
                if status is None:
                    newBaStatus = 'Awaiting Task Branch'
                else:
                    newBaStatus = status
                    
                baId = self.setBranchApproval( '', tbId=brId,
                                               status=newBaStatus,
                                               date='now',
                                               data=data, teamId=teamId)
                self.sfb.setLog('setBATeam:%s teamBA NEW %s team:%s for uid:%s in:%s'%(branch, status, team, ownerId, brId),'new')
                if baId in badInfoList:
                    self.sfb.setLog('setBA:%s Updating teamBA %s to %s ret:%s in %s'%(branch, rolePick, status, baId, team),'error')
                    #continue

            else:   # have a teamBA
                baStat = baMap[branch].get('status')
                baId = baMap[branch].get('baId')
                
                if status is None:
                    newBaStatus = baStat
                else:
                    newBaStatus = status

                if self.sfb.debug > 1:
                    msg = "branch: %s, baStat: %s, status: %s" %(branch, baStat, status)
                    self.sfb.setLog(msg, 'info')
                    print msg

                if baId in extraBAs:
                    extraBAs.remove(baId)

                # If the target BA status is Team-Approved, set the Approve field to Approve
                if status == 'Team Approved':
                    action = 'Approve'
                elif baStat == 'Team Approving' and action == 'Approve':
                    # PE has set approval manually on the BA
                    newBaStatus = 'Team Approved'
                elif action == 'Approve':
                    # BA is no longer Team-Approved, but Approve is still set - clear it
                    action = ''
                else:
                    action = baMap[branch].get('action')

                data['Approve__c'] =  action
                
                
                # find the right tbId - error here otherwise
                baId = self.setBranchApproval(baId, tbId=brId,
                                              status=newBaStatus,
                                              data=data, teamId=teamId)

                if baId in badInfoList:
                    self.sfb.setLog('setBA:%s Updating teamBA %s to %s ret:%s' %(self.branch, rolePick, newBaStatus, baId), 'error')
                    
                elif baStat == newBaStatus: # Set ba.stat to passed in Status
                    # update complete, no status change
                    self.sfb.setLog('setBA:%s teamBA updated, Status OK of %s '%(self.branch, baStat),'info3')

                else:
                    # status has changed!
                    self.sfb.setLog('setBA:%s teamBA updated. Status changed TO %s for baId:%s'%(self.branch, newBaStatus, baId),'event')  

                    # anyone to notify?
                    if baStat in ['Requires Approval','Approving']:
                        self.sfb.setLog('setBA:%s Ready to notify Team Mgr'\
                                        %(branch),'info')
                        info = {'status':baStat, 'role':role,
                                'actor':ownerId, 'tbId':brId}
                        notify[baId]=info

        if len(extraBAs) > 0:
            self.sfb.setLog('setBATeam:Found Extra BAs %s baMap:%s'%(extraBAs, baMap),'warn')
        for baId in extraBAs:
            self.sfb.setLog('setBA:%s DELETING Extra teamBA %s' \
                            %(self.branch, baId),'error')
            self.sfb.delete([baId])
            pass
            
        return notify

    
    def setTeamBranch(self, tbId='', teamBR='', stream='', data={'Status__c':'Open'}, numCRs=None ):
        """ update a Team Branch object with minimal fields 
            Other fields can be set using passed in data dictionary
        """
        pdata = data
        data = self.getData('Team_Branch__c')
        data.update(pdata) # should command line override
                
        if tbId != '': 
            data['Id'] = tbId
            if not data.has_key('Team__c'):
                data['Team__c'] = 'sf'    
        if teamBR not in [None,'']:
            data['Name'] = teamBR
            data['Branch__c'] = teamBR
            self.branch = teamBR
        if stream not in [None,'']:
            data['Stream__c'] = stream
        if numCRs not in [None,'']:
            data['Num_CRs__c'] = numCRs
        if data.has_key('type'):
            del data['type']
        if data.has_key('Team__c'):
            data['Team__c'] = data['Team__c'].lower()
            tbOwner = self.getOwnerIdFromTeamLabel(data.get('Team__c'))    
            data['OwnerId'] = tbOwner
        
        
        if tbId == '':            
            res = self.sfb.create('Team_Branch__c',data)            
            mode = 'Created'
        else:
            res = self.sfb.update('Team_Branch__c',data)
            mode = 'Updated'

        if res in self.badInfoList:
            if self.debug >0: print 'ERROR: %s Team Branch, %s %s %s'%(mode,stream,teamBR,res)
            return ''
        tbId = res[0]
        data['Id'] = tbId
        self.setData({'Team_Branch__c':data})
        if self.debug >0: 
            print '%s Team Branch, %s %s %s CR at https://na1.salesforce.com/%s'\
                                            %(mode,stream,teamBR,data.get('Num_CRs__c',0),tbId)
        return tbId
    
    def setPETeamBranch(self, tbId='', teamBR='', stream='', data={'Status__c':'Open'}, numCRs=None ):
        """ update a Team Branch object with minimal fields 
            Other fields can be set using passed in data dictionary
        """
                
        if tbId != '':            
            data['Id'] = tbId
            if not data.has_key('Team__c'):
                data['Team__c'] = 'sf'    
        if teamBR not in [None,'']:
            data['Name'] = teamBR
            data['Branch__c'] = teamBR
            self.branch = teamBR
        if stream not in [None,'']:
            data['Stream__c'] = stream
        if numCRs not in [None,'']:
            data['Num_CRs__c'] = numCRs
        if data.has_key('type'):
            del data['type']
        if data.has_key('Team__c'):
            data['Team__c'] = data['Team__c'].lower()
            tbOwner = self.getOwnerIdFromTeamLabel(data.get('Team__c'))    
            data['OwnerId'] = tbOwner
        
        
        if tbId == '':        
            res = self.sfb.create('Team_Branch__c',data)            
            mode = 'Created'
        else:
            res = self.sfb.update('Team_Branch__c',data)
            mode = 'Updated'

        if res in self.badInfoList:
            if self.debug >0: print 'ERROR: %s Team Branch, %s %s %s'%(mode,stream,teamBR,res)
            return ''
        tbId = res[0]
        data['Id'] = tbId
        self.setData({'Team_Branch__c':data})
        if self.debug >0: 
            print '%s Team Branch, %s %s %s CR at https://na1.salesforce.com/%s'\
                                            %(mode,stream,teamBR,data.get('Num_CRs__c',0),tbId)
        return tbId
    

    def sendNotifyEmail(self, baUid=None, validStat=None):
        """  This method generates a notification for any branch status change.
        """
        if baUid in [None,'']: baUid = self.sfb.uid
        if validStat in [None,'',[]]:
            validStat = ['Requires Approval','Approving','Submitted to SCM','Merged - Notifying Originator']
        hideStat = ['Pending Merged Fix','Pending Submission','Pending Fix']
        approved = ['Approve']  # ['Approved','Rejected','Approve','Reject']

        tbInfo = self.getData('Team_Branch__c')
        blList = self.getData('Branch_Team_Link__c')
        baList = self.getData('Branch_Approval__c')
        if tbInfo in BAD_INFO_LIST:
            return ''
        
        tbId   = tbInfo.get('Id')
        status = tbInfo.get('Status__c')
        stream = tbInfo.get('Stream__c')
        branch = tbInfo.get('Name')

        toInfo = self.sfb.getUserById(baUid)
        uemail = toInfo.get('Email','')
        tbBand = '%s in blast%s\n'%(branch,stream)
        tbBand += 72*'='+'\n'
        tbBand += '   status:%s  with priority:%s\n'%(status, tbInfo.get('Branch_Priority__c'))
        tbBand += '   https://na1.salesforce.com/%s\n'%tbId
        tbBand += '   \n'
        
        preSubj = 'SF notify only:'
        baLine = 'You have the following approval records for this branch:\n'
        for baInfo in baList:
            ownerId = baInfo.get('OwnerId')
            stat = baInfo.get('Status__c')
            appr = baInfo.get('Approve__c')
            if baUid == ownerId and appr not in approved and stat not in hideStat:  #and stat in validStat 
                role = baInfo.get('Approval_Role__c')
                preSubj = 'SF Approval: %s '%role
                baLine += '  Status:%s  Your Role:%s\n'%(stat,role)
                baLine += '  Subject:%s\n'%(baInfo.get('Name'))
                baLine += '  for CRs %s\n'%(baInfo.get('CR_List__c'))
                baLine += '  https://na1.salesforce.com/%s\n\n'%baInfo.get('Id')
        
        brBand = '\nThis branch addresses the following Branches:\n'
        for btLinkInfo in blList:
            tblId   = btLinkInfo.get('Id')
            tblStat = btLinkInfo.get('Status__c')
            brId    = btLinkInfo.get('Task_Branch__c')
            brInfo = self.sfb.getTBInfoById(brId)       # the TaskBranch info
            branch = brInfo.get('Branch__c')        # text branch label
            brStat = brInfo.get('Branch_Status__c') # need to update?
            
            brBand += '  %s \n'%(branch)
            brBand += '  Satus:%s\n'%(brStat)
            brBand += '  https://na1.salesforce.com/%s\n\n'%brId

        msgBody = '%s%s%s'%(tbBand,baLine,brBand)
        if uemail in [None,'']:
            print 'No Email found in uInfo:%s'%toInfo
            uemail = 'kshuk@molten-magma.com'
        #uemail = 'kshuk@molten-magma.com'                #debug, remove
        
        statOrder = self.getStatOrder(status)
        if statOrder < 40:
            postSubj = 'awaiting individual task branch approvals %s %s'%(self.branch, self.stream)
        elif statOrder > 41 and statOrder < 44:
            preSubj = 'SF Approval: Team'
            postSubj = '%s %s awaits your approval'%(self.branch, self.stream)
        elif statOrder > 44 and statOrder < 53:
            postSubj = 'in SCM as %s %s %s '%(status, self.branch, self.stream)
        else:
            postSubj = 'status:%s %s %s '%(status, self.branch, self.stream)
        subject = '%s %s' %(preSubj, postSubj)    
        
        msg = self.sendMsg([uemail], subject, msgBody)
        return msg
        

    def getStatOrder(self, status=None):
        """ need to finish this """
        ret = False
        if status in [None,'']:
            tbInfo = self.getData('Team_Branch__c')
            status = tbInfo.get('Status__c','')
        statMap = self.sfb.getStatMap(status)   # statMap = {'order':36.0, 'role':'dev'}
        statOrder = statMap.get('order')
        return statOrder

    def getTeamBranchInfo(self, email='you', viewUid=None, target='token'):
        """ create a text representation of the Team Branch contents 
        """
        if viewUid in [None,'']:
            viewUid = self.sfb.uid
        tbInfo = self.getData('Team_Branch__c')
        blList = self.getData('Branch_Team_Link__c')
        baList = self.getData('Branch_Approval__c')
        tbId   = tbInfo.get('Id')
        status = tbInfo.get('Status__c')
        stream = tbInfo.get('Stream__c')
        branch = tbInfo.get('Name')

        tbBand  = 'Team Branch Information for %s Task Branches follows:\n'%len(blList) + 72*'='+'\n'
        tbBand += '%s in blast%s\n'%(branch,stream)
        tbBand += '   status:%s  with priority:%s\n'%(status, tbInfo.get('Priority__c'))
        tbBand += '   https://na1.salesforce.com/%s\n'%tbId
        tbBand += '   \n'
        
        baLine = 'You have the following approval records for this branch:\n'
        for baInfo in baList:
            ownerId = baInfo.get('OwnerId')
            stat = baInfo.get('Status__c')
            appr = baInfo.get('Approve__c')
            if viewUid == ownerId:  #and stat in validStat 
                role = baInfo.get('Approval_Role__c')
                preSubj = 'SF Approval: %s '%role
                baLine += '  Status:%s  Your Role:%s\n'%(stat,role)
                baLine += '  Subject:%s\n'%(baInfo.get('Name'))
                baLine += '  for CRs %s\n'%(baInfo.get('CR_List__c'))
                baLine += '  https://na1.salesforce.com/%s\n\n'%baInfo.get('Id')
        
        brObj = SFTaskBranch(sfTool=self.sfb)
        brBand = 'This branch addresses the following Branches:\n'
        for btLinkInfo in blList:
            tblId   = btLinkInfo.get('Id')
            tblStat = btLinkInfo.get('Status__c')
            brId    = btLinkInfo.get('Task_Branch__c')
            brInfo = self.sfb.getTBInfoById(brId)
            branch = brInfo.get('Branch__c')
            stream = brInfo.get('Code_Stream__c')
            msg = brObj.loadBranch(branch, stream)
            brBand  += brObj.getBranchInfo(email,target)
        
        msg = '%s%s%s'%(tbBand,baLine,brBand)
        return msg
        

    def getTeamBranchList(self, target='token'):
        """ create a list representation of the Team Branch contents 
        """
        tbInfo = self.getData('Team_Branch__c')
        blList = self.getData('Branch_Team_Link__c')
        baList = self.getData('Branch_Approval__c')
        tbId   = tbInfo.get('Id')
        status = tbInfo.get('Status__c')
        stream = tbInfo.get('Stream__c')
        branch = tbInfo.get('Name')

        tbBand = 'Team Branch %s in stream %s has %s Task Branches as follows:\n'%(branch,stream,len(blList)) + 72*'='+'\n'
        brBand = ''
        brObj = SFTaskBranch(sfTool=self.sfb)
        for btLinkInfo in blList:
            tblId   = btLinkInfo.get('Id')
            brId    = btLinkInfo.get('Task_Branch__c')
            brInfo = self.sfb.getTBInfoById(brId)

            #branch = brInfo.get('Branch__c')
            #if show == 'info':
            branch = '%-45s %-30s ' %(brInfo.get('Branch__c'),
                                       brInfo.get('Branch_Status__c'))
            brBand += '%s\n'%(branch)
        
        msg = '%s%s'%(tbBand,brBand)
        return msg

    def getTeamPEBranchList(self, peList):
        """ create a list representation of the Team Branch with PE checkpoints known 
        """
        tbInfo = self.getData('Team_Branch__c')
        blList = self.getData('Branch_Team_Link__c')
        baList = self.getData('Branch_Approval__c')
        tbId   = tbInfo.get('Id')
        status = tbInfo.get('Status__c')
        stream = tbInfo.get('Stream__c')
        branch = tbInfo.get('Name')
        peInfo = {} # save some info ?
        tbInPEs = []
        tbBand = '%s %s Task Branches in %20s %s :\n'%(stream,len(blList),status,branch) + 72*'='+'\n'
        brBand = ''
        #brObj = SFTaskBranch(sfTool=self.sfb)
        peObj = SFPEBranch(sfTool=self.sfb)

        for pe in peList: # list of lined PE Checkpoint header objects
            pename = pe.get('Name')
            pestatus = pe.get('Status__c')
            brBand += '%-45s %-32s %-17s\n'%(pename,pestatus,'PE_CHKPNT')
            
            peinf = peObj.loadBranch(pename, stream)
            # {'Checkpoint_Branch__c':{}, 'Cases':[],
            #  'Branch_Approval__c':[], 'Task_Branch__c':[]}
            TBs =  peObj.getData('Task_Branch__c')
            #CRs = peinf.get('Cases')
            for TB in TBs:
                branch = TB.get('Branch__c')
                status = TB.get('Branch_Status__c')
                brBand += '- %-43s %-32s %-17s\n'%(branch,status,'PETask')
                tbInPEs.append(branch)
    
        for btLinkInfo in blList:
            tblId   = btLinkInfo.get('Id')
            brId    = btLinkInfo.get('Task_Branch__c')
            brInfo = self.sfb.getTBInfoById(brId)
            branch = brInfo.get('Branch__c')
            status = brInfo.get('Branch_Status__c')
            if branch not in tbInPEs:
                brBand += '%-45s %-32s %-17s\n'%(branch,status,'Task')
        
        msg = '%s%s'%(tbBand,brBand)
        return msg

    
    ##################################################################################################
    #   Status oriented methods
    ##################################################################################################
    def approveBranch(self, branch, stream, st=None):
        """ decide what approval role the user needs for this 
            branch and do it.
        """
        ld = self.checkLoad(branch, stream, cl=True)
        if -1 in ld[:2]: return -1
        num = 0
        role = self.getNextApprovalRole()   # dev, mgr, pe, scm, ae
        if role == 'dev':   num = self.submitByDev(branch, stream, st)
        elif role == 'mgr': num = self.submitByMgr(branch, stream, st)
        elif role == 'pe':  num = self.submitByPe(branch, stream, st)
        elif role == 'scm': num = self.submitToSCM(branch, stream, st)
        elif role == 'ae':  num = self.submitByAe(branch, stream, st)
        else: print 'ERROR: approveBranch, getNextApprovalRole returned %s'%role
        return num, role
            

    def rejectBranch(self, branch, stream, st=None):
        """
        reject the branch back to the developer
        """
        ld = self.checkLoad(branch, stream, cl=True)
        if -1 in ld[:2]: return -1
        num = self.rejectToDev(branch, stream)
        return num

    ########################################################################
    # methods to support the submission of a team branch to SCM
    ########################################################################

    def submitByTeam(self, branch, stream, st=0):
        """ set status on branch to trigger state change """
        num = 0

        ld = self.loadTeamBranch(branch, stream)
        if -1 in ld[:2]: return -1
        
        tmbInfo = self.getData('Team_Branch__c')
        tmbStatus = tmbInfo.get('Status__c','')
        baList = self.getData('Branch_Approval__c')
        myBaList = copy.deepcopy(baList)
        teamBaCt = 0
        approvedCt = 0
        for ba in myBaList:
            baId = ba.get('Id')
            tbId = ba.get('Task_Branch__c')
            baApprove =  ba.get('Approve__c','')
            baStatus = ba.get('Status__c','')
            
            if ba.get('Approval_Role__c','') == 'Team Manager':
                teamBaCt += 1
                
                if baStatus == 'Team Approving' and baApprove == 'Approve':
                    self.setBranchApproval(baId, tbId, data={}, date='now',
                                           status='Team Approved')
                    approvedCt += 1

                elif baStatus == 'Team Approved':
                    approvedCt += 1
                    pass
                pass
            continue

        # team branch status will be set to team-approved by a sweep
        # into a checkpoint branch.
        if tmbStatus == 'Team-Approved':
            num, notify = self.submitAndNotify(status, st)
            pass
        
        return num


    def submitToSCM(self, branch, stream, st=0):
        """ set status on branch to trigger state change 
             not used, August 6th, 2004
        """
        status = 'Submitted to SCM'
        #print " team branch %s ..... and stream %s ...." %(branch,stream)
        ld = self.loadTeamBranch(branch, stream)
        if -1 in ld[:2]: return -1
        updated = self.postSCMTokenAndNotify(type='team')
        num, notify = self.submitAndNotify(status, st)
        return num

    def setBranchStatusCL(self, status, scmTS=None, qorrespin=False):
        #print "Inisde setBranchStatusCL... ...."
        teamData = self.getData()
        teamInfo = teamData.get('Team_Branch__c')
        teamStatus = teamInfo.get('Status__c')
        
        btLinkList = teamData.get('Branch_Team_Link__c')
        # gotta operate on a copy or else we won't hit all the linked branches
        btLinkListCopy = copy.deepcopy(btLinkList)

        brObj = SFTaskBranch(sfTool=self.sfb, debug=self.debug)

        updated = False

        # update the constituent branch and branch team link states as well
        # but only if the team branch is into SCM
        sm = self.sfb.getStatMap(status)
        subSCMsm = self.sfb.getStatMap('Submitted to SCM')
        tbHoldsm = self.sfb.getStatMap('Team Branch Hold')
        tbRecvsm = self.sfb.getStatMap('Awaiting Branches')

        numTaskBranches = len(btLinkListCopy)
        tbCount = 0

        print "\nUpdating %d task branches\n in team branch %s, stream %s" \
              %(numTaskBranches, teamInfo.get('Branch__s'),
                teamInfo.get('Stream__s'))
        print "Please be patient - this may take a while"
        
        for btLink in btLinkListCopy:
            tbCount += 1
            print "* Updating %d of %d Task Branches" %(tbCount, numTaskBranches)
            brId = btLink.get('Task_Branch__c')
            brInfo = brObj.loadBranchById(brId)
            brData = brObj.getData('Task_Branch__c')
            brStatus = brData.get('Branch_Status__c')
            brsm = self.sfb.getStatMap(brStatus)

            # hacks to special-case set tb status for receiving and
            # holding bin
            if sm.get('order') >= subSCMsm.get('order') or \
                   sm.get('order') in [tbHoldsm.get('order'),
                                       tbRecvsm.get('order')]:
                
                if sm.get('order') == tbHoldsm.get('order'):
                    status = 'Team Branch Hold'
                elif sm.get('order') == tbRecvsm.get('order'):

                    if brsm.get('order') > 35.2:
                        status = 'Approved, pending Team Branch'
                    else:
                        # task branch is linked to team, but not yet approved,
                        # so leave its status alone
                        status = brStatus
                        pass
                    pass
                
                updated = brObj.setBranchStatus(status, scmTS=scmTS,
                                                qorrespin=qorrespin)
            
                btlUpdData = {'Branch_Status__c': status}
                self.setTeamBranchLink(btLink.get('Id'),
                                       btLink.get('Team_Branch__c'),
                                       data=btlUpdData)
            else:
                # just refresh the task branch
                updated = brObj.setBranchStatus()
                
        return updated
    
    def setPEBranchStatusCL(self, status, scmTS=None, qorrespin=False):
        #print "Inisde setPEBranchStatusCL ...."
        teamData = self.getData()
        teamInfo = teamData.get('Team_Branch__c')
        teamStatus = teamInfo.get('Status__c')
        teamId=teamInfo.get('Id')
        teamName=teamInfo.get('Name')       
        where = [['Team_Branch__c','=',teamId]]   
        res=False     
        #print "Team barnch ID ....... %s" %teamId
        queryList = self.sfb.query('Checkpoint_Branch__c', where=where, sc='all')
        
        if queryList in self.badInfoList:
            print "No PE checkpoint barnch found which is linked with the team branch %s " %teamName
            pass
        else:
            #Propogate the status of the team barnch to the PE checkpoint branch            
            tbCount=0
            for qr in queryList:
                tbCount += 1
                print "* Updating %d of %d PE Checkpoints" %(tbCount, len(queryList))
                peId=qr.get('Id')
                #print "PE ID ..... %s " %peId
                newPEData = {'Id': peId, 'Status__c': teamStatus,'Need_Check__c':True}
                res = self.sfb.update('Checkpoint_Branch__c', newPEData)
                       
                           
        return res
            
        
    def updateSFonSubmitToSCM(self):
        """ set the Team Branch status """
        status = 'Submitted to SCM'
        updated = self.setBranchStatus(status)
        if not updated:
            self.sfb.setLog('updateSFonSubmitToSCM: did not update anything with setBranchStatus(%s)'%status,'error')
        return 0


    def getBranchInfo(self, email='you', target='token'):
        """
        return a text version of the team branch info suitable
        for the SCM token and display at commandline
        """
        # get each task branch in the team branch.
        teamInfo = self.getData('Team_Branch__c')
        teamBaList = self.getData('Branch_Approval__c')
        btLinkList = self.getData('Branch_Team_Link__c')
        
        teamBrId = teamInfo.get('Id')
        teamBranch = teamInfo.get('Branch__c')
        teamStream = teamInfo.get('Stream__c')
        teamStatus = teamInfo.get('Status__c')
        
        # heading Team Branch band
        tbBand  = 'Team Branch Information for %s follows:\n'%email + 72*'='+'\n'
        tbBand += '%s in blast%s\n'%(teamBranch, teamStream)
        tbBand += '   Status:%s\n'%(teamStatus)
        tbBand += '   https://na1.salesforce.com/%s\n'%teamBrId

        tbBand += 'Other Details:  %s\n'%(teamInfo.get('Details__c'))
        tbBand += 'Merge Details:  %s\n'%(teamInfo.get('Merge_Details__c'))
        tbBand += '   \n'

        crBand = '\nThis team branch addresses the following CRs:\n\n'
        
        # get each task branch's info
        brObj = SFTaskBranch(sfTool=self.sfb, debug=self.debug)
        for btLink in btLinkList:
            brId = btLink.get('Task_Branch__c')
            brInfo = brObj.loadBranchById(brId)
            brInfo = brObj.getData('Task_Branch__c')
            clList = brObj.getData('Branch_CR_Link__c')
            baList = brObj.getData('Branch_Approval__c')

            status = brInfo.get('Branch_Status__c')
            stream = brInfo.get('Code_Stream__c')
            branch = brInfo.get('Name')
            brPath = brInfo.get('Branch_Path__c')

            for clInfo in clList:
                crId   = clInfo.get('Case__c')
                crInfo = self.sfb.getCrById(crId)
                name = crInfo.get('Subject','')
                comp = crInfo.get('Component__c','')
                crNum = 'CR#: %s'%int(crInfo.get('CaseNumber',0))
                streams = crInfo.get('Code_Streams_Priority__c','')
                crStat  = crInfo.get('Status')
                crBand += '  Subject:%s\n'%(name)
                crBand += '  https://na1.salesforce.com/%s\n'%crId
                crBand += '  %s needs fixes in streams:%s for component:%s \n'%(crNum,streams,comp)
                crBand += '  CR Status:%s needs \n'%(crStat)
                crBand += '  Details:  %s\n\n'%(clInfo.get('Details__c'))

        msgBody = '%s%s'%(tbBand,crBand)
        return msgBody
        
    # FIXME - convert for team branch - Fixed?
    def getCRList(self):
        """ get existing CR list for the team branch """
        
        btLinkList = self.getData('Branch_Team_Link__c')
        # Loop over Branch Team Links to get the CR links from each, then
        # process as below
        brObj = SFTaskBranch(sfTool=self.sfb, debug=self.debug)

        crNums = []

        for btLink in btLinkList:
            clList = []
            brId = btLink.get('Task_Branch__c')
            brInfo = brObj.loadBranchById(brId)
            clList = brObj.getData('Branch_CR_Link__c')
        
            if clList == []:
                self.sfb.setLog('getCRList called but data not loaded','error')
                
            for clInfo in clList:
                crNum = clInfo.get('CR_Num__c')
                if crNum in [None,'',0,'0']:
                    crId = clInfo.get('Case__c')
                    crNum = self.sfb.getCrNumByCrId(crId)
                    #print 'getCRList: got crNum:%s from crId:%s'%(crNum,crId)
                crNums.append(crNum)

        if self.debug>1:print 'getCRList: returning crList: %s'%crNums
        return crNums


class SFTeamBranchTool(SFTaskBranchTool):
    """ This is a subclass of the SFEntityTool to hold any Branch specific
        SOQL query methods and entity linking  methods
    """
    logname = 'sfTmBt'



    #######################################################################
    #  Branch Approval methods
    #######################################################################

    def checkIntrudingTaskBr(self, taskBr, stream):
        """
        If a task branch exists with the given name and stream, it is in the way.
        Attempt to get rid of it if it is a shell, otherwise complain.

        Returns None if the coast is clear (or has been cleared) or
        the task branch ID if we cannot remove it.
        """
        taskBrObj = SFTaskBranch(sfTool=self)
        taskbl = taskBrObj.loadBranch(taskBr, stream)
        linkCrCount = taskbl[0]

        taskBrInfo = taskBrObj.getData('Task_Branch__c')
        taskBrId = taskBrInfo.get('Id',None)
        
        retVal = None
        if taskBrId is None:
            # no task branch exists with this name and stream
            pass
        elif linkCrCount == 0:
            # task branch exists, but is a shell - remove it
            msg = "checkIntrudingTaskBr: Deleting Task Branch %s because new team branch %s in %s matches"\
                  %(taskBrId, taskBr, stream)
            self.setLog(msg, 'warn')
            delResult = self.delete([taskBrId])
            if delResult in BAD_INFO_LIST:
                msg = "checkIntrudingTaskBr: Deletion of Task Branch %s failed" %taskBrId
                self.setLog(msg, 'error')
                retVal = taskBrId
        else:
            # Task branch exists and has linked CRs. Cannot proceed
            msg = "Task branch with %s linked CRs exists with desired team name and stream %s %s" \
                  %(linkCrCount, taskBr, stream)
            self.setLog(msg, 'error')
            retVal = taskBrId

        return retVal


    def linkTask2TeamBranch(self, tmbID, tbID, tbaID, tblID):
        """ move Task Branch from one Team Branch to another 
        """
        tmbObj = SFTeamBranch(sfTool=self)
        inf = tmbObj.loadTeamBranchById(tmbID)
        #inf = [numTBs,numBAs,status,branch,stream]
        teamInfo = self.getData('Team_Branch__c')
        teamBaList = self.getData('Branch_Approval__c')
        btLinkList = self.getData('Branch_Team_Link__c')
        
        
        # move TeamBranch link to another Team
        data = {'Task_Branch__c':tbID, 'Team_Branch__c':tmbID}
        tmbObj.setTeamBranchLink(tblID, data=data)
        

                

    def showTeamBranches(self, team=None, user=None, uid=None, stream=None, branch=None, show='list'):
        """ one call to get all Team Branch objects, Task, PE Checkpoint
            will return data as a list of data dictionaries [{data}] or []
            show -> 'list' = [list of branch labels], 'all' = [list of full tbData structure]
        """
        origteam = team
        where = [['Team__c','!=','']]
        if team not in [None,'','all']:
            team = team.lower()
            team = self.devTeamToScmTeam(team)    
            if team is None:
                print 'The team "%s" is unknown.\nFor a list of known teams, please use the "teams" command. EXITING' %origteam
                sys.exit(1)

            where = [['Team__c','=',team],'and','(',
                     ['Name','=','%s' %team],'or',
                     ['Name','=','%s_Hold' %team],'or',
                     ['Name','like','%s_%%QOR' %team],')']

        elif team in ['all']: 
            where = [['Team__c','!=','""'],'and',['Status__c','!=','Merged']]
        
                
        elif uid not in [None,'']: 
            where.extend(['OwnerId','=',uid])
            
        elif user not in [None,'','my']:  
            userInfo = self.getUserByAlias(user)
            uid = userInfo.get('Id')
            userName = '%s %s' %(userInfo.get('FirstName'),userInfo.get('LastName'))
            if show != 'min': print 'Getting info for %s'%userName
            where = [['OwnerId','=',uid]]
        
        res = []
        if stream not in [None,'','any','all']:
            where.extend(['and',['Stream__c','=',stream]])
            
        if branch not in [None,'']:
            where.extend(['and',['Branch__c','like',branch]])
        
        queryList = self.query('Team_Branch__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'showTeamBranches: NO Team Branch Found in stream %s ' %(stream)
            return res
        print 'Found %s Team Branches in stream %s for Team %s %s'%(len(queryList),stream,team,origteam)

        queryList.sort(lambda a,b: cmp(a.get('CreatedDate'),
                                       b.get('CreatedDate')))
        
        collect = {}
        tmbObj = SFTeamBranch(sfTool=self)
        peObj = SFPEBranch(sfTool=self)
        for info in queryList:   # list of Team Branches
            if type(info) not in dictTypes:
                return 'showTeamBranches: Error for %s or %s returned %s' %(user, branch, info)
            tbId = info.get('Id','')
            if tbId in [None,'']:
                print 'Could not find a tbId in %s' %info
            else:
                branch = info.get('Name')
                branch = info.get('Branch__c')  # why this second?
                stream = info.get('Stream__c')
                status = info.get('Status__c')
                priority = info.get('Priority__c')
                if status in ['Merged']:
                    print 'Skipping Team Branch %s in %s with status %s\n'%(branch,stream,status)
                else:
                    print 'Found %s Team Branch with status %25s called %s'%(stream,status,branch)
                    inf = tmbObj.loadTeamBranch(branch, stream)
                
                    if show in ['pe','listpe','pelist']:
                        # Sept 28, 06 CV Get the PE Checkpoints linked to this Team Branch
                        peList = self.getLinkedPECheckpoints(tmbObj, tbId, stream)
                        tbmsg = tmbObj.getTeamPEBranchList(peList)
                        res.append(tbmsg)
                       
                    elif show in ['list','min']:
                        tbmsg = tmbObj.getTeamBranchList()
                        res.append(tbmsg)
                    
                    elif show in ['info']:
                        btlList = tmbObj.getData('Branch_Team_Link__c')
                        for btl in btlList:
                            brId    = btl.get('Task_Branch__c')
                            brInfo = self.getTBInfoById(brId)
                            branch = brInfo.get('Branch__c')
                            status = brInfo.get('Branch_Status__c')
                            info = {'branch':branch, 'stream':stream, 'status':status, 'type':'Task'}
                            res.append(info)

                    elif show in ['all']:
                        print 'Getting detailed branch information'
                        teamStr = tmbObj.getTeamBranchInfo()
                        res.append(teamStr)
                
        if self.debug>1:print '---Found %s Team Branch ---'%(len(queryList))  
        return res

    
    def getLinkedPECheckpoints(self, tbObj, teamBrId, stream):
        """ Return a list of PE Checkpoint objects linked up to this Team branch
        """
        where = [['Team_Branch__c','=',teamBrId]]
        tbList = tbObj.sfb.query('Checkpoint_Branch__c', where=where)
        if tbList in self.badInfoList:
            if self.debug > 0:  
                print '  NO PE Checkpoints found with %s'%where
                print '  Found: %s'%pprint.pformat(tbList)
        return tbList


    def isValidProductTeam(self, teamName):
        teamName = teamName.lower()

        ptList = self.getTeamList()
        teamList = []

        for team in ptList:
            if team.has_key('Lookup__c'):
                teamList.append(team['Lookup__c'].lower())
                pass
            continue
        
        if teamName in teamList:
            return True
        else:
            return False
    ## END isValidProductTeam

    def showTeamNames(self, team=None, show='list'):
        """ show the active Product teams and the members """
        ptList = self.getTeamList()
        if ptList in badInfoList:
            return ptList

        ret = []
        #print 'Found %s Product Teams and will now provide %s info\n' \
        #      %(len(ptList),show)


        ptList.sort(lambda a, b: cmp(a.get('Team_Alias__c'),
                                     b.get('Team_Alias__c')))

        # collect owner alias names
        ownerIdList = []
        ptOwnerMap = {}
        for pti in ptList:
            ptOwner = pti.get('OwnerId')
            ownerIdList.append(ptOwner)
            pass

        res = self.retrieve(ownerIdList, 'User', ('Id', 'Alias'))
        for user in res:
            ptOwnerMap[user.get('Id')] = user.get('Alias')
            continue

        # print header
        print
        print "SCM Team      Build                   Development"
        print "Abbreviation  Account     Team Lead   Team"
        print "------------  ----------  ----------  ---------------"

        # print the results
        for ptI in ptList:
            teamLookup  = ptI.get('Lookup__c')
            description = ptI.get('Description__c')
            buildAcct = ptI.get('Build_Account__c')
            ptOwner = ptI.get('OwnerId')
            teamAlias = ptI.get('Team_Alias__c')

            # show only teams with a team alias
            if teamAlias is None or teamAlias == 'sf':
                continue
            
            info = '%-12s  %-10s  %-10s  %-15s' \
                   %(teamAlias, buildAcct, ptOwnerMap.get(ptOwner),
                     teamLookup)

            print info
            ret.append(info)
            continue
        
        return ret
        

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
def overviewUsage(err=''):
    """ default overview information highlighting active scripts"""
    m = '%s\n' %err
    m += '  The following scripts allow you to manage Team Branches (TmB) on SalesForce.\n'
    m += '    Use one of the scripts below to meet your needs.\n'
    m += ' \n'
    m += ' 1. First link Task Branches to Team Branches \n'
    m += '    teamaddbranch -s4.1 -n<RTL|SI|Timing> -t<Team_branch> -b<branch_Name>  \n'       
    m += ' \n'
    m += ' 2. List Task Branches linked to a Team Branches \n'
    m += '    teamaddbranch -s4.1 -n<RTL|SI|Timing> -t<Team_branch> -b<branch_Name> -d  \n'       
    m += ' \n'
    m += ' 3. First link Task Branches to Team Branches \n'
    m += '    teamaddbranch -s4.1 -n<RTL|SI|Timing> -t<Team_branch> -b<branch_Name> -p <low|medium|high|urgent|critical> \n'       
    m += ' \n'
    return m


def addTeamBranchUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = ''
    
    if len(err):
        m += '%s\n\n' %err

    m += 'Link a Task Branch (TB) with a Team Branch (TmB) on Salesforce.\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    teamlnbr [OPTIONS] -s <stream> -n <team name> -b <task branch>\n'       
    m += '\n'
    m += 'Options include:\n'
    m += '    -p <priority> (One of low, medium, high, urgent, or critical)'
    m += '    \n'
    m += '    -t <team Branch> (Checkpoint in SCM that should be linked)'
    m += '    \n'
    m += '    -d  (flag to prompt for general details about the team branch)\n'
    return m

def remTeamBranchUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = ''
    
    if len(err):
        m += '%s\n\n' %err

    m += 'Unlink(s) a Task Branch (TB) from a Team Branch (TmB) on Salesforce.\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    teamunlnbr -s <stream> -n <team name> -t<team Branch> -b <task branch>\n'       
    m += '\n'
    return m

def overviewUsage(err=''):
    """ default overview information highlighting active scripts"""
    m = '%s\n' %err
    m += '  The following scripts allow you to manage Team Branches (TmB) on SalesForce.\n'
    m += '    Use one of the scripts below to meet your needs.\n'
    m += ' \n'
    m += ' 1. First link Task Branches to Team Branches \n'
    m += '    teamaddbranch -s4.1 -n<RTL|SI|Timing> -t<Team_branch> -b<branch_Name>  \n'       
    m += ' \n'
    m += ' 2. List Task Branches linked to a Team Branches \n'
    m += '    teamaddbranch -s4.1 -n<RTL|SI|Timing> -t<Team_branch> -b<branch_Name> -d  \n'       
    m += ' \n'
    m += ' 3. First link Task Branches to Team Branches \n'
    m += '    teamaddbranch -s4.1 -n<RTL|SI|Timing> -t<Team_branch> -b<branch_Name> -p <low|medium|high|urgent|critical> \n'       
    m += ' \n'
    return m
    
def addTeamBranchCL(team, teamBR, branch, stream, options, st, teamTool=None,
                    checkTmb=True, scmFlag=False):
    """ command line logic for addTeamBranch
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
                print 'Please provide some branches to link to %s in team %s'%(teamBR,team)
                sys.exit()
            brList = [branch]
        else:
            brList = branch
        db=options.debug
    
        # if we were passed a team tool, use it
        if teamTool is None:
            print 'Connecting to SalesForce for the %s team branch %s in code stream %s' %(team,teamBR,stream)
            sfb = SFTeamBranchTool(debug=db, logname='addTmB')
            sfb.getConnectInfo(version,st)
        else:
            sfb = teamTool
            pass
    
        origteam = team
        team = sfb.devTeamToScmTeam(team)
        if team is None:
            print 'The team "%s" is unknown.\nFor a list of known teams, please use the "teams" command. EXITING' %origteam
            sys.exit(1)
            pass
    
        # default to the "Generic" branch for the specified team if a team branch name
        # isn't provided. The generic team branch has the same name as the team.
        if teamBR in ['', None]:
            teamBR = team
    
        #taskBrTool = SFTaskBranchTool(debug=db, logname='addTmB')
        tbrObj = SFTeamBranch(sfTool=sfb)
        inlist = tbrObj.loadTeamBranch(teamBR, stream)
    
        #print ' Team Branch loaded as: %s '%(inlist[:5])  # [numCLs,numBAs,status,team,stream]
        if db>2: tbrObj.showData(target='user')
        crInfos = {}
        teamInfo = tbrObj.getData('Team_Branch__c')
        sfBAs  = tbrObj.getData('Branch_Approval__c')
        status = 'Awaiting Branches'
        if teamInfo in [{}]:
            isNew = True  
            teamId = '' 
            teamData = {'Team__c': team }
            teamData['Branch__c']=teamBR
            teamData['Name']=teamBR
            teamData['Stream__c']=stream
            teamData['Status__c']=status
        else:
            teamData = {'Branch__c': teamBR }
            teamData['Name']=teamBR
            teamData['Stream__c']=stream
            isNew = False
            teamId = teamInfo.get('Id')
        tbStatus = teamInfo.get('Status__c',status)
    
        sfTBLs = tbrObj.getData('Branch_Team_Link__c')
        if len(sfTBLs) == 0:  print '  No existing TB is linked to %s in %s'%(teamBR, stream)
        else:   print '  %s existing TB(s) are linked to %s in %s with status %s'%(len(sfTBLs),teamBR,stream, tbStatus)
        tbInfos = {}
        for tblInfo in sfTBLs:
            tbId = tblInfo.get('Task_Branch__c','')
            tbInfo = sfb.getTBInfoById(tbId)
            if tbInfo in [None,{}]: 
                sfb.setLog('Failed to get TaskBR info for %s'%(tbId),'warn')
                continue
            tbSub   = tbInfo.get('Name')
            tbranch = tbInfo.get('Branch__c')
            tbStat  = tbInfo.get('Branch_Status__c')
            tbInfos[tbranch] = {'tbId':tbId, 'status':tbStat, 'subject':tbSub}
        branches = tbInfos.keys()
        #print '  branches are %s'%branches
        updateList = []
        if options.mdesc is True:
            msg = "\nPlease enter the specific MERGE Instructions for this Task Branch"
            teamData['Merge_Details__c'] = inputTextFromCmdline(msg)
            updateList.append('Merge Details')
        if options.desc is True:
            msg = "\nPlease enter the general comments for this Task Branch"
            teamData['Details__c'] = inputTextFromCmdline(msg)
            updateList.append('General Comments')
        if options.priority not in [None,'']:
            priority = options.priority.lower()
            if priority in ['low', 'medium', 'high', 'urgent', 'critical']:
                teamData['Priority__c'] = priority
                updateList.append('Priority')
            else:
                print 'You entered an unknown priority %s, the Branch will default to medium'%options.priority
        if isNew:
            print '  Creating a new Team Branch for %s in code stream %s\n'%(teamBR,stream)
            #print 'Based on your information the %s attributes will be updated\n'%(','.join(updateList))
    
            taskCheck = sfb.checkIntrudingTaskBr(teamBR, stream)
            if taskCheck is not None:
                print ' A task branch having the name %s in %s already exists and' \
                      %(teamBR, stream)
                print ' Cannot be removed. This team branch cannot be created.'
                sys.exit(1)
                
        else:
            print '  Updating the Team Branch %s in code stream %s\n'%(teamBR,stream)
            #print 'Based on your information the %s attributes will be updated\n'%(','.join(updateList))
        
        sfId = tbrObj.setTeamBranch(tbId=teamId, teamBR=teamBR, stream=stream, data=teamData)
        tbInfo = tbrObj.getData('Team_Branch__c')
        teamId = tbInfo.get('Id')
        teamStatMap = statMap.get(tbStatus)
        if teamId != sfId: 
            print 'setTeamBranch returned %s and getData returned %s'%(sfId,teamId)
            #print 'tbrObj.data %s'%tbInfo
    
        brObj = SFTaskBranch(sfTool=sfb)
        for br in brList:
            if br in branches:
                print '  Skipping %s.\nTask Branch is already linked to target Team Branch.'%(br)
                continue
    
            if options.debug > 1:
                sfb.setLog('Checking for %s in %s'%(br,stream),'info')
                pass
            
            info = brObj.checkLoad(br, stream)
            #print 'Loading branch:%s as %s'%(br,info)
            brInfo = brObj.getData('Task_Branch__c')
            btlList = brObj.getData('Branch_Team_Link__c')
            baList = brObj.getData('Branch_Approval__c')
            
            if len(btlList):
                msg = "Skipping %s.\nTask Branch is already linked to a Team Branch." %br
                print msg
                continue
            
            if brInfo in [None,{}]:
                print 'No Information found in codestream %s for the branch %s'%(stream,br)
                print '  This branch will be skipped. Please, try with another branch and stream.'
                #print 'All Data:%s\n'%brObj.getData()
                continue
            
            brId   = brInfo.get('Id')
            numCRs = brInfo.get('Num_CRs__c')
            brStat = brInfo.get('Branch_Status__c')
            brStatMap = statMap.get(brStat)
    
            # check that branch is not already submitted to SCM unless scm flag
            # is True
            if brStatMap.get('order') >= 36.0 and scmFlag is False:
                print "This branch has already progressed into SCM so you may not link it to a"
                print "team branch. Please contact salesforce-support@molten-magma.com or cm@molten-magma.com"
                print "for assistance."
                sys.exit()
            elif brStatMap.get('order') >= 36.0 and scmFlag is True:
                # remove the token file
                tokens = tokenFile.findTokensFromBranch(branch)
                numTokens = len(tokens)
    
                if numTokens == 1:
                    # only one token - just move it
                    token = tokens[0]
                    token.move(tokenFile.replacedTokenDir)
                    print "One token for this branch was found:\n"
                    print token.formatPaths()
                    print "\nIt has been moved aside to:"
                    print tokenFile.replacedTokenDir
                elif numTokens > 1:
                    print "More than one token was found for this branch. "
                    print "Review each one and indicate whether you'd like to move it aside.\n"
                    
                    for token in tokens:
                        # more than one token - ask about each one
                        print token.formatPaths()
                        msg = "Would you like to move this token aside? <y/N>"
                        response = inputLineFromCmdline(msg)
                        if response is not None:
                            response = response.strip()
                        if response in ['y','Y']:
                            token.move(tokenFile.replacedTokenDir)
                            print "\nIt has been moved aside to:"
                            print tokenFile.replacedTokenDir
                            print
                        else:
                            print "This token will be left in place.\n"
                            pass
                        continue
                    pass
                pass
            
    
    
            # determine the proper status for the task branch after linking
            origBrStat = brStat
            if teamStatMap.get('order') < 44.0:
                if brStatMap.get('order') >= 36.0:
                    # task branch is approved, but team branch is still in process
                    brStat = 'Approved, pending Team Branch'
                else:
                    # the current brStat is correct, leave it alone.
                    pass
            else:
                # use the team branch's status
                brStat = tbStatus
                pass
            
            # update the task branch status if status change is necessary
            if origBrStat != brStat:
                brObj.setBranchStatus(status=brStat)
                pass
            
            name = 'Link to view'
            data = {'Name': name, 'Branch_Status__c':brStat, 'Team__c': team}
            #print ' Ready to create TBL teamId:%s brId:%s brInfo:%s\n' %(teamId,brId,brInfo)
            sfId = tbrObj.setTeamBranchLink(tbId='', teamId=teamId, brId=brId, data=data)
            tbInfos[br] = {'tbId':sfId, 'status':brStat, 'subject':name}
    
            # cross-link the AE BAs here...
            for ba in baList:
                if ba.get('Approval_Role__c','') == 'CR Originator':
                    data = {'Branch__c': brInfo.get('Name')}
                    baId = brObj.setBranchApproval(ba.get('Id'), brId, data=data,
                                                   teamId=teamId, setAll=False)
    
        print '\nThere are now %s Task Branches linked to %s in %s, info below:'%(len(tbInfos),teamBR,stream)
        for br, info in tbInfos.items():
            print '  %40s Status:%s'%(br,info.get('status'))
            #print '     Name:%s'%(info.get('subject'))
    
    ##    print 'Now updating Branch Approval rather then waiting for periodic cron script'
    ##    print '\n'
        if checkTmb is True:
            updated = tbrObj.setBranchStatus(tbStatus)
        else:
            print 'Skipping check of team branch.\nRun "check %s -s %s"\nafter you are finished linking' %(teamBR, stream)
            pass
    ##    if updated:
    ##        print '  Updated the Team Branch to %s status'%tbStatus
    ##    else:
    ##        print '  Refreshed the Team Branch'
    
    ##    sent = tbrObj.sendNotifyEmail()
    ##    if sent:
    ##        print 'We sent an email to you to confirm this Team branch with a link to Salesforce.'
    

def walkTeamBranchCL(team, teamBR, stream, options, st, teamTool=None):
    """ command line to walk Team Branch and update Task Branch Status
    """
    team = team.lower()
    
    db=options.debug
    # if we were passed a team tool, use it
    if teamTool is None:
        print 'Connecting to SalesForce for the %s team branch %s in code stream %s' %(team,teamBR,stream)
        sfb = SFTeamBranchTool(debug=db, logname='addTmB')
        sfb.getConnectInfo(version,st)
    else:
        sfb = teamTool
        
    if sfb.isValidProductTeam(team) is False:
        print 'The team "%s" is unknown.\nFor a list of known teams, please use the "teams" command. EXITING' %team
        sys.exit(1)

    # need to translate?
    #team = self.devTeamToScmTeam(team)
    
    # default to the "Generic" branch for the specified team if a team branch name
    # isn't provided. The generic team branch has the same name as the team.
    if teamBR in ['', None]:
        teamBR == team

    #taskBrTool = SFTaskBranchTool(debug=db, logname='addTmB')
    tbrObj = SFTeamBranch(sfTool=sfb)
    inlist = tbrObj.loadTeamBranch(teamBR, stream)
    if db>2: tbrObj.showData(target='user')
    crInfos = {}
    teamInfo = tbrObj.getData('Team_Branch__c')
    sfBAs  = tbrObj.getData('Branch_Approval__c')
    status = 'Awaiting Branches'
    if teamInfo in [{}]:
        isNew = True  
        teamId = '' 
        teamData = {'Team__c': team }
        teamData['Branch__c']=teamBR
        teamData['Name']=teamBR
        teamData['Stream__c']=stream
        teamData['Status__c']=status
    else:
        teamData = {'Branch__c': teamBR }
        teamData['Name']=teamBR
        teamData['Stream__c']=stream
        isNew = False
        teamId = teamInfo.get('Id')
    tbStatus = teamInfo.get('Status__c',status)

    sfTBLs = tbrObj.getData('Branch_Team_Link__c')
    if len(sfTBLs) == 0:  print '  No existing TB is linked to %s in %s'%(teamBR, stream)
    else:   print '  %s existing TB(s) are linked to %s in %s with status %s'%(len(sfTBLs),teamBR,stream, tbStatus)

    tbInfos = {}
    for tblInfo in sfTBLs:
        tbId = tblInfo.get('Task_Branch__c','')
        tbInfo = sfb.getTBInfoById(tbId)
        if tbInfo in [None,{}]: 
            sfb.setLog('Failed to get TaskBR info for %s'%(tbId),'warn')
            continue
        tbSub   = tbInfo.get('Name')
        tbranch = tbInfo.get('Branch__c')
        tbStat  = tbInfo.get('Branch_Status__c')
        tbInfos[tbranch] = {'tbId':tbId, 'status':tbStat, 'subject':tbSub}
    branches = tbInfos.keys()
    #print '  branches are %s'%branches

    sfId = tbrObj.setTeamBranch(tbId=teamId, teamBR=teamBR, stream=stream, data=teamData)
    tbInfo = tbrObj.getData('Team_Branch__c')
    teamId = tbInfo.get('Id')
    if teamId != sfId: 
        print 'setTeamBranch returned %s and getData returned %s'%(sfId,teamId)
        #print 'tbrObj.data %s'%tbInfo

    brObj = SFTaskBranch(sfTool=sfb)
    for br in brList:
        if br in branches:
            print '  Skipping %s. This branch is already linked.'%(br)
            continue
        if options.debug > 1: sfb.setLog('Checking for %s in %s'%(br,stream),'info')
        info = brObj.checkLoad(br, stream)
        #print 'Loading branch:%s as %s'%(br,info)
        brInfo = brObj.getData('Task_Branch__c')
        if brInfo in [None,{}]:
            print 'No Information found in codestream %s for the branch %s'%(stream,br)
            print '  This branch will be skipped. Please, try with another branch and stream.'
            #print 'All Data:%s\n'%brObj.getData()
            continue
        brId   = brInfo.get('Id')
        numCRs = brInfo.get('Num_CRs__c')
        brStat = brInfo.get('Branch_Status__c')
        name = 'Link to view'
        data = {'Name': name, 'Branch_Status__c':brStat, 'Team__c': team}
        #print ' Ready to create TBL teamId:%s brId:%s brInfo:%s\n' %(teamId,brId,brInfo)
        sfId = tbrObj.setTeamBranchLink(tbId='', teamId=teamId, brId=brId, data=data)
        tbInfos[br] = {'tbId':sfId, 'status':brStat, 'subject':name}
        
    print '\nThere are now %s Task Branches linked to %s in %s, info below:'%(len(tbInfos),teamBR,stream)
    for br, info in tbInfos.items():
        print '  %40s Status:%s'%(br,info.get('status'))
        #print '     Name:%s'%(info.get('subject'))

    #print 'Now updating Branch Approval rather then waiting for periodic cron script'
    print '\n'
    updated = tbrObj.setBranchStatus(status)
    if updated:
        print '  Updated the Team Branch to %s status'%status
    #sent = tbrObj.sendNotifyEmail()
    #if sent:
    #    print 'We sent an email to you to confirm this Team branch with a link to Salesforce.'



def unlinkTeamBranchCL(team, teamBR, stream, branch, options, st):
    """ command line to unlink Task Branch from Team Branch
    """
    
    listBranchPath = None
    
    if options is not None:
        debug = options.debug
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
        team = team.lower()
        db=options.debug
        print 'Connecting to SalesForce for the %s team branch %s in code stream %s' %(team,teamBR,stream)
        sfb = SFTeamBranchTool(debug=db, logname='rmTmB')
        if sfb.isValidProductTeam(team) is False:
            print 'The team "%s" is unknown.\nFor a list of known teams, please use the "teams" command. EXITING' %team
            sys.exit(1)
    
        # translate team name to SCM team alias
        team = sfb.devTeamToScmTeam(team)
        
        # default to the "Generic" branch for the specified team if a team branch name
        # isn't provided. The generic team branch has the same name as the team.
        if teamBR in ['', None]:
            teamBR == team
    
        tbrObj = SFTeamBranch(sfTool=sfb)
        inlist = tbrObj.loadTeamBranch(teamBR, stream)
        if db>2: tbrObj.showData(target='user')
        crInfos = {}
        teamInfo = tbrObj.getData('Team_Branch__c')
        sfBAs  = tbrObj.getData('Branch_Approval__c')
        sfTBLs = tbrObj.getData('Branch_Team_Link__c')
        tbStatus = teamInfo.get('Status__c')
        
        if len(sfTBLs) == 0:  
            print '  No existing TB are linked to %s in %s'%(teamBR, stream)
            sys.exit(1)
        else:   
            print '  %s existing TB(s) are linked to %s in %s with status %s'%(len(sfTBLs),teamBR,stream, tbStatus)
    
        tbInfos = {}
        branchID = ''
        for tblInfo in sfTBLs:
            tbId = tblInfo.get('Task_Branch__c','')
            tblId = tblInfo.get('Id')
            tbInfo = sfb.getTBInfoById(tbId)
            if tbInfo in [None,{}]: 
                msg = 'Failed to get TaskBR info for %s'%(tbId)
                sfb.setLog(msg,'warn')
                print msg
                continue
            tbSub   = tbInfo.get('Name')
            tbranch = tbInfo.get('Branch__c')
            tbStat  = tbInfo.get('Branch_Status__c')
            tbInfos[tbranch] = {'tbId':tbId, 'status':tbStat, 'subject':tbSub}
            if tbranch == branch:
                branchID = tbId
                sfid = sfb.delete([tblId])
                print 'Deleted Task Branch Link for branch %s from Team Branch %s'%(branch,sfid)
                
        for baInfo in sfBAs:
            baId = baInfo.get('Id')
            baTbId = baInfo.get('Task_Branch__c')
            if branchID == baTbId:
                sfid = sfb.delete([baId])
                print 'Deleted Branch Approval for branch %s from Team Branch %s'%(branch,sfid)
                
        print '\nThere are now %s Task Branches linked to %s in %s, info below:'%(len(tbInfos),teamBR,stream)
        for br, info in tbInfos.items():
            print '  %40s Status:%s'%(br,info.get('status'))
    



###################################################################################
def setTeamBranchUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = '%s\n' %err
    m += '  This script set the status of a Team Branch within Salesforce.\n'
    m += '    Use one of the forms below to meet your needs.\n'
    m += ' \n'
    m += ' Set the team branch status to "Team Branch Hold":\n'
    m += '    teamsethold -s4.1 -t<Team_branch>\n'       
    m += ' \n'
    m += ' Set the team branch status to "Team-Building-Testing":\n'
    m += '    teamsettest -s4.1 -t<Team_branch>\n'       
    m += ' \n'
    m += ' Give Branch Manager approval to all task branches in the team branch:\n'
    m += '    teamsubmitbranch -s4.1 -t<Team_branch>\n'       
    m += ' \n'
    return m


def setTeamBranchCL(team, stream, options, st):
    """ command line logic for setTeamBranch 
    """
    db=options.debug
    newStatus = options.parm

    # check that status is one of the acceptable options
    #...
    
    #print 'Connecting to SalesForce for the %s team branch %s in code stream %s' %(team,teamBR,stream)
    sfb = SFTeamBranchTool(debug=db, logname='setTmB')
    tbrObj = SFTeamBranch(sfTool=sfb)
    sfb.getConnectInfo(version,st)

    tbrObj.loadTeamBranch(team, stream)

    # sanity check tbr status - don't allow cmdline status changes after tbr goes to SCM
    status = tbrObj.getData('Team_Branch__c').get('Status__c','')
    tbStatMap = SFTaskBranchStatus().getStatusMap()
    statMap = tbStatMap.get(status, {})
    order = statMap.get('order', 0.0)

    if order < 36.8:
        print "Error: This team branch has an unsupported status."
        print "Please contact salesforce-support@molten-magma.com with the command you were attempting to run"
        sys.exit(1)
        
    elif order >= 44.0:
        print "Error: This team branch may no longer be modified using this script."
        print "Please contact salesforce-support@molten-magma.com with the command you were attempting to run"
        sys.exit(1)

    else:
        # all's OK
        print 'Updated Team Branch status to %s for %s in %s'%(newStatus,team,stream)
        update = tbrObj.setBranchStatus(newStatus, st)

def setTeamQorStateUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = '%s\n\n' %err
    m += '  This script set the status of a Team Branch QOR bin in Salesforce.\n'
    m += '    Use one of the forms below to meet your needs.\n'
    m += ' \n'
    m += ' Set the sf team\'s blast5_sf1 QOR bin to "SCM-QOR Testing":\n'
    m += '    teamqortest -s blast5 -n sf --tb blast5_sf1\n'       
    m += ' \n'
    m += ' Set the sf team\'s blast5_sf1 QOR bin to "SCM-QOR Result":\n'
    m += '    teamqorresult -sblast5 -n sf --tb blast5_sf1\n'       
    m += ' \n'
    m += ' Set the sf team\'s blast5_sf1 QOR bin back to "SCM-QOR Building":\n'
    m += '    teamqorbuild -sblast5 -n sf --tb blast5_sf1\n'       
    m += ' \n'
    return m

def setTeamQorStateCL(team, ccteambr, stream, newStatus, options, st):
    """
    Alter the status of a team branch QOR bin
    """
    db=options.debug

    # load the team branch holding bin
    sfb = SFTeamBranchTool(debug=db, logname='TmBHold')
    sfb.getConnectInfo(version,st)
    
    # Make sure we have a known team's name
    team = team.lower()
    scmteam = sfb.devTeamToScmTeam(team)
    if scmteam is None:
        print 'The team named %s is unknown.' %team
        print 'Please use the "teams" script to view the list of valid team names'
        sys.exit(1)
        pass
    
    team = scmteam

    tbrObj = SFTeamBranch(sfTool=sfb)

    # attempt to load a team branch having the name of the team holding bin
    teamQorName = "%s_%s_QOR" %(team, ccteambr)
    tmbInfo = tbrObj.loadTeamBranch(teamQorName, stream)
    if tmbInfo[0] == 0:
        # no team branch with the generic team label found - log & bail
        msg = 'No team holding bin found for %s in %s. EXITING.' \
              %(team, stream)
        print '\n%s' %msg
        sfb.setLog(msg, 'error')
        sys.exit()
    
    # sanity check tbr status - don't allow cmdline status changes after tbr goes to SCM
    status = tbrObj.getData('Team_Branch__c').get('Status__c','')
    tbStatMap = SFTaskBranchStatus().getStatusMap()
    statMap = tbStatMap.get(status, {})
    newStatMap = tbStatMap.get(newStatus, {})
    order = statMap.get('order', 0.0)
    newOrder = newStatMap.get('order', 0.0)

    respin = False
    if order < 38.0:
        print "Error: This team branch has an unsupported status."
        print "Please contact salesforce-support@molten-magma.com with the command you were attempting to run"
        sys.exit(1)
        
    elif order >= 47.9:
        print "Error: This team branch may no longer be modified using this script."
        print "Please contact salesforce-support@molten-magma.com with the command you were attempting to run"
        sys.exit(1)
    else:
        if newOrder < order and order != 47.8:
            # detect back-motion here and log a QOR respin
            respin = True
            pass
        
        update = tbrObj.setBranchStatus(newStatus, st=st, qorrespin=respin)
        print 'Updated Team Branch status to %s for %s in %s' \
              %(newStatus,team,stream)
        pass
    return
        
def sweepTeamHoldUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = ''
    
    if len(err):
        m += '%s\n\n' %err
        
    m += 'Set the status of a Team Branch to Team Branch Hold within Salesforce.\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    teamhold -s <stream> -n <team name>\n\n'       
    m += '    teamhold -s <stream> -n <team name> -l </path/to/branch/list/file>\n'       
    m += '\n'
    m += 'Notes:\n'
    m += '    For a list of valid team names, use the "teams" script\n\n'
    m += '    If using the -l argument to specify a file of branch names (one per line),\n'
    m += '    only branches found in that file will be moved to Team Branch Hold\n'
    return m

def sweepTeamHoldCL(team, stream, options=None):
    """
    Takes all task branches which are 'ready' (i.e., PE approved)
    and places them into the respective team's holding branch instead.
    """
    sfb = SFTeamBranchTool()
    origteam = team
    team = sfb.devTeamToScmTeam(team)
    
    if team is None:
        print 'The team "%s" is unknown.\nFor a list of known teams, please use the "teams" command. EXITING' %origteam
        sys.exit(1)
        pass
    
    holdBrStatus = "Team Branch Hold"
    teamHoldName = "%s_Hold" %team
    baTriggerStates = ['Task Branch Ready']
    baNewStatus = 'Team Approving'

    num = sweepTeamBranchFlow(team, teamHoldName, stream,
                              baTriggerStates=baTriggerStates,
                              baNewStatus=baNewStatus,
                              destTeamBrStatus=holdBrStatus, options=options,
                              logname='sf.TmBhold')

    print "Moved %d task branches from the %s team receiving branch to the holding branch" %(num, team) 

def sweepTeamQorUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = ''
    
    if len(err):
        m += '%s\n\n' %err
        
    m += 'Sweep task branches from a team\'s holding bin to the QOR bin\n'
    m += 'within Salesforce.\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    teamqor -s <stream> -n <team name> --tb <clearcase team branch>\n\n'       
    m += '    teamqor -s <stream> -n <team name> --tb <clearcase team branch> \\\n       -l </path/to/branch/list/file>\n'       
    m += '\n'
    m += 'Notes:\n'
    m += '    For a list of valid team names, use the "teams" script\n\n'
    m += '    If using the -l argument to specify a file of branch names (one per line),\n'
    m += '    only branches found in that file will be moved to Team Branch QOR\n'
    return m

def sweepTeamQorCL(team, ccteambr, stream, options=None):
    """ Takes all task branches in the holding bin for a team and sweep them to
    the QOR bin. Create bin if it doesn't yet exist.
    """
    sfb = SFTeamBranchTool()
    origteam = team
    team = sfb.devTeamToScmTeam(team)
    
    if team is None:
        print 'The team "%s" is unknown.\nFor a list of known teams, please use the "teams" command. EXITING' %origteam
        sys.exit(1)
        pass
    
    qorBrStatus = "SCM-QOR Building"
    teamHoldName = "%s_Hold" %team
    teamQorName = "%s_%s_QOR" %(team, ccteambr)
    #baTriggerStates = ['Task Branch Ready']
    baNewStatus = 'Team Approving'
    
    num = sweepTeamBranchFlow(teamHoldName, teamQorName, stream,
                              baNewStatus=baNewStatus,
                              destTeamBrStatus=qorBrStatus, options=options,
                              logname='sf.TmBqor')

    #print "Moved %d task branches from the %s team holding bin to QOR bin %s" %(num, team, ccteambr)
    return
## END sweepTeamQorCl

def teamSubmitBranchUsage(err=''):
    """  Prints the Usage() statement for this method    """
    # redo for submitTeamBranch
    m = ''
    
    if len(err):
        m += '%s\n\n' %err
        
    m += 'Submits a Team Branch QOR bin for merge into a build by assigning a\n'
    m += 'checkpoint name and creating a token file in sf-scm.\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    teamsubmitbranch -s <stream> -n <team name> -t <team branch>   \\\n'
    m += '                --tb <clearcase team branch>\n\n'
    m += '    teamsubmitbranch -s <stream> -n <team name> -t <team branch>   \\\n'
    m += '                --tb <clearcase team branch> -l </path/to/branch/list/file>\n\n'
    return m

def sweepTeamSubmitCL(team, stream, ckpntTmbName, options=None):
    """
    Takes all task branches which are Team Mgr. Approved in the team's
    holding branch and moves them to a checkpoint branch for submission to
    SCM
    """
    sfb = SFTeamBranchTool()
    origteam = team
    team = sfb.devTeamToScmTeam(team)
    
    if team is None:
        print 'The team "%s" is unknown.\nFor a list of known teams, please use the "teams" command. EXITING' %origteam
        sys.exit(1)
        pass
    
    
    ckpntTmbStatus = "Team-Approved"
    teamHoldName = "%s_Hold" %team
    if hasattr(options, 'approveall') and options.approveall is True:
        # include approved and unapproved states in the sweep
        baTriggerStates = ['Team Approved','Team Approving']
    else:
        # Only include approved team mgr BAs in the sweep
        baTriggerStates = ['Team Approved']
        
    baNewStatus = 'Team Approved'
    
    num = sweepTeamBranchFlow(teamHoldName, ckpntTmbName, stream,
                              baTriggerStates=baTriggerStates,
                              baNewStatus=baNewStatus,
                              destTeamBrStatus=ckpntTmbStatus, options=options,
                              logname='sf.TmBsub')

    print "Moved %d task branches from the %s team holding branch to the checkpoint branch %s" %(num, team, ckpntTmbName)

def moveTeamBranchUsage(err=''):
    """  Prints the Usage() statement for this method    """
    # redo for submitTeamBranch
    m = ''
    
    if len(err):
        m += '%s\n\n' %err
        
    m += 'Moves Task Branches from any Team Branch to another Team Branch\n'
    m += 'within the same code stream\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    teammv -s <stream> -t <source team branch> -u <dest team branch>\n\n'
    m += '    teammv -s <stream> -t <source team branch> -u <dest team branch>\n'
    m += '           -l /path/to/branch/list/file.txt\n'
    m += '\n'
    m += 'Note: This script may take a very long time to complete depending upon\n'
    m += '      how many task branches are in the source and destination team branches\n'
    m += '      and how many task branches are being moved.\n'
    return m



def movePEBranchUsage(err=''):
    """  Prints the Usage() statement for this method    """
    # redo for submitTeamBranch
    m = ''
    
    if len(err):
        m += '%s\n\n' %err
        
    m += 'Moves PE Checkpoint branches from any Team Branch to another Team Branch\n'
    m += 'within the same code stream\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    teammvpe -s <stream> -t <source team branch> -u <dest team branch>\n\n'
    m += '    teammvpe -s <stream> -t <source team branch> -u <dest team branch>\n'
    m += '           -l /path/to/branch/list/file.txt\n'
    m += '\n'
    m += 'Note: This script may take a very long time to complete depending upon\n'
    m += '      how many task branches are in the source and destination team branches\n'
    m += '      and how many task branches are being moved.\n'
    return m

def moveTeamBranchCL(srcTeamBrName, destTeamBrName, stream, options):
    """ Move task branches from any team branch to any other team branch
    within a code stream """
    logname = "sf.tmbMv"
    # check for destination branch first.
    # Ask for confirmation of move if it doesn't exist
    debug = 0
    if options is not None:
        debug = options.debug
    
    sfb = SFTeamBranchTool(debug=debug, logname=logname)
    tbrObj = SFTeamBranch(sfTool=sfb)
    tmbDestInfo = tbrObj.loadTeamBranch(destTeamBrName, stream) 
    tmbData = tbrObj.getData('Team_Branch__c')

    if tmbData in BAD_INFO_LIST:
        msg  = "Team branch %s in code stream %s not found.\n" \
               %(destTeamBrName, stream)
        msg += "You may only move task branches to a team branch which already exists.\n"
        msg += "Exiting.\n"
        print msg
        sys.exit(1)

        pass

    num = sweepTeamBranchFlow(srcTeamBrName, destTeamBrName, stream,
                              options=options, logname=logname)

    #print "Moved %d task branches from %s team branch\nto %s team branch in stream %s." %(num, srcTeamBrName, destTeamBrName, stream)
    return

def generateSCMToken():
    logname = "sf.genTokn"
    debug = 0
    sfb = SFTeamBranchTool(debug=debug, logname=logname)
    tbrObj = SFTeamBranch(sfTool=sfb)
    #where = [['Generate_scm_Token__c', '=', True]]]
    where =[['Generate_scm_Token__c', '=', True], 'and',['Status__c','=','Submitted to SCM']]
    res = sfb.query('Team_Branch__c', where=where, sc='all')
            
    for rs in res:
        team=rs.get('Name')            
        stream=rs.get('Stream__c') 
        tmId=rs.get('Id')
        tbrObj.submitToSCM(team, stream,st=0)         
        newTeamData = {'Id': tmId,
                  'Generate_scm_Token__c': False}
        res = sfb.update('Team_Branch__c', newTeamData)        
                  
    pass
    
    
    

def movePEBranchCL(srcTeamBrName, destTeamBrName, stream, options):
    """ Move task branches from any team branch to any other team branch
    within a code stream """
    logname = "sf.tmbPEMv"
    # check for destination branch first.
    # Ask for confirmation of move if it doesn't exist
    debug = 0
    if options is not None:
        debug = options.debug
    
    sfb = SFTeamBranchTool(debug=debug, logname=logname)
    tbrObj = SFTeamBranch(sfTool=sfb)
    tmbDestInfo = tbrObj.loadTeamBranch(destTeamBrName, stream) 
    tmbData = tbrObj.getData('Team_Branch__c')
    tmDesId=tmbData.get('Id')
    tmbDestInfo = tbrObj.loadTeamBranch(srcTeamBrName, stream)
    tmbSrcData = tbrObj.getData('Team_Branch__c')
    tmSrcId=tmbSrcData.get('Id')
    teamSrcBAs = tbrObj.getData('Branch_Approval__c')
    teamSrcBAs = copy.deepcopy(teamSrcBAs)
    teamReadyBAs = []
    for ba in teamSrcBAs:          
        if ba.get('Approval_Role__c','') == 'Team Manager':            
            
            # We don't care about the Team Mgr BA
            teamReadyBAs.append(ba)            
            pass
        continue
    
        
    taskBranchIdList = []
    for ba in teamReadyBAs:
        taskBranchId = ba.get('Task_Branch__c', None)
        if taskBranchId is not None and taskBranchId not in taskBranchIdList:
            taskBranchIdList.append(taskBranchId)
            pass
        continue
    
    # retrieve the names into a map by ID
    taskBranchNameMap = {}
    tbFields = ('Id', 'Branch__c')
    res = sfb.retrieve(taskBranchIdList, 'Task_Branch__c', tbFields)
    if res not in BAD_INFO_LIST:
        for tb in res:
            taskBranchNameMap[tb.get('Id')] = tb.get('Branch__c')
            continue
        pass
    
        
    #print "Team Data %s *******************"%tmbData

    if tmDesId in BAD_INFO_LIST:
        msg  = "Team branch %s in code stream %s not found, Hence creating new team branch.\n" \
               %(destTeamBrName, stream)
        
        print msg       
        teamDestData = {}
        teamSrcId = tmbSrcData.get('Id')
        teamSrcOwnerId = tmbSrcData.get('OwnerId')
        teamSrcTeamName = tmbSrcData.get('Team__c','')
        teamDestData['OwnerId'] = teamSrcOwnerId
        teamDestData['Team__c'] = teamSrcTeamName 
        teamDestData['Branch__c'] = destTeamBrName
        teamDestData['Name'] = destTeamBrName
        teamDestData['Stream__c'] = stream
        """if destTeamBrStatus is not None:
            teamDestData['Status__c'] = destTeamBrStatus"""
        teamDestData['Status__c'] = 'Awaiting Branches'
                            
        teamDestBrId = tbrObj.setPETeamBranch(tbId='', teamBR=destTeamBrName,
                                            stream=stream,
                                            data=teamDestData)
                
        if teamDestBrId in BAD_INFO_LIST:
            msg = "Failed to create new Team branch %s. Bailing." \
                  %destTeamBrName
            print msg
            if debug > 0: print msg
            sfb.setLog(msg, 'error')
            return 0
        else:
            createdTbFlag = True    
            tmDesId = teamDestData.get('Id')
        
    else:
        msg= "Team branch exist.......%s " %destTeamBrName
        sfb.setLog(msg, 'debug')
        pass
    
    listBranchPath = None
    pebranchList=[]
    branchList=[]
    if options is not None:
        debug = options.debug
        listBranchPath = options.listBranchPath
        pass

    # process listBranchPath to result in a list of branch names
    if listBranchPath is not None:
        # no list passed in, check options for file to parse
        pebranchList = parseBranchListFile(listBranchPath)    
    else:               
        #where = [['Name ', '=', srcTeamBrName], 'and',['Stream__c ','=',stream]]
        where = [['Team_Branch__c', '=', tmSrcId]]
        res = sfb.query('Checkpoint_Branch__c', where=where, sc='all')
        for rs in res:
            peName=rs.get('Name')            
            pebranchList.append(peName)            
        pass
    
   
    for pebr in pebranchList:
        pename=pebr        
        where = [['Name', '=', pename], 'and',['Stream__c','=',stream]]
        res1 = sfb.query('Checkpoint_Branch__c', where=where, sc='all')        
        for rs1 in res1:
            peId=rs1.get('Id')            
            where = [['PE_Checkpoint__c', '=', peId]]
            queryList = sfb.query('Task_Branch__c', where=where, sc='all')
            
            newPeData = {'Id': peId,
                  'Team_Branch__c': tmDesId}
            res = sfb.update('Checkpoint_Branch__c', newPeData)
            
            for qr in queryList:
                tbName=qr.get('Name')
                branchList.append(tbName)              
            
        
    skipBarnchList=[]
    for  ba in teamReadyBAs:
        taskBranchId = ba.get('Task_Branch__c', None)        
        #print "TaskBranch ID: %s" %taskBranchId        
        taskBranchName = taskBranchNameMap.get(taskBranchId)
        if taskBranchName in branchList:
            skipBarnchList.append(taskBranchName)
            pass
        
    #print "skipBarnchList ..... %s " %skipBarnchList
        

    num = sweepTeamBranchFlow(srcTeamBrName, destTeamBrName, stream,
                              options=options, logname=logname,branchList=skipBarnchList)

    #print "Moved %d task branches from %s team branch\nto %s team branch in stream %s." %(num, srcTeamBrName, destTeamBrName, stream)
    return

    
def sweepTeamBranchFlow(srcTeamBrName, destTeamBrName, stream,
                        baTriggerStates=None, baNewStatus=None,
                        destTeamBrStatus=None, options=None, logname=None,
                        branchList=None):
    """
    General flow for moving task branches from one team branch to another.

    - srcTeamBrName - name of the team branch to move from
    - destTeamBrName - name of the team branch to move to
    - stream - the code stream in which we're operating
    - baTriggerStates - Optional list of states which TeamMgrBA must be in
                        in order to move its task branch
    - baNewStatus - Opt. status the Team Mgr BA should be set to once the
                    task branch has been moved

    - destTeamBrStatus - Opt. status destination team branch should be set to
    """
    
    #print "BRANCH LIST.....  ..... %s  Source team name ....%s dest team name %s " %(branchList,srcTeamBrName,destTeamBrName)
    st = time.time()

    debug = 0
    listBranchPath = None
    if options is not None:
        debug = options.debug
        listBranchPath = options.listBranchPath
        pass

    # process listBranchPath to result in a list of branch names
    if branchList is None:
        # no list passed in, check options for file to parse
        branchList = parseBranchListFile(listBranchPath)
    #elif branchList not in [ListType, TupleType]:
    
    elif ((type(branchList) != types.ListType)):
        # brachList passed in, but not a list. Try making it a list
        branchList = list([branchList])
        pass
    
    
    if logname is None:
        logname = 'sf.TmBSweep'

    sfb = SFTeamBranchTool(debug=debug, logname=logname)
    sfb.getConnectInfo(version,st)
    tbrObj = SFTeamBranch(sfTool=sfb)

    msg  = "filter list of branches provided for this sweep operation is:\n"
    msg += "%s" %branchList
    sfb.setLog(msg, 'debug')

    # load the source team branch (with just the team name)
    tmbInfo = tbrObj.loadTeamBranch(srcTeamBrName, stream)    
    
    teamSrcData = tbrObj.getData('Team_Branch__c')
    if teamSrcData in BAD_INFO_LIST:
        # no team branch with the generic team label found - log & bail
        msg = 'No team branch object found for %s in %s. EXITING.' \
              %(srcTeamBrName, stream)
        print '\n%s' %msg
        sfb.setLog(msg, 'error')
        sys.exit()
    
    teamSrcBrLinks = tbrObj.getData('Branch_Team_Link__c')
    teamSrcBAs = tbrObj.getData('Branch_Approval__c')
    
    # make sure we have an indelible copy.
    teamSrcData = copy.deepcopy(teamSrcData)
    teamSrcBrLinks = copy.deepcopy(teamSrcBrLinks)
    teamSrcBAs = copy.deepcopy(teamSrcBAs)

    teamSrcId = teamSrcData.get('Id')
    teamSrcOwnerId = teamSrcData.get('OwnerId')
    teamSrcTeamName = teamSrcData.get('Team__c','')

    # Do we have any task branches ready to be swept forward?
    # Team Manager BA would be status "Task Branch Ready"
    teamReadyBAs = []
    for ba in teamSrcBAs:          
        if ba.get('Approval_Role__c','') == 'Team Manager':            
            if baTriggerStates is not None:
                # Team Mgr BA Must be in specified status
                # and not have Approve: set to Reject
                if ba.get('Status__c','') in baTriggerStates \
                       and ba.get('Approve__c','') != 'Reject':
                    teamReadyBAs.append(ba)
            else:
                # We don't care about the Team Mgr BA
                teamReadyBAs.append(ba)
                pass
            pass
        continue
    

    createdTbFlag = False
    if len(teamReadyBAs):
        # now, try to load the team holding bin branch
        tmbInfo = tbrObj.loadTeamBranch(destTeamBrName, stream)    
        teamDestData = tbrObj.getData('Team_Branch__c')

        if teamDestData in BAD_INFO_LIST:
            # gotta create the team hold branch
            teamDestData = {}
            teamDestData['OwnerId'] = teamSrcOwnerId
            teamDestData['Team__c'] = teamSrcTeamName 
            teamDestData['Branch__c'] = destTeamBrName
            teamDestData['Name'] = destTeamBrName
            teamDestData['Stream__c'] = stream
            if destTeamBrStatus is not None:
                teamDestData['Status__c'] = destTeamBrStatus
                
            teamDestBrId = tbrObj.setTeamBranch(tbId='', teamBR=destTeamBrName,
                                                stream=stream,
                                                data=teamDestData)
            if teamDestBrId in BAD_INFO_LIST:
                msg = "Failed to create new Team branch %s. Bailing." \
                      %destTeamBrName
                if debug > 0: print msg
                sfb.setLog(msg, 'error')
                return 0
            else:
                createdTbFlag = True


        else:
            teamDestBrId = teamDestData.get('Id')
    else:
        # Nothing to do for this branch!
        return 0

    # collect all the task branch names with a single retrieve call
    taskBranchIdList = []
    for ba in teamReadyBAs:
        taskBranchId = ba.get('Task_Branch__c', None)
        if taskBranchId is not None and taskBranchId not in taskBranchIdList:
            taskBranchIdList.append(taskBranchId)
            pass
        continue
    
    # retrieve the names into a map by ID
    taskBranchNameMap = {}
    tbFields = ('Id', 'Branch__c')
    res = sfb.retrieve(taskBranchIdList, 'Task_Branch__c', tbFields)
    if res not in BAD_INFO_LIST:
        for tb in res:
            taskBranchNameMap[tb.get('Id')] = tb.get('Branch__c')
            continue
        pass

    # Here's where we actually move the task branches from the source
    # team branch to the destination team branch
    numSwept = 0    
    
    for ba in teamReadyBAs:
        
        taskBranchId = ba.get('Task_Branch__c', None)        
        #print "TaskBranch ID: %s" %taskBranchId        
        taskBranchName = taskBranchNameMap.get(taskBranchId)
        #print "Task Branch Name: %s" %taskBranchName
        
        #print "BRANCH LIST 2 %s  " %branchList


        if branchList is not None:
            # we were provided a list of branch names to allow
            # is this branch in it? ADD lower() HERE TO MAKE CASE INSENS.
            #print "taskBranchName  ...... %s " %taskBranchName
            if taskBranchName not in branchList:
                #print "LEAVING taskBranchName %s " %taskBranchName
                # we're looking to include only task branches named in the
                # list for the sweep action. Skip branch if not in the list.
                msg = "leaving %s in %s; stream %s" \
                      %(taskBranchName, srcTeamBrName, stream)
                sfb.setLog(msg, 'debug')
                continue
            pass

        msg = "sweeping %s from %s to %s in stream %s" \
              %(taskBranchName, srcTeamBrName, destTeamBrName, stream)
        sfb.setLog(msg, 'debug')
        
        # find original branch team link to this task branch
        origBTLData = None
        for btl in teamSrcBrLinks:
            if btl.get('Task_Branch__c','') == taskBranchId:
                origBTLData = btl

        if origBTLData is None:
            msg = 'No Branch_Team_Link__c found between task branch %s and source team branch %s' %(taskBranchId, teamSrcId)
            if debug> 0:  print msg
            sfb.setLog(msg, 'error')
            continue

        # bring over data from origBTLink
        newBTLData = {}
        newBTLData['Branch_Status__c'] = origBTLData.get('Branch_Status__c','')
        newBTLData['Team__c'] = origBTLData.get('Team__c','')
        #newBTLData['User__c'] = origBTLData.get('User__c','')
        
        # Create new branch team link between the task branch for this BA
        # and the teamHoldBrId
        newBTLId = tbrObj.setTeamBranchLink('', teamDestBrId, taskBranchId,
                                            newBTLData)

        if newBTLId in BAD_INFO_LIST:
            msg = 'Failed to create new branch-team link between task branch %s and destination team branch %s' %(taskBranchId, teamDestBrId)
            if debug> 0:  print msg
            sfb.setLog(msg, 'error')
            continue

        # Delete old branch team link
        res = sfb.delete([origBTLData.get('Id')])
        if res in BAD_INFO_LIST:
            msg = 'Failed to delete old branch-team link %s between task branch %s and source team branch %s' \
                  %(origBTLData.get('Id'), taskBranchId, teamSrcId)
            if debug> 0:  print msg
            sfb.setLog(msg, 'error')
            # no need to continue here...
        
        # Jigger Team Mgr branch approval so it links to the teamHoldBrId
        baData = {'Branch__c': destTeamBrName}
        res = tbrObj.setBranchApproval(ba.get('Id'), taskBranchId, data=baData,
                                       status=baNewStatus, date='now',
                                       teamId=teamDestBrId)
        if res in BAD_INFO_LIST:
            msg = 'Failed to update Team Mgr BA %s with destination team branch %s' %(ba.get('Id'), teamDestBrId)

        numSwept += 1

    if numSwept > 0:
        # set/eval the dest team branch - don't change it's status.
        tbrObj.refresh()
        #pprint.pprint(tbrObj.getData())
        tbrObj.setBranchStatus()

        # now, re-eval the source team branch in order to clean up the BAs
        tbrObj.loadTeamBranch(srcTeamBrName, stream)    
        tbrObj.setBranchStatus()
        pass
    elif numSwept == 0 and createdTbFlag is True:
        tbrObj.delete()
        pass
        
    msg = "Moved %d task branches from %s\n to %s in stream %s" \
          %(numSwept, srcTeamBrName, destTeamBrName, stream)
    sfb.setLog(msg, 'info')
    print msg
        
    return numSwept


def submitTeamBranchCL(team, ccteambr, stream, tmbName, options, st):
    # attempt to load stream, generic team hold branch
    #    rename team branch to tmbName
    # if not, complain and bail
    db=options.debug
    logname = 'TmBSubmit'
    newStatus = "Team-Approved"
    teamHoldName = "%s_Hold" %team
    teamQorName = "%s_%s_QOR" %(team, ccteambr)
    holdBrStatus = "Team Branch Hold"
    baNewStatus = 'Team Approving'
    #print "Team QOR NAME....%s" %teamQorName
    
    # load the generic team branch
    sfb = SFTeamBranchTool(debug=db, logname=logname)
    sfb.getConnectInfo(version,st)

    # Make sure we have a known team's name
    scmteam = sfb.devTeamToScmTeam(team)
    if scmteam is None:
        print 'The team named %s is unknown.' %team
        print 'Please use the "teams" script to view the list of valid team names'
        sys.exit(1)
        pass
    
    team = scmteam

    tbrObj = SFTeamBranch(sfTool=sfb)
    

    # first, grab info on the destination team branch (checkpoint)
    destTmbInfo = tbrObj.loadTeamBranch(tmbName, stream)
    
    # attempt to load a team branch having the name of the team
    tmbInfo = tbrObj.loadTeamBranch(teamQorName, stream)
    #print "TEAM QOR DATA %s" %tmbInfo
    if tmbInfo[0] == 0:
        # no team branch with the generic team label found - log & bail
        msg = 'No team branch QOR bin found for %s in %s. EXITING.' %(team, stream)
        print '\n%s' %msg
        sfb.setLog(msg, 'error')
        sys.exit()
        pass
        
    # sanity check tbr status - don't allow cmdline status changes after tbr goes to SCM
    status = tbrObj.getData('Team_Branch__c').get('Status__c','')
    tbStatMap = SFTaskBranchStatus().getStatusMap()
    statMap = tbStatMap.get(status, {})
    order = statMap.get('order', 0.0)

    if order < 38.0:
        print "Error: This team branch has an unsupported status."
        print "Please contact salesforce-support@molten-magma.com with the command you were attempting to run"
        sys.exit(1)
        
    elif order > 47.4:
        print "Error: This team branch may no longer be modified using this script."
        print "Please contact salesforce-support@molten-magma.com with the command you were attempting to run"
        sys.exit(1)

    else:

        # sweep all (or listed branches) forward to checkpoint
        num = sweepTeamBranchFlow(teamQorName, tmbName, stream,
                                  destTeamBrStatus=newStatus,
                                  baNewStatus=baNewStatus,
                                  options=options, logname=logname)
        
        # If -f option is used, sweep any unlisted task branches back to
        # team_Hold
        if hasattr(options, 'listBranchPath') and \
           options.listBranchPath is not None:

            print "Sweeping remaining task branches back to %s" %teamHoldName

            # clear the filter file
            options.listBranchPath = None

            # Now, sweep any branches not in the list file back to
            # team_Hold
            num = sweepTeamBranchFlow(teamQorName, teamHoldName, stream,
                                      destTeamBrStatus=holdBrStatus,
                                      baNewStatus=baNewStatus,
                                      options=options, logname=logname)
            pass

        # Delete the empty team branch
        tbrObj.delete()
        pass
            
        print 'Updated Team Branch status to %s for %s in %s' \
              %(newStatus,team,stream)
        pass
    return


def convertQorCL(team, ccteambr, stream):
    oldTeamQorName = "%s_QOR" %(team)
    newTeamQorName = "%s_%s_QOR" %(team, ccteambr)

    sfb = SFTeamBranchTool(logname='QorCvrt')
    tbrObj = SFTeamBranch(sfTool=sfb)
    tmbInfo = tbrObj.loadTeamBranch(oldTeamQorName, stream) 
    tmbData = tbrObj.getData('Team_Branch__c')

    if tmbData in BAD_INFO_LIST:
        msg  = "Old style QOR bin for %s in code stream %s not found.\n" \
               %(team, stream)
        msg += "Exiting.\n"
        print msg
        sys.exit(1)


    newTmbData = {'Id': tmbData.get('Id'),
                  'Name': newTeamQorName,
                  'Branch__c': newTeamQorName,}

    res = sfb.update('Team_Branch__c', newTmbData)

    if res[0] == tmbData.get('Id'):
        print "Successfully converted the old style QOR bin for %s in %s" \
              %(team, stream)
        pass
    return
## END convertQorCL
                

##def submitBranchCL(branch, stream, query, options):
##    """ command line logic for submitBranch
##    """
##    print 'Connecting to SalesForce for the branch %s in code stream %s' %(branch,stream)
##    st = time.time()
##    db=options.debug
##    sfb = SFTeamBranchTool(debug=db,logname='subTB')
##    brObj = SFTeamBranch(sfTool=sfb)
##    sfb.getConnectInfo(version,st)
##    num = brObj.submitByDev(branch, stream, st)
##    if num >0:
##        print 'Submitted and notified %s users for %s %s'%(num,branch,stream)
##    elif num == -1:
##        print ' No Task Branches were found for %s in stream %s'%(branch,stream)
##        tbInfo = sfb.getBranchMapCC(branch)
##        print ' Info from Clearcase is %s'%tbInfo
##    elif num == 0:
##        print ' No CRs have been linked to the Task Branch %s in stream %s'%(branch,stream)
##    return 0


##########################################################################################################
##def approveBranchUsage(err=''):
##    """  Prints the Usage() statement for this method    """
##    m = '%s\n' %err
##    m += '  This script submits a Team Branch on SalesForce to SCM.\n'
##    m += '    Use one of the forms below or a combination to meet your needs.\n'
##    m += ' \n'
##    m += '    approveBranch -s 4.1 -b <branch_Name> \n'       
##    m += ' \n'
##    m += '      or - indicate you want to be prompted for branch details\n'
##    m += '    approveBranch -s 4.1 -b <branch_Name> -d \n'       
##    m += ' \n'
##    m += '      or - use flags to prompt you for further 255 char detail blocks\n\t\t -o command details, -e risk details \n'
##    m += '    approveBranch -s 4.1 -b <branch_Name> -m -d  \n'       
##    return m

##def approveBranchCL(branch, stream, query, options):
##    """ command line logic for approveBranch
##    """
##    print 'Connecting to SalesForce for the branch %s in code stream %s' %(branch,stream)
##    st = time.time()
##    db=options.debug
##    sfb = SFTeamBranchTool(debug=db,logname='appTB')
##    brObj = SFTeamBranch(sfTool=sfb)
##    sfb.getConnectInfo(version,st)
##    num, role = brObj.approveBranch(branch, stream, st)
##    if num >0:
##        print ' Approved and notified %s users for %s %s'%(num,branch,stream)
##    elif num == -1:
##        print ' No Task Branches were found for %s in stream %s'%(branch,stream)
##        tbInfo = sfb.getBranchMapCC(branch)
##        print ' Info from Clearcase is %s'%tbInfo
##    elif num == 0:
##        print ' No CRs have been linked to the Task Branch %s in stream %s'%(branch,stream)
##    return 0

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
## END parseBranchListFile
    

def teamlsUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = '%s\n' %err
    m += '  This script lists branches linked the specified Team Branches (TmBs) on SalesForce.\n'
    m += '    Use one of the forms below or a combination to meet your needs.\n'
    m += ' \n'
    m += '    teamls -sblast5 -n synthesis (show synthesis team receiving bin in blast5)\n'       
    m += ' \n'
    m += '    teamls -stalus1.0 -t <team branch label> (show team branch in stream talus1.0)\n'
    m += '           append "_Hold" to a team alias to display contents of the holding bin\n'
    m += ' \n'
    m += '    teamls -stalus1.0 -n rtl -xpelist (show RTL Team branches in talus with PE Checkpointoutput)\n'       
    m += ' \n'
    m += '    teamls -stalus1.0  (show team branches in stream talus1.0)\n'       
    m += ' \n'
    m += '    teamls -stalus1.0 -n all -xpelist  (show ALL none merged team branches with PE checkpoints)\n'       
    m += ' \n'
   # m += '    teamls -sall  -x info (show all team branch more info)\n'       
   # m += ' \n'
    m += '     (note: Use teams to see a list of active Product Teams\n'       
    m += ' \n'

    return m
    

def listTeamBranchCL(team='all', teambr='all', stream='all', show='list', options=None):
    """ command line logic for teamls - listBranch
    """
    db=options.debug
    if show in [None,'']: show = 'list'
    print 'Connecting to get the info for team branch %s in code stream %s for team %s' %(teambr,stream,team)
    sfb = SFTeamBranchTool(debug=db,logname='lsTB')

    dlist = sfb.showTeamBranches(team=team, branch=teambr, stream=stream, show=show)

    if dlist in [None,{},'',[]]:
        print 'There is not yet a Team Branch for the team %s in the stream %s'%(team,stream)
        sys.exit()
    
    if type(dlist[0]) == type({}):
        print '\n Status                          Task Branch Name'
        print ' ==============================  ================'

    for info in dlist:
        if type(info) == type({}):
            msg = ''
            msg = ' %-30s  %-45s ' %(info.get('status'), info.get('branch'))
            print msg
        else:
            print ' %s'%info


def listTeamNamesCL(team, show, options):
    """ command line logic for teams, listnames
    """
    db=options.debug
    print 'Connecting to SalesForce to get %s information on active Product Teams' %show
    sfb = SFTeamBranchTool(debug=db,logname='lsTBn')
    dlist = sfb.showTeamNames(team=team, show=show)
    for info in dlist:
        pass
        #print ' %s'%info


def getALLBranchApprovals(num, options):
    """ """
    db=options.debug
    if num in ['all']: num = 10000
    else:              num = int(num)
    print 'Checking on %s of the Branch approval objects'%num
    sfb = SFTeamBranchTool(debug=db)
    allBAUsers = sfb.getBAUsers()
    total = len(allBAUsers)
    num = 0
    numWarn = 0
    print 'FOUND %s Owners of Branch Approvals'%total
    print 'Now will display the status of all approvals'
    tbObj = SFTeamBranch(sfTool=sfb,debug=db)
    for uid in allBAUsers:
        num += 1
        res = sfb.getMyApprovals(uid=uid, stream=None, branch=None, show=False, getTB=False)
        print ' \n'
    

def getMyBranchApprovals(options):
    """ """
    db=options.debug
    sfb = SFTeamBranchTool(debug=db)
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
    ret = sfb.delete(baIds)
    print 'Deleted %s'%ret


def getLatestBA(options, secsAgo=None):
    """ """
    db=options.debug
    #entity = 'Team_Branch__c'
    entity = 'Branch_Approval__c'
    print 'Checking on latest %s '%entity
    sfb = SFTeamBranchTool(debug=db,logname='getBA')
    if secsAgo not in [None,0,'']:
        latestList, actionNeeded = sfb.getLatestTBA(secsAgo)      #secAgo is only parm
    else:
        latestList, actionNeeded = sfb.getLatestTBA()      #secAgo is only parm
    total = len(latestList)
    print 'FOUND %s %s items'%(total, entity)
    #tbObj = SFTeamBranch(sfTool=sfb,debug=options.debug)

def setTeamBranchStatusCL(stream, branch, query,opts):
    status = opts.status
    liststatus=query
    
    #print "Status ........ %s" %liststatus
    status=None
    ln=0
    for st in liststatus:
        if ln==0:
            status=st
        else:
            status=status+" "+st
        ln=ln+1
    #print "Status  final ...  %s"%status
        
    

    sfb = SFTeamBranchTool(logname='sf.tmbStat', debug=opts.debug)
    tmbObj = SFTeamBranch(sfTool=sfb)
    tmbInfo = tmbObj.loadTeamBranch(branch, stream)
    if tmbInfo[0] == 0:
        msg = '\n No team branch found for %s in %s. EXITING.' %(branch, stream)
        print msg
        #sfb.setLog(msg, 'error')
        print tmbInfo
    print '%s in %s using status: %s' %(branch,stream,status)    
    oldStatus = tmbObj.getData('Team_Branch__c').get('Status__c','')
    print 'Status is NOW set to  %s' %(oldStatus)
    print 'Status is CHANGING to %s' %(status)
    if status is None:
        updated = tmbObj.setBranchStatus()
    else:
        updated = tmbObj.setBranchStatus(status)        
    
    tmId=tmbObj.getData('Team_Branch__c').get('Id')    
    newTeamData = {'Id': tmId,
                  'Generate_scm_Token__c': True}
    res = sfb.update('Team_Branch__c', newTeamData)
    #print res
    
def setTeamStateUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = '%s\n\n' %err
    m += '  This script set the status of a Team Branch in Salesforce.\n'
    m += ' \n'
    m += 'Usage:\n'
    m += '    teamsetstat   -s <stream> -t <team branch> <Status to be set>\n\n'    
    m += ' \n'
    return m

def doSomething(method, term, parm, options):
    """  Command line controlled test of a method """
    print 'You called me with method:%s term:%s parm:%s ' %(method, term, parm)
    print 'Hope it was good for you'

#######################################################################################
#  Commandline management methods.  Minimal logic, just command parm processing
#######################################################################################
def mainTeamUsage():
    """ Prints the shell-script wrapped command line usage """

    m =  'TEAM BRANCH COMMAND SUMMARY\n\n'
    m += 'Issue any of these commands with no arguments to\n'
    m += 'see help for that specific command.\n\n'
    m += 'Process Flow Commands:\n'
    m += ' * teamlnbr -s<stream> -n<team name>\n'
    m += ' * teamlnbr -s<stream> -t<team branch>\n'
    m += '   Links a task branch to either a generic team branch (with the -n option)\n'
    m += '   or a specific named team branch (with the -t option).\n'
    m += '   Creates the team branch\n'
    m += '   if it does not already exist.\n'
    m += '\n'
    m += ' * teamhold -s<stream> -n<team name>\n'
    m += '   Sets the team branch to the Team Branch Hold state.\n'
    m += '\n'
    m += ' * teamqorbuild -s<stream> -n<team name>\n'
    m += '   Sets the team branch holding bin to the SCM-QOR Building state.\n'
    m += '\n'
    m += ' * teamqortest -s<stream> -n<team name>\n'
    m += '   Sets the team branch holding bin to the SCM-QOR Testing state.\n'
    m += '\n'
    m += ' * teamqorresult -s<stream> -n<team name>\n'
    m += '   Sets the team branch holding bin to the SCM-QOR Results state.\n'
    m += '\n'
    m += ' * teamsubmitbranch -s<stream> -n<team name> -t<new team branch name>\n'
    m += ' * teamsubmitbranch -s<stream> -t<team branch>\n'
    m += '   Allows the team manager to submit a team branch, allowing\n'
    m += '   it to proceed to the next step.\n'
    m += '\n'
    m += 'Reporting Commands:\n'
    m += ' * teamls -s <stream> -n <team name>\n'
    m += ' * teamls -s <stream> -t <team branch name>\n'
    m += '   list task branches in a particular team branch\n'
    m += '\n'
    m += ' * teams \n'
    m += '   list names for all teams\n'
    m += '\n'
    m += 'Additional Utilities:\n'
    m += ' * team\n'
    m += '   Prints this command summary.\n'
    m += '\n'
    m += ' * task (a.k.a. branch)\n'
    m += '   Prints the command summary for task branch operations.\n'
    m += '\n'
    return m

def usage(cmd='', err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to link a CR with a Task Branch (TB) on SalesForce.\n'
    m += ' '
    m += '    teamBranch -c lntb -s4.1 -t<Team_branch> -b<branch_Name>   \n'       # addTeamBranch
    m += '      or\n'
    m += '    teamBranch -c lntb -s4.1 -t<Team_branch> -b<branch_Name> -d -p urgent\n'  # addTeamBranch
    m += '      or\n'
    m += '    teamBranch -c list -s4.1 -t<Team_branch> -x min|other\n'  # listTeamBranch
    m += '      or\n'
    m += '    teamBranch -c set -s4.1 -t<Team_branch> -x<hold OR testing OR approve> <any text> \n'  # teamsetstatus (teamsethold, teamsettesting, teamapprovebranch)
    m += '      or\n'
    m += '    teamBranch -c approve -s4.1 -t<Team_branch>\n' # teamapprovebranch
    return m

def main_CL():
    """ Command line parsing and and defaults methods    """
    parser = OptionParser(usage=mainTeamUsage(), version='%s'%version)
    parser.add_option("-l", "--lb", dest="listBranchPath", default=None,
                      help="Path to file listing branches to allow forward."
                      "If used, branches not listed in the file will not be"
                      "moved forward. Format is one branch name per line")
    parser.add_option("-c", "--cmd",   dest="cmd",  default="add",      help="Command type to use.")
    parser.add_option("-x", "--parm",  dest="parm", default="",         help="Command parms.")
    parser.add_option("-s", "--cs",    dest="cs",   default=DEFAULT_STREAM,        help="Code Stream of Branch")
    parser.add_option("-b", "--br",    dest="br",   default="",         help="Branch Label")
    parser.add_option("-t", "--tbr",   dest="tbr",  default="",         help="Team Branch Label")
    parser.add_option("-u", "--dtbr",  dest="dtbr", default="",         help="Destination Team Branch Label (for moves)")
    parser.add_option("-n", "--team",  dest="team", default="",         help="Team Name")
    parser.add_option("--tb",          dest="ccteambr", default="",      help="ClearCase Team Branch")
    parser.add_option("-a", "--aa", "--approveall", dest="approveall", action='store_true', default=True,
                      help="For command sweepsubmit, approve all unapproved Team Mgr BAs")
    parser.add_option("--na", "--noapprove", dest="approveall", action='store_false', help="For command sweepsubmit, approve all unapproved Team Mgr BAs")
       
    parser.add_option("-p", "--priority",dest="priority",default="Low", help="Branch Priority: Low, Medium, High, Urgent, Critical")
    parser.add_option("-g", "--status",  dest="status",  default=None,  help="status to set on task branch")

    textgr = OptionGroup(parser, "Description Options","Add text description using the options below ")
    textgr.add_option("-d", "--desc",  dest="desc",  default=False, action="store_true", help="General description details")
    textgr.add_option("-m", "--mdesc", dest="mdesc", default=False, action="store_true", help="Merge description details")
    textgr.add_option("-f", "--path",  dest="path",  default="./details.txt", help="Path to details file.")
    parser.add_option_group(textgr)
    parser.add_option("-z", "--trace", dest="trace", default="soap.out", help="SOAP output trace file.")
    parser.add_option("-v", "--debug", dest='debug', action="count",     help="The debug level, use multiple to get more.")
       
    
    (options, args) = parser.parse_args()
    

    if options.debug > 1:
        print ' cmd  %s, parms  %s' %(options.cmd, options.parm)
        print ' stream %s, branch %s, team %s' %(options.cs, options.br, options.tbr)
        print ' path   %s, trace  %s, debug  %s' %(options.path,options.trace ,options.debug)
        print ' args:  %s' %args
    else:
        options.debug = 0

    if len(options.cmd) > 0: 
        team = options.team
        teamBR = options.tbr
        branch = options.br
        st = time.time()
        parm = options.parm
        query = args[1:]
        query1 = args[0:]
        
        ccteambr = options.ccteambr
        # check if user types -tb instead of --tb
        if team == 'b':
            print "The team branch argument doesn't look right."
            print 'Perhaps you meant to use "--tb" rather than "-t"'
            sys.exit(1)
            pass
        
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

        
        if options.cmd in ['lntb','link','add']:
            if team in [None,''] or stream in [None,'']: 
                print '%s' %addTeamBranchUsage('You must provide at least a valid stream and a team name')
                sys.exit()
            if teamBR in [None,'']:
                teamBR = None

            scmFlag = False
            checkTmb = True
            if parm.lower() in ['scm', 'scmfast']:
                scmFlag = True
                if parm.lower() in ['scmfast']:
                    checkTmb = False
                    pass
                pass
                
            addTeamBranchCL(team, teamBR, branch, stream, options, st,
                            checkTmb=checkTmb, scmFlag=scmFlag)

        elif options.cmd in ['unlntb','unlink','rem']:
            if team in [None,''] or stream in [None,'']: 
                print '%s' %remTeamBranchUsage('You must provide at least a valid stream and a team name')
                sys.exit()
            if teamBR in [None,'']:
                teamBR = team
            unlinkTeamBranchCL(team, teamBR, stream, branch, options, st)
            
        elif options.cmd in ['sweephold']:
            if team in [None,''] or stream in [None,'']:
                print '%s' %sweepTeamHoldUsage('You must provide a team name!')
                sys.exit()
            sweepTeamHoldCL(team, stream, options)
            
        elif options.cmd in ['sweepqor']:
            if team in [None,''] or stream in [None,''] or \
                   ccteambr in [None,'']:
                print '%s' %sweepTeamQorUsage('You must provide a stream, a team name, and a ClearCase team branch name!')
                sys.exit()
            sweepTeamQorCL(team, ccteambr, stream, options)
            
        elif options.cmd in ['teamsubmit']:
            if team in [None,''] or teamBR in [None,''] or \
                   stream in [None,''] or ccteambr in [None,'']:
                print '%s' %teamSubmitBranchUsage('You must provide a valid stream, a team name, the ClearCase team branch, and a new branch label!')
                sys.exit()
            submitTeamBranchCL(team, ccteambr, stream, teamBR, options, st)

        elif options.cmd in ['teamls', 'ls', 'list']:
            if (team in [None,''] and teamBR in [None,'']) \
                   or stream in [None,'']:
                print '\n\tYou must provide at least a valid stream and a team branch label or team name!'
                print '%s' %teamlsUsage()
                sys.exit()
            show = options.parm
            listTeamBranchCL(team, teamBR, stream, show, options)
            
        elif options.cmd in ['teamlsnames','listnames','lsnames']:
            team = options.team
            show = options.parm
            if show in [None,'']: show = 'list'
            listTeamNamesCL(team, show, options)

        elif options.cmd in ['teammv']:
            srcTeamBr = teamBR
            destTeamBr = options.dtbr
            if srcTeamBr in [None,''] or destTeamBr in [None,''] or \
               stream in [None, '']:
                err = 'You must provide a source team name, destination team name and stream!'
                print moveTeamBranchUsage(err)
                sys.exit(1)
                pass
                
            moveTeamBranchCL(srcTeamBr, destTeamBr, stream, options)
            
        elif options.cmd in ['teammvpe']:
            srcTeamBr = teamBR
            destTeamBr = options.dtbr
            if srcTeamBr in [None,''] or destTeamBr in [None,''] or \
               stream in [None, '']:
                err = 'You must provide a source team name, destination team name and stream!'
                print movePEBranchUsage(err)
                sys.exit(1)
                pass
                
            movePEBranchCL(srcTeamBr, destTeamBr, stream, options)
        
        elif options.cmd in ['submittoscm']:
            #team = options.team
             
            #if (team in [None,''] or stream in [None,'']):
            #    print '\n\tYou must provide at least a valid stream and a team branch label or team name!'
            #generateSCMToken(team, stream, st=0)    
            generateSCMToken()

        elif options.cmd in ['teamqorstat']:
            team = options.team
            newstat = options.parm
            if team in [None,''] or stream in [None, ''] or \
                   ccteambr in [None, ''] or newstat in [None,'']:
                err = 'You must provide a team name, stream, and a ClearCase team branch name!'
                print setTeamQorStateUsage(err)
                sys.exit(1)
                pass

            if newstat == 'qorbuild':
                newstat = 'SCM-QOR Building'
            elif newstat == 'qortest':
                newstat = 'SCM-QOR Testing'
            elif newstat == 'qorresult':
                newstat = 'SCM-QOR Results'
            else:
                print "New status of %s is invalid" %newstat
                sys.exit(1)
                pass
                
            setTeamQorStateCL(team, ccteambr, stream, newstat, options, st)
            sys.exit()

        elif options.cmd in ['teamhelp']:
            print mainTeamUsage()
            sys.exit()

        elif options.cmd in ['stat', 'status']:
            if options.tbr in [None,''] or stream in [None,'']:
                err= 'You must provide at least a valid stream and team branch!'
                print setTeamStateUsage(err)
                sys.exit()
            setTeamBranchStatusCL(stream, options.tbr, query1,options)

        elif options.cmd in ['convert']:
            if team in [None,''] or stream in [None, ''] or \
                   ccteambr in [None, '']:
                print 'You must provide a team name, stream, and a ClearCase team branch name to convert the old style QOR bin!'
                sys.exit(1)
                pass

            convertQorCL(team, ccteambr, stream)

        else:
            doSomething('search', query, options.parm, options)
            print 'doing nothing yet, I can do it twice if you like'
        print '\nTook a total of %3.2f secs -^' %(time.time()-st)
    else:
        print '%s' %usage(options.cmd)

if __name__ == "__main__":
    main_CL()
