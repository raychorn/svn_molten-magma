"""
Library to support email messaging
"""
import cStringIO
import sets
import types

from smtplib import *
from sfConstant import *

from sop import SFConfig

class MailServer:
    """
    This class contains the methods necessary for sending an email message and
    checking the message's delivery status to various recipients.
    """
    notifyList = []
    debug = 1
    def __init__(self, smtpServer=None, logger=None):
        sfc = SFConfig()
        sfc.load()
        
        if smtpServer is None:
            smtpServer = sfc.get('email', 'smtp_server')
        self.smtpServer = smtpServer
        self.mailServer = SMTP(smtpServer)
        self.log = logger
    ## END def __init__(self, smtpServer, logger)

    def sendEmail(self, message, trial=False):
        """
        actually send the email message.

        message - Message object
        trial - if set to True, doesn't actually send email. Default: False
        """
        msgTxt = message.message

        if trial is True:
            if self.log is not None:
                self.log.debug('TRIAL email FROM:%s \tTO:%s',
                               message.fromAdd, message.toAddList)
                self.log.debug('TRIAL email BODY:%s', msgTxt)
            
            return {'trial':[message.toAddList, msgTxt]}
        
        else:
            toSet = sets.Set(message.toAddList)
            ccSet = sets.Set(message.ccAddList)
            bccSet = sets.Set(message.bccAddList)
            sendToList = toSet | ccSet | bccSet # union 
            
            try:                
                mstat = self.mailServer.sendmail(message.fromAdd,
                                                 sendToList,
                                                 msgTxt.encode('ascii',
                                                               'replace'))
                toAlias = getAliasString(sendToList)

                if self.log is not None:                    
                    self.log.info("Sent mail with Subject '%s' to %s",
                                  message.subject[:50],toAlias)
                
                return mstat
            
            except SMTPRecipientsRefused, e:
                if self.log is not None:
                    self.log.exception('Error mail not sent, problem in Recepients %s\n', sendToList)
                    self.log.exception(' %s ERROR:%s', Exception, e)
                
                return e

            except Exception, e:
                if self.log is not None:
                    self.log.exception('Error in delivering e-mail to one of %s\n',
                                       sendToList)
                    self.log.exception(' %s ERROR:%s', Exception, e)
                
                return e
    ## END sendEmail

    def getSendResults(self, message, emailResults):
        """
        generic mail sending results printing
        accepts Message object and results structure
        """
        subject = message.subject
        
        toAddrDict = {}
        for toAddr in message.toAddList:
            if emailResults is None: 
                toAddrDict[toAddr] = False
                
            elif hasattr(emailResults, 'recipients'):
                bounces = emailResults.recipients
                
                if bounces.has_key(toAddr):
                    toAddrDict[toAddr] = False
                    
            else:                            
                toAddrDict[toAddr] = True
                
        if emailResults == {}:
            toAlias = getAliasString(message.toAddList)
            
            msg = 'Sent TO %s AS %s' % (toAlias, subject[:80])
                
        else:
            for toAddr in toAddrDict.keys():
                if toAddrDict.get(toAddr):
                    msg = 'Sent TO %s AS %s' %(toAddr, subject[:80])
                        
                else:
                    msg = "Email to %s failed %s" %(toAddr, emailResults)
                    if self.log is not None:
                        self.log.error(msg)
                    
        return msg
    ## END getSendResults
    
## END class MailServer


class Message:
    """
    Represents an email message for sending.

    Creates full text implementation on initialization as well as storing
    all fields as member variables.

    fromAdd - single address of message sender
    toAdds - single address or list of addresses of primary recipients
    body - Text of message body as string
    subject - optional subject string
    ccAdds - optional single address or list of addresses of copy recipients
    bccAdds - optional single address or list of addresses of
              blindcopy recipients
    """
    def __init__(self, fromAdd, toAdds, body,
                 subject="", ccAdds=None, bccAdds=None):
        
        self.fromAdd = fromAdd

        self.toAddList = self.stringOrIterable(toAdds)
        self.ccAddList = self.stringOrIterable(ccAdds)
        self.bccAddList = self.stringOrIterable(bccAdds)

        self.subject = subject
        self.body = body

        self.buildMsg()
        return
    ## END __init__
    
    def __str__(self):
        return "%s" %self.message
    ## END __str__

    def __repr__(self):
        return "Message('%s', %s, '''%s''', %s, %s, %s)" %(self.fromAdd,
                                                           self.toAddList,
                                                           self.body,
                                                           self.subject,
                                                           self.ccAddList,
                                                           self.bccAddList)

    def stringOrIterable(self, value):
        """
        if value is not a list or tuple, packs value as one item list
        before returning it
        """
        if value is None:
            return value
        elif type(value) == types.TupleType or type(value) == types.ListType:
            return value
        else:
            return [value]
    ## END stringOrIterable
                                                           
    def buildMsg(self):
        """
        Builds and stores message text based on the member components.
        Call this if any of the data (recipients, subject, body) has changed
        after the object has been instantiated.
        """
        msgBuf = cStringIO.StringIO()
        
        # build the header
        msgBuf.write('From: %s\r\n' % self.fromAdd)

        msgBuf.write('To: %s\r\n' %','.join(self.toAddList))

        if self.ccAddList is not None:
             msgBuf.write('CC: %s\r\n' %','.join(self.ccAddList))
        
        if self.bccAddList is not None:
            msgBuf.write('BCC: %s\r\n' %','.join(self.bccAddList))

        msgBuf.write('Subject: %s\r\n' %self.subject.encode('ascii','replace'))

        msgBuf.write('\r\n') # Separator break btwn hdr and msg

        # Add the body
            
        msgBuf.write(self.body.encode('ascii','replace'))

        self.message =  msgBuf.getvalue()

        return self.message
    ## END buildMsg
## END class Message


def getAliasString(emailList):
    """
    Function to extract and return a list (String, comma separated)
    of Mamga aliases from provided email list
    """
    toAlias = ''
    for toAdd in emailList: 
        toA = toAdd.split('@molten-magma.com')[0]

        if toAlias == '':
            toAlias = '%s' %(toA)
        else:
            toAlias = '%s,%s' %(toAlias,toA)

    return toAlias
## END def getAliasString(emailList)


