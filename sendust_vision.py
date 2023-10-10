import numpy as np
import cv2, time, threading, socketio, sys, datetime, os
from queue import Queue

class rectangle:
        
    def __init__(self, x1, y1, width, height, **kwargs):
        self.x1 = x1
        self.x2 = x1 + width
        self.y1 = y1
        self.y2 = y1 + height
        self.mean_prev = 0
        self.score_freeze = 0
        self.score_freeze_prev = 0
        self.score_black = 0
        self.score_black_prev = 0

        self.accum_freeze = 0
        self.accum_black = 0
        self.kwargs = kwargs
        self.name = kwargs["name"]
        self.status = 0         # alarm status
        self.status_disp = ["off", "on", "dirty"]
        self.margin_freeze = 1
        self.margin_black = 1
        
    def reset_accum(self):
        self.accum_freeze = 0
        self.accum_black = 0
        
    def get_width(self):
        return self.x2 - self.x1
        
    def get_height(self):
        return self.y2 - self.y1
        
    def draw(self, frame):
        cv2.rectangle(frame, (self.x1,self.y1), (self.x2,self.y2), (255,255,0),2)

    def get_average(self, frame):
        subregion = np.array(frame[self.y1:self.y2, self.x1:self.x2], int)
        self.mean = np.mean(subregion)
        if (self.mean_prev == self.mean):
            self.score_freeze += 1
            self.accum_freeze += 1
        else:
            self.score_freeze = 0
            if self.score_freeze_prev:
                threading.Thread(target=self.write_event, args=(f'freeze finish - f {self.score_freeze_prev}, value - {self.mean_prev}', )).start()

        if not self.mean:
            self.score_black += 1
            self.accum_black += 1
        else:
            self.score_black = 0
            if self.score_black_prev:
                threading.Thread(target=self.write_event, args=(f'black finish - {self.score_black_prev}', )).start()

        if (((self.score_black >= self.margin_black) or (self.score_freeze >= self.margin_freeze)) and self.status):  # set alarm state as dirty
            self.status = 2       
        
        if (self.score_freeze == 1):
            threading.Thread(target=self.write_event, args=(f'freeze begin, value - {self.mean_prev}', )).start()

        if (self.score_black == 1):
            threading.Thread(target=self.write_event, args=("black begin", )).start()
        
        self.mean_prev = self.mean
        self.score_freeze_prev = self.score_freeze
        self.score_black_prev = self.score_black
        
        self.data_json = {"name" : self.kwargs["name"], "mean" : round(self.mean, 2) , "black" :  self.accum_black,  "freeze" : self.accum_freeze, "alarm" : self.status_disp[self.status]}
        return self.mean
    
    def put_value(self, frame):

        cv2.putText(frame, "mean {:.2f}".format(self.mean), (self.x1 + 5, self.y1 + 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0),2)
        cv2.putText(frame, "B " + str(self.score_black), (self.x1 + 10, self.y1 + 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0),2)
        cv2.putText(frame, "F " + str(self.score_freeze), (self.x1 + 10, self.y1 + 155), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,0),2)
        cv2.putText(frame, self.kwargs["name"] , (self.x1 + 10, self.y1 + 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0),2)
        

    def write_event(self, name_event):
        path_log = os.path.join(os.getcwd(), 'log', f'{self.name}.log')
        tm_stamp = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f   ")
        with open(path_log, "a", encoding='UTF-8') as f:
            f.write(tm_stamp + name_event + "\n")


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
        decode_protocol(data)
       
        
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
        

def get_cvdata():
    return send_json



class webgui:

    def start(self):
        self.keep_continue = True
        self.sio = sioclient()
        if (not self.sio.connect('http://localhost:3000')):
            print("Cannot establish socketio... check server..")

        threading.Thread(target=self.run).start()

    def run(self):
        while self.keep_continue:
            self.sio.send('msg_engine', get_cvdata())
            time.sleep(3)
            
    def stop(self):
        self.keep_continue = False
        
    def send(self, msg):
        try:
            self.sio.send('msg_engine', msg)
        except Exception as e:
            print(e)

def decode_protocol(data):
    global roi_ary
    if ((data["protocol"] == "gui") and (data["data"]["cmd"] == "allon")):
        print("set all alarm on")
        for each_rect in roi_ary:
            each_rect.status = 1
            each_rect.reset_accum()
        
    if ((data["protocol"] == "gui") and (data["data"]["cmd"] == "alloff")):
        print("set all alarm off")
        for each_rect in roi_ary:
            each_rect.status = 0

    if ((data["protocol"] == "gui") and (data["data"]["cmd"] == "toggle")):
        name_channel = data["data"]["name"]
        print(f'Toggle command accepted .. {name_channel}')
        for each_rect in roi_ary:
            if each_rect.name == name_channel:
                each_rect.status = not each_rect.status
                if each_rect.status:            # reset accum at 'on' request
                    each_rect.reset_accum()

        
    if ((data["protocol"] == "gui") and (data["data"]["cmd"] == "mgnF")):
        print("set margin_freeze")
        for each_rect in roi_ary:
            each_rect.margin_freeze = int(data["data"]["data"])

        
    if ((data["protocol"] == "gui") and (data["data"]["cmd"] == "mgnB")):
        print("set margin_black")
        for each_rect in roi_ary:
            each_rect.margin_black = int(data["data"]["data"])







cap = cv2.VideoCapture(2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_FPS, 59.94)

cap_extra = cv2.VideoCapture(1)
cap_extra.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap_extra.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap_extra.set(cv2.CAP_PROP_FPS, 59.94)

pipelineOutputQueue = Queue()




for k in range(0, 1080, 270):
    for j in range(0, 1920, 480):
        print(f'suggested coord = {(j+5, k+5)}')

send_json = []
roi_ary = []
gui = webgui()
periodic = 0

with open("list.txt", "r",  encoding='utf-8') as rectangle_file:   # Read rectangle definition file
    lines = rectangle_file.readlines()
    for each in lines[3:]:
        data = each.strip().split(",")
        if len(data) > 3:
            print(data)
            roi_ary.append(rectangle(int(data[0]), int(data[1]), int(data[2]), int(data[3]), name=data[4]))  # x1, y1, x2, y2
            
    

print("=" * 20)





if not cap.isOpened():
    print("Cannot open camera")
    exit()
    
gui.start()

while True:
    periodic += 1
    # Capture frame-by-frame
    ret, frame = cap.read()
    ret2, frame2 = cap_extra.read()
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    else:
        pipelineOutputQueue.put(frame)
    # Our operations on the frame come here
    qsize = pipelineOutputQueue.qsize()
    if qsize > 0:
        print(f'queue size is {qsize} / {time.time()}', end="\r")
        hdframe = pipelineOutputQueue.get()
        
        gray = cv2.cvtColor(hdframe, cv2.COLOR_RGBA2GRAY )
        index = 0
        send_json = []
        for rect in roi_ary:
            mean = rect.get_average(gray)
            rect.put_value(hdframe)
            rect.draw(hdframe)
            send_json.append({"protocol" : "ROI", "index" : index, "data" : rect.data_json})
            index += 1

        gui.send(send_json)
        #cv2.rectangle(hdframe, (50,50), (150,100), (255,255,0),2)
        cv2.imshow('HD_resized_frame', cv2.resize(hdframe, (960, 540)))
    keystroke = cv2.waitKey(1)
    if keystroke == ord('s'):
        for each in send_json:
            print(each)
    elif keystroke ==  ord('q'):
        break
    
    if not (periodic % 30):         # do something every 30 frame
        gui.send([{"protocol" : "status", "data" : {"mgnF" : roi_ary[0].margin_freeze, "mgnB" : roi_ary[0].margin_black, "tm" : datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}}])
        
        
            # When everything done, release the capture
gui.stop()
cap.release()
cv2.destroyAllWindows()

