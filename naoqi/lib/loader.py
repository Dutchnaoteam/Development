# Written by: Camiel Verschoor
# Date: 1 April 2012
# Description: Loads the football code if the any footbumper is pressed

from naoqi import ALProxy
import time
import os
import sys

# Proxies
ttsProxy = ALProxy("ALTextToSpeech", "127.0.0.1", 9559)
audProxy = ALProxy('ALAudioDevice', '127.0.0.1', 9559)
memProxy = ALProxy("ALMemory", "127.0.0.1", 9559)
senProxy = ALProxy("ALSentinel", "127.0.0.1", 9559)

# Enable Button actions and Sound.
senProxy.enableDefaultActionSimpleClick(True)
senProxy.enableDefaultActionDoubleClick(True)
audProxy.setOutputVolume(70)

# Soul variable
soul = False

ttsProxy.say("Shall I activate my soul?")
start = time.time()

while time.time() - start < 2:
    if (((memProxy.getData("LeftBumperPressed", 0) != 0.0) or \
         (memProxy.getData("RightBumperPressed", 0) != 0.0)) or \
        ((len(sys.argv) > 1 ) and (sys.argv[1] == "True"))):
            soul = True
            break

# Activate soul
if soul:
    ttsProxy.say("Activating soul")
    senProxy.enableDefaultActionSimpleClick(False)
    senProxy.enableDefaultActionDoubleClick(False)
    os.system("python /home/nao/naoqi/lib/soul.py")
else:
    ttsProxy.say("I am ready for another great day")
