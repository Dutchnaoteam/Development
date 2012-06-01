########################
# REMOTE NAO CONTROL
# April 2012 - Hessel van der Molen
# (c) Dutch Nao Team, licensed under GNU-GPL v3.0 
#
# HOW TO USE:
# 1) Make sure you have installed:
#   - Python 2.7
#   - Naoqi SDK 12.3    (for python 2.7)
#   - Pygame            (for Python 2.7)
# 2) Determine the type of input device you want to use (keyboard, joystick..)
# 3) Check if <inputdevice>.py exists in the 'lib' directory
#           (if not, you have to create it yourself)
# 4) Determine the input-processor & motion-files
#           (you can made these yourself, or use the defaults in 'defaults')
# 5) Connect Nao & Computer to same network
# 6) get Nao-ipadress
# 7) In terminal, goto the dir containing the above described files 
# 8) run: 
#      terminal> python main.py <InputDevice> <EventProcessFile> <NaoIPadress> [optional: <inputID>]
# 7) enjoy :)
#
import sys
import platform
import os
import time

##########################
##      CLASSES
#############

class termOutput:
    cmdDict = {}
    cmdIdx = 0
    cmdSize = 10
    eventHandler = None
    input = None
    system = None
    
    def __init__(self, cmdSize, eventHandler, input, system):
        self.cmdSize = cmdSize
        self.eventHandler = eventHandler
        self.input = input
        self.system = system
        self.clear()
        
    #display a message that the cmd is executing...
    def execute(self, cmd):
        self.cmdDict[self.cmdIdx] = cmd
        if ((len(self.cmdDict) > self.cmdSize) and (self.cmdSize != -1)):
            del self.cmdDict[self.cmdIdx - self.cmdSize]
        self.refresh()
    
    #display a message that the cmd is executed
    def done(self):
        self.refreshLine()
        #increase cmd-index
        self.cmdIdx += 1

    #display the last 'cmdSize' commands from command-list
    # --> if 'cmdSize' = -1, all commands are shown
    def refresh(self):
        if (((self.cmdSize == -1) and (self.cmdIdx == 0)) or (self.cmdSize != -1)):
            self.clear()
            
            sys.stdout.write('\n')
            sys.stdout.write("   --------- REMOTE NAO CONTROL --------- " + '\n')
            sys.stdout.write("           http://dutchnaoteam.nl         " + '\n')
            sys.stdout.write("   -------------------------------------- " + '\n')
            sys.stdout.write('\n')
            sys.stdout.write("  Button Usage for system: \n")
            sys.stdout.write("   (input:" + self.system[0] + ", event-handler:" + self.system[1] + ") \n")
            sys.stdout.write('\n')
            sys.stdout.write("  Press '" + input.getQuitCommand() + "' to quit." '\n')
            sys.stdout.write('\n')
            sys.stdout.write( eventHandler.getButtonDefinition() )
            sys.stdout.write('\n')
            sys.stdout.write("   -------------------------------------- " + '\n')
            
        if (self.cmdSize != -1):    
        
            #print finished lines
            s = max(self.cmdIdx - self.cmdSize + 1, 0)
            for i in xrange(s, self.cmdIdx):
                sys.stdout.write(self.formatLine( i ))
                sys.stdout.write(" Done" + '\n')
                
            #print last send command
            if (self.cmdIdx in self.cmdDict):
                sys.stdout.write(self.formatLine( self.cmdIdx ))
            
        else:
            if (len(self.cmdDict) > 0):
                sys.stdout.write(self.formatLine(self.cmdIdx))
        
    def refreshLine(self):
        sys.stdout.write('\r' + self.formatLine(self.cmdIdx) + " Done" + '\n')
        self.waiting()
    
    def waiting(self):
        sys.stdout.write("  Ready for input...")
        
    def formatLine(self,idx):
        line = "\r  [" + str(idx) + "]" + '\t'
        line += "Sending command: '"
        line += self.cmdDict[idx]
        line += "' ..."
        return line
    
    #clear display
    def clear(self):
        if platform.system() == 'Windows':
            os.system('cls')
        else:
            os.system('clear')

##########################
##      FUNCTIONS
#############
            
def listFiles(dir):
    sys.path.append(dir)
    subdirlist = []
    for item in os.listdir(dir):
        founditem = os.path.join(dir,item)
        if not os.path.isfile(founditem):
            subdirlist.append(founditem)
        for subdir in subdirlist:
            listFiles(subdir) 
            
##########################
##      SYSTEM CALL
#############
 
arguments = len(sys.argv) - 2

if (len(sys.argv) <= 1) or (sys.argv[1] == "help"):
    sys.stdout.write( '\n')
    sys.stdout.write( "Usage:" + '\n\n')
    sys.stdout.write( "bash> python main.py <NaoIPadress> [-i <..> -p <..> -id <..> -d <..> -u <...>]" + '\n\n')    
    sys.stdout.write( "    <NaoIPadress>                            \n          ip adress of Nao, e.g. 192.168.0.24" + '\n\n')
    sys.stdout.write( "-i  <InputDevice>      default: 'keyboard'   \n          type of inputDevice (e.g. 'keyboard' or 'joystick')" + '\n\n')
    sys.stdout.write( "-p  <EventHandler>     default: 'dummy'      \n          name of file which processes data of <inputDevice> (e.g. 'keyDefault')" + '\n\n')
    sys.stdout.write( "-d  <displayLines>     default: '10'         \n          number of commands shown in output, -1 = all" + '\n\n')
    sys.stdout.write( "-id <inputID>          default: '0'          \n          ID of input-object to use when multiple are connected" + '\n\n')
    sys.stdout.write( "-u  <updateFrequency>  default: '10'         \n          maximum number of processable-events processed per second" + '\n\n')
    sys.stdout.write( '\n')
elif (arguments%2 == 1):
    sys.stdout.write( "Error: not an even number of arguments provided:" + '\n')
    sys.stdout.write( str(len(sys.argv)) + " " + str(sys.argv) + '\n')
else: 
    #default values
    inputType           = 'keyboard'
    inputTypeID         = 0
    eventHandlerFile    = 'dummy'
    cmdLines            = 10
    robotIPadress       = sys.argv[1]
    updateFreq          = 10 #updates per second
    
    # parse commands
    for i in range(arguments/2):
        cmd = sys.argv[i*2+2]
        val = sys.argv[i*2+3]
        
        if (cmd == '-p'):           #processfile
            eventHandlerFile = val
        elif (cmd == '-i'):         #input system
            inputType = val
        elif (cmd == '-id'):        #input system ID    
            inputTypeID = int(val)
        elif (cmd == '-d'):         #number of display-lines
            cmdLines = int(val)
        elif (cmd == '-u'):         #number of display-lines
            updateFreq = int(val)
        else:                       # not recognised
            sys.stdout.write( "Unknown Command '" + cmd + "' with value '" + str(val) + "', command ommitted." + '\n')
    

    #start system
    sys.stdout.write( "> Searching folders in current directory... " )
    listFiles(os.getcwd())
    sys.stdout.write( "\r> Searching folders in current directory... done" + '\n')   
  
  
    sys.stdout.write( "> Importing event-handler... \n")
    try:
        eventHandler = __import__(eventHandlerFile)
        if (not hasattr(eventHandler, "init")):
            sys.stdout.write("\nError: event-handler '" + eventHandlerFile + "' does not contain the function: 'init'" + '\n')
            exit()
        elif (not hasattr(eventHandler, "getButtonDefinition")):
            sys.stdout.write("\nError: event-handler '" + eventHandlerFile + "' does not contain the function: 'getButtonDefinition'" + '\n')
            exit()
        elif (not hasattr(eventHandler, "processEvent")):
            sys.stdout.write("\nError: event-handler '" + eventHandlerFile + "' does not contain the function: 'processEvent'" + '\n')
            exit()
        eventHandler.init(robotIPadress)
    except Exception, ee:
        sys.stdout.write( '\n>> ' + str(ee) + '\n\n')
        sys.stdout.write( "Error: can't load event-handler: '" + eventHandlerFile + "'" + '\n')
        exit()
    sys.stdout.write( "\r> Importing event-handler ... done" + '\n')
    
    
    sys.stdout.write( "> Initializing input-system... " )
    try:
        input = __import__(inputType)
        if (not hasattr(input, "init")):
            sys.stdout.write("\nError: input-system '" + inputType + "' does contain the function: 'init'" + '\n')
            exit()
        elif (not hasattr(input, "getQuitCommand")):
            sys.stdout.write("\nError: input-system  '" + inputType + "' does contain the function: 'getQuitCommand'" + '\n')
            exit()
        elif (not hasattr(input, "getAction")):
            sys.stdout.write("\nError: input-system  '" + inputType + "' does contain the function: 'getAction'" + '\n')
            exit()      
        input.init(inputTypeID)
    except Exception, ee:
        sys.stdout.write( '\n>> ' + str(ee) + '\n\n')
        sys.stdout.write( "Error: can't load input-system: '" + inputType + "'" + '\n')
        exit()
    sys.stdout.write( "\r> Initializing input-system... done" + '\n')

    time.sleep(2)
    
    #setup display (output)
    output = termOutput(cmdLines, eventHandler, input, (inputType, eventHandlerFile))
    output.refresh()
    output.waiting()

    updateTime = 1.0/updateFreq
    
    #start reading input
    while True:
    
        try:
            st = time.time()
            #print "st: " + str(st)
            
            #get input & process input
            action = input.getAction()
            if (action == "quit"): 
                input.quit()
                sys.stdout.write( "Quitting system" + '\n')
                exit()
            elif ( not(action == None)):
                eventHandler.processEvent(output, action)
                
            # check updateFrequency
            et = time.time()
            #print "et: " + str(et)
            dt = et - st
            #print "dt: " + str(dt)
            #print "uT: " + str(updateTime)
            if (dt < updateTime):
                #print("wait: " + str(updateTime - dt))
                time.sleep(updateTime - dt)
            
        except Exception, ee:
            input.quit()
            print(str(ee))
            sys.stdout.write( "Quitting system" + '\n')
            exit()            