
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

import gameStateController          # Controls the states of the nao
import motions                      # All motion actions
import visionInterface              # All vision actions
import motionHandler
import time
import math
import socket
import coach

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

# Creating classes: Protocol is first three letters with exception gameStateController (gsc)
# stateController class: robot state, penalized, etc.
gsc = gameStateController.StateController('stateController', ttsProxy, memProxy, ledProxy, sensors )
print 'Started gsc'

# Motion class: motion functions etc.
mot = motions.Motions( motProxy, posProxy )
# Motionhandler: threaded instance handling motion update
mHandler = motionHandler.MotionHandler( mot, gsc, memProxy )

mHandler.start()
print 'motionHandler started'

# VisionInterface class: goalscans, ballscans
vis = visionInterface.VisionInterface( motProxy, vidProxy, memProxy, ledProxy )
# Start the vision (ballfinding) thread
visThread = visionInterface.VisionThread( vis, memProxy, ledProxy )
visThread.start()
visThread.stopScan()

# ball location(s)
ball_loc = list()

#particleFilter   = particle.ParticleFilter()
#particleFilter.start()

goalPosKnown = (False, None)

# Initialization of state and phase , defining gameState and robotPhase
state = 0
phase = 'BallNotFound'

# Robots own variables
robot = gsc.getRobotNumber()
memProxy.insertListData([['dntBallDist', '', 0], ['dntPhase', 0, 0], ['dntNaoNum', robot, 0],['dntAction','',0],['dntKeepSawBall',0,0]])
teamColor = 0
kickOff = 0
penalty = 0

audProxy = ALProxy('ALAudioDevice', '127.0.0.1', 9559)
audProxy.setOutputVolume(60)
(teamColor, kickOff, penalty) = gsc.getMatchInfo()
#audProxy.setOutputVolume(0)

print 'test'
coa = coach.coach('', memProxy, ledProxy, 6321)
print 'coach started'

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
    global phase                                           # to change, call global, else not possible
    global ball_loc
    global firstCall
    global nameList

    if firstCall['Initial']:
        print 'In initial state'
        mHandler.killWalk()
        visThread.stopScan()                               # do not find the ball when in Initial
        print 'TeamColor: ' , teamColor                    # print the teamcolor as a check

        # Empty variables
        ball_loc = list()

        mot.stiff()                                        # stiffness on (if it wasnt already)
        mot.setHead(0,0)                                   # head in normal position

        # if a regular player
        if playerType == 0:
            phase = 'BallNotFound'
            mot.normalPose(True)                           # normalPose, forcing call
        # if a keeper
        else:
            phase = 'BallNotFoundKeep'
            mot.keepNormalPose()

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
        visThread.stopScan()
        print 'In ready state'
        mHandler.killWalk()

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
        mHandler.killWalk()
        # update info about team, it is possible that game is started in set phase
        (teamColor, kickOff, penalty) = gsc.getMatchInfo()

        print 'In set state'
        visThread.startScan()                              # start ballscan

        print 'TeamColor: ' , teamColor                    # print teamcolor as a check

        # Initial pose, if not already in it
        mot.stiff()
        if playerType == 0:
            mot.normalPose()
        else:
            mot.keepNormalPose()

        #audProxy.setOutputVolume(0)                        # set volume to zero

        firstCall['Initial']   = True
        firstCall['Ready']     = True
        firstCall['Set']       = False
        firstCall['Playing']   = True
        firstCall['Penalized'] = True

    # Head movements allowed in the set state
    # FIND A BALL #
    ball = vis.scanCircle(visThread)
    if ball:
        mHandler.setBallLoc( ball )
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
        mHandler.killWalk()
        visThread.startScan()
        print 'In playing state'
        firstCall['Initial']   = True
        firstCall['Ready']     = True
        firstCall['Set']       = True
        firstCall['Playing']   = False
        firstCall['Penalized'] = True
    
    try:
        if memProxy.getData('dntAction'):
            phase = memProxy.getData('dntAction')
            print 'coach says: '+ phase
        else:
            print 'coach says: nothing'
    except:
        pass
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
        visThread.stopScan()                               # stop looking for the ball
        
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
    visThread.stopScan()                                   # stop looking for the ball
    mHandler.killWalk()                                    # stop walking
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
        mot.setFME(False)
        
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
            if speed > 0.25 or (distnew < 0.6 and speed > 0.05 ):
                
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
                #                      A*C/B = ynew - dir
                #                      dir   = A*C/B - ynew

                dir = (yold - ynew ) * xnew / (xold - xnew) - ynew
                print 'Direction', dir
                # if a direction has been found, clear all variables
                mHandler.dive(dir)
                phase = 'BallNotFoundKeep'

                ball_loc = list()
                visThread.clearCache()
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
    mot.setFME(False)
        
    visThread.startScan()
    # if a ball is found
    if vis.scanCircle(visThread):
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

def Standby():
    global phase
    ttsProxy.say('Waiting')
    mHandler.killWalk()
    time.sleep(0.3)
    phase = 'BallFound'

def BallFound():
    global phase
    global goalPosKnown

    # FIND A BALL #
    seen = False
    ball = visThread.findBall()
    if ball:
        seen = True
        #print 'RealPosition', ball
    if firstCall['BallFound']:
        mot.setFME(True)
        firstCall['BallFound'] = False
        firstCall['BallNotFound'] = True
        # initialize mean mu for kalman filter
        if seen:
            mHandler.setBallLoc( ball )
    
    mHandler.setBallLoc( ball )    
    ball = mHandler.getKalmanBallPos()
    (x,y) = ball 
    memProxy.insertData('dntPhase', 'BallFound')
    
    if seen and x < 0.17 and -0.02 < y < 0.02:
        print 'Kick'
        # BLOCKING CALL: FIND BALL WHILE STANDING STILL FOR ACCURATE CORRECTION
        mHandler.killWalk()
        phase = 'Kick'
    else:
        if seen:
            print 'Kalman position', x,y
            theta = math.atan(y/x)
            # hacked influencing of perception, causing walking forward to have priority
            theta *= 0.4      
            x = (3.0 * (x - 0.17))  
            y *= 0.6 
            mHandler.sWTV(x , y, theta, max ( 1-x, 0.85 ))
            time.sleep(0.15)
            goalPosKnown = False, None
        else:
            print 'Not seen ball', x, y
            theta = math.atan( y / x ) 
            mHandler.postWalkTo( 0,0, math.copysign( theta, y ) / 2.0 )
            # TODO determine where ball is in headposition and look there instead of random places
            if not vis.scanCircle(visThread):
                phase = 'BallNotFound'

    # If covariance becomes too large, when?
    #if mHandler.KF.Sigma[0][0] > 0.075:
    #    print 'Sigma kalmanfilter: ' , mHandler.KF.Sigma
    #    if x > 0:
    #        theta = math.atan(y/x)
    #    else:
    #        theta = 0
    #    print 'Perhaps the ball is lost, turning ', theta,'to find it'
    #    mHandler.postWalkTo(0,0, theta)
        
    # TODO somehow influence kalman mu based on turn
    #    phase = 'BallNotFound'

def KeepDistance():
    global phase
    firstCall['BallFound'] = True
    firstCall['BallNotFound'] = True
    ball = visThread.findBall()
    print 'KeepDist'
    if ball:
        (x,y) = ball
        memProxy.insertData('dntPhase', 'KeepDistance')
        
        theta = math.atan(y/x)
        # hacked influencing of perception, causing walking forward to have priority
        theta = theta / 2.5  if theta > 0.4    else theta / 5.5
        x = (2.0 * x - 0.4) if x > 0.5        else (x - 0.4) * 1.3
        y = 0.5 * y          if -0.1 < y < 0.1 else 2.0 * y

        mHandler.sWTV(x , y, theta, 1.0)
        phase = 'BallFound'
    else:
        phase = 'BallNotFound'

def BallNotFound():
    global ball_loc
    global phase
    global goalPosKnown

    # if this is the first time the ball is not founnd
    if firstCall['BallNotFound']:
        memProxy.insertData('dntPhase', 'BallNotFound')
        mHandler.killWalk()
        ball = vis.scanCircle(visThread)
        firstCall['BallFound'] = True
        firstCall['BallNotFound'] = False
        
    # try to find a ball
    ball = vis.scanCircle(visThread)
    if ball:
        mHandler.setBallLoc( ball )
        phase = 'BallFound'
        firstCall['BallNotFound'] = True
    else:
        # if no ball is found circle slowly while searching for it
        mHandler.postWalkTo(0, 0, 2)
        goalPosKnown = False, None

def Kick():
    global phase
    global goalPosKnown
    mot.setFME(False)

    memProxy.insertData('dntPhase', 'Kick')
    visThread.stopScan()
    
    # scan for a goal
    goal = None
    if goalPosKnown[0]:
        goal = goalPosKnown[1]
    else:
        goal = vis.scanCircleGoal()
    if goal:
        goalPosKnown = (True, goal)
    
    print 'Kick phase: ', goal
    mot.setHead(0, 0.45)
    visThread.startScan()
    ball = vis.scanCircle(visThread)

    # Case 0 : Ball stolen/lost.
    # Check if the ball is still there, wait until ball is found has passed
    # Something of a mean, ...

    if not ball:
        print 'Ball gone'
        phase = 'BallNotFound'
    elif ball[0] > 0.25 or ball[1] > 0.1 or ball[1] < -0.1:
        print 'Ball too far'
        phase = 'BallFound'
    elif ball and not goal:
        mHandler.kick(0)
        phase = 'BallNotFound'
    else:
        # else a goal is found, together with it's color
        (color, kickangles ) = goal
        if type(kickangles[0]) == tuple:

            (first, second) = kickangles
            kickangle = (3 * first[0] + second[0]) / 4.0         # kick slightly more towards left pole
        else:
            kickangle = kickangles[0]

        if color == 'Blue':
            goalColor = 0
        else:
            goalColor = 1
        
        # use kalman filter to position ball in 10 measurements 
        c = 0
        while c < 10:
            c += 1
            ball = visThread.findBall()
            mHandler.setBallLoc( ball )
        ball = mHandler.getKalmanBallPos()
        
        # Cases 1-3, if you see your own goal, kick to the other side OR if the keeper saw the ball
        if memProxy.getData('dntKeepSawBall'):
            # Case 1, goal is left, kick to the right.
            if kickangle >= 0.7:
                mHandler.kick(-1.1)
            # Case 2, goal is right, kick to the left.
            if kickangle <= -0.7:
                mHandler.kick(1.1)
            else:
            # Case 3, goal is straight forward, HAK, but only in the first 2 minutes of each half.
                if gsc.getSecondsRemaining()>8:
                    mHandler.kick(1.1)
                else:
                    mHandler.kick(1.1)

        else:
            # Case 4, other player's goal is found.
            # Kick towards it.

            # general kick interface distributes kick
            if abs(kickangle < 0.6):
                mHandler.walkTo(0, math.copysign( 0.03, kickangle ) , 0)
            while c < 10:
                c += 1
                ball = visThread.findBall()
                mHandler.setBallLoc( ball )
            ball = mHandler.getKalmanBallPos()
            print 'Goalcolor', goalColor, 'KickAngle', kickangle
            print 'TeamColor', teamColor, 'Locatie', ball
            mHandler.kick(kickangle)
        phase = 'BallNotFound'
        ledProxy.fadeRGB('LeftFaceLeds', 0x00000000, 0)  # no goal yet, left led turns black

def Unpenalized():
    """When unpenalized, a player starts at the side of the field
    """
    global phase
    global playertype

    memProxy.insertListData([['dntBallDist', '', 0], ['dntPhase', 'ReturnField', 0]])

    # if case this nao is a keeper, convert to player until state changes to initial/ready/set, where it is set to keeper again
    playertype = 0

    visThread.startScan()
    # so no matter what, it's always good to walk forward (2 meters, to the center of the field)
    if not(mot.isWalking()):
        mHandler.postWalkTo(2, 0, 0)
    phase = 'ReturnField'

def ReturnField():
    # and while you're walking forward..
    global phase
    if mot.isWalking():
        # ..search for a ball
        if vis.scanCircle(visThread):
            phase = 'BallFound'
    else:
        phase = 'BallNotFound'

##### OPERATING SYSTEM #####

def awakeSoul():
    gsc.start()
    state = 0
    while(state != 4 or gsc.getSecondaryState()):
        #print 'soul.py State: ', state
        state = gsc.getState()
        states.get(state)()
    gsc.close()
    coa.close()
    mHandler.close()
    visThread.close()
    # particleFilter.close()

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
    'Standby': Standby,
    'KeepDistance' : KeepDistance
}

# Dictionary that stores if a phase has been called once already.
# TODO find a better way to check if a phase or state has been called already, perhaps
# keeping track of the previous (or all previous, as a log) states?
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

try:
    awakeSoul()
except KeyboardInterrupt:
    print('keyboard interrupt, stopping soul and closing all threads')
except Exception as e:
    print 'error [ '+str(e)+' ] in soul, closing all threads'
finally:
    gsc.close()
    mHandler.close()
    visThread.close()
    coa.close()
    audProxy.setOutputVolume(60)
    sentinel.enableDefaultActionDoubleClick(True)
    sentinel.enableDefaultActionSimpleClick(True)
# DEBUG #
def testPhase(phase, interval):
    now = time.time()
    while time.time() - now < interval:
        phases.get(phase)()
