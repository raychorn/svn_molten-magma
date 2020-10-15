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

class BAActionAlarmHandler(NotificationEventHandler):
    """ Common bits for Approval Action events.
    An approval action is when a branch approval has been approved or rejected
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
        delta = datetime.timedelta(days=self.windowDays)
        
        dt = datetime.datetime.utcfromtimestamp(time.time())
        windowDateTime = dt - delta
        windowIsoDateTime = "%sZ" %windowDateTime.isoformat()

        sts = self.sfb.getServerTimestamp()
        currentSfDatetime = datetime.datetime(sts[0], sts[1], sts[2], sts[3], sts[4],
                                              sts[5], sts[6])

        fields = ('Id', 'OwnerId', 'Task_Branch__c', 'LastModifiedDate')
        where = [['Approval_Role__c','=',self.role],'and',
                 ['Status__c','=',self.status],'and',
                 ['LastModifiedDate','>=', windowIsoDateTime]]
                 
        if hasattr(self, 'limitTimes') and self.limitTimes > 1:
            maxTriggerDays = self.triggerDays + (self.intervalDays * self.limitTimes)
            delta = datetime.timedelta(days=maxTriggerDays)            
            maxDateTime = dt - delta
            maxIsoDateTime = "%sZ" %maxDateTime.isoformat()

            where += ['and', ['LastModifiedDate','>=', maxIsoDateTime]]
            pass


        res = self.sfb.query('Branch_Approval__c', where, fields)
        if res in BAD_INFO_LIST:
            res = []
            pass

        # process the results and build up event records
        # subjectid: the task branch id
        # ownerid: the prime recipient

        for ba in res:
            # get the whole task branch here so we can tuck the data struct in
            # the event representation
            tbObj = SFTaskBranch(sfTool=self.sfb)
            tbObj.loadBranchById(ba.get('Task_Branch__c'))
            tbData = tbObj.getData('Task_Branch__c')

            lastModified = ba.get('LastModifiedDate')
            triggerObjDatetime = parseSfIsoStr(lastModified)

            rawEvent = {'timestamp': datetime.datetime.now(),
                        'triggerObjDatetime': triggerObjDatetime,
                        'eventDatetime': currentSfDatetime,
                        'seedData': tbObj,
                        'eventcode': self.eventcode,
                        'triggerId': ba.get('Id'),
                        'subjectId': ba.get('Id'),
                        'targetId': tbData.get('OwnerId'), # branch dev
                        'targetDeferred': False,
                        'intPartyIdMap': {},
                        'partyDeferred': True}

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
        why = 'it concerns a branch that you developed or are responsible for'
        self.addRecipient(recipientIdMap, targetUserId, why)


        # Next, look up additional notificants from the other branch approvals.
        tbObj = eventStruct.get('seedData')
        baDataList = tbObj.getData('Branch_Approval__c')

        for baData in baDataList:
            if baData.get('Approval_Role__c') in self.notifyRoles:
                why = 'you are a(n) %s for this branch' \
                      %baData.get('Approval_Role__c')
                self.addRecipient(recipientIdMap, baData.get('OwnerId'), why)
                pass
            continue


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
        baDataList = tbObj.getData('Branch_Approval__c')

        tbId = tbData.get('Id')
        branch = tbData.get('Branch__c')
        stream = tbData.get('Code_Stream__c')
        baUrl = '%s/%s' %(self.sfb.sfdc_base_url, event.get('triggerId'))
        tbUrl = '%s/%s' %(self.sfb.sfdc_base_url, tbId)

        # find the CR num for which the fix was rejected
        crNum = None
        for ba in baDataList:
            if ba.get('Id') == event.get('triggerId'):
                crNum = ba.get('CR_List__c')
                if crNum is not None:
                    crNum = crNum.lstrip('0')
                    pass
                pass
            continue
        

        datelineFmt = '%%%ss\n\n' %WW
        if tbId not in [None,'']:
            msg  = datelineFmt %msgDate
            msg += "%s,\n\n" %recipName
    
            delinquentDelta =  event.get('eventDatetime') - event.get('triggerObjDatetime')
            deltaText = dayNumToTxt(delinquentDelta)
            
            para = "The fix for CR %s in branch %s in stream %s has been rejected by the CR originator. For further information, please view the rejected Branch Approval record (linked below) to see if the originator left any notes, or contact the CR originator directly." %(crNum, branch, stream)
            msg += "%s\n\n" %textwrap.fill(para, WW)
            msg += "CR: %s, Branch: %s, Code Stream: %s\n" %(crNum, branch, stream)
            msg += " * Branch Approval Link: %s\n" %baUrl
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
            subj = "%s approval has been %s."\
                   %(self.role, self.actiontxt)

            # post the message to each recipient's queue
            msgMap = {}
            for recipId, recipWhy in recipientMap.items():
                # check if the user is still active - skip inactive
                userInfo = actionEvent.get('userMap').get(recipId)
                if userInfo.get('IsActive') in [False, 'false']:
                    continue

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
## END class BAActionAlarmHandler


class CROrigRejectAlarmHandler(BAActionAlarmHandler):
    """
    Sent once on detecting that a CR Originator BA has been rejected.

    """
    eventcode = "ARCO" # Approval Rejected Cr Originator
    role = 'CR Originator'
    actiontxt = 'rejected'
    status = 'Merged - Rejected'
    notifyRoles = ('Engineering Manager')
    staticRecipients = {'00530000000cZcRAAU':'kshuk@molten-magma.com'}

    windowDays = 1
    intervalDays = 0
    limitTimes = 0
    
    pass
## END class CROrigRejectAlarmHandler


class BAActionAlarmHarness:
    
    handlers = ('CROrigRejectAlarmHandler',)

    def __init__(self, opts=None):
        self.opts = opts

    def do(self):
        sfTool = SFTaskBranchTool(logname='BAAct')
    
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

    harness = BAActionAlarmHarness(opts)
    harness.do()

    
if __name__ == '__main__':
    main()
