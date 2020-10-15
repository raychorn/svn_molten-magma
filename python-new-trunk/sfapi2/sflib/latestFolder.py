import os
from stat import *
from vyperlogix.misc.ReportTheList import reportTheList

def dummy():
    pass

has_files = lambda fpath: (os.path.exists(fpath)) and (len(os.listdir(fpath)) > 0)
check_for_dbx_files = lambda args: has_files(os.sep.join([args[0],args[-1]]))

def latestFolders(top='.',logs='logs',dbx='dbx',callback=check_for_dbx_files):
    import sys, types
    from vyperlogix.misc import _utils
    
    _cmp_dates = lambda x,y:x > y
    theKey = lambda x:x[-1]
    
    def cmp_dates(x,y):
	bool = x > y
	print >>sys.stdout, '%s > %s (%s)' % (x,y,bool)
	return bool
    
    def _callback_wrapper(func,args):
        if (func is not None):
            try:
                bool = func(args)
                print >>sys.stdout, 'args=%s, bool=%s' % (str(args),bool)
                return bool
            except:
                return True
        return False
    
    get_folders_list = lambda top:[os.sep.join([top,f]) for f in os.listdir(top) if (os.path.isdir(os.sep.join([top,f]))) and (_utils.isTimeStampForFileName(f))]
    
    d_list = []
    _top = top if (os.path.exists(top)) else os.path.abspath(top)
    top = os.path.dirname(top) if (os.path.exists(top)) else os.path.abspath(top)
    if (os.path.exists(top)):
        d_list = get_folders_list(top)
        if (len(d_list) == 0):
            d_list = get_folders_list(_top)
        d_list = [(f,_utils.dateFromSeconds(os.stat(f)[ST_MTIME],useLocalTime=_utils.isUsingLocalTimeConversions)) for f in d_list if (_callback_wrapper(callback,[f,dbx]))]
        d_list2 = [(t[-1],t[0]) for t in d_list]
	d2 = dict(d_list2)
	l2 = [t[0] for t in d_list2]
        l2.sort()
	reportTheList(l2,'l2.',fOut=sys.stdout)
	l = []
	for item in l2:
	    l.append((d2[item],item))
	reportTheList(l,'l.',fOut=sys.stdout)
    return l

def latestFolder(top='.',logs='logs',dbx='dbx',callback=check_for_dbx_files):
    d_list = latestFolders(top=top,logs=logs,dbx=dbx,callback=callback)
    t = d_list if (len(d_list) == 0) else d_list.pop()
    fname = None if (len(t) == 0) else t[0]
    return fname

def allFolders(top='.',logs='logs',dbx='dbx',callback=dummy):
    return latestFolders(top=top,logs=logs,dbx=dbx,callback=callback)
