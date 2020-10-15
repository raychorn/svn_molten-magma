"""
Interactively log in and access the salesforce.com website in order to
perform a full data export.

Note: This script cannot perform an export in a single pass.  Instead,
it must check that the export window is currently open (only one
export is allowed every 6 days). If it is, then it must request the
export, which will be finished at a later time. Since the script won't
receive the email notification when the export is finished, it will
simply have to check back later until a download is available, then
fetch the package.

Author:		Kevin Shuk <kshuk@molten-magma.com>
Date:		Mar 14, 2004
Copyright: 	(c) 2004 - 2005, Kevin Shuk and Magma Design Automation, Inc.
                All Rights Reserved
"""

ident = "$ID: $"
#version = 1.0  # Mar 14, 2004. First export script.
#version = 1.1 # Apr 12, 2004. Handle multi-file export
version = 1.5  # Sep 17, 2005. Minor refactor - make standalone

import re
import glob
import time
import sys
import os
import cStringIO
import pprint
import base64
from email.MIMEText import MIMEText
import smtplib
import errno

from Properties import Properties
props = Properties()

import logging
log = logging.getLogger()
log.setLevel(logging.INFO)

import AuthUtil
from SfdcWebScrape import SfdcWebScrape

### Global definitions ###
timestampFmt = '%Y%m%d-%H%M'
### END Global definitions ###

class SfdcExport(SfdcWebScrape):
    """
    Class to manage the request and download of an SFDC weekly export.

    Instantiating this class and calling the do() method will initiate the
    action. 

    """
    cookieJar = None
    urlOpener = None
    fileOpener = None

    report = cStringIO.StringIO()

    def __init__(self):
        uname = props.uname
        if uname is None:
            uname = AuthUtil.getinput("Username")
            pass
        
        pw = None
        encpw = props.encpw
        if encpw is None:
            pw = AuthUtil.getpass()
        else:
            pw = base64.decodestring(encpw)
            pass

        # parent class init performs login
        SfdcWebScrape.__init__(self, uname, pw)
    ## END __init__
    

    def extractTitleTag(self, body):
        """
        Given HTML page source, extract and return the string within the
        title tags

        Parameters:
        body - complete HTML page source

        Returns:
        string contents of HTML title tags
        
        """
        titleTagPat = "^\s*<title>(.*)</title>"
        matchObj = re.search(titleTagPat, body, re.M|re.I)
        title = None
        if matchObj is not None:
            title = matchObj.group(1)
            pass
        
        return title
    ## END extractTitleTag


    def extractExportForm(self, body):
        """
        Finds the editPage form in the body of the main export page
        
        Parameters:
        body - complete HTML page source

        Returns:
        string text of the form named editPage, or None if this can't be found
        """
        editPageFormRE = re.compile('<form[^>]*?name="editPage".*?>.*?</form>',
                                    re.M|re.I|re.S)
        matchObj = editPageFormRE.search(body)
        form = None
        if matchObj is not None:
            form = matchObj.group()
            pass
        
        return form
    ## END extractEditPageForm


    def extractHiddenFormElts(self, formBody):
        """
        Extracts elements of type 'hidden' from a form.
        
        Parameters:
        formBody - string contiaining an entire HTML form, including the opening and closing form tags.

        Returns:
        List of tuples with name-value pairs of the hidden form fields.
        
        """
        hiddenFldRE = re.compile('<input.*?type="hidden".*?>', re.M|re.I|re.S)
        hiddenFldNameRE = re.compile('name="(.*?)"[ >]', re.M|re.I)
        hiddenFldValueRE = re.compile('value="(.*?)"[ >]', re.M|re.I)

        # find each hidden element
        hiddenFldTags = hiddenFldRE.findall(formBody)

        hiddenFldElts = []
        for hiddenFldTag in hiddenFldTags:
            # find the name and value args for each hidden field
            nameMatch = hiddenFldNameRE.search(hiddenFldTag)
            valueMatch = hiddenFldValueRE.search(hiddenFldTag)
            
            if nameMatch is not None and valueMatch is not None:
                elt = (nameMatch.group(1), valueMatch.group(1))
                hiddenFldElts.append(elt)
                pass
            continue
        
        return hiddenFldElts
    ## END extractHiddenFormElts

        
    def scanExportPage(self):
        """
        Access the export page and by parsing the title of the page,
        determine the action to be taken, then take that action.

        Possible actions are:
        - Request the export
        - Wait for the export
        - Download the waiting export

        Returns a tuple consisting of a state code and a corresponding message.
        State codes (and meanings) are:
        ERR - an expected response was recieved or the page didn't contain information we were expecting
        WAIT - export has ben requested, but is not yet ready for download
        NA - export is not available at this time (previously requested export is no longer available, but org is not eligible for another export yet)
        DONE - export has been completely downloaded

        """
        resultTuple = None
        
        response = self.sendRequest(props.exportUrl, self.urlOpener)

        responseBody = "%s" %response.read()
        response.seek(0)

        titleStr = self.extractTitleTag(responseBody)
        if titleStr is None:
            msg = "Can't find title tag in Export page source:\n\n%s" \
                  %responseBody
            self.report.write("%s\n" %msg)
            resultTuple = ("ERR", msg)
            
        # Handle various cases based upon contents of the title tag:
        if re.search("Data Export Service: Export File Delivery",
                     titleStr, re.I) is not None:
            # Need to request an export from Salesforce
            if self.requestExport(responseBody):
                msg = "Export has been requested and is in progress"
                resultTuple = ("WAIT", msg)
            else:
                msg = "Export resuest failed"
                self.report.write("%s\n" %msg)
                resultTuple = ("ERR", msg)
                pass
            
        elif re.search("Export (In Progress|Requested)", titleStr, re.I) is not None:
            # The export is in progress, but is not ready yet.
            # Punt this time and try later
            msg = "Export not yet ready for download; Sleeping until next check interval."
            resultTuple = ("WAIT", msg)
        
        elif re.search("Data Export File Delivery", titleStr,re.I) is not None:
            # It's ready! Check the timestamp and see if we've already
            # downloaded it. If not, download it now.
            if self.downloadExport(responseBody) is True:
                msg = "Data export download has completed"
                resultTuple = ("DONE", msg)
            else:
                msg = "Data export download failed"
                resultTuple = ("ERR", msg)
                pass
            
        elif re.search("Export Already Run", titleStr, re.I) is not None:
            # Export isn't available at this time - punt
            msg = "Data export is unavailable for request or download at this time"
            self.report.write("%s\n" %msg)
            resultTuple = ("NA", msg)
        
        else:
            # Unhandled case?
            msg = "Unhandled case in title string:\n%s" %titleStr
            log.warn(msg)
            self.report.write("%s\n" %msg)
            resultTuple = ("ERR", msg)
            pass

        return resultTuple
    ## END scanExportPage


    def requestExport(self, pageBody):
        """
        Sends a POST request to the export URL (set in properties) requesting
        a data export.

        Options (also set in properties) include:
        * Whether to include attachaments and docs in the export
        * Whether to replace carriags returns with spaces in the export
        * Which object types to export
        * The encoding for the export

        Parameters:
        pageBody - complete HTML source

        Returns:
        boolean indicating success of request

        """
        # NOTE - reqElems is the fields/values for the form POST
        # It can be a dict or a sequence of name/value tuples.
        # We have to use the latter method here because we have
        # checkboxes which, when multiple values are checked,
        # cannot be expressed with a dictionary in a way that
        # urllib.urlencode can grok.

        # first, get the hidden fields for the export request form
        # we may not need this step if the form values retURL,
        # save_new_url and setupid are not needed.
        exportFormBody = self.extractExportForm(pageBody)
        reqElems = self.extractHiddenFormElts(exportFormBody)
        
        # save is the Submit button
        reqElems.append(("save", "Data Export"))

        #p1 = save attachments/docs.
        # the str(int()) thing is a double coercion:
        # First we coerce the boolean property to 1 (True) or 0 (False)
        # Then we coerce that int into a string for the POST request
        reqElems.append(("p1", str(int(props.incAttach))))

        #p2 is the requested encoding for the export
        reqElems.append(("p2", props.encoding))
        
        #p6 = replace carriage returns with spaces.
        #coerce boolean property to int for 1 or 0
        reqElems.append(("p6", str(int(props.replaceCRs))))

        # entityFilter determines which entities will be exported
        for entityType in props.exportTypes:
            reqElems.append(("entityFilter", entityType))
            continue

        log.debug("Form values being sent with the export request:")
        log.debug(pprint.pformat(reqElems))

        response = self.sendRequest(props.exportUrl, self.urlOpener,
                                    params=reqElems, method='POST')

        # See if we get a reasonable response page by checking the title
        # Until then, always return False
        responseBody = "%s" %response.read()
        titleStr = self.extractTitleTag(responseBody)

        resultBool = False
        if titleStr is not None and \
               re.search("Export Requested", titleStr, re.I) is not None:
            resultBool =  True
        elif titleStr is None:
            msg = "Bad response after requesting export. Couldn't read Result page title."
        else:
            msg = "Unexpected response after requesting export\n%s" \
                  %titleStr
            pass
        
        if resultBool is False:
            log.error(msg)
            self.report.write("%s\n" %msg)
            pass
        
        return resultBool
    ## END requestExport


##    def downloadExportOld(self, dlPageBody):
##        """
##        Takes the page source of the "export ready" page, regexes for the
##        download URL(s) and downloads each component of the export.

##        Parameters:
##        dlPageBody - page source of the "export ready" page.
##        """
##        ret = False
##        bkfBase = props.exportFileBasename
##        bkfExt = props.exportFileTypeExt
##        bkfDir = props.exportFileDir

##        # Find Schedule Date:
##        sdPat = "Schedule Date:.*>\s*(\d+/\d+/\d+ \d+:\d+ [AP]M)</td>"
##        matchObj = re.search(sdPat, dlPageBody, re.I|re.S)
##        if matchObj is not None:
##            sd = matchObj.group(1)
##            sdTime = time.strptime(sd, "%m/%d/%Y %I:%M %p")
##            timestamp = time.strftime(timestampFmt, sdTime)
##        else:
##             msg = "ERROR: Cannot extract schedule date with pattern:\n%s" \
##                   %sdPat
##             log.error(msg)
##             self.report.write("%s\n" %msg)
##             return ret

##        bkfName = "%s-%s_*.%s" %(bkfBase, timestamp, bkfExt)
##        bkfPath = os.path.join(bkfDir, bkfName)

##        # regex to find all export URLs from the page
##        dlUrlPat = r'<a href="(/servlet/servlet.OrgExport\?fileName=([^"]*))">Click here'
##        dlUrlRE = re.compile(dlUrlPat, re.I|re.S|re.M)

##        # regex to extract each export file's part number
##        dlSerialRE = re.compile(r'WE_[^_]+_(\d+).ZIP')


##        # search for all the export file URLs.
##        matchList = dlUrlRE.findall(dlPageBody)

##        if len(matchList):
##            ret = True
##            pass

##        for matchTuple in matchList:
##            # the contents of this for loop would be the idea candidate to
##            # break out for multi-threaded download.
##            dlUrl = "%s%s" %(props.baseUrl, matchTuple[0])
            
##            # get the file serial number if present
##            serialMatch = dlSerialRE.search(matchTuple[1])

##            # build a filename for the export file
##            if serialMatch is not None:
##                bkfSer = serialMatch.group(1)
##                bkfName = "%s-%s_%s.%s" %(bkfBase, timestamp, bkfSer, bkfExt)
##                infoVer = "%s of %s" %(bkfSer, len(matchList))
##            else:
##                bkfName = "%s-%s_1.%s" %(bkfBase, timestamp, bkfExt)
##                infoVer = "1 of 1"
##                pass

##            bkfPath = os.path.join(bkfDir, bkfName)
            
##            if not os.path.exists(bkfPath):
##                # don't already have this file - download it
##                log.info("Downloading data export file %s..." %infoVer)

##                maxTries = 5
##                numTries = 0

##                while numTries < maxTries:
                
##                    try:
##                        zipdata = self.sendRequest(dlUrl,
##                                                   self.fileOpener).read()

##                    except IOError, e:
##                        # loop around and try again if connection is
##                        # reset by peer
##                        if sys.exc_info()[1].errno == 104:
##                            numTries += 1
##                            continue
##                        else:
##                            msg = "Download of file %s failed: %s" \
##                                  %(infoVer, e)
##                            log.error(msg)
##                            self.report.write("%s\n" %msg)
                            
##                            ret = False
##                            pass
                        
##                    except Exception, e:
##                        msg = "Download of file %s failed: %s" %(infoVer, e)
##                        log.error(msg)
##                        self.report.write("%s\n" %msg)
                        
##                        ret = False
                        
##                    else:
##                        # success! 
##                        log.info("Writing data export file %s to local filesystem" %infoVer)
##                        f = file(bkfPath, 'w+b')
##                        f.write(zipdata)
##                        f.close()
##                        msg = "Data Export File %s Download Completed:\n\t%s" \
##                              %(infoVer, bkfPath)
##                        log.info(msg)
##                        self.report.write("%s\n\n" %msg)
##                        pass
                    
##                    break

##                # note failure if we're out of retries
##                if numTries >= maxTries:
##                    msg = "Download of file %s failed. Out of retries" \
##                          %(infoVer)
##                    log.error(msg)
##                    self.report.write("%s\n\n" %msg)
##                    ret = False
##                    pass
                
##            else:
##                msg = "Export file %s has already been downloaded for %s" \
##                      %(matchTuple[1], timestamp)
##                log.warn(msg)
##                self.report.write("%s\n" %msg)
##                # ret = False # let's not call this a failure per se
##                pass
            
##            continue

##        self.enforceRetentionPolicy()
##        return ret
##    # END download export

    def downloadExport(self, dlPageBody):
        """
        Takes the page source of the 'export ready' page, regexes for the
        download URL(s) and downloads each component of the export.

        Parameters:
        dlPageBody - page source of the 'export ready' page.

        """
        success = False
        # Find Schedule Date:
        sdPat = "Schedule Date:.*>\s*(\d+/\d+/\d+ \d+:\d+ [AP]M)</td>"
        matchObj = re.search(sdPat, dlPageBody, re.I|re.S)
        if matchObj is not None:
            sd = matchObj.group(1)
            sdTime = time.strptime(sd, "%m/%d/%Y %I:%M %p")
            timestamp = time.strftime(timestampFmt, sdTime)
        else:
             msg = "ERROR: Cannot extract schedule date with pattern:\n%s" \
                   %sdPat
             log.error(msg)
             self.report.write("%s\n" %msg)
             return success

        # regex to find all export URLs from the page
        dlUrlPat = r'<a href="(/servlet/servlet.OrgExport\?fileName=.*?)">Click here'
        dlUrlRE = re.compile(dlUrlPat, re.I|re.S|re.M)

        # search for all the export file URLs.
        urlMatchList = dlUrlRE.findall(dlPageBody)

        if len(urlMatchList) > 0:
            # we may not download any files, but still be successful
            success = True
            pass

        for relativeUrl in urlMatchList:
            dlUrl = "%s%s" %(props.baseUrl, relativeUrl)
            fileSuccess = self.downloadExportFile(dlUrl,
                                                  timestamp,
                                                  len(urlMatchList))

            if success is True:
                # Only accept the status of the most recent file download
                # if none have failed so far
                success = fileSuccess
                pass
            continue

        self.enforceRetentionPolicy()
        return success

    def buildFilename(self, dlUrl, timestamp, segmentCt):
        """
        from the download URL and the export timestamp, build a filename
        for the export segment file. Also recover the segment number.

        Parameters:
        dlUrl - the download URL as extracted from the download HTML page
        timestamp - formatted string expressing the scheduled time of the export

        Returns:
        tuple of filename for the export segment and the serial number of the segment
        
        """
        expFileBase = props.exportFileBasename
        expFileExt = props.exportFileExtension

        # regex to extract the filename from the download URL
        dlFileRE = re.compile(r'fileName=(.*)', re.I|re.S|re.M)
        dlFileMatch = dlFileRE.search(dlUrl)
        dlFilename = dlFileMatch.group(1)

        # get the file serial number if present
        expFileSerial = 1
        dlSerialRE = re.compile(r'WE_[^_]+_(\d+).ZIP')
        serialMatch = dlSerialRE.search(dlFilename)

        if serialMatch is not None:
            expFileSerial = serialMatch.group(1)
            pass
        
        # build a filename for the export file
        expFileName = "%s-%s_%sof%s.%s" %(expFileBase, timestamp,
                                          expFileSerial, segmentCt,
                                          expFileExt)

        return expFileName, expFileSerial
    ## end buildFileName

            
    def downloadExportFile(self, dlUrl, timestamp, segmentCt):
        """
        Downloads the export segment file at the provided URL.

        Paramters:
        dlUrl - URL where the download file is to be found
        timestamp - formatted time string as parsed from the download page
        segmentCt - total number of export segment files in the export

        Returns:
        boolean indicating success or failure of the file download

        """
        # if anything bad happens, success goes to False
        success = True

        expFileDir = props.exportFileDir
        
        expFileName, expSegmentSerial = self.buildFilename(dlUrl, timestamp,
                                                           segmentCt)
                                         
        expFilePath= os.path.join(expFileDir, expFileName)
        infoVer = "%s of %s" %(expSegmentSerial, segmentCt)

        if not os.path.exists(expFilePath):
            # don't already have this file - download it
            maxTries = 5
            numTries = 0

            while numTries < maxTries:

                try:
                    if numTries == 0:
                        log.info("Downloading data export file %s" %infoVer)
                    else:
                        log.info("Retrying download of data export file %s" %infoVer)
                        pass
                    
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
                        log.error(msg)
                        self.report.write("%s\n" %msg)

                        success = False
                        pass

                except Exception, e:
                    msg = "Download of file %s failed: %s" %(infoVer, e)
                    log.error(msg)
                    self.report.write("%s\n" %msg)

                    success = False
                    
                else:
                    # success! 
                    log.info("Writing data export file %s to local filesystem" %infoVer)
                    f = file(expFilePath, 'w+b')
                    f.write(zipdata)
                    f.close()
                    msg = "Data Export File %s Download Completed:\n\t%s" \
                          %(infoVer, expFilePath)
                    log.info(msg)
                    self.report.write("%s\n\n" %msg)
                    pass

                break

            # note failure if we're out of retries
            if numTries >= maxTries:
                msg = "Download of file %s failed. Out of retries" \
                      %(infoVer)
                log.error(msg)
                self.report.write("%s\n\n" %msg)
                success = False
                pass

        else:
            msg = "Export file %s has already been downloaded for %s" \
                  %(expFileName, timestamp)
            log.warn(msg)
            self.report.write("%s\n" %msg)
            # ret = False # let's not call this a failure per se
            pass

        return success
    ## END downloadExportFile
       

    def enforceRetentionPolicy(self):
        """
        Look into the backup directory and prune exports that
        we no longer wish to keep and store exports eligible for
        long-term archival.

        The policy we support is to keep N most recent exports (N is
        configurable via the properties file) and also to archive the
        first backup of each month. Anything beyond this is up to the user.

        """
        exportFileBase = props.exportFileBasename
        exportFileExt = props.exportFileExtension
        exportFileGlob = "%s*.%s" %(exportFileBase, exportFileExt)

        exportDir = props.exportFileDir
        archiveDir = props.exportArchiveDir
        
        retainCount = props.retainCount
        exportFreqDays = props.frequencyDays

        # pattern to find the timestamp of each file
        tsPat = "%s-(\d{8}-\d{4})_\d+of\d+\.%s" %(exportFileBase,
                                                  exportFileExt)
        tsRE = re.compile(tsPat)

        files = glob.glob(os.path.join(exportDir, exportFileGlob))
        files.sort() # We can cheat because the timestamps are string-sortable
        files.reverse()

        savelist = []
        for exportFile in files:
            print tsPat
            print exportFile
            match = re.search(tsRE, exportFile)
            datetuple = time.strptime(match.group(1), timestampFmt)
            
            # Make sure we have the first backup of each month
            if datetuple[2] <= exportFreqDays:
                archivePath = os.path.join(archiveDir, match.group(0))
                if not os.path.exists(archivePath):
                    msg = "Retaining first backup of month:\n\t %s" \
                          %match.group(0)
                    log.info(msg)
                    self.report.write("%s\n" %msg)
                    os.link(exportFile, archivePath)
                    pass
                pass

            # Now, keep files for the first six unique datetuples
            if (len(savelist) == retainCount \
                and datetuple not in savelist) or \
                   len(savelist) > retainCount:
                
                if len(savelist) == retainCount:
                    msg = "Saving only the %d most recent backups; removing older backups:" %retainCount
                    log.info(msg)
                    self.report.write("\n%s\n" %msg)
                    pass
                
                msg = "\tRemoving %s" %exportFile
                log.info(msg)
                self.report.write("%s\n" %msg)
                os.remove(exportFile)
                pass

            if datetuple not in savelist:
                savelist.append(datetuple)
            continue

        return
    ## END enforceRetentionPolicy


    def emailReport(self, subject):
        """
        Send an email with the contents of the class report buffer
        
        """
        COMMASPACE = ", "

        msg = MIMEText(self.report.getvalue())

        msg['Subject'] = "SFDC %s" %subject
        msg['From'] = props.fromEmail
        msg['To'] = COMMASPACE.join(props.toEmailList)

        print msg

        smtpPw = None
        if props.smtpEncpw is not None:
            smtpPw = base64.decodestring(props.smtpEncpw)
            pass

        try:
            smtpserver = smtplib.SMTP(props.smtpHost, props.smtpPort)

            # optional smtp login if both user and pass are in config
            if props.smtpUser is not None and smtpPw is not None:
                print "logging into smtp server with |%s|%s|" %(props.smtpUser, smtpPw)
                smtpserver.login(props.smtpUser, smtpPw)
                pass

            smtpserver.sendmail(props.fromEmail, props.toEmailList, str(msg))
            smtpserver.quit()
        except Exception, e:
            errmsg = "Could not send email report: %s" %e
            log.error(errmsg)
            pass

        #log.info(self.report.getvalue())
        return
    ## END emailReport

    def checkExportDir(self, dirPath):
        """
        Ensure that specified dir is created and writable
        
        """
        if not os.path.exists(dirPath):
            os.makedirs(dirPath)
        elif not os.path.isdir(dirPath):
            raise IOError(errno.ENOTDIR, "Not a directory", dirPath)
        else:
            # check for writability
            # errno.EACCES "Permission denied - cannot write to dir"
            if not os.access(dirPath, os.W_OK):
                raise IOError(errno.EACCES,
                              "Permission denied - cannot write to dir",
                              dirPath)
            pass
        return
    ## END checkExportDir
    

    def do(self):
        """
        The main flow for the export process

        """
        pollIntervalSecs = props.pollIntervalMins * 60
        
        waitState = "WAIT"
        state = waitState

        # Ensure export destination directory is present and writable
        try:
            self.checkExportDir(props.exportFileDir)
            self.checkExportDir(props.exportArchiveDir)

        except Exception, e:
            msg = "Problems detected with export or archive directory: %s" %e
            log.error(msg)
            self.report.write("%s\n" %msg)
        
        else:
            # continue to loop getting the Export page
            # pausing for pollIntervalSecs between iterations,
            # as long as we're in a waiting state
            while state == waitState:
                state, msg = self.scanExportPage()
                log.info(msg)
                if state == waitState:
                    time.sleep(pollIntervalSecs)
                    pass

                continue
            pass
        
        if len(self.report.getvalue()) and \
               (state == "DONE" or not sys.stdout.isatty()):
            self.emailReport(msg)
            pass

        return
    ## END do


def main():
    export = SfdcExport()

    if export is None:
        log.critical("Login to salesforce.com failed")
        sys.exit(1)
        pass
    
    export.do()
    return
## END main()    


if __name__=='__main__':
    main()
