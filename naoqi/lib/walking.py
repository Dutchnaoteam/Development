from naoqi import ALProxy
motionProxy = ALProxy('ALMotion', '127.0.0.1', 9559)

def walk(tr_max = 4.5, tr_min = 3.5, step_max = 30, step_min = 21, x_step = 0.04, y_step = 0.04, t_step = 20, h_step= 0.015, f_s = 0.095, f_o = 00):
    # 1) Trapezoid : an angle offset in degrees added to HipRoll joint at each Simple Support Mode
    # The value is linearly interpolated between low and max frequancy.
    # So by default, 4.5 degrees for low frequency

    motionProxy.setMotionConfig([["WALK_MAX_TRAPEZOID", tr_max]]) # default 4.5
    motionProxy.setMotionConfig([["WALK_MIN_TRAPEZOID", tr_min]]) # default 3.5

    # 2) Walk Period(frequency), i.e. the time between foot Steps
    # This is a int value corresponding to the number of motion cycles.
    # So, MIN_PERIOD(MAX FREQUENCY) = 21*20ms = 440ms(2.27Hz)

    motionProxy.setMotionConfig([["WALK_STEP_MAX_PERIOD", step_max]]) # default 30
    motionProxy.setMotionConfig([["WALK_STEP_MIN_PERIOD", step_min]]) # default 21

    # 3) Step Configuration
    # When using setWalkTargetVelocity(1.0,0.0,0.0,0.0), 
    # NAO does steps of WALK_MAX_STEP_X(0.04 meter)

    motionProxy.setMotionConfig([["WALK_MAX_STEP_X", x_step]]) # default 0.04
    motionProxy.setMotionConfig([["WALK_MAX_STEP_Y", y_step]]) # default 0.04
    motionProxy.setMotionConfig([["WALK_MAX_STEP_THETA", t_step]]) # default 20
    motionProxy.setMotionConfig([["WALK_STEP_HEIGHT", h_step]]) # default 0.015

    # 4) The Foot default configuration.
    # For example, when the robot walks straight the space along y axis between the feet is WALK_FOOT_SEPARATION
    # We added a new parameter that controls the default orientation between the foot

    motionProxy.setMotionConfig([["WALK_FOOT_SEPARATION", f_s]]) # default 0.095
    motionProxy.setMotionConfig([["WALK_FOOT_ORIENTATION", f_o]]) #   default orientation 00

    # 5) Torso control.
    # OrientationY could increase stability 
    # Height could avoid singularity problems (i.e. straight leg)
    motionProxy.setMotionConfig([["WALK_TORSO_HEIGHT", 0.31]]) # default 0.31
    motionProxy.setMotionConfig([["WALK_TORSO_ORIENTATION_Y", 0]]) # default 0
