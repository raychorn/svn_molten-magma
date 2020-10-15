#!/usr/bin/env python2.3

import sys
import csv
import re
import pprint
import datetime, time
from optparse import OptionParser

from sfMagma import SFMagmaTool
from sfConstant import *

logName = "sf.crcust"
caseType = 'case'
contactType = 'contact'

class CustContactTool(SFMagmaTool):

    def __init__(self, opts):
        global logName
        SFMagmaTool.__init__(self, logname=logName)

##        # initialize the csv output file
##        hdrRow = ['caseId','caseOwnerId','caseNumber','magmaUserId',
##                  'magmaContactId','custContactId','custAcctId','custPriority']
##        self.csvw = csv.DictWriter(file(outCsv, 'w+'), hdrRow)
##        hdrMap = {}
##        for col in hdrRow:
##            hdrMap[col] = col
##        self.csvw.writerow(hdrMap)

        self.opts = opts

        self.contactIdToAcctIdCache = {}
        self.userContactMap = {}
        self.contactAccountMap = {}
        self.userEmailToIdMap = {}
        self.magmaContactIdMap = {}
        self.magmaUserIdToContactIdMap = {}

        self.userCache = {}
        return
    ## END __init__

    def queryCrs(self):
        """ Query for all CRs which have a contactID
        """
        global caseType

        timeDelta = datetime.timedelta(days=int(self.opts.daysback))
        then = datetime.datetime.now() - timeDelta
        thenISO = self.getAsDateTimeStr(time.mktime(then.timetuple()))
        
        # case is a CR record type
        f1a = ['RecordTypeId','=',RECTYPE_CR]
        f1b = ['RecordTypeId','=',RECTYPE_PVCR]
        f1c = ['RecordTypeId','=',RECTYPE_PLDCR]

        # Contact field isn't empty
        f2 = ['ContactId','!=','']

        f3 = ['LastModifiedDate', '>', thenISO]

        where = ['(',f1a,'or',f1b,'or',f1c,')','and',f2,'and',f3]

        fields = ('Id', 'ContactId', 'CustomerPriority__c',
                  'CreatedById', 'OwnerId', 'CaseNumber')

        res = self.query(CASE_OBJ, where=where, sc=fields)

        if res in BAD_INFO_LIST:
            crs = []
        else:
            crs = res

        self.crs = crs
        return
    ## END queryCrs

    def getMagmaContactIdList(self):
        # get a all magma contact IDs and distill into list
        fields = ('Id','Contact_User_Id__c','Reassign_To_User_ID__c')
        self.magmaContacts = self.getAllMagmaContacts(fields)
        for contact in self.magmaContacts:
            #self.magmaContactIds.append(contact['id'])
            self.magmaContactIdMap[contact['Id']] = contact

            if contact.has_key('Contact_User_Id__c'):
                self.magmaUserIdToContactIdMap[contact['Contact_User_Id__c']] = contact['Id']
                pass
            continue
    ## END getMagmaContactIdList

    def getContactAccountIdCached(self, contactId):
        if self.contactIdToAcctIdCache.has_key(contactId) is False:
            fields = ('Id', 'AccountId')
            contact = self.retrieve([contactId], CONTACT_OBJ, fields)[0]
            self.contactIdToAcctIdCache[contactId] = contact.get('AccountId','')

        return self.contactIdToAcctIdCache[contactId]
    ## END getContactAccountId

    def mapCustomerPriority(self, priority):
        if priority is None:
            priority = ""
        if   re.search(r'Low', priority):
            priority = "4-Low"
        elif re.search(r'Med', priority):
            priority = "3-Med"
        elif re.search(r'High', priority):
            priority = "2-High"
        elif re.search(r'Urgent', priority):
            priority = "1-Tape out Limiting"
        elif re.search(r'Critical', priority):
            priority = "0-Critical"
        elif priority == "":
            pass
        else:
            priority = ""

        return priority
    ## END mapCustomerPriority

    def populateUserCache(self):
        """
        Prestock the entire user cache
        """
        where = [['UserName','!=','']]
        users = self.query(USER_OBJ,where=where)

        for user in users:
            self.userCache[user['Id']] = user
    ## END populateUserCache

    def isUserActive(self, userId):
        """
        Given a user ID, check that this user is active.
        """
        user = self.userCache(userId)
        isactive = user.get('IsActive', False)
        if isactive in ['true', True]:
            isactive = True
        else:
            isactive = False
            pass
        return isactive
    ## END isUserActive

    def populateUserContactMap(self):
        print "Num cached users: %s" %len(self.userCache)
        print "Num entries in uid to cid map %s" %len(self.magmaUserIdToContactIdMap)
        
        for userId in self.userCache.keys():
            user = self.userCache[userId]
            email = user['Email']
            if self.magmaUserIdToContactIdMap.has_key(userId):
                self.userContactMap[userId] = self.magmaUserIdToContactIdMap[userId]
            
            self.userEmailToIdMap[email] = user['Id']

        print "num elements in userContactMap: %s" %len(self.userContactMap)


    def populateContactAccountMap(self):
        alpha = 'abcdefghijklmnopqrstuvwxyz'
        fields = ('Id', 'AccountId')

        contactList = []
        for letter in alpha:
            where = [['AccountId','!=',''],'and',['LastName','like','%s%%' %letter]]
            res = self.query(CONTACT_OBJ, where=where, sc=fields)
            if res not in BAD_INFO_LIST:
                contactList.extend(res)

        for contact in res:
            self.contactAccountMap[contact['Id']] = contact.get('AccountId','')
    ## END populateContactAccountMap

    def processCrs(self):
        """ Main flow
        """
        self.getMagmaContactIdList()
        self.queryCrs()
        self.populateUserCache()
        self.populateUserContactMap()
        self.populateContactAccountMap()

        totalCrs = len(self.crs)
        currCr = 0
        
        softDefault = self.sfc.get('main','default_soft_uid')
        for cr in self.crs:
            currCr += 1
            #print "CR %s of %s" %(currCr, totalCrs)
            if cr.has_key('ContactId') is False:
                continue
            elif not self.magmaContactIdMap.has_key(cr['ContactId']):
                # We have a CR with a customer in the contact field
                custContactId = cr['ContactId']
                crId = cr['Id']

                # Find a reasonable magma contact to fill in.
                # First find valid user
                linkOwnerId = self.cascadeToActiveUser(cr['CreatedById'])
                if linkOwnerId in [None, softDefault]:
                    linkOwnerId = self.cascadeToActiveUser(cr['OwnerId'])

                # if CR is not owned by a queue, find a valid owner for it
                # (who may well be the current owner)
                if cr['OwnerId'][:3] == '00G':
                    crOwnerId = cr['OwnerId']
                else:
                    crOwnerId = self.cascadeToActiveUser(cr['OwnerId'])
                    if crOwnerId is None:
                        crOwnerId = softDefault

                # If not null, this user is the Magma Contact

                print "CR: %s (%s)" %(int(cr['CaseNumber']), crId)
                #print "linkOwnerId: %s" %linkOwnerId
                if linkOwnerId is None:
                    magmaUserId = ""
                    magmaContactId = ""
                else:
                    magmaUserId = linkOwnerId
                    magmaContactId = self.userContactMap.get(linkOwnerId, "")
                    #print "magmaContactId: %s" %magmaContactId
                
                # Look up the customer contact's account ID
                custAcctId = self.getContactAccountIdCached(custContactId)
                #custAcctId = self.contactAccountMap.get(custContactId, "")
                
                # Translate customer priority, if any
                custPriority = self.mapCustomerPriority(cr.get('CustomerPriority__c',
                                                               None))

                # create the CR link.
                data = {'Name': 'Customer Contact Link',
                        'Resolved__c': False,
                        'Account__c': custAcctId,
                        'Parent_CR__c': crId,
                        'Customer_Contact__c': custContactId}

                if custPriority.strip() != '':
                    data['Customer_Priority__c'] = custPriority
                    pass

                
##                pprint.pprint(data)
                res = self.create('CR_Link__c', data)
                if res in BAD_INFO_LIST:
                    msg = "Failed to create CR Link: %s" %pprint.pformat(data)
                    self.setLog(msg, 'error')
                else:
                    msg = "Created CR Link for customer contact on %s" %int(cr['CaseNumber'])
                    self.setLog(msg, 'info')
                    pass

                # update the case
                data = {'Id': crId,
                        'OwnerId': crOwnerId,
                        'ContactId': magmaContactId}

##                pprint.pprint(data)
##                print

                res = self.update(CASE_OBJ, data)
                if res in BAD_INFO_LIST:
                    msg = "Failed to update CR to remove customer contact: %s" \
                          %pprint.pformat(data)
                    self.setLog(msg, 'error')
                else:
                    msg = "Updated CR %s, replacing customer as contact" %int(cr['CaseNumber'])
                    self.setLog(msg, 'info')
                    pass

                pass
            continue
        
        return
    ## END processCrs

## END class CustContact


def main():
    op = OptionParser()

#    op.add_option("-t", "--trial", dest="trial", action="store_true", default=False, help="Performs a trial run without changing any data")
    op.add_option("-b", "--daysback", dest="daysback", default=5,
                  type="int",
                  help="Integer value indicating the number of days back the scan should include")

    (opts, args) = op.parse_args()

    cc = CustContactTool(opts)
    cc.processCrs()
    return
## END main

if __name__ == "__main__":
    main()
