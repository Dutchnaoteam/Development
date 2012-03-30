cmake_minimum_required(VERSION 2.8)
project(boost_cross_compile)

set(Boost_USE_STATIC_LIBS ON)
set(Boost_USE_STATIC_RUNTIME ON)

find_package(qibuild)
find_package(boost COMPONENTS python REQUIRED)

INCLUDE_DIRECTORIES( "/home/maarten/Downloads/Choregraph/nao-geode-cross-toolchain-1.12.3/sysroot/usr/include/python2.6" )
LINK_DIRECTORIES( "/home/maarten/Downloads/Choregraph/nao-geode-cross-toolchain-1.12.3/sysroot/usr/lib" )

# Create a executable named boost_cross_compile
# with the source file: main.cpp
qi_create_lib(nao_test SHARED "nao_test.cpp")
target_link_libraries(nao_test ${Boost_LIBRARIES})
qi_use_lib( nao_test boost )
LINK_LIBRARIES( boost_python )
