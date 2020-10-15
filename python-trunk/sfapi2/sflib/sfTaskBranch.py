""" Business Logic specific to Task Branch customer object
    - Task Branch (TB) is a sForce representation of a code branch in Clearcase
    - TB is displayed as a contaiber object with a list of:
       - Branch Approvals - Developer Accept, Manager Approve, PE Approve, AE accept, Closed
       - Branch CR Links - link objects to customer oriented CRs with mirroroed CR Status
    
 ToDo:
    - Create compound object that can manage all sForce objects as one object
    - 
           Chip Vanek, June 7th, 2004
"""
import sys, time, os, datetime
if (sys.platform != 'win32'): import grp
import pprint
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
from sfUtil import getTestMailAddr
from sop import ccBranches, opBranches, sfBranches, sfEntities, SFEntitiesMixin, SFUtilityMixin, SFTestMixin, BasicCacheMixin
import tokenFile
from emailTransMap import emailTransMap

class CcBranchCache(BasicCacheMixin):
    """
    Simple wrapper to create a ClearCase branch cache object
    """
    def __init__(self):
        BasicCacheMixin.__init__(self, ccBranches())
        return
    ## END __init__
## class CcBranchCache


class OpBranchCache(BasicCacheMixin):
    """
    Simple wrapper to create an operational branch cache object
    """
    def __init__(self):
        BasicCacheMixin.__init__(self, opBranches())
        return
    ## END __init__

    def getNewKeys(self):
        """
        return keys of branches which haven't yet been inserted into
        salesforce (has no SfTaskBranchId field)
        """
        newKeyList = []
        for key in self.getKeys():
            val = self.getCache(key)
            if val.has_key('SfTaskBranchId') is False:
                newKeyList.append(key)
                pass
            continue
        return newKeyList
    ## END getNewKeys()
## class OpBranchCache


class SFTaskBranch(SFMagmaEntity):
    """ This is a composite object that represents a TaskBranch sForce object
        and related Branch Approval & Branch CR objects as one entity
    """
    tb_obj = 'Task_Branch__c'
    tb_appr = 'Branch_Approval__c'
    cr_link = 'Branch_CR_Link__c'
    branchType = 'task'
    modList = []
    loadFromSF = False

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

    def checkLoad(self, branch, stream, cl=False):
        """ check that the Task Branch is loaded
            returns [numCLs,numBAs,status,branch,stream,numBTLs]
        """
        ret = [0,0,'',branch,stream]
        if not hasattr(self.data, 'Task_Branch__c'):
            if branch in [None,''] or stream in [None,'']:
                print 'You must provide a branch label and code stream'
                return ret
            ret = self.loadBranch(branch, stream)
            if self.debug>0 : print ret

        status = self.getData().get('Task_Branch__c',{}).get('Branch_Status__c','')
        numCLs = len(self.getData().get('Branch_CR_Link__c'))
        if numCLs == 0 and cl:
            print ' No CRs are linked to the branch %s in stream %s'%(branch,stream)
            return [-1,0,status,branch,stream]
        numBAs = len(self.getData().get('Branch_Approval__c'))
        if numBAs == 0 and cl:
            print ' No BAs were created for the branch %s in stream %s'%(branch,stream)
            return [numCLs,-1,status,branch,stream]

        numBTLs = len(self.getData().get('Branch_Team_Link__c',[]))
        
        ret = [numCLs,numBAs,status,branch,stream,numBTLs]
        return ret


    def getSFData(self, branchLabel, stream, show=True):
        # Defunct? 10/11/2004
        where = [['Branch__c','like',branchLabel]
                ,'and',['Code_Stream__c','=',stream]]
        
        res = self.getSFDataCommon(where, show=show)
        return res

    def getSFDataById(self, id, show=True):
        # Defunct? 10/11/2004
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
                
                approvals = self.sfb.query('Branch_Approval__c', where=where, sc='all')   # should limit field with sc='Branch_Approval'
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
        caseFields = ('Id','Subject', 'Type', 'CaseNumber', 'Status', 'Component__c')
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
        
        #print "CR LISt ............... %s" %crList

        if crList not in [None,'','fail']:
            crList.sort(lambda a,b: cmp(a.get('CaseNumber'), b.get('CaseNumber')))
            for cr in crList:
                ret += '\n'
                ret += '  %d: %s\n' %(int(cr.get('CaseNumber')), cr.get('Subject'))
                ret += '   Component: %-25s  Type: %s\n' %(cr.get('Component__c'), cr.get('Type'))
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


    def cloneBranch(self, newstream, status=None, details=None, autocreate=False):
        """ Make a duplicate of this branch having the same name in
        a new stream
        """
        # safeguard against overduplication in a stream here!
        
        # get this task branch's info in a map
        tbData = self.getData('Task_Branch__c')
        tbClList = self.getData('Branch_CR_Link__c')

        # create new (empty) task branch obj
        newTbObj = SFTaskBranch(sfTool=self.sfb)
        newTbObj.loadBranch(self.branch, newstream)

        newTbData = {}
        xferFields = ('OwnerId','Name','High_Risk__c','Branch_Priority__c',
                      'QOR_Results__c','Branch_Or_Label__c','Branch__c',
                      'Branch_Path__c','Command_Change__c')
        
        for field in xferFields:
            if tbData.has_key(field):
                newTbData[field] = tbData[field]
                pass
            continue

        # Now, fields unique to the autocreated branch
        newTbData['Code_Stream__c'] = newstream

        if status is not None:
            newTbData['Branch_Status__c'] = status
        else:
            newTbData['Branch_Status__c'] = tbData.get('Branch_Status__c',
                                                       'Fixing')
            pass
            
        if details is not None:
            newTbData['Details__c'] = details
        else:
            newTbData['Details__c'] = tbData.get('Details__c','')
            pass

        if autocreate is True:
            newTbData['Autocreated__c'] = True
            pass

        # create the new task branch object now
        newTbId = newTbObj.setTaskBranch(id='', data=newTbData)
        
        # link all CRs that the orig branch has
        newTbObj.cloneCrLinks(tbClList)
        newTbObj.refresh()
        return newTbObj
    ## END cloneBranch


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
        

    def setBranchStatusCL(self, status, scmTS=None, psReset=False,
                          qorrespin=False):
        """ set the status on Task Branch and CR Links """
        from walkSCM import findReleasePath, findVersionNum

        data = {}
        buildData={}
        tbData = self.getData()
        tbInfo = tbData.get('Task_Branch__c')
        tbStatus = tbInfo.get('Branch_Status__c','')
        #tbStatMap = self.sfb.getStatMap(tbStatus)
        #tbStatOrder = tbStatMap.get('order')
        
        tbId = tbInfo.get('Id')
        tbStream = tbInfo.get('Code_Stream__c')
        clList = tbData.get('Branch_CR_Link__c')   
        baList = tbData.get('Branch_Approval__c')
        btlList = tbData.get('Branch_Team_Link__c')

        statMap = self.sfb.getStatMap(status,{})
        statOrder = statMap.get('order', 0.0)
        updated = False
        fvOpen = tbInfo.get('Fix_Requested__c')

        if (tbStatus != status or scmTS is not None or fvOpen is None) and status != '':
            if qorrespin is True:
                self.setQorRespin()
                pass


            # set the Merged Time field if we're at or beyond a merged
            # status and have an scm token timestamp
            if statOrder >= 54.0 and scmTS is not None:
                data['Merged_Date_Time__c'] = self.sfb.checkDate(scmTS)
                data['Fix_SCM_Merged__c'] = self.sfb.checkDate(scmTS)
                

                # find release path candidate for stream + merge date/time
                releasePath = None
                versionNum = None

                try:
                    releasePath = findReleasePath(tbStream, scmTS)                                      
                    # find the version number in the releasePath
                    if releasePath is not None:
                        data['Patch_Release_Path__c'] = releasePath
                        versionNum = findVersionNum(releasePath)
                        pass
                except Exception, e:
                    print "Uh oh, Spaghettios [TM]: %s" %e
                    print "\n\n>>> tbStream %s" %tbStream
                    print ">>> scmTS %s" %scmTS
                    pprint.pprint(tbInfo)
                    traceback.print_exc(file=sys.stdout)
                    pass

                if versionNum is not None:
                    data['Patch_Version__c'] = versionNum
                    # Calling method to create a build object
                    # Check if the build with the version number exist if none returned then create a new Build Object
                    #   
                    
                    buildData['Version__c']=tbStream
                    buildData['Build_ID__c']=versionNum
                    buildData['Build_Path__c']=releasePath
                    buildData['Account__c']='00130000000DWRJAA4'
                    buildData['Build_Date__c']=self.sfb.checkDate(scmTS)
                    self.checkIfBuildObjExist(buildData)     
                    
                    #end of the build Object call         
                    pass
                else:
                    # Misha 5/1/2005 --> send alert email since Patch Version can not be empty
                    #to_address = ['salesforce-support@molten-magma.com']
                    to_address = [getTestMailAddr()]
                    subject = 'SFDC Script (sfTaskBranch) Critical Error: Patch Version Empty'
                    msgBody = 'Critical error needs your intervention: \\n'
                    msgBody += 'Build_ID: %s, Build_Path: %s \\n' % (versionNum, releasePath)
                    msgBody = 'Patch Version is empty. Branch ID: %s' % (tbId)
                    msg = self.sendMsg(to_address, subject, msgBody)
                    pass

                pass
                

            if tbInfo.get('Fix_Requested__c') in [None]:
                reqDT = self.getCROpenStamp(clList)
                if reqDT not in [None,'',0]:
                    reqsec = self.sfb.checkDate(reqDT)
                    data['Fix_Requested__c'] = reqsec
                    
            # Set the Process Timestamps just before we change status
            try:
                updated = self.setProcessStamp(status, reset=psReset)
            except Exception,e:
                msg = 'Problem with setProcessStamp %s -> %s e:%s'%(tbStatus,status,e)
                
            data['Branch_Status__c'] = status
            sfId = self.setTaskBranch(id=tbId, data=data, numCRs=len(clList) )  #, datamerge='passedPlus'
            if '%s'%sfId != tbId:
                print 'Problem with setting status to %s for %s ret:%s'%(status, tbId, sfId)
                print self.sfb.lastRet
                return 0
            updated = True
            msg= 'STATUS %s %s %s->%s numCRs:%s numAppr:%s updated:%s'\
                 %(self.stream, self.branch, tbStatus, status, len(clList),len(baList),len(data))
            if self.debug >2: 
                print 'Updated TaskBranch %s with %s'%(tbId, data)
        else:
            msg= 'STATUS OK %s %s  %s numCRs:%s numAppr:%s updated:%s'\
                 %(self.stream, self.branch, status, len(clList),len(baList),len(data))
        self.sfb.setLog(msg,'info2')    
        if self.debug >0: print msg

        clList2 = copy.deepcopy(clList)
        for clInfo in clList2:
            clStat = clInfo.get('Branch_Status__c')
            #clInfo['Branch_Status__c'] = status
            clId = clInfo.get('Id')
            crNum = clInfo.get('CR_Num__c')
            comp = clInfo.get('Component__c')
            data = {'Branch_Status__c':status, 'Component__c':comp}  #'Name': status,
            self.setBranchCRLink(tbId, id=clId, data=data)
            msg= 'setCL:%s %s %s->%s updated CR Link with status'%(self.branch, self.stream, clStat, status)
            if clStat == status:
                msg= '      %s %s %s=%s CL comp:%s'%(self.branch, self.stream, clStat, status, comp)
            self.sfb.setLog(msg,'info')

            # Now, have the CR re-evaluate its status if the branch changed status.
            crObj = SFCr(sfTool=self.sfb)
            crObj.loadCr(crNum)
            """Commented the below command to update 2nd status"""
            #crObj.setCrStatus()
            crObj.setCrStatus(None,tbStream,clStat)
            continue


        # update status on any branch team lists
        for btl in btlList:
            # should only be one...
            btlId = btl.get('Id')
            btlTmbId = btl.get('Team_Branch__c')
            btlData = {'Branch_Status__c': status}
            self.setTeamBranchLink(btlId, btlTmbId, data=btlData)
            continue
        
        return updated
    
    #Check to see if the build object with the same verion number exist or not    
   
    def checkIfBuildObjExist(self,buildData):
        versionNumber=buildData.get('Build_ID__c')
        fields= ('Id', 'Build_ID__c')
        where = ['Build_ID__c','=',versionNumber]        
        #where = [versionNumber]
        ret = self.sfb.query('Build__c', where, fields)
        
        print "Value of query is %s" %ret
        if ret in self.badInfoList:            
            if len(ret)==0:
                msg = "Couldn't find any records in the Build Object with the given version number: %s" %(versionNumber) 
                print msg    
                self.sfb.setLog(msg,'info')       
                self.createBuildObject(buildData)
            pass
        elif len(ret)==1:
            for rt in ret:
                id =rt.get('Id')
                self.updateBuildObject(id)
                continue
            pass
        elif len(ret)>1 :
            msg="WARNING :Found more than two records with the same version number, using the latest"
            print msg
            self.setLog(msg,'warn')
            update=False     
            for rt in ret:
                id =rt.get('Id')
                if update==False:
                    self.updateBuildObject(id)
                    update=True  
                    pass
                continue   #for           
            pass  #if             
        
        pass                 
    
        
        
    
    def createBuildObject(self,buildData):
        msg= "Creating new build object"
        print msg
        self.sfb.setLog(msg,'info')
        buildData['Build_Type__c']='Patch Build'
        buildData['Needs_Check__c']=True
        versionNumber=buildData.get('Build_ID__c')
        name='Patch Build'+' '+versionNumber
        buildData['Name']=name
        res = self.sfb.create('Build__c',buildData)
        if res in self.badInfoList:
            if self.debug >0: print 'ERROR in Creating Build Object: %s '%(res)
            pass 
        
    def updateBuildObject(self,id):
        msg= "Updating the build object..."  
        print msg
        self.sfb.setLog(msg,'info')
        updData = {'Id': id,
                   'Needs_Check__c': True}                                      
        res = self.sfb.update('Build__c',updData)
        if res in self.badInfoList:
            if self.debug >0: print 'ERROR in Updating Build Object: %s '%(res)
            pass 

    def getCROpenStamp(self, clList):
        """ Find a CR Open DateTime from the list of CR Links, First one wins  """
        dt = None
        crId = ''
        for clInfo in clList:
            crNum = clInfo.get('CR_Num__c')
            crId = clInfo.get('Case__c')
            openDT = clInfo.get('Fix_Requested__c')
            if openDT not in [None,'']:
                dt = openDT
                break
        if dt not in [None,'',0]:
            return dt
        if crId not in [None,'']:
            crInfo = self.sfb.getCrById(crId)
            crNum =  crInfo.get('CaseNumber',0)
            dt = crInfo.get('CreatedDate')
            dt = self.sfb.checkDate(dt)

        return dt

    def setQorRespin(self):
        """ Increment the QOR respin counter """
        tbData = self.getData()
        tbInfo = tbData.get('Task_Branch__c')

        respincount = int(float(tbInfo.get('CRV_SCM_QOR_Recycle_Count__c', 0)))
        respincount += 1

        updData = {'Id': tbInfo.get('Id'),
                   'CRV_SCM_QOR_Recycle_Count__c': respincount}

        res = self.sfb.update('Task_Branch__c',updData)
        if res in self.badInfoList:
            msg = 'setQorRespin update failed %s ->%s %s'\
                  %(self.branch,res,updData)
            # full result is at self.sfb.lastRet
            print 'setQorRespin update error:\n%s'%self.sfb.lastRet
            self.sfb.setLog(msg,'error')
            return False
        id = res[0]
        self.setData({'Task_Branch__c':updData})
        msg = 'setQorRespin for %s updated to %s'\
              %(self.branch,respincount)
        self.sfb.setLog(msg,'info')
        return True
    ## END setQorRespin
        
    def setProcessStamp(self, status, datetime='now', reset=False):
	""" update the right 'Fix_XX' customer field on the Task Branch
	    based on the passed status using the passed date-time
	"""
	if datetime in [None]:
	    datetime = self.sfb.checkDate('now')
	try: datetime = self.sfb.checkDate(datetime)
	except Exception, e:
	    msg = 'setProcessStamp %s status:%s date:%s %s'%(self.branch,status,datetime,e)
	    self.sfb.setLog(msg,'error')
	tbData = self.getData()
        tbInfo = tbData.get('Task_Branch__c')
        tbStatus = tbInfo.get('Branch_Status__c','')
	data = {}
        if ((tbStatus != status) and status not in [None, '']) or reset == True:
            # Status is changing from one value to another
            tbStatMap = self.sfb.getStatMap(tbStatus,{})
            tbStatOrder = tbStatMap.get('order',0)
            statMap = self.sfb.getStatMap(status,{})
            statOrder = statMap.get('order')
            msg = 'setProcessStamp %s If %s>%s then %s->%s ts:%s'\
                   %(self.branch,statOrder,tbStatOrder,tbStatus,status,datetime)
            self.sfb.setLog(msg,'info')
	    if (statOrder > tbStatOrder or status in ['Fixing','SCM-Hold']) or reset == True:
		# status is changed and moving forward
                oldts = ''
                hrm = 'setProcessStamp Hours to '
		if status in ['Fixing']:
		    oldts = tbInfo.get('Fix_Linked__c')
                    if oldts in [None,''] or reset:
                        data['Fix_Linked__c'] = datetime
                        
		elif status in ['Approving by Manager']:
		    oldts = tbInfo.get('Fix_Submitted__c')
                    if oldts in [None,''] or reset:
                        data['Fix_Submitted__c'] = datetime
                    #The elapsed hours below is from the CR Creation timestamp 
                    rqdt = tbInfo.get('Fix_Requested__c')
                    if rqdt not in [None,'',0]:
                        msg = '%s unknown need Fix_Requested %s'%(hrm,self.branch)
                        self.sfb.setLog(msg,'info')
                    else:
                        hrs = (datetime - self.sfb.checkDate(rqdt))/3600 
                        data['Fix_Submitted_Hours__c'] = hrs
                        msg = '%s to submit %s for %s'%(hrm, hrs,self.branch)
                        self.sfb.setLog(msg,'info')
                        
		elif status in ['Approving by PE']:
                    # tb has been mgr approved
		    oldts = tbInfo.get('Fix_Approved_Mgr__c')
                    if oldts in [None,''] or reset:
                        data['Fix_Approved_Mgr__c'] = datetime
		    
		elif tbStatus in ['Approving by PE']:
                    # outbound from Approving by PE - tb is fully PE approved
		    oldts = tbInfo.get('Fix_Approved_PE__c')
                    if oldts in [None,''] or reset:
                        data['Fix_Approved_PE__c'] = datetime
		    
		elif status in ['Team Branch Hold','Submitted to SCM','SCM-Received']:
		    oldts = tbInfo.get('Fix_SCM_Received__c')
                    if oldts in [None,''] or reset:
                        data['Fix_SCM_Received__c'] = datetime
                    #The elapsed hours below is from the Fix Submitted timestamp 
                    sdt = tbInfo.get('Fix_Submitted__c')
                    if sdt in [None,'',0]:
                        msg = '%s unknown need Fix_SCM_Received %s'%(hrm,self.branch)
                        self.sfb.setLog(msg,'info')
                    else:
                        hrs = (datetime - self.sfb.checkDate(sdt))/3600
                        data['Fix_SCM_Received_Hours__c'] = hrs
                        msg = '%s to SCM Receive %s for %s'%(hrm, hrs,self.branch)
                        self.sfb.setLog(msg,'info')
                        
		elif status in ['SCM-QOR Building','SCM-QOR Testing']:
		    oldts = tbInfo.get('Fix_SCM_QOR__c')
                    if oldts in [None,''] or reset:
                        data['Fix_SCM_QOR__c'] = datetime
                        
		elif status in ['SCM-QOR Results']:
		    oldts = tbInfo.get('Fix_SCM_QOR_Results__c')
                    if oldts in [None,''] or reset:
                        data['Fix_SCM_QOR_Results__c'] = datetime
                    #The elapsed hours below is from the SCM Received timestamp 
                    sdt = tbInfo.get('Fix_SCM_Received__c')
                    if sdt in [None,'',0]:
                        msg = '%s unknown need Fix_SCM_Received %s'%(hrm,self.branch)
                        self.sfb.setLog(msg,'info')
                    else:
                        hrs = (datetime - self.sfb.checkDate(sdt))/3600
                        data['Fix_SCM_QOR_Results_Hours__c'] = hrs
                        msg = '%s to SCM QOR Results %s for %s'%(hrm, hrs,self.branch)
                        self.sfb.setLog(msg,'info')

                elif status in ['SCM-Hold','SCM-Post-Release']:
		    oldts = tbInfo.get('Fix_SCM_Hold__c')
                    if oldts in [None,''] or reset:
                        data['Fix_SCM_Hold__c'] = datetime
                        
                elif status in ['SCM-Bundle Results','SCM-Bundle Building'
                               ,'SCM-Bundle Testing','SCM-Ready to Bundle']:
		    oldts = tbInfo.get('Fix_SCM_Bundle__c')
                    if oldts in [None,''] or reset:
                        data['Fix_SCM_Bundle__c'] = datetime
                        
		elif status in ['SCM-Red-Building','SCM-Red-Build Results'
                               ,'SCM-Patch-Building','SCM-Patch-Build Testing'
                               ,'SCM-Patch-Build Results'
                               ,'SCM-Candidate-Build Testing'
                               ,'SCM-Candidate-Building'
                               ,'SCM-Candidate-Build Results']:
		    oldts = tbInfo.get('Fix_SCM_Build__c')
                    if oldts in [None,''] or reset:
                        data['Fix_SCM_Build__c'] = datetime
                        
		elif status in ['Merged','Merged - Testing by Originator']:
		    oldts = tbInfo.get('Fix_SCM_Merged__c')
                    # NOTE this is turned off 
                    if oldts in [None,''] or reset and 0:   
                        data['Fix_SCM_Merged__c'] = datetime
                    #The elapsed hours below is from the QOR Results timestamp 
                    sdt = tbInfo.get('Fix_SCM_QOR_Results__c')
                    if sdt in [None,'',0]:
                        msg = '%s unknown need Fix_SCM_QOR_Results %s'%(hrm,self.branch)
                        self.sfb.setLog(msg,'info')
                    else:
                        hrs = (datetime - self.sfb.checkDate(sdt))/3600
                        data['Fix_SCM_Merged_Hours__c'] = hrs
                        msg = '%s to SCM Merged %s for %s'%(hrm, hrs,self.branch)
                        self.sfb.setLog(msg,'info')

                if status in ['Approved, pending Team Branch']:
                    # task branches in team are considered submitted to SCM
                    # when mgr+PE approved and are Approved, pTB
                    # re-use team approved timestamp to measure this
                    oldts = tbInfo.get('Fix_Approved_Team__c')
		    if oldts in [None,''] or reset:
                        data['Fix_Approved_Team__c'] = datetime
                        pass
                    pass
                        
		if len(data) > 0:
		    data['Id'] = tbInfo.get('Id')
	            res = self.sfb.update('Task_Branch__c',data)
		    if res in self.badInfoList:
                        msg = 'setProcessStamp update failed %s ->%s %s'\
                                %(self.branch,res,data)
                        # full result is at self.sfb.lastRet
                        print 'setProcessStamp update error:\n%s'%self.sfb.lastRet
			self.sfb.setLog(msg,'error')
                        return False
                    id = res[0]
                    self.setData({'Task_Branch__c':data})
                    msg = 'setProcessStamp Updated! %s %s->%s ts:%s oldts:%s'\
                           %(self.branch,tbStatus,status,datetime,oldts)
                    #msg += '\n%s'%(self.sfb.lastRet)
                    self.sfb.setLog(msg,'info')
		    return True
                else:
                    msg = 'setProcessStamp No Update? Was:%s:%s -> %s:%s ts:%s oldts:%s'\
                            %(tbStatOrder,tbStatus,statOrder,status, datetime,oldts)
		    self.sfb.setLog(msg,'info')
            else:
                msg = 'setProcessStamp noop: %s status:%s date:%s '\
                           %(self.branch,status,datetime)
                self.sfb.setLog(msg,'info2')           
        return False		    
		    

    def setBranchApprovalStatus(self, status=None, st=None, scmTS=None, partData=None):
        """ Called on every change of a Task Branch to ensure the 'right' Branch Approval 
            relationships still exist.  Can be called at anytime after initial 'addMOD'
            -  checks/created following BA sub-object with correct related status
                - Developer BA owner by TB owner, subject and status wrt status parm
                - EngMgr BA owner mgr of developer, status wrt status parm
                - SCM BA owned by BA owner, status wrt status parm
                - Loop over CR Links and create BAs
                    - PE BA owned by component PE of CR
                    - CR Origin BA for each CR owned by originator of CR

            REQUIRED:   self.getData must be fully loaded
                        All CR Links must be present
            baRoleMap = {'dev':{'ids':[],'sf:'','sfids':[], 'status':'', 'order':30.0},...}
                         - ids are a list of UserIds, sfids are the list of BA object Ids
                baRoleMap used to see what branch approvals to add/update
        """
        tbInfo = self.getData('Task_Branch__c')
        btlList = self.getData('Branch_Team_Link__c')

        tbId = tbInfo.get('Id','')
        tbOwner = tbInfo.get('OwnerId')     
        if not tbOwner:
            self.sfb.setLog('setBA:%s LoadTB No OwnerId found for %s IN %s'%(self.branch,tbId,tbInfo),'error')
            return {}
        tbOwner = self.sfb.getId18(tbOwner)
        tboCont = self.sfb.getContactByUserId(tbOwner)
        tbOwnerMgr = self.sfb.getMgrIdByDevId(tbOwner,tboCont)
        tbOwnerMgr = self.sfb.getId18(tbOwnerMgr)

        if status in [None,'']:
            status = tbInfo.get('Branch_Status__c','Fixing')
        self.baRoleMap = self.setBaRoleMap()    # self.baRoleMap = {'dev':{'ids':[],'sf:'','sfids':[], 'crList':[], 'status':'', 'order':30.0}

        if len(btlList) > 0:
            # task branch is linked to team branch
            tmbId = btlList[0].get('Team_Branch__c',None)
        else:
            tmbId = None

        statMap = self.sfb.getStatMap(status,{})   # statMap = {'order':36.0, 'role':'dev', 'crStatus':'Approved', 'crStatusFirst':'First-Approved'}
        statOrder = statMap.get('order')
        if statOrder in [None,'']:
            print 'ERROR getStatMap returned wrong value for -> %s <-'%status
        
        clList = self.getData('Branch_CR_Link__c')
        crNums = []
        clMap = {}
        
        # check if Task Branch has a linked PE Checkpoint
        linkedPE_Checkpoint = False
        if tbInfo.get('Linked_Objects__c','None') == 'PE Checkpoint':
            linkedPE_Checkpoint = True
        
        for clInfo in clList:
            crId = clInfo.get('Case__c')
            clId = clInfo.get('Id')
            # Fixme after steady state, expensive call
            #  CV Oct 21, 2004
            crInfo = self.sfb.getCrById(crId)
            crNum =  crInfo.get('CaseNumber',0)
            comp =  crInfo.get('Component__c','')  # get component string directly from the CR
            #crNum = self.sfb.getCrNumByCrId(crId) # this allows PE reassignment
            clComp = clInfo.get('Component__c','')
            if comp != clComp:
                # updating CRLink object with newly found component
                msg = 'setBAStat:%30s Changing Comp:%s->%s'%(self.branch, clComp, comp)
                msg += ' for CR: %s stat:%s'%(crNum,status)
                self.sfb.setLog(msg,'info')
                #print msg
                data = {'Component__c':comp}
                self.setBranchCRLink(tbId, id=clId, data=data)
                
            #clMap[crNum] = comp         
            clMap[crNum] = crInfo       # CV 10/27/04 Need more CR info in BAs
            if crNum not in crNums:
                crNums.append(crNum)
        msg = 'setBAStat:%30s Order:%s  status:%s  for %s CRs'%(self.branch, statOrder, status, len(crNums))
        self.sfb.setLog(msg,'info')
        if self.debug>0: print msg
        totalNotify = {}

        for role in ['dev','part','mgr','pe','team','scm','ae']: # extend for Customer?
            roleMap = self.baRoleMap.get(role)
            validActions = ['Approved','Rejected','Approve','Reject','-','']
            date = 'now'        # fix this ?!
            notify = {}
            if role == 'dev':
                validStats = ['Fixing','Submitting','Submitted','Closed']
                # notify on Submitting -> Submitted TO mgr
                stat = 'Fixing'
                if statOrder > 31.9: stat = 'Rejected Back to Developer'
                if statOrder > 32.9: stat = 'Submitted'
                if statOrder > 69.9: stat = 'Closed'
                notify = self.setBranchApprovalStatusForDev( tbId, tbOwner, roleMap, clMap, stat, validStats, validActions)

            elif role == 'part':
                validStats = ['Approving',
                              'Approved',
                              'Rejecting',
                              'Rejected']
                #notify Requires Approval -> Approving TO Mgr & Rejecting -> Rejected TO Dev
                stat = 'Pending Submission'
                if statOrder >= 33.0: stat = 'Approving'     #Submitted or later
                if statOrder >= 34.0: stat = 'Approved'      #Approving by Manager or later
                notify = self.setBranchApprovalStatusForPartition(tbId, roleMap, stat, validStats,validActions, partData)
                
            elif role == 'mgr':
                validStats = ['Pending Submission',
                              'Approving',
                              'Approved',
                              'Rejecting',
                              'Rejected',
                              'Rejected by Mgr',
                              'Rejected by PE'] 
                #notify Requires Approval -> Approving TO Mgr & Rejecting -> Rejected TO Dev
                # NOTE notify method must set TB.Status to Approved by Manager to avoid looping notification
                stat = 'Pending Submission'
                #if statOrder > 32.9: stat = 'Requires Approval'     #Submitted = 33.0
                if statOrder > 33.9: stat = 'Approving'             #Approving by Manager = 34.0
                if statOrder > 34.5: stat = 'Approved'              #Approved by Manager = 34.2
                notify = self.setBranchApprovalStatusForMgr(tbId, tbOwnerMgr, roleMap, clMap, stat, validStats,validActions)
                
            elif role == 'pe' and not linkedPE_Checkpoint:
                validStats = ['Pending Submission',
                              'Requires Approval',
                              'Approving',
                              'Approved',
                              'Rejecting',
                              'Rejected'] 
                #notify Requires Approval -> Approving
                stat = 'Pending Submission'
                if statOrder > 34.5: stat = 'Requires Approval'     #Approved by Manager = 34.2
                if statOrder > 34.9: stat = 'Approving'             #Approving by PE = 35.0
                if statOrder > 35.5: stat = 'Approved'              #Approved by PE = 35.2
                notify = self.setBranchApprovalStatusForPE(tbId, roleMap, clMap, stat, validStats,validActions)
            
            elif role == 'team':
                # These are the only states valid for modification from
                # the task branch perspective
                validStats = ['Awaiting Task Branch',
                              'Task Branch Ready',]
                # Here we move a team manager BA from Awaiting to Ready when
                # it is PE approved - the team branch takes it from there...
                stat = "Awaiting Task Branch"
                if statOrder >  35.2: stat = 'Task Branch Ready'
                notify = self.setBranchApprovalStatusForTeamMgr(tbId, roleMap,
                                                                stat, validStats)

                
            elif role == 'scm':
                scmBaOwner = '00530000000cBrzAAE'
                validStats = ['Pending Fix',
                              'Requires Receipt',
                              'Received',
                              'Accepted',
                              'Testing',
                              'Patch Build Available',
                              'Merged'] 
                #notify Requires Receipt -> Received to dev & Testing -> Red Build Available to AE & dev
                # status values will not be enforced to allow walkSCM to provide new statuses
                order = 4.40
                stat = 'Pending Submission'
                if statOrder > 53.9: stat = 'Merged'
                elif statOrder > 43.9 and statOrder < 54:           #Approved, pending Branch = 36.0
                    order = statOrder/10                            # this will show the TB status through SCM
                    stat = '%s'%(status)
                    
                notify = self.setBranchApprovalStatusForSCM(tbId, scmBaOwner, roleMap, clMap, stat, order, scmTS=scmTS)

            elif role == 'ae':
                validStats = ['Pending Merged Fix',
                              'Merged - Notifying Originator',
                              'Merged - Testing by Originator',
                              'Merged - Approved',
                              'Merged - Rejected'] 
                #notify Requires Approval -> Approving
                stat = 'Pending Merged Fix'    #Merged - Notifying Originator = 54.0
                if statOrder > 54.0: stat = 'Merged - Testing by Originator'

                # this next case will (should) never happen. This state gets
                # determined inside setBranchApprovalStatusForOriginator
                if statOrder > 54.9: stat = 'Merged - Tested by Originator'
                
                notify = self.setBranchApprovalStatusForOriginator(tbId, roleMap, clMap, stat, validStats, validActions, tmbId=tmbId)
                        
            if st is not None: ts = '%.7s'%((time.time()-st))
            else:              ts = '  ' 
            msg = '%s %30s %sBA notify:%s'%(ts, self.branch, role, notify)
            totalNotify.update(notify)
            # end of role loop
        return totalNotify
        
        

    def setBranchApprovalStatusForDev(self, tbId, ownerId, roleMap, clMap, status, validStats,validActions):
        """ Check for and set/create Branch Approval for the Developer (dev)
                OwnerId = userID of the developer
                roleMap = {'ids':[],'sf:'','sfids':[], 'crList':[], 'status':'', 'order':30.0}
                crNums = list of crNumbers for the CR Links in Task Branch
            Return/change:
                change self.baRoleMap['dev'] for new or updated BA
                return notify info = {baId:status}
        """

        role = 'dev'
        order = 3.0
        notify = {}   # keyed on baId with status
        rolePick = roleMap.get('sf')
        roleIds = roleMap.get('ids')            # ids of the users who own ba object
        baIds = roleMap.get('sfids')        # ids of the BA objects
        baStat = roleMap.get('status')
        crNums = clMap.keys()
        approval = ''
        subject = '%s %s in %s for %s CRs'%(status, self.branch, self.stream, len(crNums))
        instuct = 'Please use the shell script submitbranch rather than changing the Approve Field above.'

        #print "roleIds: %s" %roleIds
        #print "ownerId: %s" %ownerId

        # Moved this out of block below...
        data ={'Name':subject,
               'Order__c': order,
               'Approval_Role__c': rolePick,
               'OwnerId': ownerId,
               'Approve__c':'',
               'Instructions__c': instuct,
               'Stream__c':self.stream,
               'Branch__c':self.branch}

        if ownerId not in roleIds:
            # create a developer BA for the owner.
            # BUT WHAT IF THE OWNER ISN'T THE DEVELOPER?
            baId = self.setBranchApproval('', tbId=tbId, status=status,
                                          data=data, crNums=crNums)
            self.sfb.setLog('setBA:%s NEW devBA %s for %s uid:%s IN %s'%(self.branch, status, crNums, ownerId, roleIds),'new')
            if baId in self.badInfoList:
                self.sfb.setLog('setBA:%s Updating devBA %s to %s ret:%s in %s'%(self.branch, rolePick, status, baId, crNums),'error')
            self.baRoleMap[role]['ids'].append(ownerId)
            self.baRoleMap[role]['sfids'].append(baId)

        else:
            baId = self.getBaId(ownerId, role)
            baInfo = self.getData('Branch_Approval__c',baId)
            baStat = baInfo.get('Status__c')
            baSubject = baInfo.get('Name')
            approval = baInfo.get('Approve__c','')
            

            if baStat not in validStats:
                self.sfb.setLog('setBA:%s devBA %s Bad Status of %s will be %s'%(self.branch, crNums, baStat,status),'warn')

            # Update everything. Actioned datetime will only change if
            # explicitly passed in or status differs.

            sfId = self.setBranchApproval(baId, tbId=tbId, status=status,
                                          data=data, crNums=crNums)

            # Log something about what just happened...
            if sfId in self.badInfoList:
                self.sfb.setLog('setBA:%s Updating devBA %s to %s ret:%s in %s'%(self.branch, rolePick, status, sfId, crNums),'error')
            elif status == baStat:
                self.sfb.setLog('setBA:%s devBA Status OK of %s ' \
                                %(self.branch, baStat),'info3')
            else:
                # status has changed!
                self.sfb.setLog('setBA:%s devBA %s Status changed TO %s for baId:%s'%(self.branch, crNums, status, sfId),'event')


                # anyone to notify of this status change?
                info = {'status':status, 'role':role,
                        'actor':ownerId, 'tbId':tbId}

                if status in ['Rejecting','Rejected',
                              'Rejected Back to Developer']:
                    self.sfb.setLog('setBA:%s Ready to notify DEV %s for Rejection'%(self.branch,ownerId),'info')
                    notify[baId]=info
                if approval in ['Approve'] and status in ['Fixing']:
                    self.sfb.setLog('setBA:%s Ready to notify MGR %s of Approval'%(self.branch,ownerId),'info')
                    notify[baId]=info
        
        return notify
        # end setBA Dev

    def setBranchApprovalStatusForPartition(self, tbId, roleMap, status, validStats, validActions, partData=None):
        """
        Check for and create Partiton Reviewer branch approvals for 

        """
        
        order = 3.3
        role = 'part'

        subjFmt = 'Approval for changes to your partition(s): %s'
        instruct = 'Please edit this item and choose Approve or Reject from the Approve Field above.'
        action = ''
        
        notify = {}

        rolePick = roleMap.get('sf') # the role name from the BA picklist
        roleIds = roleMap.get('ids') # user IDs of the approver/owner of BA
        baIds = roleMap.get('sfids') # ids of the BA objects
        baStat = roleMap.get('status')
        extraBas = copy.deepcopy(baIds) # get a copy of the ba ID list

        partMgrIdsNeeded = [] # this list drives this BA section
        partBasByMgrId = {}
        idToAliasMap = {}

        for baId in baIds:
            baData = self.getData('Branch_Approval__c',baId)
            partMgrUserId = baData.get('OwnerId')
            if partMgrUserId not in partBasByMgrId.keys():
                partBasByMgrId[partMgrUserId] = baData
                pass
            continue

        if partData is not None:
            # partition data passed in - let this drive the method
            # we'll need BA for each reviewer we have. Find their user IDs.
            for partMgrAlias in partData.keys():
                userData = self.sfb.getUserByAlias(partMgrAlias)
                partMgrUserId = userData.get('Id')
                if partMgrUserId not in partMgrIdsNeeded:
                    partMgrIdsNeeded.append(partMgrUserId)
                    pass
                idToAliasMap[partMgrUserId] = partMgrAlias
                continue
            pass
        else:
            # user the user IDs from Part BAs we already have to drive method
            partMgrIdsNeeded = copy.deepcopy(partBasByMgrId.keys())
            pass

##        print "IN setBranchApprovalStatusForPartition"
##        pprint.pprint(partData)
##        pprint.pprint(partBasByMgrId)
##        pprint.pprint(partMgrIdsNeeded)
        
        for partMgrId in partMgrIdsNeeded:
            partMgrAlias = idToAliasMap.get(partMgrId) # is only set if partData provided
            if not partBasByMgrId.has_key(partMgrId):
                # create new BA - we know we have partData for this new object
                
                # build the comment detailing the files that violate this
                # reviewer's partition(s)
                partInfo = partData.get(partMgrAlias)
                partNamesList, partFilesComment = self.buildPartitionFileComment(partInfo)
                partNamesStr = ', '.join(partNamesList)
                
                
                data ={'Name':subjFmt %partNamesStr,
                       'Order__c': order,
                       'Approval_Role__c': rolePick,
                       'OwnerId':partMgrId,
                       'Approve__c':'',
                       'Instructions__c': instruct,
                       'Stream__c':self.stream,
                       'Branch__c':self.branch,
                       'comments__c': partFilesComment}
                
                baId = self.setBranchApproval('', tbId=tbId, status=status,
                                              date='now',  data=data)
                self.sfb.setLog('setBA:%s NEW partBA %s for baId:%s uid:%s partMgrids:%s'%(self.branch,status,baId,partMgrId,roleIds),'new')
                if baId in self.badInfoList:
                    self.sfb.setLog('setBA:%s Creating partBA %s to %s ret:%s' \
                                    %(self.branch, rolePick, status, baId),
                                    'info')
                else:
                    # do we need to notify anyone of this new approval record?
                    if status in ['Requires Approval','Approving']:
                        self.sfb.setLog('setBA: %s Ready to notify Partition Reviewer '%(self.branch),'info')
                        info = {'status':status, 'role':role,
                                'actor':partMgrId, 'tbId':tbId}
                        notify[baId]=info
                        pass
                    
                    pass
                pass
            else:
               # update existing Part BA
               baData = partBasByMgrId.get(partMgrId)
               baId = baData.get('Id')
               baStat = baData.get('Status__c')
               action = baData.get('Approve__c','')
               
               extraBas.remove(baId)
               baDataUpd = {'Id': baId}

               # update files comment if partition data is provided
               if partMgrAlias is not None:
                   partInfo = partData.get(partMgrAlias)
                   
                   partNamesList, partFilesComment = self.buildPartitionFileComment(partInfo)
                   baDataUpd['comments__c'] = partFilesComment
                   
                   pass

               # reconcile the BA's action and status fields
               if len(action) and action not in validActions:
                   # wipe out ,'Not Applicable','Not Required'
                   action = '-'
                   pass

               # copy the passed-in status so as not to perturb it
               # for use in subsequent iterations
               newBaStatus = status
               
               if baStat == 'Approved':
                   # don't un-approve an approved part ba
                   newBaStatus = 'Approved'
               elif status == 'Approved':
                   action = 'Approve'
               elif status == 'Approving' and action == 'Approve':
                   # PE has set approval manually on the BA
                   newBaStatus = 'Approved'
               elif status == 'Pending Submission':
                   # BA is no longer Approved, but Approve is still set
                   # clear it
                   action = '-'
               else:
                   action = baData.get('Approve__c','')
                   pass
               
               baDataUpd['Approve__c'] =  action

               # issue the update
               baId = self.setBranchApproval(baId, tbId=tbId,
                                             status=newBaStatus,
                                             data=baDataUpd)

               if baId in self.badInfoList:
                   self.sfb.setLog('setBA:%s Updating partBA %s to %s ret:%s'%(self.branch, rolePick, status, baId),'error')
                   continue
               
               elif newBaStatus == baStat:
                   # updated but didn't change status
                   self.sfb.setLog('setBA:%s partBA Status OK of %s '%(self.branch, baStat),'info3') 
                   
               else:
                   # status has changed!
                   self.sfb.setLog('setBA:%s partBA Status changed TO %s for baId:%s'%(self.branch, newBaStatus, baId),'event')
                   
                   # any notifications of status change?
                   if status in ['Requires Approval','Approving']:
                       self.sfb.setLog('setBA: %s Ready to notify Partition Reviewer '%(self.branch),'info')
                       info = {'status':newBaStatus, 'role':role,
                               'actor':partMgrId, 'tbId':tbId}
                       notify[baId]=info
                       pass
                   pass
               
               pass
           
        # delete the extra BAs
        if len(extraBas) > 0:
            self.sfb.setLog('setBA:%s DELETING Extra partBA %s'\
                            %(self.branch, ', '.join(extraBas)),'error')
            self.sfb.delete(extraBas)
            pass
        
        

        return notify 
    ## END setBranchApprovalStatusForPartition



    def setBranchApprovalStatusForMgr(self, tbId, ownerId, roleMap, clMap, status, validStats, validActions):
        """ Check for and set/create Branch Approval for Development Manager (mgr)
                ownerId = userID of the engineering manager
                roleMap = {'ids':[],'sf:'','sfids':[], 'crList':[], 'status':'', 'order':30.0}
                clMap = {crNum:component} crNumbers mapped to components for the CR Links in Task Branch
            Return/change:
                change self.baRoleMap['mgr'] for new and updated BAs
                return notify info = {baId:status}
        """

        if self.debug >= 3:
            print "branch %s; stream %s; tbId %s; ownerId %s; status %s" \
                  %(self.branch, self.stream, tbId, ownerId, status)
            print "validStats: %s" %validStats
            print "validActions: %s" %validActions
            print "roleMap:\n%s" %pprint.pformat(roleMap)
            print "clMap:\n%s" %pprint.pformat(clMap)
            
        order = 3.4
        role = 'mgr'
        subject = 'Approval for %s in %s'%(self.branch, self.stream)
        instuct = 'Please edit this item and choose Approve or Reject from the Approve Field above.'
        action = ''
        notify = {}   # keyed on baId with status
        rolePick = roleMap.get('sf')
        roleIds = roleMap.get('ids')       # ids of the users who own ba object
        baIds = roleMap.get('sfids')       # ids of the BA objects
        baStat = roleMap.get('status')
        crNums = clMap.keys()
        try:
            if len(crNums):
                #print crNums
                crList = ','.join(crNums)
            else:
                crList = ''
        except Exception, e:
            # backout of status change?            
            self.sfb.setLog(" ERROR due to exception in setBranchApprovalStatusForMgr %s err:%s" %(Exception,e))
            pass
        
        #print "setBASForMgr - roleIds: %s" %roleIds
        #print "setBASForMgr - ownerId: %s" %ownerId

        # moved init of this data struct up from block below
        data ={'Name':subject,
               'Order__c': order,
               'Approval_Role__c': rolePick,
               'OwnerId': ownerId,
               'Approve__c':'',
               'Instructions__c': instuct,
               'Stream__c':self.stream,
               'Branch__c':self.branch}

        # FIXME
        # shouldn't check based on ownerID, just on existence
        # create one if there isn't one already.
        # also, should delete any that are owned by admin IDs.

        if len(baIds) == 0:
            # we have no eng mgr BA - create one.
            baId = self.setBranchApproval( '', tbId=tbId, status=status, date='now', data=data, crNums=crNums)
            self.sfb.setLog('setBA:%s NEW mgrBA %s %s for baId:%s uid:%s mgrids:%s'%(self.branch,crNums,status,baId,ownerId,roleIds),'new')
            if baId in self.badInfoList:
                self.sfb.setLog('setBA:%s Updating mgrBA %s to %s ret:%s in %s'%(self.branch, rolePick, status, baId, crNums),'info')
            self.baRoleMap[role]['ids'].append(ownerId)
            self.baRoleMap[role]['sfids'].append(baId)
            baIds.append(baId)

        for baId in baIds:    
            try:  
                #print "BA IS ...... %s" %baId              
                baInfo = self.getData('Branch_Approval__c',baId)            
                baStat = baInfo.get('Status__c')
                baCrList = baInfo.get('CR_List__c','')
                baOwnerId = baInfo.get('OwnerId','')
                action = baInfo.get('Approval__c','')
    
                # here's where we prevent snapping back to determined owner
                if baOwnerId != '':
                    data['OwnerId'] = baOwnerId
                    pass
                
                if len(action) and action not in validActions:
                    # wipe out ,'Not Applicable','Not Required'
                    action = '-'
    
                # Set the Approve flag accordingly if the status is set to Approved
                # copy passed status so that we don't ever perturb what we passed in
                newBaStatus = status
    
                if status == 'Approved' and action == 'Approve':
                    newBastatus = 'Approved'
                elif status == 'Approved':
                    action = 'Approve'
                elif status == 'Pending Submission':
                    # BA is no longer Approved, but Approve is still set - clear it
                    action = '-'
                else:
                    action = baInfo.get('Approval__c','')
    
                data['Approve__c'] = action
                
                if baStat not in validStats:
                    self.sfb.setLog('setBA:%s mgrBA %s Bad Status of %s will be %s'%(self.branch, crNums, baStat,status),'warn')
    
                # do the update
                baId = self.setBranchApproval(baId, tbId=tbId,
                                              status=newBaStatus,
                                              data=data,
                                              crNums=crNums)
    
                # write to log based on what just happened
                if baId in self.badInfoList:
                    self.sfb.setLog('setBA:%s Failed updating mgrBA %s to %s ret:%s in %s'%(self.branch, rolePick, status, baId, crNums),'error')
                elif status == baStat:
                    self.sfb.setLog('setBA:%s mgrBA %s Status OK of %s '%(self.branch, crNums, baStat),'info3')
                else:
                    self.sfb.setLog('setBA:%s mgrBA %s Status changed TO %s for baId:%s'%(self.branch, crNums, status, baId),'event')
    
                    # anyone to notify of status change?
                    if status in ['Requires Approval','Approving'] and \
                           action != 'Approve':
                        self.sfb.setLog('setBA:%s Ready to notify MGR %s for Approval'%(self.branch,ownerId),'info')
                        info = {'status':status, 'role':role,
                                'actor':ownerId, 'tbId':tbId}
                        notify[baId]=info
    
                # delete redundant mgrBA without creating problems ;)
                if len(baIds) >1 and baId not in self.badInfoList:
                    realOwnerID = baInfo.get('OwnerId')  # hoping the first one create is right
                    baList = copy.deepcopy(baIds)
                    for baId2 in baList:
                        if baId2 != baId:
                            baInfo = self.getData('Branch_Approval__c',baId2)
                            baOwnerId = baInfo.get('OwnerId')
                            if baOwnerId == realOwnerID:
                                self.sfb.setLog('setBA:%s DELETED redundant mgrBA for %s' \
                                                %(self.branch,baOwnerId),'warn')
                                self.sfb.delete([baId2])
            except Exception, e:
                    self.sfb.setLog('Error in function setBranchApprovalStatusForMgr %s err:%s'%(Exception,e))
        return notify
        # end setBA MGR

        
    def setBranchApprovalStatusForPE(self, tbId, roleMap, clMap, status, validStats, validActions):
        """ Check for and set/create Branch Approval for Product Engineers (pe)
        roleMap = {'ids':[],'sf:'','sfids':[], 'crList':[], 'status':'', 'order':30.0}
             'pe': {'ids':[],'sfids':[],'sf':'Product Engineer', 'crList':[]},
        clMap = {crNum:component} crNumbers mapped to result of getCrById(crId)
        Return/change:
        change self.baRoleMap['ae'] for new and updated BAs
        return notify info = {baId:status}
        """
        if self.debug >= 3:
            print "setBAStat4PE   ----------------"
            print "branch %s; stream %s; tbId %s; status %s" \
                  %(self.branch, self.stream, tbId, status)
            print "validStats: %s" %validStats
            print "roleMap:\n%s" %pprint.pformat(roleMap)
            print "clMap:\n%s" %pprint.pformat(clMap)

        order = 3.5
        role = 'pe'
        appRole = 'Product Engineer'

        rolePick = roleMap.get('sf')
        roleIds  = roleMap.get('ids')       # ids of the users who own ba object
        baIds = roleMap.get('sfids')        # ids of the BA objects
        baStat = roleMap.get('status')
        roleCrList = roleMap.get('crList')
        changes = {}   # keyed on baId with {crList:[], 'apprvId':peId, 'comp':comp, 'isNew':True|False}
        compCache = {}
        extraBAs = copy.deepcopy(baIds)
        
        ## check for reassign BAs Added Sept 27, 2006 CV
        skipBAs = []
        for baId in baIds:
            baInfo = self.getBaByIdInTb(baId,tbId)
            reassign = baInfo.get('Reassign_Owner__c', '')
            defPeId=baInfo.get('OwnerId', '')
            baResId=baInfo.get('Id', '')            
            self.sfb.setLog('setBA:%s get info for %s baInfo:%s'\
                    %(self.branch, baId, baInfo),'info')
            # change to support reassigning of PE Branch approvals
            # Must be able to see the new Reassign_Owner field 
            # PE must set this field after ownership reassign
            if reassign in ['Yes']:                
                # pop out before this BA marked as to be changed
                if baId in extraBAs:
                    extraBAs.remove(baId)
                skipBAs.append(baId)
    
        
        for crNum, crInfo in clMap.items():
            comp =  crInfo.get('Component__c','')
            # look up who we think the PE should be
            if compCache.has_key(comp):
                peId = compCache[comp]
            else:
                peId = self.sfb.getPEIdByComp(comp) # were comp is actual string from CR.Component
                peId = self.sfb.getId18(peId)
                if peId not in [None,'']:
                    compCache[comp] = peId
                else:
                    #print 'ERROR %s could not find PE for comp %s for %s'%(self.branch,comp,crNum)
                    peId = self.sfb.defaults.get('errorUId')

            # Do we already have a BA which addresses this CR?
            baId = self.getBaIdByCrNum(crNum, appRole)            
            if baId == '':
                # Do we already have a BA for this approver?
                baId = self.getBaId(peId, role)
            
            #print "Skip Ids ........... :%s " %skipBAs
            if skipBAs not in [None,'',[]]:
                baId=baResId
        
            if baId != '':                
                if baId in skipBAs:
                    # jump out of the loop to avoid adding a new BA                   
                    self.sfb.setLog('setBA:%s LOOKING at BA %s Found in Skipped'\
                        %(self.branch, baId),'info')
                    #peId=baInfo.get('OwnerId')
                    peId=defPeId                    
                    pass               
                                      
            else:
                self.sfb.setLog('setBA:%s peBA pe:%s not found in %s' \
                                %(self.branch, peId, roleIds),'info')
                        
            baInfo = self.getBaById(baId)
            peId = baInfo.get('OwnerId', peId)  
            info = changes.get(peId,{})
            crList = info.get('crList',[])
            if crNum not in crList:
                crList.append(crNum)

            info = {'baId': baId, 'crList':crList, 'comp':comp}

            changes[peId] = info            
            continue
                
        action = ''
        notify = {}   # keyed on baId with status
        for ownerId, info in changes.items():
            crList = info.get('crList',[])
            comp = info.get('comp')
            baId = info.get('baId')
            subject = 'Approval %s in %s for %s CRs'%(self.branch, self.stream, len(crList))
            instuct = 'Since you are the PE for %s you are asked to review that the CRs below are fixed in this branch, (Ensure there are Release Notes on each CR) then choose Approve or Reject from the Approve Field above.'%comp

            # moved this struct up from the block directly below
            data ={'Name':subject,
                   'Order__c': order,
                   'Approval_Role__c': rolePick,
                   'OwnerId': ownerId,
                   'Approve__c': action,
                   'Component__c':comp,
                   'Instructions__c': instuct,
                   'Stream__c':self.stream,
                   'Branch__c':self.branch}

            if baId in [None,'']:
                baId = self.setBranchApproval('', tbId=tbId, status=status,
                                              date='now', data=data,
                                              crNums=crList)
                self.sfb.setLog('setBA:%s peBA NEW %s cr:%s for uid:%s in:%s'%(self.branch, status, crList, ownerId, tbId),'new')
                if baId in self.badInfoList:
                    self.sfb.setLog('setBA:%s Updating peBA %s to %s ret:%s in %s'%(self.branch, rolePick, status, baId, crList),'error')
                    continue
                self.baRoleMap[role]['ids'].append(ownerId)
                self.baRoleMap[role]['sfids'].append(baId)

            else:
                if baId in extraBAs:
                    extraBAs.remove(baId)
                baInfo = self.getData('Branch_Approval__c',baId)
                if type(baInfo) == type([]):
                    print 'ERROR baId:%s got baInfo of:%s'%(baId, baInfo)
                baStat = baInfo.get('Status__c')
                baSubject = baInfo.get('Subject')
                action = baInfo.get('Approve__c','')
                
                if len(action) and action not in validActions:
                    # wipe out ,'Not Applicable','Not Required'
                    action = '-'

                newBaStatus = status
                
                if status == 'Approved':
                    action = 'Approve'
                elif status == 'Approving' and action == 'Approve':
                    # PE has set approval manually on the BA
                    newBaStatus = 'Approved'
                elif status == 'Pending Submission':
                    # BA is no longer Approved, but Approve is still set
                    # clear it
                    action = '-'
                else:
                    action = baInfo.get('Approve__c','')

                data['Approve__c'] =  action

                if baStat not in validStats:
                    self.sfb.setLog('setBA:%s peBA %s Bad Status of %s will be %s'%(self.branch, crList, baStat,status),'warn')

                # issue the update
                baId = self.setBranchApproval(baId, tbId=tbId,
                                              status=newBaStatus,
                                              data=data, crNums=crList)

                if baId in self.badInfoList:
                    self.sfb.setLog('setBA:%s Updating peBA %s to %s ret:%s in %s'%(self.branch, rolePick, status, baId, crList),'error')
                
                elif status == baStat:   # updated but didn't change status
                    self.sfb.setLog('setBA:%s peBA %s Status OK of %s '%(self.branch, crList, baStat),'info3') 

                else:
                    # status has changed!
                    self.sfb.setLog('setBA:%s peBA Status changed TO %s for %s baId:%s'%(self.branch, status, crList, baId),'event')
                    
                    # any notifications of status change?
                    if status in ['Requires Approval','Approving']:
                        self.sfb.setLog('setBA:%s Ready to notify PE '%(self.branch),'info')
                        info = {'status':status, 'role':role,
                                'actor':ownerId, 'tbId':tbId}
                        notify[baId]=info

        if self.debug>2:
            print 'setBA: peBA changes:%s, extraBAs:%s'%(changes,extraBAs)

        for baId in extraBAs:
            self.sfb.setLog('setBA:%s DELETING Extra peBA %s'\
                            %(self.branch, baId),'error')
            self.sfb.delete([baId])
            
        return notify
        # end setBA PE2

    def setBranchApprovalStatusForTeamMgr(self, tbId, roleMap, status, validStats):
        """
        Check for and set/create Branch Approval for Team Manager (team)
        for initial states (Awaiting Task Branch, Task Branch Ready)
                ownerId = userID of the engineering manager
                roleMap = {'ids':[],'sf:'','sfids':[], 'crList':[], 'status':'', 'order':30.0}
            Return/change:
                change self.baRoleMap['team'] for new and updated BA
                return notify info = {baId:status}

                This method ONLY updates the status of the team BA. Creation
                and other maintenance is done via the team branch itself.
                Don't have all the info to do 'snapback' here.
        """
        if self.debug >= 3:
            print "branch %s; stream %s; tbId %s; status %s" \
                  %(self.branch, self.stream, tbId, status)
            print "validStats: %s" %validStats
            print "roleMap:\n%s" %pprint.pformat(roleMap)
            
        order = 4.1
        role = 'team'
        rolePick = 'Team Manager'
        #subject = 'Approval for %s in %s'%(self.branch, self.stream)
        #instuct = 'Please edit this item and choose Approve or Reject from the Approve Field above.'
        action = ''
        notify = {}   # keyed on baId with status
        rolePick = roleMap.get('sf')
        roleIds = roleMap.get('ids')       # ids of the users who own ba object
        baIds = roleMap.get('sfids')       # ids of the BA objects
        baStat = roleMap.get('status')

        for baId in baIds:
            # ONLY update status here if it's within the range we deal with
            # Otherwise, leave it alone.
            if baStat in validStats:
                baId = self.setBranchApproval(baId, tbId=tbId, status=status,
                                              data={})

        return notify
        # end setBA Team



    def setBranchApprovalStatusForSCM(self, tbId, ownerId, roleMap, clMap, status, order, scmTS=None):
        """ Check for and set/create Branch Approval for SCM (scm)
                OwnerId = userID of the developer
                roleMap = {'ids':[],'sf:'','sfids':[], 'crList':[], 'status':'', 'order':30.0}
                crNums = list of crNumbers for the CR Links in Task Branch
            Return/change:
                change self.baRoleMap['scm'] for new or updated BA
                return notify info = {baId:status}
        """
        role = 'scm'
        subject = 'SCM Status for %s in %s'%(self.branch, self.stream)
        instuct = 'This item is the target for a cron updater to mirror branch status through SCM'
        action = ''
        notify = {}   # keyed on baId with status
        rolePick = roleMap.get('sf')
        roleIds = roleMap.get('ids')            # ids of the users who own ba object
        baIds  = roleMap.get('sfids')        # ids of the BA objects
        baStat = roleMap.get('status')
        crNums = clMap.keys()

        addNew = False
        if len(baIds) == 0: addNew = True
        elif len(baIds) == 1 and order > 45.0: addNew = True
        elif len(baIds) == 2 and order > 47.9: addNew = True
        elif len(baIds) == 3 and order > 48.9: addNew = True
        #elif len(baIds) == 3 and order > 45.0 and 'SCM-Hold' not in baStatus: addNew = True

        # promoted struct from block below
        data ={'Name':subject,
               'Order__c': order,
               'Approval_Role__c': rolePick,
               'OwnerId': ownerId,
               'Approve__c':'',
               'Instructions__c': instuct,
               'Stream__c':self.stream,
               'Branch__c': self.branch}
        
        # Only set Actioned Timestamp on Submit to SCM
	if status == 'Submitted to SCM' and scmTS not in [None,0]:
	    data['Date_Time_Actioned__c'] = scmTS
	    
        if addNew == True:
            self.sfb.setLog('setBA:%s NEW scmBA roleMap:%s\n data:%s\n'%(self.branch,roleMap, data),'new4') # change to new3

            if self.branchType == 'team':
                baId = self.setBranchApproval('', tbId=None, teamId=tbId,
                                              status=status, data=data, crNums=crNums)
            else:
                baId = self.setBranchApproval('', tbId=tbId, status=status,
                                              data=data, crNums=crNums)


            self.sfb.setLog('setBA:%s NEW scmBA %s %s for baId:%s'%(self.branch, crNums, status, baId),'new')
            self.sfb.setLog('setBA:%s NEW scmBA %s '%(self.branch, data),'new2')
            if baId in self.badInfoList:
                self.sfb.setLog('setBA:%s Updating scmBA %s to %s ret:%s in %s'%(self.branch, rolePick, status, baId, crNums),'error')
            self.baRoleMap[role]['ids'].append(ownerId)
            self.baRoleMap[role]['sfids'].append(baId)
        else:
            baId = baIds[-1]  # leave up to 3 old BAs to map progress
            baInfo = self.getData('Branch_Approval__c',baId)
            baStat = baInfo.get('Status__c')
            
            # will want to pass in token mtime if we happen to have it
            # for date. Otherwise, we'll take the current time on status
            # update
            
            if self.branchType == 'team':
                baId = self.setBranchApproval(baId, tbId=None, teamId=tbId,
                                              status=status, data=data, crNums=crNums)
            else:
                baId = self.setBranchApproval(baId, tbId=tbId,
                                              status=status, data=data, crNums=crNums)
           
            if baId in self.badInfoList:
                self.sfb.setLog('setBA:%s Updating scmBA %s to %s ret:%s in %s'%(self.branch, rolePick, status, baId, crNums),'error')
                
            elif status == baStat:
                # update complete, no status change
                self.sfb.setLog('setBA:%s scmBA updated, Status OK of %s '%(self.branch, baStat),'info3')

            else:
                # status has changed!
                self.sfb.setLog('setBA:%s scmBA updated %s Status changed TO %s for baId:%s'%(self.branch, crNums, status, baId),'event')
                
                # anyone to notify of status change?
                if status in ['Submitted to SCM']:
                    self.sfb.setLog('setBA:%s Ready to notify SCM for Acceptance'%(self.branch),'info')
                    info = {'status': status, 'role': role,
                            'actor': ownerId, 'tbId': tbId}
                    notify[baId]=info
            
        return notify
        # end setBA SCM


    def setBranchApprovalStatusForOriginator(self, tbId, roleMap, clMap, status, validStats, validActions, tmbId=None):
        """ Check for and set/create Branch Approval for CR Originators (ae)
                roleMap = {'ids':[],'sf:'','sfids':[], 'crList':[], 'status':'', 'order':30.0}
                clMap = {crNum:component} crNumbers mapped to components for the CR Links in Task Branch
            Return/change:
                change self.baRoleMap['ae'] for new and updated BAs
                return notify info = {baId:status}        """
        order = 6.0
        action = ''
        notify = {}   # keyed on baId with status
        role = 'ae'
        rolePick = roleMap.get('sf')
        baIds = roleMap.get('sfids')        # ids of the BA objects
        baStat = roleMap.get('status')
        roleCrList = roleMap.get('crList')
        crToBaIdMap = roleMap.get('crInfo')

        extraBAs = copy.deepcopy(baIds)
             


        for crNum, crInfo in clMap.items():
            #crNum=str(crNum)
            #crNum = crNum.lstrip('0')
            try:
                crNum = crNum.lstrip('0')
            except Exception, e:
                print 'error in function getBaIdByCrNum %s err:%s'%(Exception,e)        
            
            crNumZP = '0'*8 + '%s' %crNum
            crNumZP = crNumZP[-8:]
            comp =  crInfo.get('Component__c','')
            crCreated = crInfo.get('CreatedDate')
            crCreated = self.sfb.checkDate(crCreated, 'setBranchApproval')
            crId =  crInfo.get('Id')

            update = False  # or just spin

            # first try to lookup the cr num, then the zero-padded cr num if it failed
            #print "CR INFO......... %s" %crInfo
                       
            
            baId = crToBaIdMap.get(crNum,crToBaIdMap.get(crNumZP,''))
            
                       
            if baId in [None,'']:     
                try:
                    crTempNum="u'"+crNum+"'"
                    tempList=[]
                    tempList.append(crTempNum)            
                    baId = crToBaIdMap.get(tempList[0]) 
                except Exception, e:
                    print 'error in function getBaIdByCrNum %s err:%s'%(Exception,e)
                      
                if baId in [None,'']:   
                    try:
                        crTempNum="'"+crNum+"'"
                        tempList=[]
                        tempList.append(crTempNum)                                
                        baId = crToBaIdMap.get(tempList[0])                               
                    except Exception, e:
                        print 'error in function getBaIdByCrNum %s err:%s'%(Exception,e)
                 
            
            
            #if baId == '':
            #    msg = "Couldn't find crNum %s in roleMap('crInfo'):\n %s" \
            #          %(crNum, pprint.pformat(crToBaIdMap))
            #    self.sfb.setLog(msg, 'error')

            # promoted from block below
            if crNum not in [None,'']:
                ownerId = self.sfb.getCrOriginatorByCrNum(crNum)
            subject = 'Accept Fix for %s in %s in %s '%(self.branch, self.stream, crNum )
            instuct = 'Please test that this branch fixes the problem detailed in the CRs below and approve this item by changing the Approve Field above to Approve'

            data = {'Name': subject,
                    'Order__c': order,
                    'Approval_Role__c': rolePick,
                    'OwnerId': ownerId,
                    'Approve__c':'',
                    'Component__c':comp,
                    'Instructions__c': instuct,
                    'Stream__c':self.stream,
                    'Branch__c': self.branch,
                    'CR_CreateDate__c':crCreated,
                    'Case__c':crId}

            if baId in [None,'']:                # create new
                if tbId is not None:
                    sfId = self.setBranchApproval('', tbId=tbId, teamId=tmbId,
                                                  status=status, date='now',
                                                  data=data, crNums=[crNum])

                    self.sfb.setLog('setBA:%s aeBA NEW %s %s for baId:%s in:%s'%(self.branch, crNum, status, sfId, tbId),'new')
                    if sfId in self.badInfoList:
                        self.sfb.setLog('setBA:%s Updating aeBA %s to %s ret:%s in %s'%(self.branch, rolePick, status, sfId, crNum),'error')
                        continue
                    self.baRoleMap[role]['ids'].append(ownerId)
                    self.baRoleMap[role]['sfids'].append(sfId)
                else:
                    # called by a team branch with no task branch ID
                    msg = "Cannot create aeBA - no task branch ID provided"
                    self.sfb.setLog(msg, 'error')
            else:
                if baId in extraBAs:
                    extraBAs.remove(baId)
                    
                
                baInfo = self.getData('Branch_Approval__c',baId)
                if type(baInfo) == type([]):
                    print 'ERROR baId:%s got baInfo of:%s'%(baId, baInfo)
                    continue
                baStat = baInfo.get('Status__c')
                action = baInfo.get('Approve__c','')
                ownerId = baInfo.get('OwnerId','')

                # don't update the following fields if this is a team branch
                if self.branchType == 'team':
                    del(data['Name'])
                    del(data['Branch__c'])
                    
                
                if tbId in [None,'']:
                    updTbId = baInfo.get('Task_Branch__c','')
                else:
                    updTbId = tbId

                if action not in validActions:
                    # wipe out ,'Not Applicable','Not Required'
                    action = '-'
                    pass

                if baStat not in validStats:
                    self.sfb.setLog('setBA:%s aeBA %s Bad Status of %s will be %s'%(self.branch, crNum, baStat,status),'warn')
                    if status not in validStats:
                        status = 'Merged - Testing by Originator'

                newBaStatus = status
                
                if status[:13] == 'Merged - Test' \
                         and action in ['Approve']:
                    # AE has set approval manually on the BA
                    newBaStatus = 'Merged - Approved'
                elif status[:13] == 'Merged - Test' \
                         and action in ['Reject']:
                    # AE has set approval manually on the BA
                    newBaStatus = 'Merged - Rejected'
                else:
                    action = baInfo.get('Approve__c','')
                    pass
                
                data['Approve__c'] = action
                    
                # snap back - comment out this stanza to disable
##                expectedOwnerId = self.sfb.getCrOriginatorByCrNum(crNum)
##                if ownerId != expectedOwnerId:
##                    self.sfb.setLog('setBA:%s aeBA %s Bad Owner of %s will be %s'%(self.branch, crNum, ownerId,expectedOwnerId),'owner')
##                    data['OwnerId'] = expectedOwnerId
                data['OwnerId'] = ownerId # override the default with status quo


                # issue the update here
                
                sfId = self.setBranchApproval(baId, tbId=updTbId,
                                              teamId=tmbId, status=newBaStatus,
                                              data=data, crNums=[crNum])
                
                if sfId in self.badInfoList:
                    self.sfb.setLog('setBA:%s Updating aeBA %s to %s ret:%s in %s'%(self.branch, rolePick, newBaStatus, sfId, crNum),'error')
                    continue

                elif status == baStat:
                    # status hasn't changed.
                    self.sfb.setLog('setBA:%s aeBA %s Updated, Status OK of %s '%(self.branch, crNum, baStat),'info3')

                else:
                    # status has changed!
                    self.sfb.setLog('setBA:%s aeBA %s Updated, Status changed TO %s for baId:%s' %(self.branch, crNum, newBaStatus, sfId),'event')
                    
                    # Anyone to notify of status change?
                    
                    if newBaStatus in ['Merged - Notifying Originator',
                                       'Merged - Testing by Originator']:
                        self.sfb.setLog('setBA:%s Ready to notify %s CR Originator for cr:%s'%(self.branch, action, crNum),'info')
                        info = {'status':newBaStatus, 'role':role,
                                'actor':ownerId, 'tbId':updTbId}
                        notify[baId]=info

        """for baId in extraBAs:
            self.sfb.setLog('setBA:%s DELETING Extra aeBA:%s'%(self.branch, baId),'warn2')
            self.sfb.delete([baId])"""
                
        return notify
    # end setBA AE


    def buildPartitionFileComment(self, partInfoList):
        partNames = {}
        mFileBuf = StringIO.StringIO()
        for mFile in partInfoList:
            partNames[mFile.get('partition')] = mFile.get('partition')
            mFileBuf.write('User: %s\n' %mFile.get('user'))
            mFileBuf.write('%s (%s)\n' %(mFile.get('file'),
                                         mFile.get('partition')))
            mFileBuf.write('\n')
            continue
        
        # build a list of partition names for this reviewer
        partNamesList = partNames.keys()
        partNamesList.sort()
        
        return partNamesList, mFileBuf.getvalue()
    ## END buildPartitionFileComment
    

    ######################################################################################################
    #  Quick checks of main states using info set above
    ######################################################################################################
    def readyForSCM(self, status=None):
        """ check if branch now ready for SCM, return True or False"""
        ret = False
        if status in [None,'']:
            tbInfo = self.getData('Task_Branch__c')
            status = tbInfo.get('Branch_Status__c','')
        statMap = self.sfb.getStatMap(status,{})   # statMap = {'order':36.0, 'role':'dev'}
        statOrder = statMap.get('order')
        if statOrder > 35.9 and statOrder < 45.0:
            ret = True
        return ret
    
    def getNextApprovalRole(self, status=None):
        """ return the role shortcut of the next role that needs approval """
        if status in [None,'']:
            tbInfo = self.getData('Task_Branch__c')
            status = tbInfo.get('Branch_Status__c','')
        statMap = self.sfb.getStatMap(status,{})   # statMap = {'order':36.0, 'role':'dev'}
        statOrder = statMap.get('order')
        if statOrder <= 32.9: ret = 'dev'
        elif statOrder > 32.9 and statOrder < 33.8: ret = 'part'
        elif statOrder > 33.7 and statOrder < 34.2: ret = 'mgr'
        elif statOrder > 34.1 and statOrder < 35.2: ret = 'pe'
        elif statOrder > 35.1 and statOrder < 53.0: ret = 'scm'
        elif statOrder > 53.9 and statOrder < 70.0: ret = 'ae'
        else:    ret = 'dev'
        # change to full role name?
        return ret

        # another more expensive way not used, the road not traveled
        baDataList = self.getData('Branch_Approval__c')
        for baInfo in baDataList:
            if baInfo in [None,'',{},[]]:
                print 'WARN: no know Branch approval items'
                continue
            baRole = baInfo.get('Approval_Role__c','')
            baAppr = self.sfb.getId18(baInfo.get('OwnerId',''))
            status = baInfo.get('Status__c')
            baId   = self.sfb.getId18(baInfo.get('Id',''))       
            order  = baInfo.get('Order__c')


    def isRejected(self, status=None):
        """ need to finish this """
        ret = False
        if status in [None,'']:
            tbInfo = self.getData('Task_Branch__c')
            status = tbInfo.get('Branch_Status__c','')
        statMap = self.sfb.getStatMap(status,{})   # statMap = {'order':36.0, 'role':'dev'}
        statOrder = statMap.get('order')
        if statOrder > 31.0 and statOrder < 33.0:
            ret = True
        return ret

    def getStatOrder(self, status=None):
        """ need to finish this """
        ret = False
        if status in [None,'']:
            tbInfo = self.getData('Task_Branch__c')
            status = tbInfo.get('Branch_Status__c','')
        statMap = self.sfb.getStatMap(status,{})   # statMap = {'order':36.0, 'role':'dev'}
        statOrder = statMap.get('order')
        return statOrder
        


    ######################################
    def getBaId(self, userId, role):
        """ Find the baId given the role and approverID """
        sfIds = self.baRoleMap[role].get('sfids',[])
        ids = self.baRoleMap[role].get('ids',[])
        if userId not in ids:
            self.sfb.setLog('getBaId: %s in %s NOT Found %s in userIds:%s -> baId:%s '%(role, self.branch, userId, ids, sfIds),'error')
            return
        idIndex = ids.index(userId)
        if len(sfIds) > idIndex:
            return sfIds[idIndex]
        self.sfb.setLog('getBaId: %s in %s NOT Found %s in userIds:%s -> baId:%s '%(role, self.branch, userId, ids, sfIds),'error')
        return ''
        
    def getBaIdByRole(self, apprId, role):
        """ query local data to get Branch Approval ID for appr UserId and role 
             Not used as of July 7th, 2004
        """
        for baInfo in self.getData('Branch_Approval__c'):
            if baInfo.get('Approval_Role__c','') == role:
                if baInfo.get('OwnerId','') == apprId:
                    return baInfo.get('Id','')
        return ''

    def getBaIdByCrNum(self, crNum, role):
        """ query local data to get branch approval ID for case number and role
        """
        baId = ''
        #crNum=str(crNum)
        try:
            crNum = crNum.lstrip('0')
        except Exception, e:
            self.sfb.setLog('error in function getBaIdByCrNum %s err:%s'%(Exception,e))
        
        for baInfo in self.getData('Branch_Approval__c'):            
            #print "BAR INFO %s" %baInfo
            if baInfo not in ['',None,{},[]]:
                try:                    
                    myBaId = baInfo.get('Id','')                    
                    baRole = baInfo.get('Approval_Role__c','')
                    crList = self.getBranchApprovalCRList(myBaId)                    
                    if baRole == role and str(crNum) in crList:                        
                        baId = baInfo.get('Id','')                        
                        pass
                except Exception, e:
                    self.sfb.setLog('error in function getBaIdByCrNum %s err:%s'%(Exception,e))
            continue
        return baId

    def getBaIdByComponent(self, comp, role):
        """ query local data to get branch approval ID for component and role
        """
        baId = ''
        comp = comp.lower()
        for baInfo in self.getData('Branch_Approval__c'):
            # build list of non-padded case nums
            baRole = baInfo.get('Approval_Role__c','')
            baComp = baInfo.get('Component__c','').lower()
            if baRole == role and comp == baComp:
                baId = baInfo.get('Id','')
                pass
            
        return baId
            
    def getBaById(self, baId):
        """ query local data to get branch approval ID for component and role
        """
        for baInfo in self.getData('Branch_Approval__c'):
            if baInfo not in ['',None,{},[]]:
                try:
                    myBaId = baInfo.get('Id','')
                    if baId == myBaId:
                        return baInfo
                except Exception, e:
                    print 'error in function getBaById %s err:%s'%(Exception,e)
        return {}


            
    def getBaByIdInTb(self, baId, tbId):
        """ query local data to get branch approval ID for component and role
        """
        where = [['Task_Branch__c','=',tbId]]
        BAs = self.sfb.query('Branch_Approval__c', where=where, sc='all')
        for baInfo in BAs:
            if baInfo not in ['',None,{},[]]:
                try:
                    myBaId = baInfo.get('Id','')
                    if baId == myBaId:
                        return baInfo
                except Exception, e:
                    print 'error in function getBaByIdInTb %s err:%s'%(Exception,e)
        return {}
        return {}


            
    def setBaRoleMap(self):
        """ Use Branch Approval information to set a baRoleMap and return the map
            - format baRoleMap = {'dev':{'ids':[],'sf:'','sfids':[], 'status':'', 'order':30.0}
                                 ,'mgr': ... }
            sfids = branchApprovalIDs
            ids   = userIDs of the approver/owner of BA
        """
        baRoleMap = {'dev':{'ids':[],'sfids':[],'sf':'Developer', 'crList':[]},
                     'mgr':{'ids':[],'sfids':[],'sf':'Engineering Manager', 'crList':[]},
                     'part':{'ids':[],'sfids':[],'sf':'Partition Reviewer', 'crList':[]},
                     'pe': {'ids':[],'sfids':[],'sf':'Product Engineer', 'crList':[]},
                     'team': {'ids':[],'sfids':[],'sf':'Team Manager', 'crList':[]},
                     'scm':{'ids':[],'sfids':[],'sf':'SCM', 'crList':[], 'status':[]},
                     'ae': {'ids':[],'sfids':[],'sf':'CR Originator', 'crList':[], 'crInfo':{}}}

        baDataList = self.getData('Branch_Approval__c')
        for baInfo in baDataList:
            if baInfo in [None,'',{},[]]:
                print 'WARN: no know Branch approval items'
                continue
            baRole = baInfo.get('Approval_Role__c','')
            baAppr = self.sfb.getId18(baInfo.get('OwnerId',''))  #problems with case insensetive Queries
            status = baInfo.get('Status__c')
            baId   = self.sfb.getId18(baInfo.get('Id',''))       
            order  = baInfo.get('Order__c',0)
            crList = self.getBranchApprovalCRList(baId)  # needed?
            if baRole == 'Developer':         
                baRoleMap['dev']['ids'].append(baAppr)
                baRoleMap['dev']['sfids'].append(baId)
                baRoleMap['dev']['status'] = status
                baRoleMap['dev']['order'] = order
                baRoleMap['dev']['crList'] = crList    # need a merge list method!!!
            elif baRole == 'Engineering Manager': 
                baRoleMap['mgr']['ids'].append(baAppr)
                baRoleMap['mgr']['sfids'].append(baId)
                baRoleMap['mgr']['status'] = status
                baRoleMap['mgr']['order'] = order
                baRoleMap['mgr']['crList'] = crList
            elif baRole == 'Partition Reviewer': 
                baRoleMap['part']['ids'].append(baAppr)
                baRoleMap['part']['sfids'].append(baId)
                baRoleMap['part']['status'] = status
                baRoleMap['part']['order'] = order
                baRoleMap['part']['crList'] = crList
            elif baRole == 'Product Engineer':  
                baRoleMap['pe']['ids'].append(baAppr)
                baRoleMap['pe']['sfids'].append(baId)
                baRoleMap['pe']['status'] = status
                baRoleMap['pe']['order'] = order
                baRoleMap['pe']['crList'].extend(crList)
            elif baRole == 'Team Manager':  
                baRoleMap['team']['ids'].append(baAppr)
                baRoleMap['team']['sfids'].append(baId)
                baRoleMap['team']['status'] = status
                baRoleMap['team']['order'] = order
                baRoleMap['team']['crList'] = crList
            elif baRole == 'SCM':               
                baRoleMap['scm']['ids'].append(baAppr)
                baRoleMap['scm']['sfids'].append(baId)
                baRoleMap['scm']['status'].append(status)
                baRoleMap['scm']['order'] = order
                baRoleMap['scm']['crList'] = crList
            elif baRole == 'CR Originator':     
                baRoleMap['ae']['ids'].append(baAppr)
                baRoleMap['ae']['sfids'].append(baId)
                baRoleMap['ae']['status'] = status
                baRoleMap['ae']['order'] = order
                # should only be one CR per BA for AE                
                if len(crList) > 1:                                       
                    self.sfb.setLog('baRoleMap Found multiple CRs in aeBA %s'%(crList),'error')
                    
                if len(crList) > 0: 
                    baRoleMap['ae']['crList'].append(crList[0])
                    baRoleMap['ae']['crInfo'][crList[0]] = baId       # crNum -> aeBaId
            else:
                self.sfb.setLog('baRoleMap: %s Unknown Branch approval role ->%s<- found in \n%s' %(self.branch,baRole,baInfo),'warn')
                        
        return baRoleMap
                

    def getBranchApprovalCRList(self, id):
        """ get existing CR list of id of Branch_Approval__c """
        if id in [None,'']: return []
        baData = self.getData('Branch_Approval__c', id)
        crStr = baData.get('CR_List__c','')
        crNums = crStr.split(',')           # could be list of empty string ['']
        crNums = uniq(crNums)
        if crNums[0] == '': crNums.pop(0)
        newCrNums = []
        for crNum in crNums:
            crNum=crNum.strip()            
            #newCrNums.append(crNum.lstrip('0'))
            newCrNums.append(crNum)        
        return newCrNums

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

    def delCRFromTaskBranch(self, delCrNum):
        """ Remove a CR Link and related aeBA & peBA
            - also remove crNum from crList in devBAs & mgrBAs
            - all TB info must be loaded in self.data using loadBranch()
            - returns 0 or 1 if done correctly
        """
        updated = False
        if self.loadFromSF: tbData = self.getData()
        else:               tbData = self.getSFData( branch, stream, show=False)
        tbInfo = tbData.get('Task_Branch__c')
        tbId = tbInfo.get('Id')
        clList = tbData.get('Branch_CR_Link__c')
        baList = tbData.get('Branch_Approval__c')
        crNums = []
        clMap = {}
        for clInfo in clList:
            crId = clInfo.get('Case__c')
            clId = clInfo.get('Id')
            crNum = self.sfb.getCrNumByCrId(crId)
            comp = clInfo.get('Component__c')
            clMap[crNum] = {'comp':comp, 'clId': clId, 'crId':crId}
            if crNum not in crNums:
                crNums.append(crNum)
                
        if delCrNum not in crNums:
            print ' The CR %s is not linked to the branch %s in code stream %s'%(crNum, self.branch, self.stream)
            return 0
        if tbId in [None,'']:
            print 'Bad Mojo, trying to unlink a CR from an unknown Task Branch, tbData:%s'%tbData
            return 0
            
        info = clMap.get(delCrNum)
        comp = info.get('comp')
        clId = info.get('clId')
        ret = self.sfb.delete([clId])
        if ret in self.badInfoList:
            print 'Error Not able to delete Link to CR %s from Task Branch %s'%(crNum, tbId)
            return 0
        del clMap[delCrNum]            
        if 1:       # this needs to be fixed!!
            # delete all the BAs
            delIds = []
            baList = self.getData('Branch_Approval__c')
            for baInfo in baList:
                if baInfo in [None,'',{},[]]:continue
                baId = baInfo.get('Id','')
                crStr = baInfo.get('CR_List__c')
                role = baInfo.get('Approval_Role__c')
                if crStr not in [None,''] and role in ['CR Originator']:
                    crList = crStr.split(',')
                    cleanCrList = []
                    for crNum in crList:
                        cleanCrList.append(crNum.lstrip('0'))
                        continue
                    
                    if delCrNum in cleanCrList:
                        delIds.append(baId)
                elif len(clMap) == 0:           # no linked CRs so delete all
                    delIds.append(baId)
            if len(delIds) > 0:
                ret = self.sfb.delete(delIds)
                if self.debug>0:print 'Cleaned up old BAs %s'%ret
        else:
            num = self.setCRListOnBAs(tbId, crNums)
            return num
        
        
    def setCRListOnBAs(self, tbId, crNums):
        """ reset the CRList of all the dev, mgr, pe, and scm Branch approvals """
        if crNums in [None,'',[]]: return 0        
        self.baRoleMap = self.setBaRoleMap()    
        num = 0
        for role in ['dev','mgr','pe','scm']:    # extend for Customer?
            roleMap = self.baRoleMap.get(role)
            roleBaIds = roleMap.get('sfids')
            if role == 'dev':
                for baId in roleBaIds:
                    sfId = self.setBranchApproval( baId, tbId=tbId, data={}, crNums=crNums)
                    if sfId == baId: num +=1
            elif role == 'mgr':
                for baId in roleBaIds:
                    sfId = self.setBranchApproval( baId, tbId=tbId, data={}, crNums=crNums)
                    if sfId == baId: num +=1
            elif role == 'pe':
                for baId in roleBaIds:
                    sfId = self.setBranchApproval( baId, tbId=tbId, data={}, crNums=crNums)
                    if sfId == baId: num +=1
            elif role == 'scm':
                for baId in roleBaIds:
                    sfId = self.setBranchApproval( baId, tbId=tbId, data={}, crNums=crNums)
                    if sfId == baId: num +=1
            else:
                continue
        return num

    ######################################################################
    #  methods to set specifc parts of the TaskBranch composite object,
    #  remember to pass in existing ID
    ######################################################################
    def setTaskBranch(self, id='', branch='', stream='', data={}, numCRs=None, datamerge='passedOnly' ):
        """ update a Task Branch object with minimal fields 
            Other fields can be set using passed in data dictionary
        """
        pdata = data
        data = self.getData('Task_Branch__c')

        if datamerge == 'passedPlus':
            pdata.update(data)
            data = pdata
        elif datamerge == 'passedOnly':
            data = pdata
        else:
            data.update(pdata) # should command line override
        
        if data.has_key('Task_Branch__c'):
            print '\nsetData:%s\npassed:%s'%(data,pdata)
            del data['Task_Branch__c']
            print '\nDelete the bad Task_Branch__c element '
            
        if id != '':
            data['Id'] = id
        if branch not in [None,'']:
            data['Name'] = branch
            data['Branch__c'] = branch
        if stream not in [None,'']:
            # CV Sept 30,2004 - Will not effect existing streams so...
            # Strip 'blast' from stream until all streams have product prepended
            stream = str(stream)
            if stream.lower().find('blast') != -1:
                stream = stream[5:]
            data['Code_Stream__c'] = stream
            
        if numCRs not in [None,'']:
            data['Num_CRs__c'] = numCRs
        
        if id == '':
            res = self.sfb.create('Task_Branch__c',data)
            mode = 'Created'
        else:
            res = self.sfb.update('Task_Branch__c',data)
            mode = 'Updated'

        if res in self.badInfoList:
            if self.debug >0: print 'ERROR: %s Task Branch, %s %s %s'%(mode,stream,branch,res)
            return ''
        id = res[0]
        data['Id'] = id
        self.setData({'Task_Branch__c':data})
        if self.debug >1: print '%s Task Branch, %s %s %s CR at https://na1.salesforce.com/%s'\
                                            %(mode,stream,branch,data.get('Num_CRs__c'),id)
        return id
    



    def setBranchAction(self, baId, action, status=None):
        """ just set the status and approval fields, assume BA exists """
        data = {'Approve__c':action}
        if status not in [None,'']:
            data['Status__c'] = status
        ret = self.setBranchApproval(baId, tbId='', data=data)
        return ret


    def evalBranchApprovalUpdate(self, id, tbId, status='', date=None, data={},
                                 crNums=[], teamId=None):
        """
        Check to see if a proposed change to a branch approval will really update the BA.
        If so, returns True. If no changes will be made, returns False.
        """
        willChange = False

        if id in self.badInfoList:
            # no ID - will trigger insert.
            willChange = True

        else:
            baData = self.getData('Branch_Approval__c',id)

            # check the special fields first
            if status not in [None,''] and status != baData.get('Status__c',''):
                msg = 'evalBAUpdate: baId %s changing status from "%s" to "%s"' \
                      %(id, baData.get('Status__c',''), status)
                #print msg
                self.sfb.setLog(msg, 'debug2')
                willChange = True

            #if crNums not in [None,[]] and ','.join(crNums) != baData.get('CR_List__c',''):
            if crNums not in [None,[]] and crNums != baData.get('CR_List__c',''):
                #msg = 'evalBAUpdate: baId %s changing cr list from "%s" to "%s"' \
                #      %(id, baData.get('CR_List__c',''), ','.join(crNums))
                #print "CR NUMBERS %s" %crNums
                #print "CR Lists %s" %baData.get('CR_List__c','')
                msg = 'evalBAUpdate: baId %s changing cr list from "%s" to "%s"' \
                      %(id, baData.get('CR_List__c',''),baData.get('CR_List__c',''))
                #print msg
                self.sfb.setLog(msg, 'debug2')
                willChange = True
                
            if teamId not in [None,''] and teamId != baData.get('Team_Branch__c',''):
                msg = 'evalBAUpdate: baId %s changing Team_Branch__c to "%s"' \
                      %(id, teamId)
                #print msg
                self.sfb.setLog(msg, 'debug2')
                willChange = True

            if date not in [None,''] and date != baData.get('Date_Time_Actioned__c',''):
                # if we're providing a new actioned datetime, assume we're changing
		if baData.get('Approval_Role__c','') not in ['','SCM']:
	            msg = 'evalBAUpdate: baId %s changing actioned datetime from "%s" to "%s"' \
        	          %(id, baData.get('Date_Time_Actioned__c',''), date)
                    #print msg
	            self.sfb.setLog(msg, 'debug2')
        	    willChange = True

            # now check the passed data dictionary.
            for key in data.keys():
                # pass on the Approve field - this won't trigger a change if it's the only field
                # being that's been changed.
                #if key == 'Approve__c':
                #    continue                
                try:
                
                    if str(data[key]).strip() != str(baData.get(key, '')).strip():
                        msg = 'evalBAUpdate: baId %s change detected on key %s - have "%s", saw "%s"' %(id, key, baData.get(key, ''), data[key])
                        #print msg
                        self.sfb.setLog(msg, 'debug2')
                        willChange = True
                
                except :
                    if str(data[key].encode("ascii", "ignore") ).strip() != str(baData.get(key, '').encode("ascii", "ignore") ).strip():
                        msg = 'evalBAUpdate: baId %s change detected on key %s - have "%s", saw "%s"' %(id, key, baData.get(key, ''), data[key])
                        #print msg
                        self.sfb.setLog(msg, 'debug2')
                        willChange = True
                    
                    

        return willChange
    ## END evalBranchApprovalUpdate
                
    def setBranchApproval(self, id, tbId, status='', date=None, data={},
                          crNums=[], teamId=None, setAll=True):
        """ update a Branch approval object, return baId or ''
        """
        crNums.sort()
        
        # see if we even need an update...
        needsUpdate = self.evalBranchApprovalUpdate(id, tbId=tbId, status=status, date=date, data=data, crNums=crNums, teamId=teamId)
        if needsUpdate is False:
            self.sfb.setLog('setBA: no changes detected for baId %s - skipping' %id, 'info2')
            return id
        else:
            self.sfb.setLog('setBA: updating baId %s' %id, 'info3')
            
        # get existing BA data if any
        if id not in self.badInfoList:
            baData = self.getData('Branch_Approval__c',id)
        else:
            baData = {}

        # get the old status.
        baStat = baData.get('Status__c','')

        if data in [None,'',{}]:
            if setAll:
                data = baData
            else:
                data = {}

        if status not in [None,'']:
            data['Status__c'] = status
            
        if crNums not in [None,[]]:
            # uniquify the list? 
            temp=[]  
            for val in crNums:
                sval=repr(val)
                temp.append(sval)
            pass         
            #data['CR_List__c'] = ','.join(crNums)
            data['CR_List__c'] = ','.join(temp)

        if teamId not in [None,'']:                 # only for new ???
            data['Team_Branch__c'] = teamId

        if date in [None] and baStat != status and status != 'Submitted to SCM':
            # No actioned date was provided, but see if we need to set the actioned
            # datetime because the status is changing.
            dt = self.sfb.checkDate('now', 'setBranchApproval')
            if dt in [None,'']: print 'checkDate is not working--------------'
            data['Date_Time_Actioned__c'] = dt
            
        elif date not in [None]:
            # an explicit actioned datetime was passed in - honor it.
            dt = self.sfb.checkDate(date, 'setBranchApproval')
            if dt in ['']: dt = self.sfb.checkDate('now', 'setBranchApproval')
            if dt in [None,'']: print 'checkDate is not working--------------'
            data['Date_Time_Actioned__c'] = dt

        if data.has_key('Order__c'):
            ord = data.get('Order__c')
            if type(ord) != type(1.0):
                self.sfb.setLog('setBA: found order of wrong type %s %s'%(ord,type(ord)),'warn2')
                ord = float(ord)
                data['Order__c'] = ord
        
        mode = 'Updated'
        res = ''
        if id == '':
            if tbId is not None:
                # allow for team-branch-only BAs
                data['Task_Branch__c'] = tbId            
            res = self.sfb.create('Branch_Approval__c',data)            
            mode = 'Created'
        else:
            data['Id'] = id
            res = self.sfb.update('Branch_Approval__c',data)
            
            
        if res in self.badInfoList:
            if self.debug >0: print 'ERROR: %s Branch Approval, tbid:%s %s'%(mode,tbId,res)
            self.sfb.setLog('setBranchApproval data:%s\n ret:%s\n'%(data,self.sfb.lastRet),'error')
            return ''
        id = res[0]
        data['Id'] = id

        self.setData({'Branch_Approval__c':data})
        
        if self.debug >1: print '%s Branch Approval, %s %s for %s %s'%(mode,data.get('Approval_Role__c'),self.stream,self.branch, crNums)
        if self.debug >2: print '%s Branch Approval, tbid:%s %s %s %s'%(mode,tbId,self.branch,id,res)
        return id


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
        
        
    #######################################################################
    #  MAIN status change method called from submitBranch, approveBranch,
    #  etc.. plus email sending
    #######################################################################
    def submitAndNotify(self, status, st=0, partData=None):
        """ set status on branch to trigger state change 
            MUST have self.branch, stream set and self.data loaded use self.loadBranch(branch,stream)
        """
        # try to get same info for team branch....
        if self.branchType == 'team':
            tbInfo = self.getData('Team_Branch__c')
            if tbInfo in self.badInfoList:
                print 's&N TEAM branch data not loaded %s status:%s'%(tbInfo,status)
                return -1, {}
            tbId   = tbInfo.get('Id')
            tbStatus = tbInfo.get('Status__c')
        else:
            tbInfo = self.getData('Task_Branch__c')
            if tbInfo in self.badInfoList:
                print 's&N TASK branch data not loaded %s status:%s'%(tbInfo,status)
                return -1, {}
            tbId   = tbInfo.get('Id')
            tbStatus = tbInfo.get('Branch_Status__c')
        
        print ' Actioning a %s branch with status %s'%(self.branchType,tbStatus)
        #try: 
        if 1:
            # I think we should be getting something back here...
            notify = self.setBranchApprovalStatus(status, st, partData=partData)
            updated = self.setBranchStatusCL(status)    

            if len(notify) == 0: # need to coordinate status values to get right values here
                msg = 's&N: %s %s has no actions for status:%s -> %s'%(self.branch,self.stream,tbStatus, status)
                self.sfb.setLog(msg,'info')
                if self.debug>1:print msg
                #return 0, {}
            if self.debug>0:print '  %.4s Set branch %32s to status %s'%((time.time()-st), self.branch, status)
            # notify = {baId:info}
            # info = {'status':status, 'role':role, 'actor':ownerId, 'tbId':tbId}
            sendTo = {}
            for baId, info in notify.items():
                info['baId'] = baId
                actor  = info.get('actor')
                sendTo[actor] = info

            num = len(sendTo)
            for actor, info in sendTo.items():
                stat = info.get('status')
                role   = info.get('role')
                actor  = info.get('actor')
                
                if self.debug>1:
                    print 's&N: %.4s sending to %s'%((time.time()-st),actor)

                if actor in ['scm']:
                    sent = self.postSCMTokenAndNotify()
                else:
                    sent = self.sendNotifyEmail(actor)

                msg = 'Sent %s Notify message for %s'%(role,stat)
                msg += ' to %s with ret:%s'%(actor,sent)
                self.sfb.setLog(msg,'info')

                if self.debug>1:
                    print 's&N: %.4s sent %s'%((time.time()-st),sent)
                
            return num, notify
        try: pass
        except Exception, e:
            # backout of status change?
            print 'submitAndNotify %s err:%s'%(Exception,e)
            print '  Backing out status from %s backTo-> %s'%(status,tbStatus)
            notify = self.setBranchStatus(tbStatus, st)
        return 0,{}
            

    def sendNotifyEmail(self, baUid=None, validStat=None):
        """  This method generates a notification for any branch status change.
        """
        if baUid in [None,'']: baUid = self.sfb.uid
        if validStat in [None,'',[]]:
            validStat = ['Requires Approval','Approving','Submitted to SCM','Merged - Notifying Originator']
        hideStat = ['Pending Merged Fix','Pending Submission','Pending Fix',
                    'Awaiting Task Branch', 'Task Branch Ready',
                    'Team Approving']
        approved = ['Approve']  # ['Approved','Rejected','Approve','Reject']
        tbInfo = self.getData('Task_Branch__c')
        clList = self.getData('Branch_CR_Link__c')
        baList = self.getData('Branch_Approval__c')
        
        tbId   = tbInfo.get('Id')
        status = tbInfo.get('Branch_Status__c','')
        stream = tbInfo.get('Code_Stream__c','')
        branch = tbInfo.get('Name')

        toInfo = self.sfb.getUserById(baUid)
        uemail = toInfo.get('Email','')

        if stream[:1] in ['3','4','5']:
            stream = "blast%s" %stream
        tbBand = '%s in %s\n'%(branch,stream)
        tbBand += 72*'='+'\n'
        tbBand += '   status:%s  with priority:%s\n'%(status, tbInfo.get('Branch_Priority__c'))
        tbBand += '   https://na1.salesforce.com/%s\n'%tbId
        highRisk = tbInfo.get('High_Risk__c',False)
        if highRisk == True:
            tbBand += 'High Risk Branch:  %s\n'%(tbInfo.get('Risk_Details__c'))
        comChg = tbInfo.get('Command_Change__c',False)    
        if comChg == True:
            tbBand += 'Command Change:  %s\n'%(tbInfo.get('Command_Change_Details__c'))
        tbBand += '   \n'
        
        role= 'Developer'
        preSubj = 'SF notify only:'
        baLine = 'You have the following approval records for this branch:\n'
        for baInfo in baList:
            ownerId = baInfo.get('OwnerId')
            stat = baInfo.get('Status__c')
            appr = baInfo.get('Approve__c')
            if baUid == ownerId and appr not in approved and stat not in hideStat:  #and stat in validStat 
                role = baInfo.get('Approval_Role__c')
                preSubj = 'SF Approval: %s '%role
                baLine += '  Status:%s  Your Role:%s\n'%(stat,role)
                baLine += '  Subject:%s\n'%(baInfo.get('Name'))
                baLine += '  for CRs %s\n'%(baInfo.get('CR_List__c'))
                baLine += '  https://na1.salesforce.com/%s\n\n'%baInfo.get('Id')
        
        crBand = '\nThis branch addresses the following CRs:\n'
        for clInfo in clList:
            crId   = clInfo.get('Case__c')
            crInfo = self.sfb.getCrById(crId)
            name = crInfo.get('Subject','')
            comp = crInfo.get('Component__c','')
            crNum = '%s'%int(crInfo.get('CaseNumber',0))
            streams = crInfo.get('Code_Streams_Priority__c','')
            crStat  = crInfo.get('Status')
            crBand += '  %s needs fixes in streams:%s for component:%s \n'%(crNum,streams,comp)
            crBand += '  Subject:%s\n'%(name)
            crBand += '  https://na1.salesforce.com/%s\n\n'%crId

        msgBody = '%s%s%s'%(tbBand,baLine,crBand)
        if uemail in [None,'']:
            errmsg = 'No Email found in uInfo for user Id %s:%s' %(toInfo,
                                                                   baUid)
            self.sfb.log(errmsg, 'warn')
            uemail = ['kshuk@molten-magma.com']
        else:
            uemail = [uemail]
            
        #uemail = ['kshuk@molten-magma.com', 'chip@molten-magma.com']                #debug, remove

        if self.readyForSCM(status):
            postSubj = '%s %s has been submitted to SCM.'%(self.branch, self.stream)
        elif self.isRejected(status):
            preSubj = 'SF Rejected: Dev'
            postSubj = '%s %s has been Rejected back to Developer'%(self.branch, self.stream)
        elif role in ['Developer']:
            postSubj = '%s %s has been linked for Fixing'%(self.branch, self.stream)
        else:
            #role should be in ['Engineering Manager','']
            postSubj = '%s %s has been submitted for Approval'%(self.branch, self.stream)
        subject = '%s %s' %(preSubj, postSubj)    
        
        msg = self.sendMsg(uemail, subject, msgBody)
        return msg
    
    
    def sendMsg(self, toAddrs, subject, body):
        """ do the actual sending of the message 
        """
        if self.sfb.adminInfo:  fromAddr = self.sfb.adminInfo.get('mail')
        else:                   fromAddr = 'salesforce-support@molten-magma.com'

        if self.debug > 2: toAddrs = self.sfb.trialAddrList
        #toAlias = getAliasString(toAddrs) # should now call mailServer function, imported by sforceBase
        if self.debug>0:print ' Sending mail to %s'%','.join(toAddrs)
        try: pass
        except Exception,e:
            print '%s getToErr:%s'%(Exception,e)
        
        msgTxt  = self.sfb.mailServer().setEmailTxt(fromAddr, toAddrs, subject, body)
        msgStat = self.sfb.mailServer().sendEmail(fromAddr, toAddrs, msgTxt, subject)
        msg = self.sfb.mailServer().getSendResults(subject, toAddrs, msgStat)
        self.sfb.setLog('%s'%msg, 'info')
        return msg
  
    def updateSFonSubmitToSCM(self):
        """ set the TB status """
        status = 'Submitted to SCM'
        updated = self.setBranchStatus(status)
        if not updated:
            self.sfb.setLog('updateSFonSubmitToSCM: did not update anything with setBranchStatus(%s)'%status,'error')
        return 0
        
    def postSCMTokenAndNotify(self, type='task'):
        """ collect all the iformantion about this Branch and write token file
            assume that that self.getData() will have all correct Branch data
        """
        toAddrs = ['sf_scm@molten-magma.com']
        if self.debug > 1:   toAddrs.extend(self.sfb.trialAddrList)
        elif self.debug > 2: toAddrs = self.sfb.trialAddrList
        #toAddrs = ['kshuk@molten-magma.com']  # remove for production

        if self.branchType != type:
            print 'postSCMTokenAndNotify: Error the entity thinks it is %s while passed is %s'%(self.branchType,type)
            type = self.branchType
        tokenMsg = ''
        
        tokenMsg = self.getBranchInfo(toAddrs, 'token')

        sf_scm  = os.path.join(tokenFile.scm_rootDir, 'sf-scm')
        sf_drop = os.path.join(tokenFile.scm_dropDir, 'sf-scm')
        subject = 'Stream:%s Branch %s submitted to SCM' % (self.stream, self.branch)
        crList = self.getCRList()
        numCRs = len(crList)
        
        tokenFileNames = tokenFile.formTokenNames(self.branch, crList)
        self.sfb.setLog('SubmitToSCM %s CRs %s'%(numCRs, crList),'info')
        e = ''
        for tokenFileName in tokenFileNames:
            brFileName = os.path.join(sf_scm, tokenFileName)
            brFileN2   = os.path.join(sf_drop, tokenFileName)
            self.sfb.setLog('SubmitToSCM ready to write %s CRs to file %s in %s'%(numCRs, tokenFileName, sf_scm),'info')
            if self.debug < 4:
                # Generate the SCM token file
                try:
                    self.writeTokenFile(brFileName, tokenMsg)
                except Exception, e:
                    self.sfb.setLog(' Failed to write SUBMIT to SCM file %s '%brFileName,'error') 
                    self.sfb.setLog(' Failed to write SUBMIT to SCM file %s, Please check permissions and hand create file'%brFileName,'error') 
                    self.sfb.setLog('First Try Path: %s err:%s %s'%(brFileName,Exception,e), 'error')
                    self.sfb.setLog('msg: %s \n'%tokenMsg,'error')
                else:
                    self.sfb.setLog('SCM Created %s token file %s'%(self.stream, brFileName ),'info')

                # Generate a shadow token file
                try:
                    self.writeTokenFile(brFileN2, tokenMsg)
                except Exception, e2:
                    self.sfb.setLog(' Failed to write SUBMIT to SHADOW SCM file %s '%brFileN2,'error') 
                    self.sfb.setLog(' Failed to write SUBMIT to SHADOW SCM file %s, Please check permissions and hand create file'%brFileName,'error') 
                    self.sfb.setLog('Second Try Path: %s err:%s %s'%(brFileName,Exception,e2), 'error')
                    self.sfb.setLog('msg: %s \n'%tokenMsg,'error2')
                else:
                    self.sfb.setLog('SCM Created %s SHADOW file %s'%(self.stream, brFileN2),'info')

        updated = False
        if e is not '':
            tokenMsg += '\tERROR with SCM file write:  %s\n' % (e)
            subject = 'Error %s'%subject
            msg ='the SCM file WAS NOT created nor was SalesForce updated'
            msg += 'The file content is:\n %s\n'%tokenMsg
            self.sfb.setLog(msg,'critical')
        else:
            try:
                updated = self.updateSFonSubmitToSCM()
                self.sfb.setLog('Updated Submit to SCM status %s'%updated,'info')
            except Exception, e:
                msg =' Failed to UPDATE SalesForce with Submit to SCM for %s %s'%( self.stream, self.branch )
                self.sfb.setLog(' %s   for %s branch:%s '%(msg,self.stream, self.branch),'error')
                proIDs = []

        sent = self.sendMsg(toAddrs, subject, tokenMsg)
        self.sfb.setLog('SCM mail sent to %s'%toAddrs,'info')

        return updated


    def writeTokenFile(self, pathName, tokenContent):
        """
        Method writes tokenContent to a file at path fileName and then
        sets the ownership and permissions of the file to something the
        SCM group can work with.

        Create directory path if necessary. Assumption is that
        /magma/scm-release/submissions is the base SCM dir, that it
        has already been created and that we have permissions to
        write to it. 
        """
        scmGID = grp.getgrnam('scm')[2]
        # test if directory is present
        tokDir, tokFile = os.path.split(pathName)

        # Make subdirs if necessary
        if not os.path.exists(tokDir):
            os.makedirs(tokDir)
            # Set the group ownership and mode of the directories to scm
            # kludgey because specifying mode to os.makedirs doesn't seem to
            # work and there is no recursive chown to set group ownership.
            stopdir = 'submissions'
            while True:
                try:
                    os.chown(tokDir, os.getuid(), scmGID)
                    os.chmod(tokDir, 0775)
                except Exception, e:
                    pass
                tokDir, discard = os.path.split(tokDir)
                if re.search(r'%s$' %stopdir, tokDir):
                    break
            
        brFile = open(pathName,'w')
        brFile.write(tokenContent.encode('ascii','replace'))
        brFile.close()
        # Set the necessary permissions and group ownership for the SCM group.
        os.chown(pathName, os.getuid(), scmGID)
        os.chmod(pathName, 0664)
    ## END writeTokenFile(self, fileName, tokenContent)
        
        
    def getBranchInfo(self, email='you', target='token'):
        """ return a text version of the branch info suitable
            for the SCM token and display at commandline
        """
        tbInfo = self.getData('Task_Branch__c')
        clList = self.getData('Branch_CR_Link__c')
        baList = self.getData('Branch_Approval__c')
        tbId   = tbInfo.get('Id')
        status = tbInfo.get('Branch_Status__c')
        stream = tbInfo.get('Code_Stream__c')
        branch = tbInfo.get('Name')
        brPath = tbInfo.get('Branch_Path__c')
        
        # heading Branch band
        tbBand  = 'Branch Information for %s follows:\n'%email + 72*'='+'\n'
        if stream[:5] != 'blast':
            stream = 'blast%s' %stream
        tbBand += '%s in %s\n'%(branch,stream)
        tbBand += '   Status:%s  with Priority:%s\n'%(status, tbInfo.get('Branch_Priority__c'))
        tbBand += '   https://na1.salesforce.com/%s\n'%tbId
        if brPath not in [None,'']:
            tbBand += '   Branch Path: %s\n'%brPath
        highRisk = tbInfo.get('High_Risk__c',False)
        if highRisk == True:
            tbBand += 'High Risk Branch:  %s\n'%(tbInfo.get('Risk_Details__c'))
        comChg = tbInfo.get('Command_Change__c',False)    
        if comChg == True:
            tbBand += 'Command Change:  %s\n'%(tbInfo.get('Command_Change_Details__c'))
        if tbInfo.get('Details__c') not in [None,'']:
            tbBand += 'Other Details:  %s\n'%(tbInfo.get('Details__c'))
        if tbInfo.get('Merge_Details__c') not in [None,'']:
            tbBand += 'Merge Details:  %s\n'%(tbInfo.get('Merge_Details__c'))
        
        crBand = '\nThis branch addresses the following CRs:\n'
        for clInfo in clList:
            crId   = clInfo.get('Case__c')
            crInfo = self.sfb.getCrById(crId)
            name = crInfo.get('Subject','')
            comp = crInfo.get('Component__c','')
            crNum = 'CR#: %s'%int(crInfo.get('CaseNumber',0))
            streams = crInfo.get('Code_Streams_Priority__c','')
            crStat  = crInfo.get('Status')
            crBand += '  Subject:%s\n'%(name)
            crBand += '  https://na1.salesforce.com/%s\n'%crId
            crBand += '  %s needs fixes in streams:%s for component:%s \n'%(crNum,streams,comp)
            crBand += '  CR Status:%s needs \n'%(crStat)
            crBand += '  Details:  %s\n\n'%(clInfo.get('Details__c'))

        msgBody = '%s%s'%(tbBand,crBand)
        return msgBody
        

    ######################################################################
    #  MOD specific Methods, analogous methods are includes above what
    #  do not rely on MODs
    ######################################################################

    def getModData(self, branchLabel, stream='4', overwrite=True, show=True):
        """ Load data from all (branchlabel/codestream) MODs into object data """
        modList = self.sfb.getMODs(branchLabel, stream)
        if show: self.showData(modList, 'Task')
        self.modList = modList
        return modList


    def getRightPriority(self, modPrior, priority):
        """ use passed modPriority to potentially updated
            final priority"""
        modPrior = modPrior.lower()
        if modPrior.find('expedite') != -1: 
            priority = 'expedite'
        elif modPrior.find('high') != -1:     
            if priority not in ['expedite']:
                priority = 'high'
        elif modPrior.find('normal') != -1:   
            if priority not in ['expedite','high']:
                priority = 'medium'
        elif modPrior.find('medium') != -1:   
            if priority not in ['expedite','high']:
                priority = 'medium'
        elif modPrior.find('low') != -1:      
            if priority not in ['expedite','high','medium']:
                priority = 'low'
        return priority
            

    ##################################################################################################
    #  Utilities ?
    ##################################################################################################
    def delTaskBranch(self, branch, stream):
        """ Remove a CR Link and related BAs then delete Task Branch
            - all TB info must be loaded in self.data using loadBranch()
            - returns 0 or 1 if done correctly
        """
        updated = False
        self.branch = branch
        self.stream = stream
        tbData = self.getSFData( branch, stream, show=False)
        tbInfo = tbData.get('Task_Branch__c')
        tbId = tbInfo.get('Id')
        if tbId in [None,'']:
            print 'Bad Mojo, trying to delete an unknown Task Branch, tbData:%s'%tbData
            return 0
            
        clList = tbData.get('Branch_CR_Link__c')
        ids = []
        for info in clList:
            id = info.get('Id')
            if id not in [None,'']:
                ids.append(id)
        ret = self.sfb.delete(ids)
        if ret in self.badInfoList:
            print 'Error Not able to delete CR Links %s from Task Branch %s %s'%(ids, branch, tbId)
            return 0
            
        baList = tbData.get('Branch_Approval__c')
        ids = []
        for info in baList:
            id = info.get('Id')
            if id not in [None,'']:
                ids.append(id)
        ret = self.sfb.delete(ids)
        if ret in self.badInfoList:
            print 'Error Not able to delete Branch Approvals %s from Task Branch %s %s'%(ids, branch, tbId)
            return 0

        ret = self.sfb.delete([tbId])
        if ret in self.badInfoList:
            print 'Error Not able to delete Task Branch %s %s'%(branch, tbId)
            return 0
        return 1


    ##################################################################################################
    #  dead ends?
    ##################################################################################################
    def setBranchApprovalFromActor(self, actor, action, status):
        """ Sets the branch approval records owner by the actor and involved in the action to the status
            action = ['EngMgr','ProdEng','Pending','SubmitToSCM','SCM_RedBuild','Origininator']
            ----Not implemented---
        """
        if action not in ['EngMgr','ProdEng','Pending','SubmitToSCM','SCM_RedBuild','Origininator']:
            print 'ERROR the action %s is not configured yet'
        branch = self.branch
        stream = self.stream
        if self.loadFromSF: tbData = self.getData()
        else:               tbData = self.getSFData( self.branch, self.stream, show=False)
        
        statOrder = self.sfb.getStatMap(status,{}).get('order',0)
        
        newBAList = []
        for baInfo in tbData.get('Branch_Approval__c'):
            role   = baInfo.get('Approval_Role__c')
            status = baInfo.get('Status__c')
            order  = baInfo.get('Order__c')
            if action in ['EngMgr']:
                pass
            elif action in ['ProdEng']:
                pass
            elif action in ['Pending']:
                pass
            elif action in ['SubmitToSCM']:
                pass
            elif action in ['SCM_RedBuild']:
                pass
            elif action in ['Origininator']:
                pass
            elif action not in ['EngMgr','ProdEng','Pending','SubmitToSCM','SCM_RedBuild','Origininator']:
                print 'Error unknown action %s, please stop asking'%action
            

    def setTBDetailsFromMod(self, modDesc, tbId, reset=True):
        """  Update the TaskBranch data in this object with information from the passed in MOD
             - MOD.comments     -> TB.Detail/detail2/detail3 + bit bucket for 2635 chars
             NOTE: This is not working right, some global var issue and not the right approcah anyway
        """
        tbInfo = self.getData('Task_Branch__c')
        len_desc = len(modDesc)

        if modDesc != '':
            tbDetails = tbInfo.get('Details__c','')
            len_d = 0
            if not reset:
                len_d = len(tbDetails)
            vstart = 0
            if len_d < 252: 
                vadd = modDesc[vstart:255-len_d]
                if tbDetails.find(vadd) == -1:
                    if not reset:
                        tbInfo['Details__c'] = '%s%s'%(tbDetails,vadd)
                    else:
                        tbInfo['Details__c'] = '%s'%(vadd)
                    #print '   Adding Details %s'%vadd
                    vstart = 255-len_d + 1
                    len_desc = len_desc - 255-len_d + 1
                else:
                    pass
                    #print '   Comment exists %s'%vadd
            tbDetails = tbInfo.get('Merge_Details__c','')
            len_d = 0
            if not reset:
                len_d = len(tbDetails)
            if len_d < 255: 
                vadd = modDesc[vstart:255-len_d]
                if tbDetails.find(vadd) == -1:
                    if not reset:
                        tbInfo['Merge_Details__c'] = '%s%s'%(tbDetails,vadd)
                    else:
                        tbInfo['Merge_Details__c'] = '%s'%(vadd)
                    #print '   Adding Merge Details %s'%vadd
                    vstart = 255-len_d + 1
                    len_desc = len_desc - 255-len_d + 1
                else:
                    pass
                    #print '   Comment exists %s'%vadd

            self.setData({'Task_Branch__c':tbInfo})
        else:
            pass
            #print '   No Comments found for %s'%tbInfo.get('Name')
        return len_desc


    def findInterestedPartyIds(self):
        """ By tracing back the CRs->components->dev teams->user links,
        find the user IDs of all interested parties for this task branch.
        """
        brCrLinkList = self.getData('Branch_CR_Link__c')

        componentIdList = []
        for brCrLink in brCrLinkList:
            componentId = brCrLink.get('Component_Link__c')
            if componentId is not None and componentId not in componentIdList:
                componentIdList.append(componentId)
                pass
            continue
        
        # lookup the components to get product team IDs. 
        fields = ('Id', 'Product_Team__c')
        res = []

        if len(componentIdList) > 0:
            res = self.sfb.retrieve(componentIdList, 'Component__c', fields) 
            pass

        devTeamIdList = []
        for component in res:
            devTeamId = component.get('Product_Team__c')
            if devTeamId is not None and devTeamId not in devTeamIdList:
                devTeamIdList.append(devTeamId)
                pass
            continue

        # now, query the user links with Product_Team__c in list and role
        # of interested party.
        fields = ('Id', 'User__c')
        f1 = ['Link_Type__c','=','Interested Party']

        userLinkList = []
        while len(devTeamIdList):
            selectIds = devTeamIdList[:10]
            devTeamIdList = devTeamIdList[10:]
            
            refLookup = []
            for id in selectIds:
                refLookup.append(['Product_Team__c','=',id])
                refLookup.append('or')
                continue
            refLookup.pop() # nuke the last 'or'

            where = [f1, 'and', '(']
            where.extend(refLookup)
            where.append(')')

            ret = self.sfb.query('User_Link__c', where, fields)
            if ret not in BAD_INFO_LIST:
                userLinkList.extend(ret)
                pass
            continue

        # now extract a list of user IDs
        userIdList = []
        for userLink in userLinkList:
            userId = userLink.get('User__c')
            if userLink is not None and userLink not in userIdList:
                userIdList.append(userId)
                pass
            continue

        # may need to scan IP's preferences at this point as well.
        
        return userIdList
    ## END findInterestedPartyIds

    def getSubmittedDatetime(self):
        """ Returns the datetime object set to time this branch was submitted """
        # will format to DD-Mon-YY.HH:MM
        submittedDatetime = None

        devBa = {}
        baRoleMap = self.setBaRoleMap()
        devRoleMap = baRoleMap.get('dev')
        if devRoleMap is not None:
            baids = devRoleMap.get('sfids')
            if baids is not None and len(baids) > 0:
                devBaId = baids[0]

                devBa = self.getData('Branch_Approval__c', id=devBaId)
                pass
            pass

        actionedDateTimeStr = devBa.get('Date_Time_Actioned__c')
        if actionedDateTimeStr is not None:
            timeTup = self.sfb.getDateTimeTuple(actionedDateTimeStr)
            ts = time.mktime(timeTup) - (60*60*7)
            submittedDatetime = datetime.datetime.fromtimestamp(ts)
            pass

        return submittedDatetime
    ## END getSubmittedDatetime

    pass
## END class SFTaskBranch        
        
            

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
    def getLatestTB(self, secsAgo=60*60*24*5, show=False):
        """ get the Task Branch modified in the since secsAgo"""
        collect = {}
        actionNeeded = {}    # key as tbId value of action required
        fromSecs = time.time()-secsAgo
        dateStr = self.getAsDateTimeStr(fromSecs)
        where = [['OwnerId','!=',''],'and',['LastModifiedDate','>',dateStr]]
        queryList = self.query('Task_Branch__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'getLatestTB Result: NO Task Branch Found within the last %s secs'%secsAgo
            return collect
        result = []
        for info in queryList:
            result.append({'Task_Branch__c':info})
            if self.debug>3:print 'Found %25s \tupdated %s'%(info.get('Name'),info.get('LastModifiedDate'))
        print 'Found %s Task_Branches modified in the last %s hours'%(len(result),secsAgo/3600)
        return result

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


    def getBAUsers(self):
        """ just a test method to get all users of Branch Approvals"""
        res = []
        where = [['OwnerId','!=','']]
        queryList = self.query('Branch_Approval__c', where=where, sc='min')
        if queryList in self.badInfoList:
            print 'getBAUsers Result: NO Task Branch Found with non empty ownerId'
            return res
        for info in queryList:
            id = info.get('OwnerId')
            if id is not None and id not in res:
                res.append(id)
        return res


    def checkBAForAction(self, baInfo):
        """ check the fields in the Branch Approval object and decide if action is required
            return action key or ''
            THIS IS A DEAD END
        """
        if baInfo in [None,{},'']:
            return ''

        role   = baInfo.get('Approval_Role__c','')
        action = baInfo.get('Approve__c','')
        actor  = baInfo.get('OwnerId','')
        apprId = baInfo.get('Id','')
        status = baInfo.get('Status__c','')
        tbId   = baInfo.get('Task_Branch__c','')
        
        action = ''
        if role == 'dev':
            if status not in ['Fixing','Submitting','Submitted','Closed']:
                if status in ['Submitting']:
                    action = 'devBA has Submitted, Notify Manager'
            else:
                action = 'devBA has wrong status of: %s'%status
            
        elif role == 'mgr':
            if status not in ['Pending Submission','Requires Approval','Approving','Approved','Rejecting','Rejected']:
                if status in ['Approving']:
                    action = 'mgrBA has Approved, Notify PE'
                if status in ['Rejecting']:
                    action = 'mgrBA has Rejected, Notify Dev'
            else:
                action = 'mgrBA has wrong status of: %s'%status
        
        elif role == 'pe':
            if status not in ['Pending Submission','Requires Approval','Approving','Approved']:
                if status in ['Approving']:
                    action = 'peBA has Approved, Create Token, Notify SCM'
                if status in ['Rejecting']:
                    action = 'peBA has Rejected, Notify Dev'
            else:
                action = 'peBA has wrong status of: %s'%status
        
        elif role == 'ae':
            if status not in ['Pending Merged Fix','Merged - Notifying Originator',
                              'Merged - Testing by Originator','Merged - Tested by Originator',
                              'Merged - Approved', 'Merged - Rejected']:
                if status in ['Notifying Originator']:
                    action = 'aeBA has Submitted, Notify CR Originator'
            else:
                action = 'aeBA has wrong status of: %s'%status

        elif role == 'scm':
            if status not in ['Pending Fix','Requires Receipt','Received','Accepted','Testing','Patch Build Available','Merged']:
                if status in ['Merged']:
                    action = 'scmBA has Submitted, Notify CR Originator'
                else:
                    action = 'scmBA has actionable status of %s'%status
            else:
                action = 'scmBA has unactionable status of: %s'%status

        if action != '':
            return {'tbId':tbId, 'action':action}
        return ''
        

    def getLatestBA(self, secsAgo=60*60*24, show=False):
        """ get the Branch Approvals modified in the since secsAgo"""
        collect = {}
        actionNeeded = {}    # key as tbId value of action required
        fromSecs = time.time()-secsAgo
        dateStr = self.getAsDateTimeStr(fromSecs)
        where = [['OwnerId','!=',''],'and',['LastModifiedDate','>',dateStr]]
        queryList = self.query('Branch_Approval__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'getLatestBA Result: NO Branch Approvals Found within the last %s secs'%secsAgo
            return collect
        for info in queryList:
            tbId = info.get('Task_Branch__c','')
            action = self.checkBAForAction(info)
            if action not in [None,'']: 
                actionNeeded[tbId] = action
            bal = collect.get(tbId,[])
            bal.append(info)
            collect[tbId] = bal
        return collect, actionNeeded


    def getLatestTBA(self, secsAgo=60*60*24, show=False):
        """ get the Branch Approvals modified in the since secsAgo"""
        collect = {}
        actionNeeded = {}    # key as tbId value of action required
        fromSecs = time.time()-secsAgo
        dateStr = self.getAsDateTimeStr(fromSecs)
        where = [['OwnerId','!=',''],'and',['LastModifiedDate','>',dateStr]]
        queryList = self.query('Branch_Approval__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'getLatestBA Result: NO Branch Approvals Found within the last %s secs'%secsAgo
            return collect
        for info in queryList:
            tbId = info.get('Task_Branch__c','')
            action = self.checkBAForAction(info)
            if action not in [None,'']: 
                actionNeeded[tbId] = action
            bal = collect.get(tbId,[])
            bal.append(info)
            collect[tbId] = bal
        # now collect is a dictionary with key of tbId and list of baInfo
        
        result = []
        for tbId, bal in collect.items():
            if tbId in [None,'',[]]:
                self.setLog('getLatestTBA: tbId:%s bal:%s'%(tbId,bal),'error')
                continue
            tbInfo = self.retrieve([tbId], 'Task_Branch__c', fieldList='all', allowNulls=False)[0]
            print 'Task Branch: %s'%tbInfo.get('Name')
            if show: self.showData(tbInfo)
            for baInfo in bal:
                baRole = baInfo.get('Approval_Role__c')
                status = baInfo.get('Status__c')
                name   = baInfo.get('Name')
                msg = '    BA:%19s %-30s %s'%(baRole,status,name)
                print msg
                if show: self.showData(baInfo)
            result.append({'Task_Branch__c':tbInfo, 'Branch_Approval__c':bal})
        print 'Found %s Task_Branchs with %s Branch Approvals'%(len(result),len(queryList))
        return result, actionNeeded

    def delOrphanBAs(self):
        """ delete all the BAs that are no longer linked to a Task Branch"""
        where = [['Task_Branch__c','=',''],'and',['Team_Branch__c','=','']]
        queryList = self.query('Branch_Approval__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'delOrphanBAs Result: NO Branch Approvals Orphans Found using %s'%where
            return []
        delList = []
        for info in queryList:
            baId = info.get('Id')
            if baId not in [None,'']:
                delList.append(baId)
            
        if len(delList) > 0:
            res = self.delete(delList)
            print 'deleted %s BA items'%(len(delList))
        
        

    def getTBAWith(self, where=None, show=False, isTeam=False):
        """ get the Branch Approvals using passed where clause"""
        collect = {}
        actionNeeded = {}    # key as tbId value of action required
        if where is None:
            uid = '00530000000cCy5'  #Chip Vanek
            where = [['OwnerId','=',uid]]
        #print "Query %s" %where
        queryList = self.query('Branch_Approval__c', where=where, sc='all')
        if queryList in self.badInfoList:
            if self.debug>1:print 'getTBAWith Result: NO Branch Approvals Found using %s'%where
            return collect, actionNeeded
        for info in queryList:
            if isTeam:
                tbId = info.get('Team_Branch__c','')
            else:
                tbId = info.get('Task_Branch__c','')
            bal = collect.get(tbId,[])
            bal.append(info)
            collect[tbId] = bal
        #print "Collect %s and Action %s" %(collect,actionNeeded)
        return collect, actionNeeded

    def getMyApprovals(self, uid=None, stream=None, branch=None, show=False, getTB=False):
        """ one call to get all new Task Branch Approval objects
            will return data as a list of data dictionaries [{data}] or []
        """
        if uid in [None,'']:  uid = self.uid
        userInfo = self.getContactByUserId(uid)
        userName = '%s %s' %(userInfo.get('FirstName'),userInfo.get('LastName'))
        res = []

        where = [['OwnerId','=',uid]]
        if stream not in [None,'']:
            where.extend(['and',['Stream__c','=',stream]])
        if branch not in [None,'']:
            where.extend(['and',['Branch__c','like',branch]])
            
        queryList = self.query('Branch_Approval__c', where=where, sc='all')
        if queryList in self.badInfoList:
            print 'getMyApprovals Result: NO Task Branch Found for %s or %s in %s ' %(uid, branch, stream)
            return res
        
        collect = {}    
        for info in queryList:
            if type(info) not in dictTypes:
                return 'Error: getMyApprovals for %s or %s returned %s' %(uid, branch, info)

            tbId = info.get('Task_Branch__c','')
            if tbId not in [None,'']:
                res.append(info)
                if show: self.showData(info)
                id = info.get('Id')
                name = info.get('Name')
                role = info.get('Approval_Role__c')
                date = info.get('Date_Time_Actioned__c')
                order = info.get('Order__c')
                status = info.get('Status__c')
                crList = info.get('CR_List__c')
                stream = info.get('Stream__c','')
                branch = info.get('Branch__c','')
                approval = info.get('Approval__c')
                ba = {'Id':id, 'tbId':tbId, 'role':role, 'date':date, 'status':status, 'order':order
                     ,'branch':branch, 'stream':stream, 'crList':crList, 'approval':approval, 'Name':name}

                bal = collect.get(role,[])
                bal.append(ba)
                collect[role] = bal
                #print 'adding %s \nBAL:%s\nCOLLECT is:%s\n'%(role,bal,collect)
            else:
                print 'Could not find a tbId in %s' %info
                
        if self.debug>1:print '---Found %s Branch Approvals of %s types for %s ---'%(len(queryList), len(collect), userName)  
        for role, baList in collect.items():
            print '-> %s has %s Branch Approvals as %s <-'%(userName, len(baList), role)
            for ba in baList:
                if type(ba) not in dictTypes:
                    print 'ERROR ba was %s in %s'%(ba, baList)
                    continue
                if ba.get('approval') in [None,'']:
                    print '      %s %22s for %s %s '\
                          %(self.getDisplayDateTime(ba.get('date')), ba.get('status'), ba.get('stream'), ba.get('branch'))
            
        self.setData({'Branch_Approval__c':res})
        return queryList

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


    def getBranchMapCC(self, branch, stream=''):
        """ get the branch information that we have stored in the ClearCase Pickle """
        if not hasattr(self, 'ccbrsop'):
            self.ccbrsop = CcBranchCache()
    
        tbInfo = self.ccbrsop.getCache(branch)
        return tbInfo
        

    ##################################################################################################
    #  MOD migration methods
    ##################################################################################################
    def getMODs(self, branch, stream):
        """ get a list of MODs for the given branch and code stream
            return list of MODInfo or []
        """
        result = []
        
        where = [['BranchLabel__c','=',branch]
                ,'and',['CodeStream__c','=',stream]
                ,'and',['RecordTypeId','=','01230000000002vAAA']]
        #where = self.getSQOLWhereShortcut('br_mod', branch)         # NOTE this does not limit by Stream!!!
        res = self.query('Task', where, sc='fields')
        if res in self.badInfoList:
            # what to do?  munge branch string, eliminate stream?  Log erro for now
            self.setLog('getMODs: None found for %s in %s '%(branch, stream),
                        'warn')
            return result
        print '    Found %s MOD for %s in %s'%(len(res), branch, stream)
        return res
    

    def getMODsByCR(self, CR, filterCS=['all']):        
        """ get MOD in a CR filtering by filterCS   
            Called from walkSCM
        """
        crID = CR.get('Id')
        crNum = CR.get('CaseNumber')
        where = [['whatID','=',crID],'and',['RecordTypeId','=','01230000000002vAAA']]
        MODs = self.query('Task', where)
        if MODs in self.badInfoList:
            self.setLog('getMODsByCR No MODs found for cr:%s'%(crNum),'info')
            return []
        self.setLog('getMODsByCR found %s MODS cr:%s'%(len(MODs), crNum),'info')
        results = []
        branches = []
        streams = []

        for MOD in MODs:
            brMOD  = MOD.get('BranchLabel__c')
            tbrMOD = MOD.get('TeamBranch__c')
            brs = []
            if brMOD is not None:
                if brMOD.find(',') != -1: # we have a psuedo list of branches
                    brList = brMOD.split(',')
                    if brList[0] not in [None,'']:
                        brs = brList
                    else:
                        brs = brList[1:]
                    branches.extend(brs)
                else:
                    brs.append(brMOD)
                    branches.append(brMOD)
            if tbrMOD is not None:
                branches.append(tbrMOD)
                brs.append(tbrMOD)
                
            csMOD = MOD.get('CodeStream__c')
            streams.append(csMOD)
            if csMOD in filterCS:
                results.append(MOD)
            elif 'all' in filterCS:
                results.append(MOD)
            elif csMOD == self.csNextGeneric:
                if genericInBuild == True:
                    msg = 'Found %s MOD to potentially include into %s, cr:%s %s' %(self.csNextGeneric, filterCS, crNum, branches )
                        
        if len(results) == 0:
            self.setLog('No MODs in cs:%s CR:%s cs:%s brs:%s'%(filterCS, crNum, streams, branches),'warn')
        return results

    

    def delAllTaskBranches(self):
        """ danger!! deleting all Task Branches and sub objects """
        tb = self.delAllByEntity('Task_Branch__c')
        ba = self.delAllByEntity('Branch_Approval__c')
        cl = self.delAllByEntity('Branch_CR_Link__c')
        

    def delAllByEntity(self, entity):
        """ Danger Will Robinson!!! delete all of this entity """
        total = 0

        delIdList = []

        for info in self.getAllByEntity(entity):
            tag = ' ---- '
            if info.has_key('Developer__c'):
                tag  = info.get('Developer__c')
            elif info.has_key('Order__c'):
                tag  = info.get('Order__c')
            elif info.has_key('Branch__c'):
                tag  = info.get('Branch__c')
                id = info.get('Id')
                delIdList.append(id)
                #name = info.get('Name')

        total += len(delIdList)
        if len(delIdList) > 0:
            res = self.delete(delIdList)
            # call self again to get rid of any more...
            total += self.delAllByEntity(entity)

        print 'deleted %s %s objects'%(total,entity)
        return total

    def getAllByEntity(self, entity):
        """ get a list of all of one entity type
        """
        result = []
        where = [['Id','!=','']]
        res = self.query(entity, where)
        if res in self.badInfoList:
            self.setLog('getAllByEntity: No %s found '%entity,'error')
            return result
        msg = 'getAllByEntity: %s %s found '%(len(res),entity)
        print msg
        self.setLog(msg,'error')
        return res

        

    ##################################################################################################
    #   Overall Status control mapping for Branch Approvals
    ##################################################################################################
    def getStatMap(self, status, default=None):
        """ wrapper to handle status not in self.statMap 
        """
        sm = self.getStatusMap().get(status,{})
        if sm in [None,{}]:
            if self.debug>0:print ' ERROR %s not found in statusMap'%status
            if default is not None:
                return default
            sm = self.getStatusMap().get('Fixing',{})
        return sm




    ##################################################################################################
    #  utility and setup methods
    ##################################################################################################
    def sendAlert(self, uid, subject, body):
        """ send an email message to sForce userID, return 0 or 1 """
        toAddrs = []
        toInfo = self.getUserById(uid)

        msgBody = '%s'%(body)

        if self.adminInfo:  fromAddr = self.adminInfo.get('mail')
        else:               fromAddr = 'salesforce-support@molten-magma.com'

        if self.debug > 2: toAddrs = self.sfb.trialAddrList
        else: toAddrs.append(toInfo.get('Email'))
        #toAlias = getAliasString(toAddrs) # should now call mailServer() function, imported by sforceBase
        
        preSubj = 'SF Alert:'
        subject = '%s %s' %(preSubj, subject)    

        msgTxt  = self.mailServer().setEmailTxt(fromAddr, toAddrs, subject, msgBody)
        msgStat = self.mailServer().sendEmail(fromAddr, toAddrs, msgTxt, subject)
        msg = self.mailServer().getSendResults(subject, toAddrs, msgStat)
        self.sfb.og('%s'%msg,'info')
        return msg


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



def buildBranchDescr(modDescMap):
    """
    Standalone datacruncher that will build a text description
    from a map of crNumber:descr pairs
    Disregards empty descriptions
    Removes and accounts for duplicate values
    Returns full text description.
    """
    revDescrMap = {}
    for crNum in modDescMap.keys():
        descr = modDescMap[crNum].strip()

        # skip blank descriptions
        if len(descr) == 0:
            continue

        # Reverse map the descriptions to eliminate dupes
        if revDescrMap.has_key(descr):
            crNumList = revDescrMap[descr].split(',')
            crNumList.append("%s" %crNum)
            crNumListStr = ','.join(crNumList)
        else:
            crNumListStr = "%s" %crNum

        revDescrMap[descr] = crNum

    # Now, build the description
    buf = StringIO.StringIO()
    for descrTup in revDescrMap.items():
        descr, crNumListStr = descrTup
        crNumList = crNumListStr.split(',')
        descrLeader = "* From MOD(s) on %s:\n" %', '.join(crNumList)
        buf.write(descrLeader)
        buf.write(descr)
        buf.write('\n')
        continue
    
    buf.seek(0)
    return buf.read()
## END buildBranchDescr

        
##########################################################################
#  Logic methods called from command line 
##########################################################################
        
def getBranch(branch, parm, options):
    stream = options.cs
    print 'Looking for the branch %s in code stream %s' %(branch, stream) 
    sfb = SFTaskBranchTool(debug=options.debug)
    brObj = SFTaskBranch(sfTool=sfb)
    brObj.getSFData(branch, stream)
    results = brObj.data
    brObj.getModData(branch, stream)
    #pprint.pprint( results)
    

def deleteALLBranchApprovals(options):
    print 'Deleting ALL of the Branch approval objects'
    sfb = SFTaskBranchTool(debug=options.debug)
    sfb.delAllTaskBranches()
    #sfb.delAllByEntity('Branch_Approval__c')
    
def deleteBranchApprovalOrphans(options):
    print 'Deleting ALL of the Branch approval Orphan objects'
    sfb = SFTaskBranchTool(debug=options.debug,logname='delOrphans')
    sfb.delOrphanBAs()

def getALLBranchApprovals(num, skip, options):
    if num in ['all']: num = 10000
    else:              num = int(num)
    print 'Checking on %s of the Branch approval objects'%num
    sfb = SFTaskBranchTool(debug=options.debug)
    allBAUsers = sfb.getBAUsers()
    total = len(allBAUsers)
    num = 0
    numWarn = 0
    print 'FOUND %s Owners of Branch Approvals'%total
    print 'Now will display the status of all approvals'
    tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
    for uid in allBAUsers:
        num += 1
        res = sfb.getMyApprovals(uid=uid, stream=None, branch=None, show=False, getTB=False)
        print ' '

def getLatestBA(options, secsAgo=None):
    #entity = 'Task_Branch__c'
    entity = 'Branch_Approval__c'
    print 'Checking on latest %s '%entity
    sfb = SFTaskBranchTool(debug=options.debug)
    if secsAgo not in [None,0,'']:
        latestList, actionNeeded = sfb.getLatestTBA(secsAgo) 
        # actionNeeded[tbId] = action
    else:
        latestList, actionNeeded = sfb.getLatestTBA()      #secAgo is only parm
    total = len(latestList)
    print 'FOUND %s %s items'%(total, entity)
    if len(actionNeeded) == 0:
        print 'No Branch Approval action are required'
    for tbId, info in actionNeeded.items():
        print '  %s needs action of %s' %(tbId, info)
    #tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)


def getLatest(entity, options):
    """ getUpdate is not working """
    if entity in ['tb','taskbranch','branch']: entity = 'Task_Branch__c'
    if entity in ['ba','approval','branchapproval']: entity = 'Branch_Approval__c'
    if entity in ['crl','cr_link','crlink']: entity = 'Branch_CR_Link__c'
    #res = {'Task_Branch__c':{}, 'Branch_Approval__c':[], 'Branch_CR_Link__c':[]}
    print 'Checking on latest %s '%entity
    
    sfb = SFTaskBranchTool(debug=options.debug)
    latestList = sfb.getUpdated(entity)
    #myApprovals = sfb.getMyApprovals('00530000000cCy5')
    #createDate = myApprovals[0].get('CreatedDate')
    #print 'CreateDate type is %s as %s'%(type(createDate),createDate)
    total = len(latestList)
    num = 0
    numWarn = 0
    print 'FOUND %s %s items'%(total, entity)
    print 'Now will display the status of all approvals'
    tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
    for info in latestList:
        num += 1
        print '%s %s' %(num,info)
        print '-^'
    


def setStatusLatestBA(max, skip, secsAgo, options):
    if max in ['all']: max = 100
    else:              max = int(max)
    try: skip = int(skip)
    except: skip = 0
    msg = 'Checking status on up to %s of the Task Branches modified in the last %s hours, skipping first %s'%(max,secsAgo/3600,skip)
    print msg
    st = time.time()
    sfb = SFTaskBranchTool(debug=options.debug)
    sfb.setLog(msg,'info')
    print '%.5s query start'%(time.time()-st)
    #allTBs = sfb.getAllByEntity('Task_Branch__c')
    TBs = sfb.getLatestTB(secsAgo)
    print '%.5s query done'%(time.time()-st)
    total = len(TBs)
    num = 0
    print 'FOUND %s Task Branch object'%total
    print 'Checking the status of all Branches and updating Status, num CR, and Num Approvals if needed'
    tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
    print '%.7s'%(time.time()-st)
    for tbInfo in TBs[skip:]:
        if num > max: break
        info = tbInfo.get('Task_Branch__c')
        branch = info.get('Branch__c')
        stream = info.get('Code_Stream__c')
        print '%.7s %3s %27s Loading '%((time.time()-st), num, branch)
        msg = tbObj.loadBranch(branch, stream, team='')
        #foundOK, status = tbObj.getTBStatusFromMODs()
        #if foundOK:
        #    print '%.7s %3s %27s Got %s -> MODStatus %s '%((time.time()-st), num, branch, msg, status)
        #else:
        status = info.get('Branch_Status__c','')
        print '%.7s %3s %27s Got %s -> TBStatus %s '%((time.time()-st), num, branch, msg, status)
        
        num += 1
        if foundOK:
            updated = tbObj.setBranchStatus(status, st)
            
            if updated: 
                msg = '%s/%s Updated Status of %s %s TO %s' %(num, total, stream, branch, status)
                sfb.setLog(msg,'info')
                print '%.7s %31s status updated to %s'%((time.time()-st), branch, status)
            else:       
                msg = '%s/%s Skipped Status Update of %s %s TO %s' %(num, total, stream, branch, status)
                sfb.setLog(msg,'info')
        else:
            msg = '%s/%s Status NOT Found from MODs for %s %s ret:%s' %(num, total, stream, branch, status)
            sfb.setLog(msg,'info')
    sfb.setLog('Checked Status of %s of Task Branches in %s secs'%(max,(time.time()-st)),'info')
    

def loadBranchFromFile(filename, max, skip, options):
    if max in ['all']: max = 10000
    else:              max = int(max)
    try: skip = int(skip)
    except: skip = 0
    print 'Loading %s branches skipping first %s from the file %s' %(max,skip,filename)
    if len(filename.split('/')) == 1:
        fpath = os.path.join(os.getcwd(),filename)
    else:
        fpath = filename
    if os.path.isfile(fpath):
        try: fp = open(fpath, 'r')
        except Exception,e: 
            print 'Could not open the branch load file in %s' %fpath
            print '%s err:%s' %(Exception,e)
        
        sfb = SFTaskBranchTool(debug=options.debug)
        start = 0
        num = -1
        print 'Skipping the first %s rows, then processing %s rows'%(skip,max)
        for line in fp.readlines():
            row = line.split(',')
            stream = row[0]
            if stream not in ['4','4.0','4.1','4.2']:
                print 'Skipping row %s' %row
                continue
            branch = row[1]
            team = row[2]
            team = team.split('\r\n')[0]
            #print 'stream:%s branch:%s team:%s:'%(stream,branch,team)
            if team not in ['-','']:
                print '-->>Processing a TEAM Branch %s<<--' %team
                #continue
            loadStatus = sfb.getBranchMap(branch, stream, data={'loadStatus':'new', 'loadTime':0})
            if loadStatus.get('loadStatus','') == 'initialLoad':
                print 'Skipping %s  Loaded %s secs ago'%(branch, time.time()-loadStatus.get('loadTime',0))
                continue
            num += 1
            if num < skip: continue
            if num > max+skip: break
            msg = '%s:TB Found branch %s in %s  %s '%(num, branch,stream,team)
            sfb.setLog(msg,'info')
            brObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
            
            inf = brObj.loadBranch(branch, stream, team=team)             
            #foundOK, status = brObj.getTBStatusFromMODs()          # turn off
            foundOK, status = False, 'Unknown'
            if foundOK:
                updated = brObj.setBranchStatus(status)
                if updated: msg = ' %s:TB %s Updated Status of %s %s' %(num, branch,stream, status)
                else:       msg = ' %s:TB %s Skipped Status Update of %s %s' %(num, branch, stream,status)
                sfb.setLog(msg,'info')
            else:
                msg = ' %s:TB %s Skipping the updating of the status %s' %(num, branch,status)
                sfb.setLog(msg,'info')
            loadStatus = {'loadStatus':'initialLoad', 'loadTime':time.time()}
            sfb.setBranchMap(branch, stream, data=loadStatus)
            msg = '%s:TB Done migrating branch %s in %s'%(num, branch,stream)
            sfb.setLog(msg,'info')
    else:
        print 'The file %s could not be found'%fpath
            

def loadBranchFromPickle(max, skip, options):
    """
    Uses the "system" cc branch cache pickle instead of a specific file
    This pickle is presumed to have been pre-loaded by populateCcBranches
    """
    from sfTeamBranch import SFTeamBranch

    sfb = SFTaskBranchTool(debug=options.debug, logname='ccPLoad')
    ut = SFUserTool(debug=options.debug, setupLog=False)

    # try reusing same loggers from sfb tool.
    ut.setLogger(name='ccPLoad', note=sfb.note, logger=sfb.log,
                 dlogger=sfb.dlog, elogger=sfb.elog, clogger=sfb.clog)

    # non-reentrancy check
    try:
        lockHandle = cronLock('loadTaskBranchFromPickle.lock')
    except Exception, e:
        msg = "Could not acquire reentrancy lock. Assume another instance is running. EXITING."
        sfb.setLog(msg, 'warn')
        print msg
        sys.exit()

    ccBranchCache = CcBranchCache()
    opBranchCache = OpBranchCache()
    
    if max in ['all']: max = 10000
    else:              max = int(max)
    try: skip = int(skip)
    except: skip = 0
    
    print 'Loading %s branches skipping first %s from the pickle' %(max,skip)
    
    ccBranchKeys = ccBranchCache.getKeys()

    emailDomain = sfb.sfc.get('email','domain')
    defaultUserId = sfb.sfc.get('main','default_uid')
    defaultSoftUserId = sfb.sfc.get('main','default_soft_uid')
    
    start = 0
    num = 0
    print 'Skipping the first %s rows, then processing %s rows'%(skip,max)

    # create only one empty branch obj to reuse
    brObj = SFTaskBranch(sfTool=sfb,debug=options.debug)
    tbrObj = SFTeamBranch(sfTool=sfb,debug=options.debug)

    
    for key in ccBranchKeys:
        branchData = ccBranchCache.getCache(key)
        branch = key
        stream = branchData.get('stream', None)

        if stream not in ['5','4','4.0','4.1','4.2']:
            print 'Skipping branch or label %s' %branch
            continue

        labelName = branchData.get('label', None)
        branchName = branchData.get('taskBranch')
        brCreateDateTime = branchData.get('createDateTime')
        brCreateDateTimeStr = sfb.getAsDateTimeStr(time.localtime(time.mktime(brCreateDateTime.timetuple())))
        scmcdt = sfb.checkDate(brCreateDateTimeStr, 'loadBranchFromPickle')
        
        if labelName is None:
            branchOrLabel = "Branch"
        else:
            branchOrLabel = "Label"

        loadStatus = sfb.getBranchMap(branch, stream,
                                      data={'loadStatus':'new',
                                            'loadTime':0})
        if loadStatus.get('loadStatus','') == 'initialLoad':
            print 'Skipping %s  Loaded %s secs ago' \
                  %(branch, time.time()-loadStatus.get('loadTime',0))
            continue
        
        num += 1
        if num < skip: continue
        if num > max+skip: break

        # check for existing team branch having same name/stream
        tbrstat = tbrObj.loadTeamBranch(branch, stream)
        if tbrObj.getData('Team_Branch__c').get('Id',None) is not None:
            print 'Skipping %s, Team Branch already exists in stream %s' \
                  %(branch, stream)
            loadStatus = {'loadStatus':'initialLoad', 'loadTime':loadTime}
            sfb.setBranchMap(branch, stream, data=loadStatus)
            continue

        msg = '%s:TB Start load of branch %s in %s '%(num, branch,stream)
        sfb.setLog(msg,'info')

        brObj.loadBranch(branch, stream)

        # Moved status section down below...

        # attempt to find TB owner according to clearcase creator
        # Need to cascade through Reassign To users on the contact record
        # if user is inactive
        brOwnUid = None
        branchOwnerUname = branchData.get('creator', None)
        if branchOwnerUname is not None:
            # see if there's an alternate/preferred alias for this one
            branchOwnerUname = emailTransMap.get(branchOwnerUname,
                                                 branchOwnerUname)
            brUname = "%s@%s" %(branchOwnerUname, emailDomain)
            brOwnUid = ut.getUserIdByUsername(brUname)

        brOwnUid = ut.cascadeToActiveUser(brOwnUid)

        if brOwnUid == defaultSoftUserId:
            # Before we accept the soft default user ID as the owner of
            # the task branch, check to see if owner was already set in
            # the branch object. If so, don't replace it.
            tbInfo = brObj.getData('Task_Branch__c')
            curBrOwnUid = tbInfo.get('OwnerId', None)
            if curBrOwnUid is not None:
                brOwnUid = curBrOwnUid
        # end ownership section

        # other branchly information from clearcase:
        tbInfo = brObj.getData('Task_Branch__c')
        tbId = tbInfo.get('Id', '')
        tbStatus = tbInfo.get('Branch_Status__c', 'Open')

        tbUpdMap = {}
        tbUpdMap['Branch_Path__c'] = branchData.get('branchPath')
        tbUpdMap['Branch_Or_Label__c'] = branchOrLabel
        tbUpdMap['Branch_Status__c'] = tbStatus
        tbUpdMap['OwnerId'] = brOwnUid
        tbUpdMap['SCM_Create_Date_Time__c'] = scmcdt

        tbId = brObj.setTaskBranch(branch=branch, stream=stream, id=tbId,
                                   data=tbUpdMap)
        if tbId in self.badInfoList:
            msg = ' %s:TB %s Insert/Update Failed! (%s)' %(num, branch, tbId)
            sfb.setLog(msg,'error')
        else:
            msg = ' %s:TB %s Inserted/Updated ID: %s' %(num, branch, tbId)
            sfb.setLog(msg,'info')
            

        ## Move this status section down from above
        #foundOK, status = brObj.getTBStatusFromMODs() # turn off
        foundOK, status = False, 'Unknown'

        if foundOK:
            updated = brObj.setBranchStatus(status)
            if updated:
                msg = ' %s:TB %s Updated Status of %s %s' \
                      %(num, branch,stream, status)
                
            else:
                msg = ' %s:TB %s Skipped Status Update of %s %s' \
                      %(num, branch, stream,status)
                
            sfb.setLog(msg,'info')
        ## END status section


        # Tuck base information about the branch into the operational
        # branch pickle
        loadTime = time.time()
        if tbId not in self.badInfoList:
            opBranchData = {} # may not blank this here later...
            opBranchData['Id'] = tbId
            opBranchData['OwnerId'] = brOwnUid
            opBranchData['Name'] = branch
            opBranchData['Branch_Or_Label__c'] = branchOrLabel
            opBranchData['Code_Stream__c'] = stream
            opBranchData['LoadTime'] = loadTime

            opBranchCache.setCache(tbId, opBranchData)
            
            loadStatus = {'loadStatus':'initialLoad', 'loadTime':loadTime}
            sfb.setBranchMap(branch, stream, data=loadStatus)
        msg = '%s:TB Done migrating branch %s in %s'%(num, branch,stream)
        sfb.setLog(msg,'info')
        

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
    m += '  Default usage is to get Branch info from SalesForce.\n'
    m += ' '
    m += '    sfTaskBranch -cl do             (load TBs from MODs)\n'
    m += '      or\n'
    m += '    sfTaskBranch -cs -p all do|3600 (check status of all or last 3600 secs) \n'
    m += '      or\n'
    m += '    sfTaskBranch -cba do            (show status of all approvers) \n'
    m += '      or\n'
    m += '    sfTaskBranch -cu -pr 3600       (check action required on BAs modified since secs) \n'
    m += '      or\n'
    m += '    sfTaskBranch -cg blast4_michel  (get info on specific branch)\n'
    m += '      or\n'
    m += '    sfTaskBranch -cdel -pba do      (delete ALL Branches and approvals, you are warned) \n'
    return m

def main_CL():
    """ Command line parsing and and defaults methods
    """
    parser = OptionParser(usage=usage(), version='%s'%version)
    parser.add_option("-c", "--cmd",   dest="cmd",   default="get",      help="Command type to use.")
    parser.add_option("-p", "--parm",  dest="parm",  default="",         help="Command parms.")
    parser.add_option("-f", "--path",  dest="path",  default="modmigration.csv",         help="Path to load file.")
    parser.add_option("-s", "--cs",    dest="cs", default="4",           help="Code Stream of Branch")
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
        if options.cmd in ['get','g']:
            getBranch(branch, parm, options)
            
        elif options.cmd in ['load','l']:
            filename = options.path
            num = options.parm
            if num in [None,'']: num = 2
            skip = 0
            loadBranchFromFile(filename, num, skip, options)

        elif options.cmd in ['pickle','p']:
            #filename = options.path
            num = options.parm
            if num in [None,'']: num = 2
            skip = 0
            loadBranchFromPickle(num, skip, options)

        elif options.cmd in ['stat','s']:
            num = options.parm
            if num in [None,'']: num = 1
            skip = 0
            secsAgo = 60*60*24*1
            if branch not in ['now','do']:
                secsAgo = int(branch)
            setStatusLatestBA( num, skip, secsAgo, options)

        elif options.cmd in ['approvers','ba']:
            num = options.parm
            if num in [None,'']: num = 1
            skip = 0
            getALLBranchApprovals( num, skip, options)

        elif options.cmd in ['update','u']:
            if options.parm in ['tb','ba','crl','mm']:
                getLatest(options.parm, options)
            elif options.parm in ['r']:
                secsAgo = int(branch)
                getLatestBA(options, secsAgo)
            else:
                stream = options.cs
                loadBranch(branch, stream, parm, options)
        
        elif options.cmd in ['delete','del']:
            if options.parm in ['allbranchApprovals']: 
                deleteALLBranchApprovals(options)
            if options.parm in ['ba-orphans']: 
                deleteBranchApprovalOrphans(options)
            else:
                print 'You can delete Orphan Branch Approval items using the parm ba-orphans'
            
        else:
            doSomething('search', query, options.parm, options)
            print 'doing nothing yet, I can do it twice if you like'
            
        print '\nTook a total of %3f secs' %(time.time()-st)
    else:
        print '%s' %usage()

if __name__ == "__main__":
    main_CL()
