import pprint

from TestSupport import TestData

from SOAPpy import WSDL

from SfdcConnection import SfdcConnection

from SObjectClassFactory import SObjectClassFactory


#cxn = SfdcConnection('surf@surfous.com', 'frisbol7')
#cxn = SfdcConnection('ramya@molten-magma.com', '23ash')
#cxn = SfdcConnection('kshuk@molten-magma.com', 'frisbol7')

# try a datetime call
#serverDatetime = cxn.getServerTimestamp()
#print serverDatetime

print "Got Connection object"

#queryString = "select Id from Case where Subject like '%Test Create Case%'"
queryString = "select Id from Case where Subject = 'Third CR for testing workflow'"


#WSDL.Config.debug = True
#SDL.Config.dumpSOAPOut = True

queryResultBatch = cxn.query(queryString)
print "After query... %s"%queryResultBatch
pprint.pprint(dir(queryResultBatch))

deleteResult = queryResultBatch.delete()

print deleteResult
