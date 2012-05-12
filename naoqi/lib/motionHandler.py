# motionHandler.py 
import threading
import time
import particleFilter
import kalmanFilter
import fkChain

from math import atan2

def debug():
    import motions as m
    import headMotionHandler
        
    from naoqi import ALProxy
    mot = m.debug()
    ttsProxy = ALProxy("ALTextToSpeech", "127.0.0.1", 9559)
    memProxy = ALProxy("ALMemory",       "127.0.0.1", 9559)
    motProxy = ALProxy("ALMotion",       "127.0.0.1", 9559)
    ledProxy = ALProxy("ALLeds",         "127.0.0.1", 9559)
    sensors  = ALProxy("ALSensors",      "127.0.0.1", 9559)
    vidProxy = ALProxy("ALVideoDevice",  "127.0.0.1", 9559)
    hmh = headMotionHandler.HeadMotionHandler( ledProxy, memProxy,
            motProxy, vidProxy )
    mot = m.debug()
    return MotionHandler( mot, hmh, ledProxy, motProxy, memProxy, sensors,
                         ttsProxy, vidProxy, True )

class MotionHandler(threading.Thread):
    """ 
    
    MotionHandler handles complicated tasks, manages PF and KF as well. 
    
    Parent class: Soul
    SubClass(es): HeadMotionHandler, ParticleFilter, KalmanFilter, Motion 
    
    """
    # Control vector [forward, horizontal, rotational speed].
    control = [0,0,0]
    # seen fieldfeatures (bearing, range, signature)
    features = []
    # seen ball-locations (x,y).
    ballLoc = None
    lock = threading.Lock()
    
    def __init__( self, motionObject, hmh, ledProxy, motProxy, memProxy, 
                 sensors, ttsProxy, vidProxy, debug=True ):
        threading.Thread.__init__(self)

        self.running = True
        self.paused = False
        
        # booleans        
        self.debug  = debug
        self.fallManager = False
        self.localize    = True
        self.balancer    = False
        
        # used objects
        self.fkClass  = fkChain.FKChain( motProxy )
        self.pitchPID = fkChain.PID(0.35, 0.015, 0.04)
        self.rollPID  = fkChain.PID(0.35, 0.015, 0.04)
        
        # 200 samples for debugging
        self.PF       = particleFilter.ParticleFilter( 200 ) 

        # objects gotten from superclasses
        self.mot = motionObject
        self.hmh = hmh
        self.memProxy = memProxy
        
        # other        
        self.bodyState = {"RAnkleRoll"  :  0.0, \
                        "RAnklePitch"   :  0.0, \
                        "RKneePitch"    :  0.0, \
                        "RHipRoll"      :  0.0, \
                        "RHipPitch"     :  0.0, \
                        "RHipYawPitch"  :  0.0, \
                        "LAnkleRoll"    :  0.0, \
                        "LAnklePitch"   :  0.0, \
                        "LKneePitch"    :  0.0, \
                        "LHipPitch"     :  0.0, \
                        "LHipRoll"      :  0.0, \
                        "LHipYawPitch"  :  0.0, \
                        "RShoulderRoll" :  0.0, \
                        "RShoulderPitch":  0.0, \
                        "RElbowRoll"    :  0.0, \
                        "RElbowYaw"     :  0.0, \
                        "LShoulderRoll" :  0.0, \
                        "LShoulderPitch":  0.0, \
                        "LElbowRoll"    :  0.0, \
                        "LElbowYaw"     :  0.0, \
                        "HeadPitch"     :  0.0, \
                        "HeadYaw"       :  0.0, \
                         0              :  0.0   }

    def __del__( self ):
        self.close()
    
    def close( self ):
        self.killWalk()
        self.hmh.close()
        self.running = False
        print "motionHandler closed safely"
        
    def pause( self ):
        self.localize = False
        self.fallManager = False
        self.balancer = False
        self.paused = True
        self.hmh.vision.KF.reset()
        
    def restart( self ):
        self.localize = True
        self.fallManager = True
        self.balancer = False
        self.paused = False
        trackBall = True
        self.hmh.setFeatureScanning( trackBall )
        self.hmh.vision.KF.reset()
            
    """Functions for motion"""
    def sWTV( self, x, y, t, f ):
        x = max(-1, min( 1, x ))
        y = max(-1, min( 1, y ))
        t = max(-1, min( 1, t ))
        f = max(0,  min( 1, f ))
        
        vX = 0.09 * x * f
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
        self.hmh.vision.KF.iterate( None, [x,y,t] )
    
    def walkTo( self, x, y, t ):
        self.PF.iterate( None, [x,y,t] )
        self.hmh.vision.KF.iterate( None, [x,y,t] )
        self.mot.walkTo( x, y, t )
    
    def dive( self, direction ):
        self.fallManager = False
        if direction >= 0.5:
            self.mot.diveRight()
        elif direction <= -0.5:
            self.mot.diveLeft()
        elif 0.5 > direction >= 0:
            self.mot.footRight()
        elif -0.5 < direction < 0:
            self.mot.footLeft()
        self.fallManager = True
        
    def kick( self, angle ):
        self.pitchPID.reset()
        self.rollPID.reset()
        
        self.pitchPID.setSP( -0.005 * angle )
        if angle < 0:
            self.supportLeg = "R"
            self.mot.motProxy.setAngles(["LAnkleRoll","RAnkleRoll"], 
                                        [-0.2, -0.2], 0.4)
            self.rollPID.setSP( -0.01 + abs(angle) * -0.005 )
        else:
            self.supportLeg = "L"
            self.mot.motProxy.setAngles(["LAnkleRoll","RAnkleRoll"], 
                                        [ 0.2,  0.2], 0.4)
            self.rollPID.setSP( 0.01 + abs(angle ) * 0.005 )
            
        self.balancer = True 
        self.mot.kick( angle )
        time.sleep(0.1)
        self.balancer = False
        time.sleep(0.1)
        self.mot.normalPose(True)
        
    """Functions for localization"""
    def setControl( self, control ):
        self.control = control
        self.hmh.vision.setControl( control )

    def getKalmanBallPos( self ):
        if self.hmh.vision.KF.sigma[0][0] < 0.1:
            return self.hmh.vision.KF.ballPos
        else:
            return None
    
    def getParticleFilterPos( self ):
        return self.PF.meanState
            
    """Main loop"""
    def run( self ):
        timeStampBalance = time.time()
        timeStampLocalize = time.time()        
        
        while self.running:
            # get up if fallen
            # TODO implement stiffness off based on accX or accY
            if self.fallManager:
                # If falling down, kill stiffness
                threshold = 3
                torsoAngleX = self.memProxy.getData("Device/SubDeviceList/InertialSensor/AngleX/Sensor/Value")
                torsoAngleY = self.memProxy.getData("Device/SubDeviceList/InertialSensor/AngleY/Sensor/Value")
                if torsoAngleX + torsoAngleY > threshold:
                    # TODO execute motion that saves nao based on falldirection
                    mot.kill()
                # If fallen down, stand up
                if self.mot.standUp():
                    print "Fallen"
                    self.killWalk()
                    continue
            if self.balancer:  
                # update bodyAngle
                names = ["HeadYaw", "HeadPitch",\
                         "LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", \
                         "LHipYawPitch", "LHipRoll", "LHipPitch", "LKneePitch", "LAnklePitch", "LAnkleRoll", \
                         "LHipYawPitch", "RHipRoll", "RHipPitch", "RKneePitch", "RAnklePitch", "RAnkleRoll", \
                         "RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll"]
                angles = self.mot.motProxy.getAngles( "Body", True )
                
                self.bodyState = dict( zip(names, angles) )                
                    
                # calculate COM
                xCom,yCom,zCom = self.fkClass.calcCOM( self.supportLeg )
                
                interval = time.time() - timeStampBalance 
                timeStampBalance = time.time()
                pitch  = self.pitchPID.iterate( xCom, interval )
                roll   = self.rollPID.iterate( yCom,  interval )

                rollName = self.supportLeg + "AnkleRoll"
                pitchName = self.supportLeg + "AnklePitch"
                newRoll =  self.bodyState[rollName]  + atan2(roll,  zCom)
                newPitch = self.bodyState[pitchName] + atan2(pitch, zCom)
                self.mot.motProxy.setAngles([rollName, pitchName ], \
                                            [ newRoll, newPitch    ], 0.05)                        
                
            if self.localize:
                
                interval = time.time() - timeStampLocalize
                timeStampLocalize = time.time()
                
                # get features from the world
                goalLoc = self.hmh.vision.getGoal()
                if not goalLoc:
                    goalLoc = [None]
 
                # set control vector
                control = [0,0,0]
                for i in range(3):
                    control[i] = self.control[i] * interval
                # update PF
                self.PF.iteratePlus( list(goalLoc), control )
                
                # if debugging, store info in memory
                if self.debug:
                    # use the naos ip to write to memoryProxy
                    self.memorySend()
            elif self.paused:
                # if in penalized state
                print "MotionHandler pauses"
                while self.mot.isWalking():
                    self.killWalk()                        
                self.hmh.pause()
                self.mot.keepNormalPose()
                print "killed all"
                self.control = [0, 0, 0]
                time.sleep(0.5)
            else:
                # note: thread should never be able to reach here
                time.sleep(0.5)
            
    def memorySend( self ):
        """ memorySend() -> None
        
        Function involving writing info to memory
        
        
        """
        particles = self.PF.samples
        toSendParticles = list()
        # debug screen is 600 x 400
        for particle in particles:
            x = int( particle[0] * 100 )
            y = int( particle[1] * 100 )
            t = int( particle[2] * 100 )
            toSendParticles.append( [x,y,t] )
        meanState = self.PF.meanState
        print meanState
 
        toSendMeanState = [0,0,0]
        for i in range(3):
            toSendMeanState[i] = int(meanState[i] * 100)
        # store by pickling
        particles = [toSendParticles, toSendMeanState]
        self.memProxy.insertData( "PF", particles )
