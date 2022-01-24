import cv2
from base_camera import BaseCamera

class TableTennis():
    def __init__(self):
        self.current_game = None 
        self.past_games = []

    def noactive_game(self):
        # Returns boolean if there is no current game happening
        if self.current_game == None:
            return True
        else:
            return False

    def set_current_game(self, game):
        self.current_game = game

    def update_visual_display(self, frame):
        if not self.noactive_game():
            # Active game going, augment scores onto frame, who is serving; colors based on score
            score_string = str(self.current_game.score[0]) + " "
            if self.current_game.score[0] < 10:
                score_string += " "
            if self.current_game.score[1] < 10:
                score_string += " "
            score_string += " " + str(self.current_game.score[1])

            font = cv2.FONT_HERSHEY_SIMPLEX

            # get boundary of this text
            textsize = cv2.getTextSize(score_string, font, 1, 2)[0]
            text_w, text_h = textsize

            # get coords based on boundary
            textX = int((frame.shape[1] - textsize[0]) / 2)
            textY = int((frame.shape[0] + textsize[1]) / 2)

            cv2.rectangle(frame, (textX - 10, BaseCamera.frame_h - 45), (textX + text_w + 10, BaseCamera.frame_h - 55 - text_h), (0, 0, 0), -1)

            if self.current_game.server == 0:
                cv2.circle(frame, (textX - 5, BaseCamera.frame_h - 45 - 15), 3, (0, 155, 255), -1)
            elif self.current_game.server == 1:
                cv2.circle(frame, (textX + text_w + 5, BaseCamera.frame_h - 45 - 15), 3, (0, 155, 255), -1)

            cv2.putText(frame, 
                        score_string, 
                        (textX, BaseCamera.frame_h - 50), 
                        font, 1, 
                        (255, 255, 255), 
                        2, 
                        cv2.LINE_4)

        return frame

    def end_game(self):
        # Keep a log of past games.
        self.past_games.append(self.current_game)
        self.current_game = None
