from collections import OrderedDict
import sys
import os
import time

class Tracer(object):
    def __init__(self, columns=6, rows=4):
        self.columns = columns
        self.rows = rows
        self.position = (0, 0)
        self.history = OrderedDict()
        self.history[self.position] = self.possibilities()

    def possibilities(self):
        p = [(self.position[0] + l*i, self.position[1] + k*j) for k in [-1, 1] for l in [-1, 1]
                                        for i in range(1, 3) for j in range(1, 3) if i + j == 3]
        p = [(r, s) for (r, s) in p if r in range(self.columns) and s in range(self.rows)
                                                            and not (r, s) in self.history]
        return p

    def trace(self):
        while not self.done():
            possibilities = self.history[next(reversed(self.history))]
            if possibilities:
                position = possibilities.pop()
                path = self.move(position)
            else:
                try:
                    self.back()
                except StopIteration:
                    break
        if path:
            return path
        else:
            print("No solution fond!")


    def move(self, position):
        self.position = position
        self.history[position] = self.possibilities()
        if self.done():
            solution = list(self.history.keys())
            print("Found path:", solution)
            return solution

    def back(self):
        self.history.popitem()
        self.position = next(reversed(self.history))

    def done(self):
        return len(self.history) == self.columns * self.rows

def print_there(row, col, text):
    sys.stdout.write("\x1b7\x1b[%d;%df%s\x1b8" % (row + 6, col + 6, text))
    sys.stdout.flush()

if __name__ == '__main__':
    os.system("clear")
    a = int(input("Columns: "))
    b = int(input("Rows: "))
    t = Tracer(a, b)
    print("Calculating...")
    solution = t.trace()
    if solution:
        os.system("setterm -cursor off")
        for row in range(b):
            for col in range(a):
                    print_there(row, col, "*")
        prev_row, prev_col = 0, 0
        pawn = u"\u265e"
        print_there(solution[0][0], solution[0][1], "\033[92m" + pawn)
        time.sleep(1)
        for row, col in solution[1:]:
            print_there(prev_col, prev_row, "\033[94m*")
            print_there(col, row, "\033[92m" + pawn)
            prev_row, prev_col = row, col
            time.sleep(1)
        os.system("setterm -cursor on")
