import time
# PROGAMMED CONTROLS:
# (below you can find types/values of each possible activated button/input)

#Buttons
# A     : standup
# B     : toggle stiffness
# X     : stance
# RB    : shoot right 
# LB    : shoot left
# back  : quit   (goto stance, stiffness=0, shutdown)
# start : stance (goto stance, stiffness=0)

#Arrows
# left  : move left
# top   : move forward
# right : move right
# down  : move backwards

#Joysstick (right): 
# right : turn right
# left  : turn left

#constants (max 0.5!)
# --> 'superSpeed' doubles speed!
walkVelocityX = 0.4     
walkVelocityY = 0.5
rotateVelocity = 0.4

#variables
stiff = 0
veloX = 0
veloY = 0
veloT = 0
veloX_old = 0
veloY_old = 0
veloT_old = 0
superSpeed = 0
superSpeed_old = 0
def processInput(input, motionclass):
    global walkVelocityX, walkVelocityY, rotateVelocity
    global stiff, veloX, veloY, veloT
    global veloX_old, veloY_old, veloT_old
    global superSpeed, superSpeed_old
    
    #button presse 
    if (input.type == 10):
        button = input.dict["button"]
    
        #only perfom action when robot is not walking!
        if (not (motionclass.isWalking())):
            if (button == 0):       #A - stand-up when falling down
                print "standing up"
                motionclass.standUp()
            elif (button == 1):     #B - toggle stiffness
                if (stiff == 1):
                    print "stiffness off"
                    motionclass.kill()
                    stiff = 0
                else:
                    print "stiffness on"
                    motionclass.stiff()
                    stiff = 1
            elif (button == 4):     #LB - shoot with left leg
                print "shoot left"
                motionclass.cartesianLeft(0,0.05,0)
            elif (button == 5):     #RB - shoot with right leg
                print "shoot right"
                motionclass.cartesianRight(0,0.05,0)
        
        #actions which are allowed todo when walking
        if (button == 6):       #back-button
            print "Quitting..." 
            motionclass.stance()
            time.sleep(2)
            motionclass.kill()
            stiff = 0
            return "quit"
        elif (button == 7):     #start-button
            print "pausing"
            motionclass.stance()
            time.sleep(2)
            motionclass.kill()
            stiff = 0
        elif (button == 2):     #X (superspeed)
            superSpeed = 1
   
    #button release   
    if (input.type == 11):
        button = input.dict["button"]
        if (button == 2):       #X
            superSpeed = 0
    
    #arrows        
    if (input.type == 9):
        dir = input.dict["value"]
        
        #set veloY
        if (dir[0] == 0):    #no movement
            veloY = 0
        elif (dir[0] == 1):  #right
            veloY = -walkVelocityY
        elif (dir[0] == -1): #left
            veloY = walkVelocityY
        
        #set veloX
        if (dir[1] == 0):    #no movement
            veloX = 0
        elif (dir[1] == 1):  #forward
            veloX = walkVelocityX
        elif (dir[1] == -1): #backward
            veloX = -walkVelocityX

    #joystick            
    if (input.type == 7):
        angle = input.dict["value"]
        
        if (angle < -0.4):       #rotate left
            veloT = rotateVelocity
        elif (angle > 0.4):  #rotate right
            veloT = -rotateVelocity
        elif ((angle  > -0.005) and (angle < 0.005)): 
            veloT = 0 
        
    #do movement
    if ((veloX != veloX_old) or (veloY != veloY_old) or (veloT != veloT_old) or (superSpeed != superSpeed_old)):
        
        if ((superSpeed == 1) and (superSpeed_old == 0)):
            #set superspeed
            veloX = veloX*2
            veloY = veloY*2
            veloT = veloT*2
        elif ((superSpeed == 0) and (superSpeed_old == 1)):
            # go back to normal speed
            veloX = veloX/2
            veloY = veloY/2
            veloT = veloT/2         
        elif ((superSpeed == 1) and (superSpeed_old == 1)):
            # set new determined speed to superspeed
            if (veloX != veloX_old):
                veloX = veloX*2
            if (veloY != veloY_old):
                veloY = veloY*2
            if (veloT != veloT_old):
                veloT = veloT*2                
            
        print "executing: x:" + str(veloX) + " y:"+ str(veloY) + " t:" + str(veloT) + " stiff:" + str(stiff) + " speed:" + str(superSpeed)
        motionclass.setWalkTargetVelocity(veloX,veloY,veloT,1)
        
        veloX_old = veloX
        veloY_old = veloY
        veloT_old = veloT
        superSpeed_old = superSpeed
    return None
    
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
