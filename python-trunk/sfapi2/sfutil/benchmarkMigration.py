import time

from sfMagma import SFMagmaTool
from sfTechCampaign import SFTechCampaign, SFTechCampaignComment
from sfAttachment import SFAttachment
from sfNote2 import SFNote
from sfTask import SFTask
from sfEvent import SFEvent
from sfCase import SFCase, SFCaseComment
from sfContact2 import SFContact
from sfTechCampaignCaseLink import SFTechCampaignCaseLink
from sfCrLink import SFCrLink
from sfUser2 import SFUser

userCacheMap = {}

def caseToTcFlow():
    sfTool = SFMagmaTool()
    
    # query all tech campaign benchmarks that were migrated from cases
    where = [['Benchmark_Case__c', '!=', '']]
    fields = ('Id', 'Benchmark_Case__c', 'Account__c')

    tcList = SFTechCampaign.queryWhere(sfTool, where, fields)

    tcCount = 0
    for bmtc in tcList:
        tcCount += 1
        bmtcData = bmtc.getDataMap()
        bmtcId = bmtcData.get('Id')
        #raw_input("Press Enter to remigrate bmtc %s" %bmtcId)
        print "%s of %s: remigrating %s" %(tcCount, len(tcList), bmtcId)
        
        # fetch the original case object from which this benchmark was migrated
        bmc = SFCase.retrieve(sfTool, bmtcData.get('Benchmark_Case__c'))

        bmcData = bmc.getDataMap()
        bmcId = bmcData.get('Id')

        # fetch the CR links relating to the benchmark case
        where = [['Related_Case__c', '=', bmcId]]
        crLinkList = SFCrLink.queryWhere(sfTool, where)

        # Migrate each CR link to a Tech Campaign Case Link
        #(if not done already)
        for crLink in crLinkList:
            # check for an existing tc case linking Case__c crLink.parentCR
            # with Tech_Campaign__c bmtcId and having a matching Name field
            crlData = crLink.getDataMap()
            where = [['CR_Link__c', '=', crlData.get('Id')]]
            fields = ('Id', 'Name')
            tcclList = SFTechCampaignCaseLink.queryWhere(sfTool, where,
                                                         fields)
            if len(tcclList) > 0:
                # we already have a new link created for this one - skip it
                continue

            crLinkResolved = False
            if crlData.get('Resolved__c') == 'true':
                crLinkResolved = True
                pass
            
            tcclData = {'Name': crlData.get('Name','Benchmark/CR Link'),
                        'Case_Type__c': 'Change Request',
                        'Case__c': crlData.get('Parent_CR__c'),
                        'Tech_Campaign__c': bmtcId,
                        'Customer_Priority__c': crlData.get('Customer_Priority__c'),
                        'Description__c': crlData.get('Description__c'),
                        'Status__c': crlData.get('Status__c'),
                        'Promise_Date__c': crlData.get('Promise_Date__c'),
                        'Resolved__c': crLinkResolved,
                        'CR_Link__c': crlData.get('Id'),
                        }

            print "Linking to CR %s" %crlData.get('Parent_CR__c')
            tccLink = SFTechCampaignCaseLink.create(sfTool, tcclData)
            continue

        # Migrate additional fields from the bm case to the bmtc
        # migrate the account ID if it is not set in the TC
        bmtcModFlag = False
##        if bmtcData.get('Account__c',None) in [None,'']:

##            # load the contact from the benchmark case.
##            bmcContactId =  bmcData.get('ContactId')
##            print "Migrating account from contact %s on BM case" %bmcContactId
##            if bmcContactId in [None,'']:
##                continue
##            contactFields = ('Id','AccountId')
##            bmcContact = SFContact.retrieve(sfTool, bmcContactId,
##                                            contactFields)
##            contactData = bmcContact.getDataMap()
            
##            bmtcData['Account__c'] = contactData.get('AccountId')
##            bmtcModFlag = True
##            pass

        if bmtcModFlag is True:
            bmtc.update()

##        # Find and migrate attachments
##        # have to do loop hack - can only dl one att at a time
##        # and cannot do queryMore
##        while True:
##            attList = SFAttachment.queryParent(sfTool, bmcId)
##            if len(attList) == 0:
##                break
##            for att in attList:
##                att = att.relink(bmtcId)
##                continue
##            continue
        
##        # Find and migrate notes
##        noteList = SFNote.queryParent(sfTool, bmcId)
##        for note in noteList:
##            note = note.relink(bmtcId)
##            continue

        # Find and migrate Case Comments to Tech Campaign Comments
        cCommentList = SFCaseComment.queryParent(sfTool, bmcId)
        cCommentList.sort(sortCaseComment)
        cCommentList.reverse()
        for comment in cCommentList:
            commentData = comment.getDataMap()

            # check for existing migrated comment
            fields = ('Id', 'Original_Comment_Id__c')
            where = [['Original_Comment_Id__c', '=', commentData.get('Id')]]
            tcCommentList = SFTechCampaignComment.queryWhere(sfTool, where,
                                                             fields)
            if len(tcCommentList) > 0:
                # we have already migrated this comment. Skip it.
                print "Skipping comment - already seen"
                continue

            print "Migrating comment: %s bytes" %len(commentData.get('CommentBody'))
            # do the actual comment migration
            # annotate the comment with the original poster and date/time
            commentTstamp = sfTool.checkDate(commentData.get('CreatedDate'))
            commentTimeTuple = time.localtime(commentTstamp)
            commentDateStr = time.strftime('%d-%b-%Y %I:%M %p %Z',
                                           commentTimeTuple)

            commentAuthor = userCacheLookup(sfTool,
                                            commentData.get('CreatedById'))
            authorData = commentAuthor.getDataMap()
            authorName = "%s %s" %(authorData.get('FirstName',''),
                                   authorData.get('LastName'))

            byline = "Originally posted on %s by %s" %(commentDateStr,
                                                       authorName)
            commentBody = "%s\n%s" %(byline, commentData.get('CommentBody'))

            tcCommentData = {'CommentBody__c': commentBody,
                             'Original_Comment_Id__c': commentData.get('Id'),
                             'ParentId__c': bmtcId,}

            tcComment = SFTechCampaignComment.create(sfTool, tcCommentData)
            continue
                             
        

##        activityFields = ('Id','WhatId')
##        activityWhere = [['WhatId','=',bmcId]]
##        # Find and migrate Tasks
##        taskList = SFTask.queryWhere(sfTool, activityWhere, activityFields)
##        for task in taskList:
##            task.relink(bmtcId, 'WhatId')
##            continue
        
##        # Find and migrate Events
##        eventList = SFEvent.queryWhere(sfTool, activityWhere, activityFields)
##        for event in eventList:
##            event.relink(bmtcId, 'WhatId')
##            continue

        continue



def userCacheLookup(sfTool, userId):
    global userCacheMap

    if not userCacheMap.has_key(userId):
        fields = ('Id', 'FirstName', 'LastName', 'Email')
        user = SFUser.retrieve(sfTool, userId, fields)
        userCacheMap[userId] = user

    return userCacheMap[userId]
## END userCacheLookup

def sortCaseComment(a, b):
    """ sorts case comment by creation date"""
    aData = a.getDataMap()
    bData = b.getDataMap()

    aCdate = aData.get('CreatedDate')
    bCdate = bData.get('CreatedDate')

    return cmp(aCdate, bCdate)
## END sortCaseComment

if __name__ == '__main__':
    caseToTcFlow()

        
