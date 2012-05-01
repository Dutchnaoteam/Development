'''
convertImage
filter
blur
minMax
if maxValue < x:
    return None
calculatePosition
return (xPos, yPos, xAngle, yAngle)


TODO wx to pil to cv
kunnen aanvinken welke filter technieken je wil gebruiken
test nieuwe manier van foto's nemen (zou sneller moeten zijn)
    direct AL-->CV ipv AL-->PIL-->CV
'''

import cv
import wx
import Image
from math import *
from naoqi import ALProxy
import time
import os


class VisionTestTools:  
    def saveImage(self, image, name):
        # TODO
        # find out the type
        # and call one of the functions below
        pass
        
    def saveImagePil(self, pilImage, name):
        pilImage.save(name)
        
    def saveImageWx(self, wxImage, name):
        name, extension = os.path.splitext(name)
        wxImage.SaveFile(name, extension)
        
    def saveImageCv(self, cvImage, name):
        cv.SaveImage(name, cvImage)
     
    def pilToCv(self, pilImage):
        size = pilImage.size
        cvImage = cv.CreateImageHeader(size, cv.IPL_DEPTH_8U, 3)
        cv.SetData(cvImage, pilImage.tostring(), pilImage.size[0]*3)
        return cvImage
        
    def pilToWx(self, pilImage):
        wxImage = wx.EmptyImage(pilImage.size[0], pilImage.size[1])
        wxImage.SetData(pilImage.convert("RGB").tostring())
        wxImage.SetAlphaData(pilImage.convert("RGBA").tostring()[3::4])
        return wxImage
    
    #TODO fix          
    def cvFilterToWx(self, cvFilter):
        (widht, height) = size = cv.GetSize(cvFilter)
        cvImage = cv.CreateImage(size, cv.IPL_DEPTH_8U, 3)
        cv.CvtColor(cvFilter, cvImage, cv.CV_GRAY2RGB)        
        wxImage = wx.EmptyImage(widht, height)
        wxImage.SetData(cvImage.tostring())
        return wxImage
  
    def wxToCv(self, wxImage):
        cvImage = cv.CreateImageHeader(wxImage.GetSize(), cv.IPL_DEPTH_8U, 3)
        cv.SetData(cvImage, wxImage.GetData(), wxImage.GetWidth()*3)
        cv.CvtColor(cvImage, cvImage, cv.CV_RGB2BGR)
        return cvImage

    def filterImage(self, im, hsvMin, hsvMax):
        hsvFrame = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 3)
        filter = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)
        cv.CvtColor(im, hsvFrame, cv.CV_BGR2HSV)
        cv.InRangeS(hsvFrame, hsvMin, hsvMax, filter)
        return filter
        
    def filterImageBgr(self, im, bgrMin, bgrMax):
        #hsvFrame = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 3)
        filter = cv.CreateImage(cv.GetSize(im), cv.IPL_DEPTH_8U, 1)
        #cv.CvtColor(im, hsvFrame, cv.CV_BGR2HSV)
        cv.InRangeS(im, bgrMin, bgrMax, filter)
        return filter
        
    def floodFill(self, image):
        (width, height) = cv.GetSize(image)
        #mask = cv.CreateImage((width+2,height+2), cv.IPL_DEPTH_8U, 1)
        #(area, value, rect) = cv.FloodFill(image, (0,0), cv.Scalar(0), cv.Scalar(0), cv.Scalar(0), 4, mask)
        diff = 100
        (area, value, rect) = cv.FloodFill(image, (80,60), cv.Scalar(0), cv.Scalar(diff), cv.Scalar(diff))
        print 'area', area
        print 'value', value
        print 'rect', rect
        #self.saveImageCv(mask, 'mask.png')
        self.saveImageCv(image, 'floodFill.png')

    def boundedBox(self, im_filter, im_orig):
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
        
    def calcPosition(self, coord, cam, headInfo):
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
        dtf = 135.9 # distance to frame
        xAngle = atan( xCoord / dtf )
        yAngle = atan( yCoord / dtf )
        if -1 < xAngle < 1 and -1 < yAngle < 1:
            yAngle = -0.47 - headInfo[0] if yAngle + headInfo[0] < -0.47 else yAngle
            motion.changeAngles(['HeadPitch', 'HeadYaw'], [0.3*yAngle, 0.3*xAngle], 0.7)  # 0.3*angles for smoother movements, optional. Smoothinggg. 

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

class VisionTools(VisionTestTools):
    def __init__(self, ip, vmName):
        self.ip = ip
        self.vmName = vmName
        self.vidProxy = ALProxy("ALVideoDevice", self.ip, 9559)        

    def unsubscribe(self):
        try:
            self.vidProxy.unsubscribe(self.vmName)
        except:
            pass

    def subscribe(self, imageResolution, imageColorSpace, imageFps):
        self.unsubscribe()
        return self.vidProxy.subscribe(self.vmName, imageResolution, imageColorSpace, imageFps)
        
    def setParam(self, param, value):
        self.vidProxy.setParam(param, value)
    
    def startFrameGrabber(self):
        self.vidProxy.startFrameGrabber()
        
    def stopFrameGrabber(self):
        self.vidProxy.stopFrameGrabber()
        
    def getImage(self):
        shot = self.vidProxy.getImageRemote(self.vmName)
        # shot[0]=width, shot[1]=height, shot[6]=image-data
        size = (shot[0], shot[1])
        picture = cv.CreateImageHeader(size, cv.IPL_DEPTH_8U, 3)
        cv.SetData(picture, picture.tostring(), picture.size[0]*3)
        return picture