#!/usr/bin/env python
from importlib import import_module
import os
from flask import Flask, render_template, Response, request, redirect, url_for, session
import flask_login

import argparse

# import camera driver
from camera import Camera

from table_tennis import TableTennis
from table_tennis_game import TableTennisGame

parser = argparse.ArgumentParser()
parser.add_argument('--save_video', default=False, action='store_true', help="Defaults to False if not passed")
args = parser.parse_args()

app = Flask(__name__)
app.secret_key = 'adminpassword'

login_manager = flask_login.LoginManager()

login_manager.init_app(app)

# Mock database.
users = {'admin': {'password': 'admin'}}

# Initialize game states
table_tennis = TableTennis()

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
        yield b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n--frame\r\n'

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera(args.save_video)),
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
    noactivegame = table_tennis.noactive_game()
    if request.method == 'POST':
        if request.form.get('start_newgame') and request.form['start_newgame'] == "Start New Game":
            points_required = request.form.get('dropdown_points')
            game = TableTennisGame(points_required)
            table_tennis.set_current_game(game)
            noactivegame = table_tennis.noactive_game()
        elif request.form.get('increase_p1') and request.form['increase_p1'] == "Increment Player 1 Score":
            table_tennis.current_game.increment(0)
        elif request.form.get('decrease_p1') and request.form['decrease_p1'] == "Decrement Player 1 Score":
            table_tennis.current_game.decrement(0)
        elif request.form.get('increase_p2') and request.form['increase_p2'] == "Increment Player 2 Score":
            table_tennis.current_game.increment(1)
        elif request.form.get('decrease_p2') and request.form['decrease_p2'] == "Decrement Player 2 Score":
            table_tennis.current_game.decrement(1)
        return render_template('admin.html', noactivegame=noactivegame)
    elif request.method == 'GET':
        return render_template('admin.html', noactivegame=noactivegame)

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
