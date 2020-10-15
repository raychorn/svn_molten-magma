from mail import MailServer, Message
import sfUtil
from sop import SFConfig
import os, sys

smtpServer1 = '127.0.0.1'
smtpServer2 = 'mail.moltenmagma.com'

smtpServers = []

if (sys.platform == 'win32'):
    smtpServers.append(smtpServer1)

smtpServers.append(smtpServer2)

mailserver = None

testMailAddr = 'rhorn@molten-magma.com'

def buildGenericMessage(msgQueue, userName):
    from cStringIO import StringIO
    msgBuf = StringIO()
    for msg in msgQueue:           
        msgBuf.write('\n')
        if msg.get('subj') is not None:
            subj = 'RE: %s' %msg.get('subj').encode('ascii','replace')
            msgBuf.write('%s\n' %textwrap.fill(subj, WW))
            pass

        # body has already been formatted - do not wrap
        if msg.get('body') is not None:
            msgBuf.write('%s\n' %msg.get('body').encode('ascii','replace'))
            pass
        
        msgBuf.write('-' * WW+'\n' )            
    
    return msgBuf.getvalue()

def buildAlarmMessage(userName, alarmQueue):
    from cStringIO import StringIO
    msgBuf = StringIO()
    subject = '%s: Magma Case Watcher Notifications (%d event)' %(userName,len(alarmQueue))
    
    intro = 'The following Case Watcher Notification are for your information'
    if len(alarmQueue) > 1:
        subject = '%s: Magma Case Watcher Notification (%d Events)' %(userName,len(alarmQueue))
        intro = 'The following %d notifications are for your information:' %len(alarmQueue)
        pass
    msgBuf.write('%s,\n\n' %userName)
    msgBuf.write('%s\n' %intro)
    msgBuf.write('-' * WW + '\n')

    msgBuf.write(buildGenericMessage(alarmQueue, userName))
    
    return subject, msgBuf.getvalue()

def sendMessage(smtp,recip, subj, body):  
    from mail import MailServer, Message
    ms = MailServer(smtp)     
    
    fromAdd = 'salesforce-support@molten-magma.com'
    
    toAdd = recip
    print "Sending notification mail for %s" %toAdd

    logmsg = 'Sending notification mail for %s' %toAdd

    try:            
        msg = Message(fromAdd, toAdd, body, subj)            
        ms.sendEmail(msg)            
    except Exception, details:
        return False

    return True
## END sendMessage
            
def main():
    #sfc = SFConfig()
    #sfc.load()
    
    #_smtp = sfc.get('email', 'smtp_server')
    #smtpServers[-1] = _smtp
        
    for smtp in smtpServers:
        print 'smtp=[%s]' % smtp
        sendMessage(smtp,testMailAddr,'+++test+++ (%s) from (%s)' % (smtp,sys.platform),'testing 1.2.3. (%s) from (%s)' % (smtp,sys.platform))
    pass

if (__name__ == '__main__'):
    main()

