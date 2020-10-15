import os 
from os.path import getsize
import md5, sha

myfile = "C:\\temp\\vobs.tar.gz"
#myfile = "/upload/2006_03_07.0203.tar.gz"
myhandle = open(myfile, "r")
data = myhandle.read()
m = md5.new()
s = sha.new()
m.update(data)
s.update(data)
print "MD5 digest: %s" % m.hexdigest()
print "SHA1 digest: %s" % s.hexdigest()
print "Payload size: %s" % getsize(myfile)
