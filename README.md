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
gstreamer, gst-base, gst-bad, gst-python, gtk3, cv2, numpy, socketio, 

### node
express, socket.io, cloudcmd


### Added 2026
python -m pip install requests --break-system-packages

msys2 gstreamer

```bash
pacman -S mingw-w64-x86_64-gstreamer \
          mingw-w64-x86_64-gst-plugins-base \
          mingw-w64-x86_64-gst-plugins-good \
          mingw-w64-x86_64-gst-plugins-bad \
          mingw-w64-x86_64-gst-plugins-ugly \
          mingw-w64-x86_64-gst-libav \
          mingw-w64-x86_64-python \
          mingw-w64-x86_64-python-gobject \
          mingw-w64-x86_64-gst-python
```

```bash
pacman -S mingw-w64-x86_64-python-opencv
python -m pip install python-socketio --break-system-packages
python -m pip install requests --break-system-packages
```


## Check decklink input
```bash
gst-launch-1.0 decklinkvideosrc device-number=0 mode=1080i5994 ! deinterlace ! videoconvert ! autovideosink
```
