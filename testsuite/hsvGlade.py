#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
# generated by wxGlade 0.6.3 on Fri Nov 11 15:41:14 2011
#
# By Michael Cabot
# Download wx at: www.wxpython.org
# (Optional) Download wxGlade at: wxglade.sourceforge.net

import wx
import colorsys
import magicWand
import socket
import time
import threading
# own file
import filterTools

'''
TODO
update filter image
create toggle for filter options
'''

# begin wxGlade: extracode
# end wxGlade



class hsvGlade(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: hsvGlade.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.hsvRangeSizer_staticbox = wx.StaticBox(self, -1, "Set HSV range")
        self.connectSizer_staticbox = wx.StaticBox(self, -1, "Connect")
        self.naoVisionSizer_staticbox = wx.StaticBox(self, -1, "Nao Vision")
        
        # Menu Bar
        self.TestSuite_menubar = wx.MenuBar()
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(wx.NewId(), "Import...", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(wx.NewId(), "Save", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(wx.NewId(), "Save as...", "", wx.ITEM_NORMAL)
        self.TestSuite_menubar.Append(wxglade_tmp_menu, "File")
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(wx.NewId(), "Add IP...", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(wx.NewId(), "Remove IP...", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendSeparator()
        wxglade_tmp_menu.Append(wx.NewId(), "Properties...", "", wx.ITEM_NORMAL)
        self.TestSuite_menubar.Append(wxglade_tmp_menu, "Edit")
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(wx.NewId(), "About...", "", wx.ITEM_NORMAL)
        self.TestSuite_menubar.Append(wxglade_tmp_menu, "Help")
        self.SetMenuBar(self.TestSuite_menubar)
        # Menu Bar end
        self.TestSuite_statusbar = self.CreateStatusBar(1, 0)
        self.imageWindow = PreviewImage(self, -1)
        self.filterWindow = PreviewImage(self, -1)
        self.list_box_1 = wx.ListBox(self, -1, choices=["Ball", "Blue Goal", "Yellow Goal"])
        self.emptyText = wx.StaticText(self, -1, "")
        self.minText = wx.StaticText(self, -1, "Min:")
        self.maxText = wx.StaticText(self, -1, "Max:")
        self.hText = wx.StaticText(self, -1, "Hue:")
        self.hMin = wx.SpinCtrl(self, -1, "", min=0, max=180)
        self.hMax = wx.SpinCtrl(self, -1, "", min=0, max=180)
        self.sText = wx.StaticText(self, -1, "Saturation:")
        self.sMin = wx.SpinCtrl(self, -1, "", min=0, max=255)
        self.sMax = wx.SpinCtrl(self, -1, "", min=0, max=255)
        self.vText = wx.StaticText(self, -1, "Value:")
        self.vMin = wx.SpinCtrl(self, -1, "", min=0, max=255)
        self.vMax = wx.SpinCtrl(self, -1, "", min=0, max=255)
        self.paletteWindow = PreviewPalette(self, -1)
        self.addColourButton = wx.Button(self, -1, "Add Colour")
        self.removeColourButton = wx.Button(self, -1, "Remove Colour")
        self.testButton = wx.Button(self, -1, "testButton")
        self.magicRatioTextCtrl = wx.TextCtrl(self, -1, "0.125")
        self.ipListBox = wx.ListBox(self, -1, choices=[], style=wx.LB_HSCROLL|wx.LB_SORT)
        self.ipTextCtrl = wx.TextCtrl(self, -1, "")
        self.addIPButton = wx.Button(self, -1, "Add IP")
        self.removeIPButton = wx.Button(self, -1, "Remove IP")
        self.connectButton = wx.Button(self, -1, "Connect")
        self.disconnectButton = wx.Button(self, -1, "Disconnect")

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

        # set parameters
        self.rMin = 0
        self.rMax = 0
        self.gMin = 0
        self.gMax = 0
        self.bMin = 0
        self.bMax = 0
        self.visionTools = None
        self.vmName = "python_GVM"
        self.imageResolution = 0    #resolution={0,1,2}
        self.imageColorSpace = 13   #colorSpace={0,9,10,11,12,13}
        self.imageFps = 30          #fps={5,10,15,30}
        self.imageWindow.image = wx.Image('./ball2.png', wx.BITMAP_TYPE_PNG)
        self.filterWindow.image = wx.Image('./ballFilter.png', wx.BITMAP_TYPE_PNG)
        
        # events
        self.magicRatioTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.setMagicRatio)
        self.ipTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.addIP)
        self.addIPButton.Bind(wx.EVT_BUTTON, self.addIP)
        self.removeIPButton.Bind(wx.EVT_BUTTON, self.removeIP)
        self.ipListBox.Bind(wx.EVT_LISTBOX_DCLICK, self.connect)
        self.connectButton.Bind(wx.EVT_BUTTON, self.connect)
        self.disconnectButton.Bind(wx.EVT_BUTTON, self.disconnect)
        wx.EVT_SPINCTRL(self, -1, self.hsvSpinCtrl)
        #self.Bind(wx.EVT_PAINT, self.paintGradient, self.gradientPanel)
        #wx.EVT_PAINT(self.gradientPanel, self.paintGradient)
        #self.Bind(wx.EVT_LISTBOX, self.listBoxTest, self.list_box_1)
        self.addColourButton.Bind(wx.EVT_BUTTON, self.addColour)
        self.removeColourButton.Bind(wx.EVT_BUTTON, self.removeColour)
        # image events
        self.imageWindow.Bind(wx.EVT_MOTION, self.onImage)
        self.imageWindow.Bind(wx.EVT_LEFT_DOWN, self.pickColour)
        self.imageWindow.Bind(wx.EVT_LEAVE_WINDOW, self.leaveImage)
        self.imageWindow.Bind(wx.EVT_ENTER_WINDOW, self.enterImage)
        # update image from nao
        self.timerInterval = 33 # in miliseconds 
        self.timer = wx.Timer(self, self.timerInterval)
        wx.EVT_TIMER(self, self.timerInterval, self.updateImage)
        # key events
        self.ipListBox.Bind(wx.EVT_KEY_UP, self.onKeyPress)

        # test event
        self.testButton.Bind(wx.EVT_BUTTON, self.test)
        self.testImageS = "old"

        # cursor image
        self.cursorCross = False

    def __set_properties(self):
        # begin wxGlade: hsvGlade.__set_properties
        self.SetTitle("TestSuite")
        self.TestSuite_statusbar.SetStatusWidths([-1])
        # statusbar fields
        TestSuite_statusbar_fields = ["^_^"]
        for i in range(len(TestSuite_statusbar_fields)):
            self.TestSuite_statusbar.SetStatusText(TestSuite_statusbar_fields[i], i)
        self.list_box_1.SetToolTipString("Select the filter")
        self.list_box_1.SetSelection(0)
        self.minText.SetMinSize((-1, -1))
        self.maxText.SetMinSize((-1, -1))
        self.hText.SetMinSize((-1, -1))
        self.hMin.SetMinSize((60, -1))
        self.hMax.SetMinSize((60, -1))
        self.sText.SetMinSize((-1, -1))
        self.sMin.SetMinSize((60, -1))
        self.sMax.SetMinSize((60, -1))
        self.vText.SetMinSize((-1, -1))
        self.vMin.SetMinSize((60, -1))
        self.vMax.SetMinSize((60, -1))
        self.addColourButton.Enable(False)
        self.ipListBox.SetMinSize((-1,10))
        self.ipListBox.SetToolTipString("Previous IPs")
        self.ipTextCtrl.SetToolTipString("Enter a new IP")
        self.connectButton.SetMinSize((-1,-1))
        self.disconnectButton.SetMinSize((-1,-1))
        self.disconnectButton.Enable(False)
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: hsvGlade.__do_layout
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        connectSizer = wx.StaticBoxSizer(self.connectSizer_staticbox, wx.HORIZONTAL)
        connectButtonsSizer = wx.BoxSizer(wx.VERTICAL)
        addIPsizer = wx.BoxSizer(wx.VERTICAL)
        hsvRangeSizer = wx.StaticBoxSizer(self.hsvRangeSizer_staticbox, wx.HORIZONTAL)
        eyedropperSizer = wx.BoxSizer(wx.HORIZONTAL)
        eyedropperButtonsSizer = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.GridSizer(4, 3, 0, 0)
        naoVisionSizer = wx.StaticBoxSizer(self.naoVisionSizer_staticbox, wx.HORIZONTAL)
        naoVisionSizer.Add(self.imageWindow, 1, wx.EXPAND, 0)
        naoVisionSizer.Add(self.filterWindow, 1, wx.EXPAND, 0)
        naoVisionSizer.Add(self.list_box_1, 0, wx.EXPAND, 0)
        mainSizer.Add(naoVisionSizer, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(self.emptyText, 0, 0, 0)
        grid_sizer_1.Add(self.minText, 0, 0, 0)
        grid_sizer_1.Add(self.maxText, 0, 0, 0)
        grid_sizer_1.Add(self.hText, 0, 0, 0)
        grid_sizer_1.Add(self.hMin, 0, 0, 0)
        grid_sizer_1.Add(self.hMax, 0, 0, 0)
        grid_sizer_1.Add(self.sText, 0, 0, 0)
        grid_sizer_1.Add(self.sMin, 0, 0, 0)
        grid_sizer_1.Add(self.sMax, 0, 0, 0)
        grid_sizer_1.Add(self.vText, 0, 0, 0)
        grid_sizer_1.Add(self.vMin, 0, 0, 0)
        grid_sizer_1.Add(self.vMax, 0, 0, 0)
        hsvRangeSizer.Add(grid_sizer_1, 1, wx.EXPAND, 0)
        eyedropperSizer.Add(self.paletteWindow, 1, wx.EXPAND, 0)
        eyedropperButtonsSizer.Add(self.addColourButton, 0, 0, 0)
        eyedropperButtonsSizer.Add(self.removeColourButton, 0, 0, 0)
        eyedropperButtonsSizer.Add(self.testButton, 0, 0, 0)
        eyedropperButtonsSizer.Add(self.magicRatioTextCtrl, 0, 0, 0)
        eyedropperSizer.Add(eyedropperButtonsSizer, 1, wx.EXPAND, 0)
        hsvRangeSizer.Add(eyedropperSizer, 1, wx.EXPAND, 0)
        mainSizer.Add(hsvRangeSizer, 0, wx.EXPAND, 0)
        connectSizer.Add(self.ipListBox, 1, wx.EXPAND, 0)
        addIPsizer.Add(self.ipTextCtrl, 0, wx.EXPAND, 0)
        addIPsizer.Add(self.addIPButton, 0, 0, 0)
        addIPsizer.Add(self.removeIPButton, 0, 0, 0)
        connectSizer.Add(addIPsizer, 1, wx.EXPAND, 0)
        connectButtonsSizer.Add(self.connectButton, 1, wx.EXPAND, 0)
        connectButtonsSizer.Add(self.disconnectButton, 1, wx.EXPAND, 0)
        connectSizer.Add(connectButtonsSizer, 1, wx.EXPAND, 0)
        mainSizer.Add(connectSizer, 0, wx.EXPAND, 0)
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        mainSizer.SetSizeHints(self)
        self.Layout()
        self.Centre()
        # end wxGlade

    #>> TEST <<
    def test(self, event):
        testTools = filterTools.VisionTestTools()
        image = self.imageWindow.image
        image = testTools.wxToCv(image)
        # filter image
        (hsvMin, hsvMax) = self.getRangeHSV()
        print hsvMin, hsvMax
        filter = testTools.filterImage(image, hsvMin, hsvMax)
        self.filterWindow.image = testTools.cvFilterToWx(filter)
        # refresh
        self.filterWindow.Refresh()
    #>> END <<
    
    def setMagicRatio(self, evt):
        ratio = self.magicRatioTextCtrl.GetValue()
        invalid = False
        status = ["^_^"]
        try:
            ratio = float(ratio)
            if ratio<0.0 or ratio>1.0:
                invalid = True
        except:
            invalid = True
        if invalid:
            print "Invalid argument: Enter a float x, where 0.0<=x<=1.0."
            status = ["T_T Enter a float x, where 0.0<=x<=1.0."]
            self.magicRatioTextCtrl.SetValue('0.125')

        self.setStatusText(status)

    def setStatusText(self, status):
        for i in range(len(status)):
            self.TestSuite_statusbar.SetStatusText(status[i], i)

    def onKeyPress(self, event):
        keycode = event.GetKeyCode()
        if keycode==13:     # if hit enter
            self.connect(None)
        elif keycode==127:  # if hit delete
            self.removeIP(None)

    def onImage(self, event):
        self.paletteWindow.updatePreview()

    def enterImage(self, event):
        self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))

    def leaveImage(self, event):
        self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

    def pickColour(self, event):
        self.paletteWindow.updatePreview()  #update selected colour
        image = self.imageWindow.image
        pos = self.imageWindow.ScreenToClient(wx.GetMousePosition())
        ratio = self.magicRatioTextCtrl.GetValue()
        (minColour, maxColour)= magicWand.magic(image, pos, ratio)
        (rMin,gMin,bMin) = minColour
        (rMax,gMax,bMax) = maxColour
        print "hsvGlade:",minColour,maxColour

        if not self.addColourButton.IsEnabled() and not self.allZeros():
            if rMin < self.rMin:
                self.rMin = rMin
            if rMax > self.rMax:
                self.rMax = rMax
            if gMin < self.gMin:
                self.gMin = gMin
            if gMax > self.gMax:
                self.gMax = gMax
            if bMin < self.bMin:
                self.bMin = bMin
            if bMax > self.bMax:
                self.bMax = bMax
        else:
            self.rMin = rMin
            self.rMax = rMax
            self.gMin = gMin
            self.gMax = gMax
            self.bMin = bMin
            self.bMax = bMax


        (hMin,sMin,vMin) = self.rgbToHsv((self.rMin,self.gMin,self.bMin))
        (hMax,sMax,vMax) = self.rgbToHsv((self.rMax,self.gMax,self.bMax))
        
        (h1,s1,v1) = self.rgbToHsv((self.rMin,self.gMin,self.bMin))
        (h2,s2,v2) = self.rgbToHsv((self.rMax,self.gMax,self.bMax))
        # choose smallest range for Hue
        # e.g.: range(min=170,max=10)=20 < range(min=10,max=170)=160
        print str(h2)+"-"+str(h1)+"="+str(h2-h1)+", 180-"+str(h2)+"+"+str(h1)+"="+str(180-h2+h1)
        
        if h2-h1 < 180-h2+h1:
            print 'h2-h1<180-h2+h1'
            self.hMin.SetValue(hMin)
            self.hMax.SetValue(hMax)
        else:
            print 'NOT h2-h1<180-h2+h1'
            self.hMin.SetValue(hMax)
            self.hMax.SetValue(hMin)
        if s2 > s1:
            self.sMin.SetValue(sMin)
            self.sMax.SetValue(sMax)
        else:
            self.sMin.SetValue(sMax)
            self.sMax.SetValue(sMin)
        if v2 > v1:
            self.vMin.SetValue(vMin)
            self.vMax.SetValue(vMax)
        else:
            self.vMin.SetValue(vMax)
            self.vMax.SetValue(vMin)
 

    def allZeros(self):
        return self.hMin.GetValue()==self.hMax.GetValue()== \
               self.sMin.GetValue()==self.sMax.GetValue()== \
               self.vMin.GetValue()==self.vMax.GetValue()==0

    def rgbToHsv(self, (r,g,b)):
        (h, s, v) = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
        h = int(round(h*180))
        s = int(round(s*255))
        v = int(round(v*255))
        return (h,s,v)

    def hsvToRgb(self, (h,s,v)):
        (r, g, b) = colorsys.rgb_to_hsv(h/180.0, s/255.0, v/255.0)
        r = int(round(r*255))
        g = int(round(g*255))
        b = int(round(b*255))
        return (r,g,b)

    # add a colour to the HSV-range using eyedropper
    def addColour(self, event):
        self.addColourButton.Disable()
        self.removeColourButton.Enable()

    # remove a colour from the HSV-range using eyedropper
    def removeColour(self, event):
        self.removeColourButton.Disable()
        self.addColourButton.Enable()

    # add ip if not already known
    def addIP(self, event):
        ip = self.ipTextCtrl.GetValue()
        if ip == "":
            status = ["T_T enter an IP"]
        elif self.ipListBox.FindString(ip) < 0:
            self.ipListBox.Append(ip)
            self.ipListBox.SetSelection(self.ipListBox.FindString(ip))
            status = ["^_^"]
        else:
            status = ["T_T You already got this IP"]

        self.setStatusText(status)

    # remove selected ip
    def removeIP(self, event):
        i = self.ipListBox.GetSelection()
        
        if i>=0:
            self.ipListBox.Delete(i)
            # select another ip if possible
            if self.ipListBox.GetCount() == i:
                self.ipListBox.SetSelection(i-1)
            else:
                self.ipListBox.SetSelection(i)
            status = ["^_^"]
        else:
            status = ["T_T There is no IP to remove"]

        self.setStatusText(status)

    def connect(self, event):
        i = self.ipListBox.GetSelection()
        if i>=0:
            ip = self.ipListBox.GetString(i)
            self.setStatusText([">_> Connecting to " + ip + " ..."])
            
            try:
                # connect with Nao
                self.visionTools = filterTools.VisionTools(ip, self.vmName)
                self.visionTools.setParam(18,1)    #camera={top=0, bottom=1}
                self.visionTools.startFrameGrabber()
                self.visionTools.subscribe()
                # start timer
                self.timer.Start(self.timerInterval)
                # change buttons
                self.connectButton.Disable()
                self.disconnectButton.Enable()
                self.setStatusText(["^_^ Connected to " + ip + "."])
            except Exception as e:
                print "Could not connect to " + ip + "."
                print type(e)
                print e.args
                print e
                self.setStatusText(["Could not connect to " + ip + "."])
        else:
            self.setStatusText(["T_T First add an IP"])
        
    def disconnect(self, event):
        self.setStatusText(["<_< Disconnecting..."])
        
        # disconnect
        try:
            # disconnect from Nao
            self.visionTools.unsubscribe()
            self.visionTools.stopFrameGrabber()
            # stop timer
            self.timer.Stop()
            # change buttons
            self.disconnectButton.Disable()
            self.connectButton.Enable()
            self.setStatusText(["^_^ Disconnected."])
        except Exception as e:
            print "Could not disconnect."
            print type(e)
            print e.args
            print e
            self.setStatusText(["T_T Could not disconnect."])
    
    # TODO fix cvToWx
    def updateImage(self, event):
        # raw image
        image = self.visionTools.getImage()
        self.imageWindow.image = self.visionTools.cvToWx(image)
        # filter image
        (hsvMin, hsvMax) = self.getRangeHSV()
        filter = self.visionTools.filterImage(image, hsvMin, hsvMax)
        self.filterWindow.image = self.visionTools.cvTowx(filter)
        # refresh
        self.imageWindow.Refresh()
        self.filterWindow.Refresh()

    def hsvSpinCtrl(self, event):
        pass    

    def paintGradient(self, event):
        print "paintGradient"
        dc = wx.PaintDC(self.gradientPanel)
        (rgbMin, rgbMax) = self.getRangeRGB()
        dc.GradientFillLinear((-1,-1,-1,-1), self.tupleToWxColour(rgbMin), self.tupleToWxColour(rgbMax), wx.EAST)

    def tupleToWxColour(self, (a,b,c)):
        return wx.Colour(a,b,c)
    
    def getRangeHSV(self):
        return ( (self.hMin.GetValue(),self.sMin.GetValue(),self.vMin.GetValue()), (self.hMax.GetValue(),self.sMax.GetValue(),self.vMax.GetValue()) )
        
    def getRangeRGB(self):
        # convert between colourspaces
        ((hMin,sMin,vMin), (hMax,sMax,vMax)) = self.getRangeHSV()
        (rMin, gMin, bMin) = colorsys.hsv_to_rgb(hMin/180.0, \
                                                 sMin/255.0, \
                                                 vMin/255.0)
        (rMax, gMax, bMax) = colorsys.hsv_to_rgb(hMax/180.0, \
                                                 sMax/255.0, \
                                                 vMax/255.0)
        rMin *= 255; rMax *= 255; gMin *= 255
        gMax *= 255; bMin *= 255; bMax *= 255
        return ((rMin,gMin,bMin), (rMax,gMax,bMax))

# end of class hsvGlade


class hsvRanges(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        frame_1 = hsvGlade(None, -1, "")
        self.SetTopWindow(frame_1)
        frame_1.Show()
        return 1

# end of class hsvRanges


class PreviewPalette(wx.Panel):
    """Panel to display the color sampling from the eyedropper"""
    def __init__(self, parent, id=wx.ID_ANY,
                 pos=wx.DefaultPosition, size=wx.DefaultSize):
        wx.Panel.__init__(self, parent, id, pos, size)

        # Attributes
        self.color = wx.BLACK
        self.brush = wx.Brush(self.color)

        # Event Handlers
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, evt, rgbMin=None, rgbMax=None):
        dc = wx.PaintDC(self)
        dc.SetBrush(self.brush)
        rect = self.GetClientRect()
        dc.DrawRectangle(0, 0, rect.width, rect.height)
        '''
        if rgbMin==None or rgbMax==None:
            # Draw square with eyedropper colour
            dc.DrawRectangle(0, 0, rect.width, rect.height)
        else:
            # Draw 
            dc.GradientFillLinear((0,0,rect.width,rect.height), \
                                  rgbMin, rgbMax, wx.EAAST)
        '''

    def updatePreview(self):
        pos = wx.GetMousePosition()
        dc = wx.ScreenDC()
        color = dc.GetPixelPoint(pos)
        if color != self.color:
            self.color = color
            self.brush.SetColour(self.color)
            self.Refresh()

        return color

class PreviewImage(wx.Panel):
    def __init__(self, parent, id=wx.ID_ANY,
                 pos=wx.DefaultPosition, size=(-1,-1)):#size=wx.DefaultSize):
        wx.Panel.__init__(self, parent, id, pos, size)
        self.SetMinSize((160,120))
        wx.EVT_PAINT(self, self.OnPaint) 

    def OnPaint(self, event): 
        self.Paint(wx.PaintDC(self)) 

    def Paint(self, dc):
        (winX, winY) = self.GetSize()
        tempImage = self.image.Scale(winX, winY)
        dc.DrawBitmap(wx.BitmapFromImage(tempImage), 0, 0)

class Client(threading.Thread):
    on = False
    def __init__(self, gui, ip):
        threading.Thread.__init__(self)
        self.gui = gui
        self.ip = ip
        self.addr = (ip,4242)
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.sock.connect(self.addr)

    def __del__(self):
        self.sock.close()

    def run(self):
        self.self.on = True
        while self.on:
            data = self.sock.recv(10240)  #receive 2 images
            if data!=None:
                #TODO update images
                #self.gui.imageWindow.image = image
                #self.gui.imageWindow.Refresh()
                pass    
            time.sleep(1)

    def send(self, message):
        self.sock.send(message)
            
    
    

    
if __name__ == "__main__":
    hsvGlade = hsvRanges(0)
    hsvGlade.MainLoop()
