# Vision Interface for soul planner
# By: Camiel Verschoor, Auke Wiggers

#import threading
import longDistanceTracker as ball
import locateGoalzor as goal
import time
import Image
import math
import threading

def debug():
    from naoqi import ALProxy
    motProxy = ALProxy( 'ALMotion', '127.0.0.1', 9559 )
    vidProxy = ALProxy( 'ALVideoDevice', '127.0.0.1', 9559 )
    memProxy = ALProxy( 'ALMemory', '127.0.0.1', 9559 ) 
    ledProxy = ALProxy( 'ALLeds', '127.0.0.1', 9559 ) 
    vis = VisionInterface( motProxy , vidProxy, memProxy, ledProxy )
    vt = VisionThread( vis, memProxy, ledProxy )
    return vis, vt
        
class VisionInterface():
    def __init__(self, motProxy, vidProxy, memProxy, ledProxy):
        self.motProxy = motProxy
        self.vidProxy = vidProxy
        self.memProxy = memProxy
        self.ledProxy = ledProxy

        self.subscribed = False
        
        # use the bottom Camera
        self.vidProxy.setParam(18, 1)
        self.vidProxy.startFrameGrabber()
        self.visionID = self.subscribe()

    def unsubscribe(self):
        if self.subscribed:
            self.vidProxy.unsubscribe('python_GVM')
    
    def subscribe(self):
        self.unsubscribe()
        # subscribe(gvmName, resolution={0,1,2}, colorSpace={0,9,10,11,12,13},
        #           fps={5,10,15,30}

        self.subscribed = True
        return self.vidProxy.subscribe('python_GVM', 1, 11, 30)

    def snapShot(self):
        ''' TODO: test accuracy of useSensorValues={True, False} '''
        #getPosition(name, space={0,1,2}, useSensorValues)
        # Make image
        shot = self.vidProxy.getImageRemote(self.visionID)
        vid = self.motProxy.getPosition('CameraBottom', 2, True)
        head = self.motProxy.getAngles(['HeadPitch', 'HeadYaw'], True)
    
        # Get image
        # shot[0]=width, shot[1]=height, shot[6]=image-data
        size = (shot[0], shot[1])
        picture = Image.frombuffer('RGB', size, shot[6], 'raw', 'BGR', 0, 1)
        return (picture, (vid, head))
     
    def getGoal(self, image, headinfo):
        #now = time.time()
        # Filter the snapshots and return the angle and the color
        (_, head) = headinfo
        goalLoc = None
        yellow = goal.run(image, head[1], 'yellow')
        if yellow:
            goalLoc = ('Yellow', yellow)
            # yellow goal , anyone got a better value?
            self.ledProxy.fadeRGB('LeftFaceLeds',0x00ff3000, 0)     
        else:
            blue = goal.run(image, head[1], 'blue')        
            if blue:    
                goalLoc = ('Blue',blue)
                # blue LeftFaceLed
                self.ledProxy.fadeRGB('LeftFaceLeds', 0xffffff, 0)
        return goalLoc
        #print time.time()-now
        
    def getBall(self, image, headinfo):
        # Take snapshot and measure head angles
        ballLoc = ball.run(image, headinfo)
        if ballLoc:
            # Right leds turn green
            self.ledProxy.fadeRGB('RightFaceLeds', 0x0000ff00, 0)
            (x,y) = ballLoc
            if x < 0 or x > 6 or y < -4 or y > 4:
                ballLoc = None
            else:
                self.memProxy.insertData('dntBallDist', math.sqrt(x**2 + y**2))
        else:
            
            self.memProxy.insertData('dntBallDist', 0)
            self.ledProxy.fadeRGB('RightFaceLeds',0x00ff0000, 0)
        return ballLoc
    
    # scan movement to find ball
    def scanCircle( self, vt ):      
        loc = None
        
        # extra check to stop the head from making unnecessary movements
        ball = vt.findBall()
        if ball:
            return ball
        
        for yaw,pitch,t in [(-1, 0.5, 0.5), (1, 0.5, 1.5), (1, 0.1, 0.2), (-1, 0.1, 2), (-1, -0.4, 0.2), (1, -0.4, 3)]:
            self.motProxy.post.angleInterpolation( ['HeadPitch', 'HeadYaw'], [[pitch], [yaw]], [[t], [t]], True )
            
            now = time.time()
            while time.time() - now < t:
                # look for the ball in a given timespan
                loc = vt.findBall()
                if loc:
                    return loc
           
    def scanCircleGoal(self,speed = 0.125): 
        yawRange = [-1.5, 1.5]    
        # initialize variables
        realGoal = None
        tempGoal = None

        for r in [0,1]:
            if -2>yawRange[r]:
                yawRange[r] = -2
            elif 2<yawRange[r]:
                yawRange[r] = 2     
        
        # move head to starting position
        time.sleep(0.1)
        self.motProxy.angleInterpolationWithSpeed(['HeadPitch', 'HeadYaw'], \
                                    [-0.47, -1.5], 1.0, True)
        time.sleep(0.1)
        # then start headmovement
        self.motProxy.setAngles('HeadYaw', yawRange[1], speed)
        while self.motProxy.getAngles('HeadYaw', True)[0] < yawRange[1] -0.05:
            (image, headinfo) = self.snapShot()
            goal = self.getGoal(image, headinfo)
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
                self.motProxy.changeAngles('HeadYaw', 0.001, 1 )
                break
        # stop goalscanning, start finding ball again
        
        # start scanning for ball , move head to ballfinding position
        # self.motProxy.post.angleInterpolation(['HeadPitch', 'HeadYaw'], [[0.5], [0]], [[0.15], [0.15]], True)
        
        # if only one goalpost is found
        if not(realGoal) and tempGoal:
            realGoal = tempGoal
        #print 'Goal at:', realGoal
        return realGoal                                 

    def fps(self, vis):
        now = time.time()
        f = 0      
        while time.time() - now < 1:
            find = vis.findBall()
            f += 1
        return f
    
# vision class keeps scanning for ball/goal in images, depending on variables ball and goal
class VisionThread(threading.Thread):
    ballLoc = None
    on = True
    scanning = True
    checked = False
    lock = threading.Lock()
    
    # constructor    
    def __init__(self, interface, memProxy, ledProxy):
        threading.Thread.__init__(self)
        self.interface = interface
        self.memProxy = memProxy
        self.ledProxy = ledProxy
    
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
                (image, headinfo) = self.interface.snapShot()
                self.ballLoc = self.interface.getBall(image,headinfo)
                # shared variable access makes this necessary
                with self.lock:
                    self.checked = False
            else:
                time.sleep(0.1)
                self.interface.memProxy.insertData('dntBallDist', 0)
                # no ballscanning, right led turns yellow
                self.ledProxy.off('RightFaceLeds')
                
    # stop main iteration 
    def stopScan(self):
        self.scanning = False
    
    def active(self):
        return self.scanning
    
    # close thread
    def close(self):
        self.on = False
        self.scanning = False
        print 'visThread closed safely'
        
    # start finding of ball
    def startScan(self):
        self.on = True
        self.scanning = True
    
    # return last found ballloc (none if none found)
    def findBall(self):
        # while there is no 'new' balllocation available, wait
        now = time.time()
        while self.checked and time.time() - now < 0.5:
            time.sleep(0.01)
        with self.lock:
            self.checked = True
        return self.ballLoc
       
    # clear variables
    def clearCache(self):
        self.ballLoc = None        
    
# range with float step 
def xfrange(start, stop, step):
    while start < stop:
        yield start
        start += step
