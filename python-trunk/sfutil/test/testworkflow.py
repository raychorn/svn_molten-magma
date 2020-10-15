#!/usr/bin/env python2.3

'''
tests the progression of  mod(s) from addition
(binding a branch, codestream and one or more change requests),
submission and approval.

script cleans up by removing the token file it creates from
/magma/scm-release/submissions/sf-scm
'''
#version = 0.90  # 02/25/2004 First complete version, straight workflow addmod->submitbranch->approvebranch->wait for SCM token
#version = 0.91 # 02/27/2004 Functional completion. Added rmmod. 
#version = 0.99 # 03/01/2004 Some time formatting. Needs testing.
#version = 1.0 # 03/01/2004 Small syntax fixes. Tested & passed
version = 1.01 # 03/01/2004 Small fix to extractElapsedTime which recounted the seconds onverted to hours.

import sys, os, time, whrandom, re, glob, fcntl, ConfigParser
import string, StringIO
import logging, logging.handlers
import pexpect
import Timer, ConfigHelper, mailServer

# Fetch the config
props = ConfigHelper.fetchConfig('../conf/sfutil.cfg')
main = 'main' # main config file section

# setup - get the config properties we're interested in
testId = props.get(main, 'testId')

crList = ConfigHelper.parseConfigList(props.get(main, 'crList'))
streamList = ConfigHelper.parseConfigList(props.get(main, 'streamList'))

batchOwner = props.get(main, 'batchOwner')
batchOwnerHome = props.get(main, 'batchOwnerHome')

addmodPath = props.get(main, 'addmodPath')
rmmodPath = props.get(main, 'rmmodPath')
submitbranchPath = props.get(main, 'submitbranchPath')
approvebranchPath = props.get(main, 'approvebranchPath')

tokenDir = props.get(main, 'tokenDir')

tokenminderInboxName = props.get(main, 'tokenminderInbox')
tokenminderInbox = os.path.join(batchOwnerHome, tokenminderInboxName)

sfSubmitterUname = props.get(main, 'submitterUname')
sfSubmitterEncPw = props.get(main, 'submitterEncPw')
sfApproverUname = props.get(main, 'approverUname')
sfApproverEncPw = props.get(main, 'approverEncPw')
sfPeUname = props.get(main, 'peUname')
sfPeEncPw = props.get(main, 'peEncPw')

timeout = props.getint(main, 'expectTimeoutSecs')

home = os.getenv('HOME')


pwFileBaseName = props.get(main, 'pwFileBaseName')
pwFilePath = os.path.join( home, '.%s' %pwFileBaseName)
pwSideFilePath = '%s_TESTSIDE' %pwFilePath
submitterPwFilePath = os.path.join( home, '.%s-submitter' %pwFileBaseName)
approverPwFilePath = os.path.join( home, '.%s-approver' %pwFileBaseName)
pePwFilePath = os.path.join( home, '.%s-pe' %pwFileBaseName)

lockFilePath = os.path.join( home, '%s.lock' %testId)
lockFile = None


# generate a unique branch name w/ timestamp
timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime())
branchId = "testworkflow_%s" %timestamp


# setup for logging
logFilePath = os.path.join(batchOwnerHome, 'log', 'tests.log')

tlhdlr = logging.handlers.RotatingFileHandler(logFilePath, "a", 50000000, 20)
tlshdlr = logging.StreamHandler(sys.stderr)
tlfmt  = logging.Formatter("%(asctime)s %(name)-30s %(message)s", "%x %X")
tlhdlr.setFormatter(tlfmt)

testLog = logging.getLogger(branchId)

testLog.addHandler(tlhdlr)
if sys.stderr.isatty():
    testLog.addHandler(tlshdlr)

testLog.setLevel(logging.INFO)


# setup for mail
smtpServer =  props.get(main, 'smtpServer')
mailNotifyFrom = props.get(main, 'mailNotifyFrom')
mailNotifyToList = ConfigHelper.parseConfigList(props.get(main, 'mailNotifyToList'))

# store the mods we create for later removal
modList = []

# moved into mail routine
#mailserver = mailServer.MailServer(smtpServer=props.get(main, 'smtpServer'),
#                                   logger=testLog)


def cleanup():
    global lockFile
    if lockFile is not None:

        if os.path.islink(pwFilePath):
            os.remove(pwFilePath)
        
        # remove .sfdcLogin provided that it's a symlink
        if os.path.islink(pwFilePath):
            os.remove(pwFilePath)
                
        # if .sfdcLogin.SIDE exists, replace it
        if os.path.exists(pwSideFilePath):
            os.rename(pwSideFilePath, pwFilePath)
                    
        # remove sfdclogin-submitter, sfdclogin-approver
        if os.path.exists(submitterPwFilePath):
            os.remove(submitterPwFilePath)
        
        if os.path.exists(approverPwFilePath):
            os.remove(approverPwFilePath)
    
        # remove lock file
        lockFile.close()
        lockFile = None
## END cleanup()


def fail(failCode=1, msg=None):
    if msg is not None:
        msg = "FAILED: %s" % msg
    else:
        msg = "UNSPECIFIED FAILURE."

    testLog.critical(msg)

    mailSubject="testworkflow failure on branch %s" % branchId

    sendEmailNotification(subject=mailSubject,
                          msgStr=msg)

    sys.exit(failCode)
## END fail(failCode, msg)


def sendEmailNotification(subject, msgStr=None, msgBuf=None):
    '''
    Simple wrapper for sending emails. Assumes all emails come from one place
    and go to one (set of) address(es) as specified in the config file.

    parameters:
    mailserver - an instance of MailServer.
    
    subject - String with the email subject line.
    
    msgStr
    msgBuf - Either a string or a buffer with the email message body.
    May pass in either one, but if both are passed in, the string will
    be preferred. 
    '''

    mailserver = mailServer.MailServer(smtpServer=props.get(main,'smtpServer'),
                                       logger=testLog)

    if msgStr is not None:
        emailTxt = mailserver.setEmailTxt(fromAddress=mailNotifyFrom,
                                          toArray=mailNotifyToList,
                                          subject=subject,
                                          msgStr=msgStr)
    elif msgBuf is not None:
        emailTxt = mailserver.genEmailTxt(fromAddress=mailNotifyFrom,
                                          toArray=mailNotifyToList,
                                          subject=subject,
                                          buf=msgBuf)
    else:
        emailTxt = "Email body was left blank"

    mailserver.sendEmail(fromAddr=mailNotifyFrom,
                         toAddrs=mailNotifyToList,
                         emailTxt=emailTxt,
                         subject=subject)    
## END def sendEmailNotification(subject, msgStr, msgBuf)
    


def pwFileWrite(pwFilePath, uname, encPasswd):
    if os.path.exists(pwFilePath):
        os.remove(pwFilePath)
        
    pwFile = file( pwFilePath, 'w')
    pwFile.write( 'Username\t%s\n' % uname )
    pwFile.write( 'Password\t%s' % encPasswd)
    pwFile.close()
    os.chmod(pwFilePath, 0400)
## END pwFileWrite(pwFilePath, uname, passwd)

def tokenminderDrop(tmDropBox, tokenPath):
    (tokenDir, tokenBase) = os.path.split(tokenPath)
    tmDropPath = os.path.join(tmDropBox, "%s.tm" %tokenBase)
    fd = file(tmDropPath, 'w+')
    fd.write(tokenPath)
    fd.close()
    os.chmod(tmDropPath, 0770)
## END tokenminderDrop(tmDropBox, tokenPath):

def extractElapsedTime(baseSeconds):
    '''
    Given an input of elapsed seconds, returns the elapsed time
    in hours, minutes and seconds via a list.
    '''
    
    secondsInHour = 3600
    secondsInMin  = 60
    
    # throw away sub-seconds
    baseSeconds = int(baseSeconds)

    # extract the hours from the total number of seconds
    elapsedHrs = baseSeconds / secondsInHour

    # extract the minutes from the remaining seconds
    baseSeconds = baseSeconds % secondsInHour
    elapsedMins = baseSeconds / secondsInMin

    # keep the left-over seconds
    elapsedSecs = baseSeconds % secondsInMin

    return elapsedHrs, elapsedMins, elapsedSecs
## END def extractElapsedTime(baseSecs)

# the mainline
sys.exitfunc = cleanup

# Holds the results for the entire test run
resultSummaryBuf = StringIO.StringIO()
testTimer = Timer.Timer()

# write a start date/time to the buffer
# (yeah, it's unformatted for now)
resultSummaryBuf.write("%s version %s\n" %(testId, version))
resultSummaryBuf.write("Started run at %s.\n" \
                       %(time.strftime('%H:%M.%S %B %d, %Y',
                                       time.localtime(testTimer.getStartTime()))))

# Get an exclusive, non-blocking lock so that only one
# test instance may run at at time!
lockFile = file(lockFilePath, 'w+')
try:
    fcntl.flock(lockFile, fcntl.LOCK_EX|fcntl.LOCK_NB)
except IOError, (errno, errmsg):
    message = "Couldn't acquire lock at %s:\n  [errno %s] %s" \
              %(lockFilePath, errno, errmsg)
    fail(failCode=1, msg=message)

# sanity check for the existence of token drop folder here -
# /magma/scm-release/submissions/sf-scm
if not os.path.isdir(tokenDir):
    message = "Couldn't locate SCM token directory:\n\t%s" %tokenDir
    fail(failCode=1, msg=message)


# generate a sfdcLogin-submitter file in $HOME
pwFileWrite(submitterPwFilePath, sfSubmitterUname, sfSubmitterEncPw)

# generate a sfdcLogin-approver file in $HOME
pwFileWrite(approverPwFilePath, sfApproverUname, sfApproverEncPw)

# generate a sfdcLogin-pe file in $HOME
pwFileWrite(pePwFilePath, sfPeUname, sfPeEncPw)

### addmod phase
resultSummaryBuf.write("\nDeveloper addmod Phase\n")

# move aside the .sfdcLogin cookie file to .sfdclogin.SIDE (if any)
if os.path.exists(pwFilePath):
    os.rename(pwFilePath, pwSideFilePath)

# symlink in the sfdcLogin-submitter file as $HOME/.sfdcLogin
os.symlink(submitterPwFilePath, pwFilePath)

# choose 1-N CRs from pool of CRs 
crId = whrandom.choice(crList)

# choose a codestream from list of codestreams
streamId = whrandom.choice(streamList)

# spawn addmod using above information to create mod, and using
# sfdcLogin-submitter cookieFile
modData = { 'branch' : branchId,
            'stream' : streamId,
            'crs'    : [crId] }
modList.append(modData)

addmodCmd = "%s %s %s %s" %(addmodPath,
                            modData['branch'],
                            modData['stream'],
                            string.join(modData['crs'], ' '))

info = "Running: %s" % addmodCmd
resultSummaryBuf.write("%s\n" %info)
testLog.info(info)

addmodTimer = Timer.Timer()

child = pexpect.spawn(addmodCmd, timeout=timeout)
child.expect(pexpect.EOF)

addmodTotalTime = addmodTimer.stop()

addmodResult =  child.before
child.close()

# learn to scan result for myriad failure cases and report if one occurs

# check for success, give feedback (timing, etc)
#MOD for Branch testworkflow_20040224_124940 added owned by testeng@molten-magma.com
addmodSuccessRE = "MOD for Branch %s added owned by %s" \
                   %(branchId, sfSubmitterUname)
connectTimeRE = 'in (\d+\.\d) secs'
addmodSuccessPat = re.compile(addmodSuccessRE)
connectTimePat = re.compile(connectTimeRE)

if addmodSuccessPat.search(addmodResult) is None:
    message = "addmod did not complete. Command output follows:\n%s" \
              % addmodResult
    fail(failCode=1, msg=message)
else:
    connectTime = float(connectTimePat.search(addmodResult).group(1))

resultInfo = """
       Total addmod time %5.1f seconds
            Connect time %5.1f seconds
         addmod run time %5.1f seconds
""" %(addmodTotalTime, connectTime, (addmodTotalTime - connectTime))

# log and built summary email
testLog.info(resultInfo)
resultSummaryBuf.write("%s\n" %resultInfo)

resultSummaryBuf.write("\nDeveloper Submission Phase\n")

# still using submitter ID, spawn submitbranch for this branch
submitbranchCmd = "%s %s" %(submitbranchPath, branchId)
testLog.info("Running: %s" % submitbranchCmd)
submitbranchTimer = Timer.Timer()

child = pexpect.spawn(submitbranchCmd, timeout=timeout)
child.expect(pexpect.EOF)

submitbranchTotalTime = submitbranchTimer.stop()

submitbranchResult =  child.before
child.close()

# learn to watch for myriad failure cases and report if one occurs

# check for success, give feedback (timing, etc)
submitbranchSuccessRE = "UPDATED SF with \d+ MODs for %s on %s" \
                   %(sfSubmitterUname, branchId)
submitbranchSuccessPat = re.compile(submitbranchSuccessRE)

if submitbranchSuccessPat.search(submitbranchResult) is None:
    message = "submitbranch did not complete. Command output follows:\n%s" \
              %submitbranchResult
    fail(failCode=1, msg=message)
else:
    connectTime = float(connectTimePat.search(submitbranchResult).group(1))

resultInfo = """
 Total submitbranch time %5.1f seconds
            Connect time %5.1f seconds
   submitbranch run time %5.1f seconds
""" %(submitbranchTotalTime, connectTime,
      (submitbranchTotalTime - connectTime))
testLog.info(resultInfo)
resultSummaryBuf.write("%s\n" %resultInfo)

### Manager Apporval Phase
resultSummaryBuf.write("\nManager Approval Phase\n")
# remove .sfdcLogin provided that it's a symlink, else move aside
if os.path.islink(pwFilePath):
    os.remove(pwFilePath)
else:
    os.rename(pwFilePath, pwSideFilePath) 

# symlink sfdclogin-approver -> .sfdcLogin
os.symlink(approverPwFilePath, pwFilePath)

# spawn approvebranch for this branch
# This interaction has two parts, divided by a y/n prompt.
approvebranchCmd = "%s %s" %(approvebranchPath, branchId)
testLog.info("Running: %s" %approvebranchCmd)
approveQueryTimer = Timer.Timer()

child = pexpect.spawn(approvebranchCmd, timeout=timeout)
try:
    child.expect("<y/n>\?")
except pexpect.TIMEOUT:
    message = "approvebranch took longer than %s seconds to reach the query.\
Timing out.\n\
Captured output (if any) follows: %s\n" %(timeout, child.before)
    fail(failCode=1, msg=message)

approveQueryTime = approveQueryTimer.stop()
approvebranchTimer = Timer.Timer()

approveQueryResult = child.before
child.sendline("y")

child.expect(pexpect.EOF)

approvebranchTime = approvebranchTimer.stop()
approvebranchTotalTime = approveQueryTime + approvebranchTime

approvebranchResult = child.before
child.close()


# learn to watch for myriad failure cases and report if one occurs


# check for success, give feedback (timing, etc)
approvebranchSuccessRE = "UPDATED SF with \d+ MODs for %s on %s" \
                   %(sfApproverUname, branchId)
approvebranchSuccessPat = re.compile(approvebranchSuccessRE)

if approvebranchSuccessPat.search(approvebranchResult) is None:
    message = "approvebranch did not complete. Command output follows:\n%s\n%s" \
              %(approveQueryResult, approvebranchResult)
    fail(failCode=1, msg=message)
else:
    # we look for the approvebranch connect time info in the
    # first half of the interaction.
    connectTime = float(connectTimePat.search(approveQueryResult).group(1))

resultInfo = """
Total approvebranch time %5.1f seconds
            Connect time %5.1f seconds
   Connect to query time %5.1f seconds
            Approve time %5.1f seconds
""" %((approveQueryTime + approvebranchTime), connectTime,
      (approveQueryTime - connectTime), approvebranchTime)

testLog.info(resultInfo)
resultSummaryBuf.write("%s\n" %resultInfo)

### PE Approval phase
resultSummaryBuf.write("\nPE Approval Phase\n")

# remove .sfdcLogin provided that it's a symlink, else move aside
if os.path.islink(pwFilePath):
    os.remove(pwFilePath)
else:
    os.rename(pwFilePath, pwSideFilePath) 

# symlink sfdclogin-pe -> .sfdcLogin
os.symlink(pePwFilePath, pwFilePath)

# spawn approvebranch for this branch
# This interaction has two parts, divided by a y/n prompt.
approvebranchCmd = "%s %s" %(approvebranchPath, branchId)
testLog.info("Running: %s" %approvebranchCmd)
approveQueryTimer = Timer.Timer()

child = pexpect.spawn(approvebranchCmd, timeout=timeout)
try:
    child.expect("<y/n>\?")
except pexpect.TIMEOUT:
    message = "approvebranch took longer than %s seconds to reach the query.\
Timing out.\n\
Captured output (if any) follows: %s\n" %(timeout, child.before)
    fail(failCode=1, msg=message)

approveQueryTime = approveQueryTimer.stop()
approvebranchTimer = Timer.Timer()

approveQueryResult = child.before
child.sendline("y")

child.expect(pexpect.EOF)

approvebranchTime = approvebranchTimer.stop()
approvebranchTotalTime = approveQueryTime + approvebranchTime

approvebranchResult = child.before
child.close()


# learn to watch for myriad failure cases and report if one occurs


# check for success, give feedback (timing, etc)
approvebranchSuccessRE = "UPDATED SF with \d+ MODs for %s on %s" \
                   %(sfPeUname, branchId)
approvebranchSuccessPat = re.compile(approvebranchSuccessRE)

if approvebranchSuccessPat.search(approvebranchResult) is None:
    message = "approvebranch did not complete. Command output follows:\n%s\n%s" \
              %(approveQueryResult, approvebranchResult)
    fail(failCode=1, msg=message)
else:
    # we look for the approvebranch connect time info in the
    # first half of the interaction.
    connectTime = float(connectTimePat.search(approveQueryResult).group(1))

resultInfo = """
Total approvebranch time %5.1f seconds
            Connect time %5.1f seconds
   Connect to query time %5.1f seconds
            Approve time %5.1f seconds
""" %((approveQueryTime + approvebranchTime), connectTime,
      (approveQueryTime - connectTime), approvebranchTime)

testLog.info(resultInfo)
resultSummaryBuf.write("%s\n" %resultInfo)




# we can unlock the exclusive lock at this point as we're done with the
# password files and can set them back.
cleanup()

# spin-wait for the expected token file to appear.
# report success after finding file and remove it. 
# consider failure and give up after X minutes???
testLog.info("Waiting for the SCM token to arrive in %s" %tokenDir)

tokenTimer = Timer.Timer()
messagesSent = 0
secondsInHour = 3600
#secondsInHour = 60 # make for short hours for testing
tokenFileGlob = "%s/*.%s" %(tokenDir, branchId)

while True:
    if sys.stdout.isatty():
        sys.stdout.write('.')
        sys.stdout.flush()

    elapsedHrs, elapsedMins, elapsedSecs = \
                extractElapsedTime(tokenTimer.getElapsedTime())
    
    elapsedTimeStr = "%02d:%02d.%02d" \
                     %(elapsedHrs, elapsedMins, elapsedSecs)

    tokenCandidates = glob.glob(tokenFileGlob)
    if len(tokenCandidates) == 1:
        # the token has arrived. And there was much rejoicing.

        info = """
The SCM token has shown up at %s.
Elapsed time from approval until the SCM token found was %s
""" %(tokenCandidates[0], elapsedTimeStr)

        resultSummaryBuf.write(info)
        testLog.info(info)

        # send success mail message
        #successSubj="Success - SCM token has arrived for branch %s" %branchId
        #sendEmailNotification(mailserver=mailserver,
        #                      subject=successSubj,
        #                      msgBuf=resultSummaryBuf)

        # Try to remove the token file, or leave a to-do in the token
        # minder drop box
        try:
            os.remove(tokenCandidates[0])
        except OSError:
            tokenminderDrop(tokenminderInbox, tokenCandidates[0])
        break
    
    elif len(tokenCandidates) > 1:
        # uh-oh, this shouldn't be. Send out an alert and break

        info = """
More than one token has shown up for this branch:
%s
Elapsed time from approval until SCM tokens found was %s
""" %(join(tokenCandidates, "\n"), elapsedTimeStr)

        resultSummaryBuf.write(info)
        testlog.warning(info)

        # send success (sort of) mail message
        #warnSubj="Warning - more than one SCM token has arrived for branch %s"\
         #         %branchId
        
        #sendEmailNotification(mailserver=mailserver,
        #                      subject=warnSubj,
        #                      msgBuf=resultSummaryBuf)
        break


    if elapsedHrs > messagesSent:
        if messagesSent < 4:
            # wait up to 5 hours before failing.
            messagesSent += 1
            
            message = "Waiting on SCM token for test branch %s. Elapsed time: %s"  %(branchId, elapsedTimeStr)
            testLog.info(message)
            resultSummaryBuf.write("%s\n" %message)
            #send mail message
            #waitSubj = "Waiting on SCM token for test branch %s. Elapsed time: %s" \
            #           %(branchId, elapsedTimeStr)
            
            #sendEmailNotification(subject=waitSubj,
            #                      msgStr=message)

        elif messagesSent >= 4:
            # declare failure and exit.
            # send failure email.
            info = "Couldn't find the SCM token for branch %s\n\
            after five hours. Giving up and removing MODs." %branchId
            #fail(failCode=1, msg=message)
            resultSummaryBuf.write("%s\n" %info)
            testLog.warning(info)
            break

    time.sleep(5)


# Do the removal
# re-lock
lockFile = file(lockFilePath, 'w+')
try:
    fcntl.flock(lockFile, fcntl.LOCK_EX|fcntl.LOCK_NB)
except IOError, (errno, errmsg):
    message = "Couldn't acquire lock at %s:\n  [errno %s] %s" \
              %(lockFilePath, errno, errmsg)
    fail(failCode=1, msg=message)
    
# re-set the password cookie file to the submitter
pwFileWrite(submitterPwFilePath, sfSubmitterUname, sfSubmitterEncPw)

# move aside the .sfdcLogin cookie file to .sfdclogin.SIDE (if any)
if os.path.exists(pwFilePath):
    os.rename(pwFilePath, pwSideFilePath)

# symlink in the sfdcLogin-submitter file as $HOME/.sfdcLogin
os.symlink(submitterPwFilePath, pwFilePath)

# rmmod each created mod
rmmodResultBuf = StringIO.StringIO()
for modData in modList:
    rmmodResultBuf.truncate(0)
    rmmodCmd = "%s %s %s %s" %(rmmodPath,
                               modData['branch'],
                               modData['stream'],
                               string.join(modData['crs'], ' '))
    testLog.info("Running: %s" %rmmodCmd)
    rmmodTimer = Timer.Timer()
    
    child = pexpect.spawn(rmmodCmd, timeout=timeout)

    #  Do you want to remove the MODs from this CR? <y/n>?
    try:
        child.expect("<y/n>\?")
    except pexpect.TIMEOUT:
        message = "rmmod took more than %d seconds to reach the first query.\
        Timing out.\n\
        Captured output follows: \n%s" %(timeout, child.before)
        fail(failCode=1, msg=message)

    rmmodPart1Result = child.before
    rmmodQuery1Time = rmmodTimer.getElapsedTime()

    child.sendline("y")

    # Are you sure you want to remove the MOD from CR 25819? <y/n>?
    try:
        child.expect("<y/n>\?")
    except pexpect.TIMEOUT:
        message = "rmmod took more than %d seconds to reach the second query.\
        Timing out.\n\
        Captured output follows: \n$s" %(timeout, child.before)
        fail(failCode=1, msg=message)

    rmmodPart2Result = child.before
    rmmodQuery2Time = rmmodTimer.getElapsedTime()

    child.sendline("y")

    child.expect(pexpect.EOF)

    rmmodTotalTime = rmmodTimer.stop()
    
    rmmodFinalResult = child.before
    child.close()

    #Removed MOD testworkflow_20040224_145406 in 4 for 25819 for CR 25819
    rmmodSuccessRE = "Removed MOD %s in %s" \
                     %(modData['branch'],
                       modData['stream'])

    # handle failure case, but don't terminate as we may have more
    # mods to remove.
    if re.search(rmmodSuccessRE, rmmodFinalResult) is not None:
        # we look for the rmmod connect time info in the
        # first half of the interaction.
        connectTime = float(connectTimePat.search(rmmodPart1Result).group(1))
        rmmodRemoveTime = rmmodTotalTime - rmmodQuery2Time
        rmmodQuery2Time = rmmodQuery2Time - rmmodQuery1Time
        rmmodQuery1Time = rmmodQuery1Time - connectTime

        resultInfo = """
        Total rmmod time %5.1f seconds
            Connect time %5.1f seconds
 Connect to 1st qry time %5.1f seconds
 1st qry to 2nd qry time %5.1f seconds
              rmmod time %5.1f seconds
""" %(rmmodTotalTime, connectTime, rmmodQuery1Time, \
      rmmodQuery2Time, rmmodRemoveTime)
        
        testLog.info(resultInfo)
        resultSummaryBuf.write("%s\n" %resultInfo)
        
    else:
        rmmodResultBuf.write("Remove Mod command %s did not succeed.\n" \
                             %rmmodCmd)
        rmmodResultBuf.write("Output follows:\n %s" \
                             %string.join([rmmodPart1Result,
                                           rmmodPart2Result,
                                           rmmodFinalResult], "\n"))
        testLog.error(rmmodResultBuf.getvalue())
        resultSummaryBuf.write(rmmodResultBuf.getvalue())


testElapsedTime = testTimer.stop()
resultSummaryBuf.write("%s concluded at %s.\n" \
                       %(testId, time.strftime('%H:%M.%S %B %d, %Y',
                                               time.localtime())))
resultSummaryBuf.write("Elapsed time was %02d:%02d.%02d\n" \
                       %extractElapsedTime(testElapsedTime))

# Send out an email noting the results of the test.
finishSubj = "workflow test results for %s" %branchId
sendEmailNotification(subject=finishSubj,
                      msgBuf=resultSummaryBuf)


sys.exit()
    
