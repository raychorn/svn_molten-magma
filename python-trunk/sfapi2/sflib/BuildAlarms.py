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

class BuildAlarmHandler(NotificationEventHandler):
    """ Common bits for Build Alarms
    """
    role = None # must be provided by implementation
    notifyRoles = None # must be provided by implementation
    staticRecipients = None

    # override these in the subclasses
#    triggerDays = 7
#    intervalDays = 0
#    windowDays = 1
#    limitTimes = 5

    def poll(self):
        rawEventList = []

        # deltaDays is set in the event instance
        delta = datetime.timedelta(days=self.windowDays)
        
        dt = datetime.datetime.utcfromtimestamp(time.time())
        windowDateTime = dt - delta
        windowIsoDateTime = "%sZ" %windowDateTime.isoformat()

        # use the window to just as an additional limit so we are only checking
        # branches which may have become "ripe" since windowDays ago.

        sts = self.sfb.getServerTimestamp()
        currentSfDatetime = datetime.datetime(sts[0], sts[1], sts[2], sts[3],
                                              sts[4], sts[5], sts[6])

        where = [['Status__c','=',self.buildStatus],'and',
                 ['CreatedDate','>', windowIsoDateTime]]

        if hasattr(self, 'limitTimes') and self.limitTimes > 0:
            maxTriggerDays = self.triggerDays + (self.intervalDays * self.limitTimes)
            delta = datetime.timedelta(days=maxTriggerDays)            
            maxDateTime = dt - delta
            maxIsoDateTime = "%sZ" %maxDateTime.isoformat()

            where += ['and', ['LastModifiedDate','>=', maxIsoDateTime]]
            pass


        res = self.sfb.query('Build__c', where)
        if res in BAD_INFO_LIST:
            res = []
            pass

        # process the results and build up event records
        # subjectid: the task branch id
        # ownerid: the prime recipient

        for build in res:
            # get the whole task branch here so we can tuck the data struct in
            # the event representation
            lastModified = build.get('CreatedDate')
            triggerObjDatetime = parseSfIsoStr(lastModified)

            targetContactId = self.targetContactId

            # need to figure out the target of the notification
            
            rawEvent = {'timestamp': datetime.datetime.now(),
                        'triggerObjDatetime': triggerObjDatetime,
                        'eventDatetime': currentSfDatetime,
                        'seedData': build,
                        'eventcode': self.eventcode,
                        'triggerId': build.get('Id'),
                        'subjectId': build.get('Id'),
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
            why = 'you are on the build request notification email list'
            self.addRecipient(recipientIdMap, targetUserId, why)
        else:
            msg = "Target not found for event code %s on subject %s" \
                  %(self.eventcode, eventStruct.get('subjectId'))

        # add any static recipients
        if self.staticRecipients is not None:
            why = 'you are set to always receive this type of notice'
            for srId, srEmail in self.staticRecipients.items():
                self.addRecipient(recipientIdMap, srId, why)
                continue
            pass

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
        
        buildData = event.get('seedData')

        buildId = buildData.get('Id')
        buildName = buildData.get('Name')
        buildStream = buildData.get('Version__c')

        buildUrl = '%s/%s' %(self.sfb.sfdc_base_url, buildId)

        datelineFmt = '%%%ss\n\n' %WW
        msg  = datelineFmt %msgDate
        msg += "%s,\n\n" %recipName

        delinquentDelta =  event.get('eventDatetime') - event.get('triggerObjDatetime')
        deltaText = dayNumToTxt(delinquentDelta)
        
        msg += "The following build has been requested:\n\n"

        msg += "Build Name:  %s\n" %buildName
        msg += "Code Stream: %s\n" %buildStream
        msg += "Link to build: %s\n" %buildUrl
        msg += "\n"
        msg += "Please see the build object at the link above for full details\n"

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
            subj = "A new Build Request has been created."

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


class BuildRequestedHandler(BuildAlarmHandler):
    eventcode = "BLDC"
    buildStatus = "Requested"
    targetContactId = '0033000000A3q8TAAR' #sf_build_request@molten-magma.co
    staticRecipients = {'00530000000cIBPAA2':'haroonc@molten-magma.com',
                        '00530000000cZcRAAU':'kshuk@molten-magma.com'}

    triggerDays = 0
    windowDays = 1
    intervalDays = 0
    limitTimes = 0
    
    pass ## END class TeamInboxReadyHandler
        

class BuildAlarmHarness:
    
    handlers = ('BuildRequestedHandler',)

    def __init__(self, opts=None):
        self.opts = opts

    def do(self):
        sfTool = SFTaskBranchTool(logname='BldNote')
    
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

    harness = BuildAlarmHarness(opts)
    harness.do()

    
if __name__ == '__main__':
    main()
