
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
import coach
import kalmanFilter as kalman
import time
import math
import socket


# Proxy creation: protocol is first three letters with exceptions TextToSpeech (tts) and RobotPose (pos)
from naoqi import ALProxy
audProxy = ALProxy('ALAudioDevice', '127.0.0.1', 9559)
ledProxy = ALProxy('ALLeds', '127.0.0.1', 9559)
memProxy = ALProxy('ALMemory', '127.0.0.1', 9559)
motProxy = ALProxy('ALMotion', '127.0.0.1', 9559)
posProxy = ALProxy('ALRobotPose', '127.0.0.1', 9559)
ttsProxy = ALProxy('ALTextToSpeech', '127.0.0.1', 9559)
vidProxy = ALProxy('ALVideoDevice', '127.0.0.1', 9559)
sentinel = ALProxy('ALSentinel', '127.0.0.1', 9559)

# turn off sentinel
sentinel.enableHeatMonitoring(False)

# Creating classes: Protocol is first three letters with exception gameStateController (gsc)
# Motion class: motion functions etc.
mot = motions.Motions( motProxy, posProxy  )

# VisionInterface class: goalscans, ballscans
vis = visionInterface.VisionInterface( motProxy, vidProxy, memProxy )
# Start the vision (ballfinding) thread
visThread = visionInterface.VisionThread( vis )
visThread.start()
visThread.stopScan()


coachThread = None

# stateController class: robot state, penalized, etc.
gsc = gameStateController.stateController('stateController', ttsProxy, memProxy )

# kalmanFilter class: a kalman filter to keep track of the ballposition
kalmanFilterBall = kalman.KalmanBall()
# control vector containing x,y,theta-velocity
control = [0,0,0]
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
memProxy.insertListData([['dntBallDist', '', 0], ['dntPhase', 0, 0], ['dntNaoNum', robot, 0]])
teamColor = None
kickOff = None
penalty = None

(teamColor, kickOff, penalty) = gsc.getMatchInfo()

# If keeper -> different style of play , coaches other naos

# If keeper -> different style of play
playerType = 1 if robot == 1 else 0


ipList  = list()
nameList = []
#nameList = ['camlal.local', 'frank.local', 'elpresidente.local']

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
    global coachThread
    global nameList

    failedList = list()

    if firstCall['Initial']:
        mot.killWalk()
        print 'In initial state'
        visThread.stopScan()                               # do not find the ball when in Initial
        print 'TeamColor: ' , teamColor                    # print the teamcolor as a check

        # Empty variables
        ball_loc = list()

        # Team color must be displayed on left foot (Reference to rules)
        ledProxy.off('AllLeds')
        if (teamColor == 0):
            ledProxy.fadeRGB('LeftFootLeds', 0x000000ff, 0)
        else:
            ledProxy.fadeRGB('LeftFootLeds', 0x00ff0000, 0)

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

    for name in nameList:
        try:
            ipList.append(socket.gethostbyname( name ))
        except Exception as inst:
            failedList.append(name)
    nameList = failedList
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
        mot.killWalk()

        # set ChestLeds
        ledProxy.fadeRGB('ChestLeds',0x000000ff, 0)

        firstCall['Initial'] = True
        firstCall['Ready']   = False
        firstCall['Set']     = True
        firstCall['Playing'] = True
        firstCall['Penalized'] = True
        firstCall['FirstPress'] = True


def Set():
    """Set state: start searching for ball. CAUTION: Game is started in Set phase
    instead of Initial in penalty shootout!
    ledProxy:  Chest Yellow
    """
    global teamColor
    global kickOff
    global phase
    global firstCall
    global control
    # if the first iteration
    if firstCall['Set']:
        memProxy.insertData('dntBallDist', 0)
        mot.killWalk()
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

        audProxy.setOutputVolume(0)                        # set volume to zero
        ledProxy.fadeRGB('ChestLeds', 0x00ffff00, 0)       # set chestledcolor to green

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
        ball = vis.scanCircle(visThread)
        if ball:
            kalmanFilterBall.setFirstCall( True, ball )
            control = [0,0,0]
            if playerType == 0:
                phase = 'BallFound'
            else:
                phase = 'BallFoundKeep'

    # Keep finding the ball, it might move (or does it?)
    else:
        ball = visThread.findBall()
        if not ball:
            if playerType == 0:
                phase = 'BallNotFound'
            else:
                phase = 'BallNotFoundKeep'
        kalmanFilterBall.setFirstCall( True, ball )
        ball = kalmanFilterBall.iterate( ball , [0,0,0] )
        print 'Kalmanposition: ', ball

def Playing():
    """Playing state: play game according to phase transitions
    ledProxy:  Chest Green
    """
    global phase
    global firstCall
    global coachThread

    if firstCall['Playing']:
        visThread.startScan()
        try:
            coachThread.isActive()
        except:
            try:
                coachThread = coach.Coach('coach', ipList, memProxy, ledProxy)
                coachThread.start()
                print 'coaching started'
            except:
                pass
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
        #particleFilter.reset( position )
        # relocalize
    else:
        # localization features on field:
        # - goals, both yellow
        # - lines
        # - other robots ???

        # hacks:
        # - rules for placement on field -> clustered particles in according place
        # - falling                      -> scattered particles
        # - ...
        # position = particleFilter.meanState
        pass
    try:
        coachPhase = coachThread.getCoachData('dnt'+str(robot))
        if coachPhase:
            print 'Coach says: ', coachPhase
            phase = coachPhase
    except Exception as inst:
        print inst
        print 'Could not get an action'
    # Execute the phase as specified by phase variable
    phases.get(phase)()

def Penalized():
    """ Penalized state
    ledProxy:  Chest Red
    """
    global phase
    global firstCall
    memProxy.insertData('dntBallDist', 0)

    if firstCall['Penalized']:
        print 'In penalized state'
        ledProxy.fadeRGB('ChestLeds',0x00ff0000, 0)        # ledProxy on chest: red
        mot.killWalk()                                     # stop walking

        visThread.stopScan()                               # stop looking for the ball
        mot.stiff()                                        # stiffness on (just in case?)

        mot.keepNormalPose()

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
        print phase

def Finished():
    visThread.stopScan()                                   # stop looking for the ball
    ledProxy.off('AllLeds')                                # turn off leds
    mot.killWalk()                                         # stop walking
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

    maxlength = 4
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

            xlast, ylast = ball_loc[-1]
            xpenultimate, ypenultimate = ball_loc[-2]

            distlast = math.sqrt(xlast**2 + ylast**2)
            distpenultimate = math.sqrt(xpenultimate **2 + ypenultimate **2)
            speedlast = distpenultimate  - distlast

            # calc diff in distance
            distold = math.sqrt(xold**2 + yold**2)
            distnew = math.sqrt(xnew**2 + ynew**2)
            speed = distold - distnew

            print 'Ball moving from ', xold, yold, 'to', xnew, ynew, '(mean). Speed', speed, 'Speedlast', speedlast

            # calculate direction if speed is high enough
            if speed > 0.1 or speedlast > 0.1:
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
                #                      A*C/B = ynew - dir
                #                      dir   = A*C/B - ynew

                dir = (yold - ynew ) * xnew / (xold - xnew) - ynew
                print 'Direction', dir
                # if a direction has been found, clear all variables

                if dir >= 0.5:
                    print 'Dive right'
                    mot.diveRight()
                elif dir <= -0.5:
                    print 'Dive left'
                    mot.diveLeft()
                elif dir < 0.5 and dir >= 0:
                    print 'Step right'
                    mot.footRight()
                elif dir > -0.5 and dir < 0:
                    print 'Step left'
                    mot.footLeft()
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
    mot.killWalk()
    time.sleep(0.3)
    phase = 'BallFound'

def BallFound():
    global phase
    global control
    global goalPosKnown

    # FIND A BALL #
    seen = False
    ball = visThread.findBall()
    if ball:
        seen = True
        #print 'RealPosition', ball
    if firstCall['BallFound']:
        mot.setFME(True)
        ledProxy.fadeRGB('RightFaceLeds', 0x0000ff00, 0)
        firstCall['BallFound'] = False
        firstCall['BallNotFound'] = True
        # initialize mean mu for kalman filter
        if seen:
            kalmanFilterBall.setFirstCall(True, ball)
            control = [0,0,0]

    ball = kalmanFilterBall.iterate(ball, control)
    (x,y) = ball
    memProxy.insertData('dntPhase', 'BallFound')
    memProxy.insertData('dntBallDist', math.sqrt(x**2 + y**2))

    if seen and x < 0.19 and -0.02 < y < 0.02:
        print 'Kick'
        # BLOCKING CALL: FIND BALL WHILE STANDING STILL FOR ACCURATE CORRECTION
        mot.killWalk()
        time.sleep(5)
        #mot.setFootSteps( ['LLeg', 'RLeg'], [[x-0.16, y, 0],[0,0,0]], [1.0, 2.0] )
        control = [0,0,0]
        phase = 'Kick'
    else:
        if seen:
            print 'Kalman position', x,y
            theta = math.atan(y/x)
            # hacked influencing of perception, causing walking forward to have priority
            theta = theta / 2.0  #if theta > 0.4    else theta / 5.5
            x = (4.0 * (x - 0.19)) #if x > 0.5        else (x - 0.16) * 1.3
            y = 0.6 * y           #if -0.1 < y < 0.1 else 2.0 * y

        else:
            print 'Not seen ball', x, y
            # TODO determine where ball is in headposition and look there instead of random places

            head = mot.getHeadPos( False )
            yaw = head[0]
            pitch = head[1]
            # slowly move head towards 0,0 position
            mot.setHead( yaw / 1.5 , pitch / 1.5 )

            # hacked influencing, turn towards last found position first
            theta = math.atan(y/x) / 2.5
            x = (x -0.5)
            y = 0

        x = max(-1, min(1, x))
        y = max(-1, min(1, y))
        theta = max(-1, min(1, theta))
        mot.setWalkTargetVelocity(x , y, theta, 1.0)
        goalPosKnown = False, None


        # maxXSpeed 0.117 m / s for nao , backwards a lot less
        vX = x * 0.120 if x > 0 else x * 0.079
        # maxYSppeed is 0.05 m/s
        vY = y * 0.054
        # maxTSpeed 0.4 rad / s
        vT = theta * 0.410
        control = [vX,vY,vT]
        print ''

    # If covariance becomes too large, when?
    if kalmanFilterBall.Sigma[0][0] > 0.05:
        print 'Sigma kalmanfilter: ' , kalmanFilterBall.Sigma
        print 'Perhaps the ball is lost, turning ', theta,'to find it'
        mot.postWalkTo(0,0, theta)
        # TODO somehow influence kalman mu based on turn
        phase = 'BallNotFound'

def KeepDistance():
    global phase
    firstCall['BallFound'] = True
    firstCall['BallNotFound'] = True
    ball = visThread.findBall()
    print 'KeepDist'
    if ball:
        (x,y) = ball
        memProxy.insertData('dntPhase', 'KeepDistance')
        memProxy.insertData('dntBallDist', math.sqrt(x**2 + y**2))

        theta = math.atan(y/x)
        # hacked influencing of perception, causing walking forward to have priority
        theta = theta / 2.5  if theta > 0.4    else theta / 5.5
        x = (2.0 * x - 0.4) if x > 0.5        else (x - 0.4) * 1.3
        y = 0.5 * y          if -0.1 < y < 0.1 else 2.0 * y

        x = min( 1, max( -1, x))
        y = min( 1, max( -1, y))
        theta = min( 1, max( -1, theta))

        mot.setWalkTargetVelocity(x , y, theta, 1.0)
        phase = 'BallFound'
    else:
        phase = 'BallNotFound'

def BallNotFound():
    global ball_loc
    global phase
    global control
    global goalPosKnown

    # if this is the first time the ball is not founnd
    if firstCall['BallNotFound']:
        memProxy.insertData('dntPhase', 'BallNotFound')
        memProxy.insertData('dntBallDist', 0)
        ledProxy.fadeRGB('RightFaceLeds',0x00ff0000, 0) # no ball, led turns red
        mot.killWalk()
        firstCall['BallFound'] = True
        firstCall['BallNotFound'] = False
        control = [0,0,0]

    # try to find a ball
    ball = vis.scanCircle(visThread)
    if ball:
        kalmanFilterBall.setFirstCall(True, ball )
        control = [0,0,0]
        phase = 'BallFound'
        firstCall['BallNotFound'] = True
    else:
        # if no ball is found circle slowly while searching for it
        mot.postWalkTo(0, 0, 1.3)
        goalPosKnown = False, None

def Kick():
    global phase
    global goalPosKnown
    mot.setFME(False)

    memProxy.insertData('dntPhase', 'Kick')
    visThread.stopScan()

    ledProxy.fadeRGB('LeftFaceLeds',0x00000000, 0)         # no goal yet, left led turns black
    ledProxy.fadeRGB('RightFaceLeds', 0x00ff0000, 0)       # no ball anymore, right led turns red

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

    print 'Found ball: ', ball

    #ball = kalmanFilterBall.iterate( ball, [0,0,0] )
    if not ball:
        print 'Ball gone'
        phase = 'BallNotFound'
    elif ball[0] > 0.25 or ball[1] > 0.1 or ball[1] < -0.1:
        ledProxy.fadeRGB('RightFaceLeds', 0x00ff0000, 0)  #right led turns green
        print 'Ball too far'
        phase = 'BallFound'
    elif ball and not goal:
        ledProxy.fadeRGB('RightFaceLeds', 0x00ff0000, 0)  #right led turns green
        mot.walkTo(0,0.04 + ball[1],0)
        mot.kick(0)
        phase = 'BallNotFound'
    else:
        ledProxy.fadeRGB('RightFaceLeds', 0x00ff0000, 0)  #right led turns green

        # else a goal is found, together with it's color
        (color, kickangles ) = goal
        if type(kickangles[0]) == tuple:

            (first, second) = kickangles
            kickangle = (3 * first[0] + second[0]) / 4.0         # kick slightly more towards left pole
        else:
            kickangle = kickangles[0]

        if color == 'Blue':
            goalColor = 0
            ledProxy.fadeRGB('LeftFaceLeds',0x000000ff, 0) # blue goal
        else:
            goalColor = 1
            ledProxy.fadeRGB('LeftFaceLeds',0x00ff3000, 0) # yellow goal , anyone got a better value?
        print 'Goalcolor', goalColor, 'KickAngle', kickangle
        # Cases 1-3, if you see your own goal, kick to the other side

        if goalColor == teamColor:
            # Case 1, goal is left, kick to the right.
            if kickangle >= 0.7:
                mot.kick(-1.1)
            # Case 2, goal is right, kick to the left.
            if kickangle <= -0.7:
                mot.kick(1.1)
            else:
            # Case 3, goal is straight forward, HAK
                mot.sideLeftKick()

        else:
            # Case 4, other player's goal is found.
            # Kick towards it.

            # general kick interface distributes kick
            ledProxy.fadeRGB('RightFaceLeds', 0x00ff0000, 0)  #right led turns green
            mot.kick(kickangle, kalmanFilterBall.iterate(ball, [0,0,0]))
        ledProxy.fadeRGB('LeftFaceLeds',0x00000000, 0)
        phase = 'BallNotFound'

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
        mot.postWalkTo(2, 0, 0)
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
    global coachThread
    gsc.start()
    state = 0
    while(state != 4 or gsc.getSecondaryState()):
        #print 'soul.py State: ', state
        state = gsc.getState()
        states.get(state)()
    try:
        # close all threads
        coachThread.close()
    except:
        pass
    gsc.close()
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

awakeSoul()

# DEBUG #
def testPhase(phase, interval):
    now = time.time()
    while time.time() - now < interval:
        phases.get(phase)()
