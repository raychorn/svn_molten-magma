"""
Mixin for Sfdc Connection to contain all the metadata (describe) calls
"""
from Util import booleanize

from SObjectMetadata import SObjectMetadata

class ConnectionMetadataMixin:

    def describeGlobal(self):
        """ simple wrapper method for sforce API call of the same name.
        Since the returned object is of no further use than to look up
        values, we liberate it as a python dictionary before returning it
        """
        describeGlobalResult = self._callSfdc(self.sfdc.describeGlobal)
        return describeGlobalResult
    ## END describeGlobal

    def describeSObject(self, sObjectType):
        describeSObjectResult = self._callSfdc(self.sfdc.describeSObject, sObjectType)
        return SObjectMetadata(describeSObjectResult)
    ## END describeSObject

    def describeSObjects(self, sObjectTypeList):
        MAX_SOBJECT_TYPES = 100

        isList = True
        if type(sObjectTypeList) not in (types.ListType, types.TupleType):
            isList = False
            pass

        sObjectTypeList = listify(sObjectTypeList)
        sObjectTypeList = uniq(sObjectTypeList)

        describeSObjectResults = {}
        while len(sObjectTypeList):
            typeListSlice = sObjectTypeList[:MAX_SOBJECT_TYPES]
            sObjectTypeList = sObjectTypeList[MAX_SOBJECT_TYPES:]

            res = self._callSfdc(self.sfdc.describeSObjects, typeListSlice)

            if type(res) != types.ListType:
                res = [res,]
                pass

            for describeSObjectResult in res:
                sObjectType = describeSObjectResult.get('name')
                describeSObjectResults[sObjectType] = SObjectMetadata(describeSObjectResult)
                continue

            continue

        if isList is False and len(describeSObjectResults) > 0:
            describeSObjectResults = describeSObjectResults.values()[0]
            pass

        return describeSObjectResults
    ## END describeSObjects

    def describeTabs(self):
        describeTabSetResult = self._callSfdc(self.sfdc.describeTabs)
        return describeTabSetResult
    ## END describeTabs
    
    def describeLayout(self, sObjectType):
        describeLayoutResult = self._callSfdc(self.sfdc.describeLayout, sObjectType)
        return describeLayoutResult
    ## END describeLayoutResult
           
    pass
