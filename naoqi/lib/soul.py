
## NOTES TO EDITORS
# todo: Implement New Gamecontroller
# TODO: Fix locategoal
# TODO: Fix doorlopen when penalized
# TODO: Cleaning visioninterface

## FILE DESCRIPTION
# File: soul.py
# Description: The nao's footballplaying soul.
# * states call phases
# * phases call moves
# * Transitions between states through global int state
# * Transitions between phases through global string phase
# state : e.g. 1
# phase : e.g. 'BallFound'

from naoqi import ALProxy
import gameStateController          # Controls the states of the nao
import time
import math    
import Queue
import motions as mot                 # All motion actions
import visionInterface as vis         # All vision actions
import coach
import walking    
    
# Start the ballfinding thread
visThread = vis.Vision('VISION')
visThread.start()

# audio settings
ttsProxy = ALProxy('ALTextToSpeech', '127.0.0.1', 9559)
audProxy = ALProxy('ALAudioDevice', '127.0.0.1', 9559)

# Ball location
ball_loc = dict()

# Initialization of archtitecture
state = 0
phase = 'BallNotFound'

# LED and camera settings
ledProxy = ALProxy('ALLeds', '127.0.0.1', 9559)
vidProxy = ALProxy('ALVideoDevice', '127.0.0.1', 9559)
# Use the chin camera
vidProxy.setParam(18,1)

# Dictionary that stores if a phase has been called once already.
firstCall = {'Initial' : True, 
             'Ready' : True, 
             'Set': True, 
             'Playing': True, 
             'Penalized': True, 
             'BallFoundKeep' : True,
             'BallNotFoundKeep' : True,
             'BallFound' : True,
             'BallNotFound' : True}

# Gamecontroller
sc = gameStateController.stateController('stateController')

# Robots own variables
robot = sc.getRobotNumber()

# Local memProxy for storing information (coaching)
memProxy = ALProxy('ALMemory', '127.0.0.1', 9559)
memProxy.insertListData([['dntBallDist', '', 0], ['dntPhase', 0, 0], ['dntNaoNum', robot, 0]])

# specify the coach here!
try:
    coachproxy = ALProxy('ALMemory', '192.168.1.14', 9559)
except: 
    pass
    
# If keeper -> different style of play
playerType = 0
if (robot == 1):
    playerType = 1

    # Keeper coaches other naos
    try:
        # specify all playing naos here!
        coachThread = coach.Coach('coach', ['192.168.1.14', '192.168.1.13'])
        coachThread.start()
        print 'Coaching started' 
    except:
        pass
        
# If gameController is connected then initialize the teamColor, kickOff and penalty mode. Otherwise, use the button interface.
teamColor = None
kickOff = None
penalty = None
(teamColor, kickOff, penalty) = sc.getMatchInfo()   

## STATES (Gamestates)
# Initial()
# Ready()
# Set()
# Playing()
# Penalized()
# Finished()

# Initial state: do nothing, stand ready for match
# ledProxy: All ledProxy are off
# Motions: NormalPose
def Initial():
    global phase                    # to change, call global, else not possible
    global ball_loc
    global firstCall
    
    if firstCall['Initial']:
      
        print 'In initial state'
        visThread.stopScan()                  # do not find the ball when in Initial
        print 'TeamColor: ' , teamColor   # print the teamcolor as a check

        # Empty variables
        ball_loc = dict()
        
        # Team color must be displayed on left foot (Reference to rules)        
        ledProxy.off('AllLeds')       
        if (teamColor == 0):
            ledProxy.fadeRGB('LeftFootLeds', 0x000000ff, 0)
        else:
            ledProxy.fadeRGB('LeftFootLeds', 0x00ff0000, 0)
        
        mot.stiff()        # stiffness on (if it wasnt already)
        mot.setHead(0,0)   # head in normal position

        # if a regular player
        if playerType == 0:
            phase = 'BallNotFound'
            mot.normalPose(True) # normalPose, forcing call 
        # if a keeper
        else:
            phase = 'BallNotFoundKeep'
            mot.keepNormalPose()
            
        firstCall['Initial']   = False   
        firstCall['Ready']     = True
        firstCall['Set']       = True
        firstCall['Playing']   = True
        firstCall['Penalized'] = True

# Ready state: possible positioning
# ledProxy:  Chest Blue
def Ready():
    global firstCall
    
    # Reinitialize phases, stand ready for match
    if firstCall['Ready']:
        
        print 'In ready state'
        mot.killWalk()
        ledProxy.fadeRGB('ChestLeds',0x000000ff, 0) # set ChestLeds

        firstCall['Initial'] = True   
        firstCall['Ready']   = False
        firstCall['Set']     = True
        firstCall['Playing'] = True
        firstCall['Penalized'] = True
        
# Set state: start searching for ball. CAUTION: Game is started in Set phase instead of Initial in penalty shootout!
# ledProxy:  Chest Yellow
def Set():
    global teamColor
    global kickOff
    global phase
    global firstCall
    
    # if the first iteration
    if firstCall['Set']:
        
        # update info about team, it is possible that game is started in set phase
        (teamColor, kickOff, penalty) = sc.getMatchInfo()    
        
        print 'In set state'
        visThread.goBall()                                  # start ballscan

        print 'TeamColor: ' , teamColor               # print teamcolor as a check
        
        # initial pose, if not already in it
        mot.stiff()
        if playerType == 0:
            mot.normalPose()
        else:
            mot.keepNormalPose()
        
        audProxy.setOutputVolume(0)                    # set volume to zero    
        ledProxy.fadeRGB('ChestLeds', 0x00ffff00, 0)    # set chestledcolor to green
        
        # Team color must be displayed on left foot (Reference to rules)
        if (teamColor == 0):
            ledProxy.fadeRGB('LeftFootLeds', 0x000000ff, 0)
        else:
            ledProxy.fadeRGB('LeftFootLeds', 0x00ff0000, 0)
        
        firstCall['Initial']   = True   
        firstCall['Ready']     = True
        firstCall['Set']       = False
        firstCall['Playing']   = True
        firstCall['Penalized'] = True

    # Head movements allowed in the set state
    # FIND A BALL #
    if phase != 'BallFound' and phase != 'BallFoundKeep':
        if vis.scanCircle(visThread, 0.2):
            if playerType == 0:
                phase = 'BallFound'
            else:
                phase = 'BallFoundKeep'

    # Keep finding the ball, it might move (or does it?)
    if not(visThread.findBall()):
            if playerType == 0:
                phase = 'BallNotFound'
            else:
                phase = 'BallNotFoundKeep'
        
# Playing state: play game according to phase transitions
# ledProxy:  Chest Green
def Playing():
    global phase
    global firstCall
    
    if firstCall['Playing']:
        print 'In playing state'
        ledProxy.fadeRGB('ChestLeds', 0x0000ff00, 0)
        firstCall['Initial']   = True   
        firstCall['Ready']     = True
        firstCall['Set']       = True
        firstCall['Playing']   = False
        firstCall['Penalized'] = True
        
    # if nao has fallen down, stand up
    if mot.standUp():
        print 'Fallen'
        # relocalize
    else:
        pass
        # localize
    
    try:
        coachPhase = coachproxy.getData('dnt'+str(robot))
        if coachPhase:
            print 'Coach says: ', coachPhase
            phase = coachPhase
    except:
        pass
    # Execute the phase as specified by phase variable
    phases.get(phase)()

# Penalized state
# ledProxy:  Chest Red
def Penalized():
    global phase
    global firstCall
    
    if firstCall['Penalized']:
        print 'In penalized state'

        visThread.stopScan()          # stop looking for the ball
        mot.killWalk()          # stop walking
        mot.stiff()             # stiffness on (just in case?)
        
        mot.keepNormalPose()
        
        ledProxy.fadeRGB('ChestLeds',0x00ff0000, 0) # ledProxy on chest: red
        
        if playerType == 0:     # if a player, goto unpenalized phase
            phase = 'Unpenalized'
        else:                   # if a keeper, go to ballnotfoundkeep if penalty shootout
            if sc.getSecondaryState():
                phase = 'BallNotFoundKeep'
            else:               # else, become a player
                phase = 'Unpenalized'

        firstCall['Initial']   = True   
        firstCall['Ready']     = True
        firstCall['Set']       = True
        firstCall['Playing']   = True
        firstCall['Penalized'] = False
                
def Finished():
  
    visThread.stopScan()            # stop looking for the ball
    ledProxy.off('AllLeds')         # turn off ledProxy
    mot.killWalk()                  # stop walking
    mot.stance()                    # sit down
    mot.setHead(0,0)                # set head straight
    time.sleep(1)                   # wait until seated etc
    mot.killKnees()                 # stiffness off to prevent heating
    if not sc.getSecondaryState():
        sc.close()
        audProxy.setOutputVolume(85)       # volume on
    
## PHASES

# KEEPER
# BallFoundKeep()
# BallNotFoundKeep()
# BallApproaching()
# InGoalArea()

def BallFoundKeep():
    global phase
    global ball_loc
    global firstCall
    
    if firstCall['BallFoundKeep']:
        mot.stance()
        firstCall['BallFoundKeep'] = False
        
    maxlength = 6
    halfmaxlength = (maxlength/2.0)

    #  FIND A BALL  #
    ball = visThread.findBall()        
    if ball:    
        #if ball[0] < 0.3 and (ball[1] < 0.5 or ball[1] > -0.5):
        #    phase = 'InGoalArea'
        #    mot.move('normalPose')
        #    visThread.findBall()
        #    return True
        (x,y) = ball
        memProxy.insertData('dntBallDist', math.sqrt(x**2 + y**2))

        if len(ball_loc) == 0:
            ball_loc[ 0 ] = ball
            
        elif len(ball_loc) < maxlength:
            # add to dict, key being a number from maxlength to 0. Last position is position 8 (key 7)
            # but only if ball_loc is already filled and ball is a new location
            if ball != ball_loc[ len(ball_loc) - 1 ]:
                ball_loc[ len(ball_loc) ] = ball
        
        elif ball != ball_loc[ maxlength - 1 ]:
            xold = 0
            yold = 0
            xnew = 0
            ynew = 0

            # shift elements sidewards, newest ballloc becomes nr <maxlength>, oldest is thrown away
            for number in ball_loc:
                (x,y) = ball_loc[number]
                if number != 0:
                    ball_loc[number-1] = (x,y)
                            
                # add to xold/new and yold/new variables, number 0 is oldest, number <maxlength> most recent ballloc
                if number == 0:
                    pass
                elif 0 < number < halfmaxlength + 1:
                    xold += x / halfmaxlength
                    yold += y / halfmaxlength
                else:
                    xnew += x / halfmaxlength
                    ynew += y / halfmaxlength
            
            xnew += ball[0] / halfmaxlength
            ynew += ball[1] / halfmaxlength
            ball_loc[maxlength-1] = ball
                

            # calc diff in distance
            distold = math.sqrt(xold**2 + yold**2)
            distnew = math.sqrt(xnew**2 + ynew**2)
            speed = distold - distnew
            
            print 'Ball moving from ', xold, yold, 'to', xnew, ynew, '(mean). Speed', speed
            
            # calculate direction if speed is high enough
            if speed > 0.225:
                #mot.stiffKnees()
                
                # This is all triangular magic using similarity between two triangles formed by balllocations and Nao.
                # Keep in mind that y-axis is inverted and that x is forward, y is sideways!
                #
                #                                              x 
                #      (yold,xold)                             |
                #            .                                 |    
                #            | \                               |
                #          B |   \                             |
                #            |     \                           |
                #            |_______.  (ynew,xnew )           |
                #                A   | \                       |
                #                    |   \                     |
                #                  C |     \                   |
                #                    |       \                 |
                #     y _____________|_________._______________.___________ -y
                #                            (dir,0)           Nao = (0,0)
                #                               
                #                    [--- D ---]
                
                # Mathematical proof:
                # A = yold - ynew
                # B = xold - xnew
                # C = xnew
                # D = ynew - dir
                
                # Similar triangles -> C / B = D / A 
                #                      D     = A*C/B
                #                      D     = ynew - dir
                #                      dir   = A*C/B - ynew
                
                dir = (yold - ynew )* xnew / (xold - xnew) - ynew
                
                # if a direction has been found, clear all variables 
                ball_loc = dict()
                visThread.clearCache()
                
                ball_loc['Direction'] = dir
                phase = 'BallApproaching'
                firstCall['BallFoundKeep'] = True
                print 'Direction', dir
        
    else:
        #mot.stiffKnees()
        phase = 'BallNotFoundKeep'
        firstCall['BallFoundKeep'] = True
        
# Keeper lost track of ball
def BallNotFoundKeep():
    global phase
    global ball_loc
    
    # if a ball is found
    if vis.scanCircle(visThread, 0.2):
        # reinitialize
        ball_loc = dict()
        phase = 'BallFoundKeep'
        firstCall['BallNotFoundKeep'] = True
    elif firstCall['BallNotFoundKeep']:
        memProxy.insertData('dntBallDist', 0)
        mot.keepNormalPose()
        firstCall['BallNotFoundKeep'] = False

# Ball approaches keeper and goal area at considerable speed
def BallApproaching():
    global phase
    global ball_loc

    dir = ball_loc['Direction']
    
    if dir >= 0.25:
        print 'Dive right'
        mot.diveRight()
    elif dir <= -0.25:
        print 'Dive left'
        mot.diveLeft()
    elif dir < 0.25 and dir >= 0:
        print 'Step right'
        mot.footRight()
    elif dir > -0.25 and dir < 0:
        print 'Step left'
        mot.footLeft()
    phase = 'BallNotFoundKeep'
    
def InGoalArea():
    global phase
    mot.normalPose()
    ball = visThread.findBall()    
    if ball:
        (x,y) = ball
        print x,y

        if x < 0.17 and -0.06 < y < -0.02:
            print 'Kick'
            # BLOCKING CALL: FIND BALL WHILE STANDING STILL FOR ACCURATE CORRECTION
            mot.killWalk()
            mot.rKickAngled(0)
            phase = 'ReturnToGoal'
            
        else:            
            # hacked influencing of perception, causing walking forward to have priority
            theta = math.atan(y/x) / 2.5
            
            x = 3 * (x-0.17)
            
            if  -0.1 < y < 0.1 :
                y = 0.5 * y
            else:
                y = 2.0 * y
            
            mot.SWTV(x , y, theta, 1.0)
    else:
        print 'No Ball'
        mot.killWalk()
        phase = 'ReturnToGoal'

    
'''
def UnpenalizedKeep():
    global phase
    global ball_loc
    while  not( ball_loc.empty() ):
        ball_loc.get()
    ball_loc.put( (10, 10, 0) )
    phase = 'ReturnToGoal'
'''

def ReturnToGoal():
    global ball_loc
    
    if visThread.active():
        visThread.stopScan()
    
    # goalScan
    if 'Goal' in ball_loc:
        yawRange = ball_loc['Goal']
        ball_loc = dict()
        print 'Checking in range 1.5 *', yawRange
        goal = vis.scanCircleGoal((yawRange[0] * 1.5, yawRange[1] * 1.5))
    else:
        goal = vis.scanCircleGoal()
        
    if goal:
        
        (color, (post1, post2)) = goal
        goalColor = None
        if color == "Blue":
            goalColor = 0
        else:
            goalColor = 1
        if abs(post1 - post2) > 0.3 and teamColor == goalColor:
            ball_loc['Goal'] = {0:post1, 1:post2}
        
        print 'goal, team:', goalColor, teamColor    
        if teamColor == goalColor: 
            # walk towards goal
            angleToGoal = abs(post1 - post2) # if in between two posts, angleToGoal = 1/4pi and -1/4 pi respectively
            if angleToGoal == 3:
                if post1 < post2:
                    mot.walkTo(0, 0, 3 - post2 )
                    print 'done'
                    phase = 'BallNotFoundKeep'
                elif post2 < post1:
                    mot.walkTo(0, 0, 3 - post1 )
                    print 'done'
                    phase = 'BallNotFoundKeep'
                else:
                    print 'One pole found, now what?'
                    mot.postWalkTo(0, 0, 1)
            else:
                angle = (post1 + post2) / 2.0
                x = math.cos( angle )          # maximum for angle zero and minimum for angle pi/2
                y = math.sin( angle )          # maximum for angle -pi/2 and minimum for angle pi/2
                t = math.atan(y/x)
                
                # correction, max value for angle should be pi.
                c = 1 - abs(post1 - post2) /3.14159 
                
                # correction based on angle 
                x = c * x
                y = c * y
                print 'walking towards', x, y, t
                mot.walkTo(x/5.0, y/5.0, t/5.0)
        else:
            print 'other goal found'
            mot.SWTV(0,0,0,0)
            mot.postWalkTo(0,0,1.0)
    else:
        print 'no or other goal found'
        mot.postWalkTo(0, 0, 1.5)
        
            
# PLAYER
# BallFound()
# BallNotFound()
# Kick()
# Unpenalized()
# ReturnField()

def Standby():
    global phase
    ttsProxy.say('Waiting')
    mot.killWalk()
    time.sleep(1)
    phase = 'BallFound'

def BallFound():
    global phase
    
    if firstCall['BallFound']:
        ledProxy.fadeRGB('RightFaceLeds', 0x0000ff00, 0)
        firstCall['BallFound'] = False
        
    # FIND A BALL #
    ball = visThread.findBall()
    if ball:
        (x,y) = ball
        print x,y
        memProxy.insertData('dntPhase', 'BallFound')
        memProxy.insertData('dntBallDist', math.sqrt(x**2 + y**2))

        if x < 0.17 and -0.02 < y < 0.02:
            print 'Kick'
            # BLOCKING CALL: FIND BALL WHILE STANDING STILL FOR ACCURATE CORRECTION
            mot.killWalk()
            phase = 'Kick'
            
        else:            
            # hacked influencing of perception, causing walking forward to have priority
            if x > 0.3:
                walking.walk(tr_max = 4.5, tr_min = 2.5, step_max = 25, step_min = 15, x_step = 0.035, y_step = 0.035, t_step = 17.5)
            else:
                walking.walk()
            
            theta = math.atan(y/x) / 2.5
            x = 3 * (x-0.17)
            
            if  -0.1 < y < 0.1 :
                y = 0.5 * y
            else:
                y = 2.0 * y
            
            mot.SWTV(x , y, theta, 1.0)
    else:
        print 'No Ball'
        mot.killWalk()
        phase = 'BallNotFound'

def BallNotFound():
    global ball_loc
    if firstCall['BallNotFound']:
        memProxy.insertData('dntPhase', 'BallNotFound')
        memProxy.insertData('dntBallDist', 0)    
        ledProxy.fadeRGB('RightFaceLeds',0x00ff0000, 0) # no ball, led turns red
        firstCall['BallNotFound'] = False
        
    global phase
    # try to find a ball
    if vis.scanCircle(visThread, 0.2):
        phase = 'BallFound'
        firstCall['BallNotFound'] = True
    # if no ball is found
    else:
        # circle slowly
        mot.postWalkTo(0, 0, 1.3)
        
def Kick():
    global phase
    memProxy.insertData('dntPhase', 'Kick')
    visThread.stopScan()
    
    ledProxy.fadeRGB('LeftFaceLeds',0x00000000, 0) # no goal yet, left led turns black
    ledProxy.fadeRGB('RightFaceLeds', 0x00ff0000, 0) # no ball anymore, right led turns red
    
    # scan for a goal
    goal = vis.scanCircleGoal()
    
    visThread.goBall()
    
    # Case 0 : Ball stolen/lost.
    # Check if the ball is still there, wait until ball is found or 1 second has passed
    now = time.time()
    while time.time() - now < 1 and not(visThread.findBall()):
        pass    
    ball = visThread.findBall()
    if not ball:
        print 'Ball gone'
        phase = 'BallNotFound'
    elif ball[0] > 0.25 or ball[1] > 0.1 or ball[1] < -0.1:
        print 'Ball too far'
        phase = 'BallFound'
    elif ball and not goal:
        mot.walkTo(0,0.04 + ball[1],0)
        mot.rKickAngled(0)
        phase = 'BallNotFound'
    else:
        print "Kick phase:", goal
        ledProxy.fadeRGB('RightFaceLeds', 0x0000ff00, 0) # no ball anymore, right led turns red
        
        # else a goal is found, together with it's color
        (color, kickangles ) = goal        
        (first, second) = kickangles 
        kickangle = (3 * first + second) / 4.0   # kick slightly more towards left pole 
        
        if color == 'Blue':
            goalColor = 0
            ledProxy.fadeRGB('LeftFaceLeds',0x000000ff, 0) # blue goal            
        else:
            goalColor = 1
            ledProxy.fadeRGB('LeftFaceLeds',0x00ff3000, 0) # yellow goal , anyone got a better value?

            
        # Cases 1-3, if you see your own goal, kick to the other side
        if goalColor == teamColor:
            # Case 1, goal is left, kick to the right. 
            if kickangle >= 0.7:
                kickangle = -1
            # Case 2, goal is right, kick to the left.
            if kickangle <= -0.7:
                kickangle = 1
            else:
            # Case 3, goal is straight forward, HAK
                mot.walkTo(0,0.04 + ball[1],0)
                mot.normalPose()
                time.sleep(0.5)
                ledProxy.fadeRGB('LeftFaceLeds',0x00000000, 0) # led turns black
                mot.hakje(kickangle * -0.1)
                phase = 'BallNotFound'
        else:                    
            # Case 4, other player's goal is found.
            # Kick towards it. 
            if kickangle > 1.1:
                kickangle = 1.1
            if kickangle < -1.1:
                kickangle = -1.1
            
            # conversion to real kickangle
            convert = 1.1 # (60 degrees rad)
            
            # kick either left or right
            if kickangle <= 0:
                mot.walkTo(0, -0.04 + ball[1], 0)
                mot.lKickAngled(kickangle/ -convert)
            elif kickangle > 0:
                mot.walkTo(0, 0.04 + ball[1], 0)
                mot.rKickAngled(kickangle/ convert)
            
            ledProxy.fadeRGB('LeftFaceLeds',0x00000000, 0)
            phase = 'BallNotFound'

# When unpenalized, a player starts at the side of the field
def Unpenalized():
    global phase
    global playertype

    memProxy.insertListData([['dntBallDist', '', 0], ['dntPhase', 'ReturnField', 0]])

    # if case this nao is a keeper, convert to player until state changes to initial/ready/set, where it is set to keeper again
    playertype = 0
    
    visThread.goBall()
    # so no matter what, it's always good to walk forward (2 meters, to the center of the field)
    if not(mot.isWalking()):
        mot.postWalkTo(2, 0, 0)
    phase = 'ReturnField'

# and while you're walking forward..
def ReturnField():
    global phase
    if mot.isWalking():
        # ..search for a ball
        if vis.scanCircle(visThread, 0.2):
            # make an extra check to see if it's not incidental
            if visThread.findBall():
                phase = 'BallFound'
    else:
        phase = 'BallNotFound'

##### OPERATING SYSTEM #####
# The soul of the robot

def awakeSoul():
    sc.start()
    state = 0
    while(state != 4 or sc.getSecondaryState()):
        #print 'soul.py State: ', state
        state = sc.getState()
        states.get(state)()
    try:
        # close all threads
        coachThread.close()
    except:
        pass
    sc.close()
    visThread.close()
    
# DICTIONARIES
# STATES
states =     {
    0: Initial,
    1: Ready,
    2: Set,
    3: Playing,
    4: Finished,
    10: Penalized
    }

# PHASES
phases =     {
    'BallFound': BallFound,
    'BallNotFound': BallNotFound,
    'Kick' : Kick,
    'BallFoundKeep': BallFoundKeep,
    'BallNotFoundKeep': BallNotFoundKeep,
    'BallApproaching': BallApproaching,
    'InGoalArea': InGoalArea,
    'Unpenalized': Unpenalized,
    'ReturnField': ReturnField,
    'Standby': Standby
}

awakeSoul()

# DEBUG #
def testPhase(phase, interval):
    now = time.time()
    while time.time() - now < interval:
        phases.get(phase)()
