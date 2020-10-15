import os, sys
from vyperlogix.misc import _utils
from vyperlogix.misc import _base64

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

if (__name__ == '__main__'):
    _root_ = os.path.dirname(sys.argv[0])
    fname = os.sep.join([_root_,'icon.ico'])

    data = _base64.toBase64(fname)
    
    buf = StringIO()
    print >>buf, 'def make_icon(fname):'
    print >>buf, '\timport os, sys'
    print >>buf, '\tfrom vyperlogix.misc import _utils'
    print >>buf, '\tfrom vyperlogix.misc import _base64'
    print >>buf, ''
    print >>buf, '\t_data = \\'
    print >>buf, '\t"""%s' % (data)
    print >>buf, '\t"""'
    print >>buf, ''
    print >>buf, '\t_root_ = os.path.dirname(sys.argv[0])'
    print >>buf, "\tfname = os.sep.join([_root_,fname])"
    print >>buf, '\tbool = (not os.path.exists(fname))'
    print >>buf, '\tif (not bool):'
    print >>buf, '\t\tst = os.stat(fname)'
    print >>buf, '\t\tts = st.st_mtime'
    print >>buf, '\t\tdt = _utils.getFromTimeStampForFileName(_utils.getAsDateTimeStrFromTimeSeconds(ts))'
    print >>buf, '\t\t'
    print >>buf, '\t\tst2 = os.stat(sys.argv[0])'
    print >>buf, '\t\tts2 = st2.st_mtime'
    print >>buf, '\t\tdt2 = _utils.getFromTimeStampForFileName(_utils.getAsDateTimeStrFromTimeSeconds(ts2))'
    print >>buf, '\t'
    print >>buf, '\t\tbool = bool | (dt2 > dt)'
    print >>buf, '\t'
    print >>buf, '\tif (bool):'
    print >>buf, '\t\tdata = _base64.fromBase64(_data,fname)'
    print >>buf, '\treturn fname'

    fname_py = os.sep.join([_root_,'icon.py'])
    _utils.writeFileFrom(fname_py,buf.getvalue())
    
    print '%s has been saved with a new icon.' % (fname_py)
    
    pass