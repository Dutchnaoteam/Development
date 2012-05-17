pygame = None
sys = None

def setGlobal(p, s):
    global pygame, sys
    pygame = p
    sys = s

def initkeyboard():
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

def getAction():
    event = pygame.event.wait()
    if (event.type == pygame.QUIT):
        return "quit"
    elif (event.type == 2 or event.type == 3):
        if (event.key == 27): #escape character
            return "quit"
        else:
            return (event.type, event.key)
    else:
        return None