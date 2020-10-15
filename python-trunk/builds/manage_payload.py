#!/usr/bin/env python
#
# Subversion properties
#
# $LastChangedDate: 2006-06-20 23:14:27 -0700 (Tue, 20 Jun 2006) $
# $Author: misha $
# $Revision: 53 $
# $HeadURL: http://capps.moltenmagma.com/svn/sfsrc/trunk/builds/manage_payload.py $
# $Id: manage_payload.py 53 2006-06-21 06:14:27Z misha $
#
import os, sys, time, string
import sfdc_objects
import sftp_objects
from sftp_objects import *
from sfConstant import *
from os.path import getsize

if (sys.platform == 'win32'):     # Windows testing only
    UPLOAD_PATH="C:\\temp\\"
    UPLOAD_TEMP="C:\\temp\\"
    sep = "\\"
else:
    UPLOAD_PATH="/apps/upload/"
    UPLOAD_TEMP="/apps/upload/tmp/"
    sep = "/"

# import Magma SFDC API and login to SFDC
try:
    from sfMagma import *
except:
    print '--- ERROR:Couldnt import sfMagma'
    sys.exit()

def printBuildObject(one_build_object):
    # will print all fields::values of passed one_build_object
    n = 0
#    print one_build_object
    for bo in sfdc_objects.build_objects:
        print sfdc_objects.build_objects[n], one_build_object.get(sfdc_objects.build_objects[n])
        n = n + 1

def checkBuildPath(build_path):
    # will check if build_path exists and if it is a directory
#    print sys.platform
    if (sys.platform == 'win32'): os.chdir("C:")     # Windows testing only
    path_exists = os.path.exists(build_path)
    if (path_exists): path_exists = os.path.isdir(build_path)
    return path_exists

def getBuildObjects():
    # fetch from SFDC all build objects using prepared SOQL statement
    self=Test()
    try:
        ret=self.query('GetBuilds', soql=sfdc_objects.get_build_objects_soql)
    except:
        print '--- ERROR: SFDC API error executing SOQL query %s' % sfdc_objects.get_build_objects_soql
#    print "VALUE OF Query: %s" %ret
    build_names = []
    for bo in ret: build_names.append(bo.get('Name'))
    print "Total of %s build records that match criteria found." % len(ret)
    print "Build Names that will be processed: ", build_names
    self = None
    return ret

def updateBuildObject_Error(build_object, error_message):
    # update SFDC build object: change status and add error message
    if (sys.platform == 'win32'): return 0 # Windows testing only
    self=Test()
    buildObjId = build_object.get('Id')
    build_name = build_object.get('Name')
    build_id = build_object.get('Build_ID__c')
#    print buildObjId, error_message
    upData=[{'Id':buildObjId, \
            'MD5_Digest__c':'-', \
            'SHA1_Digest__c':'-', \
            'Payload_Size__c':'-', \
#            'File_Uploaded_to_Intraware__c':'Error', \
            'Magma_Intraware_Upload__c':'Error', \
            'Magma_Intraware_Upload_Error_Details__c':error_message}]
    try:
        buildUpdate=self.update('Build__c', upData)
    except:
      print "--- ERROR: SFDC API error: %s." % build_name
      return 1

    if buildUpdate in BAD_INFO_LIST:
      print '--- ERROR: SFDC not updated (_Upload=Error) for build name: %s. Object ID: %s, Build ID: %s. Error: %s' % (build_name, buildObjId, build_id, buildUpdate)
      return 1

    print 'Updated SFDC fields (_Upload=Error) with "Build path does NOT exist" message for: %s' % build_name
    return 0

def updateBuildObject_Done(build_object, error_message):
    # update SFDC build object: change status to 'Done', reset error message to empty
    self=Test()
    buildObjId = build_object.get('Id')
    build_name = build_object.get('Name')
    build_id = build_object.get('Build_ID__c')
#    print buildObjId, error_message

    upData=[{'Id':buildObjId, \
#            'MD5_Digest__c':'-', \
#            'SHA1_Digest__c':'-', \
#            'Payload_Size__c':'-', \
            'File_Uploaded_to_Intraware__c':'Ready for Intraware File Association', \
            'Magma_Intraware_Upload__c':'Done', \
            'Magma_Intraware_Upload_Error_Details__c':error_message}]
    try:
        buildUpdate=self.update('Build__c', upData)
    except:
      print "--- ERROR: SFDC API error: %s." % build_name
      return 1

    if buildUpdate in BAD_INFO_LIST:
      print '--- ERROR: SFDC not updated (_Upload=Done) for build name: %s. Object ID: %s, Build ID: %s. Error: %s' % (build_name, buildObjId, build_id, buildUpdate)
      return 1

    print 'Updated SFDC fields (_Upload=Done) with "Build path does NOT exist" message for: %s' % build_name
    return 0

def tarBuild(build_path):
    # tar.gz all files form build_path and place it temporary directory
    import tarfile
    dest = build_path
    print 'Starting tar.gz process for directory: %s' % build_path
#    print build_path
    if (sys.platform == 'win32'):
        os.chdir("C:\\")                     # Windows testing only
        build_path = "C:\\" + build_path     # Windows testing only

    os.chdir(UPLOAD_TEMP)
    tar_file = os.path.basename(build_path) + ".tar.gz"
    try:
        tar = tarfile.open(tar_file, "w:gz")
    except:
        print '--- ERROR: Could NOT open tar.gz file %s in %s' % (tar_file, UPLOAD_TEMP)
        return 1

    print 'Opened TAR.GZ file: %s in %s' % (tar_file, UPLOAD_TEMP)
    if (sys.platform == 'win32'): os.chdir("C:\\")     # Windows testing only
    try:
        tar.add(build_path)
        tar.close()
    except:
        print '--- ERROR: Could NOT add directory %s to tar.gz file %s' % (build_path, tar_file)
        tar.close()
        return 1

    print 'Created tar.gz file %s in %s' % (tar_file, UPLOAD_TEMP)
    # move the file from temporary location to upload directory --> file becomes "payload"
    src_file = UPLOAD_TEMP + tar_file
    dest_file = UPLOAD_PATH + dest + sep + tar_file
    try:
        os.rename(src_file, dest_file)
    except:
        print '--- ERROR: Could NOT create payload file %s by renaming %s' % (dest_file, src_file)
        return 1

    print 'Payload file %s created by renaming %s' % (dest_file, src_file)
    return 0

def updatePayloadAttributes(build_object):
#    - calculate: file size, MD5, SHA1, update corresponding SFDC fields
#    - (optional) sign the file using Magma certicicate, create signature file <file>.asc
#    - change status in SFDC to "In Process"
    import md5, sha, string

    self=Test()
    buildObjId = build_object.get('Id')
    build_id = build_object.get('Build_ID__c')
    build_name = build_object.get('Name')

    if (sys.platform == 'win32'):
        sep = "\\"     # Windows testing only
    else:
        sep = "/"
    build_path = os.path.normpath(build_object.get('Build_Path__c'))        # Adjust OS dependent to support Win32
    build_path_intraware = build_path + sep + os.path.basename(build_path) + ".tar.gz"
    # remove leading "/" from build_path_intraware
    build_path_intraware = string.lstrip(build_path_intraware, '/')
    build_path = UPLOAD_PATH + build_path + sep + os.path.basename(build_path) + ".tar.gz"

    myhandle = open(build_path, "r")
    data = myhandle.read()
    md5_dig = md5.new()
    sha1_dig = sha.new()
    md5_dig.update(data)
    sha1_dig.update(data)
    md5_sig = md5_dig.hexdigest()
    sha1_sig = sha1_dig.hexdigest()
    payload_size = str(getsize(build_path))
    error_message = "Payload file ready for upload on %s" % time.ctime()

    upData=[{'Id':buildObjId, \
            'MD5_Digest__c':md5_sig, \
            'SHA1_Digest__c':sha1_sig, \
            'Payload_Size__c':payload_size, \
#            'File_Uploaded_to_Intraware__c':'Error', \
            'Intraware_Build_Path__c':build_path_intraware, \
            'Magma_Intraware_Upload__c':'In Process', \
            'Magma_Intraware_Upload_Error_Details__c':error_message}]
    # submit to SFDC, catch API error
    try:
        buildUpdate=self.update('Build__c', upData)
    except:
        print '--- ERROR: SFDC API error for build name: %s. Object ID: %s, Build ID: %s. Error: %s' % (build_name, buildObjId, build_id, buildUpdate)
        return 1
    # test for success of update
    if buildUpdate in BAD_INFO_LIST:
      print "--- ERROR: SFDC not updated (MD5, SHA1 ...) for build name: %s. Object ID: %s, Build ID: %s. Error: %s" % (build_name, buildObjId, build_id, buildUpdate)
      return 1

    print "Updated build: %s with MD5=%s, SHA1=%s, File size=%s, Intraware_Build_Path=%s" % (build_name, md5_sig, sha1_sig, payload_size, build_path_intraware)
    print "Build name: %s marked as 'In process'. Object ID: %s, Build ID: %s" % (build_name, buildObjId, build_id)
    return 0

def _makedirs(name, mode=0755):
    import os, os.path

    starting_name = name
    head, tail = os.path.split(name)
    if not tail:
        head, tail = os.path.split(head)
    if ((head and tail) and not os.path.exists(head)):
        _makedirs(head, mode)
#    print name
    if (not os.path.exists(name)):
        print "Making directory: %s (from request: %s)" % (name, starting_name)
        os.mkdir(name, mode)

def checkPayloadInSFTP(file_path):
    # connect to Intraware via SFTP, try to find the file, get file size
    # return file size if exists, otherwise return 0 (zero)
    transport = sftp_connect_transport()
    sftp = sftp_connect_client(transport)
    try:
        file_attr = sftp.stat(file_path)
        payload_size_intraware = file_attr.st_size
    except Exception, e:
        print '*** Caught exception: %s: %s' % (e.__class__, e)
        traceback.print_exc()
        sftp_close(sftp, transport)
        return -1
    #payload_size_intraware = 0
    return payload_size_intraware


def getREADME(build_path):
    # extract README file and put it in directory structure
#    src_file = UPLOAD_TEMP + tar_file
    dest_file = UPLOAD_PATH + dest + sep + readme_file
    try:
        os.rename(src_file, dest_file)
        print "Payload file %s created by renaming %s" % (dest_file, src_file)
    except:
        print "--- ERROR: Could NOT create payload file %s by renaming %s" % (dest_file, src_file)
        return 1

    return 0



############################################################################################
class Test(SFMagmaTool):
    logname = 'Test'

def main():
    print "====================> Started processing at: ", time.ctime()
#   self=Test()
    BuildObjects = getBuildObjects()
    for bo in BuildObjects:
#      print bo
#      printBuildObject(bo)
      upload_status = bo.get('Magma_Intraware_Upload__c')
      build_path = os.path.normpath(bo.get('Build_Path__c'))
      build_name = bo.get('Name')
      ps = bo.get('Payload_Size__c')
#      print build_name, ps
      if ((ps == None) or (ps == '-')): payload_size_sfdc = 0
      else: payload_size_sfdc = int(float(str(ps)))
#      print payload_size_sfdc
#      payload_size_sfdc1 = float(payload_size_sfdc)
#      sys.exit()
      payload = UPLOAD_PATH + build_path + sep + os.path.basename(build_path) + ".tar.gz"
      try:
        zz, file_to_check = string.split(payload, '//')
      except:
        file_to_check = ''
      if (upload_status == 'In Process'):
          # SFDC status is 'In Process'. Check where is the payload
          # test if payload exists in UPLOAD directory
          print 'Upload status for payload: %s is "In Process"' % payload
          if (os.access(payload, os.F_OK)):
              # Payload exists, compare OS size with SFDC size, make sure it is the same
              payload_size_os = getsize(payload)
              print 'Payload: %s exists' % payload
              if (cmp(payload_size_os, payload_size_sfdc) == 0):
                  # Payload is still in the UPLOAD queue to be uploaded to Intraware; skip
                  print "Payload %s waiting to be uploaded to Intraware. Skipping." % payload
                  continue
              else:
                  print "Payload %s size in SFDC (%s) and OS (%s) don't match; payload corrupted. Changing SFDC status to 'Error'"  % (payload, payload_size_sfdc, payload_size_os)
                  # update SFDC status to 'Error'
                  error_message = "Error: payload size in SFDC and Intraware don't match (" + time.ctime() + "): Build Path " + build_path
                  updateBuildObject_Error(bo, error_message)
          else:
              print"Payload %s doesn't exist. Checking if (%s) is uploaded to Intraware" % (payload, file_to_check)
              # check if payload is in Intraware
              payload_size_intraware = checkPayloadInSFTP(file_to_check)
#              payload_size_intraware = sftp_check_file(file_to_check)
#              if (payload_size_intraware > 0):
              if (payload_size_intraware == payload_size_sfdc):
                  print "Payload %s uploaded sucessfully. Update SFDC status" % payload
                  # update SFDC status to 'Done'
                  error_message = "Done: payload in Intraware (" + time.ctime() + "): Build Path " + build_path
                  updateBuildObject_Done(bo, error_message)
              else:
                  print "Payload %s not uploaded to Intraware. Updating SFDC status to 'Error'" % payload
                  print "Intraware size: %s; SFDC size: %s" % (payload_size_intraware, payload_size_sfdc)
                  # update SFDC status to 'Error'
                  error_message = "Error: payload not in Intraware (" + time.ctime() + "): Build Path " + build_path
#                  updateBuildObject_Error(bo, error_message)
      else:
         # upload_status is either "" (empty) or "error"; create payload
         print 'Upload status from payload: %s is empty or error; Creating payload' % payload
         if (sys.platform == 'win32'): os.chdir("C:\\")     # Windows testing only
         # check if build_path exists
         path_ok = checkBuildPath(build_path)
#         print "OS Path %s exist (True or False): " % path_ok
         if (path_ok):
             # path exists, build payload
             print "Build directory OK: %s" % build_path
             # create build_path in UPLOAD_PATH to mimic product build site
             _makedirs(UPLOAD_PATH + build_path)
             # create TAR.GZ payload file from build_path collection, move it to UPLOAD_PATH
             er = tarBuild(build_path)
             # if something went wrong do it again next time
             if (er > 0): continue
             # payload created, update build attributes (file size, md5, sha1) in SFDC
             else: updatePayloadAttributes(bo)
         else:
             # Build path doesn't exist on OS level bail out
             print "Build Path %s does NOT exist on OS level" % build_path
             error_message = "Error (" + time.ctime() + "): Build Path " + build_path + " doesn't exist"
             updateBuildObject_Error(bo, error_message)

    # continue loop with next build object
    # loop finished
    print "====================> End processing at: ", time.ctime()
# end of main

if __name__ == "__main__":
    main()

