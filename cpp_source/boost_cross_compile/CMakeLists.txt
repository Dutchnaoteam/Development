cmake_minimum_required(VERSION 2.8)
project(boost_cross_compile)

set(Boost_USE_STATIC_LIBS ON)
set(Boost_USE_STATIC_RUNTIME ON)

find_package(qibuild)
find_package(boost COMPONENTS python REQUIRED)

INCLUDE_DIRECTORIES( "/home/maarten/Downloads/Choregraph/nao-geode-cross-toolchain-1.12.3/sysroot/usr/include/python2.6" )
LINK_DIRECTORIES( "/home/maarten/Downloads/Choregraph/nao-geode-cross-toolchain-1.12.3/sysroot/usr/lib" )

#LINK_LIBRARIES( boost_python )


if(Boost_FOUND)
    message("Boost found")

    qi_create_lib(nao_test SHARED "nao_test.cpp")

    include_directories(${Boost_INCLUDE_DIRS})
    target_link_libraries(nao_test ${Boost_LIBRARIES})
else()
    message("Error: Boost not found")
endif()
