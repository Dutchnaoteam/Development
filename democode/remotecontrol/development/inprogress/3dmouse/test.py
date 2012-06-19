######################################################################
# SpaceDevice demo
#
# This demo demonstrates the usage of the SpaceDevice object in the
# cgkit.spacedevice module which can be used to access events from
# a SpaceMouse or SpaceBall. You can use this module to add support
# for a SpaceDevice in your own Python application. The demo simply
# prints the events generated from a SpaceDevice to the console.
#
# This demo uses pygame as GUI toolkit (v1.7.1 is required).
# You can use any other GUI toolkit as long as it 1) lets you obtain
# the native window handle of a window and 2) provides access to
# system events.
######################################################################

import sys
import pygame
from pygame.locals import *
from cgkit import spacedevice

# handleSystemEvent
def handleSystemEvent(evt):
    """Handle a system event.

    evt is a pygame event object that contains a system event. The function
    first checks if the event was generated by a SpaceDevice and if it was,
    it prints the event data.
    """
    # sdev is the global SpaceDevice object
    global sdev

    # Translate the system event into a SpaceDevice event...
    res, evttype, data = sdev.translateWin32Event(evt.msg, evt.wparam, evt.lparam)
    # Check if the event actually was an event generated from
    # the SpaceMouse or SpaceBall...
    print res
    if res!=spacedevice.RetVal.IS_EVENT:
        return

    # Motion event?
    if evttype==spacedevice.EventType.MOTION_EVENT:
        t,r,period = data
        print "Motion: trans:%s rot:%s period:%d"%(t, r, period)
    # Button event?
    elif evttype==spacedevice.EventType.BUTTON_EVENT:
        pressed, released = data
        print "Button: pressed:%s released:%s"%(pressed, released)
    # Zero event?
    elif evttype==spacedevice.EventType.ZERO_EVENT:
        print "Zero"

######################################################################

# Check if cgkit was compiled with SpaceDevice support...
if not spacedevice.available():
    print "No SpaceDevice functionality available"
    sys.exit(1)

# Initialize pygame...
passed, failed = pygame.init()
if failed>0:
    print "Error initializing pygame"
    sys.exit(1)

# Open a window...
pygame.display.set_caption("SpaceDevice demo")
srf = pygame.display.set_mode((640,480))

# Enable system events...
pygame.event.set_allowed(SYSWMEVENT)

# Initialize the Space Device...
sdev = spacedevice.SpaceDevice()
info = pygame.display.get_wm_info()
hwnd = info["window"]
sdev.open("Demo", hwnd)

# Print some information about the driver and the device...
major, minor, build, versionstr, datestr = sdev.getDriverInfo()
print "Driver info:"
print "------------"
print "%s, v%d.%d.%d, %s\n"%(versionstr, major, minor, build, datestr)

devtyp, numbuttons, numdegrees, canbeep, firmware = sdev.getDeviceInfo()
print "Device info:"
print "------------"
print "Device ID:",sdev.getDeviceID()
print "Type     :",devtyp
print "#Buttons :",numbuttons
print "#Degrees :",numdegrees
print "Can beep :",canbeep
print "Firmware :",firmware
print ""

# Event loop...
running = True
while running:

    # Get a list of events...
    events = pygame.event.get()

    # Process the events...
    for evt in events:

        # Close button?
        if evt.type==QUIT:
            running=False

        # Escape key?
        elif evt.type==KEYDOWN and evt.key==27:
            running=False

        # System event?
        elif evt.type==SYSWMEVENT:
            handleSystemEvent(evt)

# Close the SpaceDevice
sdev.close()