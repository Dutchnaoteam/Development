import time
import Queue
import threading
from socket import *

class Receiver(threading.Thread):
    '''
    Connects to every client specified by a number of connections
    Receives data from every client (serial, not parallel)

    '''
    conn = list()
    connections = 0
    on = False
    data = ''
    extractData = Queue.Queue()
    serv = None
    
    def __init__(self, name, ADDR = ('', 4242)):        
        '''Constructor for class Receiver
        
        Arguments:
        name        -- name of the thread
        '''
        threading.Thread.__init__(self)
        self.name        = name
        self.conn        = list()      # reset list to prevent pipe errors
        
        # set up the server
        self.serv = socket( AF_INET, SOCK_STREAM )    
        self.serv.bind(ADDR)
        self.serv.listen(2)    
    
    def __del__(self):
        '''Destructor for class Receiver'''
        self.on = False         # stop programs main loop
        self.extractData.put('STOP')

    def run(self):    
        '''Main program loop of class Receiver
        
        Initiates by connecting to every client, sends start message.
        Enters loop which asks for data from clients to be extracted by main program.
        
        '''
        self.on = True
        print 'Accepting connection.'
        connect,addr = self.serv.accept() 
        print 'Connection made.'
        self.conn.append(connect)

        # send a starting message to all clients
        for c in self.conn:
            c.send('GO')    # start sending data
            
        # workaround for breaking out of the while loop when an exception is found
        doBreak = False
        
        # while receiving, get up to 4096 bytes of data from each connection
        while self.on and not doBreak:
            self.data = ''
            for c in self.conn:
                try:
                    self.data += c.recv(4096)
                    time.sleep(1)
                    c.send('GO')
                except:
                    print 'unable to receive data from client'
                    doBreak = True

            # update the new data if receiving any
            if self.data:
                self.extractData.put(self.data)
        
        # if client disconnects, stop extracting data
        print 'Extracting of data stopped'
        self.extractData.put('STOP')
        for c in self.conn:
            c.recv(4096)
            try:
                c.send('STOP')      # send stop message to remaining clients
            except:
                pass
        self.serv.close()           # close socket
                    
    def getData(self):
        '''Return data as specified in run()'''
        if (not(self.extractData.empty())):
            return self.extractData.get() # deliver data in parsed form 
        else:
            return False
        
    def stopRec(self):
        '''Stops main program loop'''
        self.on = False        # stop program

def startServer(connections = 1, interval = 9999999999):
    '''Start mimicking of user
    
    Arguments:
    connections -- number of clients to receive data from
    interval    -- number of seconds to listen to client
    '''
    
    # start an arbitrary number of connections by a thread 
    rec = Receiver('Receive')
    rec.start()        
    # wait for data to be sent
    while not(rec.getData()):
        time.sleep(0.5)
        print 'No data yet..'
        doBreak = False
        
        # start interval in which mimicking occurs
        now = time.time()
        while time.time() - now < interval and not(doBreak):
            data = rec.getData()
            if data == 'STOP':
                doBreak = True
                
            if data:
                print data            
        rec.stopRec()
        print "Server stopped"

if __name__=="__main__":
    startServer()
