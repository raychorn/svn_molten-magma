
# Created with FarPy GUIE v0.5.5

import wx
import wx.calendar

class QAMonitorDialog(wx.Dialog):	
    def __init__(self, parent, title='Processing'):
        wx.Dialog.__init__(self, parent, -1, title, wx.DefaultPosition, (700, 500), style=wx.CLOSE_BOX | wx.CAPTION | wx.SIMPLE_BORDER | wx.FRAME_NO_TASKBAR | wx.SYSTEM_MENU)
        self.panel = wx.Panel(self, -1)

	from LeadsImporter_Dialog import NewListCtrl
        self.lbMonitor = NewListCtrl(self.panel, 
                                    wx.NewId(),
                                    size=(300,420),
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

        self.btnClose = wx.Button(self.panel, -1, 'Close', (0,24), (75, 23))
        self.btnClose.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
        self.btnClose.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        import runsoftware_16x16
        self.SetIcon(wx.IconFromBitmap(runsoftware_16x16.getrunsoftware_16x16Bitmap()))

        self.Bind(wx.EVT_BUTTON, self.OnClose, self.btnClose)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hboxes = []

        hboxes.append(wx.BoxSizer(wx.HORIZONTAL))
        hboxes[-1].Add(self.lbMonitor, 0, wx.EXPAND, 8)
        vbox.Add(hboxes[-1], 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)

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

#---------------------------------------------------------------------------
class MyApp(wx.App):
    def OnInit(self):
        frame = QAMonitorDialog(None, 'App')
        frame.Show(True)
        frame.SetSize((700,500))
        self.SetTopWindow(frame)
        return True

app = MyApp(True)
app.MainLoop()