import wx
import wx.calendar
import  wx.lib.mixins.listctrl  as  listmix

import sys
from vyperlogix.misc import _utils
from vyperlogix.misc import ObjectTypeName

from vyperlogix.wx import mixins

from vyperlogix.hash import lists

import unicodedata

class NewListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, mixins.ListCtrlSelections):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

class MagmaCompetitorPanel(wx.Panel):
    def __init__(self, parent, log=None, callback=None, pane_callback=None, submit_callback=None, removeItem_callback=None, label1="Click here to show pane", label2="Click here to hide pane",data={}):
        self.log = log
        wx.Panel.__init__(self, parent, -1)

	self.label1 = label1
	self.label2 = label2
	
	self.__callback__ = callback
	self.__pane_callback__ = pane_callback
	self.__submit_callback__ = submit_callback
	self.__removeItem_callback__ = removeItem_callback
	
	self.__data__ = data
	
        self.cp = wx.CollapsiblePane(self, label=self.label1, style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.OnPaneChanged, self.cp)
        self.MakePaneContent(self.cp.GetPane())

	sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        sizer.Add(self.cp, 0, wx.EXPAND|wx.ALL, 25)

    def IsExpanded():
        doc = "IsExpanded"
        def fget(self):
            return self.cp.IsExpanded()
        return locals()
    IsExpanded = property(**IsExpanded())

    def togglePane(self):
        self.cp.Collapse(self.IsExpanded)
        self.OnPaneChanged()

    def OnPaneChanged(self, evt=None):
        if (evt) and (self.log is not None):
            self.log.write('wx.EVT_COLLAPSIBLEPANE_CHANGED: %s' % evt.Collapsed)

        # redo the layout
        self.Layout()

        if self.IsExpanded:
            self.cp.SetLabel(self.label2)
        else:
            self.cp.SetLabel(self.label1)
	    
	if (callable(self.__callback__)):
	    try:
		self.__callback__(self.IsExpanded)
	    except Exception, details:
		print >>sys.stderr, _utils.formattedException(details=details)
        
    def MakePaneContent(self, collapsible_pane):
	'''Just make a few controls to put on the collapsible pane'''
        self.lbList = NewListCtrl(collapsible_pane, 
                                    wx.NewId(),
                                    size=(200,250),
                                    style=wx.LC_REPORT 
                                    | wx.BORDER_NONE
                                    | wx.LC_SORT_ASCENDING
                                    )

        self.lbList.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.lbList.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.lbList.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.lbList.InsertColumn(0, "COMPANY NAME")

        self.labelCompanyName = wx.StaticText(collapsible_pane, -1, 'Company Name:', (16,32), (80, 17))
        self.labelCompanyName.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.labelCompanyName.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.textCompanyName = wx.TextCtrl(collapsible_pane, -1, 'company name', (16,32), size=(180, 20), style=wx.TE_PROCESS_ENTER)
        self.textCompanyName.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.textCompanyName.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.textCompanyName.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
	self.textCompanyName.SetValue('type company name & press enter')

        self.btnRemove = wx.Button(collapsible_pane, -1, 'Remove Selected Item', (24,216), (80, 30))
        self.btnRemove.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnRemove.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
	
	self.btnRemove.Disable()

	border = wx.FlexGridSizer(cols=2, hgap=5, vgap=5)
	border.AddGrowableCol(1)
	border.Add(self.labelCompanyName, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
	border.Add(self.textCompanyName, 0, wx.EXPAND)
	border.Add((5,5)) 
	border.Add(self.lbList, 0, wx.EXPAND)
	border.Add((5,0)) 
	border.Add(self.btnRemove, 0, wx.EXPAND)
	
	collapsible_pane.SetSizer(border)
        border.Fit(collapsible_pane)

        self.Bind(wx.EVT_TEXT_ENTER, self.onEnter_CompanyName, self.textCompanyName)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelected_CompanyList, self.lbList)
        self.Bind(wx.EVT_BUTTON, self.onRemoveItem, self.btnRemove)
	
    def onSelected_CompanyList(self, event):
	self.btnRemove.Enable()
    
    def onRemoveItem(self, event):
	names = []
	n = self.lbList.GetSelectedItemCount()
	if (n > 0):
	    items = self.lbList.get_selected_items()
	    for item in items:
		anItem = self.lbList.GetItem(item)
		names.append(anItem.Text)
	if (callable(self.__removeItem_callback__)):
	    try:
		self.__removeItem_callback__(self,items,names)
	    except Exception, details:
		print >>sys.stderr, _utils.formattedException(details=details)
	self.btnRemove.Disable()
    
    def bound_objects():
        doc = "bound_objects returns the objects that are bound to the submit function."
        def fget(self):
            return self.__bound_objects__
        return locals()
    bound_objects = property(**bound_objects())

    def bindPaneEvents(self, d_objs):
	self.__bound_objects__ = lists.HashedLists2(d_objs)
	btn = self.__bound_objects__['btn_submit']
	self.Bind(wx.EVT_BUTTON, self.onSubmit, btn)
	    
    def set_selection(self, value):
	n = self.lbList.GetItemCount()
	for i in xrange(0,n+1):
	    item = self.lbList.GetItem(i)
	    if (item.Text == value):
		self.lbList.SetItemState(i,wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,wx.LIST_MASK_STATE)
		break
	
    def append_to_lbList(self, data):
	'''data is a tuple that contains one element for each column to be displayed'''
	n = self.lbList.GetItemCount()
	index = self.lbList.InsertStringItem(n, '')
	l_data = list(data)
	for i in xrange(0,len(l_data)):
	    self.lbList.SetStringItem(index,i,l_data[i])
	    self.lbList.SetColumnWidth(i, wx.LIST_AUTOSIZE)
	self.lbList.SetItemData(index, n+1)

    def append_all_to_lbList(self, l_data):
	'''l_data is a list of tuples that contains one element for each column to be displayed'''
	self.lbList.DeleteAllItems()
	items = [item if (not isinstance(item,tuple)) and (not isinstance(item,list)) else list(item)[0] for item in l_data]
	items.sort()
	items.reverse()
	l_data = [tuple([item]) for item in items]
	for t in l_data:
	    self.append_to_lbList(t)
	
    def onEnter_CompanyName(self, event):
	s = event.ClientObject.GetValue()
	print '%s :: value is "%s".' % (ObjectTypeName.objectSignature(self),s)
	if (callable(self.__submit_callback__)):
	    try:
		self.__submit_callback__(self,s)
		self.set_selection(s)
	    except Exception, details:
		print >>sys.stderr, _utils.formattedException(details=details)
    
    def onSubmit(self, evt):
	print '%s' % (ObjectTypeName.objectSignature(self))
	self.togglePane()
	for k,v in self.bound_objects.iteritems():
	    if (k != 'btn_submit'):
		print '%s --> %s' % (k,v.GetValue())
	if (callable(self.__submit_callback__)):
	    try:
		self.__submit_callback__(self)
	    except Exception, details:
		print >>sys.stderr, _utils.formattedException(details=details)
	pass

class Dialog(wx.Frame,mixins.EnableMixin,mixins.DisableMixin):	
    def __init__(self, parent, title='Current Assets', onSubmitCompanyName_callback=None, removeCompanyName_callback=None, onProcess_callback=None, on_init_callback=None, on_cbLeadSourceDataTypes_list_callback=None, on_cbLeadTypes_list_callback=None, on_cbLeadSource_list_callback=None, onToggleLog_callback=None):
        wx.Frame.__init__(self, parent, -1, title, wx.DefaultPosition, (700, 500), style=wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.RESIZE_BORDER | 0 | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX) # | wx.STAY_ON_TOP
        self.panel = wx.Panel(self, -1)
        self.__onProcess_callback = onProcess_callback
        self.__onSubmitCompanyName_callback = onSubmitCompanyName_callback
        self.__onRemoveCompanyName_callback = removeCompanyName_callback
        self.__onToggleLog_callback = onToggleLog_callback

        self.btnProcess = wx.Button(self.panel, -1, 'Process', (24,216), (80, 30))
        self.btnProcess.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnProcess.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.btnToggleLog = wx.Button(self.panel, -1, 'Show Log', (24,216), (80, 30))
        self.btnToggleLog.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnToggleLog.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        self.textboxLog = wx.TextCtrl(self.panel, -1, '', (144,192), size=(500, 250), style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.textboxLog.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.textboxLog.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.textboxLog.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

	self.cpanel = MagmaCompetitorPanel(self.panel,callback=self.__resize_panel,submit_callback=self.onSubmitCompanyName,removeItem_callback=self.onRemoveCompanyName,label1='Magma Competitors',label2='Hide Magma Competitors')
	size = self.GetSize()
	self.cpanel.SetSize((size.width - 150, 60))
	self.cpanel.cp.SetSize((size.width - 150, 60))
	
        self.Bind(wx.EVT_BUTTON, self.onProcess, self.btnProcess)
        self.Bind(wx.EVT_BUTTON, self.onToggleLog, self.btnToggleLog)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hboxes = []

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))

        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(self.btnProcess, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer1.Add((-1, 1))
        sizer1.Add(self.btnToggleLog, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer1.Add((-1, 1))
        sizer1.Add(self.cpanel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer1.Add((-1, 1))
        hboxes[-1].Add(sizer1, 1)

	vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.ALL, 10)
        vbox.Add((-1, -10))

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3.Add(self.textboxLog, 0, wx.EXPAND | wx.ALL, 10)
        hbox3.Add((-1, 0))

	vbox.Add(hbox3, 0, wx.EXPAND | wx.ALL, 10)
        vbox.Add((-1, 0))
	
	self.sizer_1 = vbox
        self.panel.SetSizer(vbox)

        x = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        y = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)

        self.SetSizeHints(500,450,x,y)
        vbox.Fit(self)

        if (callable(on_init_callback)):
            try:
                on_init_callback(self.cpanel)
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def __resize_panel(self,isExpanded):
	val = 0 if (isExpanded) else -0
	size = self.GetSize()
	_size = (size.width if (not isExpanded) else (size.width - 0), 50 if (not isExpanded) else (size.height + val))
	self.cpanel.SetSize(_size)
	self.cpanel.cp.SetSize(_size)
	if (isExpanded):
	    self.textboxLog.Hide()
	else:
	    self.textboxLog.Show()
	self.Layout()
	self.sizer_1.RecalcSizes()
    
    def onSubmitCompanyName(self, pane, value):
        if (callable(self.__onSubmitCompanyName_callback)):
            try:
		self.DisableChildren()
                self.__onSubmitCompanyName_callback(value)
		self.EnableChildren()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def onRemoveCompanyName(self, pane, values, names):
        if (callable(self.__onRemoveCompanyName_callback)):
            try:
		self.DisableChildren()
                self.__onRemoveCompanyName_callback(values, names)
		self.EnableChildren()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def onProcess(self, event):
        if (callable(self.__onProcess_callback)):
            try:
		self.DisableChildren()
                self.__onProcess_callback()
		self.EnableChildren()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

    def onToggleLog(self, event):
        if (callable(self.__onToggleLog_callback)):
            try:
                self.__onToggleLog_callback()
            except Exception, details:
                print >>sys.stderr, _utils.formattedException(details=details)

