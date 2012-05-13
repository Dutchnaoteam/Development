from naoqi import ALProxy
import sys
import time
import threading
import math
from socket import *

# create brokers for nao
motion = ALProxy("ALMotion", "127.0.0.1", 9559)
pose = ALProxy("ALRobotPose", "127.0.0.1", 9559)

# enable custom arm movements during walk
motion.setWalkArmsEnable(False, False)

class Receiver(threading.Thread):
    """
    Connects to every client specified by a number of connections
    Receives data from every client (serial, not parallel)

    """
    def __init__(self, connections, ADDR = ("", 4242)):        
        """Constructor for class Receiver
        
        Arguments:
        name        -- name of the thread
        connections -- number of connections
        """
        threading.Thread.__init__(self)
        self.connections = connections        # number of connections that is to be started
        self.conn        = list()             # reset list to prevent pipe errors
        self.data          = ""
        self.extractedData = None 
        
        # set up the server
        self.serv = socket( AF_INET, SOCK_STREAM )
        self.serv.bind(ADDR)
        self.serv.listen(2)    
    
    def __del__(self):
        """Destructor for class Receiver"""
        self.running = False         
        self.extractData = "STOP"

    def run(self):    
        '''Main program loop of class Receiver
        
        Initiates by connecting to every client, sends start message.
        Enters loop which asks for data from clients to be extracted by main program.
        
        '''
        self.running = True
        print 'Accepting', self.connections, 'connection(s).'
        for i in range(self.connections):
            connect,addr = self.serv.accept() 
            print 'Connection ', i+1, 'made.'
            self.conn.append(connect)

        # send a starting message to all clients
        for c in self.conn:
            c.send('GO')    # start sending data
            
        # workaround for breaking out of the while loop when an exception is found
        doBreak = False
        
        # while receiving, get up to 4096 bytes of data from each connection
        while self.running and not doBreak:
            self.data = ""
            for c in self.conn:
                try:
                    self.data += c.recv(4096)
                    c.send('GO')
                except Exception as inst:
                    print 'Unable to receive data from client:', inst
                    doBreak = True

            # update the new data if receiving any
            if self.data:
                self.extractedData = self.data.split()
           
        # if client disconnects, stop extracting data
        print 'Extracting of data stopped'
        self.extractedData = 'STOP'
        for c in self.conn:
            c.recv(4096)
            try:
                c.send('STOP')      # send stop message to remaining clients
            except:
                pass
        self.serv.close()           # close socket
                    
    def getData(self):
        '''Return data as specified in run() in parsed form '''
        return self.extractedData
        
    def stopRec(self):
        '''Stops main program loop'''
        self.running = False

# global variable to see if Nao is standing or stancing 
stancing = False

def stanceOrStand( arg ):
    global stancing
    if arg == 1 and not stancing:
        stance()
        stancing = True
    elif arg == 0 and stancing:
        normalPose()
        stancing = False
        
def startMimic(connections = 1, interval = 99999):
    '''Start mimicking of user
    
    Arguments:
    connections -- number of clients to receive data from
    interval    -- number of seconds to listen to client
    '''
    
    # initial pose
    motion.setStiffnesses('Body', 0.95)
    motion.setStiffnesses('Head', 0.6)
    time.sleep(0.2)
    normalPose()
    time.sleep(0.2)
    motion.setAngles(['RShoulderPitch', 'RShoulderRoll',  'RElbowRoll', 
                      'RElbowYaw',      'LShoulderPitch', 'LShoulderRoll', 
                      'LElbowRoll', 'LElbowYaw'], \
                     [1, 0, 0, 0, 1, 0, 0, 0], 0.2)
    
    # start an arbitrary number of connections by a thread 
    if connections > 0 and type(connections) == int:
        rec = Receiver(connections)
        rec.start()        
        # wait for data to be sent
        while not(rec.getData()):
            time.sleep(0.5)
            print 'No data yet..'
            pass
        print 'Mimicking'
                
        # start interval in which mimicking occurs
        now = time.time()
        while time.time() - now < interval:
            walk = 0
    
            # if Nao has fallen:
            currentPose = pose.getActualPoseAndTime()[0]
            # get up according to pose
            if currentPose == 'Back':
                motion.setStiffnesses('Body', 0.95)
                motion.setStiffnesses('Head', 0.75)
                backToStand()
            elif currentPose == 'Belly':
                motion.setStiffnesses('Body', 0.95)
                motion.setStiffnesses('Head', 0.75)
                bellyToStand()
            else:
                # if not fallen, mimic
                data = rec.getData() 
                if data[0] == 'STOP':
                    break                
                data = data[0:28]
                
                names = list()
                keys = list()
                
                walk = 0
                
                # loop over the data                                    
                for i in xrange(0, len(data), 2):
                    name = data[i]
                    try:
                        key = float(data[i+1])
                    except:
                        continue
                        
                    # if name indicates a button state    
                    if name in buttons:
                        argument = arguments[name]
                        if key and not walk:
                            function = buttons[name]
                            function( argument )

                            # if wiimote arrowbutton
                            if name == 'Up' or name == 'Down' or name == 'Left' or name == 'Right':
                                walk += key
                                function( arguments[name] )
                            
                    # if data indicates existing jointname and not a duplicate                        
                    elif not(name in names) and name in ranges:
                        (minRange, maxRange) = ranges[name]
                        # and in range
                        if minRange < key < maxRange:
                            names.append(name)
                            keys.append(key)
                            
                # if jointnames and values are found, execute motion
                if len(names) > 0:
                    motion.setAngles(names, keys, 0.5)                
                    '''
                    # check to see if walking, walk in direction of headyaw
                    if "RShoulderPitch" in walkArm and "RShoulderRoll" in walkArm and "RElbowRoll" in walkArm and "RElbowYaw" in walkArm: 
                        if 0.3 > walkArm['RShoulderPitch'] > -0.3 and 0.3 > walkArm['RShoulderRoll'] > -0.3 and 0.3 > walkArm['RElbowRoll'] and 0.3 > walkArm['RElbowYaw'] > -0.3:
                            [direction] = motion.getAngles('HeadYaw', True)
                            y = max(-1, min(1, 0.5 * math.tan(direction)))
                            motion.setWalkTargetVelocity(0.5,  y, direction/6.0, 0.5)
                        else:
                            if motion.walkIsActive():
                                motion.post.setWalkTargetVelocity(0, 0, 0, 0)
                    '''                
                if walk == 0:
                    motion.setWalkTargetVelocity(0, 0, 0, 0)
        rec.stopRec()
        print 'Mimicking stopped.'
        
    else:
        print 'Number of connections invalid, must be > 0.'
        return False
    
'''
Motions

normalPose -- nao stands straight
stance     -- nao bends knees to crouch
walk       -- walk in specified direction
'''

def walk(arg):
    '''Walk in specified direction
    Arguments
    x -- forward
    y -- sideways
    t -- angle to turn to the left
    f -- stepfrequency
    '''
    (x,y,t,f) = arg
    motion.setWalkTargetVelocity(x,y,t,f)
    
def normalPose(arg=0):
    '''Stand in a normal pose (up straight)'''
    
    names = list()
    times = list()
    angles = list()
     
    names.append('HeadPitch')
    times.append([1])
    angles.append([ [ -0.5 , [ 3, -1.00000, 0.00000], [ 3, 0.00000, 0.00000]]])        
        
    names.append('HeadYaw')
    times.append([1])
    angles.append([ [ 0.0, [ 3, -1.00000, 0.00000], [ 3, 0.00000, 0.00000]]])
    
  
    names.append('LHipYawPitch')
    times.append([1])
    angles.append([ [ 0, [ 3, -1.00000, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LHipRoll')
    times.append([1])
    angles.append([ [ 0, [ 3, -1.00000, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LHipPitch')
    times.append([1])
    angles.append([ [ -0.4, [ 3, -1.00000, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LKneePitch')
    times.append([1])
    angles.append([ [ 0.95, [ 3, -1.00000, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LAnklePitch')
    times.append([1])
    angles.append([ [ -0.55, [ 3, -1.00000, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LAnkleRoll')
    times.append([1])
    angles.append([ [ 0.0, [ 3, -1.00000, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RHipRoll')
    times.append([1])
    angles.append([ [ 0.0, [ 3, -1.00000, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RHipPitch')
    times.append([1])
    angles.append([ [ -0.4, [ 3, -1.00000, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RKneePitch')
    times.append([1])
    angles.append([ [ 0.95, [ 3, -1.00000, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RAnklePitch')
    times.append([1])
    angles.append([ [ -0.55, [ 3, -1.00000, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RAnkleRoll')
    times.append([1])
    angles.append([ [ 0.0, [ 3, -1.00000, 0.00000], [ 3, 0.00000, 0.00000]]])

    motion.post.angleInterpolationBezier(names, times, angles)    
            

# Stand up from the back
def backToStand():
    # lie down on back, move arms towards pushing position and legs upwards
    motion.setAngles(['HeadPitch', 'HeadYaw'], [-0.4, 0.0], 0.4)
    motion.post.angleInterpolation(['LShoulderPitch', 'LShoulderRoll' ,'LElbowRoll', 'LElbowYaw'],
                              [[-0.1, 0.8],       [1, 0.5] ,      [ -1.5],        [1.9]       ],\
                              [[0.4, 0.8],        [0.5, 0.8],     [0.5],          [0.5]],  True)                
    motion.post.angleInterpolation(['RShoulderPitch', 'RShoulderRoll', 'RElbowRoll', 'RElbowYaw'],
                              [[0, 0.8],          [-1.0, -0.5],   [1.5],          [-1.9]],
                              [[0.5, 0.8],        [0.5, 0.8],     [0.5],          [0.5]],  True)
                            
    motion.setAngles(['LHipYawPitch', 'RKneePitch', 'LKneePitch', 'RHipRoll', 'LHipRoll', 'RAnkleRoll', 'LAnkleRoll'],
                [0             ,  0           , 0          ,  0        ,  0        ,  0          ,  0          ],  0.3)
    motion.setAngles( ['LHipPitch', 'LAnklePitch', 'RHipPitch', 'RAnklePitch'],
                 [-1.5       , 0.8          , -1.5,       0.8], 0.3 )
    time.sleep(0.9)

    # move legs down, arms down to push
    motion.setAngles(['LShoulderPitch','RShoulderPitch','RHipPitch', 'LHipPitch'],
                [2               , 2              , -0.7        ,  -0.7        ],  0.9)
    time.sleep(0.1)
    # reset legs
    motion.setAngles(['RHipPitch', 'LHipPitch'], [ -1.5, -1.5 ],  0.3 )
    time.sleep(0.2)
    # push up with arms
    motion.setAngles(['RShoulderRoll', 'LShoulderRoll'], [-0.25, 0.25], 0.5 )
    motion.setAngles(['LElbowRoll', 'RElbowRoll'], [0,0], 0.5)
    
    time.sleep(0.3)
    
    # twist legs around to sit with legs wide
    t = 0.4
    names = list()
    angles = list()
    times = list()
        
    names.extend(['RShoulderPitch', 'RShoulderRoll', 'RElbowYaw', 'RElbowRoll'])
    angles.extend([[2],           [-0.3],            [0.7] ,     [0.06]])
    times.extend([[t],              [t],              [t],         [t]])
    
    names.extend(['LShoulderPitch', 'LShoulderRoll', 'LElbowYaw', 'LElbowRoll'])
    angles.extend([[2],           [0.3],           [-0.7] ,     [-0.05]])
    times.extend([[t],              [t],             [t],         [t]])
    
    names.extend(['LHipYawPitch', 'RHipRoll', 'RHipPitch', 'RKneePitch', 'RAnklePitch', 'RAnkleRoll'])
    angles.extend([[-0.7],       [-0.23],    [-1.57],      [0.8],       [0.85],        [0.06]])
    times.extend([[t],            [t],        [t],         [t],          [t],           [t]])
    
    names.extend(['LHipRoll', 'LHipPitch', 'LKneePitch', 'LAnklePitch', 'LAnkleRoll'])
    angles.extend([[0.23],    [-1.57],      [0.8],       [0.85],        [-0.06]])
    times.extend([[t],        [t],         [t],          [t],           [t]])    
    motion.angleInterpolation(names, angles, times, True)
    
    # move one arm backwards, one arm upwards, move legs towards body
    motion.setAngles(['HeadPitch', 'HeadYaw'], [0.5, 0.0], 0.4)
    t = 0.4
    names = list()
    angles = list()
    times = list()
        
    names.extend(['RShoulderPitch', 'RShoulderRoll', 'RElbowYaw', 'RElbowRoll'])
    angles.extend([[2.085], [-0.3], [0.6764], [0.055]])
    times.extend([[t],              [t],              [t],         [t]])
    
    names.extend(['LShoulderPitch', 'LShoulderRoll', 'LElbowYaw', 'LElbowRoll'])
    angles.extend([[0.56],          [0.52],          [-0.33],     [-.55]])
    times.extend([[t],              [t],             [t],         [t]])
    
    names.extend(['LHipYawPitch', 'RHipRoll', 'RHipPitch', 'RKneePitch', 'RAnklePitch', 'RAnkleRoll'])
    angles.extend([[-0.89],       [-0.57],   [-1.31],      [0.73],       [0.93],        [0.07]])
    times.extend([[t],            [t],        [t],         [t],          [t],           [t]])
    
    names.extend(['LHipRoll', 'LHipPitch', 'LKneePitch', 'LAnklePitch', 'LAnkleRoll'])
    angles.extend([[0.54],      [-1.05],    [2.11],       [-0.13],       [-0.25]])
    times.extend([[t],        [t],         [t],          [t],           [t]])
    motion.angleInterpolation(names, angles, times, True)
    
    # move legs further towards body
    t = 0.6
    names = list()
    angles = list()
    times = list()
    
    names.extend(['LHipYawPitch', 'RHipRoll', 'RHipPitch', 'RKneePitch', 'RAnklePitch', 'RAnkleRoll'])
    angles.extend([[-1.07],      [-0.656],   [-1.67],      [1.63 ],       [0.32],       [-0.004]])
    times.extend([[t],            [t],        [t],         [t],          [t],           [t]])
    
    names.extend(['LHipRoll', 'LHipPitch', 'LKneePitch', 'LAnklePitch', 'LAnkleRoll'])
    angles.extend([[-0.01], [-0.01],     [2.11254]    , [-1] , [0.10128598]])
    times.extend([[t],        [t],         [t],          [t],           [t]])
    motion.angleInterpolation(names, angles, times, True)

    # Lift arm from ground, move right leg towards body
    t = 0.3
    names = list()
    angles = list()
    times = list()
        
    names.extend(['RShoulderPitch', 'RShoulderRoll', 'RElbowYaw', 'RElbowRoll'])
    angles.extend([[1.86205],      [-0.5913],       [0.61815],   [0.0598679]])
    times.extend([[t],              [t],              [t],         [t]])
    
    names.extend(['LShoulderPitch', 'LShoulderRoll', 'LElbowYaw', 'LElbowRoll'])
    angles.extend([[0.98],          [0.531],         [-0.03],     [-0.57]])
    times.extend([[t],              [t],             [t],         [t]])
    
    names.extend(['RHipRoll', 'RHipPitch', 'RKneePitch', 'RAnklePitch', 'RAnkleRoll'])
    angles.extend([[-0.73],    [-1.47],     [2],         [-0.13],      [0.15]])
    times.extend([[t],            [t],        [t],         [t],          [t]])
    
    names.extend(['LAnklePitch'])
    angles.extend([[-1.18]])
    times.extend([[t]])
    
    motion.angleInterpolation(names, angles, times, True)
    
    # lift right leg further towards left
    t = 0.4
    names = list()
    angles = list()
    times = list()
    
    names.extend(['LHipYawPitch', 'RHipRoll', 'RHipPitch', 'RKneePitch', 'RAnklePitch', 'RAnkleRoll'])
    angles.extend([[-0.5],      [-0.2],   [-0.55],      [2.11 ],       [-1.18],       [0.07]])
    times.extend([[t],            [t],        [t],         [t],          [t],           [t]])
    
    names.extend(['LHipRoll', 'LHipPitch', 'LKneePitch', 'LAnklePitch', 'LAnkleRoll'])
    angles.extend([[0.2],    [-0.55],     [2.11],       [-1.18] ,  [-0.07 ]])
    times.extend([[t],        [t],         [t],          [t],           [t]])
    motion.angleInterpolation(names, angles, times, True)
    
    # move legs closer to eachother (stance)
    t = 0.2
    names = list()
    angles = list()
    times = list()
    
    names.extend(['LHipYawPitch', 'RHipRoll', 'RHipPitch', 'RKneePitch', 'RAnklePitch', 'RAnkleRoll'])
    angles.extend([[0],           [0],        [-0.9],      [2.11 ],       [-1.18],       [0.0]])
    times.extend([[t],            [t],        [t],         [t],          [t],           [t]])
    
    names.extend(['LHipRoll', 'LHipPitch', 'LKneePitch', 'LAnklePitch', 'LAnkleRoll'])
    angles.extend([[0],        [-0.9],      [2.11 ],       [-1.18],       [0.0]])
    times.extend([[t],        [t],         [t],          [t],           [t]])
    motion.angleInterpolation(names, angles, times, True)        
    
    normalPose(True)

def bellyToStand():
    '''Stand up from belly'''
    names = list()
    times = list()
    angles = list()
    
    names.append('HeadYaw')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ 0.17453, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ -0.22689, [ 3, -0.33333, 0.00000], [ 3, 0.46667, 0.00000]], [ 0.28623, [ 3, -0.46667, -0.01333], [ 3, 0.36667, 0.01047]], [ 0.29671, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ -0.49567, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ -0.29671, [ 3, -0.23333, -0.07104], [ 3, 0.36667, 0.11164]], [ 0.05236, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ -0.39095, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.0, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('HeadPitch')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ -0.57683, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ -0.54768, [ 3, -0.33333, -0.02915], [ 3, 0.46667, 0.04081]], [ 0.10734, [ 3, -0.46667, -0.19834], [ 3, 0.36667, 0.15584]], [ 0.51487, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ 0.38048, [ 3, -0.43333, 0.01726], [ 3, 0.23333, -0.00930]], [ 0.37119, [ 3, -0.23333, 0.00930], [ 3, 0.36667, -0.01461]], [ -0.10472, [ 3, -0.36667, 0.13827], [ 3, 0.43333, -0.16341]], [ -0.53387, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ -0.5, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LShoulderPitch')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ 0.08433, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ -1.51146, [ 3, -0.33333, 0.00000], [ 3, 0.46667, 0.00000]], [ -1.25025, [ 3, -0.46667, -0.26120], [ 3, 0.36667, 0.20523]], [ 0.07206, [ 3, -0.36667, -0.38566], [ 3, 0.43333, 0.45578]], [ 1.27409, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ 0.75573, [ 3, -0.23333, 0.00333], [ 3, 0.36667, -0.00524]], [ 0.75049, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ 1.29154, [ 3, -0.43333, -0.15226], [ 3, 0.36667, 0.12884]], [ 1.2, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LShoulderRoll')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ 1.55390, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ 0.01683, [ 3, -0.33333, 0.00000], [ 3, 0.46667, 0.00000]], [ 0.07666, [ 3, -0.46667, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.07052, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ 0.15643, [ 3, -0.43333, -0.08590], [ 3, 0.23333, 0.04626]], [ 0.93899, [ 3, -0.23333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.67719, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ 0.84648, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.2, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LElbowYaw')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ -2.07694, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ -1.58006, [ 3, -0.33333, 0.00000], [ 3, 0.46667, 0.00000]], [ -1.60461, [ 3, -0.46667, 0.02454], [ 3, 0.36667, -0.01928]], [ -1.78715, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ -1.32695, [ 3, -0.43333, -0.11683], [ 3, 0.23333, 0.06291]], [ -1.24791, [ 3, -0.23333, -0.04593], [ 3, 0.36667, 0.07218]], [ -0.97260, [ 3, -0.36667, -0.01072], [ 3, 0.43333, 0.01267]], [ -0.95993, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LElbowRoll')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ -0.00873, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ -0.35278, [ 3, -0.33333, 0.08741], [ 3, 0.46667, -0.12238]], [ -0.63810, [ 3, -0.46667, 0.09306], [ 3, 0.36667, -0.07312]], [ -0.85133, [ 3, -0.36667, 0.13944], [ 3, 0.43333, -0.16480]], [ -1.55083, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ -0.73304, [ 3, -0.23333, 0.00000], [ 3, 0.36667, 0.00000]], [ -0.73653, [ 3, -0.36667, 0.00349], [ 3, 0.43333, -0.00413]], [ -1.15506, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RShoulderPitch')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ -0.02757, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ -1.51146, [ 3, -0.33333, 0.00000], [ 3, 0.46667, 0.00000]], [ -1.22256, [ 3, -0.46667, -0.23805], [ 3, 0.36667, 0.18704]], [ -0.23619, [ 3, -0.36667, -0.22007], [ 3, 0.43333, 0.26008]], [ 0.21787, [ 3, -0.43333, -0.14857], [ 3, 0.23333, 0.08000]], [ 0.44950, [ 3, -0.23333, -0.09028], [ 3, 0.36667, 0.14187]], [ 0.91431, [ 3, -0.36667, -0.03894], [ 3, 0.43333, 0.04602]], [ 0.96033, [ 3, -0.43333, -0.04602], [ 3, 0.36667, 0.03894]], [ 1.2, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RShoulderRoll')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ -1.53558, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ -0.19199, [ 3, -0.33333, -0.07793], [ 3, 0.46667, 0.10911]], [ -0.08288, [ 3, -0.46667, 0.00000], [ 3, 0.36667, 0.00000]], [ -0.08288, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ -0.22707, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ -0.18259, [ 3, -0.23333, -0.02831], [ 3, 0.36667, 0.04448]], [ -0.00870, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ -0.13197, [ 3, -0.43333, 0.01994], [ 3, 0.36667, -0.01687]], [ -0.2, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RElbowYaw')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ 2.07694, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ 1.56157, [ 3, -0.33333, 0.00000], [ 3, 0.46667, 0.00000]], [ 1.61373, [ 3, -0.46667, -0.02319], [ 3, 0.36667, 0.01822]], [ 1.68582, [ 3, -0.36667, -0.05296], [ 3, 0.43333, 0.06259]], [ 1.96041, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ 1.95121, [ 3, -0.23333, 0.00920], [ 3, 0.36667, -0.01445]], [ 0.66571, [ 3, -0.36667, 0.22845], [ 3, 0.43333, -0.26998]], [ 0.39573, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.90962, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RElbowRoll')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ 0.10472, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ 0.38201, [ 3, -0.33333, -0.07367], [ 3, 0.46667, 0.10313]], [ 0.63512, [ 3, -0.46667, -0.21934], [ 3, 0.36667, 0.17234]], [ 1.55705, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ 0.00870, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ 0.00870, [ 3, -0.23333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.42343, [ 3, -0.36667, -0.09786], [ 3, 0.43333, 0.11566]], [ 0.64926, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.0, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LHipYawPitch')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ -0.03371, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ 0.03491, [ 3, -0.33333, 0.00000], [ 3, 0.46667, 0.00000]], [ -0.43561, [ 3, -0.46667, 0.15197], [ 3, 0.36667, -0.11941]], [ -0.77923, [ 3, -0.36667, 0.09257], [ 3, 0.43333, -0.10940]], [ -1.04154, [ 3, -0.43333, 0.07932], [ 3, 0.23333, -0.04271]], [ -1.530, [ 3, -0.23333, 0.00000], [ 3, 0.36667, 0.00000]], [ -1, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ -0.56754, [ 3, -0.43333, -0.16414], [ 3, 0.36667, 0.13889]], [ 0.0, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LHipRoll')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ 0.06294, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ 0.00004, [ 3, -0.33333, 0.00000], [ 3, 0.46667, 0.00000]], [ 0.00158, [ 3, -0.46667, 0.00000], [ 3, 0.36667, 0.00000]], [ -0.37732, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ -0.29755, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ -0.29755, [ 3, -0.23333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.19486, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ 0.12736, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.0, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LHipPitch')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ 0.06140, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ 0.00004, [ 3, -0.33333, 0.06136], [ 3, 0.46667, -0.08590]], [ -1.56924, [ 3, -0.46667, 0.00000], [ 3, 0.36667, 0.00000]], [ -1.28085, [ 3, -0.36667, -0.08132], [ 3, 0.43333, 0.09611]], [ -1.03694, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ -1.15966, [ 3, -0.23333, 0.01464], [ 3, 0.36667, -0.02301]], [ -1.18267, [ 3, -0.36667, 0.01687], [ 3, 0.43333, -0.01994]], [ -1.27011, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ -0.4, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LKneePitch')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ 0.12043, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ 1.98968, [ 3, -0.33333, -0.08775], [ 3, 0.46667, 0.12285]], [ 2.11253, [ 3, -0.46667, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.28221, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ 0.40493, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ 0.35738, [ 3, -0.23333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.71940, [ 3, -0.36667, -0.25311], [ 3, 0.43333, 0.29913]], [ 2.01409, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.95, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LAnklePitch')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ 0.92189, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ -1.02974, [ 3, -0.33333, 0.08628], [ 3, 0.46667, -0.12080]], [ -1.15054, [ 3, -0.46667, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.21625, [ 3, -0.36667, -0.28428], [ 3, 0.43333, 0.33597]], [ 0.71020, [ 3, -0.43333, -0.15307], [ 3, 0.23333, 0.08242]], [ 0.92275, [ 3, -0.23333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.82525, [ 3, -0.36667, 0.09750], [ 3, 0.43333, -0.11522]], [ -0.50166, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ -0.55, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('LAnkleRoll')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ -0.00149, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ 0.00004, [ 3, -0.33333, 0.00000], [ 3, 0.46667, 0.00000]], [ -0.00149, [ 3, -0.46667, 0.00153], [ 3, 0.36667, -0.00121]], [ -0.45249, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ -0.30062, [ 3, -0.43333, -0.07246], [ 3, 0.23333, 0.03901]], [ -0.11808, [ 3, -0.23333, -0.03361], [ 3, 0.36667, 0.05281]], [ -0.04138, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ -0.12114, [ 3, -0.43333, 0.01632], [ 3, 0.36667, -0.01381]], [ 0.0, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RHipRoll')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ 0.03142, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ 0.00004, [ 3, -0.33333, 0.00000], [ 3, 0.46667, 0.00000]], [ 0.00158, [ 3, -0.46667, -0.00153], [ 3, 0.36667, 0.00121]], [ 0.31144, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ 0.25469, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ 0.32065, [ 3, -0.23333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.22707, [ 3, -0.36667, 0.06047], [ 3, 0.43333, -0.07146]], [ -0.07512, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RHipPitch')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ 0.07666, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ -0.00004, [ 3, -0.33333, 0.07670], [ 3, 0.46667, -0.10738]], [ -1.57699, [ 3, -0.46667, 0.10738], [ 3, 0.36667, -0.08437]], [ -1.66136, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ -1.19963, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ -1.59847, [ 3, -0.23333, 0.00000], [ 3, 0.36667, 0.00000]], [ -0.32218, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ -0.71028, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ -0.4, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RKneePitch')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ -0.07819, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ 1.98968, [ 3, -0.33333, -0.06900], [ 3, 0.46667, 0.09660]], [ 2.08628, [ 3, -0.46667, 0.00000], [ 3, 0.36667, 0.00000]], [ 1.74267, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ 2.12019, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ 2.12019, [ 3, -0.23333, 0.00000], [ 3, 0.36667, 0.00000]], [ 2.12019, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ 2.12019, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ 0.95, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RAnklePitch')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ 0.92965, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ -1.02974, [ 3, -0.33333, 0.07746], [ 3, 0.46667, -0.10844]], [ -1.13819, [ 3, -0.46667, 0.02925], [ 3, 0.36667, -0.02298]], [ -1.18645, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ -1.18645, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ -0.58901, [ 3, -0.23333, 0.00000], [ 3, 0.36667, 0.00000]], [ -1.18645, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ -1.18645, [ 3, -0.43333, 0.00000], [ 3, 0.36667, 0.00000]], [ -0.55, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    names.append('RAnkleRoll')
    times.append([0.5, 1.0, 1.7, 2.3, 2.9, 3.7, 4.4, 5.2, 6.5])
    angles.append([ [ 0.18850, [ 3, -0.33333, 0.00000], [ 3, 0.33333, 0.00000]], [ 0.00004, [ 3, -0.33333, 0.00000], [ 3, 0.46667, 0.00000]], [ 0.00618, [ 3, -0.46667, 0.00000], [ 3, 0.36667, 0.00000]], [ -0.00456, [ 3, -0.36667, 0.01074], [ 3, 0.43333, -0.01269]], [ -0.09813, [ 3, -0.43333, 0.00000], [ 3, 0.23333, 0.00000]], [ -0.01376, [ 3, -0.23333, 0.00000], [ 3, 0.36667, 0.00000]], [ -0.09507, [ 3, -0.36667, 0.00000], [ 3, 0.43333, 0.00000]], [ 0.03532, [ 3, -0.43333, -0.02825], [ 3, 0.36667, 0.02390]], [ 0.0, [ 3, -0.36667, 0.00000], [ 3, 0.00000, 0.00000]]])

    motion.angleInterpolationBezier(names, times, angles)
    
def stance(arg=0):
    '''Bend the knees in a crouching manner'''
    names = list()
    angles = list()
    times = list()
    
    names.append('LLeg')
    angles.extend([[0],  [0],  [-0.8500], [2], [-1.1],  [0]  ])
    times.extend([[0.7], [0.7], [0.7],    [0.7],     [0.7],     [0.7]])
    
    names.append('RLeg')
    angles.extend([[0], [0], [-0.8500], [2], [-1.1], [0]  ])
    times.extend([[0.7], [0.7],  [0.7],    [0.7],    [0.7],     [0.7]])
    
    motion.post.angleInterpolation(names, angles, times, True)
    
def kickStraight(angle = 0):
    # angle slightly positive, kick towards left with rightleg
    names = ['RShoulderRoll', 'RShoulderPitch', 'LShoulderRoll', 'LShoulderPitch', 'RHipRoll', 'RHipPitch', 'RKneePitch', \
             'RAnklePitch', 'RAnkleRoll', 'LHipRoll', 'LHipPitch', 'LKneePitch', 'LAnklePitch', 'LAnkleRoll']
    angles = [[-0.3], [0.4], [0.5], [1.0], [0.0], [-0.4, -0.2], [0.95, 1.5], [-0.55, -1], [0.2], [0.0], [-0.4], [0.95], [-0.55], [0.2]]
    times =  [[ 0.5], [0.5], [0.5], [0.5], [0.5], [ 0.4,  0.8], [ 0.4, 0.8],  [0.4, 0.8], [0.4], [0.5], [ 0.4], [ 0.4], [ 0.4],  [0.4]]
    motion.angleInterpolation(names, angles, times, True)
    
    motion.angleInterpolationWithSpeed(['RShoulderPitch', 'RHipPitch', 'RKneePitch', 'RAnklePitch'], 
                                         [1.5,               -0.7,        1.05,         -0.5],  
                                         1.0 , True)
    
    motion.angleInterpolation(['RHipPitch', 'RKneePitch', 'RAnklePitch'], \
                                [-0.5,         1.1,        -0.65], 
                                [[0.25],       [0.25],     [0.25]], True)
    normalPose(True)
    
    
# max range for angles of the Aldebaran Nao's joints
ranges = {  'HeadYaw'        : (-2.0857  , 2.0857 ),
            'HeadPitch'      : (-0.6720  , 0.5149 ),
            'RShoulderPitch' : (-2.0857  , 2.0857 ),
            'LShoulderPitch' : (-2.0857  , 2.0857 ),
            'RShoulderRoll'  : (-1.3265  , 0.3142 ),
            'LShoulderRoll'  : (-0.3142  , 1.3265 ),
            'RElbowYaw'      : (-2.0857  , 2.0857 ),
            'LElbowYaw'      : (-2.0857  , 2.0857 ),
            'RElbowRoll'     : ( 0.0349  , 1.5466 ),
            'LElbowRoll'     : (-1.5466  , -0.0349),        
            'RWristYaw'      : (-2.0857  , 2.0857 ),
            'LWristYaw'      : (-2.0857  , 2.0857 )  } 

buttons = { 'A'    : stanceOrStand ,
            'B'    : kickStraight ,
            'Up'   : walk ,
            'Down' : walk ,
            'Left' : walk ,
            'Right': walk }
            
arguments = {'A'  : 0,
             'B'  : 0,
             'Up' : (0.75, 0, 0, 1),
             'Down' : (-0.75, 0, 0, 1) ,
             'Left' : (0, 0, 0.75, 1) ,
             'Right' : (0, 0, -0.75, 1) }             

if __name__ == "__main__":
    try:
        number_of_connections = int(sys.argv[1])
    except:
        print "Correct way of using is python mimicker.py <number of connections>"
        sys.exit(1)
    startMimic( number_of_connections )
