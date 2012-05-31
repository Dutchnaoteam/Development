import pygame
import sys

buttonState = {}
joystickState = {}
QUITBUTTON = 6

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
            sys.stdout.write( ">>> Joysticks('" + str(x) + "'): " + joysticks[x].get_name() + '\n')
        
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
    global buttonState
    global joystickState
    event = None
    
    # check if there are items in the queue
    if (not emptyQueue()):
        #get event
        event = pollEvent()

        #check if there are multiple items in the queue
        # ifso, validateEventQueue (return None if no valid events are on the queue)
        if (not emptyQueue()):
            event = validateEventQueue(event)
            if (event != None):
                event = checkJoystickEvent(event)

    #no items in queue & no legal items in queue
    # --> wait for legal event
    if (event == None) or (not validateEvent(event, "wait")):
        event = waitForEvent()
   
    #register button press / joystick movement
    if ((event.type == pygame.JOYBUTTONDOWN) or (event.type == pygame.JOYBUTTONUP)):
        buttonState[event.button] = event.type
    if (event.type == pygame.JOYAXISMOTION):
        joystickState[event.axis] = event.dict["value"]
        
    # check if 'quit'-command has been pressed
    if (event.type == pygame.JOYBUTTONDOWN):
        if (event.button == QUITBUTTON): #xbox: 'back'-button
            return "quit"          
    
    return event
        
def quit():
    print "input:quit"
    pygame.quit()
 
#validate event-queue 
def validateEventQueue(event):
    #if first event is a joystick-movement, allow it.
    # --> joystickmotion is (almost) always a queue.
    if (event.type == pygame.JOYAXISMOTION):
        return event
    elif (validateEvent(event, "queue")):
        return event
    else:
        #validate alle events in queue untill:
        # - a valid event is found
        # - or, no events are left
        while (True):
            event = pollEvent()
            if (event.type == pygame.NOEVENT):
                return None
            if (validateEvent(event, "queue")):
                return event

#wait for next event
def waitForEvent():
    while (True):
        event = pygame.event.wait()
        if (hasattr(event, "type")):
            event = processEvent(event)
            if (validateEvent(event, "wait")):
                return event
 
#validate event
def validateEvent(event, type):    
    # only allow:
    # - joystick release (value +/- = 0)
    # - hat release
    # - button release
    if (type == "queue"):
        #print "queue: " + str(event) 
        #joystick is released
        if (event.type == pygame.JOYAXISMOTION):
            if (-0.1 <= event.dict["value"] <= 0.1):
                if (event.axis in joystickState):
                    if (joystickState[event.axis] == event.dict["value"]):
                        return False
                return True
        #hat-pad to original position
        if (event.type == pygame.JOYHATMOTION):
            if (event.dict["value"] == (0,0)):
                return True
        #quit button is pressed
        if (event.type == pygame.JOYBUTTONDOWN):
            if (event.button == QUITBUTTON):
                return True
        #button is previously pressed and now released
        if (event.type == pygame.JOYBUTTONUP):
            if (event.button in buttonState):
                if (buttonState[event.button] == pygame.JOYBUTTONDOWN):
                    return True
   
    #only allow:
    # - changed joystick movement
    # - all other inputs
    if (type == "wait"):
        # only process joystick movement if value differs from previous movement
        if (event.type == pygame.JOYAXISMOTION):
            if (event.axis in joystickState):
                if (joystickState[event.axis] == event.dict["value"]):
                    return False
        return True
        
    return False
    
#check if queue is empty
#empty queue = 'Event(xx-Unknown {})'
def emptyQueue():
    e = peekEvent()
    n = pygame.event.event_name(e.type)
    return n == "Unknown"
    
#check next event
def peekEvent():
    event = pygame.event.peek()
    if (hasattr(event, 'type')):
        return event
    else:
        return pygame.event.Event(pygame.NOEVENT, {})
 
#retrieve event from event-queue
def pollEvent():
    event = pygame.event.poll()
    if (hasattr(event, 'type')):
        #check if event is a joystick event (=queued-data)
        e = checkJoystickEvent(event)
        #map floating points to 1 decimal
        e = processEvent(e)
        return e
    else:
        return pygame.event.Event(pygame.NOEVENT, {})

# check if given event is a joystick-motion
# ifso, search most recent joystick motion in queue (= final position)
def checkJoystickEvent(event):
    if (event.type == pygame.JOYAXISMOTION):
        while (peekEvent().type == pygame.JOYAXISMOTION):
            event = pollEvent()
        
        #while (True):
        #    if (peekEvent().type == pygame.JOYAXISMOTION):
        #        event = pollEvent()
        #    else:
        #        return event
    return event

#process event: continious values are rounded to 1 decimal
def processEvent(event):
    if (event.type == pygame.JOYAXISMOTION):
        event.dict["value"] = round(event.dict["value"], 1)
    return event
