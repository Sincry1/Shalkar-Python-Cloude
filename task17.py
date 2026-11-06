
class Game:
    games_played = 0 
    def __init__(self, title):
        self.title = title
        Game.games_played += 1


if __name__ == "__main__":
    Game("Шахматы")
    Game("Шашки")
    Game("Домино")
    print("Всего игр сыграно:", Game.games_played)
