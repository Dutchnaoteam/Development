#Creator: Sander Nugteren, Erik van Egmond, Auke Wiggers
import threading
import earlights as ear
import time
import socket

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
            #logging.info('port '+str(port))
            #logging.info( 'initializing coach' )
            threading.Thread.__init__(self)
            self.name = name
            self.on = True
            #proxy of the nao itself. used to check which action has to be taken
            self.memProxy = memProxy
            self.port = port
            
            self.ownNaoNum = self.memProxy.getData('dntNaoNum')
            self.ear = ear.EarLights('', earProxy)
            self.ear.playerOffAll()
            
            #[timeSinceLastSignalRobot1, timeSinceLastSignalRobot2,...]
            self.activeNAOs = [0,0,0,0]
            self.portlist = [1,2,3,4]
            self.portlist = [self.portlist[i]+ ([port]*4)[i] for i in range(4)]
            self.portlist.remove(port+self.ownNaoNum)
            
            self.sendSocket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            self.sendSocket.bind(('',0))
            self.sendSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.socketList = list()
            for n in self.portlist:
                 s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                 s.bind(('',n))
                 s.setblocking(0)
                 self.socketList.append(s)
            self.distList = [99,99,99,99]
            self.start()
            
            
    
    def __del__(self):
        self.on = False
        for s in self.socketList:
            s.close()
    
    def close(self):
        self.on = False
        for s in self.socketList:
            s.close()
        #logging.info( 'socket closed' )
        print 'sockets closed'
        
    def run(self):
        while self.on:
            try:
                self.receive()
                self.send( self.port )
                self.deviseStrategy(self.ownNaoNum-1)
                time.sleep(0.25)
            except KeyboardInterrupt:
                #loggin.info('keyboard interrupt, closing thread')
                print 'keyboard interrupt, closing thread'
                self.close()
            except Exception as e:
                print e
     

    def receive(self):
        #Keep listening for some time.
        now = time.time()
        for s in self.socketList:
            try:
                data = s.recv(1024)
                self.extractData(data)
            except Exception as e: 
                print 'nothing recieved from '+str(s.getsockname())
                
    def send( self, port ):
        message = self.construct_message()
        self.sendSocket.sendto(message, ('<broadcast>', port+self.ownNaoNum))
            
    def extractData(self, data):
        auth = data[0:3]
        #authenticate the message. We start the message with 'dnt'
        if auth == "dnt": 
            robot = data[3]
            self.distList[int(robot)-1] = float(data[4:9])
            self.activeNAOs[int(robot)-1] = time.time()

        else:
            #logging.warning( "not a valid message" )
            print "not a valid message"
            
    def deviseStrategy(self, me):
        #start finding closest nao
        closest = 99
        closestNao = me#yourself, so good for initial value
        active = [0,0,0,0]
        action = ''
        self.distList[me]=self.memProxy.getData( 'dntBallDist' )
        for i in range(4):
            if time.time()-self.activeNAOs[i] < 0.5 or i == me:
                active[i]=1
                if self.distList[i] and self.distList[i]<closest:
                    closestNao = i
                    closest = self.distList[i]
        if closestNao != 5:
            if closestNao==me:
                action = ''
            else:
                action = 'KeepDistance'    
        #finding closest nao end
        for i in range(4):
            if active[i]:
                self.ear.playerOn(i+1)
            else:
                self.ear.playerOff(i+1)
        #logging.debug( 'action '+action )
        #logging.debug( 'active robots '+ str(active) )
        self.memProxy.insertData( 'dntAction', action ) 
        
    def construct_message( self ):
        auth = "dnt"
        robot = self.ownNaoNum
        balldist = self.memProxy.getData( 'dntBallDist' )
        return auth+str(robot)+self.makeLenght4(balldist)
        
    def makeLenght4(self, num):
        newNum = round(float(num),2)
        if newNum<10:
            return "0"+str(newNum)
        else:
            return str(newNum)