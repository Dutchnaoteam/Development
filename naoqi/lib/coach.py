#Creator: Sander Nugteren, Erik van Egmond, Auke Wiggers
#Mijn ideeen over communicatie:
#Threadable module, die structs/pickle/json kan senden en ontvangen
#elke nao stuurt hoe ver de bal van hem af is binnen een bepaalde interval
#(niet elke nao hoeft te reporten)
#de keeper beslist wie het dichtst bij de bal is, en dus er heen moet gaan
#de rest doet?
#Als de keeper de bal ziet, dan terug lopen?
#Anders vooruit lopen?

# Notulen
# - Alle data in keeper, naos lezen uit. Reden: Keeper valt uit dan geen problemen met oude waarden. 

import socket
import sys
import struct
import time
import threading
from naoqi import ALProxy

#we first insert some data that coach needs to know about every Nao
#prefix everything with DNT, to have unique names
#state is the gamestate (and also if the nao is penalized?)
#ballDist is the distance to the ball
#phase is what the nao is currently doing (going for the ball, attacking, defending)

class Coach(threading.Thread):
#nao's sturen een dict/json met hun nummer en balloc/afstand
#run blijft even luisteren voor een tijdje tot er iets binnen komt
#onthoudt alleen de nao op die het dichtst bij de bal is.
#geeft die nao de order om naar de bal te gaan.
#als de keeper (op wie dit programma zal runnen) de bal heeft gezien
#dan moet iedereen naar het eigen doel proberen te komen
#anders moet iedereen in de aanval
#stuur boodschappen naar naos.
#TODO: als er nog een actie bezig is om de bal te gaan onderscheppen, pass
#Als er een Nao bezig is met naar de bal gaan moet die dat constant uitzenden
#Als hij de bal schopt stopt hij daarmee. En dan moet er weer een nieuwe cycle beginnen van zoeken naar de bal
#Het programma moet dan een message sturen aan de rest om te stoppen met lopen en een bal te gaan zoeken
#TODO: AlmemProxy dingen bekijken om data te exchangen
# http://users.aldebaran-robotics.com/docs/site_en/bluedoc/ALmemProxy.html
    
    def __init__(self, name, ipList, memProxy):
        threading.Thread.__init__(self)
        self.name = name
        self.memProxy = memProxy
        self.on = True
        #data the coach should display to the other nao's
        self.memProxy.insertListData([['dnt1', '', 0], ['dnt2', '', 0], ['dnt3', '', 0], ['dnt4', '', 0]])
        #make a proxy dict containing proxys of all the other nao's
        self.proxyDict = {}
        for ip in ipList:
            # TODO send a reference to memproxies of other players instead
            self.proxyDict[ip] = ALProxy('ALMemory', ip, 9559)
        self.ownNaoNum = self.memProxy.getData('dntNaoNum')

    def __del__(self):
        self.on = False
    
    def close(self):
        self.on = False
    
    def run(self):
        #Keep listening for some time.
        #If no field player has reported that it found a ball, keep listening until one does 
        while self.on:
            closestNao = 0
            minDist = 10 
            keeperSawBall = False
            
            # #################### messageIn = self.receiveMessage() WHAT DOES THIS LINE DO?!!
            #ga er hier vanuit dat we een python dict/JSON krijgen
            ballSeen = list()
            for ip in self.proxyDict: 
            
                # 'receive' messages
                proxy = self.proxyDict[ip]                       
                currentDist = proxy.getData('dntBallDist')
                currentNao = proxy.getData('dntNaoNum')
                
                # track naos that have seen the ball
                if currentDist:
                    ballSeen.append( currentNao )
                    if currentNao == 1:
                        keeperSawBall = True
                
                    # update closest nao
                    if currentDist < minDist:
                        minDist = currentDist
                        closestNao = currentNao
            print 'Saw ball: ', ballSeen, 'Closest: ' ,closestNao           
            messageOut = list()
            # For every nao (including keeper, might come in handy later)
            # if keeper, dont alter actions
            if self.ownNaoNum == 1:
                action = ''
            # else if player which is the closest nao, prcoeed
            elif closestNao == self.ownNaoNum:
                action = ''      
            # else if player which is not the closest nao, standby (or possibly retreat)
            elif self.ownNaoNum in ballSeen:
                if keeperSawBall:
                    #action = 'Retreat'
                    action = 'KeepDistance'
                else:
                    action = 'KeepDistance'
            # all other cases, proceed as usual        
            else:
                action = ''
            
            # 'Send' messages 
            self.memProxy.insertData( 'dnt' + str(self.ownNaoNum), action )
            
            # pause for a short time
            time.sleep(1)

    def getCoachData(self, data):
        return self.ownProxy.getData(data)
