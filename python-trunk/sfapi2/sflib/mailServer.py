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
    def __init__(self, smtpServer='rye.moltenmagma.com', logger=None):
        self.smtpServer = smtpServer
        try:
            self.mailServer = smtplib.SMTP(smtpServer)
        except:
            pass
        self.log = logger
    ## END def __init__(self, smtpServer, logger)


    def genEmailTxt(self, fromAddress, toArray, subject, buf,
                    ccArray=None, bccArray=None):
        """
        Generates a text version of an e-mail using 'fromAddress',
        'toArray' (an array of e-mail addresses), 'subject', and
        'buf' (a buffer holding the e-mail text).
        """
        buf.seek(0)
        
        msgTxt = self.setEmailTxt(fromAddress, toArray, subject,
                                  buf.read(), ccArray, bccArray)
        
        return msgTxt
    ## END def genEmailTxt(self, fromAddress, toArray, subject, buf)


    def setEmailTxt(self, fromAddress, toArray, subject, msgStr,
                    ccArray=None, bccArray=None):
        """
        Generates a text version of an e-mail using 'fromAddress',
        'toArray' (an array of e-mail addresses), 'subject', and
        """
        hdrBuf = StringIO.StringIO()
        hdrBuf.write('From: %s\r\n' % fromAddress)

        hdrBuf.write('To: %s\r\n' %','.join(toArray))

        if ccArray is not None:
             hdrBuf.write('CC: %s\r\n' %','.join(ccArray))
        
        if bccArray is not None:
            hdrBuf.write('BCC: %s\r\n' %','.join(bccArray))

        hdrBuf.write('Subject: %s\r\n' %subject)

        hdrBuf.write('\r\n') # Separator break btwn hdr and msg
            
        msgTxt = '%s%s' % (hdrBuf.getvalue(),
                           msgStr.encode('ascii','replace'))

        if self.log is not None:
            self.log.log(5,'\n\n%s\n\n', msgTxt)
        
        return msgTxt
    ## END setEmailTxt(self, fromAddress, toArray, subject, msgStr)



    def sendEmail(self, fromAddr, toAddrs, emailTxt,
                  subject='Default subject', action='update',
                  ccAddrs=None, bccAddrs=None):
        """
        actually send the email message
        """
        if action != 'update':
            if self.log is not None:
                self.log.debug('TRIAL email FROM:%s \tTO:%s',
                               fromAddr, toAddrs)
                self.log.debug('TRIAL email BODY:%s', emailTxt)
            
            return {'trial':[toAddrs,emailTxt]}
        
        else:
            if ccAddrs is not None:
                toAddrs.extend(ccAddrs)

            if bccAddrs is not None:
                toAddrs.extend(bccAddrs)

            try:
                mstat = self.mailServer.sendmail(fromAddr, toAddrs,
                                                 emailTxt.encode('ascii',
                                                                 'replace'))
                toAlias = ''
                toAlias = getAliasString(toAddrs)

                if self.log is not None:
                    self.log.info("Sent mail with Subject '%s' to %s",
                                  subject[:50],toAlias)
                
                return mstat
            
            except SMTPRecipientsRefused, e:
                if self.log is not None:
                    
                    self.log.exception('Error mail not sent, problem in Recepients %s\n', toAddrs)
                    self.log.exception(' %s ERROR:%s', Exception, e)
                
                return e

            except Exception, e:
                if self.log is not None:
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
                    if self.log is not None:
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

