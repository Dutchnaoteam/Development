import pygame
import sys

# initialize input controller
def init(argv):
    pygame.init()
    interface = pygame.display.set_mode([200,95])
    pygame.display.set_caption("keyboardController")
    font = pygame.font.Font(None, 20)
    ID_text1 = font.render("Pygame Keyboard Input",True,[255,255,255])
    ID_text2 = font.render("---------------------",True,[255,255,255])
    ID_text3 = font.render("Press any Key...",True,[255,255,255])
    ID_text4 = font.render("(Press 'Esc' to quit)",True,[255,255,255])
    interface.blit(ID_text1, [10,10])
    interface.blit(ID_text2, [10,30])
    interface.blit(ID_text3, [10,50])
    interface.blit(ID_text4, [10,70])
    pygame.display.update()

# return name of hardcoded button definition which quits the program 
def getQuitCommand():
    return "Esc" 
    
# retrieve an action/event made by the input-system    
def getAction():
    # clear event stack to prevent sudden command-overhead
    #  (which happends when robot stalls and an user is pressing a lot of buttons)
    pygame.event.clear()
    # retrieve event
    event = pygame.event.wait()
    # check if 'quit'-command has been pressed, or input window is closed
    if (event.type == pygame.QUIT):
        return "quit"
    elif (event.type == 2 or event.type == 3):
        if (event.key == 27): #escape character
            pygame.quit()
            return "quit"
        else:
            #put relevant event-data into a nice tuple (instead of dictionary)
            return (event.type, event.key)
    else:
        # a unknown/undefined event occured
        return None