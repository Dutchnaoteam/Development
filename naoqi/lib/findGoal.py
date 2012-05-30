import math

def findGoal(image, head, cam):
    """
    findGoal(image, head) -> [ bearing, distance ]
    
    4 tot 5 cases:
    - Goal en groen
    - Paal en groen
    - Paal/goal en geen groen
    - Geen goal
    
    1. While true: Scanlines van onderaf.
    2. If found yellow: Validate pole
    3. Calculate distance based on pitch
    4. Calculate bearing  based on yaw
    
    """
    
    # Yellow goal hsv values:
    hueMin = 29
    hueMax = 37 
    saturationMin = 106 
    saturationMax = 220
    valueMin = 105
    valueMax = 255
    
    hsvFrameYellow = cv.CreateImage(size, cv.IPL_DEPTH_8U, 3)
    filterYellow   = cv.CreateImage(size, cv.IPL_DEPTH_8U, 1)
    
    hsvMinY = cv.Scalar(hueMin, saturationMin, valueMin, 0)
    hsvMaxY = cv.Scalar(hueMax, saturationMax, valueMax, 0)
    cv.CvtColor(image, hsvFrameYellow, cv.CV_BGR2HSV)
    cv.InRangeS(hsvFrameYellow, hsvMinY, hsvMaxY, filteredYellow)
    
    hsvFrameGreen = cv.CreateImage(size, cv.IPL_DEPTH_8U, 3)
    filterGreen   = cv.CreateImage(size, cv.IPL_DEPTH_8U, 1)
    
    hsvMinG = cv.Scalar(50, 51,  66, 0)
    hsvMaxG = cv.Scalar(90, 199, 255, 0)

    cv.CvtColor(image, hsvFrame, cv.CV_BGR2HSV)
    cv.InRangeS(hsvFrameGreen, hsvMinG, hsvMaxG, filteredGreen)
    
    xsize, ysize = image.size
    
    stepsizeX = [4, 2, 1]
    stepsizeY = 5
    
    #thresholdYellow =
    #thresholdGreen  =
    
    foundPole  = False
    gapFound   = False    
    firstPole  = None
    secondPole = None
    beginPole  = 0
    endPole    = 0 
    
    # first, look at the bottom 80 pixels with a certain stepsize for x.
    for x in xrange( xsize, stepsizeX[0] ):
        # if the current x is in between the begin and end of a found pole, skip it
        if beginPole-stepSize[0] < x < endPole+stepSize[0]:
            continue
        # break if second pole found
        if doBreak:
            break
        for y in xrange( 0, 240, stepsizeY ):
            # if yellow is found, look for green (underneath) or white
            if filteredYellow[y,x] > thresholdYellow:
                # if found first pole but still finding yellow (without gap)
                if foundPole == True and gapFound == False:
                    continue
                # else, look to the left, then to the right
                while filteredYellow[y,x] > thresholdYellow:
                    x -= 1
                beginPole = x
                while filteredYellow[y,x] > thresholdYellow:
                    x += 1
                endPole = x
                # use the middle x
                x = beginPole + (endPole - beginPole) / 2
                # and go down to find the correct y - value
                for i in xrange( -1, -(stepsizeY-1), -1 ):
                    if filteredGreen[i, x] > thresholdGreen:
                        # if this is the second pole to be found
                        if gapFound:
                            secondPole = [x, y + i - 1]
                            doBreak = True
                            break
                        else:
                            firstPole = [x, y + i - 1]
                        foundPole = True
                        
                # dont look further up if a yellow pixel was found. 
                continue
            # else, if a pole was already found, and no yellow value is found, the gap between pole starts.
            elif foundPole:
                gapFound = True    
    
    poles = list()
    if secondPole:
        xPos2, yPos2, xAngle2, yAngle2 = calcPosition( secondPole, head, cam )
        dist2 = math.sqrt( xPos2 ** 2 + yPos2 ** 2 )
        poles.append( (xAngle2, dist2 ) ) 
    if firstPole:
        xPos1, yPos1, xAngle1, yAngle1 = calcPosition( firstPole, head, cam )    
        dist1 = math.sqrt( xPos1 ** 2 + yPos1 ** 2 )
        poles.append( (xAngle1, dist1 ) )
    else:
        poles.append( None ) 
    return poles
    
def calcPosition(coord, cam, head):
    """ calcPosition(coord, cam, head) -> 4d tuple with positions
    
    Calculate x,y position based on position in image and camera position.
    
    """ 
    width  = 320
    height = 240
    # coord with origin in the upperleft corner of the image
    (xCoord, yCoord) = coord
    # change the origin to centre of the image
    xCoord = -xCoord + width  / 2.0
    yCoord =  yCoord - height / 2.0
    # convert pixel coord to angle
    radiusPerPixelHeight = 0.00345833333
    radiusPerPixelWidth = 0.003325
    xAngle = xCoord * radiusPerPixelWidth    
    yAngle = yCoord * radiusPerPixelHeight
    # the position (x, y, z) and angle (roll, pitch, yaw) of the camera
    (x,y,z, roll,pitch,yaw) = cam
    # position of the ball where origin with position and rotation of camera
    # ballRadius = 0.0325 in meters
    ballDiameter = 0.065
    """
    
    NAOHEAD  -----------------
       |'-_   a                         a = pitchCam + pitchAngleInImage
       |   '-_ 
       |      '-_
    z  |         '-_                    z = height   - balldiameter
       |            '-_
       |               '-_
       |__________________'-_           x = z / tan( a )
     Base       x 

      
    NAOHEAD  -----------------
       |'-_   b                         b = yawAngleInImage
       |   '-_ 
       |      '-_                       x = known
    y  |         '-_                    
       |            '-_                 y = x * tan( b )
       |               '-_
       |__________________'-_ 
                x 

    Vector must be rotated along the z-axis (yaw) afterwards
    
     """    
    xPos = (z-ballDiameter) / tan(pitch + yAngle)
    yPos = tan(xAngle) * xPos
    # origin with position of camera and rotation of body
    xPos1 = cos(yaw)*xPos - sin(yaw)*yPos
    yPos1 = sin(yaw)*xPos + cos(yaw)*yPos
    # position of the ball where
    xPos1 += x
    yPos1 += y
    return (xPos1, yPos1, xAngle + head[0], yAngle + head[1])