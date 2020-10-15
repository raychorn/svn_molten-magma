#!/usr/bin/env python
import zipfile
import os, sys
import re
from distutils import util

from vyperlogix.lists.ListWrapper import ListWrapper
from vyperlogix.misc import _utils

l_files_to_ignore = ListWrapper([])

l_folders_to_not_really_ignore = ListWrapper(['test'])

l_folders_to_ignore = ListWrapper(['cron', 'pyax-tests', 'stackless', 'test'])

l_entry_points = ListWrapper(['sfapi2\\sflib\\profiler-stats.py', 'sfapi2\\sflib\\dbtest.py', 'sfapi2\\sflib\\CaseWatcherList2.py', 'sfapi2\\sflib\\smtpMailsink.py', 'sfapi2\\sflib\\latestFolder.py', 'test\\win32\\dbtest.py', 'sfapi2\\sflib\\clearDataPathOfFiles.py', 'sfapi2\\sflib\\getLastProcessDate2.py', 'sfapi2\\sflib\\runWithAnalysis.py', 'sfapi2\\sflib\\SfStats.py', 'sfapi2\\sflib\\MailEvent.py', 'sfapi2\\sflib\\crypto.py', 'sfapi2\\sflib\\sfConstant.py'])

l_data = ListWrapper(['data\\Dead CaseWatcher List Notification.htm'])

d_entry_folders = {}

for item in l_entry_points:
    d_entry_folders[os.path.dirname(item)] = item

_root = os.path.dirname(sys.argv[0])

_root_ = _root
for dirname in l_folders_to_ignore:
    aRoot = _utils.locateRootContaining(_root_,dirname)
    if (aRoot is not None) and (os.path.exists(aRoot)):
        files = os.listdir(aRoot)
        for f in files:
            if (not any([(l_files_to_ignore.find(item) > -1) for item in l_entry_points])):
                l_files_to_ignore.append(os.sep.join([aRoot,f]))
    _root_ = os.path.dirname(aRoot)
    pass

files = [os.sep.join([_root_,f]) for f in os.listdir(_root_)]
files = [f for f in files if (os.path.isfile(f))]
for f in files:
    l_files_to_ignore.append(f)

ignore = dict([(k,1) for k in list(l_files_to_ignore.asSet())])
entry_points = {}

for f in l_entry_points:
    _f = os.sep.join([_root_,f])
    if (os.path.exists(_f)):
        ignore[_f.replace('.py','.pyo')] = f
        entry_points[_f.replace('.py','.pyo')] = f
    elif (os.path.exists(f)):
        ignore[f.replace('.py','.pyo')] = f
        entry_points[f.replace('.py','.pyo')] = f

ignore_folders = dict([(k,1) for k in list(l_folders_to_ignore.asSet())]) #  if (l_folders_to_not_really_ignore.find(k) == -1)

l_entry_folders = ListWrapper(d_entry_folders.keys())

_l_entry_folders = ListWrapper(l_entry_folders.copy())

l_files_to_ignore = ListWrapper(l_files_to_ignore.asSet())

l_folders_to_ignore = ListWrapper(ignore_folders.keys())

rx = re.compile('[.]svn')
rxLog = re.compile('log')
rxPop = re.compile('pop')
rxZip = re.compile('[.]zip')

_zipName_prefix = 'CaseWatcher_'
zipName = '%s1_0.egg' % (_zipName_prefix)
zipName2 = '%s1_0.zip' % (_zipName_prefix)

zipName = os.sep.join([_root_,zipName])
zipName2 = os.sep.join([_root_,zipName2])
ignore[zipName] = 1
ignore[zipName2] = 1

def addFileToZip(top,_zip,filename,useNoPath=False):
    print 'ZIP Adding (%s) to (%s)' % (filename,_zip.filename)
    f_base = filename.replace('.pyo','.pyc').replace(top,'')
    _zip.write(filename,f_base if (not useNoPath) else os.path.basename(f_base))

try:
    zip = zipfile.ZipFile( zipName, 'w', zipfile.ZIP_DEFLATED)
    zip2 = zipfile.ZipFile( zipName2, 'w', zipfile.ZIP_DEFLATED)
    top = os.path.abspath(_root_)
    for root, dirs, files in os.walk(top):
        if (rx.search(root) == None) and (rxLog.search(root) == None) and (rxPop.search(root) == None) and (not any([root.find(l) > -1 for l in l_folders_to_ignore])):
            py_files = [os.sep.join([root,f]) for f in files if (f.endswith('.py'))]
            if (root != top):
                print 'Compiling (%s) %s' % (root,py_files)
                util.byte_compile(py_files,optimize=2,force=1)
            _files = [os.sep.join([root,f]) for f in files if (not f.endswith('.py'))]
            for f in _files:
                if (rxZip.search(f) == None) and (not ignore.has_key(f)):
                    addFileToZip(top,zip,f)
                elif (rxZip.search(f) == None) and (entry_points.has_key(f)):
                    addFileToZip(top,zip2,f,useNoPath=True)
                    file_types = ['.py','.pyc','.pyo']
                    for ft in file_types:
                        _f = f.split('.')[0]+ft
                        _f = os.sep.join([tok for tok in _f.replace(_root_,'').split(os.sep) if (len(tok.strip()) > 0)])
                        i = l_entry_points.findFirstContaining(_f)
                        if (i > -1):
                            del l_entry_points[i]
    for f in l_entry_points:
        top = os.sep.join([_root_,os.path.dirname(f)])
        for root, dirs, files in os.walk(top):
            if (rx.search(root) == None) and (rxLog.search(root) == None) and (rxPop.search(root) == None):
                py_files = [os.sep.join([root,f]) for f in files if (f.endswith('.py') and (l_entry_points.findFirstContaining(f) > -1))]
                print 'Compiling (%s) %s' % (root,py_files)
                util.byte_compile(py_files,optimize=2,force=1)
                _files = [f.replace('.py','.pyo') for f in py_files]
                for f in _files:
                    if (rxZip.search(f) == None):
                        addFileToZip(top,zip2,f)
    for f in l_data:
        top = os.sep.join([_root_,os.path.dirname(f)])
        _f = os.sep.join([_root_,f])
	addFileToZip(os.path.dirname(top),zip2,_f)
except Exception, details:
    print 'Error in ZIP processing. (%s)' % (str(details))
finally:
    try:
        zip.close()
        zip2.close()
    except Exception, details:
        pass
    
    #import sfUtil_win32
    
    #ros = sfUtil_win32.connectToTide2()
    #if (ros.transport):
	#try:
	    #cwd = ros.os_getcwd()
	    #print 'cwd is "%s".' % (cwd)
	    #if (ros.isSFTP):
		#_remote_zipName = '@2/%s' % (os.path.basename(zipName))
		#print 'SFTP "%s" to host as "%s".' % (zipName,_remote_zipName)
		#if (ros.os_path_exists(_remote_zipName)):
		    #ros.os_remove(_remote_zipName)
		#ros.sftp.put(zipName, _remote_zipName)
    
		#_remote_zipName2 = '@4/%s' % (os.path.basename(zipName2))
		#print 'SFTP "%s" to host as "%s".' % (zipName2,_remote_zipName2)
		#if (ros.os_path_exists(_remote_zipName2)):
		    #ros.os_remove(_remote_zipName2)
		#ros.sftp.put(zipName2, _remote_zipName2)
	#finally:
	    #ros.close()
