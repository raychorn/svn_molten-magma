import unittest

from pyax.beatbox import SoapFaultError

from pyax.exceptions import ApiFault
from pyax.sobject.metadata import Metadata
from pyax.datatype.apexdatetime import ApexDatetime
from pyax.collections.clist import clist
from pyax.connection import Connection

from support import TestSession

import types
import datetime
from pprint import pprint

class Connection_test(unittest.TestCase):

    def setUp(self):
        self.tsession = TestSession()
        self.sfdc = self.tsession.sfdc

    def testLogin(self):
        """Connection constructor should succeed with good credentials"""
        try:
            sfdc = Connection.connect(self.tsession.username, 
                                      self.tsession.password,
                                      self.tsession.token)
        except SoapFaultError, f:
            self.fail('login call returned fault: %s' %f)
        except Exception, e:
            self.fail('login call raised exception: %s' %e)
            pass

        return

    def testInvalidSession(self):
        sfdc = Connection.connect(self.tsession.username, 
                                  self.tsession.password,
                                  self.tsession.token)

        #invert the session id to invalidate it
        original_session_id = sfdc.svc.sessionId
        invalid_session_id = ''.join(reversed(original_session_id))
        sfdc.svc.sessionId = invalid_session_id

        self.assertNotEqual(sfdc.svc.sessionId, original_session_id)
        sfdc.getServerTimestamp()

        # pyax should have re-logged in to "heal" the invalidated session Id
        self.assertNotEqual(sfdc.svc.sessionId, invalid_session_id)

        return


    def testFailLogin(self):
        """Connection constructor should raise an INVALID_LOGIN fault when 
        logging in with bad credentials"""            
        wrongPassword = '%sZZ' %self.tsession.password

        try:
            sfdc = Connection.connect(self.tsession.username, 
                                      wrongPassword, 
                                      self.tsession.token)
        except ApiFault, f:
            self.assertEqual(f.exception_code, 'INVALID_LOGIN')
        except Exception, e:
            self.fail('login call with bad credentials raised an exception other than an ApiFault: %s' %e)
        else:
            self.fail('login call with bad credentials did not raise a fault at all')

        return

    def testCxnUserInfo(self):
        """ Test that connection object got populated with user information """
        ui = self.sfdc.user_info

        self.assert_(type(ui) == types.DictType)
        self.assert_(len(ui) > 0)
        self.assert_(ui.has_key('userFullName'))
        self.assert_(ui.has_key('userTimeZone'))
        self.assert_(ui.has_key('roleId'))
        self.assert_(ui.has_key('profileId'))
        return

    def testGetServerTimestamp(self):
        """ Ensure that getServerTimestamp returns a datetime object """
        ts = self.sfdc.getServerTimestamp()
        self.assert_(isinstance(ts, ApexDatetime))
        return

#    def testSetPassword(self):
#        pass
#    
#    def testResetPassword(self):
#        pass
#        
    def test_CxnGlobalData(self):
        """ Test that connection object got populated with describeGlobal information """
        dg = self.sfdc.describe_global_response
        self.assert_(type(dg) == types.DictType)
        self.assert_(len(dg) > 0)
        self.assert_(dg.has_key('types'))
        self.assert_(isinstance(dg.get('types'), clist))
        return

    def test_describeSObject(self):
        do = self.sfdc.describeSObject('Account')
        self.failUnless(isinstance(do, Metadata), 
                        "test_DescribeSObject did not return an sobject.Metadata instance")
        pass

    def test_describeSObject_list(self):
        self.failUnlessRaises(ValueError, self.sfdc.describeSObject, ['Account',])
        pass

    def test_describeSObjects(self):
        objects = ['Account', 'Case', 'Contact']
        do = self.sfdc.describeSObjects(objects)
        self.failUnless(type(do) == types.DictType, 
                        "test_DescribeSObjects did not return a Map")
        objects_described = do.keys()
        objects_described.sort()
        self.failUnless(objects_described == objects, 
                        "Keys of described objects do not match objects requested")
        pass

    def test_describeSObjects_string(self):
        do = self.sfdc.describeSObjects('Account')
        self.failUnless(isinstance(do, Metadata), 
                        "describeSObjects on a single object type as a String did not return an sobject.Metadata instance")
        pass

    def test_describeSObjects_list(self):
        do = self.sfdc.describeSObjects(['Account',])
        self.failUnless(type(do) == types.DictType, 
                        "describeSObjects on a single object type as a List did not return a Map")
        pass

    def testDescribeTabs(self):
        """ Testing the describeTabs call """
        tabs = self.sfdc.describeTabs()
        self.assert_(type(tabs) == types.DictType)
        self.assert_(type(tabs[tabs.keys()[0]]) == types.DictType)
        return
    pass

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Connection_test))
    return suite

if __name__ == "__main__":
    unittest.main()
