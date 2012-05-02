""" 
File fk-chain. 
"""

from math import cos, sin, atan2
import time

""" 
Balance based on inertial unit, uses hiproll and pitch to compensate
for external disturbances
"""
def balanceGyro(supportLeg = 'R'):
    from naoqi import ALProxy
    mem = ALProxy("ALMemory", "169.254.35.27", 9559)
    mot = ALProxy("ALMotion", "169.254.35.27", 9559)

    oldAngleX = mem.getData("Device/SubDeviceList/InertialSensor/AngleX/Sensor/Value")
    oldAngleY = mem.getData("Device/SubDeviceList/InertialSensor/AngleY/Sensor/Value")

    rollName  = supportLeg + 'HipRoll'
    pitchName = supportLeg + 'HipPitch'
    oldRoll, oldPitch  = mot.getAngles([rollName, pitchName], True  )

    # factor that determines rate of exponential smoothing
    alpha = 0.9
    previous_gX = 0
    previous_gY = 0
    # set PID controllers for pitch and roll error
    rollPID = PID(0.4, 0.01, 0.04)
    pitchPID = PID( 0.4, 0.01, 0.04)
    rollPID.setSP(0)
    pitchPID.setSP(0)

    now = time.time()
    while 1:
        while time.time() - now < 0.1:
            newRoll, newPitch  = mot.getAngles([rollName, pitchName], True  )
            newAngleX = mem.getData(
                "Device/SubDeviceList/InterialSensor/AngleX/Sensor/Value")
            newAngleY = mem.getData(
                "Device/SubDeviceList/InterialSensor/AngleY/Sensor/Value")
        # a tenth of a second has passed, hopefully
        dt = time.time() - now
        now = time.time()
        refX = ( newRoll  - oldRoll  ) / dt
        refY = ( newPitch - oldPitch ) / dt

        vX = (newAngleX - oldAngleX) / dt
        vY = (newAngleY - oldAngleY) / dt
        gX = vX * alpha + previous_gX * (1-alpha)
        gY = vY * alpha + previous_gY * (1-alpha)

        errorX = gX - refX
        errorY = gY - refY
        offsetRoll = rollPID.iterate( errorX, dt )
        offsetPitch = rollPID.iterate( errorY, dt )

        mot.setAngles([rollName, pitchName], [offsetRoll, offsetPitch], 0.4)

        oldRoll = newRoll
        oldPitch = newPitch
        previous_gX = gX
        previous_gY = gY
        oldAngleX = newAngleX
        oldAngleY = newAngleY

"""PID controller with 3 factors determining output proportional, integral and
derivative term."""
class PID():
    def __init__(self, kP = 1, kI = 1, kD = 1):
        self.kP = kP
        self.kI = kI
        self.kD = kD
        self.previous_error = 0
        self.proportional = 0
        self.integral     = 0
        self.derivative   = 0
        self.desired      = 0
    
    def reset(self):
        self.previous_error = 0
        self.proportional = 0
        self.integral     = 0
        self.derivative   = 0
        
    def setSP( self, setpoint ):
        self.desired = setpoint

    def iterate(self, processvalue, dt ):
        error = self.desired - processvalue

        # Proportional part is the current error
        self.proportional = error
        # Integral part is all previous errors * the interval
        self.integral += error * dt
        # Derivative part is approximation based on this and previous error
        self.derivative = ( error - self.previous_error ) / dt
        output = self.kP * self.proportional + \
                 self.kI * self.integral + \
                 self.kD * self.derivative

        self.previous_error = error
        return output

class FKChain():
    #            name,           comX,      comY,     comZ,     mass
    jointCOM = {"RFoot"    : ( [ 0.01432, -0.00192, -0.01449], 0.30067 ),
                "RKnee"    : ( [ 0.00422, -0.00252, -0.04868], 0.29159 ),
                "RHip"     : ( [-0.00323, -0.00182, -0.04105], 0.52951 ),
                "LFoot"    : ( [ 0.01432,  0.00192, -0.01449], 0.30067 ),
                "LKnee"    : ( [ 0.00422,  0.00252, -0.04868], 0.29159 ),
                "LHip"     : ( [-0.00323,  0.00182, -0.04105], 0.52951 ),
                "Torso"    : ( [-0.00415,  0.00007,  0.04258], 1.03948 ),
                "Head"     : ( [ -0.0010, -0.00004,  0.04489], 0.66975 ),
                "RShoulder": ( [ 0.01137,  0.00537,  0.00048], 0.19305 ),
                "RElbow"   : ( [ 0.04316, -0.00025,  0.00000], 0.24471 ),
                "LShoulder": ( [ 0.01137, -0.00537,  0.00048], 0.19305 ),
                "LElbow"   : ( [ 0.04316,  0.00025,  0.00000], 0.24471 ),
                "LPelvis"  : ( [-0.00766,  0.01200,  0.02717], 0.07117 ),
                "RPelvis"  : ( [-0.00766, -0.01200,  0.02717], 0.07117 ) }
                    
    # Calculate the center of mass of the nao based on the support leg.
    jointAngles = {"RFoot"  : ["RAnkleRoll",    "RAnklePitch",    0],
            "RKnee"    : [0,               "RKneePitch",     0],
            "RHip"     : ["RHipRoll",      "RHipPitch",      0],
            "LFoot"    : ["LAnkleRoll",    "LAnklePitch",    0],
            "LKnee"    : [0,               "LKneePitch",     0],
            "LHip"     : ["LHipRoll",      "LHipPitch",      0],
            "Torso"    : [0,               0,                0],
            "Head"     : [0,               "HeadPitch",      "HeadYaw"],      
            "RShoulder": ["RShoulderRoll", "RShoulderPitch", 0 ],
            "RElbow"   : ["RElbowRoll",     0,               "RElbowYaw"],
            "LShoulder": ["LShoulderRoll", "LShoulderPitch", 0 ],
            "LElbow"   : ["LElbowRoll",     0,               "LElbowYaw"],
            "LPelvis"  : [0,                "RHipYawPitch",  "RHipYawPitch"],
            "RPelvis"  : [0,                "LHipYawPitch",  "LHipYawPitch"]
            }

    # translations based on names given for jointcombis + virtual joint 'ground'
    translation = {("Ground", "RFoot"      ) :  [0,      0,      0.04519 ],
                   ("RFoot", "RKnee"       ) :  [0,      0,      0.1029 ],
                   ("RKnee", "RFoot"       ) :  [0,      0,     -0.1029 ],
                   ("RKnee", "RHip"        ) :  [0,      0,      0.1000 ],
                   ("RHip", "RKnee"        ) :  [0,      0,     -0.1000 ],
                   ("RPelvis", "LPelvis"   ) :  [0,      0.100,  0     ],
                   ("RPelvis", "LShoulder" ) :  [0,      0.148,  0.1850 ],
                   ("RPelvis", "RShoulder" ) :  [0,     -0.048,  0.1850 ],
                   ("RPelvis", "Neck"      ) :  [0,      0.050,  0.2115 ],
                   ("RPelvis", "Torso"     ) :  [0,      0.050,  0.085  ],
                   ("RHip", "RPelvis"      ) :  [0,      0,      0     ],
                   ("RPelvis", "RHip"      ) :  [0,      0,      0     ],
                   ("Ground", "LFoot"      ) :  [0,      0,      0.04519 ],
                   ("LFoot", "LKnee"       ) :  [0,      0,      0.1029 ],
                   ("LKnee", "LFoot"       ) :  [0,      0,     -0.1029 ],
                   ("LKnee", "LHip"        ) :  [0,      0,      0.1000 ],
                   ("LHip", "LKnee"        ) :  [0,      0,     -0.1000 ],
                   ("LPelvis", "RPelvis"   ) :  [0,     -0.100,  0     ],
                   ("LPelvis", "Torso"     ) :  [0,     -0.050,  0.085    ],
                   ("LHip", "LPelvis"      ) :  [0,      0,      0     ],
                   ("LPelvis", "LShoulder" ) :  [0,      0.048,  0.1850 ],
                   ("LPelvis", "RShoulder" ) :  [0,     -0.148,  0.1850 ],
                   ("LPelvis", "Neck"      ) :  [0,     -0.050,  0.2115 ],
                   ("LPelvis", "LHip"      ) :  [0,      0,      0     ],
                   ("RShoulder", "RElbow"  ) :  [0.105, -0.015,  0     ],
                   ("LShoulder", "LElbow"  ) :  [0.105,  0.015,  0     ],
                   ("Torso", "Head"        ) :  [0,      0,      0.2115 ]
                   }

    positions6D = dict()
    weightedCOM = dict()

    def __init__(self):
        pass
    
    bodyState = {"RAnkleRoll"    :  0.0, \
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
                         0              :  0.0  }

    def setBodyState( self, bodyState ):
        self.bodyState = bodyState

    def refreshBodyState( self ):
        from naoqi import ALProxy
        mot= ALProxy('ALMotion', '169.254.35.27', 9559)
        for key in self.bodyState.keys()[1:]:
            self.bodyState[key] = mot.getAngles(key, True)[0]
      
    """function calcCOM computes the position of the center of mass based on the
    support leg and the state of the body (all angles)"""
    def calcCOM( self, sL = "both" ):
        self.refreshBodyState()
        # sL is supportLeg, either R or L or both
        if sL == "R" or sL == "L":
            oL = "L" if sL == "R" else "R"
    
            order1 = ["Ground", sL+"Foot", sL+"Knee", sL+"Hip", sL+"Pelvis"]
            order2 = [sL+"Pelvis", oL+"Pelvis", oL+"Hip", oL+"Knee", oL+"Foot"]
            order3 = [sL+"Pelvis", "RShoulder", "RElbow"]
            order4 = [sL+"Pelvis", "LShoulder", "LElbow"]
            order5 = [sL+"Pelvis", "Torso", "Head"]
    
            pos6DGround = (0.0 ,0.0 ,0.0 ,0.0 ,0.0 ,0.0 )
            pos6DSupportHip = self.transformAll( pos6DGround,     order1 )
            pos6DOtherFoot  = self.transformAll( pos6DSupportHip, order2, True )
            pos6DHead       = self.transformAll( pos6DSupportHip, order5 )
            pos6DRHand      = self.transformAll( pos6DSupportHip, order3 )
            pos6DLHand      = self.transformAll( pos6DSupportHip, order4 )
        else:
            order1 = ["Ground", "RFoot", "RKnee", "RHip", "RPelvis"]
            order2 = ["Ground", "LFoot", "LKnee", "LHip", "LPelvis"]
            order3 = ["RPelvis", "RShoulder", "RElbow"]
            order4 = ["RPelvis", "LShoulder", "LElbow"]
            order5 = ["RPelvis", "Torso", "Head"]
    
            pos6DGroundR = (0.0, -0.04, 0.0, 0.0, 0.0, 0.0 )
            pos6DGroundL = (0.0, 0.04, 0.0, 0.0, 0.0, 0.0 )
            pos6DRHip  = self.transformAll( pos6DGroundR, order1)
            pos6DLHip  = self.transformAll( pos6DGroundL, order2 )
            pos6DHead  = self.transformAll( pos6DRHip,   order5 )
            pos6DRHand = self.transformAll( pos6DRHip,   order3 )
            pos6DLHand = self.transformAll( pos6DRHip,   order4 )
    
        COM = [0,0,0]
        for _, value in self.weightedCOM.iteritems():
            for i in xrange(3):
                COM[i] += value[i]
        for i in xrange(3):
            COM[i] /= 4.879
        return COM
    
    """function transformAll takes a starting position vector (in 6d) and computes
    the resulting position given a sequence of jointnames order and a bodyState
    containing the current angles of the body"""
    def transformAll(self, pos6D, order, otherLeg = False ):
        for i in xrange(1,len(order)):
            # get jointinfo
            jointName = order[i]
            com, mass = self.jointCOM[ jointName ]
            rVector = self.jointAngles[ jointName ]
            # get translation from joint to joint
            trans = self.translation[(order[i-1], jointName )]
            # update orientation
            rot = [ self.bodyState[rVector[0]], \
                    self.bodyState[rVector[1]], \
                    self.bodyState[rVector[2]] ]
            if otherLeg :
                for i in range(3):
                    rot[i] = -rot[i]
            # perform transformation
            pos6D, comVector =  self.transform( pos6D, trans, rot, com, mass)
            self.positions6D[ jointName ] = pos6D
            self.weightedCOM[ jointName ] = comVector
            #print "Position of", jointName, pos6D[:3]
    
        return pos6D
    
    """Transforms a 6d vector based on translation/rotation"""
    def transform(self, pos6D, trans, rot, com, mass):
        x,y,z,wx,wy,wz = pos6D
        t1,t2,t3 = trans
    
        # first roll, then pitch, then yaw, then translate
        # wx = roll
        # wy = pitch
        # wz = yaw
        # homogeneous transformation matrix operation
        cx = cos(wx)
        cy = cos(wy)
        cz = cos(wz)
        sx = sin(wx)
        sy = sin(wy)
        sz = sin(wz)
    
        a = cz * cy     
        b = sz * cy     
        c = cz * sy     
    
        d = sz * cx
        e = cz * cx
        f = cz * sx
    
        g = sy * cx
        h = cy * sx
        k = cy * cx
    
        newX = a*t1 + b*t2 + c*t3 + x
        newY = d*t1 + e*t2 + f*t3 + y
        newZ = g*t1 + h*t2 + k*t3 + z
        t1 = com[0]
        t2 = com[1]
        t3 = com[2]
        comX = (a*t1 + b*t2 + c*t3 + newX) * mass
        comY = (d*t1 + e*t2 + f*t3 + newY) * mass
        comZ = (g*t1 + h*t2 + k*t3 + newZ) * mass
        wx += rot[0]
        wy += rot[1]
        wz += rot[2]
        return (newX, newY,newZ, wx,wy,wz), (comX, comY, comZ)
