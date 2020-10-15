import wx
from wx.lib.wordwrap import wordwrap

import string

import os, sys
import time
import traceback

from vyperlogix import oodb

from vyperlogix.hash import lists

from vyperlogix.daemon.daemon import Log

from vyperlogix import misc
from vyperlogix.misc import _utils
from vyperlogix.lists.ListWrapper import ListWrapper
from vyperlogix.misc import threadpool

from vyperlogix.misc import ObjectTypeName

from vyperlogix.sf.hostify import hostify

from vyperlogix.parsers.CSV import CSV

from vyperlogix.wx.PopUpDialog import wx_PopUp_Dialog

import utils

__competitors_list_ = '''
 1. Email greater than  
 2. Email does not contain magma 
 3. Email Opt Out equals False 
 4. Email does not contain 0-in.com,acadcorp.com,accelchip.com,eesof.tm.agilent.com,aldec.com,ammocore.com,anasift.com,ansoft.com,apache-da.com,aplac.com,appwave.com,apriotech.com,aptix.com,artisan.com,athenads.com,atrenta.com,avertec.com,axiom-da.com,axysdesign.com,azuro.com,beachsolutions.com,berkeley-da.com,bindkey.com,blazedfm.com,bluepearlsoftware.com,bluespec.com,brion.com,cadence.com,calypto.com,carbondesignsytems.com,softwaredrivendesign.com,catalyticinc.com,celoxica.com,certess.com,chipmd.com,chipvision.com,ciranova.com,concept.de,coware.com,criticalblue.com,dafca.com,denalisoft.com,doulos.com,eecad.com,edxact.com,e-tools.com,dataxpress.com,elementcxi.com,esterel-technologies.com,eveteam.com,fintronic.com,fortedesignsystems.com,ftlsystems.com,genesystest.com,gigaic.com,ggtcorp.com,gradient-da.com,icmanage.com,icinergy.com,imperas.com,incentia.com,interrasystems.com,jasper-da.com,jedatechnologies.net,knowlent.com,legenddesign.com 
 5. Email does not contain libtech.com,logicvision.com,lorentzsolution.com,mri-nyc.com,mathworks.com,matrixone.com,mentor.com,mips.com,nangate.com,nannor.com,nascentric.com,novas.com,obsidiansoft.com,oea.com,orora.com,pdf.com,pontesolutions.com,prolificinc.com,pulsic.com,prosilog.com,pyxis.com,realintent.com,reshape.com,sagantec.com,sandwork.com,sequencedesign.com,sierrada.com,sigmac.com,sigrity.com,sicanvas.com,siliconds.com,sidimensions.com,silvaco.com,softjin.com,spiratech.com,sd.com,synappscorp.com,synchronicity.com,synfora.com,synopsys.com,synplicity.com,syntest.com,syntricity.com,takumi-tech.com,tharas.com,tenison.com,tensilica.com,terasystems.com,transeda.com,tuscanyda.com,vastsystems.com,verific.com,verisity.com,viragelogic.com,virtual-silicon.com,xpedion.com,yxi.com,zenasis.com 
 6. Last Name does not contain x-,-x 
'''
_symbol_competitors_fname_ = 'competitors.txt'

is_checkbox_value_true = lambda value:str(value).lower() in ['true','1','yes','ok']

_info_Copyright = "(c). Copyright %s, Magma Design Automation" % (_utils.timeStampLocalTime(format=_utils.formatDate_YYYY()))

_info_site_address = 'www.moltenmagma.com'

__copyright__ = """[**], All Rights Reserved.

THE AUTHOR MAGMA DESIGN AUTOMATION DISCLAIMS ALL WARRANTIES WITH REGARD TO
THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS, IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL,
INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
WITH THE USE OR PERFORMANCE OF THIS SOFTWARE !

USE AT YOUR OWN RISK."""

__copyright__ = __copyright__.replace('[**]',_info_Copyright)

_developers = ["Ray C Horn", "Stan Fisher", "Michael Shahamatdoust"]
_writers = []
_artists = []
_translators = []

__ChangeLog__ = """
[*2a*]
(**) Version 1.2.0:
Working to make the data extraction process run in the background via the Progress Dialog.
[*2b*]

[*2a*]
Version 1.1.1:
Working to abstract-out the processing model to allow a command-line version to be created without incurring maintenance issues across versions.
[*2b*]

[*2a*]
Version 1.1.0:
Now the Contacts are filtered based on the Magma Competitors List found in SalesForce.
[*2b*]

[*2a*]
Version 1.0.1:
Now Account Contacts rather than Account Owner Contacts are being retrieved.
[*2b*]

[*2a*]
Version 1.0.0:
Initial version.
[*2b*]
"""

s = [l for l in __ChangeLog__.split('\n') if (l.find('(**) ') > -1)]
if (len(s) > 0):
    __version__ = s[0].split(':')[0].split()[-1]
else:
    __version__ = 'UNKNOWN'

s_productName = 'Current Assets'
assert __version__ != 'UNKNOWN', 'Oops, cannot determine the current version number for "%s".' % (s_productName)
__productName__ = '%s v%s' % (s_productName,__version__)

__ChangeLog__ = __ChangeLog__.replace('[*2a*]','%s %s %s' % ('='*5,'Begin','='*5)).replace('[*2b*]','%s %s   %s' % ('='*5,'End','='*5))

_smtp_server_address = 'mailhost.moltenmagma.com:25'

_info_root_folder = 'c:\\'
wildcard_csv = "CSV File (*.csv)|*.csv"

_symbol_data_cleaned_fname = 'data_cleaned.csv'

_symbol_username = 'username'
_symbol_server_end_point = 'server_end_point'
_symbol_specific_end_point = 'specific_end_point'

l_domain_names = ['.moltenmagma.com']
l_domains = ['magma']
l_domain_users = [r'magma\rhorn']

from vyperlogix.products import data as products_data
_data_path_prefix = products_data._data_path_prefix

dbx_name = lambda name:oodb.dbx_name(name,_data_path)

_csv_model = CSV()

_isRunning = True

_thread_Q = threadpool.ThreadQueue(500)

ID_ICON_TIMER = wx.NewId()

def is_running_securely():
    from vyperlogix.win import computerSystem
    s = computerSystem.getComputerSystemSmartly()
    return s.UserName.lower().split('\\')[0] in l_domains

class MyTaskBarIcon(wx.TaskBarIcon):
    def __init__(self, frame):
        wx.TaskBarIcon.__init__(self)
        self.frame = frame
        self.SetIconBar()

        self.Bind(wx.EVT_MENU, self.OnTaskBarClose, id=4)
	
    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(4, 'Exit')
        return menu

    def OnTaskBarClose(self, event):
        self.frame.Close()

    def SetIconBar(self):
        '''Sets the icon bar hover text...'''
	import salesforce_icon2
	self.SetIcon(wx.IconFromBitmap(salesforce_icon2.getsalesforce_icon2Bitmap()))

_processing_list = []

_child_process_pid = -1

def _appendText(log,x):
    try:
	log.AppendText(x+'\n')
	print >>sys.stdout, x
    except Exception, details:
	_details = _utils.formattedException(details)
	print >>sys.stderr, _details

def appendText(log,x):
    wx.CallAfter(_appendText,log,x)

@threadpool.threadify(_thread_Q)
def backgroundProcess(self):
    try:
	self.backgroundProcess(self)
    except Exception, details:
	_details = _utils.formattedException(details=details)
	print >>sys.stdout, _details
	print >>sys.stderr, _details
	try:
	    wx_PopUp_Dialog(parent=self.child_frame,msg=_details,title='ERROR',styles=wx.ICON_INFORMATION | wx.CANCEL)
	except:
	    pass
    
@threadpool.threadify(_thread_Q)
def backgroundFilterProcess(self,fname,master_list):
    if (os.path.exists(fname)):
	try:
	    csv_model = CSV(filename=fname)
	    self.number = 100 # signal the elapsed read-out to begin working...
	    self.count = 1 # signal the elapsed read-out to begin working...
	    rows = csv_model.rowsAsRecords()
	    self.number = len(rows)
	    self.append_to_message_Q('There are %d rows in the selected .CSV.' % (self.number))
	    count = self.count = 0
	    _filtered_records = []
	    for rec in rows:
		email_domain = rec['Email'].split('@')[-1]
		if (email_domain.lower() not in master_list):
		    _filtered_records.append(rec)
		count += 1
		self.count = count
	    filtered_fname = os.sep.join([_log_path,'data_filtered.csv'])
	    info_string = CSV.write_as_csv(filtered_fname,_filtered_records)
	    if (len(info_string) > 0):
		self.append_to_message_Q('%s :: %s-->%s.' % (ObjectTypeName.objectSignature(self),filtered_fname,info_string))
	except Exception, details:
	    _details = _utils.formattedException(details=details)
	    print >>sys.stdout, _details
	    print >>sys.stderr, _details
	    wx_PopUp_Dialog(parent=self.child_frame,msg=_details,title='ERROR',styles=wx.ICON_ERROR | wx.CANCEL)
    else:
	wx_PopUp_Dialog(parent=self.child_frame,msg='Cannot locate the file "%s" so cannot proceed.' % (fname),title='WARNING',styles=wx.ICON_WARNING | wx.CANCEL)

from vyperlogix.mixins.LastError import LastErrorMixin
from vyperlogix.mixins.magma.CurrentAssetsProcess_mixin import CurrentAssetsProcessMixin
from vyperlogix.wx.mixins import ProgressDialogMixin
from vyperlogix.wx.mixins import MessageQ_Mixin
from vyperlogix.wx.mixins import SalesForceLogin_Mixin
from vyperlogix.wx.mixins import ChangeLogDialog_Mixin

from vyperlogix.wx.logger import wxLog

class MainFrame(wx.App, LastErrorMixin, CurrentAssetsProcessMixin, ProgressDialogMixin, MessageQ_Mixin, SalesForceLogin_Mixin, ChangeLogDialog_Mixin):
    def OnInit(self):
	self.ProgressDialogMixin_init()
	self.MessageQ_Mixin_init()
	self.CurrentAssetsProcessMixin_init()
	self._csv_model = _csv_model
	self._log_path = _log_path
	
	import CurrentAssets_Dialog
	self.__child_frame = CurrentAssets_Dialog.Dialog(None, title=__productName__, onProcess_callback=self.onProcess, on_init_callback=self.onInitDialog, onSubmitCompanyName_callback=self.onSubmitCompanyName, removeCompanyName_callback=self.onRemoveCompanyName, onToggleLog_callback=self.onToggleLog)
        self.__child_frame.Center(wx.BOTH)
        self.__child_frame.Show(True)
        self.SetTopWindow(self.__child_frame)
	
	self.log = wxLog(self.__child_frame.textboxLog)
	
        self.__child_frame.__taskbar_icon = MyTaskBarIcon(self)
        self.__child_frame.Centre()
	
	self.create_login_dialog(self.__child_frame,callback_onProcess=self.onProcess_LoginDialog,callback_onClose=self.OnClose_LoginDialog)
	
	import salesforce_icon2
	self.__child_frame.SetIcon(wx.IconFromBitmap(salesforce_icon2.getsalesforce_icon2Bitmap()))
	
	from vyperlogix.wx import CustomStatusBar

        self.statusBar = CustomStatusBar.CustomStatusBar(self.__child_frame, None)
        self.__child_frame.SetStatusBar(self.statusBar)
        self.statusBar.SetStatusWidths([-4, -1, -4])
	
        # Menu Bar
        self.top_frame_menubar = wx.MenuBar()
        self.file_menu_item = wx.Menu()
        self.exit_menu_item = wx.MenuItem(self.file_menu_item, wx.NewId(), "Exit", "", wx.ITEM_NORMAL)
	
        self.file_menu_item.AppendItem(self.exit_menu_item)
        self.top_frame_menubar.Append(self.file_menu_item, "File")
	
        self.help_menu_item = wx.Menu()
        self.about_menu_item = wx.MenuItem(self.help_menu_item, wx.NewId(), "About", "", wx.ITEM_NORMAL)
        self.help_menu_item.AppendItem(self.about_menu_item)
        self.changelog_menu_item = wx.MenuItem(self.help_menu_item, wx.NewId(), "Change Log", "", wx.ITEM_NORMAL)
        self.help_menu_item.AppendItem(self.changelog_menu_item)
        self.top_frame_menubar.Append(self.help_menu_item, "Help")

        self.__child_frame.SetMenuBar(self.top_frame_menubar)
        # Menu Bar end
	
	self.ChangeLog = __ChangeLog__
	self.ChangeLog_title = s_productName

        self.Bind(wx.EVT_MENU, self.OnClose, self.exit_menu_item)
        self.Bind(wx.EVT_MENU, self.onAbout, self.about_menu_item)

	self.ChangeLog_binding = self.changelog_menu_item

	self.__child_frame.Bind(wx.EVT_CLOSE, self.OnClose)
	
	self.__isAppClosed = False
	
	self.__competitors_list = []

	try:
	    self.__cpanel
	except NameError:
	    self.__cpanel = None
	
        self.__contacts__ = []
	
	if (not _utils._isComputerAllowed) or (not _is_running_securely):
	    info_string = 'Sorry but you cannot use this program at this time due to Security Concerns.\nPlease try back later from safely behind the Magma Firewall as a user on the Magma domain.'
	    print >>sys.stderr, info_string
	    wx_PopUp_Dialog(parent=self.__child_frame,msg=info_string,title='USER ERROR',styles=wx.ICON_ERROR)
	    self._OnClose()
	else:
	    self.init_salesforce()
	    self.enable_ifPossible()
	    self.__child_frame.Disable()
	return True
    
    def appendText(self,msg):
	appendText(self.__child_frame.textboxLog,msg)
	
    def onInitDialog(self,panel):
	self.__cpanel = panel
	panel.append_all_to_lbList([])
	
    def onRemoveCompanyName(self,values,names):
	from vyperlogix.sf.sf import SalesForceQuery
	sfQuery = SalesForceQuery(self.__login_dialog__.sf_login_model)
	from vyperlogix.sf.magma.competitors import SalesForceMagmaCompetitors
	competitors = SalesForceMagmaCompetitors(sfQuery)
	info_string = competitors.deleteCompetitorsByName(names)
	if (len(info_string) > 0):
	    appendText(self.__child_frame.textboxLog,info_string)
	self.populateCompetitorsList()

    def onSubmitCompanyName(self,value):
	from vyperlogix.sf.sf import SalesForceQuery
	sfQuery = SalesForceQuery(self.__login_dialog__.sf_login_model)
	from vyperlogix.sf.magma.competitors import SalesForceMagmaCompetitors
	competitors = SalesForceMagmaCompetitors(sfQuery)
	d_data = {'Company_Name__c':value.lower()}
	info_string = competitors.newCompetitor(d_data)
	if (len(info_string) > 0):
	    appendText(self.__child_frame.textboxLog,info_string)
	self.populateCompetitorsList()

    def child_frame():
        doc = "child_frame"
        def fget(self):
            return self.__child_frame
        return locals()
    child_frame = property(**child_frame())
    
    def onAbout(self, event):
	import salesforce_icon2

        info = wx.AboutDialogInfo()
        info.Name = s_productName
        info.Version = __version__
        info.Copyright = _info_Copyright
        info.Description = wordwrap(
            "\"%s\" is a software program that Imports Leads with Leads Scoring into SalesForce using the Apex API and must be executed from behind the Firewall using a specific domain for security purposes. " % (__productName__),
            350, wx.ClientDC(self.__child_frame))
        info.WebSite = ("http://%s" % (_info_site_address), "%s Home Page" % (__productName__))

        info.License = wordwrap(__copyright__, 700, wx.ClientDC(self.__child_frame))

	info.SetIcon(wx.IconFromBitmap(salesforce_icon2.getsalesforce_icon2Bitmap()))
	
	for n in _developers:
	    info.AddDeveloper(n)
	for n in _writers:
	    info.AddDocWriter(n)
	for n in _artists:
	    info.AddArtist(n)
	for n in _translators:
	    info.AddTranslator(n)
        
        wx.AboutBox(info)

    def hideLog(self):
	self.__child_frame.textboxLog.Hide()
	self.__child_frame.btnToggleLog.SetLabel('Show %s' % (self.__child_frame.btnToggleLog.GetLabel().split()[-1]))
	    
    def showLog(self):
	self.__child_frame.textboxLog.Show()
	self.__child_frame.btnToggleLog.SetLabel('Hide %s' % (self.__child_frame.btnToggleLog.GetLabel().split()[-1]))

    def onToggleLog(self):
	if (self.__child_frame.textboxLog.IsShown()):
	    self.hideLog()
	else:
	    self.showLog()
	    
    @threadpool.threadify(_thread_Q)
    def doAfterExtractionProcessCompleted(self):
	self.__child_frame.btnProcess.Enable()
	self._doAfterExtractionProcessCompleted()

    def theExtractionProcessCompleted(self):
	info_string = '''The data has been extracted. Enjoy !'''
	wx_PopUp_Dialog(parent=self.__child_frame,msg=info_string,title='INFORMATION',styles=wx.ICON_INFORMATION | wx.CANCEL)
    
    def doAfterProcessCompleted(self):
	self.startProgressDialog(self.__child_frame,title='Saving Current Assets Contacts',callback_progressDialog_updated=self.process_message_Q,callback_onProcessingDone=self.theExtractionProcessCompleted,callback_timer_end_condition=self.isMessageQ_Empty)
	
	self.doAfterExtractionProcessCompleted()
    
    def onProcess(self):
	self.__child_frame.btnProcess.Disable()
	self.showLog()

	self.startProgressDialog(self.__child_frame,title='Processing Current Assets Contacts',callback_progressDialog_updated=self.process_message_Q,callback_onProcessingDone=self.doAfterProcessCompleted,callback_timer_end_condition=self.isMessageQ_Empty)
	
	isError = False
	self.__competitors_list = self.competitors_list
	try:
	    if (len(self.last_error) > 0):
		isError = True
		print >>sys.stderr, self.last_error
		wx_PopUp_Dialog(parent=self.__child_frame,msg=self.last_error,title='WARNING',styles=wx.ICON_WARNING | wx.CANCEL)
	except Exception, details:
	    info_string = _utils.formattedException(details=details)
	    print >>sys.stderr, info_string
	    wx_PopUp_Dialog(parent=self.__child_frame,msg=info_string,title='ERROR',styles=wx.ICON_ERROR | wx.CANCEL)
	if (not isError):
	    backgroundProcess(self)
    
    def _onProcessCompleted(self):
	self.enable_ifPossible()
	
    def onProcessCompleted(self, runtime):
	self._onProcessCompleted()
	
    def _OnClose(self):
	global _isRunning
	_isRunning = False
	try:
	    if (self.__login_dialog__):
		self.__login_dialog__.Destroy()
		del self.__login_dialog__
	except AttributeError:
	    pass
        self.__child_frame.__taskbar_icon.Destroy()
	self.__child_frame.Destroy()
	del self.__child_frame
	self.__isAppClosed = True
	
    def OnClose(self, event):
	self._OnClose()
	
    def OnExit(self):
	if (not self.__isAppClosed):
	    self._OnClose()
	del self
	_thread_Q.join()
	if (not _isBeingDebugged):
	    sys.stdout.close()
	sys.stderr.close()
	sys.exit()
	
    def Close(self):
	self.OnExit()
	
    def IsShown(self):
	return self.__child_frame.IsShown()
    
    def Show(self):
	self.__child_frame.Show()
    
    def Hide(self):
	self.__child_frame.Hide()

    def enable_ifPossible(self):
	self.__child_frame.btnProcess.Enable()
	
    def disable_ifPossible(self):
	self.__child_frame.btnProcess.Disable()
	
    def populateCompetitorsList(self):
	self.__cpanel.append_all_to_lbList(self._getCompetitorsList())
	
    def auto_populateCompetitorsList(self):
	master_list = [item.lower() if (not isinstance(item,tuple)) and (not isinstance(item,list)) else list(item)[0].lower() for item in self._getCompetitorsList()]
	fname = os.sep.join([_log_path,_symbol_competitors_fname_])
	if (os.path.exists(fname)):
	    lines = [l.strip() for l in _utils._readFileFrom(fname)]
	    items = []
	    final_items = []
	    for line in lines:
		some_items = line.split(',')
		items += some_items
		final_items += some_items
	    try:
		for item in items:
		    if (item not in master_list):
			self.onSubmitCompanyName(item)
			try:
			    i = final_items.index(item)
			    if (i > -1):
				del final_items[i]
			except:
			    pass
		    else:
			print >>sys.stdout, '%s :: Cannot submit "%s" again because it is already on the list.' % (ObjectTypeName.objectSignature(self),item)
	    finally:
		_utils.writeFileFrom(fname,','.join(final_items))
    
    def onProcess_LoginDialog(self):
	try:
	    self.sf_login_model = self.login_dialog.sf_login_model
	except Exception, details:
	    _details = _utils.formattedException(details)
	    print >>sys.stderr, _details
	    wx_PopUp_Dialog(parent=self.__child_frame,msg=_details,title='ERROR',styles=wx.ICON_INFORMATION | wx.CANCEL)
	
	fn = oodb.dbx_name('%s.dbx' % (_utils.getProgramName()),_data_path)
	oodb.put_data(fn,_symbol_username,self.__login_dialog__.textUsername.GetValue(),fOut=sys.stderr)
	oodb.put_data(fn,_symbol_server_end_point,self.__login_dialog__.cbServerEndPoints.GetValue(),fOut=sys.stderr)
	oodb.put_data(fn,_symbol_specific_end_point,self.__login_dialog__.textEndPoint.GetValue(),fOut=sys.stderr)

	self.auto_populateCompetitorsList()
	self.populateCompetitorsList()
	
	self._close_LoginDialog()
	self.__child_frame.Enable()
	self.hideLog()
	self.showLog()
	self.enable_ifPossible()
	
    def OnClose_LoginDialog(self):
	isLoggedIn = self.login_dialog.sf_login_model.isLoggedIn
	print 'isLoggedIn is "%s".' % (isLoggedIn)
	if (not isLoggedIn):
	    self._OnClose()
	    
    def init_salesforce(self):
	try:
	    if (not self.__login_dialog__.sf_login_model.isLoggedIn):
		self.__child_frame.btnToggleLog.Hide()
		self.hideLog()
		self.__login_dialog__.Show()
		self.__login_dialog__.CenterOnParent()
		self.disable_ifPossible()
    
		fn = oodb.dbx_name('%s.dbx' % (_utils.getProgramName()),_data_path)
		_username = oodb.get_data(fn,_symbol_username,fOut=sys.stdout)
		if (_username is not None):
		    self.__login_dialog__.textUsername.SetValue(_username)
		_server_end_point = oodb.get_data(fn,_symbol_server_end_point,fOut=sys.stdout)
		if (_server_end_point is not None):
		    self.__login_dialog__.cbServerEndPoints.SetValue(_server_end_point)
		_specific_end_point = oodb.get_data(fn,_symbol_specific_end_point,fOut=sys.stdout)
		if (_specific_end_point is not None):
		    self.__login_dialog__.textEndPoint.SetValue(_specific_end_point)
		
		self.__login_dialog__.Bind(wx.EVT_CLOSE, self.OnClose_LoginDialog)
	except Exception, details:
	    _details = _utils.formattedException(details)
	    print >>sys.stderr, _details
	    wx_PopUp_Dialog(parent=self.__child_frame,msg=_details,title='ERROR',styles=wx.ICON_INFORMATION | wx.CANCEL)
	
def main(argv=None):
    global _data_path, _log_path
    
    if argv is None:
        argv = sys.argv

    _data_path = _utils.appDataFolder(prefix=_utils.getProgramName())
    _utils._makeDirs(_data_path)
    
    log_path = os.path.dirname(sys.argv[0])
    _log_path = _utils.safely_mkdir(fpath=log_path,dirname='logs')

    if (not _isBeingDebugged):
	_stdOut = open(os.sep.join([log_path,'stdout.txt']),'w')
	sys.stdout = Log(_stdOut)

    _stdErr = open(os.sep.join([log_path,'stderr.txt']),'w')
    sys.stderr = Log(_stdErr)

    try:
	app = MainFrame(0)
	app.MainLoop()
    except Exception, exception:
	type, value, stack = sys.exc_info()
	formattedBacktrace = ''.join(traceback.format_exception(type, value, stack, 5))
	info_string = 'An unexpected problem occurred:\n%s' % (formattedBacktrace)
	print >>sys.stderr, info_string
	try:
	    wx_PopUp_Dialog(parent=None,msg=info_string,title='FATAL ERROR',styles=wx.ICON_ERROR)
	except Exception, details:
	    print >>sys.stderr, _utils.formattedException(details=details)

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

    _is_running_securely = is_running_securely()
    _utils.isComputerAllowed(l_domain_names)

    main()
