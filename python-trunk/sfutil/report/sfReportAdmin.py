#!/usr/bin/env python2.3
"""
A class for instantiation by sfNotify to generate a type of report

Not intended to stand alone.
"""
version = 1.0 # Initial version 

from sfReportBase import ReportBase
from reportSection import ReportSection

import re
import time
import cStringIO

userType = 'user'
contactType = 'contact'

class AdminReport(ReportBase):

    def __init__(self, notifier, userId, contact):
        ReportBase.__init__(self, notifier, userId, contact)
    ## END __init__(self, props, conn)

    def generateReport(self):
        """
        Central method to build user/contact report
        Calls other methods to build chunks of the report.
        """
        date = time.strftime("%A %B %d, %Y",
                             time.localtime(self.notifier.reportTime))
        subject = "SF Admin Report for %s %s on %s" \
                  %(self.contact['firstName'], self.contact['lastName'], date)
        self.subject = subject
        

        # Assemble the sections, adding them to the body

        # Users without Employee Numbers section
        if self.contact.get(self.ct_fld['Users Without Emp. Num.'], False):
            # My CRs With Fixes Available
            userNoEmpNumSec = UsersWithoutEmpNumSection(self.notifier,
                                                        self.userId,
                                                        self.contact)
            userNoEmpNumTxt = userNoEmpNumSec.getSection()
            self.body.write(userNoEmpNumTxt)

            # note if we have content for the section or not.
            self.sectionContentMap['userNoEmpNumSec'] = userNoEmpNumSec.hasContent()


        # Contacts without Employee Numbers section
        if self.contact.get(self.ct_fld['Contacts Without Emp. Num.'], False):
            # My CRs With Fixes Available
            contactNoEmpNumSec = ContactsWithoutEmpNumSection(self.notifier,
                                                              self.userId,
                                                              self.contact)
            contactNoEmpNumTxt = contactNoEmpNumSec.getSection()
            self.body.write(contactNoEmpNumTxt)

            # note if we have content for the section or not.
            self.sectionContentMap['contactNoEmpNumSec'] = contactNoEmpNumSec.hasContent()
                

        self.body.write(self.generateReportFooter())
    ## END generateReport(self)

## END class CRReport


class SfAdminReportBase(ReportSection):
    """
    Shell to hold common bits of the user reports like fetching all users
    and fetching all magma contacts plus storing this info
    """
    userList = None # persistent among instances
    contactList = None
    
    def __init__(self, notifier, userId, contact):
        ReportSection.__init__(self, notifier)
        self.userId = userId
        self.contact = contact

        self.user_fld = self.conn.userFields
        self.contact_fld = self.conn.contactFields

        # regexp for a 5 digit employee number
        self.empNoRE = re.compile(r'^\d{5}$')
    ## END __init__

    def fetchAllUsers(self):
        """
        Fetch All users
        """
        if self.userList is None:
        
            f1 = {'field': 'id',
                  'operator': 'not equals',
                  'value': ''}

            filter = [f1]

            retFldList = ['id', 'firstName', 'lastName', 'active',
                          'employeeNumber', self.user_fld['Ex-Employee']]
            userResult = self.conn.getSFInfo(userType, filter, retFldList)
            if userResult is not None:
                userList = userResult
                self.userList = userList
            else:
                self.userList = []

        return self.userList
    ## END fetchAllUsers

    def fetchAllContacts(self):
        """
        Wrap base class getAllMagmaContacts
        """
        if self.contactList is None:
            self.contactList = self.conn.getAllMagmaContacts()
            
        return self.contactList
## END class SfAdminReportBase


class UsersWithoutEmpNumSection(SfAdminReportBase):
    """
    Report on all users who are not marked "Ex-Employee" that do not have
    an Employee Number set.
    """

    def __init__(self, notifier, userId, contact):
        SfAdminReportBase.__init__(self, notifier, userId, contact)

        self.header = "Magma Users Without Employee Numbers"
    ## END __init__


    def buildSecBody(self):
        body = cStringIO.StringIO()

        userList = self.fetchAllUsers()
        problemUserList = []

        for user in userList:
            if user.get(self.user_fld['Ex-Employee'], False) is True:
                continue # Don't worry about Ex Employees

            empNo = user.get('employeeNumber', None)
            if empNo is None:
                problem = "(No Employee Number)"
            elif not self.empNoRE.search(empNo):
                problem = "(Malformed Employee Number)"
            else:
                continue # Should be OK.

            problemUserList.append(user['id'])
            userUrl = "https://na1.salesforce.com/%s" %user['id']
            userLine =  "%s %s %s" \
                      %(user.get('firstName', 'NO FIRST NAME'),
                        user.get('lastName', 'NO LAST NAME'),
                        problem)
            body.write("%s\n\t%s\n\n" %(userLine, userUrl))

        if len(problemUserList):
            # set the section footer so that it gets written
            self.footer = "(Note: Please get emp. numbers from HR for these users & update salesforce)"
            self.hasContentFlag = True
        else:
            body.write("All users have an employee number set.\n")

        return body.getvalue()
    ## END buildBody(self)
## END class UsersWithoutEmpNumSection

class ContactsWithoutEmpNumSection(SfAdminReportBase):
    """
    Report on all contacts who are not marked "InActive" in the
    Contact Status field that do not have an Employee Number set.
    """

    def __init__(self, notifier, userId, contact):
        SfAdminReportBase.__init__(self, notifier, userId, contact)

        self.header = "Magma Contacts Without Employee Numbers"
    ## END __init__


    def buildSecBody(self):
        body = cStringIO.StringIO()

        contactList = self.fetchAllContacts()
        problemContactList = []
        
        for contact in contactList:
            if contact.get(self.contact_fld['Contact Status'], "Active") == "Inactive":
                continue # Don't worry about Ex Employees (inactive contact)

            empNo = contact.get(self.contact_fld['Employee Number'], None)
            if empNo is None:
                problem = "(No Employee Number)"
            elif not self.empNoRE.search(empNo):
                problem = "(Malformed Employee Number)"
            else:
                continue # Should be OK.

            problemContactList.append(contact['id'])
            contactUrl = "https://na1.salesforce.com/%s" %contact['id']
            contactLine =  "%s %s %s" \
                      %(contact.get('firstName', 'NO FIRST NAME'),
                        contact.get('lastName', 'NO LAST NAME'),
                        problem)
            body.write("%s\n\t%s\n\n" %(contactLine, contactUrl))

        if len(problemContactList):
            # set the section footer so that it gets written
            self.footer = "(Note: Please get emp. numbers from HR for these contacts & update salesforce)"
            self.hasContentFlag = True
        else:
            body.write("All contacts have an employee number set.\n")

        return body.getvalue()
    ## END buildBody(self)
## END class ContactsWithoutEmpNumSection


def sortMODsByPriority(a, b):
    """
    Sort two MODs 
    """
    expPriFld = '00N30000000cdwH'

    # If priority isn't set, default it to 4 - Low for sort
    # If expedite priority  isn't set, default it to 2 - No for sort
    aPriority = a['CR'].get('priority', '4')[:1]
    aExpPri = a['CR'].get(expPriFld, '2')[:1]

    bPriority = b['CR'].get('priority', '4')[:1]
    bExpPri = b['CR'].get(expPriFld, '2')[:1]

    aPriVal = "%s%s" %(aPriority, aExpPri)
    bPriVal = "%s%s" %(bPriority, bExpPri)
    
    return cmp(aPriVal,bPriVal)
## END sortMODsByPriority(a, b)
