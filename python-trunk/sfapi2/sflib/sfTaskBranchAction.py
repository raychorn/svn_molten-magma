""" Business Logic specific to User Commandline Actions with the Task Branch customer object
    - Task Branch (TB) is a sForce representation of a code branch in Clearcase
    - TB is displayed as a container object with a list of:
       - Branch Approvals - Developer Accept, Manager Approve, PE Approve, AE accept, Closed
       - Branch CR Links - link objects to customer oriented CRs with mirroroed CR Status
    
 ToDo:
    - Create methods to support each specific action to call for command line
        - addMod        - create a new Branch CR link in a TB
        - submitBranch  - change status of developer Branch Approval from fix -> submitted
        - approveBranch - change status of manager Branch Approval from pending -> approved
        
    - Create walkSF methods to move TB to next step in workflow
    
           Chip Vanek, July 6th, 2004
"""
# C.T Jun 29:
from MudflowWrap import MudflowWrap
import pprint
import sys, datetime, time, os
import StringIO, getopt
import copy, re
import traceback
from types import ListType, TupleType, DictType, DictionaryType
from optparse import OptionParser, OptionGroup
from sfMagma import *
from sfTaskBranch import *   # get SFTaskBranch & SFTaskBranchTool
from sfTeamBranch import addTeamBranchCL, SFTeamBranchTool, SFTeamBranch, sweepTeamBranchFlow
from walkSFEntity import SFTaskBranchWalk
from sfUtil import *
from sop import sfEntities, SFEntitiesMixin, SFUtilityMixin, SFTestMixin

class SFTaskBranchAction(SFTaskBranchWalk):
    """ This is a composite object that represents a TaskBranch sForce object
        and related Branch Approval & Branch CR objects as one entity
    """
    modList = []
    loadFromSF = False

    ##################################################################################################
    #   Status oriented methods
    ##################################################################################################
    def approveBranch(self, branch, stream, st=None):
        """ decide what approval role the user needs for this 
            branch and do it.
        """
        ld = self.checkLoad(branch, stream, cl=True)
        # ld = [numCLs,numBAs,status,branch,stream]
        if -1 in ld[:2]: return -1
        num = 0
        role = self.getNextApprovalRole()   # dev, mgr, pe, scm, ae
        status = ld[2]
	msg = " approveBranch: The next approval role is %s, branch status is %s" %(role, status)
        print msg
        if role == 'dev':   num = self.submitByDev(branch, stream, st)
        elif role == 'part': num = self.submitByPart(branch, stream, st)
        elif role == 'mgr': num = self.submitByMgr(branch, stream, st)
        elif role == 'pe':  num = self.submitByPe(branch, stream, st)
        elif role == 'scm': num = self.submitToSCM(branch, stream, st)
        elif role == 'ae':  num = self.submitByAe(branch, stream, st)
        else: print 'ERROR: approveBranch, getNextApprovalRole returned %s'%role
        return num, role

    def rejectBranch(self, branch, stream, st=None):
        """ reject the branch back to the developer
        """
        num = 0
        ld = self.checkLoad(branch, stream, cl=True)
        if -1 in ld[:2]: return -1
        role = self.getNextApprovalRole()
        status = ld[2]
	msg = " rejectBranch: The next approval role is %s, branch status is %s" %(role, status)
        print msg
        if role == 'part': num = self.rejectToDevByPart(branch, stream, st)
        elif role == 'mgr': num = self.rejectToDevByMgr(branch, stream, st)
        elif role == 'pe':  num = self.rejectToDevByPe(branch, stream, st)
        else: print 'ERROR: Nothing to reject for role %s' %role
        return num

class SFTaskBranchActionTool(SFTaskBranchTool):
    """ This is a subclass of the SFEntityTool to hold any Branch specific
        SOQL query methods and entity linking action methods
    """
    logname = 'sfTBAct'

    def sendAlert(self, uid, subject, body):
        """ send an email message to sForce userID, return 0 or 1 """
        toAddrs = []
        toInfo = self.sfb.getUserById(uid)

        msgBody = '%s'%(body)

        if self.adminInfo:  fromAddr = self.adminInfo.get('mail')
        else:               fromAddr = 'salesforce-support@molten-magma.com'
        #if self.mailServer == None: self.mailServer = MailServer()

        if self.debug > 2: toAddrs = self.sfb.trialAddrList
        else: toAddrs.append(toInfo.get('Email'))
        #toAlias = getAliasString(toAddrs) # should now call mailServer function, imported by sforceBase
        
        preSubj = 'SF Alert:'
        subject = '%s %s' %(preSubj, subject)    

	msgTxt  = self.mailServer().setEmailTxt(fromAddr, toAddrs, subject, msgBody)
        msgStat = self.mailServer().sendEmail(fromAddr, toAddrs, msgTxt, subject)
        msg = self.mailServer().getSendResults(subject, toAddrs, msgStat)
        self.sfb.og('%s'%msg,'info')
        return msg

    ##################################################################################################
    #  Branch Approval methods
    ##################################################################################################
    def getMyBranches(self, user=None, uid=None, stream=None, branch=None, show='list'):
        """ one call to get all Task Branch objects
            will return data as a list of data dictionaries [{data}] or []
            show -> 'list' = [list of branch labels], 'all' = [list of full tbData structure]
        """
        if uid in [None,'']: uid = self.uid
        if user not in [None,'','my']:  
            userInfo = self.getUserByAlias(user)
            uid = userInfo.get('Id')
            userName = '%s %s' %(userInfo.get('FirstName'),userInfo.get('LastName'))
            if show != 'min': print 'Getting info for %s'%userName
        else:    
            userInfo = self.getContactByUserId(uid)
            userName = '%s %s' %(userInfo.get('FirstName'),userInfo.get('LastName'))
        res = []

        where = [['OwnerId','=',uid]]
        if stream not in [None,'','any','all']:
            where.extend(['and',['Code_Stream__c','=',stream]])
        if branch not in [None,'']:
            where.extend(['and',['Branch__c','like',branch]])
        
        queryList = self.query('Task_Branch__c', where=where, sc='all')
        if queryList in self.badInfoList:
	    msg = 'getMyBranches: NO Task Branch Found in stream %s ' %(stream)
            print msg
            return res
        
        collect = {}
        tbObj = SFTaskBranchAction(sfTool=self, debug=self.debug)    
        for info in queryList:
            if type(info) not in dictTypes:
		msg = 'getMyBranches: Error for %s or %s returned %s' %(user, branch, info)
                return msg

            tbId = info.get('Id','')
            if tbId not in [None,'']:
                branch = info.get('Branch__c')
                stream = info.get('Code_Stream__c')
                status = info.get('Branch_Status__c')
                if show in ['list','min']:
                    res.append(branch)
                    continue
                if show in ['info']:
                    info = {'branch':branch, 'stream':stream, 'status':status}
                    res.append(info)
                    continue
                
                inf = tbObj.loadBranch(branch, stream)
                tbData = tbObj.getData()
                res.append(tbData)
                if show in ['all']:
                    continue
                
                baList = tbData.get('Branch_Approval__c')
                for info in baList:
                    id = info.get('Id')
                    name = info.get('Name')
                    role = info.get('Approval_Role__c')
                    date = info.get('Date_Time_Actioned__c')
                    order = info.get('Order__c')
                    status = info.get('Branch_Status__c')
                    crList = info.get('CR_List__c')
                    stream = info.get('Stream__c','')
                    branch = info.get('Branch__c','')
                    approval = info.get('Approval__c')
                    ba = {'Id':id, 'tbId':tbId, 'role':role, 'date':date, 'status':status, 'order':order
                         ,'branch':branch, 'stream':stream, 'crList':crList, 'approval':approval, 'Name':name}

                    bal = collect.get(role,[])
                    bal.append(ba)
                    collect[role] = bal
		    msg = 'adding %s \nBAL:%s\nCOLLECT is:%s\n'%(role,bal,collect)
            else:
		msg = 'Could not find a tbId in %s' %info
                print msg
                
	msg = '---Found %s Task Branch for %s ---'%(len(queryList), userName)
        if self.debug>1:print msg  
        if show in ['list','listtb','all']:
            return res
            
        for role, baList in collect.items():
	    msg = '-> %s has %s Branch Approvals as %s <-'%(userName, len(baList), role)
            print msg
            for ba in baList:
                if type(ba) not in dictTypes:
		    msg = 'ERROR ba was %s in %s'%(ba, baList)
                    print msg
                    continue
                if ba.get('approval') in [None,'']:
		    msg = '      %s %22s for %s %s ' % (self.getDisplayDateTime(ba.get('date')), ba.get('status'), ba.get('stream'), ba.get('branch'))
                    print msg
        return res

    ##################################################################################################
    #   Overall Status control mapping for Branch Approvals
    ##################################################################################################
    def getStatMap(self, status, default=None):
        """ wrapper to handle status not in self.statMap 
        """
        sm = self.getStatusMap().get(status,{})
        if sm in [None,{}]:
	    msg = 'ERROR %s not found in statusMap' % status
            print msg
            if default is not None:
                return default
            sm = self.getStatusMap().get('Fixing',{})
        return sm

    ##################################################################################################
    #  utility and setup methods
    ##################################################################################################

##################################################################################################
version = 2.0  # version number shown to users at command line
##################################################################################################
#  Logic methods called from command line 
##################################################################################################
def sendMudflowForceNotification(sfb, tbInfo, forceReason):
    from MailNotification import MailNotification, WW
    from MailMessageQueue import MailMessageQueue

    mudflowContactId = '0033000000AgVjZ' # sf_mudflow contact
    mudflowContactInfo = sfb.retrieve([mudflowContactId], 'Contact')[0]
    mudflowContactId = mudflowContactInfo.get('Id')

    tbId = tbInfo.get('Id')
    branch = tbInfo.get('Name')
    stream = tbInfo.get('Code_Stream__c')

    msgQueue = MailMessageQueue(test=True)
    notification = copy.copy(MailNotification.notification)

    notification['timestamp'] = datetime.datetime.now()
    notification['subject'] = 'Branch forced past mudflow check: %s' %branch
    notification['deferred'] = True
    notification['why'] = 'you are a member of the sf_mudflow mailing list'
    notification['recipInfo'] = mudflowContactInfo

    body = 'The following branch has been submitted by the developer and has been\n'
    body += 'forced past some of the Mudflow checks.\n\n'

    body += '%s in stream %s\n' %(branch, stream)
    body += 'https://na1.salesforce.com/%s\n\n' %(tbId)

    body += '%s' %forceReason

    notification['body'] = body

    msgMap = {mudflowContactId : notification}
    msgQueue.enqueue(msgMap)
    
    return

def addModUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = ''
    
    if len(err):
        m += '%s\n\n' %err
        
    m += 'Link one or more CRs with a Task Branch (TB) on Salesforce.\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    lncr [OPTIONS] -s <stream> -b <branch_Name> -n <team_name> -c <yes|no> -v <yes|no> <CR1> [<CR2> ... <CR#>] \n'
    m += '    * use a team name of "none" to create an individual task branch.\n'
    m += '    * -c will be used to indicate whether or not branch implements a\n'
    m += '      command change.\n'
    m += '    * -v will be used to indicate whether or not branch implements a\n'
    m += '      volcano change.\n'
    m += '\n'
    m += 'Options include:\n'
    m += '    -p <priority>\n'
    m += '          (where <priority> is one of low, medium, high, urgent, or critical)\n'
    m += '\n'
    m += '    -d    (flag to prompt for general details about the branch)\n'
    m += '\n'
    m += '    -r    (flag to mark branch as High risk)\n'
    m += '    -e    (flag to prompt for details about the risk)\n'
    m += '\n'
    m += 'Note:\n'
    m += '    For a list of valid team names, use the "teams" script\n'
    return m

def addModCL(branch, stream, query, options, st):
    """ command line logic for addMod, mkCR, addcr, lncr
    """
    if type(query) not in seqTypes:
        if query in [None,'']:
            print 'Please provide one or more CR numbers to add to %s'%branch
            sys.exit()
        query = [query]
    crList = query
    
    if len(crList) == 0:
	msg = 'Please provide one or more CR numbers to add to %s' % branch
        print msg
        sys.exit()

    # uniquify the crList
    crList = uniq(crList)
    
    db=options.debug
    msg = 'Connecting to SalesForce for the branch %s in code stream %s' %(branch,stream)
    print msg
    sfbTeam = SFTeamBranchTool(debug=db, setupLog=False)
    sfb = SFTaskBranchActionTool(debug=db, logname='addCRtb')

    # try reusing same loggers from sfb tool.
    sfbTeam.setLogger(name='addCRtmb', note=sfb.note, logger=sfb.log, dlogger=sfb.dlog, elogger=sfb.elog, clogger=sfb.clog)
   
    brObj = SFTaskBranchAction(sfTool=sfb)
    sfb.getConnectInfo(version,st)

    pteam = None
    pteamComponent = None
    if options.team in [None, '','none']:
	msg = ["You must provide a team name using -n."]
	msg.append("View valid team names using the 'teams' command.")
	msg.append("Task branches must belong to a team")
        print '\n'.join(msg)
        sys.exit(1)
        """elif options.team.lower() == 'none':
        pass # pteam stays as None"""
    else:
        pteam = options.team
        # check that team is valid
        if pteam in ['si','ppro']:
	    msg = 'Branches can no longer to submitted to team name "%s". This team has been disabled. EXITING....' %pteam
            print msg
            sys.exit(1)
        if sfbTeam.isValidProductTeam(pteam) is False:
	    msg = 'The team name "%s" is unknown.\nFor a list of known teams, please use the "teams" command. EXITING' %pteam
            print msg
            sys.exit(1)

        # check if it's the synthesis team, which gets special treatment.
        """if pteam in ['synthesis','rtl']:
            pteamComponent = "RTL QOR"
            pass"""
        pass
    
    inlist = brObj.loadBranch(branch, stream, team='', label='')
    if db>1:print ' %s '%(inlist[:5])  # [numCLs,numBAs,status,branch,stream]
    if db>2: brObj.showData(target='user')
    crInfos = {}
    tbInfo = brObj.getData('Task_Branch__c')
    sfCLs = brObj.getData('Branch_CR_Link__c')
    sfBAs = brObj.getData('Branch_Approval__c')
    status = 'Fixing'
    tbUpdInfo = {}
    if tbInfo in [{}]:
        isNew = True  
        tbId = '' 
        tbUpdInfo['Branch__c']=branch
        tbUpdInfo['Name']=branch
        tbUpdInfo['Code_Stream__c']=stream
        tbUpdInfo['Branch_Status__c']=status
        tbUpdInfo['OwnerId']=sfb.uid
    else:
        isNew = False
        tbId = tbInfo.get('Id')
    tbStatus = tbInfo.get('Branch_Status__c', status)
    if tbStatus == 'Open':
        tbStatus = status
    
    if len(sfCLs) == 0:
	msg = '  No existing CR is linked to %s in %s\n'%(branch, stream)
        print msg
    else:
	msg = '  %s existing CR(s) are linked to %s in %s with status %s\n'%(len(sfCLs),branch,stream, tbStatus)
        print msg
    for clInfo in sfCLs:
        crId = clInfo.get('Case__c','')
        crInfo = sfb.getCrById(crId)
        if crInfo in [None,{}]: continue
        crNum = '%s'%int(crInfo.get('CaseNumber',''))
        crSub = crInfo.get('Subject')
        crStat= crInfo.get('Status')
        crCSP = crInfo.get('Code_Streams_Priority__c')
        crInfos[crNum] = {'crId':crId, 'status':crStat, 'subject':crSub, 'csp':crCSP}
    sfCRs = crInfos.keys()
    # Now know what exists in SF now, nothing if isNew = True

    updateList = []
    if options.risk is True:
        tbUpdInfo['High_Risk__c'] = 'Yes'
        updateList.append('High Risk')
    if options.rdesc is True:
        msg = "\nPlease enter the specific RISK comments for this Task Branch"
        details = tbInfo.get('Risk_Details__c','')
        if len(details): details += '\n'
        details += inputTextFromEditor(msg)
        tbUpdInfo['Risk_Details__c'] = details
        updateList.append('Risk Details')
        pass
    
    if options.cmdchg.lower()[0] == 'y':
        details = tbInfo.get('Command_Change_Details__c','')
        tbUpdInfo['Command_Change__c'] = 'Yes'
        updateList.append('Command Change')

        msg = "\nPlease enter comments about the COMMAND CHANGE for this Task Branch"

        if len(details):
            details += '\n'
            msg = "\nPlease enter additional comments about the COMMAND CHANGE for this branch"
            pass
        
        details += inputTextFromEditor(msg)
        tbUpdInfo['Command_Change_Details__c'] = details
        updateList.append('Command Change Details')
        pass
    
    if options.volchg.lower()[0] == 'y':
        details = tbInfo.get('Volcano_Change_Details__c','')
        tbUpdInfo['Volcano_Change__c'] = 'Yes'
        updateList.append('Volcano Change')

        msg = "\nPlease enter comments about the VOLCANO CHANGE for this Task Branch"
        if len(details):
            details += '\n'
            msg = "\nPlease enter additional comments about the VOLCANO CHANGE for this branch"
            pass
        
        details += inputTextFromEditor(msg)
        tbUpdInfo['Volcano_Change_Details__c'] = details
        updateList.append('Volcano Change Details')
        pass
    
    if options.mdesc is True:
        msg = "\nPlease enter the specific MERGE Instructions for this Task Branch"
        details = tbInfo.get('Merge_Details__c','')
        if len(details): details += '\n'
        details += inputTextFromEditor(msg)
        tbUpdInfo['Merge_Details__c'] = details
        updateList.append('Merge Details')
    if options.desc is True:
        msg = "\nPlease enter the general comments for this Task Branch"
        details = tbInfo.get('Details__c','')
        if len(details): details += '\n'
        details += inputTextFromEditor(msg)
        tbUpdInfo['Details__c'] = details
        updateList.append('General Comments')
    if options.priority not in [None,'']:
        priority = options.priority.lower()
        if priority in ['low', 'medium', 'high', 'urgent', 'critical']:
            tbUpdInfo['Branch_Priority__c'] = priority
            updateList.append('Priority')
        else:
	    msg = 'You entered an unknown priority %s, the Branch will default to medium'%options.priority
            print msg
    if options.tbr not in [None,'','-']:
        tbUpdInfo['Team_Branch__c'] = options.tbr
        updateList.append('Team Branch')
    
    if isNew:
	msg = []
	msg.append('Creating a new Task Branch for %s in code stream %s'%(branch,stream))
        msg.append('Based on your information the %s attributes will be updated\n'%(','.join(updateList)))
    else:
	msg = []
        msg.append('Updating the Task Branch %s in code stream %s'%(branch,stream))
        msg.append('Based on your information the %s attributes will be updated\n'%(', '.join(updateList)))

    sfId = brObj.setTaskBranch(id=tbId, data=tbUpdInfo)
    # now Task branch information has been updated
    tbInfo = brObj.getData('Task_Branch__c')
    tbId = tbInfo.get('Id')

    #if tbId != sfId: 
    #    print 'setTaskBranch returned %s and getData returned %s'%(sfId,tbId)
    #    print 'brObj.data %s'%brObj.getData('Task_Branch__c')

    # Here's the CR portion...
    for crNum in crList:
        if options.debug > 1: sfb.setLog('Checking for %s in %s'%(crNum,sfCRs),'info')
        if crNum in sfCRs:
	    msg = 'The CR number %s is already linked to the branch %s in code stream %s\n' %(crNum,branch,stream)
            print msg
            continue
        crInfo = sfb.getCrByNum(crNum)
        if crInfo == {}:
	    msg = 'Could not find a CR with the number %s, skipping link'%crNum
            print msg
            if len(crList) == 1:
                sys.exit(1)
            continue
        
        crId  = crInfo.get('Id')
        crSub = crInfo.get('Subject')
        crStat= crInfo.get('Status')
        crCSP = crInfo.get('Code_Streams_Priority__c')
        comp  = crInfo.get('Component__c')
        crCDt  = crInfo.get('CreatedDate')
        crCSec = sfb.checkDate(crCDt) 
        crInfos[crNum] = {'crId':crId, 'status':crStat, 'subject':crSub, 'csp':crCSP}

        # if we have a team-override component, we need to make sure the CR
        # has it set as such before we link it.
        if pteamComponent not in BAD_INFO_LIST and \
           pteamComponent != comp:
            data = {'Id': crId, 'Component__c': pteamComponent}
            res = sfb.update(CASE_OBJ, data)
            if res in BAD_INFO_LIST:
                msg = "Failed to set component on CR %s to %s for team %s" \
                      %(crNum, pteamComponent, pteam)
                logtype = 'error'
            else:
                msg = "Set component on CR %s to %s for team %s" \
                      %(crNum, pteamComponent, pteam)
                logtype = 'info'
                comp = pteamComponent
                pass
            sfb.setLog(msg, logtype)
            pass

        # Create the branch/CR link
        name = 'BrCR Link' 
        data = {'Name': name,
                'Case__c': crId,
                'CR_Status__c': crStat,
                'Fix_Requested__c':crCSec,
                'Branch_Status__c':tbStatus,
                'Component__c': comp,
                'Stream__c':stream,
                'CR_Num__c':crNum}
        clId = brObj.setBranchCRLink(tbInfo.get('Id'), id='', data=data)
        
    msg = 'There are now %s CRs linked to %s in %s, info below:'%(len(crInfos),branch,stream)
    print msg
    for crNum, info in crInfos.items():
        subject = info.get('subject')
        if subject is None:
            subject = 'No CR subject has been set'
            pass
	msg = []
	msg.append(' * CR: %s Streams: %s \tStatus: %s'%(crNum,info.get('csp'),info.get('status')))
	msg.append('     Subject: %s'%(subject.encode('ascii','replace') ))
    print '' # nice blank line for formatting goodness

    # reload the branch now that we've linked one or more CRs to it
    #inlist = brObj.loadBranch(branch, stream)
    updated = brObj.setBranchStatus(tbStatus)
    if updated:
	msg = '  Updated the Task Branch to %s status' %tbStatus
        print msg
    else:
	msg = '  Task branch status is currently %s and does not need to be updated.' %tbStatus
        print msg

    # Now, link to the receiving team branch for the stream if necessary.
    if pteam is not None:
	msg = '  Adding this Task Branch to the Team Branch %s'%pteam
        print msg
        options.listBranchPath=None
        
        addTeamBranchCL(pteam, None, branch, stream, options, st, teamTool=sfbTeam)
    
    msg = 'SalesForce Update is Complete.\nSending confirmation email to you'
    print msg
    try: 
        sent = brObj.sendNotifyEmail()
        if sent:
	    msg = 'Sent an email to you confirming the information in this Task Branch\nwith a link to Salesforce.'
            print msg
    except Exception,e:
	msg = 'Warning: could not send confirmation email to you %s' % e
        print msg
        pass
        
def rmModUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = ''
    
    if len(err):
        m += '%s\n\n' %err

    m += 'Unlink one or more CRs from a Task Branch (TB) on SalesForce.\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    unlinkcr -s <stream> -b <branch_Name> <CR1> [<CR2> ... <CR#>]\n'
    return m

def rmModCL(branch, stream, query, options, st):
    """ command line logic for rmMod, rmCR, delCR
    """
    logname = 'unlnCR'
    if type(query) not in seqTypes:
        if query in [None,'']:
            print 'Please provide one or more CR numbers to unlink from %s'%branch
            sys.exit()
        query = [query]
    crList = query

    db=options.debug
    msg = 'Connecting to SalesForce for the branch %s in code stream %s' %(branch,stream)
    print msg
    sfb = SFTaskBranchActionTool(debug=options.debug,logname=logname)
    brObj = SFTaskBranchAction(sfTool=sfb)
    sfb.getConnectInfo(version, st)
    inlist = brObj.loadBranch(branch, stream, team='', label='')
    msg = ' %s '%(inlist[:5])  # [numCLs,numBAs,status,branch,stream]
    if db>1:print msg
    if db>2: brObj.showData(target='user')
    sfCLs = brObj.getData('Branch_CR_Link__c')
    sfBAs = brObj.getData('Branch_Approval__c')
    tbInfo = brObj.getData('Task_Branch__c')
    tbStatus = tbInfo.get('Branch_Status__c','Open')
    msg = '\n%s existing CR(s) are linked to %s in %s with status %s\n'%(len(sfCLs),branch,stream, tbStatus)
    print msg
    crInfos = {}
    delCRInfo = {}
    for clInfo in sfCLs:
        crId = clInfo.get('Case__c','')
        clId = clInfo.get('Id','')
        crInfo = sfb.getCrById(crId)
        if crInfo in [None,{}]: continue
        crNum = '%s'%int(crInfo.get('CaseNumber',''))
        crSub = crInfo.get('Subject')
        crStat= crInfo.get('Status')
        crCSP = crInfo.get('Code_Streams_Priority__c')
        if crNum in crList:
	    msg = 'Ready to unlink the CR %s with status:%s subject:%s' %(crNum,crStat,crSub)
            print msg
            delCRInfo[crNum] = {'clId':clId, 'status':crStat, 'subject':crSub, 'crId':crId, 'csp':crCSP}
        else:
            crInfos[crNum] = {'crId':crId, 'status':crStat, 'subject':crSub, 'csp':crCSP}
	    msg = 'Did not unlink the CR %s with status:%s subject:%s' %(crNum,crStat,crSub)
    sfCRs = crInfos.keys()

    # Now know what exists in SF now
    for crNum, info in delCRInfo.items():
        id = info.get('clId')
	msg = '\tUnlinked CR:%s  %s\n'%(crNum,info.get('subject'))
        print msg
        num = brObj.delCRFromTaskBranch(crNum)
	msg = '\t  updated CR list in %s Branch Approvals in %s'%(num, branch)
    msg = 'There are %s CRs still linked to %s in %s' %(len(sfCRs),branch,stream)
    print msg

    msg = []
    msg.append("Task Branch InFo %s"%tbInfo)
    msg.append("TASK BRACNH ID.............. %s" %tbInfo.get('Id'))
    data = {'Id': tbInfo.get('Id'), 'Num_CRs__c': len(sfCRs)}
    res = sfb.update('Task_Branch__c', data)
    
    if len(crInfos.items()):
        brObj.setBranchStatus()
        pass

    brObj.refresh()
    
    from walkSF import checkCL
    # you're not seeing double here - have to run the check twice...
    checkCL(branch, stream)
    checkCL(branch, stream)

    for crNum, info in crInfos.items():
	msg = '  CR:%s streams:%s \tStatus:%12s\t Subject:%s'%(crNum,info.get('csp'),info.get('status'),info.get('subject'))
        print msg

########################################################################################################
def mvTBUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = '%s\n' %err
    m += '  This script will merge a number of Task Branches (TBs) on SalesForce.\n'
    m += '    Use one of the forms below to meet your needs.\n'
    m += ' \n'
    m += '    mvBR -s 4.1 -b <branch_Name> <branch to merge from1>  \n'       
    m += ' \n'
    m += '      or - indicate this is a team branch \n'
    m += '    mvBR -s 4.1 -b <branch_Name> -t <Team Branch> <branch to merge from1>  \n'       
    m += ' \n'
    return m

def mvBranchCL(branch, stream, query, options):
    """ command line logic for mvBranch
    """
    db=options.debug
    msg = []
    msg.append('Connecting to SalesForce for the branch %s in code stream %s' %(branch,stream))
    print msg[0]
    sfb = SFTaskBranchActionTool(debug=db,logname='movTB')
    msg.append('Not implemented yet, stay tuned')
    print msg[1]

def cloneTbUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = ''

    m += 'Clone a task branch in one code stream into another stream.\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    clonebranch -s <stream> -b <branch_Name> -x <new stream>\n'
    m += '      (clones the task branch)\n\n'
    m += '    clonebranch -s <stream> -b <branch_Name> -x <new stream> -n <team name>\n'
    m += '      (clones the task branch and links clone to the specified team)\n'
    return m

def cloneTbCL(branch, stream, newstream, options, st):
    """
    clone branch in stream to newstream
    cloned branch will be in 'Fixing' state and must be submitted
    """
    logname = 'cloneTB'
    db = options.debug
    sfb =  SFTaskBranchActionTool(debug=db,logname=logname)

    sfbTeam = SFTeamBranchTool(debug=db, setupLog=False)
    sfbTeam.setLogger(name=logname, note=sfb.note, logger=sfb.log, dlogger=sfb.dlog, elogger=sfb.elog, clogger=sfb.clog)
    pteam = None
    if options.team not in [None, '']:
        pteam = options.team
        # check that team is valid
        if sfbTeam.isValidProductTeam(pteam) is False:
	    msg = 'The team name "%s" is unknown.\nFor a list of known teams, please use the "teams" command. EXITING' %pteam
            print msg
            sys.exit(1)
        pass

    msg = 'see if a brnach by this name already exists in the new stream'
    testTbObj = SFTaskBranchAction(sfTool=sfb)
    testTbStats = testTbObj.loadBranch(branch, newstream)

    if testTbStats[2] != '':
        # Error - clone target already exists!
        msg = "Task branch %s already exists in code stream %s. Exiting." % (branch, newstream)
        print msg
        sfb.setLog(msg, 'error')
        sys.exit(1)
        pass
    
    testTbObj = None

    origTbObj = SFTaskBranchAction(sfTool=sfb)
    origTbStats = origTbObj.loadBranch(branch, stream)
    origBaList = origTbObj.getData('Branch_Approval__c')

    if origTbStats[0] == 0 and origTbStats[1] == 0:
        # original branch not found
        pass
    
    newTbObj = origTbObj.cloneBranch(newstream)

    newTbObj.cloneBranchApprovals(origBaList)

    newTbObj.refresh()

    from walkSF import checkCL
    checkCL(branch, newstream)

    # now, do we need to link to a team branch?
    if pteam is not None:
	msg = '  Adding this Task Branch to the Team Branch %s'%pteam
        print msg
        addTeamBranchCL(pteam, None, branch, newstream, options, st, teamTool=sfbTeam)
        

    msg = []
    msg.append('\nClone of %s into code stream %s has completed.' % (branch, newstream))
    msg.append('\nYou will need to run "submitbranch" on the cloned task branch.' )
    print ''.join(msg)

    return

##############################################################################
def submitBranchUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = ''
    
    if len(err):
        m += '%s\n\n' %err
        
    m += 'This script will submit a Task Branch (TB) for approval on Salesforce.\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    submitbranch [OPTIONS] -s <stream> -b <branch_Name> \n'       
    m += '\n'
    m += 'Options include:\n'
    m += '    -m    (flag to prompt for merge details)\n'
    m += '\n'
    m += '    -w    (flag to bypass mudflow check)\n'
    return m

def submitBranchCL(branch, stream, query, options):
    """ command line logic for submitBranch
    """
    
    #print 'Submitbranch script will be unavailable from Friday 1700 July 28 till Sunday 1900 July 30, due to ITs major outage for R&D and AE Unix environments'
    #sys.exit(1)
    
    msg = 'Connecting to SalesForce for the branch %s in code stream %s' %(branch,stream)
    print msg
    st = time.time()
    db=options.debug
    sfb = SFTaskBranchActionTool(debug=db,logname='subTB')
    brObj = SFTaskBranchAction(sfTool=sfb)
    sfb.getConnectInfo(version,st)

    inlist = brObj.loadBranch(branch, stream)
    tbInfo = brObj.getData('Task_Branch__c')
    if tbInfo in [{}]:
	msg = "Could not find Task Branch %s in stream %s" %(branch, stream)
        print msg
        sys.exit(1)
        pass
    
    tbId = tbInfo.get('Id')    

    # C.T Jun30 (invoke mudflow checks)
    msg = []
    msg.append("\nChecking this branch against ClearCase through mudflow.")
    msg.append("\tThis may take up to several minutes, depending on how many files")
    msg.append("\tare a part of your branch.")
    print ''.join(msg)

    mudflowObj = None
    try: 
        passmud=False  
        if options.part is True:  
            passmud=True    
	    msg = "MUDFLOW CHECK BYPASSED"
        mudflowObj = MudflowWrap.remoteMudflow(branch,passmud,stream)            
        
    except Exception, e:
        msg = "Mudflow could not process branch %s\n" %branch
        msg += "Exception caught was %s\n" %e
        msg += "Additional traceback in the log - submission cannot continue\n"
        msg2 = sys.exc_info()[2]
        sfb.setLog(msg, 'error')
        sfb.setLog(msg2, 'error')
        """sys.exit(1)"""
        pass
    
    # check for inadequate classification here...
    # notify dev that we can't submit
    # and send alarm to sf_mudflow
    partData={}
    if mudflowObj is not None:  
        if options.part is False:   
            #print "MUDFLOW CHECK FOR ERROR MESSAGE *********************"
            #print mudflowObj.checkMudflow(force_submission=options.force)
            if mudflowObj.checkMudflow(force_submission=options.force) is False:            
		msg = []
		msg.append("errors detected...")
		msg.append("\n\n")
                print mudflowObj.errorReport(force_submission=options.force)
		msg.append("\nPlease review the above error report completely,")
		msg.append("and correct the issue(s) in order to submit your branch.")
		msg.append("Mudflow checking by passed DUE to the error in receiving the XML data.")
                print '\n'.join(msg)
                sys.exit(1)
                pass  
            pass  
        
        partData = mudflowObj.getPartitionViolationDict()
    
    tbUpdInfo = {'Id': tbId}

    if options.mdesc is True:
        msg = "\nPlease enter the specific MERGE Instructions for this Task Branch"
        details = tbInfo.get('Merge_Details__c','')
        if len(details): details += '\n'
        details += inputTextFromEditor(msg)
        tbUpdInfo['Merge_Details__c'] = details
        pass

    # Demand details if we're forcing passage despite certain mudflow errors.
    forceReason = None
    if options.force is True:
        msg = "\nPlease provide details as to why you are bypassing the following checks:\n"
        reasonsNeeded = ""
        if mudflowObj is not None:            
            if mudflowObj.hasTest() is False:
                reasonsNeeded += " * Required unit tests not found\n"
                pass
    
            if mudflowObj.hasCleanBackMerge() is False:
                reasonsNeeded += " * Files require a backmerge\n" 
                pass

        msg += reasonsNeeded
        msg += "The reasons you provide will be sent to SCM, so providing inadequate\n"
        msg += "information may result in your branch being rejected.\n"
        reasonsGiven = inputTextFromEditor(msg)

        forceReason = "The developer has provided an explanation as to why the following checks were bypassed:\n"
        forceReason += "%s\n\n" %reasonsNeeded
        forceReason += reasonsGiven

        details = tbInfo.get('Details__c','')
        if len(details) > 0: details += '\n'
        details += forceReason
        tbUpdInfo['Details__c'] = details

    if len(tbUpdInfo) > 1:
        sfId = brObj.setTaskBranch(id=tbId, data=tbUpdInfo)

    if len(partData) > 0:
        # print a notice regarding partition violations here
        msg  = "\n\nNOTE: The following file(s) violate partition boundaries.\n"
        msg += "Your branch will need to be approved by each partition reviewer listed below.\n"
        msg += "Each partition reviewer has been notified that they need to\n"
        msg += "review and approve or reject your branch.\n\n"
        print msg

        for reviewerAlias, partInfo in partData.items():
	    msg = "Reviewer: %s\n" % reviewerAlias
            print msg

            partNames, partComment = brObj.buildPartitionFileComment(partInfo)
            print partComment
            print "-"*30
            continue
        pass

    num = brObj.submitByDev(branch, stream, st, partData)

    if forceReason is not None:
        sendMudflowForceNotification(sfb, tbInfo, forceReason)

	msg = []
	msg.append('send a notification to the sf_mudflow list with the branch,')
	msg.append('developer and reasons for bypassing unit tests and/or')
	msg.append('backmerge')
        pass
    
    print '' # blank line for formatting goodness
    if num >0:
	msg = ' Submitted and notified %s user(s) for %s %s' % (num,branch,stream)
        print msg
    elif num == -1:
	msg = ' No Task Branches were found for %s in stream %s' % (branch,stream)
        print msg
	if db >2:
            tbInfo = sfb.getBranchMapCC(branch)
	    msg = ' Info from Clearcase is %s'%tbInfo
            print msg
    elif num == -2:
	msg = []
	msg.append(' No Branch may be submitted for approval without a linked CR')
	msg.append(' lncr -s %s -b %s <CR1> <CR2> ..'%(stream, branch))
	print '\n'.join(msg)
    elif num == 0:
	msg = []
	msg.append('need to tune the return of submitBranch to correctly return number of notified users and ther names')
	msg.append(' Nothing needs to be done for Task Branch %s in stream %s'%(branch,stream))
	print msg[-1]
    return 0

########################################################################################################
def approveBranchUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = ''
    
    if len(err):
        m += '%s\n\n' %err
        
    m += 'This script will approve a Task Branch (TB) on Salesforce.\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    approvebranch -s <stream> -b <branch_Name> \n'       
    return m

def approveBranchCL(branch, stream, query, options):
    """ command line logic for approveBranch
    """
    msg = 'Connecting to SalesForce for the branch %s in code stream %s' %(branch,stream)
    print msg
    st = time.time()
    db=options.debug
    sfb = SFTaskBranchActionTool(debug=db,logname='appTB')
    brObj = SFTaskBranchAction(sfTool=sfb)
    sfb.getConnectInfo(version,st)
    num, role = brObj.approveBranch(branch, stream, st)
    if num >0:
	msg = ' Approved and notified %s users for %s %s'%(num,branch,stream)
        print msg
    elif num == -1:
	msg = []
	msg.append(' No Task Branches were found for %s in stream %s'%(branch,stream))
        tbInfo = sfb.getBranchMapCC(branch)
	msg.append(' Info from Clearcase is %s'%tbInfo)
        print '\n'.join(msg)
    elif num == 0:
	msg = ' Nothing for you to approve on Task Branch %s in stream %s'%(branch,stream)
        print msg
    return 0

def rejectBranchUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = ''
    
    if len(err):
        m += '%s\n\n' %err
        
    m += 'This script will reject a Task Branch (TB) on Salesforce.\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    rejectbranch -s <stream> -b <branch_Name> \n'       
    return m

def rejectBranchCL(branch, stream, query, options):
    """ command line logic for submitBranch
    """
    msg = 'Connecting to SalesForce for the branch %s in code stream %s' %(branch,stream)
    print msg
    st = time.time()
    db=options.debug
    sfb = SFTaskBranchActionTool(debug=db,logname='rejTB')
    brObj = SFTaskBranchAction(sfTool=sfb)
    sfb.getConnectInfo(version,st)
    num = brObj.rejectBranch(branch, stream, st)
    if num >0:
	msg = ' Rejected and notified %s users for %s %s'%(num,branch,stream)
        print msg
        return num
    elif num == -1:
	msg = []
	msg.append(' No Task Branches were found for %s in stream %s'%(branch,stream))
        tbInfo = sfb.getBranchMapCC(branch)
	msg.append(' Info from Clearcase is %s'%tbInfo)
        print '\n'.join(msg)
    elif num == 0:
	msg = ' No CRs have been linked to the Task Branch %s in stream %s'%(branch,stream)
        print msg
    return 0

def submitToSCMUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = '%s\n' %err
    m += '  This script directly submits a Task Branches (TBs) to SCM.\n'
    m += '    Use one of the forms below or a combination to meet your needs.\n'
    m += ' \n'
    m += '    submitscm -s4.1 -b<branch_name> \n'       
    m += ' \n'
    m += '    submitscm -s4.1 -b<branch_name> \n'       
    m += ' \n'
    return m

def submitToSCMCL(branch, stream, query, options):
    """ just create a new SCM token from this branch """
    st = time.time()
    db=options.debug
    sfb = SFTaskBranchActionTool(debug=db,logname='mkSCM')
    brObj = SFTaskBranchAction(sfTool=sfb)
    sfb.getConnectInfo(version,st)
    inlist = brObj.loadBranch(branch, stream)
    _msg = []
    _msg.append('submitToSCM for %s %s loadBranch:%s'%(branch,stream,inlist))
    msg = brObj.postSCMTokenAndNotify()
    _msg.append('Output of postSCMTokenAndNotify() is:%s'%msg)
    print '\n'.join(_msg)

def lsBRsUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = ''
    
    if len(err):
        m += '%s\n\n' %err
        
    m += 'This script lists your Task Branches (TBs) on SalesForce.\n'
    m += '    NOTE: The output from this command may be very long!'
    m += '\n'
    m += 'Usage:\n'
    m += '    lsbrs [OPTIONS] -s <stream>\n'
    m += '      (stream may be a stream number or "all" for all active streams)\n'       
    m += '\n'
    m += 'Options include:\n'
    m += '    -x min        (show your branches in with minimal output)\n'
    m += '    -u <username> (show branches for a particular user)\n'
    return m

def getMyBranches(stream='all', user='my', show='list', options=None):
    """ command line logic for lsbrs - listBranches
    """
    db=options.debug
    if show not in ['min']:
	msg = 'Connecting to SalesForce to show %s branches %s in %s code stream ' %(user, show, stream)
        print msg
    sfb = SFTaskBranchActionTool(debug=db,logname='lsTBs')
    dlist = sfb.getMyBranches(user=user, stream=stream, show=show)
    for info in dlist:
        print ' %s'%info
    return len(dlist)

def listBranchUsage(err=''):
    """ Prints the usage stmt for listBranch """
    m = ''
    
    if len(err):
        m += '%s\n\n' %err
        
    m += 'List status information for a single branch.\n'
    m += '\n'
    m += 'Usage:\n'
    m += '    lsbr -s <stream> -b <branch_Name>\n'
    return m

def listBranchCL(branch, stream, query, options):
    """ command line logic for lsbr - listBranch
    """
    db=options.debug
    msg = 'Connecting to SalesForce for the branch %s in code stream %s' %(branch,stream)
    print msg

    sfb = SFTaskBranchActionTool(debug=db,logname='lsTB')
    tbObj = SFTaskBranch(sfTool=sfb)
    
    msg = "Running lsbr on %s in stream %s" %(branch, stream)
    sfb.setLog(msg, 'info')
    
    tbInfo = tbObj.loadBranch(branch, stream)
    if tbInfo[0] == 0 and tbInfo[1] == 0:
        ret = "\nNo task branch %s found in stream %s\n" %(branch, stream)
    else:
        ret = tbObj.showBranch()
        pass
    ret=ret.encode("utf-8")     
    print ret

def walkSFCL(secsAgo, stream, options):
    """ command line logic for walkSF
    """
    db=options.debug
    msg = 'Connecting to SalesForce for the branch %s in code stream %s' %(branch,stream)
    print msg
    sfb = SFTaskBranchActionTool(debug=db,logname='walkSF')
        
def getALLBranchApprovals(num, options):
    """ """
    db=options.debug
    if num in ['all']: num = 10000
    else:              num = int(num)
    msg = 'Checking on %s of the Branch approval objects'%num
    print msg
    sfb = SFTaskBranchActionTool(debug=db)
    allBAUsers = sfb.getBAUsers()
    total = len(allBAUsers)
    num = 0
    numWarn = 0
    msg = []
    msg.append('FOUND %s Owners of Branch Approvals'%total)
    msg.append('Now will display the status of all approvals')
    print '\n'.join(msg)
    tbObj = SFTaskBranch(sfTool=sfb,debug=db)
    for uid in allBAUsers:
        num += 1
        res = sfb.getMyApprovals(uid=uid, stream=None, branch=None, show=False, getTB=False)
        print ' \n'

def getMyBranchApprovals(options):
    """ """
    db=options.debug
    sfb = SFTaskBranchActionTool(debug=db, logname='getMyBA')
    myBAList = sfb.getMyApprovals(uid=sfb.uid)
    total = len(myBAList)
    num = 0
    baIds = []
    msg = 'FOUND %s Branch Approvals'%total
    print msg
    for info in myBAList:
        num += 1
        baId = info.get('Id')
        name = info.get('Name')
        role = info.get('Approval_Role__c')
	msg = '%15s %s'%(role,name)
        print msg
        continue

def getLatestBA(options, secsAgo=None):
    """ """
    db=options.debug
    #entity = 'Task_Branch__c'
    entity = 'Branch_Approval__c'
    msg = 'Checking on latest %s '%entity
    print msg
    sfb = SFTaskBranchActionTool(debug=db,logname='getBA')
    if secsAgo not in [None,0,'']:
        latestList, actionNeeded = sfb.getLatestTBA(secsAgo)      #secAgo is only parm
    else:
        latestList, actionNeeded = sfb.getLatestTBA()      #secAgo is only parm
    total = len(latestList)
    msg = 'FOUND %s %s items'%(total, entity)
    print msg
    #tbObj = SFTaskBranch(sfTool=sfb,debug=options.debug)

def setTaskBranchStatusCL(stream, branch, opts):
    status = opts.status

    sfb = SFTaskBranchTool(logname='sf.tbStat', debug=opts.debug)
    tbObj = SFTaskBranch(sfTool=sfb)

    tbObj.loadBranch(branch, stream)

    updated = None
    if status is None:
        updated = tbObj.setBranchStatus()
    else:
        status = re.sub('_', ' ', status)
        updated = tbObj.setBranchStatus(status)
        pass
    
    print updated
    return
## END setTaskBranchStatusCL

def scmRejectBranchUsage(err=''):
    """  Prints the Usage() statement for this method    """
    m = '%s\n' %err
    m += '  This script allows SCM to reject a task branch that has passed its approvals back\n'
    m += '    to the developer with a status of "Rejected by SCM." This status is\n'
    m += '    equivalent to "Fixing." Additionally, if the task branch is linked to a\n'
    m += '    team branch, it will be moved back to that team\'s receiving bin\n'
    m += ' \n'
    m += '    scmrejectbranch -s<stream> -b<branch_name> \n'       
    m += ' \n'
    m += '    scmrejectbranch -s<stream> -b<branch_name> -n<team name>\n'
    m += '       (rejects the branch to a specific team\'s receiving bin)\n'
    m += ' \n'
    return m

def scmRejectBranchCL(branch, stream, options, team=None, st=0):
    logname = 'scmRej'
    minStatus = 'Approved, pending Branch'
    maxStatus = 'SCM-Approved'

    db=options.debug
    msg = 'Connecting to SalesForce for the branch %s in code stream %s' %(branch,stream)
    print msg
    sfb = SFTaskBranchActionTool(debug=db, logname=logname)

    brObj = SFTaskBranchAction(sfTool=sfb)
    sfb.getConnectInfo(version,st)

    # get out base status info
    minStatMap = sfb.getStatMap(minStatus)
    maxStatMap = sfb.getStatMap(maxStatus)

    # are we allowed to run this script?
    fields = ('Id', 'Name')
    where = [['Name','like','%SCM%'],'or',['Name','=','Corp - System Admin']]
    roles = sfb.query('UserRole', where, fields)
    roleIds = []
    for role in roles:
        if type(role) == DictType:
            roleIds.append(role.get('Id'))
            pass
        continue

    fields = ('Id','UserRoleId', 'IsActive')
    users = sfb.retrieve([sfb.uid], 'User', fields)
    user = users[0]
    if user.get('IsActive') == 'false' or user.get('UserRoleId') not in roleIds:
        msg = "You do not have sufficient priviliges to run this script. Exiting"
        print msg
        msg += "\n\tUser: %s" %sfb.uid
        sfb.setLog(msg, 'error')
        sys.exit(1)

    # load the task branch object
    inlist = brObj.loadBranch(branch, stream, team='', label='')
    (numCRs, numBAs, status, branch2, stream2, numBTLs) = inlist

    # did we load the branch correctly?
    if numCRs == 0 and numBAs == 0:
        msg = "Task branch %s in %s has not loaded properly. Check the spelling" %(branch, stream)
        sfb.setLog(msg, 'error')
        print msg
        sys.exit(1)

    # is the branch in a status where SCM rejection makes sense?
    brStatMap = sfb.getStatMap(status)
    if brStatMap.get('order', 0) < minStatMap.get('order', 100) or \
           brStatMap.get('order', 0) >= maxStatMap.get('order', 0):
        msg = "Branch is in a status not eligible for SCM rejection" 
        print msg
        sys.exit(1)

    # change branch status to rejected by SCM
    brObj.submitAndNotify('Rejected by SCM')

    # do we have to look at the team branch, too?
    if numBTLs > 0:
        btlInfo = brObj.getData('Branch_Team_Link__c')[0]
        teamName = btlInfo.get('Team__c')
        oldTmbId = btlInfo.get('Team_Branch__c')

        sfbTeam = SFTeamBranchTool(debug=db, setupLog=False)
        sfbTeam.setLogger(name='scmRejTmb', note=sfb.note, logger=sfb.log,
                          dlogger=sfb.dlog, elogger=sfb.elog, clogger=sfb.clog)
        
        if team is None:
            team = teamName
            pass

        if sfbTeam.isValidProductTeam(team) is False:
            msg =  "The team name '%s' is invalid and this script cannot continue.\n"
            msg += "The task branch has been rejected, but it may need to be moved to the\n"
            msg += "proper team's receiving bin. Please check this branch in salesforce\n"
            msg += "and use teammv if necessary to move this task branch to the\n"
            msg += "proper team receiving bin.\n"
            print msg
            sys.exit(1)

        # attempt to load the task branch by ID.
        tmbObj = SFTeamBranch(sfTool=sfbTeam)
        tmbObj.loadBranchById(oldTmbId)
        tmbInfo = tmbObj.getData('Team_Branch__c')
        teamRecvBinName = tmbInfo.get('Name')

        # check if we're already in the team's receiving bin
        if teamRecvBinName != teamName:
            # not in rec'v bin. Need to sweep.
            num = sweepTeamBranchFlow(teamRecvBinName, teamName, stream,
                                      logname=logname,
                                      branchList=str(branch))
            # check for return of 1

        else:
            # already in the proper team rec'v bin
            pass
        pass

def validateBranch(branch):
    """ Check that branch/label contains only valid characters """
    if not re.match(r'\w[\w\._]+$', branch):
        return False
    return True

def doSomething(method, term, parm, options):
    """  Command line controlled test of a method """
    msg = []
    msg.append('You called me with method:%s term:%s parm:%s ' %(method, term, parm))
    msg.append('Hope it was good for you')
    print '\n'.join(msg)

##################################################################################################
#  Commandline management methods.  Minimal logic, just command parm processing
##################################################################################################
def mainTaskUsage():
    """ Prints the shell-script wrapped command line usage """

    m =  'TASK BRANCH COMMAND SUMMARY\n\n'
    m += 'Issue any of these commands with no arguments to\n'
    m += 'see help for that specific command.\n\n'
    m += 'Process Flow Commands:\n'
    m += ' * lncr -s <stream> -b <task branch> -n <team name> CR1 [CR2 CR3 ...]\n'
    m += '   (a.k.a. addmod)\n'
    m += '   Links one or more CRs with a task branch to indicate that the \n'
    m += '   task branch addresses the specified CR(s).\n'
    m += '   Note: Use team name of "None" to create an individual task branch.\n'
    m += '\n'
    m += ' * submitbranch -s <stream> -b <task branch>\n'
    m += '   Allows the developer of a task branch to submit it for\n'
    m += '   manager approval\n'
    m += '\n'
    m += ' * approvebranch -s <stream> -b <task branch>\n'
    m += '   Allows the engineering manager or the approving PE to give\n'
    m += '   approval to a branch, allowing it to flow to the next step\n'
    m += '\n'
    m += ' * rejectbranch -s <stream> -b <task branch>\n'
    m += '   Allows the engineering manager or the approving PE to reject a\n'
    m += '   branch, requiring additional attention from the developer\n'
    m += '   before proceeding to the next step.\n'
    m += '\n'
    m += 'Reporting Commands:\n'
    m += ' * lsbr -s <stream> -b <task branch>\n'
    m += '   List the status of a branch and its approvals.\n'
    m += '\n'
    m += ' * lsbrs\n'
    m += '   List all your branches.\n'
    m += '\n'
    m += ' * lsba\n'
    m += '   List branch approvals that you have not yet approved.\n'
    m += '\n'
    m += 'Additional Utilities:\n'
    m += ' * unlinkcr (a.k.a. rmmod)\n'
    m += '   Removes a CR link from a task branch.\n'
    m += '\n'
    m += ' * task (a.k.a. branch)\n'
    m += '   Prints this command summary.\n'
    m += '\n'
    m += ' * team\n'
    m += '   Prints the command summary for team branch operations.\n\n'
    return m

def usage(cmd='', err=''):
    """  Prints the Usage() statement for the program    """
    m = '%s\n' %err
    m += '  Default usage is to link a CR with a Task Branch (TB) on SalesForce.\n'
    m += ' '
    m += '    sfTaskBranchAction.py -a lncr -s4.1 -b<branch_Name> CR1 CR2 CR3  \n'       # addMod
    m += '      or\n'
    m += '    sfTaskBranchAction.py -a lncr -s4.1 -b<branch_Name> -r -e -d CR1 CR2 CR3  \n'       # addMod
    m += '      or\n'
    m += '    sfTaskBranchAction.py -a rmcr -s4.1 -b<branch_Name> CR1 CR2 CR3  \n'       # rmMod
    m += '      or\n'
    m += '    sfTaskBranchAction.py -a mvbr -s4.1 -b<branch_Name> <source task branch>\n'# mvBranch
    m += '      or\n'
    m += '    sfTaskBranchAction.py -a submit -s4.1 -b<branch_Name> <merge comments up to 255 chars>  \n' # submitBranch
    m += '      or\n'
    m += '    sfTaskBranchAction.py -a approve -s4.1 -b<branch_Name> -p<approve OR reject> <any text> \n'  # approveBranch
    m += '      or\n'
    m += '    sfTaskBranchAction.py -a ls -s4.1 -b<branch_Name> <any text>  \n'
    m += '      or\n'
    m += '    sfTaskBranchAction.py -a walk -s4.1 <any text>  \n'
    return m

def main_CL():
    """ Command line parsing and and defaults methods
    """
    parser = OptionParser(usage=mainTaskUsage(), version='%s'%version)
    parser.add_option("-a", "--cmd",   dest="cmd",   default="get",      help="Command type to use.")
    parser.add_option("-x", "--parm",  dest="parm",  default="",         help="Command parms.")
    parser.add_option("-s", "--cs",    dest="cs",    default=DEFAULT_STREAM,        help="Code Stream of Branch")
    parser.add_option("-b", "--br",    dest="br",    default="",         help="Branch Label")
    parser.add_option("-t", "--tbr",   dest="tbr",   default="",         help="Team Branch Label")
    parser.add_option("-n", "--team",   dest="team",   default="",         help="Team Name")
    parser.add_option("-p", "--priority",dest="priority",default="Low", help="Branch Priority: Low, Medium, High, Urgent, Critical")
    parser.add_option("--status", dest="status", default=None,
                      help="status to set on task branch")
    parser.add_option("--forcenew", dest="force", default=False,
                      action="store_true",
                      help="Bypass certain Mudflow error checks. "
                      "An explanation must be given as to why you are bypassing the check(s)")

    yesnochoices = ['Yes','YES','yes','y','Y','No','NO','no','n','N']

    riskgr = OptionGroup(parser, "Branch Risk Options","Assign risk to the Branches(s) using the following options.")
    riskgr.add_option("-r", "--risk",  dest="risk",  default=False, action="store_true", help="Designate mod as High Risk")
    riskgr.add_option("-c", "--cmdchg",dest="cmdchg",default=None, action="store", choices=yesnochoices, help="Designate branch as having a Command Change")    
    riskgr.add_option("-v", "--volcanochg",dest="volchg",default=None, action="store", choices=yesnochoices, help="Designate branch as having a Volcano Change")    
    parser.add_option_group(riskgr)

    textgr = OptionGroup(parser, "Description Options","Add text description using the options below ")
    textgr.add_option("-d", "--desc",  dest="desc",  default=False, action="store_true", help="General description details")
    textgr.add_option("-e", "--rdesc", dest="rdesc", default=False, action="store_true", help="Risk description details")
    textgr.add_option("-o", "--cdesc", dest="cdesc", default=False, action="store_true", help="Command Change description details")
    textgr.add_option("-m", "--mdesc", dest="mdesc", default=False, action="store_true", help="Merge description details")
    textgr.add_option("-w", "--part", dest="part", default=False, action="store_true", help="By Pass mudflow")
    textgr.add_option("-f", "--path",  dest="path",  default="./details.txt", help="Path to details file.")
    parser.add_option_group(textgr)

    parser.add_option("-u", "--user",  dest="user",  default="my",       help="User alias on sForce")
    parser.add_option("-z", "--trace", dest="trace", default="soap.out", help="SOAP output trace file.")
    parser.add_option("--debug", dest='debug', action="count",     help="The debug level, use multiple to get more.")
    parser.add_option("-l", "--listBranchPath", dest="listBranchPath", default=None, help="no help available")
    
    if (sys.platform == 'win32'):
	(options, args) = parser.parse_args(args=sys.argv)
    else:
	(options, args) = parser.parse_args()
    
    if options.debug > 1:
	msg = []
	msg.append(' cmd  %s, parms  %s' %(options.cmd, options.parm))
	msg.append(' stream %s, branch %s, team   %s' %(options.cs, options.br, options.tbr))
	msg.append(' risk %s, cmdchg %s' %(options.risk, options.cmdchg))
	msg.append(' desc %s, risk desc %s, cmd desc %s merge desc %s' %(options.desc, options.rdesc, options.cdesc, options.mdesc))
	msg.append(' path   %s, trace  %s, debug  %s' %(options.path,options.trace ,options.debug))
	msg.append(' args:  %s' %args)
        print '\n'.join(msg)
    else:
        options.debug = 0
        
    if len(args) > 0: 
        st = time.time()
        parm = options.parm
        query = args[1:]

        # parse the stream
        if options.cs in [None,'']: stream = DEFAULT_STREAM
        else: stream = options.cs
        
	stream = str(stream).strip()
        stream = stream.lower()

	if stream[:5] == "blast" and \
           stream not in ACTIVE_STREAMS and \
           stream[5:] in LEGACY_STREAMS:
            stream = stream[5:]
            print "Stream %s" %stream
        elif stream in LEGACY_STREAMS:
            # honor legacy "number only" streams for 4 and lower.
            if stream == '5':                
                stream = 'blast%s' %stream
                #print "Error: '%s' is not a valid stream." %(stream)
                #sys.exit(1)
                pass
        elif "blast%s" %stream in ACTIVE_STREAMS:
            print "Error: '%s' is not a valid stream. You must use the full name, 'blast%s'." %(stream, stream)
            sys.exit(1)
        
        elif stream not in ACTIVE_STREAMS and stream != '':
            print "Error: '%s' is not a valid stream." %(stream)
            sys.exit(1)
            pass

        if options.cmd in ['mkcr','addmod','addcr','lncr']:
            if options.br in [None,''] or stream in [None,'']: 
                print '%s' %addModUsage('You must provide a least a valid stream, branch or label and a CR number!')
                sys.exit()
            elif validateBranch(options.br) is False:
                print '%s' %addModUsage('Branch or label "%s" contains invalid characters!\nOnly letters (upper and lower case), numbers, period (.) and underscore (_)\nare allowed.' %options.br)
                sys.exit()
            elif options.team in [None,'']:
                print '%s'  %addModUsage("You must provide a team name using -n.\nView valid team names using the 'teams' command.\nTo really create an individual task branch, use '-n none'")
                sys.exit()
            elif options.cmdchg is None:
                print '%s'  %addModUsage("You must specify whether or not your branch has a command change with '-c (yes|no)'")
                sys.exit()
            elif options.volchg is None:
                print '%s'  %addModUsage("You must specify whether or not your branch has a volcano change with '-v (yes|no)'")
                sys.exit()
                
            branch = options.br
            addModCL(branch, stream, query, options, st)
            
        elif options.cmd in ['rmcr','rmmod','delmod','delcr']:
            print "doing rmcr"
            if options.br in [None,''] or stream in [None,'']: 
                print '%s' %rmModUsage('You must provide a least a valid stream and branch or label!')
                sys.exit()
            branch = options.br
            rmModCL(branch, stream, query, options, st)
            
        elif options.cmd in ['mvbr','merge']:
            if options.br in [None,''] or stream in [None,'']: 
                print '%s' %mvTBUsage('You must provide a least a branch label!')
                sys.exit()
            branch = options.br
            mvBranchCL(branch, stream, query, options)

        elif options.cmd in ['clone']:
            if options.br in [None,''] or stream in [None,''] \
                   or parm in [None, '']: 
                print '%s' %cloneTbUsage('You must provide a task branch, stream and a new stream to clone into')
                sys.exit()
            branch = options.br
            cloneTbCL(branch, stream, parm, options, st)
            
        elif options.cmd in ['submit','submitbranch']:
            if options.br in [None,''] or stream in [None,'']: 
                print '%s' %submitBranchUsage('You must provide a least a valid stream and branch or label!')
                sys.exit()
            branch = options.br
            submitBranchCL(branch, stream, query, options)
            
        elif options.cmd in ['reject','rejectbranch']:
            if options.br in [None,''] or stream in [None,'']: 
                print '%s' %rejectBranchUsage('You must provide a least a valid stream and a branch or label!')
                sys.exit()
            branch = options.br
            rejectBranchCL(branch, stream, query, options)

        elif options.cmd in ['approve','approvebranch']:
            if options.br in [None,''] or stream in [None,'']: 
                print '%s' %approveBranchUsage('You must provide a least a valid stream and a branch or label!')
                sys.exit()
            branch = options.br
            approveBranchCL(branch, stream, query, options)
            
        elif options.cmd in ['toscm','submitscm']:
            if options.br in [None,''] or stream in [None,'']: 
                print '%s' %submitToSCMUsage('You must provide a least a valid stream and a branch or label!')
                sys.exit()
            branch = options.br
            submitToSCMCL(branch, stream, query, options)
    
        elif options.cmd in ['ls','list']:
            if options.br in [None,''] or stream in [None,'']: 
                print '%s' %listBranchUsage('You must provide a least a valid stream and branch or label!')
                sys.exit()
            branch = options.br
            listBranchCL(branch, stream, query, options)
            
        elif options.cmd in ['lsbrs','listbranches']:
            if query in [None,'']:
                print lsBRsUsage()
                sys.exit()
            user = options.user
            if options.parm not in ['min', 'list','info','all']: show = 'list'
            else: show = options.parm
            n = getMyBranches(stream, user, show, options)
            if n == 0:
                print lsBRsUsage()

        elif options.cmd in ['listapprovals']:
            try: num = int(query)
            except: num = 2000
            getALLBranchApprovals(num, options)

        elif options.cmd in ['lsba','myba','myapprovals']:
            if options.parm not in ['del', 'list','info']: do = 'list'
            else: do = options.parm
            if do == 'list':
                getMyBranchApprovals(options)
            else:
                print 'I will not do %s'%do


        elif options.cmd in ['walk','sfwalk']:
            secsAgo = int(options.parm)
            if secsAgo in [None,'',0]: secsAgo = 432000
            getLatestBA(options, secsAgo)
            #walkSFCL(secsAgo, stream options)

        elif options.cmd in ['scmreject']:
            if options.br in [None,''] or stream in [None,'']: 
                print '%s' %scmRejectBranchUsage('You must provide a least a valid stream and a branch or label!')
                sys.exit()
            branch = options.br
            team = None
            if options.team != "":
                team = options.team
            scmRejectBranchCL(branch, stream, options, team=team, st=st) 

        elif options.cmd in ['stat', 'status']:
            if options.br in [None,''] or stream in [None,'']:
		msg = 'You must provide at least a valid stream and task branch name!'
                print msg
                sys.exit()
            setTaskBranchStatusCL(stream, options.br, options)

        else:
            doSomething('search', query, options.parm, options)
	    msg = 'doing nothing yet, I can do it twice if you like'
            print msg
        if options.parm not in ['min', 'line']:
	    msg = ' Took a total of %3.2f secs -^' %(time.time()-st)
            print msg

    elif options.cmd in ['taskhelp']:
        print mainTaskUsage()
        sys.exit()
    else:
	msg = '%s' %usage(options.cmd)
        print msg

if __name__ == "__main__":
    main_CL()
