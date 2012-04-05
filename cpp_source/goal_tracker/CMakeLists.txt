cmake_minimum_required(VERSION 2.8)
project(goal_tracker)

find_package(qibuild)
include(qibuild/swig/python)

qi_swig_wrap_python(goal_tracker goal_tracker.i 
    SRC locateGoalzor.cpp)
