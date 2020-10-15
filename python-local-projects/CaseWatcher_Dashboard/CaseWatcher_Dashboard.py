import wx
import string

import os, sys
import time
import traceback

from vyperlogix import oodb

from vyperlogix.hash import lists

from vyperlogix.misc import _utils
from vyperlogix.lists.ListWrapper import ListWrapper
from vyperlogix.misc import threadpool

from vyperlogix.mail import message
from vyperlogix.mail import mailServer

from vyperlogix.misc import ObjectTypeName

from vyperlogix.ssh.sshUtils import SSHConnection

from vyperlogix.products import data as products_data

from vyperlogix.wx.Error_Handlers import WxStderr

l_test_computers = ['rhorn-lap.ad.moltenmagma.com']

__version__ = '1.0'
__productName__ = 'CaseWatcher Dashboard v%s' % (__version__)

_data_path_prefix = products_data._data_path_prefix

dbx_name = lambda name:oodb.dbx_name(name,_data_path)

__copyright__ = """\
(c). Copyright 1990-2008, Vyper Logix Corp., 

              All Rights Reserved.

Published under Creative Commons License 
(http://creativecommons.org/licenses/by-nc/3.0/) 
restricted to non-commercial educational use only., 

See also: http://www.VyperLogix.com and http://www.pypi.info for details.

THE AUTHOR VYPER LOGIX CORP DISCLAIMS ALL WARRANTIES WITH REGARD TO
THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !

USE AT YOUR OWN RISK.
"""

conn = None

_isRunning = True

_monitor_interval_secs = 60 * 1
_monitor_interval_ms = _monitor_interval_secs * 1000

l_monitor_interval_ms = ListWrapper([1000,_monitor_interval_ms])

_thread_Q = threadpool.ThreadQueue(10)

ID_ICON_TIMER = wx.NewId()

init_l_success = [1,2,3,4,5]
l_success = ListWrapper(init_l_success) # Begin looking like all is well with the world...
l_failures = ListWrapper([])

def init_lists():
    global l_success, l_failures
    l_success = ListWrapper(init_l_success) # Begin looking like all is well with the world...
    l_failures = ListWrapper([])

_email_FromAddress = 'molten-support@molten-magma.com'
_email_failure_reports_to = 'rhorn@molten-magma.com'

hasFailureReportEmailBeenSent = False
threshold_failures_count = 5

from vyperlogix.crypto import XTEAEncryption
from vyperlogix.products import keys as products_keys

_iv2 = XTEAEncryption.iv(os.path.splitext(os.path.basename(sys.argv[0]))[0])

@threadpool.threadify(_thread_Q)
def procify_initialization():
    global conn
    global mailserver
    
    if (_iv2 == 'CaseWatc'):
	_hostname = XTEAEncryption._decryptode('54343C65D8',_iv2)
	_username = XTEAEncryption._decryptode('5235377284',_iv2)
	_password = XTEAEncryption._decryptode('70383D6BAA317DD4',_iv2)
    
    mailserver = mailServer.GMailServer('','',server='tide2.moltenmagma.com:8025')
    try:
	conn = SSHConnection(hostname=_hostname,username=_username,password=_password,isLazy=True)
	print '(%s) :: conn is "%s".' % (_utils.funcName(),conn)
    except:
	conn = None

    if (conn is not None):
	procify_monitor_ssh()
    else:
	print >>sys.stderr, 'ERROR: Cannot get a connection to the "%s" host.' % (_hostname)
    
@threadpool.threadify(_thread_Q)
def sendEmailMessage(toAddress, subj, body, fromAddress=_email_FromAddress):
    from vyperlogix.misc import decodeUnicode
    
    _message = lambda reason:'Cannot perform email function for fromAddress of "%s", toAddress of "%s", subj of "%s" because %s.' % (fromAddress,toAddress,subj,reason)
    if (mailserver):
	try:
	    msg = message.Message(fromAddress, toAddress, decodeUnicode.ensureOnlyPrintableChars(decodeUnicode.decodeUnicode(body),mask='[]'), subj)
	    mailserver.sendEmail(msg)
	except:
	    exc_info = sys.exc_info()
	    info_string = '\n'.join(traceback.format_exception(*exc_info))
	    info_string = _message(info_string)
	    print >>sys.stderr, info_string
	    return False
    else:
	print >>sys.stderr, _message('there is no mailserver')
    
    return True
    
@threadpool.threadify(_thread_Q)
def procify_monitor_ssh():
    global l_success
    global hasFailureReportEmailBeenSent
    while (_isRunning):
        isSuccess = False
        conn.ssh_connect_client()
        if (conn.sftp is None):
            if (not hasFailureReportEmailBeenSent) and (len(l_failures) >= threshold_failures_count):
                print '(%s) Sending the email.' % (_utils.funcName())
		sendEmailMessage(_email_failure_reports_to, 'Server %s is down, please reboot.' % (conn.hostname.upper()), 'Cannot log into server %s, Please reboot as soon as possible.' % (conn.hostname.upper()))
                hasFailureReportEmailBeenSent = True
            l_failures.append(1)
            if (len(l_success) >= threshold_failures_count):
                l_success = ListWrapper([])
            if (len(l_success) > 0):
                l_success.pop()
        else:
	    fpath_pyDaemon_logs = '/var/log/CaseWatcher/pyDaemon/logs'
	    is_pyDaemon_installed = conn.exists(fpath_pyDaemon_logs)
	    print '(%s) :: is_pyDaemon_installed in %s (%s)' % (_utils.funcName(),fpath_pyDaemon_logs,is_pyDaemon_installed)
	    _files = conn.listdir(fpath_pyDaemon_logs)
	    has_pyDaemon_been_running = len(_files) > 0
	    print '(%s) :: has_pyDaemon_been_running (%s)' % (_utils.funcName(),has_pyDaemon_been_running)
	    
	    _console_files = ListWrapper([f for f in _files if (f.find('_console_') > -1)])
	    _log_files = ListWrapper([(f,_utils.getAsDateTimeStrFromTimeSeconds(conn.stat(conn.sep.join([fpath_pyDaemon_logs,f])).st_mtime)) for f in _files if (f.find('.log.') > -1)])
	    _log_files = ListWrapper([(f,_utils.getFromTimeStampForFileName(t),t) for f,t in _log_files])
	    
	    # _log_files happen at least once per hour so check it...
	    
	    s = set(_files)
	    s1 = set(_console_files + _log_files)
	    _s = s - s1
	    
	    x = len(_files) - (len(_console_files) + len(_log_files))
	    
	    d = lists.HashedLists()
	    for f in _console_files:
		t = f.split('_console_')[-1].split('.')[0]
		ts = _utils.getFromTimeStampForFileName(_utils.timeStampForFileName(t))
		d[ts] = f
	    sorted_console_files = ListWrapper(ListWrapper(d.keys()).sort())
	    latest_local_ts = _utils.localFromUTC(sorted_console_files[-1])
	    
	    now = _utils.getFromDateTimeStr(_utils.timeStampLocalTime())
	    
	    delta = now - latest_local_ts if (now > latest_local_ts) else latest_local_ts - now
	    delta_secs = _utils.timeDeltaAsSeconds(delta)
	    
	    d2 = lists.HashedLists()
	    for f,t,ts in _log_files:
		d2[t] = f
	    sorted_log_files = ListWrapper(ListWrapper(d2.keys()).sort())
	    latest_local_ts2 = sorted_log_files[-1]
	    
	    delta2 = now - latest_local_ts2 if (now > latest_local_ts2) else latest_local_ts2 - now
	    delta_secs2 = _utils.timeDeltaAsSeconds(delta2)

	    is_pyDaemon_logs_problem = (x != 2) or (not all([f in _s for f in ['pyMonit.log', 'pyMonit_init.log']]))
	    is_pyDaemon_console_running = (delta_secs <= _utils.seconds_per_hour)
	    is_pyDaemon_running = (not is_pyDaemon_logs_problem) and (is_pyDaemon_console_running) and (delta_secs2 <= _utils.seconds_per_hour)
	    
	    reason = ''
	    if (not is_pyDaemon_running):
		reason += '' if (not is_pyDaemon_logs_problem) else 'There is a problem with the way the pyDaemon Logs are being handled.'
		reason += '\n' if (len(reason) > 0) else ''
		reason += '' if (not is_pyDaemon_console_running) else 'There is a problem with the way the pyDaemon Console Logs are being handled - pyDaemon may not be running.'
		reason += '\n' if (len(reason) > 0) else ''
	    
	    isSuccess = True
            l_success.append(1)
            if (len(l_failures) > 0):
                l_failures.pop()
            conn.ssh_close()
        print '(%s) sFTP is "%s" or "%s".' % (_utils.funcName(),str(conn.sftp),'SUCCESS' if (isSuccess) else 'FAILURE')
	sleep_monitor_interval_secs = _monitor_interval_secs
	while (_isRunning) and (sleep_monitor_interval_secs > 0):
	    if (_isRunning):
		time.sleep(1)
		sleep_monitor_interval_secs -= 1
    print '(%s) Done !' % (_utils.funcName())

class IconBar:

    def __init__(self,l_off=[128,0,0],l_on=[255,0,0],r_off=[0,128,0],r_on=[0,255,0]):
        self.s_line = "\xff\xff\xff"+"\0"*45
        self.s_border = "\xff\xff\xff\0\0\0"
        self.s_point = "\0"*3
        self.__num_bars = threshold_failures_count
        self.sl_off = string.join(map(chr,l_off),'')*(self.num_bars+1)
        self.sl_on = string.join(map(chr,l_on),'')*(self.num_bars+1)
        self.sr_off = string.join(map(chr,r_off),'')*(self.num_bars+1)
        self.sr_on = string.join(map(chr,r_on),'')*(self.num_bars+1)

    def num_bars():
        doc = "number of bars"
        def fget(self):
            return self.__num_bars
        def fset(self, value):
            self.__num_bars = value
        return locals()
    num_bars = property(**num_bars())
    
    def Get(self,l,r):
        s=""+self.s_line
        for i in range(self.num_bars):
            if i<(self.num_bars-l):
                sl = self.sl_off
            else:
                sl = self.sl_on

            if i<(self.num_bars-r):
                sr = self.sr_off
            else:
                sr = self.sr_on

            s+=self.s_border+sl+self.s_point+sr+self.s_point
            s+=self.s_border+sl+self.s_point+sr+self.s_point
            s+=self.s_line

        image = wx.EmptyImage(16,16)
        image.SetData(s)

        bmp = image.ConvertToBitmap()
        bmp.SetMask(wx.Mask(bmp, wx.WHITE)) #sets the transparency colour to white 

        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(bmp)

        return icon

class MyTaskBarIcon(wx.TaskBarIcon):

    def __init__(self, frame):
        wx.TaskBarIcon.__init__(self)
        self.frame = frame
        self.IconBar = IconBar((127,0,0),(255,0,0),(0,127,0),(0,255,0))
        self.SetIconBar(len(l_failures),len(l_success))

        self.Bind(wx.EVT_MENU, self.OnTaskBarActivate, id=1)
        self.Bind(wx.EVT_MENU, self.OnTaskBarDeactivate, id=2)
        self.Bind(wx.EVT_MENU, self.OnTaskBarReset, id=3)
        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=4)
	
	self.SetIconTimer()
	
    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(1, 'Show')
        menu.Append(2, 'Hide')
        menu.Append(3, 'Reset')
        menu.Append(4, 'Exit')
        return menu

    def OnTaskBarReset(self, event):
	init_lists()
	self._refreshIcon()

    def OnTaskBarClose(self, event):
        self.frame.Close()

    def OnTaskBarActivate(self, event):
        if not self.frame.IsShown():
            self.frame.Show()

    def OnTaskBarDeactivate(self, event):
        if self.frame.IsShown():
            self.frame.Hide()

    def SetIconTimer(self):
        self.icon_timer = wx.Timer(self, ID_ICON_TIMER)
        wx.EVT_TIMER(self, ID_ICON_TIMER, self.refreshIcon)
        self.icon_timer.Start(l_monitor_interval_ms[0])

    def _refreshIcon(self):
        '''Refresh the icon bar with the current status of the monitor...'''
	t_success = len(l_success)
	t_failure = len(l_failures)
	t = t_failure + t_success
	p_success = 0.0
	p_failure = 0.0
	if (t > 0):
	    p_success = float(t_success / t)
	    p_failure = float(t_failure / t)
        self.SetIconBar(int(self.IconBar.num_bars * p_failure),int(self.IconBar.num_bars * p_success))
                
    def refreshIcon(self, event):
        '''Refresh the icon bar with the current status of the monitor...'''
        self._refreshIcon()
                
    def SetIconBar(self,num_failures,num_success):
        '''Sets the icon bar hover text...'''
        icon = self.IconBar.Get(num_failures,num_success)
	p_success = float(num_success / self.IconBar.num_bars) * 100.0
	p_failure = float(num_failures / self.IconBar.num_bars) * 100.0
	print '(%s) :: str(conn)=%s, l_monitor_interval_ms[0]=%s' % (ObjectTypeName.objectSignature(self),str(conn),l_monitor_interval_ms[0])
        self.SetIcon(icon, "%s\nFailures:%2.0f%%,Success:%2.0f%%\n%s"%(str(conn),p_failure,p_success,'EMail has been sent!' if (hasFailureReportEmailBeenSent) else ''))
	if (conn is not None) and (len(l_monitor_interval_ms) > 1):
	    del l_monitor_interval_ms[0]
	    self.icon_timer.Start(l_monitor_interval_ms[0])

class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, (-1, -1), (800, 600))
        self.__taskbar_icon = MyTaskBarIcon(self)
        self.Centre()

	import icon
	fname = icon.make_icon('icon2.ico')
	if (os.path.exists(fname)):
	    _icon = wx.Icon(fname, wx.BITMAP_TYPE_ICO)
	    self.SetIcon(_icon)
	else:
	    print >>sys.stderr, '(%s) :: Cannot locat the icon file "%s".' % (ObjectTypeName.objectSignature(self),fname)
	
	self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, event):
        self.__taskbar_icon.Destroy()
        self.Destroy()

class MainFrame(wx.App):
    def OnInit(self):
	frame = MyFrame(None, -1, __productName__)
        frame.Center(wx.BOTH)
        frame.Show(True) # Show the GUI when there is no data in the dbx file...
        self.SetTopWindow(frame)
	procify_initialization()
        return True

def main(argv=None):
    global _data_path
    
    if argv is None:
        argv = sys.argv

    init_lists()
    
    _data_path = _utils.appDataFolder(prefix=_data_path_prefix(_utils.getProgramName()))
    
    _utils._makeDirs(_data_path)
    
    cname = _utils.getComputerName().lower()
    if (cname in l_test_computers):
	# populate the dbx file with sample data only when running on misha's laptop or UNDEFINED3 otherwise not...
	pass

    sys.stderr = WxStderr() 
    try:
	app = MainFrame(0)
	app.MainLoop()
    except Exception, exception:
	# This handles exceptions before and after the MainLoop
	type, value, stack = sys.exc_info()
	formattedBacktrace = ''.join(traceback.format_exception(type, value, stack, 5))
	dlg = wx.MessageDialog(None, 'An unexpected problem occurred:\n%s' % (formattedBacktrace), 'Fatal Error',wx.CANCEL | wx.ICON_ERROR)
	dlg.ShowModal()
	dlg.Destroy()

from vyperlogix.decorators import onexit
@onexit.onexit
def onSysExit():
    global _isRunning
    _isRunning = False
    _thread_Q.join()
    #print >>sys.stdout, '(%s)' % (_utils.funcName())
    sys.exit(1)

def exception_callback(sections):
    _msg = 'EXCEPTION Causing Abend.\n%s' % '\n'.join(sections)
    print >>sys.stdout, _msg
    print >>sys.stderr, _msg
    sys.exit(1)

if __name__ == '__main__':
    _isBeingDebugged = _utils.isBeingDebugged
    
    if (not _isBeingDebugged):
	from vyperlogix.handlers.ExceptionHandler import *
	excp = ExceptionHandler()
	excp.callback = exception_callback

    from vyperlogix.misc._psyco import *
    importPsycoIfPossible(func=main,isVerbose=True)

    main()
