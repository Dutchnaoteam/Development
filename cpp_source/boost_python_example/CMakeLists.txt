LINK_LIBRARIES( boost_python )
INCLUDE_DIRECTORIES( "/usr/include/python2.7" )
LINK_DIRECTORIES( "/usr/lib/python2.7" )
ADD_LIBRARY( testing SHARED test.cpp )
