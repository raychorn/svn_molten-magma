""" 
Test script for CaseWatcher support. 
""" 
import os, sys

toks = os.path.abspath(os.path.curdir).split(os.sep)
if (sys.platform == 'win32'):
    t = toks[0:2]
else:
    t = toks[0:3]
homeDir = os.sep.join(t)

_isProduction = os.path.abspath(os.path.curdir).find('/src/') > -1
if (not os.environ.has_key('PYTHONPATH')):
    os.environ['PYTHONPATH'] = '%s/python/lib;' % (homeDir)
    p = ''
    if (_isProduction):
        p = '/src'
    else:
        p = '/staging'
    sys.path.insert(0,'%s%s/sfapi2/sflib' % (homeDir,p))
try:
    import sfUtil
except ImportError, details:
    print 'ERROR :: Reason is "%s".' % (details)
    print '(---) PYTHONPATH=[%s]' % (os.environ['PYTHONPATH'])
    print '(---) sys.path ::'
    for p in sys.path:
        print '\t%s' % (p)

def main():
    print 'sys.platform=[%s]' % (sys.platform)
    print 'argv[0]=[%s]' % (sys.argv[0])
    print 'curdir=[%s]' % (os.path.curdir)
    print 'curdir=[%s]' % (os.path.abspath(os.path.curdir))
    print 'homeDir=[%s]' % (homeDir)
    print 'homeFolder=[%s]' % (sfUtil.homeFolder())

if (__name__ == '__main__'):
    main()
