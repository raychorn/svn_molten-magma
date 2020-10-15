import pprint

from SOAPpy import WSDL
from SOAPpy.Types import structType, stringType

from RawSfdcConnection import RawSfdcConnection

from SObjectClassFactory import SObjectClassFactory

wsdlpath = "/home/surf/workspace/py_appforce/WSDL/partner60.wsdl.xml"
namespace="urn:partner.soap.sforce.com"
cxn = RawSfdcConnection(wsdlpath, namespace, 'surf@surfous.com', 'frisbol7')

WSDL.Config.dumpSOAPOut = True

#cxn = SfdcConnection('kshuk@molten-magma.com', 'frisbol7')

# try a datetime call
#serverDatetime = cxn.getServerTimestamp()
#print serverDatetime


# try a retrieve
#Case = SObjectClassFactory(cxn, 'Case')

sObjectType = stringType('Case', name='type', typed=False, attrs={'xmlns': 'urn:sobject.partner.soap.sforce.com'})
case1 = {'type': sObjectType,
         'Subject': 'Test Create Case Subject 1',
         'Status': 'New',
         'Origin': 'Email',
         'Description': 'Hommina hommina hommina'}


case2 = {'Subject': 'Test Create Case Subject 2',
         'Status': 'New',
         'Origin': 'Phone',
         'Description': 'Bippity boppity boo!'}



case1s = structType(data=case1, typed=False)
case2s = structType(data=case2, typed=False)

case2s._addItem('type', sObjectType)

saveResult = cxn.sfdc.create(case2s)
pprint.pprint(saveResult)
