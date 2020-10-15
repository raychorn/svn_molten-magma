#!/bin/env python2.3
import time
import os.path, os, sys
import csv
import copy
from optparse import OptionParser

from sfMagma import SFMagmaTool
from sfSolution import SFSolution
from sfAttachment import SFAttachment

walkStepSize = 500
walkStart = 0

stepMax = walkStart

dirBase = 'solution_export'
fileName = 'export_data.csv'

def flow(includeList, excludeList):
    """ include list are the solution record types to include. conversely, the
    exclude list are solution record types to exclude."""
    global stepMax
    
    sfTool = SFMagmaTool(logname='solExp')

    dirName = "%s_%s.%s" %(dirBase, time.strftime('%Y%m%d', time.localtime()),
                           os.getpid())
    path = os.path.join('~', dirName)
    path = os.path.expanduser(path)
    attachpath = os.path.join(path, 'attachments')
    filePath = os.path.join(path, fileName)

##    if not os.path.exists(path):
##        os.makedirs(path)
    if os.path.exists(path):
        print "Destination directory %s already exists!\nPlease consider removing or renaming this directory.\nRerunning this script will usually work around this error.\nEXITING"
        sys.exit()
    
    if not os.path.exists(attachpath):
        os.makedirs(attachpath)
    
    csvfh = file(filePath, 'w+')
    solFields = copy.deepcopy(sfTool.getEntityMap(SFSolution.obj)['fields'])
    solFields.append('RecordType')
    solFields.sort()
    fieldNameMap = {}
    csvw = csv.DictWriter(csvfh, solFields)

    # write the field header row
    for fld in solFields:
        fieldNameMap[fld] = fld
        continue
    csvw.writerow(fieldNameMap)


    # find the highest solution number...
    maxSolutionNumber = int(SFSolution.findMaxSolutionNumber(sfTool))
    
    while True:
        stepMin = stepMax
        stepMax = stepMin + walkStepSize
        stepMinStr = '%08d' %stepMin
        stepMaxStr = '%08d' %stepMax

        where =  [['SolutionNumber','>=',stepMinStr]]
        where += ['and', ['SolutionNumber','<',stepMaxStr]]

        recTypeMap = SFSolution.getRecordTypes(sfTool)

        ignoreRecTypeIds = []
        allowRecTypeIds = []
            
        for recTypeId, recTypeName in recTypeMap.items():
            if recTypeName in excludeList:
                ignoreRecTypeIds.append(recTypeId)
            elif recTypeName in includeList:
                allowRecTypeIds.append(recTypeId)
                pass
            continue


        if len(allowRecTypeIds):
            # modify the where clause to select only solutions of
            # desired type(s)
            where += ['and', '(']
            for allowRecTypeId in allowRecTypeIds:
                where += [['RecordTypeId','=',allowRecTypeId], 'or']
                continue

            where.pop()
            where += [')']    
            pass
        
##        print where
##        sys.exit()

        solutionList = SFSolution.queryWhere(sfTool, where)

        if len(solutionList) == 0 and stepMin > maxSolutionNumber:
            break

        for sol in solutionList:
            solData = sol.getDataMap()

            solId = solData.get('Id')
            solNum = solData.get('SolutionNumber').lstrip('0')
            solRecTypeId = solData.get('RecordTypeId')
            
            if solRecTypeId in ignoreRecTypeIds:
                print "Skipping solution number %s" %solNum
                continue
            else:
                print "Exporting solution number %s" %solNum

            # replace the record type ID with the text
            solData['RecordType'] = recTypeMap.get(solRecTypeId)
            solNote = solData.get('SolutionNote')
            if solNote is not None:
                solData['SolutionNote'] = solNote.encode('ascii','replace')
            
            try:
                del(solData['type'])
            except:
                pass

            csvw.writerow(solData)

            # check for attachment(s) on this solution
            solAttachments = SFAttachment.queryParent(sfTool, solId, 'fields')

            if len(solAttachments) > 0:
                solattpath = os.path.join(attachpath, "%08d" %int(solNum))
                os.makedirs(solattpath)

                for att in solAttachments:
                    att.writeToFile(solattpath)
                    continue
                pass

            continue # for loop
        continue # while loop

    print "\nSolutions have been exported to:\n%s" %path
    return

def main():
    """ Parse the command line and initiate the flow """
    usage = "Exports solutions from Salesforce.com into a new directory in your home directory. This directory will contain a csv file of the exported solutions along with a directory structure containing any attachments to the solutions indexed by solution number."
    
    op = OptionParser(usage=usage)

    op.add_option("-i", "--include", action="append", dest="includeList",
                  default=[], help="Solution Types to include."
                  "All are included if none are specified. Specify multiple"
                  "types to exclude with separate -e arguments.")
    
    op.add_option("-e", "--exclude", action="append", dest="excludeList",
                  default=[], help="Solution Types to exclude."
                  "None are excluded if none are specified. Specify multiple"
                  "types to exclude with separate -e arguments.")

    opts, args = op.parse_args()

    flow(opts.includeList, opts.excludeList)


if __name__ == '__main__':
    main()
