from naoqi import ALProxy
import threading, time

class Balancer(threading.Thread):
    """background-thread that balances the robot by monitoring the balance in
    each foot and adjusting the upper body correspondently"""

    def __init__(self, threshold):
        threading.Thread.__init__(self)
        self.threshold = threshold
        self.mem = ALProxy("ALMemory", "127.0.0.1", 9559)
        self.tts = ALProxy("ALTextToSpeech", "127.0.0.1", 9559)
        self.running = True

    def run(self):
        while self.running:
            balance_left = self.leftFootBalance()
            balance_right = self.rightFootBalance()

            # in case of imbalance
            if max(balance_left, balance_right) > self.threshold:
                self.tts.say("Oh no I'm falling!")
            time.sleep(1)

    def setThreshold(self, threshold):
        self.threshold = threshold

    def kill(self):
        self.running = False

    def leftFootBalance(self):
        """ returns a measure of balance for the left foot
        a higher value indicates more imbalance """
        fLeft = self.mem.getData("Device/SubDeviceList/LFoot/FSR/FrontLeft/Sensor/Value")
        fRight = self.mem.getData("Device/SubDeviceList/LFoot/FSR/FrontRight/Sensor/Value")
        rLeft = self.mem.getData("Device/SubDeviceList/LFoot/FSR/RearLeft/Sensor/Value")
        rRight = self.mem.getData("Device/SubDeviceList/LFoot/FSR/RearRight/Sensor/Value")

        return ((fLeft + rLeft) - (fRight + rRight))**2

    def rightFootBalance(self):
        """ returns a measure of balance for the right foot
        a higher value indicates more imbalance """
        fLeft = self.mem.getData("Device/SubDeviceList/RFoot/FSR/FrontLeft/Sensor/Value")
        fRight = self.mem.getData("Device/SubDeviceList/RFoot/FSR/FrontRight/Sensor/Value")
        rLeft = self.mem.getData("Device/SubDeviceList/RFoot/FSR/RearLeft/Sensor/Value")
        rRight = self.mem.getData("Device/SubDeviceList/RFoot/FSR/RearRight/Sensor/Value")

        return ((fLeft + rLeft) - (fRight + rRight))**2
