""" 
Creator: Sander Nugteren, Erik van Egmond, Auke Wiggers
"""
import time
import threading
import earlights
from naoqi import ALProxy

"""
we first insert some data that coach needs to know about every Nao
prefix everything with DNT, to have unique names
state is the gamestate (and also if the nao is penalized?)
ballDist is the distance to the ball
phase is what the nao is currently doing (going for the ball, attacking, 
defending)

TODO: als er nog een actie bezig is om de bal te gaan onderscheppen, pass
Als er een Nao bezig is met naar de bal gaan moet die dat constant uitzenden
Als hij de bal schopt stopt hij daarmee. En dan moet er weer een nieuwe cycle 
beginnen van zoeken naar de bal. Het programma moet dan een message sturen aan 
de rest om te stoppen met lopen en een bal te gaan zoeken
"""   
class Coach(threading.Thread):
    def __init__(self, name, ipList, memProxy, ledProxy):
        threading.Thread.__init__(self)
        self.name = name
        #proxy of the nao itself. used to check which action has to be taken
        self.memProxy = memProxy
        self.running = True
        #data the coach should display to the other nao's
        self.memProxy.insertListData([['dnt1', '', 0],\
                                      ['dnt2', '', 0],\
                                      ['dnt3', '', 0],\
                                      ['dnt4', '', 0]]
                                     )
        #make a proxy dict containing proxys of all the other nao's
        self.proxyDict = {}
        self.failedIpList = list()
        self.ipList = ipList
        for ip in ipList:
            # TODO send a reference to memproxies of other players instead
            self.proxyDict[ip] = ALProxy('ALMemory', ip, 9559)
        self.ownNaoNum = self.memProxy.getData('dntNaoNum')
        self.ear = earlights.EarLights( ledProxy)
        self.activeIPs = {}
        self.ear.playerOffAll()
        
    def isActive(self):
        return self.running
        
    def __del__(self):
        self.running = False
    
    def close(self):
        self.running = False
    
    def run(self):
        # Keep listening for some time. If no field player has reported that it
        # found a ball, keep listening until one does 
        now = time.time()
        
        while self.running:
            if len(self.proxyDict) == 0:
                self.close()
                return False
            closestNao = 0
            minDist = 10 
            
            ballSeen = list()
            #see which nao is closest
            #print 'dict:' ,self.proxyDict
            
            print self.activeIPs
            for ip in self.ipList: 
                
                try:
                    # 'receive' messages
                    proxy = self.proxyDict[ip]                       
                    currentDist = proxy.getData('dntBallDist')
                    currentNao = proxy.getData('dntNaoNum')
                    self.activeIPs[ip]=currentNao
                    self.ear.playerOn(currentNao)
                    # track naos that have seen the ball
                    if currentDist:
                        ballSeen.append( currentNao )
                        if currentNao == 1:
                            keeperSawBall = True
                    
                        # update closest nao
                        if currentDist < minDist:
                            minDist = currentDist
                            closestNao = currentNao
                except Exception as inst:
                    print inst
                    self.ipList.remove(ip)
                    self.failedIpList.append(ip)
                    try:
                        self.ear.playerOff(self.activeIPs[ip])
                        del(self.activeIPs[ip])
                    except Exception:
                        pass
                    
                    
            
               
            #check every minute the ip's that could not connect
            if time.time()-now > 60 and self.failedIpList:
                now = time.time()
                self.ipList = self.failedIpList
                self.failedIpList = list()
                for ip in self.ipList: 
                    print '********* RETESTING ', ip, '*********'
                    try:
                        # 'receive' messages
                        proxy = self.proxyDict[ip]                       
                        currentDist = proxy.getData('dntBallDist')
                        currentNao = proxy.getData('dntNaoNum')
                        self.activeIPs[ip]=currentNao
                        self.ear.playerOn(currentNao)
                        #self.ear.playerOn(currentNao)
                        # track naos that have seen the ball
                        if currentDist:
                            ballSeen.append( currentNao )
                            if currentNao == 1:
                                keeperSawBall = True
                        
                            # update closest nao
                            if currentDist < minDist:
                                minDist = currentDist
                                closestNao = currentNao
                    except Exception:
                        self.ipList.remove(ip)
                        self.failedIpList.append(ip)
                        try:
                            self.ear.playerOff(self.activeIPs[ip])
                            del(self.activeIPs[ip])
                        except Exception:
                            pass
                            
                
            
            print 'Saw ball:', ballSeen, 'Closest:', closestNao, 'at:',minDist          
            # For every nao (including keeper, might come in handy later)
            # if keeper, dont alter actions
            if self.ownNaoNum == 1:
                action = ''
            # elif the player is the closest nao, proceed with getting the ball
            elif closestNao == self.ownNaoNum:
                action = ''      
            # elif player is not closest nao, walk somewhere near the ball 
            elif self.ownNaoNum in ballSeen:
                '''
                if keeperSawBall:
                    #action = 'Retreat'
                    action = 'KeepDistance'
                else:
                    action = 'KeepDistance'
                '''
                #Commented out the if, as it doesn't do anything right now
                action = 'KeepDistance'
            # all other cases, proceed as usual        
            else:
                action = ''
            
            # 'Send' messages 
            self.memProxy.insertData( 'dnt' + str(self.ownNaoNum), action )
            
            # pause for a short time
            time.sleep(0.5)

    def getCoachData(self, data):
        return self.memProxy.getData(data)
        
