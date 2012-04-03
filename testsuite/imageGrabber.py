'''
Take snapshots and filter them for the testsuite
'''

from naoqi import ALProxy
import Image
import cv

vidProxy = ALProxy("ALVideoDevice", "127.0.0.1", 9559)
# use the bottom camera
vidProxy.setParam(18, 1)
vidProxy.startFrameGrabber()

def unsubscribe():
    try:
        vidProxy.unsubscribe("python_GVM")
    except:
        pass
    
def subscribe():
    unsubscribe()
    # subscribe(gvmName, resolution={0,1,2}, colorSpace={0,9,10,11,12,13},
    #           fps={5,10,15,30}
    return vidProxy.subscribe("python_GVM", 0, 11, 30)

# Vision ID
visionID = subscribe()
# METHODS FOR VISION

def snapShot(nameId):
    #getPosition(name, space={0,1,2}, useSensorValues)
    # Make image
    shot = vidProxy.getImageRemote(nameId)
    # Get image
    # shot[0]=width, shot[1]=height, shot[6]=image-data
    size = (shot[0], shot[1])
    picture = Image.frombuffer("RGB", size, shot[6], "raw", "BGR", 0, 1)
    return picture
    
def filter(im, (hMin,sMin,vMin), (hMax,sMax,vMax)):
    size = (160,120) # Size of the images
    hsvFrame = cv.CreateImage(size, cv.IPL_DEPTH_8U, 3)
    filter = cv.CreateImage(size, cv.IPL_DEPTH_8U, 1)
    # hsv-range
    hsvMin1 = cv.Scalar(hMin, sMin, vMin, 0)
    hsvMax1 = cv.Scalar(hMax, sMax, vMax, 0)
    cv.CvtColor(im, hsvFrame, cv.CV_BGR2HSV)
    cv.InRangeS(hsvFrame, hsvMin1, hsvMax1, filter)
    #opencv to pil
    pilFilter = Image.fromstring("L", cv.GetSize(filter), filter.tostring())
    return pilFilter
    
def convertImage(picture):
    ''' 
    As made by Michael Cabot
    converts a robot image into an OpenCV image
    INPUT:  picture, a robot taken snapshot
    OUTPUT: an OpenCV image
    '''
    global size
    size = (160, 120)
    # resize the image
    picture = picture.resize(size)
    # convert the type to OpenCV
    image = cv.CreateImageHeader(size, cv.IPL_DEPTH_8U, 3)
    cv.SetData(image, picture.tostring(), picture.size[0]*3)
    return image    
    
if __name__ == "__main__":
    print 'hi'
    im = snapShot("python_GVM")
    im.save("image.png")
    im = convertImage(im)
    filterIm = filter(im, (0, 55, 60), (120, 255, 255))
    # save images
    filterIm.save("filter.png")