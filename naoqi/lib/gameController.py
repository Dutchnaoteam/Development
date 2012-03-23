# File: GameController
# By: Sander Nugteren and Erik van Egmond

from socket import *
import time

# Double Dictionary
class Ddict(dict):
    def __init__(self, default=None):
        self.default = default

    def __getitem__(self, key):
        if not self.has_key(key):
            self[key] = self.default()
        return dict.__getitem__(self, key)

# Game Controller
class gameController():
    '''
    GameController contains the following methods:
    __init__()
    refresh()
    getVersion()
    getPenalty()
    getAvailableNaos()
    getUnpenalizedCountdown()
    getScore()
    getRobotsPerTeam()
    getGameState()
    getFirstHalf()
    getKickoff()
    getSecondaryState()
    getLastDropinTeam()
    getSecondsSinceLastDropin()
    getSecondsRemaining()
    getTeamColor()
    getGoalColor()

    More info about the GameController: http://sourceforge.net/projects/robocupgc/
    '''
    # VARIABLES
    ourTeamNum = 0
    socket = 0
    version = (0, 0, 0, 0)
    robotsPerTeam = 0
    gameState = 0
    firstHalf = True
    kickoff = 0
    secondaryState = 0
    lastDropinTeam = 0
    secondsSinceLastDropin = 0
    secondsRemaining = 600
    we = Ddict(dict)
    them = Ddict(dict)
    
    ourGC = True
    # CONSTRUCTOR
    def __init__(self, ourTeamNum, host = '255.255.255.255', port=3838, interval=0.25):
        '''
        Contstructor for the GameController class. Creates an instance of GameController which listens to the specified host and port every interval seconds.
        Defaults are host = 255.255.255.255, port = 3838 interval = 0,25.
        '''
        self.ourTeamNum = ourTeamNum
        self.time = 0
        self.interval = interval
        self.host = host
        self.port = port
        # Create socket and bind to address
        self.socket = socket(AF_INET,SOCK_DGRAM,)
        self.socket.bind((host,port))
        self.socket.setblocking(0)

    # DESTRUCTOR
    def __del__(self):
        self.socket.close()

    def close(self):
        self.socket.close()
    
    def controlledRefresh(self):
        active = False
        data = ''
        now = time.time()
            
        while time.time() - now < 4:
            try:
                data, addr = self.socket.recvfrom(1024)
            except:
                pass
            if data:
                self.refresh(data)
                active = True
                break
        return active
        
    def refresh(self, data):
        '''
        Refreshes all the (private) variables by reading the incoming Gamecontroller data at the specified port at the specified host. Returns False if the gamestate is finished, returns True otherwise.
        '''
        
        if time.time() - self.time > self.interval:
            # Try to listen to the socket
            # FIXME gebruik iets als select.select([self.scoket], [self.socket], [self.socket], 1)
            # om te kijken of er al nieuwe data binnen is, dan is de timer niet nodig
            # Set the socket parameters
                
            if not(ord(data[68]) == self.ourTeamNum or ord(data[20]) == self.ourTeamNum):
                print 'wrong gc'
            else:
                self.header = data[0:4]
                # Data
                self.gameState = ord(data[9])
                self.version = (ord(data[7]), ord(data[6]), ord(data[5]), ord(data[4]))
                self.robotsPerTeam = ord(data[8])
                self.firstHalf = ord(data[10])
                self.kickoff = ord(data[11])
                self.secondaryState = ord(data[12])
                self.lastDropinTeam = ord(data[13])
                self.secondsSinceLastDropin = self.stringToDecimal(data[14:15])
                self.secondsRemaining = self.stringToDecimal(data[16:19])

                for t in (0, 1):
                    # Team is a pointer to the team dictionary
                    team = self.we if ord(data[20+(48*t)]) == self.ourTeamNum else self.them
                    team['teamColor'] = ord(data[21+(48*t)])
                    team['goalColor'] = ord(data[22+(48*t)])
                    team['score'] = ord(data[23+(48*t)])
                    #likewise for robot
                    for r in xrange(0, self.robotsPerTeam):
                        # robot = team['nao'+str(r)]
                        team['nao'+str(r)]['penalty'] = self.stringToDecimal([data[24 + r*4 +(48*t)], data[25 + r*4+(48*t)]])
                        team['nao'+str(r)]['unpenalizedCountdown'] = self.stringToDecimal([data[26+r*4+(48*t)], data[27+r*4+(48*t)]])
                        #print 'r' + str(r)
                        #print _stringToDecimal([data[24 + r*4 +(48*t)], data[25 + r*4+(48*t)]])

                self.time = time.time()
    
    def gcActive():
        return self.gcActive
    
    def stringToDecimal(self, data):
        res = "0"
        for i in range(len(data)-1,-1,-1):
            s = str(bin(ord(data[i])))
            s = s[2:len(s)]
            while (len(s) < 8):
                s = "0"+s
            res += s
        return int(res,2)

    # GET METHODS
    def getVersion(self):
        '''
        Returns the version of the RoboCupGameControlData
        '''
        return self.version

    def getPenalty(self, robot, team=6):
        '''
        Returns the penalty of the robot'th nao in the given team. If no team is specified, team = 6 (the Dutch Nao Team for SPL2011).
        BALL_HOLDING            1
        PLAYER_PUSHING          2
        OBSTRUCTION             3
        INACTIVE_PLAYER         4
        ILLEGAL_DEFENDER        5
        LEAVING_THE_FIELD       6
        PLAYING_WITH_HANDS      7
        REQUEST_FOR_PICKUP      8
        MANUAL                  15
        '''
        penalty = 0
        if team == self.ourTeamNum:
            penalty = self.we['nao'+str(robot-1)]['penalty']
        else:
            penalty = self.them['nao'+str(robot-1)]['penalty']
        return penalty
        
    def getAvailableNaos(self, team=6):
        '''
        Returns an array with booleans representing which robots are penalized in the given team. For example, if the array is [1,0,1,1] then robot 2 is penalized. If no team is specified, team = 6 (the Dutch Nao Team for SPL2011).
        '''
        res = zeros(4, Int)
        for i in xrange(0, self.robotsPerTeam-1):
            res[i] = self.getPenalty(i, team)==0
        return res

    def getUnpenalizedCountdown(self, robot, team=6):
        '''
        Returns how many seconds until the robot'th nao in the given team is going to unpenalized. If no team is specified, team = 6 is used (the Dutch Nao Team for SPL2011).
        '''
        countdown = 0
        if team == self.ourTeamNum:
            countdown = self.we['nao'+str(robot)]['unpenalizedCountdown']
        else:
            countdown = self.them['nao'+str(robot)]['unpenalizedCountdown']
        return countdown
        
    def getScore(self):
        '''
        Returns the score in the format: (<Our score>,<Their score>)
        '''
        return (self.we['score'], self.them['score'])

    def getRobotsPerTeam(self):
        '''
        Returns how many robots are used in each team.
        '''
        return self.robotsPerTeam

    def getGameState(self):
        '''
        Returns the GameState.
        INITIAL               0
        READY                 1
        SET                   2
        PLAYING               3
        FINISHED              4
        '''
        return self.gameState
               
    def getFirstHalf(self):
        '''
        Returns whether we're currently in the first half of the match.
        '''
        return self.firstHalf

    def getKickOff(self):
        '''
        Returns which team has the kickoff.
        '''
        return self.kickoff

    def getSecondaryState(self):
        '''
        Returns the secondary GameState
        NORMAL               0
        PENALTYSHOOT         1
        '''    
        return self.secondaryState

    def getLastDropinTeam(self):
        '''
        Returns which team caused the last dropin.
        '''
        return self.lastDropinTeam

    def getSecondsSinceLastDropin(self):
        '''
        Returns the seconds since the last dropin (Cpt. Obvious)
        '''
        return self.lastDropinTeam

    def getSecondsRemaining(self):
        '''
        Returns the remaining seconds, for this half.
        '''
        return self.secondsRemaining

    def getTeamColor(self,team):
        '''
        Returns the color of team 'team'.
        0 = CYAN
        1 = MAGENTA
        '''
        teamcolor = 0
        if team in (6, 'we', 'us'):
            teamcolor = self.we['teamColor']
        else:
            teamcolor = self.them['teamColor']
        return teamcolor
        
    def getGoalColor(self,team):
        '''
        Returns the color of the goal of team 'team'.
        0 = BLUE
        1 = YELLOW
        '''
        goalcolor = 0
        if team in (6, 'we', 'us'):
            goalcolor = self.we['goalColor']
        else:
            goalcolor = self.them['goalColor']
        return goalcolor
