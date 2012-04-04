#!/usr/bin/python2

import cv, time, sys, math

def find_lines(image, drho, dtheta, threshold, canny, smoothing):
    img = cv.LoadImage(image)

    begin = time.time()

    imgHSV = cv.CreateImage(cv.GetSize(img), 8, 3)
    threshed = cv.CreateImage(cv.GetSize(img), 8, 1)

    cv.CvtColor(img, imgHSV, cv.CV_BGR2HSV)

    cv.InRangeS(imgHSV, cv.Scalar(0, 0, 230), cv.Scalar(180, 25, 255),
            threshed)

    if canny: cv.Canny(threshed, threshed, 100, 50);
    if smoothing: cv.Smooth(threshed, threshed, cv.CV_GAUSSIAN, 5)
    
    lines = cv.HoughLines2(threshed, cv.CreateMemStorage(),
            cv.CV_HOUGH_PROBABILISTIC, dtheta, drho, threshold)

    #lines = list(lines)

    #end = time.time()
    #elapsed = (end - begin) * 1000.0 # time in milliseconds
    #print 'Time taken: %f milliseconds' % elapsed

    #group_lines(lines)
    counter = 0
    for i in lines:
        # calculating y for x is zero
        counter+=1
        cv.Line(img,
                i[0],
                i[1],
                cv.Scalar(255, 0, 0), thickness=1)
    print counter

    return (img, threshed)

def rhotheta2xy(x, rho, theta):
    if (theta != 0):
        y = (-math.cos(theta) / math.sin(theta)) * x + (rho / math.sin(theta))
    else:
        y = rho

    return int(y)

def group_lines(lines):
    error = lambda (r1, t1), (r2, t2): abs(r1 - r2) + abs(t1 - t2)
    while True:
        i = 0
        while i < len(lines)-1:
            print error(lines[i], lines[i+1])
            if error(lines[i], lines[i+1]) < 150:
                r1, t1 = lines[i]
                r2, t2 = lines[i+1]
                lines.pop(i); lines.pop(i)
                lines.append( ((r1+r2)/2.0, (t1+t2)/2.0))
                i += 1
                continue
            i += 1
        break


if __name__ == '__main__':
    argv = sys.argv
    find_lines(argv[1])
