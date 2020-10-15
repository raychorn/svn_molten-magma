"""
List all CRs that have been closed in the last X days
03/22/2007 Chip Vanek - first release
08/21/2007 Chip Vanek - review of code and re-release to Manish Desai
"""
import sys, time, os
import StringIO, getopt
import copy, re
import traceback
import pprint
from types import ListType, TupleType, DictType, DictionaryType
from optparse import OptionParser, OptionGroup
from SfConstant import *
#from SFUtil import *
from Properties import Properties
from SfdcConnection import SfdcConnection
from SObjectClassFactory import SObjectClassFactory
from SfdcApiFault import SfdcApiFaultFactory

from SfConnection import TestCxn

from Util import booleanize, listify
#import PysfdcLogger, logging
#log = logging.getLogger('pysfdc.listCRs')


class ListCRs:
    
    modList = []
    loadFromSF = False
    seqTypes = [ListType, TupleType]

    def setUp(self):
        self.cxn = TestCxn().cxn
        self.idList = []
        return
    
    def getSFData(self, since, stream="all"):
        """
        Get the latest Cases
        'The Original!' [TM]
        """
        brId=None;
        queryStr1 ="Select c.Id, c.CaseNumber, c.ClosedDate, c.OwnerId, c.Status from Case c "
        if stream != "all":
            queryStr1 += " WHERE ClosedDate = LAST_N_DAYS:%s AND X1st_Stream__c = %s order by ClosedDate"%(since, stream)
        else:
            queryStr1 += " WHERE ClosedDate = LAST_N_DAYS:%s order by ClosedDate"%(since)
            
        #queryStr1 ="Select c.Id, c.CaseNumber, c.ClosedDate, c.OwnerId, c.Status from Case c WHERE ClosedDate = LAST_N_DAYS:%s order by ClosedDate"%since
        queryList1=self.cxn.query(queryStr1)
               
        if queryList1 not in BAD_INFO_LIST:
            found = len(queryList1)
            print 'Found %s Cases closed in the last %s days'%(found,since)
            return queryList1
            #for qr1 in queryList1:
            #    brId=qr1.get('Id')
        else:
            print "No Cases found in the last '%s' days" %since
            return []
        
     
    def listCRsCL(self, since, options, st, teamTool=None, checkTmb=True, scmFlag=False):
        """ command line logic for listCRs
        """
        stream = "all"
        if options is not None:
            debug = options.debug
            stream = options.stream
    
        cList = self.getSFData(since,stream)
        print 'Found %s closed cases in the last %s days'%(len(cList),since)
        print '==========================================='
        
        for cInfo in cList:   
            if cInfo in [None,'']:
                print 'Please correct input '
                print cInfo
                sys.exit()
            elif type(cInfo) is self.seqTypes:
                print 'Please correct input '
                print cInfo
                sys.exit()
            else:
                cn = cInfo.get('CaseNumber')
                cnum = '%s' %int(cn)
                dt = cInfo.get('ClosedDate')
                st = cInfo.get('Status')
                print '%s :: %s :: %s'%(cnum,dt,st)
        return
    
    def findCRStatus(self,crNo):
        crStatus=''
        crNo='%'+crNo        
        queryStr="Select Id,CaseNumber, Status from Case where CaseNumber like '%s'"%(crNo)                
        queryList=self.cxn.query(queryStr)           
        if queryList not in BAD_INFO_LIST:
            for qr in queryList:
                crStatus=qr.get('Status')                      
        return crStatus
    
    
    
    def parseBranchListFile(self,path):
        """ parse a file to extract the branch names and return a list of
        the branch names """
            
        branchList = []    
        if path not in [None,''] and os.path.exists(path):
            fh = file(path)
    
            for line in fh.readlines():               
                line = line.strip()            
                splitline = line.split()
                if len(splitline) == 1:
                    # ADD lower() HERE TO MAKE CASE INSENS.                
                    branchList.append(splitline[0])
                    pass
                continue
            
            fh.close()
            pass
        
        if len(branchList) == 0:
            branchList = None
            pass    
        return branchList
            
        

def usage(err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += 'Default usage is to list Cases closed for the 30 days\n'
    m += '\n Example:\n'
    m += '    closedcases -n 90   \n'     
    m += ' \n'
#    m += ' closedcases -n 60 -s blast5 \n'
    return m

def main_CL():
    """ Command line parsing and and defaults methods    """
    version=1.0
    st = time.time()
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-n", "--days",   dest="days", default="30",     help="Days ago, defaults to 30 days")
    parser.add_option("-s", "--stream", dest="stream", default="all",  help="Code Stream, defaults to all")
    parser.add_option("-u", "--usage",  dest="usage",  default="",      help="Show usage information")
    parser.add_option("-d", "--debug",  dest='debug', action="count",  help="The debug level, use multiple to get more.")
    (options, args) = parser.parse_args()

    if options.debug > 1:
        print ' days  %s' %(options.days)
        print ' args: %s' %args
    else:
        options.debug = 0
    
    if options.usage:
        print usage()
    else:
        obj=ListCRs()
        obj.setUp()
        since = options.days      
        
        #stream = str(stream).strip()           
        obj.listCRsCL(since, options, st)                        
        
    print '\nTook a total of %3.2f secs -^' %(time.time()-st)
    
if __name__ == "__main__":
    main_CL()