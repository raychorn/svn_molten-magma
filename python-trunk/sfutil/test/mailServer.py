import cStringIO as StringIO
import smtplib
from smtplib import *

default_smtp_server = 'rye.moltenmagma.com'

class MailServer:
    """
    This class contains the methods necessary for:

    """
    notifyList = []
    debug = 1
    def __init__(self, smtpServer=default_smtp_server, logger=None):
        self.smtpServer = smtpServer
        self.mailServer = smtplib.SMTP(smtpServer)
        self.log = logger
    ## END def __init__(self, smtpServer, logger)


    def genEmailTxt(self, fromAddress, toArray, subject, buf):
        """
        Generates a text version of an e-mail using 'fromAddress',
        'toArray' (an array of e-mail addresses), 'subject', and
        'buf' (a buffer holding the e-mail text).
        """
        hdrBuf = StringIO.StringIO()
        hdrBuf.write('From: %s\r\nTo: ' % fromAddress)
        
        for toIndex in range(len(toArray)):
            toAddr = toArray[toIndex]
            hdrBuf.write('%s,' % toAddr)
            
        hdrBuf.write('\r\nSubject: %s\r\n\r\n' % subject)
        hdrBuf.reset()
            
        msgTxt = '%s%s' % (hdrBuf.getvalue(), buf.getvalue())
    
        self.log.log(5,'\n\n%s\n\n', msgTxt)
        
        return msgTxt
    ## END def genEmailTxt(self, fromAddress, toArray, subject, buf)


    def setEmailTxt(self, fromAddress, toArray, subject, msgStr):
        """
        Generates a text version of an e-mail using 'fromAddress',
        'toArray' (an array of e-mail addresses), 'subject', and
        """
        ms = 'From: %s\r\nTo: ' % fromAddress
        
        for toAddr in toArray:
            ms ='%s%s,' %(ms, toAddr)
            
        ms ='%s\r\nSubject: %s\r\n\r\n' %(ms, subject)
        msgTxt = '%s%s' % (ms, msgStr)
        self.log.log(5,'\n\n%s\n\n', msgTxt)
        
        return msgTxt
    ## END def etEmailTxt(self, fromAddress, toArray, subject, msgStr)



    def sendEmail(self, fromAddr, toAddrs, emailTxt,
                  subject='Default subject', action='update'):
        """
        actually send the email message
        """
        if action != 'update':
            self.log.debug('TRIAL email FROM:%s \tTO:%s', fromAddr, toAddrs)
            self.log.debug('TRIAL email BODY:%s', emailTxt)
            
            return {'trial':[toAddrs,emailTxt]}
        
        else:
            try:
                mstat = self.mailServer.sendmail(fromAddr, toAddrs, emailTxt)
                toAlias = ''
                toAlias = getAliasString(toAddrs)
                self.log.info("Sent mail with Subject '%s' to %s",
                              subject[:50],toAlias)
                
                return mstat
            
            except SMTPRecipientsRefused, e:
                self.log.exception('Error mail not sent, problem in Recepients %s\n', toAddrs)
                self.log.exception(' %s ERROR:%s', Exception, e)
                
                return e

            except Exception, e:
                self.log.exception('Error in delivering e-mail to one of %s\n',
                                   toAddrs)
                self.log.exception(' %s ERROR:%s', Exception, e)
                
                return e
    ## END sendEmail(self, fromAddr, toAddrs, emailTxt, subject, action)

    def getSendResults(self, subject, toAddrs, emailResults, cmdLine='walkSF'):
        """
        generic mail sending results printing
        """
        toAddrDict = {}
        for toAddr in toAddrs:
            if emailResults is None: 
                toAddrDict[toAddr] = False
                
            elif hasattr(emailResults ,'recipients'):
                bounces = emailResults.recipients
                
                if bounces.has_key(toAddr):
                    toAddrDict[toAddr] = False
                    
            else:                            
                toAddrDict[toAddr] = True
                
        if emailResults == {}:
            toAlias = getAliasString(toAddrs)
            
            if cmdLine != 'walkSF':
                msg = 'Successfully sent TO %s\n\t AS %s' % (toAlias, subject)
            else:
                msg = 'Sent TO %s AS %s' % (toAlias, subject[:80])
                
        else:
            for toAddr in toAddrDict.keys():
                if toAddrDict.get(toAddr):
                    if cmdLine != 'walkSF':
                        msg = 'Successfully sent TO %s\n\t AS %s' \
                              %(toAddr, subject)
                    else:
                        msg = 'Sent TO %s AS %s' %(toAddr, subject[:80])
                        
                else:
                    msg = "e-mail to %s failed %s" %(toAddr, emailResults)
                    self.log.error(msg)
                    
        return msg
    ## END  def getSendResults(self, subject, toAddrs, emailResults, cmdLine)
    
## END class MailServer



def getAliasString(emailList):
    """
    Function to extract and return a list (String, comma separated)
    of Mamga aliases from provided email list
    """
    # Gosh, this wants to be a function of module MailServer
    toAlias = ''
    for toAdd in emailList: 
        toA = toAdd.split('@molten-magma.com')[0]

        if toAlias == '':
            toAlias = '%s' %(toA)
        else:
            toAlias = '%s,%s' %(toAlias,toA)

    return toAlias
## END def getAliasString(emailList)

