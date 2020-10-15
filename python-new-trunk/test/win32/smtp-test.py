import os, sys
import traceback

from vyperlogix.misc import _utils
from vyperlogix.mail import message
from vyperlogix.mail import mailServer

notice = 'testing...'
msg = 'testing 1.2.3... <b>(%s)</b><br><b>(%s)</b>' % (_utils.timeStamp(),_utils.timeStamp())
try:
    msg = message.Message('molten-support@molten-magma.com', 'raychorn@hotmail.com', '%s\n%s' % (notice,msg), 'Test from "%s".' % sys.argv[0])
    smtp = mailServer.AdhocServer('tide2.moltenmagma.com:8025')
    smtp.sendEmail(msg)
except:
    exc_info = sys.exc_info()
    info_string = '\n'.join(traceback.format_exception(*exc_info))
    info_string = self.api.self_asMessage(self,_message(info_string))
    print >>sys.stderr, info_string
finally:
    print 'Message sent. (%s, %s)' % (notice,msg)
    print 'DONE!'

