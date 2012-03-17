import math
import time
import random
import matrix
import visionInterface as v
from naoqi import ALProxy

motProxy = ALProxy('ALMotion', '127.0.0.1', 9559)

# Method to create samples given the mean and covariance matrix
def sample(mean, cov , dimensions):
    r = matrix.transpose( matrix.Cholesky(cov) )

    randoms = matrix.zero(dimensions, 1)
    for i in range(len(randoms)):
        randoms[i][0] = random.gauss(0,1)

    return matrix.plus( mean , matrix.mult(r, randoms))

class KalmanBall():    
    # R = noise for covariance matrix prediction step
    R = [[0.001,0],[0,0.001]]
    # Q = noise for covariance matrix correction step
    Q = [[0.001,0],[0,0.001]]

    mu = [[0],[0]]
    Sigma = [[0.1,0],[0,0.1]]
    u = matrix.zero( 2,1 )
    z = matrix.zero( 2,1 )
    I = [[1,0],[0,1]]

    firstCall = bool
    
    def init(self, measurement = (1,0)):
        self.firstCall = True
        self.mu[0][0] = measurement[0]
        self.mu[1][0] = measurement[1]

    def setFirstCall(self, arg = True, initial = (1,0)):
        self.firstCall = arg
        self.mu = [[ initial[0] ],[ initial[1] ]]
        self.Sigma = [[0.1,0],[0,0.1]]

    def iterate(self, measurement):
        now = time.time()
        # timestamps matter. IMPORTANT: Do not use if first iteration has not been set. 
        if self.firstCall:
            self.firstCall = False
            self.timeStamp = time.time()
            
        timeTaken = time.time() - self.timeStamp
        self.timeStamp = time.time() 

        velocity = motProxy.getRobotVelocity()
        #velocity = [0,0,0]
                
        # known are speeds, convert to absolute movements
        nao_movement_x     = velocity[0] * timeTaken
        nao_movement_y     = velocity[1] * timeTaken
        nao_movement_t     = velocity[2] * timeTaken

        # step forward using control vector u
        self.u[0][0] = nao_movement_x
        self.u[1][0] = nao_movement_y

        muBelief = self.mu
        
        # ________ PREDICTION ________
        
        # rotate using nao_movements theta
        t = nao_movement_t
        rotationmatrix = [[ math.cos( t ), -math.sin(t) ],[ math.sin(t), math.cos(t) ]]

        # Predict new measurement based on nao movement.
        # Nao moves x,y towards the ball 
        muBelief = matrix.subtract( muBelief , self.u )
        # Nao rotates theta
        muBelief = matrix.mult( rotationmatrix, muBelief )

        # add noise to motion
        muBelief = sample( muBelief, self.Sigma, 2)
        
        # covariance matrix update
        SigmaBelief = matrix.plus( self.Sigma , self.R)

        # ________ CORRECTION _________

        if measurement:
            self.z[0][0] = measurement[0]
            self.z[1][0] = measurement[1]

            # Since C = [1,0;0,1], drop it
            s = matrix.inverse2D( matrix.plus(  SigmaBelief, self.Q) )
            K = matrix.mult(SigmaBelief, s ) 

            self.mu = matrix.plus(  muBelief,  matrix.mult(K, matrix.subtract(self.z , muBelief)) )
            self.Sigma = matrix.mult(matrix.subtract( self.I, K ), SigmaBelief)
        else:
            # if no ball is found, use the predicted state!
            self.mu = muBelief
            self.Sigma = SigmaBelief

        #print 'Mu:',self.mu
        #print 'Sigma: '
        #matrix.show(self.Sigma)
        #print ''
        return (self.mu[0][0], self.mu[1][0])

'''
class KalmanNao():    
    # R = noise for covariance matrix prediction step
    R = [[0.01,0,0],[0,0.01,0],[0,0,0.01]]
    # Q = noise for covariance matrix correction step
    Q = [[0.01,0,0],[0,0.01,0],[0,0,0.01]]

    mu = matrix.zero( 3,1 )
    Sigma = [[0.1,0.0,0.0],[0.0,0.05,0.0],[0.0,0.0,0.1]]
    u = matrix.zero( 3,1 )
    z = matrix.zero( 3,1 )
    I = [[1,0,0],[0,1,0],[0,0,1]]

    firstCall = bool
    
    def init(self):
        self.firstCall = True

    def setFirstCall(self, arg = True):
        self.firstCall = arg
        
    def iterate(self, measurement):
        now = time.time()
        # timestamps matter. IMPORTANT: Do not use if first iteration has not been set. 
        if self.firstCall:
            self.firstCall = False
            self.timeStamp = time.time()
            
        timeTaken = time.time() - self.timeStamp
        self.timeStamp = time.time() 

        #velocity = motProxy.getRobotVelocity()
        velocity = [0,0,0]
                
        # known are speeds, convert to absolute movements
        nao_movement_x     = velocity[0] * timeTaken
        nao_movement_y     = velocity[1] * timeTaken
        nao_movement_t     = velocity[2] * timeTaken

        # step forward using control vector u
        self.u[0][0] = 1/100.0 * nao_movement_x
        self.u[1][0] = 1/100.0 * nao_movement_y
        self.u[2][0] = 1/100.0 * nao_movement_t
        
        muBelief = self.mu
        
        # ________ PREDICTION ________
        
        # rotate using nao_movements theta + OLD THETA! :D
        t = (self.u[2][0] + muBelief[2][0]) / 100.0
        print self.u[2][0], muBelief[2][0]
        rotationmatrix = [[ math.cos( t ), -math.sin(t) ],[ math.sin(t), math.cos(t) ]]

        # for multiple (=100, for now) steps: walk, turn, thus approximating constant velocity walking:
        for n in range(100):
            # Nao moves 1/100th x rotated theta and y rotated theta in the absolute world
            absControl = matrix.mult( rotationmatrix, [[self.u[0][0]], [self.u[1][0]]] )

            # new mu is oldx+rotx, oldy+roty, oldt + newt
            muBelief = matrix.plus( muBelief , [[absControl[0][0]], [absControl[1][0]], [self.u[2][0]/100.0]] )
           
        # add noise to motion
        print 'Predicted nao position without noise\n', muBelief
        muBelief = sample( muBelief, self.Sigma , 3)
        
        # covariance matrix update
        SigmaBelief = matrix.plus( self.Sigma , self.R)


        print 'Predicted nao position, orientation: \n', muBelief
        # ________ CORRECTION _________

        if measurement:
            print 'Measurement:\n', measurement
            # A feature has an x,y, orientation and ID (and a probability for this ID?)
            featureID = measurement[3]

            features = dict()
            features[featureID] = [0,0]
            absObjX,absObjY = features[featureID]

            self.z[0][0] = measurement[0]
            self.z[1][0] = measurement[1]
            self.z[2][0] = measurement[2]

            # If measurement orientation = ?, then so is that of the nao for x
            t = self.z[2][0] 

            
            rotationmatrix = [[ math.cos( t ), -math.sin(t) ],[ math.sin(t), math.cos(t) ]]

            # Nao absolute x,y = abs x,y of object - rot*measurementX,measurementY
            absMeasurement = matrix.mult(rotationmatrix, [[ self.z[0][0] ],[ self.z[1][0] ]])

            # Nao perception of Objectx,y at MeasurementX,Y,t results in naoX,Y,t
            absNaoX = absObjX + absMeasurement[0][0]
            absNaoY = absObjY + absMeasurement[1][0]
            absNaoT = -t

            self.z[0][0] = absNaoX
            self.z[1][0] = absNaoY
            self.z[2][0] = absNaoT
            print 'Based on measurement - Nao position,orientation: \n', self.z, '\n'

            # Since C = [1,0,0;0,1,0;0,0,1], drop it
            s = matrix.inverse3D( matrix.plus( SigmaBelief, self.Q) )
            #matrix.show(s)
            K = matrix.mult(SigmaBelief, s )
            #matrix.show(K)
            self.mu = matrix.plus( muBelief, matrix.mult(K, matrix.subtract(self.z , muBelief)) )
            self.Sigma = matrix.mult(matrix.subtract( self.I, K ), SigmaBelief)
        else:
            # if no ball is found, add noise to the old ballposition!
            self.mu = muBelief
            self.Sigma = SigmaBelief

        print 'Kalman position:'
        print self.mu, '\n\n'
        
        return (self.mu[0][0], self.mu[1][0], self.mu[2][0])
'''        