from collections import deque
import datetime
import random
import cv2, os
from playsound import playsound


from base_camera import BaseCamera
from camera import Camera

root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
serve_bell = os.path.join(root_dir, "sound", "serve_bell.wav")
score_bell = os.path.join(root_dir, "sound", "score_bell.wav")

class TableTennisGame():
    # Keep track of the game state
    def __init__(self, pr):
        self.score = [0, 0]
        self.set_first_server()
        self.points_required = int(pr)
        self.set_serves_per_turn()
        self.recalculate_server()
        self.current_state = "PRE-SERVE"
        self.timeout = None

    def __str__(self):
        return "Game to " + str(self.points_required) + " with score " + str(self.score[0]) + "-" + str(self.score[1])

    def set_serves_per_turn(self):
        # If both players have deuce, then there is 1 serve per turn
        if self.points_required == 21:
            if self.score[0] >= 20 and self.score[1] >= 20:
                self.serves_per_turn = 1
            else:
                self.serves_per_turn = 5
        elif self.points_required == 11:
            if self.score[0] >= 10 and self.score[1] >= 10:
                self.serves_per_turn = 1
            else:
                self.serves_per_turn = 2
        else:
            self.serves_per_turn = 1

    def set_first_server(self):
        # Randomly determine the first server
        self.first_server = random.getrandbits(1)

    def increment(self, player):
        if not self.check_winner():
            self.score[player] += 1
            playsound(score_bell)
        self.recalculate_server()
        self.current_state = "PRE-SERVE"

    def decrement(self, player):
        if not self.check_winner() and self.score[player] > 0:
            self.score[player] -= 1
        self.recalculate_server()
        self.current_state = "PRE-SERVE"

    def recalculate_server(self):
        # Based on the points, first server, and num serves per turn
        points_done = self.score[0] + self.score[1]
        self.set_serves_per_turn()
        serve_turns_completed = points_done // self.serves_per_turn
        if serve_turns_completed % 2 == 1:
            # Server is not the first server since odd number of turns completed
            if self.first_server == 0:
                self.server = 1
            else:
                self.server = 0
        else:
            self.server = self.first_server

    def get_non_server(self):
        if self.server == 0:
            return 1
        elif self.server == 1:
            return 0

    def check_winner(self):
        if ((self.score[0] >= self.points_required and self.score[0] >= self.score[1] + 2) or 
            (self.score[1] >= self.points_required and self.score[1] >= self.score[0] + 2)):
            return True
        else:
            return False

    def find_winner(self):
        if (self.score[0] >= self.points_required and self.score[0] >= self.score[1] + 2):
            return 0
        elif (self.score[1] >= self.points_required and self.score[1] >= self.score[0] + 2):
            return 1
        else:
            return None

    def unconfirm_winner(self):
        # reduce highest score by 1 since last point is not counting
        if self.score[0] > self.score[1]:
            self.score[0] -= 1
            self.recalculate_server()
        elif self.score[0] < self.score[1]:
            self.score[1] -= 1
            self.recalculate_server()
        else:
            print("Warning: Unconfirming a winner with tied score is not valid")

    def update_game_state(self, pts, frame):
        # Update the game's state machine
        # States include: PRE-SERVE, SERVE, BEFORE-NET, OVER-NET, EXPECT-HIT, GAME-OVER
        if self.current_state == "PRE-SERVE":
            if self.check_winner():
                self.current_state = "GAME-OVER"
                self.set_timeout(None)
            elif self.detect_pre_serve(pts):
                self.current_state = "SERVE"
                playsound(serve_bell)
                self.set_timeout(None)
        elif self.current_state == "SERVE":
            if self.detect_bounce(pts, frame) and self.server == self.get_ball_side(pts):
                self.current_state = "BEFORE-NET"
                self.set_timeout(datetime.datetime.now()) # state change
        elif self.current_state == "BEFORE-NET":
            if (self.detect_bounce(pts, frame) and self.server == self.get_ball_side(pts)) or self.detect_timeout():
                # Double bounce on server's side; award point to nonserver
                self.increment(self.get_non_server())
                self.set_timeout(None)
            elif self.get_ball_side(pts) == self.get_non_server():
                self.current_state = "OVER-NET"
                self.set_timeout(datetime.datetime.now()) # state change
        elif self.current_state == "OVER-NET":
            if self.detect_hit(pts, frame) or self.detect_timeout():
                # Hit before bounce; award point to non ball side
                self.increment(self.get_non_ball_side(pts))
                self.set_timeout(None)
            elif self.detect_bounce(pts, frame):
                self.current_state = "EXPECT-HIT"
                self.set_timeout(datetime.datetime.now()) # state change
        elif self.current_state == "EXPECT-HIT":
            if self.detect_bounce(pts, frame) or self.detect_timeout():
                # 2nd bounce on same side
                self.increment(self.get_non_ball_side(pts))
                self.set_timeout(None)
            elif self.detect_hit(pts, frame):
                self.current_state = "BEFORE-NET"
                self.set_timeout(datetime.datetime.now()) # state change
        elif self.current_state == "GAME-OVER":
            # Check for reversal of last point...
            if not self.check_winner():
                self.current_state = "PRE-SERVE"
                self.set_timeout(None)
        else:
            print("Warning: Unrecognized state in state machine:", self.current_state)

    def detect_pre_serve(self, pts):
        # Returns True/False if ball is above serve height on server's side of screen
        pts = list(pts)[0:3] # check most recent 3 points
        for pt in pts:
            if pt != None and pt[1] < 70 and self.server == self.get_ball_side(pts):
                return True
        # Checked points are bad
        return False

    def detect_bounce(self, pts, frame):
        # Returns True/False if ball went down then up (inspect Camera.hotbox_log)
        motion_seq = [] # list of relative down/up or -1, 1
        hotboxes = Camera.hotbox_log
        # Exactly 1 upward and 1 downward box transitions means bounce
        for idx in range(len(hotboxes) - 1):
            h1_box = hotboxes[idx]
            h2_box = hotboxes[idx + 1]
            if h1_box == None or h2_box == None or h1_box[1] or h2_box[1]:
                return False # not enough hotboxes or already used hotbox
            h1 = h1_box[0]
            h2 = h2_box[0]
            if h1[1] < h2[1]:
                motion_seq.append(-1) # down
            elif h1[1] >= h2[1]:
                motion_seq.append(1) # up

        if motion_seq != [-1, 1]:
            return False
        else:
            # Mark the hotboxes as 'used' for the bounce
            for i in range(len(Camera.hotbox_log)):
                Camera.hotbox_log[i] = (Camera.hotbox_log[i][0], True, Camera.hotbox_log[i][2])
            if Camera.debug:
                cv2.putText(frame, "BOUNCE", pts[0], cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_4)
            return True

    def get_ball_side(self, pts):
        # Returns 0 or 1 for Left/Right side of frame
        for pt in pts:
            if pt == None: # try a different point
                continue
            if pt[0] < int(BaseCamera.get_frame_size()[1] / 2):
                return 0
            elif pt[0] > int(BaseCamera.get_frame_size()[1] / 2):
                return 1
        return -1 # not found

    def get_non_ball_side(self, pts):
        side = self.get_ball_side(pts)
        if side == 0:
            return 1
        elif side == 1:
            return 0
        else:
            return -1

    def detect_hit(self, pts, frame):
        # Returns True/False if ball went left then right or
        # right then left (depending on side of table)
        if self.get_ball_side(pts) == 0:
            goal = [-1, 1] # left side of table means left then right
        elif self.get_ball_side(pts) == 1:
            goal = [1, -1] # right side of table means right then left
        else:
            return False # no ball in frame...
        motion_seq = [] # list of relative left/right or -1, 1
        hotboxes = Camera.hotbox_log
        # Exactly 3 upward and 3 downward box transitions means bounce
        for idx in range(len(hotboxes) - 1):
            h1_box = hotboxes[idx]
            h2_box = hotboxes[idx + 1]
            if h1_box == None or h2_box == None or h1_box[2] or h2_box[2]:
                return False # not enough hotboxes or already used hotbox
            h1 = h1_box[0]
            h2 = h2_box[0]
            if h1[0] > h2[0]:
                motion_seq.append(-1) # left
            elif h1[0] <= h2[0]:
                motion_seq.append(1) # right

        if motion_seq != goal:
            return False
        else:
            # Mark the hotboxes as 'used' for the hit
            for i in range(len(Camera.hotbox_log)):
                Camera.hotbox_log[i] = (Camera.hotbox_log[i][0], Camera.hotbox_log[i][1], True)
            if Camera.debug:
                cv2.putText(frame, "HIT", pts[0], cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_4)
            return True

    def set_timeout(self, time):
        # Sets the time for the last state change
        # None: reset the timeout as we went back to "PRE-SERVE"
        # actual time: other state change
        self.timeout = time


    def detect_timeout(self):
        # Returns True/False if last state change was more than 5 seconds or not
        if self.timeout == None:
            return False
        elif datetime.datetime.now() - self.timeout >= datetime.timedelta(seconds=5):
            return True
        else:
            return False