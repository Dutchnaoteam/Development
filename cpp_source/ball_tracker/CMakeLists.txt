PROJECT( cpp_orig )
FIND_PACKAGE( OpenCV REQUIRED )
ADD_EXECUTABLE( balltracker cpp_orig.cpp )
TARGET_LINK_LIBRARIES( balltracker ${OpenCV_LIBS} )
