"""
Authenticates a connection with salesforce.com
maintains a session
provides server-scope calls - utility API calls defined here, CRUD and Metadata
calls are in respective mixins
"""
import os
import sys
import types

from SOAPpy import WSDL
from SOAPpy import structType
from SOAPpy import headerType
from SOAPpy import faultType

from pytz import timezone

from Properties import Properties
from RawSfdcConnection import RawSfdcConnection
from SfdcApiFault import handleFault, SfdcApiFaultFactory
from SObjectMetadata import SObjectMetadata, SObjectMetadataCache

from ConnectionCrudMixin import ConnectionCrudMixin
from ConnectionMetadataMixin import ConnectionMetadataMixin

from Util import listify, uniq

import PysfdcLogger, logging
log = logging.getLogger('pysfdc.cxn')

class SfdcConnection(RawSfdcConnection, ConnectionCrudMixin, ConnectionMetadataMixin):
	 
	def __init__(self, username, password):
		""" perform a login and create a SFDC connection """
		self.p = Properties()
	
		self.userTz = None
		self.globalData = None

		try:
			RawSfdcConnection.__init__(self, self.p.wsdlPath, self.p.namespace,
									   username, password)
		except faultType, f:	
			# catch and translate any SOAP faults on login
			# other exceptions to be raised normally
			fault = handleFault(f)
			raise fault
		
		# get the newly logged in user's info
		#self.userInfo = self.getUserInfo()

		# Augment user info with Profile and Role IDs
		roleProfileInfo = self.__getUserProfileAndRole()
		self.userInfo.update(roleProfileInfo)
		
		# note the user's timezone as a tzinfo object
		if self.userInfo.has_key('userTimeZone'):
			self.userTz = timezone(self.userInfo.get('userTimeZone'))
			pass

		self.globalData = self.describeGlobal()
		  
		return

	def _callSfdc(self, sfdcMethod, *args, **kw):
		"""
		Wrapper with which to run all sForce calls (after login).
		
		Catches any faultType exception, parses it, then turns it into an
		exception of the specific type returned (the possibilites are
		documented in the sForce API docs). If it is an INVALID_SESSION
		error, we will re-login and retry the call.
		  
		Parameters:
		sfdcMethod - reference to the method we're calling
		retryCt - used internally by this method - don't pass in any value and you'll be fine
		parameters to sfdcMethod come in on *args
		  
		"""
		sfdcResult = None
		  
		retryCt = kw.get('retryCt',0)
		if kw.has_key('retryCt'):
			del kw['retryCt']
			pass
		  
		try:
			try:
				sfdcResult = sfdcMethod(*args, **kw)
			except faultType, f:
				fault = handleFault(f)
				raise fault
				
		except (SfdcApiFaultFactory('INVALID_SESSION_ID')), e:
			retryCt += 1
			if retryCt < self.p.maxRetryCount:
				 #relogin the session
				 self.reLogin()
					
				 sfdcResult = self._callSfdc(sfdcMethod, retryCt=retryCt, *args, **kw)
			else:
				 raise e

		return sfdcResult
	## END _callSfdc

	def getServerTimestamp(self):
		""" simple wrapper method for sforce API call of the same name.
		parse the returned date into a datetime object
		"""
		from SfdcDatetime import SfdcDatetime
		  
		timestampResult = self._callSfdc(self.sfdc.getServerTimestamp)
		serverDatetime = SfdcDatetime.fromSfIso(timestampResult.get('timestamp'))
		return serverDatetime
	## END getServerTimestamp
 

	def getUserInfo(self):
		""" simple wrapper method for sforce API call of the same name. """
		userInfo = self._callSfdc(self.sfdc.getUserInfo)
		return userInfo
	## END getUserInfo

	def __getUserProfileAndRole(self):
		"""
		special wrapper to do a retrieve for the logged-in user's
		role and profile IDs. Wish this data were part of the getUserInfo.
		 
		We need to do this outside the whole CrudObject structure as
		that relies on profile-specific sObject metadata, and we don't
		yet know the user's profile.

		"""
		userRecord = {}

		userId = self.userInfo.get('userId')
		if userId is None:
			log.critical('userId not found in connection attr userInfo')
			sys.exit(1)
			pass
		  
		fields = "ProfileId, UserRoleId"
		res = self._callSfdc(self.sfdc.retrieve, fields, 'User', userId)

		self.userInfo['ProfileId'] = res.get('ProfileId')
		self.userInfo['UserRoleId'] = res.get('UserRoleId')
		result = {'ProfileId': res.get('ProfileId'),
				  'UserRoleId': res.get('UserRoleId')}
		return result
	## END getUserProfileAndRole


	def resetPassword(self, userId):
		"""
		reset password for a user to a generated value. Returns
		generated password value

		Parameters
		userId - user sObject ID
		"""
		password = self._callSfdc(self.sfdc.resetPassword, userId)
		return password
	## END resetPassword

	def setPassword(self, userId, password):
		"""
		set password for a user to the specified value

		Parameters
		userId - user sObject ID
		password - new password for the user
		"""
		# setPasswordReswult will be nothing if successful
		setPasswordResult = self._callSfdc(self.sfdc.setPassword, userId, password)
		return
	## END setPassword

	pass
## END class SfdcConnection
