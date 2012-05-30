"""
File: visionHandler
Author: Camiel Verschoor & Auke Wiggers
"""

import longDistanceTracker as ballFinder
import locateGoalzor       as goalFinder
import kalmanFilter
import time
import Image
import math
import threading
import cv 

def debug():
    """ debug() -> visionHandler object

    Debug method that creates the correct instances to test classes 
    visionInterface and visionThread
    
    """
    from naoqi import ALProxy
    motProxy = ALProxy( "ALMotion", "127.0.0.1", 9559 )
    vidProxy = ALProxy( "ALVideoDevice", "127.0.0.1", 9559 )
    memProxy = ALProxy( "ALMemory", "127.0.0.1", 9559 ) 
    ledProxy = ALProxy( "ALLeds", "127.0.0.1", 9559 ) 
    vt = VisionHandler( ledProxy, memProxy, motProxy, vidProxy )
    return vt
    
class VisionHandler(threading.Thread):  	
    """
    
    VisionHandler class is a threaded instance that looks in images for either
    the ball, goal, or both.
    
    Parent class: HeadMotionHandler
    Subclass(es): None (files longdistancetracker, locategoalzor)    
    """    
    ballLoc = None
    running = True
    scanning = True
    checkedBall = False
    checkedGoal = False
    lock = threading.Lock()
    seenBall = False 
    # constructor    
    def __init__(self, ledProxy, memProxy, motProxy, vidProxy ):
        threading.Thread.__init__(self)
        self.memProxy = memProxy
        self.ledProxy = ledProxy
        self.motProxy = motProxy
        self.vidProxy = vidProxy
        
        # Booleans
        self.running  = True 
        self.ballScanning = False
        self.featureScanning = False
        self.goalScanning = False
        
        self.ballLoc = None
        self.goalLoc = None
        self.checkedGoal = False
        self.checkedBall = False
        
        self.trackBall =  True
        
        # use the bottom Camera
        self.vidProxy.setParam(18, 1)
        self.vidProxy.startFrameGrabber()
        self.visionID = self.subscribe()

        self.KF       = kalmanFilter.KalmanFilter( ) 
        self.timeStampLocalize = time.time()
        self.control = [0, 0, 0]                
        
    def __del__(self):
        self.running = False
        
    def run(self):
        """ Main loop """
        self.timeStampLocalize = time.time()
        # currently no safe way to stop thread
        while self.running:
            # scanning states if a ball should be found and tracked
            if self.ballScanning:
                (image, headinfo) = self.snapShot()
                self.ballLoc = self.findBall( image, headinfo, self.trackBall )
                # shared variable access makes this necessary
                with self.lock:
                    self.checkedBall = False
                self.goalLoc = None
                
            # localizing looks for features to use, but also the ball
            elif self.featureScanning:
                # take a snapshot
                (image, headinfo) = self.snapShot()
                self.ballLoc = self.findBall( image, headinfo, self.trackBall )
                self.goalLoc = self.findGoal( image, headinfo )
                # shared variable access makes this necessary
                with self.lock:
                    self.checkedBall = False
                    self.checkedGoal = False
            # scan for goal 
            elif self.goalScanning:
                (image, headinfo) = self.snapShot()
                self.goalLoc = self.findGoal( image, headinfo )
                with self.lock:
                    self.checkedGoal = False
                self.ballLoc = None
            else:
                # no ballscanning or goalscanning, leds turn off entirely
                self.memProxy.insertData("dntBallDist", 0)
                self.ledProxy.off("RightFaceLeds")
                self.ledProxy.off("LeftFaceLeds")                
                self.ballLoc = None
                self.goalLoc = None
                with self.lock:
                    self.checkedGoal = False
                    self.checkedBall = False
                time.sleep(0.5)
                self.control = [0, 0, 0]
                self.timeStampLocalize = time.time()
                
    def getBall(self):
        """ return last found ballloc (none if none found) """
        now = time.time()
        while self.checkedBall and time.time() - now < 0.5:
            pass
        with self.lock:
            self.checkedBall = True
        return self.ballLoc
    
    def getGoal(self):
        """ return last found goalLoc (none if none found) """
        now = time.time()
        while self.checkedGoal and time.time() - now < 0.5:
            pass
        with self.lock:
            self.checkedGoal = True
        return self.goalLoc
        
    def unsubscribe(self):
        """Try to unsubscribe from the camera""" 
        try:
            self.vidProxy.unsubscribe("python_GVM")
        except Exception as inst:
            print "Unsubscribing impossible:", inst
    
    def subscribe(self, resolution=1):
        """ subscribe() -> String visionID

        Subscribe to the camera feed.
        
        """
        self.unsubscribe()
        # subscribe(gvmName, resolution={0,1,2}, colorSpace={0,9,10,11,12,13},
        #           fps={5,10,15,30}
        return self.vidProxy.subscribe("python_GVM", resolution, 11, 30)

    def snapShot(self):
        """ snapShot() -> iplImg, (cameraPos6D, headAngles)

        Take a snapshot from the current subscribed video feed. 
        
        """
        # getPosition(name, space={0,1,2}, useSensorValues)
        # Make image
        camPos = self.motProxy.getPosition("CameraBottom", 2, True)
        headAngles = self.motProxy.getAngles(["HeadPitch", "HeadYaw"], True)
        shot = self.vidProxy.getImageRemote(self.visionID)
        
        # Get image
        # shot[0]=width, shot[1]=height, shot[6]=image-data
        size = (shot[0], shot[1])
        picture = Image.frombuffer("RGB", size, shot[6], "raw", "BGR", 0, 1)
        
        size = picture.size
        # convert the type to OpenCV
        image = cv.CreateImageHeader(size, cv.IPL_DEPTH_8U, 3)
        cv.SetData(image, picture.tostring(), picture.size[0]*3)
        hsvFrame = cv.CreateImage(cv.GetSize(image), cv.IPL_DEPTH_8U, 3)
        cv.CvtColor(image, hsvFrame, cv.CV_BGR2HSV)
    
        return (hsvFrame, (camPos, headAngles))
    
    def findBall(self, image, headinfo, track=True ):
        """ getBall(image, headinfo) -> tuple BallLocation

        Search a given image for a ball. Return None if no ball found.        
        
        """         
        ballLoc = ballFinder.run(image, headinfo, track)
        if ballLoc:
            # Right leds turn green
            self.ledProxy.fadeRGB("RightFaceLeds", 0x0000ff00, 0)
            self.seenBall = True
            (x, y) = ballLoc
            if x < -0.5 or x > 6 or y < -4 or y > 4:
                ballLoc = None
            else:
                self.memProxy.insertData("dntBallDist", math.sqrt(x**2 + y**2))
        else:            
            self.seenBall = False
            self.memProxy.insertData("dntBallDist", 0)
            self.ledProxy.fadeRGB("RightFaceLeds", 0x00ff0000, 0)
            
        interval = time.time() - self.timeStampLocalize
        self.timeStampLocalize = time.time()
        control = []
        for i in range(3):
            control.append( self.control[i] * interval ) 
        self.KF.iterate( ballLoc, control )
        return ballLoc
    
    def setControl( self, control ):
        """ Set a control vector """
        self.control = control
                    
    def findGoal(self, image, headinfo):
        """ getGoal( image, headinfo ) -> tuple goalLocation
        
        Search a given image for a goal. Return None if no goal found.
        
        """
        # Filter the snapshots and return the angle and the color
        (_, head) = headinfo
        goalLoc = goalFinder.run(image, head[1])
        if goalLoc[0]:
            # yellow goal -> yellow leds
            self.ledProxy.fadeRGB("LeftFaceLeds", 0x00ff3000, 0)
        else:
            self.ledProxy.off("LeftFaceLeds")
        return goalLoc
    
    # start tracking of ball
    def setBallScanning(self, arg = True, trackBall = True):
        """ set the main loop to only scan for ball """
        self.ballScanning = arg
        self.goalScanning = False
        self.featureScanning = False
        self.trackBall = trackBall
        self.ledProxy.off("LeftFaceLeds")
        
    def setGoalScanning(self, arg  = True):
        """ set the main loop to only scan for goal """
        self.goalScanning = arg
        self.ballScanning = False
        self.featureScanning = False
        self.ledProxy.off("RightFaceLeds")
        
    def setFeatureScanning( self, arg=True, trackBall=True ):
        """ set the main loop to scan for all features """
        self.featureScanning = arg
        self.goalScanning = False
        self.ballScanning = False
        self.trackBall = trackBall

    def pause( self ):  
        """ set the main loop to not scan for everything, 
        reset every variable """
        self.featureScanning = False
        self.goalScanning = False
        self.ballScanning = False
        with self.lock:
            self.ballLoc = None
            self.goalLoc = None
            self.checkedBall = False
            self.checkedGoal = False
        
    def close(self):
        """ close thread """
        self.running = False
           
    def clearCache(self):
        """ clear variables """
        self.ballLoc = None  
        self.goalLoc = None