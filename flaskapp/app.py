#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response
import argparse

# import camera driver
from camera import Camera

parser = argparse.ArgumentParser()
parser.add_argument('--save_video', default=False, action='store_true', help="Defaults to False if not passed")
args = parser.parse_args()

app = Flask(__name__)

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    while True:
        frame = camera.get_frame()
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera(args.save_video)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
