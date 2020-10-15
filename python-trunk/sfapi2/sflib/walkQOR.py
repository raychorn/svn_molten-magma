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
from sfTaskBranch import SFTaskBranchTool
from sfConstant import *
import walkFiles
from walkFiles import  *

badInfoList = BAD_INFO_LIST  # from sfConstant

        
class QORFileNode(walkFiles.FileNode):
    """ A subclass of a node that is customised for each specific usage.  Leaves
        that are representing a file contents contain elements that are lines in the
        file.  Leaves that are lines in a file contain words that could be control tokens.
        A leaf will have portable data specific methods that enliven the content.
        Leaf:
           Node.all: the basic node attributes of id, access, views, contents, & state.
           subclass of any method that needs to be different then standard.
    """
    meta_type = 'QORFileNode'
    header = {}

    def load(self, path=None, contents=True):
        """ open the file at path and load file lines in data
        """
        if path is None: path = self.path
        fpath = os.path.normpath(os.path.join(self.rootpath,path))
        if not os.path.isfile(fpath): 
            self.log('load error not a file %s'%(fpath),0,100,tag='QORFileNode')
            return 
        self.name = os.path.basename(path)
        ext = os.path.splitext(self.name)[1]
        ret = ''
        self.log('loading %s ext:%s in %s'%(self.name,ext,fpath),2,0,tag='QORFileNode')
        if ext in ['.rpt','rpt','.gold']:  
            type = 'csv'
            self.log('load found a QOR rpt file %s'%(fpath),2,0,tag='QORFileNode')
            ret = self.loadQORrpt(fpath)
        elif ext in ['.summary','summary']:  
            type = 'csv'
            self.log('load found a Summary QOR file %s'%(fpath),2,0,tag='QORFileNode')
            ret = self.loadQORsumm(fpath)
        elif ext in ['.csv','csv','.xls','xls']:  
            type = 'xls'
            ret = self.loadCSV(fpath)
        else: 
            type = 'text'
            ret = self.loadText(fpath)
        return ret    

    def parseHeaderInfo(self, header=''):
        """ parse the information in the file header into a dictionary
             more 050417.cpu (12 lines)
             # Testcase:   ti_GAP_case1
             # Date:       Sun Apr 17 16:31:08 PDT 2005
             # Build:      mantle version 4.2.71-linux24_x86 (compiled Apr 16 2005 20:44:29)
             # Location:   /magma/scm-release/bundle/blast4_scmbuild_merge1-2005_04_16/linux24_x86/bin/mantle
             # Machine:    Linux opteron0527 2.4.21-143-smp #1 SMP Thu Oct 30 23:48:07 UTC 2003 x86_64 unknown speed=2200.0
             # Workdir:    /vobs/design.ti/design/ti/GAP_case1/scripts
             # Goldfile:   /vobs/seismic/test/design/ti/GAP_case1/scripts/result.gold.linux24_x86
             # Scale:      0.54 (multiple to gold cpu time)
             # User:       linuxqa
             # View:       blast4.2_qor_daily_linux24_x86
             #  
          OR
          ################################################################################################################################
          #
          # 2005.04.21_18.09:08_9
          #
          ################################################################################################################################
         . #Dataset:                                                       dataset/fix_flow/xcompute_tsmc90ghp-od-svt                                            
         . #Test:                                                          test/fix_wire_prototype                                                               
          #Reference Path:                                                /home/rod/qor/results/dataset/fix_flow/xcompute_tsmc90ghp-od-svt/routing_only/2005.04.19_18.29:31
         . #Results Path:                                                  /home/rod/qor/results/dataset/fix_flow/xcompute_tsmc90ghp-od-svt/fix_wire_prototype/2005.04.21_18.09:08
         . #Clearcase View:                                                blast4_fwang_1                                                                        
         . #Mantle Path:                                                   /vobs/magmadt/release                                                                 
         . #Mantle Architecture:                                           linux24_x86                                                                           
         . #Date/Time Submitted:                                           Thu Apr 21 18:09:41 2005                                                              
        """
        result = {}
        self.log('parseHeaderInfo Header IS %s'%(header),1,0)
        if header[0].find('####') != -1:
            head = header[3:]
            self.log('parseHeaderInfo BEQoR Header IS %s'%(head),1,0)
            for line in head:
                field = line[:50]
                field = self.toStr([field])
                val = line[50:]
                val = self.toStr([val])
                self.log('parseHeaderInfo found %s as %s'%(field,val),4,0)
                result[field] = val
        else:
            for line in header:
                tokens = line.split(' ')
                if len(tokens) < 2:
                    self.log('parseHeaderInfo not tokens found in %s of %s'%(line,header),6,0)
                    continue
                field = tokens[1]
                val = self.toStr(tokens[2:])
                result[field] = val
        self.log('parseHeaderInfo returned %s from %s\n'%(result,header),4,0)
        return result

    def toStr(self, vlist):
        """ parse tight string out of a list like:
            from ['', '', '', '', '', '', 'blast5.0_qor_linux24_x86\n']
        """
        ret = ''
        for s in vlist:
            if s not in ['',None,'\n']:
                s = s.strip()
                s = string.replace(s,'\n','')
                s = string.replace(s,'\t','')
                s = string.replace(s,'#','')
                ret = '%s %s'%(ret,s)
                ret = ret.strip()
        return ret
        
        
    def parseDataRows(self, rows, format='qor'):
        """ Parse just the data rows and return list of dicts
        Sample qor input format below
        tag                            item                 sign          new         gold    tolerance        delta
        ------------------------------------------------------------------------------------------------------------
        constrain-hier                 memstep              pass      564.375      554.982       27.750        9.393
        constrain-hier                 cpustep              FAIL        3.505        0.962        0.049        2.543
        constrain-hier                 cpucmd               FAIL        3.505        0.962        0.049        2.543

        Sample teamqor input format below:
        Stage                     Check     Test  Reference  Delta  Tolerance  Result  Detail
        ---------------------------------------------------------------------------------  
        default: default          msgcount  580    2563      -1983  +/- 128    FAIL   
        fix_wire: default         msgcount   25      16          9  +/- 0      FAIL   
        fix_wire: fix-wire-start  msgcount    7       7          0  +/- 0      Pass  
        
        """
        result = []
        header_row = 0
        for line in rows:
            if line.find('----') != -1:
                break
            header_row += 1
        if header_row == 0:
            msg = 'parseDataRows could not find header break in %s'%rows
            print msg
            sys.exit(0)
        tag_row = header_row -1
        data_row = header_row +1
        fields = rows[tag_row]
        if len(fields) < 5: 
            msg = 'parseDataRows found wrong tag row %s %s'%(tag_row,fields)
            print msg
            sys.exit(0)
        fields = fields.split()
        self.log('parseDataRows tag_row:%s is %s'%(tag_row,rows[tag_row]),5,0)
        self.log('parseDataRows tag_row:%s fields are %s'%(tag_row,fields),3,0)
        for line in rows[data_row:]:
            rd = {}
            if format == 'qor':
                values = line.split()
                fn = 0
            else: # for new teamtest format
                rd[field[0]] = line[:27].strip()
                fn = 1
                values = line[28:].split()
            if len(values) < 1: continue
            if values[0] in ['#']: continue
            for val in values:
                if len(fields) > fn:
                    rd[fields[fn]] = val
                    fn += 1
            result.append(rd)
            
        self.log('parseDataRows %s rows '%(len(result)),3,0)
        self.log('parseDataRows like %s '%(result[:10]),5,0)
        return result
        
    def loadQORrpt(self, fpath):
        """ load without csv module """
        if os.path.isfile(fpath):
            f_stat = os.stat(fpath)
            self.mdate = f_stat[8]
            self.cdate = f_stat[9]
            fp = open(fpath)
            self.filelines = fp.readlines()
            fp.close()
            header = []
            header_row = 0
            for line in self.filelines:
                if line.find('-----') != -1:
                    break
                header_row += 1
            if header_row == 0:
                 msg = 'parseDataRows could not find header break "------" in %s'%fpath
                 print msg
                 sys.exit(0)
            tag_row = header_row -1
            data_row = header_row +1
            header = self.filelines[:tag_row]
            if len(header) > 5:
                for line in self.filelines[:11]:
                    if line[:3].find('#') != -1:
                        header.append(line)
                    else:
                        break  # got all the header lines
            self.log('loadQORrpt after header %s'%(header),4,0)
            header_dict = self.parseHeaderInfo(header)
            self.header = header_dict
            self.log('loadQORrpt HEADER dict:%s'%(self.header),2,0)
            ll = self.parseDataRows(self.filelines)
            self.filedata = ll
            ln = len(ll)
            if ln > 2:
                self.log('loadQORrpt %s processed lines'%(ln),1,0,tag='QORFileNode')
                self.log('loadQORrpt lines like %s'%(ll[int(ln/2)]),3,0,tag='QORFileNode')
            else:
                self.log('loadQORrpt NO processed lines in %s '%(fpath),1,100,tag='QORFileNode')
            return ll
        self.log('loadQORrpt Error could not find %s' %(fpath),0,0)
            

    def loadQORsumm(self, fpath):
        """ load just as CSV """
        if os.path.isfile(fpath):
            f_stat = os.stat(fpath)
            self.mdate = f_stat[8]
            self.cdate = f_stat[9]
            fp = open(fpath)
            self.filelines = fp.readlines()
            header = []
            for line in self.filelines[:11]:
                if line[:3].find('#') != -1:
                    header.append(line)
                else:
                    break  # got all the header lines
            #self.log('loadQORrpt after header %s'%(self.filelines),0,0)
            header_dict = self.parseHeaderInfo(header)
            self.header = header_dict
            self.log('loadQORrpt dict:%s'%(self.header),4,0)
            # should I seek(0) the file? or create proxy file?
            cvs_start = 0
            for ln in range(1,len(self.filelines)):
                linestart = self.filelines[ln][:2]
                if linestart in ['\n','','\r\n','#\n','# ','# \n']:
                    continue
                if ln > 6:
                    cvs_start = ln
                    break
            self.log('loadQORsumm start of CVS proxy is: %s'%(self.filelines[cvs_start-1-cvs_start+2]),0,0)        
            fileProxy = StringIO.StringIO()
            for line in self.filelines[cvs_start:]:
                fileProxy.write(line)
            fileProxy.seek(0,0)
            #fp.seek(0)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(self.filelines[14],delimiters=' ')
            csv.register_dialect("qor", dialect)
            print 'Dialects are: %s %s'%(csv.list_dialects(),dialect)
            csvreader = csv.reader(fileProxy)  #, dialect='qor'
            ll = []
            for row in csvreader:
                ll.append(row)
            self.filedata = ll
            fp.close()
            ln = len(ll)
            if ln > 2:
                self.log('loadQORrpt %s CSV lines like \n %s'%(ln,ll[int(ln/2)]),1,0,tag='QORFileNode')
            else:
                self.log('loadQORrpt NO CSV lines in %s '%(fpath),1,100,tag='QORFileNode')
            return ll
        self.log('loadQORrpt Error could not find %s' %(fpath),0,0)
            

    def loadCSV(self, fpath):
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
            self.log('loadCSV %s CSV lines like \n %s'%(ln,ll[int(ln/2)]),2,0,tag='QORFileNode')
            return
        self.log('loadCSV Error could not find %s' %(fpath),0,0)

    def loadText(self, fpath):
        """ """
        if os.path.isfile(fpath):
            f_stat = os.stat(fpath)
            self.adate = f_stat[7]
            self.mdate = f_stat[8]
            self.cdate = f_stat[9]
            if 1:
                fp = open(fpath)
                self.filedata = fp.readlines()
                fp.close()
                self.log('loadText Loaded %s lines from %s'%(len(self.data),fpath),2,0,tag='QORFileNode')
            else:
                self.data = ''
                self.log('loadText Loaded %s lines from %s'%(len(self.data),fpath),2,0,tag='QORFileNode')
            return         
        self.log('loadText Error could not find %s' %(fpath),2,0,tag='QORFileNode')
        
        
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
class SFTool(SFTaskBranchTool):
    """ handle to a sForce connection tool """
        
#############################################################################################################
#   nodeTool with Link to sforceBase 
#############################################################################################################
class QORnodeTool(walkFiles.nodeTool):
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
    meta_type = 'QORNodeTool'

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

        
    def getDesignRun(self, info={}, entity='Design_Run__c'):
        """ use header info from qor file to find right Design Run
            return DR id or user info 
        """
        if type(info) not in [type({})]:
            self.log('get%s info not dictionary %s'%(entity,info),0,0)
            return {'id':'','msg':'Error provide query dictionary', 'data':''}
        return self.getSF(info,entity)

    def getQoRTag(self, info={}, entity='QoR_Tag__c'):
        """ use info to find right entity info or empty  """
        if type(info) not in [type({})]:
            self.log('get%s info not dictionary %s'%(entity,info),0,0)
            return {'id':'','msg':'Error provide query dictionary', 'data':''}
        return self.getSF(info,entity)

    def getDataset(self, info={}, entity='Dataset__c'):
        """ use info to find right entity info or empty  """
        if type(info) not in [type({})]:
            self.log('get%s info not dictionary %s'%(entity,info),0,0)
            return {'id':'','msg':'Error provide query dictionary', 'data':''}
        return self.getSF(info,entity)

    def getQoR_Test(self, info={}, entity='QoR_Test__c'):
        """ use info to find right entity info or empty  """
        if type(info) not in [type({})]:
            self.log('get%s info not dictionary %s'%(entity,info),0,0)
            return {'id':'','msg':'Error provide query dictionary', 'data':''}
        return self.getSF(info,entity)

    def getQoR_Test_Runset(self, info={}, entity='QoR_Test_Runset__c'):
        """ use info to find right entity info or empty  """
        if type(info) not in [type({})]:
            self.log('get%s info not dictionary %s'%(entity,info),0,0)
            return {'id':'','msg':'Error provide query dictionary', 'data':''}
        return self.getSF(info,entity)

        
    def getSF(self, info={}, entity=''):
        """ use query info to find right Entity
            return Entity id, data, and message 
        """
        result = {'id':'','msg':'', 'data':''}
        if type(info) != type({}):
            self.log('get%s info not dictionary %s'%(entity,info),1,0)
            return result
        if entity in [None,'']:
            self.log('get%s unknown entity provided info:%s'%(entity,info),1,0)
            return result
        where = []
        for k,v in info.items():
            if k == entity:
                clause = ['Id','=',v]
            else:    
                clause = [k,'=',v]
            if len(where) > 0:
                where.append('and')
            where.append(clause)
        self.log('get%s using where of %s'%(entity,where),4,0)    
        ids = self.sfb.query(entity, where=where) 
        if ids in badInfoList:
            result['msg'] = 'No %s Found'%entity
        else:
            data = ids[0]
            result['id'] = data.get('Id','')
            result['data'] = data
            result['msg'] = 'Found %s %s'%(len(ids),entity)
            if len(ids) >1: 
                self.log('getSF found multiple %s Where %s using %s'%(entity,where,data),2,0)
        return result

    def setSF(self, data={}, entity=''):
        """ use create to add info to right Entity
            return Entity id, data, and message 
        """
        result = {'id':'','msg':'', 'data':''}
        if type(data) != type({}):
            self.log('set%s info not dictionary %s'%(entity,data),1,0)
            return result
        if entity in [None,'']:
            self.log('set%s unknown entity provided info:%s'%(entity,data),1,0)
            return result
        self.log('set%s using %s'%(entity,data),6,0)    
        ids = self.sfb.create(entity, data) 
        if ids in badInfoList:
            result['msg'] = 'Error Create failure for %s '%entity
        else:
            result['id'] = ids[0]
            result['data'] = data
            result['msg'] = 'Created %s %s'%(len(ids),entity)
            if len(ids) >1: 
                self.log('setSF found multiple %s using %s'%(entity,data),2,0)
        return result

        

    def setDesignRunFromHeader(self, header={}, tcId='', drname=''):
        """ Take a dictionary from a file load to update a DR 
          {'Location:': '/magma/scm-release/bundle/blast5_scmbuild_merge1-2005_04_19/linux24_x86/bin/mantle'
          , 'User:': 'linuxqa'
          , 'Date:': 'Tue Apr 19 15:11:24 PDT 2005'
          , 'Build:': 'mantle version 2005.03.a.26-linux24_x86 (compiled Apr 19 2005 13:48:13)'
          , 'Scale:': '0.48 (multiple to gold cpu time)'
          , 'Goldfile:': '/vobs/seismic/test/design/broadcom/mpis_core/scripts/result.gold.linux24_x86'
          , 'View:': 'blast5.0_qor_linux24_x86'
          , 'Machine:': 'Linux opteron0509.moltenmagma.com 2.4.21-20.ELsmp #1 SMP Wed Aug 18 20:34:58 EDT 2004 x86_64 x86_64 x86_64 GNU/Linux speed=2200.0'
          , 'Testcase:': 'broadcom_mpis_core'
          , 'Workdir:': '/vobs/design.broadcom/design/broadcom/mpis_core/scripts'}
          OR
          ################################################################################################################################
          #
          # 2005.04.21_18.09:08_9
          #
          ################################################################################################################################
         . #Dataset:                                                       dataset/fix_flow/xcompute_tsmc90ghp-od-svt                                            
         . #Test:                                                          test/fix_wire_prototype                                                               
          #Reference Path:                                                /home/rod/qor/results/dataset/fix_flow/xcompute_tsmc90ghp-od-svt/routing_only/2005.04.19_18.29:31
         . #Results Path:                                                  /home/rod/qor/results/dataset/fix_flow/xcompute_tsmc90ghp-od-svt/fix_wire_prototype/2005.04.21_18.09:08
         . #Clearcase View:                                                blast4_fwang_1                                                                        
         . #Mantle Path:                                                   /vobs/magmadt/release                                                                 
         . #Mantle Architecture:                                           linux24_x86                                                                           
         . #Date/Time Submitted:                                           Thu Apr 21 18:09:41 2005                                                              
          into sf entity Design_Run__c with:
            Clearcase_View__c, CPU_Scale_to_Gold__c
          , Mantle_Path__c, Mantle_Type__c, Mantle_Version__c
          , Run_Start__c, Run_Status__c, Run_Time__c, Run_Complete__c, Peak_Memory_GB__c
          , Workstation_Name__c, Workstation_Speed__c, Workstation_Type__c    
          , Tech_Campaign__c, QoR_Test__c, Design__c, Dataset__c     
        """
        time_format1 = '%a %b %d %X %Z %Y'
        time_format2 = '%a %b %d %X %Y'
        data = {}
        data['OwnerId'] = '00530000000cCy5'
        result = {'id':'','msg':'','data':{}}
        if type(header) != type({}):
            self.log('setDRfromFile header not dictionary %s'%header,0,0)
            return result
        tcName = drname
        lookup = ''
        runset_data = {}
        add_runset = False
        for k,v in header.items():
            if k in [None,'']: continue
            if k[0] == '#': k= k[1:] # strip off #
            if k[-1] == ':': k= k[:-1] # strip off :
            if k in ['Testcase','Testcase:']:  
                data['Testcase_Name__c'] = v
                tcName = v
            elif k in ['View','View:','Clearcase View','Clearcase View:']:        
                data['Clearcase_View__c'] = v
                runset_data['Clearcase_View__c'] = v
                
            elif k in ['Date/Time Submitted']:      # backendQoR oriented  
                dt = time.strptime(v,time_format2)
                self.log('setDRfromHead Date/Time: %s became %s'%(v,dt),2,0)
                data['Run_Start__c'] = time.mktime(dt)
                
            elif k in ['Mantle Architecture']:        
                data['Workstation_Type__c'] = v
                
            elif k in ['Workstation Name','Workstation Name:']:        
                data['Workstation_Name__c'] = v
                
            elif k in ['Peak Memory (GByte)','Peak Memory (GByte):']:        
                data['Peak_Memory_GB__c'] = float(v)
                
            elif k in ['Runtime (Hours)','Runtime (Hours):']:        
                data['Run_Time__c'] = float(v)
                
            elif k in ['Job Status','Job Status:']:        
                data['Run_Status__c'] = v
                
            elif k in ['Results Path','Results Path:']:        
                data['Results_Path__c'] = v
            elif k in ['Mantle Path','Mantle Path:']:        
                data['Mantle_Path__c'] = v
                runset_data['Mantle_Path__c'] = v
                
            elif k in ['Runset','Runset:']:      
                ret = self.getQoR_Test_Runset({'Name':v},'QoR_Test_Runset__c')
                id = ret.get('id','')
                runset_data['Name'] = v
                self.log('Runset found:%s using:%s with %s'%(id,v,ret),2,0)
                if id in [None,'']:
                    add_runset = True
                data['QoR_Test_Runset__c'] = id

            elif k in ['Dataset']:        
                if v[:8] == 'dataset/': v=v[8:]
                info = {'Name':v}
                ret = self.getDataset(info,'Dataset__c')
                id = ret.get('id','')
                data['Dataset__c'] = id
                
            elif k in ['Test']:        
                if v[:5] == 'test/': v=v[5:]
                info = {'Name':v}
                ret = self.getQoR_Test(info,'QoR_Test__c')
                id = ret.get('id','')
                data['QoR_Test__c'] = id
               
            elif k in ['Scale','Scale:']:           # scmQoR oriented      
                snum = v.split()[0]
                num = float(snum)
                self.log('DRLoadfromHeader s:%s n:%s'%(snum,num),6,0)
                data['CPU_Scale_to_Gold__c'] = num
            elif k in ['User','User:']:  
                if v in ['linuxqa']:
                    uid = '00530000000cCy5'
                else:
                    uinfo = self.sfb.getUserByAlias(v)
                    uid = uinfo.get('Id','00530000000cCy5')
                data['OwnerId'] = uid
                
            elif k in ['Date','Date:']:      
                dt = time.strptime(v,time_format1)
                self.log('setDRfromHead Date: %s became %s'%(v,dt),2,0)
                data['Run_Complete__c'] = time.mktime(dt)
                
            elif k in ['Location','Location:']:        
                data['Mantle_Path__c'] = v
            elif k in ['Workdir','Workdir:']:        
                data['Work_Path__c'] = v
               
            elif k in ['Build','Build:']:      
                data['Mantle_Version__c'] = v
                lookup = v.split()[2]
                data['Lookup__c'] = lookup

            elif k in ['Machine','Machine:']:
                # 'Linux opteron0509.moltenmagma.com 2.4.21-20.ELsmp #1 SMP Wed Aug 18 20:34:58 EDT 2004 x86_64 x86_64 x86_64 GNU/Linux speed=2200.0'
                vl = v.split()
                data['Workstation_Name__c'] = vl[1]
                try:  data['Workstation_Speed__c'] = float(vl[-1].split('=')[1])
                except: 
                    self.log('setDRfromHead %s value of %s not converted to float'%(k,v),1,0)
                data['Workstation_Type__c'] = '%s %s %s %s'%(vl[0],vl[2],vl[4],vl[-3])
                data['Mantle_Version__c']

        # add a QoR Runset if needed        
        if add_runset == True:
            ret = self.setSF(runset_data,'QoR_Test_Runset__c')
            id = ret.get('id','')
            self.log('setDRfromHead Runset:%s  data:%s'%(id,ret),2,0)
            data['QoR_Test_Runset__c'] = id
            
        data['Tech_Campaign__c'] = tcId
        # now need DR id and Tech_Campaign
        if lookup not in [None,'']:   # scmQoR oriented 
            info = {'Lookup__c':lookup,'Tech_Campaign__c':tcId}
        else:                         # backend QoR oriented 
            data['Testcase_Name__c'] = drname
            info = {'Testcase_Name__c':drname,'Tech_Campaign__c':tcId}
            lookup = drname
        # now need DR id
        ret = self.getDesignRun(info, entity='Design_Run__c')
        drId = ret.get('id','')
        updateDR = True
        if drId in [None,'']:
            self.log('setDRfromFile Creating Design_Run__c with data:%s'%data,1,0)
            ret = self.sfb.create('Design_Run__c', data)
            drId = ret[0]
            updateDR = False
            
        if updateDR:
            data['Id'] = drId
            self.log('setDRfromFile Updating Design_Run__c with data:%s'%data,1,0)
            ret = self.sfb.update('Design_Run__c', data)
        if ret in badInfoList:
            result['msg'] = 'Error: %s No Design Run Found'%ret
            self.log('setDRfromFile ERROR %s'%(self.sfb.lastError),0,0)
            self.log('setDRfromFile sfData:%s'%data,0,0)
            self.log('setDRfromFile Results %s'%(self.sfb.lastResult),0,0)
            #tf = file('soap.trace', 'w+')
            #self.sfdc.binding.trace = tf
        else:
            if drId in [None,'']:
                result['msg'] = 'Created %s Design Run for %s'%(len(ret),lookup)
            else:
                result['msg'] = 'Updated %s Design Run from %s'%(len(ret),lookup)
            result['id'] = ret[0]
            result['data'] = data
        return result

    qorTagList = []        
        
    def setQoRTagFromRow(self, row={}, drId=''):
        """ Take a dictionary from a file load to update a QoRTag Entity
          {'gold': 'x', 'sign': 'xxxx', 'item': 'fixnetlistcpucmdtotal'
          , 'tag': 'final', 'delta': 'x', 'new': '2.047', 'tolerance': 'x'}
          into sf entity QoR_Tag__c with:
            Check__c, Design_Run__c, Difference__c, Gold__c, Name
          , New__c, Sequence__c, Status__c, Tag__c, Threshold__c   
        """
        data = {}
        result = {'id':'','msg':'','data':{}}
        if type(row) != type({}):
            self.log('setQoRTagFromRow row not dictionary %s'%row,0,0)
            return result
        if drId in [None,'']:
            self.log('setQoRTagFromRow need DesignRun id for %s'%row,0,0)
            return result
            
        data['Design_Run__c'] = drId
        search = {'Design_Run__c':drId}
        for k,v in row.items():
            if k in ['tag','Stage']:            
                data['Tag__c'] = v
                search['Tag__c'] = v
                if not v in self.qorTagList:
                    self.qorTagList.append(v)
                seq = self.qorTagList.index(v)
                data['Sequence__c'] = seq
                
            elif k in ['item','Check']:         
                data['Check__c'] = v
                search['Check__c'] = v
                
            elif k in ['gold','Reference']:
                try:  data['Gold__c'] = float(v)
                except: 
                    self.log('setQoRTagFromRow %s value of %s not converted to float'%(k,v),4,0)
                    
            elif k in ['new','test','Test','New']:           
                try:  data['New__c'] = float(v)
                except: 
                    self.log('setQoRTagFromRow %s value of %s not converted to float'%(k,v),4,0)
                
            elif k in ['tolerance','Tolerance']:
                try: data['Threshold__c'] = float(v)
                except: 
                    self.log('setQoRTagFromRow %s value of %s not converted to float'%(k,v),4,0)
                
            elif k in ['delta','Delta']:        
                try:   data['Difference__c'] = float(v)
                except: 
                    self.log('setQoRTagFromRow %s value of %s not converted to float'%(k,v),4,0)
                
            elif k in ['sign','Result']:        
                data['Status__c'] = v
        
        
        # try to find existing record using tag & check        
        ret = self.getQoRTag(info=search, entity='QoR_Tag__c')
        qtId = ret.get('id','')
        if qtId in [None,'']:
            ret = self.sfb.create('QoR_Tag__c', data)
        else:
            data['Id'] = qtId
            ret = self.sfb.update('QoR_Tag__c', data)
        if ret in badInfoList:
            result['msg'] = 'Error: %s No QoR Tags Found'%ret
            self.log('setQoRTagFromRow ERROR %s'%(self.sfb.lastError),0,0)
            self.log('setQoRTagFromRow sfData:%s'%data,0,0)
            self.log('setQoRTagFromRow Results %s'%(self.sfb.lastResult),0,0)
            tf = file('soap.trace', 'w+')
            self.sfb.sfdc.binding.trace = tf
        else:
            if qtId in [None,'']:
                result['msg'] = 'Created %s QoR Tags'%len(ret)
            else:
                result['msg'] = 'Updated %s QoR Tags'%len(ret)
            result['id'] = ret[0]
            result['data'] = data
        return result

    ############################################################################
    #  Used as target for walker
    #    v1.0 not used need to process QoRs
    ############################################################################
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
            node = QORFileNode(path=spath, data=None, info=info, tool=self)
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



#############################################################################################################
#   A directory walker that compares the production directory to a temp copy to find difference
#   and trigger change events to drive an updater.
#############################################################################################################
class walkQORDir(walkFiles.walkdir):
    """ walk a QOR directory tree and compare to a temp version of the same tree
        and generate processing events on each directory
    """

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
def loadQORDir(options):
    """ load all QorFile in dirQOR test file set"""
    result = ''
    db = int(options.debug)
    tcId = options.tcId
    startTime = time.time()
    tool = None
    tool = QORnodeTool(logname='qor.load1',options=options, db=db)
    tool.sfb.getConnectInfo(version, startTime)
    path = os.getcwd()
    passed_path = options.file
    if passed_path not in [None,'']:
        path = passed_path
    processed_path = os.path.join(path,'processed')
    if not os.path.isdir(processed_path):
        os.mkdir(processed_path)
    fname = os.path.basename(passed_path)
    file_list = os.listdir(path)
    num = 1
    max = int(options.num)
    #max = 300
    for fname in file_list:
        if num > max: break
        num +=1
        ext = os.path.splitext(fname)[1]
        if ext in ['.rpt','rpt']:
            fpath = os.path.normpath(os.path.join(path,fname))
            ppath = os.path.normpath(os.path.join(processed_path,fname))
            ret = loadQORFromFile(fpath,tool,db,tcId)
            print '##############################'
            if ret == 'OK':
                print '# Completed %s'%fname
                os.rename(fpath,ppath)
            else:
                print '# Failed parsing %s'%fname
            print '##############################'
            
            
            
def loadQOR(options):
    """ load a single QOR test file set"""
    result = ''
    db = int(options.debug)
    tcId = options.tcId
    startTime = time.time()
    tool = None
    tool = QORnodeTool(logname='qor.load1',options=options, db=db)
    tool.sfb.getConnectInfo(version, startTime)
    
    passed_path = options.file
    path = passed_path
    fname = os.path.basename(passed_path)
    if fname in [None,'']:
        print ' Please provide a filename with the -f switch'
        sys.exit(0)
    if passed_path == fname:
        cur_path = os.getcwd()
        path = os.path.normpath(os.path.join(cur_path,fname))
    loadQORFromFile(path,tool,db,tcId)    
        
        
        
def loadQORFromFile(path,tool,db,tcId='a0Q300000000Hfg'):
    """ load one QoR file """
    print 'Loading QOR info from %s'%path
    node = QORFileNode(path=path, data=None, info='', tool=tool, db=db)
    node.load(contents=False)      # sets mdate
    filedata = node.filedata
    filelines = node.filelines
    data = node.data
    header = node.header 
    fname = os.path.basename(path)
    fname = os.path.splitext(fname)[0]
    print 'Loading QOR Rundata %s into Tech Campaign https://na1.salesforce.com/%s'%(fname,tcId)
    #print 'Header is: %s\n'%header
    ret = tool.setDesignRunFromHeader(header, tcId=tcId, drname=fname) #a0Q300000000Hfg
    if ret.get('msg','').find('Error') != -1:
        print 'Error from setDesignRunFromHeader %s'%ret
        return 'Error'
    print '%s \n'%ret.get('msg','')
    
    drId = ret.get('id','')
    rownum = len(filedata)
    tool.qorTagList = []  # reset sequence number
    #print '\nFileData is: %s rows like:'%(len(filedata))
    #print filedata[2-4]
    print 'Now updating %s rows into https://na1.salesforce.com/%s\n'%(rownum,drId)
    maxrows = rownum+1
    i = 0
    print '%8s %2s %32s %12s %8s %10s %10s'\
          %('action','#','Tag','Check','result','Value','Difference')
    for line in filedata:
        i += 1
        if i >= maxrows: break 
        ret = tool.setQoRTagFromRow(row=line, drId=drId)
        data = ret.get('data',{})
        action = 'Updated '
        if ret.get('msg','').find('Created') != -1:
            action = 'Added '
        if ret.get('msg','').find('Error') != -1:
            print ret
            return 'Error'
        else:
            #print data
            print '%8s %2s %32s %16s %8s %14s %14s'%(action,data.get('Sequence__c','')\
                          ,data.get('Tag__c',''),data.get('Check__c','')\
                          ,data.get('Status__c',''),data.get('New__c','')\
                          ,data.get('Difference__c','')) 
    print 'Updated %s rows into https://na1.salesforce.com/%s\n'%(rownum,drId)
    return 'OK'       
    
    
    
            
def walk_list(options):
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
    walkQORDir = walkQORDir(tool.rootpath, tool.tmp_root, tool, ignore)
    tool.sfb.dlog.info('SF Connect %s secs and Compare paths took %s secs' %(sfTime,(time.time()-ts1)))
    print '______________________________________________________________'
    walkQORDir.walk_breadth_dir(options) 
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
    m += '  Default usage is to load a specific .rpt file in current working directory.\n'
    m += '    use the -t option to indicate the sf.com ID of the parent Tech Campaign\n'
    m += '    the -c dir switch will load all rpt file in the current working directory. \n'
    m += ' \n'
    m += '    qor2sf -c load -f <filename-in-cwd> -t a0Q3000000000K1 \n'
    m += '        NOTE: the filename must have an extension of .rpt or .gold\n'
    m += '      or\n'
    m += '    qor2sf -c dir  -t a0Q3000000000K1  \n'
    m += '        NOTE: only filename with an extension of .rpt or .gold will be processed\n'
    m += '      '
    return m

def main_CL():
    """ Command line parsing and and defaults method for walk
    """
    parser = OptionParser(usage=usage(), version='1.0')
    parser.add_option("-c", "--cmd", dest="cmd",    default="unknown", help="What command to run.")
    parser.add_option("-w", "--walk", dest="walk",  default="none",  help="Scope of status to walk in the directory.")
    parser.add_option("-s", "--cs",   dest="code",  default="4",     help="The Code version <4|4.0|4.1|4.2|all> to use.")
    parser.add_option("-t", "--tcId",  dest="tcId", default="a0Q300000000Hj9",    help="Tech Campaign ID in SalesForce")
    parser.add_option("-n", "--num",  dest="num",   default="4000",  help="Max number of items to process")
    parser.add_option("-x", "--parm",  dest="parm", default="",    help="Parms used by a method")
    parser.add_option("-f", "--file",  dest="file", default="",     help="path to the file to load, current dir if just a filename")
    parser.add_option("-q", "--quiet", dest='quiet',default="1",   help="Show less info in output")
    parser.add_option("-d", "--debug", dest='debug',action="count",help="The debug level, use multiple to get more.")
    (options, args) = parser.parse_args()
    if options.debug > 2:
        print ' verbose %s\tdebug %s' %(options.quiet, options.debug)
        print ' command %s\twalk  %s' %(options.cmd, options.walk)
        print ' version  %s' %options.code
        print ' tcId     %s' %options.tcId
        print ' num     %s' %options.num
        print ' file    %s' %options.file
        print ' args:   %s' %args
    else:
        options.debug = 0
    crList = []
    version = str(options.code)
    
    if options.cmd in ['load']:
        loadQOR(options=options)
    elif options.cmd in ['dir']:
        loadQORDir(options=options)
    elif options.cmd in ['rpt']:
        walk_list(options=options)
    else:
        print '%s' %usage()

if __name__ == '__main__':
    """ go juice """
    main_CL()
