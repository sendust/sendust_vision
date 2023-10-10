import numpy as np
import cv2, time, threading, socketio, sys, datetime, os
from queue import Queue

cv2.ocl.setUseOpenCL(True)

cap = cv2.VideoCapture(2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
cap.set(cv2.CAP_PROP_FPS, 59.94)


while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    gpumem = cv2.cuda_GpuMat()
    gpumem.upload(frame)
    #gray = cv2.cvtColor(gpuframe, cv2.COLOR_RGBA2GRAY )
    gray = cv2.cuda.cvtColor(gpumem, cv2.COLOR_RGBA2GRAY )


    cv2.imshow('HD_resized_frame', cv2.resize(gray, (960, 540)))

    
    keystroke = cv2.waitKey(1)
    if keystroke ==  ord('q'):
        break
        
cap.release()
cv2.destroyAllWindows()      