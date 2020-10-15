"""
List of related sfdc objects

Provides UD facilities
"""
from types import ListType, TupleType, IntType, SliceType, StringType

from Util import listify, booleanize
from SfdcUtil import id15to18
from SObjectType import verifySObjectType

from odict import odict

import PysfdcLogger, logging
log = logging.getLogger('pysfdc.batch')

class SObjectBatch(odict):
    """
    Manages a dictionary of like sfdc objects (keyed by id) for the purposes
    of performing batch functions. 
    """

    def __init__(self, cxn, sObjectType=None, memberObjList=None):
        """
        Creates a batch object to contain like sObjects

        """
        log.debug3('SObjectBatch: in __init__')

        odict.__init__(self)
        
        self.cxn = cxn
        self.data = {}

        self._sObjectTypeStr = None

        if sObjectType is not None:
            verifySObjectType(self.cxn, sObjectType)
            self._sObjectTypeStr = sObjectType
            pass
        
        if memberObjList is not None:
            self.add(memberObjList)
            pass
        
        return
    ## END __init__

    def __getitem__(self, key):
        """
        Gets and returns a single sObject if given an integer index or an
        sObject ID.

        If a slice is provided, returns an SObjectBatch containing the slice
        of items
        """
        log.debug3('SObjectBatch: in __getitem__')
        if type(key) == IntType:
            return self.values()[key]
        elif type(key) == SliceType:
            keys = self._keys[key]
            retlist = []
            for key in keys:
                retlist.append(self.get(key))
                continue
            return SObjectBatch(self.cxn, self._sObjectType, retlist)
        else:
            # assume key is an Id
            # translate to id18
            key = id15to18(key)
            return self.get(key)
        pass
    ## END __getitem__

    def __delitem__(self, key):
        """
        Deletes an index, slice, Id or list of IDs from the batch
        """
        log.debug3('SObjectBatch: in __delitem__')
        if type(key) == IntType:
            key = self._keys[key]
            self.__delitem__(key)
        elif type(key) == SliceType:
            keys = self._keys[key]
            self.__delitem__(keys)
        elif type(key) in [ListType, TupleType]:
            keys = key
            for key in keys:
                del self[key]
                continue
            pass
        elif type(key) == StringType:
            # key is a string (most likely an sObject ID)
            key = id15to18(key)
            odict.__delitem__(self, key)
        else:
            raise KeyError
        return
    ## END __delitem__


    def add(self, objList):
        """
        Adds an sObject or list of sObjects 
        """
        log.debug3('SObjectBatch: in add')
        rejectList = []

        objList = listify(objList)

        # if the batch's sObjectType isn't defined, set it to that of the
        # first object in the list
        if self._sObjectTypeStr is None and len(objList) > 0:
            self._sObjectTypeStr = objList[0]._sObjectTypeStr
            pass

        for obj in objList:
            if obj._sObjectTypeStr == self._sObjectTypeStr:
                self[obj.get('Id')] = obj
            else:
                rejectList.append(obj)
                pass
            continue

        return rejectList
    ## END add

    def move(self, key, index):
        log.debug3('SObjectBatch: in move')

        key = id15to18(key)
        odict.move(self, key, index)
        return
    ## END move

    def update(self):
        """
        Performs an update for all items in this SObjectBatch
        
        """
        log.debug3('SObjectBatch: in update')
        
        updateList = []
        for sObject in self.values():
            updateList.append(sObject.getUpdates())
            continue
        
        saveResultBatch = self.cxn._callSfdc(self.cxn.sfdc.update, [updateList])
        
        # look through the saveResults and commit the batch members for which the commit succeeded
        saveResultBatch = listify(saveResultBatch)
        for saveResult in saveResultBatch:
            if booleanize(saveResult.get('success', False)) is True:
                self[saveResult['id']].commit()
                pass
            continue
            
        return saveResultBatch
    ## END update

    def delete(self):
        """
        Delete all sObjects in this batch
        """
        log.debug3('SObjectBatch: in delete')
        deleteResultBatch = self.cxn.delete(self.keys())
        
        # remove all successfully deleted sObjects from the batch
        for deleteResult in deleteResultBatch:
            if booleanize(deleteResult.get('success', False)) is True:
                del self[deleteResult['id']]
                pass
            continue
        
        return deleteResultBatch
    ## END delete

    def refresh(self, allFields=False):
        """
        Re-retrieves all the sObjects in the batch and repopulates the batch
        with the results. 
        """
        log.debug3('SObjectBatch: in refresh')
        sObjectBatchIdList = self.keys()

        fieldList = None
        if allFields is False:
            fieldList = self[0].keys()
            pass

        retrievedBatch = self.cxn.retrieve(self._sObjectTypeStr, sObjectBatchIdList, fieldList)
        
        # clear the existing batch and add all the elements of the retrieved batch
        self.clear()
        self.add(list(retreivedBatch))
        return
    
    pass
## END SfdcBatch
