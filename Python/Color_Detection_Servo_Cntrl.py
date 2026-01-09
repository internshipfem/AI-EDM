import cv2
print(cv2.__version__)
import numpy as np
import serial

# print(f"Trying for PORT no: {i}")
serialData = serial.Serial('COM4', '115200', timeout=5)

pan=90
tilt=60
width=320
height=160
flip=2


def nothing(x):
    pass

cv2.namedWindow('Trackbars')
cv2.moveWindow('Trackbars',0,510)

cv2.createTrackbar('hueLower', 'Trackbars',5,179,nothing)
cv2.createTrackbar('hueUpper', 'Trackbars',12,179,nothing)

cv2.createTrackbar('hue2Lower', 'Trackbars',0,179,nothing)
cv2.createTrackbar('hue2Upper', 'Trackbars',9,179,nothing)

cv2.createTrackbar('satLow', 'Trackbars',141,255,nothing)
cv2.createTrackbar('satHigh', 'Trackbars',255,255,nothing)
cv2.createTrackbar('valLow','Trackbars',150,255,nothing)
cv2.createTrackbar('valHigh','Trackbars',190,255,nothing)

import platform

def try_open(source, backend=None):
    """Try to open a cv2.VideoCapture with optional backend."""
    try:
        if backend is not None:
            cap = cv2.VideoCapture(source, backend)
        else:
            cap = cv2.VideoCapture(source)
    except Exception as e:
        print(f"Exception while opening camera source={source!r} backend={backend}: {e}")
        return None

    if cap is not None and cap.isOpened():
        print(f"Opened camera source={source!r} backend={backend}")
        return cap
    
    if cap is not None:
        cap.release()
    return None

# Display dimensions
dispW = 640  # Display width
dispH = 480  # Display height

# Updated GStreamer pipeline
camSet = (
    'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=1280, height=720, format=NV12, framerate=30/1 ! '
    f'nvvidconv flip-method={flip} ! video/x-raw, width={dispW}, height={dispH}, format=BGRx ! '
    'videoconvert ! video/x-raw, format=BGR ! appsink'
)

# Try opening camera with different methods
cam = None
if hasattr(cv2, 'CAP_GSTREAMER'):
    cam = try_open(camSet, cv2.CAP_GSTREAMER)
if cam is None:
    # Try DirectShow on Windows
    cam = try_open(0, cv2.CAP_DSHOW)
if cam is None:
    # Try default capture
    cam = try_open(0)

if cam is None:
    print("Failed to open camera with any method")
    exit(1)

width = cam.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
print('width:', width, 'height:', height)
while True:   
    ret, frame = cam.read()
    #frame = cv2.flip(frame,1)
    #frame=cv2.resize(frame,(width,height))
    #frameGray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)

    hueLow=cv2.getTrackbarPos('hueLower', 'Trackbars')
    hueUp=cv2.getTrackbarPos('hueUpper', 'Trackbars')

    hue2Low=cv2.getTrackbarPos('hue2Lower', 'Trackbars')
    hue2Up=cv2.getTrackbarPos('hue2Upper', 'Trackbars')

    Ls=cv2.getTrackbarPos('satLow', 'Trackbars')
    Us=cv2.getTrackbarPos('satHigh', 'Trackbars')

    Lv=cv2.getTrackbarPos('valLow', 'Trackbars')
    Uv=cv2.getTrackbarPos('valHigh', 'Trackbars')

    l_b=np.array([hueLow,Ls,Lv])
    u_b=np.array([hueUp,Us,Uv])

    l_b2=np.array([hue2Low,Ls,Lv])
    u_b2=np.array([hue2Up,Us,Uv])

    FGmask=cv2.inRange(hsv,l_b,u_b)
    FGmask2=cv2.inRange(hsv,l_b2,u_b2)
    FGmaskComp=cv2.add(FGmask,FGmask2)
    cv2.imshow('FGmaskComp',FGmaskComp)
    cv2.moveWindow('FGmaskComp',640,0)
    
    (contours,_)=cv2.findContours(FGmaskComp,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    contours=sorted(contours,key=lambda x:cv2.contourArea(x),reverse=True)
    for cnt in contours:
        area=cv2.contourArea(cnt)
        (x,y,w,h)=cv2.boundingRect(cnt)
        if area>=50:
            #cv2.drawContours(frame,[cnt],0,(255,0,0),3)
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2) 
            cv2.putText(frame, "TARGET LOCKED", (x-50, y-15), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 127), 3 )
            cv2.circle(frame,(x+w, y+h), 10, (0, 255, 255), cv2.FILLED)
            objX=x+w/2
            objY=y+h/2
            errorPan=objX-width/2
            errorTilt=objY-height/2
            if abs(errorPan)>15:
                pan=pan-errorPan/75
            if abs(errorTilt)>15:
                tilt=tilt-errorTilt/75

            if pan>125:
                pan=125
                
            if pan<55:
                pan=55
                
            if tilt>145:
                tilt=145
                
            if tilt<55:
                tilt=55 
                                      
            Yangle=pan
            Xangle=tilt
            
            serialData.write(('a'+ str(int(Yangle))+'b'+ str(int(Xangle))).encode('utf-8'))
            cv2.putText(frame, f'Servo X: {int(Xangle)} deg', (5, 60), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 200), 2)
            cv2.putText(frame, f'Servo Y: {int(Yangle)} deg', (5, 90), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 200), 2)
            break
         
    
    if cv2.waitKey(1)& 0xff==ord('c'):
        serialData.write('c'.encode('utf-8')) 
    
            #break
          
    cv2.imshow('nanoCam',frame)
    cv2.moveWindow('nanoCam',0,0)
    
    
    if cv2.waitKey(1)& 0xff==ord('q'):
        break
cam.release()
cv2.destroyAllWindows()
