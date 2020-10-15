"""
Actual events to poll for and operate upon
"""
import copy
import datetime
import time
import pprint
import textwrap
from optparse import OptionParser

from NotificationEventHandler import NotificationEventHandler
from sfConstant import *
from sfTaskBranch import SFTaskBranch, SFTaskBranchTool
from MailNotification import MailNotification, WW
from MailMessageQueue import MailMessageQueue
from TimeUtil import parseSfIsoStr, dayNumToTxt

class BranchAlarmHandler(NotificationEventHandler):
    """ Common bits for Branch Dunning events.
    """
    role = None # must be provided by implementation
    notifyRoles = None # must be provided by implementation
    staticRecipients = None

    # override these in the subclasses
#    triggerDays = 7
#    intervalDays = 0
#    limitTimes = 5

    def poll(self):
        rawEventList = []

        # deltaDays is set in the event instance
        delta = datetime.timedelta(days=self.triggerDays)
        
        dt = datetime.datetime.utcfromtimestamp(time.time())
        delinquentDateTime = dt - delta
        delinquentIsoDateTime = "%sZ" %delinquentDateTime.isoformat()

        sts = self.sfb.getServerTimestamp()
        currentSfDatetime = datetime.datetime(sts[0], sts[1], sts[2], sts[3], sts[4],
                                              sts[5], sts[6])

        fields = ('Id', 'OwnerId', 'Name', 'LastModifiedDate')
        where = [['Branch_Status__c','=',self.branchStatus],'and',
                 ['LastModifiedDate','<', delinquentIsoDateTime]]

        if hasattr(self, 'limitTimes') and self.limitTimes > 0:
            maxTriggerDays = self.triggerDays + (self.intervalDays * self.limitTimes)
            delta = datetime.timedelta(days=maxTriggerDays)            
            maxDateTime = dt - delta
            maxIsoDateTime = "%sZ" %maxDateTime.isoformat()

            where += ['and', ['LastModifiedDate','>=', maxIsoDateTime]]
            pass


        res = self.sfb.query('Task_Branch__c', where, fields)
        if res in BAD_INFO_LIST:
            res = []
            pass

        # process the results and build up event records
        # subjectid: the task branch id
        # ownerid: the prime recipient

        for tb in res:
            # get the whole task branch here so we can tuck the data struct in
            # the event representation
            tbObj = SFTaskBranch(sfTool=self.sfb)
            tbObj.loadBranchById(tb.get('Id'))
            btlDataList = tbObj.getData('Branch_Team_Link__c')

            lastModified = tb.get('LastModifiedDate')
            triggerObjDatetime = parseSfIsoStr(lastModified)

            targetContactId = None
            if self.eventcode in ['SCMH']:
                targetContactId = self.scmContactId
            else:
                if len(btlDataList):
                    btlData = btlDataList[0] # should only be one BTL
                    teamLookup = btlData.get('Team__c')
                    teamLookup = self.sfb.devTeamToScmTeam(teamLookup)
                    if teamLookup is not None:
                        # look up the dev team
                        pt = self.sfb.getProductTeam(teamLookup)
                        targetContactId= pt.get('Build_Account_Contact__c')
                        pass
                    pass
                pass

            print

##            delinquentDelta = currentSfDatetime - lastModDatetime
##            print ba.get('Id')
##            print dayNumToTxt(delinquentDelta.days)
##            print

            # need to figure out the target of the notification
            
            rawEvent = {'timestamp': datetime.datetime.now(),
                        'triggerObjDatetime': triggerObjDatetime,
                        'eventDatetime': currentSfDatetime,
                        'seedData': tbObj,
                        'eventcode': self.eventcode,
                        'triggerId': tb.get('Id'),
                        'subjectId': tb.get('Id'),
                        'targetId': targetContactId,
                        'targetDeferred': False,
                        'intPartyIdMap': {},
                        'partyDeferred': True}

            if targetContactId is None:
                continue

            rawEventList.append(rawEvent)
            continue
        
        self.rawEventList = rawEventList
        return ## END poll


    def gatherRecipients(self, eventStruct):
        """ Determine the recipients of this message in a number of ways.
        Note the reason each recipient is getting the notice - Should be a
        phrase which completes the sentence, 'You are receiving this notice
        because...'
        """
        targetUserId = eventStruct.get('targetId')
        recipientIdMap = {}

        # first, the target of the notification
        if targetUserId is not None:
            why = 'this notice describes an action you need to take'
            self.addRecipient(recipientIdMap, targetUserId, why)
        else:
            msg = "Target not found for event code %s on subject %s" \
                  %(self.eventcode, eventStruct.get('subjectId'))

##        # Now, look up the target's engineering manager
##        mgrData = self.sfb.getMgrByID(targetUserId)
##        mgrId = mgrData.get('Id')
##        why = 'you are the manager of the recipient of this notice'
##        self.addRecipient(recipientIdMap, mgrId, why)


        # Next, look up additional notificants from the other branch approvals.
        tbObj = eventStruct.get('seedData')
        baDataList = tbObj.getData('Branch_Approval__c')

        engMgrId = None

        for baData in baDataList:
            if baData.get('Approval_Role__c') in self.notifyRoles:
                if baData.get('Approval_Role__c') == 'Engineering Manager':
                    engMgrId = baData.get('OwnerId')
                    pass
                
                why = 'you are a(n) %s for this branch' \
                      %baData.get('Approval_Role__c')
                self.addRecipient(recipientIdMap, baData.get('OwnerId'), why)
                pass
            continue

        # look up the eng mgr's VP
        if engMgrId is not None and 'RDVP' in self.notifyRoles:
            vpData = self.sfb.getVpByUserId(engMgrId)
            vpId = vpData.get('Id')
            why = 'you are the R&D VP for this branch'
            if vpId is not None:
                self.addRecipient(recipientIdMap, vpId, why)
            else:
                self.sfb.setLog('Could not determine VP for %s' %targetUserId)
                pass
            pass

        # add any static recipients
        if self.staticRecipients is not None:
            why = 'you are set to always receive this type of notice'
            for srId, srEmail in self.staticRecipients.items():
                self.addRecipient(recipientIdMap, srId, why)
                continue
            pass

        
        # Finally include all interested parties.
        interestedPartyIds = tbObj.findInterestedPartyIds()
        why = 'you are noted as an interested party to a component the branch addresses'
        for IPId in interestedPartyIds:
            self.addRecipient(recipientIdMap, IPId, why)
            continue


        #tbData = tbObj.getData('Task_Branch__c')
        #branchName = tbData.get('Branch__c')
        #print branchName
        #pprint.pprint(recipientIdMap)
        #print
        
        return recipientIdMap
    ## END gatherRecipients


    def buildNotification(self, event):
        msgDate = "%s Pacific Time" \
                  %event.get('timestamp').strftime('%d-%b-%Y %I:%M %p')

        targetId = event.get('targetId')
        recipInfo = event.get('userMap').get(targetId)
        recipName = "%s %s" %(recipInfo.get('FirstName',''),
                              recipInfo.get('LastName'))
        recipName = recipName.strip()
        
        tbObj = event.get('seedData')
        tbData = tbObj.getData('Task_Branch__c')

        tbId = tbData.get('Id')
        branch = tbData.get('Branch__c')
        stream = tbData.get('Code_Stream__c')
        #baUrl = '%s/%s/e' %(self.sfb.sfdc_base_url, event.get('triggerId'))
        tbUrl = '%s/%s' %(self.sfb.sfdc_base_url, tbId)

        datelineFmt = '%%%ss\n\n' %WW
        if tbId not in [None,'']:
            msg  = datelineFmt %msgDate
            msg += "%s,\n\n" %recipName
    
            delinquentDelta =  event.get('eventDatetime') - event.get('triggerObjDatetime')
            deltaText = dayNumToTxt(delinquentDelta)
            
            para = "The following branch has been waiting %s for %s. Please examine this branch and, if possible, move it forward." %(self.branchStatusText, deltaText)
            msg += "%s\n\n" %textwrap.fill(para, WW)
            msg += "Branch: %s, Code Stream: %s\n" %(branch, stream)
            msg += " * Task Branch Link: %s\n" %tbUrl
            return msg
    ## END buildNotification

    def action(self):
        """ Process actionable events """
        msgQueue = MailMessageQueue(test=self.opts.testflag)

        for actionEvent in self.actionList:
            # Gather all recipients
            recipientMap = self.gatherRecipients(actionEvent)
            actionEvent['intPartyIdMap'] = recipientMap
            actionEvent['userMap'] = self.queryRecipients(recipientMap.keys())

            delinquentDelta =  actionEvent.get('eventDatetime') \
                              - actionEvent.get('triggerObjDatetime')
            deltaText = dayNumToTxt(delinquentDelta)

            # build a notification and post it to each recipient's queue.
            # flag each with the immediate flag...
            body = self.buildNotification(actionEvent)
            subj = "Branch has been %s for %s."\
                   %(self.branchStatusText, deltaText)

            # post the message to each recipient's queue
            msgMap = {}
            for recipId, recipWhy in recipientMap.items():
                # check if the user is still active - skip inactive
                userInfo = actionEvent.get('userMap').get(recipId)
                if userInfo.get('IsActive') in [False, 'false']:
                    continue

                #print "%s %s" %(recipId, recipWhy)
                #print "%s %s" %(userInfo.get('Id'), userInfo.get('Email'))
                #print

                notification = copy.copy(MailNotification.notification)
                notification = {'subject': subj,
                                'body': body,
                                'timestamp': actionEvent.get('timestamp')}

                # note the recipient's user info
                notification['recipInfo'] = userInfo
                
                if recipId == actionEvent.get('targetId'):
                    notification['deferred'] = actionEvent.get('targetDeferred')
                else:
                    notification['deferred'] = actionEvent.get('partyDeferred')   
                    pass
                notification['why'] = recipWhy
                # collect for batch enqueueing
                #pprint.pprint(notification)
                msgMap[recipId] = notification
                
                continue
            # now, enqueue all the messages at once
            success = msgQueue.enqueue(msgMap)
            if success is True:
                # Finally, create the exclusion condition to prevent this
                # event from being processed again.
                self.exclude(actionEvent, subj, body)

            #break # for debug
            continue
        
        return ## END action

    pass
## END class ApprovalAlarmHandler


class TeamInboxAlarmHandler(BranchAlarmHandler):
    eventcode = "TBIN"
    branchStatus = "Approved, pending Team Branch"
    branchStatusText = "approved and in the team's SCM receiving bin"
    notifyRoles = ('Engineering Manager', 'RDVP')
    staticRecipients = {'00530000000cIBPAA2':'haroonc@molten-magma.com',
                        '00530000000cZcRAAU':'kshuk@molten-magma.com'}

    triggerDays = 5
    intervalDays = 1
    #limitTimes = 5
    
    pass ## END class MgrAppAlarmHandler
        

class TeamHoldAlarmHandler(BranchAlarmHandler):
    eventcode = "TBHD"
    branchStatus = "Team Branch Hold"
    branchStatusText = "in the team's SCM holding bin"
    notifyRoles = ('Engineering Manager', 'RDVP')
    staticRecipients = {'00530000000cIBPAA2':'haroonc@molten-magma.com',
                        '00530000000cZcRAAU':'kshuk@molten-magma.com'}

    triggerDays = 5 # How many days must condition exist before alarm triggers
    intervalDays = 1 # 0 to send once, 1 to send daily, 2 for every other day, etc.
    #limitTimes = 5 # Stop sending after triggerDays + (intervalDays * limit)

    pass ## END class PeAppAlarmHandler

class ScmHoldAlarmHandler(BranchAlarmHandler):
    eventcode = "SCMH"
    branchStatus = "SCM-Hold"
    branchStatusText = "in SCM Hold"
    scmContactId = '00330000009L0muAAC'
    notifyRoles = ('Developer','Engineering Manager')
    staticRecipients = {'00530000000cIBPAA2':'haroonc@molten-magma.com',
                        '00530000000cZcRAAU':'kshuk@molten-magma.com'}

    triggerDays = 2 # How many days must condition exist before alarm triggers
    intervalDays = 1 # 0 to send once, 1 to send daily, 2 for every other day, etc.
    #limitTimes = 5 # Stop sending after triggerDays + (intervalDays * limit)

    pass ## END class PeAppAlarmHandler



class ApprovalAlarmHarness:
    
    handlers = ('TeamInboxAlarmHandler',
                'TeamHoldAlarmHandler',
                'ScmHoldAlarmHandler')

    def __init__(self, opts=None):
        self.opts = opts

    def do(self):
        sfTool = SFTaskBranchTool(logname='BrDun')
    
        for handlerName in self.handlers:
            runHandler = '%s(sfTool, self.opts)' %handlerName
            
            handler = eval(runHandler)
            handler.flow()
            continue

        return


def main():
    op = OptionParser()
    op.add_option('-l', '--live', dest='testflag', action='store_false',
                  default=True,
                  help='connects to live storage for events - default is test')

    (opts, args) = op.parse_args()

    harness = ApprovalAlarmHarness(opts)
    harness.do()

    
if __name__ == '__main__':
    main()
