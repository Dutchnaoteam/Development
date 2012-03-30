#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <cv.h>
#include <highgui.h>
#include <sys/time.h>
#include <unistd.h>

typedef struct {
    CvPoint max_loc;
    double max_val;
} maxValLoc;

void filterIm(IplImage *img);
void blur(IplImage *img);
maxValLoc findMax(IplImage *img);

int main(int argc, char *argv[])
{
    IplImage* img = 0;

    if(argc < 2) {
        printf("Usage: main <image-file-name>\n\7");
        exit(0);
    }

    // load an image
    img=cvLoadImage(argv[1]);
    if(!img) {
        printf("Could not load image file: %s\n",argv[1]);
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

    cvCircle(imgOrig, max.max_loc, 3, CV_RGB(0, 255, 0), -1, 8, 0);

    // create a window
    cvNamedWindow("mainWin", CV_WINDOW_AUTOSIZE);
    cvShowImage("mainWin", imgOrig);
    cvWaitKey(0);
    cvReleaseImage(&img);
    cvReleaseImage(&imgOrig);
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
    ret.max_loc = max_loc;
    ret.max_val = max_val;

    return ret;
}
