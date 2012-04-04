'''
TO DO:
*Needs a filter that takes t-splisting out of the list if a corner is to close by
*More testing on variable pitches of Nao head (the idea: the higher the pitch the smaller
    the thresholds, smaller maxGap for a line etc. ) danger!!! to small will find lines in
    in Nao's
*Filter 1st for green field, and only keep track of lines that are in the region of this
    green field 
*fix in cornersTsplits() that when a corner is found what the angle is
   

About:
LineCorners finds lines and the corners and tJunctions between these lines.

run() --  Main function calls all the functions.
          Possible to return List of Corners, Tjunctions and Lines
          
setGlobals(pitch) -- Sets the globals so they change per pitch and lines found will be
        more accurate
        
dotLines() -- Reads the list of found Corners and Tjunctions and shows these in a new image(scribble)
   
calcXangle() -- gives you the oritation of a x coordinate on the image in alligmend to the
        nao's body
        
cornersTsplits() 'aka Magic' -- in the lines found with houghlines 1st check all the coordinates
        off the lines with each other to see if they form a corner. If so check if there is a corner
        near by and ifso take the average between them for you new corner. If its not a corner check
        if its a Tjunction. By using findTsplitsing() if line2 has a to big distance to line 1 
        switch them around so if the minimale distand is than short enough to be a tjunction. Again
        check if there is no tjunction close by if so take the avarge.
        Returns a list of corners and Tjunctions
        
findTsplitsing() -- look for smallest distance between 2 lines by projection 1 line on the other
            returns coordinates off where the projection off the smallest distance would be
            
markFieldW() -- filters the image on RGB values of white
            Returns White filter Image
            
getLines() -- Use houghlines to find all the lines in White filter Image
                Returns: List of lines, all lines consist of 2 xy coordinates ((x1,y1),(x2,y2))
                
filterLines() -- Filters a lines on angle's, than checks if a angle is already in the list.
        If so find if a line belongs together by checking its smallest Distance. If so use mergLines()
        to merge these lines together. If not its a diffrent line and put it second list. Do this for
        all lines. Same goes for the second list keep track if lines with same angle are the same line.

mergeLines() -- mergeLines that are the same. by finding the longest new Line between the coordinates
        of the old lines.
        
'''
from naoqi import ALProxy

import cv
import Image
import motions

from math import*
motionProxy = ALProxy("ALMotion", "localhost", 9559)
camProxy = ALProxy("ALVideoDevice", "localhost", 9559)
camProxy.setParam(18, 1)
subscribe = None

global cvCreateMemStorage

#change hough'stuff' to change the rate of lines you finf in a whitefilter image
global houghRho 
global houghThres
global houghMinLine 
global houghMaxGap 
#absDistanceMerge is the pixel distance between lines that are allowed to merge
global absDistMerge 
#max range for corners to be allowed to be around other cornes
global rangeCorner 
#max dist between 2 possible lines to be considerd Tsplitsing
global minAbsDistT 
global mergeAngleLines

def pKeep((image, headinfo)):
    #global subscribe
    #camProxy.unsubscribe("python_GVM")
	#2 = 640
	#1 = 320
	#0 = 160
    # subscribe to the camera	
    #subscribe = camProxy.subscribe("python_GVM",0,11,5)
    (_, head) = headinfo
    
    [headPitch , headYaw] = head
    #cam = motionProxy.getPosition('CameraBottom', 2, True)
    #print head
    setGlobals(headPitch)
    # get the filtered image for the given colour
    image = markFieldW('white')
    # get the lines
    lines = getLines(image)
    hough = scribble(lines)
    cv.SaveImage("hough.jpg", hough)

    lines = filterLines(lines)
    final = scribble(lines)
    #print "test lines"
   # print lines
    cv.SaveImage("final.jpg", final)
    return lines, headYaw



def setGlobals(pitch):
    global houghRho 
    global houghThres
    global houghMinLine 
    global houghMaxGap 
    global absDistMerge 
    global rangeCorner 
    global minAbsDistT 
    global mergeAngleLines
    
    if ( pitch >= -0,486 and pitch <= -0,286):
        #change hough'stuff' to change the rate of lines you finf in a whitefilter image
        houghRho = 2.1
        houghThres = 65
        houghMinLine = 9
        houghMaxGap = 15
        #absDistanceMerge is the pixel distance between lines that are allowed to merge
        absDistMerge = 30
        #max range for corners to be allowed to be around other cornes
        rangeCorner = 12
        #max dist between 2 possible lines to be considerd Tsplitsing
        minAbsDistT = 5
           #stepSize = 0.261799 = 15 degrees
        mergeAngleLines = 0.261799 *1.25
 
    
    if ( pitch >= -0,286 and pitch <= 0):
        #change hough'stuff' to change the rate of lines you finf in a whitefilter image
        houghRho = 2.4
        houghThres = 60
        houghMinLine = 9
        houghMaxGap = 15
        #absDistanceMerge is the pixel distance between lines that are allowed to merge
        absDistMerge = 30
        #max range for corners to be allowed to be around other cornes
        rangeCorner = 12
        #max dist between 2 possible lines to be considerd Tsplitsing
        minAbsDistT = 5
        mergeAngleLines = 0.261799 *2
  

##############################################################
#           MAIN METHOD
#               run()
##########################        
def run():
    global subscribe
    try:
        camProxy.unsubscribe("python_GVM")
    except:
        pass
	#2 = 640
	#1 = 320
	#0 = 160
    # subscribe to the camera	
    subscribe = camProxy.subscribe("python_GVM",0,11,5)
    [headPitch , headYaw] = motionProxy.getAngles(["HeadPitch","HeadYaw"], True)
    cam = motionProxy.getPosition('CameraBottom', 2, True)
    #print head
    setGlobals(headPitch)
    # get the filtered image for the given colour
    image = markFieldW('white')
    # get the lines
    lines = getLines(image)
    maxlines = 0 
    maxpoint = ((), ())
    for i in lines:
        if( (i[0][0] - i[1][0])**2  + (i[1][0] -
            i[1][0])**2 > maxlines ):
            maxlines =  (i[0][0] - i[1][0])**2  + (i[1][0] -i[1][0])**2 

            maxpoint = ((i[0][0], i[0][1]), (i[1][0],
                i[1][1]))
    hough = scribble(maxpoint)
    
    #find function through maxpoints
    (a,b)= findFunction(maxpoint)
    print 'a en b'
    print a
    print b
    keeperTurn(a)
    cv.SaveImage("hough.jpg", hough)

    lines = filterLines(lines)
    final = scribble(lines)
    #print "test lines"
   # print lines
    cv.SaveImage("final.jpg", final)
    #corners, tSplitsing = cornersTsplits(lines)
    #print "corners", corners
   # print "tSplitsing", tSplitsing
    #corners.extend(tSplitsing)
    #foundCorners = dot([corners, tSplitsing])
    #cv.SaveImage("foundCorners.jpg", foundCorners)
    
    #scribble = probFindLines(lines)
    # find the corners
    #findCorners(scribble)
    #camProxy.unsubscribe(subscribe)  
    #return [corners, tSplitsing, cam]

def findFunction(point_tuple):
    a = point_tuple[1][1]- point_tuple[0][1] / point_tuple[1][0] - point_tuple[0][0]
    b = -a * point_tuple[0][0] + point_tuple[0][1]
    return (a,b)

# keeperTurn uses the RC to determin which side to move to
def keeperTurn(rc):
    # determin when nao isn't looking straight at the line
    while(rc < -0.5 or rc >0,5):
        #turning of the nao.. Must still be calculated!!!!!
        if(rc > 0):
            motions.walkTo(0,0 , math.pi/4 ) 
        else:
            motions.walkTo(0 ,0 ,-math.pi/4 )
            allpoints= allpoints()
            max =  maxpoints( )
            (rc, b)

def allpoints():

def maxpoints():

        


def dot(stuff):
    [corners, Tsplits] = stuff
    size = (160, 120)
    #object to draw on
    scribble = cv.CreateImage(size, cv.IPL_DEPTH_64F, 1)
    ##print len(lines)
    for (x,y,angle, line1, line2) in corners:
        #print 'draw corner', x,y, angle
        newX = cos(angle) * 25 + x
        newY = sin(angle) * 25 + y
        cv.Circle(scribble, (x,y),2, (255,255,1), 2, 0)
        cv.Line(scribble, (x,y),(int(newX),int(newY)), (255,255,1), 1, 0)
        
    for (x,y, angle) in Tsplits:
       # print "draw Tsplit", x, y, angle
        newX = cos(angle) * 25 + x
        newY = sin(angle) * 25 + y
        cv.Circle(scribble, (x,y),2, (255,255,1), 3, 0)
        cv.Line(scribble, (x,y),(int(newX),int(newY)), (255,255,1), 2, 0)
    return scribble
    
def calcXangle(xcoord, yawHead):
    #print yawHead
    (width, height) = (160, 120)
    xDiff = width/2 - xcoord
    distanceToFrame = 0.5 * width / 0.42860054745600146
    xAngle = math.atan(xDiff/distanceToFrame)
    return xAngle + yawHead

def cornersTsplits(lines):
    #find corner and t splitsing if its a corner its not a tsplitsing.
    #if a corner was already close by take average of those corners/tsplits
    #findTsplistsing needs to check lines1 with line2 but, also other way around
    #IMPORTANT voor corner neem gemiddelde van 2 punten
    
    corners = []
    tSplitsing = []
    for index,line1 in enumerate(lines):
        for line2 in lines[index+1:]:
            (cornerX, cornerY, newAngle) = rangeLines(line1 ,line2)
            newAngle = int(newAngle)
            if((cornerX, cornerY, newAngle)!= (0,0, 0)):
                p1 = (cornerX, cornerY)
                #if its the 1st corner found append rigth away
                if( len(corners) >=1 ):
                   # print "2nd corner AAAAARRRGGGGG"
                   # print corners
                    for (oldX,oldY, oldAngle, oldLine1, oldLine2) in corners:
                        if(rangePoints(p1, (oldX,oldY)) == 1):
                            corners.remove((oldX,oldY, oldAngle,oldLine1, oldLine2))
                            (x1, y1) = (oldX, oldY)
                            (l2x1, l2y1) = p1
                            newX = (x1 + l2x1) /2
                            newY = (y1 + l2y1) /2
                            newAngle = (oldAngle + newAngle) /2
                            ((pa1),(pb1)) = oldLine1
                            ((pa2),(pb2)) = oldLine2
                           # print 'pa1, pb1 etc', pa1,pb1
                            deg1 = angle(pa1, pb1)
                            deg2 = angle(pa2,pb2)
                            newLine1 = mergeLines(oldLine1, line1, deg1)
                            newLine2 = mergeLines(oldLine2, line2, deg2)
                    #        print "Average of 2 corners"
                            corners.append((newX,newY, newAngle, newLine1,newLine2))
                        else:
                           # "New Corner"
                            corners.append((cornerX, cornerY, newAngle,line1, line2))
                else:
               #     print 'new corner'
                    corners.append((cornerX, cornerY, newAngle, line1, line2))
            else:
                (smalDist, tPoint, newTangle)= findTsplitsing(line1, line2)
                #print "TSPLITSING", smalDist, tPoint
                #switch lines for function if to big dist
                if (smalDist > minAbsDistT):
                    (smalDist, tPoint, newTangle)= findTsplitsing(line2, line1)
                   # print "TSPLITSING SWITCHED", smalDist, tPoint
                if (smalDist <= minAbsDistT):
                    (p1, p2) = tPoint
                    if (len(tSplitsing) >=1):
                        for (oldX,oldY, oldAngle) in tSplitsing:
                            point = (oldX, oldY)
                            p3 = round(p1)
                            p4 = round(p2)
                            if(rangePoints((p3,p4), point) == 1):
                                tSplitsing.remove((oldX, oldY, oldAngle))
                                (x1, y1) = point
                                newX = (x1 + p1) /2
                                newY = (y1 + p2) /2
                                newAngle = (oldAngle + newTangle) /2
                                tSplitsing.append((newX,newY,newAngle))
                            else:
                                tSplitsing.append((int(p1),int(p2), newTangle))
                    else:
                        tSplitsing.append((int(p1),int(p2), newTangle))
    return corners, tSplitsing
    
def rangePoints(point1, point2):
    (x1, y1) = point1
    (l2x1, l2y1) = point2
    #how big is the search around a point
    #dist = 10
    if(abs(x1-l2x1) <= rangeCorner and abs(y1-l2y1) <= rangeCorner):
        #newX = (x1 + l2x1) /2
        #newY = (y1 + l2y1) /2
        #return (newX, newY)
        return 1
    else:
        return 0

    
    
def findTsplitsing(line1, line2):
    #print 'lineDistance ', line1, line2
    (p11, p12) = line1
    (p21, p22) = line2
    # D = line between a point of line2 and the projected point
    #     on line1
    # beta = angle opposite to D
    angleP1 = angle(p11, p12)
    angleP2 = angle(p21, p22)
    beta1 = angleP1 - angle(p11, p21)
    beta2 = angleP1 - angle(p11, p22)
    # S is distance between p11 and point of line2
    S1 = distance(p11, p21)
    S2 = distance(p11, p22)
    # D is the distance from a point of line2 to line1
    D1 = abs(sin(beta1) * S1)
    D2 = abs(sin(beta2) * S2)
    #IF Kleinste distance te groot is switch de lijnen
        

    (p1x, p1y) = p11
    (p1x2, p1y2) = p12
    distLine1 = distance(p11,p12)
    
    if( D1 < D2 ):
        aanLiggend = cos(beta1) * S1   
        #delingLengte = aanLiggend / distLine1
        #deltaX =  p1x2 -  p1x
        #deltaY = p1y2 - p1y
        #newY = deltaY / delingLengte
        #newX = deltaX / delingLengte
        newX = cos(angleP1) * aanLiggend + p1x
        newY = sin(angleP1) * aanLiggend + p1y
        return D1, (newX, newY), angleP2
    else:
        aanLiggend = cos(beta2) * S2
        #delingLengte = aanLiggend / distLine1
        #deltaX =  p1x2 -  p1x
        #deltaY = p1y2 - p1y
        #newY = deltaY / delingLengte
        #newX = deltaX / delingLengte
        newX = cos(angleP1) * aanLiggend + p1x
        newY = sin(angleP1) * aanLiggend + p1y
        return D2, (newX, newY) ,angleP2
    
    
def rangeLines(line1, line2):
    ((x1, y1),(x2, y2)) = line1
    ((l2x1, l2y1),(l2x2, l2y2)) = line2
    p1 = (x1, y1) 
    p2 = (x2, y2) 
    p21 = (l2x1, l2y1) 
    p22 = (l2x2, l2y2) 
    
    #how big is the search around a point
    dist = rangeCorner
    if(abs(x1-l2x1) <= dist and abs(y1-l2y1) <= dist):
        return ((x1+l2x1)/2,(y1+l2y1)/2, (angle(p1,p2)+angle(p21,p22))/2)
    elif(abs(x1-l2x2) <= dist and abs(y1-l2y2) <= dist):
        return ((x1+l2x2)/2,(y1+l2y2)/2, (angle(p1,p2)+angle(p22,p21))/2)
    elif(abs(x2-l2x2) <= dist and abs(y2-l2y2) <= dist):
        return ((x2+l2x2)/2,(y2+l2y2)/2, (angle(p2,p1)+angle(p22,p21))/2)
    elif(abs(x2-l2x1) <= dist and abs(y2-l2y1) <= dist):
        return ((x2+l2x1)/2,(y2+l2y1)/2, (angle(p2,p1)+angle(p21,p22))/2)
    else:
        return (0,0, 0)

def scribble(lines):
    size = (160, 120)
    #object to draw on
    scribble = cv.CreateImage(size, cv.IPL_DEPTH_64F, 1)
   # print len(lines)
    ##for (p1, p2) in lines:
       # print p1, p2
    ##    cv.Line(scribble, p1, p2, (255,255,255), 1, 0)
    print 'lines'
    print lines[0][0]
    print lines[0][1]
    print lines[1][0]
    print lines[1][1]
    x = (lines[0][0], lines[0][1]) 
    y = (lines[1][0], lines[1][1])
    cv.Line(scribble, x, (lines[1][0], lines[1][1]), (255, 255, 255), 1, 0) 
    return scribble

def white():
    markFieldW('white')
    
'''
Take a snapshot and filter it for the given colour.
Returns the filtered image
'''

def snapShot():    
    global subscribe
    camProxy.unsubscribe("python_GVM")
	#2 = 640
	#1 = 320
	#0 = 160
    # subscribe to the camera	
    subscribe = camProxy.subscribe("python_GVM",0,11,5)
    shot = camProxy.getImageRemote(subscribe)
    size = (shot[0], shot[1])       #size = (160, 120)
    picture = Image.frombuffer("RGB", size, shot[6], "raw", "BGR", 0, 1)
    im = cv.CreateImageHeader(size, cv.IPL_DEPTH_8U, 3)
    cv.SetData(im, picture.tostring(), picture.size[0]*3)
    headPY = motionProxy.getAngles(["HeadPitch","HeadYaw"], True)
    return im, headPY
    
def markFieldW(color):
    # head = motionProxy.getangles(["HeadYaw", "HeadPitch"], True)
    # Make image
    #shot = camProxy.getImageRemote(subscribe)
    # Get image
    #size = (shot[0], shot[1])       #size = (160, 120)
    #picture = Image.frombuffer("RGB", size, shot[6], "raw", "BGR", 0, 1)
    
    # To openCV
    #im = cv.CreateImageHeader(size, cv.IPL_DEPTH_8U, 3)

    
    #cv.SetData(im, picture.tostring(), picture.size[0]*3)
    im = cv.LoadImage('line.png')
    cv.SaveImage("image.png", im)
    
    hsvFrame = cv.CreateImage((160, 120), cv.IPL_DEPTH_8U, 3)
    filter = cv.CreateImage((160,120), cv.IPL_DEPTH_8U, 1)
    
    # Goalfilter values
    if(color == 'green'): #KLOPT NIET.. ZOEK DE JUISTE HUE VALUES        
        hueMin = 54
        hueMax = 143
        saturationMin = 20
        saturationMax = 180
        valueMin = 33
        valueMax = 138
    if(color == 'white'): #Is RGB not HSV!!!
        hueMin = 231
        hueMax = 256
        saturationMin = 189
        saturationMax = 256
        valueMin = 245
        valueMax = 256
    if( color == 'black'):
        hueMin = 0
        hueMax = 5
        saturationMin = 0
        saturationMax = 5
        valueMin = 0
        valueMax = 5
    
    hsvMin1 = cv.Scalar(hueMin, saturationMin, valueMin, 0)
    hsvMax1 = cv.Scalar(hueMax, saturationMax, valueMax, 0)
    # Color detection using HSV
    #cv.CvtColor(im, im, cv.CV_BGR2HSV)
    
    cv.InRangeS(im, hsvMin1, hsvMax1, filter)
    #cv.Smooth(filter, filter, cv.CV_BLUR, 10, 10)
    cv.SaveImage('imageAfterWHITE.jpg', filter)
    return filter

'''
def findCorners(src):
    size = (160, 120)
    #eigenvv = cv.CreateImage(size, cv.IPL_DEPTH_64F, 1)
    eigenvv = cv.CreateImage((6*cv.GetSize(src)[0],
                               cv.GetSize(src)[1]), cv.IPL_DEPTH_64F, 1)
    blockSize = 10
    cv.CornerEigenValsAndVecs(src, eigenvv, blockSize, aperture_size=3)
    cv.SaveImage('findCorners.jpg', eigenvv)
'''

def getLines(image):
    # In storage the coordinates and radius of the images found
    storage = cv.CreateMemStorage();
    #print "storage"
    # Hough Lines 
    # HoughLines2(image, storage, method, rho, theta, threshold, param1=0, param2=0) -> lines
    # rho(float) - distance resolution in pixel-related units
    #rho = 1.5
    # theta(float) - Angle resolution measured in radians
    theta = 0.1 #math.pi/90
    #threshold(int) - Threshold parameter. A line is returned by the function
    #threshold = 85
    # if the corresponding accumulator value is greater than threshold
    lines = cv.HoughLines2(image, storage, cv.CV_HOUGH_PROBABILISTIC, houghRho, theta, houghThres,houghMinLine,houghMaxGap)
   # print "HoughLines"
    return lines

'''
Smooth the angle of each line so that it is a multiplication
of the step size. This means that lines that have a similar
angle are now parrallel to each other.
If an angle is found for the second time it will be merged
to the existing line in one of the two dictionaries.
'''
def filterLines(lines):
    # The minimum step size between 2 lines in radians
    # 0.261799 radians = 15 degrees
    #stepSize = 0.261799
    stepSize = mergeAngleLines
    # 2 dictionaries, where key: angle and value: line
    mergedLines1 = {}
    mergedLines2 = {}
    for (p1, p2) in lines:
        angleLine = angle(p1, p2)
        # correct the angle according to the step size
        # this means that every angle is multiplication of 'stepSize'
        angleLine = stepSize * round(angleLine/stepSize)
        # add the line to 'mergedLines1' if it doesn't already exist
        if not angleLine in mergedLines1:
      #      print "1 NEWLINE"
            mergedLines1.update({angleLine:(p1, p2)})
            continue

        # get the line in mergedLines1
        mergedLine = mergedLines1[angleLine]
        # calculate the distance to the mergedLine
        dist = lineDistance(mergedLine, (p1, p2))
        # if the distance is small, then merge the lines
        if  abs(dist) < absDistMerge:
            #merge the lines
            newLine = mergeLines(mergedLine, (p1, p2), angleLine)
            mergedLines1.update({angleLine:newLine})
      #      print "2 MERGEDLINE", newLine, "DIST" , dist
            continue

        # add the line to 'mergedLines2' if it doesn't already exist
        if not angleLine in mergedLines2:
     #       print "3 SAME DEG  BUT NEWLINE ", (p1,p2) 
            mergedLines2.update({angleLine:(p1, p2)})
            continue

        # get the line in mergedLines2
        mergedLine = mergedLines2[angleLine]
        # merge the lines
        newLine = mergeLines(mergedLine, (p1, p2), angleLine)
     #   print "4 SAME DEG BUT NEWLINE MERGED"
        mergedLines2.update({angleLine: newLine})

    values1 = mergedLines1.values()
    values2 = mergedLines2.values()
    print values1, values2
    return values1 + values2
    

'''
Stretch the line.
Shift the stretched line to the centre of the two lines.
'''
def mergeLines(line1, line2, deg):
    ((x1, y1),(x2, y2)) = line1
    ((l2x1, l2y1),(l2x2, l2y2)) = line2
    deg = deg *(180/pi)

    if( 85 >= deg >= 95 or  -85 <= deg <= -95):
        #print "orgDeg"
        #print orgDeg
        if( y1 <=l2y1):
             newPoint1 = (x1,y1)
        else:
            newPoint1 = (l2x1,l2y1)
            
    elif ( deg >=-1):
        #print "AAA1"
        if( y1<= l2y1):
            newPoint1 = (x1,y1)
        else:
            newPoint1 = (l2x1,l2y1)
            
    else:
        #print "BBB1"
        if (x1<=l2x1):
            newPoint1 = (x1,y1)
        else:
            newPoint1 = (l2x1,l2y1)

    if( 85 >= deg >= 95 or  -85 <= deg <= -95):
        #print "orgDeg"
        #print orgDeg
        if( y2 >l2y2):
            newPoint2 = (x2,y2)
        else:
            newPoint2 = (l2x2,l2y2)
            
    elif ( deg >=-1):
        #print "AAA2"
        if( y2>= l2y2):
            newPoint2 = (x2,y2)
        else:
            newPoint2 = (l2x2,l2y2)
            
    else:
        #print "BBB2"
        if (x2>=l2x2):
            newPoint2 = (x2,y2)
        else:
            newPoint2 = (l2x2,l2y2)

    

    newLine = (newPoint1, newPoint2)
    return newLine
    
                

	

	
	
def lineDistance(line1, line2):
    #print 'lineDistance ', line1, line2
    (p11, p12) = line1
    (p21, p22) = line2
    # D = line between a point of line2 and the projected point
    #     on line1
    # beta = angle opposite to D
    angleP1 = angle(p11, p12)
    beta1 = angleP1 - angle(p11, p21)
    beta2 = angleP1 - angle(p11, p22)
    # S is distance between p11 and point of line2
    S1 = distance(p11, p21)
    S2 = distance(p11, p22)
    # D is the distance from a point of line2 to line1
    D1 = sin(beta1) * S1
    D2 = sin(beta2) * S2

    if( D1 > D2 ):
        return D1
    return D2
        


def distance(p1, p2):
    (x1, y1) = p1
    (x2, y2) = p2
    return sqrt(pow(x1-x2, 2) + pow(y1-y2, 2))

def angle(p1, p2):
    (x1, y1) = p1
    (x2, y2) = p2
    return atan2(y2-y1, x2-x1)
