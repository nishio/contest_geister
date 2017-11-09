# -*- encoding: utf-8 -*-
"""
サーバと接続せずにローカルで対戦実験するためのコード
"""
from time import time
from random import choice, random, shuffle
import numpy as np
from collections import Counter, defaultdict
import geister
from pomcp import simulate, tree

TIME_LIMIT = 1  # seconds
DEPTH_LIMIT = 100
gamma = 0.95

def search(h):
    #print 'search', h
    start_time = time()

    while time() - start_time < TIME_LIMIT:
        if h == None or not tree[h].belief:
            s = sim.sample_from_initial_observation()
        else:
            s = sample_from_belief(tree[h].belief)
        #print "s:", s
        simulate(s, h, 0)
    action_index = np.argmax(tree[h].action_value)
    return tree[h].actions[action_index]


class GeisterSimulator(object):
    def __init__(self, op_policy=geister.Random()):
        self.op_policy = op_policy

    def _game_to_state(self, game):
        me = tuple(game.me)
        op = tuple(game.op)
        return (me, op)

    def sample_from_initial_observation(self):
        v = self.initial_observation
        op = [geister.IS_DEAD] * 8
        index = [0, 1, 2, 3][:4 - v.dead_blue] + [4, 5, 6, 7][:4 - v.dead_red]
        shuffle(index)
        for i, p in zip(index, v.alive):
            op[i] = p
        g = geister.Game.by_val(0, v.me, op)
        return self._game_to_state(g)

    def n_init(self, h, a):
        return 0

    def v_init(self, h, a):
        return 0.0

    def available_actions(self, s):
        g = geister.Game.by_val(0, *s)
        moves = geister.find_possible_move(g.to_view(0))
        return moves

    def step(self, s, a):
        g = geister.Game.by_val(0, *s)
        g = geister.do_move(g, 0, a)
        if g == geister.WIN:
            return (None, None, +0.5)
        elif g == geister.LOSE:
            return (None, None, -0.5)

        op_action = self.op_policy.choice(g.to_view(1))
        g = geister.do_move(g, 1, op_action)
        if g == geister.WIN:
            return (None, None, -0.5)
        elif g == geister.LOSE:
            return (None, None, +0.5)
        s2 = self._game_to_state(g)
        o = g.to_view(0)
        o = self._serialize_o(o)
        return (s2, o, 0.0)

    def make_new_history(self, h, a, o):
        if isinstance(o, geister.View):
            o = self._serialize_o(o)
        return (h, tuple(a), o)

    def _serialize_o(self, o):
        return (tuple(o.me), tuple(sorted(o.alive)), o.dead_blue, o.dead_red)

#__builtins__["sim"] = GeisterSimulator(geister.FastestP(0.1))
__builtins__["sim"] = GeisterSimulator(geister.Ichi())

class POMCP(geister.AI):
    def __init__(self):
        tree.clear()
    def choice(self, view):
        if not tree:
            # first time
            sim.initial_observation = view
            #print 'no tree'
            self.prev_history = None
            a = search(None)
        else:
            hao = sim.make_new_history(
                self.prev_history, self.prev_action, view)
            #print 'hao', hao
            if tree.has_key(hao):
                #print 'has key'
                if 1:
                    thao = tree[hao]
                    tree.clear()
                    tree['ROOT'] = thao
                    self.prev_history = 'ROOT'
                else:
                    self.prev_history = hao
                a = search(self.prev_history)
            else:
                #print 'no key'
                sim.initial_observation = view
                tree.clear()
                self.prev_history = None
                a = search(None)
        self.prev_action = a
        return a
