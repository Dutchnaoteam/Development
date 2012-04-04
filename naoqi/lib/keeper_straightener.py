import cv
import math

# the white/green hsv values
GREEN_MIN = (0, 25, 25)
GREEN_MAX = (50, 100, 255)

WHITE_MIN = (0, 0, 240)
WHITE_MAX = (180, 15, 255)

def is_green(color):
    return GREEN_MIN < color < GREEN_MAX

def is_white(color):
    return WHITE_MIN < color < WHITE_MAX

def find_some_edgels(filename):
    # loading the image
    img = cv.LoadImage(filename)

    # converting to HSV colorspace
    hsv = cv.CreateImage(cv.GetSize(img), 8, 3)
    cv.CvtColor(img, hsv, cv.CV_BGR2HSV)

    transitions = []

    # scanning for green/white/green transitions
    for x in xrange(0, hsv.width, 10):
        greens_in_a_row = 0
        whites_in_a_row = 0
        tuple_index = []
        y = 0
        finalcoords = []
        while y < hsv.height:
            # if color is green
            if(is_green(hsv[y,x]) ):
                # check if we had a white streak 
                if (whites_in_a_row > 4 and whites_in_a_row < 10 ):
                    finalcoords = tuple_index[math.ceil(len(tuple_index)/2)] 
                whites_in_a_row= 0 
                greens_in_a_row +=1
            # if color is white
            elif(is_white(hsv[y,x])):
                whites_in_a_row += 1
                tuple_index = tuple_index + [(x,y)]
            # no green, no white 
            else:
                whites_in_a_row = 0
                greens_in_a_row = 0
                tuple_index = []
            # check if there is any white in the image at the given points
            if (whites_in_a_row > 4 and whites_in_a_row < 10 ):
                finalcoords = tuple_index[math.ceil(len(tuple_index)/2)] 
            whites_in_a_row = 0 
            greens_in_a_row = 0
            tuple_index = []
            y+=1
    solution = cv.CreateMat(len(transitions), 2, cv.CV_32FC1)
    solution =  leastSquares(finalcoords)
    point1x = 5 
    point1y = solution[0,0] * point1x + solution[1,0]
    point2x = 50
    point2y = solution[0,0] * point2x + solution[1,0]
    cv.Line(img,(point1x, point1y), (point2x, point2y),(0,0,255) ,2,8, 2)
    cv.SaveImage('newImage.jpg',img )

        

    return transitions

def leastSquares(transitions):
    # transitions with xvalues
    A = cv.CreateMat(len(transitions), 2, cv.CV_32FC1)
    B = cv.CreateMat(len(transitions), 1, cv.CV_32FC1)
    for i in xrange(0, len(transitions)):
        A[i, 0] = transitions[i][0]
        B[i,0] = transitions[i][1]


    for i in xrange(0, len(transitions)):
        A[i, 1] = 1

    X = cv.CreateMat(2,1, cv.CV_32FC1)
    # transitions with yvalues
    solution = cv.Solve(A, B, X, cv.CV_LU)
    return X
    



    # debugging
    #for x, y in transitions:
    #    cv.Circle(img, (x, y), 1, (0, 0, 255))
#
 #   cv.SaveImage('test.png', img)
 #   cv.SaveImage('hsv.png', hsv)

  #  return transitions
