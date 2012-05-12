"""
File: buttonController
Author: Camiel Verschoor, Sander Nugteren & Erik van Egmond
"""

import time

""" class ButtonController

Presents get methods for different buttons on the body (chest, feet) plus a 
manual setup.

"""
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
            print 'Pressed'
            while self.memProxy.getData("ChestButtonPressed", 0):
                pass
            return 1
        else:
            return 0
                
    def bumperButton(self):
        return self.memProxy.getData("LeftBumperPressed", 0) or \
               self.memProxy.getData("RightBumperPressed", 0)
    
    # THE FUNCTIONS TO SETUP THE NAO
    def getSetup(self):
        if self.manual:
            self.ttsProxy.say("This is the manual setup. Choose my team")
            if (self.teamColor == 0):
                self.ttsProxy.say("My current team color is, blue")
            else:
                self.ttsProxy.say("My current team color is, red")
            self.teamColor = self.chooseTeam()
            
            self.ttsProxy.say("Choose mode")
            if (self.penalty == 0):
                self.ttsProxy.say("Current mode, Match mode")
            else:
                self.ttsProxy.say("Current mode, Penalty mode")
            self.penalty = self.chooseMode()
            self.manual = False
        return (self.teamColor, self.penalty)

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