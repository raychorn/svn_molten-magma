
# Created with FarPy GUIE v0.5.5

import wx
import wx.calendar

class EntityEditor(wx.Frame):	
	def __init__(self, parent, title):
		wx.Frame.__init__(self, parent, -1, 'Editor', wx.DefaultPosition, (200, 400), style=wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.CAPTION | wx.SIMPLE_BORDER | wx.FRAME_NO_TASKBAR | 0 | 0 | 0)
		self.panel = wx.Panel(self, -1)

		self.tbName = wx.TextCtrl(self.panel, -1, 'textbox', (0,0), size=(120, 20))
		self.tbName.SetBackgroundColour(wx.Colour(255, 255, 255))
		self.tbName.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
		self.tbName.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

		self.lbChoices_list = ['']
		self.lbChoices = wx.ListBox(self.panel, -1, (0,16), (120, 350), self.lbChoices_list)
		self.lbChoices.SetBackgroundColour(wx.Colour(255, 255, 255))
		self.lbChoices.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
		self.lbChoices.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

		self.btnRemove = wx.Button(self.panel, -1, '>>', (120,24), (70, 23))
		self.btnRemove.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
		self.btnRemove.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

		self.btnAdd = wx.Button(self.panel, -1, '(+)', (120,0), (70, 21))
		self.btnAdd.SetFont(wx.Font(8.25, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, 'Microsoft Sans Serif'))
		self.btnAdd.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

		
#---------------------------------------------------------------------------
class MyApp(wx.App):
	def OnInit(self):
		frame = MyFrame(None, 'App')
		frame.Show(True)
		self.SetTopWindow(frame)
		return True

app = MyApp(True)
app.MainLoop()