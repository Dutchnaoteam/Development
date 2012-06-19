########################
# REMOTE NAO CONTROL - README.txt V0.1
# April 2012 - Hessel van der Molen
# (c) Dutch Nao Team, licensed under GNU-GPL v3.0 
# http://dutchnaoteam.nl
########################

QUICKSTART:
#################
1) Make sure you have installed:
  - Python 2.7
  - Naoqi SDK 12.3    (for python 2.7) [used by libs & eventHandlers]
  - Pygame            (for Python 2.7) [used by libs & eventHandlers]
2) Determine the type of input device you want to use (keyboard, xbox..)
3) Check if <inputdevice>.py exists in the 'lib' directory
          (if not, you have to create it yourself [see README] )
          (default: keyboard)
4) Determine the eventHandler to use.
          (provided handlers can be found in the 'eventHandler' directory)
          (see README for instructions to build your own)
          (default: dummy)
5) Connect Nao & Computer to same network 
6) Get Nao-ipadress
7) In terminal, goto the directory containing 'main.py' 
8) run: 
     terminal> python main.py <NAOipadress> [-i <inputDevice> -p <eventHandler>]
9) enjoy :)

NOTE: for more options, run:
     terminal> python main.py help
     
     
HOW DOES THE SYSTEM WORK?
#################
The presented framework consists of 4 modules: a display, an input, a processer and a main module.

> mainmodule: 
Verifies and initializes the input & processer module. It is also responsible for retrieving events
from the input modules and passing it to the processor (eventHandler). Finally it regulates the 
frequency of calls to the processor, making sure that the robot does not recieve an overload and 
it initializes the display module.
> inputmodule: [Lib]
Retrieves events from an input device. When the mainmodule asks for an event, the input modules returns it
> processermodule: [eventHandler]
Processes events passed from the main module. This module recieves a pointer from the main module to
the display module, enabling it to display send instructions (recieved events).
> display module
Displays button-usage and instructions which are send to the robot

These modules are connected as follow:

terminal --->  [mainmodule]
                 ^  ^  ^
                 |  |  +---> [input]
                 |  +------> [processor] <-+
                 |                         |
                 +---------> [display] <---+
                 
From the terminal, the main module is called. This main module validates the input & processor modules, 
checking if these files contain errors and contain the correct interface.
If a module has passed the tests, it is initialized. 
If it fails a test, the framework terminates (while reporting the error)
After both modules are initialized, the display module is called.
The main module now enters an infinit loop, asking for events from the input module and passing these events
to the processor module. If an error occures the system will shut down.


CREATING A NEW EVENTHANDLER
#################
An eventHandler consists of (at least) the following interfaces:

- init(<naoipadress>)
- getButtonDefinition()
- processEvent(display, event)

> init(<naoipadress>)
The init-interface recieves the ipadress given by the user at the commandline-interface.
Using this ip-adress, the init-function should setup a connection with the robot.
If necessary it should setup and initialize additional datastructures and connections
'init(<naoipadress>)' is called only once by the main-module, after validation.
The framework does not expect a return of this interface.

> getButtonDefinition()
This interface contains a string defining the button-usage. The display module calls this function
and prints the retrieved string in its output. A line-break in the text is simply created by adding
"\n" in the string. The display module expects a single string as return value.

> processEvent(display, event)
The framework passes a pointer to the display module and an event to this interface. There are no
guidelines of how to process an event: the event-data structure depends on the library implementation.
Use the dummy-eventHandler to print events in order to determine the data-structure.
With use of the 'display.execute(<string>)' and 'display.done()' commands, a message can be send to the display.
The 'display.execute(<string>)' results in the message 'Sending command <string> ...'.
If 'display.done()' is called after execution of some code, the display adds 'done' to the message and will 
display that it is ready to recieve new commands.
The framework does not expect a return of this interface.


CREATING A NEW LIBRARY
#################

A library consists of (at least) the following interfaces:

- init(<inputID>)
- getQuitCommand()
- getAction()

> init(<inputID>)
The init-interface should initialize the input device and event-retrievement.
The framework does not depend on event-structure, so any implementation can be used.
In the provided libraries the pygame event-queue is used for its simplicity.
No return is expected.

> getQuitCommand()
This function should return a string, with the textual name of the 'quit'-button. 
The 'quit'-button is library defined and cannot be used in the eventHandler to execute some action.

> getAction()
'getAction()' should return an event-data structure, or the string "quit" when the 'quit'-event occured.
Since the framework does not rely on the event-data structure, any implementation can be used.