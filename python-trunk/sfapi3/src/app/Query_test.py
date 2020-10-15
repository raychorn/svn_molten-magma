import unittest

from Properties import Properties
from SfdcConnection import SfdcConnection
from SObjectClassFactory import SObjectClassFactory
from SfdcApiFault import SfdcApiFaultFactory

from SfConnection import TestCxn

from Util import booleanize, listify
import PysfdcLogger, logging
log = logging.getLogger('pysfdc.query')

class Query_test:
    
    def setUp(self):
        self.cxn = TestCxn().cxn
        self.idList = []
        return

        
    def queryData(self):
        """ Create a single Case sObject """
        
        
        """ Create a single Case sObject """
        print "CONNECTION %s" %self.cxn
        CaseTest = {}
        CaseTest[0] = {'Subject': 'Test Create Case Subject 1',
               'Status': 'New',
               'Origin': 'Email',
               'Description': 'Test api3 test api3 ',
               'PE_Checkpoint__c': 'a1930000000CaWX',
               'Priority': 'Low'}
        Case = SObjectClassFactory(self.cxn, 'Case')
        #saveResult = self.cxn.create(Case, CaseTest[0])
        #self.idList = self.checkSaveResult(saveResult)
        #print "ID ... %s" %saveResult
        
        #describeSObject      
        queryString = "select Id from Case where Subject = 'Third CR for testing workflow'"
        print "QUERY................%s" %queryString
        queryResultBatch = self.cxn.query(queryString)
        print "After query... %s"%queryResultBatch
        for qr in queryResultBatch:
            log.info("ID is %s"%qr.get('Id'))
            print "ID =============== %s"%qr.get('Id')
            #pprint.pprint(dir(queryResultBatch))
            pass
        
        
    pass
## END class Create_test

"""def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Create_test))
    return suite"""

def main():  
    n=Query_test()  
    n.setUp()
    n.queryData()
    
    
if __name__ == "__main__":
    main()
    pass
