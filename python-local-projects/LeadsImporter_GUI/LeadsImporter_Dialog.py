
# Created with FarPy GUIE v0.5.5

import wx
import wx.calendar
import  wx.lib.mixins.listctrl  as  listmix

import sys
from vyperlogix.misc import _utils
from vyperlogix.misc import ObjectTypeName

from vyperlogix.hash import lists

import unicodedata

class EntityEditor:
    def __init__(self, parent, size):
        '''parent is a wx.panel instance.'''
	w = size.GetWidth()-80
        parent.tbName = wx.TextCtrl(parent, -1, '', (0,0), size=(w, 20), style=wx.TE_PROCESS_ENTER)
        parent.tbName.SetBackgroundColour(wx.Colour(255, 255, 255))
        parent.tbName.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        parent.tbName.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        parent.lbChoices = wx.ListBox(parent, -1, (0,16), (w, 350), ['+++'], style=wx.LB_SINGLE | wx.LB_SORT)
        parent.lbChoices.SetBackgroundColour(wx.Colour(255, 255, 255))
        parent.lbChoices.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        parent.lbChoices.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        
        parent.btnRemove = wx.Button(parent, -1, '>>', (w,24), (30, 23))
        parent.btnRemove.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        parent.btnRemove.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        parent.btnAdd = wx.Button(parent, -1, '(+)', (w,0), (30, 21))
        parent.btnAdd.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        parent.btnAdd.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        parent.btnAdd.SetToolTip(wx.ToolTip('Click this button to add the new entry to the existing list of entries.'))
        parent.btnRemove.SetToolTip(wx.ToolTip('Click this button to remove the selected entry from the existing list of entries.'))

        self.__vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)

        hbox.Add(parent.tbName, 0, wx.LEFT, 8)
        hbox.Add((5, -1))
        hbox.Add(parent.btnAdd, 0, wx.LEFT, 8)

        self.__vbox.Add(hbox, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        self.__vbox.Add((-1, 1))

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)

        hbox2.Add(parent.lbChoices, 0, wx.LEFT, 8)
        hbox2.Add((5, -1))
        hbox2.Add(parent.btnRemove, 0, wx.LEFT, 8)

        self.__vbox.Add(hbox2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        self.__vbox.Add((-1, 1))

    def vbox():
        doc = "vbox"
        def fget(self):
            return self.__vbox
        return locals()
    vbox = property(**vbox())
        
class EntitiesEditorDialog(wx.Dialog):	
    def __init__(self, parent, title, src_widget=None, callback_onAdd=None, callback_onRemove=None):
        wx.Dialog.__init__(self, parent, -1, title, wx.DefaultPosition, (300, 300), style=wx.SYSTEM_MENU | wx.CAPTION | wx.STAY_ON_TOP | wx.CLOSE_BOX) # | wx.RESIZE_BORDER | 0 | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX
        self.__panel = wx.Panel(self, -1)
	
	self.__src_widget = src_widget
	self.__callback_onAdd = callback_onAdd
	self.__callback_onRemove = callback_onRemove
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.SetSize((300,300))
        sz = self.GetClientSize()
	
        self.__panel.SetSizer(sizer)
        o = wx.BoxSizer(wx.HORIZONTAL)
        e = EntityEditor(self.__panel, sz)
	try:
	    self.__panel.lbChoices.Set(self.__src_widget.GetStrings())
        except Exception, details:
            print >>sys.stderr, _utils.formattedException(details=details)
        self.__panel.lbChoices.Bind(wx.EVT_LEFT_UP, self.onSelectedEntityItem)
        o.Add(e.vbox, 1, wx.GROW)
        self.SetSizer(o)

        self.__panel.btnAdd.Bind(wx.EVT_BUTTON, self.onAddButtonClicked)
        self.__panel.btnRemove.Bind(wx.EVT_BUTTON, self.onRemoveButtonClicked)
        self.__panel.tbName.Bind(wx.EVT_TEXT_ENTER, self.onAddButtonClicked)
	
        self.__panel.SetSize(sz)
        self.__panel.SetFocus()
	
    def onAddButtonClicked(self, event):
	val = self.__panel.tbName.GetValue()
	if (len(val) > 0):
	    if (callable(self.__callback_onAdd)):
		try:
		    self.__callback_onAdd(val,self.__src_widget)
		except Exception, details:
		    print >>sys.stderr, _utils.formattedException(details=details)
	    print '%s :: Clicked with "%s".' % (ObjectTypeName.objectSignature(self),val)
	else:
	    print '%s :: Nothing to add.' % (ObjectTypeName.objectSignature(self))

    def onRemoveButtonClicked(self, event):
	sels = self.__panel.lbChoices.GetSelections()
	if (len(sels) > 0):
	    if (callable(self.__callback_onRemove)):
		try:
		    self.__callback_onRemove(sels,self.__src_widget)
		except Exception, details:
		    print >>sys.stderr, _utils.formattedException(details=details)
	    print '%s :: Clicked with "%s".' % (ObjectTypeName.objectSignature(self),str(sels))
	else:
	    print '%s :: Nothing to remove.' % (ObjectTypeName.objectSignature(self))

    def onSelectedEntityItem(self, evt):
        chosen = self.__panel.lbChoices.HitTest(evt.GetPosition())
        if chosen == -1:
            chosen = None
        try:
            if (chosen is not None):
                self.__panel.lbChoices.Select(chosen,True)
        except Exception, details:
            print >>sys.stderr, _utils.formattedException(details=details)
        print >>sys.stdout, '%s :: chosen=%s' % (ObjectTypeName.objectSignature(self),chosen)

class Dialog(wx.Frame):	
    def __init__(self, parent, title='Leads Importer', onReset_callback=None, onProcess_callback=None, on_init_callback=None, on_cbLeadSourceDataTypes_list_callback=None, on_cbRecordTypes_list_callback=None, on_cbLeadTypes_list_callback=None, on_cbLeadSource_list_callback=None, on_cbLeadSourceDescr_list_callback=None, onToggleLog_callback=None,onAnalysis_callback=None, onProcessMode_callback=None, onLeadSourceDescr_callback=None):
        wx.Frame.__init__(self, parent, -1, title, wx.DefaultPosition, (700, 500), style=wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.RESIZE_BORDER | 0 | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX) # | wx.STAY_ON_TOP
        self.panel = wx.Panel(self, -1)
        self.__onProcess_callback = onProcess_callback
	self.__onProcessMode_callback = onProcessMode_callback
	self.__onLeadSourceDescr_callback = onLeadSourceDescr_callback
        self.__onReset_callback = onReset_callback
        self.__onToggleLog_callback = onToggleLog_callback

        self.cbLeadSourceDataTypes_list = ['']
        if (callable(on_cbLeadSourceDataTypes_list_callback)):
            try:
                self.cbLeadSourceDataTypes_list = on_cbLeadSourceDataTypes_list_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

        self.cbRecordTypes_list = ['']
        if (callable(on_cbRecordTypes_list_callback)):
            try:
                self.cbRecordTypes_list = on_cbRecordTypes_list_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

        self.cbLeadTypes_list = ['']
        if (callable(on_cbLeadTypes_list_callback)):
            try:
                self.cbLeadTypes_list = on_cbLeadTypes_list_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

        self.cbLeadSource_list = ['']
        if (callable(on_cbLeadSource_list_callback)):
            try:
                self.cbLeadSource_list = on_cbLeadSource_list_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

        self.cbLeadSourceDescr_list = ['']
        if (callable(on_cbLeadSourceDescr_list_callback)):
            try:
                self.cbLeadSourceDescr_list = on_cbLeadSourceDescr_list_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

        self.labelLeadSourceDataTypes = wx.StaticText(self.panel, -1, 'Lead Source Data Types:', (21,140), (135, 18))
        self.labelLeadSourceDataTypes.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.labelLeadSourceDataTypes.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.cbLeadSourceDataTypes = wx.ComboBox(self.panel, -1, 'combobox for Lead Source Data Types', (164,136), (150, 21), self.cbLeadSourceDataTypes_list, style=wx.CB_READONLY | wx.CB_SORT)
        self.cbLeadSourceDataTypes.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.cbLeadSourceDataTypes.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.cbLeadSourceDataTypes.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

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

        self.btnAnalysis = wx.Button(self.panel, -1, 'Analysis', (24,216), (80, 30))
        self.btnAnalysis.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnAnalysis.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.labelRecordTypes = wx.StaticText(self.panel, -1, 'Record Types:', (76,8), (80, 18))
        self.labelRecordTypes.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.labelRecordTypes.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.cbRecordTypes = wx.ComboBox(self.panel, -1, 'combobox for RecordTypes', (164,4), (150, 21), self.cbRecordTypes_list, style=wx.CB_READONLY | wx.CB_SORT)
        self.cbRecordTypes.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.cbRecordTypes.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.cbRecordTypes.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.labelLeadTypes = wx.StaticText(self.panel, -1, 'Lead Types:', (76,41), (80, 18))
        self.labelLeadTypes.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.labelLeadTypes.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.cbLeadTypes = wx.ComboBox(self.panel, -1, 'combobox for LeadTypes', (164,36), (150, 21), self.cbLeadTypes_list, style=wx.CB_READONLY | wx.CB_SORT)
        self.cbLeadTypes.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.cbLeadTypes.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.cbLeadTypes.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.labelLeadSource = wx.StaticText(self.panel, -1, 'Lead Source:', (76,74), (80, 18))
        self.labelLeadSource.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.labelLeadSource.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.cbLeadSource = wx.ComboBox(self.panel, -1, 'combobox for Lead Source', (164,70), (150, 21), self.cbLeadSource_list, style=wx.CB_READONLY | wx.CB_SORT)
        self.cbLeadSource.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.cbLeadSource.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.cbLeadSource.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.labelLeadSourceDescr = wx.StaticText(self.panel, -1, 'Lead Source Descriptions:', (16,107), (140, 18))
        self.labelLeadSourceDescr.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.labelLeadSourceDescr.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        #self.labelLeadSourceDescr.SetToolTip(wx.ToolTip('Click this button to edit the %s items.' % (self.labelLeadSourceDescr.GetLabelText().split(':')[0])))

        self.cbLeadSourceDescr = wx.ComboBox(self.panel, -1, 'combobox for Lead Source Descriptions', (164,102), (150, 21), self.cbLeadSourceDescr_list, style=wx.CB_READONLY | wx.CB_SORT)
        self.cbLeadSourceDescr.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.cbLeadSourceDescr.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.cbLeadSourceDescr.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
	
	self.__edited_widget_label = ''
	self.__d_editable_fields_via_popup = lists.HashedLists2({self.labelLeadSourceDescr.GetLabelText().split(':')[0]:self.cbLeadSourceDescr})
	self.__d_edited_fields_via_popup = lists.HashedLists2({self.cbLeadSourceDescr.Id:self.labelLeadSourceDescr.GetLabelText().split(':')[0]})

        self.labelCSVEmailAddressCol = wx.StaticText(self.panel, -1, 'CSV Email Address Column:', (16,171), (140, 18))
        self.labelCSVEmailAddressCol.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.labelCSVEmailAddressCol.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.cbCSVEmailAddressCol = wx.ComboBox(self.panel, -1, 'combobox for CSV Email Addrs Col', (164,166), (150, 21), [''], style=wx.CB_READONLY | wx.CB_SORT)
        self.cbCSVEmailAddressCol.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.cbCSVEmailAddressCol.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.cbCSVEmailAddressCol.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

	self.cbProcessMode_default = 'Choose a Processing Mode...'
	self.cbProcessMode_preload_leads = 'Preload Unicode Leads into TEMP_OBJECT__c'
	self.cbProcessMode_match_lead_sources = 'Match Lead Sources'
	self.cbProcessMode_import_leads = 'Import Leads'
	
        self.cbProcessMode = wx.ComboBox(self.panel, -1, 'Choose a Processing Mode...', (164,70), (300, 21), [self.cbProcessMode_default,self.cbProcessMode_preload_leads,self.cbProcessMode_match_lead_sources,self.cbProcessMode_import_leads], style=wx.CB_READONLY)
        self.cbProcessMode.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.cbProcessMode.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.cbProcessMode.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

	self.textboxLog = wx.TextCtrl(self.panel, -1, '', (144,192), size=(536, 269), style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.textboxLog.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.textboxLog.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.textboxLog.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnReset = wx.Button(self.panel, -1, 'Reset', (24,216), (80, 30))
        self.btnReset.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnReset.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        self.btnReset.SetBackgroundColour('red')

        self.cbSendEmailsForSalesForce = wx.CheckBox(self.panel, -1, 'Send Emails to Lead Owners when New Leads are Imported.', (16,160), (330, 24))
        self.cbSendEmailsForSalesForce.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.cbSendEmailsForSalesForce.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        self.cbSendEmailsForSalesForce.SetValue(0)

        self.Bind(wx.EVT_BUTTON, self.onProcess, self.btnProcess)
        self.Bind(wx.EVT_BUTTON, self.onProcess, self.btnProcess1)
        self.Bind(wx.EVT_BUTTON, self.onProcess, self.btnProcess2)
        self.Bind(wx.EVT_BUTTON, self.onProcess, self.btnProcess3)
        self.Bind(wx.EVT_BUTTON, self.onToggleLog, self.btnToggleLog)
        self.Bind(wx.EVT_BUTTON, self.onAnalysis, self.btnAnalysis)
        self.Bind(wx.EVT_BUTTON, self.onReset, self.btnReset)
        self.Bind(wx.EVT_COMBOBOX, self.onProcessMode, self.cbProcessMode)
        self.Bind(wx.EVT_COMBOBOX, self.onLeadSourceDescr, self.cbLeadSourceDescr)

        #self.Bind(wx.EVT_BUTTON, self.onEditLeadSourceDescr, self.labelLeadSourceDescr)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hboxes = []

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.labelLeadSourceDescr, 0, wx.RIGHT, 8)
        hboxes[-1].Add(self.cbLeadSourceDescr, 1)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.labelLeadSource, 0, wx.RIGHT, 8)
        hboxes[-1].Add((60, -1))
        hboxes[-1].Add(self.cbLeadSource, 1)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.labelLeadTypes, 0, wx.RIGHT, 8)
        hboxes[-1].Add((60, -1))
        hboxes[-1].Add(self.cbLeadTypes, 1)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.labelRecordTypes, 0, wx.RIGHT, 8)
        hboxes[-1].Add((60, -1))
        hboxes[-1].Add(self.cbRecordTypes, 1)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.labelLeadSourceDataTypes, 0, wx.RIGHT, 8)
        hboxes[-1].Add((5, -1))
        hboxes[-1].Add(self.cbLeadSourceDataTypes, 1)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.labelCSVEmailAddressCol, 0, wx.RIGHT, 8)
        hboxes[-1].Add(self.cbCSVEmailAddressCol, 1)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.cbSendEmailsForSalesForce, 0, wx.ALL, 8)
        hboxes[-1].Add((1, -1))
        hboxes[-1].Add(self.cbProcessMode, 0, wx.ALL, 8)
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
        vbox2.Add(self.btnAnalysis, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox2.Add((-1, 5))
        vbox2.Add(self.btnReset, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox2.Add((-1, 20))
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

    def onProcessMode(self, event):
        if (callable(self.__onProcessMode_callback)):
            try:
                self.__onProcessMode_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def onLeadSourceDescr(self, event):
        if (callable(self.__onLeadSourceDescr_callback)):
            try:
                self.__onLeadSourceDescr_callback()
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
		pass # mainly Unicode errors that don't matter come thru here.
    
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

class SalesForceLogin(wx.Dialog):	
    def __init__(self, parent, title, onProcess_callback=None, onClose_callback=None, onRadioStaging_callback=None, onRadioProduction_callback=None, isStaging=False):
        self.__onProcess_callback = onProcess_callback
        self.__onClose_callback = onClose_callback
        self.__onRadioStaging_callback = onRadioStaging_callback
        self.__onRadioProduction_callback = onRadioProduction_callback

        wx.Dialog.__init__(self, parent, -1, title, wx.DefaultPosition, (300, 160), style=wx.SYSTEM_MENU | wx.CAPTION | wx.STAY_ON_TOP) # | wx.CLOSE_BOX | wx.RESIZE_BORDER | 0 | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX
        self.panel = wx.Panel(self, -1)

        self.labelUsername = wx.StaticText(self.panel, -1, 'UserName:', (16,10), (65, 17))
        self.labelUsername.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.labelUsername.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.textUsername = wx.TextCtrl(self.panel, -1, 'username', (96,8), size=(185, 20))
        self.textUsername.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.textUsername.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.textUsername.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.labelPassword = wx.StaticText(self.panel, -1, 'Password:', (16,32), (65, 17))
        self.labelPassword.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.labelPassword.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.textPassword = wx.TextCtrl(self.panel, -1, 'password', (96,32), size=(185, 20), style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        self.textPassword.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.textPassword.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.textPassword.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.rbProduction = wx.RadioButton(self.panel, -1, 'Production', (96,64), (80, 24))
        self.rbProduction.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.rbProduction.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        self.rbProduction.SetValue(1 if (not isStaging) else 0)

        self.rbStaging = wx.RadioButton(self.panel, -1, 'Staging', (24,67), (65, 18))
        self.rbStaging.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.rbStaging.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        self.rbStaging.SetValue(1 if (isStaging) else 0)

        self.btnLogin = wx.Button(self.panel, -1, 'Login', (24,96), (75, 23))
        self.btnLogin.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnLogin.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnCancel = wx.Button(self.panel, -1, 'Cancel', (120,96), (75, 23))
        self.btnCancel.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnCancel.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.boxRadioButtons = wx.StaticBox(self.panel, -1, "SalesForce Instance" )
        self.boxRadioButtons.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.boxRadioButtons.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        import salesforce_icon
        self.SetIcon(wx.IconFromBitmap(salesforce_icon.getsalesforce_iconBitmap()))

        vbox = wx.BoxSizer(wx.VERTICAL)

        hboxes = []

        box1 = wx.StaticBoxSizer( self.boxRadioButtons, wx.VERTICAL )
        grid1 = wx.FlexGridSizer( 0, 2, 0, 0 )

        grid1.Add(self.rbStaging, 0, wx.ALIGN_CENTRE|wx.LEFT|wx.RIGHT|wx.TOP, 5 )
        grid1.Add(self.rbProduction, 0, wx.ALIGN_CENTRE|wx.LEFT|wx.RIGHT|wx.TOP, 5 )

        box1.Add(grid1, 0, wx.ALIGN_LEFT | wx.ALL, 5 )

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.labelUsername, 0, wx.RIGHT, 8)
        hboxes[-1].Add((5, -1))
        hboxes[-1].Add(self.textUsername, 1)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.labelPassword, 0, wx.RIGHT, 8)
        hboxes[-1].Add((5, -1))
        hboxes[-1].Add(self.textPassword, 1)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

        vbox.Add(box1, 0, wx.ALIGN_LEFT | wx.ALL, 10)
        vbox.Add((-1, 1))

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.btnLogin, 0, wx.RIGHT, 8)
        hboxes[-1].Add((5, -1))
        hboxes[-1].Add(self.btnCancel, 1)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vbox.Add((-1, 1))

        self.panel.SetSizer(vbox)

        x = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        y = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)

        self.SetSizeHints(300,160,x,y)
        vbox.Fit(self)

        self.Bind(wx.EVT_BUTTON, self.onProcess, self.btnLogin)
        self.Bind(wx.EVT_BUTTON, self.OnClose, self.btnCancel)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.Bind(wx.EVT_TEXT_ENTER, self.onProcess, self.textPassword)

        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioProduction, self.rbProduction)
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioStaging, self.rbStaging)

    def onRadioStaging(self, event):
        if (callable(self.__onRadioStaging_callback)):
            try:
                self.__onRadioStaging_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def onRadioProduction(self, event):
        if (callable(self.__onRadioProduction_callback)):
            try:
                self.__onRadioProduction_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def onProcess(self, event):
        if (callable(self.__onProcess_callback)):
            try:
                self.__onProcess_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def OnClose(self, event):
        if (callable(self.__onClose_callback)):
            try:
                self.__onClose_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def _Disable(self):
        self.textUsername.Disable()
        self.textPassword.Disable()
        self.rbProduction.Disable()
        self.rbStaging.Disable()
        self.btnLogin.Disable()
        self.btnCancel.Disable()

    def _Enable(self):
        self.textUsername.Enable()
        self.textPassword.Enable()
        self.rbProduction.Enable()
        self.rbStaging.Enable()
        self.btnLogin.Enable()
        self.btnCancel.Enable()

class NewListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

class CSVColumnMapper(wx.Frame):	
    def __init__(self, parent, title, onProcess_callback=None, onClose_callback=None):
        self.__onProcess_callback = onProcess_callback
        self.__onClose_callback = onClose_callback
        self.__d_sortable_items = lists.HashedLists2()

        wx.Frame.__init__(self, parent, -1, '%s - Maps Columns from YOUR .CSV to the Internal .CSV Data Model' % (title), wx.DefaultPosition, (700, 500), style=wx.CAPTION | wx.STAY_ON_TOP) # wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.RESIZE_BORDER
        self.panel = wx.Panel(self, -1)

        self.gboxLeft = wx.StaticBox(self.panel, -1, "External .CSV Columns", (8,8), (200, 450))
        self.gboxLeft.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.gboxLeft.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.bsizerLeft = wx.StaticBoxSizer(self.gboxLeft, wx.VERTICAL)

        self.lbLeft = wx.ListBox(self.panel, -1, (216,16), (160, 448), [''], style=wx.LB_SORT)
        self.lbLeft.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.lbLeft.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.lbLeft.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.bsizerLeft.Add(self.lbLeft, 0, wx.TOP|wx.LEFT, 10)

        self.gboxRight = wx.StaticBox(self.panel, -1, "Internal .CSV Columns", (480,8), (200, 450))
        self.gboxRight.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.gboxRight.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.bsizerRight = wx.StaticBoxSizer(self.gboxRight, wx.VERTICAL)

        self.lbRight = wx.ListBox(self.panel, -1, (216,16), (160, 448), [''], style=wx.LB_SORT)
        self.lbRight.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.lbRight.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.lbRight.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.bsizerRight.Add(self.lbRight, 0, wx.TOP|wx.LEFT, 10)

        self.gboxCenter = wx.StaticBox(self.panel, -1, ".CSV Column Associations", (480,8), (300, 450))
        self.gboxCenter.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.gboxCenter.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.bsizerCenter = wx.StaticBoxSizer(self.gboxCenter, wx.VERTICAL)

        self.lbCenter = NewListCtrl(self.panel, 
                                    wx.NewId(),
                                    size=(300,450),
                                    style=wx.LC_REPORT 
                                    #| wx.BORDER_SUNKEN
                                    | wx.BORDER_NONE
                                    #| wx.LC_EDIT_LABELS
                                    | wx.LC_SORT_ASCENDING
                                    #| wx.LC_NO_HEADER
                                    #| wx.LC_VRULES
                                    #| wx.LC_HRULES
                                    | wx.LC_SINGLE_SEL
                                    )

        self.lbCenter.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.lbCenter.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.lbCenter.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.lbCenter.InsertColumn(0, "LEFT")
        self.lbCenter.InsertColumn(1, "RIGHT")

        self.bsizerCenter.Add(self.lbCenter, 0, wx.EXPAND, 10)

        self.btnLeftRemove = wx.Button(self.panel, -1, '<<', (24,96), (30, 23))
        self.btnLeftRemove.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnLeftRemove.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnLeftRemove.SetToolTip(wx.ToolTip('Click this button to remove an Associated Item from the LEFT.  Select the item from the Center List to remove and then click this button.'))

        self.btnLeftAdd = wx.Button(self.panel, -1, '>>', (24,96), (30, 23))
        self.btnLeftAdd.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnLeftAdd.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnLeftAdd.SetToolTip(wx.ToolTip('Click this button to add an Associated Item to the LEFT.  Select the item to add from the left List and then click this button to add the selected item to the selected item in the Center or the first open item in the Center.'))

        self.btnRightRemove = wx.Button(self.panel, -1, '>>', (24,96), (30, 23))
        self.btnRightRemove.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnRightRemove.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnRightRemove.SetToolTip(wx.ToolTip('Click this button to remove an Associated Item to the RIGHT.  Select the item to remove from the center List and then click this button to remove the selected item from the selected item in the Center.'))

        self.btnRightAdd = wx.Button(self.panel, -1, '<<', (24,96), (30, 23))
        self.btnRightAdd.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnRightAdd.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnRightAdd.SetToolTip(wx.ToolTip('Click this button to add an Associated Item to the RIGHT.  Select the item to add from the right List and then click this button to add the selected item to the selected item in the Center or the first open item in the Center.'))

        self.btnOK = wx.Button(self.panel, -1, 'OK', (24,96), (75, 23))
        self.btnOK.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnOK.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnOK.SetToolTip(wx.ToolTip('Click this button to accept the Mapper Associations and process the selected .CSV File.'))

        self.btnCancel = wx.Button(self.panel, -1, 'Cancel', (120,96), (75, 23))
        self.btnCancel.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnCancel.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnCancel.SetToolTip(wx.ToolTip('Click this button to cancel the %s dialog and exit the program.' % (title)))

        self.Bind(wx.EVT_BUTTON, self.onProcess, self.btnOK)
        self.Bind(wx.EVT_BUTTON, self.OnClose, self.btnCancel)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        vboxLeftBtns = wx.BoxSizer(wx.VERTICAL)
        vboxLeftBtns.Add(self.btnLeftRemove, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vboxLeftBtns.Add((-1, 1))
        vboxLeftBtns.Add(self.btnLeftAdd, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        vboxRightBtns = wx.BoxSizer(wx.VERTICAL)
        vboxRightBtns.Add(self.btnRightRemove, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vboxRightBtns.Add((-1, 1))
        vboxRightBtns.Add(self.btnRightAdd, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

        hbox.Add(self.bsizerLeft, 0, wx.LEFT, 8)
        hbox.Add((5, -1))
        hbox.Add(vboxLeftBtns, 0, wx.LEFT, 8)
        hbox.Add((5, -1))
        hbox.Add(self.bsizerCenter, 0, wx.LEFT, 8)
        hbox.Add((5, -1))
        hbox.Add(vboxRightBtns, 0, wx.LEFT, 8)
        hbox.Add((5, -1))
        hbox.Add(self.bsizerRight, 0, wx.LEFT, 8)

        vbox.Add(hbox, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add((-1, 1))

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(self.btnOK, 0, wx.LEFT, 8)
        hbox2.Add((5, -1))
        hbox2.Add(self.btnCancel, 0, wx.LEFT, 8)

        vbox.Add(hbox2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        vbox.Add((-1, 1))

        self.panel.SetSizer(vbox)

        vbox.Fit(self)

    def onProcess(self, event):
        if (callable(self.__onProcess_callback)):
            try:
                self.__onProcess_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def OnClose(self, event):
        if (callable(self.__onClose_callback)):
            try:
                self.__onClose_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def sortCenterItems(self,x,y):
        return self.__d_sortable_items[x] > self.__d_sortable_items[y]

    def populate_suggestions(self, d_suggestions):
        if (lists.isDict(d_suggestions)):
            i = 0
            for k,v in d_suggestions.iteritems():
                index = self.lbCenter.InsertStringItem(i, '')
                if (index > -1):
                    self.lbCenter.SetStringItem(index,0,k)
                    self.lbCenter.SetStringItem(index,1,v if (not isinstance(v,list)) else v[0])
                    self.lbCenter.SetItemData(index, i)
                    self.__d_sortable_items[i] = k
                    i += 1
        self.lbCenter.SortItems(self.sortCenterItems)
        self.lbCenter.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.lbCenter.SetColumnWidth(1, wx.LIST_AUTOSIZE)

    def get_suggestions(self):
        l = []
        n = self.lbCenter.GetItemCount()
        m = self.lbCenter.GetColumnCount()
        for index in xrange(0,n):
            r = []
            for c_index in xrange(0,m):
                anItem = self.lbCenter.GetItem(index,c_index)
                r.append(anItem.GetText())
            l.append(tuple(r))
        return lists.HashedLists2(dict(l))

#---------------------------------------------------------------------------
if (__name__ == '__main__'):
    class MyApp(wx.App):
        def OnInit(self):
            frame = Dialog(None, 'App')
            frame.Show(True)
            self.SetTopWindow(frame)
            return True

    app = MyApp(True)
    app.MainLoop()
