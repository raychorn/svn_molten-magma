""" Specific to Task Branch customer object
    - Task Branch (TB) is a sForce representation of a code branch in Clearcase
    - TB is displayed as a container object with a list of:
    -
           Chip Vanek, May 16th, 2005
"""
# Subversion properties
#
# $LastChangedDate: 2006-06-16 16:46:16 -0700 (Fri, 16 Jun 2006) $
# $Author: ramya $
# $Revision: 47 $
# $HeadURL: http://capps.moltenmagma.com/svn/sfsrc/trunk/sfapi2/sflib/sfTaskBranchList.py $
# $Id: sfTaskBranchList.py 47 2006-06-16 23:46:16Z ramya $
import sys, time, os, datetime
import grp, pprint
import StringIO, getopt
import copy, re
import pprint
import traceback
from types import ListType, TupleType, DictType, DictionaryType
from optparse import OptionParser
from sfMagma import *
from sfUser import SFUserTool
from sfNote import *
from sfCr import *
from sfConstant import *
from sfUtil import cronLock, uniq
from sfTaskBranch import SFTaskBranch
from sop import ccBranches, opBranches, sfBranches, sfEntities, SFEntitiesMixin, SFUtilityMixin, SFTestMixin, BasicCacheMixin
import tokenFile
from emailTransMap import emailTransMap

class SFTaskBranch2(SFTaskBranch):
    """ This is a local override of the SFTaskBranch object
    """

    def __init__(self, entity=None, data={}, action=None, sfTool=None, debug=0):
        """  If an active tool object is not passed in then a connection is created.   """
        if entity is None: entity = 'Task_Branch__c'
        SFEntityBase.__init__(self, entity, data=data, action=action, sfTool=sfTool, debug=debug)

    ##################################################################################################
    #  General Task Branch methods: load, setStatus, check, updateSF
    ##################################################################################################
    def loadBranch(self, branch, stream, team='', label=''):
        """
        load elements from existing Task Branch Object
        """
        self.branch = branch
        self.stream = stream

        where = [['Branch__c','like',branch], 'and',
                 ['Code_Stream__c','=',stream]]

        tbData = self.getSFDataCommon(where, show=False)
        tbInfo = tbData.get('Task_Branch__c')
        if tbInfo in [{},'fail']:
            if not stream[:5] in ['blast','Blast']:
                where = [['Branch__c','like',branch], 'and',
                        ['Code_Stream__c','=','blast%s'%stream]]
                tbData = self.getSFDataCommon(where, show=False)

        status = tbInfo.get('Branch_Status__c','') #?? Right?
        numCLs = len(tbData.get('Branch_CR_Link__c'))
        numBAs = len(tbData.get('Branch_Approval__c'))
        numBTLs = len(tbData.get('Branch_Team_Link__c',[]))
        info = [numCLs,numBAs,status,branch,stream,numBTLs]
        return info

    def loadBranchById(self, id):
        """
        load elements from existing Task Branch Object
        given a task branch Id
        """
        where = [['Id','=', id]]
        tbData = self.getSFDataCommon(where, show=False)

        # tbData = self.getSFDataById(id, show=False)

        taskBr = tbData.get('Task_Branch__c')
        branch = taskBr.get('Branch__c','')
        stream = taskBr.get('Code_Stream__c','')
        status = taskBr.get('Branch_Status__c','')
        numCLs = len(tbData.get('Branch_CR_Link__c'))
        numBAs = len(tbData.get('Branch_Approval__c'))
        numBTLs = len(tbData.get('Branch_Team_Link__c',[]))

        self.branch = branch
        self.stream = stream
        info = [numCLs,numBAs,status,branch,stream,numBTLs]
        return info

    def refresh(self):
        info = self.loadBranch(self.branch, self.stream)
        return info
    ## END refresh


    def getSFData(self, branchLabel, stream, show=True):
        """ """
        where = [['Branch__c','like',branchLabel]
                ,'and',['Code_Stream__c','=',stream]]

        res = self.getSFDataCommon(where, show=show)
        return res

    def getSFDataById(self, id, show=True):
        """ """
        where = [['Id','=', id]]
        res = self.getSFDataCommon(where, show=show)
        return res


    def getSFDataCommon(self, where, show=True):
        """
        one call to get all new Task branch object related to a
        ClearCase branch will set data as a list of entity-data pairs
        [('entity', {data})] return this data structure or {}
        """
        res = {'Task_Branch__c':{}, 'Branch_Approval__c':[], 'Branch_CR_Link__c':[], 'Branch_Team_Link__c':[]}
        self.setData(res, reset=True)

        queryList = self.sfb.query('Task_Branch__c', where=where, sc='fields')

        if queryList in self.badInfoList:
            if self.debug>1:
                print '    NO Task Branch Found for %s' \
                      %pprint.pformat(where)
            return res

        if len(queryList) > 1:
            self.sfb.setLog('WARNING: There should be only ONE TB object found by %s' \
                  %pprint.pformat(where),'warn')

        numCL = 0
        numBA = 0
        tbData = queryList[0]
        #for tbData in queryList:
        # CV Oct 14, 2004 We only want one Branch loaded, the loop was causing some walkSF problems
        if 1:
            if type(tbData) not in dictTypes:
                return 'Error: getSFData for %s Query returned %s' %(where, tbData)
            tbId = tbData.get('Id','')
            res['Task_Branch__c'] = tbData
            if tbId not in [None,'']:
                branch = tbData.get('Branch__c','')
                stream = tbData.get('Code_Stream__c','')

                where = [['Task_Branch__c','=',tbId]]

                approvals = self.sfb.query('Branch_Approval__c', where=where)   # should limit field with sc='Branch_Approval'
                if approvals not in self.badInfoList:
                    res['Branch_Approval__c'] = approvals
                    if self.debug>0: self.sfb.setLog('->%25s ba:%s'%(branch,approvals),'info3')
                    numBA = len(approvals)

                cr_links  = self.sfb.query('Branch_CR_Link__c', where=where)    # should limit for performance with , sc='Branch_CR_Link'
                if cr_links not in self.badInfoList:
                    res['Branch_CR_Link__c'] = cr_links
                    if self.debug>0: self.sfb.setLog('->%25s cl:%s'%(branch,cr_links),'info3')
                    numCL = len(cr_links)

                team_links = self.sfb.query('Branch_Team_Link__c', where=where)
                if team_links not in self.badInfoList:
                    res['Branch_Team_Link__c'] = team_links
                    if self.debug>0: self.sfb.setLog('->%25s mm:%s'%(branch,team_links),'info3')
                #if self.debug >2: pprint.pprint(res)

            else:
                if self.debug>=2: print '    NO Task Branch Found for query %s ' %where
                return res
        self.setData(res)
        self.sfb.setLog('getSFData %25s cl:%s ba:%s'%(branch,numCL,numBA),'info2')
        self.loadFromSF = True
        if show: self.showData(res)

        return res


    def showBranch(self):
        tbInfo = self.getData('Task_Branch__c')
        baList = self.getData('Branch_Approval__c')
        crLinkList = self.getData('Branch_CR_Link__c')

        crIdList = []
        for crLink in crLinkList:
            crIdList.append(crLink.get('Case__c'))
            continue

        # fetch the CRs.
        caseFields = ('Id','Subject', 'Type', 'CaseNumber', 'Status',
                      'Component__c')
        crList = self.sfb.retrieve(crIdList, 'Case', fieldList=caseFields)

        ret = "\n"

        ret += 'Branch: %s  \tStream: %s\n'%(tbInfo.get('Name'),tbInfo.get('Code_Stream__c'))
        ret += '  Branch Status: %s\n'%tbInfo.get('Branch_Status__c',
                                                  'No Status!')
        ret += '  Priority:      %-10s  Num CRs:        %s\n'%(tbInfo.get('Priority__c'),int(float(tbInfo.get('Num_CRs__c','0').strip())))
        ret += '  High Risk:     %-10s  Command Change: %-3s  Volcano Change: %s\n'%(tbInfo.get('High_Risk__c'),tbInfo.get('Command_Change__c'),tbInfo.get('Volcano_Change__c','Unspecified'))
        ret += '  https://na1.salesforce.com/%s\n' %tbInfo.get('Id')

        ret += '\n'
        ret += 'CR Information:\n'

        crList.sort(lambda a,b: cmp(a.get('CaseNumber'), b.get('CaseNumber')))
        for cr in crList:
            ret += '\n'
            ret += '  %d: %s\n' %(int(cr.get('CaseNumber')), cr.get('Subject'))
            ret += '   Component: %-25s  Type: %s\n' \
                   %(cr.get('Component__c'), cr.get('Type'))
            ret += '   Status: %s\n' %cr.get('Status')
            ret += '   https://na1.salesforce.com/%s\n' %(cr.get('Id'))
            continue

        ret += '\n'
        ret += 'Branch Approval Information:\n'

        baList.sort(lambda a,b: cmp(a.get('Order__c'), b.get('Order__c')))
        for ba in baList:
            ret += '\n'
            ret += '  %s - %s\n' %(ba.get('Approval_Role__c'), ba.get('Name'))
            ret += '   Status: %s;   Approval: %s\n' \
                   %(ba.get('Status__c'), ba.get('Approve__c'))

            if ba.get('Approval_Role__c') in ['CR Originator',
                                              'Product Engineer']:
                ret += '   crs: %s\n' %(ba.get('CR_List__c'))
                pass

            ret += '   %s\n' %(ba.get('Date_Time_Actioned__c'))
            ret += '   https://na1.salesforce.com/%s\n' %(ba.get('Id'))
            continue

        return ret




    def cloneCrLinks(self, ClList):
        """ Helper routine for creating CR links to task branch having id
        tbId based on a link of Cr Links from another branch
        """
        tbData = self.getData('Task_Branch__c')
        tbId = tbData.get('Id')
        tbStatus = tbData.get('Branch_Status__c')
        tbStream = tbData.get('Code_Stream__c')

        for crLink in ClList:
            clData = {"Name": 'BrCR Link',
                      "Case__c": crLink.get('Case__c'),
                      "Branch_Status__c": tbStatus,
                      "CR_Status__c": crLink.get('CR_Status__c'),
                      "CR_Subject__c": crLink.get('CR_Subject__c'),
                      "Component__c": crLink.get('Component__c'),
                      "CR_Num__c": crLink.get('CR_Num__c'),
                      "Stream__c": tbStream}
            clId = self.setBranchCRLink(tbId, id='', data=clData)
            continue
        return
    ## END cloneCrLinks

    def cloneBranchApprovals(self, baList):
        """ Clone provided list of branch approvals AS-IS to the
        instances task branch """

        tbData = self.getData('Task_Branch__c')
        tbId = tbData.get('Id')
        tbStatus = tbData.get('Branch_Status__c')
        tbStream = tbData.get('Code_Stream__c')

        for ba in baList:
            newBaData = {"Name": ba.get("Name"),
                         "OwnerId": ba.get("OwnerId"),
                         "Approval_Role__c": ba.get("Approval_Role__c"),
                         "Approve__c": ba.get("Approve__c"),
                         "Branch__c": ba.get("Branch__c"),
                         "Case__c": ba.get("Case__c"),
                         "Component__c": ba.get("Component__c"),
                         "CR_CreateDate__c": ba.get("CR_CreateDate__c"),
                         "CR_List__c": ba.get("CR_List__c"),
                         "Instructions__c": ba.get("Instructions__c"),
                         "Order__c": ba.get("Order__c"),
                         "Status__c": ba.get("Status__c"),
                         "Stream__c": tbStream,
                         "Task_Branch__c": tbId,
                         }

            # remove any null-valued entries
            for key in newBaData.keys():
                if newBaData[key] is None:
                    del(newBaData[key])
                    pass
                continue

            baId = self.setBranchApproval(id='', tbId=tbId, data=newBaData)

            continue
        return
    ## END cloneBranchApprovals



    #######################################################################
    #   Status oriented methods
    #######################################################################
    def setBranchStatus(self, status='', st=None, scmTS=None, psReset=False,
                        qorrespin=False):
        """ Set the status fields for the Task Branch and CR Link entities
            This involved a complete query of prior information
            REQUIRED: All CR Link objects must already be created
            scmTS is an optional timestamp from walkSCM which is the
            mtime of the token file - used only as the actioned time for the
            most recent SCM band
        """
        branch = self.branch
        stream = self.stream

        if self.loadFromSF:
            tbData = self.getData()
        else:
            tbData = self.getSFData( branch, stream, show=False)

        if status in [None,'']:
            tbInfo = tbData.get('Task_Branch__c',{})
            tbId = tbInfo.get('Id')
            tbStatus = tbInfo.get('Branch_Status__c')
            status = tbStatus

        notify = self.setBranchApprovalStatus(status, st, scmTS=scmTS)
        if len(notify) == 0: nt = ' no changes'
        else:     nt = ' notify for %s user'%len(notify)
        if st is not None: ts = '%.7s'%((time.time()-st))
        else:              ts = ' '
        #clList = tbData.get('Branch_CR_Link__c',[])
        #baList = tbData.get('Branch_Approval__c'.[])
        #msg = '%s->>setTBStat-> %25s CL:%s BA:%s %s status:%s '%(ts,branch,len(clList),len(baList),nt,tbStatus)
        #self.sfb.setLog(msg,'info')

        return self.setBranchStatusCL(status, scmTS=scmTS, psReset=psReset,
                                      qorrespin=qorrespin)



    def getCRList(self):
        """ get existing CR list for the branch """
        crNums = []
        clList = self.getData('Branch_CR_Link__c')
        if clList == []: self.sfb.setLog('getCRList called but data not loaded','error')
        for clInfo in clList:
            crNum = clInfo.get('CR_Num__c')
            if crNum in [None,'',0,'0']:
                crId = clInfo.get('Case__c')
                crNum = self.sfb.getCrNumByCrId(crId)
                #print 'getCRList: got crNum:%s from crId:%s'%(crNum,crId)

            # only add the cr num once
            if not crNum in crNums:
                crNums.append(crNum)

        if self.debug>1:print 'getCRList: returning crList: %s'%crNums
        return crNums



    def setBranchCRLink(self, tbId, id='', data=''):
        """ update or create a Branch CR Link object """
        if data in [None,'']:
            if id in [None,'']:
                print 'Bad Mojo, no data and no id.  Result is no update'
            data = self.getData('Branch_CR_Link__c',id)
        #print 'setBranchCRLink:%s\n'%data
        if id in [None]:
            self.setLog('setBranchCRLink with ID of None data:%s'%(data),'error')
            return ''

        if not data.has_key('Component__c'):
            ddata = self.getData('Branch_CR_Link__c',id)
            data['Component__c'] = ddata.get('Component__c','')
            data['Component_Link__c'] = ddata.get('Component_Link__c','')

        if not data.has_key('Component_Link__c'):
            if data.has_key('Component__c'):
                lookup = data.get('Component__c')
                compInfo = self.sfb.getComponent(lookup)
                compId = compInfo.get('Id')
                data['Component_Link__c'] = compId
                self.sfb.setLog('setBranchCRLink linked %s to TB:%s'%(lookup,tbId),'info2')

        res = ''
        mode = 'Updated'
        if id != '':
            data['Id'] = id
            if not data.has_key('CR_Num__c'):
                crId = data.get('Case__c')
                if crId in [None,'']:
                    dt = self.getData('Branch_CR_Link__c',id)
                    crId = dt.get('Case__c')
                    if crId in [None,'']:
                        self.sfb.setLog('setBACRL getting crNum using crId:%s from CL:%s'%(crId,data),'warn')
                crInfo = self.sfb.getCrById(crId)
                crNum =  crInfo.get('CaseNumber',0)
                data['CR_Num__c'] = '%s'%int(crNum)
                csecs = self.sfb.checkDate(crInfo.get('CreatedDate'))
                data['Fix_Requested__c'] = csecs
            res = self.sfb.update('Branch_CR_Link__c',data)
        else:
            data['Task_Branch__c'] = tbId
            res = self.sfb.create('Branch_CR_Link__c',data)
            mode = 'Created'
        if res in self.badInfoList:
            msg = '%s Branch CR Link, tbid:%s %s %s\ndata: %s' \
                  %(mode,tbId,self.branch,res, data)
            self.sfb.setLog(msg, 'error')
            if self.debug >1: print 'ERROR: %s' %msg
            return ''
        id = res[0]
        data['Id'] = id
        self.setData({'Branch_CR_Link__c':data})
        if self.debug >3:
            print '%s Branch CR Link, %s %s Status-> CR:%s  branch:%s'%(mode,self.stream,self.branch,data.get('CR_Status__c',''),data.get('Branch_Status__c'))
        return id


    def setTeamBranchLink(self, tbId, teamId, brId='', data=''):
        """ update or create a Team Branch Link object """
        if data in [None,'']:
            if tbId in [None,'']:
                print 'Bad Mojo, no data and no id.  Result is no update'
            data = self.getData('Branch_Team_Link__c',tbId)

        if tbId != '':
            data['Id'] = tbId
            res = self.sfb.update('Branch_Team_Link__c',data)
            mode = 'Updated'
            if self.debug >1:
                print 'Updated TeamBRLink with data:%s\n res:%s'%(data,res)
        else:
            data['Task_Branch__c'] = brId
            data['Team_Branch__c'] = teamId
            res = self.sfb.create('Branch_Team_Link__c',data)
            mode = 'Created'
            if self.debug >1:
                print 'Create TeamBRLink with data:%s\n res:%s'%(data,res)
        if res in self.badInfoList:
            if self.debug >1: print 'ERROR: %s Team Branch Link, tbid:%s %s %s'%(mode,tbId,self.branch,res)
            return ''
        id = res[0]
        data['Id'] = id
        self.setData({'Branch_Team_Link__c':data})
        if self.debug >0: print '%s Team Branch Link, %s %s Status-> %s'%(mode,self.stream,self.branch,data.get('Branch_Status__c'))
        return id
    ## END setTeamBranchLink



class SFTaskBranchTool(SFMagmaTool):
    """ This is a subclass of the SFEntityTool to hold any Branch specific
        SOQL query methods and entity linking action methods
    """

    tb_obj = 'Task_Branch__c'
    tb_appr = 'Branch_Approval__c'
    cr_link = 'Branch_CR_Link__c'
    csNextGeneric = '4'
    logname = 'sfTBT'

    #debug = 3   # CV Sept 7th, 2004 remove this??

    def setupChild(self):
        """ add methods in child classes"""
        home = os.environ.get('USER')
        self.brsop = sfBranches()


    ##################################################################################################
    #  Branch access methods
    ##################################################################################################
    def getTBInfoById(self, tbId, fields=[]):
        """ get the Task Branch info or a subset """
        if tbId in [None,'',[]]: return {}
        if fields in [None,'',[]]: fields = 'all'
        if fields in ['min']: fields = ['Branch_Status__c','Branch__c']
        tbList = self.retrieve([tbId], 'Task_Branch__c', fieldList=fields)
        if tbList in self.badInfoList:
            print 'getTBInfoById: NO Task Branch Found for %s ret:%s ' %(tbId, tbList)
            return {}
        return tbList[0]


    def getTBWith(self, where=None, show=False):
        """ get the Branch Approvals using passed where clause"""
        collect = []
        if where is None:
            if hasattr(self,'uid'):
                uid = self.uid
            else:
                uid = '00530000000cCy5'  #Chip Vanek
            where = [['OwnerId','=',uid]]
        queryList = self.query('Task_Branch__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'getTBWith Result: NO Task Branches Found using %s'%where
            return collect
        for info in queryList:
            collect.append(info)
        return collect

    def getTBAnyInfo(self, branch):
        """ get the Task Branch Info for a specific branch
        """
        res = {}
        where = [['Name','=',branch]]
        queryList = self.query('Task_Branch__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'getTBAnyInfo: NO Task Branch Found for %s ' %(branch)
            return res
        res = queryList
        return res

    def getTBInfo(self, branch, stream):
        """ get the Task Branch Info for a specific branch/stream pair
        """
        res = {}
        where = [['Name','=',branch],'and',['Code_Stream__c','=',stream]]
        #print where
        queryList = self.query('Task_Branch__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'getTBInfo: NO Task Branch Found for %s in %s ' %(branch, stream)
            return res
        if len(queryList) > 1:
            print 'getTBInfo: WARN There should be one ONE TB object per Branch/stream pair %s %s'%(stream,branch)
        res = queryList[0]
        #print res
        return res

    def setTBInfo(self, data=[{}]):
        """ get the Task Branch Info for a specific branch/stream pair
        """
        res = {}
        sdata ={}

        updateList = self.update('Task_Branch__c', data=data)
        if updateList in self.badInfoList:
            print 'setTBInfo: NO Task Branch Found for %s in %s ' %(branch, stream)
            return res
        if len(updateList) > 1:
            print 'setTBInfo: WARN There should be one ONE TB object per Branch/stream pair %s %s'%(stream,branch)
        res = updateList[0]
        return res

    def setTBFixStamp(self, branch, stream, status, ts='now', tb='task'):
        """  Set the Process metric timestamp fields on Task Branch
             object.
        """
        if ts in [None,'now']: ts = time.time()
        if status in [None,'']:
            print 'Please provide a status as next step'
            return False

        if type(ts) == type(0.0):
            dateStr = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.localtime(ts))
        else:
            dateStr = self.checkDate(ts)

        if tb in ['task']:
            entity = 'Task_Branch__c'
            where = [['Branch__c','like',branch], 'and',
                     ['Code_Stream__c','=',stream]]
        else:
            entity = 'Team_Branch__c'
            where = [['Branch__c','like',branch], 'and',
                     ['Stream__c','=',stream]]

        tbList = self.query(entity, where=where, sc='all')
        total = len(tbList)
        if tbList in self.badInfoList:
            msg = 'setTBFixStamp FOUND no %s items using %s'%(entity, where)
            self.setLog(msg,'error')
            return False
        msg = 'setTBFixStamp FOUND %s %s %s %20s time:%s stat:%s '\
                      %(total, entity, stream, branch, dateStr, status)
        self.setLog(msg,'info')
        tbObj = SFTaskBranch(sfTool=self,debug=self.debug)
        if tbList > 1:
            tbInfo = tbList[0]
        tbId = tbInfo.get('Id')
        tokens = tbObj.loadBranchById(tbId)
        # tokens = [numCLs,numBAs,status,branch,stream]
        tbStatus = tokens[2]
        msg = 'setTBFixStamp Checking %s -> %s AT %s ts:%s'\
                            %(tbStatus, status, dateStr, ts)
        self.setLog(msg,'info')
        updated = False
        updated = tbObj.setProcessStamp(status, datetime=dateStr)
        if updated:
            print 'Updated %s'%(tokens)
        return updated


    def getTBsByCR(self, CR, fix=False):
        """ get the Task Branch info linked to a CR
            returns list of {'branch':branch, 'stream'stream, 'Task_Branch__c':{tbInfo} }
        """
        crNum = int(CR.get('CaseNumber',0))
        crId  = CR.get('Id')
        crStatus = CR.get('Status')
        where = [['Case__c','=',crId]]
        result = []
        fixed = 0
        queryList = self.query('Branch_CR_Link__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print '    NO Task Branch Found linked to CR %s'%crNum
            queryList = []
        tot = len(queryList)
        streams = self.getCRcsPriority(CR=CR)
        if tot > 0:
            print '  CR info for %s with %s branches streams %s and CR.status %s'%(crNum, tot, streams, crStatus)
        num = 0
        for info in queryList:
            tbId   = info.get('Task_Branch__c')
            brStat = info.get('Branch_Status__c')
            crStat = info.get('CR_Status__c')
            stream = info.get('Stream__c')
            if tbId in [None,'',[]]:
                self.setLog('getTBsByCR: no tbId in:%s'%info,'error')
                continue
            tbInfo = self.retrieve([tbId], 'Task_Branch__c')[0]
            brStatus = tbInfo.get('Branch_Status__c')
            branch = tbInfo.get('Branch__c')
            msg = ''
            data = {}
            if crStat != crStatus:
                msg = 'Link has Bad CR.status of %s'%crStat
                data['CR_Status__c'] = crStatus
            if brStat != brStatus:
                msg += ' Link has Bad BR.status of %s'%brStat
                data['Branch_Status__c'] = brStatus
            if stream in streams: streams.remove(stream)
            else:  msg += ' %s NOT in stream priority'%stream
            if fix and len(data) > 0:
                data['Id'] = info.get('Id')
                sfId = self.update('Branch_CR_Link__c', [data])
                msg += ' sForce UPDATED'
                fixed += 1

            result.append({'branch':branch,'stream':stream,'Task_Branch__c':tbInfo, 'fixed':fixed})
            print '  %15s %25s %s'%(brStatus,branch,msg)
        if len(streams) > 0:
            print '    FIXES REQUIRED: Missing Branch for stream >%s<'%streams
        return result


    def showBranch(self, stream=None, branch=None, where=[]):
        res = []

        print "DEPRECATED! Please report this along with which command you are running"
        print "to salesforce-support@molten-magma.com"
        print

        if stream not in [None,'']:
            if len(where): where.append('and')
            where.append(['Stream__c','=',stream])

        if branch not in [None,'']:
            if len(where): where.append('and')
            where.append(['Branch__c','like',branch])

        queryList = self.query('Branch_Approval__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'showBranch Result: NO Branch Approvals Found for %s in %s ' %(branch, stream)
            return res
        ret = '\n'
        tbInfo = {}
        for info in queryList:
            if type(info) not in dictTypes:
                return 'Error: showMyBranch for %s returned %s' %(branch, info)
            tbId = info.get('Task_Branch__c','')
            if tbId not in [None,'']:
                if tbInfo == {}:
                    tbInfo = self.retrieve([tbId], 'Task_Branch__c')[0]
                    ret += 'Branch: %s  \tStream: %s\n'%(tbInfo.get('Name'),tbInfo.get('Code_Stream__c'))
                    ret += '  Branch Status: %s\n'%tbInfo.get('Branch_Status__c',
                                                             'No Status!')
                    ret += '  Priority:      %-10s  Num CRs:        %s\n'%(tbInfo.get('Priority__c'),tbInfo.get('Num_CRs__c','').strip())
                    ret += '  High Risk:     %-10s  Command Change: %s\n'%(tbInfo.get('High_Risk__c'),tbInfo.get('Command_Change__c'))
                    ret += '  https://na1.salesforce.com/%s\n'%tbId
                    ret += '\n'
                    ret += '  Approval Information:\n'
                baId = info.get('Id')
                name = info.get('Name')
                role = info.get('Approval_Role__c')
                date = info.get('Date_Time_Actioned__c')
                status = info.get('Status__c')
                approval = info.get('Approve__c','')
                crList = info.get('CR_List__c')
                ret += '     %s - %s\n' %(role, name)
                ret += '     Status: %s;   Approval: %s\n'%(status, approval)
                ret += '     crs: %s\n'%(crList)
                ret += '     %s\n'%(date)
                ret += '     https://na1.salesforce.com/%s\n\n'%(baId)
        return ret



    def showMyBranch(self, uid=None, stream=None, branch=None):
        """ one call to get all new Task Branch Approval objects
            will return data as a list of data dictionaries [{data}] or []
        """
        if uid in [None,'']:  uid = self.uid
        userInfo = self.getContactByUserId(uid)
        userName = '%s %s' %(userInfo.get('FirstName'),userInfo.get('LastName'))
        res = []
        where = []
        where=[['OwnerId','=',uid]]

        res = self.showBranch(stream=stream, branch=branch, where=where)
        if res in self.badInfoList:
            print 'showMyBranch Result: NO Branch Approvals Found for %s or %s in %s ' %(uid, branch, stream)

        return res




    ##################################################################################################
    #  Branch information access methods
    ##################################################################################################
    def getBranchMap(self, branch, stream, data={}, reset=False):
        """ main accessor for getting branch load status information
        """
        key = '%s@@%s'%(branch,stream)
        if self.debug > 2: print 'Branch Load status for %s loaded %3d secs ago' %(branch, self.brsop.getAge(key))
        if reset: self.brsop.reset(True)
        if self.brsop.isStale(key):
            if self.debug > 2: print 'Updating sop for %s' %key
            self.setBranchMap(branch, stream, data)
            if reset: self.brsop.reset(False)
        return self.brsop.getData(key)

    def setBranchMap(self, branch, stream, data={}):
        """ load the latest metadata for branch load status into a simple object persitence dictionary
        """
        st = time.time()
        key = '%s@@%s'%(branch,stream)
        if data in [None,{},[],'']:
            data = {}

        if self.debug > 3: print '%2d sec Got %s keys and in %s' %(time.time()-self.startTime, len(data.keys()), key)
        self.brsop.setData(key, data)
        self.brsop.commit()



    def getSQOLWhereShortcut(self, where='', parm=''):
        """ convert some shortcut strings into valid WHERE clause
             Output is a a list of clause triplets and operators [and, or, not]
        """
        likeParm = '%'+parm+'%'
        if where in [None, '']: where = 'tb'
        if where in ['tb_obj']:                               # get the core TaskBranch object
            where = [['Branch__c','like',likeParm]]
        elif where in ['tb_link']:                            # get objects linked to this tb
            where = [['Task_Branch__c','=','%s'%parm]]
        elif where in ['cr_mod']:                             # get CR linked to this MOD
            where = [['WhatId','=','%s'%parm]]
        elif where in ['br_mod']:                             # get MODs with this branch label
            where = [['BranchLabel__c','like',likeParm]]
        return where



##########################################################################
#  Logic methods called from command line
##########################################################################

def getBranchFromFile(filename, parm, options):
    # Misha and Chip --> 5/17/2006
    stream = options.cs
    db = options.debug
    if len(filename.split('/')) == 1:
        fpath = os.path.join(os.getcwd(),filename)
    else:
        fpath = filename
    if not os.path.isfile(fpath):
        print 'Could not find a file at %s'%fpath
    else:
        try: fp = open(fpath, 'r')
        except Exception,e:
            print 'Could not open the branch load file in %s' %fpath
            print '%s err:%s' %(Exception,e)

        sfb = SFTaskBranchTool(debug=options.debug)
        brObj = SFTaskBranch2(sfTool=sfb)
        num = 1
        print ''
        print ' %-10s  %-35s  %-35s' % ('Stream', 'Branch', 'Status')
        print ' =========================================================================== '
        for line in fp.readlines():
            rw = line.split('\r')
            rw = rw[0].split('\n')
            if db > 0: print 'Found branch %s %s'%(num,row)
            #print rw
            row = rw[0].split(' ')
            #print row
            branch = row[0]
            if branch not in [None,'']:
                num += 1
                #brObj.getSFData(branch, stream)
                #results = brObj.data
                #pprint.pprint( results)
                brs = sfb.getTBAnyInfo(branch)
                if db > 1: print brs
                for br in brs:
                   status = br.get('Branch_Status__c','')
                   stream = br.get('Code_Stream__c','')
                   print ' %-10s  %-35s  %-35s' % (stream, branch, status)
                   if db > 1: pprint.pprint( br )

def setBranchFromFile(filename, parm, options):
    # Misha and Chip --> 5/17/2006
    import re
    stream = options.cs
    new_status = options.status
    new_status = re.sub('_', ' ', new_status)
    if (new_status == ''):
        new_status_print = '(Unchanged)'
    else:
        new_status_print = new_status

    db = options.debug
    if len(filename.split('/')) == 1:
        fpath = os.path.join(os.getcwd(),filename)
    else:
        fpath = filename
    if not os.path.isfile(fpath):
        print 'Could not find a file at %s'%fpath
    else:
        try: fp = open(fpath, 'r')
        except Exception,e:
            print 'Could not open the branch load file in %s' %fpath
            print '%s err:%s' %(Exception,e)

        sfb = SFTaskBranchTool(debug=options.debug)
        brObj = SFTaskBranch2(sfTool=sfb)
        # get picklist for table Task_Branch__c, field Branch_Status__c
        plv = sfb.getPicklist('Task_Branch__c', 'Branch_Status__c')
        if db > 0: print plv
        valid_picklist = []
        for plvs in plv:
                tmatch = re.search(r'SCM', plvs, re.IGNORECASE)
                if (tmatch): valid_picklist.append(plvs)

        valid_picklist.sort()
        #if db > 0: print valid_picklist
        if (new_status not in valid_picklist):
                print 'Invalid Status: %s. Valid Status must be one of:' % new_status
                for vp in valid_picklist:
                        print ('\t\t%s') % (vp)
                sys.exit()

        num = 1
        print ''
        print ' %-10s  %-35s  %-35s  %-35s' % ('Stream', 'Branch', 'Old Status', 'New Status')
        print ' ========================================================================================================= '
        for line in fp.readlines():
            rw = line.split('\r')
            rw = rw[0].split('\n')
            if db > 0: print 'Found branch %s %s'%(num,row)
            #print rw
            row = rw[0].split(' ')
            #print row
            branch = row[0]
            if branch not in [None,'']:
                num += 1
                #brs = sfb.getTBAnyInfo(branch)
                brs = sfb.getTBInfo(branch, stream)
                if (brs == {}): continue
                if db > 1: print brs
                #for br in brs:
                old_status = brs.get('Branch_Status__c','')
                stream = brs.get('Code_Stream__c','')
                bid = brs.get('Id','')
                data={'Id':bid}
                data['Branch_Status__c'] = new_status
                brs = sfb.setTBInfo(data)
                print ' %-10s  %-35s  %-35s  %-35s' % (stream, branch, old_status, new_status_print)
                if db > 1: pprint.pprint( brs )

def doCreate(entity, where, parm, options):
    print 'Creating the %s items found with query %s using parm %s' %(entity, where, parm)
    print 'Just kidding, not implemented'

def doSomething(method, term, parm, options):
    """  Command line controlled test of a method """
    print 'You called me with method:%s term:%s parm:%s ' %(method, term, parm)
    print 'Hope it was good for you'

##################################################################################################
#  Commandline management methods.  Minimal logic, just command parm processing
##################################################################################################
def usage(err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to get Branch status info from SalesForce using branch names in a file.\n'
    m += '  Branch name is first space seperated value on a row of the file.\n'
    m += '  \n'
    m += '    branchls -f path_to_file \n'
    m += '      or\n'
    m += '    branchls -f filename_in_cwd \n  '
    return m

def main_CL():
    """ Command line parsing and and defaults methods
    """
    parser = OptionParser(usage=usage(),version='%s'%version)
    parser.add_option("-c", "--cmd ", dest="cmd",   default="get",      help="Command type to use (default=get).")
    parser.add_option("-p", "--parm", dest="parm",  default="",         help="Command parms.")
    parser.add_option("-f", "--path", dest="path",  default="brlist",   help="Path to load file (default=brlist).")
    parser.add_option("-x", "--status", dest="status",default="",         help="New Branch Status.")
    parser.add_option("-s", "--cs  ", dest="cs",    default="blast5",   help="Code Stream of Branch (default=blast5)")
    parser.add_option("-t", "--trace", dest="trace", default="soap.out", help="SOAP output trace file.")
    parser.add_option("-d", "--debug", dest='debug', action="count",     help="The debug level, use multiple to get more.")
    (options, args) = parser.parse_args()
    if options.debug > 1:
        print ' cmd    %s' %options.cmd
        print ' path   %s' %options.path
        print ' parms  %s' %options.parm
        print ' trace  %s' %options.trace
        print ' debug  %s' %options.debug
        print ' args:  %s' %args
    else:
        options.debug = 0

    if len(args) > 0:
        st = time.time()
        parm = options.parm
        query = args[0:]
        branch = args[0]

        if options.cmd in ['get','branchls']:
            getBranchFromFile(options.path, parm, options)

        elif options.cmd in ['set','branchset']:
            setBranchFromFile(options.path, parm, options)

        elif options.cmd in ['load','l']:
            filename = options.path
            num = options.parm
            if num in [None,'']: num = 2
            skip = 0
            loadBranchFromFile(filename, num, skip, options)

        else:
            doSomething('search', query, options.parm, options)
            print 'doing nothing yet, I can do it twice if you like'

        print '\nTook a total of %3f secs' %(time.time()-st)
    else:
        print '%s' %usage()

if __name__ == "__main__":
    main_CL()
