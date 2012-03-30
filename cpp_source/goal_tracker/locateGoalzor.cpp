#include "locateGoalzor.h"

using namespace std;


IplImage* markGoalCV(IplImage *im, string color)
{
    /**
     * As made by Michael Cabot
     * Ported to C++ by Maarten de Jonge
     *
     * Image color filter, can be thresholded (70 recommended) to find
     * locations containing the calibrated color
     * INPUT:  im, a [160-by-120] image needed to be filtered
     *         color, the filter color a string, can be 'blue' or 'yellow'
     * OUTPUT: returns an OpenCV color filtered image with values of the
     *         color match, values over a threshold of 70 are sugested
     */


    CvSize size = cvSize(160, 120);
    IplImage* hsvFrame = cvCreateImage(size, IPL_DEPTH_8U, 3);

    //IplImage* filter = new(IplImage);
    IplImage* filter = cvCreateImage(size, IPL_DEPTH_8U, 1);

    int hueMin, hueMax, saturationMin, saturationMax, valueMin, valueMax;

    // color is blue
    if (color.compare("blue") == 0)
    {
        hueMin = 116;
        hueMax = 130;
        saturationMin = 185;
        saturationMax = 255;
        valueMin = 75;
        valueMax = 210;
    }

    // color is yellow
    else if (color.compare("yellow") == 0)
    {
        hueMin = 20;
        hueMax = 41;
        saturationMin = 55;
        saturationMax = 255;
        valueMin = 60;
        valueMax = 210;
    }

    CvScalar hsvMin1 = cvScalar(hueMin, saturationMin, valueMin, 0);
    CvScalar hsvMax1 = cvScalar(hueMax, saturationMax, valueMax, 0);
    cvCvtColor(im, hsvFrame, CV_BGR2HSV);
    cvInRangeS(hsvFrame, hsvMin1, hsvMax1, filter);

    // releasing hsvFrame
    cvReleaseImage(&hsvFrame);

    return filter;
}

double calcXangle(int xcoord)
{
    /**
     * As made by Michael Cabot
     * Ported to C++ by Maarten de Jonge
     * calculates the angle towards a location in an image
     * INPUT:  xcoord, a x coordinate in a [160-by-120] image
     * OUTPUT: returns the angle to the x coordinate with the middle of
     * the image being 0 degrees
     */

    int width = 160;
    int height = 120;

    // using integer vision, just like the Python code
    int xDiff = width/2.0 - xcoord;
    double distanceToFrame = 0.5 * width / 0.42860054745600146;
    double xAngle = atan(xDiff / distanceToFrame);

    return xAngle;
}

tup run(IplImage* image, double yawHead, string color)
{
    /**
     * By Author
     * Ported to C++ by Maarten de Jonge
     * Recognizes poles of a color with a minimum lenght of 20 pixels
     * INPUT:  image, a [160-by-120] image needed to be filtered
     *         yawHead, the Robot Head Yaw, to make the angle absolute
     *         color, the filter color a string, can be 'blue' or 'yellow'
     * OUTPUT: returns a tupple (x, y) containing to angles for the best two
     *         poles. (None,None) is given if poles are missing
     *         At one missing pole (angle, None) will be returned
     *         (None, angle) will never be.
     */

    image = markGoalCV(image, color);
    cvSmooth(image, image, CV_GAUSSIAN, 5,5);

    int threshold = 70; // threshold for the grayscale

    // resolution of the input image
    int width = 160;
    int height = 120;

    // Form a map of vertical lines
    map<int, CvSize> lines;

    for (int x = 0; x < width; ++x) {
        for (int y = 10; y < height; y+= 10) {
            if ((double) CV_IMAGE_ELEM(image, uchar, y, x) > threshold) {
                int ry = y - 9;

                while ((double) CV_IMAGE_ELEM(image, uchar, ry, x) <= 70) {
                    ry += 1;
                }

                bool checker = false;
                int m = min(ry + 20, height);
                for (int checky = ry; checky < m; checky += 1) {
                    if ((double) CV_IMAGE_ELEM(image, uchar, checky, x) <= 70)
                        break;
                        if (checky == ry+19)
                        checker = true;
                }

                if (checker) {
                    for (int by = height-10; by > 0; by -= 10) {
                        if ((double) CV_IMAGE_ELEM(image, uchar, by, x) > threshold) {
                            int bry = by + 9;

                            while ((double) CV_IMAGE_ELEM(image, uchar, by, x) <= 70) {
                                bry -= 1;
                            }

                            checker = false;
                            for (int checky = max(bry-20, 0); checky < bry; ++checky) {
                                if ((double) CV_IMAGE_ELEM(image, uchar, checky, x) <= 70)
                                    break;
                                if (checky == bry - 19)
                                    checker = true;
                            }

                            if (checker) {
                                lines[x] = cvSize(ry, bry);
                                break;
                            }
                        }
                    }
                    break;
                }
            }
        }
    }

    cvReleaseImage(&image);

    // group the vertical lines together

    // first we get a sorted list of each key
    pair<int, CvSize> key;
    vector<int> sortedlines;

    for(map<int,CvSize>::iterator it = lines.begin(); it != lines.end(); ++it) {
      sortedlines.push_back(it->first);
    }

    sort(sortedlines.begin(), sortedlines.end());

    string currentBlob = "empty";
    int upperline = 0;
    int underline = 0;

    // initiate top two maximum values
    int Max = 0;
    int NotQuiteAsMax = 0;
    int posMax = 0;
    int posNotQuiteAsMax = 0;

    for (int i = 0; i < sortedlines.size() - 1; ++i) {
        if (currentBlob.compare("empty") == 0) {
            currentBlob = "full";
            underline = sortedlines[i];
        }

        int left = sortedlines[i];
        int right = sortedlines[i + 1];
        int leftTop = lines[left].width;
        int leftBot = lines[left].height;
        int rightTop = lines[right].width;
        int rightBot = lines[right].height;

        if (((right - left) == 1) && !((leftBot < rightTop) || (rightBot < leftTop))) {
            upperline = sortedlines[i + 1];
        }
        else {
            if ((upperline - underline) > 3) {
                int pos = (upperline + underline) / 2;
                int dif = upperline - underline;

                if (dif > NotQuiteAsMax) {
                    if (dif > Max) {
                        posNotQuiteAsMax = posMax;
                        NotQuiteAsMax = Max;
                        posMax = pos;
                        Max = dif;
                    }

                    else {
                        posNotQuiteAsMax = pos;
                        NotQuiteAsMax = dif;
                    }
                }
            }
            currentBlob = "empty";
        }
    }

    if ((upperline - underline) > 3) {
        int pos = (upperline + underline) / 2;
        int dif = upperline - underline;

        if (dif > NotQuiteAsMax) {
            if (dif > Max) {
                posNotQuiteAsMax = posMax;
                NotQuiteAsMax = Max;
                posMax = pos;
                Max = dif;
            }

            else {
                posNotQuiteAsMax = pos;
                NotQuiteAsMax = dif;
            }
        }
    }

    // return angles to the found positions
    double tupplepart1 = 0;
    double tupplepart2 = 0;

    if (posNotQuiteAsMax)
        tupplepart1 = calcXangle(posNotQuiteAsMax) + yawHead;
    if (posMax)
        tupplepart2 = calcXangle(posMax) + yawHead;

    if (tupplepart1 || tupplepart2) {
        tup ret;
        ret.first = tupplepart2;
        ret.second = tupplepart1;

        return ret;
    }
}

tup goaltrack(IplImage* img, string color)
{
    tup goal = run(img, 0, color);
    cvReleaseImage(&img);
    return goal;
}
