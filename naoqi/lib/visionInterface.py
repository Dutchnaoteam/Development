# Vision Interface for soul planner
# By: Camiel Verschoor, Auke Wiggers

#import threading
import longDistanceTracker as ball
import locateGoalzor as goal
import time
import Image
import math
import threading
from naoqi import ALProxy

motProxy = ALProxy("ALMotion", "127.0.0.1", 9559)
vidProxy = ALProxy("ALVideoDevice", "127.0.0.1", 9559)
memProxy = ALProxy("ALMemory", "127.0.0.1", 9559)

# use the bottom Camera
vidProxy.setParam(18, 1)
vidProxy.startFrameGrabber()
def unsubscribe():
    try:
        vidProxy.unsubscribe("python_GVM")
    except:
        pass
    
def subscribe():
    unsubscribe()
    # subscribe(gvmName, resolution={0,1,2}, colorSpace={0,9,10,11,12,13},
    #           fps={5,10,15,30}
    return vidProxy.subscribe("python_GVM", 0, 11, 30)

# Vision ID
unsubscribe()
visionID = subscribe()
# METHODS FOR VISION

def snapShot(nameId):
    ''' TODO: test accuracy of useSensorValues={True, False} '''
    #getPosition(name, space={0,1,2}, useSensorValues)
    # Make image
    shot = vidProxy.getImageRemote(nameId)
        
    vid = motProxy.getPosition('CameraBottom', 2, True)
    head = motProxy.getAngles(["HeadPitch", "HeadYaw"], True)
    
    # Get image
    # shot[0]=width, shot[1]=height, shot[6]=image-data
    size = (shot[0], shot[1])
    picture = Image.frombuffer("RGB", size, shot[6], "raw", "BGR", 0, 1)
    return (picture, (vid, head))
 
def getGoal(image, headinfo):
    #now = time.time()
    # Filter the snapshots and return the angle and the color
    (_, head) = headinfo
    goalLoc = None
    yellow = goal.run(image, head[1], 'yellow')
    if yellow:
        goalLoc = ('Yellow', yellow)
    else:
        blue = goal.run(image, head[1], 'blue')        
        if blue:
            goalLoc = ('Blue',blue)
    return goalLoc
    #print time.time()-now
    
def getBall(image, headinfo):
    # Take snapshot and measure head angles
    ballLoc = ball.run(image, headinfo)
    if ballLoc:
        (x,y) = ballLoc
        if x < 0 or x > 6 or y < -4 or y > 4:
            ballLoc = None
        else:
            memProxy.insertData('dntBallDist', math.sqrt(x**2 + y**2))
    else:
        memProxy.insertData('dntBallDist', '')                
    return ballLoc
    
    
# vision class keeps scanning for ball/goal in images, depending on variables ball and goal
class Vision(threading.Thread):
    '''TODO: Make visioninterface update goalposition only at certain headpositions, no movement during scan'''
    ballLoc = None
    on = True
    scanning = True
    checked = False
    lock = threading.Lock()
    
    # constructor    
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
    
    # destructor
    def __del__(self):
        self.scanning = False
        self.on = False
        
    # main iteration    
    def run(self):
        # currently no safe way to stop thread
        while self.on:
            # on is the variable that states if a ball and/or goal should be found
            if self.scanning:
                
                # take a snapshot
                (image, headinfo) = snapShot(visionID)
                self.ballLoc = getBall(image,headinfo)
                # shared variable access makes this necessary
                with self.lock:
                    self.checked = False
            else:
                time.sleep(0.1)
                
    # stop main iteration 
    def stopScan(self):
        self.scanning = False
    
    def active(self):
        return self.scanning
    
    # close thread
    def close(self):
        self.on = False
        self.scanning = False
        
    # start finding of ball
    def startScan(self):
        self.on = True
        self.scanning = True
    
    # return last found ballloc (none if none found)
    def findBall(self):
        # while there is no 'new' balllocation available, wait
        while self.checked or self.lock.locked():
            pass
        with self.lock:
            self.checked = True
        return self.ballLoc
       
    # clear variables
    def clearCache(self):
        self.ballLoc = None
    
# scan movement to find ball
def scanCircle(vis, interval):            
    loc = None
    
    # extra check to stop the head from making unnecessary movements
    ball = vis.findBall()
    if ball:
        loc = ball
    for angles in [(-1.1, -0.4), (-0.75, -0.4), (-0.5, -0.4), (-0.25, -0.4), ( 0, -0.4), (0.25, -0.4), ( 0.5, -0.4), ( 1.1, -0.4), \
                   ( 1,  0.1  ), (0.75, 0.1), ( 0.5,  0.1  ), (0.25, 0.1), ( 0,  0.1  ), (-0.25, 0.1), (-0.5,  0.1  ), (-0.75, 0.1), (-1,  0.1  ), \
                   (-1,  0.4), (-0.5,  0.4),  ( 0,  0.5),  ( 0.5,  0.4),( 1,  0.4), (0,0) ]: # last one is to make successive scans easier
        motProxy.setAngles(['HeadYaw', 'HeadPitch'], [angles[0], angles[1]], 0.5)
    
        # look for the ball in a given timespan
        now = time.time()
        while time.time() - now < interval and not(loc):
            loc = vis.findBall()
        if loc: 
            break
    
    return loc
            
def scanCircleGoal(yawRange = {0:-1.5, 1:1.5}):            
    # initialize variables
    realGoal = None
    tempGoal = None

    for r in [0,1]:
        if -2>yawRange[r]:
            yawRange[r] = -2
        elif 2<yawRange[r]:
            yawRange[r] = 2     
    
    # move head to starting position
    motProxy.setAngles(['HeadPitch', 'HeadYaw'], [-0.5, yawRange[0] ], 0.8)
    time.sleep(0.6)
    
    increment = math.copysign(0.25, yawRange[1])
    for yaw in xfrange( yawRange[0] + increment, yawRange[1] + increment, increment):
        # take a snapshot..
        (image, headinfo) = snapShot(visionID)
        # then start headmovement
        motProxy.setAngles('HeadYaw', yaw, 0.5)
        # finally, start calculations
        goal = getGoal(image, headinfo)
        time.sleep(0.2)
        if goal:
            # goal is ( color, ( (angle, width), (angle, width) )
            #      or ( color, ( (angle, width),  None          )
            #      or   None (but not in this case)
            
            (color, posts) = goal
            # CASE 0: two poles found. exit if they are not the same pole
            if posts[1]:                        # if two poles found
                if abs( posts[0][0] - posts[1][0] ) > 0.2: # if not the same pole
                    realGoal = goal                 # escape while loop
                else:
                    tempGoal = ( color, posts[0] )
                    
            # CASE 1: one pole found, one in mem. exit
            elif tempGoal:                      # if one found and one remembered
                if tempGoal[0] == color:        # if of the correct color
                    
                    if abs( posts[0][0] - tempGoal[1][0] ) > 0.2: # if not the same pole
                        realGoal = (color, (tempGoal[1], posts[0]))  # return the entire goal
                        
            # CASE 2: one pole found, none in mem. Store pole
            else:
                tempGoal = ( color, posts[0] )
                
        if realGoal:
            break
    # stop goalscanning, start finding ball again
    
    # start scanning for ball , move head to ballfinding position
    # motProxy.post.angleInterpolation(['HeadPitch', 'HeadYaw'], [[0.5], [0]], [[0.15], [0.15]], True)
    
    # if only one goalpost is found
    if not(realGoal) and tempGoal:
        realGoal = tempGoal
    #print 'Goal at:', realGoal
    return realGoal                                 

# range with float step 
def xfrange(start, stop, step):
    while start < stop:
        yield start
        start += step


    
def fps(vis):
    now = time.time()
    f = 0      
    while time.time() - now < 1:
        find = vis.findBall()
        while vis.findBall() == find: 
            pass
        f += 1
    return f
    
    
def calcPosition(coordInImage, size):
    vid = motProxy.getPosition('CameraBottom', 2, True)
    
    (width, height) = size
    #print 'size: ', width, ', ', height
    # coord with origin in the upperleft corner of the image
    (xCoord, yCoord) = coordInImage
    #print 'pixelCoord from upperLeft: ', xCoord, ', ', yCoord
    # change the origin to centre of the image
    xCoord = -xCoord + width/2.0
    yCoord = yCoord - height/2.0
    #print 'pixelCoord from centre: ', xCoord, ', ', yCoord
    # convert pixel coord to angle
    radiusPerPixel = 0.005061454830783556
    xAngle = xCoord * radiusPerPixel
    yAngle = yCoord * radiusPerPixel
    if -1 < xAngle < 1 and -1 < yAngle < 1:
        motion.changeAngles(['HeadPitch', 'HeadYaw'], [0.5*yAngle, 0.5*xAngle], 0.4)  # 0.5*angles for smoother movements, optional. Smoothinggg. 

    #print 'angle from camera: ' + str(xAngle) + ', ' + str(yAngle)

    # the position (x, y, z) and angle (roll, pitch, yaw) of the camera
    (x,y,z, roll,pitch,yaw) = vid
    #print 'cam: ', cam

    # the pitch has an error of 0.940063x + 0.147563
    pitch = 0.940063*pitch + 0.147563
    #print 'correctedPitch: ', pitch
    
    # position of the ball where
    #  origin with position and rotation of camera
    #ballRadius = 0.0325     # in meters
    ballRadius = 0.065
    xPos = (z-ballRadius) / tan(pitch + yAngle)
    yPos = tan(xAngle) * xPos
    #print 'position from camera: ', xPos, ', ', yPos
    # position of the ball where
    #  origin with position of camera and rotation of body 
    xPos =math.cos(yaw)*xPos + -math.sin(yaw)*yPos
    yPos =math.sin(yaw)*xPos + math.cos(yaw)*yPos
    # position of the ball where
    #  origin with position and rotation of body
    xPos += x
    yPos += y
    #print 'position ball: ', xPos, ', ', yPos
    #print 'new yaw/pitch: ', xAngle+yaw, yAngle+pitch
    #print 'z / tan(pitch): ',(z-ballRadius) / tan(pitch)
    return (xPos, yPos, xAngle, yAngle)

def calcCoordInImage(position, size):
    (xAngle,yAngle) = calcHeadAngle(position, size)

    # convert pixel coord to angle
    radiusPerPixel = 0.005061454830783556
    xCoord = xAngle / radiusPerPixel
    yCoord = yAngle / radiusPerPixel

    # change the origin to upper left corner of the image
    xCoord = -(xCoord - width/2.0)
    yCoord = (yCoord + height/2.0)

    # coord with origin in the upperleft corner of the image
    (xCoord, yCoord) = coord

    return coord

def calcHeadAngle(position, size, relative = True):
    vid = motProxy.getPosition('CameraBottom', 2, True)
    
    # the position (x, y, z) and angle (roll, pitch, yaw) of the camera
    (x,y,z, roll,pitch,yaw) = vid
    # the pitch has an error of 0.940063x + 0.147563 or something
    pitch = 0.940063*pitch + 0.147563

    # the size of the image
    (width, height) = size
    
    (xPos, yPos) = position
    xPos -= x
    yPos -= y
    
    # rotation backwards according to neckyaw
    xPos = math.cos(-yaw)*xPos + -math.sin(-yaw)*yPos
    yPos = math.sin(-yaw)*xPos + math.cos(-yaw)*yPos

    #ballRadius = 0.0325     # in meters
    ballRadius = 0.065
    
    yAngle = math.atan( (z-ballRadius) / xPos )
 
    # convert to nao values!
    print yAngle
    
    xAngle = math.atan(yPos/xPos)
    
    if not relative:
        return yaw+xAngle, pitch+yAngle
    else:
        return xAngle, yAngle