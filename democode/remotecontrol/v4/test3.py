import comtypes.client as client 
from ctypes import * 

import logging 
console = logging.StreamHandler() 
console.setLevel(logging.DEBUG) 
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s') 
console.setFormatter(formatter) 
logging.getLogger('').addHandler(console) 

types = { # What others? 
   0:"Unknown", 
   6:"SpaceNavigator", 
   4:"SpaceExplorer", 
   25:"SpaceTravler", 
   29:"SpacePilot" 
} 

class POINT(Structure): 
    """Point struct used in Win32 api functions.""" 
    _fields_ = [("x", c_long), 
                ("y", c_long)] 

class MSG(Structure): 
    """Message struct used in Win32 api functions.""" 
    _fields_ = [("hWnd", c_ulong), 
                ("message", c_uint), 
                ("wParam", c_ulong), 
                ("lParam", c_ulong), 
                ("time", c_ulong), 
                ("pt", POINT)] 
    
def PumpWaitingMessages(): 
    """Windows API function.""" 
    user32 = windll.user32 
    msg = MSG() 
    PM_REMOVE = 0x0001 
    while user32.PeekMessageA(byref(msg), 0, 0, 0, PM_REMOVE): 
        user32.TranslateMessage(byref(msg)) 
        user32.DispatchMessageA(byref(msg)) 

def GetMessage(): 
    """Windows API function.""" 
    #BOOL GetMessage(LPMSG lpMsg, HWND hWnd, UINT wMsgFilterMin, UINT wMsgFilterMax); 
    user32 = windll.user32 
    msg = MSG() 
    user32.GetMessageW(byref(msg), None, 0, 0) 
    return msg 

def DispatchMessage(msg): 
    """Windows API function.""" 
    user32 = windll.user32 
    user32.DispatchMessageW(byref(msg)) 

class KeyListener: 
    """Catch and print keyboard events. 

    Note: some keys either don't send events or give bad key codes. 
    """ 
    def __init__(self, keyboard): 
        self.exit = False 
        self.keyboard = keyboard 
        self.exitCode = 1 

    def cont(self): 
        return not self.exit 
    
    def KeyDown(self, this, code): 
        print 'Keydown: %s, %s' %(code, self.keyboard.GetKeyName(code)) 
        if code == self.exitCode: 
            self.exit = True 

    def KeyUp(self, this, code): 
        print 'Keyup: %s, %s' %(code, self.keyboard.GetKeyName(code)) 

class SensorListener: 
    """Catch and print sensor events.""" 
    def __init__(self, sensor): 
        self.sensor = sensor 
    
    def SensorInput(self, this, inval=None): 
        print "Rot: ", 
        print self.sensor.Rotation.X, 
        print self.sensor.Rotation.Y, 
        print self.sensor.Rotation.Z 
        print "Trans: ", 
        print self.sensor.Translation.X, 
        print self.sensor.Translation.Y, 
        print self.sensor.Translation.Z 

# Get device 
device = client.CreateObject("TDxInput.Device") 
print types[device.Type], 

if not device.Connect(): # Returns failed 
   print ": Connected!" 

# Setup keyboard listener 
keyboard = device.Keyboard 
listener = KeyListener(keyboard) 
client.GetEvents(keyboard, listener) 

# Setup sensor listener 
sensor = device.Sensor 
client.GetEvents(sensor, SensorListener(sensor)) 

# Start event loop 
while listener.cont(): 
    msg = GetMessage() 
    print msg
    DispatchMessage(msg) 
    #PumpWaitingMessages() 
    