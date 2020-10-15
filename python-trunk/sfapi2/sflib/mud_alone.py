import os, re, sys, string, time
import socket
import cStringIO as StringIO
from tempfile import mkdtemp
import logging, logging.handlers  
import pprint
from optparse import OptionParser
import urllib
import types
import XmlHelper

MUDFLOW_LOG = "/local/zope/mudflow/mudflow_run.log"
CTPATH = '/usr/atria/bin'
CT = os.path.join(CTPATH, 'cleartool')
MUDFLOW = '/home/scmbuild/.mudflow/bin/mudflow.sh'
ccView = 'salesforce_verification'

socket.setdefaulttimeout(None)
    
class MudTool:
    """ Main entry point for running the external mudflow command
    """
    id        = 'MudTool'
    meta_type = 'MudTool Container'
    isPrincipiaFolderish = 1 
    content_icon = 'images/workspace.gif'
    
        
    def runMudflow(self, branchName='', checkSince=None):
        
        saveUmask = os.system('umask')
        tmpDirPath = mkdtemp()
        self.log("Temp dir %s" %tmpDirPath,1)      
        #curDirPath = os.getcwd()    # this line broke Jan 25th because????
	    # need to find if we need to be in a certain directory for some other method
        try: curDirPath = os.getcwd()    
        except: curDirPath = '/local/zope/server/var'  
               
        self.log("Current Directory %s" %curDirPath,1)
        os.chdir(tmpDirPath)
        
        self.log("Current New Working directory: %s" %tmpDirPath)

        mudflowCmd = '%s -sf-checklist %s' %(MUDFLOW, branchName)
        if checkSince is not None:
            mudflowCmd += ' -checksince %s' %checkSince
            pass

        ccCmd = '%s setview -exec "%s" %s' %(CT, mudflowCmd, ccView)
        sTime = time.time() 
        self.log("<<<:: BEGIN %s %s: %s\n" %(branchName, tmpDirPath, time.ctime(sTime)))
        
        os.system('umask 000')
        ph = os.popen(ccCmd)
        for line in ph.readlines():
            self.log("Command Output %s " %line)
            continue
        ph.close()
        os.system('umask %s' %saveUmask)
        self.log("Command is %s" %ccCmd)

        eTime = time.time()
        elapseTime = eTime - sTime
        tempFiles = os.listdir(tmpDirPath)       
        brInfoPath = ""
        self.log("TEMP Files: %s" %(tempFiles))
        for filePath in tempFiles:
            if filePath[:3] == 'sf.' and filePath[-4:] == '.xml':
                # this is our result file.
                #self.log("BR INFO: %s" %(filePath))
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
            self.log(">>>!! FAIL %s %s: %s; Time Elapsed %.2f\n" %(branchName, tmpDirPath, errmsg, elapseTime))

            xmldata =  '<magma-sf-checklist>\n'
            xmldata += '  <mudflowerror>%s</mudflowerror>\n' %errmsg
            xmldata +=  '</magma-sf-checklist>\n'
            return xmldata
            pass

        # write out the xml data and cleanup
        logf.write("%s\n" %xmldata)

        self.log(">>>:: END %s %s: %s; Time Elapsed %.2f\n" %(branchName, tmpDirPath, time.ctime(eTime), elapseTime))

        for filePath in tempFiles:
            os.remove(filePath)
            continue

        os.chdir(curDirPath)
        os.rmdir(tmpDirPath)
        return xmldata

        
    def setData(self, data={}):
        """ set the data """
        self._data = data

    def getData(self):
        """ set the data """
        if not hasattr(self, '_data'):
            self.resetData()
        return self._data

    def getActions(self):
        """ set the data """
        return self.getData()
    
    def resetData(self):
        """ reset """
        self._data = []
 
    def getHeadings(self):
        """ return the dictionary keys """
        data = self.getData()
        return data[0].keys()

    def showInfo(self, value):
        """ """
        return 'Some information: %s'%value

    def __initProps__(self):
        self._data = {}
        self._data['globalCategories', '']
        self._data['activeState', 1]
        self._data['updateSalesForce', 1]
        self._data['logLevel', '1']

    def log(self, msg, level=1, severity=0, tag='', sum=''):
        """ Write out log messages """
        if type(level) not in [type(1),type(1.0)]:
            level = 1
        db = 2
        db = int(db)
        if db <= level:  
            return
        if severity not in [-200,-100,0,100,200,300]:
            severity = 0
        if tag in [None,'']:
            tag = self.meta_type
        if severity > 0:
            sum = msg
            msg = self.getExceptionStr()
        # fix this by using setLog from CMFSForce.sflib.sfBase3.py   
        logf = file(MUDFLOW_LOG, 'a+')
        secs = time.gmtime(time.time()+0)
        tsnow = time.strftime('%Y-%m-%dT%H:%M:%S', secs)
        #tsnow = time.ctime(secs)
        entry = '%s %s %s %s '%(tsnow, tag, severity, msg) 
        logf.write(entry)
        logf.flush()
        
        
    
    def getExceptionStr(self):
        """Get exception string"""
        text='\n'.join(traceback.format_exception(*sys.exc_info()))
        return text


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
                print "Error: %s" %e
                print "xml data:\n-----\n%s\n-----" %xmldata

            self.brInfoMap = brInfoMap.get('magma-sf-checklist',{})
        return
    ## END __init__

    def remoteMudflow(klass, branchName, checkSince=None):
        """
        constructor for a remote call to mudflow
        """
        # call the remote mudflow
        mudflowUrl = 'http://mudflow.moltenmagma.com/branch/MudTool/doMud?branch=%s' %branchName

        if checkSince is not None:
            mudflowUrl += "&checksince=%s" %checkSince
            pass

        oldTimeout = socket.getdefaulttimeout()
        mudflowTimeout = 1.0 * 60 * 30 # 30 min timeout for mudflow
        socket.setdefaulttimeout(mudflowTimeout)

        opener = urllib.FancyURLopener()
        f = opener.open(mudflowUrl)
        xmlData = f.read()
        f.close()

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
        result = False

        if bm in [None,[],{}]:
            result = True
            pass
        
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
	checkout_pass = self.hasAllFilesCheckedIn()
	unit_test_pass = self.hasTest()
	back_merge_pass = self.hasCleanBackMerge()

        

	return checkout_pass and ( unit_test_pass or force_submission ) and ( back_merge_pass or force_submission )

    ## END checkMudflowReport

    def errorReport(self,force_submission=False):
	error_report = 'Error Report\n\tBranch: ' +  MudflowWrap.branch + '\n\n'

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
	    error_report += '\t(Please use "--force" to override)' + '\n'

	# If the files need to be back merged, update report
	# (special case where the backmerge is not needed are processed with "--force"
	if ( self.hasCleanBackMerge() is False and force_submission is False):
	    error_report += '\n\n======> The following files need a backmerge\n\n'
            bm = self.brInfoMap.get('backmerge', None)

            if type(bm) is types.DictType:
                bm = [bm,]
                pass
            
	    for i in bm:
	    	error_report += '\t\t%s\n' %i['file']
	    error_report += '\t(Please use "--force" to override)' + '\n'

	return error_report

    ## END errorReport
    pass
## class MudflowWrap


def runMudflow(branchName, checkSince=None):
    """ this is duplicate and dead, delete meeee """
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
        logf.write(">>>!! FAIL %s %s: Couldn't find sf.*.xml file; Time Elapsed %.2f\n" %(branchName, tmpDirPath, elapseTime))
        return xmldata
        pass

    # write out the xml data and cleanup
    logf.write("%s\n" %xmldata)

    logf.write(">>>:: END %s %s: %s; Time Elapsed %.2f\n" %(branchName, tmpDirPath, time.ctime(eTime), elapseTime))
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

    op.add_option('-l', '--local', dest='local', action='store_true', default=False)
    op.add_option('-r', '--remote', dest='remote', action='store_true',default=False)
    op.add_option('-f', '--force', dest='force', action='store_true',  default=False)
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
        mft = MudTool()
        xmlout = mft.runMudflow(branchName, opts.checksince)
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