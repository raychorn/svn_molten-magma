import os, sys, traceback

import sfUtil_win32

from vyperlogix.misc import Args
from vyperlogix.misc import PrettyPrint

from vyperlogix.misc import _utils
from vyperlogix.misc import _psyco

from pyax_code.specific import CaseWatcher

_server_tide2 = ['tide2']
_server_river = ['river']
_available_servers = _server_tide2 + _server_river

def do_sftp(server,source,dest):
    _has_server_connection = False
    try:
	if (server in _server_tide2):
	    ros = sfUtil_win32.connectToTide2()
	elif (server in _server_river):
	    ros = sfUtil_win32.connectToRiver()
	else:
	    print >>sys.stderr, '(%s) :: Cannot connect to "%s".' % (_utils.funcName(),server)
	_has_server_connection = True
    except:
	exc_info = sys.exc_info()
	info_string = CaseWatcher.asMessage('\n'.join(traceback.format_exception(*exc_info)))
	print >>sys.stderr, info_string
    if (_has_server_connection) and (ros.transport):
	try:
	    cwd = ros.os_getcwd()
	    print 'cwd is "%s".' % (cwd)
	    if (ros.isSFTP):
		print 'SFTP "%s" to host as "%s".' % (source,dest)
		if (ros.os_path_exists(dest)):
		    ros.os_remove(dest)
		ros.sftp.put(source, dest)
	finally:
	    ros.close()

def main(server,source,dest):
    if (server in _available_servers):
	if (os.path.exists(source)):
	    do_sftp(server,source,dest)
	else:
	    print >>sys.stderr, '(%s) :: Source of "%s" does not apparently exist.' % (_utils.funcName(),source)
    else:
	print >>sys.stderr, '(%s) :: Server of "%s" is not one of the available servers %s.' % (_utils.funcName(),server,_available_servers)

if (__name__ == '__main__'):
    def ppArgs():
	pArgs = [(k,args[k]) for k in args.keys()]
	pPretty = PrettyPrint.PrettyPrint('Computer Name: %s' % (_utils.getComputerName().lower()),pArgs,True,' ... ')
	pPretty.pprint()

    args = {'--help':'show some help.',
	    '--verbose':'output more stuff.',
	    '--computer=?':'name the computer this command should run on.',
	    '--server=?':'name the server (tide2 or river).',
	    '--source=?':'name the source file path.',
	    '--dest=?':'name the dest file path.',
	    }
    _argsObj = Args.Args(args)

    if (len(sys.argv) == 1):
	ppArgs()
    else:
	_progName = _argsObj.programName
	_isVerbose = False
	try:
	    if _argsObj.booleans.has_key('isVerbose'):
		_isVerbose = _argsObj.booleans['isVerbose']
	except:
	    exc_info = sys.exc_info()
	    info_string = CaseWatcher.asMessage('\n'.join(traceback.format_exception(*exc_info)))
	    print >>sys.stderr, info_string
	    _isVerbose = False

	if (_isVerbose):
	    print '_argsObj=(%s)' % str(_argsObj)
	    
	_isHelp = False
	try:
	    if _argsObj.booleans.has_key('isHelp'):
		_isHelp = _argsObj.booleans['isHelp']
	except:
	    pass
	
	if (_isHelp):
	    ppArgs()
	
	_server = ''
	try:
	    if _argsObj.arguments.has_key('server'):
		__server = _argsObj.arguments['server']
		if (len(__server) > 0):
		    _server = __server
	except:
	    exc_info = sys.exc_info()
	    info_string = CaseWatcher.asMessage('\n'.join(traceback.format_exception(*exc_info)))
	    print >>sys.stderr, info_string
	    
	_computer = _utils.getComputerName().lower()
	try:
	    if _argsObj.arguments.has_key('computer'):
		__computer = _argsObj.arguments['computer']
		if (len(__computer) > 0):
		    _computer = __computer
	except:
	    exc_info = sys.exc_info()
	    info_string = CaseWatcher.asMessage('\n'.join(traceback.format_exception(*exc_info)))
	    print >>sys.stderr, info_string

	_source = ''
	try:
	    if _argsObj.arguments.has_key('source'):
		__source = _argsObj.arguments['source']
		if (len(__source) > 0):
		    _source = __source
	except:
	    exc_info = sys.exc_info()
	    info_string = CaseWatcher.asMessage('\n'.join(traceback.format_exception(*exc_info)))
	    print >>sys.stderr, info_string

   	_dest = ''
	try:
	    if _argsObj.arguments.has_key('dest'):
		__dest = _argsObj.arguments['dest']
		if (len(__dest) > 0):
		    _dest = __dest
	except:
	    exc_info = sys.exc_info()
	    info_string = CaseWatcher.asMessage('\n'.join(traceback.format_exception(*exc_info)))
	    print >>sys.stderr, info_string
 
	s_computer = _computer.lower()
	s_ComputerName = _utils.getComputerName().lower()
	if (s_computer == s_ComputerName):
	    _psyco.importPsycoIfPossible(main)
	    main(_server,_source,_dest)
	else:
	    print >>sys.stderr, 'Nothing to do because "%s" is not "%s".' % (s_computer,s_ComputerName)
	    
	