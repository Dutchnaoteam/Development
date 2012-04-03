import socket
import time

# Timer delay
delay = 200

# Set the socket parameters
host = "169.254.39.105"
port = 4242
buf = 1024
addr = (host,port)

# Connection variable
connected = False;

# Create socket
sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.connect(addr)

def update():
    sock.send("1")
    
    # Set timer again
    time.sleep(1)

start = time.time()

while True:
    data = sock.recv(1024)
    while not(data == 'GO'):
        data = sock.recv(1024)
    sock.send("Hoi")
# Close the connection
sock.close()
