
# Created with FarPy GUIE v0.5.5

import wx
import wx.calendar

class MyFrame(wx.Frame):	
	def __init__(self, parent, title):
		wx.Frame.__init__(self, parent, -1, 'QA Monitor', wx.DefaultPosition, (700, 500), style=wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.RESIZE_BORDER | wx.FRAME_NO_TASKBAR | 0 | 0 | 0)
		self.panel = wx.Panel(self, -1)

		self.progressbar1 = wx.Gauge(self.panel, -1, 100, (8,8), (100, 23))
		self.progressbar1.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
		self.progressbar1.SetValue(0)

		self.listbox1_list = ['']
		self.listbox1 = wx.ListBox(self.panel, -1, (120,8), (120, 450), self.listbox1_list)
		self.listbox1.SetBackgroundColour(wx.Colour(255, 255, 255))
		self.listbox1.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
		self.listbox1.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

		
#---------------------------------------------------------------------------
class MyApp(wx.App):
	def OnInit(self):
		frame = MyFrame(None, 'App')
		frame.Show(True)
		self.SetTopWindow(frame)
		return True

app = MyApp(True)
app.MainLoop()