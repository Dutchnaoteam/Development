'''
convertImage
filter
blur
minMax
if maxValue < x:
    return None
calculatePosition
return (xPos, yPos, xAngle, yAngle)

height of image is 240
angle of image in height is 47.80 degrees
radians per pixel in height is 0.834267382 radians
radians per pixel = 0.83 / 240 = 0.00345833333   

width of image is 320
angle of image in width is 60.97 degrees
radians per pixel in width is 1.064 radians
radians per pixel = 1.064 / 320 = 0.003325   
'''
import time
import cv
from math import tan, cos, sin
from naoqi import ALProxy
motion = ALProxy("ALMotion", "127.0.0.1", 9559)

size = None

""" returns x,y position as a tuple

Calculates the position of the ball based on position of the camera and 
an image. Returns none if no ball found.

""" 
def run(im, headInfo, track ):
    (cam, head) = headInfo
    # convert the image 
    im = convertImage(im)

    #use filterGreen to take only the image
    green_thresh = filterGreen(im)

    im = boundedBox(green_thresh, im)
    #cv.SaveImage( str(time.time()) +  '.jpg', im)
    
    # filter the image
    im = filterImage(im)
    #cv.SaveImage('filter' + str(time.time()) +  '.jpg', im)
    # blur the image
    cv.Smooth(im, im, cv.CV_BLUR, 4, 4)
    # find the max value in the image    
    (_, maxValue, _, maxLocation) = cv.MinMaxLoc(im)
    #print maxValue/256.0
    
    # if the maxValue isn't hight enough return 'None'
    if maxValue/256.0 < 0.4:
        return None
    
    # if tracking
    if track:
        # else, finish head tasks
        motion.killTasksUsingResources( ['HeadYaw', 'HeadPitch'] )
    
    # calculate the angles to the ball
    #(xAngle, yAngle) = calcAngles((xcoord, ycoord ), cam)
    # calculate the position of the ball
    position = calcPosition(maxLocation, cam, head, track)
    (xPos, yPos, _, _) = position
    
    return (xPos, yPos)

def calcPosition(coord, cam, headInfo, track):
    """ calcPosition(coord, cam, headInfo) -> 4d tuple with positions
    
    Calculate x,y position based on position in image and camera position.
    
    """
    (width, height) = size
    #print 'size: ', width, ', ', height
    # coord with origin in the upperleft corner of the image
    (xCoord, yCoord) = coord
    #print 'pixelCoord from upperLeft: ', xCoord, ', ', yCoord
    # change the origin to centre of the image
    xCoord = -xCoord + width/2.0
    yCoord = yCoord - height/2.0
    #print 'pixelCoord from centre: ', xCoord, ', ', yCoord
    # convert pixel coord to angle
    radiusPerPixelHeight = 0.00345833333
    radiusPerPixelWidth = 0.003325
    xAngle = xCoord * radiusPerPixelWidth    
    yAngle = yCoord * radiusPerPixelHeight
    if track:
        if -1 < xAngle < 1 and -1 < yAngle < 1:
            yAngle = -0.47 if yAngle + headInfo[0] < -0.47 \
                                         else yAngle
            motion.changeAngles(['HeadPitch', 'HeadYaw'], \
                                [0.3*yAngle, 0.3*xAngle], 0.7)
                                # 0.3*angles for smoother movements, optional. 

    # the position (x, y, z) and angle (roll, pitch, yaw) of the camera
    (x,y,z, roll,pitch,yaw) = cam
    
    # position of the ball where origin with position and rotation of camera
    # ballRadius = 0.0325 in meters
    ballDiameter = 0.065
    xPos = (z-ballDiameter) / tan(pitch + yAngle)
    yPos = tan(xAngle) * xPos
    # position of the ball where
    #  origin with position of camera and rotation of body 
    xPos1 = cos(yaw)*xPos + -sin(yaw)*yPos
    yPos1 = sin(yaw)*xPos +  cos(yaw)*yPos
    # position of the ball where
    #  origin with position and rotation of body
    xPos1 += x
    yPos1 += y
    return (xPos1, yPos1, xAngle, yAngle)

"""Convert image to cv Format"""
def convertImage(picture):
    global size
    size = picture.size
    # convert the type to OpenCV
    image = cv.CreateImageHeader(size, cv.IPL_DEPTH_8U, 3)
    cv.SetData(image, picture.tostring(), picture.size[0]*3)
    return image

def filterImage(im):
    """Filter a cv image for the correct color"""
    # Size of the images
    (width, height) = size
    
    hsvFrame = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 3)
    filtered = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)
    #filter2 = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)
    
    # Values Iran 4/2012
    #hsvMin1 = cv.Scalar(4,  140,  140, 0)
    #hsvMax1 = cv.Scalar(9,  255,  256, 0)
    
    # Values Eindhoven 4/2012
    #hsvMin1 = cv.Scalar(4,  109,  142, 0)
    #hsvMax1 = cv.Scalar(14,  230,  255, 0)
    
    # Values RoboW 2012 day 1
    hsvMin1 = cv.Scalar(12,  158, 213, 0)
    hsvMax1 = cv.Scalar(20,  255, 255, 0)

    # Values RoboW 2012 day 2
    hsvMin1 = cv.Scalar(9,   146, 167, 0)
    hsvMax1 = cv.Scalar(17,  255, 255, 0)

    # Color detection using HSV
    cv.CvtColor(im, hsvFrame, cv.CV_BGR2HSV)
    cv.InRangeS(hsvFrame, hsvMin1, hsvMax1, filtered)
    #cv.InRangeS(hsvFrame, hsvMin2, hsvMax2, filter2)
    #cv.Or(filter, filter2, filter)
    return filtered


def filterGreen(im):
    """filterGreen(im) -> single-channel IplImage

    Thresholds an image for the color green
    """
    size = cv.GetSize(im)
    hsvFrame = cv.CreateImage(size, cv.IPL_DEPTH_8U, 3)
    filtered = cv.CreateImage(size, cv.IPL_DEPTH_8U, 1)
    ####################
    # filters for green# 

    # Iran values 4/2012
    #hsvMin1 = cv.Scalar(60,  3,  90, 0)
    #hsvMax1 = cv.Scalar(100,  190,  210, 0)
    
    # Eindhoven values 4/2012 Aanpassen Tijmen
    # hsvMin1 = cv.Scalar(46,  94,  89, 0)
    # hsvMax1 = cv.Scalar(75,  204,  212, 0)
    
    # RoboW values 
    hsvMin1 = cv.Scalar(50, 51,  66, 0)
    hsvMax1 = cv.Scalar(90, 199, 255, 0)

    # Color detection using HSV
    cv.CvtColor(im, hsvFrame, cv.CV_BGR2HSV)
    cv.InRangeS(hsvFrame, hsvMin1, hsvMax1, filtered)

    return filtered

def boundedBox(im_filter, im_orig):
    """ boundedBox(im_filter, im_orig) -> im_orig
    
    calculates a bounding box around the white pixels of a
    single-channel thresholded image and sets it as ROI on
    the original image
    
    """
    bbox = cv.BoundingRect(cv.GetMat(im_filter))

    # checking if a box is found
    _, _, width, height = bbox
    if width < (im_orig.width / 2.0) or height < (im_orig.height / 2.0):
        return im_orig

    cv.SetImageROI(im_orig, bbox)
    return im_orig