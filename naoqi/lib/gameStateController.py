# File: gameStateController
# File: gameStateController
# By: Camiel Verschoor, Sander Nugteren & Erik van Egmond

from socket import *
import time
import gameController as gameC
import buttonController as buttonC
import threading
import swearingEngine as swe

class StateController(threading.Thread):
    # VARIABLES
    f = open('/home/nao/naoinfo/NAOINFO.txt','r')
    robot = int(f.readline())
    team = int(f.readline())
    state = 0
    gcActive = True
    lastCheck = 0
    secondaryState = 0

    def __init__(self, name, ttsProxy, memProxy, ledProxy, sensors ):
        threading.Thread.__init__(self)
        self.name = name
        self.running = True
        self.bc = buttonC.buttonController( ttsProxy, memProxy, sensors )
        self.gc = gameC.gameController( self.team )
        self.ledProxy = ledProxy
        self.firstCallPenalty = True
        
    def __del__(self):
        self.running = False
        self.gc.close()

    def run(self):
        gcState = 0
        buttonState = 0
        now = time.time()
        
        while(self.running):
            previous = self.state
            # if gamecontroller active
            if self.gc.controlledRefresh():
                gcState = self.gc.getGameState()                # get state from GameController
                buttonState = self.listenToButtons(buttonState) # get buttonstate 

                if (buttonState == 10 or self.gc.getPenalty(self.robot, self.team)):
                    self.state = 10
                else:
                    self.state = gcState
                self.manageLeds( self.state )
                self.swearingEngine()
            # if gamecontroller not active, listen to buttons for some time (10 seconds) then try refreshing
            else: 
                #print 'Gc, not active, listen to buttonInterface'
                now = time.time()
                while time.time() - now < 10.0:
                    self.state = self.listenToButtons( self.state )
                    self.manageLeds( self.state )
                    self.swearingEngine()
                    
                               
                    

    def swearingEngine(self):
        if self.state == 10 and self.firstCallPenalty:
            try:
                swe.penalized(self.getPenalty())
            except:
                pass
            self.firstCallPenalty = False
        if not(self.state==10) and not(self.firstCallPenalty):
            self.firstCallPenalty = True 
    def manageLeds( self, state ): 
        # case initial
        if state == 0:
            self.ledProxy.off('AllLeds')
            # Team color must be displayed on left foot (Reference to rules)
            if (self.getTeamColor == 0):
                self.ledProxy.fadeRGB('LeftFootLeds', 0x000000ff, 0)
            else:
                self.ledProxy.fadeRGB('LeftFootLeds', 0x00ff0000, 0)
        elif self.state == 1:
            # ChestLed is blue
            self.ledProxy.fadeRGB('ChestLeds',0x000000ff, 0)
        elif self.state == 2:
            # ChestLed is yellow
            self.ledProxy.fadeRGB('ChestLeds', 0x00ffff00, 0)       # set chestledcolor to green
            # Team color must be displayed on left foot (Reference to rules)
            if (self.getTeamColor == 0):
                self.ledProxy.fadeRGB('LeftFootLeds', 0x000000ff, 0)
            else:
                self.ledProxy.fadeRGB('LeftFootLeds', 0x00ff0000, 0)
        elif self.state == 3:
            # ChestLed is greens
            self.ledProxy.fadeRGB('ChestLeds', 0x0000ff00, 0)
        elif self.state == 10:
            # ChestLed is red 
            self.ledProxy.fadeRGB('ChestLeds',0x00ff0000, 0)                               
        elif self.state == 4:
            # Leds are off
            self.ledProxy.off('AllLeds')                                

    def getState(self):
        return self.state

    def listenToButtons(self, buttonState):
        state = 0
        if self.bc.chestButton(): #change the phase if the ChestButton was pressed
            if(buttonState == 0):    # initial   -> penalized
                state = 10
            elif(buttonState == 10): # penalized -> playing
                state = 3
            elif(buttonState == 3):  # playing   -> penalized
                state = 10
            else:                    # all other states ? -> playing
                state = 3
        else:
            state = buttonState      # if not pressed, remain in current state
        return state
        
    def getSetup(self):
        return self.bc.getSetup()

    def setup(self, teamColor = 0, penalty = 0):
        return self.bc.setup(teamColor, penalty)

    # GET FUNCTIONS
    def getTeamNumber(self):
        return self.team

    def getRobotNumber(self):
        return self.robot

    def getTeamColor(self, side):
        return self.gc.getTeamColor(side)

    def getKickOff(self):
        return self.gc.getKickOff()

    def getSecondaryState(self):
        if self.gc.controlledRefresh():
            return self.gc.getSecondaryState()
        return self.secondaryState

    def getMatchInfo(self):
        teamColor = kickOff = penalty = 0
        if self.gc.controlledRefresh():
            teamColor = self.gc.getTeamColor('we')
            penalty = self.gc.getSecondaryState()
            kickOff = self.gc.getKickOff()
        else:
            (teamColor, penalty, kickOff) = self.bc.getSetup()
        self.secondaryState = penalty
        return (teamColor, penalty, kickOff)

    def getPenalty(self):
        return self.gc.getPenalty(self.robot, self.team)
        
    def getSecondsRemaining():
        return self.gc.getSecondsRemaining()

    # Closes thread
    def close(self):
        self.running = False
        self.gc.close()
        print 'gameStateController closed safely'

# This code will only be executed if invoked directly. Not when imported from another file.
# It shows how to use this module
if __name__ == '__main__':
    sc = stateController("stateController")
    sc.start()
    now = time.time()
    while (sc.getState() != 4):
        pass
    sc.close()
