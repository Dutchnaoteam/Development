import cv

def find_some_edgels(filename):
    # loading the image
    img = cv.LoadImage(filename)

    # converting to HSV colorspace
    hsv = cv.CreateImage(cv.GetSize(img), 8, 3)
    cv.CvtColor(img, hsv, cv.CV_BGR2HSV)

    # the white/green hsv values
    green_min = (0, 25, 25)
    green_max = (50, 100, 255)

    white_min = (0, 0, 240)
    white_max = (180, 15, 255)

    transitions = []

    # scanning for green/white/green transitions
    for x in xrange(0, hsv.width, 10):
        greens_in_a_row = 0
        whites_in_a_row = 0

        y = 0
        while y < hsv.height:
    
    # transitions with xvalues
    A = cv.CreateMat(len(transition), 2, cv.32FC1)
    B = cv.CreateMat(len(transition), 1, cv.32FC1)
    for i in xrange(0, len(transitions)):
        A[i, 0] = transitions[i][0]
        B[0] = transitions[i][1]

    for i in xrange(0, len(transitions))
        A[i, 1] = 1

    X = cv.CreateMat(2,1 cv.CV_32FC1)
    # transitions with yvalues
    solution = cv.Solve(A, B, X, cv.CV_LU)
    



    # debugging
    for x, y in transitions:
        cv.Circle(img, (x, y), 1, (0, 0, 255))

    cv.SaveImage('test.png', img)
    cv.SaveImage('hsv.png', hsv)

    return transitions
