#Creator: Sander Nugteren, Erik van Egmond, Auke Wiggers
import threading
import earlights as ear
import time
import logging
from socket import *

######
## oude comments
######

#Mijn ideeen over communicatie:
#Threadable module, die structs/pickle/json kan senden en ontvangen
#elke nao stuurt hoe ver de bal van hem af is binnen een bepaalde interval
#(niet elke nao hoeft te reporten)
#de keeper beslist wie het dichtst bij de bal is, en dus er heen moet gaan
#de rest doet?
#Als de keeper de bal ziet, dan terug lopen?
#Anders vooruit lopen?
#
# Notulen
# - Alle data in keeper, naos lezen uit. Reden: Keeper valt uit dan geen problemen met oude waarden. 
#
#we first insert some data that coach needs to know about every Nao
#prefix everything with DNT, to have unique names
#state is the gamestate (and also if the nao is penalized?)
#ballDist is the distance to the ball
#phase is what the nao is currently doing (going for the ball, attacking, defending)
#
#TODO: als er nog een actie bezig is om de bal te gaan onderscheppen, pass
#Als er een Nao bezig is met naar de bal gaan moet die dat constant uitzenden
#Als hij de bal schopt stopt hij daarmee. En dan moet er weer een nieuwe cycle beginnen van zoeken naar de bal
#Het programma moet dan een message sturen aan de rest om te stoppen met lopen en een bal te gaan zoekenimport sys





class coach(threading.Thread):
    def __init__(self, name, memProxy, earProxy, port=9876):
            logging.info( 'initializing coach' )
            threading.Thread.__init__(self)
            self.name = name
            self.on = True
            #proxy of the nao itself. used to check which action has to be taken
            self.memProxy = memProxy
            
            self.s=socket(AF_INET,SOCK_DGRAM)
            self.s.bind(('',port))
            
            self.ownNaoNum = self.memProxy.getData('dntNaoNum')
            
            self.ear = ear.EarLights('', earProxy)
            self.ear.playerOffAll()
            
            #[timeSinceLastSignalRobot1, timeSinceLastSignalRobot2,...]
            self.activeNAOs = [0,0,0,0]
            
            self.distList = [99,99,99,99]
            
            self.start()
            
    
    def __del__(self):
        self.on = False
        self.s.close()
    
    def close(self):
        self.on = False
        self.s.close()
        logging.info( 'socket closed' )
        
    def run(self):
        logging.debug('coach running')
        #Keep listening for some time.
        #If no field player has reported that it found a ball, keep listening until one does 
        now = time.time()
        try:
            while self.on:
                data,addr = self.s.recvfrom(1024)
                self.extractData(data)
                self.deviseStrategy(self.ownNaoNum)
                time.sleep(0.25)
        except KeyboardInterrupt:
            loggin.info('keyboard interrupt, closing thread')
        except Exception as e:
            logging.critical('error [ %s ] in coach, closing thread', e)
        finally:
            self.close()
            
    def extractData(self, data):
        auth = data[0:3]
        #authenticate the message. We start the message with 'dnt'
        if auth == "dnt": 
            robot = data[3]
            #baldist = data[4:9]
            self.distList[int(robot)-1] = float(data[4:9])
            self.activeNAOs[int(robot)-1] = time.time()
            

        else:
            logging.warning( "not a valid message" )
            
    def deviseStrategy(self, me):
        logging.debug('divising strategy...')
        #start finding closest nao
        closest = 99
        closestNao = 5#doesn't excist, so good for initial value
        active = [0,0,0,0]
        for i in range(4):
            if time.time()-self.activeNAOs[i] < 0.5:
                active[i]=1
                logging.debug( 'active nao'+str(i+1) )
                if balldistList[i]<closest:
                    closestNao = i
                    closest = balldistList[i]
        logging.debug( closestNao )
        if closestNao != 5:
            if closestNao==me:
                action = ''
            else:
                action = 'keepDistance'        
        #finding closest nao end
        for i in range(4):
            if active[i]:
                ear.playerOn(i)
            else:
                ear.playerOff(i)
        logging.debug( 'action '+action )
        logging.debug( 'active robots '+ str(active) )
        self.memProxy.insertData( 'dnt'+str(me), action )
        
    def setLeds(self, active):
        for i in range(4):
            if active[i]:
                ear.playerOn(i)
            else:
                ear.playerOff(i)