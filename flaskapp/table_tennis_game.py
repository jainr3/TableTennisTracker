
class TableTennisGame():
    # Keep track of the game state
    def __init__(self, pr):
        self.score = [0, 0]
        self.first_server = 0 # TODO
        self.server = None
        self.points_required = int(pr)
        self.set_serves_per_turn()

    def set_serves_per_turn(self):
        if self.points_required == 21:
            self.serves_per_turn = 5
        else:
            self.serves_per_turn = 2

    def set_first_server(self, sv):
        self.first_server = sv

    def increment(self, player):
        self.score[player] += 1
        self.recalculate_server()
        self.check_winner()
        # TODO: Update visual display as well

    def decrement(self, player):
        if self.score[player] > 0:
            self.score[player] -= 1
        self.recalculate_server()
        # TODO: Update visual display as well

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
        if self.score[0] == self.points_required:
            print("P1 wins")
            # TODO end game
        elif self.score[1] == self.points_required:
            print("P2 wins")

    def update_game_state():
        pass
