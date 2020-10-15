# Subversion properties
#
# $LastChangedDate: 2006-06-05 09:52:45 -0700 (Mon, 05 Jun 2006) $
# $Author: misha $
# $Revision: 41 $
# $HeadURL: http://capps.moltenmagma.com/svn/sfsrc/trunk/builds/sftp_objects.py $
# $Id: sftp_objects.py 41 2006-06-05 16:52:45Z misha $
import os
import sys
import traceback
import paramiko
# setup logging
paramiko.util.log_to_file('sftp_objects.log')

def sftp_connect_transport():
  """
  """
  hostname = 'upload.subscribenet.com'
  port = 22
# Staging:
#  username = 'lavauat'
#  password = 'YDBs3^7C76Ne'
# Production:
  username = 'lava'
  password = 'uLz$u25J1%'
# get host key, if we know one
  hostkeytype = None
  hostkey = None
  try:
    host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
  except IOError:
    try:
        host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
    except IOError:
        print '*** Unable to open host keys file'
        host_keys = {}
#  print host_keys
#  if host_keys.has_key(hostname):
  if host_keys.lookup(hostname):
    hostkeytype = host_keys[hostname].keys()[0]
    hostkey = host_keys[hostname][hostkeytype]
    print 'Using host key of type %s' % hostkeytype
  else:
    print "Host key not found. Please create key manually using: ssh %s" % hostname
# now, connect and use paramiko Transport to negotiate SSH2 across the connection
  try:
    t = paramiko.Transport((hostname, port))
    t.connect(username=username, password=password, hostkey=hostkey)
  except Exception, e:
    print '*** Caught exception: %s: %s' % (e.__class__, e)
    traceback.print_exc()
    try:
        t.close()
    except:
        pass
    sys.exit(1)

  return t


def sftp_connect_client(transport=None):
  """ connect and use paramiko Transport to negotiate SSH2 across the connection
  """
  if ((transport == None) or (transport == '')): transport = sftp_connect_transport()
  try:
    sftp = paramiko.SFTPClient.from_transport(transport)
  except Exception, e:
    print '*** Caught exception: %s: %s' % (e.__class__, e)
    traceback.print_exc()
    try:
        sftp_close(sftp, transport)
    except:
        pass
    sys.exit(1)

  return sftp

def sftp_close(sftp, transport):
  """
  """
  sftp.close()
  transport.close()
  return

def sftp_list_directory(dir_path, transport=None, sftp=None):
  """
  """
  if ((sftp == None) or (transport == None)): sftp = sftp_connect_client(transport)
  if ((dir_path == None) or (dir_path == '')): dir_path = '.'
  try:
     dirlist = sftp.listdir(dir_path)
#        print "Dirlist:", dirlist
  except:
     sftp_close(sftp, transport)
     return -1
  return dirlist

def sftp_check_file(file_path, transport=None, sftp=None):
  """
  """
  if ((sftp == None) or (transport == None)): sftp = sftp_connect_client(transport)
  try:
     file_attr = sftp.stat(sftp.normalize(file_path))
#     file_size = file_attr.st_size
#     md_5 = sftp.check(file_path, 'md5')        # Not supported
#     sha_1 = sftp.check(file_path, 'sha1')        # Not supported
#     print 'Size: %s, Last Access: %s, Modified: %s' % (file_size, file_attr.st_atime, file_attr.st_mtime)
#     print file_attr
  except Exception, e:
      sftp_close(sftp, transport)
      print '*** Remote SFTP server exception: %s: %s (%s)' % (e.__class__, e, file_path)
#      traceback.print_exc()
      return -1
#    return (file_size, md_5, sha_1)
  file_size = file_attr.st_size
  return (file_size)

def sftp_makedirs(name, transport=None, sftp=None, mode=0711):
  import os, os.path

  if ((sftp == None) or (transport == None)):
#      print 'Transport and sftp are empty'
      sftp = sftp_connect_client(transport)
  if ((name == None) or (name == '')):
      print 'Invalid directory (none): %s. can NOT make dir.' % name
      return -1
#  print "Entering with name: %s" % name
  starting_name = name
  head, tail = os.path.split(name)
  if not tail:
      head, tail = os.path.split(head)
  try:
      sftp.mkdir(head)
#      print "Created 1 %s." % head
      status = 1
#      sftp.rmdir(head)
  except:
#      print "Can't make %s" % head
      status = 0
  if ((head and tail) and not status):
      sftp_makedirs(head, mode, transport, sftp)
#  if (not os.path.exists(name)):
#  print "Making directory: %s (from request: %s)" % (name, starting_name)
  try:
      sftp.mkdir(name, mode)
#      print "Created 2 %s." % name
  except:
#      print "Can't make %s" % name
      pass

  return 0

def sftp_upload_file(local_file, remote_path, transport=None, sftp=None):
  """
  """
  if ((sftp == None) or (transport == None)): sftp = sftp_connect_client(transport)
  if ((local_file == None) or (local_file == '')):
      print 'Invalid Payload file (none): %s. can NOT upload.' % local_file
      return -1
  # check if payload file exists
  if (os.access(local_file, os.F_OK)): pass
  else:
      print 'Payload file: %s does NOT exist. Can NOT upload.' % local_file
      return -1
  # split payload information into file_path and file_name
  payload_path, payload_name = os.path.split(local_file)
#  print 'Payload path: %s, Payload file: %s' % (payload_path, payload_name)
  # create directory on SFTP side
  status = sftp_makedirs(remote_path, transport, sftp)
  if (status == 0):
      pass
  else:
      print "makedirs failed"
      sftp_close(sftp, transport)
      return 1

  remote_file = remote_path + '/' + payload_name
#  print 'Remote file: %s' % remote_file
  # ready to upload the file
  try:
      data = open(local_file, 'rb').read()
      status = sftp.open(remote_file, 'w').write(data)
  except Exception, e:
      print '*** Caught exception: %s: %s' % (e.__class__, e)
#      traceback.print_exc()
      sftp_close(sftp, transport)
      return 1
  return status

def main():
  """
  """
  print " You can NOT run this interactively "
  return


if __name__ == "__main__":
  main()
