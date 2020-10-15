"""
SSH support for win32 development to spoof accessing server based Linux resources.
"""

import os, sys
import types
import traceback

from binascii import hexlify

from vyperlogix.misc import ObjectTypeName

_iv = __name__[len(__name__)-8:]

if (sys.platform == 'win32'):
    _using_paramiko = True
    try:
        import paramiko
    except ImportError, details:
        _using_paramiko = False

class remote_os:
    def __init__(self, hostname, port, username, password=''):
        self.__remote_command_getcwd__ = 'getcwd()'
        self.__remote_command_listdir__ = 'listdir()'
        self.__remote_command_listdir_attr__ = 'listdir_attr()'
        self.__remote_command_lstat__ = 'lstat()'
        self.__remote_command_stat__ = 'stat()'
        self.__remote_command_mkdir__ = 'mkdir()'
        self.__remote_command_normalize__ = 'normalize()'
        self.__remote_command_readlink__ = 'readlink()'
        self.__remote_command_remove__ = 'remove()'
        self.__remote_command_rename__ = 'rename()'
        self.__remote_command_rmdir__ = 'rmdir()'
        self.__remote_command_stat__ = 'stat()'
        self.__remote_command_symlink__ = 'symlink()'
        self.__remote_command_truncate__ = 'truncate()'
        self.__remote_command_unlink__ = 'unlink()'
        self.__remote_command_utime__ = 'utime()'
        
        self.__isRemote__ = (len(hostname) > 0) and (port > -1) and (len(username) > 0) and (len(password) > 0)
            
        self.__hostname__ = hostname
        self.__port__ = port
        self.__username__ = username
        self.__password__ = password
        self.__isSFTP__ = True
        self.__isSSH__ = False

        self.__os_sep__ = '/'

        self.__transport__ = None
        self.__ssh__ = None
        self.__sftp__ = None

    def get_transport(self):
        return self.__transport__

    def set_transport(self, _transport):
        self.__transport__ = _transport

    def get_ssh(self):
        return self.__ssh__

    def set_ssh(self, _ssh):
        self.__ssh__ = _ssh

    def get_sftp(self):
        return self.__sftp__

    def set_sftp(self, _sftp):
        self.__sftp__ = _sftp

    def get_os_sep(self):
        return self.__os_sep__

    def get_remote_command_getcwd(self):
        return self.__remote_command_getcwd__

    def get_remote_command_listdir(self):
        return self.__remote_command_listdir__

    def get_remote_command_listdir_attr(self):
        return self.__remote_command_listdir_attr__

    def get_remote_command_lstat(self):
        return self.__remote_command_lstat__

    def get_remote_command_stat(self):
        return self.__remote_command_stat__

    def get_remote_command_mkdir(self):
        return self.__remote_command_mkdir__

    def get_remote_command_normalize(self):
        return self.__remote_command_normalize__

    def get_remote_command_readlink(self):
        return self.__remote_command_readlink__

    def get_remote_command_remove(self):
        return self.__remote_command_remove__

    def get_remote_command_rename(self):
        return self.__remote_command_rename__

    def get_remote_command_rmdir(self):
        return self.__remote_command_rmdir__

    def get_remote_command_symlink(self):
        return self.__remote_command_symlink__

    def get_remote_command_truncate(self):
        return self.__remote_command_truncate__

    def get_remote_command_unlink(self):
        return self.__remote_command_unlink__

    def get_remote_command_utime(self):
        return self.__remote_command_utime__

    def get_isRemote(self):
        return self.__isRemote__

    def get_hostname(self):
        return self.__hostname__

    def get_port(self):
        return self.__port__

    def get_username(self):
        return self.__username__

    def get_password(self):
        return self.__password__

    def get_isSFTP(self):
        return self.__isSFTP__

    def set_isSFTP(self, bool):
        self.__isSFTP__ = bool

    def get_isSSH(self):
        return self.__isSSH__

    def set_isSSH(self, bool):
        self.__isSSH__ = bool

    def exec_command(self, trans, command):
        chan = trans.open_session()
        chan.exec_command(command)
        stdin = chan.makefile('wb')
        stdout = chan.makefile('rb')
        stderr = chan.makefile_stderr('rb')
        return stdin, stdout, stderr

    def agent_auth(self,transport):
	"""
	Attempt to authenticate to the given transport using any of the private
	keys available from an SSH agent.
	"""
	transport = transport if (not self.transport) else self.transport
	if (transport):
	    agent = paramiko.Agent()
	    agent_keys = agent.get_keys()
	    if len(agent_keys) == 0:
		return False
		
	    for key in agent_keys:
		print 'Trying ssh-agent key %s' % hexlify(key.get_fingerprint()),
		try:
		    transport.auth_publickey(self.username, key)
		    print '%s ... success!' % (self.username)
		    return True
		except paramiko.SSHException:
		    print '%s ... nope.' % (self.username)
	else:
	    print >>sys.stderr, '(%s) :: Transport is not connected.' % (ObjectTypeName.objectSignature(self))
	return False

    def ssh_connect_transport(self):
        """ Make an SSH connection with the server to mimic certain functions only for win32 platform to facilitate development.
        """
        if (len(self.hostname) > 0) and (len(self.username) > 0) and (self.port > 0): #  and (len(self.password) > 0)
            # get host key, if we know one
            hostkeytype = None
            hostkey = None
            host_keys = {}
            if (sys.platform != 'win32'):
                try:
                    host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/.ssh/known_hosts'))
                except IOError:
                    try:
                        host_keys = paramiko.util.load_host_keys(os.path.expanduser('~/ssh/known_hosts'))
                    except IOError:
                        print '*** Unable to open host keys file'
                #  print host_keys
                if host_keys.has_key(hostname):
                    hostkeytype = host_keys[hostname].keys()[0]
                    hostkey = host_keys[hostname][hostkeytype]
                    print 'Using host key of type %s' % hostkeytype
                else:
                    print "Host key not found. Please create key manually using: ssh %s" % hostname
            # now, connect and use paramiko Transport to negotiate SSH2 across the connection
            try:
                if (self.isSFTP):
                    t = paramiko.Transport((self.hostname, self.port))
                    t.use_compression(True)
		    if (self.agent_auth(t)):
			t.connect(username=self.username, hostkey=hostkey)
		    else:
			t.connect(username=self.username, password=self.password, hostkey=hostkey)
                elif (self.isSSH):
                    t = paramiko.Transport((self.hostname, self.port))
                    t.use_compression(True)
		    if (self.agent_auth(t)):
			t.connect(username=self.username, hostkey=hostkey)
		    else:
			t.connect(username=self.username, password=self.password, hostkey=hostkey)
            except Exception, e:
                print '*** Caught exception: %s: %s' % (e.__class__, e)
                traceback.print_exc()
                try:
                    t.close()
                except:
                    pass
                sys.exit(1)
        else:
            print 'WARNING :: Unable to make a connection with the server using hostname of "%s", port of "%s", username of "%s" and password of "%s".' % (self.hostname,self.port,self.username,self.password)
            return None
        return t
    # END ssh_connect_transport

    def close(self):
        """ Close the SSH connection.
        """
        if (self.ssh):
            try:
                self.ssh.close()
                self.ssh = None
            except:
                pass
        if (self.sftp):
            try:
                self.sftp.close()
                self.sftp = None
            except:
                pass
        if (self.transport):
            try:
                self.transport.close()
                self.transport = None
            except:
                pass
        return
    # END close

    def ssh_connect_client(self, transport):
        """ connect and use paramiko Transport to negotiate SSH2 across the connection
        """
        if (transport in [None,'',""]):
            self.transport = self.ssh_connect_transport()
        try:
            if (self.isSFTP):
                if (self.sftp == None):
                    self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            elif (self.isSSH):
                if (self.ssh == None):
                    self.ssh = self.transport
        except Exception, e:
            print '*** Caught exception: %s: %s' % (e.__class__, e)
            traceback.print_exc()
            try:
                if (self.isSFTP):
                    self.close()
                elif (self.isSSH):
                    self.close()
            except:
                pass
            sys.exit(1)
    
        if (self.isSFTP):
            return self.sftp
        return self.ssh
    # END ssh_connect_client

    def ssh_exec_cmd(self, *args):
        """ Perform a command against an SSH accessible server.
        """
        def getDirName():
            dirName = '.'
            if (len(args) > 1):
                dirName = args[1]
            return dirName
        def getMode():
            mode = 511
            if (len(args) > 2):
                mode = args[2]
            return mode
        def getDirName2():
            dirName = '.'
            if (len(args) > 2):
                dirName = args[2]
            return dirName
        def getSize():
            size = 0
            if (len(args) > 2):
                size = args[2]
            return size
        def getTimes():
            times = ()
            if (len(args) > 3):
                times = (args[2],args[2])
            return times
        if (self.sftp == None):
            self.sftp = self.ssh_connect_client(self.transport)
        value = None
        try:
            if (args[0].find(self.const_getcwd_symbol) > -1):
                self.sftp.chdir(getDirName())
                value = self.sftp.getcwd()
            elif (args[0].find(self.const_listdir_symbol) > -1):
                value = self.sftp.listdir(getDirName())
            elif (args[0].find(self.const_listdir_attr_symbol) > -1):
                value = self.sftp.listdir_attr(getDirName())
            elif (args[0].find(self.const_lstat_symbol) > -1) or (args[0].find(self.const_stat_symbol) > -1):
                value = self.sftp.lstat(getDirName())
            elif (args[0].find(self.const_mkdir_symbol) > -1):
                value = self.sftp.mkdir(getDirName(),getMode())
            elif (args[0].find(self.const_normalize_symbol) > -1):
                value = self.sftp.normalize(getDirName())
            elif (args[0].find(self.const_readlink_symbol) > -1):
                value = self.sftp.readlink(getDirName())
            elif (args[0].find(self.const_remove_symbol) > -1):
                value = self.sftp.remove(getDirName())
            elif (args[0].find(self.const_rename_symbol) > -1):
                value = self.sftp.rename(getDirName(),getDirName2())
            elif (args[0].find(self.const_rmdir_symbol) > -1):
                value = self.sftp.rmdir(getDirName())
            elif (args[0].find(self.const_stat_symbol) > -1):
                value = self.sftp.stat(getDirName())
            elif (args[0].find(self.const_symlink_symbol) > -1):
                value = self.sftp.symlink(getDirName(),getDirName2())
            elif (args[0].find(self.const_truncate_symbol) > -1):
                value = self.sftp.truncate(getDirName(),getSize())
            elif (args[0].find(self.const_unlink_symbol) > -1):
                value = self.sftp.unlink(getDirName())
            elif (args[0].find(self.const_utime_symbol) > -1):
                value = self.sftp.utime(getDirName(),getTimes())
        except:
            return None
        return value
    # END ssh_exec_cmd

    def __run__(self, t, cmd):
	'Open channel on transport, run command, capture output and return'
	# See the demos for paramiko for the interactive portion - use it to make this work...
	out = ''
	
	chan = t.open_session()
	chan.setblocking(0)
	chan.ultra_debug = True
	
	if not chan.exec_command(cmd):
	    raise UserWarning('ERROR: Failed to run command: %s' % (cmd))
	
	while select.select([chan,], [], []):
	    x = chan.recv(1024)
	    if not x: break
	    out += x
	    select.select([],[],[],.1)
	
	chan.close()
	return out

    def remote_os_exec_cmd(self,command):
        """ Perform remote command execution using SSH link.
        """
	value = None
        if (self.transport not in [None,'',""]):
	    value = self.__run__(self.transport, command)
	else:
	    print >>sys.stderr, '(%s) :: Transport is not connected.' % (ObjectTypeName.objectSignature(self))
        return value
    # END remote_os_exec_cmd

    def homeFolder(self):
        """ home folder for current user """
        f = self.os_normalize(self.os_getcwd())
        toks = f.split(self.os_sep)
        t = toks[0:3]
        return self.os_sep.join(t)
    
    def searchForFolderNamed(self,fname,top='/'):
        """ Search for a folder of a specific name """
        for root, dirs, files in self.os_walk(top, topdown=True):
            if (fname in dirs):
                return self.os_sep.join([root,fname])
        return ''

    def os_getcwd(self):
        """ Perform os.getcwd() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_getcwd_symbol, '')
        else:
            return os.getcwd()
    # END os_getcwd

    def os_path_exists(self, pathName):
        """ Perform os.path.exists() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.os_stat(pathName) != None
        else:
            return os.path.exists(pathName)
    # END os_path_exists

    def os_listdir(self, pathName):
        """ Perform os.listdir() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_listdir_symbol, pathName)
        else:
            return os.listdir(pathName)
    # END os_listdir

    def os_listdir_attr(self, pathName):
        """ Perform os.listdir() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_listdir_attr_symbol, pathName)
        else:
            return os.listdir(pathName)
    # END os_listdir_attr

    def remote_os_lstat(self, pathName):
        """ Perform os.lstat() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_lstat_symbol, pathName)
        else:
            return os.lstat(pathName)
    # END os_lstat

    def os_mkdir(self, pathName, fileMode=511):
        """ Perform os.mkdir() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_mkdir_symbol, pathName, fileMode)
        else:
            return os.mkdir(pathName,fileMode)
    # END os_mkdir

    def os_normalize(self, pathName):
        """ Perform os.path.abspath() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_normalize_symbol, pathName)
        else:
            return os.path.abspath(pathName)
    # END os_normalize

    def os_readlink(self, pathName):
        """ Perform os.path.abspath() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_readlink_symbol, pathName)
        else:
            return os.path.abspath(pathName)
    # END os_readlink

    def os_remove(self, pathName):
        """ Perform os.remove() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_remove_symbol, pathName)
        else:
            return os.remove(pathName)
    # END os_remove

    def os_rename(self, pathName, pathName2):
        """ Perform os.rename() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_rename_symbol, pathName, pathName2)
        else:
            return os.rename(pathName, pathName2)
    # END os_rename

    def os_rmdir(self, pathName):
        """ Perform os.rmdir() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_rmdir_symbol, pathName)
        else:
            return os.rmdir(pathName)
    # END os_rmdir

    def os_stat(self, pathName):
        """ Perform os.stat() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_stat_symbol, pathName)
        else:
            return os.stat(pathName)
    # END os_stat

    def os_lstat(self, pathName):
        """ Perform os.lstat() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_lstat_symbol, pathName)
        else:
            return os.lstat(pathName)
    # END os_stat

    def os_getsize(self, pathName):
        """ Perform os.stat().st_size if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            stat = self.ssh_exec_cmd(self.__remote_command_stat__, pathName)
        else:
            stat = os.stat(pathName)
        return stat.st_size
    # END os_getsize

    def os_symlink(self, pathName, pathName2):
        """ Perform os.mkdir if platform is win32 otherwise use remote os.symlink() variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_symlink_symbol, pathName, pathName2)
        else:
            stat = os.symlink(pathName, pathName2)
    # END os_symlink

    def os_truncate(self, pathName, fileSize=0):
        """ Perform file truncate if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_truncate_symbol, pathName, fileSize)
        else:
            if (os.path.exists(pathName)):
                fHand = open(pathName, 'rb')
                fHand.truncate(fileSize)
                fHand.flush()
                fHand.close()
    # END os_truncate

    def os_unlink(self, pathName):
        """ Perform os.unlink() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_unlink_symbol, pathName)
        else:
            if (os.path.exists(pathName)):
                os.unlink(pathName)
    # END os_unlink

    def os_utime(self, pathName, times):
        """ Perform os.utime() if platform is win32 otherwise use remote variant using SSH link.
        """
        if (sys.platform == 'win32'):
            return self.ssh_exec_cmd(self.const_utime_symbol, pathName, times)
        else:
            if (os.path.exists(pathName)):
                os.utime(pathName, times)
    # END os_utime

    def os_isdir(self, pathName):
        """Test whether a remote path is a directory"""
        import stat
        try:
            st = self.os_stat(pathName)
            return False if (st == None) else stat.S_ISDIR(st.st_mode)
        except os.error:
            return False
        return False

    def os_islink(self, pathName):
        """Test whether a path is a symbolic link"""
        import stat
        try:
            st = self.os_lstat(pathName)
        except (os.error, AttributeError):
            return False
        return stat.S_ISLNK(st.st_mode)

    def os_walk(self, top, topdown=True, onerror=None):
        """Remote Directory tree generator.
    
        For each directory in the remote directory tree rooted at top (including top
        itself, but excluding '.' and '..'), yields a 3-tuple
    
            dirpath, dirnames, filenames
    
        dirpath is a string, the path to the directory.  dirnames is a list of
        the names of the subdirectories in dirpath (excluding '.' and '..').
        filenames is a list of the names of the non-directory files in dirpath.
        Note that the names in the lists are just names, with no path components.
        To get a full path (which begins with top) to a file or directory in
        dirpath, do os.path.join(dirpath, name).
    
        If optional arg 'topdown' is true or not specified, the triple for a
        directory is generated before the triples for any of its subdirectories
        (directories are generated top down).  If topdown is false, the triple
        for a directory is generated after the triples for all of its
        subdirectories (directories are generated bottom up).
    
        When topdown is true, the caller can modify the dirnames list in-place
        (e.g., via del or slice assignment), and walk will only recurse into the
        subdirectories whose names remain in dirnames; this can be used to prune
        the search, or to impose a specific order of visiting.  Modifying
        dirnames when topdown is false is ineffective, since the directories in
        dirnames have already been generated by the time dirnames itself is
        generated.
    
        By default errors from the os.listdir() call are ignored.  If
        optional arg 'onerror' is specified, it should be a function; it
        will be called with one argument, an os.error instance.  It can
        report the error to continue with the walk, or raise the exception
        to abort the walk.  Note that the filename is available as the
        filename attribute of the exception object.
    
        Caution:  if you pass a relative pathname for top, don't change the
        current working directory between resumptions of walk.  walk never
        changes the current directory, and assumes that the client doesn't
        either.
    
        Example:
    
        from os.path import join, getsize
        for root, dirs, files in walk('python/Lib/email'):
            print root, "consumes",
            print sum([getsize(join(root, name)) for name in files]),
            print "bytes in", len(files), "non-directory files"
            if 'CVS' in dirs:
                dirs.remove('CVS')  # don't visit CVS directories
        """
    
        from posixpath import join
    
        # We may not have read permission for top, in which case we can't
        # get a list of the files the directory contains.  os.path.walk
        # always suppressed the exception then, rather than blow up for a
        # minor reason when (say) a thousand readable directories are still
        # left to visit.  That logic is copied here.
        try:
            # Note that listdir and error are globals in this module due
            # to earlier import-*.
            names = self.os_listdir(top)
        except error, err:
            if (onerror is not None) and (type(onerror) == types.FunctionType):
                try:
                    onerror(err)
                except:
                    pass
            return
    
        dirs, nondirs = [], []
	if (names is not None):
	    for name in names:
		if self.os_isdir(join(top, name)):
		    dirs.append(name)
		else:
		    nondirs.append(name)
	
	    if topdown:
		yield top, dirs, nondirs
	    for name in dirs:
		path = join(top, name)
		if not self.os_islink(path):
		    for x in self.os_walk(path, topdown, onerror):
			yield x
	    if not topdown:
		yield top, dirs, nondirs
	else:
	    print '(%s) :: Possibly no files found at "%s".' % (ObjectTypeName.objectSignature(self),top)

    const_getcwd_symbol = property(get_remote_command_getcwd)
    const_listdir_symbol = property(get_remote_command_listdir)
    const_listdir_attr_symbol = property(get_remote_command_listdir_attr)
    const_lstat_symbol = property(get_remote_command_lstat)
    const_mkdir_symbol = property(get_remote_command_mkdir)
    const_normalize_symbol = property(get_remote_command_normalize)
    const_readlink_symbol = property(get_remote_command_readlink)
    const_remove_symbol = property(get_remote_command_remove)
    const_rename_symbol = property(get_remote_command_rename)
    const_rmdir_symbol = property(get_remote_command_rmdir)
    const_stat_symbol = property(get_remote_command_stat)
    const_symlink_symbol = property(get_remote_command_symlink)
    const_truncate_symbol = property(get_remote_command_truncate)
    const_unlink_symbol = property(get_remote_command_unlink)
    const_utime_symbol = property(get_remote_command_utime)
    isRemote = property(get_isRemote)
    
    hostname = property(get_hostname)
    port = property(get_port)
    username = property(get_username)
    password = property(get_password)
    isSFTP = property(get_isSFTP, set_isSFTP)
    isSSH = property(get_isSSH, set_isSSH)
    
    os_sep = property(get_os_sep)
    
    transport = property(get_transport, set_transport)
    ssh = property(get_ssh, set_ssh)
    sftp = property(get_sftp, set_sftp)
    
def connectToRiver():
    from vyperlogix.products import keys
    from vyperlogix.crypto import XTEAEncryption

    ros = remote_os('river.moltenmagma.com', 22, XTEAEncryption.decryptode(keys._key,'86E953418DFA2831',_iv), XTEAEncryption.decryptode(keys._key,'86E9604F9EF43524EDFF',_iv))
    ros.transport = ros.ssh_connect_transport()
    return ros

def connectToTide2():
    from vyperlogix.products import keys
    from vyperlogix.crypto import XTEAEncryption

    ros = remote_os('tide2.moltenmagma.com', 22, XTEAEncryption.decryptode(keys._key,'87E74F5091',_iv), XTEAEncryption.decryptode(keys._key,'A5EA4549BFF16875',_iv))
    ros.transport = ros.ssh_connect_transport()
    return ros

if __name__ == "__main__":
    print 'This module was not intended to be run interactively.'
    ros = connectToTide2()
    if (0):
        files = ros.os_listdir_attr('.')
        print '\n'.join([str(f) for f in files])

    if (ros.transport):
        #bash = ros.remote_os_exec_cmd('sudo su')
        #if (len(bash) > 0):
            #l_bash = list(bash)
            #for l in l_bash:
                #lines = l._wbuffer.readlines()
                #print 'nytes[0]=[%s]' % '\n'.join(lines)
        #bool = ros.os_path_exists('reallyfakefile_forsure.txt')
        #assert bool == None, 'Oops - looks like the os_path_exists() function is broken !'
        cwd = ros.os_getcwd()
	print 'cwd is "%s".' % (cwd)
        for root, dirs, files in ros.os_walk('%s' % cwd):
            print root, "consumes",
            print sum([ros.os_getsize(ros.os_sep.join([root, name])) for name in files]),
            print "bytes in", len(files), "non-directory files"
        ros.close()
