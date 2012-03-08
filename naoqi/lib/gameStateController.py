# File: gameStateController
# File: gameStateController
# By: Camiel Verschoor, Sander Nugteren & Erik van Egmond

from socket import *
import time
import gameController as gameC
import buttonController as buttonC
import threading

class stateController(threading.Thread):
    # VARIABLES
    f = open('/home/nao/naoinfo/NAOINFO.txt','r')
    robot = int(f.readline())
    team = int(f.readline())
    state = 0
    gcActive = True
    lastCheck = 0
    bc = buttonC.buttonController()
    gc = gameC.gameController(team)

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name
        self.running = True

    def __del__(self):
        self.running = False
        self.gc.close()

    def run(self):
        gcState = 0
        buttonState = 0
        counter = 0
        now = time.time()
        while(self.running):
            counter += 1
            # if gamecontroller active
            if self.gc.controlledRefresh():
                gcState = self.gc.getGameState()                # get state from GameController
                buttonState = self.listenToButtons(buttonState) # get buttonstate 

                if (buttonState == 10 or self.gc.getPenalty(self.robot, self.team)):
                    self.state = 10
                else:
                    self.state = gcState
            # if gamecontroller not active, listen to buttons for some time (10 seconds) then try refreshing
            else: 
                print 'else'
                now = time.time()
                while time.time() - now < 10.0:
                    self.state = self.listenToButtons(buttonState)
            print 'gamecontroller state : ', self.state
            if counter % 100 == 0:
                print 'Time for 100 iterations: ', (time.time()-now) / 100.0
                now = time.time()
                
    def getState(self):
        return self.state

    def listenToButtons(self, buttonState):
        state = 0
        if self.bc.getChestButton(): #change the phase if the ChestButton was pressed
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
        return self.gc.getSecondaryState()

    def getMatchInfo(self):
        if self.gc.controlledRefresh():
            teamColor = self.gc.getTeamColor('we')
            kickOff = self.gc.getKickOff()
            penalty = self.gc.getSecondaryState()
        else:
            (teamColor, kickOff, penalty) = self.bc.getSetup()
        return (teamColor, kickOff, penalty)


    # Closes thread
    def close(self):
        self.running = False
        self.gc.close()

# This code will only be executed if invoked directly. Not when imported from another file.
# It shows how to use this module
if __name__ == '__main__':
    sc = stateController("stateController")
    sc.start()
    now = time.time()
    while (sc.getState() != 4):
        pass
    sc.close()
