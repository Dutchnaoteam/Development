pygame = None
sys = None

def setGlobal(p, s):
    global pygame, sys
    pygame = p
    sys = s
    
def initjoystick():
    pygame.joystick.init()
    joysticksFound = pygame.joystick.get_count()
    if (joysticksFound > 0):
        sys.stdout.write( "found: " + str(joysticksFound) + " joystick(s)" + '\n')
        joystickID = 0
        if (len(sys.argv) > 2):
            joystickID = int(sys.argv[2])
        sys.stdout.write( ">>> selected joystick: " + str(joystickID) + '\n')
        joystick = pygame.joystick.Joystick(joystickID)	
        joystick.init()
        sys.stdout.write( ">>> joystick initialized: "  + joystick.get_name() + '\n')
    else:
        sys.stdout.write( "\nError: No joystick is found" + '\n')
        exit
        
def getAction():
    event = pygame.event.wait()
    if (event.type == 10):  #back-button is pressed
        if (event.button == 6):
            return "quit"
    else:
        return event