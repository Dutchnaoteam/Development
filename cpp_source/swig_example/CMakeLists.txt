cmake_minimum_required(VERSION 2.8)
project(swig_cross_compile)

find_package(qibuild)
include(qibuild/swig/python)

qi_swig_wrap_python(nao_test nao_test.i 
    SRC nao_test.cpp)
