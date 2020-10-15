
# Created with FarPy GUIE v0.5.5

import wx
import wx.calendar
import  wx.lib.mixins.listctrl  as  listmix

import sys
from vyperlogix.misc import _utils
from vyperlogix.misc import ObjectTypeName

from vyperlogix.hash import lists

import unicodedata

class Dialog(wx.Frame):	
    def __init__(self, parent, title='Leads Importer', onReset_callback=None, onProcess_callback=None, on_init_callback=None, on_cbLeadSourceDataTypes_list_callback=None, on_cbRecordTypes_list_callback=None, on_cbLeadTypes_list_callback=None, on_cbLeadSource_list_callback=None, on_cbLeadSourceDescr_list_callback=None, onToggleLog_callback=None,onAnalysis_callback=None):
        wx.Frame.__init__(self, parent, -1, title, wx.DefaultPosition, (700, 500), style=wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.RESIZE_BORDER | 0 | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX) # | wx.STAY_ON_TOP
        self.panel = wx.Panel(self, -1)
        self.__onProcess_callback = onProcess_callback
        self.__onReset_callback = onReset_callback
        self.__onToggleLog_callback = onToggleLog_callback

        self.btnProcess = wx.Button(self.panel, -1, 'Process', (24,216), (80, 30))
        self.btnProcess.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnProcess.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnProcess1 = wx.Button(self.panel, -1, 'Step 1', (24,216), (80, 30))
        self.btnProcess1.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnProcess1.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnProcess2 = wx.Button(self.panel, -1, 'Step 2', (24,216), (80, 30))
        self.btnProcess2.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnProcess2.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnProcess3 = wx.Button(self.panel, -1, 'Next Step', (24,216), (80, 30))
        self.btnProcess3.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnProcess3.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnToggleLog = wx.Button(self.panel, -1, 'Show Log', (24,216), (80, 30))
        self.btnToggleLog.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnToggleLog.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.labelCSVEmailAddressCol = wx.StaticText(self.panel, -1, 'CSV Email Address Column:', (16,171), (140, 18))
        self.labelCSVEmailAddressCol.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.labelCSVEmailAddressCol.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.cbCSVEmailAddressCol = wx.ComboBox(self.panel, -1, 'combobox for CSV Email Addrs Col', (164,166), (150, 21), [''], style=wx.CB_READONLY | wx.CB_SORT)
        self.cbCSVEmailAddressCol.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.cbCSVEmailAddressCol.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.cbCSVEmailAddressCol.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

	self.cbProcessMode_default = 'Choose a Processing Mode...'
	self.cbProcessMode_import_leads = 'Process Headcount'
	
        self.cbProcessMode = wx.ComboBox(self.panel, -1, 'Choose a Processing Mode...', (164,70), (300, 21), [self.cbProcessMode_default,self.cbProcessMode_import_leads], style=wx.CB_READONLY)
        self.cbProcessMode.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.cbProcessMode.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.cbProcessMode.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

	self.textboxLog = wx.TextCtrl(self.panel, -1, '', (144,192), size=(536, 269), style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.textboxLog.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.textboxLog.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.textboxLog.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.Bind(wx.EVT_BUTTON, self.onProcess, self.btnProcess)
        self.Bind(wx.EVT_BUTTON, self.onProcess, self.btnProcess1)
        self.Bind(wx.EVT_BUTTON, self.onProcess, self.btnProcess2)
        self.Bind(wx.EVT_BUTTON, self.onProcess, self.btnProcess3)
        self.Bind(wx.EVT_BUTTON, self.onToggleLog, self.btnToggleLog)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hboxes = []

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.labelCSVEmailAddressCol, 0, wx.RIGHT, 8)
        hboxes[-1].Add(self.cbCSVEmailAddressCol, 1)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))

        vbox2 = wx.BoxSizer(wx.VERTICAL)
        vbox2.Add(self.btnProcess, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox2.Add((-1, 1))
        vbox2.Add(self.btnProcess1, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox2.Add((-1, 1))
        vbox2.Add(self.btnProcess2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox2.Add((-1, 1))
        vbox2.Add(self.btnProcess3, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox2.Add((-1, 1))
        vbox2.Add(self.btnToggleLog, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox2.Add((-1, 1))
        hboxes[-1].Add(vbox2, 1)

        hboxes[-1].Add(self.textboxLog, 0, wx.LEFT, 8)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

        self.panel.SetSizer(vbox)

        x = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        y = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)

        self.SetSizeHints(350,300,x,y)
        vbox.Fit(self)

        if (callable(on_init_callback)):
            try:
                on_init_callback(self)
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def onProcess(self, event):
        if (callable(self.__onProcess_callback)):
            try:
                self.__onProcess_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def onToggleLog(self, event):
        if (callable(self.__onToggleLog_callback)):
            try:
                self.__onToggleLog_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def onAnalysis(self, event):
        if (callable(self.__onAnalysis_callback)):
            try:
                self.__onAnalysis_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def onReset(self, event):
        if (callable(self.__onReset_callback)):
            try:
                self.__onReset_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def Disable(self):
        for w in self.GetChildren():
            try:
                for ww in w.GetChildren():
                    try:
                        ww.Disable()
                    except Exception, details:
                        print >>sys.stderr, _utils.formattedException(details=details)
            except:
                try:
                    w.Disable()
                except Exception, details:
                    print >>sys.stderr, _utils.formattedException(details=details)

    def Enable(self):
        for w in self.GetChildren():
            try:
                for ww in w.GetChildren():
                    try:
                        ww.Enable()
                    except Exception, details:
                        print >>sys.stderr, _utils.formattedException(details=details)
            except:
                try:
                    w.Enable()
                except Exception, details:
                    print >>sys.stderr, _utils.formattedException(details=details)

    def onClose_LeadSourceDescr(self, event):
        try:
	    self.__editor_dialog__.Destroy()
	    del self.__editor_dialog__
	    self.Enable()
        except Exception, details:
            print >>sys.stdout, _utils.formattedException(details=details)

    def onAdd_EntitiesFromEditor(self,val,src_widget):
	try:
	    s_edited = self.__d_edited_fields_via_popup[src_widget.Id]
	    if (self.labelLeadSourceDescr.GetLabelText().find(s_edited) > -1):
		# BEGIN: It does not seem possible to change or update the metadata via Apex and pyax...
		l = self.__leads__
		picks = l.d_LeadSourceData__c.metadata['fields']['Description__c']['picklistValues']
		d = {'active':True,'defaultValue':False,'label':val,'value':val}
		picks[val] = d
		# END!  It does not seem possible to change or update the metadata via Apex and pyax...
		pass
        except Exception, details:
            print >>sys.stdout, _utils.formattedException(details=details)
    
    def onRemove_EntitiesFromEditor(self,sels,src_widget):
	try:
	    s_edited = self.__d_edited_fields_via_popup[src_widget.Id]
	    if (self.labelLeadSourceDescr.GetLabelText().find(s_edited) > -1):
		pass
        except Exception, details:
            print >>sys.stdout, _utils.formattedException(details=details)
    
    def onEditLeadSourceDescr(self, event):
        try:
	    self.Disable()
	    self.__edited_widget_label = event.EventObject.GetLabelText().split(':')[0]
	    self.__editor_dialog__ = EntitiesEditorDialog(self, 'Editing %s' % (self.__edited_widget_label), src_widget=self.__d_editable_fields_via_popup[self.__edited_widget_label], callback_onAdd=self.onAdd_EntitiesFromEditor, callback_onRemove=self.onRemove_EntitiesFromEditor)
	    self.__editor_dialog__.Show()
	    self.__editor_dialog__.CenterOnParent()
	    self.__editor_dialog__.Bind(wx.EVT_CLOSE, self.onClose_LeadSourceDescr)
        except Exception, details:
            print >>sys.stdout, _utils.formattedException(details=details)

class ChangeLogDialog(wx.Dialog):	
    def __init__(self, parent, title='Change Log'):
        wx.Dialog.__init__(self, parent, -1, title, wx.DefaultPosition, (700, 500), style=wx.CLOSE_BOX | wx.CAPTION | wx.SIMPLE_BORDER | wx.FRAME_NO_TASKBAR | wx.SYSTEM_MENU)
        self.panel = wx.Panel(self, -1)

        self.tbChangeLog = wx.TextCtrl(self.panel, -1, 'textbox', (0,0), size=(670, 420),style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.tbChangeLog.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.tbChangeLog.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.tbChangeLog.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnClose = wx.Button(self.panel, -1, 'Close', (0,24), (75, 23))
        self.btnClose.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnClose.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        import script_16x16
        self.SetIcon(wx.IconFromBitmap(script_16x16.getscript_16x16Bitmap()))

        self.Bind(wx.EVT_BUTTON, self.OnClose, self.btnClose)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hboxes = []

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.tbChangeLog, 0, wx.EXPAND, 8)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.btnClose, 0, wx.EXPAND, 8)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

        self.panel.SetSizer(vbox)

        x = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        y = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
        
        self.SetSizeHints(700,500,x,y)
        vbox.Fit(self)

    def OnClose(self, event):
	self.Destroy()
	del self

class QAMonitorDialog(wx.Dialog):	
    def __init__(self, parent, title='Processing', logger=None):
	style=wx.CAPTION | wx.FRAME_NO_TASKBAR | wx.SIMPLE_BORDER #  | wx.RESIZE_BORDER
        wx.Dialog.__init__(self, parent, -1, title, wx.DefaultPosition, (700, 500), style=style)
        self.panel = wx.Panel(self, -1)
	
	self.__logger__ = logger
	
	self.__allow_cancel__ = (style & (wx.CLOSE_BOX | wx.SYSTEM_MENU)) != 0
	self.__email_to_index__ = lists.HashedFuzzyLists()
	self.__email_to_index_copy__ = lists.HashedFuzzyLists()

        self.lbMonitor = NewListCtrl(self.panel, 
                                    wx.NewId(),
                                    size=(500,420),
                                    style=wx.LC_REPORT 
                                    | wx.BORDER_NONE
                                    | wx.LC_SORT_ASCENDING
                                    | wx.LC_SINGLE_SEL
                                    )

        self.lbMonitor.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.lbMonitor.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.lbMonitor.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.lbMonitor.InsertColumn(0, "EMAIL")
        self.lbMonitor.InsertColumn(1, "STATUS")
        self.lbMonitor.InsertColumn(1, "SCORED")
        self.lbMonitor.InsertColumn(1, "VALIDATED")

	if (self.allow_cancel):
	    self.btnClose = wx.Button(self.panel, -1, 'Close', (0,24), (75, 23))
	    self.btnClose.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
	    self.btnClose.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        import runsoftware_16x16
        self.SetIcon(wx.IconFromBitmap(runsoftware_16x16.getrunsoftware_16x16Bitmap()))

	if (self.allow_cancel):
	    self.Bind(wx.EVT_BUTTON, self.OnClose, self.btnClose)
	    self.Bind(wx.EVT_CLOSE, self.OnClose)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hboxes = []

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.lbMonitor, 0, wx.EXPAND, 8)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

	if (self.allow_cancel):
	    hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
	    hboxes[-1].Add(self.btnClose, 0, wx.EXPAND, 8)
	    vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
	    vbox.Add((-1, 1))

        self.panel.SetSizer(vbox)

        x = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        y = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
        
        self.SetSizeHints(700,500,x,y)
        vbox.Fit(self)

    def log(self, msg):
	if (callable(self.__logger__)):
	    try:
		self.__logger__(msg)
	    except Exception, details:
		info_string = _utils.formattedException(details=details)
		print info_string
    
    def allow_cancel():
        doc = "allow_cancel"
        def fget(self):
            return self.__allow_cancel__
        def fset(self, allow_cancel):
	    allow_cancel = allow_cancel if (isinstance(allow_cancel,bool)) else False
            self.__allow_cancel__ = allow_cancel
        return locals()
    
    allow_cancel = property(**allow_cancel())
    
    def append_to_lbMonitor(self, data):
	'''data is a tuple that contains one element for each column to be displayed'''
	n = self.lbMonitor.GetItemCount()
	index = self.lbMonitor.InsertStringItem(n, '')
	l_data = list(data)
	self.__email_to_index__[l_data[0]] = n
	self.__email_to_index_copy__[l_data[0]] = n
	for i in xrange(0,len(l_data)):
	    self.lbMonitor.SetStringItem(index,i,l_data[i])
	    self.lbMonitor.SetColumnWidth(i, wx.LIST_AUTOSIZE)
	self.lbMonitor.SetItemData(index, n+1)
        #self.lbMonitor.SortItems(self.sortCenterItems)

    def append_all_to_lbMonitor(self, l_data):
	'''l_data is a list of tuples that contains one element for each column to be displayed'''
	for t in l_data:
	    self.log('(append_all_to_lbMonitor) :: "%s".' % (str(t)))
	    self.append_to_lbMonitor(t)
	    
    def percentage_completed(self):
	length_0 = self.__email_to_index__.length()
	length_1 = self.__email_to_index_copy__.length()
	num_yes = length_0 - length_1
        n = self.lbMonitor.GetItemCount()
	nn = 0
	for k,v in self.__email_to_index__.iteritems():
	    nn += len(v)
	assert n == nn, '%s :: Oops, something wrong with the way the items are being counted, expected n to be "%d" but nn is "%d".' % (ObjectTypeName.objectSignature(self),n,nn)
	p = float(num_yes)/(float(n))*100.0
	print '%s :: num_yes is "%d", length_0 is "%d", length_1 is "%d", n is "%d", nn is "%d", p is "%3.0f".' % (ObjectTypeName.objectSignature(self),num_yes,length_0,length_1,n,nn,p)
	return p

    def update_lbMonitor_item(self,data):
	'''Make sure to handle all the possible repeats that may exist because we are allowing repeats.'''
	l_data = list(data)
	_index = self.__email_to_index_copy__[l_data[0]]
	if (_index is not None):
	    index = _index.pop()
	    for i in xrange(0,len(l_data)):
		try:
		    self.lbMonitor.SetStringItem(index,i,l_data[i])
		    self.log('%s :: "%s".' % (ObjectTypeName.objectSignature(self),l_data[i]))
		except Exception, details:
		    info_string = _utils.formattedException(details=details)
		    self.log(info_string)
		    
		self.lbMonitor.SetColumnWidth(i, wx.LIST_AUTOSIZE)
	    if (len(_index) == 0):
		del self.__email_to_index_copy__[l_data[0]]
	    else:
		del self.__email_to_index_copy__[l_data[0]]
		for i in _index:
		    self.__email_to_index_copy__[l_data[0]] = i
	    pc = self.percentage_completed()
	    self.log('(update_lbMonitor_item) :: email is "%s", index is "%s", %2.0f%%.' % (l_data[0],index,pc))
	    print self.__email_to_index_copy__.prettyPrint(title='%s' % (ObjectTypeName.objectSignature(self)))
	else:
	    self.log('(update_lbMonitor_item) :: Unable to locate "%s" in the list of Leads.  This is a processing error !  Doh !' % (l_data[0]))
	    
    def report_email_to_indexes(self):
	print self.__email_to_index__.prettyPrint(title='%s' % (ObjectTypeName.objectSignature(self)))
	
    def _OnClose(self):
	self.Destroy()
	del self

    def OnClose(self, event):
	if (self.allow_cancel):
	    self._OnClose()

class NewListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

