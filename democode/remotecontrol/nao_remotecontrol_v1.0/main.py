########################
# NAO CONTROL THROUGH XBOX 360 WIRED CONTROLLER
# April 2012 - Hessel van der Molen
# (c) Dutch Nao Team, licensed under GNU-GPL v3.0 
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
#      terminal> python main.py <NaoIPadress> <JoystickID>
#           (JoystickID is by default '0')
# 7) enjoy :) [program controls/button definition can be found in 'processmotion.py']
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
joysticksFound = pygame.joystick.get_count()
print ">>> found: " + str(joysticksFound) + " joysticks"

if (joysticksFound > 0):
    joystickID = 0
    if (len(sys.argv) > 2):
        joystickID = int(sys.argv[2])
    print ">>> selected joystick: " + str(joystickID) 
    joystick = pygame.joystick.Joystick(joystickID)	
    joystick.init()
    print ">>> joystick initialized: "  + joystick.get_name()

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
            #TODO: test set_{allowed,blocked}
            # --> disabling xbox xontrolloer when robot is executing command
            # --> If robot-movement is slow, pygame.event will not build large queue
            #       --> so no overload when robot is done with movement
            #pygame.event.set_blocked(None)
            e = pygame.event.wait()
            #pygame.event.set_allowed(None)
            r = processmotion.processInput(e, motionclass)
            if (r == "action"):
                print " >>> executed"
            elif (r == "quit"):
                print "quit."
                exit(1)
                break
        except KeyboardInterrupt,ee:
            print "forced quit."
            print str( ee )
            exit(1)
            break
else:
    print "------------------------------"
    print "No joysticks found, program terminated."
    
