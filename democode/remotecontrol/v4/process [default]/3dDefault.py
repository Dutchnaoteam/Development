import motions
import copy
import time
import pygame

motion = None
old_state = None
new_state = None

# 'normal' walking speeds
walkVelocityForward = 0.4     
walkVelocityLeft = 0.5
rotateVelocityLeft = 0.4
noMovementVelocity = 0.01

#used state of robot: walking direction
class state:
    stiff      = 0
    veloX      = 0
    veloY      = 0
    veloT      = 0
    superSpeed = 0

#init event-processor
def init(IPADRESS):
    global motion, old_state, new_state
    PORT = 9559

    from naoqi import ALProxy
    motionProxy = ALProxy("ALMotion", IPADRESS, PORT)
    poseProxy = ALProxy("ALRobotPose", IPADRESS, PORT)
    motion = motions.Motions(motionProxy, poseProxy)
    
    old_state = state()
    new_state = state()
    new_state.stiff = 1 if(motionProxy.getStiffnesses('Body')[0] > 0) else 0

#retrieve button definition
def getButtonDefinition():
    text  = "   r = stand-up when fallen\n"
    text += "   t = toggle stiffness\n"
    text += "   p = pauze mode (stance, stiff=off)\n"
    text += "   d = shoot with left leg\n"
    text += "   f = shoot with right leg\n"
    text += "   a = rotate left leg\n"
    text += "   s = rotate right leg\n"
    text += "   3D mouse = movement\n"
    text += "   shift = stop moving\n"
    text += "   space = maximum speed\n"
    return text    

#process event
#
# When a event 'e' is executed, use to following statements to update the screen:
#   display.execute('<What command is send to the robot?>')
#   .... some executed code
#   display.done()
#
def processEvent(display, event):
    global old_state, new_state

    #event[0] = keypressed (2 = pressed, 3 = released)
    #event[1] = key-number:
    #               a - z = ascii value: 97 - 122
    #               space = 32
    #               up    = 273
    #               left  = 274
    #               right = 275
    #               down  = 276    
    
    if (event.type == pygame.USEREVENT):
        d = event.dict
        
        x = d["tz"]
        y = d["tx"]
        t = d["ry"]
        
        if (x > 10):
            new_state.veloX = -walkVelocityForward        
        elif (x < -10):
            new_state.veloX = walkVelocityForward
        else:
            new_state.veloX = noMovementVelocity        
            
        if (y > 10):
            new_state.veloY = -walkVelocityForward        
        elif (y < -10):
            new_state.veloY = walkVelocityForward
        else:
            new_state.veloY = noMovementVelocity        
        
        if (t == 1):
            new_state.veloT = rotateVelocityLeft        
        elif (t == -1):
            new_state.veloT = -rotateVelocityLeft
        else:
            new_state.veloT = noMovementVelocity        
        
    elif (hasattr(event, 'key')):
        
        keyEvent = event.type
        keyID = event.key
    
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
            if (keyID == 100):
                display.execute("shoot left")
                new_state.veloX = 0
                new_state.veloY = 0
                new_state.veloT = 0
                motion.setWalkTargetVelocity(0,0,0,1)
                motion.normalPose()
                motion.cartesianLeft(0,0.08,0)
                display.done()
            elif (keyID == 102):
                display.execute("shoot right")
                new_state.veloX = 0
                new_state.veloY = 0
                new_state.veloT = 0
                motion.setWalkTargetVelocity(0,0,0,1)
                motion.normalPose()
                motion.cartesianRight(0,0.08,0)
                display.done()
            elif (keyID == 303):
                new_state.veloX = 0
                new_state.veloY = 0
                new_state.veloT = 0
            elif (keyID == 112):
                display.execute("Pausing")
                new_state.veloX = 0
                new_state.veloY = 0
                new_state.veloT = 0
                motion.setWalkTargetVelocity(0,0,0,1)
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
   

    #toggle "no-movement" values
    if ((new_state.veloX == noMovementVelocity) or (new_state.veloX == -noMovementVelocity)):
        new_state.veloX = -new_state.veloX
    if ((new_state.veloY == noMovementVelocity) or (new_state.veloY == -noMovementVelocity)):
        new_state.veloY = -new_state.veloY
    if ((new_state.veloT == noMovementVelocity) or (new_state.veloT == -noMovementVelocity)):
        new_state.veloT = -new_state.veloT
    
    #do movement
    if  ((old_state.veloX != new_state.veloX) or \
            (old_state.veloY != new_state.veloY) or \
            (old_state.veloT != new_state.veloT) or \
            (old_state.superSpeed != new_state.superSpeed) ):
    
        if (new_state.superSpeed == 1):
            sX = 0
            if (new_state.veloX > noMovementVelocity):   sX = 1
            elif (new_state.veloX < -noMovementVelocity): sX = -1
            
            sY = 0
            if (new_state.veloY > noMovementVelocity):   sY = 1
            elif (new_state.veloY < -noMovementVelocity): sY = -1
            
            sT = 0
            if (new_state.veloT > noMovementVelocity):   sT = 1
            elif (new_state.veloT < -noMovementVelocity): sT = -1
                
            display.execute("walk: x:" + str(sX) + "\ty:"+ str(sY) + "\tt:" + str(sT) + "\t stiff:" + str(new_state.stiff))
            motion.setWalkTargetVelocity(sX,sY,sT,1)
            display.done()
        else:  
            display.execute("walk: x:" + str(new_state.veloX) + "\ty:"+ str(new_state.veloY) + "\tt:" + str(new_state.veloT) + "\t stiff:" + str(new_state.stiff))
            motion.setWalkTargetVelocity(new_state.veloX, new_state.veloY, new_state.veloT,1)
            display.done()
            
        old_state = copy.copy(new_state)
        