#!/usr/bin/env python
#
# Subversion properties
#
# $LastChangedDate: 2006-06-20 23:14:27 -0700 (Tue, 20 Jun 2006) $
# $Author: misha $
# $Revision: 53 $
# $HeadURL: http://capps.moltenmagma.com/svn/sfsrc/trunk/builds/upload_payload.py $
# $Id: upload_payload.py 53 2006-06-21 06:14:27Z misha $
#
import time, os, sys, string
from os.path import join, split, getsize, normpath
from sftp_objects import *

def main():
  """
  """
  LOCAL_PATH = "/magma/apps/upload"
#  LOCAL_PATH = "C:\\temp\\vobs"

  nfiles = 0
  local_files = []
  remote_paths = []
  print "List of files to be processed:"
  for root, dirs, files in os.walk(LOCAL_PATH, topdown=False):
#      print root, dirs, files
      for name in files:
          aa, bb = string.split(root, LOCAL_PATH)
          remote_paths.append(bb)
          local_files.append(join(root, name))
          print '%s ---> %s (size: %s bytes)' % (local_files[nfiles], remote_paths[nfiles], getsize(local_files[nfiles]))
          nfiles = nfiles + 1

  print 'Total of %i files ready for upload' % (nfiles)
  if (nfiles < 1): return

  transport = sftp_connect_transport()
  sftp = sftp_connect_client(transport)

  dirlist = sftp_list_directory("/magma", transport, sftp)
  if (dirlist < 0): 
      print 'Remote ROOT Directory "/magma " doesnt exist'
  else:
          print 'List of ROOT Directory on remote server'
          for dir in dirlist:
                  print '\t\tDir: %s' % dir

#  print remote_paths
#  print local_files
#  sftp_close(sftp, transport)
#  sys.exit()
  
  nfiles = 0
  for rp in remote_paths:
    local_file = local_files[nfiles]
    aa, file_name = split(local_file)
    remote_file = normpath(rp + "/" + file_name)
    payload_size_os = getsize(local_file)
    print "=> Start uploading %s at: %s" % (local_file, time.ctime())
    status = sftp_upload_file(local_file, rp, transport, sftp)
#    status = sftp_upload_file(local_file, '/magma/vobs/', transport, sftp)
    payload_size_sftp = sftp_check_file(remote_file, transport, sftp)
#    payload_size_sftp = sftp_check_file('/magma/vobs/vobs.zip', transport, sftp)
    if (payload_size_sftp == payload_size_os): 
        print "Payload file %s (%s) successfully uploaded" % (local_file, remote_file)
        print "Payload size is: %i bytes" % (payload_size_os)
        try:
            os.remove(local_file)
            print "Payload file %s removed" % (local_file)
        except:
            print "Could NOT remove payload file %s" % (local_file)
    else:
        print "Payload file %s (%s) NOT uploaded" % (local_file, remote_file)
        print "Local file size is: %i bytes; remote file size is: %i bytes" % (payload_size_os, payload_size_sftp)
    nfiles = nfiles + 1
    print "=> End uploading %s at: %s" % (local_file, time.ctime())
# end loop
  sftp_close(sftp, transport)

if __name__ == "__main__":
  print "====================> Start processing at: ", time.ctime()
  main()
  print "====================> End processing at: ", time.ctime()
  