#!/usr/bin/env python2.3
"""
Nightly script to produce periodic reports on branches & CRs
"""

import sys
import os
import time
import cStringIO
import pprint

import ConfigHelper
from sfReportCR import CRReport
from sfReportAdmin import AdminReport

try: 
    import mailServer
except:
    print 'Please ensure that the "mailServer.py[co]" file is in your'
    print 'PYTHONPATH environment variable list.'

try:
    import sforceBase as sfb	    	    
except:
    print 'Please ensure that the "sforceXMLRPC.py[co]" file is in your'
    print 'PYTHONPATH environment variable list.'

try:
    from cookie_xmlrpclib import DateTime
except:
    print 'Please ensure that the "cookie_xmlrpclib.py[co]" file is in your'
    print 'PYTHONPATH environment variable list.'


contactType = 'contact'
caseType = 'case'

dateTimeFmt = "%Y%m%dT%H:%M:%S %Z"

defLogName = "sf.Notify"
version = 0.10 # Initial version under development


class Notify:
    contactList = None # The list of contacts who have asked for a report
        
    def __init__(self, props, conn=None, logName=defLogName):
        self.props = props
        self.reportTime = time.time()
        self.startTime = self.reportTime
        
        # get a connection to use throughout the report process.
        if conn is None:
            sfConn = sfb.SalesForceBase(logname=logName)
            self.conn = sfConn
        else:
            self.conn = conn

        self.conn.setAction('update')

        self.ct_fld = self.conn.contactFields
        self.ct_lab = self.conn.contactLabels
        self.ct_fl = self.conn.contactFieldList
        self.ct_cfl = self.conn.contactCustomFieldList

        self.retFldList =  ['id', 'firstName', 'lastName', 'email',
                            self.ct_fld['Frequency'],
                            self.ct_fld['Last Report'],
                            self.ct_fld['My CRs with Fixes'],
                            self.ct_fld['My CRs in Development'],
                            self.ct_fld['My CRs Pending Development'],
                            self.ct_fld['My CRs in SCM'],
                            self.ct_fld['My CRs in the Approval Cycle'],
                            self.ct_fld['My Unassigned CRs'],
                            self.ct_fld['My Recently Closed CRs'],
                            self.ct_fld['Users Without Emp. Num.'],
                            self.ct_fld['Contacts Without Emp. Num.'],
                            self.ct_fld["Don't Send Empty Report"]]
    ## END __init__(self)

    def query(self):
        """
        Query for contacts who are requesting reports. 
        """
        # Frequency is set to some period (Daily|Weekly|Monthly)
        f1 = {'field':    self.ct_fld['Frequency'],
              'operator': 'not equals',
              'value':    ''}

        f2 = {'field': self.ct_fld['Contact Status'],
              'operator': 'not equals',
              'value': 'Inactive'}

        qryF = [f1, f2]

        contactList = self.conn.getSFInfo(contactType, qryF, self.retFldList)

        if contactList is not None:
            self.contactList = contactList

        self.conn.log.info("Found %d active contacts found who have requested a report" \
                           %len(self.contactList))
    ## END query()

    def queryByID(self, contactIdList):
        contactList = self.conn.getSFInfoByID(contactType, contactIdList,
                                              self.retFldList)
        if contactList is not None:
            self.contactList = contactList
    ## END queryByID(self, contactIdList)
            
    def parseLastReportDate(self, contact):
        """
        from the contact map provided, takes value of the
        lastReportDate field if it exists, or the default last report
        time if it does not, and returns a time struct and epoch time
        """
        if contact.has_key(self.ct_fld['Last Report']):
            # parse last report time into epoch time
            UTCTimeStr = "%s UTC" %contact[self.ct_fld['Last Report']]
        else:
            # use a default value
            UTCTimeStr = self.props.get('notify', 'defaultLastReportTime')

        # Switch to UTC tome zone to parse time from SF
        os.environ['TZ'] = "UTC"
        time.tzset()

        lastReportUTCStruct = time.strptime(UTCTimeStr, dateTimeFmt)
        
        lastReportEpoch = time.mktime(lastReportUTCStruct)

        # Back to our time
        os.environ['TZ'] = self.props.get('main', 'defaultTZ')
        time.tzset()
        
        lastReportTimeStruct = time.localtime(lastReportEpoch)

        return lastReportTimeStruct, lastReportEpoch
    ## END parseLastReportDate(self, contact)


    def determineEligibility(self):
        """
        Method scans through the list of contacts to receive reports and
        sees if it's time for them to get another report.
        """
        eligibleContactList = []

        FUDGE = 5 * 60
        DAILY = (24 * 60 * 60) - FUDGE
        WEEKLY = (7 * DAILY) - FUDGE
        EVERY30 = (30 * DAILY) - FUDGE
            
        for contact in self.contactList:
            #pprint.pprint(contact)

            # refetch limited contact info by ID here to get latest
            # update time in case two notify processes are 'racing'
            retFieldList = ['id', self.ct_fld['Frequency'],
                            self.ct_fld['Last Report']]

            contactInfo = self.conn.getSFInfoByID(contactType,
                                                  [contact['id']],
                                                  retFieldList)[0]
            
            discard, lastReportEpoch = self.parseLastReportDate(contactInfo)

            #self.conn.log.info("lastReportEpoch = %s" %lastReportEpoch)
                
            # subtract last report epoch from self.reportTime
            secsSinceLastReport = self.reportTime - lastReportEpoch

            #self.conn.log.info("secsSinceLastReport = %s" %secsSinceLastReport)

            # contactInfo had *better* have Frequency field as we
            # queried based on it being set
            
            if contactInfo[self.ct_fld['Frequency']] == 'Daily' and \
                   secsSinceLastReport > DAILY:
                # Eligible for daily report
                eligibleContactList.append(contact)
            elif contactInfo[self.ct_fld['Frequency']] == 'Weekly' and \
                     secsSinceLastReport > WEEKLY:
                # Eligible for weekly report
                eligibleContactList.append(contact)
            elif contactInfo[self.ct_fld['Frequency']] == 'Every 30 Days' and \
                     secsSinceLastReport > EVERY30:
                # Eligible for monthly report
                eligibleContactList.append(contact)
            else:
                # Not eligible for any reports
                pass

        self.contactList = eligibleContactList

        self.conn.log.info("%d contact(s) eligible for a report this run" \
                           %len(self.contactList))
    ## END determineEligibility(self)

    
    def generateReports(self):
        """
        
        """
        self.determineEligibility()


        for contact in self.contactList:
            self.conn.log.info("Generating report(s) for %s" %contact.get('email'))
            
            try:
                userId = self.conn.getUserIdFromEmail(contact.get('email'))
            except Exception, e:
                self.conn.dlog.error("Cannot get userId from email address %s:\n\t%s" %(contact.get('email'), e))
                continue

            reportsMap = {'cr': False,
                          'branch': False,
                          'admin': False}
            

            # Figure out which reports to send to this person
            crReportSections = ['My CRs with Fixes',
                                'My CRs in Development',
                                'My CRs Pending Development',
                                'My CRs in SCM',
                                'My CRs in the Approval Cycle',
                                'My Unassigned CRs',
                                'My Recently Closed CRs',]
            for section in crReportSections:
                if contact.get(self.ct_fld[section], False) is True:
                    reportsMap['cr'] = True
                

            adminReportSections = ['Users Without Emp. Num.',
                                   'Contacts Without Emp. Num.']
            for section in adminReportSections:
                if contact.get(self.ct_fld[section], False) is True:
                    reportsMap['admin'] = True

            # Now, generate each report called for this user
            # CR Report
            if reportsMap['cr'] is True:
                # call to get the CR report
                crReport = CRReport(self, userId, contact)
                crReport.generateReport()
                
                # Right now, only send if has content.
                # Don't Send Empty Reports
                if crReport.hasContent() or \
                       contact.get(self.ct_fld["Don't Send Empty Report"],
                                   False) is False:
                    self.sendReport(contact, crReport)

            # Admin Report
            if reportsMap['admin'] is True:
                adminReport = AdminReport(self, userId, contact)
                adminReport.generateReport()
                # Right now, only send if has content.
                # Don't Send Empty Reports
                if adminReport.hasContent() or \
                       contact.get(self.ct_fld["Don't Send Empty Report"],
                                   False) is False:
                    self.sendReport(contact, adminReport)

            # Branch report
            if reportsMap['branch'] is True:
                pass

        
            # Mark the contact record with last report date
            if True in reportsMap.values():
                self.updateContactLastRptDate(contact)
    ## END requestReports(self)

                
    def updateContactLastRptDate(self, contact):
        """
        Update contact's Last Report field with notifier's reportTime
        (as a UTC time struct). 
        """
        contactUpdMap = {}

        contactUpdMap['id'] = contact['id']
        contactUpdMap[self.ct_fld['Last Report']] = DateTime(time.gmtime(self.reportTime))

        updateResponse = self.conn.setSFInfo(contactUpdMap, contactType)
    ## END updateContactLastRptDate(self, contact)
        

    def sendReport(self, contact, report):
        """
        Email the generated report to the contact
        """
        smtpserver = self.props.get('main', 'smtpServer')
        notifyFrom = self.props.get('notify', 'notifyFrom')
        notifyToList = [contact['email']]

        if self.props.get('notify', 'notifyBccList'):
            notifyBccList = ConfigHelper.parseConfigList(self.props.get('notify', 'notifyBccList'))
        else:
            notifyBccList = None

        if self.props.get('notify', 'debug') == "True":
            notifyToList = notifyBccList
            notifyBccList = None
        
        self.conn.log.info("About to email report for %s" \
                           %contact.get('email'))

        mailserver = self.conn.mailServer

        mailServer.MailServer(smtpServer=smtpserver,
                              logger=self.conn.log)

        emailTxt = mailserver.setEmailTxt(fromAddress=notifyFrom,
                                          toArray=notifyToList,
                                          bccArray=notifyBccList,
                                          subject=report.getSubject(),
                                          msgStr=report.getBody())

        mailserver.sendEmail(fromAddr=notifyFrom,
                             toAddrs=notifyToList,
                             emailTxt=emailTxt,
                             subject=report.getSubject(),
                             bccAddrs=notifyBccList)
    ## END sendReport(self, contact, report)


    def do(self, contactIdList=None):
        """
        Main flow for notifier
        """
        os.environ['TZ'] = self.props.get('main', 'defaultTZ')
        time.tzset()

        global startTime
        self.conn.getConnectInfo(version, startTime=self.startTime)

        if contactIdList is None:
            self.query()
        else:
            self.queryByID(contactIdList)

        self.generateReports()

        self.conn.note.info('Finished. Total Runtime is %s secs.'
                            %(time.time() - self.startTime))
    ## END do(self)
## END class Notify



def main():
    if len(sys.argv) > 1:
        contactIdList = sys.argv[1:]
    else:
        contactIdList = None
    
    # Fetch the config
    props = ConfigHelper.fetchConfig('../conf/sfutil.cfg')

    notifier = Notify(props)

    notifier.do(contactIdList)
## END main()
    

if __name__ == "__main__":
    main()
