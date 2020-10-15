"""
Look through all queues with items in them and see if we can send the deferred
items for each queue. If so, send all queued message. If not, send any 'alarm'
messages """
import os, sys
import time
from cStringIO import StringIO
import textwrap
from optparse import OptionParser

from sfUser2 import SFUser
from sfContact2 import SFContact

from MailMessageQueue import MailMessageQueue
from sfMagma import SFMagmaTool
from mail import MailServer, Message

from sfUtil import getTestMailAddr

WW = 72

myTZ = 'US/Pacific'
dateTimeFmt = "%Y-%m-%dT%H:%M:%S.000Z"

testMailAddr = getTestMailAddr()

class MailNotification:

    WW = 72 # wrap width
    notification = {'subject': None,
                    'body': None,
                    'timestamp': None,
                    'recipInfo': None,
                    'deferred': None,
                    'why': None}
                    
    FREQ_RA = 'Right Away'
    FREQ_DY = 'Once a Day'
    allFreqList = [FREQ_RA, FREQ_DY]

    def __init__(self, opts=None):
        self.opts = opts

        # determine test status from opts
        self.mq = MailMessageQueue(test=opts.testflag)
        self.sfb = SFMagmaTool(logname='mailNotf')
        self.recipientMap = {}

        self.nowTime = time.time()
        return
    ## END __init__
    
    def do(self):
        recipIdList = self.mq.getQueueIds()
        recipMap = self.getRecipientInfo(recipIdList)
        
        #print "RECEIPENT MAP...............:" %recipMap

        for recipId, userTuple in recipMap.items():
            (user, contact) = userTuple

            # prefer user over contact as the "recipient object"
            recipient = user
            if recipient is None:
                recipient = contact
            
            recipFullName = self.getFullName(recipient)

            # OK if contact is None here - method handles it
            deferredReady = self.isDeferredReady(contact)
            
            # open the queue again
            q = self.mq.open()
            if q is False:
                self.mq.close()
                pass

            try:
                self.mailserver = MailServer()
                
                messageQueue = self.mq.readUserQueue(recipId)
                
                alarmQueue, deferQueue, otherQueue = self.separateAlarms(messageQueue)

                if len(alarmQueue) > 0:                       
                    # send the alarm message(s)
                    if ((self.buildAlarmMessage(recipFullName,alarmQueue) not in [None,''])):
                        subj, alarmMessage = self.buildAlarmMessage(recipFullName,
                                                                    alarmQueue)
                        if self.sendMessage(recipient, subj, alarmMessage):
                            # success - clear the alarms
                            alarmQueue = []
                            pass
                    pass

                if (len(deferQueue) > 0) and deferredReady is True:
                    # send the deferred notice(s)
                    if (self.buildDeferredMessage(recipFullName,deferQueue)) not in [None,'']:
                        subj, deferMessage = self.buildDeferredMessage(recipFullName,
                                                                       deferQueue)
                        if self.sendMessage(recipient, subj, deferMessage):
                            # success - clear the deferreds
                            deferQueue = []
    
                            # set the last sent date
                            # again, OK if contact is None - method handles it
                            self.updateLastNotificationDate(contact)
                            pass

                    pass
                
                residualQueue = alarmQueue + deferQueue + otherQueue
                if len(residualQueue) > 0:
                    residualQueue.sort(lambda a, b: cmp(a.get('timestamp'),
                                                        b.get('timestamp')))
                    pass

                self.mq.writeUserQueue(recipId, residualQueue)
                self.mq.commit()
            finally:
                self.mailserver = None
                self.mq.close()
                self.mq.pack()
                pass
            continue
        return
    ## END flow
            
    def getRecipientInfo(self, idList):
        userIdList = []
        contactIdList = []
        for id in idList:
            if id[:3] == '005':
                userIdList.append(id)
            elif id[:3] == '003':
                contactIdList.append(id)
                pass
            continue

        recipientMap = {}

        # get the users
        if len(userIdList):
            userMap = self.getUserInfo(userIdList)
            recipientMap.update(userMap)
            pass

        # now, get the contacts
        if len(contactIdList):
            contactMap = self.getContactInfo(contactIdList)
            recipientMap.update(contactMap)
            pass

        self.recipientMap = recipientMap
        return recipientMap
    ## END getRecipientInfo
        

    def getUserInfo(self, userIdList):
        """ Given a list of user IDs, return a map by user ID of user object,
        and associated contact object tuples """
        userList = SFUser.retrieve(self.sfb, userIdList)
        userMap = {}
        for user in userList:
            contact = None
            userData = user.getDataMap()
            userId = userData.get('Id')
            contactId = userData.get('User_Contact_Id__c')
            
            if contactId is not None:
                contact = SFContact.retrieve(self.sfb, contactId)
                pass

            userMap[userId] = (user, contact)
            continue

        return userMap
    ## getUserInfo

    def getContactInfo(self, contactIdList):
        contactList = SFContact.retrieve(self.sfb, contactIdList)
        contactMap = {} 
        
        for contact in contactList:
            user = None
            contactData = contact.getDataMap()
            contactId = contactData.get('Id')
            userId = contactData.get('Contact_User_Id__c')
            
            if userId is not None:
                user = SFUser.retrieve(self.sfb, userId)
                pass
            
            contactMap[contactId] = (user, contact)
            continue
        
        return contactMap
    ## END getContactInfo
   
    def getFullName(self, obj):
        """ Given a user or contact object, return the Full Name """
        objData = obj.getDataMap()
        fullName = "%s %s" %(objData.get('FirstName',''),
                             objData.get('LastName'))
        fullName = fullName.strip()
        return fullName
    ## END getFullname
    
    def parseLastNotificationDate(self, contact):
        """
        from the contact provided, takes value of the lastReportDate
        field if it exists, or the default last report time if it
        does not, and returns a time struct and epoch time
        """
        global myTZ
        
        contactData = contact.getDataMap()

        if os.environ.get('TZ','') != myTZ:
            os.environ['TZ'] = myTZ
            time.tzset()
            pass

        if contactData.has_key('Notification_Last_Sent__c'):
            # parse last report time into epoch time
            UTCTimeStr = contactData['Notification_Last_Sent__c']
            os.environ['TZ'] = "UTC"
            time.tzset()
        else:
            # use a default value
            UTCTimeStr = "2005-01-01T00:30:00.000Z"
            pass

        lastReportUTCStruct = time.strptime(UTCTimeStr, dateTimeFmt)
        
        lastReportEpoch = time.mktime(lastReportUTCStruct)

        # Back to our time
        if os.environ['TZ'] != myTZ:
            os.environ['TZ'] = myTZ
            time.tzset()
            pass

        lastReportTimeStruct = time.localtime(lastReportEpoch)

        return lastReportTimeStruct, lastReportEpoch, UTCTimeStr
    ## END parseLastNotificationDate(self, contact)
        
    def updateLastNotificationDate(self, contact):
        """
        Update contact's Last Report field with notifier's reportTime
        (as a UTC time struct). 
        """
        success = False
        contactData = {}
        if contact is not None:
            # check that reportTime isn't getting shifted upon insert...
            contactData = contact.getDataMap()
            contactData['Notification_Last_Sent__c'] = self.nowTime

            if self.opts.testflag is False:
                success = contact.update()
                pass
            pass
            
        if success is False:
            msg = 'Update of last notification time for contact %s (%s) FAILED' %(contactData.get('Email'), contactData.get('Id'))

            if self.opts.testflag is True:
                msg = 'Test mode - skipping update of last notification time for contact %s (%s)' %(contactData.get('Email'), contactData.get('Id'))
                pass
                
            self.sfb.setLog(msg, 'info')
            pass
        return success
    ## END updateLastNotificationDate(self, contact)

    def isDeferredReady(self, contact):
        """ Determine if a user is ready to recieve deferred notifications.
        Return True or False """

        frequency = self.FREQ_RA
        secsSinceLastNotification = 1000000000
        if contact is not None:
            (lastStruct, lastEpoch, lastUTC) = \
                         self.parseLastNotificationDate(contact)
            secsSinceLastNotification = int(self.nowTime - lastEpoch)

            ctData = contact.getDataMap()
            #print "Note for %s" %ctData['Email']
            frequency = ctData.get('Notification_Frequency__c',self.FREQ_RA)
            if frequency not in self.allFreqList:
                frequency = self.FREQ_RA
                pass
            pass

        #print "frequency is %s" %frequency

        FUDGE = 5 * 60
        DAILY = (24 * 60 * 60) - FUDGE
        ready = False
        if frequency == self.FREQ_DY and \
               secsSinceLastNotification > DAILY:
            #print "secsSinceLastNotification: %s" %secsSinceLastNotification
            #print "DAILY: %s" %DAILY
            ready = True
        elif frequency == self.FREQ_RA:
            ready = True
        elif self.opts.testflag is True:
            ready = True
            pass
        
        #print "Good to send? %s\n" %ready
        return ready
    ## END isDeferredReady


    def separateAlarms(self, userMsgQueue):
        """ Iterate through the message queue and separate alarms from
        deferrable notifications """

        alarmQueue = []
        deferQueue = []
        otherQueue= []
        for msg in userMsgQueue:  
            isCustom=msg.get('eventcode')            
            if isCustom not in ['CUSTOM']:
                            
                if msg.get('deferred') is True:
                    deferQueue.append(msg)
                else:
                    alarmQueue.append(msg)
                    pass
            else:
                otherQueue.append(msg)
            continue

        return alarmQueue, deferQueue, otherQueue
    ## END separateAlarms
    
    def buildAlarmMessage(self, userName, alarmQueue):
        msgBuf = StringIO()
        #print "alarmQueue LENGTH ......................... %s"%len(alarmQueue)
        if len(alarmQueue) < 1 :            
            return
        else:
            #subject = '%s: An alarm requires your attention' %userName
            #intro = 'The following alarm requires your attention:'
            if len(alarmQueue) > 0:
                subject = '%s: An alarm requires your attention' %userName
                intro = 'The following alarm requires your attention:'
                subject = '%s: %d alarms require your attention' %(userName,
                                                                   len(alarmQueue))
                intro = 'The following %d alarms require your attention:' \
                        %len(alarmQueue)
                
                msgBuf.write('%s,\n\n' %userName)
                msgBuf.write('%s\n' %intro)
                msgBuf.write('-' * WW + '\n')
                if  (self.buildGenericMessage(alarmQueue, userName)  in [None,'']):
                    return
        
                msgBuf.write(self.buildGenericMessage(alarmQueue, userName))
                pass
                        
            return subject, msgBuf.getvalue()

    def buildDeferredMessage(self, userName, deferQueue):
        msgBuf = StringIO()
        
        if len(deferQueue) < 1:
            return
        else:
            #subject = '%s: Event Notification (1 event)' %userName
            #intro = 'The following notification is for your information:'
            if len(deferQueue) > 0:
                subject = '%s: Event Notification (1 event)' %userName
                intro = 'The following notification is for your information:'
                subject = '%s: Event Notification (%d events)' %(userName,
                                                                 len(deferQueue))
                intro = 'The following %d notifications are for your information:' \
                        %len(deferQueue)
                
    
                msgBuf.write('%s,\n\n' %userName)
                msgBuf.write('%s\n' %textwrap.fill(intro, WW))
                msgBuf.write('-' * WW + '\n')  
                #print "deferQueue, userName .. %s, %s" %(deferQueue, userName)
                
                #print "BUILD ........ %s"%(self.buildGenericMessage(deferQueue, userName))
                if  (self.buildGenericMessage(deferQueue, userName)  in [None,'']):
                    return                        
                    
                msgBuf.write(self.buildGenericMessage(deferQueue, userName))
                pass
            
            return subject, msgBuf.getvalue()


    def buildGenericMessage(self, msgQueue, userName):
        msgBuf = StringIO()
       
        for msg in msgQueue:
            
            msgBuf.write('\n')
            if msg.get('body') in [None,'']:
                return None
            
            if msg.get('subj') is not None:
                subj = 'RE: %s' %msg.get('subj').encode('ascii','replace')
                msgBuf.write('%s\n' %textwrap.fill(subj, WW))
                msgBuf.write('\n')
                pass

            # body has already been formatted - do not wrap
            if msg.get('body') is not None:
                msgBuf.write('%s\n' %msg.get('body').encode('ascii','replace'))
                msgBuf.write('\n')
                pass
            
            if msg.get('why') is not None:
                msgBuf.write('%s, you are receiving this notification because:\n' %userName)
                msgBuf.write('%s\n' %msg.get('why').encode('ascii','replace'))
                msgBuf.write('\n')
                pass
                             
            msgBuf.write('-' * WW + '\n')
            continue
        
        return msgBuf.getvalue()
    ## END buildGenericMessage
            

    def sendMessage(self, recip, subj, body):
        global testMailAddr
        
        fromAdd = 'salesforce-support@molten-magma.com'
        toAdd = recip.getDataMap()['Email']


        logmsg = 'Sending notification mail for %s' %toAdd
        if self.opts.testflag is True:
            logmsg = 'Notification mail for %s, sent to test recipient %s' \
                     %(toAdd, testMailAddr)
            toAdd = testMailAddr
            pass

        self.sfb.setLog(logmsg , 'info')

        try:
            msg = Message(fromAdd, toAdd, body, subj)
            self.mailserver.sendEmail(msg)
        except:
            return False

        return True
    ## END sendMessage


def main():
    global testMailAddr
    
    op = OptionParser()
    op.add_option('-l', '--live', dest='testflag', action='store_false',
                  default=True,
                  help='connects to live storage for events - default is test')

    (opts, args) = op.parse_args()

    if opts.testflag is True:
        print "Connecting to test message queue storage and sending all messages to:\n\t%s" %testMailAddr
        pass

    mn = MailNotification(opts)
    mn.do()
    return


if __name__ == '__main__':
    main()
    
