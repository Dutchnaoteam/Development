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

height of image is 320
angle of image in height is 60.97 degrees
radians per pixel in height is 1.064 radians
radians per pixel = 1.064 / 320 = 0.003325   
'''

import cv
from math import *
size = None
from naoqi import ALProxy
motion = ALProxy("ALMotion", "127.0.0.1", 9559)
import time

def run(im, headInfo):
    (cam, head) = headInfo
    # convert the image 
    im = convertImage(im)

    #use filterGreen to take only the image
    green_thresh = filterGreen(im)

    im = boundedBox(green_thresh, im)
    # filter the image
    im = filterImage(im)
    #cv.SaveImage('filter' + str(time.time()) +  '.jpg', im)
    # blur the image
    cv.Smooth(im, im, cv.CV_BLUR, 2, 2)
    # find the max value in the image    
    (minVal, maxValue, minLoc, maxLocation) = cv.MinMaxLoc(im)
    #print maxValue/256.0
    
    # if the maxValue isn't hight enough return 'None'
    if maxValue/256.0 < 0.4:
        return None
    
    # else, finish head tasks
    motion.killTasksUsingResources( ['HeadYaw', 'HeadPitch'] )
    
    # calculate the angles to the ball
    #(xAngle, yAngle) = calcAngles((xcoord, ycoord ), cam)
    # calculate the position of the ball

    # we need to compensate for the ROI being set
    x_pos, y_pos = maxLocation
    x_off, y_off, _, _ = cv.GetImageROI(im)

    position = calcPosition((x_pos + x_off, y_pos + y_off), cam, head)
    (xPos, yPos, xAngle, yAngle) = position
    
    #print position
    #track(position)
    return (xPos, yPos)

def calcPosition(coord, cam, headInfo):
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
    xAngle = (xCoord +0.5) * radiusPerPixelWidth    
    yAngle = (yCoord+ 0.5) * radiusPerPixelHeight
    if -1 < xAngle < 1 and -1 < yAngle < 1:
        yAngle = -0.47 - headInfo[0] if yAngle + headInfo[0] < -0.47 else yAngle
        motion.changeAngles(['HeadPitch', 'HeadYaw'], [0.1*yAngle, 0.1*xAngle], 0.7)  # 0.3*angles for smoother movements, optional. Smoothinggg. 
        #motion.changeAngles(['HeadPitch', 'HeadYaw'], [0.3*yAngle, 0.3*xAngle], 0.7)  # 0.3*angles for smoother movements, optional. Smoothinggg. 

    #print 'angle from camera: ' + str(xAngle) + ', ' + str(yAngle)

    # the position (x, y, z) and angle (roll, pitch, yaw) of the camera
    (x,y,z, roll,pitch,yaw) = cam
    #print 'cam: ', cam

    # the pitch has an error of 0.940063x + 0.147563
    # print 'correctedPitch: ', pitch
    
    # position of the ball where
    # origin with position and rotation of camera
    #ballRadius = 0.0325     # in meters
    ballRadius = 0.065
    xPos = (z-ballRadius) / tan(pitch + yAngle)
    yPos = tan(xAngle) * xPos
    #print 'position from camera: ', xPos, ', ', yPos
    # position of the ball where
    #  origin with position of camera and rotation of body 
    xPos = cos(yaw)*xPos + -sin(yaw)*yPos
    yPos = sin(yaw)*xPos +  cos(yaw)*yPos
    # position of the ball where
    #  origin with position and rotation of body
    xPos += x
    yPos += y
    #print 'position ball: ', xPos, ', ', yPos
    #print 'new yaw/pitch: ', xAngle+yaw, yAngle+pitch
    #print 'z / tan(pitch): ',(z-ballRadius) / tan(pitch)
    return (xPos, yPos, xAngle, yAngle)
    
def convertImage(picture):
    global size
    size = picture.size
    # convert the type to OpenCV
    image = cv.CreateImageHeader(size, cv.IPL_DEPTH_8U, 3)
    cv.SetData(image, picture.tostring(), picture.size[0]*3)
    return image

def filterImage(im):
    # Size of the images
    (width, height) = size
    
    hsvFrame = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 3)
    filter = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)
    #filter2 = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)
    
    # Values Iran 4/2012
    #hsvMin1 = cv.Scalar(4,  140,  140, 0)
    #hsvMax1 = cv.Scalar(9,  255,  256, 0)
    
    # Values Eindhoven 4/2012
    # TODO AANPASSEN TIJMEN
    #hsvMin1 = cv.Scalar(4,  109,  142, 0)
    #hsvMax1 = cv.Scalar(14,  230,  255, 0)

    #Red values Mexico
    hsvMin1 = cv.Scalar(5, 174, 137)
    hsvMax1 = cv.Scalar(23, 238, 255)
    
    #hsvMin2 = cv.Scalar(170,  90,  130, 0)
    #hsvMax2 = cv.Scalar(200, 256, 256, 0)

    # Color detection using HSV
    cv.CvtColor(im, hsvFrame, cv.CV_BGR2HSV)
    cv.InRangeS(hsvFrame, hsvMin1, hsvMax1, filter)
    #cv.InRangeS(hsvFrame, hsvMin2, hsvMax2, filter2)
    #cv.Or(filter, filter2, filter)
    return filter

def filterGreen(im):
    """filterGreen(im) -> single-channel IplImage

    Thresholds an image for the color green
    """
    size = cv.GetSize(im)
    hsvFrame = cv.CreateImage(size, cv.IPL_DEPTH_8U, 3)
    filter = cv.CreateImage(size, cv.IPL_DEPTH_8U, 1)
    filter2 = cv.CreateImage(size, cv.IPL_DEPTH_8U, 1)
    filter3 = cv.CreateImage(size, cv.IPL_DEPTH_8U, 1)
    ####################
    # filters for green# 

    # Iran values 4/2012
    #hsvMin1 = cv.Scalar(60,  3,  90, 0)
    #hsvMax1 = cv.Scalar(100,  190,  210, 0)
    
    #Eindhoven values
    #hsvMin1 = cv.Scalar(46,  94,  89, 0)
    #hsvMax1 = cv.Scalar(75,  204,  212, 0)

    #Mexico values
    hsvMin1 = cv.Scalar(49,  55,  40, 0)
    hsvMax1 = cv.Scalar(91,  158,  105, 0)

    hsvMin2 = cv.Scalar(0,  0,  18, 0)
    hsvMax2 = cv.Scalar(90,  149,  41, 0)

    # Color detection using HSV
    cv.CvtColor(im, hsvFrame, cv.CV_BGR2HSV)
    cv.InRangeS(hsvFrame, hsvMin1, hsvMax1, filter)
    cv.InRangeS(hsvFrame, hsvMin1, hsvMax1, filter2)
    cv.Or(filter, filter2, filter3)
    return filter3

def boundedBox(im_filter, im_orig):
    """ boundedBox(im_filter, im_orig) -> im_orig
    
    calculates a bounding box around the white pixels of a
    single-channel thresholded image and sets it as ROI on
    the original image"""
    bbox = cv.BoundingRect(cv.GetMat(im_filter))

    # checking if a box is found
    _, _, width, height = bbox
    if width < (im_orig.width / 2.0) or height < (im_orig.height / 2.0):
        return im_orig

    cv.SetImageROI(im_orig, bbox)
    return im_orig

def zero(m,n):
    new_matrix = [[0 for row in range(n)] for col in range(m)]
    return new_matrix
 
def show(matrix):
    # Print out matrix
    for col in matrix:
        print(col) 
 
def mult(matrix1,matrix2):
    # Matrix multiplication
    if len(matrix1[0]) != len(matrix2):
        # Check matrix dimensions
        print('Matrices must be m*n and n*p to multiply!')
    else:
        # Multiply if correct dimensions
        new_matrix = zero(len(matrix1),len(matrix2[0]))
        for i in range(len(matrix1)):
            for j in range(len(matrix2[0])):
                for k in range(len(matrix2)):
                    new_matrix[i][j] += matrix1[i][k]*matrix2[k][j]
        return new_matrix
            
# form a rotation translation matrix            
def rtmatrix(rotation, translation):
    [a1, a2, a3] = rotation # 1 = roll 2 = pitch 3 = yaw
    [t1, t2, t3] = translation # xyz
    # calculate the transformation matrix 
    matrix = [[math.cos(a1) * math.cos(a3) - math.sin(a1) * math.cos(a2) * math.sin(a3), 
               -math.sin(a1) * math.cos(a3) - math.cos(a1) * math.cos(a2) * math.sin(a3),
               math.sin(a2) * math.sin(a3), t1 ],
              [math.cos(a1) * math.sin(a3) + math.sin(a1) * math.cos(a2) * math.cos(a3), 
              -math.sin(a1) * math.sin(a3) + math.cos(a1) * math.cos(a2) * math.cos(a3),
              -math.sin(a2) * math.cos(a3), t2 ],
              [math.sin(a1) * math.sin(a2), math.cos(a1) * math.sin(a2) , math.cos(a2) , t3 ],[0,0,0,1]]
    return matrix
