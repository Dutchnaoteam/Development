"""
File: kalmanFilter
Author: Auke Wiggers
"""

import math
import random
import matrix

class KalmanFilter():    
    """ class KalmanFilter

    Creates a kalmanfilter object that performs the prediction and measurement
    step based on input given by set methods.

    """
    # R = noise for covariance matrix prediction step
    R = [[0.01, 0], [0, 0.01]]
    # Q = noise for covariance matrix correction step
    Q = [[0.01, 0], [0, 0.01]]

    mu = [[0], [0]]
    sigma = [[0.1, 0], [0, 0.1]]
    u = matrix.zero( 2, 1 )
    z = matrix.zero( 2, 1 )
    I = [[1, 0], [0, 1]]
    
    def __init__(self):
        self.mu = [[0], [0]]
        self.ballPos = None
    
    def reset(self, position = (0, 0) ):
        """Reset the kalman filters mu and sigma"""
        xPos, yPos = position
        self.mu = [[xPos], [yPos]]
        self.ballPos = None
        self.sigma = [[0.1, 0], [0, 0.1]]
        
    def iterate(self, measurement, control ):
        """ Perform one iteration (prediction/correction) """
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
        theta = nao_movement_t
        rotationmatrix = [[ math.cos( theta ), -math.sin(theta) ], \
                          [ math.sin( theta ),  math.cos(theta) ]]

        # Predict new measurement based on nao movement.
        # Nao moves x,y towards the ball 
        muBelief = matrix.subtract( muBelief , self.u )
        #print muBelief
        # Nao rotates theta
        muBelief = matrix.mult( rotationmatrix, muBelief )

        # add noise to motion
        muBelief = sample( muBelief, self.sigma, 2)
        
        # covariance matrix update
        sigmaBelief = matrix.plus( self.sigma , self.R)

        # ________ CORRECTION _________
        if measurement:
            self.z[0][0] = measurement[0]
            self.z[1][0] = measurement[1]

            # Since C = [1,0;0,1], drop it
            inverse = matrix.inverse2D( matrix.plus(  sigmaBelief, self.Q) )
            K = matrix.mult(sigmaBelief, inverse ) 

            self.mu = matrix.plus( muBelief, 
                                   matrix.mult(K, 
                                               matrix.subtract(self.z , 
                                                               muBelief ) 
                                               )
                                 )
            self.sigma = matrix.mult(matrix.subtract( self.I, K ), sigmaBelief)
        else:
            # if no ball is found, use the predicted state!
            self.mu = muBelief
            self.sigma = sigmaBelief

        self.ballPos = self.mu[0][0], self.mu[1][0]    

def sample(mean, cov, dimensions):
    """ sample(mean, covariance, dimensions) -> vector of size dimensions x 1

    Method to create samples given the mean and covariance matrix using 
    Cholesky

    """
    transposed = matrix.transpose( matrix.Cholesky(cov) )

    randoms = matrix.zero(dimensions, 1)
    for i in range(len(randoms)):
        randoms[i][0] = random.gauss(0, 0.0025)

    return matrix.plus( mean , matrix.mult(transposed, randoms))

        