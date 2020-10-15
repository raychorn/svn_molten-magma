import unittest
import types
import copy

from Properties import Properties
from SfdcConnection import SfdcConnection
from SObjectClassFactory import SObjectClassFactory
from SfdcApiFault import SfdcApiFaultFactory
from SObjectBatch import SObjectBatch

from TestSupport import TestCxn, TestData

from Util import booleanize, listify

class Retrieve_test(unittest.TestCase):
    
    def setUp(self):
        self.cxn = TestCxn().cxn
        self.sObjectType = 'Case'
        Case = SObjectClassFactory(self.cxn, self.sObjectType)
    
        objects = []
        objects.append(TestData.Case[0])
        objects.append(TestData.Case[1])
        saveResult = self.cxn.create(Case, objects)

        caseIds = []
        for saveResultItem in saveResult:
            id = saveResultItem.get('id')
            caseIds.append(id)
            continue
 
        self.idList = caseIds
        return
    ## END setUp
    
    
    def compareResult(self, compareSObjectType, retrievedSObjects, ids):
        compareSObject = SObjectClassFactory(self.cxn, compareSObjectType)
        compareSObjectInstance = compareSObject()
        
        compareBatch = SObjectBatch(self.cxn)
        
        if type(retrievedSObjects) == type(compareSObjectInstance):
            self.compareResultUnit(retrievedSObjects, compareSObjectInstance, ids)
        elif type(retrievedSObjects) == type(compareBatch):
            ct = 0
            for retrievedSObject in retrievedSObjects:
                self.compareResultUnit(retrievedSObject, compareSObjectInstance, ids[ct])
                ct += 1
                continue
        else:
            errmsg = 'retrieved Type %s not one of %s or %s type' \
                     %(type(retrievedSObjects), type(sompareSObjectInstance), type(compareBatch))
            self.fail(errmsg)
            pass

        return
    ## END compareResult
    

    def compareResultUnit(self, retrievedSObject, compareSObjectInstance, compareId):
        self.assertEqual(type(retrievedSObject), type(compareSObjectInstance))
        self.assertEqual(retrievedSObject.get('Id'), compareId)
        return
    ## END compareResultUnit
    
    
    def testSingleRetrieve(self):
        """ Test retrieve of a single scalar sObjectListId """
        testId = self.idList[0]
        retrieved = self.cxn.retrieve(self.sObjectType, testId)
        self.compareResult(self.sObjectType, retrieved, testId)
        return
    ## END testSingleRetrieve

    
    def testSingleListRetrieve(self):
        """ Test retrieve of a list of a single sObjectListId """
        testIdList = self.idList[:1]
        retrieved = self.cxn.retrieve(self.sObjectType, testIdList)
        self.compareResult(self.sObjectType, retrieved, testIdList)
        return
    ## END testSingleListRetrieve
    

    def testListRetrieve(self):
        """ Test retrieve of a list of muliple sObjectListIds """
        retrieved = self.cxn.retrieve(self.sObjectType, self.idList)
        self.compareResult(self.sObjectType, retrieved, self.idList)
        return
    ## END testListRetrieve


    def testDuplicateListRetrieve(self):
        """ Test retrieve of a list of muliple sObjectListIds with a duplicated Id """
        numIds = len(self.idList)
        
        # Adjust the source and destination of the record to be duplicated
        # based on the size of the test fixture
        insertIdx = numIds
        sourceIdx = 0
        if numIds > 2:
            insertIdx = -1
        elif numIds > 3:
            sourceIdx = 1
            pass
        
        testIdList = copy.copy(self.idList)
        testIdList.insert(insertIdx, self.idList[sourceIdx])
        
        retrieved = self.cxn.retrieve(self.sObjectType, testIdList)
        self.compareResult(self.sObjectType, retrieved, testIdList)        
        return
    ## END testListRetrieve

    
    def tearDown(self):
        """
        Clean up any objects created in the course of the test fixture

        """
        if len(self.idList):
            self.cxn.delete(self.idList)
            pass
        return

    pass
## END class Create_test

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Retrieve_test))
    return suite
    
if __name__ == "__main__":
    unittest.main()
    pass
