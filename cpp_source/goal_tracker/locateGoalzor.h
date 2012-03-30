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
#include <boost/python.hpp>
#include <Python.h>

using namespace std;


struct tup {
    double first;
    double second;
} ;

// prototypes
IplImage* markGoalCV(IplImage* im, string color);
double calcXangle(int xcoord);
tup run(IplImage* image, double yawHead, string color);
tup goaltrack(IplImage* img, string color);



BOOST_PYTHON_MODULE(goaltracker)
{
    using namespace boost::python;
    def("goaltrack", goaltrack);
    class_<tup>("tup")
        .def_readwrite("first", &tup::first)
        .def_readwrite("second", &tup::second);
}

