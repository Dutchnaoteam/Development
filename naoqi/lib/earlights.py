"""
Name: earLights.py
Author: Erik van Egmond
Description: Manages the lights of the ear based on the number of active 
communicating players. 
"""

class EarLights():
    """ 
    class Earlights manages the lights of the ear based on input by coach. 
    """
    def __init__(self, ledProxy):
        self.ledProxy = ledProxy
        self.ledProxy.off('EarLeds')

    def playerOne(self, onOff):
        """Show part of the ear based on the number of players"""
        if onOff:
            self.ledProxy.on('Ears/Led/Left/0Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Left/36Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Left/72Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Right/0Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Right/36Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Right/72Deg/Actuator/Value')
        else:
            self.ledProxy.off('Ears/Led/Left/0Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Left/36Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Left/72Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Right/0Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Right/36Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Right/72Deg/Actuator/Value')

    def playerTwo(self, onOff):
        """Show part of the ear based on the number of players"""
        if onOff:
            self.ledProxy.on('Ears/Led/Left/108Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Left/144Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Right/108Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Right/144Deg/Actuator/Value')
        else:
            self.ledProxy.off('Ears/Led/Left/108Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Left/144Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Right/108Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Right/144Deg/Actuator/Value')
            
    def playerThree(self, onOff):
        """Show part of the ear based on the number of players"""
        if onOff:
            self.ledProxy.on('Ears/Led/Left/180Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Left/216Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Left/252Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Right/180Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Right/216Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Right/252Deg/Actuator/Value')
        else:
            self.ledProxy.off('Ears/Led/Left/180Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Left/216Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Left/252Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Right/180Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Right/216Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Right/252Deg/Actuator/Value')
            
    def playerFour(self, onOff):
        """Show part of the ear based on the number of players"""
        if onOff:
            self.ledProxy.on('Ears/Led/Left/288Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Left/324Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Right/288Deg/Actuator/Value')
            self.ledProxy.on('Ears/Led/Right/324Deg/Actuator/Value')
        else:
            self.ledProxy.off('Ears/Led/Left/288Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Left/324Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Right/288Deg/Actuator/Value')
            self.ledProxy.off('Ears/Led/Right/324Deg/Actuator/Value')

    def playerOn(self, player):
        """Find which players are active, incur corresponding function"""
        self.players.get(player)(self,1)
        
    def playerOff(self, player):
        """Find which players are active, incur corresponding function"""        
        self.players.get(player)(self,0)
        
    def playerOffAll(self):
        """If zero players are active, earleds are off"""
        self.ledProxy.off('EarLeds')

    players = {
            1: playerOne,
            2: playerTwo,
            3: playerThree,
            4: playerFour
        }

    
