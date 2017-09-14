#!/usr/bin/python3

from itertools import product
from collections import deque
from random import shuffle

class Card():
    symbols = {"spades": u"\u2660",
               "hearts": u"\u2665",
               "diamonds": u"\u2666",
               "clubs": u"\u2663"}
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        try:
            self.points = int(rank)
        except ValueError:
            if rank in ["J", "Q", "K"]:
                self.points = 10
            else:
                self.points = None
    def __repr__(self):
        top = u"\u256d" + u"\u2500"*5 + u"\u256e\n"
        bottom = u"\u2570"+ u"\u2500"*5 + u"\u256f"
        interior = (u"\u2502" + Card.symbols[self.suit] + " " * 4 + u"\u2502\n"
                    + u"\u2502" + "     " + u"\u2502\n"
                    + u"\u2502" + " " + "{:>2}".format(self.rank) + "  " + u"\u2502\n"
                    + u"\u2502" + "     " + u"\u2502\n"
                    + u"\u2502" + " " * 4 + Card.symbols[self.suit] + u"\u2502\n")
        return top + interior + bottom

class Deck(list):
    suits = ["spades", "hearts", "diamonds", "clubs"]
    ranks = [str(n) for n in range(2, 11)] + ["J", "Q", "K", "A"]
    base_deck = list(map(lambda c: Card(*c), list(product(ranks, suits)) * 6))

    def __init__(self):
        shuffle(Deck.base_deck)
        super().__init__(Deck.base_deck)


if __name__ == "__main__":
    d = Deck()
    print(d.pop())
