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
import datetime
from optparse import OptionParser

from sfMagma import *
from sfConstant import *
from sfUtil import *

WW = 72

myTZ = 'US/Pacific'
dateTimeFmt = "%Y-%m-%dT%H:%M:%S.000Z"

testMailAddr = getTestMailAddr()

class CustomMailNotification(SFMagmaTool):

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
        self.sfb = SFMagmaTool(logname='CustMailNotf')
        self.recipientMap = {}

        self.nowTime = time.time()
        return
    ## END __init__
    
    def do(self):      
        queueEmail=False  
        recipIdList = self.mq.getQueueIds()  
                      
        recipMap = self.getRecipientInfo(recipIdList)
        deferredReady = self.isTime() 
                
        for recipId, userTuple in recipMap.items():
            (user, contact) = userTuple
            
            q = self.mq.open()
            if q is False:
                self.mq.close()
                pass

            try:
                self.mailserver = MailServer()                
                messageQueue = self.mq.readUserQueue(recipId)           
                
                """for msg in messageQueue:   
                                                                                     
                    isAlias=msg.get('isAlias')
                    print "is Alias ........%s"%isAlias
                    email=msg.get('email')
                    print "Email ADD %s" %email
                    eventCode=msg.get('eventcode')
                    pass  """               
                if recipId in ['0033000000HPwQRAA1','0033000000HPwQR']:                    
                    recipient = user            
                    if recipient is None:
                        recipient = contact
                    recipFullName="Salesforce User"
                    queueEmail=True
                    aliasContactId=[]
                    aliasContactId.append(recipId)
                    #recipient = self.getAliasInfo(aliasContactId,messageQueue)                    
                    alarmQueue, deferQueue ,otherQueue = self.separateAlarms(messageQueue)
                    if len(alarmQueue):
                        # send the alarm message(s)
                        disEmail=self.separateAliasEmail(alarmQueue)
                        for ds in disEmail:                            
                            aliasQueue=self.separateAliasQueue(alarmQueue, ds)
                            subj, alarmMessage = self.buildAlarmMessage(recipFullName,
                                                                    aliasQueue)
                            if self.sendMessageAlias(ds, subj, alarmMessage):
                            # success - clear the alarms
                                aliasQueue = []
                                pass
                            pass #for
                        alarmQueue = []
                        pass
    
                    if len(deferQueue) and deferredReady is True:
                        # send the deferred notice(s)
                        disEmail=self.separateAliasEmail(deferQueue)
                        for ds in disEmail:
                            aliasDefQueue=self.separateAliasQueue(deferQueue, ds)
                            subj, deferMessage = self.buildDeferredMessage(recipFullName,
                                                                       aliasDefQueue)
                            if self.sendMessageAlias(ds, subj, deferMessage):
                                # success - clear the deferreds
                                aliasDefQueue = []   
                                pass 
                            pass #for
                        deferQueue = []
    
                        pass
                    pass   #if           
            
                else:  
                    recipient = user            
                    if recipient is None:
                        recipient = contact
                    
                    recipFullName = self.getFullName(recipient)                    
                    pass         
                                        
                    # OK if contact is None here - method handles it                                                     
                    alarmQueue, deferQueue ,otherQueue = self.separateAlarms(messageQueue)
                    if len(alarmQueue):
                        # send the alarm message(s)
                        subj, alarmMessage = self.buildAlarmMessage(recipFullName, alarmQueue)
                        if self.sendMessage(recipient, subj, alarmMessage):
                            # success - clear the alarms
                            alarmQueue = []
                            pass
                        pass
    
                    if len(deferQueue) and deferredReady is True:
                        # send the deferred notice(s)
                        subj, deferMessage = self.buildDeferredMessage(recipFullName, deferQueue)
                        if self.sendMessage(recipient, subj, deferMessage):
                            # success - clear the deferreds
                            deferQueue = []                                
                            pass    
                        pass
                
                residualQueue = alarmQueue + deferQueue +otherQueue
                if len(residualQueue):
                    residualQueue.sort(lambda a, b: cmp(a.get('timestamp'), b.get('timestamp')))
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
    
    def isTime(self):
        isTime = getLastProcessDate({'update' : False, 'filename' : 'DateOfLastCustomNotification', 'isTime' : True})
        return  isTime   
            
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
    
    def getAliasInfo(self, alsContactIdList,msgQueue):
        aliasList = SFContact.retrieve(self.sfb, alsContactIdList)
        aliasMap = {} 
        
        for alias in aliasList:            
            aliasData = alias.getDataMap()
            aliasContactId = aliasData.get('Id')
            
            for mg in msgQueue:
                    email = mg.get('email')
                    isAlias = mg.get('isAlias')                    
                    
            if aliasContactId in ['0033000000HPwQRAA1','0033000000HPwQR']:                                                
                aliasData['Email']=email    
                  
            aliasMap[aliasContactId] = (alias)
            continue
    
        #return aliasMap
        return alias
    ## END getContactInfo
    
   
   
    def getFullName(self, obj):
        """ Given a user or contact object, return the Full Name """
        objData = obj.getDataMap()
        fullName = "%s %s" %(objData.get('FirstName',''), objData.get('LastName'))
        fullName = fullName.strip()
        return fullName
    ## END getFullname
    
    
    def separateAlarms(self, userMsgQueue):
        """ Iterate through the message queue and separate alarms from
        deferrable notifications """

        alarmQueue = []
        deferQueue = []
        otherQueue= []
        for msg in userMsgQueue:  
            
            isCustom=msg.get('eventcode')
            
            if isCustom in ['CUSTOM']:
                if msg.get('deferred') is True:
                    deferQueue.append(msg)
                else:
                    alarmQueue.append(msg)
                    pass
            else:
                otherQueue.append(msg)
            continue

        return alarmQueue, deferQueue,  otherQueue
    ## END separateAlarms
    
    def separateAliasEmail(self, userMsgQueue):
        """ Iterate through the message queue and separate alarms from
        deferrable notifications """

        distinctEmailList=[]
        for msg in userMsgQueue:                            
            dupId=False
            newEmail=msg.get('email')
            for disEv in distinctEmailList:
                disEmail=disEv.get('email')
                if disEmail==newEmail:
                    dupId=True
                    pass
            if dupId is False:
                emailMap={'email':newEmail}
                distinctEmailList.append(emailMap)
            continue
       
        return distinctEmailList
    ## END separateAlarms
    
    def separateAliasQueue(self, userMsgQueue,emailMap):
        """ Iterate through the message queue and separate alarms from
        deferrable notifications """

        distinctAliasQueue=[]        
        emailAdd=emailMap.get('email')
        for msg in userMsgQueue: 
            newEmail=msg.get('email')            
            if emailAdd==newEmail:
                distinctAliasQueue.append(msg)

        return distinctAliasQueue
    
    
    def buildAlarmMessage(self, userName, alarmQueue):
        from cStringIO import StringIO
        msgBuf = StringIO()
        subject = '%s: Magma Case Watcher Notifications (%d event)' %(userName,len(alarmQueue))
        
        #subject = 'Magma CaseWatcher (%d event)' %(len(alarmQueue))
        intro = 'The following Case Watcher Notification are for your information'
        if len(alarmQueue) > 1:
            subject = '%s: Magma Case Watcher Notification (%d Events)' %(userName,len(alarmQueue))
            intro = 'The following %d notifications are for your information:' %len(alarmQueue)
            pass
        msgBuf.write('%s,\n\n' %userName)
        msgBuf.write('%s\n' %intro)
        msgBuf.write('-' * WW + '\n')

        msgBuf.write(self.buildGenericMessage(alarmQueue, userName))
        
        return subject, msgBuf.getvalue()
    

    def buildDeferredMessage(self, userName, deferQueue):
        from cStringIO import StringIO
        msgBuf = StringIO()
        subject = '%s: Magma Case Watcher Notifications (%d Event)' %(userName,len(deferQueue))
        #subject = '%s: Case Watcher Notifications (%d event)' %(userName,len(deferQueue))
        intro = 'The following Case Watcher Notification are for your information'
        if len(deferQueue) > 1:
            subject = '%s: Magma Case Watcher Notification (%d events)' %(userName,len(deferQueue))
            intro = 'The following %d notifications are for your information:' \
                    %len(deferQueue)
            pass

        msgBuf.write('%s,\n\n' %userName)
        msgBuf.write('%s\n' %textwrap.fill(intro, WW))
        msgBuf.write('-' * WW + '\n')

        msgBuf.write(self.buildGenericMessage(deferQueue, userName))
        
        return subject, msgBuf.getvalue()


    def buildGenericMessage(self, msgQueue, userName):
        from cStringIO import StringIO
        msgBuf = StringIO()
        for msg in msgQueue:           
            msgBuf.write('\n')
            if msg.get('subj') is not None:
                subj = 'RE: %s' %msg.get('subj').encode('ascii','replace')
                msgBuf.write('%s\n' %textwrap.fill(subj, WW))
                #msgBuf.write('\n')
                pass

            # body has already been formatted - do not wrap
            if msg.get('body') is not None:
                msgBuf.write('%s\n' %msg.get('body').encode('ascii','replace'))
                #msgBuf.write('\n')
                pass
            
            """if msg.get('why') is not None:
                msgBuf.write('%s, you are receiving this notification because:\n' %userName)
                msgBuf.write('%s\n' %msg.get('why').encode('ascii','replace'))
                msgBuf.write('\n')
                pass"""
                             
            msgBuf.write('-' * WW+'\n' )            
            continue
        
        return msgBuf.getvalue()
    ## END buildGenericMessage
    
    def sendMessage(self, recip, subj, body):  
        from mail import MailServer, Message
        ms = MailServer()     
        global testMailAddr
        
        fromAdd = 'salesforce-support@molten-magma.com'
        
        toAdd = recip.getDataMap()['Email']
        print "Sending notification mail for %s" %toAdd

        logmsg = 'Sending notification mail for %s' %toAdd
        if self.opts.testflag is True:
            logmsg = 'Notification mail for %s, sent to test recipient %s' %(toAdd, testMailAddr)
            toAdd = testMailAddr
            pass

        self.sfb.setLog(logmsg, 'info')

        try:            
            msg = Message(fromAdd, toAdd, body, subj)            
            ms.sendEmail(msg)            
        except Exception, details:
            return False

        return True
    ## END sendMessage
            

    def sendMessageAlias(self, emailMap, subj, body):  
        from mail import MailServer, Message
        ms = MailServer()     
        global testMailAddr
        
        toAdd=emailMap.get('email')
        fromAdd = 'salesforce-support@molten-magma.com'
        
        #toAdd = recip.getDataMap()['Email']
        print "Sending notification mail for %s" %toAdd

        logmsg = 'Sending notification mail for %s' %toAdd
        if self.opts.testflag is True:
            logmsg = 'Notification mail for %s, sent to test recipient %s' \
                     %(toAdd, testMailAddr)
            toAdd = testMailAddr
            pass

        self.sfb.setLog(logmsg, 'info')

        try:            
            msg = Message(fromAdd, toAdd, body, subj)            
            ms.sendEmail(msg)            
        except Exception, details:
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

    mn = CustomMailNotification(opts)
    mn.do()
    return


if __name__ == '__main__':
    main() 
    
