import motions
import copy
import time

motion = None
old_state = None
new_state = None

class state:
    stiff      = 0
    veloX      = 0
    veloY      = 0
    veloT      = 0
    superSpeed = 0

def init(motionproxy, poseproxy):
    global motion, old_state, new_state
    motion = motions.Motions(motionproxy, poseproxy)
    old_state = state()
    new_state = state()
    new_state.stiff = 1 if(motionproxy.getStiffnesses('Body')[0] > 0) else 0

def buttonDefinition():
    text  = "   r = stand-up when fallen\n"
    text += "   t = toggle stiffness\n"
    text += "   p = pauze mode (stance, stiff=off)\n"
    text += "   d = shoot with left leg\n"
    text += "   f = shoot with right leg\n"
    text += "   a = rotate left leg\n"
    text += "   s = rotate right leg\n"
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
                
    #actions which are allowed todo when walking
    
    #toggle 'superspeed'
    if (keyID == 32):             # space-bar
        if (keyEvent == 2):       #button is pressed
            new_state.superSpeed = 1
        else:                     #button is released
            new_state.superSpeed = 0
   

   
   
    #WALKING
    
    if (keyID == 273):             # up
        if (keyEvent == 2):        #button is pressed
            new_state.veloX = walkVelocityForward
        else:                      #button is released
            new_state.veloX = 0        
    elif (keyID == 274):           # down
        if (keyEvent == 2):        #button is pressed
            new_state.veloX = -walkVelocityForward
        else:                      #button is released
            new_state.veloX = 0 
    elif (keyID == 276):           # left
        if (keyEvent == 2):        #button is pressed
            new_state.veloY = walkVelocityLeft
        else:                      #button is released
            new_state.veloY = 0
    elif (keyID == 275):           # right
        if (keyEvent == 2):        #button is pressed
            new_state.veloY = -walkVelocityLeft
        else:                      #button is released
            new_state.veloY = 0 
    elif (keyID == 97):            #a- rotate left
        if (keyEvent == 2):        #button is pressed
            new_state.veloT = rotateVelocityLeft
        else:                      #button is released
            new_state.veloT = 0 
    elif (keyID == 115):           #s- rotate right right
        if (keyEvent == 2):        #button is pressed
            new_state.veloT = -rotateVelocityLeft
        else:                      #button is released
            new_state.veloT = 0 

    #do movement
    if  ((old_state.veloX != new_state.veloX) or \
            (old_state.veloY != new_state.veloY) or \
            (old_state.veloT != new_state.veloT) or \
            (old_state.superSpeed != new_state.superSpeed) ):
    
        if (new_state.superSpeed == 1):
            sX = 1 if (new_state.veloX > 0) else 0
            sY = 1 if (new_state.veloY > 0) else 0
            sT = 1 if (new_state.veloT > 0) else 0
            display.execute("walk: x:" + str(sX) + "\t y:"+ str(sY) + "\t t:" + str(sT) + "\t stiff:" + str(new_state.stiff))
            motion.setWalkTargetVelocity(sX,sY,sT,1)
            display.done()
        else:  
            display.execute("walk: x:" + str(new_state.veloX) + "\t y:"+ str(new_state.veloY) + "\t t:" + str(new_state.veloT) + "\t stiff:" + str(new_state.stiff))
            motion.setWalkTargetVelocity(new_state.veloX, new_state.veloY, new_state.veloT,1)
            display.done()
            
        old_state = copy.copy(new_state)
        