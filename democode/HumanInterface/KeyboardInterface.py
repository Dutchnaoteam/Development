from Tkinter import *
import socket
import time

# Set the socket parameters
host = "192.168.1.108"
port = 4242
buf = 1024
addr = (host,port)
delay = 25

# Dictionary for keys
keys = {"Left" :0,
        "Up"   :0,
        "Right":0,
        "Down" :0,
        "z"    :0,
        "x"    :0 }

# Connection variable
connected = False;

# Create socket
sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

def keyPress(event):
    if event.keysym in keys:
        keys[event.keysym] = 1

def keyRelease(event):
    if event.keysym in keys:
        keys[event.keysym] = 0

def update():
    # Receive messages
    data,addr = sock.recvfrom(1024)
    print "updating"   ,time.time() 
    # Send messages
    sock.send("Up " + str(keys["Up"]) +
              " Down " + str(keys["Down"]) +
              " Left " + str(keys["Left"]) +
              " Right " + str(keys["Right"]) +
              " A " + str(keys["z"]) +
              " B " + str(keys["x"]) )

    # Set timer again
    f.after(delay,update)

class InputDialog:

    def __init__(self, parent):

        top = self.top = Toplevel(parent)

        # Add a frame to the widget
        self.f = Frame(top)
        self.f.pack()
        self.f.focus_set()
        top.bind("<Return>", self.connect_button)
        
        # Add the label to the frame
        self.l = Label(self.f, text="Enter ip:")
        self.l.grid(row=0)

        # Add entry field to the frame
        self.e = Entry(self.f)
        self.e.grid(row=0,column=1)
    
        # Add connect button to the frame
        self.b = Button(self.f, text="Connect!", command=self.connect_button, width=16)
        self.b.grid(row=1,columnspan=2)
        

    def connect_button(self, event=0):
        # Try to make a connection
        print "Trying to connect to", self.e.get()
        host = self.e.get()
        addr = (host,port)
        sock.connect(addr)

        # Start updating
        update()

        # Set the focus to the main window
        f.focus_set()
        self.top.destroy()

# Create root widget
root = Tk()
root.title("Nao Keyboard Client")

# Create the main frame
f = Frame(root,width=200,height=100)
f.bind("<Any-KeyPress>", keyPress)
f.bind("<Any-KeyRelease>",keyRelease)
f.pack()

# Create the input dialog
d = InputDialog(root)

# Main loop of widget
mainloop()

# Close the connection
sock.close()
