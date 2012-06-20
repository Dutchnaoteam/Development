import motWedding as motions
import copy
import time
import sys
import os

motion = None
old_state = None
new_state = None

class state:
    stiff      = 0
    veloX      = 0
    veloY      = 0
    veloT      = 0
    superSpeed = 0

def init(IPADRESS):
    global motion, old_state, new_state
    PORT = 9559

    from naoqi import ALProxy
    motionProxy = ALProxy("ALMotion", IPADRESS, PORT)
    poseProxy = ALProxy("ALRobotPose", IPADRESS, PORT)
    speechProxy = ALProxy("ALTextToSpeech", IPADRESS, PORT)
    motion = motions.Motions(motionProxy, poseProxy, speechProxy)
    
    old_state = state()
    new_state = state()
    new_state.stiff = 1 if(motionProxy.getStiffnesses('Body')[0] > 0) else 0
        
def getButtonDefinition():
    text  = "   1 = ring for reuben (rightarm)\n"
    text += "   2 = ring for kim (leftarm)\n"
    text += "   r = stand-up when fallen\n"
    text += "   h = set head to (0,0)\n"
    text += "   t = toggle stiffness\n"
    text += "   p = pauze mode (stance, stiff=off)\n"
    text += "   n = normal pose(stiff=on)\n"
    text += "   d = shoot with left leg\n"
    text += "   f = shoot with right leg\n"
    text += "   a = rotate left\n"
    text += "   s = rotate right\n"
    text += "   up = move forward\n"
    text += "   down = move backward\n"
    text += "   left = move left\n"
    text += "   right = move right\n"
    text += "   space = maximum speed\n"
    return text


    
walkVelocityForward = 0.4     
walkVelocityLeft = 0.5
rotateVelocityLeft = 0.4
def processEvent(display, event):
    global old_state, new_state

    #event[0] = keypressed (2 = pressed, 3 = released)
    #event[1] = key-number:
    #               a - z = ascii value: 97 - 122
    #               space = 32
    #               up    = 273
    #               left  = 274
    #               right = 275
    #           down  = 276
    
    keyEvent = event[0]
    keyID = event[1]
    
    #show key-data:
    #display.execute(str(event))
    #display.done()
    
    #motions which can only be executed when robot does nothing
    if (keyEvent == 2): #key is pressed
        if (not(motion.isWalking())):
            if (keyID == 114):       #r - stand-up when falling down
                display.execute("standing up")
                motion.standUp()
                display.done()
            elif (keyID == 116):     #t - toggle stiffness
                if (new_state.stiff == 1):
                    display.execute("stiffness off")
                    motion.kill()
                    new_state.stiff = 0
                else:
                    display.execute("stiffness on")
                    motion.stiff()
                    new_state.stiff = 1
                display.done()
            elif (keyID == 100):      #d - shoot with left leg
                display.execute("shoot left")
                motion.normalPose()
                motion.cartesianLeft(0,0.08,0)
                display.done()
            elif (keyID == 102):     #f - shoot with right leg
                display.execute("shoot right")
                motion.normalPose()
                motion.cartesianRight(0,0.08,0)
                display.done()
            elif (keyID == 112):     #p - pausing
                display.execute("Pausing")
                motion.stance()
                time.sleep(2)
                motion.kill()
                new_state.stiff = 0
                display.done()
            elif (keyID == 110):     #n - normal pose
                display.execute("Taking 'normal-pose'")
                motion.stiff()
                new_state.stiff = 1
                motion.normalPose()
                display.done()
                
                
    #actions which are allowed todo when walking
    #toggle 'superspeed'
    if (keyID == 32):             # space-bar
        if (keyEvent == 2):       #button is pressed
            new_state.superSpeed = 1
        else:                     #button is released
            new_state.superSpeed = 0
   
    #ring for Kim
    if (keyID == 50):
        if (keyEvent == 2):       #button is pressed
            display.execute("kim's ring")
            motion.leftArm()
            display.done()
    
    #Ring for reuben 
    if (keyID == 49):
        if (keyEvent == 2):       #button is pressed
            display.execute("reubens's ring")
            motion.rightArm()
            display.done()
            
    #set head        
    if ((keyID == 104) and (keyEvent == 2)):
        display.execute("Head positioning")
        pos = motion.getHeadPos()
        motion.changeHead(-pos[0],-pos[1])
        display.done()
   
    #WALKING
    # note: the 'elif' after a 'if keyEvent == x' statement is necessary because
    # the robot could have changed direction (have a different speed: forward/backwards for example). \
    # Resetting the speed whould thus result in incorrect behaviour 
    
    if (keyID == 273):                                      # up
        if (keyEvent == 2):                                 #button is pressed
            new_state.veloX = walkVelocityForward
        elif(new_state.veloX == walkVelocityForward):       #button is released
            new_state.veloX = 0        
    elif (keyID == 274):                                    # down
        if (keyEvent == 2):                                 #button is pressed
            new_state.veloX = -walkVelocityForward
        elif (new_state.veloX == -walkVelocityForward):     #button is released
            new_state.veloX = 0 
    elif (keyID == 276):                                    # left
        if (keyEvent == 2):                                 #button is pressed
            new_state.veloY = walkVelocityLeft
        elif (new_state.veloY == walkVelocityLeft):         #button is released
            new_state.veloY = 0
    elif (keyID == 275):                                    # right
        if (keyEvent == 2):                                 #button is pressed
            new_state.veloY = -walkVelocityLeft
        elif (new_state.veloY == -walkVelocityLeft):        #button is released
            new_state.veloY = 0 
    elif (keyID == 97):                                     #a- rotate left
        if (keyEvent == 2):                                 #button is pressed
            new_state.veloT = rotateVelocityLeft
        elif (new_state.veloT == rotateVelocityLeft):       #button is released
            new_state.veloT = 0 
    elif (keyID == 115):                                    #s- rotate right right
        if (keyEvent == 2):                                 #button is pressed
            new_state.veloT = -rotateVelocityLeft
        elif (new_state.veloT == -rotateVelocityLeft):      #button is released
            new_state.veloT = 0 

    #do movement
    if  ((old_state.veloX != new_state.veloX) or \
            (old_state.veloY != new_state.veloY) or \
            (old_state.veloT != new_state.veloT) or \
            (old_state.superSpeed != new_state.superSpeed) ):
    
        if (new_state.superSpeed == 1):
            sX = 0
            if (new_state.veloX > 0):   sX = 1
            elif (new_state.veloX < 0): sX = -1
            
            sY = 0
            if (new_state.veloY > 0):   sY = 1
            elif (new_state.veloY < 0): sY = -1
            
            sT = 0
            if (new_state.veloT > 0):   sT = 1
            elif (new_state.veloT < 0): sT = -1
                
            display.execute("walk: x:" + str(sX) + "\t y:"+ str(sY) + "\t t:" + str(sT) + "\t stiff:" + str(new_state.stiff))
            motion.setWalkTargetVelocity(sX,sY,sT,1)
            display.done()
        else:  
            display.execute("walk: x:" + str(new_state.veloX) + "\t y:"+ str(new_state.veloY) + "\t t:" + str(new_state.veloT) + "\t stiff:" + str(new_state.stiff))
            motion.setWalkTargetVelocity(new_state.veloX, new_state.veloY, new_state.veloT,1)
            display.done()
            
        #oldstate is a shallow copy of the just processed newstate!
        old_state = copy.copy(new_state)
    