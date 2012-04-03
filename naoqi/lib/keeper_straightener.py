import cv

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

def scan(img, x, y, return_thresh = 10, reset_tresh = 5):
    noise_count = 0
    green_count = 0
    white_count = 0
    scanning = True

    while scanning and y < img.height:
        val = img[y, x]

        # the relevant counter gets incremented
        if is_green(val):
            green_count += 1
        else if is_white(val):
            white_count += 1
        else:
            noise_count += 1

        counts = [("noise_count", noise_count),
                  ("green_count", green_count),
                  ("white_count", white_count)]

        counts = sorted(counts, key=lambda x: x[1])
        highest = counts.pop()

        # if we've seen more than 5 pixels of the same color in a row, the other
        # counters get reset to zero
        # if the color was not green/white and we did see more than 10
        # green/white pixels previously, we return that patch of pixels
        if highest[1] > reset_thresh:
            if highest[0] != "white_count" and white_count > return_thresh:
                return ("white", y)
            else if highest[0] != "green_count" and green_count > return_thresh:
                return ("green", y)

            for var_name, _ in counts:
                eval(var_name + " = 0")

        y += 1
