#   Video freeze, black detector by sendust...
#   Capture image from Decklink 
#   Create ROI, calculate mean value..
#   Shows black score, freeze score
#   WWW GUI integration with socketio
#
#   2023/10/18  Last state save/load
#
#


import numpy as np
import cv2, time, threading, socketio, sys, datetime, os, gi
gi.require_version('Gst', '1.0')
from queue import Queue
from gi.repository import Gst

Gst.init(None)

def updatelog(txt, consoleout = False):
    pid = os.getpid()
    path_log = os.path.join(os.getcwd(), 'logmain', f'sendust_vision.log')
    tm_stamp = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f   ")
    
    try:
        if (os.stat(path_log).st_size > 3000000):
            path_archive = os.path.splitext(path_log)[0]
            path_archive += '_' + datetime.datetime.now().strftime("_%m%d%Y-%H%M%S.log")
            os.rename(path_log, path_archive)
    except:
        print("Log with file....")
        
    txt = str(txt)
    with open(path_log, "a", encoding='UTF-8') as f:
        f.write(tm_stamp + txt + "\n")
    if consoleout:
        col = os.get_terminal_size().columns
        print(" " * (int(col) - 1), end='\r')     # clear single line
        print(tm_stamp + txt)




class decklinksrc:
    def __init__(self, index_device):
        self.framequeue = Queue()
        self.frame_clean = ''
        self.frame_roi = ''
        self.keep_going = True
        self.index_device = index_device

    def gst_to_opencv(self, sample):
        
        buf = sample.get_buffer()
        caps = sample.get_caps()
        #print(caps.get_structure(0).get_value('format'))
        #print(caps.get_structure(0).get_value('height'))
        #print(caps.get_structure(0).get_value('width'))

        #print(buf.get_size())

        arr = np.ndarray(
            (caps.get_structure(0).get_value('height'),
             caps.get_structure(0).get_value('width'),
             3),
            buffer=buf.extract_dup(0, buf.get_size()),
            dtype=np.uint8)

        if (caps.get_structure(0).get_value('height') == 1080):  # there is valid frame data
            self.framequeue.put(arr)
            self.frame_clean = arr
        return arr

    def save_frame(self, frame):
        path_im = os.path.join(os.getcwd(), 'image', f'decklink {self.index_device}-{get_timestamp("file")}.jpg')
        cv2.imwrite(path_im, frame)
        print(f'Decklink index {self.index_device} -- last frame saved...')


    def new_buffer(self, sink, data):     # run every new frame..
        sample = sink.emit("pull-sample")
        buf = sample.get_buffer()
        #print("Timestamp: ", buf.pts, "   " , periodic)
        arr = self.gst_to_opencv(sample)
        return Gst.FlowReturn.OK

    def play(self):
        
        # Create the elements
        source = Gst.ElementFactory.make("decklinkvideosrc", "source")
        convert = Gst.ElementFactory.make("videoconvert", "convert")
        sink = Gst.ElementFactory.make("appsink", "sink")


        # Modify the source's properties
        # HD1080 59.94i
        source.set_property("mode", 12)
        source.set_property("device-number", self.index_device)
        # SDI
        #source.set_property("connection", 0)

        # Create the empty pipeline
        self.pipeline = Gst.Pipeline.new("decklink-pipeline" + str(self.index_device))

        if not source or not sink or not self.pipeline:
            print("Not all elements could be created.")
            exit(-1)

        sink.set_property("emit-signals", True)
        # sink.set_property("max-buffers", 2)
        # sink.set_property("drop", True)
        # sink.set_property("sync", False)

        caps = Gst.caps_from_string("video/x-raw, format=(string){BGR, GRAY8}; video/x-bayer,format=(string){rggb,bggr,grbg,gbrg}")

        sink.set_property("caps", caps)

        sink.connect("new-sample", self.new_buffer, sink)

        # Build the pipeline
        self.pipeline.add(source)
        self.pipeline.add(convert)
        self.pipeline.add(sink)
        if not Gst.Element.link(source, convert):
            print("Elements could not be linked.")
            exit(-1)

        if not Gst.Element.link(convert, sink):
            print("Elements could not be linked.")
            exit(-1)


        # Start playing
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("Unable to set the pipeline to the playing state.")
            exit(-1)

        # Wait until error or EOS
        self.bus = self.pipeline.get_bus()

        while self.keep_going:
            message = self.bus.timed_pop_filtered(10000, Gst.MessageType.ANY)
            
            if message:
                if message.type == Gst.MessageType.ERROR:
                    err, debug = message.parse_error()
                    print(("Error received from element %s: %s" % (
                        message.src.get_name(), err)) , f'  index = {self.index_device}')
                    print(("Debugging information: %s" % debug),  f'  index = {self.index_device}')
                    break
                elif message.type == Gst.MessageType.EOS:
                    print("End-Of-Stream reached.",  f'  index = {self.index_device}')
                    break
                elif message.type == Gst.MessageType.STATE_CHANGED:
                    if isinstance(message.src, Gst.Pipeline):
                        old_state, new_state, pending_state = message.parse_state_changed()
                        print(("Pipeline state changed from %s to %s." %
                               (old_state.value_nick, new_state.value_nick)), f'  index = {self.index_device}')
                               
                elif message.type == Gst.MessageType.WARNING:
                    print("Warning message...",  f'  index = {self.index_device}')

                elif message.type == Gst.MessageType.QOS:
                    print("QOS message...",  f'  index = {self.index_device}')
                               
                else:
                    print("Unexpected message received." , f'  index = {self.index_device}')
                    print(message.type)
                    
            time.sleep(0.001)
    def stop(self):
        self.keep_going = False
        self.pipeline.set_state(Gst.State.NULL)




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
        self.index = kwargs["index"]
        self.decklink = kwargs["decklink"]
        self.status = 0         # alarm status
        self.status_disp = ["off", "on", "dirty"]
        self.margin_freeze = 1
        self.margin_black = 1
        
    def reset_accum(self):
        self.accum_freeze = 0
        self.accum_black = 0
        self.score_freeze = 0
        self.score_black = 0
        
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
        
        try:
            if (os.stat(path_log).st_size > 3000000):
                path_archive = os.path.splitext(path_log)[0]
                path_archive += '_' + datetime.datetime.now().strftime("_%m%d%Y-%H%M%S.log")
                os.rename(path_log, path_archive)
        except:
            print("Log with file....")

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

    def isconnected(self):
        return self.sio.connected

    def disconnect(self):
        try:
            self.sio.disconnect()
        except Exception as e:
            print(e)

    def send(self, name_event, data):
        try:
            self.sio.emit(name_event, data)
        except Exception as e:
            print(e)
    


class webgui:

    def start(self):
        self.keep_continue = True
        self.sio = sioclient()
        if (not self.sio.connect('http://localhost:3000')):
            print("Cannot establish socketio... check server..")

        threading.Thread(target=self.run).start()

    def run(self):
        while self.keep_continue:
            if not self.sio.isconnected():
                self.sio.connect('http://localhost:3000')
            time.sleep(3)
            
    def stop(self):
        self.keep_continue = False
        
    def send(self, msg):
        if self.sio.isconnected():
            self.sio.send('msg_engine', msg)


def get_timestamp(s):
    if s not in ["log", "file"]:
        s = "log"
    tm_stamp = {}
    tm_stamp["log"] = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f")
    tm_stamp["file"] = datetime.datetime.now().strftime("%Y-%m-%d-%Hh%Mm%Ss.%f")
    return tm_stamp[s]



def decode_protocol(data):
    global roi_ary, decklink
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

    if ((data["protocol"] == "gui") and (data["data"]["cmd"] == "capture")):
        for decklink in list_decklink:
            print(f'Capture and save decklink frame.. {decklink.index_device}')
            decklink.save_frame(decklink.frame_roi)


    if ((data["protocol"] == "gui") and (data["data"]["cmd"] == "reset")):
        close_gracefully()
        
    if ((data["protocol"] == "gui") and (data["data"]["cmd"] == "mgnF")):
        print("set margin_freeze")
        for each_rect in roi_ary:
            each_rect.margin_freeze = int(data["data"]["data"])

        
    if ((data["protocol"] == "gui") and (data["data"]["cmd"] == "mgnB")):
        print("set margin_black")
        for each_rect in roi_ary:
            each_rect.margin_black = int(data["data"]["data"])



def get_decklink_list(config):
    count = 0
    dl = []
    for each in config:
        dl.append(each["decklink"])
    
    return set(dl)
   
   
def read_config(file_config):
    index = 0
    config = []
    with open(file_config, "r",  encoding='utf-8') as rectangle_file:   # Read rectangle definition file
        lines = rectangle_file.readlines()
        for each in lines[3:]:
            data = [element.strip() for element in each.strip().split(",")]
            config.append({"index" : int(index), "x" : int(data[0]), "y" : int(data[1]),
            "width" : int(data[2]), "height" : int(data[3]), "name" : data[4], "decklink" : int(data[5])})
            index += 1
    return config


def save_status():
    global roi_ary
    updatelog("save status", True)
    with open("status.txt", "w") as f:
        f.write("name, margin_freeze, margin_black, status\n")
        for each in roi_ary:
            newline = f'{each.name}|{each.margin_freeze}|{each.margin_black}|{int(each.status)}\n'
            f.write(newline)
            updatelog(newlinee, True)


def load_status():
    global roi_ary
    updatelog("load status", True)
    try:
        with open("status.txt", "r") as f:
            header = f.readline()
            print(header)
            for each in roi_ary:
                body = f.readline().strip()
                value = body.split("|")
                updatelog(value, True)
                each.margin_freeze = int(value[1])
                each.margin_black = int(value[2])
                each.status = int(value[3])
    except Exception as e:
        print(e)



def close_gracefully():
    global decklink, keep_playing, gui
    updatelog("Try to close program....", True)
    keep_playing = False
    for decklink in list_decklink:
        try:
            decklink.stop()
        except Exception as e:
            print(e)
    updatelog("close gui", True)
    gui.stop()
    save_status()
    
       
       
send_json = []
roi_ary = []
gui = webgui()
periodic = 0 


gui.start()

list_config = read_config('list_dl.txt')
list_decklink = []


for deck_index in get_decklink_list(list_config):     # Probe total number of decklink
    updatelog("Create Decklink array...", True)
    list_decklink.append(decklinksrc(deck_index))
    print("add decklink list with index ..." , deck_index)


for each_config in list_config:         # Fill up ROI array
    updatelog("Create ROI array...", True)
    roi_ary.append(rectangle(each_config["x"], each_config["y"], each_config["width"], 
        each_config["height"], name=each_config["name"], decklink=each_config["decklink"], index = each_config["index"]))

load_status()

for decklink in list_decklink:      # Start pipeline for each decklink src
    updatelog("start Decklink pipeline play ...", True)
    threading.Thread(target=decklink.play).start()
    

keep_playing = True
declink_index_min = min(get_decklink_list(list_config))
updatelog("Decklin index minimum is " + str(declink_index_min), True)
print("=" * 20)

count = 0
while keep_playing:
    for decklink in list_decklink:
        qsize = decklink.framequeue.qsize()
        print("  qsize = " , qsize, end='')
        if (qsize > 0):
            hdframe = decklink.framequeue.get()
            gray = cv2.cvtColor(hdframe, cv2.COLOR_BGR2GRAY )
            send_json = []
            for each_roi in roi_ary:
                if (each_roi.decklink == decklink.index_device):
                    mean = each_roi.get_average(gray)
                    each_roi.put_value(hdframe)
                    each_roi.draw(hdframe)
                    send_json.append({"protocol" : "ROI", "index" : each_roi.index, "data" : each_roi.data_json})
            decklink.frame_roi = hdframe
            if (qsize == 1):            # show only qsize is optimal
                cv2.imshow('decklink_index ' + str(decklink.index_device), cv2.resize(hdframe, (960, 540)))
            #if (decklink.index_device == declink_index_min):
                keystroke = cv2.waitKey(1)
                if keystroke ==  ord('q'):
                    close_gracefully()
                if keystroke ==  ord('s'):
                    for decklink in list_decklink:
                        decklink.save_frame(decklink.frame_roi)


                    
            gui.send(send_json)
    print("  " , time.time(), end="\r")
    if (periodic < (time.time() - 1)):  # report every second...
        gui.send([{"protocol" : "status", "data" : {"mgnF" : roi_ary[0].margin_freeze, "mgnB" : roi_ary[0].margin_black, "qsize" : qsize, "tm" : datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}}])
        periodic = time.time()
gui.stop()
            