#!/usr/bin/python3

from itertools import product, cycle
from collections import defaultdict
from random import shuffle
import time
import os

def print_there(row, col, text):
    sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (row, col + 40, text))
    sys.stdout.flush()

class MauMau(Exception):
    pass

class Card(object):
    symbols = {"spades": u"\u2660",
               "hearts": u"\u2665",
               "diamonds": u"\u2666",
               "clubs": u"\u2663"}
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
    def __repr__(self):
        top = u"\u256d" + u"\u2500"*5 + u"\u256e\n"
        bottom = u"\u2570"+ u"\u2500"*5 + u"\u256f"
        interior = (u"\u2502" + Card.symbols[self.suit] + " " * 4 + u"\u2502\n"
                    + u"\u2502" + "     " + u"\u2502\n"
                    + u"\u2502" + " " + "{:>2}".format(self.rank) + "  " + u"\u2502\n"
                    + u"\u2502" + "     " + u"\u2502\n"
                    + u"\u2502" + " " * 4 + Card.symbols[self.suit] + u"\u2502\n")
        return top + interior + bottom

class Player(object):
    def __init__(self, game, name):
        self.cards = []
        self.game = game
        self.name = name
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
        print("{} has to draw {} cards!".format(self.name, 2 * self.game.sevens))
        self.game.sevens = 0
    def play(self, card):
        self.cards.remove(card)
        self.game.central_stack.append(card)
        print("{} plays {} of {}.".format(self.name, card.rank, card.suit))
        if card.rank == "7":
            self.game.sevens += 1
        else:
            self.game.sevens = 0
        if not self.cards:
            raise MauMau

class AIPlayer(Player):
    def move(self, skipped):
        top_card = self.game.central_stack[-1]
        if top_card.rank == "7":
            sevens = [c for c in self.cards if c.rank == "7"]
            if sevens:
                self.play(sevens[0])
                return False
            else:
                self.handle_sevens()
        elif top_card.rank == "8" and not skipped:
            print("{} has to skip one round.".format(self.name))
            return True
        matching_suit = [c for c in self.cards if c.suit == top_card.suit]
        matching_rank = [c for c in self.cards if c.rank == top_card.rank]
        if matching_suit:
            self.play(matching_suit[0])
            return False
        elif matching_rank:
            self.play(matching_rank[0])
            return False
        else:
            self.take_card()
            matching_suit = [c for c in self.cards if c.suit == top_card.suit]
            matching_rank = [c for c in self.cards if c.rank == top_card.rank]
            if matching_suit:
                self.play(matching_suit[0])
            elif matching_rank:
                self.play(matching_rank[0])
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
    def move(self, skipped):
        top_card = self.game.central_stack[-1]
        if top_card.rank == "7":
            sevens = [c for c in self.cards if c.rank == "7"]
            if not sevens:
                self.handle_sevens()
        elif top_card.rank == "8" and not skipped:
            print("{} has to skip one round.".format(self.name))
            return True
        matching_suit = [c for c in self.cards if c.suit == top_card.suit]
        matching_rank = [c for c in self.cards if c.rank == top_card.rank]
        if not matching_suit and not matching_rank:
            if self.game.sevens:
                self.handle_sevens()
            self.take_card()
        matching_suit = [c for c in self.cards if c.suit == top_card.suit]
        matching_rank = [c for c in self.cards if c.rank == top_card.rank]
        if not matching_suit and not matching_rank:
            return False
        else:
            card_index = int(input("Enter the card you want to play: "))
            card = self.cards[card_index - 1]
            self.play(card)


    def __repr__(self):
        return "\n".join(["".join([str(card).split("\n")[index][:4]
                                            for card in self.cards[:-1]])
                                    + str(self.cards[-1]).split("\n")[index]
                                                    for index in range(7)])


class Deck(list):
    suits = ["spades", "hearts", "diamonds", "clubs"]
    ranks = [str(n) for n in range(7, 11)] + ["J", "Q", "K", "A"]
    base_deck = list(map(lambda c: Card(*c), list(product(ranks, suits))))
    def __init__(self):
        shuffle(Deck.base_deck)
        super().__init__(Deck.base_deck)


class Game(object):
    def __init__(self):
        self.row = 1
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
                print("{} has won!".format(self.current_player.name))
                break

    def __repr__(self):
        anchor = "\x1b7\x1b[1;1f"
        cards = "\n".join([str(player) for player in self.player_list])
        center = [""] * 4 + [(" " * 7) + line for line in str(self.central_stack[-1]).splitlines()] + [""]*12
        all = "\n".join([anchor] + [c + l for c, l in zip(cards.splitlines(), center)] +
                ["  ".join(["{:>2}".format(str(i)) for i in range(1, len(self.player_list[2].cards) + 1)])] + ["\x1b8"])
        return all

if __name__ == "__main__":
    game = Game()
    game.play()
