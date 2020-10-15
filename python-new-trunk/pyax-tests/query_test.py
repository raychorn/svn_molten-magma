import unittest
import types
import copy
from pprint import pprint, pformat

from pyax.sobject.classfactory import ClassFactory
from pyax.sobject.batch import Batch
from pyax.exceptions import SObjectTypeError, ApiFault
from pyax.util import booleanize, listify

from support import TestSession, TestData


class query_test(unittest.TestCase):
    
    def setUp(self):
        self.sfdc = TestSession().sfdc
        self.start_timestamp = self.sfdc.getServerTimestamp()    
        self.sObjectType = 'Case'
        Case = ClassFactory(self.sfdc, self.sObjectType)
    
        objects = []
        objects = TestData.gen_cases(5)
        saveResult = self.sfdc.create(Case, objects)
        caseIds = []
        for saveResultItem in saveResult:
            id = saveResultItem.get('id')
            caseIds.append(id)
            continue
 
        self.id_list = caseIds
        return
    ## END setUp
    
    def test_simple_query(self):
        """ Test a simple query that should return list of results"""
        query_str = "SELECT Id, Subject FROM Case WHERE subject LIKE '!@#$%'"
        queried = self.sfdc.query(query_str)
        self.assertEqual(type(queried), type(Batch(self.sfdc)))
        return
    ## END test_simple_query
    
    def test_simple_query_single(self):
        """ Test a simple query that should return one result"""
        query_str = "SELECT Id, Subject FROM Case WHERE subject LIKE '!@#$% Subject 3' LIMIT 1"
        queried = self.sfdc.query(query_str)
        self.assertEqual(type(queried), type(Batch(self.sfdc)))
        self.assertEqual(len(queried), 1)
        return
    ## END test_simple_query_single

    def test_query_invalid(self):
        """ Test a simple query that should throw an ApiFault code MALFORMED_QUERY"""
        query_str = "SEQECT Id, Zorchplox FROM Case WHERE subject LIKE '!@#$% Subject 3' LIMIT 1"
        try:
            self.sfdc.query(query_str)
        except ApiFault, f:
            self.assertEqual(f.exception_code, "MALFORMED_QUERY")
        except Exception, f:
            self.fail("Invalid query raised exception other than ApiFault: %s"%type(f))
        return
    ## END test_query_invalid
    
    def test_query_invalid_field(self):
        """ Test a simple query that should throw an ApiFault code INVALID_FIELD"""
        query_str = "SELECT Id, Zorchplox FROM Case WHERE subject LIKE '!@#$% Subject 3' LIMIT 1"
        #self.assertRaises(ApiFault, self.sfdc.query, query_str)
        try:
            self.sfdc.query(query_str)
        except ApiFault, f:
            self.assertEqual(f.exception_code, "INVALID_FIELD")
        except Exception, f:
            self.fail("Query with invalid field raised exception other than ApiFault: %s"%type(f))
        return
    ## END test_query_invalid_field  
    
    def test_query_all(self):
        """ Test that queryAll can return deleted fields where query cannot"""
        query_str = "SELECT Id FROM Case WHERE subject LIKE '!@#$%' " +\
            "AND CreatedDate >= %s" %self.start_timestamp
        query_deleted_str = "%s AND isDeleted = true" %query_str
        del_id_list = [self.id_list[1], self.id_list[3]]
        self.sfdc.delete(del_id_list)
        
        query_result_batch = self.sfdc.query(query_str)
        query_all_result_batch = self.sfdc.queryAll(query_str)
        query_deleted_result_batch = self.sfdc.queryAll(query_deleted_str)
        
        # regular query should only see three of the five cases
        self.assertEqual(len(query_result_batch), 3)
        # query all should see all five cases
        self.assertEqual(len(query_all_result_batch), 5)
        # query all for isDeleted=true should see the two deleted cases
        self.assertEqual(len(query_deleted_result_batch), 2)

    def test_pprint_batch(self):
        """ Test that an sobject batch can be pprinted"""
        query_str = "SELECT Id, Subject FROM Case WHERE subject LIKE '!@#$%'"
        queried = self.sfdc.query(query_str)
        self.assertTrue(len(queried) > 0)
        self.assertTrue(isinstance(queried, Batch))
        try:
            pformat(queried)
        except Exception, e:
            self.fail(e)
        return
                          
    def tearDown(self):
        """
        Clean up any objects created in the course of the test fixture

        """
        if len(self.id_list):
            self.sfdc.delete(self.id_list)
            pass
        return
    pass
## END class Create_test

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(query_test))
    return suite
    
if __name__ == "__main__":
    unittest.main()
    pass
