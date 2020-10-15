# Rotate Logs for River and Ebb

import os
import sys
from stat import *
from sfUtil import *

from optparse import OptionParser

import re

_has_date_regex = "(19|20)[0-9]{2}[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])"

from sfUtil_win32 import *

def main(ros,fname,_opts):
    files = [(ros.os_isdir(ros.os_sep.join([fname,f])),ros.os_sep.join([fname,f])) for f in ros.os_listdir(fname)]
    d_folders = {}
    for f in files:
        if (f[0]):
            d_folders[f[-1]] = f[-1]
    tstamp = timeStamp()
    t_folder = ''.join(tstamp.split('T')[0]).replace(':','-').replace('.','_')
    for f in files:
        if (not f[0]):
            f_root = os.path.dirname(f[-1])
            f_base = os.path.basename(f[-1])
	    if (not f_base.startswith('.')) and (not f_base.startswith('walk')):
		_t_folder = ros.os_sep.join([f_root,t_folder])
		if (not ros.os_path_exists(_t_folder)):
		    if (_opts.testflag == False):
			ros.os_mkdir(_t_folder)
		folderName = '%s%slogs_%s' % (_t_folder,ros.os_sep,f_base)
		if (not d_folders.has_key(folderName)):
		    new_folder = ros.os_sep.join([f_root,folderName])
		    if (not ros.os_path_exists(new_folder)):
			if (_opts.testflag == False):
			    ros.os_mkdir(new_folder)
			logPrint('(_opts.testflag=[%s]), os.mkdir(%s)' % (_opts.testflag,new_folder))
		if (_opts.testflag == False):
		    ros.os_rename(f[-1],ros.os_sep.join([new_folder,f_base]))
		logPrint('(_opts.testflag=[%s]), os.rename(%s,%s)' % (_opts.testflag,f[-1],ros.os_sep.join([new_folder,f_base])))
    for f in d_folders.keys():
	if (not re.search(_has_date_regex, f)):
	    main(ros,f,_opts)

if (__name__ == '__main__'):
    op = OptionParser()
    op.add_option('-d', '--dry', dest='testflag', action='store_true', default=True,
                  help='flags the dry-run mode, default is "true".')
    op.add_option('-x', '--xpert', dest='testflag', action='store_false', default=False,
                  help='flags the real-run mode, default is "false".')

    (opts, args) = op.parse_args()

    ros = connectToRiver()
    logPath = ros.searchForFolderNamed('log',ros.homeFolder())
    main(ros,logPath,opts)
    ros.close()
