import pprint
import sets
import sys
import re
from types import ListType, TupleType, DictType, DictionaryType
from optparse import OptionParser

from sfConstant import *
from sfMagma import SFMagmaEntity, SFMagmaTool, dictTypes
import sfUser2
import sfTaskBranchStatusMap
import mail

class SFCr(SFMagmaEntity):
    """
    This is a composite object that represents a Change Request sForce object
    and related Branch_CR_Link__c objects as one entity
    """
    def __init__(self, entity=None, data={}, action=None, sfTool=None, debug=0):
        """
        If an active tool object is not passed in then a connection is created.
        """

        self.caseNum = ''
        
        if entity is None: entity = 'Case'
        SFMagmaEntity.__init__(self, entity, data=data, action=action, sfTool=sfTool, debug=debug)

        return

    def loadCr(self, crNum):
        """
        Load elemnts from an existing CR object given a CR number
        """
        # format CR num into 8 digit zero padded string
        #print "CR NUM ................%s"%crNum
        if crNum not in [None,'']:            
            crNum = '%08d' %int(crNum)
            where = [['CaseNumber','=', crNum]]
            crData = self.getSFData(where, show=False)
    
            status = crData.get('Case').get('Status','')
            numCLs = len(crData.get('Branch_CR_Link__c'))
    
            info = [numCLs, status]
            return info
    ## END loadCr


    def loadCrById(self, id):
        """
        Load elemnts from an existing CR object given a CR id
        """
        where = [['Id','=', id]]
        crData = self.getSFData(where, show=False)

        status = crData.get('Case__c').get('Status','')
        numCLs = len(crData.get('Branch_CR_Link__c'))

        info = [numCLs, status]
        return info
    ## END loadCrById
    

    def getSFData(self, where, show=True):
        """
        one call to get all new CR object as a list of entity-data pairs
        [('entity', {data})] return this data structure or {}
        This will consist of a CR map, a list of Branch CR Links and
        a list of CR Originator Branch Approvals 
        """
        res = {'Case': {},
               'Branch_CR_Link__c': [],
               'Branch_Approval__c': []}

        self.setData(res, reset=True)

        queryList = self.sfb.query(self.entity, where=where, sc='all')

        if queryList in self.badInfoList:
            if self.debug>1:
                print '    NO CR Found for %s' \
                      %pprint.pformat(where)
            return res

        if len(queryList) > 1:
            print 'WARNING: There should be only ONE TB object found by %s' \
                  %pprint.pformat(where)

        numCL = 0

        crData = queryList[0]
            
        if type(crData) not in dictTypes:
            return 'Error: getSFData for %s Query returned %s' %(where, crData)

        crId = crData.get('Id','')
        res['Case'] = crData

        if crId not in BAD_INFO_LIST:
            self.caseNum = crData.get('CaseNumber','')

            # get the Branch CR Links on this CR
            where = [['Case__c','=',crId]]
            br_links  = self.sfb.query('Branch_CR_Link__c', where=where)
            if br_links not in self.badInfoList:
                res['Branch_CR_Link__c'] = br_links
                numCL = len(br_links)
                pass

            # get the CR Originator BAs on this CR
            where = [['Case__c','=',crId], 'and',
                     ['Approval_Role__c','=','CR Originator']]
            ba_list  = self.sfb.query('Branch_Approval__c', where=where)
            if ba_list not in self.badInfoList:
                res['Branch_Approval__c'] = ba_list
                pass
            
        else:
            if self.debug >= 2:
                print '\tNO CR Found for query %s' %where
                return res

        self.setData(res)
        self.sfb.setLog('getSFData %25s brcrl:%s'%(self.caseNum,numCL),'info2')
        if show: self.showData(res)

        return res

    def updateBrCrLinks(self):
        """
        propagate pieces of CR information forward into the Branch CR Links.
        CR must have already been loaded
        This information always flows from CR -> Branch CR Link, never
        vice versa:
        * CR Status
        * Component
        """

        crData = self.getData()
        crInfo = crData.get('Case')
        brCrList = crData.get('Branch_CR_Link__c',[])

        crStatus = crInfo.get('Status')
        crComponent = crInfo.get('Component__c','')
        crSubject = crInfo.get('Subject','')

        crLinkUpdList = []
        for brCrLinkInfo in brCrList:
            data = {}

            brCrId = brCrLinkInfo.get('Id')

            brCrStatus = brCrLinkInfo.get('CR_Status__c','')
            brCrSubject = brCrLinkInfo.get('CR_Subject__c','')
            brCrComponent = brCrLinkInfo.get('Component__c','')
            brCrComponentId = brCrLinkInfo.get('Component_Link__c','')

            if brCrStatus != crStatus:
                data['CR_Status__c'] = crStatus

            if brCrSubject != crSubject:
                data['CR_Subject__c'] = crSubject

            componentInfo = self.sfb.getComponent(crComponent)
            if componentInfo in BAD_INFO_LIST:
                msg = 'Cannot find component object for %s' %crComponent
                print msg
                self.sfb.setLog(msg, 'error')
                
            elif brCrComponent != crComponent or \
                     brCrComponentId != componentInfo.get('Id'):
                data['Component_Link__c'] = componentInfo.get('Id')
                data['Component__c'] = crComponent

            if len(data) > 0:
                data['Id'] = brCrId
                #issue the update
                res = self.sfb.update(BRANCH_CR_LINK_OBJ, data)

                if res in BAD_INFO_LIST:
                    msg = 'UpdateBrCrLinks: FAILED Update Branch CR Link, link ID: %s data: %s' %(brCrId, data)
                    self.sfb.setLog(msg, 'error')
                    if self.debug >=1: print 'ERROR: %s' %msg
                    
                else:
                    msg = 'UpdateBrCrLinks: Update Branch CR Link ID: %s data: %s' %(brCrId, data)
                    self.sfb.setLog(msg, 'info')
                    if self.debug >=1: print 'INFO: %s' %msg
                    crLinkUpdList.append(data)

        if len(crLinkUpdList) > 0:
            self.setData({BRANCH_CR_LINK_OBJ: crLinkUpdList})
        return
    
    def updateCrCodeStreams(self):
        """
        Examine the Code Streams and Priority field against the streams
        of existing Branch CR links and update the field accordingly.
        Return the final list of streams
        """
        crData = self.getData()
        crInfo = crData.get('Case')

        brCrList = crData.get('Branch_CR_Link__c',[])

        crId = crInfo.get('Id')
        crCsp = crInfo.get('Code_Streams_Priority__c','')

        # Get list of streams from the CR
        crStreamSet = sets.Set()
        crStreamList = []
        for stream in crCsp.split(','):
            stream = stream.strip()
            crStreamSet.add(stream)
            continue

        # Get list of streams from the branch cr links
        brStreamSet = sets.Set()
        for brCrLink in brCrList:
            stream = brCrLink.get('Stream__c',None)
            if stream is not None:
                brStreamSet.add(stream)

        if not brStreamSet.issubset(crStreamSet):
            crStreamSet.union_update(brStreamSet)

            # cast the set into a list so that we may sort it
            crStreamList = list(crStreamSet)
            crStreamList.sort()
            
            # update the CR
            crCsp = ', '.join(crStreamList)
            data = {'Id':crId,
                    'Code_Streams_Priority__c': crCsp}
            res = self.sfb.update(CASE_OBJ, data)
            if res in BAD_INFO_LIST:
                msg = 'UpdateCrCodeStreams: FAILED Update CR %s' %crId
                self.sfb.setLog(msg, 'error')
                if self.debug >=1:
                    print 'ERROR: %s' %msg
                    pass
                pass
            
        else:
            crStreamList = list(crStreamSet)
            crStreamList.sort()
                

        return crStreamList
            


    def evalCrStatus(self):
        """
        Evaluates the task branch status(es) (propagated to the Branch CR Links
        by the Task Branch objects) to determine the overall state of the CR.

          Valid CR status fields include:
              # manually set states
              Open            
              Confirming            
              Verifying No Need
              Pending Complete Test Case
              Cannot Reproduce         
              Testing Fail          

              # manually set closed states
              Closed Will Not Fix           
              Closed Duplicate           
              Closed Not a Problem           
              Closed User Error
              Closed 

              # states set based on the mods on the CR
              Fixing             
              First-Approving             
              Approving             
              First-Approved             
              Approved             
              First-SCM-Received             
              SCM-Received             
              First-SCM-Merging             
              SCM-Merging             
              First-Testing            
              Testing             
              Remaining-Streams             
              Closed # May be set this way as well
        """
        crCloseable = False
        crData = self.getData()
        crInfo = crData.get('Case')
        brCrList = crData.get('Branch_CR_Link__c',[])
        baList = crData.get('Branch_Approval__c',[])

        crStatus = crInfo.get('Status')
        crNum = crInfo.get('CaseNumber','')
        
        if crStatus in ['Will Not Fix']:
            return 'Closed Will Not Fix', crCloseable
        elif crStatus in ['Can Not Reproduce']:
            return 'Cannot Reproduce', crCloseable

        # If CR has been closed, leave it alone.
        if crStatus in ['Closed Will Not Fix',
                        'Closed Duplicate',
                        'Closed Not a Problem',
                        'Closed User Error',
                        'Closed Fixed by Subsequent Change',
                        'Closed']:
            crCloseable = True
            return crStatus, crCloseable

        # If no branch links to CR, and in manually set state, leave it alone.
        if len(brCrList) == 0: 
            if crStatus in ['Confirming',
                            'Verifying No Need',
                            'Cannot Reproduce',
                            'Need More Information',
                            'Pending Complete Test Case',
                            'Testing Fail']:
                return crStatus, crCloseable
            else:
                return 'Open', crCloseable
            
        crStreamList = self.updateCrCodeStreams()
        
        statMap = sfTaskBranchStatusMap.SFTaskBranchStatus().getStatusMap()

        # find status of branch farthest along
        farthestBrOrdinal = 0
        farthestBrStatus = None
        closedOrdinal  = statMap['Closed']['order']
        
        for brCrLink in brCrList:
            brStat = brCrLink.get('Branch_Status__c','')
            if brStat.lower()[:5] == 'post-':
                # branch stat is (probably) "post-XXXX-release"
                brStat = 'SCM-Post-Release'
                pass


            statMapInfo = statMap.get(brStat, None)

            if statMapInfo is None:
                # Branch Status is not in the statMap - log error and return
                # CR status of Unknown
                msg = 'getCRStatus CR:%s unknown Branch status %s' \
                      %(crNum, brStat)
                self.sfb.setLog(msg, 'error')
                return 'Unknown', crCloseable
            
            brStatOrdinal = statMapInfo['order']
            if brStatOrdinal > farthestBrOrdinal:
                farthestBrOrdinal = brStatOrdinal
                farthestBrStatus = brStat
            
            if brStatOrdinal <= closedOrdinal:
                pass 

        isSingleStream = self.isCrSingleStream(brCrList, crStreamList)
        #print "isSingleStream: %s" %isSingleStream
        if isSingleStream is True:
            statusType = 'crStatus'
        else:
            statusType = 'crStatusFirst'
            pass

        # Now, actually determine the CR's status
        if farthestBrStatus is None:
            return 'Open', crCloseable

        allMerged = self.areAllStreamsMerged(brCrList, crStreamList)
        #print "allMerged: %s" %allMerged
        if allMerged is True:
            # all streams are merged, mark CR as candidate for auto-closure
            crCloseable = True
            pass
        
        anySatisfied = self.isAnyStreamSatisfied(brCrList, baList)
        #print "anySatisfied: %s" %anySatisfied

        if anySatisfied is True:
            # At least one branch on this CR has been approved
            allClosed = self.areAllBranchesClosed(brCrList, baList)
            allSatisfied = self.areAllStreamsSatisfied(brCrList, baList,
                                                       crStreamList)
            #print "allClosed: %s" %allClosed
            #print "allSatisfied: %s" %allSatisfied
            
            if allClosed is True and allSatisfied is True:
                # all existing branches are closed,
                # and all requested streams satisfied
                crStatus = "Closed"
            else:
                # at least one linked branch is closed
                crStatus = "Remaining-Streams"
                
        else:
            # No branches linked to this CR are approved
            crStatus = statMap[farthestBrStatus][statusType]
            pass
            

        if crStatus in ['Confirming']:
            # at this point there are at least 2 linked Branches
            return 'Fixing', crCloseable
        
        return crStatus, crCloseable
    ## END evalCrStatus

    def isCrSingleStream(self, brCrList, crStreamList):
        """
        If there's only one cr code stream and only one linked branch and the
        branche's code stream equals the cr's code stream, then we're
        truly a single-stream CR.
        """
        if len(crStreamList) == 1 and len(brCrList) == 1 \
           and brCrList[0].get('Stream__c','') == crStreamList[0]:
            return True
        else:
            return False
    ## END isCrSingleStream

    def isAnyStreamSatisfied(self, brCrList, baList):
        """
        Is any code stream on this CR successfully closed?
        We consider a branch to be closed with respect to this CR
        if the branch for the stream has been merged and the CR originator BA
        has been approved. 
        """
        baseMergedOrder = 54.0
        statMap = sfTaskBranchStatusMap.SFTaskBranchStatus().getStatusMap()

        for brCrLink in brCrList:
            taskBranchId = brCrLink.get('Task_Branch__c')
            
            brStat = brCrLink.get('Branch_Status__c','')
            if statMap[brStat]['order'] < baseMergedOrder:
                continue

            # OK, the task branch is merged, now has this CR been approved
            # in it?
            for ba in baList:
                if ba.get('Task_Branch__c') == taskBranchId:
                    if ba.get('Approve__c') == 'Approve':
                        return True
                        pass
                    pass
                continue

            continue
        
        return False
    ## END isAnyStreamSatisfied
        
    def areAllBranchesClosed(self, brCrList, baList):
        """
        Are all branches linked to this CR closed?
        We consider a branch to be closed with respect to this CR
        if the branch for the stream has been merged and the CR originator BA
        has been approved OR rejected. 
        """
        baseMergedOrder = 54.0
        statMap = sfTaskBranchStatusMap.SFTaskBranchStatus().getStatusMap()

        crStreamScore = {}

        for brCrLink in brCrList:
            taskBranchId = brCrLink.get('Task_Branch__c')
            crStreamScore[taskBranchId] = False # init to false
            
            brStat = brCrLink.get('Branch_Status__c','')
            if statMap[brStat]['order'] < baseMergedOrder:
                return False

            # OK, the task branch is merged, now has this CR been approved
            # in it?
            for ba in baList:
                if ba.get('Task_Branch__c') == taskBranchId:
                    if ba.get('Status__c') == 'Merged - Tested by Originator' \
                           or ba.get('Approve__c') == 'Approve' \
                           or ba.get('Approve__c') == 'Reject':
                        crStreamScore[taskBranchId] = True
                        pass
                    pass
                continue

            continue
        
        if False in crStreamScore.values():
            return False
        else:
            return True
    ## END areAllBranchesClosed


    def areAllStreamsSatisfied(self, brCrList, baList, crStreamList):
        """
        return True if we have at least one mod in each code stream designated
        by the cr in a successful close state, otherwise return False
        """
        statMap = sfTaskBranchStatusMap.SFTaskBranchStatus().getStatusMap()

        # create a scorecard for each code stream the CR wants.
        crStreamScore = {}
        for crStream in crStreamList:
            crStreamScore[crStream] = False

        for brCrLink in brCrList:
            taskBranchId = brCrLink.get('Task_Branch__c')
            brStat = brCrLink.get('Branch_Status__c','')
            brStream = brCrLink.get('Stream__c','')

            if statMap[brStat]['order'] >= statMap['Merged']['order']:
                for ba in baList:
                    if ba.get('Task_Branch__c') == taskBranchId:
                        if ba.get('Approve__c') == 'Approve':
                            crStreamScore[brStream] = True
                            pass
                        pass
                    continue
                
                pass
            
            continue

        # Check that the scorecard is all true
        if False in crStreamScore.values():
            return False
        else:
            return True
    ## END areAllStreamsSatisfied


    def areAllStreamsMerged(self, brCrList, crStreamList):
        """
        return True if we have at least one mod in each code stream designated
        by the cr in a successful merge or close state, otherwise return False
        """
        statMap = sfTaskBranchStatusMap.SFTaskBranchStatus().getStatusMap()

        # create a scorecard for each code stream the CR wants.
        crStreamScore = {}
        for crStream in crStreamList:
            crStreamScore[crStream] = None

        for brCrLink in brCrList:
            brStat = brCrLink.get('Branch_Status__c','')
            brStream = brCrLink.get('Stream__c','')

            if statMap[brStat]['order'] >= statMap['Merged - Notifying Originator']['order'] and \
                   crStreamScore.get(brStream) is not False:
                # only score the stream "True" if it hasn't been scored "False"
                crStreamScore[brStream] = True
            else:
                crStreamScore[brStream] = False

        # Check that the scorecard is all true
        if None in crStreamScore.values():
            # we have designated streams without branches
            #print "streams without branches"
            #pprint.pprint(crStreamScore)
            return False
        elif False in crStreamScore.values():
            # we have designated streams with unmerged branches
            #print "streams with unmerged branches"
            return False
        else:
            # all streams have all branches merged
            return True
    ## END areAllStreamsMerged
    
    
    def findCRStreamStatus(self,codeStream,stream):        
        validStreams=[]
        if codeStream not in [None,'']:
            streams=codeStream.split(',')
            for st in streams:
                st=st.strip()
                if st in ACTIVE_STREAMS:
                    validStreams.append(st)
            #print "Valid active streams %s" % validStreams
        count =0
        for vs in validStreams:
            if vs==stream:
                break
            else:
                count=count+1       
        if count ==0:
            stField='Status_1_Stream__c'              
            stStream='X1st_Stream__c'
        elif count==1:
            stField='Status_2_Stream__c'
            stStream='X2nd_Stream__c'
        else:
            stField='Status_3_Stream__c'  
            stStream='X3rd_Stream__c'              
           
        return stField,stStream

    def setCrStatus(self, status=None,stream=None,brStat=None):
        """
        Sets the status of the CR to the passed value, or evaluates the status
        based upon the states of branches linked to the CR.
        """
        
        #print "status... %s ...and Stream ... %s" %(status,stream)
        stFiled=None
        stStream=None
        closedStatList = self.getClosedStatusList()
        
        closeable = False
        if status is None:
            status, closeable = self.evalCrStatus()
        elif status[:6] == 'Closed':
            closeable = True

        crData = self.getData()
        crInfo = crData.get('Case')

        crId = crInfo.get('Id')
        crStatus = crInfo.get('Status')
        
        codeSt=crInfo.get('Code_Streams_Priority__c')
        if stream is not None:            
            stFiled,stStream=self.findCRStreamStatus(codeSt,stream)             

        wasClosed = False
        if crStatus in closedStatList:
            wasClosed = True

        crIsCloseable = crInfo.get('IsCloseable__c')
        if crIsCloseable in ['true', True]:
            crIsCloseable = True
        else:
            crIsCloseable = False
        
        if stFiled not in [None,'']:            
            data = {'Id': crId,
                    'Status': crStatus,
                    stFiled:brStat,
                    stStream:stream,
                    'IsCloseable__c': crIsCloseable}
                   
            #print "Data ...... %s" %data
            res = self.sfb.update(CASE_OBJ, data)
       
        #print "stFiled,stStream %s ... %s ... %s ... %s...%s ...%s"%(stFiled,stStream,crStatus,status,crIsCloseable,closeable)                          

        if crStatus != status or crIsCloseable != closeable:
            #print "Inside CR Status"
            crIsCloseable = closeable
            crStatus = status

            willBeClosed = False
            if crStatus in closedStatList:
                willBeClosed = True

            # set the status of the CR
            
            if stFiled not in [None,'']:
                data = {'Id': crId,
                        'Status': crStatus,
                        stFiled:brStat,
                        stStream:stream,
                        'IsCloseable__c': crIsCloseable}
            else:                
                data = {'Id': crId,
                        'Status': crStatus,
                        'IsCloseable__c': crIsCloseable}
            
            #print "Data ...... %s" %data
            res = self.sfb.update(CASE_OBJ, data)

            if res in BAD_INFO_LIST:
                msg = 'setCrStatus: FAILED attempt Update CR %s Status to %s' \
                      %(crId, status)
                self.sfb.setLog(msg, 'error')
                if self.debug >=1: print 'ERROR: %s' %msg
                return ''
            else:
                self.setData({CASE_OBJ: data})
                self.updateBrCrLinks()
                msg = 'setCrStatus: Updated CR %s Status to %s' \
                      %(crId, status)
                self.sfb.setLog(msg, 'info')
                if self.debug >=1: print 'INFO: %s' %msg

                if wasClosed is False and willBeClosed is True:
                    # send notification of the CR closure
                    closeMsg =  "This CR has been closed because it has been reported fixed in all desired\n"
                    closeMsg += "code streams."
                    
                    ## Notification off for initial run
                    self.notifyOfClosure(closeMsg)
                    pass
                
        return crStatus


    def getClosedStatusList(self):
        """ Return a list of the Closed states for cases """
        if hasattr(self, 'closedStatList') is False:
        
            where = [['IsClosed','=',True]]
            fields = ('Id', 'MasterLabel')
            closedStatList = []
            res = self.sfb.query('CaseStatus', where, sc=fields)
            if res not in BAD_INFO_LIST:
                for statRec in res:
                    closedStatList.append(statRec.get('MasterLabel'))
                    continue
                pass
            
            self.closedStatList = closedStatList
            pass
        
        return self.closedStatList
    ## END getClosedStatusList

        
    def notifyOfClosure(self, msgBody=None):
        mailServer = self.sfb.mailServer2()
        
        crData = self.getData()
        crInfo = crData.get('Case')

        crId = crInfo.get('Id')
        crOrigId = self.sfb.getCrOriginator(crInfo)
        crCreatorId = crInfo.get('CreatedById')
        crSubject = crInfo.get('Subject', 'CR has no subject')
        crNum = crInfo.get('CaseNumber').lstrip('0')

        # get the originator's email
        crOriginator = sfUser2.SFUser.retrieve(self.sfb, crOrigId)
        if crOriginator is None:
            # uh oh - didn't get back a user for the originator
            msg = "sfCr:notifyOfClosure lookup user with id %s failed" \
                  %crOrigId
            self.sfb.setLog(msg, 'error')
            print "ERROR: %s" %msg
            return
        
        origData = crOriginator.getDataMap()
        origEmail = origData.get('Email')
        origName = "%s %s" %(origData.get('FirstName',''),
                             origData.get('LastName'))
        origName.strip()

        msgSubject = "Closure of CR %s: %s" %(crNum, crSubject)

        whyRec = "You are receiving this notification because you were the creator of this CR."
        if crOrigId[15:] != crCreatorId[15:]:
            whyRec = "You are receiving this notification because it was determined\nthat you are the responsible party for this CR."
            pass

        if msgBody is None:
            msgBody = "The following CR has been automatically closed:"
            pass

        crInfoBody =  "%s: %s\n" %(crNum, crSubject)
        crInfoBody += "%s/%s" %(self.sfb.sfdc_base_url, crId)

        body = "%s,\n\n%s\n\n%s\n\n%s\n" \
               %(origName, whyRec, msgBody, crInfoBody)


        message = mail.Message(fromAdd=self.sfb.from_addr, toAdds=origEmail,
                               body=body, subject=msgSubject)

        mailServer.sendEmail(message)
        return
    ## END notifyOfClosure
    
class SFCrTool(SFMagmaTool):
    logname = 'sfCr'


def evalCrStatus(crNum, setStatus=False, debug=0):
    crTool = SFCrTool(debug=debug)
    crObj = SFCr(sfTool=crTool)
    crObj.loadCr(crNum)
    
    if setStatus is True:
        print crObj.setCrStatus()
    else:
        print crObj.evalCrStatus()

    return
## END evalCrStatus


def refreshBranchCrLinks(crNum, debug=0):
    crTool = SFCrTool(debug=debug)
    crObj = SFCr(sfTool=crTool)
    crObj.loadCr(crNum)
    crObj.updateBrCrLinks()
    #pprint.pprint(crObj.getData())
    return
## END refreshBranchCrLinks


def main_CL():
    op = OptionParser()
    op.add_option('-c', '--cmd', dest='cmd', help='Command to run')
    op.add_option('--set', dest='set', action='store_true', default=False,
                  help='Set the CR status if determined to be different')
    op.add_option("-d", "--debug", dest='debug', action="count",
                  help="The debug level, use multiple to get more.")

    (opts, args) = op.parse_args()

    if opts.debug > 1:
        print ' cmd    %s' %opts.cmd
        print ' debug  %s' %opts.debug
        print ' set    %s' %opts.set
        print ' args:  %s' %args
    else:
        opts.debug = 0

    if len(args) > 0:
        crNumList = args[0:]
    else:
        errmsg = 'You must provide a CR number!'
        print errmsg
        sys.exit(1)
        
    if opts.cmd in ['status', 'stat', 's']:
        for crNum in crNumList:
            print "Evaluating CR %s" %crNum
            evalCrStatus(crNum, opts.set, debug=opts.debug)
            continue
        
    elif opts.cmd in ['refresh','r']:
        for crNum in crNumList:
            print "Refreshing CR %s" %crNum
            refreshBranchCrLinks(crNum, debug=opts.debug)
            continue
        
if __name__ == "__main__":
    main_CL()
