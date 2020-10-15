#!/usr/bin/env python2.3
import datetime
import time
import pprint

from sfTask import SFTask
from sfSolution import SFSolution
from sfUser2 import SFUser

from sfMagma import SFMagmaTool
from sfConstant import BAD_INFO_LIST

class SolPubFlow:
    logname = "solpub"

    def __init__(self, sfTool=None):
        if sfTool is None:
            self.sfTool = SFMagmaTool(logname=self.logname)
        else:
            self.sfTool = sfTool 
            pass

        # make this into a list for multiple addrs, or 
        #self.mailCC = sfTool.from_addr
        self.mailCC = None
        return
    ## END __init__


    def findPubReqSolutions(self):
        f1 = ['Publish_Request__c', '=', True]
        f2 = ['Status', '=', 'Draft']

        where = [f1, 'and', f2]
        fields = ('Id', 'Status', 'Publish_Request__c', 'SolutionNumber',
                  'SolutionName', 'Component__c', 'CreatedById')

        return  SFSolution.queryWhere(self.sfTool, where, fields)
    ## END findPubReqSolutions


    def createSolReviewTask(self, solution):
        solData = solution.getDataMap()
        solNum = solData.get('SolutionNumber').lstrip('0')
        task = None

        dueDelta = datetime.timedelta(weeks=1)
        nowDate = datetime.date.today()
        dueDate = nowDate + dueDelta
        dueDateSecs = time.mktime(dueDate.timetuple())
        
        # lookup component to find PE
        peId = self.sfTool.getPEIdByComp(solData.get('Component__c'))
        if peId in ['', None]:
            msg = "Cannot determine PE for component %s" \
                  %solData.get('Component__c')
            self.sfTool.setLog(msg, 'error')
        else:    

            taskData = {'OwnerId': peId,
                        'Subject': "Review Solution #%s" %solNum,
                        'Status': "Not Started",
                        'Priority': "Normal",
                        'WhatId': solData.get('Id'),
                        'ActivityDate': dueDateSecs,
                        'Description': solData.get('SolutionName'),
                        'Type': 'Other'}

            task = SFTask.create(self.sfTool, taskData)
            pass
        
        return task
    ## END createSolReviewTask


    def solPubRequested(self, solution):
        solData = solution.getDataMap()
        solData['Publish_Request__c'] = False
        solData['Status'] = 'In First Technical Review'
        return solution.update()
    ## END solPubRequested


    def pubRequestFlow(self):
        solList = self.findPubReqSolutions()

        for solution in solList:
            solData = solution.getDataMap()

            # create a solution review task
            task = self.createSolReviewTask(solution)

            if task is not None:
                # reset the Publish Request checkbox on the solution
                self.solPubRequested(solution)

                taskData = task.getDataMap()
                body  = 'A Solution entitled "%s" has been nominated for publishing.\n' %solData.get('SolutionName')
                body += 'Based on information contained in the solution, you have been selected\n'
                body += 'to review this solution for publication.\n\n'

                body += 'Please review solution number %s located at:\n' \
                        %solData.get('SolutionNumber').lstrip('0')
                body += '%s/%s\n' %(self.sfTool.sfdc_base_url,
                                    taskData.get('WhatId'))
                body += 'to determine if the solution should be published.\n\n'

                body += 'If the solution requires modification or is inappropriate for publication,\n'
                body += 'please work directly with the author to resolve the issues.\n\n'

                body += 'If the solution is acceptable, please:\n'
                body += '1. Edit the solution\n'
                body += '2. Change the status to "Reviewed"\n'
                body += '3. Check the "Published" checkbox\n'
                body += '4. Click "Save"\n\n'

                body += 'This action item has been entered as a task for you in Salesforce.com:\n'
                body += "%s/%s\n" %(self.sfTool.sfdc_base_url,
                                          taskData.get('Id'))

                # find the solution author's email
                solAuthorId = solData.get('CreatedById')
                author = SFUser.retrieve(self.sfTool, solAuthorId)
                authorData = author.getDataMap()
                authorEmail = authorData.get('Email')
                ccList = [authorEmail]

                if self.mailCC is not None:
                    ccList.append(self.mailCC)
                    pass
                
                # Notify task owner about the task by email
                task.notifyTaskOwner(body=body, ccAddrs=ccList)

            else:
                msg = "Couldn't create soluton publishing task for solution #%s" \
                      %solData.get('SolutionNumber').lstrip('0')
                self.sfTool.setLog(msg, 'critical')
            continue
        return 
    ## END doFlow
    
            
if __name__ == '__main__':
    sfTool = SFMagmaTool(logname=SolPubFlow.logname)
    spf = SolPubFlow(sfTool=sfTool)
    spf.pubRequestFlow()
    




