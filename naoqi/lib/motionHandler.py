"""
File: motionHandler.py 
Author: Auke Wiggers
Description: File contains a class that regulates passive motion behavior, e.g.
balancing, penalizing, fallmanaging, etc. Also acts as a gate to VisionHandler
and HeadMotionHandler classes. 
"""
import threading
import time
import particleFilter
import fkChain
import visionHandler 
import headMotionHandler 
import motions

from math import atan2

def debug():        
    """ debug() -> motionHandler object

    Returns a mHandler object for debugging purposes.
    
    """ 
    from naoqi import ALProxy
    memProxy = ALProxy("ALMemory",       "127.0.0.1", 9559)
    motProxy = ALProxy("ALMotion",       "127.0.0.1", 9559)
    posProxy = ALProxy("ALRobotPose",    "127.0.0.1", 9559)
    vidProxy = ALProxy("ALVideoDevice",  "127.0.0.1", 9559)
    return MotionHandler(memProxy, motProxy, posProxy,
                         vidProxy, True)

class MotionHandler(threading.Thread):
    """ 
    
    MotionHandler handles complicated (passive) tasks. 
    
    Parent class: Soul
    SubClass(es): HeadMotionHandler, ParticleFilter, KalmanFilter, Motion 
    
    """    
    def __init__(self, ledProxy, memProxy, motProxy, posProxy, 
                 vidProxy, debug=False):
        threading.Thread.__init__(self)

        self.running = True
        self.paused = False
        
        # booleans        
        self.debug       = debug
        self.fallManager = False
        self.localiser   = True
        self.balancer    = False
        
        # used objects
        self.fkClass  = fkChain.FKChain(motProxy)
        self.pitchPID = fkChain.PID(0.3, 0.015, 0.04)
        self.rollPID  = fkChain.PID(0.35, 0.015, 0.04)
        
        # 200 samples for debugging
        self.PF       = particleFilter.ParticleFilter(200) 

        self.vis = visionHandler.VisionHandler(ledProxy, memProxy, 
                                               motProxy, vidProxy)
        self.hmh = headMotionHandler.HeadMotionHandler(motProxy, self.vis)
        self.mot = motions.Motions(motProxy, posProxy)
        
        self.memProxy = memProxy
        self.motProxy = motProxy
        
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

    def __del__(self):
        self.close()
    
    def close(self):
        self.killWalk()
        self.hmh.close()
        self.running = False
        
    def pause(self):
        """ Pauses all passive tasks """
        self.killWalk()
        self.localiser = False
        self.fallManager = False
        self.balancer = False
        self.paused = True
        self.vis.KF.reset()
        
    def restart(self, position=None, restartKF=True, trackBall=True):
        """ Restarts passive tasks after a pause """
        self.localiser   = True
        self.fallManager = True
        self.balancer    = False
        self.paused      = False
        # restart headMotionHandler
        self.hmh.setFeatureScanning(trackBall)
        if restartKF:
            self.vis.KF.reset()
        if type(position) == list:
            self.PF.reset( 200 , position )
            
    """Functions for motion"""
    def stance(self):
        """ stance movement """
        self.killWalk()
        self.mot.stance() 
        
    def normalPose(self):
        """ normalPose movement """
        self.killWalk()
        self.mot.normalPose()
        
    def keepNormalPose(self):
        """ keepNormalPose movement """
        self.killWalk()
        self.mot.keepNormalPose()
    
    def sWTV(self, x, y, t, f):
        """ setWalkTargetVelocity call """
        x = max(-1, min(1, x))
        y = max(-1, min(1, y))
        t = max(-1, min(1, t))
        f = max(0,  min(1, f))
        
        vX = 0.09 * x * f
        vY = 0.05 * y * f
        vT = 0.50 * t * f
        
        self.setControl([vX, vY, vT])
        self.mot.setWalkTargetVelocity(x, y, t, f)
        
    def killWalk(self):
        """ stops walking """
        self.setControl([0, 0, 0]) 
        self.mot.killWalk()
        
    def postWalkTo(self, x, y, t):
        """ non-blocking walking behavior """
        self.PF.iterate(None, [x, y, t])
        self.vis.KF.iterate(None, [x, y, t])
        self.mot.postWalkTo(x, y, t)
    
    def walkTo(self, x, y, t):
        """ blocking walking behavior """ 
        self.PF.iterate(None, [x, y, t])
        self.vis.KF.iterate(None, [x, y, t])
        self.mot.walkTo(x, y, t)
    
    def dive(self, direction):
        """ Execute a diving/sidestepping motion """
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
        
    def kick(self, angle):
        """ Kick in a given angle, and keep balance using PID controllers """
        self.pitchPID.reset()
        self.rollPID.reset()
        
        self.pitchPID.setSP(-0.0025 * angle)
        if angle < 0:
            self.supportLeg = "R"
            self.motProxy.setAngles(["LAnkleRoll","RAnkleRoll"], 
                                        [-0.2, -0.2], 0.4)
            self.rollPID.setSP(-0.0075 + abs(angle) * -0.005)
        else:
            self.supportLeg = "L"
            self.motProxy.setAngles(["LAnkleRoll","RAnkleRoll"], 
                                        [ 0.2,  0.2], 0.4)
            self.rollPID.setSP(0.0075 + abs(angle) * 0.005)
            
        #self.balancer = True 
        self.balancer = False 
        self.mot.kick(angle)
        time.sleep(0.1)
        self.balancer = False
        time.sleep(0.1)
        self.mot.normalPose(True)
        
    """Functions for localization"""
    def setControl(self, control):
        """ set the control vector for all classes that need it """
        self.control = control
        self.vis.setControl(control)

    def getKalmanBallPos(self):
        """ get the ball position according to the KF """
        if self.vis.KF.sigma[0][0] < 0.1:
            return self.vis.KF.ballPos
        else:
            return None
    
    def getParticleFilterPos(self):
        """ get the current position of the nao """
        return self.PF.meanState
            
    def run(self):
        """Main loop, contains passive behaviors which can be switched on/off
        using setfunctions for booleans balancer, fallmanager, localiser 
        and paused """
        self.vis.start()
        self.hmh.start()
        
        timeStampBalance = time.time()
        timeStampLocalize = time.time()        
        
        while self.running:
            # get up if fallen
            # TODO implement stiffness off based on accX or accY
            if self.fallManager:
                # If falling down, kill stiffness
                threshold = 3
                torsoAngleX = self.memProxy.getData(\
                    "Device/SubDeviceList/InertialSensor/AngleX/Sensor/Value")
                torsoAngleY = self.memProxy.getData(\
                    "Device/SubDeviceList/InertialSensor/AngleY/Sensor/Value")
                if torsoAngleX + torsoAngleY > threshold:
                    # TODO execute motion that saves nao based on falldirection
                    self.mot.kill()
                # If fallen down, stand up
                if self.mot.standUp():
                    print "Fallen"
                    self.killWalk()
                    continue
            if self.balancer:  
                # update bodyAngle
                names = ["HeadYaw", "HeadPitch", "LShoulderPitch", 
                         "LShoulderRoll", "LElbowYaw", "LElbowRoll",
                         "LHipYawPitch", "LHipRoll", "LHipPitch", "LKneePitch",
                         "LAnklePitch", "LAnkleRoll", "LHipYawPitch", 
                         "RHipRoll", "RHipPitch", "RKneePitch", "RAnklePitch", 
                         "RAnkleRoll", "RShoulderPitch", "RShoulderRoll",
                         "RElbowYaw", "RElbowRoll"]
                angles = self.motProxy.getAngles("Body", True)
                
                self.bodyState = dict(zip(names, angles))                
                    
                # calculate COM
                xCom, yCom, zCom = self.fkClass.calcCOM(self.supportLeg)
                
                interval = time.time() - timeStampBalance 
                timeStampBalance = time.time()
                pitch  = self.pitchPID.iterate(xCom, interval)
                roll   = self.rollPID.iterate(yCom,  interval)

                rollName = self.supportLeg + "AnkleRoll"
                pitchName = self.supportLeg + "AnklePitch"
                newRoll =  self.bodyState[rollName]  + atan2(roll,  zCom)
                newPitch = self.bodyState[pitchName] + atan2(pitch, zCom)
                self.motProxy.setAngles([rollName, pitchName],
                                        [newRoll,  newPitch], 0.05)
                
            if self.localiser:
                interval = time.time() - timeStampLocalize
                timeStampLocalize = time.time()
                
                # get features from the world
                goalLoc = self.vis.getGoal()
                if not goalLoc:
                    goalLoc = [None]
 
                # set control vector
                control = [0,0,0]
                for i in range(3):
                    control[i] = self.control[i] * interval
                # update PF
                self.PF.iteratePlus(list(goalLoc), control)
                
                # if debugging, store info in memory
                if self.debug:
                    # use the naos ip to write to memoryProxy
                    self.memorySend()
            elif self.paused:
                # if in initial or penalized state
                print "MotionHandler pauses"
                self.hmh.pause()
                while self.mot.isWalking():
                    self.killWalk()     
                self.mot.stiff()
                self.mot.keepNormalPose()
                time.sleep(0.5)
            else:
                # note: thread should never be able to reach this
                time.sleep(0.5)
            
    def memorySend(self):
        """ memorySend() -> None
        
        Function involving writing info to memory for debugging purposes
        
        """
        particles = self.PF.samples
        toSendParticles = list()
        # debug screen is 600 x 400
        for particle in particles:
            x = int(particle[0] * 100)
            y = int(particle[1] * 100)
            t = int(particle[2] * 100)
            toSendParticles.append([x, y, t])
        meanState = self.PF.meanState
        print meanState
 
        toSendMeanState = [0, 0, 0]
        for i in range(3):
            toSendMeanState[i] = int(meanState[i] * 100)
        particles = [toSendParticles, toSendMeanState]
        self.memProxy.insertData("PF", particles)