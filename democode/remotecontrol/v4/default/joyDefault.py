import motions
import copy
import time

motion = None
old_state = None
new_state = None

# 'normal' walking speeds
walkVelocityForward = 0.4     
walkVelocityLeft = 0.5
rotateVelocityLeft = 0.4

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
    text  = "   A = stand-up when fallen\n"
    text += "   B = toggle stiffness\n"
    text += "   X = maximum speed\n"
    text += "   LB = shoot with left leg\n"
    text += "   RB = shoot with right leg\n"
    text += "   right joystick, pushed to left = rotate left\n"
    text += "   right joystick, pushed to right = rotate right\n"
    text += "   button-up = move forward\n"
    text += "   button-down = move backward\n"
    text += "   button-left = move left\n"
    text += "   button-right = move right\n"
    text += "   start = pauze mode (stance, stiff=off)\n"
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
    #see below for available buttons and their event-data
    
    #print event data
    #display.execute(str(event))
    #display.done()
    
    # a button is pressed
    if (input.type == 10):
        button = input.dict["button"]
    
        #only perfom action when robot is not walking!
        if (not (motionclass.isWalking())):
            if (button == 0):       #A - stand-up when falling down
                display.execute("standing up")
                motion.standUp()
                display.done()
            elif (button == 1):     #B - toggle stiffness
                if (new_state.stiff == 1):
                    display.execute("stiffness off")
                    motion.kill()
                    new_state.stiff = 0
                else:
                    display.execute("stiffness on")
                    motion.stiff()
                    new_state.stiff = 1
                display.done()
            elif (button == 4):     #LB - shoot with left leg
                display.execute("shoot left")
                motion.normalPose()
                motion.cartesianLeft(0,0.08,0)
                display.done()
            elif (button == 5):     #RB - shoot with right leg
                display.execute("shoot right")
                motion.normalPose()
                motion.cartesianRight(0,0.08,0)
                display.done()
            elif (button == 7):     #start-button
                display.execute("Pausing")
                motion.stance()
                time.sleep(2)
                motion.kill()
                new_state.stiff = 0
                display.done()
       

    #superspeed
    if (input.type == 10) or (input.type == 11):
        button = input.dict["button"]
        if (button == 2):        #X (superspeed)
            if (input.type == 2):       #button is pressed
                new_state.superSpeed = 1
            else:                     #button is released
                new_state.superSpeed = 0

   
    #WALKING
    
    #arrows        
    if (input.type == 9):
        dir = input.dict["value"]
        
        #set veloY
        if (dir[0] == 0):    #no movement
            new_state.veloY = 0
        elif (dir[0] == 1):  #right
            new_state.veloY = -walkVelocityLeft
        elif (dir[0] == -1): #left
            new_state.veloY = walkVelocityLeft
        
        #set veloX
        if (dir[1] == 0):    #no movement
            new_state.veloX = 0
        elif (dir[1] == 1):  #forward
            new_state.veloX = walkVelocityForward
        elif (dir[1] == -1): #backward
            new_state.veloX = -walkVelocityForward
            
    #rotate robot            
    if (input.type == 7):
        angle = round(input.dict["value"], 1)
        axis = input.dict["axis"]
        
        if (axis == 4):             #right joystick, horizontal movement
            if (angle < -0.6):      #rotate left
                new_state.veloT = rotateVelocityLeft
            elif (angle > 0.6):     #rotate right
                new_state.veloT = -rotateVelocityLeft
            elif ((angle  > -0.2) and (angle < 0.2)): 
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
        
#######################################################
# 'input' is defined as a struct:
# input.joy = ID of joystick pressed [not used]
# input.type = a number defining the pressed button
# input.dict = dictionary with vales
#   -> if type = {10,11}, dict["button"] is the value/identifier of the pressed button
#   -> if type = { 7, 9}, dict["values"] is the values/identifier of the pressed button
#
#
#TYPES:
# 7 - joysticks         dict.["value"]      movement
#      > axis 0:        -1..1 [0=default]   joystick left, horizontal
#      > axis 1:        -1..1 [0=default]   joystick left, vertical
#      > axis 2:        -1..1 [0=default]   joystick right, vertical
#      > axis 3:        -1..1 [0=default]   joystick right, horizontal

# 9 - arrows            dict.["value"]
#       > left:         (-1, 0)
#       > left-top:     (-1, 1)
#       > top:          ( 0, 1)
#       > top-right:    ( 1, 1)
#       > right:        ( 1, 0)
#       > right-bottom: ( 1,-1)
#       > bottom:       ( 0,-1)
#       > bottom-left:  (-1,-1)

# 10 - button press     dict.["button"]
# 11 - button release   dict.["button"]
#       > A:            0
#       > B:            1
#       > X:            2
#       > Y:            3
#       > LB:           4
#       > RB:           5
#       > back:         6
#       > start:        7
