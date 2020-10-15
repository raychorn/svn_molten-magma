#!/usr/bin/env python2.3
"""
A class for instantiation by sfNotify to generate a type of report

Not intended to stand alone.
"""
#version = 0.10 # Initial version under development
#version = 1.10 # factor common elements out for use by other reports
version = 2.0 # 10/25/2004 Moved to new API and Task Branches

from sfReportBase import ReportBase
from reportSection import ReportSection
from sfUtil import *

from sfConstant import *

import time
import cStringIO
import re
import pprint
import copy
import textwrap
import types

class CRReport(ReportBase):

    def __init__(self, sfTool, userId, contact, sectionList=[]):
        ReportBase.__init__(self, sfTool, userId, contact)
        self.sectionList = sectionList
        self.crList = []
        self.modList = []

        self.crSectionCore = None
    ## END __init__
        
    def generateReport(self):
        """
        Central method to build CR report
        Calls other methods to build chunks of the report.
        """
        print "CR REPORT"
        date = time.strftime("%A %B %d, %Y",
                             time.localtime(self.sfTool.reportTime))
        subject = "CR Report for %s %s on %s" %(self.contact.get('FirstName'),
                                                self.contact.get('LastName'),
                                                date)
        self.subject = subject
        

        # Assemble the sections, adding them to the body
        section = 'TestFixes'
        if section in self.sectionList:
            # My CRs (MODs, really) With Fixes Available
            crWithFixSec = CRsWithFixesSection(self.sfTool, self.userId,
                                               self.contact)
            crWithFixTxt = crWithFixSec.getSection()
            self.body.write(crWithFixTxt)

            # note if we have content for the section or not.
            self.sectionContentMap[section] = crWithFixSec.hasContent()
                
        section = 'Unassigned'
        if section in self.sectionList:
            crSecCore = self.prepCrSectionData()
            crUnasgSec = UnassignedCrSection(self.sfTool, self.userId,
                                        self.contact, crSecCore)
            crUnasgTxt = crUnasgSec.getSection()
            self.body.write(crUnasgTxt)

            # note if we have content for the section or not.
            self.sectionContentMap[section] = crUnasgSec.hasContent()

        section = 'RecentClose'
        if section in self.sectionList:
            crClosedSec = ClosedCrSection(self.sfTool, self.userId,
                                          self.contact)
            crClosedTxt = crClosedSec.getSection()
            self.body.write(crClosedTxt)

            # note if we have content for the section or not.
            self.sectionContentMap[section] = crClosedSec.hasContent()

        section = 'SCM'
        if section in self.sectionList:
            crSecCore = self.prepCrSectionData()
            crScmSec = ScmCrSection(self.sfTool, self.userId,
                                    self.contact, crSecCore)
            crScmTxt = crScmSec.getSection()
            self.body.write(crScmTxt)

            # note if we have content for the section or not.
            self.sectionContentMap[section] = crScmSec.hasContent()

        section = 'Team'
        if section in self.sectionList:
            crSecCore = self.prepCrSectionData()
            crTeamSec = TeamCrSection(self.sfTool, self.userId,
                                      self.contact, crSecCore)
            crTeamTxt = crTeamSec.getSection()
            self.body.write(crTeamTxt)

            # note if we have content for the section or not.
            self.sectionContentMap[section] = crTeamSec.hasContent()

        section = 'PE'
        if section in self.sectionList:
            crSecCore = self.prepCrSectionData()
            crAppPeSec = AppPeCrSection(self.sfTool, self.userId,
                                        self.contact, crSecCore)
            crAppPeTxt = crAppPeSec.getSection()
            self.body.write(crAppPeTxt)

            # note if we have content for the section or not.
            self.sectionContentMap[section] = crAppPeSec.hasContent()

        section = 'EngMgr'
        if section in self.sectionList:
            crSecCore = self.prepCrSectionData()
            crAppMgrSec = AppMgrCrSection(self.sfTool, self.userId,
                                          self.contact, crSecCore)
            crAppMgrTxt = crAppMgrSec.getSection()
            self.body.write(crAppMgrTxt)

            # note if we have content for the section or not.
            self.sectionContentMap[section] = crAppMgrSec.hasContent()        
            

        section = 'Dev'
        if section in self.sectionList:
            crSecCore = self.prepCrSectionData()
            crDevSec = DevCrSection(self.sfTool, self.userId,
                                    self.contact, crSecCore)
            crDevTxt = crDevSec.getSection()
            self.body.write(crDevTxt)

            # note if we have content for the section or not.
            self.sectionContentMap[section] = crDevSec.hasContent()

        section = 'Untouched'
        if section in self.sectionList:
            crSecCore = self.prepCrSectionData()
            crUntouchSec = UntouchedCrSection(self.sfTool, self.userId,
                                              self.contact, crSecCore)
            crUntouchTxt = crUntouchSec.getSection()
            self.body.write(crUntouchTxt)

            # note if we have content for the section or not.
            self.sectionContentMap[section] = crUntouchSec.hasContent()

        
        


        self.body.write(self.generateReportFooter())

        
    ## END generateReport(self)

    def prepCrSectionData(self):
        if self.crSectionCore is None:
            self.crSectionCore = CrSectionCore(self.sfTool, self.userId,
                                               self.contact)
        return self.crSectionCore
    ## END prepCrSectionData
## END class CRReport

class ReportQueryMixin:
    """ Provides a collection of queries used to build related reports so that
    such code may be shared.
    """
    seriesSize = 15
    
    def fetchOriginatorTestingBAs(self):
        """
        Fetch CR Originator BAs which have the status Merged - Testing
        by Originator and the Approve field is not marked 'Approve'

        This query will need to change to find BAs which are of role
        CR Originator, Status = Merged - Testing by Originator and
        Approve != Approve.

        returns map of BAs keyed by task (or team?) branch
        """
        baList = []

        f1 = ['Approval_Role__c','=','CR Originator']
        f2 = ['Status__c','=','Merged - Testing by Originator']
        f3 = ['Approve__c','!=','Approve']
        f4 = ['Approve__c','!=','Reject']
        f5 = ['OwnerId','=',self.userId]
        where = [f1, 'and', f2, 'and', f3, 'and', f4, 'and', f5]
        
        print "QUERY  ........ %s" %where

        baList = self.sfTool.query(BRANCH_APPROVAL_OBJ, where, sc='all')

        if baList in BAD_INFO_LIST:
            baList = []
            pass

        baMap = {}
        tbIdList = []
        baByTbCrMap = {}
        for ba in baList:
            tbId = ba.get('Task_Branch__c')
            aeBaCrNum = ba.get('CR_List__c','').lstrip('0')
            print "Task Branch Id %s .... and CR num %s ..." %(tbId,aeBaCrNum)
            if tbId is None:
                continue

            if tbId not in tbIdList:
                tbIdList.append(tbId)
                
            key = '%s:%s' %(tbId, aeBaCrNum)
            if baByTbCrMap.has_key(key):
                msg = "Already saw an AE BA on task branch %s for CR num %s" \
                      %(tbId, aeBaCrNum)
                self.sfTool.setLog(msg, 'warn')
            baByTbCrMap[key] = ba
            
            if baMap.has_key(tbId):
                baMap[tbId].append(ba)
            else:
                baMap[tbId] = [ba]
                pass

            continue
        
        #return baMap
        return tbIdList, baByTbCrMap
    ## END fetchUserTestingBAa

    def retrieveTaskBranches(self, taskBranchIdList):
        """Performs a retrieve of the supplied task branch list
        """
        tbFieldList = ('Id','Branch_Status__c','Code_Stream__c',
                       'Merged_Date_Time__c')
        
        tbList = self.sfTool.retrieve(taskBranchIdList, TASK_BRANCH_OBJ,
                                      fieldList=tbFieldList)
        if tbList in BAD_INFO_LIST:
            tbList = []
            pass
        
        tbMap = {}
        for tb in tbList:
            tbMap[tb.get('Id')] = tb
            continue
        
        return tbMap
    ## END retrieveTaskBranches

    def fetchBranchCRLinks(self, taskBranchIdList):
        """Performs a series of queries to find BranchCR links on supplied
        TaskBranchIds.

        Returns two maps relating branch IDs to CR IDs and vice versa
        """
        myTbIdList = copy.deepcopy(taskBranchIdList)
        # divvy ID list into subgroups of no more than seriesSize
        brCrList = []
        while len(myTbIdList) > 0:
            series = myTbIdList[:self.seriesSize]
            myTbIdList = myTbIdList[self.seriesSize:]

            # Build where list for the series and query the links, appending
            # results to a list
            where = []
            for tbId in series:
                where.append(['Task_Branch__c','=',tbId])
                where.append('or')
                continue

            # delete the straggling 'or'
            if len(where) > 1:
                where.pop()
                pass
            
            # run the query with the where clause
            res = self.sfTool.query(BRANCH_CR_LINK_OBJ, where,
                                    sc='brcrl')

            if res not in BAD_INFO_LIST and \
               type(res) in [types.ListType, types.TupleType]:
                brCrList.extend(res)
                pass
            continue
        return self.processFetchedBranchCrLinks(brCrList)
    ## END fetchBranchCRLinks

    def fetchCrBranchLinks(self, crIdList):
        brCrMap = {}
        crBrMap = {}

        # divvy ID list into subgroups of no more than seriesSize
        brCrList = []
        while len(crIdList) > 0:
            series = crIdList[:self.seriesSize]
            crIdList = crIdList[self.seriesSize:]
           
            where = []
            for crId in series:
                #crId = cr['Id']
                where.append(['Case__c','=',crId])
                where.append('or')
                continue

            # delete the straggling 'or'
            where.pop()

            # run the query with the where clause
            res = self.sfTool.query(BRANCH_CR_LINK_OBJ, where,
                                    sc='brcrl')

            if res not in BAD_INFO_LIST and \
               type(res) in [types.ListType, types.TupleType]:
                brCrList.extend(res)
                pass
            continue
        
        return self.processFetchedBranchCrLinks(brCrList)
    ## END fetchCRBranchLinks

    def processFetchedBranchCrLinks(self, brCrList):
        """
        Common
        """
        # slice list into two maps: BranchId -> CrId and CrId -> BranchId
        brCrMap = {}
        crBrMap = {}
        for brCrLink in brCrList:
            caseId = brCrLink.get('Case__c',None)
            tbId = brCrLink.get('Task_Branch__c',None)

            if caseId is not None and tbId is not None:
                # add to the branch -> cr map 
                if not brCrMap.has_key(tbId):
                    brCrMap[tbId] = []

                if caseId not in brCrMap[tbId]:
                    brCrMap[tbId].append(caseId)

                # add to the cr -> branch map
                if not crBrMap.has_key(caseId):
                    crBrMap[caseId] = []

                if tbId not in crBrMap[caseId]:
                    crBrMap[caseId].append(tbId)

            continue
        
        return brCrMap, crBrMap
    ## END processFetchedBranchCrLinks

    def retrieveCRs(self, crIdList):
        """Performs a retrieve of the supplied CR Id list
        """

        crFieldList = ('Id','OwnerId','CaseNumber','Subject','Status',
                       'Priority','ExpeditedPriority__c')
        crList = self.sfTool.retrieve(crIdList, CASE_OBJ,
                                      fieldList=crFieldList)
        if crList in BAD_INFO_LIST:
            crList = []
            pass
        
        crMap = {}
        for cr in crList:
            crMap[cr.get('Id')] = cr
            continue

        return crMap
    ## END retrieveCRs
## END class ReportQueryMixin
    
class CrSectionCore(ReportSection, ReportQueryMixin):

    def __init__(self, sfTool, userId, contact):
        ReportSection.__init__(self, sfTool)

        self.userId = userId
        self.contact = contact

        self.crMap = None
        self.tbMap = None
        self.recentClosedCrList = None

        self.scmCrList = []
        self.MgrAppCrList = []
        self.PEAppCrList = []
        self.TeamCrList = []
        self.devCrList = []
        self.untouchedCrList = []
        self.unassignedCrList = []
        
        self.brCrMap = {}
        self.crBrMap = {}
        
        # This will cause the data to be initialized
        self.classifyCrs()
        self.classifyTaskBranches()
        return
    ## END __init__

    def fetchOpenCreatedCrs(self):
        """ Query for all open CRs that our user has created.
        """
        if self.crMap is None:
            crList = []
            crMap = {}

            f1  = ['CreatedById','=',self.userId]
            f2  = ['IsClosed','=',False]

            f3a = ['RecordTypeId','=',RECTYPE_CR]
            f3b = ['RecordTypeId','=',RECTYPE_PVCR]
            f3c = ['RecordTypeId','=',RECTYPE_PLDCR]

            where = [f1,'and',f2,'and','(',f3a,'or',f3b,'or',f3c,')']
            fields = ('Id','CaseNumber','Subject','Priority', 'OwnerId',
                      'ExpeditedPriority__c', 'Status', 'CreatedById')
            res = self.sfTool.query(CASE_OBJ, where, fields)
            if res not in BAD_INFO_LIST:
                crList = res
                pass

            for cr in crList:
                crMap[cr['Id']] = cr

            self.crMap = crMap
            pass
        
        return self.crMap
    ## END fetchOpenCreatedCrs

    def fetchBranchesOnCrs(self, crIdList):
        if self.tbMap is None:
            self.tbMap = []
            # Fetch branch CR links on cases
            self.brCrMap, self.crBrMap = self.fetchCrBranchLinks(crIdList)

            # retrieve task branches by ID
            self.tbMap = self.retrieveTaskBranches(self.brCrMap.keys())
            pass
        
        return self.tbMap
    ## END fetchBranchesOnCrs

    def classifyCrs(self):
        crMap = self.fetchOpenCreatedCrs()
        crList = crMap.values()
        crList.sort(sortCRsByPriority)

        scmStatusRE = re.compile(r'(^|-)SCM-')
        approveStatusRE = re.compile(r'Approv')
       
        scmCrList = []
        approveCrList = []
        devCrList = []
        untouchedCrList = [] # CR that's been assigned but is still open
        unassignedCrList = []
        
        unclassCrList = [] # CRs that we don't classify and report on (yet)
      
        for cr in crList:
            status = cr['Status']
            if status == 'Open':
                if cr['CreatedById'] == cr['OwnerId']:
                    # CR hasn't been assigned by the creator
                    unassignedCrList.append(cr)
                else:
                    # CR has been assigned, but work hasn't yet started on it
                    untouchedCrList.append(cr)
                    pass
                pass
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
                pass
            continue
        self.scmCrList = scmCrList
        self.approveCrList = approveCrList 
        self.devCrList = devCrList
        self.untouchedCrList = untouchedCrList
        self.unassignedCrList = unassignedCrList
        self.unclassCrList = unclassCrList
        return
    ## END classifyCrs

    def classifyTaskBranches(self):
        crMap = self.fetchOpenCreatedCrs()
        tbMap = self.fetchBranchesOnCrs(crMap.keys())

        fixingStates = ['Fixing', 'Rejected by Mgr', 'Rejected by PE']
        mgrAppStates = ['Approving by Manager']
        peAppStates = ['Approving by PE']
        teamStates = ['Approved, pending Team Branch']
        scmStates = ['Submitted to SCM','SCM-Submitted','SCM-Received','SCM-Need Branch','SCM-QOR Building','SCM-QOR Testing','SCM-QOR Results','SCM-Hold','post_release','SCM-Post-Release','SCM-Ready to Bundle','SCM-Bundle Building','SCM-Bundle Testing','SCM-Bundle Results','SCM-Approved','SCM-Patch-Build-Delayed','SCM-Patch-Building','SCM-Patch-Build Testing','SCM-Patch-Build Results','SCM-Red-Building','SCM-Red-Build Results','SCM-Candidate-Building','SCM-Candidate-Build Testing','SCM-Candidate-Build Results','SCM-Patch-Build Today','SCM-Ready-for-Patch-Build','SCM-Red-Build Today']
        testingStates = ['Merged']
        
        devTbList = [] # Branches in Fixing state
        mgrAppTbList = [] # Branches in Mgr Approving
        peAppTbList = [] # Branches in PE Approving
        teamTbList = [] # Branches in Team phase
        scmTbList = [] # Branches in SCM
        testTbList = [] # Branches in testing

        unclassTbList = [] # all other Branches

        for tbId, tb in tbMap.items():
            status = tb.get('Branch_Status__c','')

            if status in fixingStates:
                devTbList.append(tb)
            elif status in mgrAppStates:
                mgrAppTbList.append(tb)
            elif status in peAppStates:
                peAppTbList.append(tb)
            elif status in teamStates:
                teamTbList.append(tb)
            elif status in scmStates:
                scmTbList.append(tb)
            elif status in testingStates:
                testTbList.append(tb)
            else:
                unclassTbList.append(tb)
                pass
            continue

        self.devTbList = devTbList
        self.mgrAppTbList = mgrAppTbList
        self.peAppTbList = peAppTbList
        self.teamTbList = teamTbList
        self.scmTbList = scmTbList
        self.testTbList = testTbList
        self.unclassTbList = unclassTbList

        return
    ## END def classifyBranches

## END class CrSectionCore
    
class CrTbSectionBase(ReportSection):
    """ Common bits for CR sections that rely on Task Branch info
    """
    seriesSize = 15
    def __init__(self, sfTool, userId, contact, core, tbList):
        """
        sfTool - sfTool instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        ReportSection.__init__(self, sfTool)

        self.userId = userId
        self.contact = contact

        # core is the CrSectionCore instance with the user's CR data in it
        self.tbList = tbList
        self.core = core
        return
    ## END __init__

    def buildSecBody(self):
        body = cStringIO.StringIO()

        if len(self.tbList):
            for tb in self.tbList:
                tbId = tb['Id']
                crIdList = self.core.brCrMap.get(tbId, [])

                for crId in crIdList:
                    cr = self.core.crMap[crId]
                    tbUrl = "%s/%s" %(self.baseUrl, tbId)
                    tbLine = "%08d (%s in %s)" \
                             %(int(cr['CaseNumber']),
                               self.sfTool.getCrPriority(cr),
                               tb.get('Code_Stream__c','No Code Stream'))
                    tbLine2 = "%s" %textwrap.fill(cr.get('Subject', 'No CR Subject'))
                    outStr = "%s\n%s\n\tTask Branch: %s\n\n" %(tbLine, tbLine2, tbUrl)
                    body.write(outStr.encode('ascii','replace'))

            self.hasContentFlag = True

        return body.getvalue()
    ## END buildSecBody
## END class CrTbSectionBase

    
class CrSectionBase(ReportSection):
    """
    Common bits for CR sections that don't rely on MOD info
    """

    def __init__(self, sfTool, userId, contact, core, crList):
        """
        sfTool - sfTool instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        ReportSection.__init__(self, sfTool)

        self.userId = userId
        self.contact = contact

        # core is the CrSectionCore instance with the user's CR data in it
        self.crList = crList
        self.core = core
        return
    ## END __init__

    def buildSecBody(self):
        body = cStringIO.StringIO()

        if len(self.crList):
            for cr in self.crList:
                crUrl = "%s/%s" %(self.baseUrl, cr['Id'])
                crLine = "%08d (%s)\n%s" \
                         %(int(cr['CaseNumber']), self.sfTool.getCrPriority(cr),
                           textwrap.fill(cr.get('Subject', 'No Subject')))
                outStr = "%s\n\t%s\n\n" %(crLine, crUrl)
                body.write(outStr.encode('ascii','replace'))
                continue

            self.hasContentFlag = True
            pass
        return body.getvalue()
    ## END buildSecBody
## END class CrSectionBase


class CRsWithFixesSection(ReportSection, ReportQueryMixin):
    # First section to convert.....

    def __init__(self, sfTool, userId, contact):
        ReportSection.__init__(self, sfTool)

        self.header = "My CRs With Fixes Available"
        
        self.userId = userId
        self.contact = contact
    ## END __init__


    def buildSecBody(self):
        body = cStringIO.StringIO()

        dataList = self.fetchSectionDataFlow()
        
        if len(dataList):
            for dataTuple in dataList:
                crData = dataTuple[0]
                tbData = dataTuple[1]
                baData = dataTuple[2]
                
                #baUrl = "Edit Branch Approval: %s/%s/e" \
                baUrl = "Branch Approval: %s/%s" \
                        %(self.baseUrl, baData.get('Id',''))
                tbUrl = "Task Branch:          %s/%s" \
                        %(self.baseUrl, tbData['Id'])
                tbLine1 = "%08d (%s in %s)" \
                           %(int(crData.get('CaseNumber','').lstrip('0')),
                             self.sfTool.getCrPriority(crData),
                             tbData.get('Code_Stream__c',''))
                tbLine2 = "%s" %textwrap.fill(crData.get('Subject', 'No CR Subject'))
                outStr = "%s\n%s\n\t%s\n\t%s\n\n" %(tbLine1, tbLine2, baUrl, tbUrl)
                body.write(outStr.encode('ascii','replace'))

            # set the section footer so that it gets written
            self.footer = "(Note: Please test these CRs and mark the Branch Approvals as appropriate)"
            self.hasContentFlag = True
        else:
            body.write("No CRs are available for you to test at this time.\n")

        return body.getvalue()
    ## END buildBody(self)

    def fetchSectionDataFlow(self):
        """ Contains the flow for assembling this section's data
        """
        tbMap = {}
        brCrMap = {}
        crBrMap = {}
        crMap = {}
        
        tbIdList, baByTbCrMap = self.fetchOriginatorTestingBAs()

        if len(tbIdList):
            tbMap = self.retrieveTaskBranches(tbIdList)
            brCrMap, crBrMap = self.fetchBranchCRLinks(tbIdList)

        if len(crBrMap):
            crMap = self.retrieveCRs(crBrMap.keys())
            pass

        # now, correlate the data:
        crList = [] #[ ({crData}, {tbData}, {baData})]

        # crawl found TBs
        for tbId, tbData in tbMap.items():
            crIdList = brCrMap.get(tbId, [])

            for crId in crIdList:
                crData = crMap.get(crId, None)

                if crData is None:
                    continue

                crNum = crData.get('CaseNumber','').lstrip('0')

                baKey = '%s:%s' %(tbId, crNum)

                baData = baByTbCrMap.get(baKey, None)

                if crData is not None and baData is not None:
                    crList.append((crData, tbData, baData))
                    pass
                continue
            continue
        
        crList.sort(sortBaCrsByPriority)

        return crList
    ## END fetchSectionDataFlow

## END class CRsWithFixesSection(ReportSection)


class ScmCrSection(CrTbSectionBase):
    """
    Report section on CRs that are in SCM
    """
    def __init__(self, sfTool, userId, contact, core):
        """
        sfTool - SFMagmaTool (or subclass) instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        CrTbSectionBase.__init__(self, sfTool, userId, contact,
                                  core, core.scmTbList)

        self.header = "My CRs in SCM"
        return
    ## END __init__
    
    def buildSecBody(self):
        # Override parent method, but still call it.
        body = CrTbSectionBase.buildSecBody(self)

        if self.hasContent():
            # set self.footer here to add a footer to the section
            pass
        else:
            body = "You have no CRs in SCM at the time of this report.\n"
        
        return body
    ## END buildSecBody
## END class ScmCrSection

class TeamCrSection(CrTbSectionBase):
    """
    Report section on CRs that are in the Team phase
    """
    def __init__(self, sfTool, userId, contact, core):
        """
        sfTool - SFMagmaTool (or subclass) instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        CrTbSectionBase.__init__(self, sfTool, userId, contact,
                                  core, core.teamTbList)

        self.header = "My CRs in the Team Phase"
        return
    ## END __init__
    
    def buildSecBody(self):
        # Override parent method, but still call it.
        body = CrTbSectionBase.buildSecBody(self)

        if self.hasContent():
            # set self.footer here to add a footer to the section
            pass
        else:
            body = "You have no CRs in the Team Phase at the time of this report.\n"
        
        return body
    ## END buildSecBody
## END class TeamCrSection

class AppPeCrSection(CrTbSectionBase):
    """
    Report section on CRs that have branches up for approval by PE
    """
    def __init__(self, sfTool, userId, contact, core):
        """
        sfTool - SFMagmaTool (or subclass) instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        CrTbSectionBase.__init__(self, sfTool, userId, contact,
                                  core, core.peAppTbList)

        self.header = "My CRs in Branches Awaiting PE Approval"

        # select the PE BAs on the TbList which are "Approving"
        self.approverMap = self.fetchPEApprovers(core.peAppTbList)

        return
    ## END __init__
    
    def fetchPEApprovers(self, tbList):
        """ Get Approving managers on listed task branches for role
        """
        f1 = ['Status__c','=','Approving']
        f2 = ['Approval_Role__c','=','Product Engineer']

        fields = ('Id','Task_Branch__c','CR_List__c','OwnerId')
        approverMap = {}
        uidList = []
        myTbList = copy.deepcopy(tbList)
        while len(myTbList) > 0:
            series = myTbList[:self.seriesSize]
            myTbList = myTbList[self.seriesSize:]

            where = [f1,'and',f2,'and','(']
            for tb in series:
                tbId = tb['Id']
                where.append(['Task_Branch__c','=',tbId])
                where.append('or')
                continue
            where.pop()
            where += [')']

            # run the query with the where clause
            res = self.sfTool.query('Branch_Approval__c', where,
                                    sc=fields)
            if res not in BAD_INFO_LIST:
                for ba in res:
                    crListStr = ba.get('CR_List__c')
                    crList = crListStr.split(',')

                    for crNum in crList:
                        if crNum == '': continue
                        crNum = crNum.lstrip('0')
                        
                        key = "%s-%s" %(ba['Task_Branch__c'], crNum)
                        approverMap[key] = ba
                        continue
                    
                    if ba['OwnerId'] not in uidList:
                        uidList.append(ba['OwnerId'])
                        pass
                    continue
                pass
            continue

        # retrieve the list of owner IDs
        userNameMap = {}
        fields = ('Id', 'FirstName', 'LastName')
        res = self.sfTool.retrieve(uidList, 'User', fieldList=fields)
        if res not in BAD_INFO_LIST:
            for user in res:
                userName = "%s %s" %(user.get('FirstName',''), user.get('LastName'))
                userNameMap[user['Id']] = userName.lstrip()

        # now match the names up with the approver IDs
        for key, ba in approverMap.items():
            approverId = ba['OwnerId']
            ba['OwnerName'] = userNameMap.get(approverId,'Name Not Found')
            approverMap[key] = ba

        return approverMap
    ## END fetchPEApprovers

    def buildSecBody(self):
        body = cStringIO.StringIO()

        if len(self.tbList):
            for tb in self.tbList:
                tbId = tb['Id']
                crIdList = self.core.brCrMap.get(tbId, [])

                for crId in crIdList:
                    cr = self.core.crMap[crId]
                    crNum = cr.get('CaseNumber').lstrip('0')
                    key = "%s-%s" %(tbId, crNum)
                    approverInfo = self.approverMap.get(key,{})
                    approverName = approverInfo.get('OwnerName','')
                    
                    tbUrl = "%s/%s" %(self.baseUrl, tbId)

                    if len(approverName):
                        tbLine = "%08d (%s in %s by %s)" \
                                 %(int(cr['CaseNumber']),
                                   self.sfTool.getCrPriority(cr),
                                   tb.get('Code_Stream__c','No Code Stream'),
                                   approverName)
                    else:
                        tbLine = "%08d (%s in %s)" \
                                 %(int(cr['CaseNumber']),
                                   self.sfTool.getCrPriority(cr),
                                   tb.get('Code_Stream__c','No Code Stream'))

                    tbLine2 = "%s" %textwrap.fill(cr.get('Subject', 'No CR Subject'))
                    tbLine2 = tbLine2.strip()
                    outStr =  "%s\n" %tbLine
                    outStr += "%s\n" %tbLine2
                    outStr += "\tTask Branch: %s\n\n" %tbUrl
                    body.write(outStr.encode('ascii','replace'))

            self.hasContentFlag = True


        if self.hasContent():
            # set self.footer here to add a footer to the section
            # set the section footer so that it gets written
            self.footer =  "(Note: Each of the CRs listed above may have already been\n"
            self.footer += "approved in the linked task branch, however the task branch\n"
            self.footer += "may still be waiting for approval by other PEs on other CRs.)"
        else:
            body.write("You have no CRs in branches awaiting PE approval at the time of this report.\n")
            pass
        return body.getvalue()
    ## END buildSecBody## END class ScmAppPeSection

class AppMgrCrSection(CrTbSectionBase):
    """
    Report section on CRs that have branches up for approval by Eng Mgr.
    """
    def __init__(self, sfTool, userId, contact, core):
        """
        sfTool - SFMagmaTool (or subclass) instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        CrTbSectionBase.__init__(self, sfTool, userId, contact,
                                  core, core.mgrAppTbList)

        self.header = "My CRs in Branches Awaiting Engineering Manager Approval"

        # select the manager BAs on the TbList which are "Approving"
        self.approverMap = self.fetchMgrApprovers(core.mgrAppTbList)
        return
    ## END __init__

    def fetchMgrApprovers(self, tbList):
        """ Get Approving managers on listed task branches for role
        """
        f1 = ['Status__c','=','Approving']
        f2 = ['Approval_Role__c','=','Engineering Manager']

        fields = ('Id','Task_Branch__c','OwnerId')
        approverMap = {}
        uidList = []
        myTbList = copy.deepcopy(tbList)
        while len(myTbList) > 0:
            series = myTbList[:self.seriesSize]
            myTbList = myTbList[self.seriesSize:]

            where = [f1,'and',f2,'and','(']
            for tb in series:
                tbId = tb['Id']
                where.append(['Task_Branch__c','=',tbId])
                where.append('or')
                continue
            where.pop()
            where += [')']

            # run the query with the where clause
            res = self.sfTool.query('Branch_Approval__c', where,
                                    sc=fields)
            if res not in BAD_INFO_LIST:
                for ba in res:
                    approverMap[ba['Task_Branch__c']] = ba
                    if ba['OwnerId'] not in uidList:
                        uidList.append(ba['OwnerId'])
                    continue
                pass
            continue

        # retrieve the list of owner IDs
        userNameMap = {}
        fields = ('Id', 'FirstName', 'LastName')
        res = self.sfTool.retrieve(uidList, 'User', fieldList=fields)
        if res not in BAD_INFO_LIST:
            for user in res:
                userName = "%s %s" %(user.get('FirstName',''), user.get('LastName'))
                userNameMap[user['Id']] = userName.lstrip()

        # now match the names up with the approver IDs
        for tbId, ba in approverMap.items():
            approverId = ba['OwnerId']
            ba['OwnerName'] = userNameMap.get(approverId,'Name Not Found')
            approverMap[tbId] = ba

        return approverMap
    ## END fetchMgrBAs
    
    def buildSecBody(self):
        body = cStringIO.StringIO()

        if len(self.tbList):
            for tb in self.tbList:
                tbId = tb['Id']
                crIdList = self.core.brCrMap.get(tbId, [])

                for crId in crIdList:
                    cr = self.core.crMap[crId]
                    approverInfo = self.approverMap.get(tbId,{})
                    approverName = approverInfo.get('OwnerName','')

                    tbUrl = "%s/%s" %(self.baseUrl, tbId)

                    if len(approverName):
                        tbLine = "%08d (%s in %s by %s)" \
                                 %(int(cr['CaseNumber']),
                                   self.sfTool.getCrPriority(cr),
                                   tb.get('Code_Stream__c','No Code Stream'),
                                   approverName)
                    else:
                        tbLine = "%08d (%s in %s)" \
                                 %(int(cr['CaseNumber']),
                                   self.sfTool.getCrPriority(cr),
                                   tb.get('Code_Stream__c','No Code Stream'))
                        
                    tbLine2 = "%s" %textwrap.fill(cr.get('Subject', 'No CR Subject'))
                    tbLine2 = tbLine2.strip()
                    outStr = "%s\n%s\n\tTask Branch: %s\n\n" %(tbLine, tbLine2, tbUrl)
                    body.write(outStr.encode('ascii','replace'))

            self.hasContentFlag = True


        if self.hasContent():
            # set self.footer here to add a footer to the section
            pass
        else:
            body.write("You have no CRs in branches awaiting mgr. approval at the time of this report.\n")
        
        return body.getvalue()
    ## END buildSecBody
## END class ScmAppMgrSection

class DevCrSection(CrTbSectionBase):
    """
    Report section on CRs that are in development
    """
    def __init__(self, sfTool, userId, contact, core):
        """
        sfTool - SFMagmaTool (or subclass) instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        CrTbSectionBase.__init__(self, sfTool, userId, contact,
                                  core, core.devTbList)

        self.header = "My CRs in Development"
        return
    ## END __init__
    
    def buildSecBody(self):
        # Override parent method, but still call it.
        body = CrTbSectionBase.buildSecBody(self)

        if self.hasContent():
            # set self.footer here to add a footer to the section
            pass
        else:
            body = "You have no CRs in development at the time of this report.\n"
        
        return body
    ## END buildSecBody
## END class DevCrSection

class UnassignedCrSection(CrSectionBase):
    """
    Report section on CRs that are owned by creator and status is Open
    """
    def __init__(self, sfTool, userId, contact, core):
        """
        notifier - sfNotify instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        CrSectionBase.__init__(self, sfTool, userId, contact,
                               core, core.unassignedCrList)

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
    def __init__(self, sfTool, userId, contact, core):
        """
        notifier - sfNotify instance
        userId - sfdc user ID of the person we're generating the report for
        contact - contact record of the person we're writing report for
        core - CrSectionCore instance 
        """
        CrSectionBase.__init__(self, sfTool, userId, contact,
                               core, core.untouchedCrList)

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

class ClosedCrSection(ReportSection):
    def __init__(self, sfTool, userId, contact):
        ReportSection.__init__(self, sfTool)

        self.header = "My CRs That Were Closed Since the Last Report"

        self.userId = userId
        self.contact = contact

        self.recentClosedCrList = []

        return
    ## END __init__

    def buildSecBody(self):
        body = cStringIO.StringIO()

        self.fetchRecentClosedCrs()

        if len(self.recentClosedCrList):
            for cr in self.recentClosedCrList:
                if cr['closeInfo']['CreatedById'] == self.userId:
                    closerName = "you"
                else:
                    closerName = "%s %s" %(cr['closeUser'].get('FirstName', ''),
                                           cr['closeUser'].get('LastName'))
                    closerName = closerName.strip() # in case no fname
                
                crUrl = "%s/%s" %(self.baseUrl, cr['Id'])
                crLine1 = "%08d (%s) %s" \
                          %(int(cr['CaseNumber']),
                            self.sfTool.getCrPriority(cr),
                            cr.get('Subject', 'No CR Subject'))
                crLine2 = "has been closed by %s" %closerName
                outStr = "%s\n\t%s\n\t%s\n\n" %(crUrl, crLine1, crLine2)
                body.write(outStr.encode('ascii','replace'))

            self.hasContentFlag = True
        else:
            body.write("No CRs you created have been closed since the last time your report was run.\n")

        return body.getvalue()
    ## END buildSecBody
        
    def fetchRecentClosedCrs(self):
        """
        Fetch user's CRs which have been closed since the last report run date
        """
        
        f1a = ['RecordTypeId', '=', RECTYPE_CR]
        f1b = ['RecordTypeId', '=', RECTYPE_PVCR]
        f1c = ['RecordTypeId', '=', RECTYPE_PLDCR]

        f2  = ['CreatedById', '=', self.userId]

        f3  = ['IsClosed', '=', True]

        # This is all operated on in UTC
        (discard, discard, lastReportDate) = self.sfTool.parseLastReportDate(self.contact)
        f4 = ['LastModifiedDate', '>', lastReportDate]

        where = ['(',f1a,'or',f1b,'or',f1c,')','and',f2,'and',f3,'and',f4]

        fields = ()
        crResult = self.sfTool.query(CASE_OBJ, where, sc='all')

        crList = []
        if crResult not in BAD_INFO_LIST:
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
        (discard, discard, lastReportDate) = self.sfTool.parseLastReportDate(self.contact)
        
        f1 = ['CaseId', '=', cr['Id']]
        f2 = ['Field', '=', 'Status']
        f3 = ['NewValue', 'like', 'Closed%']
        f4 = ['CreatedDate', '>', lastReportDate]

        where = [f1, 'and', f2, 'and', f3, 'and', f4]

        chResult = self.sfTool.query(CASE_HISTORY_OBJ, where, sc='all')


        if chResult in BAD_INFO_LIST:
            cr['closeInfo'] = None
            cr['closeUser'] = None
        elif len(chResult) >= 1:
            chResult.sort(lambda a, b: cmp(a['CreatedDate'], b['CreatedDate']))
            cr['closeInfo'] = chResult[-1]
            # Also, grap the user record of who closed it.
            cr['closeUser'] = self.lookupUserByIdCache(cr['closeInfo']['CreatedById'])
            
        return cr
    ## END getCrClosureInfo
## END class ClosedCrSection

    
def sortBaCrsByPriority(a, b):
    """
    Sort two MODs by their parent CRs (must be included in MOD dict)
    """
    aCr = a[0]
    bCr = b[0]
    
    return sortCRsByPriority(aCr, bCr)
## END sortMODsByPriority(a, b)


def sortCRsByPriority(a, b):
    """
    Compare two CRs by their priority fields
    """
    
    # If priority isn't set, default it to 3 - Medium for sort
    # If expedite priority  isn't set, default it to 2 - No for sort
    aPriority = a.get('Priority', '3')[:1]
    aExpPri = a.get('ExpeditedPriority__c', '2')[:1]

    bPriority = b.get('Priority', '3')[:1]
    bExpPri = b.get('ExpeditedPriority__c', '2')[:1]

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
