# csv tester

from vyperlogix.parsers.CSV import CSV
from vyperlogix.misc.ReportTheList import reportTheList

csv_fname = "Z:\\@myMagma\\!Research WalkSCMTalus1.0\\branches in set33 24jun2008 IST for TAT estimate.csv"

if (__name__ == '__main__'):
    try:
        csv = CSV(csv_fname)
        
        print 'There are %d rows of data in "%s".' % (len(csv.rows),csv.filename)
        print ''
        l = csv.column(1)
        reportTheList(l,'The Data from %s' % (csv.filename))
    except Exception, details:
        logging.warning('Cannot process "%s" because "%s".' % (fname,details))
    pass
