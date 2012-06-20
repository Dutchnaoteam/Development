"""
File: LocateGoalzor.py
Author:  Justin van Zanten
"""
import cv
import math

def markGoalCV(im):
    """ 
    As made by Michael Cabot
    Image color filter, can be thresholded (70 recommended) to find 
    locations containing the calibrated color
    INPUT:  im, a [160-by-120] image needed to be filtered
            color, the filter color a string, can be "blue" or "yellow"
    OUTPUT: returns an OpenCV color filtered image with values of the 
            color match, values over a threshold of 70 are sugested
    """
    filtered = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)
    
    """
    --------------------------------------------------------
    Goalfilter values (made in Istanbul 06/07/2011)
    if(color == "blue"):
        hueMin = 116
        hueMax = 130
        saturationMin = 117 
        saturationMax = 255 
        valueMin = 134 
        valueMax = 210
    if(color == "yellow"):
        hueMin = 20 
        hueMax = 41 
        saturationMin = 100 
        saturationMax = 255
        valueMin = 60
        valueMax = 210 
    ---------------------------------------------------------
    Goalfilter values made in Eindhoven 04/2012
    if(color == "blue"):
        hueMin = 106
        hueMax = 113
        saturationMin = 204 
        saturationMax = 255 
        valueMin = 119 
        valueMax = 197
    """
    
    # GoalFilter values yellow RoboW 05/2012:    
    hueMin = 29
    hueMax = 37 
    saturationMin = 106 
    saturationMax = 220
    valueMin = 105
    valueMax = 255 
    hsvMin = cv.Scalar(hueMin, saturationMin, valueMin, 0)
    hsvMax = cv.Scalar(hueMax, saturationMax, valueMax, 0)
    cv.InRangeS(im, hsvMin, hsvMax, filtered)
    
    return filtered
    
def calcXangle(xcoord):
    """
    As made by Michael Cabot
    calculates the angle towards a location in an image
    INPUT:  xcoord, a x coordinate in a [320-by-240] image
    OUTPUT: returns the angle to the x coordinate with the middle of
    the image being 0 degrees
    """
    (width, height) = (320, 240)
    xDiff = width / 2.0 - xcoord
    distanceToFrame = 0.5 * width / 0.42860054745600146
    xAngle = math.atan(xDiff/distanceToFrame)
    return xAngle

def convertImage(picture):
    """ 
    As made by Michael Cabot
    converts a robot image into an OpenCV image
    INPUT:  picture, a robot taken snapshot
    OUTPUT: an OpenCV image
    """
    global size
    size = (320, 240)
    # resize the image
    picture = picture.resize(size)
    # convert the type to OpenCV
    image = cv.CreateImageHeader(size, cv.IPL_DEPTH_8U, 3)
    cv.SetData(image, picture.tostring(), picture.size[0]*3)
    return image    
    
def run(image, yawHead ):
    """
    Recognizes poles of a color with a minimum lenght of 20 pixels
    INPUT:  image, a [160-by-120] image needed to be filtered
            yawHead, the Robot Head Yaw, to make the angle absolute
            color, the filter color a string, can be "blue" or "yellow"
    OUTPUT: returns a tuple (x, y) containing to angles for the best two
            poles. (None,None) is given if poles are missing
            At one missing pole (angle, None) will be returned
            (None, angle) will never be returned.
    """

    # Filter an image based on color.
    #image = convertImage(image)
    #cv.SaveImage("raw" + str(time.time()) +  ".jpg", image)
    image = markGoalCV(image )
    #cv.SaveImage("filter" + color + str(time.time()) +  ".jpg", image)
    cv.Smooth(image, image, cv.CV_GAUSSIAN, 5,5)
    
    threshold = 70   # threshold for the grayscale
    (width, height) = cv.GetSize(image) # resolution of the input images
    
    #######################ALGORITHMICDIVISION#######################
    
    # Form a dict of vertical lines.
    lines = {}
    for x in xrange(width):                                              # for every vertical line
        
        checker = False
        for y in xrange(10,height,10):                                   # iterate from top down steps of ten pixels (start at ten)
            if (image[y,x] > threshold):                                 # when a true pixel is found 
                ry = y - 9                                               # go back nine pixels
                while(image[ry,x] <= threshold):                         # start iterating by one pixel until a true pixel is found
                    ry += 1
                checker = False
                
                # count until 30 pixels are found in a row or until a false pixel is found
                for checky in xrange(ry, min(ry + 20, height)):   
                    if (image[checky,x] <= 70):
                        break
                    elif (checky == ry+19):
                        checker = True
            if checker: 
                break
        if checker:               # when a line of true pixels is found do the same from the bottom up
            for by in xrange(height-10,0,-10):                  # iterate from top down steps of ten pixels (start at ten)
                if (image[by,x] > threshold):                   # when a true pixel is found 
                    bry = by + 9                                # go back nine pixels
                    while(image[bry,x] <= threshold):           # start iterating by one pixel until a true pixel is found
                        bry = bry - 1
                    checker = False
                    for checky in xrange(max(bry - 20,0), bry):    # count until 15 pixels in this column are found or until a false pixel is found
                        if (image[checky,x] <= 70):
                            break
                        elif checky == bry - 19 or checky == ry:   # also stop if lines overlap 
                            checker = True
                            
                    if (checker):                               # if bottom up searching goes past the starting pixel: Im an idiot
                        lines[x] = (ry, bry)                    # remember starting and ending pixel
                        
                                                                # when a false pixel is found retry at the last known pixel (ten further)
    # IN CONCLUSION: A line on x has at least 10 pixels of yellow color
    
    #######################ALGORITHMICDIVISION#######################
      
    # Group the veritcal lines together.
    sortedlines = sorted(lines.keys())
    currentBlob = "empty"
    upperline = 0
    underline = 0
    # initiate top two maximum values
    Max = None
    NotQuiteAsMax = None
    posMax = None
    posNotQuiteAsMax = None
    
    for i in xrange(len(lines)-1):                                      # iterate from left to right (only where a line is found)
        if (currentBlob == "empty"):                                    # remember first line
            currentBlob = "full"
            underline = sortedlines[i]
        left = sortedlines[i]
        right = sortedlines[i+1]
        
        (leftTop,leftBot) = lines[left]
        (rightTop,rightBot) = lines[right]
        
        # if 2 lines are directly connected
        if right - left == 1 and not (leftBot<rightTop or  rightBot<leftTop):
            upperline = sortedlines[i+1]                                # find the most outer line attached to the first line
        # if they are separated    
        else:
            if upperline - underline > 3:                               # remember that one
                pos = (upperline + underline)/2
                dif = upperline - underline                             # and the difference between the two
                if (dif > NotQuiteAsMax):                               # save it if its greater than the others found
                    if (dif > Max):
                        posNotQuiteAsMax = posMax
                        NotQuiteAsMax = Max
                        posMax = pos
                        Max = dif
                    else:
                        posNotQuiteAsMax = pos
                        NotQuiteAsMax = dif
            currentBlob = "empty"                                       # repeat for the next line found
    if ((upperline - underline) > 3):                                   # when passed through all the lines, save the last ()
        pos = (upperline + underline)/2                                 # if its greater than the others found
        dif = upperline - underline
        
        if (dif > NotQuiteAsMax):
            if (dif > Max):
                posNotQuiteAsMax = posMax
                NotQuiteAsMax = Max
                posMax = pos
                Max = dif
            else:
                posNotQuiteAsMax = pos
                NotQuiteAsMax = dif
    
    #######################ALGORITHMICDIVISION#######################
    
    # convert pixelwidth to actual width, which is 0.07 metres 
    
    
    # return angles to the found positions
    tuplepart1 = None                                                  # calculate the angles to the position of the two found poles
    if posNotQuiteAsMax:
        tuplepart1 = calcXangle(posNotQuiteAsMax) + yawHead, pixelsToMeters( NotQuiteAsMax )
    tuplepart2 = None
    if posMax:
        tuplepart2 = calcXangle(posMax)  + yawHead, pixelsToMeters( Max )
    if tuplepart1 or tuplepart2:
        return [tuplepart2, tuplepart1] # (closest, furthest)         # return the angles
    else:
        return [None]
        
def pixelsToMeters( pixels ):
    radiusPerPixelWidth = 0.003325
    pixels /= 2.0
    angle = pixels * radiusPerPixelWidth
    return 0.05 / math.tan( angle )
    
    
