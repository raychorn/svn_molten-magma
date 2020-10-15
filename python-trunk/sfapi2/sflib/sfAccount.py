#!/bin/env python2.3
"""
Business logic specific to an Account object in salesforce.com
"""
import pprint
import types
from sfConstant import *
from sfMagma import *
from salesforceId import convertId15ToId18

class SFAccount(SFMagmaEntity):
    def __init__(self, entity=None, data={}, action=None, sfTool=None,
                 debug=0):
        """
        If an active tool object is not passed in then a connection is created.
        """

        if entity is None:
            entity = ACCOUNT_OBJ
            
        SFEntityBase.__init__(self, entity, data=data, action=action,
                              sfTool=sfTool, debug=debug)

        self.data = self.getData(ACCOUNT_OBJ)

        return
    ## __init__



class SFAccountTool(SFMagmaTool):
    """
    This is a subclass of the SFEntityTool to hold any Account specific
    SOQL query methods and entity linking action methods
    """
    ###
    # Account related helpers
    # These will undoubtedly move to sfAccount.py or somesuch
    ###
        
    def findTopAccountIdsFromCandidates(self, accountIdList):
        """
        Given a list of account IDs, return a unique list of the top
        account IDs in the hierarchy for each.

        Ideally we always return one and only one, but the world isn't ideal...
        """
        # Find the list of unique top accounts for the account IDs we have
        topAccountUniq = {}
        for accountId in accountIdList:
            topAccountId = self.findTopAccountId(accountId)
            topAccountUniq[topAccountId] = topAccountId
        topAccountIdList = topAccountUniq.keys()

        return topAccountIdList
    ## END findTopAccountIdFromCandidates

    def _buildAccountInfoMaps(self):
        """
        Internal helper to build map members of various bits of account info
        """
        soql = "select Id, OwnerId, ParentId from Account"
        queryList = self.query(ACCOUNT_OBJ, soql=soql)

        accountParentMap = {}
        accountOwnerMap = {}

        for info in queryList:
            accountParentMap[info['Id']] = info.get('ParentId', None)
            accountOwnerMap[info['Id']] = info.get('OwnerId', None)
            continue

        self.accountParentMap = accountParentMap
        self.accountOwnerMap = accountOwnerMap
        return
    ## END _buildAccountInfoMaps

    def getAccountParentMap(self, refresh=False):
        """
        Like the name says, queries all accounts to have the data locally.
        """
        if not hasattr(self, 'accountParentMap') or refresh is True:
            self._buildAccountInfoMaps()
            
        return self.accountParentMap
    ## END getAccountParentMap

    def getAccountOwnerMap(self, refresh=False):
        if not hasattr(self, 'accountOwnerMap') or refresh is True:
            self._buildAccountInfoMaps()
            
        return self.accountOwnerMap
    ## END getAccountOwnerMap
            

    def findAccountOwnerId(self, accountId):
        """
        Given an account ID, return that account owner's UserId
        """
        accountOwnerMap = self.getAccountOwnerMap()
        accountId = convertId15ToId18(accountId)

        return accountOwnerMap.get(accountId, None)
    ## END findAccountParent

    def findAccountParentId(self, accountId):
        """
        Given an account ID, return that account's parent account Id
        """
        accountParentMap = self.getAccountParentMap()
        accountId = convertId15ToId18(accountId)

        return accountParentMap.get(accountId, None)
    ## END findAccountParent

    def findTopAccountId(self, accountId):
        """
        Given an accountId, return the top account in its hierarchy
        """
        accountId = convertId15ToId18(accountId)

        parentId = self.findAccountParentId(accountId)
        if parentId is None:
            topId = accountId
        else:
            topId =  self.findTopAccountId(parentId)

        return topId
    ## END findTopAccountId
    
    def getTopLevelAccounts(self, refresh=False):
        if not hasattr(self, 'topLevelAccountList') or refresh is True:
            accountParentMap = self.getAccountParentMap()
            
            topLevelAccountList = []
            for accountId in accountParentMap.keys():
                if accountParentMap[accountId] is None:
                    topLevelAccountList.append(accountId)
                    pass

                continue
            
            self.topLevelAccountList = topLevelAccountList
            pass
        
        return self.topLevelAccountList

    ## END getTopLevelAccounts

    
    def findAccountIdCandidatesFromEmail(self, email):
        """
        Given an email address, determine the IDs of all accounts the contact
        having the email may belong in be searching through existing contacts.
        """
        accountIdList = []
        
        m = re.search(r'(@.*)$', email)
        if m is not None:
            domain = m.group(1)
        else:
            return accountIdList

        soql = "select AccountId from %s where Email like '%%%s'" \
               %(CONTACT_OBJ, domain)
        queryList = self.query(CONTACT_OBJ, soql=soql)

        # Uniquify the account IDs gathered from contacts having matching
        # email domain
        accountUniq = {}

        if type(queryList) is types.ListType or \
           type(queryList) is types.TupleType:
            for info in queryList:
                if info.has_key('AccountId'):
                    accountUniq[info['AccountId']] = info['AccountId']
        accountIdList = accountUniq.keys()

        return accountIdList
    ## END findAccountIdCandidatesFromEmail

    def getAccountDataById(self, accountId):
        """
        base retrieve wrapper that uses cache. Fetches all fields.
        """
        accountId = convertId15ToId18(accountId)

        accountData = self.getCache(accountId)
        if accountData.get('loadStatus', None) == 'new' and \
               accountId not in [None,'']:
            ret = self.retrieve([accountId], ACCOUNT_OBJ)
            if ret == 'fail' or len(ret[0]) == 0:
                accountData = None
            else:
                accountData = ret[0]
                self.setCache(accountId, accountData)

        return accountData
    ## END getAccountDataById
