"""
Simple function that can convert a 15 character salesforce ID string
to the case-safe 18-character version
"""

import string
import types
import sys
import os
if (sys.platform != 'win32'): import fcntl, pty
import time
import re
import tempfile
import cStringIO
from RuntimeContext import *

TRANSLATION_TABLE = string.ascii_uppercase + string.digits[:6]

_cronLocks = []

def salesForceURL(force=False):
    """
    Returns the SalesForce URL for the environment of execution.
    """
    ctx = RuntimeContext()
    if (ctx.isProduction) or (force):
        return 'https://na1.salesforce.com'
    return 'https://cs1.salesforce.com'

def getTestMailAddr():
    """
    Returns the test email address for all instances of use.
    """
    return 'rhorn@molten-magma.com'

def osLogPath():
    """
    Returns the log file path for the environment of execution.
    """
    if (sys.platform == 'win32'):
        logPath = 'log'
    else:
        logPath = searchForFolderNamed('log',homeFolder())
    return logPath

def convertId15ToId18(id15):
    
    chunkSize = 5
    caseSafeExt = ''
        
    if id15 not in [None,'']:          
        if len(id15) != 15:
            if len(id15) == 18:
                return id15
            id15 = id15[:15]
            
        idStr = id15
        while len(idStr) > 0:
            chunk = idStr[:chunkSize]
            idStr = idStr[chunkSize:]
            caseSafeExt += convertChunk(chunk)
        print "id..... %s" %id15
        return "%s%s" %(id15, caseSafeExt)
## END convertId15ToId18


def convertChunk(chunk):
    """
    Used by convertId15ToId18
    """
    global BINARY, DECIMAL
    global TRANSLATION_TABLE
    chunkBinList = []

    # for each character in chunk, give that position a 1 if uppercase,
    # 0 otherwise (lowercase or number)
    for character in chunk:
        if character in string.ascii_uppercase:
            chunkBinList.append('1')
        else:
            chunkBinList.append('0')

    chunkBinList.reverse() # flip it around so rightmost bit is most significant
    chunkBin = "".join(chunkBinList) # compress list into a string of the binary num
    chunkCharIdx = baseconvert(chunkBin, BINARY, DECIMAL) # convert binary to decimal
    return TRANSLATION_TABLE[int(chunkCharIdx)] # look it up in our table
## END convertChunk


########################################################################
# base converter utility function - may go to live with other utility
# classes someday...
########################################################################

BASE2  = string.digits[:2]
BINARY = BASE2

BASE8  = string.octdigits
OCTAL = BASE8

BASE10 = string.digits
DECIMAL = BASE10

BASE16 = string.digits + string.ascii_uppercase[:6]
HEX = BASE16

def baseconvert(number,fromdigits,todigits):
    if str(number)[0]=='-':
        number = str(number)[1:]
        neg = True
    else:
        neg = False

    # make an integer out of the number
    x=long(0)
    for digit in str(number):
        x = x*len(fromdigits) + fromdigits.index(digit)
    
    # create the result in base 'len(todigits)'
    res=''
    while x>0:
        digit = x % len(todigits)
        res = todigits[digit] + res
        x /= len(todigits)
    if len(res) == 0:
        res = 0
    if neg:
        res = "-%s" %res

    return res

"""
General utility functions 
"""

def inputTextFromCmdline(premsg=None):
    """
    Prompt for multi-line input from the user and return entered test as
    a string.

    Parameters:
    premsg - Text to print to the tty before prompting for input
    """
    txt = ''
    if premsg is not None:
        print premsg
        
    print "End with a ^D (UNIX) or a ^Z (Windows) on a blank line:"

    emptyLine = 0
    while True:
        try:
            line = raw_input()
        except EOFError:
            break

        if not line:
            if emptyLine > 1:
                break
            emptyLine += 1
        else:
            emptyLine = 0

        txt += "%s\n" %line
        
    if len(txt) == 0:
        query = raw_input("You didn't enter anything. Do you wish to try again? <[y]/n>:")

        if query in ['y','Y','']:
            txt = inputTextFromCmdline(premsg)
        else:
            txt = None

    print "\nThank you."
    return txt
## END inputTextFromCmdline(premsg)

def inputLineFromCmdline(premsg=None, required=False):
    """
    Prompt for single-line input from the user and return entered test as
    a string.

    Parameters:
    premsg - Text to print to the tty before prompting for input
    """
    premsg = "%s>" %premsg
        
    line = raw_input(premsg)

    line.strip()

    if len(line) == 0 and required is True:
        print "You must supply a response before you may continue!\n"
        line = inputLineFromCmdline(premsg)

    if len(line) == 0:
        line = None

    return line
## END inputLineFromCmdline(premsg, required)


def inputTextFromEditor(premsg=None, defaultEd=None):
    """
    Uses $EDITOR env var to collect text.

    if $EDITOR is not set, use the default editor. If no default editor is
    provided, use the command line collection method.
    """
    widget = '#>>:'
    widgetlen = len(widget)

    txt = None
    
    EDITOR=os.environ.get('EDITOR', defaultEd)
    if EDITOR is not None:
        # create a known-location text file

        inputHdr = '\n'
        inputHdr +=  widget + ' ' + '-'*70 + '\n'
        if premsg is not None:
            inputHdr +=  "%s %s\n" %(widget, premsg)
            inputHdr +=  "%s\n" %widget
        inputHdr += "%s Enter your text. Lines beginning with `%s' are removed automatically\n" %(widget, widget)
        inputHdr += widget + ' ' + '-'*70

        try:
            fd, fpath = tempfile.mkstemp()
            os.write(fd, inputHdr)
            os.close(fd)

            # open $EDITOR on the file
            edCmd = "%s %s" %(EDITOR, fpath)
            retval = os.system(edCmd)
            if retval != 0:
                raise Exception 
            
            # suck in the contents of the file
            fh = file(fpath)

            buf = cStringIO.StringIO()
            for line in fh.readlines():
                # trim off inputHeader
                if line[:widgetlen] == widget:
                    continue
                buf.write(line)
                continue
            txt = buf.getvalue().rstrip()

            if len(txt) == 0:
                query = raw_input("You didn't enter anything.\nPerhaps you needed to save before exiting your editor.\nDo you wish to try again? <[y]/n>:")
                
                if query in ['y','Y','']:
                    txt = inputTextFromEditor(premsg)

            # cleanup the temp file
            fh.close()
            os.unlink(fpath)

        except Exception, e:
            premsg = "An error occured while trying to gather text using `%s'\nBacking off to command line collection\n\n%s" %(EDITOR, premsg)
            txt = inputTextFromCmdline(premsg=premsg)

    else:
        txt = inputTextFromCmdline(premsg=premsg)

    return txt

def getCronLockPath(fname='sfwalkerDefault.lock'):
    if (sys.platform == 'win32'):
        homeDir = os.getenv('TEMP', 'c:/temp')
        if (os.path.exists(homeDir) == False):
            os.mkdir(homeDir)
        homeDir = os.sep.join([homeDir,'.locks'])
        if (os.path.exists(homeDir) == False):
            os.mkdir(homeDir)
    else:
        homeDir = os.getenv('HOME', '/tmp')
    fn = '.%s'%fname
    return os.path.join(homeDir, fn)

def cleanCronLocks(fname='sfwalkerDefault.lock'):
    """ Cleans-up all the pre-existing cronLocks, if they exist.
    This is a win32 platform issue that does not exist for other non-win32 platforms that support fcntl.
    """
    # put the lock in the user's home dir,
    # or in /tmp if env HOME is not set
    lockPath = getCronLockPath(fname)
    toks = lockPath.split(os.sep)
    parent = os.sep.join(toks[0:-1])
    for f in os.listdir(parent):
        try:
            os.rmdir(os.sep.join([parent,f]))
        except IOError:
            pass

def cronLock(fname='sfwalkerDefault.lock'):
    """
    A simple fcntl locking scheme to ensure that sfBranchWalkSF jobs
    run via cron do not overlap.

    We assume that if stdout has no tty attached, then the job is a cron
    job (the most likely explanation by far)

    We let the caller handle exceptions. If one is thrown, assume that locking
    failed and caller should act accordingly.

    Lock is released automatically (and lock file closed) when this script
    exits.
    """
    # put the lock in the user's home dir,
    # or in /tmp if env HOME is not set
    lockPath = getCronLockPath(fname)

    if (sys.platform == 'win32'):
        _cronLocks.append(lockPath)
        os.mkdir(lockPath)
    else:
        if sys.stdout.isatty() is False:
            f = file(lockPath, 'w')
            # request an exclusive, non-blocking lock on the file
            fcntl.flock(f, fcntl.LOCK_EX|fcntl.LOCK_NB)
            return f
        else:
            f = file(lockPath, 'w')
            # request an exclusive, non-blocking lock on the file
            fcntl.flock(f, fcntl.LOCK_EX|fcntl.LOCK_NB)
            return f
        
    return None
## END cronLock()

def splitFilenameExtension(filename):
    fnPat = '^(.+)\.([^\.]+)$'
    fnRE = re.compile(fnPat)
    m = fnRE.search(filename)

    filebase = None
    fileext = None

    if m is not None:
        filebase = m.group(1)
        fileext = m.group(2)

    return filebase, fileext
# end splitFilenameExtension()

def genBackupTimestampFilename(filebase, fileext):
    """
    Given a filename of the pattern base.ext, generate a backup filename
    base-YYYYmmdd-HHMMSS.ext
    """
    tstamp = time.strftime('%Y%m%d-%H%M%S')
    tsfile = "%s-%s.%s" %(filebase, tstamp, fileext)
    return tsfile
## END genBackupTimestampFilename()
    
def enforceRollingRetentionPolicy(bkfDir, bkfBase, bkfExt, retainNum):
    """
    bkfDir - directory in which backups reside
    bkfBase - the base name of the backup file (i.e., left of the dot)
    bkfExt - the backup file extension (i.e., right of the dot)
    retainNum - the number of backups to retain
    
    Look into the the backup directory and prune backup archives that
    we no longer wish to keep.

    Files must be in the format of bkfDir/bkfBase-YYYYmmdd-HHMMSS.bkfExt
    """
    import glob

    bkfGlob = "%s*.%s" %(bkfBase, bkfExt)

    tsPat = "%s-(\d{8}-\d{4})\.%s" %(bkfBase, bkfExt)
    tsRE = re.compile(tsPat)

    files = glob.glob(os.path.join(bkfDir, bkfGlob))
    files.sort() # We can cheat because the timestamps are string-sortable

    # Delete all but the six most recent
    delFiles = files[:-retainNum]
    if len(delFiles) > retainNum:
        msg = "Saving only the %d most recent backups; removing older backups:" %retainNum
        print msg

    for bkfile in delFiles:
        msg = "Removing " + bkfile
        print msg
        os.remove(bkfile)

## END enforceRetentionPolicy(self)


def uniq(alist):    # Fastest order preserving
    set = {}
    return [set.setdefault(e,e) for e in alist if e not in set]
# END uniq

def numToTxt(num):
    """ Integer < 10 to textual representation """
    
    lookup = {0: 'zero',
              1: 'one',
              2: 'two',
              3: 'three',
              4: 'four',
              5: 'five',
              6: 'six',
              7: 'seven',
              8: 'eight',
              9: 'nine',
              10: 'ten'}
    
    dayTxt = lookup.get(num, str(num))
    return dayTxt
## END numToTxt
    
def homeFolder():
    """ home folder for current user """
    import os
    f = os.path.abspath(os.curdir)
    toks = f.split(os.sep)
    if (sys.platform == 'win32'):
        t = toks[0:2]
    else:
        t = toks[0:3]
    return os.sep.join(t)

def _searchForFileOrFolderNamed(fname,top='/',isFile=False):
    """ Search for a folder of a specific name """
    import os
    _found = False
    for root, dirs, files in os.walk(top, topdown=True):
        if (not isFile):
            if (fname in dirs):
                _found = True
                break
        else:
            if (fname in files):
                _found = True
                break
    if (_found):
        return os.sep.join([root,fname])
            
    return ''

def searchForFolderNamed(fname,top='/'):
    """ Search for a folder of a specific name """
    return _searchForFileOrFolderNamed(fname,top,False)

def searchForFileNamed(fname,top='/'):
    """ Search for a folder of a specific name """
    return _searchForFileOrFolderNamed(fname,top,True)

def getAsDateTimeStr(value, offset=0):
    """ return time as 2004-01-10T00:13:50.000Z """
    import time
    from types import StringType, UnicodeType, TupleType, LongType, FloatType
    strTypes = [StringType, UnicodeType]
    numTypes = (LongType, FloatType)
    if isinstance(value, (TupleType, time.struct_time)):
        return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', value)
    if isinstance(value, numTypes):
        secs = time.gmtime(value+offset)
        return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', secs)
        
    if isinstance(value, strTypes):
        try: 
            value = time.strptime(value, '%Y-%m-%dT%H:%M:%S.000Z')
            return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', value)
        except: 
            print 'ERROR:getDateTimeTuple Could not parse %s'%value
            secs = time.gmtime(time.time()+offset)
            return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', secs)
# END getAsDateTimeStr

def timeStamp():
    """ get standard timestamp """
    import time, datetime
    fromSecs = time.time()
    fromSecs = datetime.datetime.fromtimestamp(fromSecs)
    currentDay = time.mktime(fromSecs.timetuple())
    return getAsDateTimeStr(currentDay)

def callersName():
    """ get name of caller for a function """
    import sys
    return sys._getframe(2).f_code.co_name

def functionName():
    """ get name of a function """
    import sys
    return sys._getframe(1).f_code.co_name

def logPrint(s):
    """ log a line to a file """
    import os, sys
    if (sys.platform in ['linux2','win32']):
        try:
            logPath = osLogPath()
            tstamp = timeStamp()
            folder = ''.join(tstamp.split('T')[0]).replace(':','-').replace('.','_')
            if (os.path.exists(logPath) == False):
                os.mkdir(logPath)
            logPath = os.sep.join([logPath,'details'])
            if (os.path.exists(logPath) == False):
                os.mkdir(logPath)
            logPath = os.sep.join([logPath,folder])
            if (os.path.exists(logPath) == False):
                os.mkdir(logPath)
            logFile = '%s.log' % (os.sep.join([logPath,sys.argv[0].split(os.sep)[-1]]).replace('.','_'))
            fOut = open(logFile,'a')
            fOut.write('%s::%s -- %s\n' % (tstamp,callersName(),s))
            fOut.flush()
            fOut.close()
        except:
            pass
# END logPrint

def getLastProcessDate(*args,**kw): 
    import datetime
    update = True
    isTime = False
    _isTime = False # this is the return value whenever isTime is True
    filename = 'LastCheckedCRNotificationDate'   
    diff_hours = 0
    diff_minutes = 0
    if (len(kw) == 0):
        kw = args[-1]
    try:
        if (kw.has_key('update')):
            update = kw['update']
        if (kw.has_key('isTime')):
            isTime = kw['isTime']
        if (kw.has_key('filename')):
            filename = kw['filename']
        if (kw.has_key('diff_hours')):
            try:
                diff_hours = int(kw['diff_hours'])
            except:
                pass
        if (kw.has_key('diff_minutes')):
            try:
                diff_minutes = int(kw['diff_minutes'])
            except:
                pass
    except:
        pass
    if (sys.platform == 'win32'): 
        tmp_root = os.sep.join([os.environ['TMP'],'processDates']) 
        if (os.path.exists(tmp_root) == False): 
            os.mkdir(tmp_root) 
    else: 
        tmp_root = '/home/sfscript/tmp/processDates' 
    checksince = None 
                   
    curDirPath = os.getcwd() 
    tmpDirPath = tmp_root 
    os.chdir(tmpDirPath)        
     
    tmpPath = os.path.join(tmp_root,filename) 
    if os.path.isfile(tmpPath): 
        curFile=open(tmpPath, "rb", 0) 
        lines = [l for l in curFile.readlines() if len(l.strip()) > 0] 
        checksince = None 
        if (sys.platform != 'win32'): 
            if (len(lines) > 0): 
                checksince = lines[-1] 
        curFile.close() 
        os.remove(tmpPath)             

    if (update) or (isTime):
        try: 
            newfilename=os.path.join(tmp_root,filename) 
            file = open(newfilename, 'a') 
            if (not isTime):
                file.write(timeStamp()) 
                file.close() 
        except IOError: 
            msg= "There was an error writing to %s" %filename 
            self.setLog(msg, 'warn') 
            pass 
    
    if (isTime):
        now = datetime.date.today()            
     
    if checksince in [None,'',""]: 
        if (isTime):
            lastTime=time.mktime(time.strptime(checksince,"%Y-%m-%d"))                
            epc = datetime.date.fromtimestamp(lastTime)                
            parseEpc = epc.strftime("%Y-%m-%d")                
            dif = (epc - now)                
            if dif.days < 0:                    
                _isTime = True             
                dateStr = now.strftime("%Y-%m-%d")                                
                file.write(dateStr)            
                file.close()
            else:
                file.write(checksince)  
                file.close()                    
        else:
            fromSecs = time.time() 
            fromSecs = datetime.datetime.fromtimestamp(fromSecs) 
            if (diff_hours != 0):
                if (sys.platform == 'win32'): 
                    diff = datetime.timedelta(hours=-48) # debugging code - never used in production
                else:
                    diff = datetime.timedelta(hours=diff_hours) 
            if (diff_minutes != 0):
                if (sys.platform == 'win32'): 
                    diff = datetime.timedelta(hours=-48) # debugging code - never used in production
                else:
                    diff = datetime.timedelta(hours=diff_minutes) 
            previousHour=fromSecs + diff             
            previousHour=time.mktime(previousHour.timetuple())                     
            preHourStr = self.getAsDateTimeStr(previousHour)             
            checksince=preHourStr 
        if (isTime):
            dateStr = now.strftime("%Y-%m-%d")                            
            file.write(dateStr)
            file.close() 

    os.chdir(curDirPath) 

    if (isTime):
        return _isTime
    return checksince
    
def getLastProcessDate2(*args,**kw): 
    import datetime
    update = True
    isTime = False
    _isTime = False # this is the return value whenever isTime is True
    filename = 'LastCheckedCRNotificationDate'   
    diff_hours = 0
    diff_minutes = 0
    if (len(kw) == 0):
        kw = args[-1]
    try:
        if (kw.has_key('update')):
            update = kw['update']
        if (kw.has_key('isTime')):
            isTime = kw['isTime']
        if (kw.has_key('filename')):
            filename = kw['filename']
        if (kw.has_key('diff_hours')):
            try:
                diff_hours = int(kw['diff_hours'])
            except:
                pass
        if (kw.has_key('diff_minutes')):
            try:
                diff_minutes = int(kw['diff_minutes'])
            except:
                pass
    except:
        pass

    checksince = None 
                   
    tmp_root = os.path.abspath('.')
    tmpPath = os.path.join(tmp_root,filename) 
    if os.path.isfile(tmpPath): 
        curFile=open(tmpPath, "rb", 0) 
        lines = [l for l in curFile.readlines() if len(l.strip()) > 0] 
        checksince = None 
        if (sys.platform != 'win32'): 
            if (len(lines) > 0): 
                checksince = lines[-1] 
        curFile.close() 
        os.remove(tmpPath)             

    if (update) or (isTime):
        try: 
            newfilename=os.path.join(tmp_root,filename) 
            file = open(newfilename, 'a') 
            if (not isTime):
                file.write(timeStamp()) 
                file.close() 
        except IOError: 
            msg= "There was an error writing to %s" %filename 
            self.setLog(msg, 'warn') 
            pass 
    
    if (isTime):
        now = datetime.date.today()            
     
    if checksince in [None,'',""]: 
        if (isTime):
            lastTime=time.mktime(time.strptime(checksince,"%Y-%m-%d"))                
            epc = datetime.date.fromtimestamp(lastTime)                
            parseEpc = epc.strftime("%Y-%m-%d")                
            dif = (epc - now)                
            if dif.days < 0:                    
                _isTime = True             
                dateStr = now.strftime("%Y-%m-%d")                                
                file.write(dateStr)            
                file.close()
            else:
                file.write(checksince)  
                file.close()                    
        else:
            fromSecs = time.time() 
            fromSecs = datetime.datetime.fromtimestamp(fromSecs) 
            if (diff_hours != 0):
                if (sys.platform == 'win32'): 
                    diff = datetime.timedelta(hours=-48) # debugging code - never used in production
                else:
                    diff = datetime.timedelta(hours=diff_hours) 
            if (diff_minutes != 0):
                if (sys.platform == 'win32'): 
                    diff = datetime.timedelta(hours=-48) # debugging code - never used in production
                else:
                    diff = datetime.timedelta(hours=diff_minutes) 
            previousHour=fromSecs + diff             
            previousHour=time.mktime(previousHour.timetuple())                     
            preHourStr = getAsDateTimeStr(previousHour)             
            checksince=preHourStr 
        if (isTime):
            dateStr = now.strftime("%Y-%m-%d")                            
            file.write(dateStr)
            file.close() 

    if (isTime):
        return _isTime
    return checksince
    
if __name__ == "__main__":
    print 'My Nifty Instructional Text'
