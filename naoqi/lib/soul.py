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
import motions                      # All motion actions
import motionHandler
import headMotionHandler
import time
import math


""" Proxy creation: protocol is first three letters with exceptions 
TextToSpeech (tts), RobotPose (pos), Sentinel and Sensors """
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
gsc = gameStateController.StateController( ledProxy, memProxy, 
                                           sensors, ttsProxy )
print 'Started gsc'

# Motion class: motion functions etc.
mot = motions.Motions( motProxy, posProxy )
print 'Made motion object'
# Motionhandlers: threaded instance handling motion updates
HeadMotionHandler = headMotionHandler.HeadMotionHandler(ledProxy, memProxy, 
                                                        motProxy, vidProxy)
HeadMotionHandler.start()
print 'Started headmotionHandler'

MotionHandler = motionHandler.MotionHandler( mot, HeadMotionHandler, 
                                            ledProxy, motProxy, memProxy, 
                                            sensors,  ttsProxy, vidProxy, )
MotionHandler.start()
print 'motionHandler started'

# ball location(s)
ball_loc = list()

# Initialization of state and phase , defining gameState and robotPhase
state = 0
phase = 'BallNotFound'

# Robots own variables
robot = gsc.getRobotNumber()
memProxy.insertListData([['dntBallDist', '', 0], ['dntPhase', 0, 0], 
                         ['dntNaoNum', robot, 0]])
teamColor = 1
penalty = 0

audProxy.setOutputVolume(60)
#(teamColor, penalty) = gsc.getMatchInfo()
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

        mot.stiff()                           # stiffness on
        MotionHandler.killWalk()
        HeadMotionHandler.pause()             # do not find the ball in Initial
        print 'TeamColor: ' , teamColor       

        # if a regular player
        if playerType == 0:
            phase = 'BallNotFound'
            mot.normalPose(True)              # normalPose, forcing call
        # if a keeper
        else:
            phase = 'BallNotFoundKeep'
            mot.keepNormalPose()
        
        # Empty variables
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
        # stop ballfinding, there is no ball anyway
        MotionHandler.localize = True
        
        print 'In ready state'
        MotionHandler.killWalk()

        firstCall['Initial'] = True
        firstCall['Ready']   = False
        firstCall['Set']     = True
        firstCall['Playing'] = True
        firstCall['Penalized'] = True
        firstCall['FirstPress'] = True


def Set():
    '''Set state: start searching for ball. CAUTION: Game is started in Set phase
    instead of Initial in penalty shootout!
    ledProxy:  Chest Yellow
    '''
    global teamColor
    global kickOff
    global phase
    global firstCall
    # if the first iteration
    if firstCall['Set']:
        MotionHandler.killWalk()
        # update info about team, possible that game is started in set phase
        (teamColor, penalty) = gsc.getMatchInfo()

        print 'In set state'
        HeadMotionHandler.setBallScanning()                
        print 'TeamColor: ' , teamColor                    
        
        # Initial pose, if not already in it
        mot.stiff()
        if playerType == 0:
            mot.normalPose()
        else:
            mot.keepNormalPose()

        audProxy.setOutputVolume(0)                        # set volume to zero

        firstCall['Initial']   = True
        firstCall['Ready']     = True
        firstCall['Set']       = False
        firstCall['Playing']   = True
        firstCall['Penalized'] = True

    # Head movements allowed in the set state
    # FIND A BALL #
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
        MotionHandler.killWalk()
        MotionHandler.restart()
        HeadMotionHandler.setFeatureScanning()
        print 'In playing state'
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
            if gsc.getSecondaryState() or firstCall['FirstPress']:         # if penalty shootout
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
    mot.stance()                                           # sit down
    mot.setHead(0,0)                                       # set head straight
    time.sleep(1)                                          # wait until seated etc
    mot.killKnees()                                        # stiffness off to prevent heating
    if not gsc.getSecondaryState():                        # if not penalty shootout
        gsc.close()
        audProxy.setOutputVolume(85)                       # volume on

## PHASES

# KEEPER
# BallFoundKeep()
# BallNotFoundKeep()
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
    ball = MotionHandler.getKalmanBallPos()
    if ball:
        #if ball[0] < 0.3 and (ball[1] < 0.5 or ball[1] > -0.5):
        #    phase = 'InGoalArea'
        #    mot.move('normalPose')
        #    VisionHandler.findBall()
        #    return True
        (x,y) = ball

        length = len(ball_loc)
        if length == maxlength:
            ball_loc = ball_loc[1:]
            ball_loc.append(ball)
        else:
            ball_loc.append( ball )
        if length == maxlength:
            xold = 0
            yold = 0
            xnew = 0
            ynew = 0

            # shift elements sidewards, newest ballloc becomes nr <maxlength>, oldest is thrown away
            for number in range(maxlength):
                (x,y) = ball_loc[number]

                # add to xold/new and yold/new variables, number 0 is oldest, number <maxlength> most recent ballloc
                if 0 <= number < halfmaxlength:
                    xold += x
                    yold += y
                else:
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
            speed = distold - distnew

            print 'Ball moving from ', xold, yold, 'to', xnew, ynew, '(mean). Speed', speed

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
                dir = (yold - ynew ) * xnew / (xold - xnew) - ynew
                print 'Direction', dir
                # if a direction has been found, clear all variables
                MotionHandler.dive(dir)
                phase = 'BallNotFoundKeep'

                ball_loc = list()
                firstCall['BallFoundKeep'] = True
                print 'Direction', dir
    else:
        phase = 'BallNotFoundKeep'
        firstCall['BallFoundKeep'] = True

def BallNotFoundKeep():
    """ Keeper lost track of ball
    """
    global phase
    global ball_loc
        
    HeadMotionHandler.setBallScanning()
    # if a ball is found
    if MotionHandler.getKalmanBallPos():
        # reinitialize
        ball_loc = list()
        phase = 'BallFoundKeep'
        firstCall['BallNotFoundKeep'] = True
    elif firstCall['BallNotFoundKeep']:
        memProxy.insertData('dntBallDist', 0)
        mot.keepNormalPose()
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
        HeadMotionHandler.setBallScanning()
    
    ball = MotionHandler.getKalmanBallPos()
    
    if ball:
        (x,y) = ball
        if x < 0.18 and -0.04 < y < 0.04:
            print 'Kick'
            MotionHandler.killWalk()
            phase = 'Kick'
        else:         
            print 'Soul x,y =', x,y
            theta = math.atan2(y, x)
            # hacked influencing of perception, causing walking forward to have
            # priority
            theta *= 0.4      
            x = (3.0 * (x - 0.17))  
            y *= 0.6 
            MotionHandler.sWTV(x , y, theta, max ( 1-x, 0.85 ))
            time.sleep(0.05)
    else:
        x,y = MotionHandler.hmh.vision.KF.ballPos
        print 'Not seen ball', x, y
        theta = math.atan2( y, x ) 
        MotionHandler.postWalkTo( 0,0, math.copysign( theta, y ) / 2.0 )
        # TODO determine where ball is in headposition and look there 
        # instead of random places
        phase = 'BallNotFound'

def BallNotFound():
    """ Ball not found, look for it """
    global ball_loc
    global phase

    # if this is the first time the ball is not founnd
    if firstCall['BallNotFound']:
        memProxy.insertData('dntPhase', 'BallNotFound')
        MotionHandler.killWalk()
        HeadMotionHandler.setBallScanning()
        firstCall['BallFound'] = True
        firstCall['BallNotFound'] = False
        
    # try to find a ball
    ball = MotionHandler.getKalmanBallPos()
    if ball:
        phase = 'BallFound'
        firstCall['BallNotFound'] = True
    else:
        # if no ball is found circle slowly while searching for it
        MotionHandler.postWalkTo(0, 0, 2)
 
def Kick():
    """ Look for a goal, kick ball in correct direction """
    global phase
    print 'Kick phase '
    ball     = MotionHandler.getKalmanBallPos()
    position = MotionHandler.getParticleFilterPos()
    if not ball:
        print 'Ball gone'
        phase = 'BallNotFound'
    elif ball[0] > 0.25 or ball[1] > 0.1 or ball[1] < -0.1:
        print 'Ball too far'
        phase = 'BallFound'
    else:
        # Cases 1-3, if you see your own goal, kick to the other side
        if teamColor == 0:
            print 'Trying to score in the far goal'
            goalPosX, goalPosY = (6, 2)
        else:
            print 'Trying to score in the close goal'
            goalPosX, goalPosY = (0, 2)
        
        x, y, t   = position
        kickangle = math.atan2( goalPosY - y, goalPosX - x ) + t            
        
        if abs(kickangle) < 1:
            MotionHandler.walkTo(0, math.copysign( 0.03, kickangle ) , 0)
        MotionHandler.kick(kickangle)
        phase = 'BallNotFound'
        
def Unpenalized():
    """When unpenalized, a player starts at the side of the field
    """
    global phase
    global playerType

    memProxy.insertListData([['dntBallDist', '', 0], 
                             ['dntPhase', 'ReturnField', 0]])

    # if case this nao is a keeper, convert to player until state changes 
    # to initial/ready/set, where it is set to keeper again
    playerType = 0

    MotionHandler.restart()
    HeadMotionHandler.setFeatureScanning()
    # so no matter what, it's always good to walk forward (2 meters, to 
    # the center of the field)
    if not(mot.isWalking()):
        MotionHandler.postWalkTo(2, 0, 0)
    phase = 'ReturnField'

def ReturnField():
    # and while you're walking forward..
    global phase
    if mot.isWalking():
        # ..search for a ball
        if MotionHandler.getKalmanBallPos():
            phase = 'BallFound'
    else:
        phase = 'BallNotFound'

##### OPERATING SYSTEM #####

def awakeSoul():
    gsc.start()
    state = 0
    print 'Awakened!'
    while(state != 4 or gsc.getSecondaryState()):
        #print 'soul.py State: ', state
        state = gsc.getState()
        states.get(state)()
    print 'Slumbering....'
    gsc.close()
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
    'BallFound': BallFound,
    'BallNotFound': BallNotFound,
    'Kick' : Kick,
    'BallFoundKeep': BallFoundKeep,
    'BallNotFoundKeep': BallNotFoundKeep,
    'Unpenalized': Unpenalized,
    'ReturnField': ReturnField,
}

# Dictionary that stores if a phase has been called once already.
# TODO find a better way to check if a phase or state has been called already, 
# perhaps keeping track of the previous (or all previous, as a log) states?
firstCall = {'Initial' : True,
             'Ready' : True,
             'Set': True,
             'Playing': True,
             'Penalized': True,
             'BallFoundKeep' : True,
             'BallNotFoundKeep' : True,
             'BallFound' : True,
             'BallNotFound' : True,
             'FirstPress' : True}

awakeSoul()

# DEBUG #
def testPhase(phase, interval):
    now = time.time()
    while time.time() - now < interval:
        phases.get(phase)()