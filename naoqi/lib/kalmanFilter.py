import math
import random
import matrix

# Method to create samples given the mean and covariance matrix
def sample(mean, cov , dimensions):
    r = matrix.transpose( matrix.Cholesky(cov) )

    randoms = matrix.zero(dimensions, 1)
    for i in range(len(randoms)):
        randoms[i][0] = random.gauss(0,0.025)

    return matrix.plus( mean , matrix.mult(r, randoms))

class KalmanFilter():    
    # R = noise for covariance matrix prediction step
    R = [[0.01,0],[0,0.01]]
    # Q = noise for covariance matrix correction step
    Q = [[0.01,0],[0,0.01]]

    mu = [[0],[0]]
    Sigma = [[0.1,0],[0,0.1]]
    u = matrix.zero( 2,1 )
    z = matrix.zero( 2,1 )
    I = [[1,0],[0,1]]
    
    def __init__(self):
	self.mu = [[0],[0]]
	self.lost = True
	
    def iterate(self, measurement, control ):
        if measurement:
	    self.lost = False
	
        velocity = control
                
        # known are speeds, convert to absolute movements
        nao_movement_x     = velocity[0]
        nao_movement_y     = velocity[1]
        nao_movement_t     = velocity[2]
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
        #print muBelief
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

        self.ballPos = self.mu[0][0], self.mu[1][0]    