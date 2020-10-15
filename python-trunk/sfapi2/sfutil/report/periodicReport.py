#!/usr/bin/env python2.3
"""
Notification engine for periodic reports on branches and CRs.
"""

import sys
import os
import time
import cStringIO
import pprint
import optparse

import mail

from sfConstant import *
from sfMagma import SFMagmaTool

from sfReportCR import CRReport

from sfUtil import getTestMailAddr

dateTimeFmt = "%Y-%m-%dT%H:%M:%S.000Z"

debugEmailAddr = getTestMailAddr()
notifyBccList = None
fromAddr = 'salesforce-support@molten-magma.com'

myTZ = 'US/Pacific'

version=2.0

class PeriodicReport(SFMagmaTool):
    # the list of contacts who have asked for a report.
    contactList = []
    
    def __init__(self, debug=0, logname='sf.preport'):
        self.reportTime = time.time() # UTC time struct)
        self.startTime = self.reportTime

        SFMagmaTool.__init__(self, debug=debug, logname=logname)

        self.debug=False
        return
    ## END __init__

    def queryContactList(self):
        """
        Get the list of contacts who are requesting reports.
        """

        q1 = ['PR_Frequency__c','!=','']
        q2 = ['ContactStatus__c','!=','Inactive']
        q3=['RecordTypeId','=','0123000000000sjAAA']
        q4=['RecordTypeId','=','0123000000001trAAA']
        q5=['RecordTypeId','=','012300000000RwfAAE']
               
        q3a = ['PR_CR_Detail_Level__c','!=','']
        q3b = ['PR_Branch_Detail_Level__c','!=','']
        
        where = [q1, 'and', q2, 'and', '(', q3a, 'or', q3b, ')','and', '(', q3, 'or', q4, ')']
                
        contactQryRes = self.query(CONTACT_OBJ, where=where, sc='all')

        if contactQryRes not in BAD_INFO_LIST:
            self.contactList = contactQryRes

        msg = 'Found %s active Magma contacts who have requested a report.' \
              %len(self.contactList)
        self.setLog(msg, 'info')
        
        #print "CONATCT Object length is: %s"%len(self.contactList)

        return
    ## END queryContactList
        

    def queryContactsById(self, contactIdList):
        contactQryRes = self.retrieve(contactIdList, CONTACT_OBJ)
        
        if contactQryRes not in BAD_INFO_LIST:
            self.contactList = contactQryRes
            pass

        return
    ## END queryContactByID
    
    def parseLastReportDate(self, contact):
        """
        from the contact map provided, takes value of the
        lastReportDate field if it exists, or the default last report
        time if it does not, and returns a time struct and epoch time
        """
        global myTZ

        if os.environ.get('TZ','') != myTZ:
            os.environ['TZ'] = myTZ
            time.tzset()
        
        if contact.has_key('PR_Last_Report_Date_Time__c'):
            # parse last report time into epoch time
            UTCTimeStr = contact['PR_Last_Report_Date_Time__c']
            os.environ['TZ'] = "UTC"
            time.tzset()
        else:
            # use a default value
            #UTCTimeStr = self.props.get('notify', 'defaultLastReportTime')
            UTCTimeStr = "2004-11-01T00:30:00.000Z"


        lastReportUTCStruct = time.strptime(UTCTimeStr, dateTimeFmt)
        
        lastReportEpoch = time.mktime(lastReportUTCStruct)

        # Back to our time
        if os.environ['TZ'] != myTZ:
            os.environ['TZ'] = myTZ
            time.tzset()
        
        lastReportTimeStruct = time.localtime(lastReportEpoch)

        return lastReportTimeStruct, lastReportEpoch, UTCTimeStr
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
                                 
            discard, lastReportEpoch, discard = self.parseLastReportDate(contact)

            secsSinceLastReport = self.reportTime - lastReportEpoch

            if contact.get('Email', None) is None:
                self.setLog("Contact has no email address - skipping: %s" \
                            %contact, 'warn')
                continue

            if self.outofband is True:
                # we don't care about the last report date
                eligibleContactList.append(contact)
            elif contact.get('PR_Frequency__c','') == 'Daily' and \
                   secsSinceLastReport > DAILY:
                # Eligible for daily report
                eligibleContactList.append(contact)
            elif contact.get('PR_Frequency__c','') == 'Weekly' and \
                     secsSinceLastReport > WEEKLY:
                # Eligible for weekly report
                eligibleContactList.append(contact)
            elif contact.get('PR_Frequency__c','') == 'Every 30 Days' and \
                     secsSinceLastReport > EVERY30:
                # Eligible for monthly report
                eligibleContactList.append(contact)
            else:
                # Not eligible for any reports
                pass

        self.contactList = eligibleContactList
        #print "Eligible Contact List: %s"%contactList
        self.setLog("%d contact(s) eligible for a report this run" \
                    %len(self.contactList), 'info')

        return
    ## END determineEligibility(self)

    def determineSections(self, detailLvl):
        """
        Move to the CR report class
        """
        lowSections = ['TestFixes',
                       'Unassigned',
                       'RecentClose',]

        medSections = []

        verboseSections = ['Dev',
                           'PendDev',
                           'SCM',
                           'EngMgr',
                           'PE',
                           'Team',
                           'Untouched',]

        if detailLvl == 'Low Detail':
            sectionList = lowSections
        elif detailLvl == 'Medium Detail':
            sectionList = lowSections + medSections
        elif detailLvl == 'Verbose':
            sectionList = lowSections + medSections + verboseSections
        else:
            sectionList = []
            msg = 'Invalid detail level "%s"' %detailLvl
            self.setLog(msg, 'error')

        return sectionList
    ## END determineSections


    def generateReports(self):
        """
        Pare down the list of contacts to those eligible, then
        build a report for each contact found.
        """
        self.determineEligibility()

        for contact in self.contactList:
            msg = "Generating report for %s (%s)" %(contact.get('Email'),
                                                    contact.get('Id'))
            self.setLog(msg, 'info')
            
            userId = contact.get('Contact_User_Id__c', None)

            if userId is None:
                msg = 'No userID for contact %s' %contact.get('Email')
                self.setLog(msg, 'error')
                continue

            # figure out which CRreport sections to send to this person
            detailLvl = contact.get('PR_CR_Detail_Level__c','')
            crSectionList = self.determineSections(detailLvl)
            if len(crSectionList) > 0:                
                crReport = CRReport(self, userId, contact, crSectionList)
                crReport.generateReport()

                if crReport.hasContent() or \
                       contact.get('PR_No_Empty__c', 'false') == 'false':
                    self.sendReport(contact, crReport)
                
            # Mark the contact record with last report date if we generated any
            # report
            if len(crSectionList) > 0 and self.outofband is False:
                self.updateContactLastRptDate(contact)
    ## END generateReports
            
            
    def updateContactLastRptDate(self, contact):
        """
        Update contact's Last Report field with notifier's reportTime
        (as a UTC time struct). 
        """
        # check that reportTime isn't getting shifted upon insert...
        data = {'Id': contact['Id'],
                'PR_Last_Report_Date_Time__c': self.reportTime}
                

        res = self.update(CONTACT_OBJ, data)
        if res in BAD_INFO_LIST:
            msg = 'Update of last report time for contact %s (%s) FAILED' \
                  %(contact['Email'], contact['Id'])
            self.setLog(msg, 'error')
            
    ## END updateContactLastRptDate(self, contact)

    def sendReport(self, contact, report):
        """
        Email the generated report to the contact
        """
        global fromAddr
        toAddr = contact['Email']

        if self.debug is True:
            toAddr = debugEmailAddr
            bccAddr = None
        else:
            bccAddr = notifyBccList
        
        self.setLog("About to email report for %s" %contact.get('Email'),
                    'info')

        mailserver = mail.MailServer(logger=self.log)

        message = mail.Message(fromAddr, toAddr, report.getBody(),
                               subject=report.getSubject(),
                               bccAdds=bccAddr)

        mailserver.sendEmail(message)
        return
    ## END sendReport(self, contact, report)

    def do(self, contactIdList=None, opts=None):
        """
        Main flow for notifier
        """
        global myTZ

        if opts is not None:
            self.debug = opts.debug
            self.outofband = opts.oob
        else:
            self.debug=False
            self.outofband=False
        
        os.environ['TZ'] = myTZ
        time.tzset()

        global startTime
        self.getConnectInfo(version, startTime=self.startTime)

        if contactIdList is None:
            self.queryContactList()
        else:
            self.queryContactsById(contactIdList)

        self.generateReports()

        self.setLog('Finished. Total Runtime is %s secs.' \
                    %(time.time() - self.startTime), 'info')
        return
    ## END do(self)

def main():
    op = optparse.OptionParser()

    op.add_option('-d','--debug', action='store_true', dest='debug',
                  default=False, help='run in debug mode')
    op.add_option('-o','--outofband', action='store_true', dest='oob',
                  default=False, help='Send report regardless of last sent.'
                  'Also, don\'t update last sent date/time')
                  

    opts, args = op.parse_args()

    if len(args) > 0:
        contactIdList = args
    else:
        contactIdList = None
    
    notifier = PeriodicReport()

    notifier.do(contactIdList, opts)
## END main()


        
if __name__ == "__main__":
    main()
