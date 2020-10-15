import sys, os

if (sys.platform == 'win32'):     # Windows testing only
    UPLOAD_TEMP="C:\\temp\\"
    UPLOAD_PATH="C:\\temp\\"
    sep = "\\"     # Windows testing only
else:
    UPLOAD_TEMP="/upload/tmp/"
    UPLOAD_PATH="/upload/"
    sep = "/"

def checkPayloadExists(build_path):
   payload = UPLOAD_PATH + build_path + sep + os.path.basename(build_path) + ".tar.gz"
   payload_exists = os.access(payload, os.F_OK)
   if (payload_exists):
     # Payload is still in the queue to be uploaded to Intraware; skip
     print "Payload %s waiting to be uploaded to Intraware" % payload
     return 1
   else:
     print"Payload %s doesn't exist. Checking if it is uploaded to Intraware" % payload
     # check if payload is in Intraware
   return

checkPayloadExists('vobs')
def _lock():
    fn = "test.lck"
#    flag = os.O_EXCL
#    flag = ioctl.LOCK_EX
#    fh = os.open(fn, flag, 0777)
    flock(fh.fileno(), LOCK_EX)
    return 0

#_lock()
#input ("type")
#print "pid: %s" % os.getpid()
# find process with pid
