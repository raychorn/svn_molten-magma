"""
Mixin for SfdcConnection to contain utility CRUD API 
calls that are not specific to an sObject instance
"""
import re
import types

from SOAPpy import structType, arrayType, stringType

from Util import listify, booleanize
from SfdcUtil import uniqIdList

from SObjectClassFactory import SObjectClassFactory
from SObjectBatch import SObjectBatch

class ConnectionCrudMixin:
    
    def __resultToObject(self, listMapAttr):
        """
        Translate a list of query or retrieve results into objects

        Parameters
        
        """
        listSfObj = []

        sObjects = SObjectBatch(self)
        listMapAttr = listify(listMapAttr)
        sObjectType = None        
        
        if listMapAttr not in [None, [None],[], [{}], {}, '', 'fail', 'warn']:
            
            if len(listMapAttr) and listMapAttr[0].get('type') is not None:
                sObjectType = listMapAttr[0].get('type')
                sObjectClass = SObjectClassFactory(self, sObjectType)
    
                for mapAttr in listMapAttr:
                    if mapAttr is not None:
                        # For some reason, the ID field comes back as a list of 
                        # identical values. Grab only the first one.
                        if type(mapAttr.get('Id')) == types.ListType:
                            mapAttr['Id'] = mapAttr.get('Id')[0]
                            pass
                
                        # get rid of the type field - it's not an actual field that can be requested
                        # and we're putting the data into a typed object anyhow.
                        if mapAttr.has_key('type'):
                            del mapAttr['type']
                            pass
                        
                        sfObj = sObjectClass(mapAttr)
                        sObjects.add(sfObj)
                        pass
                
                    continue
                pass
            pass
        
        return sObjects
    ## END __resultToObject


    def create(self, sObjectClass, sObjectMapList):
        MAX_CREATE = self.p.maxCreate
        isList = True
        
        #sObjectClass = SObjectClassFactory(self, sObjectType)

        # ensure that sObjectMapList is a sequence of dictionaries
        if type(sObjectMapList) == types.DictType:
            isList = False
            sObjectMapList = [sObjectMapList,]
        elif type(sObjectMapList) not in [types.ListType, types.TupleType]:
            errmsg = "sObjectMapList not a dictionary, list or tuple"
            raise TypeError(errmsg)
        
        saveResult = []
        
        sliceCursor = 0
        while len(sObjectMapList[sliceCursor:sliceCursor+MAX_CREATE]):
            sObjectListSlice = sObjectMapList[sliceCursor:sliceCursor+MAX_CREATE]
            sliceCursor += MAX_CREATE
            
            sObjectCreateList = []
            ct = 0
            for sObjectMap in sObjectListSlice:
                sObjectStruct = structType(data=sObjectMap, typed=False)
                # brand the struct with the sObject type
                sObjectStruct._addItem('type', sObjectClass._sObjectSoapType)
                sObjectCreateList.append(sObjectStruct)
                ct += 1
                continue

            sliceSaveResult = self._callSfdc(self.sfdc.create, sObjectCreateList)
            if isList:
                saveResult.extend(sliceSaveResult)
            else:
                saveResult = sliceSaveResult
                pass
            continue
    
        return saveResult
    ## END create
 
    def retrieve(self, sObjectType, idList, fieldList=None):
        """
        
        Retrieves objects for the list of IDs

        idList - List of sObject IDs to retrieve. All IDs must be of the same sObject type. The maximum number of IDs to retrieve is 2000, and if more are supplied to this method, multiple retrieve calls will automatically be made and the results combined.
        fieldList - List of fields to retrieve for each sObject. If not provided or None, all fields for the object will be retrieved.
        """
        MAX_RETRIEVE_IDS = self.p.maxRetrieve
        
        sObjectClass = SObjectClassFactory(self, sObjectType)
        
        isList = True
        if type(idList) not in (types.ListType, types.TupleType):
            isList = False
            pass
        
        idList = listify(idList)
        # we must insure that there are no duplicate IDs otherwise SOAPpy
        # generates a strange outgoing SOAP message that blows the
        # session ID
        #idList = uniqIdList(idList)
        
        # FIXME check the signature of the first ID against the sObjectClass signature
        
        if fieldList is None:
            fieldList = sObjectClass.getFieldnames()
            pass
        
        retrieveResult = []
        sliceCursor = 0
        while len(idList[sliceCursor:sliceCursor+MAX_RETRIEVE_IDS]):
            idListSlice = idList[sliceCursor:sliceCursor+MAX_RETRIEVE_IDS]
            sliceCursor += MAX_RETRIEVE_IDS
            res = self._callSfdc(self.sfdc.retrieve,
                                     ', '.join(fieldList),
                                     sObjectClass._sObjectTypeStr,
                                     idListSlice)

            if type(res) == types.ListType:
                retrieveResult.extend(res)
            else:
                retrieveResult.append(res)
                pass
            
            continue
        
        retrievedObjects = self.__resultToObject(retrieveResult)
        
        if isList is False:
            if len(retrievedObjects) > 0:
                retrievedObjects = retrievedObjects[0]
            else:
                retrievedObjects = None
                pass
            pass
        
        return retrievedObjects
    ## END retrieve
 
    def query(self, queryString):
        """
        Run a query for this type of object using the supplied where clause
        and return either the provided list of fields or all available fields
        (default).

        In the event that more records are found than can be returned in a
        single batch, query will automatically call _queryMore until it has
        fetched all objects found by the query, returning the combined
        result.

        Returns a batch object containing all objects found by the query or
        an empty batch if none were found.

        Parameters:
        whereClause - string containing the where clause of the SOQL query. Should not begin with the word 'where,' however it fill be stripped off if necessary.
        fieldList - default None - list of field names to return from the object type being queried. If not supplied, the default action will be to return all fields. 
        """
        queryString = queryString.strip()

        queryResult = self._callSfdc(self.sfdc.query, queryString)
                 
        sObjectRecords = queryResult.get('records')
        done = booleanize(queryResult.get('done'))
        queryLocator = queryResult.get('queryLocator')
        while done is False:
            queryResult = self.__queryMore(queryLocator)
            sObjectRecords.extend(queryResult.get('records'))
            done = booleanize(queryResult.get('done'))
            queryLocator = queryResult.get('queryLocator')
            continue
                
        queryResultBatch = self.__resultToObject(sObjectRecords)
        return queryResultBatch
    ## END query
    
    def __queryMore(self, queryLocator):
        queryResult = self._callSfdc(self.sfdc.queryMore, queryLocator)
        return queryResult
    ## END __queryMore
    
    def search(self, searchString):
        raise notImplementedError
        pass
    ## END search
    
    def delete(self, idList):
        """
        A connection version of the delete call that can take a list
        having any mix of sObject ids for deletion

        Parameters:
        idList - list of sObject ids to delete
        """
        MAX_DELETE = self.p.maxDelete
        
        idList = listify(idList)
        idList = uniqIdList(idList)
        
        deleteResult = []
        sliceCursor = 0
        while len(idList[sliceCursor:sliceCursor+MAX_DELETE]):
            deleteSlice = idList[sliceCursor:sliceCursor+MAX_DELETE]
            sliceCursor += MAX_DELETE
            result = self._callSfdc(self.sfdc.delete, deleteSlice)
            deleteResult.extend(result)
            continue
        
        return deleteResult
    ## END deleteIds

    def getDeleted(self, sObjectType, startDateTime, endDateTime):
        getDeletedResult = self._callSfdc(self.sfdc.getDeleted,
                                               startDateTime, endDateTime)
        return getDeletedResult
    ## END getDeleted
    
    def getUpdated(self, sObjectType, startDateTime, endDateTime):
        getUpdatedResult = self._callSfdc(self.sfdc.getUpdated,
                                               startDateTime, endDateTime)
        return getUpdatedResult
    ## END getUpdated
