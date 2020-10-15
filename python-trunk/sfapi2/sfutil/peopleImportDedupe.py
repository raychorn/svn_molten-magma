#!/bin/env python2.3
"""
Looking at a csv of people, lookup each email as a contact and/or lead
and generate two lists: known imports and new imports.
"""

import csv
import pprint
import os
import sys
from optparse import OptionParser

from sfMagma import *
from sfConstant import *

class PeopleDedupeTool(SFMagmaTool):

    def __init__(self, inCsvPath, idCol, opts):

        SFMagmaTool.__init__(self)

        self.idCol = idCol
        self.seenIds = []
        self.opts = opts

        inCsvDir, inCsvFile = os.path.split(inCsvPath)
        
        # open in file
        headerList, self.inCsvr = self.openCsvReader(inCsvPath)

        if idCol not in headerList:
            msg  = "Column %s cannot be found in the input csv file's header.\n" \
                  %self.idCol
            msg += "Please specify one of the following columns:\n"
            print msg
            for col in headerList:
                print "\t%s" %col
                continue
            
            sys.exit()
            pass
            
        # open known out file
        knownCsvPath = os.path.join(inCsvDir,'known_people.csv')
        self.knownCsvw = self.openCsvWriter(knownCsvPath, headerList)
        
        # open new out file
        newCsvPath = os.path.join(inCsvDir,'new_people.csv')
        self.newCsvw = self.openCsvWriter(newCsvPath, headerList)
        return
    ## END __init__


    def openCsvReader(self, inCsvPath):
        fh = file(inCsvPath, 'rU')
        dialect = csv.Sniffer().sniff(fh.read(2048))

        fh.seek(0)
        csvHdrReader = csv.reader(fh, dialect=dialect)
        hdrRow = csvHdrReader.next()
        csvHdrReader = None

        fh.seek(0)
        csvr = csv.DictReader(fh, hdrRow, dialect=dialect)
        csvr.next() # get rid of the header row

        return hdrRow, csvr
    ## END openReader


    def openCsvWriter(self, outCsvPath, headerList):
        headerDict = {}
        for col in headerList:
            headerDict[col] = col
            continue
        fh = file(outCsvPath, 'w+')
        csvw = csv.DictWriter(fh, headerList)
        csvw.writerow(headerDict)
        return csvw
    ## END openCsvWriter


    def lookupPersonByEmail(self, email, entity):
        """ Return a list of the specified entity records having the
        supplied email address.
        Returns an empty list if none are found
        """
        if entity not in [LEAD_OBJ, CONTACT_OBJ]:
            return []

        email = email.lower()
        where = [['Email', '=', email]]

        res = self.query(entity, where, sc='all')
        if res in BAD_INFO_LIST:
            res = []
            pass
        
        return res
    ## END lookupPersonByEmail
    

    def lookupLeadByEmail(self, email):
        """ Return a list of leads having the supplied email address.
        Returns an empty list if none are found
        """
        return self.lookupPersonByEmail(email, LEAD_OBJ)
    ## END lookupLeadByEmail


    def lookupContactByEmail(self, email):
        """ Return a list of contacts having the supplied email address.
        Returns an empty list if none are found
        """
        return self.lookupPersonByEmail(email, CONTACT_OBJ)
    ## END lookupContactByEmail

    
    def processPeople(self):

        for row in self.inCsvr:
            known = False
            idKey = row.get(self.idCol, None)
            idKey = idKey.lower()
            
            if idKey in self.seenIds:
                continue

            self.seenIds.append(idKey)
            
            if self.opts.complead is True:
                leadList = self.lookupLeadByEmail(idKey)
                if len(leadList) > 0:
                    known = True
                    pass
                pass

            if self.opts.compcontact is True:
                contactList = self.lookupContactByEmail(idKey)
                if len(contactList) > 0:
                    known = True
                    pass
                pass


            if known is True:
                self.knownCsvw.writerow(row)
            else:
                self.newCsvw.writerow(row)
                pass
            continue
        return
    ## END processPeople

def main():
    op = OptionParser()
    op.add_option('-l','--lead', action='store_true', dest='complead',
                  default=False,
                  help='Compare email addresses against Leads')
    op.add_option('-c','--contact', action='store_true', dest='compcontact',
                  default=False,
                  help='Compare email addresses against Contacts')

    opts, args = op.parse_args()

    if len(args) < 2:
        msg = "You must provide a pathname to a CSV file and the name of the column holding Email addresses!"
        op.error(msg)
        sys.exit()
        pass

    if opts.complead is False and opts.compcontact is False:
        msg = "You must supply at least one of the -l or -c flags!"
        op.error(msg)
        
    inCsvPath = args[0]
    idCol = args[1]

    pdt = PeopleDedupeTool(inCsvPath, idCol, opts)
    pdt.processPeople()
    return

if __name__ == "__main__":
    main()



