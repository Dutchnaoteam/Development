import copy
import time
import sys
import os


def init(IPADRESS):
    pass
    
def getButtonDefinition():
    text  = "   Dummy\n"
    text  += "   Press any key...\n"
    return text

def processEvent(display, event):
    display.execute(str(event))
    display.done()
    #time.sleep(1)
    