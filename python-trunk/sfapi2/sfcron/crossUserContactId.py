#/usr/bin/env python2.3
"""
Manage user and contact ID cross reference for Magma employees.
Also, ensure that Reassign To and Branches Approved By fields are user ID18
and that the corresponding email address fields are updated properly.
"""

import re
import pprint
from optparse import OptionParser

from sfUtil import *
from sfConstant import *
from sfMagma import SFMagmaTool

class crossUserContactTool(SFMagmaTool):
    """Containter class for user/contact xref methods
    """
    logname = 'sf.xuser'

    def __init__(self):
        SFMagmaTool.__init__(self, logname=self.logname)

        self.userRecords = None
        #self.debug = 2
        return

    def fetchAllUsers(self):
        """ Gets all users, active and inactive """
        if self.userRecords is None:
            self.userRecords = []
            where = [['Username','!=','']]
            fields = ('Id','Username', 'FirstName', 'LastName', 'Email',
                      'EmployeeNumber', 'User_Contact_Id__c', 'IsActive')
            res = self.query(USER_OBJ, where=where, sc=fields)
            if res not in BAD_INFO_LIST:
                self.userRecords = res
                pass
            pass
        return self.userRecords
    ## END fetchAllUsers
        

    def buildUserMapById(self):
        users = self.fetchAllUsers()
        userIdMap = {}
        
        for user in users:
            userIdMap[user.get('Id')] = user
            continue
        
        self.userIdMap = userIdMap
        return self.userIdMap
    ## END buildUserMapById
    

    def buildContactMapById(self):
        fields = ('Id', 'FirstName', 'LastName', 'Email', 'Contact_User_Id__c',
                  'Branches_Approved_By__c', 'Branches_Approved_By_User_ID__c',
                  'Reassign_To__c', 'Reassign_To_User_ID__c',
                  'EmployeeNumber__c')

        contacts = self.getAllMagmaContacts(fields)
        contactIdMap = {}
        for contact in contacts:
            contactIdMap[contact['Id']] = contact

        self.contactIdMap = contactIdMap
        return
    ## END buildContactMapById

    def updateContactRecord(self, contactId, userId):
        print "Will update contact %s with user ID %s" \
              %(contactId, userId)
        
        updateMap = {'Id': contactId,
                     'Contact_User_Id__c': userId}

        res = self.update(CONTACT_OBJ, updateMap)
        return
    ## END updateContactRecord


    def updateUserRecord(self, userId, contactId):
        print "Will update user %s with contact ID %s" \
              %(userId, contactId)
        
        updateMap = {'Id': userId,
                     'User_Contact_Id__c': contactId}

        res = self.update(USER_OBJ, updateMap)
        return
    ## END updateUserRecord

    def expandId15ToId18(self):
        """
        Updates user and contact cross reference ID fields that have 15 character IDs
        to 18 character IDs
        """
        self.buildUserMapById()
        self.buildContactMapById()

        for userId in self.userIdMap.keys():
            user = self.userIdMap[userId]
            userId = convertId15ToId18(userId)
            if user.has_key('User_Contact_Id__c'):
                userContactId = user.get('User_Contact_Id__c')
                if len(userContactId) == 15:
                    userContactId = convertId15ToId18(userContactId)
                    self.updateUserRecord(userId, userContactId)
                    pass

                contact = self.contactIdMap.get(userContactId, None)
                if contact is None:
                    print "Contact is None for Id: %s" %userContactId
                    
                if contact is not None and contact.has_key('Contact_User_Id__c'):
                    contactUserId = contact['Contact_User_Id__c']
                    if len(contactUserId) == 15:
                        self.updateContactRecord(userContactId, userId)
                        pass
                    pass
                pass
           
            continue
        return
    ## END expandId15ToId18
    

    def expandContactIDRefFields(self):
        """
        expand the ID in Branches Approved By User ID and Reassign To UserId
        fields to 18 chars.
        """

        self.buildContactMapById()
        self.buildUserMapById()

        for contact in self.contactIdMap.values():
            contactUpdateMap = {}

            if contact.has_key('Reassign_To_User_ID__c'):
                reassignUserId = contact['Reassign_To_User_ID__c']
                if len(reassignUserId) != 18:
                    reassignUserId = convertId15ToId18(reassignUserId[:15])
                    contactUpdateMap['Reassign_To_User_ID__c'] = reassignUserId
                    pass

                user = self.userIdMap.get(reassignUserId, None)
                if user is None:
                    msg = "ERROR - Invalid reassign to user id %s on contact %s" %(reassignUserId, contact['Id'])
                    print msg
                    self.log.error(msg)
                elif contact.get('Reassign_To__c', '') != user['Email']:
                    contactUpdateMap['Reassign_To__c'] = user['Email']
                    pass
                pass
            

            if contact.has_key('Branches_Approved_By_User_ID__c'):
                approvalUserId = contact['Branches_Approved_By_User_ID__c']
                if len(approvalUserId) != 18:
                    approvalUserId = convertId15ToId18(approvalUserId[:15])
                    contactUpdateMap['Branches_Approved_By_User_ID__c'] = approvalUserId
                    pass
                
                user = self.userIdMap.get(approvalUserId, None)
                if user is None:
                    msg = "ERROR - Invalid branches approved by user id %s on contact %s" %(approvalUserId, contact['Id'])
                    print msg
                    self.log.error(msg)
                elif contact.get('Branches_Approved_By__c', '') != user['Email']:
                    contactUpdateMap['Branches_Approved_By__c'] = user['Email']
                    pass
                pass


            if len(contactUpdateMap) > 0:
                contactUpdateMap['Id'] = contact['Id']
                #pprint.pprint(contactUpdateMap)
                res = self.update(CONTACT_OBJ, contactUpdateMap)
                pass
            continue
        return
    ## END expandContactIDRefFields


def xref15to18_main():
    u2cm = crossUserContactTool()
    u2cm.expandId15ToId18()
## END xref15to18_main

def contactRef15to18_main():
    u2cm = crossUserContactTool()
    u2cm.expandContactIDRefFields()
## END contactRef15to18_main



if __name__ == "__main__":
    op = OptionParser()

    op.add_option("-x", "--xrefxpand", dest="xref", action="store_true",
                  default=False,
                  help="Expand user/contact xrefs to ID18")
    op.add_option("-c", "--crefxpand", dest="cref", action="store_true",
                  default=False,
                  help="Expand contact ref fields to ID18, update corresponding informational email address fields.")
    (opts, args) = op.parse_args()
    
    if opts.xref is True:
        xref15to18_main()
        pass

    if opts.cref is True:
        contactRef15to18_main()
        pass
    


