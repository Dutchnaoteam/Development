# Written by: Camiel Verschoor
# Date: 1 April 2012
# Description: Loads the football code if the any footbumper is pressed

from naoqi import ALProxy
import time
import os
import sys

# Built ins loaded
ttsProxy = ALProxy("ALTextToSpeech", "127.0.0.1", 9559)
audProxy = ALProxy('ALAudioDevice', '127.0.0.1', 9559)
memProxy = ALProxy("ALMemory", "127.0.0.1", 9559)
senProxy = ALProxy("ALSentinel", "127.0.0.1", 9559)
audProxy = ALProxy('ALAudioDevice', '127.0.0.1', 9559)

# Enable Button actions and Sound.
senProxy.enableDefaultActionSimpleClick(True)
senProxy.enableDefaultActionDoubleClick(True)
audProxy.setOutputVolume(90)

# Set variable to active football soul.
soul = False

ttsProxy.say("Should I activate my soul?")
start = time.time()
while time.time() - start < 2:
    # Check for bumper sensors and command line argument
    if ( not((memProxy.getData("LeftBumperPressed", 0) == 0.0)) or \
       ( not((memProxy.getData("RightBumperPressed", 0) == 0.0)) or \
       (( len( sys.argv ) > 1 ) and ( sys.argv[1] == "True" ) ) ) ):
            soul = True
            break;

# Load football code if pressed
if soul:
    ttsProxy.say("Initializing Football Soul")
    senProxy.enableDefaultActionSimpleClick(False)
    senProxy.enableDefaultActionDoubleClick(False)
    os.system("python /home/nao/naoqi/lib/soul.py")
else:
    ttsProxy.say("I am now ready to use")
