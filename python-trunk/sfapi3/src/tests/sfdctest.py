import pprint

from TestSupport import TestData

from SOAPpy import WSDL

from SfdcConnection import SfdcConnection

from SObjectClassFactory import SObjectClassFactory


cxn = SfdcConnection('surf@surfous.com', 'frisbol7')

#cxn = SfdcConnection('kshuk@molten-magma.com', 'frisbol7')

# try a datetime call
#serverDatetime = cxn.getServerTimestamp()
#print serverDatetime

fieldlist = ['Id', 'Subject', 'Description']
caseObj = cxn.retrieve('Case', '50030000000LDxF', fieldlist)

print caseObj

caseObj.refresh(allFields=True)

print caseObj


