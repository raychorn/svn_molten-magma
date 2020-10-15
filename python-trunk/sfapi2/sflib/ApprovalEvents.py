"""
Poll for 'Ripe' approvals and provide a summary of all branches needing
approval
"""
import copy
import datetime
import time
import pprint
import textwrap
from optparse import OptionParser

from sfUtil import numToTxt
from NotificationEventHandler import NotificationEventHandler
from sfConstant import *
from sfTaskBranch import SFTaskBranch, SFTaskBranchTool
from MailNotification import MailNotification, WW
from MailMessageQueue import MailMessageQueue
from TimeUtil import parseSfIsoStr, dayNumToTxt

class ApprovalEventHandler(NotificationEventHandler):
    """ Common bits for Approval events.
    """

    role = None # must be provided by implementation
    notifyRoles = None # must be provided by implementation
    staticRecipients = None

    def poll(self):
        rawEventList = []

        dt = datetime.datetime.utcfromtimestamp(time.time())

        fields = ('Id', 'OwnerId', 'Task_Branch__c', 'LastModifiedDate')
        where = [['Approval_Role__c','=',self.role],'and',
                 '(',['Approve__c','!=','Approve'],'or',
                 ['Approve__c','!=','Reject'],')','and',
                 ['Status__c','=','Approving']]

        res = self.sfb.query('Branch_Approval__c', where, fields)
        if res in BAD_INFO_LIST:
            res = []
            pass

        eventMap = {}
        tbIdList = []
        for ba in res:
            tbId = ba.get('Task_Branch__c')
            if tbId not in tbIdList:
                tbIdList.append(tbId)
                pass

            ownerId = ba.get('OwnerId')
            if eventMap.has_key(ownerId):
                eventMap[ownerId]['approvals'].append(ba)
            else:
                eventMap[ownerId] = {'approvals': [ba,],
                                     'timestamp': dt,
                                     'targetId': ownerId,
                                     'targetDeferred': True,
                                     'intPartyIdMap': {},
                                     'partyDeferred': True}

                pass
            continue

        # now, retrieve the task branch info
        tbFields = ('Id', 'Branch__c', 'Code_Stream__c')
        tbList = []
        res = self.sfb.retrieve(tbIdList, 'Task_Branch__c', tbFields)
        if res not in BAD_INFO_LIST:
            tbList = res
            pass

        # map the task branch info by ID
        tbMap = {}
        for tb in tbList:
            tbMap[tb.get('Id')] = tb
            continue

        # store in the handler object
        self.rawEventList = eventMap.values()
        self.tbMap = tbMap
        return ## END poll


    def filter(self):
        """ Override filter method as we're really building a report. """
        self.actionList = self.rawEventList
    
            
    def exclude(self):
        """ No exclusion needed. The event trigger is really a cron job. """
        return
    
    

    def gatherRecipients(self, eventStruct):
        """ Determine the recipients of this message in a number of ways.
        Note the reason each recipient is getting the notice - Should be a
        phrase which completes the sentence, 'You are receiving this notice
        because...'
        """
        targetUserId = eventStruct.get('targetId')
        recipientIdMap = {}

        # first, the target of the notification
        why = 'this notice describes action(s) you need to take'
        self.addRecipient(recipientIdMap, targetUserId, why)

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

        datelineFmt = '%%%ss\n\n' %WW
        msg  = datelineFmt %msgDate
        msg += "%s,\n\n" %recipName

        approvalList = event.get('approvals')
        # sort to group like streams together
        
        #print "self.tbMap .... %s" %self.tbMap
        if(self.tbMap not in [None,'',{}]):
            approvalList.sort(lambda a, b: cmp(self.tbMap.get(a.get('Task_Branch__c')).get('Code_Stream__c'), self.tbMap.get(b.get('Task_Branch__c')).get('Code_Stream__c')))

        branchNumTxt = 'branch is'
        if len(approvalList) > 1:
            branchNumTxt = "%s branches are" %numToTxt(len(approvalList))
            pass
                                                       
        para = "Here is your %s approval to-do list as of the date and time above." %self.role
        msg += "%s\n\n" %textwrap.fill(para, WW)
        
        para = "The following %s awaiting your approval as %s. Using the links provided, please investgate each branch and then approve or reject the related branch approval." %(branchNumTxt, self.role)
        msg += "%s\n\n" %textwrap.fill(para, WW)

        para = "If any branches listed below need to be removed from Salesforce, please contact salesforce-support@molten-magma.com"
        msg += "%s\n\n" %textwrap.fill(para, WW)

        msg += '\n'


        for ba in approvalList:
            baId = ba.get('Id')
            tbId = ba.get('Task_Branch__c')
            tbData = self.tbMap.get(tbId)
            if tbData not in [None,'']:

                branch = tbData.get('Branch__c')
                stream = tbData.get('Code_Stream__c')
    
                #baUrl = '%s/%s/e' %(self.sfb.sfdc_base_url, baId)
                baUrl = '%s/%s' %(self.sfb.sfdc_base_url, baId)
                tbUrl = '%s/%s' %(self.sfb.sfdc_base_url, tbId)
    
                msg += "Branch: %s, Code Stream: %s\n" %(branch, stream)
                msg += " * Branch Approval: %s\n" %baUrl
                msg += " * Task Branch Link: %s\n\n" %tbUrl
                continue

        msg += '\n'

        para = "For a constantly updated list of all branches needing your approval, please visit https://na1.salesforce.com/00O30000000fcAy"
        msg += "%s\n\n" %textwrap.fill(para, WW)
        
        return msg
    ## END buildNotification

    def action(self):
        """ Process actionable events """
        msgQueue = MailMessageQueue(test=self.opts.testflag)

        for actionEvent in self.actionList:
            # Gather all recipients
            recipientMap = self.gatherRecipients(actionEvent)
            actionEvent['userMap'] = self.queryRecipients(recipientMap.keys())

            # build a notification and post it to each recipient's queue.
            # flag each with the immediate flag...
            body = self.buildNotification(actionEvent)
            subj = "You have %s branches pending your %s approval."\
                   %(len(actionEvent.get('approvals')), self.role)

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
                msgMap[recipId] = notification
                
                continue

            # now, enqueue all the messages at once
            success = msgQueue.enqueue(msgMap)

            #break # for debug
            continue
        
        return ## END action

    pass ## END class ApprovalDunningEventHandler


class MgrAppEventHandler(ApprovalEventHandler):
    eventcode = "MAPD" # Manager Approvals, daily
    role = "Engineering Manager"
    notifyRoles = ()
    staticRecipients = {'00530000000cZcRAAU':'kshuk@molten-magma.com'}

    triggerDays = 0
    intervalDays = 1
    #limitTimes = 5
    
    pass ## END class MgrAppEventHandler
        

class PeAppEventHandler(ApprovalEventHandler):
    eventcode = "PAPD" # PE Approvals, daily
    role = "Product Engineer"
    notifyRoles = ()
    staticRecipients = {'00530000000cZcRAAU':'kshuk@molten-magma.com'}

    triggerDays = 0 # How many days must condition exist before alarm triggers
    intervalDays = 1 # 0 to send once, 1 to send daily, 2 for every other day, etc.
    #limitTimes = 5 # Stop sending after triggerDays + (intervalDays * limit)

    pass ## END class PeAppEventHandler


class ApprovalHarness:
    
    handlers = ('MgrAppEventHandler',
                'PeAppEventHandler')

    def __init__(self, opts=None):
        self.opts = opts

    def do(self):
        sfTool = SFTaskBranchTool(logname='AppNote')
    
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

    harness = ApprovalHarness(opts)
    harness.do()

    
if __name__ == '__main__':
    main()
