"""
File: particleFilter.py
Author: Auke Wiggers
"""

from random import random, gauss, uniform
from math import cos, sin, pi, sqrt, exp, atan2
import sys

class ParticleFilter():
    """
    ParticleFilter instance that is used for localization. Particles are 3d 
    vectors (lists) containing x, y, orientation.     
    """
    
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
    worldMap = { "RightPoleFar"   :    (6.0, 1.25),  
                 "LeftPoleFar"    :    (6.0, 2.75), 
                 "RightPoleClose" :    (0.0, 1.25), 
                 "LeftPoleClose"  :    (0.0, 2.75) }

    def __init__( self, numberOfSamples, position = [0,0,0] ):
        self.reset( numberOfSamples )
        self.running = False
        self.meanState = position
                
    def __del__(self):
        self.close()
            
    def close(self):
        self.running = False
                 
    def getPosition(self):
        """ Get the current position based on particles """
        return self.meanState
             
    def reset( self, numberOfSamples, position = [0,0,0] ):
        """Reset field variables for this particleFilter. """
        self.num_samples = numberOfSamples
        self.wslow = 0
        self.wfast = 0
        self.counter = 0
        self.createSamples( position )    
            
    def createSamples( self, position ):
        """ Create particles. If given a position, all particles are at 
        this position. """
        field_width = 6
        field_height = 4
        
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
        """ Iterate, given zero or more measurements and a control vector """
        
        if measurements :
            length = len(measurements)
        else:
            length = 0
        if length == 0:
            self.iterate( None, control )            
        else:        
            for i in range(len(measurements)):
                if measurements[i] == None:
                    continue
                mostProbableFeature = None
                chance = 0                  
                bearingM, rangeM = measurements[ i ]
                # Check what the most probable feature is that is perceived
                for idFeature in self.worldMap:
                    xR, yR       = self.worldMap[idFeature]
                    x, y, theta  = self.meanState
                    rangeR = sqrt( ( x - xR )**2 + ( y - yR )**2 )
                    bearingR = self.minimizedAngle( atan2( yR-y, xR-x)+ theta )
            
                    sigmaRange = 0.3          # range is very uncertain
                    sigmaBearing =  0.005     # bearing is very precise
                    
                    curChance = self.prob( rangeR-rangeM , sigmaRange ) * \
                              self.prob( bearingR-bearingM , sigmaBearing )
                    
                    if curChance > chance:
                        chance = curChance
                        mostProbableFeature = idFeature
                measurements[ i ] = bearingM, rangeM, mostProbableFeature
                
            for measurement in measurements:                
                self.iterate( measurement, control)
                control = [0,0,0]
                
    def iterate( self, measurement, control):
        """ One iteration of the particle filter. """
	
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

            # These are "learning rate"-like factors that determine 
            # how fast random samples are introduced
            self.wslow += 0.05 * (meanWeight - self.wslow)
            self.wfast += 0.3 * (meanWeight - self.wfast)
            if self.wslow == 0 :
                print "What the fuck is happening"
                self.wslow = 0.01
            newsamples = []
            
            
            # RESAMPLING
            for m in range(self.num_samples):
                # If wfast/wslow is large, pick random samples to tackle the 
                # kidnapping problem
                if random() < max(0, 1 - self.wfast/self.wslow):
                    newsamples.append( [uniform(0,6), 
                                        uniform(0,4), 
                                        uniform(-pi, pi)] )
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
        
        # The mean of all samples is (probably) the current position and 
        # orientation
        self.meanState = self.findBest(self.samples, self.weights)
        
        if counter:
            print "Introduced", counter, "random samples."
                            
    def motionModel( self, sample, control ):
        """ Simple motion model: Increment the state by the rotated control 
        Add noise to the motion, currently 0.001 meters per 1 meter and 
        0.02 rad per 1? or 2 pi rad (I think)
        """
        control[0] += gauss( 0, 0.001 ) 
        control[1] += gauss( 0, 0.001 )
        control[2] += gauss( 0, 0.002 )
        
        x = sample[0]+control[0] * cos(sample[2]) - control[1] * sin(sample[2])
        y = sample[1]+control[0] * sin(sample[2]) + control[1] * cos(sample[2])
        theta = self.minimizedAngle(sample[2] + control[2])
        return x, y, theta

    def sensorModel( self, state, measurement ):
        """Sensor model calculates probability of a state given measurement """ 
        try:
            bearingM, rangeM, idFeature = measurement
        except:
            print "Stuff went wrong namely", measurement
            sys.exit(1)
        x,y,theta = state

        # Only keep a sample if it is in the field
        if -0.7 < x < 6.7 and -0.7 < y < 4.7:
            xR, yR = self.worldMap[idFeature]
            
            rangeR = sqrt( ( x-xR )**2 + ( y-yR )**2 )
            bearingR = self.minimizedAngle( atan2( yR - y, xR - x) + theta )
            
            sigmaRange = 0.3        # range is very uncertain
            sigmaBearing =  0.005     # bearing is very precise
        
            weight = self.prob( rangeR-rangeM , sigmaRange ) * \
                      self.prob( bearingR-bearingM , sigmaBearing )
        else:
            weight = 0
            
        return weight

    def observation( self, state, idFeature ) :
        """ Create an observation given a state and the id of a feature on the 
        map. """
        x,y,theta = state
        xR, yR = self.worldMap[idFeature]
            
        rangeR = sqrt( (x-xR )**2 + (y-yR)**2 )
        bearingR = self.minimizedAngle( atan2( yR - y, xR - x) - theta )
        return bearingR, rangeR, 0, idFeature

    def minimizedAngle( self, angle ) :
        """ Convert numbers from range 0 to 2pi to -pi to pi """
        if angle > pi:
            angle -= 2*pi
        if angle <= -pi:
            angle += 2*pi
        return angle

    def prob( self, x, sigma ):
        """ Calculate density given x and sigma """
        return exp( - x**2 / (2*sigma) ) / sqrt( sigma * 2 * pi ) 
            
    def findBest( self, samples, weights ):
        """ In the case of weights, take the best sample """
        bestSoFar = samples[0]
        bestWeight = weights[0]
        
        for i in range(1, len(samples)):
            if weights[i] > bestWeight:
                bestWeight = weights[i]
                bestSoFar = samples[i]
        return bestSoFar
