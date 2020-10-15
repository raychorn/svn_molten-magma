#!/bin/env python2.3
"""
Business logic specific to a Contact object in salesforce.com
"""
import pprint
import types
import time
from sfAccount import SFAccountTool
from sfUser import SFUserTool
from sfConstant import *
from sfMagma import *

class SFContact(SFMagmaEntity):

    def __init__(self, entity=None, data={}, action=None, sfTool=None,
                 debug=0):
        """
        If an active tool object is not passed in then a connection is created.
        """

        if entity is None:
            entity = CONTACT_OBJ
        SFEntityBase.__init__(self, entity, data=data, action=action,
                              sfTool=sfTool, debug=debug)

        return

    def attachNote(self, title, body):
        """
        Attach a note to this object
        This can later probably move to sfNote as a note may be attached to
        an account, contact, opportunity or contract.
        """
        contactId = self.getData(CONTACT_OBJ)['Id']
    
        noteData = {'Title': title,
                    'Body': body,
                    'ParentId': contactId}
        
        # insert the note
        noteId = self.sfb.create(NOTE_OBJ, [noteData])

        self.sfb.setLog("Attached note to contact %s: %s" \
                        %(contactId, noteData), 'debug')
        # return the notes sfid
        return noteId
    ## END attachNote

class SFContactTool(SFMagmaTool):
    """ This is a subclass of the SFEntityTool to hold any Contact specific
        SOQL query methods and entity linking action methods
    """
    accountTool = SFAccountTool()
    userTool = SFUserTool()

    ####
    # Contact access methods
    ####
    def getContactByEmail(self, email):
        contactInfo = None
        contact = None
        
        where = [['Email', '=', email]]
        queryList = self.query(CONTACT_OBJ, where=where, sc='all')
        if queryList in self.badInfoList:
            msg = "getContactByEmail Result: NO Contact found with Email %s" \
                  %email
            self.setLog(msg, 'debug')
            
        else:
            contactInfo = queryList[0] 

            if len(queryList) > 1:
                msg =  "getContactByEmail Result: Found more than one contact with Email %s" %email
                self.setLog(msg, 'error')
                # later, sort query list and choose mose recently modified.
                #Sort on LastModifiedDate
                queryList.sort(lambda a, b: cmp(a['LastModifiedDate'],
                                                b['LastModifiedDate']))
                

        if contactInfo is not None:
            contactData = { CONTACT_OBJ : contactInfo }
            contact = SFContact(CONTACT_OBJ, contactData, sfTool=self)

        return contact
    ## END getContactByEmail


    def getContactByEmpNum(self, empnum):
        contactInfo = SFMagmaTool.getContactByEmpNum(self, empnum)
        if contactInfo in self.badInfoList:
            contact = None
        else:
            contactData = { CONTACT_OBJ : contactInfo }
            contact = SFContact(CONTACT_OBJ, contactData, sfTool=self)

        return contact
    ## END getContactByEmpNum
    
    ###
    # Lead entity access methods
    ###
    def getLeadsByOwner(self, OwnerId):
        """
        fetches all Leads owned by specified entity
        Returns list of lead dictionaries
        """
        result=[]

        # is owner valid? 
        if OwnerId[:3] not in LEAD_OWNER_SIG:
            print 'ID is not a valid user or Queue ID'
            print '  %s should start with %s'%(OwnerId, LEAD_OWNER_SIG)
            return None
        
        where = [['OwnerId', '=', OwnerId]]
        queryList = self.query(LEAD_OBJ, where=where, sc='fields')

        if queryList in self.badInfoList:
            print 'getLeadsByOwner Result: NO Lead found having owner %s' \
                  %OwnerId
            return result

        for info in queryList:
            result.append(info)
            print 'Found Lead: %s %s\towned by %s' \
                  %(info.get('FirstName',''), info.get('LastName'),
                    info.get('OwnerId'))
            
        print 'Found %s Leads'%(len(result))
        return result
    ## END getLeadsByOwner

    def matchLeadToContact(self, leadData):
        """
        given a dictionary of a single lead, try to find a matching contact
        by looking for an exact match on email address. If a match cannot be
        found, then create a new contact and transfer the lead's information
        onto the new contact.

        Then, after finding or creating a contact, if the lead has a
        description, trasnfer the content of the lead description field into
        a note attached to the contact.

        Returns: Reference to created/correlated contact object, the action
        performed as a string, and a list of potential account Ids that this
        contact could belong to (always empty if we updated a contact)
        """
        contact = None
        accountIdCandidates = []

        if leadData.has_key('Email'):
            # Try to find existing contact by email
            contact = self.getContactByEmail(leadData['Email'])
            contactAction = "update"

        if contact in self.badInfoList:
            print "No contact found for lead %s" %leadData.get('Email',
                                                               leadData['Id'])
            
            contact, accountIdCandidates = self.createContactFromLead(leadData)
            contactAction = "create"
        else:
            print "Found contact %s" %contact

        if contact is not None:
            # Note the lead's description on the contact we found or created.
            if leadData.has_key('Description'):
                descr = leadData['Description']
                title = leadData.get('LeadSource', 'Description from Lead')
                noteId = contact.attachNote(title, descr)
                pass

            # create any campaign links the lead may have had on the contact
            contactData = contact.getData('Contact')
            self.moveLeadCampaignMemberToContact(leadData['Id'], contactData['Id'])
            
            # Remove the lead
            self.deleteLead(leadData['Id'])

        # Return data to allow notification
        return contact, contactAction, accountIdCandidates
    ## END matchLeadToContact

    def createContactFromLead(self, leadData):
        """
        Given the data structure of a lead, creates a contact based upon the
        lead and attempts to find an account to associate contact with based
        on the lead's email address domain.

        Returns the created contact object and the list of candidate account
        IDs that were considered for the new contact.
        """
        contactInfo = {}

        # sanity check and populate contact fields from the lead fields
        leadContactMap = {'LastName': 'LastName',
                          'FirstName': 'FirstName',
                          'Salutation': 'Salutation',
                          'Title': 'Title',
                          'LeadSource': 'LeadSource',
                          'Street': 'MailingStreet',
                          'City': 'MailingCity',
                          'State': 'MailingState',
                          'PostalCode': 'MailingPostalCode',
                          'Country': 'MailingCountry',
                          'Email': 'Email',
                          'Phone': 'Phone',
                          'MobilePhone': 'MobilePhone',
                          'HasOptedOutOfEmail': 'HasOptedOutOfEmail',
                          }
                          

        for leadKey in leadContactMap.keys():
            contactKey = leadContactMap[leadKey]
            
            if leadData.has_key(leadKey):
                contactInfo[contactKey] = leadData[leadKey]


        # Find Account ID from Email Address
        # First, get all accounts this contact may fit into (for notification)
        # Next, determine the top account to assign this contact to
        # and set contact owner to be the same as that account's owner
        accountId = None
        accountIdCandidates = self.accountTool.findAccountIdCandidatesFromEmail(leadData.get('Email',''))
        topAccountIds = self.accountTool.findTopAccountIdsFromCandidates(accountIdCandidates)
        if len(topAccountIds) > 0:
            accountId = topAccountIds[0]
        
        if accountId is not None:
            contactInfo['AccountId'] = accountId

            ownerId = self.accountTool.findAccountOwnerId(accountId)
            if ownerId is not None and \
                   self.userTool.isActiveUserId(ownerId) is True:
                # Owner ID is set and is an active SF user
                contactInfo['OwnerId'] = ownerId
                # otherwise contact will be owned by script runner

        # create contact using contact tool obj
        try:
            contactId = self.create(CONTACT_OBJ, contactInfo)[0]
            # retrieve the newly created contact
            ret = self.retrieve([contactId], CONTACT_OBJ)
            if ret == 'fail':
                msg = "createContactFromLead: Couldn't fetch contact with ID %s" %contactId
                self.setLog(msg, 'error')
                contact = None
            else:
                contactData = { CONTACT_OBJ: ret[0] }
                contact = SFContact(CONTACT_OBJ, data=contactData, sfTool=self)

        except Exception, e:
            # something in the create failed
            msg = "createContactFromLead: Contact Creation Failed - %s %s" \
                  %(Exception, e)
            self.setLog(msg, 'error')
            contact = None

        # return the contact object after we create it
        return contact, accountIdCandidates
    
    ## END createContactFromLead

    def deleteLead(self, leadId):
        """
        Delete the lead having given ID
        """
        global LEAD_SIG
        res = None
        
        if leadId[:3] == LEAD_SIG:
            res = self.delete([leadId])
            pass

        return res
    ## END deleteLead

    def moveLeadCampaignMemberToContact(self, leadId, contactId):
        """
        find all campaign links from the given Id and create a corresponding links to the
        given contact Id
        """
        fields = ('Id', 'CampaignId', 'HasResponded', 'Status')
        where = [['LeadId','=',leadId]]

        res = self.query('CampaignMember', where, fields)

        if res in BAD_INFO_LIST:
            res = []
            pass
        
        for member in res:
            newMemberData = {'CampaignId': member.get('CampaignId'),
                             'Status': member.get('Status'),
                             'ContactId': contactId}

            ret = self.create('CampaignMember', newMemberData)
            
            continue
        
        return
    ## END moveLeadCampaignMemberToContact
                
    

    def getAllMagmaContacts(self, retFldList=None):
        """
        Fetch all contacts (not having a contact status of Inactive)
        with one of the Magma account Ids

        WARNING - this will break when we get > 2000 contacts. Need to
        implement the Get More functionality at a lower level...
        """

        # get list of Magma account IDs - Good candidate for separate method
        # getAllMagmaAccounts
        magmaAcctIds = []
        AcctIdSOQL = "select Id from Account where Type = 'Magma'" 
        queryList = self.query(ACCOUNT_OBJ, soql=AcctIdSOQL)
        if queryList not in BAD_INFO_LIST:
            for acctRec in queryList:
                magmaAcctIds.append(acctRec['Id'])

        
        magmaAcctWhereList = []
        for magmaAcctId in magmaAcctIds:
            magmaAcctWhereList.append("AccountId = '%s'" %magmaAcctId)
            


        magmaAcctWhereClause = " or ".join(magmaAcctWhereList)

        magmaContactWhere = "ContactStatus__c != 'Inactive' and (%s)" \
                             %magmaAcctWhereClause

        if retFldList == None:
            queryList = self.query(CONTACT_OBJ, where=magmaContactWhere, sc='fields')
        else:
            fieldClause = ", ".join(retFldList)
            magmaContactSOQL = "select %s from %s where %s" \
                               %(fieldClause, CONTACT_OBJ, magmaContactWhere)
            queryList = self.query(CONTACT_OBJ, soql=magmaContactSOQL)
            

        if queryList in BAD_INFO_LIST:
            queryList = []

        return queryList
    ## END getAllMagmaContacts

