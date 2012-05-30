"""
File: headMotionHandler.py
Author: Auke Wiggers
Description: Contains a class that has full control over the head, enabling
passive scan movements (to look for features or the ball while walking or 
performing other tasks)
"""
import time
import threading

def debug():
    """ debug() -> headMotionHandler object

    Returns a hmHandler object for debugging purposes.
    
    """ 
    from naoqi import ALProxy
    import visionHandler as v
    ledProxy = ALProxy('ALLeds',   '127.0.0.1', 9559)
    memProxy = ALProxy('ALMemory',   '127.0.0.1', 9559)
    motProxy = ALProxy('ALMotion', '127.0.0.1', 9559)    
    vidProxy = ALProxy('ALVideoDevice', '127.0.0.1', 9559)
    vis = v.VisionHandler(ledProxy, memProxy, motProxy, vidProxy)
    hmh = HeadMotionHandler(motProxy, vis)
    return hmh

class HeadMotionHandler(threading.Thread):
    """ class HeadMotionHandler
    
    Threaded instance that has full control over the head of the nao. 
    Executes scanning motions. Receives info from VisionHandler about perceived
    obects.
    
    Parent class: MotionHandler.
    Subclass(es): VisionHandler.   
    
    """
    def __init__(self, motProxy, visionHandler):
        threading.Thread.__init__(self)

        self.motProxy      = motProxy
        self.visionHandler = visionHandler    
                
        self.ballScan    = False
        self.goalScan    = False
        self.featureScan = False
        self.running     = True

    def __del__(self):
        self.close()
        
    def close(self):
        """ safely close the thread """
        self.running = False        
        
    def run(self):
        """ Main loop, either performs ballscanning behavior or feature-
        scanning or goalscanning """
        while self.running:
            if self.ballScan:
                if not self.visionHandler.seenBall:
                    self.scanForBall()
            elif self.goalScan:
                self.scanForGoal()
                
            elif self.featureScan:
                if not self.visionHandler.seenBall:
                    self.scanForFeatures()
            else:
                self.setHead(0, 0)
                time.sleep(0.25)
                
    def setBallScanning(self, trackBall=True):
        """ Make nao scan for ball, not features """
        self.visionHandler.setBallScanning(True, trackBall) 
        self.ballScan    = True
        self.goalScan    = False
        self.featureScan = False

    def setGoalScanning(self):
        """ Makes nao scan for goal and nothing else """
        self.visionHandler.setGoalScanning(True)
        self.ballScan    = False
        self.goalScan    = True
        self.featureScan = False

    def setFeatureScanning(self, trackBall=True):
        """ Makes nao scan for both ball and goal"""
        self.visionHandler.setFeatureScanning(True, trackBall)
        self.ballScan    = False
        self.goalScan    = False
        self.featureScan = True
    
    def pause(self):
        """ Pause headmotionhandler """
        self.visionHandler.pause()
        self.ballScan    = False
        self.goalScan    = False
        self.featureScan = False
        self.setHead(0, 0)
        
    def scanForGoal(self, speed = 0.125):
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
            goal = self.visionHandler.getGoal()
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
        """ 
        
        Execute a motion that scans for features in the field. 
        
        """
        now = time.time()
        while time.time() - now < 0.2:
            if self.visionHandler.seenBall:
                return True
        
        for yaw, pitch, t in [(-1, 0.5, 0.5), ( 1,  0.5, 1.5), (1,  0.1, 0.2),
                            (-1, 0.1, 2),   (-1.5, -0.4, 0.5), (1.5, -0.4, 3)]:
            self.motProxy.post.angleInterpolation( ["HeadPitch", "HeadYaw"],
                                                   [[pitch],      [yaw]   ],
                                                   [[t],          [t]     ],
                                                   True )
            
            now = time.time()
            while time.time() - now < t:
                # look for the ball in a given timespan
                if self.visionHandler.seenBall == True:
                    return True
                time.sleep(0.05)
                
    def scanForBall( self ):
        """ scanForBall() -> None
        
        Execute a motion that scans for the ball.
        
        """
        now = time.time()
        while time.time() - now < 0.2:
            if self.visionHandler.seenBall:
                return True
            
        for yaw, pitch, t in [(-1, 0.5, 0.5), (1, 0.5, 1.5), (1, 0.1, 0.2),
                             (-1, 0.1, 2),  (-1.5, -0.4, 0.5), (1.5, -0.4, 3)]:
            self.motProxy.post.angleInterpolation( ["HeadPitch", "HeadYaw"],
                                                   [[pitch],      [yaw]   ], 
                                                   [[t],          [t]     ], 
                                                   True )
            
            now = time.time()
            while time.time() - now < t:
                if self.visionHandler.seenBall == True:
                    return True
                time.sleep(0.05)
        
    def setHead( self, yaw, pitch, speed = 0.6 ):
        """ setHead( yaw, pitch, speed ) -> None
        
        Set the head in a specific position. Note that if control is given to 
        balltracking (parameter trackBall), this will not work.
        
        """
        self.motProxy.killTasksUsingResources( ["HeadYaw", "HeadPitch"] )
        self.motProxy.setAngles(["HeadYaw", "HeadPitch"],
                                [yaw,        pitch     ],
                                speed )