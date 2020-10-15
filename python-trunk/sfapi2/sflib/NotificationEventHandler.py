"""
"""
import datetime

from EventHandler import EventHandler
from sfConstant import *
from TimeUtil import parseSfIsoStr
from sfUtil import convertId15ToId18

# structure to define a notification (MOVE TO NotificationQueue)
notification = {'subject': '',
                'body': '',
                'timestamp': datetime.datetime.now(),
                'deferred': True,
                'why': 'text describing why recipient is getting the notice',
                'recipInfo': {}
                }

class NotificationEventHandler(EventHandler):
    """
    Generic class from which types of Notification Events will be subclassed
    """
    # use parent's __init__

    # override these in the subclasses
    triggerDays = 5
    intervalDays = 0 # how often (in days) to trigger on event? zero for once only
    limitTimes = 0 # how many days past triggerDays should event no longer trigger?
                   # zero for ad infinitum (upper limit = limitTimes * intervalDays)

    def filter(self):
        """ Implement a common way to detect exclusion condition for
        Noticiation Events """
        actionList = []

        for rawEvent in self.rawEventList:

            fields = ('Id', 'Event_Code__c', 'CreatedDate')
            where = [['Event_Code__c','=',rawEvent.get('eventcode')],'and',
                     ['WhatId','=',rawEvent.get('subjectId')]]

            # is the event target a user or contact?
            if rawEvent.get('targetId')[:3] == '005':
                where += ['and', ['OwnerId','=',rawEvent.get('targetId')]]
            elif rawEvent.get('targetId')[:3] == '003':
                where += ['and', ['WhoId','=',rawEvent.get('targetId')]]
                pass
            

            # this is so we can re-trigger if the event was reset after notifications
            # were sent and now the event has occurred again.
            if rawEvent.get('lastModDatetime') is not None:
                where += ['and', ['CreatedDate', '>=', rawEvent.get('TriggerObjDatetime')]]
                pass
            
            res = self.sfb.query('Task', where, fields)
            if res in BAD_INFO_LIST:
                res = []
                pass

            if self.opts.testflag is True:
                # always allow if testing
                print "filter - always allow in test mode\ntargetId: %s, subjectId: %s; ecode: %s" %(rawEvent.get('targetId'), rawEvent.get('subjectId'), rawEvent.get('eventcode'))
                actionList.append(rawEvent)
            elif len(res) == 0:
                # Didn't find any exclusion conditions since the trigger object was last
                # touched
                actionList.append(rawEvent)
            elif self.intervalDays > 0:
                # sort the result task list by created date to pick the latest one
                res.sort(lambda a, b: cmp(a.get('CreatedDate'),
                                          b.get('CreatedDate')))

                lastTask = res[-1]
                lastTaskCreateDt = parseSfIsoStr(lastTask.get('CreatedDate'))
                lastTaskDelta = rawEvent.get('eventDatetime') - lastTaskCreateDt

                # are we at least 'intervalDays' days past
                # the last time this event triggered?
                if self.intervalDays <= lastTaskDelta.days:
                    actionList.append(rawEvent)
                    #print "yup, we can trigger again"
                else:
                    #print "nope, not time yet"
                    pass
                
                pass
            
            continue

        self.actionList = actionList
        return

    def exclude(self, eventStruct, subj, desc, priority='Normal'):
        """
        This will implement the exclusion condition for notification events
        which is to create a notification task. """
        notificationTaskType = '0123000000009xEAAQ'

        if self.opts.testflag is True:
            print "exclude - not creating exclusion condition in test mode"
            return

        if priority not in ['Low','Normal','High']:
            priority = 'Normal'
        
        # create a task as the exclusion condition
        taskData = {'RecordTypeId': notificationTaskType,
                    'Type': 'Other',
                    'Status': 'Complete',
                    'WhatId': eventStruct.get('subjectId'),
                    'Event_Code__c': eventStruct.get('eventcode'),
                    'Priority': priority,
                    'Subject': subj,
                    'Description': desc}

        # is the event target a user or contact?
        if eventStruct.get('targetId')[:3] == '005':
            taskData['OwnerId'] = eventStruct.get('targetId')
        elif eventStruct.get('targetId')[:3] == '003':
            taskData['WhoId'] = eventStruct.get('targetId')
            pass
       

        # insert the task
        ret = self.sfb.create('Task', data=taskData)
        taskId = None
        if ret not in BAD_INFO_LIST:
            taskId = ret[0]
            pass

        #print "Exclusion task: %s" %taskId
        
        return taskId
    ## END exclude

    def addRecipient(self, recipMap, userId, why):
        noMailList  = ['00530000000KnJgAAK', '00330000000MDhwAAG'] #hamid
        noMailList += ['00530000000KnPiAAK', '00330000000MDjXAAW'] #gregw
        noMailList += ['00530000000UrerAAC', '00330000000MDhBAAW'] #rajeev
        noMailList += ['00530000000KnPQAA0', '00330000000MDgvAAG'] #roy

        userId = convertId15ToId18(userId) # ensure id18
        
        if userId not in noMailList:
            if recipMap.has_key(userId):
                recipMap[userId] += '\n * %s' %why
            else:
                recipMap[userId] = ' * %s' %why
                pass
            pass
        return
    ## END addRecipient

    def queryRecipients(self, recipientIdList):
        """
        Get the first name, last name, email address and active status
        of each recipient.
        """
        recipMap = {}

        userIdList = []
        contactIdList = []
        
        #print "recipientIdList .... %s" %recipientIdList
        for id in recipientIdList:            
            if id not in [None,'']:
                if id[:3] == '005':
                    userIdList.append(id)
                elif id[:3] == '003':
                    contactIdList.append(id)
                    pass
                continue
            
        if len(userIdList):
            fields = ('Id', 'FirstName', 'LastName', 'Email', 'IsActive')
            res = self.sfb.retrieve(userIdList, 'User', fields)

            if res not in BAD_INFO_LIST:
                for user in res:
                    userId = user.get('Id')
                    recipMap[userId] = user
                    continue
                pass
            pass
        
        if len(contactIdList):
            fields = ('Id', 'FirstName', 'LastName', 'Email')
            res = self.sfb.retrieve(contactIdList, 'Contact', fields)

            if res not in BAD_INFO_LIST:
                for user in res:
                    userId = user.get('Id')
                    recipMap[userId] = user
                    continue
                pass
            pass

        return recipMap ## END queryRecipients
    

    

        
