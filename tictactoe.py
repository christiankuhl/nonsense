#!/usr/bin/python3

from itertools import cycle, product
import sys
import os

class Board(list):
    """
    This class represents the game's board. b = Board(n) generates an n by n grid.
    Internally, this is simply a matrix (nested list) with some fancy attributes
    for pretty printing and a possibility to get and set board values by address
    (like "A2") instead of index.
    """
    LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    def __init__(self, dimension):
        self.dimension = dimension
        self.letters = list(Board.LETTERS[:dimension])
        self.rows = list(reversed(range(1, dimension + 1)))
        self.fields = [l + str(d) for l, d in product(self.letters, self.rows)]
        # fancy unicode/terminal stuff for pretty printing
        straights = [u"\u2550"] * dimension
        self.anchor = "\x1b7\x1b[4f"
        self.top = u"\n   \u2554"+ u"\u2566".join(straights) + u"\u2557\n"
        self.bottom = u"   \u255a"+ u"\u2569".join(straights) + u"\u255d\n    " + " ".join(self.letters) + "\n\x1b8"
        self.bar = u"   \u2560" + u"\u256c".join(straights) + u"\u2563\n"
        # this is the important part: build a matrix filled with blanks
        super().__init__([[Game.BLANK for _ in range(dimension)] for _ in range(dimension)])
    def __call__(self, address, value=None):
        """
        Read/write the board by address instead of index.
        Example: If b = Board(3), b('A2') is the value of the field 'A2', and
        b('C3', 'X') sets the field 'C3' to 'X'
        """
        if value:
            self[self.dimension - int(address[1:])][self.letters.index(address[0])] = value
        else:
            return self[self.dimension - int(address[1:])][self.letters.index(address[0])]

class Game(object):
    """
    Encapsulates the game logic. Game(p1, p2, dim) sets up a game on a grid of
    dim rows and columns between players named p1 and p2.
    """
    BLANK = " "
    X = "X"
    O = "O"
    def __init__(self, player1, player2, dimension):
        self.dimension = dimension
        self.board = Board(dimension)
        # cycle(it) is a generator which cycles through the elements of it.
        # In our case, we cycle through the player names along with their
        # symbols and store the current player in self.current_player
        self.player = cycle([(player1, Game.X), (player2, Game.O)])
        self.current_player = next(self.player)
        # Move down (cheap ass version)
        for _ in range(2 * dimension + 3):
            print()
    def check(self, symbol):
        "Checks if the player using the symbol 'symbol' has won"
        rows = any([all([mark == symbol for mark in row]) for row in self.board])
        columns = any([all([row[column] == symbol for row in self.board]) for column in range(self.dimension)])
        diagonals = (all([self.board[j][j] == symbol for j in range(self.dimension)])
                     or all([self.board[j][self.dimension-1-j] == symbol for j in range(self.dimension)]))
        return rows or columns or diagonals
    def over(self):
        """
        Check if the game is over. Return the winner if there is one, raise an
        exception in case of a draw and return None otherwise
        """
        winner = None
        # Lazy: Check if either X or O has won, winner is the current player in any case
        if self.check(Game.X) or self.check(Game.O):
            # Remember: First component of self.current_player is the player's name
            winner = self.current_player[0]
        # No blank field left and no winner -> draw
        if not Game.BLANK in [s for row in self.board for s in row] and not winner:
            raise ValueError
        return winner
    def move(self, move):
        "Move the current player's symbol to the board"
        self.board(move, self.current_player[1])
    def legal(self, move):
        "Check if the chosen move is a legal one"
        if not move in self.board.fields:
            print("{} is not a field on this board. Those are {}.".format(move, ", ".join(self.board.fields)))
            return False
        if not self.board(move) == Game.BLANK:
            print("Field {} is already taken!".format(move))
            return False
        return True
    def next(self):
        """
        Next step in the game loop. Prompt for the player's move until we have a
        legal one, move, try to determine a winner, and if there is none, hand
        over to the next player.
        """
        print(self)
        while True:
            # Remember: First component of self.current_player is the player's name
            move = input("{}, enter your move: ".format(self.current_player[0]))
            if self.legal(move):
                break
        self.move(move)
        try:
            winner = self.over()
            if not winner:
                # Hand over to next player
                self.current_player = next(self.player)
            else:
                print(self)
                print("Congratulations, {}, you have won this game!".format(winner))
        except ValueError:
            print("Draw!")

    def play(self):
        """
        This is the main game loop. Repeat Game.next() until it is over.
        """
        gameover = False
        while not gameover:
            self.next()
            try:
                gameover = self.over()
            except:
                gameover = True

    def __repr__(self):
        """
        Generate a representation string so we can print the board by simply
        stating print(self).
        """
        anchor = self.board.anchor
        top = self.board.top
        bottom = self.board.bottom
        interior = self.board.bar.join(
            ["{:>2}".format(str(j)) + u" \u2551" + u"\u2551".join(s)  + u"\u2551\n"
                            for j, s in zip(self.board.rows, self.board)])
        return "".join([anchor, top, interior, bottom])

if __name__ == "__main__":
    """
    All external control is handled here (no game logic!), just parametrisation
    of the game itself.
    """
    # Clear the screen
    os.system("clear")
    player1 = input("Player 1, what's your name? [Dickmilch] ")
    player2 = input("Player 2, what's your name? [Biene] ")
    dimension = input("How big should the board be? [3] ")
    # Set default values in case a player has just hit enter
    if player1 == "":
        player1 = "Dickmilch"
    if player2 == "":
        player2 = "Biene"
    if dimension == '':
        dimension = 3
    else:
        dimension = int(dimension)
    playing = True
    while playing:
        # Set up game
        game = Game(player1, player2, dimension)
        # Play!
        game.play()
        # Do we want to play again?
        playagain = input("Do you want to play again (y/n)? ")
        if playagain == "y" or playagain == "yes":
            playing = True
        else:
            playing = False
    print("Thank you for playing!")
