from vyperlogix.misc import _utils

def dummy():
    pass

asMessage = lambda reason:'(%s) %s.' % (_utils.callersName(),reason)

def _sf_query(sfdc,soql,callback_before=dummy,callback_after=dummy):
    import sys, types, traceback, logging
    from pyax.exceptions import ApiFault

    try:
	if (type(callback_before) == types.FunctionType):
	    try:
		callback_before()
	    except:
		pass
	ret = sfdc.query(soql)
	if (type(callback_after) == types.FunctionType):
	    try:
		callback_after()
	    except:
		pass
        return ret
    except ApiFault:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
	info_string = asMessage('soql=%s, Reason: %s' % (soql,info_string))
	print >>sys.stderr, info_string
        logging.error(info_string)
        return None

