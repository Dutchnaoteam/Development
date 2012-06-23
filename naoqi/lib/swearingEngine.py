import os
import random


path = '/home/nao/naoqi/swearingEngine/'
program = 'aplay'


def penalized(type):
    rand = random.random()
    #general swearing
    if rand<0.5:
        standard()
    else:
        #PENALTY_SPL_BALL_HOLDING 
        if(type == 1):
            print 'Fuck you!'
            os.system(program+" "+path+"insult-01.wav")
         #PENALTY_SPL_PLAYER_PUSHING   
        if(type == 2):
            rand = random.random()
            if(rand>0.75):
                print 'You call that pushin\'!? You should ask your mom, \'cause I showed her some real pushin\' last night, he'
                os.system(program+" "+path+"insult-07.wav")
            elif(rand>0.5):
                print 'Yo reff, he was pushin\' me! I sear!'
                os.system(program+" "+path+"insult-08.wav")
            elif(rand>0.25):
                print 'No way reff, he was the one pushin\' me'
                os.system(program+" "+path+"insult-19.wav")
            elif(rand>=0):
                print 'No, I would never touch that filthy bagger'
                os.system(program+" "+path+"insult-21.wav")
             
        #PENALTY_SPL_OBSTRUCTION
        if(type == 3):
            print 'lalala'
            os.system(program+" "+path+"lalalala.wav")
        
        #PENALTY_SPL_INACTIVE_PLAYER 
        if(type == 4):
            rand = random.random()
            if(rand>0.66):
                print 'I was just restin\' me eyes'
                os.system(program+" "+path+"insult-09.wav")
            elif(rand>0.33):
                print 'Just leave me be, I\'m oke'
                os.system(program+" "+path+"insult-15.wav")
            elif(rand>=0):
                print 'no lady, just leave me'
                os.system(program+" "+path+"insult-16.wav")
        
        #PENALTY_SPL_ILLEGAL_DEFENDER      
        if(type == 5):
            print 'No, no, reff, I think I dropped a penny here'
            os.system(program+" "+path+"insult-14.wav")
        
        #PENALTY_SPL_LEAVING_THE_FIELD    
        if(type == 6):
            rand = random.random()
            if(rand>0.66):
                print 'I\'ll just be off to the pub for a bit'
                os.system(program+" "+path+"insult-10.wav")
            elif(rand>0.33):
                print 'No, I\'ve had enough. I\'m leavin\''
                os.system(program+" "+path+"insult-12.wav")
            elif(rand>0):
                print 'Ha, I... I think I\'ll just... no... no...'
                os.system(program+" "+path+"insult-22.wav")
        
        #PENALTY_SPL_PLAYING_WITH_HANDS    
        if(type == 7):
            standard()
            print 'Hands'
            os.system(program+" "+path+"lalalala.wav")
         
        #PENALTY_SPL_REQUEST_FOR_PICKUP 
        if(type == 8):
            print 'Your mother requested me to pick her op too the other day'
            os.system(program+" "+path+"insult-05.wav")
        
        #MANUAL   
        if(type == 15):
            print 'manual'
            standard()
            os.system(program+" "+path+"lalalala.wav")
        
        
def goal(who):
    print 'Oh, don\'t worry guys, that was just a lucky shot, he'
    os.system(program+" "+path+"insult-25.wav")

def rejection():
    print 'rejected'
    standard()
    os.system(program+" "+path+"lalalala.wav")
    
def setPhase():
    rand = random.random()
    if(rand>0.5):
        print 'Maybe you should just consider givin\' up.'
        os.system(program+" "+path+"insult-26.wav")
    elif(rand>=0):
        print 'Oh, you\'ve practicly already lost'
        os.system(program+" "+path+"insult-27.wav")
        
def fallen():
    rand = random.random()
    if(rand>0.84):
        print 'Whoah! What happend!?'
        os.system(program+" "+path+"insult-28.wav")
    elif(rand>0.76):
        print 'Don\'t worry, I always walk like this on mondays'
        os.system(program+" "+path+"insult-29.wav")
    elif(rand>0.50):
        print 'Tgah, bagger'
        os.system(program+" "+path+"insult-30.wav")
    elif(rand>0.34):
        print 'Oh, hold on'
        os.system(program+" "+path+"insult-31.wav")
    elif(rand>0.16):
        print 'Oah!'
        os.system(program+" "+path+"insult-32.wav")
    elif(rand>=0):
        print 'Oah, I\'v probably had one to much'
        os.system(program+" "+path+"insult-33.wav")
        
def balLost():
    rand = random.random()
    if(rand>0.66):
        print 'Ha, I... I think I\'ll just... no... no...'
        os.system(program+" "+path+"insult-22.wav")
    elif(rand>0.33):
        print 'Well, I can\'t find her'
        os.system(program+" "+path+"insult-23.wav")
    elif(rand>=0):
        print 'Where the hell is that thing?'
        os.system(program+" "+path+"insult-24.wav")

def standard():
    rand = random.random()
    if(rand>0.84):
        print 'Fuck you!'
        os.system(program+" "+path+"insult-01.wav")
    elif(rand>0.70):
        print 'Bagger off!'
        os.system(program+" "+path+"insult-02.wav")
    elif(rand>0.56):
        print 'Ye bloody arsehole!'
        os.system(program+" "+path+"insult-03.wav")
    elif(rand>0.42):
        print 'Well shite!'
        os.system(program+" "+path+"insult-04.wav")
    elif(rand>0.28):
        print 'Just keep your bloody hands off me!'
        os.system(program+" "+path+"insult-13.wav")
    elif(rand>0.14):
        print 'jo pal, just leave me standin\' here'
        os.system(program+" "+path+"insult-17.wav")
    elif(rand>=0):
        print 'just leave me be'
        os.system(program+" "+path+"insult-18.wav")

        
