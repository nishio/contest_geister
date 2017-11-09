# -*- encoding: utf-8 -*-
from random import choice, shuffle, seed, random
from copy import copy
from collections import defaultdict, Counter
#seed(1234)

try:
    profile
except:
    profile =  lambda f: f

NUM_GEISTER = 8
BOARD_WIDTH = 6

MAX_POS = BOARD_WIDTH * BOARD_WIDTH - 1
IS_DEAD = MAX_POS + 1

UP = -BOARD_WIDTH
DOWN = BOARD_WIDTH
RIGHT = 1
LEFT = -1

WIN = 'WIN'
LOSE = 'LOSE'
EVEN = 'EVEN'

class Game(object):
    def __init__(self):
        op = [1, 2, 3, 4, 7, 8, 9, 10]
        me = [MAX_POS - pos for pos in op]
        shuffle(op)
        shuffle(me)
        self.me = me
        self.op = op

    @staticmethod
    def rotate(val):
        return [MAX_POS - pos if pos != IS_DEAD else IS_DEAD for pos in val]

    def get_rotated(self, side):
        if side == 1:
            me = self.op
            op = self.me
            # rotate
            me = Game.rotate(me)
            op = Game.rotate(op)
        else:
            me = self.me[:]
            op = self.op[:]

        return me, op

    def to_view(self, side):
        me, op = self.get_rotated(side)

        # drop hidden data of opponent
        dead_blue = 0
        dead_red = 0
        alive = []
        for pos in get_blue(op):
            if pos == IS_DEAD:
                dead_blue += 1
            else:
                alive.append(pos)
        for pos in get_red(op):
            if pos == IS_DEAD:
                dead_red += 1
            else:
                alive.append(pos)

        return View(side, me, alive, dead_blue, dead_red)

    @staticmethod
    def by_val(side, me, op):
        self = Game()
        return self.set_val(side, me, op)

    def set_val(self, side, me, op):
        if side == 0:
            self.me = list(me)
            self.op = list(op)
        else:
            self.me = Game.rotate(op)
            self.op = Game.rotate(me)
        return self


def get_blue(val):
    return val[:NUM_GEISTER / 2]

def get_red(val):
    return val[NUM_GEISTER / 2:NUM_GEISTER]

class View(object):
    def __init__(self, side, me, alive, dead_blue, dead_red):
        self.side = side
        self.me = me
        self.alive = alive
        self.dead_blue = dead_blue
        self.dead_red = dead_red

    def get_blue(self):
        return get_blue(self.me)

    def get_red(self):
        return get_red(self.me)

@profile
def do_move(game, side, move, show_detail=False):
    me, op = game.get_rotated(side)  # copied
    i, d = move
    if d == WIN: return WIN
    if show_detail: print board, move
    newpos = me[i] + d
    if newpos in op:
        #print 'killing', newpos
        opi = op.index(newpos)
        op[opi] = IS_DEAD
        # dead end check
        if all(x == IS_DEAD for x in get_blue(op)):
            return WIN
        if all(x == IS_DEAD for x in get_red(op)):
            return LOSE

    me[i] = newpos
    if show_detail: print board
    #return Game.by_val(side, me, op)
    return game.set_val(side, me, op)


def print_view(view):
    ret = ['.'] * (BOARD_WIDTH * BOARD_WIDTH)
    for pos in view.get_blue():
        if pos != IS_DEAD:
            ret[pos] = 'o'
    for pos in view.get_red():
        if pos != IS_DEAD:
            ret[pos] = 'x'
    for pos in view.alive:
        ret[pos] = 'v'

    print '\n'.join(
        ''.join(ret[i * BOARD_WIDTH:(i + 1) * BOARD_WIDTH])
        for i in range(BOARD_WIDTH))
    print 'o' * view.dead_blue, 'x' * view.dead_red
    print

def get_my_blue(board):
    return board[:NUM_GEISTER / 4]

def swap_turn(board):
    board = [MAX_POS - pos if pos != IS_DEAD else IS_DEAD for pos in board]
    board = board[NUM_GEISTER:] + board[:NUM_GEISTER]
    return board




def to_xy(pos):
    return (pos % BOARD_WIDTH, pos / BOARD_WIDTH)

def find_possible_move(view):
    ret = []
    me = view.me
    for i, pos in enumerate(me):
        if pos == IS_DEAD: continue
        x, y = to_xy(pos)
        if y != 0 and pos + UP not in me:
            ret.append((i, UP))
        if y !=  BOARD_WIDTH - 1 and pos + DOWN not in me:
            ret.append((i, DOWN))
        if x != 0 and pos + LEFT not in me:
           ret.append((i, LEFT))
        if x != BOARD_WIDTH - 1 and pos + RIGHT not in me:
           ret.append((i, RIGHT))

        if (x == 0 or x == BOARD_WIDTH - 1) and y == 0 and i < NUM_GEISTER / 2:
            return [(i, WIN)]  # 上がれる手があるときにはそれだけを候補とする

    return ret


def find_kiki(view):
    "相手が次に動きうるマス(つまりそこに動かすと取られうるところ)を返す"
    ret = []
    for i, pos in enumerate(view.alive):
        x, y = to_xy(pos)
        if y != 0:
            ret.append(pos + UP)
        if y !=  BOARD_WIDTH - 1:
            ret.append(pos + DOWN)
        if x != 0:
           ret.append(pos + LEFT)
        if x != BOARD_WIDTH - 1:
           ret.append(pos + RIGHT)

    return ret



class AI(object):
    def __repr__(self):
        return self.__class__.__name__

    def choice(self, board):
        "board -> (index, direction/WIN)"

class Random(AI):
    def choice(self, board):
        moves = find_possible_move(board)
        return choice(moves)


def is_blue(i):
    return i < NUM_GEISTER / 2

def is_red(i): return not is_blue(i)

class Fastest(AI):
    "自分のゴールインまでの手数を短くする"
    def choice(self, view):
        moves = find_possible_move(view)
        if moves[0][1] == WIN: return moves[0]
        scored_moves = defaultdict(list)
        def calc_dist(pos):
            x, y = to_xy(pos)
            return y + min(x, 3 - x)

        for move in moves:
            # 勝てるなら勝つ
            if move[1] == WIN: return move
            i, d = move
            if is_red(i):
                dist = 1000
                # 本当は正確には「自分の駒が道を塞いでいる」効果を求めるために
                # きちんと最短パスを計算するべきだが、このAIでは省略
            else:
                blue = view.get_blue()
                blue[i] += d
                dist = min(calc_dist(pos) for pos in blue)
                #print "dist", move, dist
            scored_moves[dist].append(move)
        #print scored_moves
        return choice(scored_moves[min(scored_moves)])

class FastestP(AI):
    "epsilon greedy"
    def __init__(self, p=0.1):
        self.p = p
    def choice(self, view):
        moves = find_possible_move(view)
        if random() < self.p:
            return choice(moves)
        return Fastest().choice(view)


class ColorlessFastest(AI):
    "自分のゴールインまでの手数を短くする/色無関係"
    def choice(self, view):
        moves = find_possible_move(view)
        if moves[0][1] == WIN: return moves[0]
        scored_moves = defaultdict(list)
        def calc_dist(pos):
            x, y = to_xy(pos)
            return y + min(x, 3 - x)

        for move in moves:
            # 勝てるなら勝つ
            if move[1] == WIN: return move
            i, d = move
            m = view.me[:]
            m[i] += d
            dist = min(calc_dist(pos) for pos in m)
            scored_moves[dist].append(move)
        #print scored_moves
        return choice(scored_moves[min(scored_moves)])


MAX_TURNS = 300
def match(p1_gen, p2_gen, show_detail=True, record=True):
    "match p1 and p2, return p1's WIN/LOSE/EVEN"
    g = Game()
    #print g
    p1 = p1_gen()
    p2 = p2_gen()
    for i in range(MAX_TURNS):
        v = g.to_view(0)
        if show_detail:
            print p1
            print_view(v)
        move = p1.choice(v)
        #print move
        g = do_move(g, 0, move)
        if g == WIN: return WIN
        if g == LOSE: return LOSE
        if show_detail:
            v = g.to_view(0)
            print_view(v)

        v = g.to_view(1)
        if show_detail:
            print p2
            print_view(v)
        move = p2.choice(v)
        #print move
        g = do_move(g, 1, move)
        if g == WIN: return LOSE
        if g == LOSE: return WIN
        if show_detail:
            v = g.to_view(1)
            print_view(v)

    return EVEN


def foo(p1, p2, show_detail=True):
    g = Game()
    v_prev = g.to_view(1)

    v = g.to_view(0)
    if show_detail:
        print p1
        print_view(v)
    move = p1.choice(v)

    g = do_move(g, 0, move)
    if g == WIN: return WIN
    if g == LOSE: return LOSE
    if show_detail:
        print move
        v = g.to_view(0)
        print_view(v)

    v = g.to_view(1)
    print_view(v_prev)

    stat = defaultdict(str)
    for i in range(1000):
        vg = make_virtual_game(v_prev, 1)

        v2 = vg.to_view(0)
        move2 = p1.choice(v2)
        vg = do_move(vg, 0, move2)

        alive1 = list(sorted(vg.to_view(1).alive))
        alive2 = list(sorted(v.alive))
        if alive1 == alive2:
            #print_view(vg.to_view(0))
            for x in blue:
                stat[x] += 'o'
            for x in red:
                stat[x] += 'x'

    for k in stat:
        print k, stat[k].count('o') / float(len(stat[k]))

    print_view(v)


@profile
def make_virtual_game(v, side):
    """
    given a view, return a game
    filling opponent's invisible ghost randomly
    """
    alive = copy(v.alive)
    shuffle(alive)
    split = 4 - v.dead_blue
    blue = alive[:split] + [IS_DEAD] * v.dead_blue
    red = alive[split:] + [IS_DEAD] * v.dead_red
    vg = Game.by_val(side, v.me, blue + red)
    return vg


class Montecarlo(AI):
    "モンテカルロ"
    @profile
    def choice(self, view):
        side = 0
        moves = find_possible_move(view)
        if moves[0][1] == WIN: return moves[0]
        score = defaultdict(int)

        for move in moves:
            # 勝てるなら勝つ
            if move[1] == WIN: return move
            for i in range(10):
                g = make_virtual_game(view, side)
                g = do_move(g, side, move)
                x = random_playout(g, 1 - side)
                if x == LOSE: score[move] += 1
                if x == WIN: score[move] -= 1

        best = list(sorted((score[move], move) for move in score))[-1]
        return best[1]


@profile
def random_playout(g, side):
    if g == WIN: return LOSE
    if g == LOSE: return WIN
    random = Random()
    for i in range(MAX_TURNS):
        v = g.to_view(side)
        move = random.choice(v)
        #print move
        g = do_move(g, side, move)
        if g == WIN: return WIN
        if g == LOSE: return LOSE

        v = g.to_view(1 - side)
        move = random.choice(v)
        #print move
        g = do_move(g, 1 - side, move)
        if g == WIN: return LOSE
        if g == LOSE: return WIN

    return EVEN


class Ichi(AI):
    "FastestじゃPOMCPに食わすにしてもあんまりなのでもう少しましなやつ"
    def choice(self, view):
        moves = find_possible_move(view)
        if moves[0][1] == WIN: return moves[0]
        kiki = find_kiki(view)
        scored_moves = defaultdict(list)
        def calc_dist(pos):
            x, y = to_xy(pos)
            return y + min(x, 3 - x)

        ops = view.alive
        for move in moves:
            # 勝てるなら勝つ
            if move[1] == WIN: return move
            i, d = move
            is_blue = (i < 4)
            score = 0
            pos = view.me[i]
            x, y = to_xy(pos)
            dest = pos + d

            # もし行先に敵コマがいて、かつそのコマに利きがない(ただ取り)
            if dest in ops and dest not in kiki:
                # もし今までに取った赤の方が多ければ
                if view.dead_red > view.dead_blue:
                    # 赤を取らせる戦略を警戒する
                    # ゴールに近いときだけ取る
                    ox, oy = to_xy(pos)
                    d = min(ox, 5 - ox) + (5 - oy)
                    score += {0: 100, 1: 60, 2: 30}.get(d, 0)
                else:
                    score += 100

            # もし現在の自分に利きがあり、移動先に利きがない
            if pos in kiki and dest not in kiki:
                score += 90

            # もし移動先に利きがなく、前進である
            if dest not in kiki and d == UP:
                score += 80

            # もし移動先に利きがなく、ゴールに近づく左右動きである
            if dest not in kiki and (d == LEFT and x < 3) :
                score += 70
            if dest not in kiki and (d == RIGHT and x >= 3) :
                score += 70

            if not(is_blue):
                score -= 2

            # 上記好ましい動きができない場合の、あえて言うならこう、という動き
            # もし行先に敵コマがいる(利きはあるので交換になる)
            #if dest in ops and dest in kiki:
            #    score += 30

            # 前進である
            if dest in kiki and d == UP:
                score += 20

            # ゴールに近づく左右動きである
            if dest in kiki and (d == LEFT and x < 3) :
                score += 10
            if dest in kiki and (d == RIGHT and x >= 3) :
                score += 10

            # 取られない動きである
            if dest not in ops:
                score += 2
            # 端を避ける
            dx, dy = to_xy(dest)
            if dx == 0 or dx == 5 or dy == 0:
                score += 1

            score += random() * 50
            scored_moves[score].append(move)

        return choice(scored_moves[max(scored_moves)])

#print Counter(match(Montecarlo, Random, False) for i in range(1))

def allmatch(N=100):
    """
    print "Fastest"
    print Counter(match(Ichi, Fastest, False) for i in range(N))
    print Counter(match(Fastest, Ichi, False) for i in range(N))
    print "Random"
    print Counter(match(Ichi, Random, False) for i in range(N))
    print Counter(match(Random, Ichi, False) for i in range(N))
    print "ColerlessFastest"
    print Counter(match(Ichi, ColorlessFastest, False) for i in range(N))
    print Counter(match(ColorlessFastest, Ichi, False) for i in range(N))
    """
    from original_pomcp import POMCP
    print "Fastest"
    print Counter(match(POMCP, Fastest, False) for i in range(N))
    print Counter(match(Fastest, POMCP, False) for i in range(N))
    print "Random"
    print Counter(match(POMCP, Random, False) for i in range(N))
    print Counter(match(Random, POMCP, False) for i in range(N))
    print "ColerlessFastest"
    print Counter(match(POMCP, ColorlessFastest, False) for i in range(N))
    print Counter(match(ColorlessFastest, POMCP, False) for i in range(N))
    print "Ichi"
    print Counter(match(POMCP, Ichi, False) for i in range(N))
    print Counter(match(Ichi, POMCP, False) for i in range(N))



if __name__ == "__main__":
    allmatch(10)
    if 0:
        while 1:
            v = match(Ichi, Random, True)
            if v == "LOSE": break
