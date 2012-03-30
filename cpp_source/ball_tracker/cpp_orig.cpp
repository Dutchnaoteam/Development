#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <cv.h>
#include <highgui.h>
#include <sys/time.h>
#include <unistd.h>
#include <boost/python.hpp>
#include <Python.h>

typedef struct {
    int max_loc_x;
    int max_loc_y;
    double max_val;
} maxValLoc;

maxValLoc balltrack(char image[]);
void filterIm(IplImage *img);
void blur(IplImage *img);
maxValLoc findMax(IplImage *img);


BOOST_PYTHON_MODULE(balltracker)
{
    using namespace boost::python;
    def("balltrack", balltrack);
    class_<maxValLoc>("maxValLov")
        .def_readwrite("max_loc_x", &maxValLoc::max_loc_x)
        .def_readwrite("max_loc_y", &maxValLoc::max_loc_y)
        .def_readwrite("max_val", &maxValLoc::max_val);
}

maxValLoc balltrack(char image[])
{
    IplImage* img = 0;

    // load an image
    img=cvLoadImage(image);
    if(!img) {
        printf("Could not load image file: %d\n", 1 );
        exit(0);
    }

    IplImage *imgOrig = cvCreateImage(cvGetSize(img), 8, 3);
    *imgOrig = *img;

    // some setup for calculating the time
    struct timeval start, end;
    long mtime, seconds, useconds;
    gettimeofday(&start, NULL);

    // This is where it's at!
    filterIm(img);
    blur(img);

    maxValLoc max = findMax(img);

    gettimeofday(&end, NULL);
    seconds = end.tv_sec - start.tv_sec;
    useconds = end.tv_usec - start.tv_usec;
    mtime = ( (seconds) * 1000 + useconds/1000.0 ) + 0.5;
    printf("Time taken: %ld milliseconds\n", mtime);
    

    cvReleaseImage(&img);
    cvReleaseImage(&imgOrig);
    return max;
}

void filterIm(IplImage* img)
{
    CvSize size = cvGetSize(img);
    IplImage* imgHSV = cvCreateImage(size, 8, 3);
    IplImage* filter = cvCreateImage(size, 8, 1);
    IplImage* filter2 = cvCreateImage(size, 8, 1);

    CvScalar hsvMin1 = cvScalar(0,  90,  130, 0);
    CvScalar hsvMax1 = cvScalar(12, 256, 256, 0);
    CvScalar hsvMin2 = cvScalar(170,  90,  130, 0);
    CvScalar hsvMax2 = cvScalar(200, 256, 256, 0);

    cvCvtColor(img, imgHSV, CV_BGR2HSV);

    cvInRangeS(imgHSV, hsvMin1, hsvMax1, filter);
    cvInRangeS(imgHSV, hsvMin2, hsvMax2, filter2);

    cvOr(filter, filter2, filter);

    *img = *filter;
}

void blur(IplImage* img)
{
    cvSmooth(img, img, CV_BLUR, 5, 5);
}

maxValLoc findMax(IplImage* img)
{
    double min_val, max_val;
    CvPoint min_loc, max_loc;
    maxValLoc ret;

    cvMinMaxLoc(img, &min_val, &max_val, &min_loc, &max_loc);
    ret.max_loc_x = max_loc.x;
    ret.max_loc_y = max_loc.y;
    ret.max_val = max_val;

    return ret;
}
