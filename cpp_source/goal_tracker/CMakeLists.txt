PROJECT( goal_tracker )
FIND_PACKAGE( OpenCV REQUIRED )
ADD_EXECUTABLE( goal_tracker locateGoalzor.cpp )
TARGET_LINK_LIBRARIES( goal_tracker ${OpenCV_LIBS})
