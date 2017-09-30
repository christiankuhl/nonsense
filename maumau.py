#!/usr/bin/python3

from itertools import product, cycle
from collections import defaultdict, deque
from random import shuffle
import time
import os
import sys
import tty
import termios

class MessageHandler(object):
    def __init__(self):
        self.messages = deque([], maxlen=20)
    def push(self, text):
        self.messages.append(text)
        for row, line in enumerate(self.messages, start=2):
            line = "{:<40}".format(line)
            sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (row, 60, line))
            sys.stdout.flush()
    def user_message(self, msg=""):
        print("\x1b7\x1b[%d;%df%s\x1b8" % (26, 5, "{:<54}".format(msg)))

class MauMau(Exception):
    pass

class GameAbort(Exception):
    pass

class Card(object):
    symbols = {"spades": u"\u2660",
               "hearts": u"\u2665",
               "diamonds": u"\u2666",
               "clubs": u"\u2663"}
    def __init__(self, rank, suite):
        self.rank = rank
        self.suite = suite
    def __repr__(self):
        top = u"\u256d" + u"\u2500"*5 + u"\u256e\n"
        bottom = u"\u2570"+ u"\u2500"*5 + u"\u256f"
        if len(self.rank) < 3:
            rank = self.rank
        else:
            rank = self.rank[0].upper()
        interior = (u"\u2502" + Card.symbols[self.suite] + " " * 4 + u"\u2502\n"
                    + u"\u2502" + "     " + u"\u2502\n"
                    + u"\u2502" + " " + "{:>2}".format(rank) + "  " + u"\u2502\n"
                    + u"\u2502" + "     " + u"\u2502\n"
                    + u"\u2502" + " " * 4 + Card.symbols[self.suite] + u"\u2502\n")
        return top + interior + bottom

class Hand(list):
    alphabet = "123456789abcdefghijklmnopqrstuvwxyz"
    def __call__(self, index):
        position = Hand.alphabet.find(index.lower())
        if position > -1:
            return self[position]
        else:
            raise IndexError

class Player(object):
    def __init__(self, game, name):
        self.cards = Hand()
        self.game = game
        self.name = name
        self.message = self.game.message
    def take_card(self):
        self.cards.append(self.game.deck.pop())
        if not self.game.deck:
            self.game.deck = self.game.central_stack[:-1]
            self.central_stack = self.game.central_stack[-1]
            shuffle(self.game.deck)
    def handle_sevens(self):
        for _ in range(self.game.sevens):
            self.take_card()
            self.take_card()
        self.message.push("{} has to draw {} cards!".format(self.name, 2 * self.game.sevens))
        self.game.sevens = 0
        print(self.game)
    def play(self, card):
        self.cards.remove(card)
        self.game.central_stack.append(card)
        self.message.push("{} plays {} of {}.".format(self.name, card.rank, card.suite))
        if card.rank == "7":
            self.game.sevens += 1
        else:
            self.game.sevens = 0
        if not self.cards:
            raise MauMau

class AIPlayer(Player):
    def move(self, skipped):
        top_card = self.game.central_stack[-1]
        if top_card.rank == "7" and self.game.sevens:
            sevens = [c for c in self.cards if c.rank == "7"]
            if sevens:
                self.play(sevens[0])
                return False
            else:
                self.handle_sevens()
        elif top_card.rank == "8" and not skipped:
            self.message.push("{} has to skip one round.".format(self.name))
            return True
        matching_suite = [c for c in self.cards if c.suite == top_card.suite]
        matching_rank = [c for c in self.cards if c.rank == top_card.rank]
        if matching_suite:
            self.play(matching_suite[0])
            return False
        elif matching_rank:
            self.play(matching_rank[0])
            return False
        else:
            self.take_card()
            matching_suite = [c for c in self.cards if c.suite == top_card.suite]
            matching_rank = [c for c in self.cards if c.rank == top_card.rank]
            if matching_suite:
                self.play(matching_suite[0])
            elif matching_rank:
                self.play(matching_rank[0])
            else:
                self.message.push("{} has to pass.".format(self.name))
            return False
    def __repr__(self):
        top = u"\u256d" + u"\u2500"*5 + u"\u256e\n"
        bottom = u"\u2570"+ u"\u2500"*5 + u"\u256f"
        interior = (u"\u2502" + " " * 5 + u"\u2502\n"
                    + u"\u2502" + self.name + u"\u2502\n"
                    + u"\u2502" + " " + "{:>2}".format(len(self.cards)) + "  " + u"\u2502\n"
                    + u"\u2502" + "     " + u"\u2502\n"
                    + u"\u2502" + " " * 5 + u"\u2502\n")
        return top + interior + bottom

class HumanPlayer(Player):
    def get_user_input(self, msg="Enter the card you want to play! [X to exit game]"):
        print("\033[30;1H")
        self.message.user_message(msg)
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch.lower() == "x":
                raise GameAbort
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    def move(self, skipped):
        top_card = self.game.central_stack[-1]
        if top_card.rank == "7" and self.game.sevens:
            sevens = [c for c in self.cards if c.rank == "7"]
            if not sevens:
                self.handle_sevens()
        elif top_card.rank == "8" and not skipped:
            self.message.push("{} has to skip one round.".format(self.name))
            return True
        matching_suite = [c for c in self.cards if c.suite == top_card.suite]
        matching_rank = [c for c in self.cards if c.rank == top_card.rank]
        if not matching_suite and not matching_rank:
            if self.game.sevens:
                self.handle_sevens()
            self.take_card()
            print(self.game)
        matching_suite = [c for c in self.cards if c.suite == top_card.suite]
        matching_rank = [c for c in self.cards if c.rank == top_card.rank]
        if not matching_suite and not matching_rank:
            self.message.push("{} has to pass.".format(self.name))
            return False
        else:
            while True:
                try:
                    card_index = self.get_user_input()
                    card = self.cards(card_index)
                    if self.game.is_legal(card):
                        self.play(card)
                        self.message.user_message("")
                        break
                    else:
                        self.message.user_message("You can't play {} of {} now!".format(card.rank, card.suite))
                        time.sleep(1)
                except IndexError:
                    pass
                except GameAbort:
                    char = self.get_user_input("Do you really want to quit the game? [y/n]")
                    if char.lower() == "y":
                        self.message.user_message("Thank you for playing!")
                        raise GameAbort
                    else:
                        continue

    def __repr__(self):
        try:
            hand = "\n".join(map("{:<59}".format,
                                 ["".join([str(card).split("\n")[index][:4]
                                            for card in self.cards[:-1]])
                                    + str(self.cards[-1]).split("\n")[index]
                                                    for index in range(7)]))
        except IndexError:
            hand = "\n".join([" " * 59] * 7)
        return hand

class Deck(list):
    suites = ["spades", "hearts", "diamonds", "clubs"]
    ranks = [str(n) for n in range(7, 11)] + ["jack", "queen", "king", "ace"]
    base_deck = list(map(lambda c: Card(*c), list(product(ranks, suites))))
    def __init__(self):
        shuffle(Deck.base_deck)
        super().__init__(Deck.base_deck)

class Game(object):
    def __init__(self):
        self.message = MessageHandler()
        self.deck = Deck()
        self.central_stack = []
        self.player_list = [AIPlayer(self, "Fritz"), AIPlayer(self, "Franz"), HumanPlayer(self, "Horst")]
        self.players = cycle(self.player_list)
        for _ in range(7):
            for _ in range(3):
                self.current_player = next(self.players)
                self.current_player.take_card()
        self.central_stack.append(self.deck.pop())
        if self.central_stack[-1].rank == "7":
            self.sevens = 1
        else:
            self.sevens = 0
    def is_legal(self, card):
        top_card = self.central_stack[-1]
        return top_card.suite == card.suite or top_card.rank == card.rank
    def play(self):
        os.system("clear")
        skipped = False
        while True:
            print(self)
            self.current_player = next(self.players)
            time.sleep(1)
            try:
                skipped = self.current_player.move(skipped)
            except MauMau:
                print(self)
                self.message.push("{} has won!".format(self.current_player.name))
                if type(self.current_player) == AIPlayer:
                    self.message.user_message("Sorry, you have lost against {}!".format(self.current_player.name))
                else:
                    self.message.user_message("Congratulations, you have won this game!")
                break
    def __repr__(self):
        anchor = "\x1b7\x1b[1;1f"
        cards = "\n".join([str(player) for player in self.player_list])
        center = [""] * 4 + [(" " * 7) + line for line in str(self.central_stack[-1]).splitlines()] + [""]*12
        all = "\n".join([anchor] + [c + l for c, l in zip(cards.splitlines(), center)] +
                ["{:<59}".format("  ".join(["{:>2}".format(Hand.alphabet[i].upper()) for i in range(len(self.player_list[2].cards))]))] + ["\x1b8"])
        return all

if __name__ == "__main__":
    os.system('setterm -cursor off')
    game = Game()
    try:
        game.play()
    except:
        pass
    finally:
        os.system('setterm -cursor on')
