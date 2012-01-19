# Motion Interface for soul planner

# How to call a move
# you import the motioninterface as mot
# mot.move('normalPose')
# mot.move('rKickAngled', 0.5)
# mot.move('walkTo', (1,0,0))

import time
import motions as motion

# METHOD FOR MOTIONS
def changeHead(Arg):
    motion.changeHead(Arg)

def setHead(Arg):
    motion.setHead(Arg)

def normalPose(Arg = False):
    motion.normalPose(Arg)

def keepNormalPose():
    motion.keepNormalPose()

def normalHead():
    motion.normalHead()

def SWTV(Arg):    
    motion.SWTV(Arg)
    
def walkTo(Arg):
    motion.walkTo(Arg)

def postWalkTo(Arg):
    motion.postWalkTo(Arg)    

def rKickAngled(Arg):
    motion.rKickAngled(Arg)

def lKickAngled(Arg):
    motion.lKickAngled(Arg)

def hakje(Arg):
    motion.hakje(Arg)

def footLeft():
    motion.footLeft()

def footRight():
    motion.footRight()

def diveLeft():
    motion.diveLeft()

def diveRight():
    motion.diveRight()

def stance():
    motion.stance()    
    
def setHeadBlock(Arg):
    motion.setHeadBlock(Arg)
    
moves =    {
    'setHead': setHead,
    'changeHead': changeHead,
    'normalPose': normalPose,
    'keepNormalPose': keepNormalPose,
    'normalHead': normalHead,
    'postWalkTo': postWalkTo,
    'walkTo': walkTo,
    'rKickAngled': rKickAngled,
    'lKickAngled': lKickAngled,
    'hakje': hakje,
    'footLeft': footLeft,
    'footRight': footRight,
    'diveLeft': diveLeft,
    'diveRight': diveRight,
    'stance': stance,
    'SWTV': SWTV,
    'setHeadBlock': setHeadBlock
}

# MOVES
def standUp():
    pose = motion.getPose()
    if pose == 'Back':
        motion.stiff()
        motion.backToStand()
        
        return True
    elif pose == 'Belly':
        motion.stiff()
        motion.bellyToStand()
        return True
    return False

def move(Type, Arg = None):
    # Voer movement uit
    if Arg == None:
        moves.get(Type)()
    else:
        moves.get(Type)(Arg)
        
def stiff():
    motion.stiff()

def setStiffnesses(Arg):
    motion.setStiffnesses(Arg)
    
def killWalk():
    motion.killWalk()

def getHeadPos():
    return motion.getHeadPos()

def kill():
    motion.kill()

def killKnees():
    motion.killKnees()
    
def stiffKnees():
    motion.stiffKnees()
    
# BOOLEANS
def isWalking():
    return motion.isWalking()
        
def killAllTasks():
    motion.killAllTasks()