#!/usr/bin/env python2.3
"""
Script to scan for specific events related to CRs and to publish those
events as case comments on related Support Cases.
"""
import sys
import datetime
import time
import pprint
from optparse import OptionParser

from sfMagma import SFMagmaTool
from sfConstant import *
from sfUtil import *

CR_TYPES = (RECTYPE_CR, RECTYPE_PVCR, RECTYPE_PLDCR)
SC_TYPES = (RECTYPE_SC, RECTYPE_PLDSC)

class GenericEventHandler(SFMagmaTool):

    def __init__(self, logname='sf.evntscan', debug=0, setupLog=True, opts=None):
        SFMagmaTool.__init__(self, logname=logname, debug=debug, setupLog=setupLog)
        if opts is None:
            self.trial = False
        else:
            self.trial = opts.trial
            pass
        self.opts = opts
        
        return

    def scan(self):
        raise NotImplementedError

    def doAction(self, actionList):
        raise NotImplementedError
        
    def flow(self):
        raise NotImplementedError


class CaseCommentEventHandler(GenericEventHandler):
    """
    Handler framework for events resulting in case comments
    """

    def flow(self):
        # pick out interesting options
        id = None
        timeDelta = None
        
        if self.opts is not None:
            id = self.opts.id
            if self.opts.daysback is not None:
                timeDelta = datetime.timedelta(days=int(self.opts.daysback))
                pass
            pass

        # set a default for timeDelta if neither id nor timeDelta are provided
        if id is None and timeDelta is None:
            timeDelta = datetime.timedelta(days=3)
            pass

        # run the flow for the event
        actionList = self.scan(timeDelta, id)
        self.doAction(actionList)
        return

    def doAction(self, actionList):

        for actionData in actionList:
            action = actionData.get('action', None)

            if action == 'comment':
                self.addCaseComment(actionData)
                
            else:
                msg = "Unhandled action type '%s'. Skipping." %action
                print msg
                self.setLog(msg, 'warn')
                pass
            
            continue

        return

    def addCaseComment(self, actionData):
        """ Adds a case comment to case if a comment having
        the same commentTag does not already exist.

        actionData had element 'action' == 'comment' to get here
        Expects the following elements:
        caseId - valid salesforce ID to a case object
        comment - text of the comment to add
        commentPub - is comment published (default False)
        commentTag - unique identifier for the comment, so it won't be
           added again
        """
        maxLen = 4090
        entity = 'CaseComment'
        
        caseId = actionData.get('caseId',None)
        comment = actionData.get('comment',None)
        commentPub = actionData.get('commentPub',False)
        commentTag = actionData.get('commentTag',None)

        if caseId is None or comment is None or commentTag is None:
            msg = "Incomplete data for action 'comment.' Requires caseId, comment, commentTag. Got: %s" %actionData
            print msg
            self.setLog(msg, 'error')

            return None

        # check for existing comment.
        where = [['ParentId','=',caseId],'and',
                 ['CommentBody','like','%%%s' %commentTag]]
        fields = ('Id', 'CreatedDate')
        res = self.query(entity, where=where, sc=fields)
        if res not in BAD_INFO_LIST:
            foundId = res[0].get('Id')
            return foundId

        # trim the comment text if too long so tag doesn't get truncated
        if len(comment) + len(commentTag) + 1 > maxLen:
            newLen = maxLen - len(commentTag) - 3
            comment = comment[:newLen]
            pass
        
        # insert the new comment
        commentText = "%s\n%s" %(comment, commentTag)
            
        data = {'ParentId': caseId,
                'CommentBody': commentText,
                'IsPublished': commentPub}

        #self.trial = True # Force trial during development
        if self.trial is True:
            res = ["123456789012345AAA"] # bogus ID for trial runs
            pprint.pprint(data)
        else:
            msg = 'Logging event %s for %s' %(comment, caseId)
            print msg
            self.setLog(msg, 'info')
            res = self.create(entity, data=data)
            pass
        
        if res in BAD_INFO_LIST:
            msg = 'CaseComment create failed. Data was %s' %data
            print msg
            self.setLog(msg, 'error')
            pass

        return res[0]
    ## END addCaseComment

    def queryCaseHistory(self, whereClause):
        """ Query case history and returns a list of history elements.
        In the event that more than one history element on a case matches,
        only the most resent is returned
        """
        fields = ('Id','CaseId','NewValue', 'CreatedDate')
        res = self.query('CaseHistory', where=whereClause, sc=fields)

        if res in BAD_INFO_LIST:
            res = []
            pass

        # Extract a list of case Ids and a map of the info by case Id
        histMap = {}
        caseIdList = []
        for he in res:
            caseId = he.get('CaseId')
            if caseId not in caseIdList:
                caseIdList.append(caseId)

            if histMap.has_key(caseId) and \
                   histMap[caseId].get('CreatedDate') > he.get('CreatedDate'):
                # if we already have a history entry for this case newer
                # than the current one, then skip the current one
                continue

            histMap[caseId] = he
            continue

        return histMap
    ## END queryCaseHistory 

    def getCrLinksByParentId(self, caseIdList):
        """ Does an iterative series of selects to fetch all the CR Links
        where the parent CR is in the supplied list.
        """
        sliceSize = 15
        # do an iterative select for CR Links
        f1 = ['Related_Case_Type__c','=','Support Case']
        crLinkList = []
        while len(caseIdList):
            selectIds = caseIdList[:sliceSize]
            caseIdList = caseIdList[sliceSize:]
            
            sfList = []
            for id in selectIds:
                sfList.append(['Parent_CR__c','=',id])
                sfList.append('or')
                continue
            sfList.pop() # nuke the last or

            where = [f1, 'and', '(']
            where.extend(sfList)
            where.append(')')

            fields = ('Id', 'Parent_CR__c', 'Related_Case__c',
                      'Publish_CR_Events__c')
            ret = self.query('CR_Link__c', where=where, sc=fields)
            if ret not in BAD_INFO_LIST:
                crLinkList.extend(ret)
                pass
            continue

        return crLinkList
    ## END getCrLinksByParentId(

    def getLinkedCases(self, crLinkList):
        """ Fetch a map of linked cases
        
        Currently only good for a CR parent linked to a Support Case
        with a link having Related Case Type set to 'Support Case'
        """
        caseIdList = []
        crLinkMap = {}
        for crLink in crLinkList:
            crId = crLink.get('Parent_CR__c', None)
            if crId is not None and crId not in caseIdList:
                caseIdList.append(crId)
                pass
            
            scId = crLink.get('Related_Case__c', None)
            if scId is not None and scId not in caseIdList:
                caseIdList.append(scId)
                pass

            crLinkMap[crLink.get('Id')] = {'Link': crLink,
                                           'CR': {'Id': crId},
                                           'SC': {'Id': scId}}
            continue
        
        # get all the cases and build a map by ID
        fields = ('Id', 'RecordTypeId', 'CreatedDate', 'CaseNumber',
                  'Status', 'Subject')
        res = self.retrieve(caseIdList, 'Case', fieldList=fields)
        if res in BAD_INFO_LIST:
            res = []
            pass

        caseMap = {}
        for case in res:
            caseMap[case.get('Id')] = case
            continue

        # now, match the linked CRs to their support cases
        actions = []
        for crLinkId in crLinkMap.keys():
            commentTag = "[%s%s]" %(self.eventCode, crLinkId)

            #match only those where Parent CR record type is in CR_TYPES and
            #where Related Case record type is in SC_TYPES
            crId = crLinkMap[crLinkId]['CR']['Id']
            scId = crLinkMap[crLinkId]['SC']['Id']
            
            crInfo = caseMap.get(crId,{})
            scInfo = caseMap.get(scId,{})

            # check to ensure that the linked cases are of the correct
            # record types
            if crInfo.get('RecordTypeId','') not in CR_TYPES or \
                   scInfo.get('RecordTypeId','') not in SC_TYPES:
                # get rid of this link - it doesn't link the types
                # of case records that it advertises
                crLinkMap.pop(crLinkId)

            else:
                crLinkMap[crLinkId]['CR'].update(crInfo)
                crLinkMap[crLinkId]['SC'].update(scInfo)
                pass
            
            continue

        return crLinkMap
    ## END getLinkedCases
    

class SceCrCreated(CaseCommentEventHandler):
    eventCode = 'OP'

    def scan(self, timeDelta, crId):
        """Scanner to find created CR events

        We look for CR Links with Related Case Type of Support Case
        either within timeDelta back from now, or with Parent CR of
        crId (or both, but that would be of dubious usefulness)
        """
        where = [['Related_Case_Type__c','=','Support Case']]

        if crId is not None:
            crId = convertId15ToId18(crId)
            where.extend(['and',['Parent_CR__c','=',crId]])
            pass

        if timeDelta is not None:
            now = datetime.datetime.now()
            then = now - timeDelta
            thenISO = self.getAsDateTimeStr(time.mktime(then.timetuple()))
            where.extend(['and',['CreatedDate','>',thenISO]])
            pass

        #fields I want:
        fields = ('Id', 'Parent_CR__c', 'Related_Case__c',
                  'Publish_CR_Events__c')
        res = self.query('CR_Link__c', where=where, sc=fields)

        if res in BAD_INFO_LIST:
            res = []
            pass

        crLinkMap = self.getLinkedCases(res)

        actions = []
        for crLinkId in crLinkMap.keys():
            crInfo = crLinkMap[crLinkId]['CR']
            scInfo = crLinkMap[crLinkId]['SC']
            crLink = crLinkMap[crLinkId]['Link']
            
            scId = scInfo.get('Id')
            crNum = crInfo.get('CaseNumber')
            crSubject = crInfo.get('Subject', 'No CR Subject Set')
            pubFlag = crLink.get('Publish_CR_Events__c', False)
            if pubFlag == 'false':
                pubFlag = False
            elif pubFlag == 'true':
                pubFlag = True
                
            crCreateDate = self.checkDate(crInfo.get('CreatedDate'))
            crCreateDate = datetime.date.fromtimestamp(crCreateDate)
            
            comment  = "A CR has been opened for this support case on %s:\n" \
                       %crCreateDate.strftime('%d-%b-%Y')
            comment += "%s %s" %(crNum, crSubject)
            commentTag = "[%s%s]" %(self.eventCode, crLinkId)
            
            actionInfo = {'action': 'comment',
                          'caseId': scId,
                          'comment': comment,
                          'commentPub': pubFlag,
                          'commentTag': commentTag}
            actions.append(actionInfo)

            continue

        return actions
    ## END scan
## END class SceCrCreated

class SceCrPostOpen(CaseCommentEventHandler):
    eventCode = 'PO'

    def scan(self, timeDelta, crId):
        """Scanner to find CR moved out of open state events

        Look first for Case History events in the timeframe where Status
        was moved from Open to something else.

        # common flow for other history-based events
        Retrieve these cases, and
        retain only the CRs. Get the CR links parented by these CRs that
        have a related case type of Support Case. Retrieve the related cases
        and pare down to only those that are actually support cases. 
        """

        where = [['Field','=','Status'],'and','(',['OldValue','=','Open'],
                 'or','(',
                 ['OldValue','=','New'],'and',['NewValue','!=','Open'],')',')']

        if crId is not None:
            crId = convertId15ToId18(crId)
            where.extend(['and',['CaseId','=',crId]])
            pass

        if timeDelta is not None:
            now = datetime.datetime.now()
            then = now - timeDelta
            thenISO = self.getAsDateTimeStr(time.mktime(then.timetuple()))
            where.extend(['and',['CreatedDate','>',thenISO]])
            pass
        
        histMap = self.queryCaseHistory(where)
        
        crLinkList = self.getCrLinksByParentId(histMap.keys())

        crLinkMap = self.getLinkedCases(crLinkList)

        actions = []
        for crLinkId in crLinkMap.keys():
            crInfo = crLinkMap[crLinkId]['CR']
            scInfo = crLinkMap[crLinkId]['SC']
            crLink = crLinkMap[crLinkId]['Link']
            
            scId = scInfo.get('Id')
            crId = crInfo.get('Id')
            crNum = crInfo.get('CaseNumber')
            pubFlag = crLink.get('Publish_CR_Events__c', False)
            if pubFlag == 'false':
                pubFlag = False
            elif pubFlag == 'true':
                pubFlag = True
            newState = histMap.get(crId).get('NewValue')
            statChangeDate2 = histMap.get(crId).get('CreatedDate')
            statChangeDate1 = self.checkDate(statChangeDate2)
            statChangeDate = datetime.date.fromtimestamp(statChangeDate1)

            comment  = "CR %s has moved from the Open state to %s on %s" \
                       %(crNum, newState, statChangeDate.strftime('%d-%b-%Y'))
            ## Should this be tagged by history item ID instead?
            ## in case the CR goes back into Open for some reason?
            commentTag = "[%s%s]" %(self.eventCode, crLinkId)


            actionInfo = {'action': 'comment',
                          'caseId': scId,
                          'comment': comment,
                          'commentPub': pubFlag,
                          'commentTag': commentTag}
            actions.append(actionInfo)
            
            continue
        
        return actions
    ## END scan
## END class SceCrPostOpen

        
class SceCrFixed(CaseCommentEventHandler):
    eventCode = "FX"
    def scan(self, timeDelta, crId):
        """Scanner to find CR moved out of open state events

        Look first for Case History events in the timeframe where Status
        was moved from Open to something else.

        # common flow for other history-based events
        Retrieve these cases, and
        retain only the CRs. Get the CR links parented by these CRs that
        have a related case type of Support Case. Retrieve the related cases
        and pare down to only those that are actually support cases. 
        """

        where = [['Field','=','Status'],'and',
                 '(',['NewValue','=','Testing'],'or',
                 ['NewValue','=','First-Testing'],')']

        if crId is not None:
            crId = convertId15ToId18(crId)
            where.extend(['and',['CaseId','=',crId]])
            pass

        if timeDelta is not None:
            now = datetime.datetime.now()
            then = now - timeDelta
            thenISO = self.getAsDateTimeStr(time.mktime(then.timetuple()))
            where.extend(['and',['CreatedDate','>',thenISO]])
            pass
        
        histMap = self.queryCaseHistory(where)
        
        crLinkList = self.getCrLinksByParentId(histMap.keys())

        crLinkMap = self.getLinkedCases(crLinkList)

        actions = []
        for crLinkId in crLinkMap.keys():
            crInfo = crLinkMap[crLinkId]['CR']
            scInfo = crLinkMap[crLinkId]['SC']
            crLink = crLinkMap[crLinkId]['Link']
            
            scId = scInfo.get('Id')
            crId = crInfo.get('Id')
            crNum = crInfo.get('CaseNumber')
            pubFlag = crLink.get('Publish_CR_Events__c', False)
            if pubFlag == 'false':
                pubFlag = False
            elif pubFlag == 'true':
                pubFlag = True
            newState = histMap.get(crId).get('NewValue')
            statChangeDate2 = histMap.get(crId).get('CreatedDate')
            statChangeDate1 = self.checkDate(statChangeDate2)
            statChangeDate = datetime.date.fromtimestamp(statChangeDate1)

            comment  = "CR %s has a fix merged into a test build on or before %s" \
                       %(crNum, statChangeDate.strftime('%d-%b-%Y'))
            ## Should this be tagged by history item ID instead?
            ## in case the CR goes back into Testing for some reason?
            commentTag = "[%s%s]" %(self.eventCode, crLinkId)


            actionInfo = {'action': 'comment',
                          'caseId': scId,
                          'comment': comment,
                          'commentPub': pubFlag,
                          'commentTag': commentTag}
            actions.append(actionInfo)
            
            continue
        
        return actions
    ## END scan
## END class SceCrFixed
            

def main():
    op = OptionParser()

    op.add_option("-t", "--trial", dest="trial", action="store_true", default=False, help="Performs a trial run without changing any data")
    op.add_option("-b", "--daysback", dest="daysback", default=None,
                  type="int",
                  help="Integer value indicating the number of days back the scan should include")
    op.add_option("-i", "--id", dest="id", default=None)
    op.add_option("-d", "--debug", dest="debug", action="count", default=0) 
    (opts, args) = op.parse_args()

    debug=opts.debug

    SceCrCreated(debug=debug, opts=opts).flow()
    SceCrPostOpen(debug=debug, opts=opts).flow()
    SceCrFixed(debug=debug, opts=opts).flow()
    
if __name__ == '__main__':
    trial = True
    main()
    #SceCrCreated(trial=trial, caseList=None).flow()
