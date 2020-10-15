#!/usr/bin/env python2.3
"""
Interactively log in and access the salesforce.com website in order to
perform a full data export.

Note: This script cannot perform a backup in a single pass.  Instead,
it must check that the export window is currently open (only one
export is allowed every 6 days). If it is, then it must request the
export, which will be finished at a later time. Since the script won't
receive the email notification when the export is finished, it will
simply have to check back later until a download is available, then
fetch the package.
"""

version = 1.0  # Mar 30, 2004. First backup script.

import re
import time
import sys
import os
import cStringIO
import socket
import pprint

import ConfigHelper
from sfWebScrape import WebScrape

try: 
    import mailServer
except:
    print 'Please ensure that the "mailServer.py[co]" file is in your'
    print 'PYTHONPATH environment variable list.'


### Global definitions ###
timestampFmt = '%Y%m%d-%H%M'
### END Global definitions ###

class Backup(WebScrape):
    """

    """
    
    props = {}
    cookieJar = None
    urlOpener = None
    fileOpener = None
    backupPath = None

    report = cStringIO.StringIO()

    def __init__(self, props):
        self.props = props

        uname = self.props.get('backup','backupUname')
        encpw = self.props.get('backup','backupEncPw')

        # parent class init performs login
        WebScrape.__init__(self, props, uname, encpw)

    ## END __init__(self)
    

    def extractTitleTag(self, body):
        titleTagPat = "^\s*<title>(.*)</title>"
        matchObj = re.search(titleTagPat, body, re.M|re.I)
        if matchObj is not None:
            return matchObj.group(1)
        else:
            return None
    ## END extractTitleTag(self, body)

    def sfExportPage(self):
        exportURL = self.props.get('backup','exportURL')

        response = self.sendRequest(exportURL, self.urlOpener)

        responseBody = "%s" %response.read()
        response.seek(0)

        titleStr = self.extractTitleTag(responseBody)
        if titleStr is None:
            msg = "Can't find title tag in Export page source:\n\n%s" \
                  %responseBody
            self.report.write("%s\n" %msg)
            return ("ERR", msg)
        
        # Handle various cases based upon contents of the title tag:
        if re.search("Data Export Service: Export File Delivery",
                     titleStr, re.I) is not None:
            # Need to request an export from Salesforce
            if self.requestExport(responseBody):
                msg = "Export has been requested and is in progress"
                return ("WAIT", msg)
            else:
                msg = "Export resuest failed"
                self.report.write("%s\n" %msg)
                return ("ERR", msg)
            
        elif re.search("Export (In Progress|Requested)", titleStr, re.I) is not None:
            # The export is in progress, but is not ready yet.
            # Punt this time and try later
            msg = "Export is in progress. Trying again later."
            return ("WAIT", msg)
        
        elif re.search("Data Export File Delivery", titleStr,re.I) is not None:
            # It's ready! Check the timestamp and see if we've already
            # downloaded it. If not, download it now.
            if self.downloadExport(responseBody) is True:
                msg = "Data export download has completed"
                return ("DONE", msg)
            else:
                msg = "Data export download failed"
                return ("ERR", msg)
            
        elif re.search("Export Already Run", titleStr, re.I) is not None:
            # Export isn't available at this time - punt
            msg = "Data export is unavailable for request or download at this time"
            self.report.write("%s\n" %msg)
            return ("NA", msg)
        
        else:
            # Unhandled case?
            msg = "Unhandled case in title string:\n%s" %titleStr
            print msg
            self.report.write("%s\n" %msg)

            return ("ERR", msg)
            
    ## END sfExportPage(self)

    def requestExport(self, pageBody):
        exportURL = self.props.get('backup', 'exportURL')

        # p1 = 1 means to save attachemnts. Always do it for now.
        requestElems = {'p1': '1',
                        'save': 'Data Export',
                        'retURL': '/setup?page=Setup&amp;setupid=DataManagement',
                        'setupid': 'DataManagementExport',
                        'save_new_url': '/setup/org/orgExportSchedule.jsp?retURL=%2Fsetup%3Fpage%3DSetup%26setupid%3DDataManagement&amp;setupid=DataManagementExport'}

        response = self.sendRequest(exportURL, self.urlOpener,
                                    params=requestElems, method='POST')

        # See if we get a reasonable response page. Until then, always return
        responseBody = "%s" %response.read()
        titleStr = self.extractTitleTag(responseBody)

        if titleStr is not None and \
               re.search("Export Requested", titleStr, re.I) is not None:
            return True
        elif titleStr is None:
            msg = "Bad response after requesting export. Couldn't read Result page title."
        else:
            msg = "Unexpected response after requesting export\n%s" \
                  %titleStr

        print msg
        self.report.write("%s\n" %msg)
        return False
    ## END requestExport(self)


    def downloadExport(self, dlPageBody):
        ret = False
        bkfBase = self.props.get('backup','backupFileBasename')
        bkfExt = self.props.get('backup','backupFileTypeExt')
        bkfDir = self.props.get('backup','backupFileDir')

        # Find Schedule Date:
        #sdPat = "Schedule Date:.*(\d+/\d+/\d+ \d+:\d+ [AP]M)</td>" # old broke
        sdPat = "Schedule Date:.*>\s*(\d+/\d+/\d+ \d+:\d+ [AP]M)</td>"
        matchObj = re.search(sdPat, dlPageBody, re.I|re.S)
        if matchObj is not None:
            sd = matchObj.group(1)
            sdTime = time.strptime(sd, "%m/%d/%Y %I:%M %p")
            timestamp = time.strftime(timestampFmt, sdTime)
        else:
             msg = "ERROR: Cannot extract schedule date with pattern:\n%s" \
                   %sdPat
             print msg
             self.report.write("%s\n" %msg)
             return ret

        bkfName = "%s-%s_*.%s" %(bkfBase, timestamp, bkfExt)
        bkfPath = os.path.join(bkfDir, bkfName)

        # Extract the download URL
        dlUrlPat = '<a href="(/servlet/servlet.OrgExport.*)">Click here'
        dlUrlRE = re.compile(r'<a href="(/servlet/servlet.OrgExport\?fileName=([^"]*))">Click here', re.I|re.S|re.M)
        dlSerialRE = re.compile(r'WE_[^_]+_(\d+).ZIP')

        #matchObj = re.search(dlUrlPat, dlPageBody, re.I|re.S|re.M)
        matchList = dlUrlRE.findall(dlPageBody)

        if len(matchList):
            ret = True

        for matchTuple in matchList:
            dlUrl = "%s%s" %(self.props.get('backup','baseurl'),
                             matchTuple[0])
            
            # get the file serial number if present
            serialMatch = dlSerialRE.search(matchTuple[1])
            if serialMatch is not None:
                bkfSer = serialMatch.group(1)
                bkfName = "%s-%s_%s.%s" %(bkfBase, timestamp, bkfSer, bkfExt)
                infoVer = "%s of %s" %(bkfSer, len(matchList))
            else:
                bkfName = "%s-%s_1.%s" %(bkfBase, timestamp, bkfExt)
                infoVer = "1 of 1"
                pass

            bkfPath = os.path.join(bkfDir, bkfName)
            if not os.path.exists(bkfPath):
                # don't already have this file - download it
                print "Downloading data export file %s..." %infoVer

                maxTries = 5
                numTries = 0

                while numTries < maxTries:
                
                    try:
                        zipdata = self.sendRequest(dlUrl,
                                                   self.fileOpener).read()

                    except IOError, e:
                        # loop around and try again if connection is
                        # reset by peer
                        if sys.exc_info()[1].errno == 104:
                            numTries += 1
                            continue
                        else:
                            msg = "Download of file %s failed: %s" \
                                  %(infoVer, e)
                            print msg
                            self.report.write("%s\n" %msg)
                            
                            ret = False
                            
                    except Exception, e:
                        msg = "Download of file %s failed: %s" %(infoVer, e)
                        print msg
                        self.report.write("%s\n" %msg)
                        
                        ret = False

                    else:
                        # success! 
                        print "Writing data export file %s to local filesystem" \
                              %infoVer
                        f = file(bkfPath, 'w+b')
                        f.write(zipdata)
                        f.close()
                        self.backupPath = bkfPath
                        msg = "Data Export File %s Download Completed:\n\t%s" \
                              %(infoVer, bkfPath)
                        print msg
                        self.report.write("%s\n\n" %msg)
                        pass
                    
                    break

                # note failure if we're out of retries
                if numTries >= maxTries:
                    msg = "Download of file %s failed. Out of retries" \
                          %(infoVer)
                    print msg
                    self.report.write("%s\n\n" %msg)
                    ret = False

                
                
            else:
                msg = "Export file %s has already been downloaded for %s" \
                      %(matchTuple[1], timestamp)
                print msg
                self.report.write("%s\n" %msg)
                # ret = False # let's not call this a failure per se
                pass
            
            continue

        self.enforceRetentionPolicy()
        return ret
    # END download export
            

    def enforceRetentionPolicy(self):
        """
        Look into the backup directory and prune backup archives that
        we no longer wish to keep.  Current policy is to keep the
        six most recent backups, while always saving the first backup
        of a given month.

        """
        import glob
        
        bkfBase = self.props.get('backup','backupFileBasename')
        bkfExt = self.props.get('backup','backupFileTypeExt')
        bkfDir = self.props.get('backup','backupFileDir')
        bkfGlob = "%s*.%s" %(bkfBase, bkfExt)

        bkMonthlyDir = self.props.get('backup','backupMonthlyDir')
        
        retainNum = self.props.getint('backup','backupRetainNum')
        bkFreqDays = self.props.getint('backup','backupFreqDays')

        tsPat = "%s-(\d{8}-\d{4})(_[\d\*]+)?\.%s" %(bkfBase, bkfExt)
        tsRE = re.compile(tsPat)

        files = glob.glob(os.path.join(bkfDir, bkfGlob))
        files.sort() # We can cheat because the timestamps are string-sortable
        files.reverse()
        #pprint.pprint(files)

        savelist = []
        for bkfile in files:
            match = re.search(tsRE, bkfile)
            datetuple = time.strptime(match.group(1), timestampFmt)
            
            # Make sure we have the first backup of each month
            if datetuple[2] <= bkFreqDays:
                bkMonthlyPath = os.path.join(bkMonthlyDir, match.group(0))
                if not os.path.exists(bkMonthlyPath):
                    msg = "Retaining first backup of month:\n\t %s" \
                          %match.group(0)
                    print msg
                    self.report.write("%s\n" %msg)
                    os.link(bkfile, bkMonthlyPath)
                    pass
                pass

            # Now, keep files for the first six unique datetuples
            if (len(savelist) == retainNum and datetuple not in savelist) or \
                   len(savelist) > retainNum:
                
                if len(savelist) == retainNum:
                    msg = "Saving only the %d most recent backups; removing older backups:" %retainNum
                    print msg
                    self.report.write("\n%s\n" %msg)
                    pass
                
                msg = "\tRemoving " + bkfile
                print msg
                self.report.write("%s\n" %msg)
                os.remove(bkfile)
                pass

            if datetuple not in savelist:
                savelist.append(datetuple)
            continue

        return
    ## END enforceRetentionPolicy(self)

    def emailReport(self, msg):
        """
        Send an email with the contents of the class report buffer
        """
        subject = "SFDC %s" %msg

        smtpserver = self.props.get('main', 'smtpServer')
        mailNotifyFrom = self.props.get('backup', 'backupNotifyFrom')
        mailNotifyToList = ConfigHelper.parseConfigList(self.props.get('backup', 'backupNotifyToList'))
        mailserver = mailServer.MailServer(smtpServer=smtpserver)
        emailTxt = mailserver.setEmailTxt(fromAddress=mailNotifyFrom,
                                          toArray=mailNotifyToList,
                                          subject=subject,
                                          msgStr=self.report.getvalue())

        mailserver.sendEmail(fromAddr=mailNotifyFrom,
                             toAddrs=mailNotifyToList,
                             emailTxt=emailTxt,
                             subject=subject)
    ## END emailReport(self)


    def do(self):
        """
        The main flow for Backup
        """
        requestIntervalSecs = self.props.getint('backup',
                                                'backupReqRetryMins') * 60
        
        # get the Export page
        waitState = "WAIT"
        state = waitState
        while state == waitState:
            state, msg = self.sfExportPage()
            print msg
            if state == waitState:
                time.sleep(requestIntervalSecs)

        if len(self.report.getvalue()) and \
               (state == "DONE" or not sys.stdout.isatty()):
            self.emailReport(msg)
    ## END do()


def main():
    # Fetch the config
    props = ConfigHelper.fetchConfig('conf/sfutil.cfg')
    
    backup = Backup(props)

    if backup is None:
        print "Login to salesforce.com failed"
        sys.exit(1)
        
    backup.do()
## END main()    


if __name__=='__main__':
    main()
