# -*- coding: utf-8 -*-
from collections import Counter, defaultdict
from random import random, choice
from geister import Ichi, AI, match, find_possible_move, WIN, LOSE, EVEN, find_kiki, to_xy, UP, LEFT, RIGHT, DOWN
import hyperopt

class Nii(AI):
    "FastestじゃPOMCPに食わすにしてもあんまりなのでもう少しましなやつ"
    def __init__(self, params):
        self.params = params

    def choice(self, view):
        moves = find_possible_move(view)
        if moves[0][1] == WIN: return moves[0]
        p = self.params

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
                    score += {0: p[1],
                              1: p[2],
                              2: p[3]}.get(d, 0)
                else:
                    score += p[0]

            # もし現在の自分に利きがあり、移動先に利きがない
            if pos in kiki and dest not in kiki:
                score += p[4]

            # もし移動先に利きがなく、前進である
            if dest not in kiki and d == UP:
                score += p[5]
                if is_blue:
                    score += p[7]

            # もし移動先に利きがなく、ゴールに近づく左右動きである
            if dest not in kiki and (d == LEFT and x < 3) :
                score += p[6]
                if is_blue:
                    score += p[7]

            if dest not in kiki and (d == RIGHT and x >= 3) :
                score += p[6]
                if is_blue:
                    score += p[7]


            # 上記好ましい動きができない場合の、あえて言うならこう、という動き
            # もし行先に敵コマがいる(利きはあるので交換になる)
            if dest in ops and dest in kiki:
                score += p[8]

            # 前進である
            if dest in kiki and d == UP:
                score += p[9]
                if is_blue:
                    score += p[13]

            # ゴールに近づく左右動きである
            if dest in kiki and (d == LEFT and x < 3) :
                score += p[10]
                if is_blue:
                    score += p[13]
            if dest in kiki and (d == RIGHT and x >= 3) :
                score += p[10]
                if is_blue:
                    score += p[13]

            # 取られない動きである
            if dest not in ops:
                score += p[11]

            # 端を避ける
            dx, dy = to_xy(dest)
            if dx == 0 or dx == 5 or dy == 0:
                score += p[12]

            score += random() * 10
            scored_moves[score].append(move)

        return choice(scored_moves[max(scored_moves)])


current_best_score = 0
best_param = ( 90,  98, 96, 96, 27,15, 45, 22, 85, 98, 64, 98, 45, 55)
def calc_cost(params, N=100):
    global current_best_score
    #score = Counter(match(Ichi, lambda :Nii(params), False) for i in range(N)).get("WIN", 0)
    #score += Counter(match(lambda :Nii(params), Ichi, False) for i in range(N)).get("LOSE", 0)
    f = Ichi
    #f = lambda :Nii(best_param)
    g = lambda :Nii(params)
    score = Counter(
        match(g, f, False)
        for i in range(N)).get("WIN", 0)
    score += Counter(
        match(f, g, False)
        for i in range(N)).get("LOSE", 0)

    score = score * 0.5 / N
    if score > current_best_score:
        current_best_score = score
        print "*", params, score
    else:
        print " ", params, score
    return 1 - score

def find_best():
    from hyperopt import fmin, tpe, hp
    best = fmin(
        fn=calc_cost,
        space=[
            hp.quniform("blue_tadadori", 0, 100, 1),
            hp.quniform("red_tadadori_0", 0, 100, 1),
            hp.quniform("red_tadadori_1", 0, 100, 1),
            hp.quniform("red_tadadori_2", 0, 100, 1),
            hp.quniform("avoid_kiki", 0, 100, 1),

            hp.quniform("no_kiki_up", 0, 100, 1),
            hp.quniform("no_kiki_lr", 0, 100, 1),
            hp.quniform("no_kiki_blue_bonus", 0, 100, 1),
            hp.quniform("koukan", 0, 100, 1),
            hp.quniform("kiki_up", 0, 100, 1),

            hp.quniform("kiki_lr", 0, 100, 1),
            hp.quniform("no_kiki", 0, 100, 1),
            hp.quniform("avoid_edge", 0, 100, 1),
            hp.quniform("kiki_blue_bonus", 0, 100, 1),
        ],
        algo=tpe.suggest,
        max_evals=10000)
    print best

def allmatch(N=1000):
    from geister import Fastest, Random, ColorlessFastest
    f = lambda :Nii(best_param)
    print "Fastest"
    print Counter(match(f, Fastest, False) for i in range(N))
    print Counter(match(Fastest, f, False) for i in range(N))
    print "Random"
    print Counter(match(f, Random, False) for i in range(N))
    print Counter(match(Random, f, False) for i in range(N))
    print "ColerlessFastest"
    print Counter(match(f, ColorlessFastest, False) for i in range(N))
    print Counter(match(ColorlessFastest, f, False) for i in range(N))
    print "Ichi"
    print Counter(match(f, Ichi, False) for i in range(N))
    print Counter(match(Ichi, f, False) for i in range(N))

if __name__ == "__main__":
    #find_best()
    allmatch()
