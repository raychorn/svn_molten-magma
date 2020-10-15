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

class ApprovalAlarmHandler(NotificationEventHandler):
    """ Common bits for Approval Dunning events.
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

        fields = ('Id', 'OwnerId', 'Task_Branch__c', 'LastModifiedDate')
        where = [['Approval_Role__c','=',self.role],'and',
                 '(',['Approve__c','!=','Approve'],'or',
                 ['Approve__c','!=','Reject'],')','and',
                 ['Status__c','=','Approving'],'and',
                 ['LastModifiedDate','<', delinquentIsoDateTime]]

        if hasattr(self, 'limitTimes') and self.limitTimes > 0:
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

            lastModified = ba.get('LastModifiedDate')
            triggerObjDatetime = parseSfIsoStr(lastModified)

##            delinquentDelta = currentSfDatetime - lastModDatetime
##            print ba.get('Id')
##            print dayNumToTxt(delinquentDelta.days)
##            print
            
            rawEvent = {'timestamp': datetime.datetime.now(),
                        'triggerObjDatetime': triggerObjDatetime,
                        'eventDatetime': currentSfDatetime,
                        'seedData': tbObj,
                        'eventcode': self.eventcode,
                        'triggerId': ba.get('Id'),
                        'subjectId': ba.get('Task_Branch__c'),
                        'targetId': ba.get('OwnerId'),
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
        
        #print "recipient Map  %s" %recipientIdMap

        # first, the target of the notification
        why = 'this notice describes an action you need to take'
        self.addRecipient(recipientIdMap, targetUserId, why)


        # Now, look up the target's engineering manager
        mgrData = self.sfb.getMgrByID(targetUserId)
        mgrId = mgrData.get('Id')
        why = 'you are the manager of the recipient of this notice'
        self.addRecipient(recipientIdMap, mgrId, why)


        # look up the target's VP (thru manager)
        vpData = self.sfb.getVpByUserId(targetUserId)
        vpId = vpData.get('Id')
        why = 'you are the VP for the recipient of this notice'
        if vpId is not None:
            self.addRecipient(recipientIdMap, vpId, why)
        else:
            self.sfb.setLog('Could not determine VP for %s' %targetUserId)
            pass
        
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


        #tbData = tbObj.getData('Task_Branch__c')
        #branchName = tbData.get('Branch__c')
        #print branchName
        #print" Rec id ..... %s" %recipientIdMap
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
        baUrl = '%s/%s' %(self.sfb.sfdc_base_url, event.get('triggerId'))
        tbUrl = '%s/%s' %(self.sfb.sfdc_base_url, tbId)

        datelineFmt = '%%%ss\n\n' %WW
        if tbId not in [None,'']:
            msg  = datelineFmt %msgDate
            msg += "%s,\n\n" %recipName
    
            delinquentDelta =  event.get('eventDatetime') - event.get('triggerObjDatetime')
            deltaText = dayNumToTxt(delinquentDelta)
            
            para = "The following branch has been waiting for your approval as %s for %s. Please approve this branch if it is acceptable or reject it back to the developer if it requires additional work." %(self.role, deltaText)
            msg += "%s\n\n" %textwrap.fill(para, WW)
            msg += "Branch: %s, Code Stream: %s\n" %(branch, stream)
            msg += " * Branch Approval: %s\n" %baUrl
            msg += " * Task Branch Link: %s\n" %tbUrl
            return msg
    ## END buildNotification

    def action(self):
        """ Process actionable events """
        msgQueue = MailMessageQueue(test=self.opts.testflag)

        for actionEvent in self.actionList:
            # Gather all recipients
            #print "Action event ....... %s" %actionEvent
            recipientMap = self.gatherRecipients(actionEvent)
            #print "recipient map ......." %recipientMap
            actionEvent['intPartyIdMap'] = recipientMap
            actionEvent['userMap'] = self.queryRecipients(recipientMap.keys())

            delinquentDelta =  actionEvent.get('eventDatetime') \
                              - actionEvent.get('triggerObjDatetime')
            deltaText = dayNumToTxt(delinquentDelta)

            # build a notification and post it to each recipient's queue.
            # flag each with the immediate flag...
            body = self.buildNotification(actionEvent)
            subj = "%s approval has been pending for %s."\
                   %(self.role, deltaText)

            # post the message to each recipient's queue
            msgMap = {}
            for recipId, recipWhy in recipientMap.items():
                # check if the user is still active - skip inactive
                if recipId not in [None,'']:
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


class MgrAppAlarmHandler(ApprovalAlarmHandler):
    eventcode = "MDN5"
    role = "Engineering Manager"
    notifyRoles = ('Developer','CR Originator')
    staticRecipients = {'00530000000cIBPAA2':'haroonc@molten-magma.com',
                        '00530000000cyplAAA':'dlee@molten-magma.com',
                        '00530000000cZcRAAU':'kshuk@molten-magma.com'}

    triggerDays = 5
    intervalDays = 1
    #limitTimes = 5
    
    pass ## END class MgrAppAlarmHandler
        

class PeAppAlarmHandler(ApprovalAlarmHandler):
    eventcode = "PDN5"
    role = "Product Engineer"
    notifyRoles = ('Developer','CR Originator')
    staticRecipients = {'00530000000cIBPAA2':'haroonc@molten-magma.com',
                        '00530000000cyplAAA':'dlee@molten-magma.com',
                        '00530000000cZcRAAU':'kshuk@molten-magma.com'}

    triggerDays = 5 # How many days must condition exist before alarm triggers
    intervalDays = 1 # 0 to send once, 1 to send daily, 2 for every other day, etc.
    #limitTimes = 5 # Stop sending after triggerDays + (intervalDays * limit)

    pass ## END class PeAppAlarmHandler


class ApprovalAlarmHarness:
    
    handlers = ('MgrAppAlarmHandler',
                'PeAppAlarmHandler')

    def __init__(self, opts=None):
        self.opts = opts

    def do(self):
        sfTool = SFTaskBranchTool(logname='AppDun')
    
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
