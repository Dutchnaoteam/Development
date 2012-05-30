"""
## NOTES TO EDITORS
# TODO: find way to make HMH and soul communicate correctly
# i.e. soul should wait for goalposition, should know when
# no ball is found, etc. 


## FILE DESCRIPTION
# File: soul.py
# Description: The nao's footballplaying soul.
# * states call phases
# * phases call moves
# * Transitions between states through global int state
# * Transitions between phases through global string phase
# state : e.g. 1
# phase : e.g. 'BallFound'
"""

import gameStateController          # Controls the states of the nao
import motionHandler
import time
import math

# Proxy creation 
from naoqi import ALProxy
audProxy = ALProxy('ALAudioDevice', '127.0.0.1', 9559)
ledProxy = ALProxy('ALLeds', '127.0.0.1', 9559)
memProxy = ALProxy('ALMemory', '127.0.0.1', 9559)
motProxy = ALProxy('ALMotion', '127.0.0.1', 9559)
posProxy = ALProxy('ALRobotPose', '127.0.0.1', 9559)
ttsProxy = ALProxy('ALTextToSpeech', '127.0.0.1', 9559)
vidProxy = ALProxy('ALVideoDevice', '127.0.0.1', 9559)
sentinel = ALProxy('ALSentinel', '127.0.0.1', 9559)
sensors  = ALProxy('ALSensors', '127.0.0.1', 9559)

# turn off default beavior
sentinel.enableDefaultActionSimpleClick(False)
sentinel.enableDefaultActionDoubleClick(False)
        
# turn off sentinel
sentinel.enableHeatMonitoring(False)
motProxy.setWalkArmsEnable(True, True)

# stateController class: robot state, penalized, etc.
GSC = gameStateController.StateController(ledProxy, memProxy, 
                                          sensors, ttsProxy)

# Motionhandler: threaded instance handling motion updates
MotionHandler = motionHandler.MotionHandler(ledProxy, memProxy, motProxy, posProxy, 
                 vidProxy)

# ball location(s)
ball_loc = list()

# Initialization of state and phase , defining gameState and robotPhase
state = 0
phase = 'BallNotFound'

# Robots own variables
robot = GSC.getRobotNumber()
memProxy.insertListData([['dntBallDist', '', 0], ['dntPhase', 0, 0], 
                         ['dntNaoNum', robot, 0]])
teamColor = 1
penalty = 0

audProxy.setOutputVolume(60)
#(teamColor, penalty) = GSC.getMatchInfo()
teamColor = 0
penalty = 0
audProxy.setOutputVolume(0)
print 'Set teamcolor, penalty '
# If keeper -> different style of play
playerType = 1 if robot == 1 else 0

## STATES (Gamestates)
# Initial()
# Ready()
# Set()
# Playing()
# Penalized()
# Finished()

def Initial():
    """Initial state: do nothing, stand ready for match
    ledProxy: All ledProxy are off
    Motions: NormalPose
    """
    global phase
    global ball_loc
    global firstCall

    if firstCall['Initial']:
        print 'In initial state'
        MotionHandler.mot.stiff()    # stiffness on
        MotionHandler.pause()

        # if a regular player
        if playerType == 0:
            phase = 'BallNotFound'
        # if a keeper
        else:
            phase = 'BallNotFoundKeep'
        
        # Empty all variables
        ball_loc = list()        
       
        firstCall['Initial']   = False
        firstCall['Ready']     = True
        firstCall['Set']       = True
        firstCall['Playing']   = True
        firstCall['Penalized'] = True

    time.sleep(0.1)

def Ready():
    """Ready state: possible positioning
    ledProxy: Chest Blue
    """
    global firstCall

    # Reinitialize phases, stand ready for match
    if firstCall['Ready']:
        print 'In ready state'
        # restart featurescanning
        MotionHandler.restart(trackBall=True)
        MotionHandler.killWalk()

        firstCall['Initial'] = True
        firstCall['Ready']   = False
        firstCall['Set']     = True
        firstCall['Playing'] = True
        firstCall['Penalized'] = True
        firstCall['FirstPress'] = True


def Set():
    '''Set state: start searching for ball. CAUTION: Game is started in Set 
    phase instead of Initial in penalty shootout!
    ledProxy:  Chest Yellow
    '''
    global teamColor
    global penalty
    global phase
    global firstCall
    # if the first iteration
    if firstCall['Set']:
        print 'In set state'
        # update info about team, possible that game is started in set phase
        (teamColor, penalty) = GSC.getMatchInfo()
        # Initial pose, if not already in it
        MotionHandler.restart(restartKF=False)
        MotionHandler.mot.stiff()
        MotionHandler.killWalk()
        
        if playerType == 0:
            MotionHandler.normalPose()
        else:
            MotionHandler.keepNormalPose()

        audProxy.setOutputVolume(0)                        # set volume to zero

        firstCall['Initial']   = True
        firstCall['Ready']     = True
        firstCall['Set']       = False
        firstCall['Playing']   = True
        firstCall['Penalized'] = True

    # Head movements allowed in the set state
    ball = MotionHandler.getKalmanBallPos()
    if ball:
        if playerType == 0:
            phase = 'BallFound'
        else:
            phase = 'BallFoundKeep'
        
def Playing():
    """Playing state: play game according to phase transitions
    ledProxy:  Chest Green
    """
    global phase
    global firstCall
   
    if firstCall['Playing']:
        print 'In playing state'
        
        MotionHandler.killWalk()
        
        firstCall['Initial']   = True
        firstCall['Ready']     = True
        firstCall['Set']       = True
        firstCall['Playing']   = False
        firstCall['Penalized'] = True

    # Execute the phase as specified by phase variable
    phases.get(phase)()

def Penalized():
    """ Penalized state
    ledProxy:  Chest Red
    """
    global phase
    global firstCall
    
    if firstCall['Penalized']:
        print 'In penalized state'
        MotionHandler.pause()
        if playerType == 0:                                # if a player, goto unpenalized phase
            phase = 'Unpenalized'
        else:                                              # if a keeper, go to ballnotfoundkeep..
            if GSC.getSecondaryState() or firstCall['FirstPress']:         # if penalty shootout
                phase = 'BallNotFoundKeep'
            else:                                          # else, become a player
                phase = 'Unpenalized'

        firstCall['Initial']   = True
        firstCall['Ready']     = True
        firstCall['Set']       = True
        firstCall['Playing']   = True
        firstCall['Penalized'] = False
        firstCall['FirstPress']= False
        
def Finished():
    MotionHandler.close()                                  # stop walking
    MotionHandler.stance()                                 # sit down
    MotionHandler.hmh.setHead(0,0)                         # set head straight
    time.sleep(1)                                          # wait until seated etc
    MotionHandler.mot.killKnees()                                        # stiffness off to prevent heating
    if not GSC.getSecondaryState():                        # if not penalty shootout
        GSC.close()
        audProxy.setOutputVolume(85)                       # volume on

## PHASES
# KEEPER
# BallFoundKeep()
# BallNotFoundKeep()
# InGoalArea()

def BallFoundKeep():
    """Goalie sees the ball. Keep track of previous positions to calculate
    where the ball is going, as there is no ball model yet. TODO ballmodel"""
    global phase
    global ball_loc
    global firstCall
    global timeStampKeeper
    
    if firstCall['BallFoundKeep']:
        MotionHandler.stance()
        firstCall['BallFoundKeep'] = False
        timeStampKeeper = time.time()
        time.sleep(0.1)
        
    maxlength = 6
    halfmaxlength = (maxlength/2.0)

    ball = MotionHandler.getKalmanBallPos()
    if ball:
        # ballpositions are kept in a list
        (x,y) = ball
        if len(ball_loc) == maxlength:
            del( ball_loc[0] )
            ball_loc.append(ball)
        else:
            ball_loc.append( ball )
        if len(ball_loc) == maxlength:
            xold = 0
            yold = 0
            xnew = 0
            ynew = 0
            # calculate 2 mean values (called old/new)
            for number in xrange(halfmaxlength):
                (x,y) = ball_loc[number]
                xold += x
                yold += y
            for number in xrange(int(halfmaxlength), maxlength):
                (x,y) = ball_loc[number]                
                xnew += x
                ynew += y

            # calculate the mean of measurements
            xold /= halfmaxlength
            yold /= halfmaxlength
            xnew /= halfmaxlength
            ynew /= halfmaxlength
            
            # calc diff in distance
            distold = math.sqrt(xold**2 + yold**2)
            distnew = math.sqrt(xnew**2 + ynew**2)
            interval = time.time() - timeStampKeeper
            timeStampKeeper = time.time()
            
            speed = (distold - distnew) / interval

            print 'Ball moving from ', xold, yold, 'to', xnew, ynew, \
                  '(mean). Speed', speed

            # calculate direction if speed is high enough
            if speed > 0.2 or (distnew < 1 and speed > 0.05 ):
                """
                This is all triangular magic using similarity between two
                triangles formed by balllocations and Nao. Keep in mind that 
                y-axis is inverted and that x is forward, y is sideways!
                
                                                              x
                      (yold,xold)                             |
                            .                                 |
                            | \                               |
                          B |   \                             |
                            |     \                           |
                            |_______.  (ynew,xnew )           |
                                A   | \                       |
                                    |   \                     |
                                  C |     \                   |
                                    |       \                 |
                     y _____________|_________._______________.___________ -y
                                            (dir,0)           Nao = (0,0)
                
                                    [--- D ---]

                Mathematical proof:
                A = yold - ynew
                B = xold - xnew
                C = xnew
                D = ynew - dir

                Similar triangles -> C / B = D / A
                                     D     = A*C/B
                                     D     = ynew - dir
                                     A*C/B = ynew - dir
                                     dir   = A*C/B - ynew
                """
                direction = (yold - ynew ) * xnew / (xold - xnew) - ynew
                print 'Direction', direction
                # if a direction has been found, clear all variables
                MotionHandler.dive(direction)
                phase = 'BallNotFoundKeep'

                ball_loc = list()
                firstCall['BallFoundKeep'] = True
                print 'Direction', direction
    else:
        phase = 'BallNotFoundKeep'
        firstCall['BallFoundKeep'] = True

def BallNotFoundKeep():
    """ Keeper lost track of ball, stand up after it can not be found to 
    prevent heated knees """
    global phase
    global ball_loc
    
    # if a ball is found
    if MotionHandler.getKalmanBallPos():
        # reinitialize
        ball_loc = list()
        phase = 'BallFoundKeep'
        firstCall['BallNotFoundKeep'] = True
    elif firstCall['BallNotFoundKeep']:
        memProxy.insertData('dntBallDist', 0)
        MotionHandler.keepNormalPose()
        firstCall['BallNotFoundKeep'] = False


# PLAYER
# BallFound()
# BallNotFound()
# Kick()
# Unpenalized()
# ReturnField()

def BallFound():
    """ Ball found, walk towards it. """
    global phase

    # FIND A BALL #
    if firstCall['BallFound']:
        firstCall['BallFound'] = False
        firstCall['BallNotFound'] = True
    
    ball = MotionHandler.getKalmanBallPos()
    
    if ball:
        (x,y) = ball
        if x < 0.17 and -0.02 < y < 0.02:
            print 'Kick'
            MotionHandler.killWalk()
            phase = 'Kick'
        else:         
            print 'Soul x,y =', x,y
            if x < 0.3:
                MotionHandler.hmh.setBallScanning()
                
            theta = math.atan2(y, x)
            # hacked influencing of perception, causing walking forward to have
            # priority
            x = 4.0 * (x - 0.17)  
            y *= 0.5 
            theta *= 0.4      
            MotionHandler.sWTV(x , y, theta, max ( 1-x, 0.95 ))
            time.sleep(0.025)
            
    else:
        x,y = MotionHandler.vis.KF.ballPos
        print 'Not seen ball', x, y
        theta = math.atan2( y, x ) 
        MotionHandler.postWalkTo( 0,0, math.copysign( theta, y ) / 2.0 )
        # TODO determine where ball is in headposition and look there 
        # instead of random places
        phase = 'BallNotFound'

def BallNotFound():
    """ Ball not found, turn if still no ball is found """
    global ball_loc
    global phase

    # if this is the first time the ball is not founnd
    if firstCall['BallNotFound']:
        memProxy.insertData('dntPhase', 'BallNotFound')
        MotionHandler.killWalk()
        firstCall['BallFound'] = True
        firstCall['BallNotFound'] = False
        
    # try to find a ball
    now = time.time()
    while time.time() - now < 2:
        ball = MotionHandler.getKalmanBallPos()
        if ball:
            phase = 'BallFound'
            firstCall['BallNotFound'] = True
            break
    if not MotionHandler.mot.isWalking():
        # if no ball is found circle slowly while searching for it
        MotionHandler.sWTV(0, 0, 0.2, 0.8)
 
def Kick():
    """ Kick ball in correct direction based on particle filter """
    global phase
    print "Kick phase"
    ball     = MotionHandler.getKalmanBallPos()
    position = MotionHandler.getParticleFilterPos()
    if not ball:
        print "Ball gone"
        phase = "BallNotFound"
    elif ball[0] > 0.25 or ball[1] > 0.1 or ball[1] < -0.1:
        print "Ball too far"
        phase = "BallFound"
    else:
        # Cases 1-3, if you see your own goal, kick to the other side
        if teamColor == 0:
            print "Trying to score in the far goal from", position
            goalPosX, goalPosY = (6, 2)
        else:
            print "Trying to score in the close goal from", position
            goalPosX, goalPosY = (0, 2)
        
        x, y, t   = position
        kickangle = math.atan2( goalPosY - y, goalPosX - x ) + t            
       
        if abs(kickangle) < 1:
            MotionHandler.walkTo(0, ball[1] + math.copysign( 0.035, kickangle ), 0)
        MotionHandler.kick(kickangle)
        phase = "BallNotFound"
        
def Unpenalized():
    """When unpenalized, a player starts at the side of the field """
    global phase
    global playerType
    # TODO reset particlefilter at certain position
    # if case this nao is a keeper, convert to player until state changes 
    # to initial/ready/set, where it is set to keeper again
    playerType = 0
    memProxy.insertListData([["dntBallDist", "", 0], 
                             ["dntPhase", "ReturnField", 0]])

    position = [2, 0, -1.5]
    MotionHandler.restart(position)
    # so no matter what, it"s always good to walk forward (2 meters, to 
    # the center of the field)
    if not(MotionHandler.mot.isWalking()):
        MotionHandler.postWalkTo(2, 0, 0)
    phase = "ReturnField"

def ReturnField():
    # and while you"re walking forward..
    global phase
    if MotionHandler.mot.isWalking():
        # ..search for a ball
        if MotionHandler.getKalmanBallPos():
            phase = "BallFound"
    else:
        phase = "BallNotFound"

##### OPERATING SYSTEM #####

def awakeSoul():
    GSC.start()
    MotionHandler.start()
    state = 0
    print "Awakened!"
    while(state != 4 or GSC.getSecondaryState()):
        #print "soul.py State: ", state
        state = GSC.getState()
        states.get(state)()
    print "Slumbering...."
    GSC.close()
    MotionHandler.close()
   
# DICTIONARIES
states =     {
    0: Initial,
    1: Ready,
    2: Set,
    3: Playing,
    4: Finished,
    10: Penalized
    }

phases =     {
    "BallFound": BallFound,
    "BallNotFound": BallNotFound,
    "Kick" : Kick,
    "BallFoundKeep": BallFoundKeep,
    "BallNotFoundKeep": BallNotFoundKeep,
    "Unpenalized": Unpenalized,
    "ReturnField": ReturnField,
}

# Dictionary that stores if a phase has been called once already.
# TODO find a better way to check if a phase or state has been called already, 
# perhaps keeping track of the previous (or all previous, as a log) states?
firstCall = {"Initial" : True,
             "Ready" : True,
             "Set": True,
             "Playing": True,
             "Penalized": True,
             "BallFoundKeep" : True,
             "BallNotFoundKeep" : True,
             "BallFound" : True,
             "BallNotFound" : True,
             "FirstPress" : True}

awakeSoul()

# DEBUG #
def testPhase(phase, interval):
    now = time.time()
    while time.time() - now < interval:
        phases.get(phase)()
