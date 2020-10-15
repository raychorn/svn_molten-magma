#!/usr/bin/env python2.3
#
# This script wlks files in a  directory tree and extracts info from token
# files
#
version = 1.00    #Nov 11, 2004 - used to get number from sf-scm dropbox

import os, re, sys, string, time, stat
import getopt, copy
import traceback
import cStringIO as StringIO
import csv
from filecmp import *
from itertools import ifilter, ifilterfalse
from types import ListType, TupleType, DictType, DictionaryType
from optparse import OptionParser, OptionGroup

DEFAULT_STREAM = '4'

class Node:
    """ data management structure to load from file and then output
        in multiple formats.  A node hangs in a tree and contains leafs
        or other node objects.  A Node has the basic structure show below.
        A leaf is a core content object that maps to files or display items.
        Node:
           id:    unique id that can be used as a token in other structure
           path:  path to file or XPath to node
           acl:   list of access control tokens
           type:  node usage tokens; rw file path, ro path view, rw service api, ...
           owner: list of [owner token, role, address] triplets
           cdate: Creation date of containing date, int of sec or isoDateTime()
           mdate: Last mod date of containing data, int of sec or isoDateTime()
           topic: ordered list of index words that describe node contents
           info:  human text information about node contents
           data:  list of the actual content items, other nodes or leaves.
           load:  load method to get data from path while updating info and topic
           nodes: list of containing node objects
           nids : list of unique node ids for queries of self.nodes, could be ordered
           status: state of the node; [active|new|changed|check|report|closed]
           action: list of available actions in the present state.
           tool:   reference to a tool object
           toolclass: global name of class to initialize to create a tool
    """
    acl  = ['pub']
    type = ['dir']
    owner= [['god','creator','/']]
    cdate= 0                        # 0 seconds from epoch
    mdate= 0
    views= ['html','xml','rss']
    topic= ['all']
    info = ''
    data = []
    nids = []
    nodes = []
    status= ''
    action= []
    updateList = []
    tool = None
    toolclass = 'NodeTool'
    results  = []
    
    def __init__(self, id='', name='name', path='/', data=None, info=None, tool=None):
        """ create and load node from data passed in or call to load method on path.
        """
        self.id   = self.getNid(id)
        self.name = name
        if tool is None: 
            tool = nodeTool()
        self.tool = tool
        self.rootpath = self.tool.rootpath
        self.path = path
        if info is not None:
            self.info = info      # note this will overwrite info updated by load
        
    def get(self, attr):
        """ generic value getting method """
        getMeth = 'get%s' %attr
        if hasattr(self, getMeth):
            # forgot basic call structure will finish later
            return getattr(self, getMeth)
        if hasattr(self, attr):
            a = getattr(self, attr)
            if len(a) == 1: return a[0]
            return a
        return 'not implemented'
    
    def load(self, p=None):
        """ For default directory implementation load directory list into data
        """
        if p is None: p = self.path
        npath = os.path.join(self.rootpath, p)
        if not os.path.isdir(npath): 
            self.tool.log('fileLoad Not a path %s'%npath)
            return 
        #print 'Loading %s' %npath
        f_stat = os.stat(npath)
        self.adate = f_stat[7]
        self.mdate = f_stat[8]
        self.cdate = f_stat[9]
        self.data = os.listdir(npath)
        msg = 'Loaded %s filenames from %s mdate:%s' %(len(self.data),npath, self.mdate)
        #self.tool.sfb.dlog.debug(msg)
        if self.tool.debug > 1: print msg
    
    def getNid(self, id):
        """ get the next unique node id  """
        
        if id == '': nid = 'id'
        else:        nid = id
        index = len(self.nids)
        while hasattr(self.nids, nid): 
            nid = '%s%s' %(id,index)
        self.nids.append(nid)
        return nid
    
    def getFilesNodes(self, name=None, stream=None):
        """  assume self.data is list of filenames in path and load then in objects 
        """
        self.nodes = []             # empty out old nodes
        for fname in self.data:
            id = fname.split('.')[0]
            id = self.getNid(id)
            fpath = os.path.join(self.path,fname) 
            info = 'File contents of %s' %fname
 #           try:pass
            if 1:
		node = FileNode(id, fname, path=fpath, data=None, info=info, tool=self.tool)
                node.load()
                if fname.find('merged_crs') != -1:   # you found a merged CR file to open and parse
                    node.loadCRs()
                else:
                    node.getTokenFileInfo(stream)
                self.nodes.append(node)
#            except Exception, e:
#                print 'Error %s msg:%s' %(Exception, e)
#                #self.tool.setProblem(p, 'fileLoad', ['Not a path'], npath)

class FileNode(Node):
    """ A subclass of a node that is customised for each specific usage.  Leaves
        that are representing a file contents contain elements that are lines in the
        file.  Leaves that are lines in a file contain words that could be control tokens.
        A leaf will have portable data specific methods that enliven the content.
        Leaf:
           Node.all: the basic node attributes of id, access, views, contents, & state.
           subclass of any method that needs to be different then standard.
    """
    def load(self, path=None, contents=True):
        """ open the file at path and load file lines in data
        """
        if path is None: path = self.path
        fpath = os.path.normpath(os.path.join(self.rootpath,path))
        if not os.path.isfile(fpath): 
            print 'Load error %s is not a file' %(fpath)
            return 
        self.name = os.path.basename(path)
        ext = os.path.splitext(self.name)[1]
        if ext in ['.csv','csv']:  
            type = 'csv'
            print '\nFound a CSV file that I will parse into a list of lists'
            self.loadCSV(fpath)
            return
        if ext in ['.xls','xls']:  type = 'xls'
        else:                      type = 'text'

        if os.path.isfile(fpath):
            f_stat = os.stat(fpath)
            self.adate = f_stat[7]
            self.mdate = f_stat[8]
            self.cdate = f_stat[9]
            
            if contents:
                fp = open(fpath)
                self.data = fp.readlines()
                fp.close()
                if self.tool.debug >1: print 'Loaded %s lines from %s' %(len(self.data),path)
            else:
                self.data = ''
                if self.tool.debug >1: print 'Loaded stat info from %s' %(path)
                
    def loadCSV(self, fpath):
        """ load just as CSV """
        if os.path.isfile(fpath):
            f_stat = os.stat(fpath)
            self.mdate = f_stat[8]
            self.cdate = f_stat[9]
            csvreader = csv.reader(file(fpath), dialect='excel')
            ll = []
            for row in csvreader:
                ll.append(row)
            self.data = ll
            ln = len(ll)
            print 'Loaded %s CSV lines like \n %s' %(ln,ll[int(ln/2)])
        print 'Loaded %s CSV lines from %s' %(len(self.data),fpath)
            
    def loadSSV(self, fpath):
        """ load the rows of the file in a space seperated values, for ps output or log output, very simple parse """
        if os.path.isfile(fpath):
            f_stat = os.stat(fpath)
            self.mdate = f_stat[8]
            self.cdate = f_stat[9]
            #self.tool.sfb.dlog.info('FOUND mdate:%s  %s ', self.mdate, path )
            csvreader = csv.reader(file(fpath), dialect='excel')
            ll = []
            for row in csvreader:
                ll.append(row)
            self.data = ll
            ln = len(ll)
            print 'Loaded %s CSV lines like \n %s' %(ln,ll[int(ln/2)])
        print 'Loaded %s CSV lines from %s' %(len(self.data),fpath)
        
    def getMergedCRsFileInfo(self):
        """
        """
        fileName = self.name
        dateStr  = fileName.split('.',1)[1]
        dateList = dateStr.split('_')
        if len(dateList) == 3: isoDateStr = '%s-%s-%sT00:01:00' %(dateList[0],dateList[1],dateList[2])
        else:                  isoDateStr = 'unknown'
        #self.tool.sfb.log.info('FOUND mergedCR date of %s as %s iso:%s', dateStr, dateList, isoDateStr )
        self.doneDate = isoDateStr
        self.doneDateStr = self.tool.sfb.getTime(self.doneDate)

    def loadCRs(self):
        """ load the CR structure from the data lines loaded from a merged_crs file
        """    
        if len(self.data) == 0: self.load(self.path)
        if len(self.data) == 0:
            self.tool.log('No Merged CRs FOUND in %s %s', self.path, self.id )
            return
        self.getMergedCRsFileInfo()
        self.doneCRs = {}
        for line in self.data:
            lineArray = string.split(line)
            crNum = lineArray[0]
            if ((lineArray[1] == "Already" or lineArray[1] == "already")
                and (lineArray[2] == "Merged" or lineArray[2] == "merged")):
                action = lineArray[1] + ' ' + lineArray[2]
                codeStream = lineArray[4]
                release = lineArray[8]
                self.doneCRs[crNum] = {'action':action, 'cs':codeStream, 'mantlepath':release, 'mantleTS':self.doneDate}
            elif ((lineArray[1] == "No" or lineArray[1] == "no")
                  and (lineArray[2] == "Merge" or lineArray[2] == "merge")
                  and (lineArray[3] == "needed" or lineArray[3] == "Needed")):
                action = lineArray[1] + ' ' + lineArray[2] + ' ' + lineArray[3]
                authority = lineArray[6]
                self.doneCRs[crNum] = {'action':action, 'cs':'na', 'authority':authority, 'mantlepath':'noRelease', 'mantleTS':self.doneDate}
            elif (lineArray[1] == "Merged" or lineArray[1] == "merged"):
                action = lineArray[1]
                codeStream = lineArray[3]
                release = lineArray[7]
                self.doneCRs[crNum] = {'action':action, 'cs':codeStream, 'mantlepath':release, 'mantleTS':self.doneDate}
            elif lineArray[1] == "Correction:":
                action = lineArray[1]
                codeStream = 'N/A'
                release = lineArray[4]
                self.doneCRs[crNum] = {'action':action, 'cs':codeStream, 'mantlepath':release, 'mantleTS':self.doneDate}
            else:
                self.doneCRs[crNum] = 'Not able to detect information!'
            self.tool.log('CR:%s IS %s', crNum,  self.doneCRs[crNum])
        
    def getTokenFileInfo(self, stream=None):
        """ parse crInfo and mantle time stamp from filename
            sets self.branch, self.codeStream
            loads self.doneCRs as {cs:, changes:, action:, branch:, mantleTS:}
        """
        fileName = self.name
        self.branch = 'unknown'
        self.codeStream = '4.0'
        blastStr = 'blast4'
        self.crList = []
        dateStr  = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.mdate))
        self.doneDate = dateStr
        self.doneDateStr = time.strftime("%Y/%m/%d", time.localtime(self.mdate))
        self.doneDateTup = time.localtime(self.mdate)
        self.doneDateSec = self.mdate

        brSearch = self.tool.branchRE.search(fileName)
        if brSearch:
            self.branch = brSearch.group('brString')
            blastStr = self.branch.split('_')[0]  
            if stream is not None:
                self.codeStream = stream
            else:
                blastStrLow = string.lower(blastStr)
                if blastStrLow[:5] == 'blast' and blastStrLow != 'blast5':
                    # strip off the first 5 char 'blast'
                    self.codeStream = blastStrLow[5:]         
            if self.codeStream not in ['3','3.0','3.1','3.2','4','4.0','4.1','4.2','4.3','5','blast5','capi1']:
                self.codeStream = '4'
        crSearch = self.tool.crRE.search(fileName)
        if crSearch:
            crStr  = crSearch.group('crString')
            self.crList = string.split(crStr, '_')
        
	self.tool.addSCMDate(self.doneDateStr, self.codeStream, self.branch, self.name)    
        
    
	
    def setSFStatus(self, cstream=None, action='NEW' , fix='no'):
        """  set SalesForce with status information, 
             not working Feb 11, need to rework processfile or pass stream & mante timestamp
        """
        numDone = self.tool.processFile(self.path, self.name, action)
        return numDone


    def out(self):
        """ output the node data to screen
        """    
        s = ''
        modNum = 0
        for crNum in self.doneCRs.keys():
            modNum = modNum + 1
            crInfo = self.doneCRs[crNum]
            s += '\n\t %3s CR:%s MOD%s %s' %(crInfo.get('cs'), crNum, modNum, crInfo.get('changes')) 
        print 'Result: MTS:%s %s%s' %(self.doneDateStr, self.branch, s)    
            
#############################################################################################################
#  Global constants
#############################################################################################################
hr = '_______________________________________________________________________________________\n'

# Compare two files.
# Return:
#       0 for equal
#       1 for different
#       2 for funny cases (can't stat, etc.)
#
def _cmp(a, b, sh, abs=abs, cmp=cmp):
    try:
        return not abs(cmp(a, b, sh))
    except os.error:
        return 2


# Return a copy with items that occur in skip removed.
#
def _filter(flist, skip):
    return list(ifilterfalse(skip.__contains__, flist))

    
class nodeTool(Node):
    """Token and service manage tool.  Session management, token lists. service
       API, and transform methods are stored in the tool.  Every tree has access to 
       one node tool to manage its collection of nodes.  There are sepreate leaf tools.
       Tool:
           Node.all: the basic node attributes of id, access, views, contents, & state.
           version:  version of tool
           libpath:  path to the active software library
           acltree:  tree of access control nodes containing leaves
           typetree: tree of type nodes and their usage description leaves
           viewtree: tree of view implementation leaves
           nodetrees: list of connected data node trees
         
    """
    rootpath = '/home/sfscript'
    problems = {}
    scm_root = '/magma/scm-release/submissions'
    tmp_root = '/var/sfscript/SCM2/submissions'
    numReady = 0
    numDone  = 0
    numDoneMax  = 100
    numPassed = 0
    numPassedMax = 300
    BRs = {}
    CRs = {}
    allStreams = ['3','3.0','3.1','3.2','4.0','4','4.1','blast5','capi']
    blast5RE   = re.compile('blast5',re.I)
    branchRE   = re.compile("\.(?P<brString>[a-zA-Z0-9_\.]+)-?")
    crRE       = re.compile("^(?P<crString>[a-zA-Z0-9_]+)\.")
    commentRE  = re.compile("-+(?P<commentString>.+)$")
    
    reportType = 'line'
    
    def __init__(self, username=None, upass=None, logname='sf.walkScm', sfb=None, options=None):
        self.debug = 1
        if options is not None:
            if hasattr(options, 'debug'):
                dl = options.debug
                if dl is None:
                    self.debug = 0
                else:
                    self.debug = dl
                print 'Set Tool debug level to %s' %self.debug
        if sfb is None:
            sfb = None
        self.sfb  = sfb

    def log(self, msg, type=''):
        """ default logger   """
        print '%s %s'%(type, msg)
	pass
    
    def getRelPath(self, path):
        """ return path string reletive to scm root"""
        lenRootPath = len(self.scm_root)
        return path[lenRootPath:]
        
    def getFullPath(self, path, fileName='', root='tmp'):
        """ get the full path to the SCM or tmp path """
        if path[0] == '/':  path = path[1:]
        if root == 'scm':
            spath = os.path.join(self.scm_root, path, fileName)
        else:
            spath = os.path.join(self.tmp_root, path, fileName)
        return spath

    def getTempPathFromSCMPath(self, path):
        """ get the temp version of the same path"""
        relpath = self.getRelPath(path)
        tmpPath = self.getFullPath(relpath, root='tmp')
        return tmpPath

    def setReport(self, type='line'):
        """ set the type of output report """
        self.reportType=type
        
    def setCodeStreams(self, streams=['4']):
        """ set the list of code stream to act upon """
        if type(streams) is not type([]):
            streams = [streams]
        print 'Setting Code Streams to %s' %streams
        self.codeStreams=streams

    def setCodeStream(self, stream=DEFAULT_STREAM):
        """ set the active code stream to act upon """
        #print 'Setting Code Streams to %s' %stream
        self.codeStream=stream

    def addSCMDate(self, date, cs, branch='',filename=''):
        """ add the changes to this class global dictionary """
        print 'Adding %s  %s  %s  %s'%(date, cs, branch, filename)
	if cs is None: cs ='unknown'
	cs = str(cs)
	if not hasattr(self, 'scmDone'):
	    self.scmDone = {}
        if not self.scmDone.has_key(date):
	    csInfo = {'total':1,'brs':[branch]}
	    csInfo[cs] = 1
	    self.scmDone[date] = csInfo
        else:
            csInfo = self.scmDone.get(date)
	    newInfo = copy.deepcopy(csInfo)
	    for k,v in csInfo.items():
		if k == 'total':
		    newInfo[k] = v+1
		elif k == 'brs':
		    if v not in [None,'']:
 		        newInfo[k] = v.append(branch)
	            else:
			newInfo[k] = [branch]
		elif k == cs:
		    newInfo[k] = v+1
	    if not newInfo.has_key(cs):
		newInfo[cs] = 1
	    self.scmDone[date] = newInfo

    def outputSCMDate(self):
	"""Output CSV of SCM Done trend"""
	result = []
        for date, info in self.scmDone.items():
	    total = info.get('total',0)
	    s40 = info.get('4.0',0)
	    s41 = info.get('4.1',0)
	    s4 = info.get('4',0)
	    s5 = info.get('5',0)
	    brs = info.get('brs',[])
	    msg = '%s,%s,%s,%s,%s,%s,%s,\n'%(date,total,s40,s41,s4,s5,brs)
	    print msg
	    result.append(msg)
	return result
	
    def loadSCMDateFromFile(self, fpath):
        """ load a fpath and update scmDone not needed done by loadfilenodes
        """
        node = FileNode(path=fpath, data=None, info='SCM Drop', tool=self)
        node.getTokenFileInfo()  # load whole csv file in the attribute node.data
        self.numDone += 1

    def getReport(self, path, file, mtime=0):
        """ create a terse output string to explain state of this token based
            on reletive path in scm_root and file name
        """
        pathList = path.split('/')
        blast = pathList[0]
        status, tokens = self.getStatusFromPath(path, file)
        # tokens = [view,branch,scmbranch,bundle,crList,action,info,path,stream]    
        view   = tokens[0]
        branch = tokens[1]
        scmbranch = tokens[2]
        bundle = tokens[3]
        crList = tokens[4]
        action = tokens[5]
        info   = tokens[6]
        
        if file.find('.') != -1:
            crs = file.split('.',1)[0]
            tl  = file.split('.',1)[1] # stream with a '.'
        else:
            tl = file
                
        msg =  "'%s' for the branch: %s \n" %(status, branch)
        msg += '       %s.\n' %(info) 
        if scmbranch != '':
            msg += '        With an SCM branch of %s\n' %scmbranch
        if view != '':
            msg += '        With a SCM view of %s\n' %view
        if bundle != '':
            msg += '        With a Merging Bundle of %s\n' %bundle

        if mtime != 0:
            hrsAgo = (time.time() - mtime)/3600
            msg += '  %s hours ago - %s\n' %(int(hrsAgo), time.ctime(mtime))
        #if tokens[4] != '':
        #    msg += '        %s\n' %tokens[4]

        return msg

    def loadFileInfo(self, filename):
	"""Load the info from this file into a tool based data structure
	   {'fileDate': tokenNumbers}  collection of all files in dir
	   tokenNumbers = {'3.2':#, '4.0':#, '':#, '':#, '':#, [branchlist]}
	"""
	branch, crList = self.getCRBRfromFileName(filename)
	
    def rmGeneric(self, path, __func__):
        """ generic call routine for remove functions """
        try:
            __func__(path)
            if self.debug >1: print 'Removed ' %path
        except OSError, (errno, strerror):
            print 'Error removing %s %s' %(path, strerror)
            
    def removeAll(self, path):
        """ remove the whole directory tree, all files and sub directories """
        if not os.path.isdir(path):
            return
        files=os.listdir(path)
        for x in files:
            fullpath=os.path.join(path, x)
            if os.path.isfile(fullpath):
                self.rmGeneric(fullpath, os.remove)
            elif os.path.isdir(fullpath):
                self.removeAll(fullpath)
                self.rmGeneric(fullpath, os.rmdir)
            
    def getBranchOwnerData(self, fpath):
        """ load a list of definitive branch owners from a ClearCase file export
        """
        if fpath is None: fpath = '/home/sfscript/src/data/branch-owner.csv'
        node = FileNode(path=fpath, data=None, info='Branch Owner Data', tool=self)
        node.load()         # load whole csv file in the attribute self.data
        self.lookupBranchOwner = {}
        # csv format is ['Branch-Label',mail-alias]
        num = 0
        for row in node.data:
            num += 1
            if self.debug > 1: 
                if num < 10: print row
            branch = row[0]
            alias  = row[1]
            self.lookupBranchOwner[branch] = alias
        print '\ngetBranchOwnerData found %s branches as keys with alias of owner\n' %len(self.lookupBranchOwner)

    def getTokensCreatedData(self, fpath):
        """ load a list of token file submission report from a ~/log/note.log extract
        """
        if fpath is None: fpath = '/home/sfscript/tmp/scm-file-create.log'
        node = FileNode(path=fpath, data=None, info='Branch Owner Data', tool=self)
        node.load()         # load whole csv file in the attribute self.data
        self.createdTokenFiles = {}
        

    def setMODStatusFromCSV(self, fpath):
        """ load a CSV from fpath and update MOD status
        """
        node = FileNode(path=fpath, data=None, info='MOD Status', tool=self)
        node.load()  # load whole csv file in the attribute node.data
        # raw CSV format is 4,CR:19941,blast4_riepe_19941,Merged - Testing by Originator
        # node.data format is ['4', 'CR:19941', 'blast4_riepe_19941', 'Merged - Testing by Originator']
        doneList = []
        num = 0
        total = len(node.data)
        #tbObj = SCMTaskBranch(sfTool=self.sfb)
        for row in node.data:
            num += 1
            #if num < 20: print row
            #if len(row) < 2: continue
            stream = row[0]
            crNum = row[1].split(':')[1]
            branch = row[2]
            modStatus = row[3]
            newStatus = 'Closed - Passed'
            doneStr = '%s-%s-%s' %(stream, crNum, branch)
            if doneStr in doneList:
                continue
            doneList.append(doneStr)
            num += 1
            print '%s/%s Updating status %s -> %s' %(num,total, modStatus, newStatus)
            numCRLs = tbObj.setBranchStatusForCRnums( branch=branch, crList=[crNum], cstream=stream, modStatus=newStatus, mantleTime=None, addMissing=False, fix='yes')
            print '%s/%s Updated %s cs:%s cr:%s br:%s  %s -> %s' %(num,total, numCRLs, stream, crNum, branch, modStatus, newStatus)




#############################################################################################################
#   Methods called from the command line - cron oriented to update SalesForce
#############################################################################################################
def processDir(path, format='list'):
    """ main logic method to be called from command line
    """
    if path is None: dPath = '/home/sfscript/data/drop/sf-scm'
    else:            dPath = path 
    ts1 = time.time()
    tool = nodeTool()
    doneTree = Node(id='sf_drop', name='drop', path=dPath, data=None, info='drop directory', tool=tool)
    print 'doneTree created with path:%s rpath:%s' %(doneTree.path, doneTree.rootpath)
    doneTree.load()
    doneTree.getFilesNodes()
    total = len(doneTree.nodes)
    done = 0
    print 'LOADED %s fileNodes in %s' %(total,path)
    
    data = tool.outputSCMDate()
    outfn = 'procFileOUT.txt'
    fp = open(outfn, 'w')
    fp.writelines(data)
    fp.close()    
    
    print 'Wrote %s lines to %s'%(len(data),outfn)
    print '%s\n%s' %(hr,hr)



def usage(err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to search the SCM drop directory\n'
    m += ' '
    m += '    procfiles  -p <file path> \n'
    m += '      or\n'
    return m


def main_CL():
    """ Command line parsing and and defaults method for walkSCM
    """
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-x", "--parm", dest="parm", default="list", help="Format of the output")
    parser.add_option("-t", "--ago",  dest="ago",  default=30.0,     help="Dates ago to look for modified items.")
    parser.add_option("-n", "--num",  dest="num",  default="4000",   help="Max number of items to process")
    parser.add_option("-p", "--path",  dest="path", default="data/drop/sf-scm",     help="file path to work on")
    parser.add_option("-q", "--quiet", dest='quiet', default="1",    help="Show less info in output")
    parser.add_option("-d", "--debug", dest='debug', action="count", help="The debug level, use multiple to get more.")
    (options, args) = parser.parse_args()
    if options.debug > 1:
        print ' verbose %s\tdebug %s' %(options.quiet, options.debug)
        print ' parm    %s' %options.parm
        print ' ago     %s' %options.ago
        print ' num     %s' %options.num
        print ' path    %s' %options.path
        print ' args:   %s' %args
    else:
        options.debug = 0
    ago = float(options.ago)
    parm = str(options.parm)
    num = int(options.num)
    
    if options.path not in ['','.'] or num >0:
        processDir(options.path, parm)

    elif len(args) > 0: 
        branch = args[0]
        print 'you typed %s'%branch
    else:
        print '%s' %usage()

if __name__ == '__main__':
    """ go juice """
    main_CL()
		