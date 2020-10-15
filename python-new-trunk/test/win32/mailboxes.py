import os, sys
import traceback

from vyperlogix.misc import _utils
from vyperlogix.hash import lists

import sfUtil_win32

def main():
    d = lists.HashedLists2()
    ros = sfUtil_win32.connectToTide2()
    if (ros.transport):
	try:
	    for root,dirs,files in ros.os_walk('/var/log/CaseWatcher/smtpMailsink_logs/mailboxes'):
		if (len(dirs) == 0):
		    print 'Scanning "%s".' % (root)
		    for f in files:
			toks = os.path.splitext(f)
			ts = _utils.getFromTimeStampForFileName(toks[0])
			if (_utils.isSometimeToday(ts)):
			    d[root] = (f,ts)
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    info_string = self.api.self_asMessage(self,_message(info_string))
	    print >>sys.stderr, info_string
	finally:
	    ros.close()
	
	print 'BEGIN:'
	if (len(d) > 0):
	    d.prettyPrint(title='Mailboxes with mail for today...',fOut=sys.stderr)
	else:
	    print >>sys.stderr, 'No Mailboxes with mail for today.'
	print 'END !'

if (__name__ == '__main__'):
    main()
    pass
