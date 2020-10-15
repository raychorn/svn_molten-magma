#!/usr/bin/env python2.3
#
# This script walks the directory tree and finds changes since the last run.
# Generates change events to SalesForce and sends email to user
#
version = 1.00    #April 15 1005

import os, re, sys, string, time, stat
import getopt, copy
import traceback
import cStringIO as StringIO
import csv
import glob
import datetime
from filecmp import *
from itertools import ifilter, ifilterfalse
from types import ListType, TupleType, DictType, DictionaryType
from optparse import OptionParser, OptionGroup

#from Products.CMFCore.utils import getToolByName
inPlone = False  # true if you can use getToolByName
from sfMagma import SFMagmaTool


class Node:
    """ data management structure to load from walkDir and then output
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
           views: list of supported view tokens, view methods are contained in nodeTool.
            html: html 1.1 wrapping of node contents, options css path, header type
            xml:  xml 1.0 wrapping of content, no attributes
            rss:  rss 0.92, 1.0, 2.0 wrapping of node contents
            out:  stdout line oriented output, \n \t, ...
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
    meta_type = 'Node'
    results  = []
    loglines = []
    
    
    def __init__(self, id='', name='name', path='/', data=None, info=None, tool=None, db=0):
        """ create and load node from data passed in or call to load method on path.
        """
        self.id   = self.getNid(id)
        self.name = name
        if tool is None: 
            tool = nodeTool(db=db)
        self.tool = tool
        self.rootpath = '/'
        if hasattr(self.tool,'rootpath'):
            self.rootpath = self.tool.rootpath
        self.path = path
        if info is not None:
            self.info = info      # note this will overwrite info updated by load
        self.loglines.append('created ')
        self.debug = db

    def setDebug(self, db=0):
        """ set debug level """
        self.debug = db
        
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
            self.tool.setProblem(p, 'fileLoad', 'Not a path', npath)
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
    
    def getFilesNodes(self, name=None, version=None):
        """  assume self.data is list of filenames in path and load then in objects 
        """
        self.nodes = []             # empty out old nodes
        for fname in self.data:
            id = fname.split('.')[0]
            id = self.getNid(id)
            fpath = os.path.join(self.path,fname) 
            info = 'File contents of %s' %fname
            try:
                node = FileNode(id, fname, path=fpath, data=None, info=info, tool=self.tool)
                node.load()
                node.getFileInfo(version)
                self.nodes.append(node)
            except Exception, e:
                print 'Error %s msg:%s' %(Exception, e)
                #self.tool.setProblem(p, 'fileLoad', ['Not a path'], npath)

    def log(self, msg, level=1, severity=0, tag='', sum=''):
        """ Write out log messages """
        if type(level) not in [type(1),type(1.0)]:
            level = 1
        db = int(self.debug)
        if db < level:  return
        if severity not in [-200,-100,0,100,200,300]:   severity = 0
        if tag in [None,'']: tag = self.meta_type
        if severity > 0:
            sum = msg
            msg = self.getErrorDetailStr()
        lm = '%s %s %s %s'%(time.ctime(),tag,sum,msg)
        if len(self.loglines) > 5:
            self.loglines.pop(0)
        self.loglines.append(lm)
        if not inPlone:
            print '%s %s %s'%(tag,sum,msg)
    
    def getErrorDetailStr(self):
        """ dump the file details"""
        msg = '\n'
        if hasattr(self,'filedata'):
            msg = '%sfiledata:%s'%(msg,self.filedata)
        if hasattr(self,'data'):
            msg = '%s data:%s'%(msg,self.data)
        return msg
        
class FileNode(Node):
    """ A subclass of a node that is customised for each specific usage.  Leaves
        that are representing a file contents contain elements that are lines in the
        file.  Leaves that are lines in a file contain words that could be control tokens.
        A leaf will have portable data specific methods that enliven the content.
        Leaf:
           Node.all: the basic node attributes of id, access, views, contents, & state.
           subclass of any method that needs to be different then standard.
    """
    meta_type = 'FileTool'
    filelines = []
    filedata = []
    
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
            #self.tool.sfb.dlog.info('FOUND mdate:%s  %s ', self.mdate, path )
            if contents:
                fp = open(fpath)
                self.data = fp.readlines()
                fp.close()
                if self.tool.debug >1: print 'Loaded %s lines from %s' %(len(self.data),path)
            else:
                self.data = ''
                if self.tool.debug >1: print 'Loaded stat info from %s' %(path)
        else:
            print 'No File at %s' %(path)
                
        
        
    def loadCSV(self, fpath):
        """ load just as CSV """
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
        
    def getDateInfoFromFileName(self):
        """
        """
        fileName = self.name
        dateStr  = fileName.split('.',1)[1]
        dateList = dateStr.split('_')
        if len(dateList) == 3: isoDateStr = '%s-%s-%sT00:01:00' %(dateList[0],dateList[1],dateList[2])
        else:                  isoDateStr = 'unknown'
        self.tool.sfb.log.info('FOUND mergedCR date of %s as %s iso:%s', dateStr, dateList, isoDateStr )
        self.doneDate = isoDateStr
        self.doneDateStr = self.tool.sfb.getTime(self.doneDate)


    def getFileInfo(self, version=None):
        """ parse tech, process, metal top, etc from filename
        """
        fileName = self.name
        self.branch = 'unknown'
        self.version = version
        blastStr = 'blast4'
        self.crList = []
        self.doneCRs = {}
        dateStr  = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.mdate))
        self.doneDate = dateStr
        self.doneDateStr = time.strftime("%Y/%m/%d", time.localtime(self.mdate))
        self.doneDateTup = time.localtime(self.mdate)
        self.doneDateSec = self.mdate
        brSearch = self.tool.branchRE.search(fileName)
        if brSearch:
            self.branch = brSearch.group('brString')
            blastStr = self.branch.split('_')[0]  
            if version is not None:
                self.version = version
  
        #self.tool.sfb.log.info('FOUND done TOKEN file date %s cs:%s br:%s CRs:%s', dateStr, self.version, self.branch, self.crList )
    
    
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
class SFTool(SFMagmaTool):
    """ handle to a sForce connection tool """

        
#############################################################################################################
#   nodeTool with Link to sforceBase 
#############################################################################################################
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
    problems = {}
    rootpath = '/local/static/test' 
    tmp_root = '/var/sfscript/SCM2/submissions'
    numReady = 0
    numDone  = 0
    numDoneMax  = 100
    numPassed = 0
    numPassedMax = 300
    psReset= False
    branchRE   = re.compile("\.(?P<brString>[a-zA-Z0-9_\.]+)-?")
    commentRE  = re.compile("-+(?P<commentString>.+)$")
    reportType = 'line'
    meta_type = 'NodeTool'
    version = 0
    
    def __init__(self, username=None, upass=None, logname='sf.walkFile', sfb=None, options=None, db=None):
        self.debug = 0
        if options is not None:
            if hasattr(options, 'debug'):
                dl = options.debug
                if dl is None:  self.debug = 0
                else:           self.debug = dl
        if db is not None:
            dl = options.debug
            if dl is None:  self.debug = 0
            else:           self.debug = dl
        #print 'Set Tool debug level to %s' %self.debug
        
        if sfb is None:
            sfb = self.getTool()
        self.sfb  = sfb

        self.setupBase(username, upass, self.sfb.elog)        

    def getTool(self):
        """ get access to Plone based sfTool"""
        if inPlone:
           tool = getToolByName(self, 'sfa')
        else:
           tool = SFTool()
        self.sfa = tool
        return tool
        
    def setupBase(self, username=None, upass=None, logger=None):
        """ setup or reset base methods    """
        pass
    
    def getRelPath(self, path):
        """ return path string reletive to root"""
        lenRootPath = len(self.rootpath)
        return path[lenRootPath:]
        
    def getFullPath(self, path, fileName='', root='tmp'):
        """ get the full path to the Scan or tmp path """
        if path[0] == '/':  path = path[1:]
        if root == 'root':
            spath = os.path.join(self.rootpath, path, fileName)
        else:
            spath = os.path.join(self.tmp_root, path, fileName)
        return spath

    def getTempPathFromPath(self, path):
        """ get the temp version of the same path"""
        relpath = self.getRelPath(path)
        tmpPath = self.getFullPath(relpath, root='tmp')
        return tmpPath

    def setReport(self, type='line'):
        """ set the type of output report """
        self.reportType=type
        
    def getReport(self, path, file, mtime=0):
        """ create a terse output string to explain state of this token based
            on reletive path in rootpath and file name
        """
        pathList = path.split('/')
        msg =  "%s \n" %(file)
        return msg

    def processFile(self, path, fileName, action='NEW', isDir=False):
        """ Check what type of path we have right now just from the filename and containing directory
        """
        if self.numDone > self.numDoneMax: return 0   # debug escape
        if self.numPassed > self.numPassedMax: return 0   # debug escape
        #fileName = os.path.basename(path)
        #dirName  = os.path.dirname(path)
        status = 'new'
        msg = self.getReport(path, fileName)
        print msg
        if action != 'NEW': # No update of SF just sync in trees
            # update something
            # self.updateFile(fileName, path, action)
            return 0
        
        else: # This is default update of SF on new files in Scan tree
            spath = self.getFullPath(path, fileName, 'root')
            node = FileNode(path=spath, data=None, info=info, tool=self)
            node.load(contents=False)                # sets mdate
            node.getFileInfo(version=version)   
            # sets self.branch, self.version, self.doneDate, 
            cversion    = node.version
            mantleTime = node.doneDate
            self.numDone += 1
            return 0
        

    def updateFile(self, fileName, path, action='NEW'):
        """ Create or delete files in the tmp_root version of the Scan tree """
        if path == '/': return 0
        elif path[0] == '/': path = path[1:]
        spath = os.path.join(self.rootpath, path, fileName)
        tpath = os.path.join(self.tmp_root, path, fileName)
        if os.path.isdir(tpath):
            if action == 'NEW':
                try:
                    os.mkdir(tpath)
                    if self.debug >0: print 'Scan-tmp DIR create %s\n' %(tpath)
                except Exception, e:
                    msg = 'ERROR updateTokenFile Make DIR Failed for %s  %s, %s\n' %(tpath, Exception, e)
                    print msg
            else:
                try:
                    self.removeAll(tpath)
                    if self.debug >0:print 'Scan-tmp DIR delete %s\n' %(tpath)
                    if self.debug >1:print '      with files %s' %(os.listdir(tpath))
                except Exception, e:
                    msg = 'ERROR updateTokenFile Delete DIR Failed for %s  %s, %s\n' %(tpath, Exception, e)
                    print msg
                

        elif os.path.isfile(tpath):
            if action == 'NEW':
                print 'ERROR cannot OVERWRITE %s\n' %(tpath)
            else:
                try:
                    if self.debug >0:print 'Scan-tmp Deleting %s\n' %(tpath)
                    os.remove(tpath)
                    return 1
                except Exception, e:
                    msg = 'ERROR updateTokenFile Delete Failed for %s  %s, %s\n' %(tpath, Exception, e)
                    print msg
        else:
            if action == 'NEW':
                if os.path.isdir(spath):
                    print 'Making subdirectories\n'
                    os.makedirs(tpath)
                    return 1
                
                data = '' # declare data in this scope...
                try:
                    sp = open(spath)
                    data = sp.readlines()
                    sp.close()
                except Exception, e:
                    msg = 'updateTokenFile Failed to READ %s in %s\n' %(fileName, spath)
                    msg += 'ERROR %s, %s' %(Exception, e)
                    print msg
                try:
                    if self.debug >0:print 'Scan-tmp Writing %s bytes in %s\n' %(len(data), tpath)
                    fp = open(tpath, 'w')
                    fp.writelines(data)
                    fp.close()
                    return 1
                except Exception, e:
                    msg = 'ERROR updateTokenFile WRITE Failed in %s' %(tpath)
                    print msg
                    print '%s'%e
                    if e[0] == 2:
                        print 'Making subdirectories\n'
                        os.makedirs(os.path.join(self.tmp_root, path))
                        try:
                            print 'Scan-tmp Writing %s bytes in %s\n' %(len(data), tpath)
                            fp = open(tpath, 'w')
                            fp.writelines(data)
                            fp.close()
                            return 1
                        except Exception, e:
                            msg = 'ERROR updateTokenFile WRITE Failed in %s %s\n' %(tpath, e)
                            print msg
                        
            else:
                print 'ERROR cannot find to delete %s\n' %( tpath)
        return 0   


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
            


    #############################################################################################################
    #  structure to collect problems and report them to command line
    #############################################################################################################
    def setProblem(self, name, type='sfSet', results='', parms={}):
        """ load the node specific activity problems """
        if self.problems.has_key(name):
            pd = self.problems[name]
            pt = pd['type']
            self.sfb.log.error('Another %s problem with %s result:%s parms%s', type,name,results,parms.get('subject',''))
            pd['results'] = results
            pd['data'] = parms
        else:
            pd = {'name':name, 'type':type, 'results':results, 'parms':parms}
            self.sfb.log.error('New %s problem with %s result:%s parms%s', type,name,results,parms.get('subject',''))
            #self.sfb.dlog.error('New %s problem with %s result:%s parms%s', type,name,results,parms)
        self.problems[name] = pd


#############################################################################################################
#   A directory walker that compares the production directory to a temp copy to find difference
#   and trigger change events to drive an updater.
#############################################################################################################
class walkdir:
    """ walk a directory tree and compare to a temp version of the same tree
        and generate processing events on each directory
    """
    def __init__(self, a, b, tool, ignore=None, hide=None, maxNum=100): # Initialize
        self.left = a
        self.right = b
        self.tool = tool
        self.maxNum = maxNum
        self.totalNum = 0
        if hide is None:
            self.hide = [os.curdir, os.pardir] # Names never to be shown
        else:
            self.hide = hide
        if ignore is None:
            # Names ignored in comparison
            self.ignore = ['RCS', 'CVS', 'tags','logfiles','.htaccess','tsmc'] 
        else:
            self.ignore = ignore

    def _filter(flist, skip):
        return list(ifilterfalse(skip.__contains__, flist))
            
            
    def phase0(self): # Compare everything except common subdirectories
        self.left_list = self._filter(os.listdir(self.left),
                                 self.hide+self.ignore)
        self.right_list = self._filter(os.listdir(self.right),
                                  self.hide+self.ignore)
        self.left_list.sort()
        self.right_list.sort()

    def phase1(self): # Compute common names
        b = dict.fromkeys(self.right_list)
        common = dict.fromkeys(ifilter(b.has_key, self.left_list))
        self.left_only = list(ifilterfalse(common.has_key, self.left_list))
        self.right_only = list(ifilterfalse(common.has_key, self.right_list))
        self.common = common.keys()

    def phase2(self): # Distinguish files, directories, funnies
        self.common_dirs = []
        self.common_files = []
        self.common_funny = []
        for x in self.common:
            a_path = os.path.join(self.left, x)
            b_path = os.path.join(self.right, x)
            ok = 1
            try:
                a_stat = os.stat(a_path)
            except os.error, why:
                msg = 'Stat failed for %s why:%s'%(a_path,why[1])
                self.tool.sfb.dlog.error(msg)
                ok = 0
            try:
                b_stat = os.stat(b_path)
            except os.error, why:
                msg = 'Stat failed for %s why:%s'%(b_path,why[1])
                self.tool.sfb.dlog.error( msg)
                ok = 0

            if ok:
                a_type = stat.S_IFMT(a_stat.st_mode)
                b_type = stat.S_IFMT(b_stat.st_mode)
                if a_type != b_type:
                    self.common_funny.append(x)
                elif stat.S_ISDIR(a_type):
                    self.common_dirs.append(x)
                elif stat.S_ISREG(a_type):
                    self.common_files.append(x)
                else:
                    self.common_funny.append(x)
            else:
                self.common_funny.append(x)

    def phase3(self): # Find out differences between common files
        xx = cmpfiles(self.left, self.right, self.common_files)
        self.same_files, self.diff_files, self.funny_files = xx

    def phase4(self): # Find out differences between common subdirectories
        # A new dircmp object is created for each common subdirectory,
        # these are stored in a dictionary indexed by filename.
        # The hide and ignore properties are inherited from the parent
        self.subdirs = {}
        for x in self.common_dirs:
            a_x = os.path.join(self.left, x)
            b_x = os.path.join(self.right, x)
            self.subdirs[x]  = walkdir(a_x, b_x, self.tool, self.ignore, self.hide, self.maxNum)

    def phase4_closure(self): # Recursively call phase4() on subdirectories
        self.phase4()
        for sd in self.subdirs.itervalues():
            sd.phase4_closure()

    methodmap = dict(subdirs=phase4,
                     same_files=phase3, diff_files=phase3, funny_files=phase3,
                     common_dirs = phase2, common_files=phase2, common_funny=phase2,
                     common=phase1, left_only=phase1, right_only=phase1,
                     left_list=phase0, right_list=phase0)

    def __getattr__(self, attr):
        if attr not in self.methodmap:
            raise AttributeError, attr
        self.methodmap[attr](self)
        return getattr(self, attr)

    def walk_one_level(self): # Print reports on self and on subdirs
        self.report()
        for sd in self.subdirs.itervalues():
            #print
            sd.report()

    def walk_breadth_dir(self, options=None): # Walks on self and subdirs recursively
        self.report(options)
        for sd in self.subdirs.itervalues():
            sd.walk_breadth_dir(options)

    def report(self, options=None):
        """ just care about differences in left dir (rootdir) """
        dname = self.left[len(self.tool.rootpath):]
        if self.totalNum > self.maxNum: return
        #print 'diff', self.left, self.right
        pnum = 0
        procType = 'update'
        if hasattr(options, 'list'):
            procType = options.list
        
        if self.left_only and dname not in [None,'']:
            self.left_only.sort()
            msg = 'Scan dir %s has %s NEW Files to Process' %(dname, len(self.left_only))
            if self.tool.debug >0: print '%s' %(msg)
            #self.tool.sfb.dlog.info(msg)
            if procType != 'update':
                for fileName in self.left_only:
                    msg = self.tool.getDupReport(dname, fileName, 'NEW')
                    if msg not in [None,'']:
                        print msg
            else:
                for fileName in self.left_only:
                    fpath = os.path.join(self.left, fileName) 
                    tpath = self.tool.getTempPathFromPath(fpath)
                    if not os.path.exists(tpath): 
                        if os.path.isdir(fpath): 
                            print 'INFO missing the temp directory %s'%tpath
                            try: os.makedirs(tpath)
                            except:
                                head,tail = os.path.split(tpath)
                                try: os.mkdir(head)
                                except: print 'ERROR Could not create new directory %s'%tpath
                     
                    if os.path.isdir(fpath): 
                        fileList = self._filter(os.listdir(fpath),self.hide+self.ignore)  # go down one level to process this new directory
                        sdname = os.path.join(dname,fileName)                         # add this dir name to end of relative path
                        msg = 'Scan subdir %s Processed %s NEW files' %(sdname, len(fileList))
                        if self.tool.debug >0: print msg
                        for fName in fileList:
                            self.tool.processFile(sdname, fName, 'NEW')
                            pnum += 1
                    else:
                        self.tool.processFile(dname, fileName, 'NEW')
                        pnum += 1
                msg = 'Scan dir %s Processed %s NEW files' %(dname, pnum)
                print msg
                self.totalNum += pnum
            
            
        if self.right_only:
            self.right_only.sort()
            msg = 'Scan dir %s has %s MOVED Files to Process' %(dname, len(self.right_only))
            if self.tool.debug >0: print msg
            #self.tool.sfb.dlog.info(msg)
            if procType != 'update':
                for fileName in self.right_only:
                    msg = self.tool.getDupReport(dname, fileName, 'MOVED')
                    if msg not in [None,'']:
                        print msg
            else:
                for fileName in self.right_only:
                    fpath = os.path.join(self.left, fileName) 
                    if os.path.isdir(fpath): 
                        fileList = self._filter(os.listdir(fpath),self.hide+self.ignore)  # go down one level to process this new directory
                        sdname = os.path.join(dname,fileName)                        # add this dire name to end of relative path
                        msg = 'Scan dir %s has %s MOVED files to process' %(sdname, len(fileList))
                        if self.tool.debug >0: print msg
                        for fName in fileList:
                            self.tool.processFile(sdname, fileName, 'MOVED')
                            pnum += 1
                    else:
                        self.tool.processFile(dname, fileName, 'MOVED')
                        pnum += 1
                        
                msg = 'Scan dir %s Processed %s MOVED files' %(dname, pnum)
                print msg
                self.totalNum += pnum
            
        if self.diff_files:
            self.diff_files.sort()
            msg = 'Scanning for Differing file the Scan Directory %s %s' %(dname, self.diff_files)
            if self.tool.debug >1:print msg
            #self.tool.sfb.dlog.info(msg)
        if self.funny_files:
            self.funny_files.sort()
            msg = 'Scanning for Troubled file the Scan Directory %s %s' %(dname, self.funny_files)
            if self.tool.debug >1: print msg
            #self.tool.sfb.dlog.info(msg )
        if self.common_funny:
            self.common_funny.sort()
            msg = 'Scanning for Common Funny file the Scan Directory %s %s' %(dname, self.common_funny)
            if self.tool.debug >1: print msg
            #self.tool.sfb.dlog.info(msg )
        if self.common_dirs:
            self.common_dirs.sort()
            msg = 'Common subdirectories in the Scan Directory %s %s' %(dname, self.common_dirs)
            if self.tool.debug >1: print msg
            #self.tool.sfb.dlog.info(msg )
        if self.same_files:
            pass
            #self.same_files.sort()
            if self.tool.debug >0: print '%3s Identical files in %s' %(len(self.same_files),dname )
    
        
#############################################################################################################
#   Methods called from the command line - cron oriented to update SalesForce
#############################################################################################################
def walk_list(version=None):
    """ compare the two directories and print the state """
    ts1 = time.time()
    tool = nodeTool(options=options)
    # Acquire lock - exit if script is running
    try:
        lockHandle = cronLock('ScanWalkLib.lock')
    except Exception, e:
        msg = 'Could not acquire exclusive lock for cron run. Assume another instance is being run. EXITING.'
        tool.sfb.setLog(msg, 'warn')
        tool.sfb.setLog('Information from locking operation was: %s' %e,'warn')
        print msg
        sys.exit()
        
    sfTime = (time.time()-ts1)
    tool.sfb.dlog.info('Connecting to SalesForce took %s secs' %(sfTime))
    tool.setReport('line')
    ignore = ['RCS', 'CVS', 'tags','logfiles','.htaccess','replaced','replacement'] 
    print 'IGNORING the dirs %s' %ignore
    walkDir = walkdir(tool.rootpath, tool.tmp_root, tool, ignore)
    tool.sfb.dlog.info('SF Connect %s secs and Compare paths took %s secs' %(sfTime,(time.time()-ts1)))
    print '______________________________________________________________'
    walkDir.walk_breadth_dir(options) 
    print '______________________________________________________________'
    secs = (time.time() - ts1)        
    min  = int(secs/60)
    sec  = int(secs-min*60)
    msg = 'Updated %s and scanned %s tokens for versions %s in %s min %s secs' %(tool.numDone, tool.numPassed, version,min,sec)
    print msg
    tool.sfb.log.info(msg)
    
def usage(err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to seach the Scan library tree for your branch.\n'
    m += ' '
    m += '    walklib  \n'
    m += '      or\n'
    m += '    walklib -w tech_rules \n'
    m += '      or\n'
    return m

def main_CL():
    """ Command line parsing and and defaults method for walk
    """
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-w", "--walk",  dest="walk", default="none", help="Scope of status to walk in the directory.")
    parser.add_option("-s", "--cs",    dest="code", default="4",    help="The Code version <4|4.0|4.1|4.2|all> to use.")
    parser.add_option("-t", "--ago",   dest="ago",  default=30.0,   help="Dates ago to look for modified items.")
    parser.add_option("-n", "--num",   dest="num",  default="4000", help="Max number of items to process")
    parser.add_option("-x", "--parm",  dest="parm", default="",     help="Parms used by a method")
    parser.add_option("-l", "--list",  dest="list", default="junk", help="List the branch status in the tree")
    parser.add_option("-q", "--quiet", dest='quiet',default="1",    help="Show less info in output")
    parser.add_option("-d", "--debug", dest='debug',action="count", help="The debug level, use multiple to get more.")
    (options, args) = parser.parse_args()
    if options.debug > 1:
        print ' verbose %s\tdebug %s' %(options.quiet, options.debug)
        print ' walk    %s' %options.walk
        print ' version  %s' %options.code
        print ' ago     %s' %options.ago
        print ' num     %s' %options.num
        print ' list    %s' %options.list
        print ' args:   %s' %args
    else:
        options.debug = 0
    crList = []
    version = str(options.code)
    ago = float(options.ago)
    
    if options.walk in ['none']:
        walk_list(version, options=options)
    elif options.walk in ['tech_rules']:
        walk_list(version, options=options)
    else:
        print '%s' %usage()

if __name__ == '__main__':
    """ go juice """
    main_CL()
