# download 3Dx driver from 3dconnexxion.com
# download comptypes (python plugin) from "http://sourceforge.net/projects/comtypes/"

from comtypes.client import GetEvents, CreateObject

class SensorListener:
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

        
def PumpMessages():
    from ctypes import windll, byref
    from ctypes.wintypes import MSG
    user32 = windll.user32
    msg = MSG()
    PM_REMOVE = 0x0001
    
    
    while user32.GetMessageA(byref(msg), 0, 0, 0):
        user32.TranslateMessage(byref(msg))
        print "bla"
        user32.DispatchMessageA(byref(msg))
        print "bla2"

        
def main():
    # Get device
    device = CreateObject("TDxInput.Device")
    if device.Connect() == 0:
        print "3DConnexion Device Connected!"
        con = GetEvents(device.sensor, SensorListener(device.sensor))
        print con
        try:
            print "bla4"
            PumpMessages()
        except KeyboardInterrupt:
            return
        print "bla3"

if __name__ == "__main__":
    main()