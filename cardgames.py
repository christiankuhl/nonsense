from itertools import product
from random import shuffle

class Card(object):
    """
    A Card is made up of a suite and a rank, and a fancy unicode __repr__ string.
    """
    symbols = {"spades": u"\u2660",
               "hearts": u"\u2665",
               "diamonds": u"\u2666",
               "clubs": u"\u2663"}
    def __init__(self, rank, suite):
        self.rank = rank
        self.suite = suite
    def __repr__(self):
        """
        Paint a card with the rank in the top left and bottom right corner
        and the suite symbol printed in the middle.
        """
        bottom = u"\u2570"+ u"\u2500"*5 + u"\u256f"
        if len(self.rank) < 3:
            rank = self.rank
        else:
            rank = self.rank[0].upper()
        top = u"\u256d" + u"\u2500"*5 + u"\u256e\n"
        interior = (u"\u2502" + "{:<2}".format(rank) + " " * 3 + u"\u2502\n"
                    + u"\u2502" + "     " + u"\u2502\n"
                    + u"\u2502" + "  " + Card.symbols[self.suite] + "  " + u"\u2502\n"
                    + u"\u2502" + "     " + u"\u2502\n"
                    + u"\u2502" + " " * 3 + "{:>2}".format(rank) + u"\u2502\n")
        return top + interior + bottom

class Hand(list):
    """
    A Hand() object is just a list of Card() objects, which additionally can be
    addressed by an alphabetical index in order for the user to be able to
    select a card with a single key press.
    """
    alphabet = "123456789abcdefghijklmnopqrstuvwxyz"
    def __call__(self, index):
        position = Hand.alphabet.find(index.lower())
        if position > -1:
            return self[position]
        else:
            raise IndexError

class Deck(list):
    """
    A Deck(n, s) is a shuffeled list of n copies of the cartesian product of
    Deck.suites and ranks from s to 10 and "jack", "queen", "king" and "ace".
    """
    suites = ["spades", "hearts", "diamonds", "clubs"]
    def __init__(self, n=1, start=7):
        ranks = [str(n) for n in range(start, 11)] + ["jack", "queen", "king", "ace"]
        base_deck = list(map(lambda c: Card(*c), list(product(ranks, Deck.suites)))) * n
        shuffle(base_deck)
        super().__init__(base_deck)
