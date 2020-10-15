"""
Base class for sObject instances
"""
import copy
import types
import sets

from SOAPpy import structType

from UpdateDict import UpdateDict
from SObjectMetadata import SObjectMetadata, MetadataHelperMixin
from SObjectBatch import SObjectBatch
from SoqlHelperMixin import SoqlHelperMixin
from SfdcUtil import uniqIdList
from Util import listify, booleanize

#from SOAPpy.Types import faultType, structType

import PysfdcLogger, logging
log = logging.getLogger('pysfdc.sobject.crudbase')

class SObjectCrudBase(UpdateDict, MetadataHelperMixin):
    """ Abstract base class for all sfdc object types. Provides basic CRUD
    features. Not intended to be instanced directly
    """

    # maintain the dictionary class' update method, but move it aside to make
    # room for the CRUD update
    dictupdate = UpdateDict.update

    # string of an official sObjectType from salesforce
    _sObjectTypeStr = None # Holder for the object type string
    _sObjectSoapType = None # Holder for the soap-ified object type
    
    # SObjectMetadata instance 
    _metadata = None

    # temporarily take on the module's logger
    # will be replaced by sObject-specific logger
    # when instantiated by the SObjectClassFactory
    log = log

    def __init__(self, mapAttr={}):
        """ cxn is an connection to salesforce.com
        mapAttr is a map of fields and values

        Not called directly to instantiate salesforce objects - called by
        other static constructor methods
        """
        if self._sObjectTypeStr is None:
            raise NotImplemetedError

        # store two copies of the data map. perform deepcopy so we're
        # not beholden to the structure passed in.
        #this is dict.update, not SObjectCrudBase.update

        UpdateDict.__init__(self, copy.deepcopy(mapAttr))

        return
    ## END __init__


    #############################
    ## sObjectType-specific utility class methods
    #############################
    def describeSObject(klass):
        """
        Wrapper around Connection's describeSObject call specific to an
        sObject class instance
        
        """
        describeSObjectResult = klass.cxn.describeSObject(klass._sObjectTypeStr)
        # FIXME - install new metadata object into klass
        return describeSObjectResult
    describeSObject = classmethod(describeSObject)
    ## END describeSObject

    def describeLayout(klass):
        """
        Wrapper around Connection's describeLayout call specific to an
        sObject class instance
        """
        describeLayoutResult = klass.cxn.describeLayout(klass._sObjectTypeStr)
        return describeLayoutResult
    describeLayout = classmethod(describeLayout)
    ## END describeLayout


    def getDeleted(klass, startDateTime, endDateTime):
        getDeletedResult = klass.cxn.getDeleted(klass._sObjectTypeStr,
                                                 startDateTime, endDateTime)
        return getDeletedResult
    getDeleted = classmethod(getDeleted)
    ## END getDeleted
     
    def getUpdated(klass, startDateTime, endDateTime):
        getUpdatedResult = klass.cxn.getUpdated(klass._sObjectTypeStr,
                                                 startDateTime, endDateTime)
        return getUpdatedResult
    getUpdated = classmethod(getUpdated)
    ## END getDeleted
     
    #############################
    ## CRUD support class methods
    #############################

    def create(klass, sObjectMapList):
        saveResult = klass.cxn.create(klass, sObjectMapList)
        return saveResult
    create = classmethod(create)
    ## END create

    #############################
    ## CRUD support instance methods
    #############################

    def refresh(self, allFields=False):
        """
        Re-retrieve this sObject from Salesforce.com and replace the reference 
        to the current object with the newly retrieved one.
        
        Parameters:
        allFields - boolean, if set to True, refresh will retrieve all the objects fields. If false
            will retrieve the same set of fields the object was originally retrieved with. Default
            is False.
        
        """
        if self.has_key('Id') is False:
            raise KeyError("Cannot refresh: %s sObject has no Id field set" %self._sObjectTypeStr)
            
        fieldList = None
        if allFields is False:
            self.clear()
            fieldList = self.keys()
            pass
        
        refreshedSObject = self.cxn.retrieve(self._sObjectTypeStr, self.get('Id'), fieldList)
        self._initialize(refreshedSObject)
        return
    ## END refresh


    def delete(self):
        """
        Wrapper on connection delete call that deletes only this sObject
        """
        if self.has_key('Id') is False:
            raise KeyError("Cannot delete: %s sObject has no Id field set" %self._sObjectTypeStr)

        deleteResult = self.cxn.delete(self.get('Id'))
        return deleteResult
    ## END delete

    def getUpdates(self):
        """
        Overridden UpdateDict getUpdates method to return a dictionary of updates
        including the Sobject SOAP type and Id
        
        """
        updateDict = UpdateDict.getUpdates(self)
        if updateDict.has_key('fieldsToNull') and len(updateDict['fieldsToNull']) == 0:
            del updateDict['fieldsToNull']
            pass
        updateDict['Id'] = self.get('Id')
        
        # pour the update into a structType
        updateStruct = structType(data=updateDict, typed=False)
        
        # now set the sObjectType for the update struct
        updateStruct._addItem('type', self._sObjectSoapType)
        
        return updateStruct
    ## END getUpdates
        
        
    def update(self):
        """
        Updates a changed CrudObject in salesforce.com

        Compares the sObject's data fields against a stored copy and commits
        any differences to sfdc.

        NB: Even though an object based upon SObjectCrudBase is a subclass
        of a python dictionary-like mapping object, this update method is not equivalent
        to the dict.update method. To access the latter method in an object
        of a class descended from SObjectCrudBase, use 'dictupdate' instead.
        """
        if self.has_key('Id') is False:
            raise KeyError("Cannot update: %s sObject has no Id field set" %self._sObjectTypeStr)

        updateDict = self.getUpdates()

        saveResult = self.cxn._callSfdc(self.cxn.sfdc.update, [updateDict])
    
        # commit the changes to the sObject if the update succeeded
        if booleanize(saveResult.get('success', False)) is True:
            self.commit()
            pass
        
        return saveResult
    ## END update
    
    pass
## END class SObjectCrudBase
