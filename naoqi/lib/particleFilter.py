from random import *
from math import *
import time
import threading

motProxy = ALProxy('ALMotion', '127.0.0.1', 9559)

class ParticleFilter(threading.Thread):

    # Field Parameters
    num_samples = 100
    wslow = 0
    wfast = 0
    samples = []
    timeStamp = time.time()
    
    measurements = [None]
    control = [0,0,0]
    meanState = [0,0,0]
    counter = 0
    lock = threading.Lock():
    
    # feature coordinates per id, (x,y).
    # note that the naming is based on naoviewpoint (left poles are
    # on the left side of the nao when it sees the goal)
    worldMap = { 'YellowPoleRight':    (6.0, 1.25), 
                 'YellowPoleLeft' :    (6.0, 2.75),
                 'BluePoleLeft'   :    (0.0, 1.25),
                 'BluePoleRight'  :    (0.0, 2.75) }

    # The default number of samples. 
    def __init__( self, position = False, numberOfSamples = 100 ):
        threading.Thread.__init__(self)
        self.reset( position, numberOfSamples )
        self.running = False
        self.closed = False
        
    # destructor for this class
    def __del__(self):
        self.running = False
        self.closed = True

    def active(self):
        return self.running
    
    def close(self):
        self.__del__()
    
    def startFilter(self):
        self.running = True
    
    def pauseFilter(self):
        self.running = False
        
    # main thread function
    def run(self):
        while not self.closed:
            while self.running:
                # get the current timestamp
                interval = time.time()- self.timeStamp
                self.timeStamp = time.time()

                oldState = self.meanState

                # get measurements, if available
                measurements = self.measurements()
                self.measurements = [None]
                # get the current robot velocity
                
                control = motProxy.getRobotVelocity()
                if control != [0,0,0]:
                    self.control[0] += control[0] * interval
                    self.control[1] += control[1] * interval
                    self.control[2] += control[2] * interval
                    
                    self.counter += 1
                    
                if self.counter == 20 or measurements[0] != None:
                    self.counter = 0
                    self.meanState = self.iteratePlus( measurements , self.control ) 
                if oldState != self.meanState:
                    print 'Current position', self.meanState
                
        print 'Closed particle filter thread safely.'
     
    def getPosition(self):
        return self.meanState
                 
    def setMeasurements( self,measurements ):
        with self.lock
            self.measurements = measurements
        
    # Reset field variables for this particleFilter. 
    def reset( self, position = False, numberOfSamples = 100 ):
        # Field Parameters
        self.num_samples = numberOfSamples
        self.wslow = 0
        self.wfast = 0
        self.timeStamp = time.time()
        
        self.measurements = [None]
        self.control = [0,0,0]
        self.counter = 0
            
    # Create particles. If given a position, all particles are at this position. 
    def createSamples( self, position ):
        field_width = 6;
        field_height = 4;
        
        self.samples = []

        for i in range(self.num_samples):
            if not position:
                x = random() * field_width
                y = random() * field_height
                theta = uniform( -pi, pi )
            else:
                # add noise to the given position 
                x = position[0] + gauss(0, 0.1)
                y = position[1] + gauss(0, 0.1)
                theta = self.minimizedAngle( position[2] + gauss(0, 1.5) )
            self.samples.append( [ x, y, theta ] )
        self.meanState = self.calcMean( self.samples )

    def setTime( self,timestamp ):
        self.timestamp = timestamp
    
    def iteratePlus( self, measurements, control ):

        length = len(measurements)
        #print 'Control: ' ,control, 'Length', length
        
        control[0] = control[0] / float(length)
        control[1] = control[1] / float(length)
        control[2] = control[2] / float(length)
        
        meanState = [0,0,0]
        for measurement in measurements: 
            meanState = self.iterate( measurement, control)
        return meanState
    
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
        meanState = self.calcMean(self.samples)
        
        #print '\nIteration ', iteration, ':'
        if counter:
            print 'Introduced', counter, 'random samples.'
        #print 'Mean:' , meanState
        #print 'Measured', measurement
        #print 'Wfast/wslow', wfast, wslow
        
        return meanState
                    
    # Simple motion model: Increment the state by the rotated control vector
    def motionModel( self, sample, control, interval ):
                
        # Add noise to the motion, currently 0.1 meters per 1 meter and 0.2 rad per 1 rad (I think)
        
        control[0] = (control[0] + gauss( 0, 0.001 ) )
        control[1] = (control[1] + gauss( 0, 0.001 ) )
        control[2] = (control[2] + gauss( 0, 0.002 ) )
        
        x = sample[0] + control[0] * cos(sample[2]) + control[1] * cos(sample[2] + 0.5 * pi )
        y = sample[1] + control[0] * sin(sample[2]) + control[1] * sin(sample[2] + 0.5 * pi )
        theta = sample[2] + control[2]
        return x, y, theta

    # Sensor model calculates the probability of a state given a measurement 
    def sensorModel( self, state, measurement ):
        bearingM, rangeM, signature, idFeature = measurement
        x,y,theta = state

        # Only keep a sample if it is in the field
        if -0.7 < x < 6.7 and -0.7 < y < 4.7:
            xR, yR = self.worldMap[idFeature]
            
            rangeR = sqrt( ( x-xR )**2 + ( y-yR )**2 )
            bearingR = self.minimizedAngle( atan2( yR - y, xR - x) - theta )
            
            sigmaRange = 0.1
            sigmaBearing =  0.005
            sigmaSignature = 0.01

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
            
    # Calculate the mean of 3D samples
    def calcMean( self, samples ):
        x = 0
        y = 0
        t = 0
        
        for sample in samples:
            xs , ys, ts = sample
            x += xs / self.num_samples
            y += ys / self.num_samples
            t += ts / self.num_samples
        return x,y,t