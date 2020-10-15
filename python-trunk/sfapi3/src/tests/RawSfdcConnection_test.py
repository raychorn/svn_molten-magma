import unittest

from Properties import Properties
from RawSfdcConnection import RawSfdcConnection
from SObjectClassFactory import SObjectClassFactory
from SfdcApiFault import parseFaultObject

from SOAPpy import faultType

class RawSfdcConnection_test(unittest.TestCase):
    
    def setUp(self):
        self.p = Properties()
    
    def testRawLogin(self):
        """RawSfdcConnection constructor for should succeed with good credentials"""
        try:
            rcxn = RawSfdcConnection(self.p.wsdlPath, self.p.namespace, self.p.testUsername, self.p.testPassword)
        except faultType, f:
            self.fail('login call returned fault: %s' %f)
        except Exception, e:
            self.fail('login call raised exception: %s' %e)
            pass

        return

    def testFailRawLogin(self):
        """RawSfdcConnection constructor should raise an INVALID_LOGIN fault when login with bad credentials"""            
        wrongPassword = '%sZZ' %self.p.testPassword
        
        try:
            rcxn = RawSfdcConnection(self.p.wsdlPath, self.p.namespace, self.p.testUsername, wrongPassword)
        except faultType, f:
            faultDict = parseFaultObject(f)
            self.assertEqual(faultDict.get('exceptionCode'), 'INVALID_LOGIN')
        except Exception, e:
            self.fail('login call with bad credentials raised an exception other than a SOAP fault: %s' %e)
        else:
            self.fail('login call with bad credentials did not raise a fault at all')
            pass
        return

    pass
    
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RawSfdcConnection_test))
    return suite
    
if __name__ == "__main__":
    unittest.main()   