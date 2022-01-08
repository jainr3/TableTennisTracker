# Script to center the net and level the table surface
# May vary based on video stream resolution
import cv2

cv2.namedWindow("Calibrate Center")
vc = cv2.VideoCapture(1)

if vc.isOpened():
    rval, frame = vc.read()
else:
    rval = False

(h, w) = frame.shape[:2]

while rval:
    cv2.imshow("Calibrate Center", frame)
    rval, frame = vc.read()
    key = cv2.waitKey(20)
    if key == 27: # exit on ESC
        break
    else:
        cv2.line(img=frame, pt1=(int(w/2), 0), pt2=(int(w/2), h), color=(255, 0, 0), thickness=2, lineType=8, shift=0)
        cv2.line(img=frame, pt1=(0, h - 20), pt2=(w, h - 20), color=(255, 0, 0), thickness=2, lineType=8, shift=0)

vc.release()
cv2.destroyWindow("preview")  
