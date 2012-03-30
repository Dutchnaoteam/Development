#include <cv.h>
#include <highgui.h>
#include <math.h>
#include <sys/time.h>
#include <unistd.h>

#include <vector>
#include <string>
#include <iostream>
#include <map>
#include <algorithm>
#include <boost/foreach.hpp>

using namespace std;

typedef struct tuple {
    double first;
    double second;
} tuple;

// prototypes
IplImage* markGoalCV(IplImage* im, string color);
double calcXangle(int xcoord);
tuple run(IplImage* image, double yawHead, string color);
