import socketio, time, sys

class sioclient():
    def __init__(self):
        print('Create python socket.io object')
        self.sio = socketio.Client(reconnection = True, reconnection_delay=0.1, request_timeout = 0.1)
        self.sio.on("connect", self.on_connect)
        self.sio.on("disconnect", self.on_disconnect)
        self.sio.on("msg_gui", self.on_msg_gui)
        
        
    def on_connect(self):
        print('connection established')
        
    def on_msg_gui(self, data):
        print('gui message received with ', data)
        
    def on_disconnect(self):
        print('disconnected from server')
        
    def connect(self, address):
        self.address = address

        result = False
        try:
            self.sio.connect(address)
            result = True
        except Exception as e:
            print(e)
            result = False
        finally:
            return result

    def disconnect(self):
        try:
            self.sio.disconnect()
        except Exception as e:
            print(e)

    def send(self, name_event, data):
        if self.sio.connected:
            self.sio.emit(name_event, data)
        else:
            self.disconnect()
            self.connect(self.address)
        


sio = sioclient()
if (not sio.connect('http://localhost:3000')):
    print("Cannot establish socketio... check server..")
    

i = 0
try:
    while True:
        i += 1
        sio.send('msg_engine', {'foo' : 'bar', 'count': i})
        print("emit signal .. ", i , end='\r')
        time.sleep(1)
        
except KeyboardInterrupt:
    time.sleep(1)
    sio.disconnect()