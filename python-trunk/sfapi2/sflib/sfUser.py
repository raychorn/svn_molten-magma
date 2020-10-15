#!/bin/env python2.3
"""
Business logic specific to an User object in salesforce.com
"""
import pprint
import types
from sfConstant import *
from sfMagma import *

class SFUser(SFMagmaEntity):
    def __init__(self, entity=None, data={}, action=None, sfTool=None,
                 debug=0):
        """
        If an active tool object is not passed in then a connection is created.
        """

        if entity is None:
            entity = USER_OBJ

        if sfTool is None:
            sfTool = SFUserTool()
            
        SFEntityBase.__init__(self, entity, data=data, action=action,
                              sfTool=sfTool, debug=debug)

        self.data = self.getData(USER_OBJ)

        return

    def getSFData(self, userId, show=True):
        res = {USER_OBJ: {}, CONTACT_OBJ: {}}
        self.setData(res, reset=True)

        userRet = None
        if userId in BAD_INFO_LIST:
            msg = "SFUser.getSfData: Bad UserId: '%s'" %userId
            self.sfb.setLog(msg, 'error')
        else:
            userRet = self.sfb.retrieve([userId], USER_OBJ)


        if userRet in BAD_INFO_LIST:
            msg = "SFUser.getSFData: NO User found for ID %s" %userId
            self.sfb.setLog(msg, 'warn')


        else:
            userData = userRet[0]
            res[USER_OBJ] = userData
            contactId = userData.get('User_Contact_Id__c', None)

            contactRet = None
            if contactId in BAD_INFO_LIST:
                msg = "SFUser.getSFData: Bad ContactId %s" %contactId
                self.sfb.setLog(msg, 'error')
            else:
                contactRet = self.sfb.retrieve([contactId], CONTACT_OBJ)
                
            if contactRet in BAD_INFO_LIST:
                msg = "SFUser.getSFData: NO contact found for ID %s" %contactId
                self.sfb.setLog(msg, 'warn')

            else:
                contactData = contactRet[0]
                res[CONTACT_OBJ] = contactData
            
        self.setData(res)
        self.loadFromSF = True

        if show:
            self.showData(res)

        return res
    ## __init__



class SFUserTool(SFMagmaTool):
    """
    This is a subclass of the SFEntityTool to hold any Account specific
    SOQL query methods and entity linking action methods
    """

    def getUserDataById(self, userId):
        """
        base retrieve wrapper that uses cache. Fetches all fields.
        """
        userData = None
        
        if userId in BAD_INFO_LIST:
            msg = "SFUserTool.getUserDataById: Bad UserId: '%s'" %userId
            self.setLog(msg, 'error')
        else:
            userData = self.getCache(userId)

            if userData.get('loadStatus', None) == 'new':
                ret = self.retrieve([userId], USER_OBJ)
                if ret == 'fail' or len(ret[0]) == 0:
                    userData = None
                else:
                    userData = ret[0]
                    self.setCache(userId, userData)

        return userData
    ## END getUserDataById


    def isActiveUserId(self, userId):
        """
        Returns True is user ID is active (and valid)
        Returns False if user ID is inactive or is not valid
        """

        userData = self.getUserDataById(userId)

        if userData is not None and \
               userData.has_key('IsActive') and \
               userData['IsActive'] == "true":
            return True
        else:
            return False
    ## END isActiveUserId

    def cascadeToActiveUser(self, userId):
        """
        If a user is active, return the user ID.

        If inactive, return the user ID from the associated contact record
        Reassign To field.

        If that field is not filled in, return the soft default user ID.
        If some other problem prevents resolution, return the default user ID.
        """

##        if userId in BAD_INFO_LIST:
##            activeUserId = self.sfc.get('main','default_soft_uid')
##        el

        if self.isActiveUserId(userId):
            activeUserId =  userId
        else:
            user = SFUser(USER_OBJ, sfTool=self)
            user.getSFData(userId, show=False)
            contactData = user.getData(CONTACT_OBJ)
            reassignUserId = contactData.get('Reassign_To_User_ID__c', None)

            if reassignUserId is None:
                activeUserId = self.sfc.get('main','default_soft_uid')
            else:
                activeUserId = self.cascadeToActiveUser(reassignUserId)
                pass

        
        return activeUserId

##    def getUserIdByUsername(self, email):
##        """
##        Given an email address (or username), find the salesforce User ID
##        if that email address is indeed a username.
##        """

##        soql = "select Id from User where Username = '%s'" %email
##        queryList = self.query(USER_OBJ, soql=soql)

##        userId = None
        
##        if queryList in BAD_INFO_LIST:
##            msg = "getUserIdByUsername Result: NO User found with Username %s" \
##                  %email
##            self.setLog(msg, 'debug')
            
##        elif len(queryList) > 1:
##            # This should never happen - SF shouldn't allow duplicate usernames
##            msg = "getUserIdByUsername found more than one User having the Username %s" %email
##            self.setLog(msg, 'critical')
##        else:
##            userInfo = queryList[0]
##            userId = userInfo['Id']
##            pass
        
##        return userId
##    ## END getUserIdByUsername

    def getUserIdByUsername(self, email):
        """
        Simple wrapper as this routine was moved into sForceApi3
        """
        return sForceApi3.getUserIdByUsername(self, email)
