
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

    def end_game(self):
        # Keep a log of past games, scores, point sequences, etc.
        self.past_games.append(self.current_game)
        self.current_game = None
