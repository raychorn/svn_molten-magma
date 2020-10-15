import os, sys, traceback
import logging

from vyperlogix import misc
from vyperlogix.misc import _utils
from vyperlogix.daemon.daemon import Log

from pyax.connection import Connection
from pyax.exceptions import ApiFault

from vyperlogix.crypto import blowfish

from vyperlogix.logging import standardLogging

is_platform_not_windows = lambda _sys:(_sys.platform != 'win32')
bool_is_platform_not_windows = is_platform_not_windows(sys)

_isBeingDebugged = _utils.isBeingDebugged

_logging = logging.INFO

_isVerbose = True

_isStaging = True

def _sf_query(sfdc,soql):
    try:
	ret = sfdc.query(soql)
	sf_stats.count_query()
        return ret
    except ApiFault:
        exc_info = sys.exc_info()
        info_string = '\n'.join(traceback.format_exception(*exc_info))
        logging.error('(%s) soql=%s, Reason: %s' % (misc.funcName(),soql,info_string))
    return None

def exception_callback(sections):
    _msg = 'EXCEPTION Causing Abend.\n%s' % '\n'.join(sections)
    print >>sys.stdout, _msg
    print >>sys.stderr, _msg
    logging.error('(%s) :: %s' % (misc.funcName(),_msg))
    sys.stdout.close()
    sys.stderr.close()
    sys.exit()

_log_path = ''

def process(sfdc):
    begin_ts = _utils.timeStampSalesForce(-600)
    end_ts = _utils.timeStampSalesForce()
    d = sfdc.getDeleted('Lead',begin_ts,end_ts)
    for k in d.keys():
	v = d[k]
	is_error = False
	try:
	    if (len(v) > 0):
		print 'BEGIN:'
		for kk in v.keys():
		    vv = v[kk]
		    print '%s is "%s"' % (kk,vv)
		print 'END!'
	except:
	    is_error = True
	if (not is_error):
	    print '%s is "%s"' % (k,v)
    pass

def main():
    global _log_path
    
    name = _utils.getProgramName()
    
    if (os.path.exists(_folderPath)):
	_log_path = _utils.safely_mkdir(fpath=_folderPath)
    else:
	_log_path = _utils.safely_mkdir(fpath=_cwd)
    
    logFileName = os.sep.join([_log_path,'%s_%s.log' % (_utils.timeStamp().replace(':','-'),name)])
    
    standardLogging.standardLogging(logFileName,_level=_logging,console_level=logging.INFO,isVerbose=_isVerbose)
    
    logging.info('Logging to "%s" using level of "%s:.' % (logFileName,standardLogging.explainLogging(_logging)))
    
    if (not _isBeingDebugged):
	_stdOut = open(os.sep.join([_log_path,'stdout.txt']),'w')
	_stdErr = open(os.sep.join([_log_path,'stderr.txt']),'w')
	
	sys.stdout = Log(_stdOut)
	sys.stderr = Log(_stdErr)
    
	logging.warning('stdout to "%s".' % (_stdOut.name))
	logging.warning('stderr to "%s".' % (_stdErr.name))
    
    s = [110,111,119,105,115,116,104,101,116,105,109,101,102,111,114,97,108,108,103,111,111,100,109,101,110,116,111,99,111,109,101,116,111,116,104,101,97,105,100,111,102,116,104,101,105,114,99,111,117,110,116,114,121]
    _cipher_password = ''.join([chr(ch) for ch in s])
    _cipher_password = blowfish.seedPassword(_cipher_password)
    
    from vyperlogix.products import keys
    
    if (_isStaging):
	#_username = 'rhorn@molten-magma.com.stag'
	#_password = 'sisko7660boo'
    
	#e_username = keys._encode(blowfish.encryptData(_username,_cipher_password))
	#e_password = keys._encode(blowfish.encryptData(_password,_cipher_password))
	
	p_username = _utils.strip(blowfish.decryptData(keys._decode('CCB35D1FE1DA16FF0C997A0EA7E3384198088F7D94E5B2AF'),_cipher_password))
	p_password = _utils.strip(blowfish.decryptData(keys._decode('17128C5071D0A7E233115DBA4482911A'),_cipher_password))
    
	#assert p_username == _username, '"%s" is not equal to "%s".' % (p_username,_username)
	#assert p_password == _password, '"%s" is not equal to "%s".' % (p_password,_password)
    else:
	#_username = 'molten_admin@molten-magma.com'
	#_password = 'u2cansleeprWI2X9JakDlxjcuAofhggFbaf'
    
	#e_username = keys._encode(blowfish.encryptData(_username,_cipher_password))
	#e_password = keys._encode(blowfish.encryptData(_password,_cipher_password))
	
	p_username = _utils.strip(blowfish.decryptData(keys._decode('1485E59D768462B2428DFA0E453842DA41E6313966C012372453A99EADD981A1'),_cipher_password))
	p_password = _utils.strip(blowfish.decryptData(keys._decode('32BF51A7190DCEA4BA1A5481041D6B606CDA5B46805B3B540A9D56077A04F699B6B62C9D5500DAF0'),_cipher_password))
    
	#assert p_username == _username, '"%s" is not equal to "%s".' % (p_username,_username)
	#assert p_password == _password, '"%s" is not equal to "%s".' % (p_password,_password)
  
    _username = p_username
    _password = p_password
    
    if (len(_username) > 0) and (len(_password) > 0):
	logging.info('username is "%s", password is known and assumed to be valid.' % (_username))
	try:
	    from pyax_code.context import getSalesForceContext
	    
	    _ctx = getSalesForceContext()
	    if (_isStaging):
		_srvs = _ctx.get__login_servers()
		print '_srvs=%s' % str(_srvs)
		if (_srvs.has_key('production')) and (_srvs.has_key('sandbox')):
		    _ctx.login_endpoint = _ctx.login_endpoint.replace(_srvs['production'],_srvs['sandbox'])
		print '_ctx.login_endpoint=%s' % str(_ctx.login_endpoint)
	    try:
		sfdc = Connection.connect(_username, _password, context=_ctx)
	    except Exception, details:
		exc_info = sys.exc_info()
		info_string = '\n'.join(traceback.format_exception(*exc_info))
		print >>sys.stderr, '(%s) :: "%s". %s' % (misc.funcName(),str(details),info_string)
		sfdc = None
		
	    logging.info('sfdc=%s' % str(sfdc))
	    if (sfdc is not None):
		logging.info('sfdc.endpoint=%s' % str(sfdc.endpoint))
		
	    if (sfdc):
		process(sfdc)
	except Exception, details:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    print >>sys.stderr, '(%s) :: "%s". %s' % (misc.funcName(),str(details),info_string)

if (__name__ == '__main__'):
    print 'sys.version=[%s]' % sys.version
    v = _utils.getFloatVersionNumber()
    if (v >= 2.51):
	if (not _isBeingDebugged):
	    from vyperlogix.handlers.ExceptionHandler import *
	    excp = ExceptionHandler()
	    excp.callback = exception_callback
    
	from vyperlogix.misc._psyco import *
	importPsycoIfPossible(func=main,isVerbose=True)
    
	__folder = os.path.dirname(sys.argv[0])
	_folderPath = __folder

	main()
