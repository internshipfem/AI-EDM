import cv2
import time
import serial
serialData = serial.Serial('COM3', '115200', timeout=5)
pan=90
tilt=90
width=640
height=390
cam=cv2.VideoCapture(0,cv2.CAP_DSHOW)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
cam.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))
if not cam.isOpened():
    print("Camera couldn't Access!!!")
    exit()
faceCascade=cv2.CascadeClassifier('haar\haarcascade_frontalface_default.xml')
eyeCascade=cv2.CascadeClassifier('haar\haarcascade_eye.xml')
fps=15
timeStamp=time.time()
while True:
    ignore,  frame = cam.read()
    frame=cv2.resize(frame,(width,height))
    frameGray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    faces=faceCascade.detectMultiScale(frameGray,1.2,5,minSize=(15, 15))
    for face in faces:
        x,y,w,h=face
        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),3)
        
        cv2.line(frame, (0, y+65), (width, y+65), (0, 255, 0), 2) 
        cv2.line(frame, (x+55, height), (x+55, 0), (0, 255, 0), 2)  
        cv2.putText(frame, "TARGET LOCKED", (x-50, y-15), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 127), 3 )
        cv2.circle(frame, (x+55, y+65), 10, (0, 255, 255), cv2.FILLED)
        frameROI=frame[y:y+h,x:x+w]
        frameROIGray=cv2.cvtColor(frameROI,cv2.COLOR_BGR2GRAY)
        if cv2.waitKey(1)& 0xff==ord('c'):
            serialData.write('c'.encode('utf-8'))
            break
                
        eyes=eyeCascade.detectMultiScale(frameROIGray)
        for eye in eyes:
            xeye,yeye,weye,heye=eye
            cv2.rectangle(frame[y:y+h,x:x+w],(xeye,yeye),(xeye+weye,yeye+heye),(0,255,255),2)
        objX=x+w/2
        objY=y+h/2
        errorPan=objX-width/2
        errorTilt=objY-height/2
        if abs(errorPan)>15:
            pan=pan-errorPan/75
        if abs(errorTilt)>15:
            tilt=tilt-errorTilt/75


        if pan>130:
            pan=130
            #print("Pan Out of  Range")   
        if pan<60:
            pan=60
            #print("Pan Out of  Range") 
        if tilt>130:
            tilt=130
            #print("Tilt Out of  Range") 
        if tilt<60:
            tilt=60
            #print("Tilt Out of  Range")                 

        Yangle=pan
        Xangle=tilt 
        serialData.write(('a'+ str(int(Yangle))+'b'+ str(int(Xangle))).encode('utf-8'))
        cv2.putText(frame, f'Servo X: {int(Xangle)} deg', (5, 60), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 200), 2)
        cv2.putText(frame, f'Servo Y: {int(Yangle)} deg', (5, 90), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 200), 2)
        break
        

    loopTime=time.time()-timeStamp
    timeStamp=time.time()
    fpsNEW=1/loopTime
    fps=.9*fps+.1*fpsNEW
    fps=int(fps)
    cv2.putText(frame,str(fps)+'fps',(5,30),cv2.FONT_HERSHEY_PLAIN,1,(0,255,125),2)
    cv2.imshow('my WEBcam', frame)
    cv2.moveWindow('my WEBcam',0,0)
    if cv2.waitKey(1) & 0xff ==ord('q'):
        break
cam.release()
cv2.destroyAllWindows()