# File: buttonController
# By: Camiel Verschoor, Sander Nugteren & Erik van Egmond

import time
import logging

class buttonController():
    # VARIABLES
    chestButtonPressed = False
    manual = True
    teamColor = 0
    penalty = 0
    kickOff = 0

    # CONSTRUCTOR
    def __init__(self, ttsProxy, memProxy, sensors, interval=0.5):
        self.interval = interval
        #self.chestButtonPressed = False
        self.manual = True
        self.memProxy = memProxy
        self.ttsProxy = ttsProxy
        self.sensors  = sensors
        
    # FUNCTIONS
    def chestButton(self):
        if self.memProxy.getData("ChestButtonPressed", 0):
            logging.debug( 'Pressed' )
            while self.memProxy.getData("ChestButtonPressed", 0):
                pass
            return 1
        else:
            return 0
                
    def bumperButton(self):
        return self.memProxy.getData("LeftBumperPressed", 0) or self.memProxy.getData("RightBumperPressed", 0)
    
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