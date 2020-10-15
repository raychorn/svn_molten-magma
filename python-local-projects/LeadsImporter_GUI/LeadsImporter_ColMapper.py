
# Created with FarPy GUIE v0.5.5

import wx
import wx.calendar

class MyFrame(wx.Frame):	
	def __init__(self, parent, title):
		wx.Frame.__init__(self, parent, -1, '.CSV Column Mapper', wx.DefaultPosition, (700, 500), style=wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.RESIZE_BORDER | 0 | wx.STAY_ON_TOP | 0 | 0)
		self.panel = wx.Panel(self, -1)

		self.gbox1 = wx.StaticBox(self.panel, -1, "Your .CSV Columns", (8,8), (200, 450))
		self.gbox1.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
		self.gbox1.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

		self.gbox2 = wx.StaticBox(self.panel, -1, "Internal .CSV Columns", (480,8), (200, 450))
		self.gbox2.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
		self.gbox2.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

		self.listbox2_list = ['']
		self.listbox2 = wx.ListBox(self.panel, -1, (216,16), (260, 448), self.listbox2_list)
		self.listbox2.SetBackgroundColour(wx.Colour(255, 255, 255))
		self.listbox2.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
		self.listbox2.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

		
#---------------------------------------------------------------------------
if (__name__ == '__main__'):
	class MyApp(wx.App):
		def OnInit(self):
			frame = MyFrame(None, 'App')
			frame.Show(True)
			self.SetTopWindow(frame)
			return True
	
	app = MyApp(True)
	app.MainLoop()
