'''
resolution      width, height
0               160, 120
1               320, 240
2               640, 480

colorSpace      type
0               kYuv
9               kYUV422
10              kYUV
11              kRGB
12              kHSY
13              kBGR

space           type
0               SPACE_TORSO
1               SPACE_WORLD
2               SPACE_NAO
'''


from naoqi import ALProxy
import Image

motion = ALProxy("ALMotion", "127.0.0.1", 9559)
cam = ALProxy("ALVideoDevice", "127.0.0.1", 9559)
# use the bottom camera
cam.setParam(18, 1)
cam.startFrameGrabber()
unsubscribe()

def unsubscribe():
    try:
        vidProxy.unsubscribe("python_GVM")
    except:
        pass

def subscribe():
        unsubscribe()
        # subscribe(gvmName, resolution={0,1,2}, colorSpace={0,9,10,11,12,13},
        #           fps={5,10,15,30}
        return cam.subscribe("python_GVM", 0, 11, 30)

def snapShot(nameId):
        ''' TODO: test accuracy of useSensorValues={True, False} '''
        useSensorValues = True
        #getPosition(name, space={0,1,2}, useSensorValues)
        camBottom = motion.getPosition('CameraBottom', 2, useSensorValues)
        head = motion.getAngles(["HeadPitch", "HeadYaw"], useSensorValues)
        # Make image
        shot = cam.getImageRemote(nameId)
        # Get image
        # shot[0]=width, shot[1]=height, shot[6]=image-data
        size = (shot[0], shot[1])
        picture = Image.frombuffer("RGB", size, shot[6], "raw", "BGR", 0, 1)
        return (picture, (camBottom, head))
