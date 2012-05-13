"""
File: headMotionHandler
Author: Auke Wiggers
"""
import time
import visionHandler 
import threading

def debug():
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
    hmh = HeadMotionHandler( ledProxy, memProxy, motProxy, vidProxy )
    return hmh

class HeadMotionHandler(threading.Thread):
    """ 
    
    Threaded instance that has full control over the head of the nao. 
    Executes scanning motions. Receives info from VisionHandler about perceived
    obects (e.g. ball, goal). 
    
    Parent class: MotionHandler.
    Subclass(es): VisionHandler.   
    
    """
    def __init__(self, ledProxy, memProxy, motProxy, vidProxy ):
        threading.Thread.__init__(self)

        self.motProxy  = motProxy
        self.vision    = visionHandler.VisionHandler( ledProxy, memProxy,
                                                       motProxy, vidProxy )    
        self.vision.start()
        self.goalLoc = None
        self.features = list()
        
        self.lock = threading.Lock()
        
        self.ballScan = False
        self.goalScan = False
        self.featureScan = False
        self.running = True

    def __del__( self ):
        self.close()
        
    def close( self ):
        self.running = False        
        
    def run(self):
        while self.running:
            if self.ballScan:
                if not self.vision.seenBall:
                    self.scanForBall()
            elif self.goalScan:
                self.scanForGoal()
                
            elif self.featureScan:
                if not self.vision.seenBall:
                    self.scanForFeatures()
            else:
                self.setHead( 0, 0 )
                time.sleep(0.25)
                
                
    def setBallScanning( self, trackBall = True ):
        self.vision.setBallScanning( True, trackBall ) 
        self.ballScan    = True
        self.goalScan    = False
        self.featureScan = False
        
    def setGoalScanning( self ):    
        self.timestampGoal = time.time()
        self.vision.setGoalScanning( True )
        self.ballScan    = False
        self.goalScan    = True
        self.featureScan = False
        
    def setFeatureScanning( self, trackBall = True ):    
        self.vision.setFeatureScanning( True, trackBall )
        self.ballScan    = False
        self.goalScan    = False
        self.featureScan = True
    
    def pause( self ):
        self.vision.pause()
        self.ballScan    = False
        self.goalScan    = False
        self.featureScan = False        
        self.features = list()
        self.goalLoc = None
        
    def scanForGoal( self, speed = 0.125 ):
        """ scanForGoal() -> tuple goalLocation
        
        Scans for a goal at shoulderheight, fluent motion. Returns 
        None if no goal found. 
        
        """
        
        yawRange = [-1.5, 1.5]    
        # initialize variables
        realGoal = None
        tempGoal = None

        # move head to starting position
        time.sleep(0.1)
        self.motProxy.angleInterpolationWithSpeed(["HeadPitch", "HeadYaw"], \
                                    [-0.47, -1.5], 1.0, True)
        time.sleep(0.1)
        # then start headmovement
        self.motProxy.setAngles("HeadYaw", yawRange[1], speed)
        while self.motProxy.getAngles("HeadYaw", True)[0] < yawRange[1] -0.05:
            goal = self.vision.getGoal()
            if goal:
                # goal is ( color, ( (angle, width), (angle, width) )
                #      or ( color, ( (angle, width),  None          )
                #      or   None (but not in this case)
                
                (color, posts) = goal
                # CASE 0: two poles found. exit if they are not the same pole
                if posts[1]:                            # if two poles found
                    # if not same pole                    
                    if abs( posts[0][0]-posts[1][0] ) > 0.2: 
                        realGoal = goal                 # escape while loop
                    else:
                        tempGoal = ( color, posts[0] )
                        
                # CASE 1: one pole found, one in mem. exit
                elif tempGoal:                    # if one found,one remembered
                    if tempGoal[0] == color:      # if of the correct color
                        # if not the same pole
                        if abs( posts[0][0] - tempGoal[1][0] ) > 0.2:    
                            # return the entire goal
                            realGoal = (color, (tempGoal[1], posts[0]))  
                            
                # CASE 2: one pole found, none in mem. Store pole
                else:
                    tempGoal = ( color, posts[0] )
                    
            if realGoal:
                self.motProxy.changeAngles("HeadYaw", 0.001, 1 )
                break

        # if only one goalpost is found
        if not(realGoal) and tempGoal:
            realGoal = tempGoal
        #print "Goal at:", realGoal
        return realGoal  
        
    def scanForFeatures( self ):
        """ scanForFeatures() -> features as list [[bearing, range, ID],...]
        
        Execute a motion that scans for features in the field. 
        
        """
        now = time.time()
        while time.time() - now < 0.2:
            if self.vision.seenBall:
                    return True
        
        for yaw,pitch,t in [(-1, 0.5, 0.5), ( 1,  0.5, 1.5), (1,  0.1, 0.2), \
                            (-1, 0.1, 2),   (-1, -0.4, 0.2), (1, -0.4, 3   )]:
            self.motProxy.post.angleInterpolation( ["HeadPitch", "HeadYaw"], \
                                                   [[pitch],      [yaw]   ], 
                                                   [[t],          [t]     ], 
                                                   True )
            
            now = time.time()
            while time.time() - now < t:
                # look for the ball in a given timespan
                if self.vision.seenBall == True:
                    return True
                time.sleep(0.05)
                
    def scanForBall( self ):
        """ scanForBall() -> ball location as tuple
        
        Execute a motion that scans for the ball.
        
        """
        now = time.time()
        while time.time() - now < 0.2:
            if self.vision.seenBall:
                    return True
            
        for yaw,pitch,t in [(-1, 0.5, 0.5), ( 1,  0.5, 1.5), (1,  0.1, 0.2), \
                            (-1, 0.1, 2),   (-1, -0.4, 0.2), (1, -0.4, 3   )]:
            self.motProxy.post.angleInterpolation( ["HeadPitch", "HeadYaw"], \
                                                   [[pitch],      [yaw]   ], 
                                                   [[t],          [t]     ], 
                                                   True )
            
            now = time.time()
            while time.time() - now < t:
                if self.vision.seenBall == True:
                    return True
                time.sleep(0.05)
        
    def setHead( self, yaw, pitch, speed = 0.6 ):
        """ setHead( yaw, pitch, speed ) -> None
        
        Set the head in a specific position. Note that if control is given to 
        balltracking, this will not work.
        
        """
        self.motProxy.killTasksUsingResources( ["HeadYaw", "HeadPitch"] )
        self.motProxy.setAngles([ "HeadYaw", "HeadPitch"],
                                [ yaw,        pitch     ],
                                speed )