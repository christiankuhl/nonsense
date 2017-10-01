#!/usr/bin/python3

from cardgames import Card, Hand, Deck

class Game(object):
    def __init__(self):
        self.deck = Deck(n=6, start=2)

class Croupier(object):
    def __init__(self, game):
        self.game = game

if __name__ == "__main__":
    d = Deck(n=6, start=2)
    print(len(d))
