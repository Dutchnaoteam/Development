
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
import kalmanFilter as kalman
import particleFilter as particle

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
#(teamColor, kickOff, penalty) = sc.getMatchInfo()   
teamColor = 0
kickOff = 0
penalty = 0

kalmanFilterBall = kalman.KalmanBall()
particleFilter   = particle.ParticleFilter()
particleFilter.start()

# testposition
position         = [3, 2, 0]

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
        print 'TeamColor: ' , teamColor       # print the teamcolor as a check

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
        # stop ballfinding, there is no ball anyway
        visThread.stopScan()
        print 'In ready state'
        mot.killWalk()
        ledProxy.fadeRGB('ChestLeds',0x000000ff, 0) # set ChestLeds

         
        firstCall['Initial'] = True   
        firstCall['Ready']   = False
        firstCall['Set']     = True
        firstCall['Playing'] = True
        firstCall['Penalized'] = True
    
        # feed the particle filter the nao's current position (remember, we already know it!)
        numberOfSamples = 100
        particleFilter.reset( position, numberOfSamples )
        particleFilter.startFilter()
        
    goal = vis.scanCircleGoal()
    desiredPosition = [ 6.0, 2.0, 1.57 ] 
    
    localize( goal, 'Goal' , desiredPosition )
    
    #print 'At position', position
    
def localize( features, featureType, desiredPosition ):
    global position
    
    # begin with an empty measurement
    measurement = [None]
    
    # if there are features found 
    if features:
        # of type goal
        if featureType == 'Goal':
            # try to distinguish the pole and use it to create a valid measurement
            x,y,theta = position
            print features
            
            ( color , goalposts ) = features
            # When found two posts, goalposts format 
            # = ((post1,distance1), (post2, distance2))
            if type(goalposts[1]) == tuple:
                post1, post2 = goalposts
                bearing1, range1 = post1
                bearing2, range2 = post2
                
                signature1 = 0
                signature2 = 0
                
                if bearing1 > bearing2:
                    idFeature1 = color + 'PoleLeft'
                    idFeature2 = color + 'PoleRight'
                else:
                    idFeature1 = color + 'PoleRight'
                    idFeature2 = color + 'PoleLeft'
                measurement = [[ bearing1, range1, signature1, idFeature1 ],\
                               [ bearing2, range2, signature2, idFeature2 ]]
            else:
                bearing, range = goalposts
                signature = 0       
                
                ''' TODO find which pole is more likely to be seen '''
                if color == 'Blue':
                    if (y < 3 and theta + bearing > 0) or theta + bearing  > 0.5:
                        idFeature = 'BluePoleLeft'
                        print 'Saw left blue pole'
                    else:
                        idFeature = 'BluePoleRight'
                        print 'Saw blue right pole'
                else:
                    if (y < 3 and theta + bearing < 0) or (theta + bearing < -0.5):
                        idFeature = 'YellowPoleRight'
                        print 'Saw yellow right pole'
                    else:
                        idFeature = 'YellowPoleLeft'
                        print 'Saw yellow left pole'

                measurement = [[ bearing, range, signature, idFeature]]
        
    control = mot.getRobotVelocity() 

    particleFilter.setMeasurements( measurement )
    
    position = particleFilter.getPosition()
    
    x1,y1,t1 = position
    x2,y2,t2 = desiredPosition
    
    t = minimizedAngle( t2 - t1 )
    
    print 'walking to ', x2 - x1 , y2 - y1, t
    mot.SWTV( ( x2 - x1) / 3.0, (y2 -y1)/5.0, 0 )
    
# Convert numbers from range 0 to 2pi to -pi to pi
def minimizedAngle( angle ) :
    if angle > math.pi:
        angle -= 2*math.pi
    if angle <= -math.pi:
        angle += 2*math.pi
    return angle
   
        
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
        visThread.startScan()                           # start ballscan

        print 'TeamColor: ' , teamColor                 # print teamcolor as a check
        
        # Initial pose, if not already in it
        mot.stiff()
        if playerType == 0:
            mot.normalPose()
        else:
            mot.keepNormalPose()
        
        audProxy.setOutputVolume(0)                     # set volume to zero    
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
        particleFilter.reset( position )
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
        position = particleFilter.meanState
    
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

    

def UnpenalizedKeep():
    global phase
    global ball_loc
    global position
    
    if color == 0:
        desiredPosition = [0, 2, 0]
    else:
        desiredPosition = [6, 2, math.pi]
    
    goal = vis.scanCircleGoal()
    localize( goal, 'Goal' , desiredPosition )
    
    print 'At position', position
    
    x1,y1,t1 = position
    x2,y2,t2 = desiredPosition
    
    # walk straight towards a goal if you see one
    mot.postWalkTo( x2-x1,y2-y1, minimizedAngle( (t2-t1)-math.pi ) )
    
    
    
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
    
    seen = False
    
    # FIND A BALL #
    ball = visThread.findBall()
    if ball:
        seen = True
    
    if firstCall['BallFound']:
        ledProxy.fadeRGB('RightFaceLeds', 0x0000ff00, 0)
        firstCall['BallFound'] = False
        # initialize mean mu for kalman filter
        if seen:
            kalmanFilterBall.setFirstCall(True, ball)
        
    ball = kalmanFilterBall.iterate(ball)
    
    (x,y) = ball
    print x,y
    memProxy.insertData('dntPhase', 'BallFound')
    memProxy.insertData('dntBallDist', math.sqrt(x**2 + y**2))

    if x < 0.17 and -0.02 < y < 0.02 and seen:
        print 'Kick'
        # BLOCKING CALL: FIND BALL WHILE STANDING STILL FOR ACCURATE CORRECTION
        mot.killWalk()
        phase = 'Kick'
        
    else:            
        if seen:
            print 'Seen ball'
            # hacked influencing of perception, causing walking forward to have priority
            theta = math.atan(y/x) / 2.5
            x = 3 * (x-0.17)
            
            if  -0.1 < y < 0.1 :
                y = 0.5 * y
            else:
                y = 2.0 * y
        else:
            print 'Not seen ball'
            # find the 'ideal' headposition based on the kalman filter position
            (yaw, pitch) = vis.calcHeadAngle( (x,y), (320,480), True)
            mot.changeHead( yaw * 0.5, pitch * 0.5 )
            
            # hacked influencing, turn towards last found position first
            theta = math.atan(y/x) / 2.0
            x = (x/3.0 -0.2)
            y = 0
            

        mot.SWTV(x , y, theta, 1.0)
    
    # If covariance becomes too large, when?
    if kalmanFilterBall.Sigma[0][0] > 4.0:
        
        print kalmanFilterBall.Sigma
        print 'Perhaps the ball is lost, turning ', y,'to find it' 
        mot.postWalkTo(0,0, math.atan(y / x))
        phase = 'BallNotFound'

def BallNotFound():
    global ball_loc
    global phase
    
    # if this is the first time the ball is not founnd
    if firstCall['BallNotFound']:
        memProxy.insertData('dntPhase', 'BallNotFound')
        memProxy.insertData('dntBallDist', 0)    
        ledProxy.fadeRGB('RightFaceLeds',0x00ff0000, 0) # no ball, led turns red
        mot.killWalk()
        firstCall['BallNotFound'] = False
        
    # try to find a ball
    if vis.scanCircle(visThread, 0.2):
        phase = 'BallFound'
        firstCall['BallNotFound'] = True
    else:
        # if no ball is found circle slowly while searching for it
        mot.postWalkTo(0, 0, 1.3)
        
def Kick():
    global phase
    memProxy.insertData('dntPhase', 'Kick')
    visThread.stopScan()
    
    ledProxy.fadeRGB('LeftFaceLeds',0x00000000, 0) # no goal yet, left led turns black
    ledProxy.fadeRGB('RightFaceLeds', 0x00ff0000, 0) # no ball anymore, right led turns red
    
    # scan for a goal
    goal = vis.scanCircleGoal()
    motProxy.post.angleInterpolation(['HeadPitch', 'HeadYaw'], [[0.5], [0]], [[0.15], [0.15]], True)
    visThread.startScan()
    
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
        if len(kickangles) == 2:
        
            (first, second) = kickangles 
            kickangle = (3 * first + second) / 4.0   # kick slightly more towards left pole 
        else:
            kickangle = kickangles[0]
            
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
    
    visThread.startScan()
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
    particleFilter.close()
    
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

#awakeSoul()

# DEBUG #
def testPhase(phase, interval):
    now = time.time()
    while time.time() - now < interval:
        phases.get(phase)()
