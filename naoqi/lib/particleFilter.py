from random import *
from math import *
import time
import threading

class ParticleFilter():

    # Field Parameters
    num_samples = 10
    wslow = 0
    wfast = 0
    samples = []
    
    meanState = None
    counter = 0
    
    # feature coordinates per id, (x,y).
    # note that the naming is based on naoviewpoint (left poles are
    # on the left side of the nao when it sees the goal)
    worldMap = { 'YellowPoleRight':    (6.0, 1.25), 
                 'YellowPoleLeft' :    (6.0, 2.75),
                 'BluePoleLeft'   :    (0.0, 1.25),
                 'BluePoleRight'  :    (0.0, 2.75) }

    # The default number of samples. 
    def __init__( self, numberOfSamples ):
                
        self.reset( numberOfSamples )
        self.running = False
        self.closed = False
                
    # destructor for this class
    def __del__(self):
        self.running = False
        self.closed = True
            
    def close(self):
        self.__del__()
                 
    def getPosition(self):
        return self.meanState
             
    # Reset field variables for this particleFilter. 
    def reset( self, numberOfSamples, position = [3,2,0.0] ):
        # Field Parameters
        self.num_samples = numberOfSamples
        self.wslow = 0
        self.wfast = 0
        self.counter = 0
        self.createSamples( position )    
            
    # Create particles. If given a position, all particles are at this position. 
    def createSamples( self, position ):
        field_width = 6;
        field_height = 4;
        
        self.samples = []
        self.weights = []
	print position
        for i in range(self.num_samples):
            if type(position) != list:
		x = random() * field_width
                y = random() * field_height
                theta = uniform( -pi, pi )
            else:
                # add noise to the given position 
                x = position[0] + gauss(0, 0.1)
                y = position[1] + gauss(0, 0.1)
                theta = self.minimizedAngle( position[2] + gauss(0, 1.5) )
            self.samples.append( [ x, y, theta ] )
            self.weights.append( random() )
        self.meanState = self.findBest( self.samples, self.weights )

    def iteratePlus( self, measurements, control ):
        length = len(measurements)
        
        if length == 0:
            self.iterate( None, control )
        else:        
            for measurement in measurements:
                self.iterate( measurement, control)
                control = [0,0,0]
                
    # One iteration of the particle filter. 
    def iterate( self, measurement, control):
	
        predictedSamples = []
        weights = []

        for sample in self.samples:

            # Predict the new state based on the control vector
            x, y, theta = self.motionModel( sample, control )
            predictedSamples.append( [ x, y, theta ] )

            # If a measurement is given..
            if measurement:
                # ..find weights
                weight = self.sensorModel( [x,y,theta], measurement )
                weights.append( weight )
                
        # counter keeps track of the number of random samples
        counter = 0
        
        # Resampling is only possible if weights are used        
        if measurement:
	    self.weights = weights
            meanWeight = sum(weights) / self.num_samples

            # These are 'learning rate'-like factors that determine how fast random samples are introduced
            self.wslow += 0.05 * (meanWeight - self.wslow)
            self.wfast += 0.3 * (meanWeight - self.wfast)
            if self.wslow == 0 :
                print 'What the fuck is happening'
                self.wslow = 0.01
            newsamples = []
            
            
            # RESAMPLING
            for m in range(self.num_samples):
                # If wfast/wslow is large, pick random samples to tackle the kidnapping problem
                if random() < max(0, 1 - self.wfast/self.wslow):
                    newsamples.append( [uniform(0,6), uniform(0,4), uniform(-pi, pi)] )
                    counter += 1
                else:
                    # else, draw samples with probability weight
                    threshold = uniform( 0, meanWeight ) + m * meanWeight
                    i = 0
                    W = weights[0]

                    while threshold > W:
                        i += 1
                        W += weights[i]
                    newsamples.append( predictedSamples[i]  )
            
            self.samples = newsamples
        else:
            # if no measurement was given, use the prediction
            self.samples = predictedSamples
        
        # The mean of all samples is (probably) the current position and orientation
        self.meanState = self.findBest(self.samples, self.weights)
        
        if counter:
            print 'Introduced', counter, 'random samples.'
                            
    # Simple motion model: Increment the state by the rotated control vector
    def motionModel( self, sample, control ):
                
        # Add noise to the motion, currently 0.001 meters per 1 meter and 0.02 rad per 1? or 2 pi rad (I think)
        control[0] += gauss( 0, 0.001 ) 
        control[1] += gauss( 0, 0.001 )
        control[2] += gauss( 0, 0.002 )
        
        x = sample[0] + control[0] * cos(sample[2]) - control[1] * sin(sample[2])
        y = sample[1] + control[0] * sin(sample[2]) + control[1] * cos(sample[2])
        theta = self.minimizedAngle(sample[2] + control[2])
        return x, y, theta

    # Sensor model calculates the probability of a state given a measurement 
    def sensorModel( self, state, measurement ):
        bearingM, rangeM, signature, idFeature = measurement
        x,y,theta = state

        # Only keep a sample if it is in the field
        if -0.7 < x < 6.7 and -0.7 < y < 4.7:
            xR, yR = self.worldMap[idFeature]
            
            rangeR = sqrt( ( x-xR )**2 + ( y-yR )**2 )
            bearingR = self.minimizedAngle( atan2( yR - y, xR - x) + theta )
            
            sigmaRange = 0.3        # range is very uncertain
            sigmaBearing =  0.005     # bearing is very precise
            sigmaSignature = 0.01    # signature does not really matter here
	    
	    weight = self.prob( rangeR-rangeM , sigmaRange ) * \
                     self.prob( bearingR-bearingM , sigmaBearing ) * \
                     self.prob( signature, sigmaSignature )
        else:
            weight = 0
            
        return weight

    # Create an observation given a state and the id of a feature on the map.
    def observation( self, state, idFeature ) :
        x,y,theta = state
        xR, yR = self.worldMap[idFeature]
            
        rangeR = sqrt( (x-xR )**2 + (y-yR)**2 )
        bearingR = self.minimizedAngle( atan2( yR - y, xR - x) - theta )
        return bearingR, rangeR, 0, idFeature

    # Convert numbers from range 0 to 2pi to -pi to pi
    def minimizedAngle( self, angle ) :
        if angle > pi:
            angle -= 2*pi
        if angle <= -pi:
            angle += 2*pi
        return angle

    # Calculate density given x and sigma 
    def prob( self, x, sigma ):
        return exp( - x**2 / (2*sigma) ) / sqrt( sigma * 2 * pi ) 
            
    # In the case of weights, take the best sample
    def findBest( self, samples, weights ):
      
        bestSoFar = samples[0]
        bestWeight = weights[0]
        
        for i in range(1, len(samples)):
	    if weights[i] > bestWeight:
	        bestWeight = weights[i]
	        bestSoFar = samples[i]
	        
	return bestSoFar