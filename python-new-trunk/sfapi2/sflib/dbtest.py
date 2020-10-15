from vyperlogix import oodb
from vyperlogix.hash import lists
from vyperlogix.misc import _utils

import latestFolder

def main(fname=''):
    import os, sys
    
    fpath = ''
    _top = os.sep.join([os.path.abspath(os.curdir),'logs'])
    print >>sys.stdout, '_top is "%s".' % (_top)
    if (len(fname) > 0):
        fpath = os.sep.join([_top,fname])
    if (not os.path.exists(fpath)):
        fpath = latestFolder.latestFolder(top=_top,logs='logs',dbx='dbx')
    print >>sys.stdout, 'fpath is "%s".' % (fpath)
    dbxPath = os.sep.join([fpath,'dbx'])
    logsPath = os.sep.join([fpath,'logs'])
    files = os.listdir(dbxPath)
    for f in files:
        dbx_name = os.sep.join([dbxPath,f])
        print >>sys.stdout, 'dbx_name is "%s".' % (dbx_name)
        report_name = 'report-dbtest_%s.txt' % (f.split('.')[0])
        fq_report_name = os.sep.join([logsPath,report_name])
        print >>sys.stdout, 'fq_report_name is "%s".' % (fq_report_name)
        fOut = open(fq_report_name,'w')
        try:
            dbx = oodb.openPickledHashBasedOnFilename(dbx_name)
            try:
                lists.prettyPrint(dbx,title='%s'%(dbx.fileName),fOut=fOut)
            except Exception, details:
                print >>sys.stdout, 'dbx.fileName is "%s" has %d records.' % (dbx.fileName,len(dbx))
            finally:
                dbx.close()
            print >>fOut, '='*80
            print >>fOut
        finally:
            fOut.flush()
            fOut.close()

if (__name__ == '__main__'):
    if (_utils.isUsingWindows):
        from vyperlogix.misc import _psyco
        _psyco.importPsycoIfPossible(main)
    
    import sys
    fname = '' if (len(sys.argv) == 1) else sys.argv[1]
    main(fname)
    