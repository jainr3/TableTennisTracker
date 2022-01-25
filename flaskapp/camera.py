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
    writer = None
    table_tennis = None # Set elsewhere to reference app.py's object
    guidelines = False
    buffer = 5
    hotbox_buffer = 3
    hotbox_log = deque(maxlen=hotbox_buffer)
    debug = True
    game_state_frame = None # for debug

    def __init__(self):
        if os.environ.get('OPENCV_CAMERA_SOURCE'):
            Camera.set_video_source(int(os.environ['OPENCV_CAMERA_SOURCE']))
        super(Camera, self).__init__()

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source

    @staticmethod
    def frames():
        # define the lower and upper boundaries of the colored
        # ball in the HSV color space, then initialize the
        # list of tracked points
        colorLower = (0, 94, 108)
        colorUpper = (25, 255, 197)
        buffer = Camera.buffer
        pts = deque(maxlen=buffer)
        camera = cv2.VideoCapture(Camera.video_source)
        #camera = VideoStream(src=0).start() 
        # allow the camera or video file to warm up
        time.sleep(2.0)

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
                if radius > 3:
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

            # Set the frame size for use elsewhere
            (h, w) = frame.shape[:2]
            if BaseCamera.frame_h == None or BaseCamera.frame_w == None:
                BaseCamera.frame_h = h
                BaseCamera.frame_w = w

            # Update visual display and gamestate
            a, b = Camera.update_hotbox(mask)

            if Camera.debug and a != None and b != None:
                cv2.circle(frame, (a, b), 5, (0, 255, 0), -1)
            frame = Camera.table_tennis.update_visual_display(frame)

            if not Camera.table_tennis.noactive_game():
                Camera.game_state_frame = frame
                Camera.table_tennis.current_game.update_game_state(pts)
                frame = Camera.game_state_frame

            # Draw the guidelines
            if Camera.guidelines:
                cv2.line(img=frame, pt1=(int(w/2), 0), pt2=(int(w/2), h), color=(255, 0, 0), thickness=2, lineType=8, shift=0)
                cv2.line(img=frame, pt1=(0, h - 15), pt2=(w, h - 15), color=(255, 0, 0), thickness=2, lineType=8, shift=0)

            # Save the video frame if the writer is active
            if Camera.writer != None:
                Camera.writer.write(frame)

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', frame)[1].tobytes()

        camera.release()

    @staticmethod
    def update_hotbox(mask):
        # Divide up the pixels into boxes and track the box
        x_array, y_array = np.where((mask == [255]))

        boxsize_w = 10
        boxsize_h = 10
        hotbox_pixel_count = np.zeros(shape=(int(BaseCamera.frame_w / boxsize_w) + 1 , int(BaseCamera.frame_h / boxsize_h) + 1))
        for x, y in zip(x_array, y_array):
            hotbox_pixel_count[y // boxsize_w][x // boxsize_h] += 1

        result = np.where(hotbox_pixel_count == np.amax(hotbox_pixel_count))

        if len(result[0]) in range(1, 5) and len(result[1]) in range(1, 5):
            proposed_hotbox = ((result[0][0], result[1][0]), False, False)
        else:
            return None, None # no proposed hotbox (or too many low quality points)

        if len(Camera.hotbox_log) == 0:
            last_hotbox = None
        else:
            last_hotbox = list(Camera.hotbox_log)[0]

        if last_hotbox != proposed_hotbox:
            Camera.hotbox_log.appendleft(proposed_hotbox)

        return result[0][0]*boxsize_w, result[1][0]*boxsize_h