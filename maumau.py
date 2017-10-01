#!/usr/bin/python3

from cardgames import Card, Hand, Deck
from itertools import cycle
from collections import deque
from random import randint
import time
import os
import sys
import tty
import termios
import types

class MessageHandler(object):
    """
    MessageHandler handles writing messages to different areas of the screen.
    push(msg) pushes msg to the queue on the right hand side, while user_message(msg)
    posts to the bottom area, below the displayed cards
    """
    def __init__(self):
        self.messages = deque([], maxlen=20)
    def push(self, text):
        self.messages.append(text)
        for row, line in enumerate(self.messages, start=2):
            line = "{:<40}".format(line)
            sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (row, 60, line))
            sys.stdout.flush()
    def user_message(self, msg=""):
        print("\033[30;1H") # Place the (invisible) cursor at line 30, column 1
        print("\x1b7\x1b[%d;%df%s\x1b8" % (26, 5, "{:<54}".format(msg)))

class MauMau(Exception):
    """
    Exception raised when somebody has won.
    """
    pass

class GameAbort(Exception):
    """
    Exception raised when the user wants to end the game.
    """
    pass

class Player(object):
    """
    Base class for player objects. Encapsulates the core game mechanics of drawing
    and playing cards.
    """
    def __init__(self, game, name):
        self.cards = Hand()
        self.game = game
        self.name = name
        self.message = self.game.message
    def take_card(self):
        """
        Take a card from the deck. If the deck is empty, take the bottom n-1 cards
        from the central stack and shuffle them to get a new deck.
        """
        if not self.game.deck:
            self.game.deck = self.game.central_stack[:-1]
            self.game.central_stack = [self.game.central_stack[-1]]
            shuffle(self.game.deck)
        self.cards.append(self.game.deck.pop())
    def handle_sevens(self):
        """
        Take 2n cards from the deck if there are n "active" sevens in the middle.
        """
        for _ in range(self.game.sevens):
            self.take_card()
            self.take_card()
        self.message.push("{} has to draw {} cards!".format(self.name, 2 * self.game.sevens))
        self.game.sevens = 0
        print(self.game)
    def matches(self, top_card):
        matching_suite = [c for c in self.cards if c.suite == top_card.suite]
        matching_rank = [c for c in self.cards if c.rank == top_card.rank]
        return matching_suite, matching_rank
    def move(self):
        """
        Automates the players choices as far as possible regardless of if it is
        a human or AI player. Returns True, if we have to skip one round, False,
        if the player has to pass, and None otherwise.
        """
        top_card = self.game.central_stack[-1]
        # If the top card is a 8, we have to skip this round if the 8 is still
        # effective, that is, if no other player before us has skipped because
        # of this card.
        if self.game.eights:
            self.message.push("{} has to skip one round.".format(self.name))
            self.game.eights = 0
            return True
        # If the top card is a 7, we can avoid having to draw 2(n) cards if we play
        # a 7 of our own. However, we leave this choice (if there is one) to the
        # player, hence, we call handle_sevens only if there is no other possibility
        elif top_card.rank == "7" and self.game.sevens:
            sevens = [c for c in self.cards if c.rank == "7"]
            if not sevens:
                self.handle_sevens()
        # Now look if we have matching cards. If not, draw a card from the deck.
        matching_suite, matching_rank = self.matches(top_card)
        if not matching_suite and not matching_rank:
            self.take_card()
            self.message.push("{} has to draw a card.".format(self.name))
            print(self.game)
        # Look (possibly) again for a match. If there is none, we have to pass.
        matching_suite, matching_rank = self.matches(top_card)
        if not matching_suite and not matching_rank:
            self.message.push("{} has to pass.".format(self.name))
            return False
        # At this point, there is (possibly) a choice left to the player, which
        # may differ for AI and human players. Therefore, we return None.
        return None
    def play(self, card):
        """
        Play out a card, announce that we have won by raising MauMau, increment
        and decrement the counters of unhandeled sevens and eights
        """
        self.cards.remove(card)
        self.game.central_stack.append(card)
        self.message.push("{} plays {} of {}.".format(self.name, card.rank, card.suite))
        if card.rank == "7":
            self.game.sevens += 1
        else:
            self.game.sevens = 0
        if card.rank == "8":
            self.game.eights = 1
        else:
            self.game.eights = 0
        if not self.cards:
            raise MauMau

class AIPlayer(Player):
    """
    Fairly unintelligent AI player - simply follows the rules and prefers dick
    moves over harmless ones.
    """
    def move(self):
        # Delegate to general Player object. If there is already a decision,
        # we are done. Otherwise, select the next best dick move.
        auto_decision = super().move()
        if auto_decision is not None:
            return
        top_card = self.game.central_stack[-1]
        # Always respond to an "active" seven with a seven
        if top_card.rank == "7" and self.game.sevens:
            sevens = [c for c in self.cards if c.rank == "7"]
            if sevens:
                self.play(sevens[0])
                return
            else:
                self.handle_sevens()
        # Otherwise, select next best a****** move
        matching_suite, matching_rank = self.matches(top_card)
        if matching_suite:
            sevens = [c for c in matching_suite if c.rank == "7"]
            eights = [c for c in matching_suite if c.rank == "8"]
            if sevens:
                self.play(sevens[0])
            elif eights:
                self.play(eights[0])
            else:
                self.play(matching_suite[0])
        elif matching_rank:
            self.play(matching_rank[0])
        return
    def _repr(self):
        """
        Print a single box with the player's name and the number of cards in the
        player's hand in it.
        """
        top = u"\u256d" + u"\u2500"*5 + u"\u256e\n"
        bottom = u"\u2570"+ u"\u2500"*5 + u"\u256f"
        interior = (u"\u2502" + " " * 5 + u"\u2502\n"
                    + u"\u2502" + self.name + u"\u2502\n"
                    + u"\u2502" + " " + "{:>2}".format(len(self.cards)) + "  " + u"\u2502\n"
                    + u"\u2502" + "     " + u"\u2502\n"
                    + u"\u2502" + " " * 5 + u"\u2502\n")
        return top + interior + bottom
    def __repr__(self):
        return self._repr()

class HumanPlayer(Player):
    """
    Class for human players.
    """
    def get_user_input(self, msg="Enter the card you want to play! [X to exit game]"):
        """
        Get a single character user input.
        """
        self.message.user_message(msg)
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)    # store old terminal settings
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)  # read single character
            if ch.lower() == "x":   # "x" is reserved for quitting the game
                raise GameAbort
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings) # restore old settings
        return ch
    def move(self):
        """
        Human player move.
        """
        # Delegate to general Player object. If there is already a decision,
        # we are done. Otherwise, select the next best dick move.
        auto_decision = super().move()
        if auto_decision is not None:
            return
        # At this point, there are still choices left to the user. Loop until
        # we either get a valid card to play or the user decides to end the game.
        while True:
            try:
                card_index = self.get_user_input()
                card = self.cards(card_index)
                if self.game.is_legal(card):
                    if card.rank != "7" and self.game.sevens:
                        # The user chose not to respond to an "active" 7, even
                        # if he could have. Now live with it and draw 2(n) cards.
                        self.handle_sevens()
                    self.play(card)
                    self.message.user_message("")
                    break
                else:
                    # You selected an invalid card, dumbass!
                    self.message.user_message("You can't play {} of {} now!".format(card.rank, card.suite))
                    time.sleep(1)
            except IndexError:
                pass
            except GameAbort:
                char = self.get_user_input("Do you really want to quit the game? [y/n]")
                if char.lower() == "y":
                    raise GameAbort
                else:
                    continue
    def __repr__(self):
        """
        Displays the human player's hand.
        """
        try:
            hand = "\n".join(map("{:<59}".format,
                                 ["".join([str(card).split("\n")[index][:4]
                                            for card in self.cards[:-1]])
                                    + str(self.cards[-1]).split("\n")[index]
                                                    for index in range(7)]))
        except IndexError:
            # Occurs when the human player has won.
            hand = "\n".join([" " * 59] * 7)
        return hand

class Game(object):
    """
    Game is the class encapsulating the game logic of (counterclockwise) rounds
    of the players in Game().player_list, breaking out of the endless loop in
    Game().play() only if either MauMau or GameAbort is raised.
    """
    def __init__(self, demo=False):
        """
        Sets the stage: Shuffles the deck, hands out 7 cards to each player
        and places a card in the middle.
        demo = True creates a game with 3 AI players.
        """
        self.message = MessageHandler()
        self.deck = Deck()
        self.central_stack = []
        if not demo:
            self.horst = HumanPlayer(self, "Horst")
        else:
            # Patch "Horst" to be an AIPlayer with the same __repr__ as a human player
            self.horst = AIPlayer(self, "Horst")
            self.horst._repr = types.MethodType(HumanPlayer.__repr__, self.horst)
        self.player_list = [AIPlayer(self, "Fritz"), AIPlayer(self, "Franz"), self.horst]
        self.players = cycle(self.player_list)
        # When simulating 3 random players a million times, it turns out that the
        # last player has a 2% handicap compared to the others. Hence: Random beginner.
        for _ in range(randint(0, 2)):
            next(self.players)
        # Distribute cards.
        for _ in range(7):
            for _ in range(3):
                self.current_player = next(self.players)
                self.current_player.take_card()
        self.central_stack.append(self.deck.pop())
        # Set up central counters for the number of unhandeled sevens and eights.
        if self.central_stack[-1].rank == "7":
            self.sevens = 1
        else:
            self.sevens = 0
        if self.central_stack[-1].rank == "8":
            self.eights = 1
        else:
            self.eights = 0
    def is_legal(self, card):
        top_card = self.central_stack[-1]
        return top_card.suite == card.suite or top_card.rank == card.rank
    def play(self):
        skipped = False
        length = 0
        while True:
            length += 1
            # Print the game
            print(self)
            # Next player
            self.current_player = next(self.players)
            time.sleep(1)
            try:
                self.current_player.move()
            except MauMau:
                # Winner, winner, chicken dinner!
                print(self)
                self.message.push("{} has won!".format(self.current_player.name))
                if self.current_player != self.horst:
                    self.message.user_message("Sorry, you have lost against {}!".format(self.current_player.name))
                else:
                    self.message.user_message("Congratulations {}, you have won this game!".format(self.current_player.name))
                break
            except GameAbort:
                self.message.user_message("Thank you for playing!")
                break
        return self.current_player.name, length

    def __repr__(self):
        """
        Representing unicode string for the game: First row is Fritz, then Franz, then Horst (the human player).
        """
        anchor = "\x1b7\x1b[1;1f" # ANSI escape sequence to start at row 1, columm 1
        cards = "\n".join([str(player) for player in self.player_list]) # the players' cards
        center = [""] * 4 + [(" " * 7) + line for line in str(self.central_stack[-1]).splitlines()] + [""]*12 # the central stack gets printed in the middle
        # Join everything up.
        all = "\n".join([anchor] + [c + l for c, l in zip(cards.splitlines(), center)] +
                ["{:<59}".format("  ".join(["{:>2}".format(Hand.alphabet[i].upper()) for i in range(len(self.player_list[2].cards))]))] + ["\x1b8"])
        return all

if __name__ == "__main__":
    # Clear the screen and turn the cursor off.
    os.system('setterm -cursor off')
    os.system("clear")
    game = Game()
    try:
        game.play()
    finally:
        # No matter what happens during game.play(), turn the cursor back on.
        os.system('setterm -cursor on')
