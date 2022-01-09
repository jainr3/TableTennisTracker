import os
import cv2
from base_camera import BaseCamera
from collections import deque
from imutils.video import VideoStream
import numpy as np
import imutils
import time

class Camera(BaseCamera):
    # PC: Video Source = 0 is generally the embedded webcam; 1 is the USB camera
    # Raspberry Pi: Video Source = 0 is the USB camera
    video_source = 1
    save_video = False

    def __init__(self, sv):
        Camera.set_save_video(sv)
        if os.environ.get('OPENCV_CAMERA_SOURCE'):
            Camera.set_video_source(int(os.environ['OPENCV_CAMERA_SOURCE']))
        super(Camera, self).__init__()

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source

    @staticmethod
    def set_save_video(sv):
        Camera.save_video = sv

    @staticmethod
    def frames():
        # define the lower and upper boundaries of the colored
        # ball in the HSV color space, then initialize the
        # list of tracked points
        colorLower = (0, 94, 108)
        colorUpper = (25, 255, 197)
        buffer = 4
        pts = deque(maxlen=buffer)
        camera = cv2.VideoCapture(Camera.video_source)
        #camera = VideoStream(src=0).start() 
        # allow the camera or video file to warm up
        time.sleep(2.0)
        # initialize the fourcc, videowriter, dimensions
        if Camera.save_video:
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            writer = None
            (h, w) = (None, None)

        while camera.isOpened():
            # read current frame
            _, frame = camera.read()

            # frame = camera.read()
            # resize the frame, blur it, and convert it to the HSV
            # color space
            frame = imutils.resize(frame, width=600)
            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
            # construct a mask for the color, then perform
            # a series of dilations and erosions to remove any small
            # blobs left in the mask
            mask = cv2.inRange(hsv, colorLower, colorUpper)
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)

            # find contours in the mask and initialize the current
            # (x, y) center of the ball
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            center = None
            # only proceed if at least one contour was found
            if len(cnts) > 0:
                # find the largest contour in the mask, then use
                # it to compute the minimum enclosing circle and
                # centroid
                c = max(cnts, key=cv2.contourArea)
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                # only proceed if the radius meets a minimum size
                if radius > 10:
                    # draw the circle and centroid on the frame,
                    # then update the list of tracked points
                    cv2.circle(frame, (int(x), int(y)), int(radius),
                        (0, 255, 255), 2)
                    cv2.circle(frame, center, 5, (0, 0, 255), -1)
            # update the points queue
            pts.appendleft(center)

            # loop over the set of tracked points
            for i in range(1, len(pts)):
                # if either of the tracked points are None, ignore
                # them
                if pts[i - 1] is None or pts[i] is None:
                    continue
                # otherwise, compute the thickness of the line and
                # draw the connecting lines
                thickness = int(np.sqrt(buffer / float(i + 1)) * 2.5)
                cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)

            (h, w) = frame.shape[:2]

            # TODO: Update gamestate

            if Camera.save_video and writer is None:
                filename = time.strftime("%Y-%m-%d %H-%M-%S") + '.avi'
                writer = cv2.VideoWriter(filename, fourcc, 20, (w, h), True)

            # Draw the guidelines
            cv2.line(img=frame, pt1=(int(w/2), 0), pt2=(int(w/2), h), color=(255, 0, 0), thickness=2, lineType=8, shift=0)
            cv2.line(img=frame, pt1=(0, h - 15), pt2=(w, h - 15), color=(255, 0, 0), thickness=2, lineType=8, shift=0)

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', frame)[1].tobytes()
            # Save to file
            if Camera.save_video:
                writer.write(frame)

        camera.release()
        writer.release()