"""
File: gameStateController
Author: Camiel Verschoor, Sander Nugteren & Erik van Egmond
"""

import time
import gameController as gameC
import buttonController as buttonC
import threading

class StateController(threading.Thread):
    """ Class StateController
    
    A threaded class that keeps checking gamecontroller and buttons for changes 
    in the game state.  
    
    """
    # VARIABLES
    f = open('/home/nao/naoinfo/NAOINFO.txt','r')
    robot = int(f.readline())
    team = int(f.readline())
    state = 0
    gcActive = True
    lastCheck = 0
    secondaryState = 0

    def __init__(self, ledProxy, memProxy, sensors, ttsProxy):
        threading.Thread.__init__(self)
        self.running = True
        self.bc = buttonC.buttonController( ttsProxy, memProxy, sensors)
        self.gc = gameC.gameController(self.team)
        self.ledProxy = ledProxy
        
    def __del__(self):
        self.running = False
        self.gc.close()

    def run(self):
        gcState = 0
        buttonState = 0
        now = time.time()
        
        while(self.running):
            # if gamecontroller active
            if self.gc.controlledRefresh():
                # get state from GameController
                gcState = self.gc.getGameState()                
                # get buttonstate
                if self.bc.chestButton():             
                    buttonState = self.listenToButtons(self.state)  
                
                # if penalized
                if (buttonState == 10 or self.gc.getPenalty(self.robot, \
                                                            self.team)):
                    self.state = 10
                else:
                    self.state = gcState
                self.manageLeds( self.state )
            # if gamecontroller not active, listen to buttons for some time 
            # (10 seconds) then try refreshing
            else: 
                #print 'Gc, not active, listen to buttonInterface'
                now = time.time()
                while time.time() - now < 10.0:
                    if self.bc.chestButton():
                        self.state = self.listenToButtons( self.state )
                    self.manageLeds( self.state )

    def manageLeds( self, state ): 
        """ returns None
        
        Uses chestleds to display gamestate. TODO make this non-iterative? 
        
        """
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
            self.ledProxy.fadeRGB('ChestLeds', 0x000000ff, 0)
        elif self.state == 2:
            # ChestLed is yellow
            self.ledProxy.fadeRGB('ChestLeds', 0x00ffff00, 0)       
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
            self.ledProxy.fadeRGB('ChestLeds', 0x00ff0000, 0)
        elif self.state == 4:
            # Leds are off
            self.ledProxy.off('AllLeds')                                
    
    def getState(self):
        """ Get the current state """
        return self.state

    def listenToButtons(self, buttonState):
        """ listenToButtons( buttonState ) -> None
    
        Invoked if button pressed, change state accordingly
        
        """
        if(buttonState == 0):    # initial   -> penalized
            state = 10
        elif(buttonState == 10): # penalized -> playing
            state = 3
        elif(buttonState == 3):  # playing   -> penalized
            state = 10
        else:                    # all other states ? -> playing
            state = 3
        return state
    
    def getSetup(self):
        """Invoke manual setup"""
        return self.bc.getSetup()

    def getTeamNumber(self):
        """ The current team number """
        return self.team

    def getRobotNumber(self):
        """ The current robot number """
        return self.robot

    def getTeamColor(self, side):
        """ The current team color """
        return self.gc.getTeamColor(side)

    def getSecondaryState(self):
        """ If in penalty state, return True """
        if self.gc.controlledRefresh():
            return self.gc.getSecondaryState()
        return self.secondaryState

    def getMatchInfo(self):
        """ The current teamColor and penalty phase y/n """
        teamColor = penalty = 0
        if self.gc.controlledRefresh():
            teamColor = self.gc.getTeamColor('we')
            penalty = self.gc.getSecondaryState()
        else:
            (teamColor, penalty) = self.bc.getSetup()
        self.secondaryState = penalty
        return (teamColor, penalty)

    def close(self):
        """ Safely closes this thread """
        self.running = False
        self.gc.close()

if __name__ == '__main__':
    sc = StateController()
    sc.start()
    while (sc.getState() != 4):
        pass
    sc.close()