#!/usr/bin/env python
from importlib import import_module
import cv2, time
from flask import Flask, render_template, Response, request, redirect, url_for, session
import flask_login

import argparse

# import camera driver
from camera import Camera
from base_camera import BaseCamera

from table_tennis import TableTennis
from table_tennis_game import TableTennisGame

parser = argparse.ArgumentParser()
args = parser.parse_args()

app = Flask(__name__)
app.secret_key = 'adminpassword'

login_manager = flask_login.LoginManager()

login_manager.init_app(app)

# Mock database.
users = {'admin': {'password': 'admin'}}

# Initialize game states
table_tennis = TableTennis()
Camera.table_tennis = table_tennis
recording_active = False

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    if username not in users:
        return

    user = User()
    user.id = username
    return user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    if username not in users:
        return

    user = User()
    user.id = username
    return user

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def gen(camera):
    """Video streaming generator function."""
    yield b'--frame\r\n'
    while True:
        frame = camera.get_frame()

        if recording_active:
            if Camera.writer is None:
                (h, w) = BaseCamera.get_frame_size()
                filename = time.strftime("%Y-%m-%d %H-%M-%S") + '.avi'
                # initialize the fourcc, videowriter, dimensions
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                Camera.writer = cv2.VideoWriter(filename, fourcc, 20, (w, h), True)
        else:
            if Camera.writer is not None:
                Camera.writer.release()
                Camera.writer = None

        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form["username"]
        if username in users and request.form['password'] == users[username]['password']:
            user = User()
            user.id = username
            flask_login.login_user(user)
            return redirect(url_for('admin'))
        else:
            error = 'Invalid Credentials. Please try again.'
    return render_template('login.html', error=error)

@app.route('/admin', methods=['GET', 'POST'])
@flask_login.login_required
def admin():
    global recording_active
    noactivegame = table_tennis.noactive_game()
    if not noactivegame:
        winner = table_tennis.current_game.check_winner()
    else:
        winner = False
    if request.method == 'POST':
        # Handle the recording button
        if request.form.get('record') and request.form['record'] == "Start Recording":
            recording_active = True
        elif request.form.get('record') and request.form['record'] == "Stop Recording":
            recording_active = False

        if request.form.get('toggle_guidelines') and request.form['toggle_guidelines'] == "Toggle Guidelines":
            Camera.guidelines = not Camera.guidelines
        elif request.form.get('start_newgame') and request.form['start_newgame'] == "Start New Game":
            points_required = request.form.get('dropdown_points')
            game = TableTennisGame(points_required)
            table_tennis.set_current_game(game)
            noactivegame = table_tennis.noactive_game()
        elif request.form.get('increase_p1') and request.form['increase_p1'] == "Increment Player 1 Score":
            table_tennis.current_game.increment(0)
            winner = table_tennis.current_game.check_winner()
        elif request.form.get('decrease_p1') and request.form['decrease_p1'] == "Decrement Player 1 Score":
            table_tennis.current_game.decrement(0)
            winner = table_tennis.current_game.check_winner()
        elif request.form.get('increase_p2') and request.form['increase_p2'] == "Increment Player 2 Score":
            table_tennis.current_game.increment(1)
            winner = table_tennis.current_game.check_winner()
        elif request.form.get('decrease_p2') and request.form['decrease_p2'] == "Decrement Player 2 Score":
            table_tennis.current_game.decrement(1)
            winner = table_tennis.current_game.check_winner()
        elif ((request.form.get('confirm_winner') and request.form['confirm_winner'] == "Confirm Winner") or 
              (request.form.get('end_game') and request.form['end_game'] == "End Game")):
            table_tennis.end_game()
            noactivegame = table_tennis.noactive_game()
            winner = False
            recording_active = False
        elif request.form.get('unconfirm_winner') and request.form['unconfirm_winner'] == "Unconfirm Winner":
            table_tennis.current_game.unconfirm_winner()
            winner = False
        return render_template('admin.html', noactivegame=noactivegame, winner=winner, recording_active=recording_active)
    elif request.method == 'GET':
        return render_template('admin.html', noactivegame=noactivegame, winner=winner, recording_active=recording_active)

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
