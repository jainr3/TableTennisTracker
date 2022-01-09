import random

class TableTennisGame():
    # Keep track of the game state
    def __init__(self, pr):
        self.score = [0, 0]
        self.first_server = self.set_first_server()
        self.server = self.recalculate_server()
        self.points_required = int(pr)
        self.set_serves_per_turn()

    def __str__(self):
        return "Game to " + str(self.points_required) + " with score " + str(self.score[0]) + "-" + str(self.score[1])

    def set_serves_per_turn(self):
        if self.points_required == 21:
            self.serves_per_turn = 5
        else:
            self.serves_per_turn = 2

    def set_first_server(self):
        # Randomly determine the first server
        self.first_server = random.getrandbits(1)

    def increment(self, player):
        if not self.check_winner():
            self.score[player] += 1
        self.recalculate_server()

    def decrement(self, player):
        if not self.check_winner() and self.score[player] > 0:
            self.score[player] -= 1
        self.recalculate_server()

    def recalculate_server(self):
        # Based on the points, first server, and num serves per turn
        points_done = self.score[0] + self.score[1]
        serve_turns_completed = points_done // self.serves_per_turn
        if serve_turns_completed % 2 == 1:
            # Server is not the first server since odd number of turns completed
            if self.first_server == 0:
                self.server = 1
            else:
                self.server = 0
        else:
            self.server = self.first_server

    def check_winner(self):
        if self.score[0] == self.points_required or self.score[1] == self.points_required:
            return True
        else:
            return False

    def find_winner(self):
        if self.score[0] == self.points_required:
            return 0
        elif self.score[1] == self.points_required:
            return 1
        else:
            return None