sendust_vision

Detect freeze, black frame from decklink input\
User configurable with multiple ROI.\
Multiple decklink input support

## how to run

1. start www server\
node.exe fm_socketio.js\
or run_server_www.bat

2. start python application\
python.exe decklink_src.py\
or run vision_decklinksrc_loop.bat


## Required modules

### python
==========
gstreamer, gst-base, gst-bad, gst-python, gtk3, cv2, numpy, socketio, 

### node
========
express, socket.io, cloudcmd
