import os, sys, pstats
from stat import *
from vyperlogix.misc import _utils
from vyperlogix.daemon.daemon import Log

cmp_dates = lambda x,y:x > y
theKey = lambda x:x[-1]

_fpath = os.path.abspath('logs/profiler.txt')
fpath = _fpath if (len(sys.argv) == 1) else sys.argv[1] if (os.path.exists(sys.argv[1])) else _fpath

_root_ = os.path.dirname(fpath) if (os.path.isfile(fpath)) else fpath

fname = os.sep.join([_root_,'profiler.txt'])
if (not os.path.exists(fname)):
    dname = os.path.dirname(fname)
    d_list = [os.sep.join([dname,f]) for f in os.listdir(dname) if (os.path.isdir(os.sep.join([dname,f])))]
    d_list = [(f,_utils.dateFromSeconds(os.stat(f)[ST_MTIME],useLocalTime=_utils.isUsingLocalTimeConversions)) for f in d_list]
    d_list.sort(cmp_dates,theKey)
    while (len(d_list) > 0):
        t = d_list.pop()
        dlogs = os.sep.join([t[0],'logs'])
        dplogs = os.sep.join([dlogs,'profiler.txt'])
        if (os.path.exists(dlogs)) and (os.path.exists(dplogs)):
            fname = dplogs
            break
    pass

_stdOut = open(os.sep.join([os.path.dirname(fname),'profiler_report.txt']),'w')
_sys_stdout = sys.stdout
sys.stdout = Log(_stdOut)
try:
    p = pstats.Stats(fname)
    print >>sys.stdout, p.strip_dirs().sort_stats(-1).print_stats()
finally:
    sys.stdout.close()
    sys.stdout = _sys_stdout


