#!/usr/bin/env python2.3
#
# This script walks the SCM directory tree and finds changes since the last
# run and generates change events to SalesForce and to the loggers
#
#version = 1.10    #Feb 12, 2004 - added -w all -l dup command line to list out duplicates in the SCM tree
version = 2.00    #July 20, 2004 - rework this walker to update the new Task Branch objects in sForce

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
from sfMagma import *
from sfTaskBranch import *   # get SFTaskBranch & SFTaskBranchTool
from sfTeamBranch import *
from sfUtil import *
from sop import sfEntities, SFEntitiesMixin, SFUtilityMixin, SFTestMixin
from sfConstant import *
from walkSF import SFTaskBranchWalkTool

#from cookie_xmlrpclib import DateTime  # need to rework DateTime


class Node:
    """ data management structure to load from walkSCM and then output
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
    
    def getFilesNodes(self, name=None, stream=None):
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
                if fname.find('merged_crs') != -1:   # you found a merged CR file to open and parse
                    node.loadCRs()
                else:
                    node.getTokenFileInfo(stream)
                self.nodes.append(node)
            except Exception, e:
                print 'Error %s msg:%s' %(Exception, e)
                #self.tool.setProblem(p, 'fileLoad', ['Not a path'], npath)
        
        
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
            #self.tool.sfb.dlog.info('FOUND mdate:%s  %s ', self.mdate, path )
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
        
    def getMergedCRsFileInfo(self):
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


    def loadCRs(self):
        """ load the CR structure from the data lines loaded from a merged_crs file
        """    
        if len(self.data) == 0: self.load(self.path)
        if len(self.data) == 0:
            self.tool.sfb.log.info('No Merged CRs FOUND in %s %s', self.path, self.id )
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
            self.tool.sfb.log.info('CR:%s IS %s', crNum,  self.doneCRs[crNum])
        
    def getTokenFileInfo(self, stream=None):
        """ parse crInfo and mantle time stamp from filename
            sets self.branch, self.codeStream
            loads self.doneCRs as {cs:, changes:, action:, branch:, mantleTS:}
        """
        fileName = self.name
        self.branch = 'unknown'
        self.codeStream = '4'
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
            if stream is not None:
                self.codeStream = stream
            else:
                blastStrLow = string.lower(blastStr)
                if blastStrLow[:5] == 'blast' \
                       and blastStrLow[5:] in ACTIVE_STREAMS:
                    # strip off the first 5 char 'blast'
                    self.codeStream = blastStrLow[5:]
                else:
                    self.codeStream = blastStr
                    pass
                pass

            if self.codeStream not in ALL_STREAMS:
                self.tool.sfb.dlog.error('getTokenFileInfo failed to parse CS for %s in %s', self.branch, self.name )
                self.codeStream = DEFAULT_STREAM
        crSearch = self.tool.crRE.search(fileName)
        if crSearch:
            crStr  = crSearch.group('crString')
            self.crList = string.split(crStr, '_')
            for crNum in self.crList:
                self.addDoneCR(crNum, '', self.codeStream, {'action':'uk', 'branch':self.branch, 'mantleTS':self.doneDate})
  
        #self.tool.sfb.log.info('FOUND done TOKEN file date %s cs:%s br:%s CRs:%s', dateStr, self.codeStream, self.branch, self.crList )
    
    def addDoneCR(self, crNum, changes, cs=None, other={}):
        """ add the changes to this class global dictionary """
        if cs is None: cs ='unknown'
        if not self.doneCRs.has_key(crNum):
            self.doneCRs[crNum] = {'cs':cs, 'changes':changes}
        else:
            self.doneCRs[crNum]['cs'] = cs
            self.doneCRs[crNum]['changes'] = changes
        for key in other.keys():
            self.doneCRs[crNum][key]= other[key]

    
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
        


#############################################################################################################
#   Link to sforceBase - will migrate to the nodeTool 
#############################################################################################################
class SCMTaskBranchTool(SFTaskBranchTool):
    """ hang any walkSCM specific tool methods 
    """
    

class SCMTaskBranch(SFTaskBranch):
    """
    Create or remove a TB.  A TB is the linkage between a CR and a branch in a code stream

    """
    debug = 1
    action = 'update'
    logname = 'sf3.walkSCMOther'
    addedModID = 0
    psReset = False

    def __init__(self, entity=None, data={}, action=None, sfTool=None, debug=0):
        """  If an active tool object is not passed in then a connection is created.   """
        if entity is None: entity = 'Task_Branch__c'
        SFTaskBranch.__init__(self, entity, data=data, action=action, sfTool=sfTool, debug=debug)

    def autocreateFromTaskBranch(self, branches, branchname, newstream,
                                 status):
        if len(branches) == 0:
            # complain that we don't have any alt branches and bail
            msg = "autocreateFromTaskBranch: No alternate task branch found with name %s" %(branchname)
            self.sfb.setLog(msg, 'critical')
            return False
        if len(branches) > 1:
            # sort by create date and take earliest one?

            # complain that we don't have 1 and only one alt branch & bail
            msg = "autocreateFromTaskBranch: More than one alternate task branch found with name %s:\n%s" %(branchname, pprint.pformat(branches))
            self.sfb.setLog(msg, 'critical')
            return False

        # now we're sure we have one and only one alternate branch
        altTbObj = SCMTaskBranch(sfTool=self.sfb)
        altTb = branches.values()[0]
        altStream = altTb.get('stream')

        # load the alternate branch and get pertinent info from it
        info = altTbObj.loadBranch(branchname, altStream)
        altCLs = altTbObj.getData('Branch_CR_Link__c')
        altTbInfo = altTbObj.getData('Task_Branch__c')
        altTbId = altTbInfo.get('Id')
        
        # note autocreation and include link to original branch
        details  = "This task branch was autocreated from %s in stream %s:\n" \
                   %(branchname, altStream) 
        details += "https://na1.salesforce.com/%s\n" %(altTbId)
        details += "Please view the original task branch for any details specific to these changes/fixes."

        # wire in cloneBranch here!!
        newTbObj = altTbObj.cloneBranch(newstream, status, details=details,
                                        autocreate=True)

        # now, load the newly cloned branch into this branch instance
        tbStats = self.loadBranch(branchname, newstream)

        success=True
        tbInfo = self.getData('Task_Branch__c')
        if tbInfo in [None,{}]:
            success = False
            pass
        
##        # create new (empty) task branch obj
##        self.loadBranch(branchname, newstream)
##        newTbData = {}
##        xferFields = ('OwnerId','Name','High_Risk__c','Branch_Priority__c',
##                      'QOR_Results__c','Branch_Or_Label__c','Branch__c',
##                      'Branch_Path__c','Command_Change__c')

##        for field in xferFields:
##            if altTbInfo.has_key(field):
##                newTbData[field] = altTbInfo[field]
##                pass
##            continue

##        # Fields unique to the autocreated branch
##        newTbData['Code_Stream__c'] = newstream
##        newTbData['Details__c'] = details
##        newTbData['Branch_Status__c'] = status
        
##        # create the new task branch object now
##        tbId = self.setTaskBranch(id='', data=newTbData)
        
##        # link all CRs that the orig branch has
##        self.autocreateCloneCrLinks(tbId, newstream, status, altCLs)

##        self.refresh()

        return success
    ## END autocreateFromTaskBranch

    def autocreateFromTeamBranch(self, branches, branchname, newstream,
                                 status):
        if len(branches) == 0:
            # complain that we don't have any alt branches and bail
            msg = "autocreateFromTeamBranch: No alternate team branch found with name %s" %(branchname)
            self.sfb.setLog(msg, 'critical')
            return False
        if len(branches) > 1:
            # complain that we don't have 1 and only one alt branch & bail
            msg = "autocreateFromTeamBranch: More than one alternate team branch found with name %s:\n%s" %(branchname, pprint.pformat(branches))
            self.sfb.setLog(msg, 'critical')
            return False

        # now we're sure we have one and only one alternate branch
        # create a team and task branch object to use in getting info
        # onthe alt branch
        altTbObj = SCMTaskBranch(sfTool=self.sfb)
        altTmbObj = SCMTeamBranch(sfTool=self.sfb)
        
        altTmb = branches.values()[0]
        altStream = altTmb.get('stream')

        # load the alternate branch and get pertinent info from it
        info = altTmbObj.loadBranch(branchname, altStream)
        altTmbInfo = altTmbObj.getData('Team_Branch__c')
        altTmbId = altTmbInfo.get('Id')

        # get the task branches linked to this team branch
        altTmbBrLinks = altTmbObj.getData('Branch_Team_Link__c')

        details = 'This task branch was autocreated from team branch %s in stream %s:\n' %(branchname, altStream)
        details += 'https://na1.salesforce.com/%s\n' %(altTmbId)
        details += 'Constituent task branches are listed in an attached Note below.'

        # create new task  branch obj
        self.loadBranch(branchname, newstream)
        newTbData = {'OwnerId': altTmbInfo['OwnerId'],
                     'Name': branchname,
                     'Autocreated__c': True,
                     'Branch_Status__c': status,
                     'Code_Stream__c': newstream,
                     'Branch_Priority__c': altTmbInfo['Priority__c'],
                     'Branch__c': branchname,
                     'Details__c': details }

        tbId = self.setTaskBranch(id='', data=newTbData)

        # crawl through the linked task branches and instantiate each one
        teamAltCLs = {}
        detailNote = "Task branches which were a part of the original team branch\n\n"
        for tmbBrLink in altTmbBrLinks:
            altTbId = tmbBrLink.get('Task_Branch__c')
            altTbObj.loadBranchById(altTbId)

            altCLs = altTbObj.getData('Branch_CR_Link__c')
            for cl in altCLs:
                crNum = cl.get('CR_Num__c')
                teamAltCLs[crNum] = cl
                continue

            altTbInfo = altTbObj.getData('Task_Branch__c')
            tbName = altTbInfo.get('Name')
            detailNote += "%s https://na1.salesforce.com/%s\n" \
                          %(tbName, altTbId)

            continue

        # link all CRs that the orig branch has
#        self.autocreateCloneCrLinks(tbId, newstream, status,
#                                    teamAltCLs.values())
        self.cloneCrLinks(teamAltCLs.values())

        self.refresh()
        return True
    ## END autocreateFromTeamBranch

    def autocreateCloneCrLinks(self, tbId, stream, status, ClList):
        """ Helper routine for creating CR links to task branch having id
        tbId based on a link of Cr Links from another branch
        """
        for crLink in ClList:
            clData = {"Name": 'BrCR Link',
                      "Case__c": crLink.get('Case__c'),
                      "Branch_Status__c": status,
                      "CR_Status__c": crLink.get('CR_Status__c'),
                      "CR_Subject__c": crLink.get('CR_Subject__c'),
                      "Component__c": crLink.get('Component__c'),
                      "CR_Num__c": crLink.get('CR_Num__c'),
                      "Stream__c": stream}
            clId = self.setBranchCRLink(tbId, id='', data=clData)
            continue
        return
    ## END autocreateCloneCrLinks
    
    ###################################################################################################
    #  MOD management
    ###################################################################################################
    def setBranchStatusForCRnums(self, branch, crList, stream, modStatus, mantleTime, addMissing=False, fix='no'):
        """  set the branch status based on the state of the token in the SCM tree
             return integer with number of MODs updated or 0
             returns number of added CR links
        """

        # convert mantleTime to seconds to avoid zone conversion later...
        mantleTimeSecs = time.mktime(time.strptime(mantleTime, '%Y-%m-%dT%H:%M:%S')) - time.timezone
        
        cutoffTup = time.strptime("10/01/2003", "%m/%d/%Y")
        cutOffSec = time.mktime(cutoffTup)
        clarify = False
        result = 0
        numDone = 0
        print "branch is: %s, %s" %(branch, stream)
        self.loadBranch(branch, stream, team='', label='')
        # this sets self.branch, self.stream, and loads all SF TB data into self.data
        tbInfo = self.getData('Task_Branch__c')
        if tbInfo in [None,{}]:           # create new ????
            # Look to see if there are any team or task branches having the
            # same name, but in another stream (i.e. automerge case)
            brTool = SFTaskBranchWalkTool()

            # first, look for team branched with this name
            team = True
            altbrs = brTool.findBranchByName(branch, team=team)

            if len(altbrs) == 0:
                team = False
                # no team branched found, look for alternate task branch(es)
                # that have not been autocreated
                altbrs = brTool.findBranchByName(branch, team=team,
                                                 noAutocreate=True)
                pass

            if len(altbrs) == 0:
                # no alternate branches with this name
                return -1
            
            """Commenting the suto-creation code to test before deleting it"""
            """elif team is True:
                # clone the team branch as a task branch in the new stream
                # with modStatus and mantleTime
                msg = "Attempting to autocreate task branch %s in %s with status %s from a team branch found with the same name" %(branch, stream, modStatus)
                self.sfb.setLog(msg, 'info')

                if self.autocreateFromTeamBranch(altbrs, branch, stream,
                                                 modStatus) is False:
                    # failed for some reason
                    msg = "autocreate task branch %s into stream %s from team branch failed" %(branch, stream)
                    self.sfb.setLog(msg, 'error')
                    return -1
                pass
            
            else:
                # clone the found alternate task branch into the new stream
                # with modStatus and load into this task branch object
                msg = "Attempting to autocreate task branch %s in %s with status %s from an alternate found with the same name" %(branch, stream, modStatus)
                self.sfb.setLog(msg, 'info')
                
                if self.autocreateFromTaskBranch(altbrs, branch, stream,
                                                 modStatus) is False:
                    # failed for some reason
                    msg = "autocreate task branch %s into stream %s failed" \
                          %(branch, stream)
                    self.sfb.setLog(msg, 'error')
                    return -1
                pass"""                
            
        tbId = tbInfo.get('Id')
        
        for crNum in crList:
            clarify = False
            if crNum == 'nocr': 
                print '%20s Update SF with no CRnum as:%s' %(branch, modStatus)
                self.setBranchStatus(modStatus, scmTS=mantleTimeSecs)
                self.sfb.setLog(' %25s %s %s'%(branch,stream,'Updated noCR branch'),'warn')
                continue
            try:  crInt = int(crNum)
            except: 
               self.sfb.setLog(' %25s %s %s'%(branch,stream,'cr:%s could not be cast as an integer'%crNum),'warn')
               continue           # must be bad parsing of filename
            
            crInfo = self.sfb.getCrByNum(crNum)
            # No longer consider that CR < 23600 may be clarify number
##            if crInt < 23600:     # COULD BE Clarify ID
##                clarify = True
##                if crInfo in [None,{},[]]: 
##                    msg = 'CR:%s CANNOT FIND a Clarify CR with id of %s in branch:%s' %(crNum, crNum, branch)
##                    print msg
##                    self.sfb.setLog(msg,'warn')
##                    continue
            if crInfo in [None,{},[]]:
                msg = 'Cannot Find SF CR %s linked to branch:%s' %(crNum, branch)
                print msg
                numDone = -1
                self.sfb.setLog(' %25s %s %s'%(branch,stream,msg),'error')
                continue
            if clarify: msg= 'Found Clarify:%s TS:%s Stat:%s' %(crNum, mantleTime, modStatus)
            else:       msg= 'Found SFCR:%s TS:%s Stat:%s' %(crNum, mantleTime, modStatus)
            
            crId = crInfo.get('Id')
            name = 'CR Link for %s'%stream
            crStatus = crInfo.get('Status')
            component = crInfo.get('Component__c')
            foundClId = ''
            clDataList = self.getData('Branch_CR_Link__c')
            for clInfo in clDataList:
                if clInfo.get('Case__c','') == crId: 
                    foundClId = clInfo.get('Id')
            name = 'CR Link for %s'%(stream)
            data = {'Name': name,'Case__c': crId,'CR_Status__c': crStatus, 'Branch_Status__c':modStatus
                   ,'Component__c': component, 'Stream__c':stream, 'CR_Num__c':crNum}
            if foundClId == '':
                clId = self.setBranchCRLink(tbId, id=foundClId, data=data)
                msg += ' cr:%s ADDED crid:%s'%(crNum, crId)
                self.sfb.setLog(' %25s %s %s'%(branch,stream,msg),'info')
            else:
                # don't do anything here - we already have a CR link on the branch for this CR.
                #msg += ' cr:%s Updated crid:%s'%(crNum, crId)
                pass

            numDone += 1

        self.setBranchStatus(modStatus, scmTS=mantleTimeSecs, psReset=self.psReset)
        msg = '%s %s UPDATED with %s CRs to status %s TD %s'%(branch, numDone, stream,
                                                              modStatus, mantleTime)
                    
        if result < 0: return result
        return numDone
        

    def setBranchCR(self, CR, mantleTime, cstream, modStatus=None, addMissing=False, fix='no'):
        """  Used by processToken from walkSCM but may be used by setBranchStatusForCRnums
             Need to pass in a full CR dictionary
        """
        crID = CR.get('id')
        crClosed = CR.get('closed')   # boolean
        changes = []
        if crID is not None:
            crNum      = CR.get('caseNumber')
            crInt      = int(crNum)
            crStatusNow= CR.get('status')

            if self.branchType == 'Team':
                MODs = self.getMODsByCR(CR, self.branch, cstream, mantleTime)
                self.sfb.setLog('setBranchCR found %s MODs for %s Team Branch %s '%(len(MODs), cstream, self.branch),'info')
            else:
                MODs = self.getMODsByCR(CR, self.branch, cstream, mantleTime)
            
            if len(MODs) == 0 and crInt < 23600:                   # second chance to get the correct CR
                CR, clarify = self.getCaseByCRNum(crNum=crNum)
                MODs = self.getMODsByCR(CR, self.branch, cstream, mantleTime)
            
            if crClosed:
                crStatus= CR.get('status')
                if crStatus[:6] != 'Closed':
                    crStatus  = 'Closed'
                if modStatus[:6] != 'Closed':
                    modStatus = 'Closed - Automatic'
            else:
                crStatus = self.getCRStatus(CR=CR, MODs=None)
                if modStatus is None:     
                    modStatus = 'Fixing'

            if fix != 'no':
                changes = self.fixCR(CR, options={}, status=modStatus)
            #crOwnID    = self.getCROwnerID(CR)     # should be the Developer, if queue use clarifier Originator or David
            
                
            if len(MODs) == 0 and addMissing:
                self.sfb.setLog('NO MOD found for Stream:%s in CR:%s  %s'%(cstream, crNum, self.branch),'error')
                changes = self.addMOD( CR=CR, branch=self.branch, stream=cstream, status=modStatus, ownerID=None, ownerEmail=None, mantleTimeStamp=mantleTime, teamBranch=None )
                print '%s' %changes
                return -1, 1                # skip the rest of the loop for this CR
            else:    
                numModChanges, changes = self.setMODStatus(MODs, CR, modStatus, mantleTime, fix)
                if modStatus in ['Merged - Testing by Originator-offNow']:
                    try:    sendToDict = self.sendOwnerEmail(CR, MODs, self.branch, 'walkSCM')
                    except: self.elog.exception('sendOwnerEmail')
            changes = 'CR:%s %s' %(crNum,changes)

            # now set the status of the CR 
            crChanges = self.setCRStatus(CR, crStatus)
            if crChanges != 0:     # changes = 0 means all changes have been made correctly, -1 is error
                pass
                #print 'CR:%s was changed' %crNum
            if numModChanges != 0:
                print 'CR:%s MOD changes %s' %(crNum, changes)

            return numModChanges, changes
            


##class TeamBranch(SCMTaskBranch):
##    """
##    Rename and update whole branches
##    """
##    debug = 1
##    action = 'update'
##    logname = 'sf3.walkRTL'
##    addedModID = 0


class SCMTeamBranchTool(SFTeamBranchTool):
    """ hang any walkSCM specific tool methods 
    """
    

class SCMTeamBranch(SFTeamBranch):
    """
    Create or remove a TB.  A TB is the linkage between a CR and a branch in a code stream

    """
    debug = 1
    action = 'update'
    logname = 'sf3.walkSCMOther'
    addedModID = 0
    psReset= False

    def __init__(self, entity=None, data={}, action=None, sfTool=None, debug=0):
        """  If an active tool object is not passed in then a connection is created.   """
        if entity is None: entity = 'Team_Branch__c'
        SFTeamBranch.__init__(self, entity, data=data, action=action, sfTool=sfTool, debug=debug)
        
    def setBranchStatusForCRnums(self, branch, crList, stream, modStatus, mantleTime, addMissing=False, fix='no'):
        """  set the branch status based on the state of the token in the SCM tree
             return integer with number of MODs updated or 0
             returns number of added CR links
        """
        # convert mantleTime to seconds to avoid zone conversion later...
        mantleTimeSecs = time.mktime(time.strptime(mantleTime, '%Y-%m-%dT%H:%M:%S'))

        cutoffTup = time.strptime("10/01/2003", "%m/%d/%Y")
        cutOffSec = time.mktime(cutoffTup)
        clarify = False
        result = 0
        numDone = 0
        self.loadTeamBranch(branch, stream)
        # this sets self.branch, self.stream, and loads all SF TB data into self.data
        tbInfo = self.getData('Team_Branch__c')
        btLinkList = self.getData('Branch_Team_Link__c')
        
        if tbInfo in [None,{}]:           # create new ????  NO just exit with -1
            # The clearCase loader should create all TaskBranches as at least a shell
            # just skip and try again until found
            # or maybe there is no team branch and we need to check for a task branch?
            return -1
            
        tbId = tbInfo.get('Id')
        
        for crNum in crList:
            if crNum == 'nocr':
                # Handle the nocr token case - should be the only element in the list
                print '%20s Update SF with no CRnum as:%s' %(branch, modStatus)
                self.setBranchStatus(modStatus, scmTS=mantleTimeSecs)
                continue
            
            try:  crInt = int(crNum)
            except: 
               continue           # must be bad parsing of filename
            
            crInfo = self.sfb.getCrByNum(crNum)
##            if crInt < 23600:     # COULD BE Clarify ID
##                clarify = True
##                if crInfo in [None,{},[]]: 
##                    msg = 'CR:%s CANNOT FIND a Clarify CR with id of %s in branch:%s' %(crNum, crNum, self.branch)
##                    print msg
##                    self.sfb.setLog(msg)
##                    continue
            if crInfo in [None,{},[]]:
                print 'Cannot Find SF CR of %s in branch:%s' %(crNum, self.branch)
                print 'ERROR Found MISSING SF CR'
                numDone = -1
                continue
            if clarify: msg= 'Found ClarifyCR:%s, as SFCR:%s with MTS:%s Status-> mod:%s' %(crNum,crInfo.get('CaseNumber'), mantleTime, modStatus)
            else:       msg= 'Found SForceCR:%s,  with MTS:%s Status-> mod:%s' %(crNum, mantleTime, modStatus)
            
            crId = crInfo.get('Id')
            name = 'CR Link for %s'%stream
            crStatus = crInfo.get('Status')
            component = crInfo.get('Component__c')
            foundClId = ''
            
            # Hmm, don't have this in a team branch
            # need to loop over branch team links to get cr links from each
            brObj = SCMTaskBranch(sfTool=self.sfb, debug=self.debug)
            for btLink in btLinkList:
                brId = btLink.get('Task_Branch__c')
                brInfo = brObj.loadBranchById(brId)
                clDataList = brObj.getData('Branch_CR_Link__c')

                # Don't know where to add a CR link in a team branch- don't try
                if foundClId == '':
                    msg = 'CR num %s found in token, but not in team branch. Cannot autocreate.' %crNum
                    self.sfb.setLog(' %25s %s %s %s'%(branch,stream,crNum,msg),'info')
                else:
                    # don't do updates here... these are handles by setBranchStatus
                    #clId = self.setBranchCRLink(tbId, id=foundClId, data=data)
                    #msg = 'cr:%s Updated crid:%s'%(crNum, crId)
                    pass
                
                numDone += 1

                brObj.setBranchStatus(modStatus, scmTS=mantleTimeSecs, psReset=self.psReset) # sanity check this...

        self.setBranchStatus(modStatus, scmTS=mantleTimeSecs)
        msg = '%s %s UPDATED with %s CRs to status %s'%(branch, numDone, stream, modStatus)
                    
        if result < 0: return result
        return numDone



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
    scm_path = '/magma/scm-release'
    scm_root = '%s/submissions' %scm_path
    rootpath = '%s/submissions' %scm_path
    #scm_root = '/var/sfscript/SCM/testonly/submissions'
    tmp_root = '/local/sfscript/SCM2/submissions'
    numReady = 0
    numDone  = 0
    numDoneMax  = 100
    numPassed = 0
    numPassedMax = 300
    BRs = {}
    CRs = {}
    psReset= False
    
    #allStreams = ['3','3.0','3.1','3.2','4.0','4','4.1','blast5','capi']
    allStreams = ALL_STREAMS

    mcapi      = re.compile('mcapi',re.I)
    blast6RE   = re.compile('blast6',re.I)
    blast5RE   = re.compile('blast5',re.I)
    blast4RE   = re.compile('blast4',re.I)
    blast41RE  = re.compile('blast4.1', re.I)
    blast40RE  = re.compile('blast4.0', re.I)
    blast400RE = re.compile('blast40', re.I)
    blast32RE  = re.compile('blast3.2', re.I)
    blast320RE = re.compile('blast32', re.I)
    branchRE   = re.compile("\.(?P<brString>[a-zA-Z0-9_\.]+)-?")
    crRE       = re.compile("^(?P<crString>[a-zA-Z0-9_]+)\.")
    commentRE  = re.compile("-+(?P<commentString>.+)$")
    
    reportType = 'line'
    
    def __init__(self, username=None, upass=None, logname='sf.walkSCMOther', sfb=None, options=None):
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
            sfb = SCMTaskBranchTool(debug=self.debug, logname='sf.walkSCMOther')
        self.sfb  = sfb

        self.setupBase(username, upass, self.sfb.elog)        

    def setupBase(self, username=None, upass=None, logger=None):
        """ setup or reset base methods    """
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
        
    def setCodeStreams(self, streams=[DEFAULT_STREAM]):
        """ set the list of code stream to act upon """
        if type(streams) not in [types.ListType, types.TupleType]:
            streams = [streams]
        print 'Setting Code Streams to %s' %str(streams)
        self.codeStreams=streams

    def setCodeStream(self, stream=DEFAULT_STREAM):
        """ set the active code stream to act upon """
        #print 'Setting Code Streams to %s' %stream
        self.codeStream=stream

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

    def getCrReport(self, path, file, crList=None):
        """ create a terse output string to show the state of these CR
            using the relative path in scm_root and file name
        """
        status, tokens = self.getStatusFromPath(path, file)
        # tokens = [view,branch,scmbranch,bundle,crList,action,info,path,stream]    

        msg =  'The %s branch is in the state %s \n' %(file,status)
        msg += ' %s. scm tokens are %s' %(file, tokens) 
        return msg


    def getStatusFromPath(self, path, fileName='', action='NEW'):
        """ get SF status from path and action,
            return SF status, user reply info string, and 
            a token list: [view,branch,scmbranch,bundle,crList,action,info,path] 
        """
        pathList = path.split('/')
        if len(pathList) > 1:
            blast = pathList[1]
        else:
            blast = 'root'
            pass
        
        if blast[:5] == 'blast' and blast not in ALL_STREAMS:
            stream = blast[5:]
            stream = stream.strip()
            if '_' in stream:
                stream = stream.split('_')[0]
        else:
            stream = blast
            
        if stream not in ALL_STREAMS:
            #msg = "getStatusFromPath: determined stream %s not in allStreams. blast was %s, pathList was %s" \
            #      %(stream, blast, pathList)
            #self.sfb.setLog(msg, 'warn')
            stream = DEFAULT_STREAM

        self.setCodeStream(stream)


        branch, crList = self.getCRBRfromFileName(fileName)       # note branch is now a list
        scmbranch = branch
        view = pathList[-1]
        viewList = view.split('_')
        if len(viewList) > 1:
            team = viewList[1][:2]
        else:
            team = ''
        info   = ''
        bundle = ''
        step   = ''
        stage  = ''
        if len(pathList) > 2:   step  = pathList[2]
        if len(pathList) > 3:   stage = pathList[3]
        status = step
        
        if blast in ['sf-scm']:
            status = 'Submitted to SCM'
            info = ''
            return status, ['view','branch','scmbranch','bundle',crList,'sf-scm',info,path,stream]
                           #[view,branch,scmbranch,bundle,crList,action,info,path,stream]    
        
        if blast in ['blast4.0_rtl2','blast4.0_rtl1','blast4.1_rtl4','blast4_rtl2','blast4_rtl1','blast4.2_rtl2']:
            status = 'Submitted to Team Testing'
            info = 'Special Directory for RTL trial builds'
            action = 'RTL-Build/Test'
            if step in ['received']:
                status = 'Submitted to Team Testing'
                info = 'Received into RTL trial builds'
                action = 'received'
            elif step in ['rtlteam']:
                status = 'Team Branch Hold'
                info = 'Active RTL trial builds'
                action = 'test'
            elif step in ['checkedin']:
                status = 'Team Branch Hold'
                info = 'Team Branch checked in'
                action = 'hold'
            elif step in ['today']:
                status = 'Team Branch Build Today'
                action = 'build'
            elif step in ['done']:
                status = 'Submitted to SCM'
                info = 'RTL trial build DONE'
                action = 'done'

            return status, ['team',branch,'scmbranch','bundle',crList,action,info,path,stream]
                           #[view,branch,scmbranch,bundle,crList,action,info,path,stream]    
                
        if step in ['done']:
            #status = 'Merged - Testing by Originator'
            status = 'Merged'
            action = 'done'
            info = 'This branch has merged into the %s stream' %blast
            #fnList = fileName.split('-')       #18584.blast4.0_premal_18584-blast4.0_psqorbld_3-blast4.0_psqorbld_bundle_2
            #if len(fnList) > 2:                #16457.blast4.0_petec_16457_continued-NF-blast4.0_anqorbld_6-blast4.0_anqorbld_bundle_3
            #    bundle   = fnList[-1]
            #    bldList  = fnList[1:-1]
            #    qorbuild = bldList
            #    if len(bldList) > 1:
            #        if bldList[0] == 'NF':     #18094.blast4.0_borah_18094-NF-blast4.0_qorbuild_45-blast4.0_anqorbld_4-blast4.0_anqorbld_bundle_2
            #            if len(bldList) > 1:
            #                qorbuild = ''
            #                for b in bldList[1:]
            #                   qorbuild += b
            #elif len(fnList) == 2:
            #    qorbuild = fnList[1]
            return status, [view,branch,scmbranch,bundle,crList,action,info,path,stream]
        
        #need_blast4.1_branch 
        if step[:5] == 'need_': step = 'need_branch'

        if step in ['received']:
            team = stage                  # should be in ['an','fe','be','ps']
            #if team in ['an']:    status = 'SCM-Received Analysis'
            #elif team in ['fe']:  status = 'SCM-Received FrontEnd'
            #elif team in ['be']:  status = 'SCM-Received Backend'
            #elif team in ['ps']:  status = 'SCM-Received Synthesis'
            status = 'SCM-Received'
            action = 'Received'
            info   = 'bin' 
                                        
        elif step in ['hold']:
            status = 'SCM-Hold'
            action = 'Note comment %s' %fileName
            info = 'Hold Pending %s' %fileName

        elif step in ['need_branch']:
            status = 'SCM-Need Branch'                      
            action = 'Need sync branch'
            info = 'Need new code stream branch'
            
        elif step in ['archived']:
            print "This is archived folder"
            status = 'Archived directory'                      
            action = 'Archived'
            info = 'Archived Directory of old tokens'

        elif step in ['post_release']:
            status = 'SCM-Post-Release'                      
            action = 'Wait for next release'
            info = 'Testing and merging delayed until next release.'

        elif step in ['checkedin']:
            status = 'SCM-Patch-Build-Delayed'                      
            action = 'Wait for next release'
            info = 'Patch build with this branch delayed.'


        elif step in ['approved']:
            status = 'SCM-Approved'              
            # 'SCM-Approved' need to ignore until can check for same branch in Red-Build-* & Done
            action = 'Approved'
            if len(pathList) > 3:   
                bundle   = pathList[3]
                bundleList = bundle.split('_')
            # check for approved/blast4.0_psqorbld_bundle1/blast4.0_psqorbld3/18500.blast4.0_michel_18500-NF-blast4.0_psqorbld_13-blast4.0_psqorbld_bundle_5
            info = 'bundle %s' %(bundle)


        elif step in ['qor']:
            status = 'SCM-QOR'
            action = 'building'
            if stage in ['build']:
                status = 'SCM-QOR Building'
            elif stage in ['results']:
                status = 'SCM-QOR Results'
                action = 'Evaluating'
            elif stage in ['test']:
                status = 'SCM-QOR Testing'
                action = 'Testing'
            info = 'QOR build'
                
        elif step in ['ready_to_bundle']:
            status = 'SCM-Ready to Bundle'
            action = 'Bundling'
            if len(pathList) > 3:   bundle   = pathList[3]
            #/ready_to_bundle/blast4.0_psqorbld1/24768.blast4.0_lippens_24768-NF-blast4.0_psqorbld_12
            info = ' bundle %s' %(bundle)

        elif step in ['bundle']:
            status = 'alertOff'
            action = 'Bundling'
            branch = fileName
            if stage in ['build']:
                status = 'SCM-Bundle Building'
                action = 'Building'
            elif stage in ['results']:
                status = 'SCM-Bundle Results'
                action = 'Evaluating'
            elif stage in ['test']:
                status = 'SCM-Bundle Testing'
                action = 'Testing'
            if len(pathList) > 4:   bundle = pathList[4]     # check for blast4.1_psqorbld_bundle3/blast4.1_psqorbld6
            info = ' bundle %s'%bundle
            
        elif step in ['scmbuild']:
            status = 'SCM-Candidate-Building'
            action = 'SCM Building next Candidate'
            if stage in ['build']:
                status = 'SCM-Candidate-Building'
                if len(pathList) > 4:   view = pathList[4]
            elif stage in ['results']:
                status = 'SCM-Candidate-Build Results'
                if len(pathList) > 4:   view = pathList[4]
                action = 'Evaluating'
            elif stage in ['test']:
                status = 'SCM-Candidate-Build Testing'
                if len(pathList) > 4:   view = pathList[4]
                action = 'Testing'
            info = 'SCM Candidate Build %s' %view
                
        elif step in ['today']:
            status = 'SCM-Patch-Build Today'
            action = 'Patch Building Today!'
            info   = 'Patch build today directory'

        else:
            action = '%s' %step
            info   = '%s directory' %step
            
        if team in ['fe']:   info = ' %s in Frontend team %s'%(action,info)
        elif team in ['be']: info = ' %s in Backend team %s'%(action,info)
        elif team in ['an']: info = ' %s in Analysis team %s'%(action,info)
        elif team in ['ps']: info = ' %s in Physical Synthesis %s' %(action,info)
        else:                info = ' %s in %s ' %(action,info)
        
        return status, [view,branch,scmbranch,bundle,crList,action,info,path,stream]    


    def getDupReport(self, path, fileName, action='NEW'):
        """ create a terse output string to show the state of duplicate tokens
        """
        if fileName.find('summary') != -1: return ''
        status, tokens = self.getStatusFromPath(path, fileName, action)
        # tokens = [view,branch,scmbranch,bundle,crList,action,info,path,stream]    
        branch = tokens[1]
        crList = tokens[4]
        if crList[0] in ['nocr']:
            return ''
        dupBR, dupCR, dupStatus = self.setCRBRStatus(branch, crList, path, status)
        if dupBR > 0: msg = 'BR->'
        else:         msg = '    '
        if dupCR > 0: msg += 'CR->'
        else:         msg += '    '
        if dupStatus > 0: msg += '->Stat '
        else:             msg += '       '
        
        msg += '%16s %24s %s %s %s' %(status, branch, tokens[0], crList, path)
        return msg


    def setCRBRStatus(self, branch, crList, path, status='done'):
        """ sets two tool global dictionaries to highlight duplicate branches & CRs """
        dupBR = 0
        dupCR = 0
        dupStatus = 0
        #print "self.BRs: %s; branch: %s" %(self.BRs, branch)

        if type(branch) == type([]):
            branch = branch[0]
            
        if self.BRs.has_key(branch):
            dupBR = 1
            tokens = self.BRs[branch]
            dupStatus += len(tokens.keys())
            tokens[status] = [crList,path]
            self.BRs[branch] = tokens
        else:
            self.BRs[branch] = {status:[crList,path]}
            
        for cr in crList:
            if self.CRs.has_key(cr):
                dupCR += 1
                tokens = self.CRs[cr]
                dupStatus += len(tokens.keys())
                tokens[status] = [branch,path]
                self.CRs[cr] = tokens
            else:
                self.CRs[cr] = {status:[branch,path]}
        
        return dupBR, dupCR, dupStatus    
            

    def getCRBRfromFileName(self, fileName):
        """ just return the prepended CR list and remaining branchname from filename string 
        """
        branch = []
        crList = ['nocr']
        if fileName[:5] == 'blast':  branch = [fileName]
        else:
            brSearch = self.branchRE.search(fileName)
            if brSearch:
                br1 = brSearch.group('brString')
                branch.append(br1)
                branchList = string.split(fileName,'%s-'%br1)
                if len(branchList) > 1:                           #April 30, 2004 CV use last branch in token file
                    branch.append(branchList[-1])
                    #msg = 'WARNING: Found multiple branch names using in this order %s' %(branch)
                    #print(msg)
                    #self.sfb.dlog.info(msg)
                
            crSearch = self.crRE.search(fileName)
            if crSearch:
                crStr  = crSearch.group('crString')
                crList = string.split(crStr, '_')
                if crList[0] == 'nocr':
                    msg = 'Found NOCR in branch %s of %s ' %(branch, fileName)
                    #self.sfb.dlog.warn(msg)
        return branch, crList

    def processFile(self, path, fileName, action='NEW', isDir=False):
        """ Check what type of path we have right now just from the filename and containing directory
        """
        #print "File Names & paths %s ... %s ... %s ...%s "% (path,fileName,action,isDir)
        valpath=path.find('archived')
        if valpath != -1:            
            return 0
                
        if self.numDone > self.numDoneMax: return 0   # debug escape
        if self.numPassed > self.numPassedMax: return 0   # debug escape
        #fileName = os.path.basename(path)
        #dirName  = os.path.dirname(path)
        if fileName in ['summary.txt','summary.txt~','old-summary.txt','old_summary.txt']:
            return 0
        if fileName.find('summary') != -1: return 0
        crList = ['cr_unknown']
        branch = 'branch_unknown'
        status, tokens = self.getStatusFromPath(path, fileName, action)      # set self.codeStream for use below
        # tokens = [view,branch,scmbranch,bundle,crList,action,info,path,stream]
        if status in ['SCM-Need Branch']: return 0   # skip token files that are in a no operation directory
        if status in ['Archived directory']: return 0 # Skip Old Archived Directory
        if status == 'alert': 
            self.sfb.setLog('walkSCMOther is looping on a branch %s' %tokens, 'critical')
            
        view   = tokens[0]
        branch = tokens[1]
        if branch == []:
            branch = ''
            print 'Empty branch for %s' %fileName
        elif type(branch) is type([]):
            branch = branch[0]
        scmbranch = tokens[2]
        bundle = tokens[3]
        crList = tokens[4]
        state = tokens[5]
        #if state == 'done':
        #    branch = tokens[1][-1]
        info   = tokens[6]
        scmpath = tokens[7]
        stream = tokens[8]

        if crList[0] in ['list','nocr']: return 0   # skip temporary listing files
        
        if self.reportType == 'line':
            if isDir: p ='D'
            else:     p ='-'
            if action == 'NEW': p+='N-'
            else:               p+='D-'
            self.numReady +=1
            msg = '%s-%s%s-%s %s %35s %s for %s ' %(self.numReady, p, stream, status, view, branch, info, crList)
            print msg
            if crList[0] != 'nocr':
                self.sfb.dlog.info(msg)
            if self.debug >2: print '%s' %tokens
        else:
            msg = self.getReport(path, fileName)
            print msg
            
        if action != 'NEW': # No update of SF just sync in trees
            done = self.updateTokenFile(fileName, path, action)
            return 0
        
        elif view == 'team': # handle RTL test Build sub process
            done = self.updateForTeam(fileName, path, action)
            return done

        else: # This is default update of SF on new files in SCM tree
            spath = self.getFullPath(path, fileName, 'scm')
            node = FileNode(path=spath, data=None, info=info, tool=self)
            node.load(contents=False)                # sets mdate
            node.getTokenFileInfo(stream=stream)   # sets self.branch, self.codeStream, self.doneDate, loads self.doneCRs
            cstream    = node.codeStream
            mantleTime = node.doneDate
        
            tbObj = SCMTaskBranch(sfTool=self.sfb)
            teamObj = SCMTeamBranch(sfTool=self.sfb)
            
            #allow Process Timestamp reset value to be passed in
            tbObj.psReset=self.psReset
            teamObj.psReset=self.psReset

            ### Here's where we actually try to find the (team|task) branch
            ### in SF based on the token file and action it.
            numCRLs = teamObj.setBranchStatusForCRnums( branch, crList, cstream, status, mantleTime, False, 'yes')

            if numCRLs < 0:
                # team failed - try the task branch version
                numCRLs = tbObj.setBranchStatusForCRnums( branch, crList, cstream, status, mantleTime, False, 'yes')
                
                if numCRLs < 0:
                    # TaskBranch not found
                    oldCR = False
                    for crNum in crList:
                        try:
                            if int(crNum) < 19900:  oldCR = True
                        except: pass
                        
                    if oldCR == True:
                        done = self.updateTokenFile(fileName, path, action)
                        self.sfb.setLog('walkSCMOther oldCR %s IN %s not found in SF oldCR in %s, NOT processing anymore' %(branch,scmpath,crList), 'warn')
                        return 0
                    else:
                        done = self.updateTokenFile(fileName, path, action)
                        self.sfb.setLog('walkSCMOther skipped %s IN %s unable to updated one of %s' %(branch,scmpath,crList), 'warn')
                        self.sfb.setLog('%s' %(tokens), 'warn2')
                        return 0
                
                                 
            self.numPassed += 1

            if numCRLs >= 0:
                done = self.updateTokenFile(fileName, path, action)

            if numCRLs > 0:
                self.numDone += 1
                
            return numCRLs


    def updateForTeam(self, fileName, path, action ):
        """ team branch specific sForce Updates
            Need to be sure that all token files are in directory, this could be triggered in process
        """
        print 'Called updateForTeam with %s at %s as %s'%(fileName, path, action)
        print ' This method is disabled for testing.'
        if 0:
            spath = self.getFullPath(path, fileName, 'scm')
            node = FileNode(path=spath, data=None, info=info, tool=self)
            node.load(contents=False)                # sets mdate
            node.getTokenFileInfo()   
            # sets self.branch, self.codeStream, self.doneDate, loads self.doneCRs
            stream    = node.codeStream
            mantleTime = node.doneDate
            state = 'done'   
            # CV saw the bug below and set the value not sure what to do

            if state == 'done':
                #accessDateStr = time.strftime("%Y/%m/%d %H:%M", time.localtime(node.adate))
                #diffSec =  time.time() - node.adate
                #print 'Team token %s last accessed %s %s secs ago' %(path,accessDateStr, diffSec)
                #if diffSec < 60:    #File accessed in last 60 seconds
                #    return 0
                pathList = path.split('/')    # note first element will be empty string
                print "pathList: %s " %pathList
                blastDir = '%s/%s' %(pathList[1],pathList[2])
                if blastDir == path:
                    checkPoint = fileName
                else:
                    checkPoint = pathList[-1]
                dpath = self.getFullPath(blastDir, checkPoint, 'scm')
                print 'path:%s, blastDir:%s, checkPoint:%s dpath:%s' %(path, blastDir, checkPoint, dpath)
                dnode = Node(path=dpath, data=None, info=info, tool=self)     
                dnode.load()                      # not dnode.data has list of token files
                dnode.getFilesNodes()             # loads fileNodes in list of nodes with node.data & node.crList
                msg = 'Found new RTL team Checkpoint path: %s %s with tokens%s' %(blastDir, checkPoint, dnode.data)
                self.sfb.log.info(msg)
                print msg

                # Check for LOADING flag file in this dir.
                # Bail on this team branch if we find it.
                loadFlagPath = os.path.join(self.scm_root, blastDir,
                                            checkPoint, 'LOADING')
                if os.path.exists(loadFlagPath):
                    msg = "Checkpoint %s is not yet ready for submission - will check at next run" \
                          %checkPoint
                    self.sfb.log.info(msg)
                    print msg
                    return 0

                ckpntCRList = []
                fdata  = ''
                brObj = TeamBranch(branch='junk', logname='sf.rtlWalk')
                totalNodes = len(dnode.nodes)
                num = 0
                for fnode in dnode.nodes:         # each node represents a token file (branch & crs)
                    num += 1
                    branch = fnode.branch
                    crList = fnode.crList
                    print '%s/%s Ready to set Team label MODs for %s TO %s for %s' %(num, totalNodes, branch, checkPoint, crList)
                    brObj.loadBranch(branch=branch, stream=stream)
                    bmtot = len(brObj.MODs)
                    updatedIDs = brObj.setTeamBranch(checkPoint)
                    msg = '%s/%s Updated %s/%s MODs from %s TO %s' %(num, totalNodes, len(updatedIDs),bmtot, branch, checkPoint)
                    self.sfb.log.info(msg)
                    print msg
                    fdata = '%s\n%s' %(fdata, fnode.data)  # need to pass this to the new token file??
                    ckpntCRList.append(crList)
                    done = self.updateTokenFile(fnode.name, path, action)
                # load branch object with this new checkpoint branch
                brObj.setStream(stream)
                brObj.getTeamMODs(tbranch=checkPoint, useStatus=False, status='Team Branch Hold')  # ignore status ?? check later
                tMODs = brObj.teamMODs
                print 'Found %s team branch MODs '%len(tMODs)
                brObj.getTeamCRs(tbranch=checkPoint)
                brObj.MODs = tMODs
                brObj.setBranch(checkPoint)
                msg = 'Loaded new Team Branch %s with %s MOD in %s' %(brObj.branch, len(brObj.MODs), brObj.crNums)
                self.sfb.log.info(msg)
                print msg
                updatedIDs = brObj.submitToSCM()
                num = len(updatedIDs)
                msg = 'Update %s MODs and created new token in SCM' %(num)
                self.sfb.log.info(msg)
                print msg
                branch=checkPoint
                cstream = stream
                exitNow = True
            else:
                exitNow = False
        
            tbObj = SCMTaskBranch(sfTool=self.sfb)
            numCRLs = tbObj.setBranchStatusForCRnums( branch, crList, cstream, status, mantleTime, False, 'yes')
                               
            if exitNow == True: sys.exit(0)
                                 
            self.numPassed += 1
            if numCRLs == 0:
                done = self.updateTokenFile(fileName, path, action)
                return 0
            elif numCRLs > 0:
                self.numDone += 1
            return numCRLs
                
            
        

    def updateTokenFile(self, fileName, path, action='NEW'):
        """ Create or delete files in the tmp_root version of the SCM tree """
        if path == '/': return 0
        else:
            if path[0] == '/': 
                path = path[1:]
        spath = os.path.join(self.scm_root, path, fileName)
        tpath = os.path.join(self.tmp_root, path, fileName)
        if os.path.isdir(tpath):
            if action == 'NEW':
                try:
                    os.mkdir(tpath)
                    if self.debug >0: print 'SCM-tmp DIR create %s\n' %(tpath)
                except Exception, e:
                    msg = 'ERROR updateTokenFile Make DIR Failed for %s  %s, %s\n' %(tpath, Exception, e)
                    print msg
            else:
                try:
                    self.removeAll(tpath)
                    if self.debug >0:print 'SCM-tmp DIR delete %s\n' %(tpath)
                    if self.debug >1:print '      with files %s' %(os.listdir(tpath))
                except Exception, e:
                    msg = 'ERROR updateTokenFile Delete DIR Failed for %s  %s, %s\n' %(tpath, Exception, e)
                    print msg
                

        elif os.path.isfile(tpath):
            if action == 'NEW':
                print 'ERROR cannot OVERWRITE %s\n' %(tpath)
            else:
                try:
                    if self.debug >0:print 'SCM-tmp Deleting %s\n' %(tpath)
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
                    if self.debug >0:print 'SCM-tmp Writing %s bytes in %s\n' %(len(data), tpath)
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
                            print 'SCM-tmp Writing %s bytes in %s\n' %(len(data), tpath)
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
            
    def getBranchMods(branch, codestream):
        """ get the list of MOD dictionaries for the given branch in codeastream """
        MODs = self.sfb.getSFInfoByContains(branchField, branch)
        if len(MODs) == 0: 
            self.sfb.dlog.warn('WARN not MOD found in cs:%s for Branch:%s' %(codestream, branch))
            return []
        return MODs

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
        


    def getCRBackupData(self, fpath):
        """ load a back of the Case data to fix problem we introduced in the live data
        """
        node = FileNode(path=fpath, data=None, info='CR Backup Data', tool=self)
        node.load()  # load whole csv file in the attribute self.data
        self.lookupCR = {}
        # csv format is ['50030000000EOId', '23401', 'Clarify CR', '19233', '"Neil ', 'Wright"', 'run plan create subcap  fails in v4.0 on alibrary & design that passes in 3.2', 'Closed', 'Bug']
        num = 0
        for row in node.data:
            num += 1
            #if num < 20: print row
            #if len(row) < 2: continue
            if row[2] == 'Clarify CR':
                crID   = row[0]
                crNum  = int(row[1])
                clfID  = row[3]
                if clfID in [None,'']:
                    print 'No Clarify Number found for imported CR %s  %s' %(crNum, row)
                else:
                    if clfID[0] == 'C': clfID = clfID[1:]
                clfOrg = row[4]
                crSubj = row[5]
                crOpen = row[6]
                self.lookupCR[crNum] = {'crID':crID, 'clarifyID':clfID, 'clarifyName':clfOrg, 'subject':crSubj, 'crOpen':crOpen }
        print '\ngetCRBackupData found %s CRs as keys\n' %len(self.lookupCR)
      
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
        tbObj = SCMTaskBranch(sfTool=self.sfb)
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



    def fixCRSubject(self, CR):
        """  reset the CR subject to the value from the key file
        """
        crNum = int(CR.get('caseNumber'))
        if crNum is not None:
            crInt = int(crNum)
            if not self.lookupCR.has_key(crInt):
                print 'CR %s (%s) not found in lookup table of %s elements' %(crInt, crNum, len(self.lookupCR))
            else:
                keyVal = self.lookupCR[crInt]
                newSubject = '%s' %keyVal.get('subject')
                oldSubject = '%s' %CR.get('subject')
                clarifyID = keyVal.get('clarifyID')
                crID = keyVal.get('crID')
                if crID != CR.get('id'):
                    msg = 'fixCRSubject found the wrong CR %s clarify:%s,  %s' %(crNum, clarifyID, newSubject)
                    self.sfb.dlog.error(msg)
                    print msg
                    return 0
                if oldSubject not in newSubject:
                    self.sfb.fixCR(CR, options={'subject':newSubject}, status='noChange')
                    msg = 'fixCRSubject updated CR:%s clarify:%s, FROM:%s:  TO:%s:' %(crNum, clarifyID, oldSubject, newSubject)
                    self.sfb.log.info(msg)
                    print msg
                    return 1
                return 0
        

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

    def setProblemMod(self, name, type='sfSet', results='', sfDict={}):
        """ load the MOD specific loading problems, name is modID or CaseID"""
        clarifyCrField   = self.sfb.caseFields['Clarify ID']
        if self.problems.has_key(name):
            pd = self.problems[name]
            pt = pd['type']
            self.sfb.dlog.warn('%s %s  %s clarifyID:%s', type,name,results, sfDict.get(clarifyCrField,''))
            pd['results'] = results
            pd['data'] = sfDict
        else:
            pd = {'name':name, 'type':type, 'results':results, 'data':sfDict}
            self.sfb.dlog.warn('%s %s  %s clarifyID:%s', type,name,results,sfDict.get(clarifyCrField,''))
        self.problems[name] = pd





#############################################################################################################
#   A directory walker that compares the production directory to a temp copy to find difference
#   and trigger change events to drive an updater.
#############################################################################################################
class walkSCMdir:
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
            self.ignore = ['RCS', 'CVS', 'tags','logfiles','.htaccess','blast3.2','blast4.1','blast3.1','blast3','replacement','replaced'] 
        else:
            self.ignore = ignore

    def phase0(self): # Compare everything except common subdirectories
        self.left_list = _filter(os.listdir(self.left),
                                 self.hide+self.ignore)
        self.right_list = _filter(os.listdir(self.right),
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
            self.subdirs[x]  = walkSCMdir(a_x, b_x, self.tool, self.ignore, self.hide, self.maxNum)

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
        """ just care about differences in left dir (scm_dir) """
        dname = self.left[len(self.tool.scm_root):]
        if self.totalNum > self.maxNum: return
        #print 'diff', self.left, self.right
        pnum = 0
        procType = 'update'
        if hasattr(options, 'list'):
            procType = options.list
        
        if self.left_only and dname not in [None,'']:
            self.left_only.sort()
            #self.tool.sfb.dlog.info('Scanning for New file the SCM Directory %s', dname)
            msg = 'SCM dir %s has %s NEW Files to Process' %(dname, len(self.left_only))
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
                    tpath = self.tool.getTempPathFromSCMPath(fpath)
                    if not os.path.exists(tpath): 
                        if os.path.isdir(fpath): 
                            print 'INFO missing the temp directory %s'%tpath
                            try: os.makedirs(tpath)
                            except:
                                head,tail = os.path.split(tpath)
                                try: os.mkdir(head)
                                except: print 'ERROR Could not create new directory %s'%tpath
                     
                    if os.path.isdir(fpath): 
                        fileList = _filter(os.listdir(fpath),self.hide+self.ignore)  # go down one level to process this new directory
                        sdname = os.path.join(dname,fileName)                         # add this dir name to end of relative path
                        msg = 'SCM subdir %s Processed %s NEW files' %(sdname, len(fileList))
                        if self.tool.debug >0: print msg
                        for fName in fileList:
                            self.tool.processFile(sdname, fName, 'NEW')
                            pnum += 1
                    else:
                        self.tool.processFile(dname, fileName, 'NEW')
                        pnum += 1
                msg = 'SCM dir %s Processed %s NEW files' %(dname, pnum)
                print msg
                self.totalNum += pnum
            
            
        if self.right_only:
            self.right_only.sort()
            msg = 'SCM dir %s has %s MOVED Files to Process' %(dname, len(self.right_only))
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
                        fileList = _filter(os.listdir(fpath),self.hide+self.ignore)  # go down one level to process this new directory
                        sdname = os.path.join(dname,fileName)                        # add this dire name to end of relative path
                        msg = 'SCM dir %s has %s MOVED files to process' %(sdname, len(fileList))
                        if self.tool.debug >0: print msg
                        for fName in fileList:
                            self.tool.processFile(sdname, fileName, 'MOVED')
                            pnum += 1
                    else:
                        self.tool.processFile(dname, fileName, 'MOVED')
                        pnum += 1
                        
                msg = 'SCM dir %s Processed %s MOVED files' %(dname, pnum)
                print msg
                self.totalNum += pnum
            
        if self.diff_files:
            self.diff_files.sort()
            msg = 'Scanning for Differing file the SCM Directory %s %s' %(dname, self.diff_files)
            if self.tool.debug >1:print msg
            #self.tool.sfb.dlog.info(msg)
        if self.funny_files:
            self.funny_files.sort()
            msg = 'Scanning for Troubled file the SCM Directory %s %s' %(dname, self.funny_files)
            if self.tool.debug >1: print msg
            #self.tool.sfb.dlog.info(msg )
        if self.common_funny:
            self.common_funny.sort()
            msg = 'Scanning for Common Funny file the SCM Directory %s %s' %(dname, self.common_funny)
            if self.tool.debug >1: print msg
            #self.tool.sfb.dlog.info(msg )
        if self.common_dirs:
            self.common_dirs.sort()
            msg = 'Common subdirectories in the SCM Directory %s %s' %(dname, self.common_dirs)
            if self.tool.debug >1: print msg
            #self.tool.sfb.dlog.info(msg )
        if self.same_files:
            pass
            #self.same_files.sort()
            if self.tool.debug >0: print '%3s Identical files in %s' %(len(self.same_files),dname )
    
        


#############################################################################################################
#   Methods called from the command line - cron oriented to update SalesForce
#############################################################################################################
def setMODStatus(path=None):
    """ set the MOD status from a CSV list of cs,CR,branch,status values """
    if path is None:
        path = '/home/sfscript/src/setModStatus.csv'
    tool = nodeTool()
    tool.setMODStatusFromCSV(path)
    

def updateDoneTokens(codeStream):
    """ Scan just the ~/blastX/done directories and update SF with the token info.
        Not using any temp directory to avoid multiple brute force updates.
    """
    if codeStream == 'all':
        #codeStream = ['3','3.0','3.1','3.2','4','4.0','4.1','4.2']
        #codeStream = ['4.1','4','4.0']
        codeStream = ACTIVE_STREAMS
    else:
        codeStream = [codeStream]
        
    fix = 'yes'    
    for cs in codeStream:
        if cs[:1] in ['3','4']:
            #prepend a 'blast' is stream is 3.x or 4.x 
            pathStr = 'blast%s/done' %cs
        else:
            pathStr = '%s/done' %cs
            
        getDoneCRs(pathStr, str(cs), fix)
        print 'Processing token files in %s\n' %pathStr



def getDoneCRs(path, cstream=None, fix='no'):
    """ main logic method to be called from command line
    """
    if path is None: donePath = 'sf-scm/done'
    else:            donePath = path 
    ts1 = time.time()
    tool = nodeTool(sfb=None)
    tool.sfb.getConnectInfo(version, ts1)
    ts2 = time.time()
    doneTree = Node(id='sf_done', name='done', path=donePath, data=None, info='done directory', tool=tool)
    print 'doneTree created with path:%s rpath:%s' %(doneTree.path, doneTree.rootpath)
    doneTree.load()
    doneTree.getFilesNodes(cstream)
    total = len(doneTree.nodes)
    done = 0
    print 'LOADED %s fileNodes in %s' %(total,path)
    keyPath = '/home/sfscript/data/caseBackup12-02-03-subset.csv'
    tool.getCRBackupData(keyPath)
    for node in doneTree.nodes:
        numDone = node.setSFDone(cstream, fix)
        done = done + 1
        #if done > 6: break
        if numDone > 0:
            tool.sfb.log.info('Processed %s/%s and updated %s CRs & MODs', done, total, numDone)
        node.out()
    print '\nHow is that?\n'
    print '%s The Problems \n%s' %(hr,hr)
    for pdk in tool.problems.keys():
        pd = tool.problems[pdk]
        print '%s Problem with %s' %(pd['type'],pdk)
        print '\t%s' %pd.get('results')
        pp = pd['data']
        if pp.has_key('caseNumber'): print '\tCaseNumber: %s\n'%pp['caseNumber']
        if pp.has_key('subject'):    print '\tSubject: %s\n'%pp['subject']
        print '\t%s\n%s' %(pp,hr)
    print '%s\n%s' %(hr,hr)


        
def walkSCM_updateSF(codeStream, options=None):
    """ compare the two directories """
    #  get reference to Salesforce
    ts1 = time.time()
    sfb = SCMTaskBranchTool(debug=options.debug, logname='sf.walkSCMOther')

    # Acquire lock - exit if script is running
    try:
        lockHandle = cronLock('sfwalkSCMOther.lock')
    except Exception, e:
        msg = 'Could not acquire exclusive lock for cron run. Assume another instance is being run. EXITING.'
        sfb.setLog(msg, 'warn')
        sfb.setLog('Information from locking operation was: %s' %e,'warn')
        print msg
        sys.exit()
        
    sfTime = (time.time()-ts1)
    tool = nodeTool(sfb=sfb, options=options)
    if options.parm in ['psReset']:
        tool.psReset=True
        sfb.dlog.info('Connecting to SalesForce took %s secs PSReset Active' %(sfTime))
    else:
        sfb.dlog.info('Connecting to SalesForce took %s secs' %(sfTime))
    ts2 = time.time()
    tool.setReport('line')
    tool.setCodeStreams(codeStream)
    ignore = ['RCS', 'CVS', 'tags','logfiles','.htaccess','replaced','replacement'] 
    for cs in tool.allStreams:
        if cs not in tool.codeStreams:
            if cs[:1] in ['3','4','5']:
                ignore.append('blast%s'%cs)
            else:
                ignore.append('%s'%cs)

    
    print 'Starting Script with CodeStream set to %s' %str(codeStream)
    maxNum = int(options.num)/100
    if options.list == 'update': print ' sForce will be update a max of %s tokens with the status from the SCM directory'%maxNum
    else:    print 'This run will just check for duplicate branches, use -lupdate to update'
    print 'IGNORING the dirs %s' %ignore

    print "\n\n\nleft: %s, right: %s\n" %(tool.scm_root, tool.tmp_root)
    walkDir = walkSCMdir(tool.scm_root, tool.tmp_root, tool, ignore, maxNum=maxNum)
    sfb.dlog.info('SF Connect %s secs and Compare paths took %s secs' %(sfTime,(time.time()-ts2)))
    print '______________________________________________________________'
    walkDir.walk_breadth_dir(options) 
    # The real work is done recusiveley by the call above with the call: 
    #   self.tool.processFile(dname, fileName, 'NEW')
    #     dname is directory name to determine status
    #     filename will be parsed for crList & branch label
    print '______________________________________________________________'
    secs = (time.time() - ts1)        
    min  = int(secs/60)
    sec  = int(secs-min*60)
    msg = 'Updated %s and scanned %s tokens for streams %s in %s min %s secs' %(tool.numDone, tool.numPassed, codeStream,min,sec)
    print msg
    sfb.log.info(msg)
    

def walkSCM_list(codeStream, options=None):
    """ compare the two directories and print the state """
    ts1 = time.time()
    tool = nodeTool(options=options)

    # Acquire lock - exit if script is running
    try:
        lockHandle = cronLock('sfwalkSCMOther.lock')
    except Exception, e:
        msg = 'Could not acquire exclusive lock for cron run. Assume another instance is being run. EXITING.'
        tool.sfb.setLog(msg, 'warn')
        tool.sfb.setLog('Information from locking operation was: %s' %e,'warn')
        print msg
        sys.exit()
    
    
    sfTime = (time.time()-ts1)
    tool.sfb.dlog.info('Connecting to SalesForce took %s secs' %(sfTime))
    tool.setReport('line')
    tool.setCodeStreams(codeStream)
    ignore = ['RCS', 'CVS', 'tags','logfiles','.htaccess','replaced','replacement'] 
    for cs in tool.allStreams:
        if cs not in tool.codeStreams:
            if cs[:1] in ['3','4']:
                ignore.append('blast%s'%cs)
            else:
                ignore.append('%s'%cs)
    print 'Starting Script with CodeStream set to %s' %codeStream
    print 'IGNORING the dirs %s' %ignore
    walkDir = walkSCMdir(tool.scm_root, tool.tmp_root, tool, ignore)
    tool.sfb.dlog.info('SF Connect %s secs and Compare paths took %s secs' %(sfTime,(time.time()-ts1)))
    print '______________________________________________________________'
    walkDir.walk_breadth_dir(options) 
    print '______________________________________________________________'
    secs = (time.time() - ts1)        
    min  = int(secs/60)
    sec  = int(secs-min*60)
    msg = 'Updated %s and scanned %s tokens for streams %s in %s min %s secs' %(tool.numDone, tool.numPassed, codeStream,min,sec)
    print msg
    #tool.sfb.log.info(msg)
    
    
#############################################################################################################
#   Methods called from the command line - User oriented to update CRs or MODs
#############################################################################################################
def walkCRs_setStatus(daysAgo, options=None):
    """ walk all CRs and reset the status based on the containing MODs 
        Not needed, right?
    """
    ts1 = time.time()
    print 'Debug is %s' %options.debug
    sfb = SCMTaskBranchTool(debug=options.debug, logname='sf.walkCRs')
    CRs = sfb.getActiveCRs(daysAgo)
    if hasattr(options, 'num'):
        num = options.num.split(',')
        max = int(num[0])
        if len(num) == 2:
            start = int(num[1])
        else: start = 0
    else:
        max = 5
        start = 0
    print 'Found %s CRs to process in %1d secs will process %s starting at %s' %(len(CRs),(time.time()-ts1),max, start)
    num = 0
    for CR in CRs:
        crClosed = CR.get('closed')   # boolean
        num +=1
        if num < start: continue
        if num > max : break
        crStatOrg = CR.get('status')
        crStatus  = sfb.getCRStatus(CR=CR, MODs=None, fixMods=False)             # an opportunity to fix the MODs
        crNum = int(CR.get('caseNumber'))
        csPriority = CR.get(sfb.caseFields.get('Code Streams & Priority'),'')

        if crClosed:
            crStatus  = 'Closed'
        else:
            if crStatus[:6] == 'Closed':
                sfb.log.warn('Closing the CR:%s All MOD for streams %s have been completed', crNum, csPriority)
                crStatus = 'Fixing'
        ts = time.strftime('%y%m%d-%H:%M:%S',time.localtime())
        if crStatOrg == crStatus:
            print '%s %3s CR:%s %s - %s No change' %(ts, num, crNum, csPriority, crStatus)
        else:
            print '%s %3s CR:%s %s - %s -> %s' %(ts, num, crNum, csPriority, crStatOrg, crStatus)
            crChanges = sfb.setCRStatus(CR, crStatus)      # crChanges is -1 for not change else number of changes

    secs = (time.time() - ts1)        
    min  = int(secs/60)
    sec  = int(secs-min*60)
    print 'Processed %s of %s CRs in %s min %s secs' %(num,len(CRs),min,sec)



#############################################################################################################
#   Methods called from the command line - User oriented to just show the sate of the SCM tree
#############################################################################################################
def searchForBranch(branch, teamBranch=None, options=None):
    """  Search the directory tree for the branch and output
         the status and the contents of the token file
    """
    debug = 0
    if hasattr(options, 'debug'): debug = options.debug
    print 'This command will search the SCM directory tree then SalesForce'
    startTime = time.time()
    tool = nodeTool(logname='sf.walkFix')
    #tool.sfb.getConnectInfo(version, startTime)
    branchRE = re.compile(branch)
    found = []
    reports = []
    branches = {}
    brstr = branch
    csstr = options.code
    ts1 = time.time()
    def getStream(path):
        pathList = path.split('/')
        if len(pathList) > 1:
            blast = pathList[1]
        else:
            blast = 'root'

        if blast[:5] == 'blast' and blast != 'blast5':
            stream = blast[5:8]
            if '_' in stream:
                stream = stream.split('_')[0]

        else:
            stream = blast
        
        if stream not in tool.allStreams:
            if options.code in tool.allStreams:
                stream = options.code
            else:
                stream = DEFAULT_STREAM
        return stream
    ignoreDirs = ['replaced','replacement']
    print 'Searching the SCM directories for tokens with the string %s'%branch
    for root, dirs, files in os.walk(tool.scm_root):  # root is just dirpath for the loop
        thisdir = os.path.basename(root)
        if thisdir in [None,'']: thisdir = os.path.basename(root[:-1])
        if thisdir in ignoreDirs:
            continue
        for file in files:
            if branchRE.search(file):
                path = tool.getRelPath(root)
                found.append(os.path.join(path, file))
                fpath = os.path.join(root,file)
                if os.path.isfile(fpath):
                    f_stat = os.stat(fpath)
                    mdate = f_stat[8]
                else: mdate = 0
                report = tool.getReport(path,file, mdate)
                reports.append(report)
                branch, crList = tool.getCRBRfromFileName(file)
                stream = getStream(path)
                if branch != []:
                    if type(branch) == type([]): branch = branch[0]
                    branches[branch]=stream
                else:
                    print 'Could not find branch label in %s cs:%s'%(file,stream)
                
            elif teamBranch:
                if teamRE.search(file):
                    path = tool.getRelPath(root)
                    found.append(os.path.join(path, file))
                    report = tool.getReport(path,file)
                    reports.append(report)
        for dir in dirs:
            if branchRE.search(dir):
                path = tool.getRelPath(root)
                found.append(os.path.join(path, dir))
                fpath = os.path.join(root,dir)
                if os.path.isdir(fpath):
                    f_stat = os.stat(fpath)
                    mdate = f_stat[8]
                else: mdate = 0
                report = tool.getReport(path,dir, mdate)
                reports.append(report)
                branch, crList = tool.getCRBRfromFileName(file)
                stream = getStream(path)
                branches[branch[0]]=stream
            

    print 'Scanned SCM in %s secs and found %s branches\n' %(int(time.time() - ts1),len(found))
    if len(found) > 40:
        print 'Dude, take it easy. use a more specific string'
    num = 0
    for token in found:
        num += 1
        print '%s %s' %(num, token)
    if len(found) > 0:
        print 'Detailed Status these Branches:'    
    num = 0
    for report in reports:
        num += 1
        if report != '':
            print '%s %s' %(num, report)
    num = 0
    total = len(branches)
    if total == 0:
        if options.code in tool.allStreams:
            stream = options.code
        else:
            stream = '4'
        if hasattr(options,'cs'): stream = options.cs
        branches[branch] = stream
    show=False
    if debug >2:
        show = True
        
    print 'Task Branch information from SalesForce for branch %s in stream %s'%(branch, stream)
    brObj = SFTaskBranch(sfTool=tool.sfb, debug=debug)
    simpleBranch = {brstr:csstr}
    for br in simpleBranch.keys():
    #for br in branches.keys():
        num += 1
        if br != '':
            #stream = branches.get(br)
            stream = csstr
            #print '%s/%s %s in %s' %(num, total, br, stream)
            #ret = brObj.getSFData('%%%s%%'%br, stream, show=show)
            ret = brObj.getSFData('%s'%br, stream, show=show)
            tbInfo = brObj.getData('Task_Branch__c')
            if tbInfo in [None,'',{}]:
                print 'No branch found on SalesForce with the string %s in stream %s'%(br,stream)
                continue
            nbr = len(tbInfo)
            if nbr >0:
                br = tbInfo.get('Branch__c')
                cs = tbInfo.get('Code_Stream__c')
                brObj.branch = br
                brObj.stream = cs
                print 'Found branch %s in stream %s on SalesForce\n'%(br,cs)
                updated = brObj.setBranchStatus()
                if updated == True:
                    print 'Fixed a problem in branch %s stream %s'%(br,cs)
                brText = brObj.getBranchInfo()
                print '\n%s'%brText
            
    tool.sfb.log.info('Search for Branch: %s, found %s items in %s sec',branch, len(reports),int(time.time()-startTime))    


def fixBranch(branch, options=None):
    """  Search the directory tree for the branch find status
         and update sForce based on SCM status
    """
    debug = 0
    if hasattr(options, 'debug'): debug = options.debug
    print 'This command will search the SCM directory tree for status then update SalesForce'
    startTime = time.time()
    tool = nodeTool(logname='sf.walkFix')
    branchRE = re.compile(branch)
    found = []
    reports = []
    branches = {}
    brstr = branch
    csstr = options.code
    ts1 = time.time()
    def getStream(path):
        pathList = path.split('/')
        blast = 'root'
        stream = '0'
        if len(pathList) > 1:  blast = pathList[1]
        if blast[:5] == 'blast' and blast != 'blast5':
            stream = blast[5:8]
            if '_' in stream:
                stream = stream.split('_')[0]
                pass
        else:
            stream = blast
            pass
        
        if stream not in tool.allStreams:
            stream = DEFAULT_STREAM
            if options.code in tool.allStreams:
                stream = options.code
                pass
            pass
        
        return stream
    ignoreDirs = ['replaced','replacement']
    print 'Searching the SCM directories for tokens with the string %s'%branch
    for root, dirs, files in os.walk(tool.scm_root):  # root is just dirpath for the loop
        thisdir = os.path.basename(root)
        if thisdir in [None,'']: thisdir = os.path.basename(root[:-1])
        if thisdir in ignoreDirs:
            continue
        for file in files:
            if branchRE.search(file):
                path = tool.getRelPath(root)
                found.append(os.path.join(path, file))
                fpath = os.path.join(root,file)
                if os.path.isfile(fpath):
                    f_stat = os.stat(fpath)
                    mdate = f_stat[8]
                else: mdate = 0
                report = tool.getReport(path,file, mdate)
                reports.append(report)
                branch, crList = tool.getCRBRfromFileName(file)
                stream = getStream(path)
                if branch != []:
                    if type(branch) == type([]): branch = branch[0]
                    branches[branch]=stream
                else:
                    print 'Could not find branch label in %s cs:%s'%(file,stream)
                
        for dir in dirs:
            if branchRE.search(dir):
                path = tool.getRelPath(root)
                found.append(os.path.join(path, dir))
                fpath = os.path.join(root,dir)
                if os.path.isdir(fpath):
                    f_stat = os.stat(fpath)
                    mdate = f_stat[8]
                else: mdate = 0
                report = tool.getReport(path,dir, mdate)
                reports.append(report)
                branch, crList = tool.getCRBRfromFileName(file)
                stream = getStream(path)
                branches[branch[0]]=stream

    print 'Scanned SCM in %s secs and found %s branches\n' %(int(time.time() - ts1),len(found))
    num = 0
    for token in found:
        num += 1
        print '%s %s' %(num, token)
    show=False
    if debug >3:
        show = True
        
    print 'Task Branch information from SalesForce for branch %s in stream %s'%(branch, stream)
    brObj = SFTaskBranch(sfTool=tool.sfb, debug=debug)
    simpleBranch = {brstr:csstr}
    for br in simpleBranch.keys():
        if br != '':
            #stream = simpleBranch.get(br)
            stream = csstr
            ret = brObj.getSFData('%s'%br, stream, show=show)
            tbInfo = brObj.getData('Task_Branch__c')
            if tbInfo in [None,'',{}]:
                print 'No branch found on SalesForce with the string %s in stream %s'%(br,stream)
                continue
            nbr = len(tbInfo)
            if nbr >0:
                br = tbInfo.get('Branch__c')
                cs = tbInfo.get('Code_Stream__c')
                stat = tbInfo.get('Branch_Status__c')
                brObj.branch = br
                brObj.stream = cs
                print 'Found branch %s in stream %s with Status:%s on SalesForce'%(br,cs, stat)
                if stat in ['Closed - Passed']:
                    print '   Changing status to Merged'
                    stat = 'Merged'
                    
                updated = brObj.setBranchStatus(stat)
                if updated == True:
                    print 'Fixed a problem in branch %s stream %s'%(br,cs)
                #brText = brObj.getBranchInfo()
                #print '\n%s'%brText
            
    tool.sfb.log.info('Search for Branch: %s, found %s items in %s sec',branch, len(reports),int(time.time()-startTime))    

def ccSetStatusValues():
    """ return a list of valid SCM Status Values"""
    statList = []
    statList.append('Submitted to SCM')
    statList.append('SCM-Received')
    statList.append('SCM-Hold')
    statList.append('SCM-Need Branch')
    statList.append('SCM-Post-Release')
    statList.append('SCM-Patch-Build-Delayed')
    statList.append('SCM-Approved')
    statList.append('SCM-QOR Building')
    statList.append('SCM-QOR Results')
    statList.append('SCM-QOR Testing')
    statList.append('SCM-Ready to Bundle')
    statList.append('SCM-Bundle Building')
    statList.append('SCM-Bundle Results')
    statList.append('SCM-Bundle Testing')
    statList.append('SCM-Candidate-Building')
    statList.append('SCM-Patch-Build Today')
    statList.append('Merged')
    return statList

def ccSetBranchStatus(branch, stream, status, options=None):
    """  Called from ClearCase to set Branch Status
         for the branch in SForce.
         Warn but accept Status string as given
    """
    debug = 0
    if hasattr(options, 'debug'): debug = options.debug
    br = branch
    cs = options.code
    if cs[:5] == 'blast' and cs != 'blast5':
        stream = cs[5:8]
        
    print 'Will set the sForce Branch status for %s in %s'%(br,cs)
    startTime = time.time()
    if stream not in ['4','4.0','4.1','4.2','5','5.1']:
        print 'Warning: Code stream %s is unexpected' 
    if status not in ccSetStatusValues():
        print 'Warning: Status %s is not a valid status'%status
        
    sfb = SCMTaskBranchTool(debug=debug, logname='sf.ccSetStat')
    brObj = SFTaskBranch(sfTool=sfb, debug=debug)
    tbrObj = SCMTeamBranch(sfTool=sfb, debug=debug)
    branches = {br:stream}
    for br, stream in branches.items():
        eObj = tbrObj
        ret = eObj.loadTeamBranch(br, stream)
        if ret in brObj.badInfoList:
            eObj = brObj
            ret = eObj.loadBranch(br, stream)
            if ret in brObj.badInfoList:
                print 'Error: No branch found on SalesForce with branch %s in stream %s'%(br,stream)
                continue

        tbInfo = eObj.getData('Task_Branch__c')
        stat = tbInfo.get('Branch_Status__c')
        print 'Found branch %s in stream %s with Status:%s on SalesForce'%(br,cs, stat)
        statMap = sfb.getStatMap(stat,{})
        statOrder = statMap.get('order')
        statusMap = sfb.getStatMap(status,{})
        statusOrder = statMap.get('order')
        if statusOrder < statOrder:
            print 'Warning: You are moving the status backwards status:%s stat:%s'%(statusOrder,statOrder)
        
        # the next method does all the real work, plus runs metrics    
        updated = eObj.setBranchStatus(status)
        if updated == True:
            print 'Updated %s -> %s for branch %s stream %s'%(stat,status,br,cs)
        else:
            print 'No Change status %s for branch %s stream %s'%(stat,br,cs)
            

    
def resetBranch(stream, branch, options):
    """ reset the branch token in the shadow directory """
    debug = 0
    if hasattr(options, 'debug'): debug = options.debug
    print 'This command will search the SCM directory tree then SalesForce'
    startTime = time.time()
    tool = nodeTool()
    branchRE = re.compile(branch)
    found = []
    reports = []
    branches = {}
    ts1 = time.time()
    def getStream(path):
        pathList = path.split('/')
        if len(pathList) > 1:
            blast = pathList[1]
        else:
            blast = 'root'
            
        if blast[:5] == 'blast' and blast != 'blast5':
            stream = blast[5:8]
            if '_' in stream:
                stream = stream.split('_')[0]
        else:
            stream = blast
            
        if stream not in tool.allStreams:
            if options.code in tool.allStreams:
                stream = options.code
            else:
                stream = DEFAULT_STREAM
        return stream
    ignoreDirs = ['replaced','replacement']
    print 'Searching the SCM directories for tokens with the string %s'%branch
    for root, dirs, files in os.walk(tool.scm_root):  # root is just dirpath for the loop
        thisdir = os.path.basename(root)
        if thisdir in [None,'']: thisdir = os.path.basename(root[:-1])
        if thisdir in ignoreDirs:
            continue
        for file in files:
            if branchRE.search(file):
                path = tool.getRelPath(root)
                found.append(os.path.join(path, file))
                fpath = os.path.join(root,file)
                if os.path.isfile(fpath):
                    f_stat = os.stat(fpath)
                    mdate = f_stat[8]
                else: mdate = 0
                report = tool.getReport(path,file, mdate)
                reports.append(report)
                branch, crList = tool.getCRBRfromFileName(file)
                stream = getStream(path)
                branches[branch[0]]=stream
                
        for dir in dirs:
            if branchRE.search(dir):
                path = tool.getRelPath(root)
                found.append(os.path.join(path, dir))
                fpath = os.path.join(root,dir)
                if os.path.isdir(fpath):
                    f_stat = os.stat(fpath)
                    mdate = f_stat[8]
                else: mdate = 0
                report = tool.getReport(path,dir, mdate)
                reports.append(report)
                branch, crList = tool.getCRBRfromFileName(file)
                stream = getStream(path)
                branches[branch[0]]=stream
            

    print 'Scanned SCM in %s secs and found %s branches\n' %(int(time.time() - ts1),len(found))
    print '  Now deleting these tokens from %s'%tool.tmp_root
    num = 0
    for token in found:
        num += 1
        print '%s %s' %(num, token)
        tmpPath = os.path.join(tool.tmp_root,token)
        tpath = '%s%s'%(tool.tmp_root,token)
        print ' Delete? %s'%tpath
        if os.path.isfile(tpath):
            r = os.remove(tpath)
            print ' Deleted '
        else:
            print '  Does not exist'



def searchForCRs(crList, stream=None):
    """  Search the directory tree for the list of CRs and output
         the status and the contents of the token file
    """
    print 'You entered %s' %crList
    print 'You can use part of a branch string to see more branches'
    startTime = time.time()
    tool = nodeTool()
    tool.sfb.getConnectInfo(version, startTime)
    crRE = tool.crRE               # use common regex for supportability
    found = []
    reports = []
    ts1 = time.time()
    for root, dirs, files in os.walk(tool.scm_root):
        for file in files:
            crSearch = crRE.search(file)
            if crSearch:
                path = tool.getRelPath(root)
                found.append(os.path.join(path, file))
                crStr  = crSearch.group('crString')
                crList = string.split(crStr, '_')
                report = tool.getCrReport(path, file, crList)
                reports.append(report)

    print 'Scanned SCM in %s secs' %int(time.time() - ts1)
    num = 0
    for token in found:
        num += 1
        print '%s %s' %(num, token)
    print 'Status report for your Branches'    
    num = 0
    for report in reports:
        num += 1
        if report != '':
            print '%s %s' %(num, report)
    tool.sfb.log.info('Search for CRs %s, found %s items in %s sec',crList, len(reports),int(time.time()-startTime))    

def searchForStep(step, stream=None):
    """  Search the directory tree for a list of all the branches in a status.
         Possbile statuses are: ['received','qor','bundle','scmbuild']
    """
    print 'You looking for all the branches in %s' %step
    startTime = time.time()
    tool = nodeTool()
    tool.sfb.getConnectInfo(version, startTime)
    #stepRE = re.compile("^%s"%step)
    stepRE = re.compile("/*/%s"%step)
    branchRE = tool.branchRE
    found = []
    reports = []
    ts1 = time.time()
    for root, dirs, files in os.walk(tool.scm_root):
        for file in files:
            path = tool.getRelPath(root)
            brSearch = branchRE.search(file)
            if stepRE.search(path) and brSearch:
                brStr  = brSearch.group('brString')     # should be able to use this string to filter the output
                fpath = os.path.join(root,file)
                if os.path.isfile(fpath):
                    f_stat = os.stat(fpath)
                    mdate = f_stat[8]
                else: mdate = 0
                found.append(os.path.join(path, file))
                report = tool.getReport(path, file, mdate)
                reports.append(report)

    print 'Scanned SCM in %s secs' %int(time.time() - ts1)
    #for token in found:
    #    num += 1
    #    print '%s %s' %(num, token)
    print 'Status report for the Step %s' %step
    num = 0
    for report in reports:
        num += 1
        if report != '':
            print '%s %s' %(num, report)
    tool.sfb.log.info('Search Step %s, found %s items in %s sec',step, len(reports),int(time.time()-startTime))    
    

def findReleasePath(stream, scmTS):
    """ given code stream and scm timestamp, find the release path of the
    most likely build to contain the fix. Call this in a try block"""
    releasePath = None   
    
    scm_path = nodeTool.scm_path
        
    if stream in LEGACY_STREAMS:
        stream = 'blast%s' %stream
        pass

    # parse the scm timestamp into a date obj
    #scmTimestamp = time.mktime(time.strptime(scmTS, "%Y-%m-%dT%H:%M:%S"))
    scmDatetime = datetime.date.fromtimestamp(scmTS)

    releaseDir = os.path.join(scm_path, stream)    
    if os.path.isdir(releaseDir):        
        #globPath = '%s/2???_??_??.????*' %releaseDir
        globPath = '%s/2???_??_??*' %releaseDir       
        pathList = glob.glob(globPath)           
        
        # parse dates of all the valid possible release paths an map them
        relPathMap = {}
        for relDirPath in pathList:
            # check the perms - only accept ones which are g+rx
            stat_result = os.stat(relDirPath)
            mode = stat.S_IMODE(stat_result[stat.ST_MODE])
            if oct(mode)[2] < oct(5):
                # skip non group accesible or non-directories
                continue
            
            leadPath, relDir = os.path.split(relDirPath)
            relDirDateStr = relDir.split('-', 1)[0]                    
            try:
                relTimestamp = time.mktime(time.strptime(relDirDateStr,'%Y_%m_%d.%H%M'))
                #relTimestamp = time.mktime(time.strptime(relDirDateStr,
                #                                        '%Y_%m_%d'))                         
            except Exception, e:
                # problem parsing date string. Skip this release dir
                continue
            
            relDatetime = datetime.datetime.fromtimestamp(relTimestamp)
            if relDatetime < scmDatetime:
                # skip earlier builds
                continue
            
            relPathMap[relDatetime] = relDirPath            
            
            continue
        
        relPathDateList = relPathMap.keys()
        relPathDateList.sort()        

        # crawl through the release path dates in order, stopping at the
        # first which is >= the scm timestamp        
        for relPathDatetime in relPathDateList:
            if relPathDatetime >= scmDatetime and releasePath is None:
                # choose the first build on or after the merged date
                releasePath = relPathMap.get(relPathDatetime)
            elif relPathDatetime == scmDatetime:
                # choose later builds on the same day as the scm timestamp
                releasePath = relPathMap.get(relPathDatetime)
            elif relPathDatetime > scmDatetime:
                # don't choose subsequent builds after the scm date
                # after we've selected the first one
                break
            continue  
      

    return releasePath
## END findReleasePath


def findVersionNum(releasePath):
    """ reads the first line of the version.txt file which is supposed to be
    in the provided release path """
    versionTxt = None
    versionPath = os.path.join(releasePath, 'version.txt')
    if os.path.exists(versionPath):
        vfh = file(versionPath)
        versionTxt = vfh.readline()
        vfh.close()

        versionTxt = versionTxt.strip()
        if len(versionTxt) == 0:
            versionTxt = None
            pass
        pass
    
    return versionTxt
## END findVersionNum
    

def usage(err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to seach the SCM directory for your branch.\n'
    m += '  Enter you branch name or a subset of the branch to list multiple\n'
    m += ' '
    m += '    walkscm  <branch name> \n'
    m += '      or\n'
    m += '    walkscm -b <branch name>  -s <codeStream> \n'
    m += '      or\n'
    m += '    walkscm -l <qor|build|bundle> -s <codeStream> \n'
    m += '      or\n'
    return m

def usageCCSet(err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '    ccset -s <codeStream> -b <Branchname> -x <Branch Status> \n'
    m += '      \n'
    m += '     Branch Status can only be one of the values below\n'
    for st in ccSetStatusValues():
        m += '       %s\n'%st
    m += '     \n'
    return m


    

def main_CL():
    """ Command line parsing and and defaults method for walkSCM
    """
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-w", "--walk", dest="walk", default="none",  help="Scope of status to walk in the directory.")
    """Updated below line to blast5"""
       
    #parser.add_option("-s", "--cs",   dest="code", default="4",     help="The Code Stream <4|4.0|4.1|4.2|all> to use.")
    parser.add_option("-s", "--cs",   dest="code", default="qf2",     help="The Code Stream <4|4.0|4.1|4.2|all> to use.")
    
    #End change
    parser.add_option("-c", "--crs",  dest="crs",  action="append", help="List of Case Numbers to search for in tree.")
    parser.add_option("-b", "--br",   dest="br",   default="junk",  help="Branch label to search for in the tree.")
    parser.add_option("-t", "--ago",  dest="ago",  default=30.0,    help="Dates ago to look for modified items.")
    parser.add_option("-n", "--num",  dest="num",  default="4000",  help="Max number of items to process")
    parser.add_option("-x", "--parm",  dest="parm",  default="",  help="Parms used by a method")
    parser.add_option("-l", "--list",  dest="list", default="junk", help="List the branch status in the tree")
    parser.add_option("-q", "--quiet", dest='quiet', default="1",   help="Show less info in output")
    parser.add_option("-d", "--debug", dest='debug', action="count",help="The debug level, use multiple to get more.")
    (options, args) = parser.parse_args()
    if options.debug > 1:
        print ' verbose %s\tdebug %s' %(options.quiet, options.debug)
        print ' walk    %s' %options.walk
        print ' stream  %s' %options.code
        print ' CRs     %s' %options.crs
        print ' branch  %s' %options.br
        print ' ago     %s' %options.ago
        print ' num     %s' %options.num
        print ' list    %s' %options.list
        print ' args:   %s' %args
    else:
        options.debug = 0
    crList = []
    stream = str(options.code)
    
    """Modified below lines for blast5 only"""
    validStreams = ('all','active')
    if stream not in validStreams:
        print '%s is not in the list of valid codestreams %s, defaulting to 4' %(stream,validStreams)
        sys.exit()
        stream = ('qf2')
    if stream =='all':
        stream = ('qf2')
    if stream =='active':
        stream = ('qf2')
        
        
    """validStreams = ALL_STREAMS + ('all','active')
    if stream not in validStreams:
        print '%s is not in the list of valid codestreams %s, defaulting to 4' %(stream,validStreams)
        sys.exit()
        stream = DEFAULT_STREAM
    if stream =='all':
        stream = ALL_STREAMS
    if stream =='active':
        stream = ACTIVE_STREAMS"""
        
    ago = float(options.ago)
    
    if options.walk in ['none','fix']:
        if options.walk == 'fix':
            fixBranch(options.br, options=options)
        else:    
            searchForBranch(options.br, options=options)
        
    elif options.crs not in [None,'',' ']:
        print 'doing CR list'
        searchForCRs(options.crs)

    elif options.walk == 'all':
        walkSCM_updateSF(stream, options)    

    elif options.walk == 'reset':
        branch = args[0]
        print 'Resetting the branch %s in %s'%(branch,stream)
        resetBranch(stream, branch, options)

    elif options.walk == 'setCR':
        walkCRs_setStatus(ago, options)

    elif options.walk in ['ccSetStatus','ccSet']:
        status = options.parm
        branch = options.br
        if branch in [None, '', 'junk']:
            print '%s' %usageCCSet()
            sys.exit(1)
        ccSetBranchStatus(branch, stream, status, options)
            
    elif options.walk == 'crtbs':
        fix = False
        if 'fix' in args:
            fix = True
        walkCRs_showTBs(ago, options, fix)

    elif options.walk == 'setMODs':
        setMODStatus()
    
    elif options.list not in ['update']:
        if options.walk == 'all':
            walkSCM_list(stream, options)    
        else:
            print 'doing State listing'
            searchForStep(options.list, stream)

    elif len(args) > 0: 
        branch = args[0]
        searchForBranch(branch, options=options)
    
    else:
        print '%s' %usage()

if __name__ == '__main__':
    """ go juice """
    main_CL()
