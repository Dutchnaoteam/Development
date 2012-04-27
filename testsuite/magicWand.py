# magic wand

import wx
import math

#TODO duurt te lang: slimmer algoritme nodig
'''
def magic(image, startPos, ratio):
    minColour = maxColour = getRGB(image, startPos)
    (minColour, maxColour, xL) = goHorizontal(image, startPos, minColour, maxColour, ratio, -1) #go left
    (minColour, maxColour, xR) = goHorizontal(image, startPos, minColour, maxColour, ratio, 1)  #go right
    (x,y) = startPos
    (minColour, maxColour) = goVertical(image, xL, xR, y, minColour, maxColour, ratio, -1)   #go up
    (minColour, maxColour) = goVertical(image, xL, xR, y, minColour, maxColour, ratio, 1)    #go down
    return (minColour, maxColour)
'''

def magic(image, startPos, ratio):
    minColour = maxColour = getRGB(image, startPos)
    (minColour, maxColour) = search(image, startPos, minColour, maxColour,
                                    ratio, -1, 0)
    (minColour, maxColour) = search(image, startPos, minColour, maxColour,
                                    ratio, 1, 0)
    (minColour, maxColour) = search(image, startPos, minColour, maxColour,
                                    ratio, 0, -1)
    (minColour, maxColour) = search(image, startPos, minColour, maxColour,
                                    ratio, 0, 1)
    return (minColour, maxColour)
    

def getRGB(image, (x,y)):
    return (image.GetRed(x,y),image.GetGreen(x,y),image.GetBlue(x,y))

def search(image, (x,y), minColour, maxColour, ratio, stepHor, stepVer):
    while True:
        if x<=0 or x>=image.GetWidth()-1 or y<=0 or y>=image.GetHeight()-1:
            break
        x += stepHor
        y += stepVer
        
        c1 = getRGB(image, (x,y))
        if inRange(c1, minColour, maxColour):
            continue
        if closeColour(c1, maxColour, ratio):
            maxColour = makeGreater(c1, maxColour)
        else:
            break
        if closeColour(c1, minColour, ratio):
            minColour = makeSmaller(c1, minColour)
        else:
            break
        
    return (minColour, maxColour)


# step = -1 (goLeft) or 1 (goRight)
def goHorizontal(image, (x,y), minColour, maxColour, ratio, step):
    while True:
        if x<=0 or x>=image.GetWidth()-1:
            break
        x += step
        
        c1 = getRGB(image, (x,y))
        if greaterThan(c1, maxColour):
            if closeColour(c1, maxColour, ratio):
                maxColour = c1
            else:                
                break
        if smallerThan(c1, minColour):
            if closeColour(c1, minColour, ratio):
                minColour = c1
            else:
                break
    return (minColour, maxColour, x)

# step = -1 (goUp) or 1 (goDown)
def goVertical(image, xL, xR, y, minColour, maxColour, ratio, step):
    search = True
    while search:
        y += step
        if y<0 or y>=image.GetHeight():
            break
        search = False
        for i in xrange(xL,xR+1):
            c1 = getRGB(image, (i,y))
            if (not greaterThan(c1, maxColour) or closeColour(c1, maxColour, ratio)) and \
               (not smallerThan(c1, minColour) or closeColour(c1, minColour, ratio)):
                (minColour, maxColour, xL) = goHorizontal(image, (i,y),   
                                                      minColour, maxColour, ratio, -1)
                (minColour, maxColour, xR) = goHorizontal(image, (i,y),   
                                                      minColour, maxColour, ratio, 1)
                search = True
                break

    return (minColour, maxColour) 
        
                    


# c1 = colour1, c2 = colour2, ratio = max diff between c1 and c2
# expected colour space = rgb {0-255}
# expected ratio = {0.0-1.0}
def closeColour((r1,g1,b1), (r2,g2,b2), ratio):
    diff = math.sqrt((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) / math.sqrt(195075)
    #diff = math.sqrt((c1[0]-c2[0])**2+(c1[1]-c2[1])**2+(c1[2]-c2[2])**2) / math.sqrt(765)
    return diff < ratio

def inRange((r,g,b), (rMin,gMin,bMin), (rMax,gMax,bMax)):
    return r>=rMin and r<=rMax and g>=gMin and g<=gMax and b>=bMin and b<=bMax

def makeGreater((r1,g1,b1), (r2,g2,b2)):
    r3=r2
    g3=g2
    b3=b2
    if r1>r2:
        r3 = r1
    if g1>g2:
        g3 = g1
    if b1>b2:
        b3 = b1
    return (r3,g3,b3)

def makeSmaller((r1,g1,b1), (r2,g2,b2)):
    r3=r2
    g3=g2
    b3=b2
    if r1<r2:
        r3 = r1
    if g1<g2:
        g3 = g1
    if b1<b2:
        b3 = b1
    return (r3,g3,b3)

def greaterThan((r1,g1,b1), (r2,g2,b2)):
    return r1>r2 or g1>g2 or b1>b2
                  
def smallerThan((r1,g1,b1), (r2,g2,b2)):
    return r1<r2 or g1<g2 or b1<b2                  

def getNeighbours((width, height), (x,y)):
    neighbours = []
    if x < width:
        neighbours.append((x+1,y))
    if x > 0:
        neighbours.append((x-1,y))
    if y < height:
        neighbours.append((x,y+1))
    if y > 0:
        neighbours.append((x,y-1))
    return neighbours

if __name__=="__main__":
    image = wx.Image('./ball2.png', wx.BITMAP_TYPE_PNG)
    (minColour, maxColour) = magic(image, (102,57), 0.125)
    #(minColour, maxColour) = search(image, (102,57), (34,177,76), (34,177,76), 0.125, -1, 0)
    print minColour, maxColour
    raw_input()
