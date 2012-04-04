# Written by: Camiel Verschoor
# Date: 18 April 2011
# Description: Loads the football code if the any footbumper is pressed

from naoqi import ALProxy
import time
import os
import sys

# Built ins loaded
speak = ALProxy("ALTextToSpeech", "127.0.0.1", 9559)
audio = ALProxy('ALAudioDevice', '127.0.0.1', 9559)
memory = ALProxy("ALMemory", "127.0.0.1", 9559)
sentinel = ALProxy("ALSentinel", "127.0.0.1", 9559)
audio = ALProxy('ALAudioDevice', '127.0.0.1', 9559)

# Enable Button actions and Sound.
sentinel.enableDefaultActionSimpleClick(True)
sentinel.enableDefaultActionDoubleClick(True)
audio.setOutputVolume(90)
football = False

# Check if commandline arguments are given
if ( ( len( sys.argv ) > 1 ) and ( sys.argv[1] == "True" ) ):
   football = True
else:
    speak.say("Press my bumper to awake my football soul")
    start = time.time()
    while time.time() - start < 2:
        if (not((memory.getData("LeftBumperPressed", 0) == 0.0)) or not((memory.getData("RightBumperPressed", 0) == 0.0))):
            football = True

# Load football code if pressed
if football:
    speak.say("Awaking football soul")
    sentinel.enableDefaultActionSimpleClick(False)
    sentinel.enableDefaultActionDoubleClick(False)
    os.system("python /home/nao/naoqi/lib/soul.py")
else:
    speak.say("Awaking normal soul")
