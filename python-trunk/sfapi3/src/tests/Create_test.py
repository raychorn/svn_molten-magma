import unittest

from Properties import Properties
from SfdcConnection import SfdcConnection
from SObjectClassFactory import SObjectClassFactory
from SfdcApiFault import SfdcApiFaultFactory

from TestSupport import TestCxn, TestData

from Util import booleanize, listify

class Create_test(unittest.TestCase):
    
    def setUp(self):
        self.cxn = TestCxn().cxn
        self.idList = []
        return

    def checkSaveResult(self, saveResult):
        idList = []
        saveResult = listify(saveResult)
        
        for saveResultItem in saveResult:
            self.assertEqual(booleanize(saveResultItem.get('success')), True)
            id = saveResultItem.get('id')
            
            self.assertNotEqual(id, None)
            idList.append(id)
            continue

        return idList
    
    def testSingleCreate(self):
        """ Create a single Case sObject """
        Case = SObjectClassFactory(self.cxn, 'Case')
        saveResult = self.cxn.create(Case, TestData.Case[0])
        self.idList = self.checkSaveResult(saveResult)
        return

    
    def testMultipleCreate(self):
        """ Create multiple Case sObjects in batch """
        Case = SObjectClassFactory(self.cxn, 'Case')
        objects = []
        objects.append(TestData.Case[0])
        objects.append(TestData.Case[1])
        saveResult = self.cxn.create(Case, objects)
        self.idList = self.checkSaveResult(saveResult)
        return

    def testObjectCreate(self):
        """ Create a Case sObject by calling the create class method on the Case sObjectClass """
        Case = SObjectClassFactory(self.cxn, 'Case')
        saveResult = Case.create(TestData.Case[0])
        self.idList = self.checkSaveResult(saveResult)
        return
    
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
    suite.addTest(unittest.makeSuite(Create_test))
    return suite
    
if __name__ == "__main__":
    unittest.main()
    pass
