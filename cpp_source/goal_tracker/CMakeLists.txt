LINK_LIBRARIES( boost_python )
FIND_PACKAGE( OpenCV REQUIRED )
INCLUDE_DIRECTORIES( "/usr/include/python2.7" )
LINK_DIRECTORIES( "/usr/lib/python2.7" )
ADD_LIBRARY( goaltracker SHARED locateGoalzor.cpp )
TARGET_LINK_LIBRARIES( goaltracker ${OpenCV_LIBS} )

