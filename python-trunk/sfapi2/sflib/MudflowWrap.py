"""
Gather information about a branch from the SCM mudflow script
"""
import os
import sys
import pprint
from tempfile import mkdtemp
from optparse import OptionParser
import urllib
import types
import socket
import time

import XmlHelper

MUDFLOW_LOG = "/local/zope/mudflow/mudflow_run.log"

CTPATH = '/usr/atria/bin'
CT = os.path.join(CTPATH, 'cleartool')
#MUDFLOW = '/home/scmbuild/.mudflow/bin/mudflow.sh'
ccView = 'salesforce_verification'
MUDFLOW = '/home/scmbuild/.mudflow/bin/mudflow-test-011107.sh'

class MudflowWrap:

    branch=''
    checksince=None

    def __init__(self, xmldata):
        self.brInfoMap = {}
        xmldata = xmldata.strip()
        if xmldata not in [None, '', [], {}]:
            try:
                brInfoMap = XmlHelper.parseXml(xmldata=xmldata)
            except Exception, e:
		msg = []
		msg.append("Error: %s" % e)
		msg.append("xml data:\n-----\n%s\n-----" % xmldata)
                print '\n'.join(msg)

            self.brInfoMap = brInfoMap.get('magma-sf-checklist',{})
        return
    ## END __init__

    def remoteMudflow(klass, branchName, passmud,stream,checkSince=None):
        """
        constructor for a remote call to mudflow
        """
        stream=stream.lower()
        if stream in ['blast5']:
            ccView='salesforce_verification_blast5'
        elif stream in ['talus1.0']:
            ccView='salesforce_verification_talus1.0'
        else:
            ccView = 'salesforce_verification'
              
        # call the remote mudflow
	msg = "MUDFLOW CHECK %s" %passmud
        #mudflowUrl = 'http://granite.moltenmagma.com/branch/MudTool/doMud?branch=%s' %branchName
        mudflowUrl = 'http://ebb.moltenmagma.com/branch/MudTool/doMud?branch=%s&mudcheck=%s&st=%s' %(branchName,passmud,stream)
        #mudflowUrl = 'http://localhost:9080/branch/MudTool/doMud?branch=%s' %branchName

        if checkSince is not None:
            mudflowUrl += "&checksince=%s" %checkSince

        oldTimeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(None)
        
	msg = "Waiting to read the XML file"
        print msg

        opener = urllib.FancyURLopener()
        f = opener.open(mudflowUrl)
        xmlData = f.read()
        f.close()
	msg = []
	msg.append("After reading XML data")
	msg.append("XML FILE %s" % xmlData)
        print msg[0]

        socket.setdefaulttimeout(oldTimeout)

	klass.branch = branchName
        klass.checksince = checkSince

        return MudflowWrap(xmlData)

    remoteMudflow = classmethod(remoteMudflow)

    def localMudflow(klass, branchName, checkSince=None):
        xmlData = runMudflow(branchName, checkSince)

	klass.branch = branchName
        klass.checksince = checkSince
        return MudflowWrap(xmlData)

    localMudflow = classmethod(localMudflow)
    
    def showStruct(self):
        return pprint.pformat(self.brInfoMap)

##    def hasAllFilesClassified(self):
##        """
##        Returns True if all files have been classified in mudflow, False if not
##        """
##        result = False
##        if checkSomeDataForClassified:
##            result = True

##        return result
##    ## END hasAllFilesClassified
    
    def hasErrorResult(self):
        result = self.brInfoMap.get('result', None)

        if result is not None:
            return True

        return False
    ## hasErrorResult
            
    def hasMudflowRunSuccessfully(self):
        result = self.brInfoMap.get('mudflowerror', None)
        #print "hasMudflowRunSuccessfully ......result %s"%result

        if result in [None,'']:
            #print "NO MUDFLOW ERROR ................."
            return True

        return False
    ## hasMudflowRunSuccessfully
            

    def hasAllFilesCheckedIn(self):
        result = False

        numCheckedOut = 0
        checkout_count = self.brInfoMap.get('checkout_count', None)
        if checkout_count is not None:
            numCheckedOut = checkout_count['count'] 
            pass
        if numCheckedOut == '0':
            result = True
            pass

        return result
    ## END hasFilesCheckedIn

    def hasTest(self):
        result = False
        td = self.brInfoMap.get('test_files_changed', 0)
        if td > 0:
            result = True
            pass
        
        return result
    ## END hasTest

    def hasCleanBackMerge(self):
        bm = self.brInfoMap.get('backmerge', None)
	msg = "mudflow error hasCleanBackMerge......result %s"%self.brInfoMap
        result = False

        if bm in [None,[],{}]:
            result = True
            pass
	msg = "hasCleanBackMerge:::  %s"%result
        return result
    ## END hasCleanBackMerge


    def getPartitionViolationDict(self):
        pv = self.brInfoMap.get('partition_violation', None)
	# Create a dictionary for each partition violation
	# Example:
	#	p_dict['cteli']=['/vobs/magmadt/scripts/cov.sh','cteli','infra']
	
	# Create an empty dictionary
        p_dict = {}

        #print "pv is..."
        #pprint.pprint(pv)
        #print "end pv"
        if type(pv) not in [types.NoneType,types.ListType,types.TupleType]:
            pv = [pv,]
            pass

        if pv is not None:
	    # Iterate through the children
	    for violation in pv:
		filename = violation['file']
		user = violation['user']
		contact = violation['contact']
		partition = violation['partition']

                p_item = {'file': filename,
                          'user': user,
                          'partition': partition}

                p_list = p_dict.get(contact, [])
                p_list.append(p_item)
                p_dict[contact] = p_list
                
            pass

        return p_dict
    ## END getPartitionViolationDict

    def hasDelta(self):
        """
        Function checks to see if there is any delta data.
        Delta data is defined as any new changes to the clearcase DB
        since the 'submitbranch'
        """
        # No delta data
        result = False
        td = self.brInfoMap.get('delta_file', 0)
        if td > 0:
            result = True
            pass
        
        return result
    ## END hasDelta 

    def checkMudflow(self, force_submission=False):
        run_successful = self.hasMudflowRunSuccessfully()

	checkout_pass = self.hasAllFilesCheckedIn()
	unit_test_pass = self.hasTest()
	back_merge_pass = self.hasCleanBackMerge()

	return run_successful and checkout_pass and ( unit_test_pass or force_submission ) and ( back_merge_pass or force_submission )

    ## END checkMudflowReport

    def errorReport(self,force_submission=False):
	error_report = 'Error Report\n\tBranch: ' +  MudflowWrap.branch + '\n\n'

        # if mudflow didn't run successfully, dump the error, then bail.
        if self.hasMudflowRunSuccessfully() is False:
            error_report += 'An error has occurred in the integration with the Mudflow script:\n'
            error_report += '   %s\n\n' %self.brInfoMap.get('mudflowerror','')
            error_report += 'Please report this to sf_mudflow@molten-magma.com\n\n'
            return error_report

	# If there are files still checkout update report
	if ( self.hasAllFilesCheckedIn() is False):
            error_report += '======> FILES STILL CHECKEDOUT, please checkin all files and resubmit branch:' + '\n\n'

            files = self.brInfoMap.get('checkout_count', {}).get('checkedout_file', [])
            if type(files) not in [types.ListType]:
                files = [files,]
                pass

            for f in files:
                error_report += '\t%s\n' %f
            
            error_report += '\t(You may not override this error)\n'
	
	# If there are no testcases please update report
	# (special case where unit tests are skipped on purpose are processed with "--force"
	if ( self.hasTest() is False and force_submission is False):
            error_report += '\n\n======> This branch has no test changes, please create testcases for the changes\n\n'
	    #error_report += '\t(Please use "--force" to override)' + '\n'

	# If the files need to be back merged, update report
	# (special case where the backmerge is not needed are processed with "--force"
	if ( self.hasCleanBackMerge() is False and force_submission is False):
	    error_report += '\n\n======> The following files need a backmerge\n\n'
            bm = self.brInfoMap.get('backmerge', None)

            if type(bm) is types.DictType:
                bm = [bm,]
                pass
            
	    for i in bm:
	    	error_report += '\t\t%s\n' %i['file']+'\n'
	    #error_report += '\t(Please use "--force" to override)' + '\n'

	return error_report

    ## END errorReport

## class MudflowWrap

def runMudflow(branchName, checkSince=None):
    global ccView
    global CT
    global MUDFLOW
    global MUDFLOW_LOG

    logf = file(MUDFLOW_LOG, 'a+')

    saveUmask = os.system('umask')
    curDirPath = os.getcwd()
    tmpDirPath = mkdtemp()
    
    os.chdir(tmpDirPath)
    
    mudflowCmd = '%s -sf-checklist %s' %(MUDFLOW, branchName)
    if checkSince is not None:
        mudflowCmd += ' -checksince %s' %checkSince
        pass
    
    ccCmd = '%s setview -exec "%s" %s' %(CT, mudflowCmd, ccView)

    #print ccCmd
    sTime = time.time()

    logf.write("<<<:: BEGIN %s %s: %s\n" %(branchName, tmpDirPath, time.ctime(sTime)))
    logf.flush()
    
    #print >> sys.stderr
    os.system('umask 000')
    ph = os.popen(ccCmd)
    for line in ph.readlines():
        #print line,
        continue
    ph.close()
    os.system('umask %s' %saveUmask)

    eTime = time.time()
    elapseTime = eTime - sTime

    #print >> sys.__stdout__
    
    # find the sf.*.xml file
    tempFiles = os.listdir(tmpDirPath)
    
    brInfoPath = ""
    for filePath in tempFiles:
        if filePath[:3] == 'sf.' and filePath[-4:] == '.xml':
            # this is our result file.
            brInfoPath = filePath
            break
        continue

    xmldata = ""

    if len(brInfoPath):
        fh = file(brInfoPath)
        xmldata =  fh.read()
        fh.close()
    else:
        errmsg = "mudflow script didn't generate sf.*.xml file"
	msg = ">>>!! FAIL %s %s: %s; Time Elapsed %.2f\n" %(branchName, tmpDirPath, errmsg, elapseTime)
        logf.write(msg)
        
        xmldata =  '<magma-sf-checklist>\n'
        xmldata += '  <mudflowerror>%s</mudflowerror>\n' %errmsg
        xmldata +=  '</magma-sf-checklist>\n'
        return xmldata

    # write out the xml data and cleanup
    logf.write("%s\n" %xmldata)

    msg = ">>>:: END %s %s: %s; Time Elapsed %.2f\n" %(branchName, tmpDirPath, time.ctime(eTime), elapseTime)
    logf.write(msg)
    logf.flush()
    logf.close()

    for filePath in tempFiles:
        os.remove(filePath)
        continue
    
    # finish cleanup
    os.chdir(curDirPath)
    
    os.rmdir(tmpDirPath)
    
    return xmldata

    
    
if  __name__ == '__main__':

    op = OptionParser()

    op.add_option('-l', '--local', dest='local', action='store_true',
                  default=False)
    op.add_option('-r', '--remote', dest='remote', action='store_true',
                  default=False)
    #op.add_option('-f', '--force', dest='force', action='store_true',
    #              default=False)
    op.add_option('-f', '--forcenew', dest='force', action='store_true',
                  default=False)

    op.add_option('--checksince', dest='checksince', default=None)

    opts, args = op.parse_args()

    if len(args) < 1:
        print "You must supply a branch name!"
        sys.exit(1)

    branchName = args[0]

    mf = None
    if opts.local is True:
        mf = MudflowWrap.localMudflow(branchName, opts.checksince)
    elif opts.remote is True:
        mf = MudflowWrap.remoteMudflow(branchName, opts.checksince)
    else:
        # just run the wrapper script
        xmlout = runMudflow(branchName, opts.checksince)
        print xmlout
        sys.exit(0)
        pass
    
    if mf is not None:
        print mf.showStruct()
        pass

    if mf.checkMudflow(force_submission=opts.force) is False:
	print 'Submission can not proceed; please see the error report'
	print '(-- in case of problems, please contact '
        print '    salesforce-support@molten-magma.com or scm@molten-magma.com --)\n'
	print mf.errorReport(opts.force)
	sys.exit(-1);
