# File: buttonController
# By: Camiel Verschoor, Sander Nugteren & Erik van Egmond

from naoqi import ALProxy
import time

class buttonController():
    # VARIABLES
    memProxy = ALProxy("ALMemory","127.0.0.1", 9559)
    ttsProxy = ALProxy("ALTextToSpeech", "127.0.0.1", 9559)
    chestButtonPressed = False
    manual = True
    teamColor = 0
    penalty = 0
    kickOff = 0

    # CONSTRUCTOR
    def __init__(self, interval=0.5):
        self.interval = interval
        #self.chestButtonPressed = False
        self.manual = True
    
    # FUNCTIONS
    def chestButton(self):
        return not(self.memProxy.getData("ChestButtonPressed", 0) == 0.0)
        
    def bumperButton(self):
        return not((self.memProxy.getData("LeftBumperPressed", 0) == 0.0) or (self.memProxy.getData("RightBumperPressed", 0) == 0.0))
    
    # THE FUNCTIONS TO SETUP THE NAO
    def getSetup(self):
        if self.manual:
            self.ttsProxy.say("This is the manual setup. Choose my team")
            if (self.teamColor == 0):
                self.ttsProxy.say("My current team color is, blue")
            else:
                self.ttsProxy.say("My current team color is, red")
            self.teamColor = self.chooseTeam()
            time.sleep(1)
            
            self.ttsProxy.say("Choose mode")
            if (self.penalty == 0):
                self.ttsProxy.say("Current mode, Match mode")
            else:
                self.ttsProxy.say("Current mode, Penalty mode")
            self.penalty = self.chooseMode()
            time.sleep(1)
            
            self.ttsProxy.say("Choose kick off")
            if (self.kickOff == 0):
                self.ttsProxy.say("I have kick off")
            else:
                self.ttsProxy.say("I do not have kick off")
            self.kickOff = self.chooseKickOff()
            time.sleep(1)
            
            self.manual = False
        return (self.teamColor, self.penalty, self.kickOff)

    def chooseTeam(self):
        startTime = time.time()
        while (time.time() - startTime < 4):
            if (self.bumperButton()):
                if(self.teamColor == 0):
                    self.teamColor = 1
                    self.ttsProxy.say("My team color is, red")
                else:
                    self.teamColor = 0
                    self.ttsProxy.say("My team color is, blue")
                time.sleep(0.5)
        return self.teamColor

    def chooseMode(self):
        startTime = time.time()
        while (time.time() - startTime < 4):
            if (self.bumperButton()):
                if(self.penalty == 0):
                    self.penalty = 1
                    self.ttsProxy.say("Penalty mode")
                else:
                    self.penalty = 0
                    self.ttsProxy.say("Match mode")
                time.sleep(0.5)
        return self.penalty

    def chooseKickOff(self):
        startTime = time.time()
        while (time.time() - startTime < 4):
            if (self.bumperButton()):
                if(self.kickOff == 0):
                    self.kickOff = 1
                    self.ttsProxy.say("Kick off")
                else:
                    self.kickOff = 0
                    self.ttsProxy.say("No kick off")
                time.sleep(0.5)
        return self.kickOff

    # GET FUNCTIONS
    def getChestButton(self):
        button = self.chestButton()
        if button:
            while self.chestButton():
                pass
        return button