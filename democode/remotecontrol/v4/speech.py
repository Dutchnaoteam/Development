import sys

from naoqi import ALProxy

a = None

if (len(sys.argv) == 3):
    a = ALProxy("ALTextToSpeech", sys.argv[1], 9559)
    a.say(sys.argv[2])

    
def say(text):
    a.say(text)
    
def init(ip):
    global a
    a = ALProxy("ALTextToSpeech", ip, 9559)
    