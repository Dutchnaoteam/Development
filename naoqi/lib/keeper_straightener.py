import cv

def find_some_edgels(filename):
    # loading the image
    img = cv.LoadImage(filename)

    # converting to HSV colorspace
    hsv = cv.CreateImage(cv.GetSize(img), 8, 3)
    cv.CvtColor(img, hsv, cv.CV_BGR2HSV)

    # the white/green hsv values
    
    white_min = (0, 0, 240)
    white_max = (180, 15, 255)

    transitions = []

    # scanning for green/white/green transitions
    for x in xrange(0, hsv.width, 10):
        greens_in_a_row = 0
        whites_in_a_row = 0
        y = 0
        while y < hsv.height:
            # if color is green
            if(hsv[x,y] > green_min and hsv[x,y] < greem_max):
                whites_in_a_row= 0 
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
