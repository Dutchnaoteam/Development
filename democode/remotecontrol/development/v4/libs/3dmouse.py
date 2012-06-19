########################################################
# 3D-MOUSE - LIBRARY FOR REMOTE-NAO-CONTROL FRAMEWORK
########################################################
#   May 2012, Hessel van der Molen, hmolen.science@gmail.com
#   Dutch Nao Team - http://dutchnaoteam.nl
#
#   Requires:
#   - python    [threading, time, sys]
#   - pygame    [python library: http://pygame.org]
#   - comtypes  [python library: http://sourceforge.net/projects/comtypes/]
#   - ctypes    [python library: default on python 2.5+]
#   - remote control framework
#   - keyboard
#   - 3D mouse (spaceNavigator from 3Dconexxion.nl)
#   - 3D mouse drivers (http://www.3dconnexion.com/service/drivers.html)
#
#   Processes input from 3D-mouse and returns events (rotations & translations) to framework

import pygame
import threading
import time
from comtypes.client import GetEvents, CreateObject

import sys
from ctypes import *
from ctypes.wintypes import *

ESCAPEBUTTON = 27

#processes sensor readings
class SensorListener:
    def __init__(self, sensor):
        self.sensor = sensor

    def SensorInput(self, this, inval=None):
        d = {}
        d["rx"] = round(self.sensor.Rotation.X, 1)
        d["ry"] = round(self.sensor.Rotation.Y, 1)
        d["rz"] = round(self.sensor.Rotation.Z, 1)
        d["tx"] = round(self.sensor.Translation.X, 1)
        d["ty"] = round(self.sensor.Translation.Y, 1)
        d["tz"] = round(self.sensor.Translation.Z, 1)
        event = pygame.event.Event(pygame.USEREVENT, d)
        pygame.event.post(event)

#Thread listening to 3D-mouse        
class mouse_thread(threading.Thread):
    device = None
    con = None
    loop = True
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.device = CreateObject("TDxInput.Device")
        if self.device.Connect() == 0:
            print "3DConnexion Device Connected!"
            
    def run(self):
        if (self.device != None):
            self.con = GetEvents(self.device.sensor, SensorListener(self.device.sensor))
            print self.con
            try:
                self.PumpMessages()
            except Exception, ee:
                print ee
                exit()
        
    def PumpMessages(self):
        self.user32 = windll.user32
        while (self.loop) and (self.user32.GetMessageA(msg, None, 0, 0)):
            self.user32.TranslateMessage(msg)
            self.user32.DispatchMessageA(msg)

    def quit(self):
        pass
        
        
mouseThread = None
def init(inputID):
    global mouseThread
    #create & start thread
    mouseThread = mouse_thread()
    mouseThread.start()
    
    #######
    pygame.init()
    interface = pygame.display.set_mode([190,115])
    pygame.display.set_caption("keyboardController")
    font = pygame.font.Font(None, 20)
    ID_text1 = font.render("Pygame Keyboard Input",True,[255,255,255])
    ID_text2 = font.render("----------------------------",True,[255,255,255])
    ID_text3 = font.render("Keep window focused to",True,[255,255,255])
    ID_text4 = font.render("recieve keyboard input.",True,[255,255,255])
    ID_text5 = font.render("  Press '" + getQuitCommand() + "' to quit.",True,[255,255,255])
    interface.blit(ID_text1, [10,10])
    interface.blit(ID_text2, [10,30])
    interface.blit(ID_text3, [10,50])
    interface.blit(ID_text4, [10,70])
    interface.blit(ID_text5, [10,90])
    pygame.display.update()
        
def quit():
    global mouseThread
    mouseThread.quit()
    mouseThread.join()
    pygame.quit()

def getQuitCommand():
    return "Esc" 

# retrieve an action/event made by the input-system
def getAction():
    event = pygame.event.wait()

    # check if 'quit'-command has been pressed, or input window is closed
    if (event.type == pygame.QUIT):
        return "quit"
    elif (event.type == pygame.KEYDOWN or event.type == pygame.KEYUP):
        if (event.key == ESCAPEBUTTON):
            return "quit"
    return event