"""
Test File to test ceratil API functionalities
"""

sfUrl = 'https://na1.salesforce.com'

import pprint
import sys
import textwrap
from optparse import OptionParser

from sfMagma import *
from sfConstant import *
from sfUtil import *

class TestTool(SFMagmaTool):
    logname = 'TestTool'
    
    
    def getTestObjects(self):
        
                
        """
        Get all records form the UserChanges object and update contact and user objects
        """
        print "Querying all required data from salesforce...."
        
        
        #soql1 = "Select Id from Product2 where RecordTypeId='0123000000008OwAAI'" #Record Type: End of life # 21
        #soql1 = "Select Id from Product2 where RecordTypeId='0123000000007kAAAQ'" #Record Type:Unreleased Product #44
        soql1 = "Select Id from Product2 where RecordTypeId='0123000000007k9AAA'" #Record Type:Revenue Planning #44
        ret = self.query('Product2', soql=soql1)                                                                                  
            
        print "Number of Products records that were quried are.. %s " %len(ret)
        return 
    
    
    
def main():    
    n=TestTool()
    n.getTestObjects()
    

if __name__ == "__main__":
    main()
    