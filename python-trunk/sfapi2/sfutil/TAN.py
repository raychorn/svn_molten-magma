#!/usr/bin/env python2.3
"""
Process a Termination Action Notice given a Salesforce user id

Actions to take:

Get the subject's user record and contact record

Get the subject's Reassign To User ID (check for)

Get the reassign user's user record and contact record

Get lookup list of case record types

Reparent all open Cases

Reparent any non-merged task branches
    Reparent any BAs owned by the subject on these task branches


Set any contacts where
    Reassign To targets the subject user
    Branches Approved By targets the subject user
    Reports To targets the subject contact
"""

sfUrl = 'https://na1.salesforce.com'

import pprint
import sys
import textwrap
from optparse import OptionParser

from sfMagma import *
from sfConstant import *
from sfUtil import *


class TanTool(SFMagmaTool):
    logname = 'TANtool'
    trial = False
    debug = False

    def updateObject(self, entity, data):
        """Nifty wrapper for doing updates
        """
        objId = data.get('Id', None)
        if objId is None:
            msg = "updateObject: data map doesn't contain Id field. EXITING."
            self.setLog(msg, 'error')
            print msg
            sys.exit(1)
            pass

        if self.debug is True:
            print "trial = %s; Updating %s %s: \n%s" %(self.trial, entity,
                                                       objId,
                                                       pprint.pformat(data))

        if self.trial is True:
            ret = [objId]
        else:
            ret = self.update(entity, data)
            
        if ret in BAD_INFO_LIST:
            msg = "shutdownUser: update of %s %s failed. Data follows:\n%s" \
                  %(entity, objId, pprint.pformat(data))
            print msg
            self.setLog(msg, 'error')
            pass
        return ret[0]
    
    def reparentObject(self, entity, objId, newOwnerId):
        """Reparent any object
        """
        data = {'Id': objId,
                'OwnerId': newOwnerId}
        
        ret = self.updateObject(entity, data)
        return ret
    ## END reparentObject


    def getObjInfo(self, entity, objId):
        """
        Wrapper to fetch an entire record
        """
        objInfo = {}
        ret = self.retrieve([objId], entity)
        if ret in BAD_INFO_LIST:
            msg = "Retrieve of %s %s failed" %(entity, objId)
            print msg
            self.setLog(msg, 'error')
        else:
            objInfo = ret[0]

        return objInfo
    ## END getObjInfo


    def getEntityRecordTypes(self, entity):
        """
        Return a dictionary of record type IDs and their names for a specified
        entity type
        """
        soql = "select Id, Name from RecordType where TableEnumOrId = '%s'" %entity
        ret = self.query('RecordType', soql=soql)
        objInfo = {}
        if ret in BAD_INFO_LIST:
            msg = "Couldn't find any record types for %s entity" %entity
            print msg
            self.setLog(msg, 'error')
        else:
            for recType in ret:
                objInfo[recType['Id']] = recType['Name']
                continue
            pass
        return objInfo
    ## END getEntityRecordTypes


    def getActorInfo(self, userId):
        """
        Gets the user info and contact info for a user Id
        """
        userInfo = self.getObjInfo('User', userId)
        contactId = userInfo.get('User_Contact_Id__c', None)

        if contactId is not None:
            contactInfo = self.getObjInfo('Contact', contactId)
            
        else:
            msg = "Could not find corresponding contact id for user %s" %userId
            print msg
            self.setLog(msg, 'error')
            contactInfo = {}
            pass

        return userInfo, contactInfo
    ## END getActorInfo


    def shutdownUser(self):
        """
        flips any necessary switches to deactivate the subject user
        isActive -> False
        Ex_Employee_c -> True
        """
        userInfo = self.subjectUser
        data = {}
        
        if userInfo.get('IsActive', True) is not False:
            data['IsActive'] = False
            pass

        if userInfo.get('Ex_Employee__c', False) is not True:
            data['Ex_Employee__c'] = True
            pass
            
        if len(data):
            data['Id'] = userInfo.get('Id')
            ret = self.updateObject('User', data)
            pass
        
        return ret
    ## END shutdownUser


    def shutdownContact(self):
        """
        flips any necessary switches to deactivate the subject contact
        ContactStatus__c -> Inactive
        PR_Frequency__c -> ''
        PR_CR_Detail_Level__c -> ''
        PR_Branch_Detail_Level__c -> ''
        """
        contactInfo = self.subjectContact
        contactId = contactInfo.get('Id')
        
        data = {'Id': contactId}
        data['ContactStatus__c'] = 'Inactive'
        data['PR_Frequency__c'] = ''
        data['PR_CR_Detail_Level__c'] = ''
        data['PR_Branch_Detail_Level__c'] = ''

        if contactInfo.get('FirstName','')[-2:] != '-x':
            data['FirstName'] = "%s-x" %contactInfo.get('FirstName','')

        if contactInfo.get('LastName','')[-2:] != '-x':
            data['LastName'] = "%s-x" %contactInfo.get('LastName','')

        ret = self.updateObject('Contact', data)

        return ret
    ## END shutdownContact

    def reassignOpenCases(self):
        actionList = []
        subjectUserId = self.subjectUser.get('Id')

        subjectUserName = "%s %s" %(self.subjectUser.get('FirstName',''),
                                    self.subjectUser.get('LastName'))
        subjectUserName = subjectUserName.strip()
        targetUserId = self.targetUser.get('Id')

        caseTypes = self.getEntityRecordTypes('Case')

        soql = "select Id, RecordTypeId, CaseNumber, Subject, Status, Tag__c from Case where OwnerId = '%s' and IsClosed = False" %subjectUserId
        ret = self.query('Case', soql=soql)
        if ret in BAD_INFO_LIST:
            msg = "Couldn't find any open cases owned by %s" %subjectUserId
            print msg
            self.setLog(msg, 'warn')
            return actionList

        for case in ret:
            tag = case.get('Tag__c','').rstrip('\n')
            if len(tag) > 0:
                tag += '\n'
                pass
            tag += 'Reassigned from %s\n' %subjectUserName
            
            data = {'Id': case['Id'],
                    'OwnerId': targetUserId,
                    'Tag__c': tag}

            res = self.updateObject('Case', data)
            
            #res = self.reparentObject('Case', case['Id'], targetUserId)
            if res[:15] == case['Id'][:15]:
                caseNum = case.get('CaseNumber').lstrip('0')
                recTypeId = case.get('RecordTypeId','')
                recType = caseTypes.get(recTypeId, 'Case')
                subjectList = textwrap.wrap(case.get('Subject','No Subject'))
                subject = '\n'.join(subjectList)
                status = case.get('Status','Unknown')

                descr = "%s %s; Status: %s\n%s" %(recType, caseNum, status, subject)
                actionList.append({'id': case['Id'], 'descr': descr})
                pass
            continue
        return actionList
    ## END reassignOpenCases

    def reassignUnmergedBranches(self):
        """Reparents any branches which are not Merged - Testing along with any BAs
        on the branch owned by the subject.
        """
        actionList = []
        subjectUserId = self.subjectUser.get('Id')
        targetUserId = self.targetUser.get('Id')

        soql = "Select Id, Name, Branch_Status__c, Code_Stream__c, Num_CRs__c from Task_Branch__c where OwnerId = '%s' and Branch_Status__c != 'Merged'" %subjectUserId
        ret = self.query('Task_Branch__c', soql=soql)
        if ret in BAD_INFO_LIST:
            msg = "Couldn't find any unmerged task branches owned by %s" %subjectUserId
            print msg
            self.setLog(msg, 'warn')
            return actionList

        tbidList = []
        for tb in ret:
            res = self.reparentObject('Task_Branch__c', tb['Id'], targetUserId)
            if res[:15] == tb['Id'][:15]:
                tbidList.append(tb['Id'])
                tbstatus = tb.get('Branch_Status__c','Open')
                if tbstatus == 'Open':
                    # don't notify about "shell" branches
                    continue
                tbname = tb.get('Name','No Task Branch Name')
                tbstream = tb.get('Code_Stream__c','No Code Stream')
                tbnumcrs = int(float(tb.get('Num_CRs__c','0')))
                descr = "%s in stream %s on %s CR(s)\nStatus: %s" %(tbname, tbstream, tbnumcrs, tbstatus)
                actionList.append({'id': tb['Id'], 'descr': descr})
                pass
            continue

        self.reassignBAs(tbidList)

        return actionList
    ## END reassignUnmergedBranches

    def reassignBAs(self, tbList):
        """
        Reassign BAs on the branches we found.
        """
        sliceSize = 15
        
        subjectUserId = self.subjectUser.get('Id')
        targetUserId = self.targetUser.get('Id')

        f1 = ['OwnerId', '=', subjectUserId]

        baList = []
        while len(tbList):
            selectIds = tbList[:sliceSize]
            tbList = tbList[sliceSize:]

            sfList = []
            for id in selectIds:
                sfList.append(['Task_Branch__c','=',id])
                sfList.append('or')
                continue
            sfList.pop() # nuke the last or

            where = [f1, 'and', '(']
            where.extend(sfList)
            where.append(')')

            ret = self.query('Branch_Approval__c', where=where, sc='min')
            if ret not in BAD_INFO_LIST:
                baList.extend(ret)
                pass
            continue

        for ba in baList:
            res = self.reparentObject('Branch_Approval__c', ba['Id'], targetUserId)
            continue

        return
    ## END reassignBAs
        
    def reassignAccount(self):
        actionList = []
        f1 = ['OwnerId', '=', self.subjectUserId]
        where = [f1]
        fields = ('Id','OwnerId', 'Name', 'Site')
        ret = self.query('Account', where=where, sc=fields)

        if ret in BAD_INFO_LIST:
            msg = "Couldn't find any accounts owned by %s" %self.subjectUserId
            print msg
            self.setLog(msg, 'warn')
            return actionList

        for acct in ret:
            res = self.reparentObject('Account', acct['Id'],
                                      self.targetUserId)
            if res[:15] == acct['Id'][:15]:
                acctName = acct['Name']
                acctSite = acct.get('Site','')
                if len(acctName):
                    descr = "%s" %(acctName)
                else:
                    descr = "%s - %s" %(acctName, acctSite)
                    pass
                actionList.append({'id': acct['Id'], 'descr': descr})
                pass
            continue
        return actionList
    ## END reassignAccounts

    def reassignOpportunity(self):
        actionList = []
        f1 = ['OwnerId', '=', self.subjectUserId]
        f2 = ['IsClosed', '=', False]
        where = [f1, 'and', f2]
        fields = ('Id','OwnerId', 'Name')
        ret = self.query('Opportunity', where=where, sc=fields)

        if ret in BAD_INFO_LIST:
            msg = "Couldn't find any open opportunities owned by %s" \
                  %self.subjectUserId
            print msg
            self.setLog(msg, 'warn')
            return actionList

        for opp in ret:
            res = self.reparentObject('Opportunity', opp['Id'],
                                      self.targetUserId)
            if res[:15] == opp['Id'][:15]:
                oppName = opp['Name']
                descr = "%s" %(oppName)
                actionList.append({'id': opp['Id'], 'descr': descr})
                pass
            continue
        return actionList
    ## END reassignOpportunity

    def reassignContact(self):
        actionList = []
        f1 = ['OwnerId', '=', self.subjectUserId]
        where = [f1]
        fields = ('Id','OwnerId', 'FirstName', 'LastName', 'Email')
        ret = self.query('Contact', where=where, sc=fields)

        if ret in BAD_INFO_LIST:
            msg = "Couldn't find any contacts owned by %s" %self.subjectUserId
            print msg
            self.setLog(msg, 'warn')
            return actionList

        for contact in ret:
            res = self.reparentObject('Contact', contact['Id'],
                                      self.targetUserId)
            if res[:15] == contact['Id'][:15]:
                contactFName = contact.get('FirstName','')
                contactLName = contact.get('LastName','')
                contactEmail = contact.get('Email','')
                descr = "%s %s" %(contactFName, contactLName)
                descr = descr.lstrip()
                if len(contactEmail):
                    descr += " (%s)" %contactEmail
                actionList.append({'id': contact['Id'], 'descr': descr})
                pass
            continue
        return actionList
    ## END reassignContact
        
    def reassignUnconvLead(self):
        actionList = []
        f1 = ['OwnerId', '=', self.subjectUserId]
        f2 = ['IsConverted', '=', False]
        where = [f1, 'and', f2]
        fields = ('Id','OwnerId', 'FirstName', 'LastName', 'Email', 'Company')
        ret = self.query('Lead', where=where, sc=fields)

        if ret in BAD_INFO_LIST:
            msg = "Couldn't find any unconverted leads owned by %s" \
                  %self.subjectUserId
            print msg
            self.setLog(msg, 'warn')
            return actionList

        for lead in ret:
            res = self.reparentObject('Lead', lead['Id'],
                                      self.targetUserId)
            if res[:15] == lead['Id'][:15]:
                leadFName = lead.get('FirstName','')
                leadLName = lead.get('LastName','')
                leadCo = lead.get('Company','')
                leadEmail = lead.get('Email','')
                descr = "%s %s" %(leadFName, leadLName)
                descr = descr.lstrip()
                if len(leadCo):
                    descr += ", %s" %leadCo
                if len(leadEmail):
                    descr += " (%s)" %leadEmail
                actionList.append({'id': lead['Id'], 'descr': descr})
                pass
            continue
        return actionList
    ## END reassignContact

    def buildActionReport(self, actionMap):
        global sfUrl
        order = ('Cases','Branches','Accounts','Contacts','Opportunities',
                 'Leads')
        buf = cStringIO.StringIO()

        su = self.subjectUser
        tu = self.targetUser

        salutation = '%s,' %tu.get('FirstName')
        header = "As the Salesforce.com account for %s %s has been deactivated, and since you are listed as the Reassign To contact of record for that person, we are reassigning the following objects to you:" %(su.get('FirstName'), su.get('LastName'))
        if self.trial is True:
            header = "As the Salesforce.com account for %s %s has been deactivated, we need to reassign this user's salesforce objects (listed below). You are listed as the reassign-to person for this user's objects - should we reassign these objects to you, or should someone else receive them. Please let us know as soon as possible." %(su.get('FirstName'), su.get('LastName'))
        
        headerlist = textwrap.wrap(header)
        header = '\n'.join(headerlist)
        header += '\n\nRegards,\n'
        header += 'The Magma Salesforce Support team\n'

        opening = False
        for entity in order:
            if actionMap.has_key(entity) and len(actionMap[entity]):

                if opening is False:
                    buf.write("%s\n\n" %salutation)
                    buf.write("%s\n\n" %header)
                    opening = True
                    pass

                secheader = "%s reassigned to you" %entity
                if self.trial is True:
                    secheader = "%s" %entity
                    pass
                
                buf.write("%s\n\n" %secheader.upper())
                for item in actionMap[entity]:
                    url = "%s/%s" %(sfUrl, item['id'])
                    buf.write("%s\n\t%s\n\n" %(item['descr'].encode('ascii','replace'), url))
                    continue
                
                buf.write("-"*75 + "\n"*3)
                pass
            continue

        actionTxt = buf.getvalue()
        return actionTxt.encode('ascii','replace')

    def tanFlow(self, subjectUserId):
        """
        Main flow for managing a TAN for the supplied user ID
        """
        # sanity check the user ID
        if len(subjectUserId) == 15:
            subjectUserId = convertId15ToId18(subjectUserId)
            pass

        if len(subjectUserId) != 18:
            msg = "User ID %s is invalid. EXITING" %subjectUserId
            print msg
            sys.exit(1)
            pass

        # get the subject info
        self.subjectUser, self.subjectContact = self.getActorInfo(subjectUserId)

        # get the target info
        targetUserId = self.subjectContact.get('Reassign_To_User_ID__c',None)
        if targetUserId is None:
            # handle no reassign to user ID
            msg = "Subject user does not have a Reassign To User ID set on his or her contact record\n"
            msg += "Please correct this before continuing."
            print msg
            sys.exit()

        self.targetUser, self.targetContact = self.getActorInfo(targetUserId)
        self.subjectUserId = self.subjectUser.get('Id')
        self.targetUserId = self.targetUser.get('Id')

        actionMap = {}
        actionMap['Cases'] = self.reassignOpenCases()
        actionMap['Branches'] = self.reassignUnmergedBranches()
        actionMap['Accounts'] = self.reassignAccount()
        actionMap['Contacts'] = self.reassignContact()
        actionMap['Opportunities'] = self.reassignOpportunity()
        actionMap['Leads'] = self.reassignUnconvLead()
        

        self.shutdownUser()
        self.shutdownContact()

        actionText = self.buildActionReport(actionMap)

        print "\n\nTO: %s\n\n" %self.targetUser.get('Email')
        if self.trial is True:
            print "SUBJECT: %s %s's salesforce objects need to be reassigned\n\n" %(self.subjectUser.get('FirstName'), self.subjectUser.get('LastName'))
        else:
            print "SUBJECT: %s %s's salesforce objects now reassigned to you\n\n" %(self.subjectUser.get('FirstName'), self.subjectUser.get('LastName'))
            pass
        
        print actionText


def main():
    op = OptionParser()
    op.add_option('-t', '--trial', dest='trial', default=False,
                  action='store_true', help='Do a dry run')
    op.add_option('-d', '--debug', dest='debug', default=False,
                  action='store_true', help='print debug info')
    
    (opts, args) = op.parse_args()
    
    subjectUserId = args[0]
    
    t = TanTool()
    t.trial = opts.trial
    t.debug = opts.debug
    t.tanFlow(subjectUserId)    

if __name__ == "__main__":
    main()
