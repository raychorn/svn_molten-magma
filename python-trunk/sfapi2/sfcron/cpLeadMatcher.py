#!/bin/env python2.3
"""
Class and script to scour leads in the Customers and Prospects queue
"""

import pprint
import sets
import cStringIO

from sfMagma import *
from sfContact import *
from sfConstant import *
from sfAccount import SFAccountTool
from sfUser import SFUserTool
from sop import SFSOP
import mail

CP_QUEUE_ID = '00G30000000fyFfEAI' # the Customers & Prospects Queue
DEFAULT_USER_ID = '00530000000cBrzAAE'
SF_WEB_URL = 'https://na1.salesforce.com'
FROM_EMAIL = 'sfscript@molten-magma.com'

class LeadNotificationSOP(SFSOP):
    maxObjAge = 60*60*24*1000 # ~ 3 years in seconds
    lastUpdate = 0
    lastEntity = ''
    resetStale = False

    def filename(self):
        # this is where the data will be pickled to
        return '/home/sfscript/data/sfapi/leadNotification.pickle'

    def __init__(self):
        SFSOP.__init__(self)
## END class LeadNotificationSOP


class LeadNotificationCache:
    cache = LeadNotificationSOP()
    debug = 0
    #####################################################################
    #  Basic local caching of entiy information for quick access,
    #  Non volitile info like User/Contact info
    #####################################################################
    def getCache(self, key, data={}, reset=False):
        """
        main accessor for getting cache information
        """
        if self.debug > 2: print 'Load status for %s loaded %3d secs ago' %(key, self.cache.getAge(key))
        if reset: self.cache.reset(True)
        if self.cache.isStale(key):
            if self.debug > 2: print 'Updating SOP for %s' %key
            self.setCache(key, data)
            if reset: self.cache.reset(False)
        return self.cache.getData(key)
    ## END getCache
    
    def setCache(self, key, data={}):
        """ load the latest data for the key into a simple object
        persitence dictionary
        """
        st = time.time()
        if data in [None,{},[],'']:
            data = {'loadStatus':'new'}
        
        if self.debug > 3: print '%2d sec Got %s keys and in %s' %(time.time()-st, len(data.keys()), key)
        self.cache.setData(key, data)
        self.cache.commit() 
        return
    ## END setCache
## END LeadNotificationCache

class CPLeadMatcher(LeadNotificationCache):
    user_obj = 'User'

    def __init__(self, contactTool=None):

        if contactTool is None:
            contactTool = SFContactTool()

        self.cTool = contactTool
        self.uTool = SFUserTool()
        self.aTool = SFAccountTool()

        self.leads = []

        # init the notification queues
        self.priUpd = {}
        self.priNew = {}
        self.auxNew = {}
        return
    ## END __init__
    
    
    def fetchAllCPLeads(self):
        """
        Gets all leads in the customers and prospects queue
        """
        global CP_QUEUE_ID
        
        leadList = self.cTool.getLeadsByOwner(CP_QUEUE_ID)
        self.leads = leadList
        return
    ## END fetchAllCPLeads


    def dictList(self, map, key, value):
        """
        add a value to a dictionary of lists
        """
        if map.has_key(key):
            map[key].append(value)
        else:
            map[key] = [value]

        return
    ## END dictList
    

    def collectLeadNotif(self, contact, action, accountCandidates):
        contactData = contact.getData(CONTACT_OBJ)
        primaryAccountId = contactData.get('AccountId','Default')

        # Pull the primary account ID from the candidate list
        if primaryAccountId in accountCandidates:
            accountCandidates.remove(primaryAccountId)
            pass

        # get the primary account owner
        if primaryAccountId != "Default":
            owner = self.getAccountListOwners([primaryAccountId])[0]
        else:
            owner = DEFAULT_USER_ID

        # get the dictionaries from the cache
        priUpd = self.getCache('priUpd')
        priNew = self.getCache('priNew')
        auxNew = self.getCache('auxNew')

        if action == "update":
            self.dictList(priUpd, owner, contactData)
        elif action == "create":
            self.dictList(priNew, owner, contactData)

        # handle auxiliary account owners
        if len(accountCandidates):
            auxOwnerList = self.getAccountListOwners(accountCandidates)
            for userId in auxOwnerList:
                if userId == owner:
                    # skip same owner as primary account
                    continue
                self.dictList(auxNew, userId, contactData)
                continue
            pass

        # set the changed dictionaries back into the cache
        self.setCache('priUpd', priUpd)
        self.setCache('priNew', priNew)
        self.setCache('auxNew', auxNew)
                
        return
    ## END collectLeadNotif
            
    
    def getAccountListOwners(self, accountIdList):
        """
        Given a list of accounts, get back a list of owning user IDs
        """
        accountRet = self.cTool.retrieve(accountIdList, ACCOUNT_OBJ)
        
        ownerIdUniq = {}
        for accountData in accountRet:
            ownerId = accountData['OwnerId']
            ownerIdUniq[ownerId] = ownerId
            continue
        
        return ownerIdUniq.keys()
     ## END getAccountListOwners
     
         
    def sendNotifications(self):
        ##Collect the set of unique account owner IDs.
        ## Generate a report for each

        # get the dictionaries from the cache
        priUpd = self.getCache('priUpd')
        priNew = self.getCache('priNew')
        auxNew = self.getCache('auxNew')

        ownerIdSet = sets.Set(priUpd.keys())
        ownerIdSet = ownerIdSet.union(priNew.keys())
        ownerIdSet = ownerIdSet.union(auxNew.keys())
        ownerIdSet.discard('loadStatus')
        for ownerId in ownerIdSet:
            notification = LeadNotification(ownerId,
                                            priUpd.get(ownerId, []),
                                            priNew.get(ownerId, []),
                                            auxNew.get(ownerId, []),
                                            self.uTool, self.aTool)
            notification.send()

            if priUpd.has_key(ownerId):
                del  priUpd[ownerId]
                self.setCache('priUpd', priUpd)

            if priNew.has_key(ownerId):
                del  priNew[ownerId]
                self.setCache('priNew', priNew)

            if auxNew.has_key(ownerId):
                del  auxNew[ownerId]
                self.setCache('auxNew', auxNew)
                
            continue

        return
    ## END sendNotifications
            
    def processLeads(self):
        self.fetchAllCPLeads()
        count = 0
        for lead in self.leads:
            count += 1
            # if count > 1: break # for debug
            contact, action, acctCandidates = self.cTool.matchLeadToContact(lead)
            if contact is not None:
                print "%s: %s" %(action, contact.getData(CONTACT_OBJ)['Id'])
                self.collectLeadNotif(contact, action, acctCandidates)

            continue
        # uncomment for real run...
        self.sendNotifications()

        return
    ## END processLeads
## END class CPLeadMatcher


class LeadNotification(LeadNotificationCache):

    def __init__(self, userId, priUpdList, priNewList, auxNewList,
                 userTool=None, accountTool=None):
        """
        userId - ID of user owning the accounts all contacts belong to.
        priUpdList - list of existing contacts in accounts owned by the user
                     that we have annotated
        priNewList - list of new contacts we created in accounts owned by
                     the user.
        auxNewList - list of new contacts created in a top level account that
                     could belong to a sub account owned by the user.
        """

        if userTool is None:
            userTool = SFUserTool()
        self.uTool = userTool

        if accountTool is None:
            accountTool = SFAccountTool()
        self.aTool = accountTool

        self.userId = userId
        self.userData = self.uTool.getUserDataById(self.userId)
        self.defaultUserData = self.uTool.getUserDataById(DEFAULT_USER_ID)
        
        # later, check if userData is None or user is not active, add note
        # accordingly and send to default user
        
        self.priUpdList = priUpdList
        self.priNewList = priNewList
        self.auxNewList = auxNewList

        self.body = cStringIO.StringIO()

        self.generateBody()

        self.subject = "Updated contacts from leads"

        return
    ## END __init__


    def generateHeader(self):
        preheader = None
        if self.userData is None:
            # This case should never happen..
            preheader = """\
Could not look up the user having the ID %s who owns the account(s) that
contain the following contacts.
Please assign the accounts to an active user and forward this
message to that user.
""" %self.userId
        elif self.uTool.isActiveUserId(self.userId) is False:
            # inactive user owns accounts. Send to default user and request fix

            preheader = """\
The user who owns the accounts that contain the following contacts,
%s %s (%s/%s) is inactive.
Please assign the accounts to an active user and forward this
message to that user.
""" %(self.userData.get('FirstName', ''), self.userData['LastName'],
      SF_WEB_URL, self.userData['Id'])


        header = """\
New leads have been imported into Salesforce from a recent Magma event.
As a result, some contacts on accounts that you care about have been
changed or created."""

        if preheader is not None:
            header = "%s\n%s" %(preheader, header)


        return header
    ## END generateHeader

    def send(self):
        if self.uTool.isActiveUserId(self.userId) is False:
            # have to send to alternate address
            toAddr = self.defaultUserData['Email']
        else:
            # can send to user address
            toAddr = self.userData['Email']

        ## FOR DEBUG:
        #toAddr = self.defaultUserData['Email']
        #bccAddr = 'kshuk@molten-magma.com'
        bccAddrs = ['kshuk@molten-magma.com', 'aila@molten-magma.com']
        
        message = mail.Message(FROM_EMAIL, toAddr, self.body.getvalue(),
                               self.subject, bccAdds=bccAddrs)
                               
        mailserver = mail.MailServer()
        mailserver.sendEmail(message)
    ## END send
        
    def generateBody(self):
        """
        Build the notification report
        """
        hdr = self.generateHeader()
        if hdr is not None:
            self.body.write("%s\n\n" %hdr)
        
        sect = self.buildPriUpdSection()
        if len(sect):
            self.body.write(sect)

        sect = self.buildPriNewSection()
        if len(sect):
            self.body.write(sect)

        sect = self.buildAuxNewSection()
        if len(sect):
            self.body.write(sect)

        pass
    ## END generate

    def buildPriUpdSection(self):
        title = "Annotated Contacts in Accounts You Own"
        blurb = """\
New leads have matched these contacts, so we added a note to each contact with
the matching lead's description."""
        section = self.formatSection(self.priUpdList, title, blurb)
        return section

    def buildPriNewSection(self):
        title = "New Contacts Created in Accounts You Own"
        blurb = """\
These contacts were created based upon newly imported leads."""
        section = self.formatSection(self.priNewList, title, blurb)
        return section

    def buildAuxNewSection(self):
        title = "New Contacts Created that May Belong in One of Your Accounts"
        blurb = """\
Since we cannot reliably determine the level in an account hierarchy
where a new contact should be placed, we created these contacts at the
highest level account. You own an account that, based on email address, may
also be a match for some of the contacts below."""
        section = self.formatSection(self.auxNewList, title, blurb)
        return section

    def formatSection(self, contactDataList, title, blurb):
        section = cStringIO.StringIO()
        if len(contactDataList):
            section.write("-"*72 + "\n")
            section.write("%s\n" %title)
            if len(blurb):
                section.write("\n%s\n" %blurb)
            section.write("-"*72 + "\n\n")

            for contactData in contactDataList:
                section.write("%s\n" %self.formatContactLineItem(contactData))
                
            section.write("\n\n")
        return section.getvalue()


    def formatContactLineItem(self, contactData):
        """
        general format for a line of the report.
        """
        contactUrl = "%s/%s" %(SF_WEB_URL, contactData['Id'])
        name = "%s %s" %(contactData.get('FirstName', ''),
                         contactData['LastName'])
        contactInfoList = [name.strip()]

        # get title if set
        if contactData.has_key('Title'):
            contactInfoList.append(contactData['Title'])

        # If contact has an account, get the name
        if contactData.has_key('AccountId'):
            accountData = self.aTool.getAccountDataById(contactData['AccountId'])
            contactInfoList.append(accountData['Name'])
        
        line = "%s\n\t%s\n" %('; '.join(contactInfoList), contactUrl)
        line = line.encode('ascii','replace')

        return line
    ## END formatContactLineItem
## END class LeadNotification

    
def main():
    cplm = CPLeadMatcher()
    cplm.processLeads()
        
if __name__ == "__main__":
    main()
