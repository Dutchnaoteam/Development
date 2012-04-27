# motionHandler.py 
import threading
import time
import math
import particleFilter
import kalmanFilter
from socket import *
import cPickle as pickle


def debug():
    import motions as m
    import gameStateController
    from naoqi import ALProxy
    mot = m.debug()
    ttsProxy = ALProxy('ALTextToSpeech', '127.0.0.1', 9559)
    memProxy = ALProxy('ALMemory', '127.0.0.1', 9559)
    ledProxy = ALProxy('ALLeds', '127.0.0.1', 9559)
    sensors  = ALProxy('ALSensors', '127.0.0.1', 9559)
    gsc = gameStateController.StateController('stateController', ttsProxy, memProxy, ledProxy, sensors )
    mot = None
    
    debugBool = True
    debugIP = '127.0.0.1'
    return MotionHandler( (debugBool, debugIP), mot, gsc, memProxy )

class MotionHandler(threading.Thread):
    # Control vector [forward, horizontal, rotational speed].
    control = [0,0,0]
    # seen fieldfeatures (bearing, range, signature)
    features = []
    # seen ball-locations (x,y).
    ballLoc = None
    lock = threading.Lock()
    
    def __init__(self, (debugBool, debugIP), motionObject, gameStateController, memProxy ):
        threading.Thread.__init__(self)
        self.debug = debugBool
        
        self.running = True
        self.PF = particleFilter.ParticleFilter( 200 ) # 200 samples for debugging
        self.KF = kalmanFilter.KalmanFilter( ) 
        self.mot = motionObject
        self.gsc = gameStateController
        self.memProxy = memProxy

        if debugBool:
            host = debugIP
            port = 4242
            addr = (host,port)
            self.server = socket( AF_INET, SOCK_STREAM )
            self.server.connect(addr)
        
    def __del__(self):
        self.close()
    
    def close(self):
        try:
            self.server.send('STOP')
        except:
            pass
        self.running = False
        print 'motionHandler closed safely'
    
    """Functions for motion"""
    def sWTV( self, x, y, t, f ):
        x = max(-1, min( 1, x ))
        y = max(-1, min( 1, y ))
        t = max(-1, min( 1, t ))
        f = max(0,  min( 1, f ))
        
        vX = 0.07 * x * f
        vY = 0.05 * y * f
        vT = 0.50 * t * f
        
        self.setControl( [vX, vY, vT] )
        self.mot.setWalkTargetVelocity( x, y, t, f )
        
    def killWalk( self ):
        self.setControl( [0,0,0] ) 
        self.mot.killWalk()
        
    def postWalkTo( self, x, y, t ):
        self.mot.postWalkTo( x, y, t )
        self.PF.iterate( None, [x,y,t] )
        self.KF.iterate( None, [x,y,t] )
    
    def walkTo( self, x, y, t ):
        self.PF.iterate( None, [x,y,t] )
        self.KF.iterate( None, [x,y,t] )
        self.mot.walkTo( x, y, t )
    
    """Functions for localization"""
    def setControl( self, control ):
        self.control = control
            
    # note: problem with this is that the cycles might not be aligned, causing delayed use of a feature
    def setFeatures( self, measurements ):
        with self.lock:
            self.features = measurements
	print 'Use once', measurements
            
    def getFeatures(self):
        with self.lock:
            m = self.features
            self.features = []
        return m
    
    def setBallLoc( self,measurement ):
        with self.lock:
            self.ballLoc = measurement

    def getBallLoc(self ):
	with self.lock:
	    m = self.ballLoc
	    self.ballLoc = None
	return m
    
    def getKalmanBallPos( self ):
        return self.kalmanBallPos
	
    """Main loop"""
    def run(self):
        timeStamp = time.time()
        while self.running:
            # pause, but if there is a feature available, use it immediately
            now = time.time()
            while time.time() - now < 0.5:
                if self.gsc.getState() == 10:
                    print 'Penalized by motionHandler!!!\n'
                    while self.mot.isWalking():
                        self.killWalk()
                    time.sleep(0.5)
                    self.mot.keepNormalPose()
                    self.mot.motProxy.killTasksUsingResources(['HeadYaw', 'HeadPitch'])
                    time.sleep(0.1)
                    self.mot.setHead(0, 0)
                    print 'killed all'
                    while self.gsc.getState() == 10:
                        time.sleep(0.1)
                else:
                    time.sleep(0.025)
                    if self.features or self.ballLoc:
                        break
            
            interval = time.time() - timeStamp
            timeStamp = time.time()
                    
            measurements = self.getFeatures()
            ballLoc = self.getBallLoc()
            control = [0,0,0]
            for i in range(3):
                control[i] = self.control[i] * interval
            self.PF.iteratePlus( measurements, control )
            self.KF.iterate( ballLoc, control )
            self.kalmanBallPos = self.KF.ballPos
            
            if self.debug:
                # use the naos ip to write to memory(Proxy)
                self.memorySend()
		# second option: self.serverSend(), which uses socket programming

    """Function involving writing info to memory"""
    def memorySend( self ):
        particles = self.PF.samples
        toSendParticles = list()
        # debug screen is 600 x 400
        for particle in particles:
            x = int( particle[0] * 100 )
            y = int( particle[1] * 100 )
            t = int( particle[2] * 100 )
            toSendParticles.append( [x,y,t] )
        meanState = self.PF.meanState
        
        toSendMeanState = [0,0,0]
        for i in range(3):
            toSendMeanState[i] = int(meanState[i] * 100)
        # store by pickling
        particles = pickle.dumps( {'PF': toSendParticles, 'NAO':toSendMeanState} )
        
        self.memProxy.insertData( 'PF', particles )
	
    """Functions involving socket programming"""
    def socketSend( self ):
        # receive go message from debugging server
        self.server.recv( 128 )
            # prepare data for sending
        particles = self.PF.samples 
        
        toSendParticles = list()
        # debug screen is 600 x 400
        for particle in particles:
            x = int(particle[0] * 100)
            y = int(particle[1] * 100)
            t = int(particle[2] * 100)
            toSendParticles.append( [x,y,t] )
        meanState = self.PF.meanState
        
        toSendMeanState = [0,0,0]
        for i in range(3):
            toSendMeanState[i] = int(meanState[i] * 100)
        # store by pickling
        particles = pickle.dumps( {'PF': toSendParticles, 'NAO':toSendMeanState} ).encode("UTF-8")
        try:
            self.server.send( particles )
            #print 'Sent' 
        except:
            print 'Server closed (probably)'
            self.server.close()