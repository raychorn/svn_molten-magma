#!/usr/bin/env python2.3
"""
By default, cases (namely CRs and Benchmarks) are visible to customers
in SalesForce.  We do not want this, so this simple script searches
for Cases which are visible to customers and makes them invisible.
"""
#version = 1.0  # Mar 16, 2004. First reworked version using only new API
version = 2.0  # Jan 4, 2004. Second reworked version using only SOAP API

import time
import sys

from sfMagma import SFMagmaTool
from sfConstant import *

# Map of Case Type to Case Type ID
# Add to this dictionary to hide more case record types
CaseStoI = { 'CR'        : '01230000000001YAAQ',
             'PLD CR'    : '0123000000000HIAAY',
             'Phy Ver CR': '0123000000003qfAAA',
             'Benchmark' : '01230000000008jAAA' }

# Generate an inverse map of Case Type ID to Case Type
CaseItoS = {}
for rectype in CaseStoI.keys():
    CaseItoS[CaseStoI[rectype]] = rectype

class hideCaseBase(SFMagmaTool):

    visibleCases = []
    logName = "hideCase"

    def __init__(self):

        SFMagmaTool.__init__(self, logname=self.logName)
        self.loadVisibleCases()
        return
    ## END __init__

    def loadVisibleCases(self):
        """
        query for an array of Cases which are visible to the customer
        and set the results in member variable visibleCases.
        """

        fields = ('Id', 'IsVisibleInCss', 'Customer_Visible__c', 'CaseNumber',
                  'RecordTypeId')
        
        rectypeFilterList = []
        for rectype in CaseStoI.keys():
            rectypeFilterList.append(['RecordTypeId','=',CaseStoI[rectype]])
            rectypeFilterList.append('or')
            continue
              
        rectypeFilterList.pop()

        f1 = ['Customer_Visible__c', '=', 'No']
        f2 = ['IsVisibleInCss', '=', True]

        where = [f1, 'and', f2, 'and', '(']
        where.extend(rectypeFilterList)
        where.append(')')

        res = self.query(CASE_OBJ, where, fields)
        if res in BAD_INFO_LIST:
            res = []
            pass
        self.visibleCases = res
        return
    ## END loadVisibleCases


    def hideCase(self, case):
        """
        Given a Case, set it to be hidden from the customer
        """
        cid = case.get('Id')
        data = {'Id':cid,
                'IsVisibleInCss':False}

        #print data
        res = self.update(CASE_OBJ, data)
        res = [cid]
        if res in BAD_INFO_LIST:
            resultStr = 'Failed to hide case %s' %cid
        else:
            resultStr = "%s %s (%s)" %(CaseItoS[case.get('RecordTypeId')],
                                       cid, case.get('CaseNumber'))
        self.setLog(resultStr, 'info')
        return resultStr
    ## END hideCase
        
    def hideVisibleCases(self):
        resultStrList = []

        totalMsg = "Total Visible Cases found: %s" %len(self.visibleCases)
        self.setLog(totalMsg, 'info')

        for visibleCase in self.visibleCases:
            hideResult = self.hideCase(visibleCase)
            resultStrList.append(hideResult + "\n")
            
        return resultStrList
    ## END hideVisibleCases


    def do(self):
        """
        The main flow for hideCasesFromCust
        """
        startTime = time.time()

        if len(self.visibleCases) == 0:
            self.setLog('No work to do... Exiting', 'info')
            return None

        hiddenCaseList = self.hideVisibleCases()

        # report on changes made by email
        elapsedSecs = time.time() - startTime
        doneMsg = 'Hid %d Cases. Total runtime was %s seconds.' \
                  %(len(hiddenCaseList), int(elapsedSecs))
        self.setLog(doneMsg, 'info')
    ## END do
        
def main():
    hideBase = hideCaseBase()
    hideBase.do()
## END main()    

if __name__=='__main__':
    main()


        
