import unittest

from Properties import Properties
from SfdcConnection import SfdcConnection
from SObjectClassFactory import SObjectClassFactory
from SfdcApiFault import SfdcApiFaultFactory
from SfdcDatetime import SfdcDatetime

import types
import datetime

class SfdcConnection_test(unittest.TestCase):
    
    def setUp(self):
        self.p = Properties()
        self.cxn = SfdcConnection(self.p.testUsername, self.p.testPassword)
        return
        
    def tearDown(self):
        self.cxn = None
        return
        
    def testCxnUserInfo(self):
        """ Test that connection object got populated with user information """
        ui = self.cxn.userInfo
        
        self.assert_(type(ui) == types.DictType)
        self.assert_(len(ui) > 0)
        self.assert_(ui.has_key('userFullName'))
        self.assert_(ui.has_key('userTimeZone'))
        return

    def testGetServerTimestamp(self):
        """ Ensure that getServerTimestamp returns a datetime object """
        ts = self.cxn.getServerTimestamp()
        testTs = SfdcDatetime.utcnow()
        self.assert_(type(ts) == type(testTs))
        return
    
    def testSetPassword(self):
        pass
    
    def testResetPassword(self):
        pass
        
    def testCxnGlobalData(self):
        """ Test that connection object got populated with describeGlobal information """
        dg = self.cxn.globalData
        
        self.assert_(type(dg) == types.DictType)
        self.assert_(len(dg) > 0)
        self.assert_(dg.has_key('types'))
        self.assert_(type(dg.get('types')))
        return
        
    def testDescribeSObject(self):
        pass
        
    def testDescribeSObjects(self):
        pass
    
    def testDescribeTabs(self):
        """ Testing the describeTabs call """
        tabs = self.cxn.describeTabs()
        self.assert_(type(tabs) == types.ListType)
        self.assert_(type(tabs[0]) == types.DictType)
        return
    pass
    
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SfdcConnection_test))
    return suite
    
if __name__ == "__main__":
    unittest.main()

