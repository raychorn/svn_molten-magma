#!/usr/bin/env python2.3
"""
A class for instantiation by sfNotify to generate a type of report

Not intended to stand alone.
"""
#version = 0.10 # Initial version under development
version = 1.10 # factor common elements out for use by other reports

from sfReportBase import ReportBase
from reportSection import ReportSection

import time
import cStringIO
import re

from cookie_xmlrpclib import DateTime

caseType = 'case'
taskType = 'task'

class CRReport(ReportBase):

    def __init__(self, notifier, userId, contact):
        ReportBase.__init__(self, notifier, userId, contact)
        self.crList = []
        self.modList = []

        self.crSectionCore = None
    ## END __init__
        
    def generateReport(self):
        """
        Central method to build CR report
        Calls other methods to build chunks of the report.
        """
        date = time.strftime("%A %B %d, %Y",
                             time.localtime(self.notifier.reportTime))
        subject = "CR Report for %s %s on %s" %(self.contact['firstName'],
                                                self.contact['lastName'],
                                                date)
        self.subject = subject
        

        # Assemble the sections, adding them to the body

        if self.contact.get(self.ct_fld['My CRs with Fixes'], False):
            # My CRs (MODs, really) With Fixes Available
            crWithFixSec = CRsWithFixesSection(self.notifier, self.userId,
                                               self.contact)
            crWithFixTxt = crWithFixSec.getSection()
            self.body.write(crWithFixTxt)

            # note if we have content for the section or not.
            self.sectionContentMap['crWithFixSec'] = crWithFixSec.hasContent()
                

        if self.contact.get(self.ct_fld['My CRs in SCM'], False):
            crSecCore = self.prepCrSectionData()
            crScmSec = ScmCrSection(self.notifier, self.userId,
                                        self.contact, crSecCore)
            
            crScmTxt = crScmSec.getSection()
            self.body.write(crScmTxt)
            
            # note if we have content for the section or not.
            self.sectionContentMap['crScmSec'] = crScmSec.hasContent()


        if self.contact.get(self.ct_fld['My CRs in the Approval Cycle'],
                            False):
            crSecCore = self.prepCrSectionData()
            crApproveSec = ApproveCrSection(self.notifier, self.userId,
                                        self.contact, crSecCore)
            
            crApproveTxt = crApproveSec.getSection()
            self.body.write(crApproveTxt)
            
            # note if we have content for the section or not.
            self.sectionContentMap['crApproveSec'] = crApproveSec.hasContent()


        if self.contact.get(self.ct_fld['My CRs in Development'], False):
            crSecCore = self.prepCrSectionData()
            crDevSec = DevCrSection(self.notifier, self.userId,
                                    self.contact, crSecCore)
            
            crDevTxt = crDevSec.getSection()
            self.body.write(crDevTxt)
    
            # note if we have content for the section or not.
            self.sectionContentMap['crDevSec'] = crDevSec.hasContent()
            

        if self.contact.get(self.ct_fld['My CRs Pending Development'], False):
            # My CRs that I haven't assigned yet
            crSecCore = self.prepCrSectionData()
            crUntouchedSec = UntouchedCrSection(self.notifier, self.userId,
                                                self.contact, crSecCore)
            
            crUntouchedTxt = crUntouchedSec.getSection()
            self.body.write(crUntouchedTxt)

            # note if we have content for the section or not.
            self.sectionContentMap['crUntouchedSec'] = crUntouchedSec.hasContent()


        if self.contact.get(self.ct_fld['My Unassigned CRs'], False):
            # My CRs that I haven't assigned yet
            crSecCore = self.prepCrSectionData()
            crUnassignedSec = UnassignedCrSection(self.notifier, self.userId,
                                                  self.contact, crSecCore)
            
            crUnassignedTxt = crUnassignedSec.getSection()
            self.body.write(crUnassignedTxt)

            # note if we have content for the section or not.
            self.sectionContentMap['crUnassignedSec'] = crUnassignedSec.hasContent()

        if self.contact.get(self.ct_fld['My Recently Closed CRs'], False):
            # My CRs that have been closed since the last report
            crClosedSec = ClosedCrSection(self.notifier, self.userId,
                                          self.contact)
            
            crClosedTxt = crClosedSec.getSection()
            self.body.write(crClosedTxt)

            # note if we have content for the section or not.
            self.sectionContentMap['crClosedSec'] = crClosedSec.hasContent()

            
        self.body.write(self.generateReportFooter())
    ## END generateReport(self)

    def prepCrSectionData(self):
        if self.crSectionCore is None:
            self.crSectionCore = CrSectionCore(self.notifier, self.userId,
                                               self.contact)
        return self.crSectionCore
    ## END prepCrSectionData
## END class CRReport


class CRsWithFixesSection(ReportSection):

    def __init__(self, notifier, userId, contact):
        ReportSection.__init__(self, notifier)

        self.header = "My CRs With Fixes Available"
        
        self.userId = userId
        self.contact = contact

        self.tsk_fld = self.conn.taskFields
    ## END __init__


    def buildSecBody(self):
        body = cStringIO.StringIO()

        self.fetchUserTestingMODs()
        
        if len(self.modList):
            for mod in self.modList:
                modUrl = "%s/%s" %(self.baseUrl, mod['id'])
                modLine1 = "%08d (%s in %s) %s" \
                           %(int(mod['CR']['caseNumber']),
                             self.conn.getCrPriority(mod['CR']),
                             mod[self.tsk_fld['Code Stream']],
                             mod['CR'].get('subject', 'No CR Subject'))
                modLine2 = "%s" %mod.get('subject', 'No MOD Subject')
                outStr = "%s\n\t%s\n\t%s\n\n" %(modLine1, modLine2, modUrl)
                body.write(outStr.encode('ascii','replace'))

            # set the section footer so that it gets written
            self.footer = "(Note: Please test these CRs and close the Mods as appropriate)"
            self.hasContentFlag = True
        else:
            body.write("No CRs are available for you to test at this time.\n")

        return body.getvalue()
    ## END buildBody(self)

    def fetchUserTestingMODs(self):
        """
        Fetch MODs owned by user which have the status
        Merged - Testing by Originator
        """
        modList = []

        # task is a MOD
        modRecordType = "01230000000002v"
        f1 = {'field': 'recordTypeID',
              'operator': 'equals',
              'value': modRecordType}

        # MOD is testing by owner
        f2 = {'field': 'Mod Status',
              'operator': 'equals',
              'value': 'Merged - Testing by Originator'}

        # MOD ownerID is our user
        f3 = {'field': 'ownerID',
              'operator': 'equals',
              'value': self.userId}

        # MOD is not closed
        f4 = {'field': 'closed',
              'operator': 'equals',
              'value': False}

        qryF = [f1, f2, f3, f4]
            
        modResult = self.conn.getSFInfo(taskType, qryF)
        if modResult is not None:
            modList = modResult

        self.modList = modList

        self.fetchMODRelatedCRs()

        self.modList.sort(sortMODsByPriority)
    ## END fetchUserTestingMODs(self)


    def fetchMODRelatedCRs(self):
        # build a list of MOD case ids
        modCaseIdList = []
        for mod in self.modList:
            modCaseIdList.append(mod['whatID'])

        # Fetch the CRs in the list
        modCRList = self.conn.getSFInfoByID(caseType, modCaseIdList)

        # Build a dictionary so we can reference the CRs by ID
        modCRDict = {}
        for cr in modCRList:
            modCRDict[cr['id']] = cr

        # Store each CR with related MOD
        newModList = []
        for mod in self.modList:
            mod['CR'] = modCRDict[mod['whatID']]
            newModList.append(mod)

        self.modList = newModList
    ## END fetchMODRelatedCRs(self)
## END class CRsWithFixesSection(ReportSection)


class CrSectionCore(ReportSection):
    """
    This "section" doesn't really generate a report. Rather it is used
    by actual sections as the source for the user's CR data. This is so we
    can query and sort the data once, then use it for all the reports.
    """
    def __init__(self, notifier, userId, contact):
        ReportSection.__init__(self, notifier)

        self.userId = userId
        self.contact = contact

        self.crList = None
        self.recentClosedCrList = None
        self.modList = None

        self.scmCrList = []
        self.approveCrList = []
        self.devCrList = []
        self.untouchedCrList = []
        self.unassignedCrList = []

        self.cr_fld = self.conn.caseFields

        # This will cause the data to be initialized
        self.classifyCrs()
        self.classifyMods()
    ## END __init__

    def getOpenCreatedCrs(self):
        """
        Query for all open CRs that our user has created.
        """
        global caseType

        if self.crList is None:
            crList = []

            sf1 = {'field': 'recordTypeID',
                   'operator': 'equals',
                   'value': self.conn.recordTypeCR}

            sf2 = {'field': 'recordTypeID',
                   'operator': 'equals',
                   'value': self.conn.recordTypePVCR}

            f1 = {'operator': 'or',
                  'value': [sf1, sf2]}

            f2 = {'field': 'createdByID',
                  'operator': 'equals',
                  'value': self.userId}

            f3 = {'field': 'closed',
                  'operator': 'equals',
                  'value': False}

            qryF = [f1, f2, f3]
            
            fieldDic, flabels, flist, cflist = self.conn.getFieldsDictsLocal(caseType)
            crResult = self.conn.sfAPI.simpleFilterQuery(caseType, qryF, flist)
            if crResult is not None:
                crList = crResult

            crList.sort(sortCRsByPriority)
            self.crList = crList
            
        return self.crList
    ## END getOpenCreatedCrs


    def getModsOnCrs(self):
        if self.modList is None:
            crList = self.getOpenCreatedCrs()
            modList = []

            for cr in crList:
                modsOnCr = self.conn.getAllMODsByCR(cr)
                
                # Tuck the CR in each of its mods
                for mod in modsOnCr:
                    mod['CR'] = cr
                    modList.append(mod)

            modList.sort(sortMODsByPriority)
            self.modList = modList
            
        return self.modList
    ## END getModsOnCrs



    def classifyCrs(self):
        """
        classify CRs into buckets that we'll report on
        """
        crList = self.getOpenCreatedCrs()

        scmStatusRE = re.compile(r'(^|-)SCM-')
        approveStatusRE = re.compile(r'Approv')

        scmCrList = []
        approveCrList = []
        devCrList = []
        untouchedCrList = [] # CR that's been assigned but is still open
        unassignedCrList = []

        unclassCrList = [] # CRs that we don't classify and report on (yet)
        
        for cr in crList:
            status = cr['status']
            if status == 'Open':
                if cr['createdByID'] == cr['ownerID']:
                    # CR hasn't been assigned by the creator
                    unassignedCrList.append(cr)
                else:
                    # CR has been assigned, but work hasn't yet started on it
                    untouchedCrList.append(cr)
            elif status == 'Fixing':
                # CR is in development
                devCrList.append(cr)
            elif scmStatusRE.search(status):
                # CR is in an SCM state
                scmCrList.append(cr)
            elif approveStatusRE.search(status):
                # CR is approving or has been approved
                approveCrList.append(cr)
            else:
                unclassCrList.append(cr)

        self.scmCrList = scmCrList
        self.approveCrList = approveCrList 
        self.devCrList = devCrList
        self.untouchedCrList = untouchedCrList
        self.unassignedCrList = unassignedCrList
        self.unclassCrList = unclassCrList
        return
    ## END classifyCrs

    def classifyMods(self):
        """
        classify MODs into buckets that we'll report on
        """
        modList = self.getModsOnCrs()

        devModList = [] # Mods in Fixing state
        appModList = [] # Mods in Approving/Approved state
        scmModList = [] # Mods in SCM
        tstModList = [] # Mods in testing
        
        unclassModList = [] # all other Mods
        
        for mod in modList:
            status = mod['status']

            if status == 'Fixing':
                devModList.append(mod)
            elif status in self.conn.approveStates:
                appModList.append(mod)
            elif status in self.conn.scmAllStates:
                scmModList.append(mod)
            elif status in self.conn.scmDoneState:
                tstModList.append(mod)
            else:
                unclassModList.append(mod)

        self.devModList = devModList
        self.appModList = appModList
        self.scmModList = scmModList
        self.tstModList = tstModList
        self.unclassModList = unclassModList
    ## END classifyMods
## END class CrSectionCore


class CrSectionBase(ReportSection):
    """
    Common bits for CR sections that don't rely on MOD info
    """

    def __init__(self, notifier, userId, contact, crList):
        """
        notifier - sfNotify instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        ReportSection.__init__(self, notifier)

        self.userId = userId
        self.contact = contact

        # core is the CrSectionCore instance with the user's CR data in it
        self.crList = crList
        
        self.task_fld = self.conn.taskFields
        return
    ## END __init__

    def buildSecBody(self):
        body = cStringIO.StringIO()

        if len(self.crList):
            for cr in self.crList:
                crUrl = "%s/%s" %(self.baseUrl, cr['id'])
                crLine = "%08d (%s) %s" \
                         %(int(cr['caseNumber']), self.conn.getCrPriority(cr),
                           cr.get('subject', 'No Subject'))
                outStr = "%s\n\t%s\n\n" %(crLine, crUrl)
                body.write(outStr.encode('ascii','replace'))

            self.hasContentFlag = True

        return body.getvalue()
    ## END buildSecBody
## END class CrSectionBase


class CrModSectionBase(ReportSection):
    """
    Common bits for CR sections that rely on MOD info
    """

    def __init__(self, notifier, userId, contact, modList):
        """
        notifier - sfNotify instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        ReportSection.__init__(self, notifier)

        self.userId = userId
        self.contact = contact

        # core is the CrSectionCore instance with the user's CR data in it
        self.modList = modList
        
        self.task_fld = self.conn.taskFields
        return
    ## END __init__

    def buildSecBody(self):
        body = cStringIO.StringIO()

        if len(self.modList):
            for mod in self.modList:
                modUrl = "%s/%s" %(self.baseUrl, mod['id'])
                modLine = "%08d (%s in %s) %s" \
                          %(int(mod['CR']['caseNumber']),
                            self.conn.getCrPriority(mod['CR']),
                            mod[self.task_fld['Code Stream']],
                            mod['CR'].get('subject', 'No CR Subject'))
                outStr = "%s\n\t%s\n\n" %(modLine, modUrl)
                body.write(outStr.encode('ascii','replace'))

            self.hasContentFlag = True

        return body.getvalue()
    ## END buildSecBody
## END class CrModSectionBase

class UnassignedCrSection(CrSectionBase):
    """
    Report section on CRs that are owned by creator and status is Open
    """
    def __init__(self, notifier, userId, contact, core):
        """
        notifier - sfNotify instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        CrSectionBase.__init__(self, notifier, userId, contact,
                               core.unassignedCrList)

        self.header = "My CRs That I Haven't Assigned Yet"
        return
    ## END __init__
    
    def buildSecBody(self):
        # Override parent method, but still call it.
        body = CrSectionBase.buildSecBody(self)

        if self.hasContent():
            self.footer = "You may need to assign the CRs in this section to a User or a Queue. See this solution for details: %s/501300000000DiE" %self.baseUrl
        else:
            body = "You have no CRs that you may need to assign at the time of this report.\n"
            
        return body
    ## END buildSecBody
## END class UnassignedCrSection


class UntouchedCrSection(CrSectionBase):
    """
    Report section on CRs that have been assigned and status is Open
    """
    def __init__(self, notifier, userId, contact, core):
        """
        notifier - sfNotify instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        CrSectionBase.__init__(self, notifier, userId, contact,
                               core.untouchedCrList)

        self.header = "My CRs Pending Development"
        return
    ## END __init__
    
    def buildSecBody(self):
        # Override parent method, but still call it.
        body = CrSectionBase.buildSecBody(self)

        if self.hasContent():
            # set self.footer here to add a footer to the section
            pass
        else:
            body = "You have no CRs pending development at the time of this report.\n"
        
        return body
    ## END buildSecBody
## END class UntouchedCrSection


class DevCrSection(CrModSectionBase):
    """
    Report section on CRs that are in development
    """
    def __init__(self, notifier, userId, contact, core):
        """
        notifier - sfNotify instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        CrModSectionBase.__init__(self, notifier, userId, contact,
                                  core.devModList)

        self.header = "My CRs in Development"
        return
    ## END __init__
    
    def buildSecBody(self):
        # Override parent method, but still call it.
        body = CrModSectionBase.buildSecBody(self)

        if self.hasContent():
            # set self.footer here to add a footer to the section
            pass
        else:
            body = "You have no CRs in development at the time of this report.\n"
        
        return body
    ## END buildSecBody
## END class DevCrSection


class ApproveCrSection(CrModSectionBase):
    """
    Report section on CRs that are in the approving/approved states
    """
    def __init__(self, notifier, userId, contact, core):
        """
        notifier - sfNotify instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        CrModSectionBase.__init__(self, notifier, userId, contact,
                                  core.appModList)

        self.header = "My CRs in the Approval Cycle"
        return
    ## END __init__

    def buildSecBody(self):
        body = cStringIO.StringIO()

        approvedRE = re.compile(r'Approved')
        approvingRE = re.compile(r'Approving by (.+)')

        if len(self.modList):
            for mod in self.modList:
                # Come up with a meaningful substatus phrase, like:
                # "is Approved, Pending Branch" or
                # "by John Prodeng as PE"
                approvalSubStatus = "has an unknown approval state"
                if approvedRE.match(mod['status']):
                    approvalSubStatus = "is %s" %mod['status']
                else:
                    match = approvingRE.match(mod['status'])
                    if match is not None:
                        owner = self.lookupUserByIdCache(mod['ownerID'])
                        if owner is None:
                            ownerName = "Unknown"
                        else:
                            ownerName = "%s %s" %(owner.get('firstName', ''),
                                                  owner.get('lastName'))
                            ownerName = ownerName.strip() # in case no fname
                        approvalSubStatus = "by %s as %s" %(ownerName,
                                                            match.group(1))  

                # Now, build the stanza for this mod
                modUrl = "%s/%s" %(self.baseUrl, mod['id'])
                modLine = "%08d (%s in %s %s) %s" \
                          %(int(mod['CR']['caseNumber']),
                            self.conn.getCrPriority(mod['CR']),
                            mod[self.task_fld['Code Stream']],
                            approvalSubStatus,
                            mod['CR'].get('subject', 'No CR Subject'))
                outStr = "%s\n\t%s\n\n" %(modLine, modUrl)
                body.write(outStr.encode('ascii','replace'))

            self.hasContentFlag = True
        else:
            body.write('You have no CRs in the approval cycle at the time of this report.\n')

        return body.getvalue()
    ## END buildSecBody
## END class ApproveCrSection


class ScmCrSection(CrModSectionBase):
    """
    Report section on CRs that are in SCM
    """
    def __init__(self, notifier, userId, contact, core):
        """
        notifier - sfNotify instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        CrModSectionBase.__init__(self, notifier, userId, contact,
                                  core.scmModList)

        self.header = "My CRs in SCM"
        return
    ## END __init__
    
    def buildSecBody(self):
        # Override parent method, but still call it.
        body = CrModSectionBase.buildSecBody(self)

        if self.hasContent():
            # set self.footer here to add a footer to the section
            pass
        else:
            body = "You have no CRs in SCM at the time of this report.\n"
        
        return body
    ## END buildSecBody
## END class ScmCrSection

class ClosedCrSection(ReportSection):
    def __init__(self, notifier, userId, contact):
        ReportSection.__init__(self, notifier)

        self.header = "My CRs That Were Closed Since the Last Report"

        self.userId = userId
        self.contact = contact

        self.recentClosedCrList = []

        self.case_fld = self.conn.caseFields
        return
    ## END __init__

    def buildSecBody(self):
        body = cStringIO.StringIO()

        self.fetchRecentClosedCrs()

        if len(self.recentClosedCrList):
            for cr in self.recentClosedCrList:
                if cr['closeInfo']['createdByID'] == self.userId:
                    closerName = "you"
                else:
                    closerName = "%s %s" %(cr['closeUser'].get('firstName', ''),
                                           cr['closeUser'].get('lastName'))
                    closerName = closerName.strip() # in case no fname
                
                crUrl = "%s/%s" %(self.baseUrl, cr['id'])
                crLine1 = "%08d (%s) %s" \
                          %(int(cr['caseNumber']),
                            self.conn.getCrPriority(cr),
                            cr.get('subject', 'No CR Subject'))
                crLine2 = "has been closed by %s" %closerName
                outStr = "%s\n\t%s\n\t%s\n\n" %(crUrl, crLine1, crLine2)
                body.write(outStr.encode('ascii','replace'))

            self.hasContentFlag = True
        else:
            body.write("None of your CRs have been closed since the last time your report was run.\n")

        return body.getvalue()
    ## END buildSecBody
        
    def fetchRecentClosedCrs(self):
        """
        Fetch user's CRs which have been closed since the last report run date
        """
        
        sf1 = {'field': 'recordTypeID',
               'operator': 'equals',
               'value': self.conn.recordTypeCR}

        sf2 = {'field': 'recordTypeID',
               'operator': 'equals',
               'value': self.conn.recordTypePVCR}

        f1 = {'operator': 'or',
              'value': [sf1, sf2]}

        f2 = {'field': 'createdByID',
              'operator': 'equals',
              'value': self.userId}

        f3 = {'field': 'closed',
              'operator': 'equals',
              'value': True}

        # This is all operated on in UTC
        f4 = {'field': 'lastModifiedDate',
              'operator': 'greater than',
              'value': self.contact.get(self.conn.contactFields['Last Report'], DateTime(self.props.get('notify', 'defaultLastReportTime')))}

        qryF = [f1, f2, f3, f4]

        fieldDic, flabels, flist, cflist = self.conn.getFieldsDictsLocal(caseType)
        crResult = self.conn.sfAPI.simpleFilterQuery(caseType, qryF, flist)
            
        if crResult is not None:
            crList = crResult

        crList.sort(sortCRsByPriority)

        # annotate each CR with who closed it.
        # Also throw out false positives (CR which is closed, and
        # last modified is later than Last Report, but latest
        # closed history item shows CR was closed earlier
        newCrList = []
        for cr in crList:
            cr = self.getCrClosureInfo(cr)
            if cr['closeInfo'] is None:
                continue
            else:
                newCrList.append(cr)

        self.recentClosedCrList = newCrList

        return self.recentClosedCrList
    ## END getRecentClosedCrs

    def getCrClosureInfo(self, cr):
        """
        Look in case history to see who closed the CR
        We only care about most recent closure.
        If no records are found, that means that while the CR may have
        been modified in the time period we're looking at, it was closed
        prior.
        CR map is populated with a closeInfo key and returned.
        """
        caseHistoryType = 'caseHistory'

        f1 = {'field': 'caseID',
              'operator': 'equals',
              'value': cr['id']}

        f2 = {'field': 'field',
              'operator': 'equals',
              'value': 'status'}

        f3 = {'field': 'newValue',
              'operator': 'starts with',
              'value': 'Closed'}

        f4 = {'field': 'createdDate',
              'operator': 'greater than',
              'value': self.contact.get(self.conn.contactFields['Last Report'],
                                                 DateTime(self.props.get('notify', 'defaultLastReportTime')))}

        qryF = [f1, f2, f3, f4]

        chResult = self.conn.getSFInfo(caseHistoryType, qryF)
        if chResult is None or len(chResult) == 0:
            cr['closeInfo'] = None
            cr['closeUser'] = None
        elif len(chResult) >= 1:
            chResult.sort(lambda a, b: cmp(a['createdDate'], b['createdDate']))
            cr['closeInfo'] = chResult[-1]
            # Also, grap the user record of who closed it.
            cr['closeUser'] = self.lookupUserByIdCache(cr['closeInfo']['createdByID'])
            
        return cr
    ## END getCrClosureInfo
## END class ClosedCrSection


def sortMODsByPriority(a, b):
    """
    Sort two MODs by their parent CRs (must be included in MOD dict)
    """
    aCr = a['CR']
    bCr = b['CR']
    
    return sortCRsByPriority(aCr, bCr)
## END sortMODsByPriority(a, b)


def sortCRsByPriority(a, b):
    """
    Compare two CRs by their priority fields
    """
    expPriFld = '00N30000000cdwH'
    
    # If priority isn't set, default it to 3 - Medium for sort
    # If expedite priority  isn't set, default it to 2 - No for sort
    aPriority = a.get('priority', '3')[:1]
    aExpPri = a.get(expPriFld, '2')[:1]

    bPriority = b.get('priority', '3')[:1]
    bExpPri = b.get(expPriFld, '2')[:1]

    aPriVal = "%s%s" %(aPriority, aExpPri)
    bPriVal = "%s%s" %(bPriority, bExpPri)
    
    return cmp(aPriVal,bPriVal)
## END sortCRsByPriority


def sortEntityListByCreatedDate(a, b):
    """
    As the name says...
    The Created Date is an ISO-8601 DateTime which is sortable as a string.
    """
    aDate = a['createdDate']
    bDate = b['createdDate']

    return cmp(aDate, bDate)
## END sortEntityListByCreatedDate
