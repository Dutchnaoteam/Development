########################
# NAO CONTROL THROUGH XBOX 360 WIRED CONTROLLER
# 27 april 2012 - Hessel van der Molen
#
# HOW TO USE:
# 1) Make sure you have installed:
#   - Python 2.7
#   - Naoqi SDK 12.3    (for python 2.7)
#   - PyGame            (for Python 2.7)
#   - xbox-360 controller
# 2) Make sure you have this files in the same directory:
#    - 'main.py'        (this file)
#    - 'motions.py'     (a Dutch Nao Team motion-file)
#    - 'processmotion.py' 
# 3) Connect Nao & Computer to same network
# 4) get Nao-ipadress
# 5) In terminal, goto the dir containing the above described files 
# 6) run: 
#      terminal> python main.py <NaoIPadress>
# 7) enjoy :) [programme controls can be found in 'processmotion.py']
#

print "Setting up system one moment please..."
print "------------------------------"

print "> importing motion-modules..."
import sys
import processmotion
import motions

print "> searching joystick..."
import pygame
pygame.init()
pygame.joystick.init()
joystickID = 0
myjoy = pygame.joystick.Joystick(joystickID)	

print "> setting up joystick..."
myjoy.init()
print ">>> Joystick: "  + myjoy.get_name()

print "> importing naoqi..."
from naoqi import ALProxy

print "> setting connection data..."
IPADRESS = sys.argv[1]
PORT = 9559

print ">>> setting motion proxy..."
motionProxy = ALProxy("ALMotion", IPADRESS, PORT)
print ">>> setting pose proxy..."
poseProxy = ALProxy("ALRobotPose", IPADRESS, PORT)

print "> fetching DNT-motion class..."
motionclass = motions.Motions(motionProxy, poseProxy)

print "------------------------------"
print "System setup is complete!"
print "Ready: reading joystick.."        
while True:
    try:
        e = pygame.event.wait()
        r = processmotion.processInput(e, motionclass)
        if (r == "quit"):
            print "quit."
            exit(1)
            break
    except KeyboardInterrupt,ee:
        print( "\n\nClosed" )
        print( str( ee ) )
        exit(1)
        break
