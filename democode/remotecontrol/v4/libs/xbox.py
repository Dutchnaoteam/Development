import pygame
import sys

# initialize input controller
def init(inputID):
    pygame.init()
    pygame.joystick.init()
    joysticksFound = pygame.joystick.get_count()
    if (joysticksFound > 0):
        sys.stdout.write( "found: " + str(joysticksFound) + " joystick(s)" + '\n')
        
        #get all joysticks
        joysticks = {}
        for x in range(joysticksFound):
            joysticks[x] = pygame.joystick.Joystick(x)
            sys.stdout.write( ">>> Joysticks('" + str(x) + "'): " + joystick.get_name() + '\n')
        
        #select joystick
        sys.stdout.write( ">> Selected joystick: #" + str(inputID) + '\n')
        joystick = joysticks[inputID]	
        joystick.init()
        sys.stdout.write( ">> Joystick initialized: "  + joystick.get_name() + '\n')
    else:
        sys.stdout.write( "\nError: No joystick is found" + '\n')
        pygame.quit()
        exit()
        
# return name of hardcoded button definition which quits the program 
def getQuitCommand():
    return "back" 

# retrieve an action/event made by the input-system
def getAction():
    # clear event stack to prevent sudden command-overhead
    #  (which happends when robot stalls and an user is pressing a lot of buttons)
    pygame.event.clear()
    # retrieve event
    event = pygame.event.wait()
    # check if 'quit'-command has been pressed
    if (event.type == 10):
        if (event.button == 6): #xbox: 'back'-button
            pygame.quit()
            return "quit"
    else:
        return event