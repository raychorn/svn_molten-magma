#!/usr/bin/env python2.3
"""
By default, cases (namely CRs and Benchmarks) are visible to customers
in SalesForce.  We do not want this, so this simple script searches
for Cases which are visible to customers and makes them invisible.
"""

version = 1.0  # Mar 16, 2004. First reworked version using only new API

import string, re, getpass, socket, smtplib, time, pprint
import ConfigHelper
import cStringIO as StringIO

try: 
    import mailServer
except:
    print 'Please ensure that the "mailServer.py[co]" file is in your'
    print 'PYTHONPATH environment variable list.'

try:
    from sforceBase import *	    	    
except:
    print 'Please ensure that the "sforceXMLRPC.py[co]" file is in your'
    print 'PYTHONPATH environment variable list.'


### Global definitions ###

# Map of Case Type to Case Type ID
# Add to this dictionary to hide more case record types
CaseStoI = { 'CR'        : '01230000000001Y',
             'Benchmark' : '01230000000008j' }

# Generate an inverse map of Case Type ID to Case Type
CaseItoS = {}
for type in CaseStoI.keys():
            CaseItoS[CaseStoI[type]] = type

### END Global definitions ###

class hideCaseBase(SalesForceBase):
    """
    This class creates an object for the specified case which
    presents certain case information and contains methods for
    inserting, updating, adding a task, or attaching to this case
    in the SalesForce.com database.
    """

    visibleCases = []
    logName = "sf.hideCase"

    def __init__(self, props):
        SalesForceBase.__init__(self, logname=self.logName)
        self.props = props
        self.loadVisibleCases()
    ## END __init__(self)
    
    def loadVisibleCases(self):		
        """
        query for an array of Cases which are visible to the customer
        and set the results in member variable visibleCases.
        Currently, we are insterested in CRs and Benchmarks
        """
        sfType = 'case'
        cFields, cLabels, cFList, cCFList = self.getFieldsDictsLocal(sfType)
 
        recordTypeFilterList = []
        for type in CaseStoI.keys():
            recordTypeFilterList.append({'field':'recordTypeID',
                                         'value':CaseStoI[type]})
        
        filter = [{'field':cFields['Visible in Self-Service Portal'],
                   'value':True},
                  {'field':cFields['Customer Visible'],
                   'value':'No'},
                  {'operator': 'or', 'value': recordTypeFilterList}
                  ]

        self.dlog.debug(pprint.pformat(filter))

        fieldList =['id', cFields['Visible in Self-Service Portal'],
                    cFields['Customer Visible'], 'caseNumber', 'recordTypeID']

        vcrs = self.sfAPI.simpleFilterQuery(sfType, filter, fieldList)
        
        self.visibleCases = vcrs
    ## END loadVisibleCases(self)


    def hideCase(self, case):
        """
        Given a Case, set it to be hidden from the customer
        """
        cid = case.get('id')
        recordMap = {'id':cid,'external':False}

        updateID = self.sfAPI.update(recordMap, 'case')
        resultStr = "%s %s %s" %(CaseItoS[case.get('recordTypeID')], cid,
                                 case.get('caseNumber'))
        self.dlog.info("Hid Case: %s" %resultStr)

        return resultStr
    ## END hideCase(self, case)


    def hideVisibleCases(self):
        resultStrList = []

        totalMsg = "Total Visible Cases found: %s" %len(self.visibleCases)
        self.dlog.info(totalMsg)

        for visibleCase in self.visibleCases:
            hideResult = self.hideCase(visibleCase)
            resultStrList.append(hideResult + "\n")
            
        return resultStrList
    ## END  hideVisibleCases(self)


    def do(self):
        """
        The main flow for hideCasesFromCust
        """
        startTime = time.time()

        self.getConnectInfo(version, startTime)

        if len(self.visibleCases) == 0:
            self.dlog.info('No work to do... Exiting')
            return None

        hiddenCaseList = self.hideVisibleCases()

        # report on changes made by email
        elapsedSecs = time.time() - startTime
        self.dlog.info('Hid %d Cases. Total runtime was %s seconds.',
                          len(hiddenCaseList), elapsedSecs)
    ## END do()

def main():
    # Fetch the config
    props = ConfigHelper.fetchConfig('conf/sfutil.cfg')
    
    hideBase = hideCaseBase(props)
    hideBase.do()
## END main()    


if __name__=='__main__':
    main()

