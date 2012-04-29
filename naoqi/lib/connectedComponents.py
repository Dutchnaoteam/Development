import cv

def findField(fileName):
    im = cv.LoadImage(fileName)
    size = cv.GetSize(im)
    hsvFrame = cv.CreateImage(size, cv.IPL_DEPTH_8U, 3)
    image = cv.CreateImage(size, cv.IPL_DEPTH_8U, 1)
    ####################
    # filters for green# 

    # Iran values 4/2012
    hsvMin1 = cv.Scalar(60,  3,  90, 0)
    hsvMax1 = cv.Scalar(100,  190,  210, 0)
    
    # Eindhoven values 4/2012 Aanpassen Tijmen
    #hsvMin1 = cv.Scalar(46,  94,  89, 0)
    #hsvMax1 = cv.Scalar(75,  204,  212, 0)

    # Color detection using HSV
    cv.CvtColor(im, hsvFrame, cv.CV_BGR2HSV)
    cv.InRangeS(hsvFrame, hsvMin1, hsvMax1, image)

    largest_component = connectedComponents(image)
    if largest_component is not []:
        rect = x_y_height_width(largest_component)
        print rect
        cv.SetImageROI(im, (rect[0], rect[1], rect[2], rect[3]))
        cv.SaveImage("newROI.jpg", im)
    return image



# returns all points that contour the biggest connected components
def connectedComponents(image):
    stor = cv.CreateMemStorage()
    seq = cv.FindContours(image, stor, cv.CV_RETR_LIST, cv.CV_CHAIN_APPROX_SIMPLE)
    largest = (None, 0)
    
    #TODO: make things better
    largest = []
    while(seq != None):
        print len(seq)
        if len(seq) >=50:
            print 'adding component with'
            print len(seq)
            print 'elements'
            largest = largest + list(seq)
        seq = seq.h_next()
    for i in largest:
        cv.Circle(image, i, 1,(0, 0, 250), 1)
    cv.SaveImage("lineimage.png", image)
    print(len(largest))
    return largest
    
# returns minimal x minimal y height and width value in list
# these values are extracted from a list of tuples (component_points)
def x_y_height_width(component_points):
    print component_points
    #return 0s if there was no field
    if(component_points == []):
        return [0,0,0,0]

    # find the tuples with smallest x values
    smallest_x = component_points[0][0]
    for i in component_points:
        if(i[0] < smallest_x):
            smallest_x = i[0]
    # from those tuples find  y value with smallest x value
    smallest_y = component_points[0][1]
    for i in component_points:
        if i[1] < smallest_y:
            smallest_y = i[1]
    # now we decide the max xy point the same way
    biggest_x = component_points[0][0]
    for i in component_points:
        if(i[0] > biggest_x):
            biggest_x = i[0]
    # from those tuples find  y value with smallest x value
    biggest_y = component_points[0][1]
    for i in component_points:
        if i[1] > biggest_y:
            biggest_y = i[1]
    width = biggest_x - smallest_x
    height = biggest_y - smallest_y
    print smallest_x
    print smallest_y
    print biggest_x
    print biggest_y
    return [smallest_x, smallest_y, width, height]






    # from these tuples select smallest y value
    
    # do the same thing for max x values and max y values
