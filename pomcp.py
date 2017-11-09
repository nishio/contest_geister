# -*- coding: utf-8 -*-

from time import time
from random import choice, random, shuffle
import numpy as np
from collections import Counter, defaultdict
import geister

from random import seed
seed(1234)
np.random.seed(1234)

try:
    profile
except:
    profile = lambda f:f

TIME_LIMIT = 9  # seconds
DEPTH_LIMIT = 100
tree = {}
gamma = 0.95

def pos_tuple_to_int(pos):
    x, y = pos
    if pos == (9, 9):
        return geister.IS_DEAD
    return y * 6 + x

class GeisterSimulator(object):
    def __init__(self, op_policy=geister.Random()):
        self.op_policy = op_policy

    def _game_to_state(self, game):
        me = tuple(game.me)
        op = tuple(game.op)
        return (me, op)

    def sample_from_initial_observation(self):
        v = self.initial_observation
        op_ghosts = v[8:]
        op = [geister.IS_DEAD] * 8
        blue = [0, 1, 2, 3]
        red = [4, 5, 6, 7]
        for i, x in enumerate(op_ghosts):
            if x.color == 'r':
                j = red.pop()
                op[j] = pos_tuple_to_int(x.pos)

            if x.color == 'b':
                j = blue.pop()
                op[j] = pos_tuple_to_int(x.pos)

        for i, x in enumerate(op_ghosts):
            if x.color == 'u':
                if random() * (len(blue) + len(red)) < len(blue):
                    j = blue.pop()
                else:
                    j = red.pop()
                op[j] = pos_tuple_to_int(x.pos)

        me_ghosts = v[:8]
        me = [geister.IS_DEAD] * 8
        blue = [0, 1, 2, 3]
        red = [4, 5, 6, 7]
        self.j_to_i = {}  # geister.pyが「青4つ赤4つ」のリストで管理していてclient.pyが「初期配置順」で管理しているギャップを埋めるマップ
        for i, x in enumerate(me_ghosts):
            if x.color == 'R' or x.color == 'r':
                j = red.pop()
            if x.color == 'B' or x.color == 'b':
                j = blue.pop()
            me[j] = pos_tuple_to_int(x.pos)
            self.j_to_i[j] = i
        #print "me, op:", me, op
        g = geister.Game.by_val(0, me, op)
        return self._game_to_state(g)

    def n_init(self, h, a):
        return 0

    def v_init(self, h, a):
        return 0.0

    def available_actions(self, s):
        g = geister.Game.by_val(0, *s)
        moves = geister.find_possible_move(g.to_view(0))
        if len(moves) == 1 and moves[0][1] == 'WIN':
            # 適切な方向への移動に置きかえる
            j = moves[0][0]
            if g.me[j] == 0:
                return [[j, -1]]
            else:
                return [[j, 1]]

        return moves

    @profile
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
        if isinstance(o, list):
            o = self._serialize_ghosts(o)
            #o = "".join(x.to_str() for x in o)
        return (h, tuple(a), o)

    def _serialize_o(self, o):
        return (tuple(sorted(o.alive)), o.dead_blue, o.dead_red)

    def _serialize_ghosts(self, o):
        op_ghosts = o[8:]
        dead_blue = 0
        dead_red = 0
        op_pos = []
        for i, x in enumerate(op_ghosts):
            if x.color == 'r':
                dead_red += 1
            if x.color == 'b':
                dead_blue += 1
            if x.color == 'u':
                op_pos.append(pos_tuple_to_int(x.pos))
        op_pos.sort()
        return (tuple(op_pos), dead_blue, dead_red)


class TreeNode(object):
    def __init__(self, h, s):
        self.belief = defaultdict(int)
        self.history = h
        self.actions  = np.array(sim.available_actions(s))
        self.action_num = np.array([
            sim.n_init(h, a) for a in self.actions
        ])
        self.action_value = np.array([
            sim.v_init(h, a) for a in self.actions
        ])
        self.num = self.action_num.sum()

    def show_actions(self):
        return "\n".join(
            "Action{}: value={:.3f}, num={}".format(a, v, n)
            for (a, v, n) in zip(
                    self.actions,
                    self.action_value,
                    self.action_num)
        )

    def feedback(self, action_index, reward):
        self.num += 1
        self.action_num[action_index] += 1
        n = self.action_num[action_index]
        v = self.action_value[action_index]
        self.action_value[action_index] += (reward - v) / n


def sample_from_belief(b):
    keys = b.keys()
    values = b.values()
    p = np.array(values, dtype=np.float)
    p /= p.sum()
    return keys[np.random.choice(len(keys), p=p)]


def search(h):
    print 'search', h
    start_time = time()

    while time() - start_time < TIME_LIMIT:
        if h == None or not tree[h].belief:
            s = sim.sample_from_initial_observation()
        else:
            s = sample_from_belief(tree[h].belief)
        #print "s:", s
        simulate(s, h, 0)
    if 1:
        print "current belief:"
        #file("belief", "a").write("{}\n\n".format(tree[h].belief))
        stat = defaultdict(int)
        total = 0
        for (me, op), count in tree[h].belief.items():
            for x in op[:4]:
                if x == 36: continue  # dead
                stat[x] += count
            total += count
        #for x in sorted(stat):
        #    print "{},{}: {:.2f}%".format(
        #        5 - x % 6, 5 - x / 6,
        #        stat[x] * 100.0 / total)
        buf = [["   __"] * 6 for i in range(6)]
        for x in stat:
            buf[5 - x / 6][5 - x % 6] = (
                "   %2d" % (stat[x] * 99.9 // total))
        print "\n\n".join(
            ("".join(line) for line in buf))
    action_index = np.argmax(tree[h].action_value)
    return tree[h].actions[action_index]


@profile
def choose_action_ucb1(t):
    if not t.num:
        return np.random.randint(len(t.actions))
    denom = t.action_num + 0.01
    ucb1 = np.sqrt(np.log(t.num) / denom)
    ucb1 += t.action_value
    return np.argmax(ucb1)


def choose_action_random(s):
    return choice(sim.available_actions(s))


@profile
def simulate(s, h, depth):
    if depth > DEPTH_LIMIT: return 0.0
    if h not in tree:
        tree[h] = TreeNode(h, s)
        return rollout(s, h, depth)
    t = tree[h]

    action_index = choose_action_ucb1(t)
    a = t.actions[action_index]
    (s2, o, r) = sim.step(s, a)
    if s2 != None:  # not finished
        r += gamma * simulate(s2, sim.make_new_history(h, a, o), depth + 1)
    t.belief[s] += 1
    t.feedback(action_index, r)
    return r


@profile
def rollout(s, h, depth):
    if depth > DEPTH_LIMIT: return 0.0
    a = choose_action_random(s)
    (s2, o, r) = sim.step(s, a)
    if s2 != None:  # not finished
        r += gamma * rollout(s2, sim.make_new_history(h, a, o), depth + 1)
    return r


def show(h):
    print h
    print Counter(tree[h].belief)
    print tree[h].show_actions()

class WrapGeisterAI(geister.AI):
    def __init__(self, ai):
        self.ai = ai

    def choice(self, view):
        op_ghosts = view[8:]
        dead_red = 0
        dead_blue = 0
        alive = []
        for i, x in enumerate(op_ghosts):
            if x.color == 'r':
                dead_red += 1
            if x.color == 'b':
                dead_blue += 1
            if x.color == 'u':
                alive.append(pos_tuple_to_int(x.pos))

        me_ghosts = view[:8]
        me = [geister.IS_DEAD] * 8
        blue = [0, 1, 2, 3]
        red = [4, 5, 6, 7]
        self.j_to_i = {}  # geister.pyが「青4つ赤4つ」のリストで管理していてclient.pyが「初期配置順」で管理しているギャップを埋めるマップ
        for i, x in enumerate(me_ghosts):
            if x.color == 'R' or x.color == 'r':
                j = red.pop()
            if x.color == 'B' or x.color == 'b':
                j = blue.pop()
            me[j] = pos_tuple_to_int(x.pos)
            self.j_to_i[j] = i

        v = geister.View(None, me, alive, dead_blue, dead_red)
        print v
        a = self.ai.choice(v)
        target = view[self.j_to_i[a[0]]]
        direction = a[1]
        if direction == 1:
            ret = (target, 'E')
        if direction == -1:
            ret = (target, 'W')
        if direction == -6:
            ret = (target, 'N')
        if direction == 6:
            ret = (target, 'S')

        print ret
        return ret

class POMCP(geister.AI):
    def __init__(self, mentalmodel=geister.Ichi()):
        global sim
        tree.clear()
        #sim = GeisterSimulator(geister.FastestP(0.1))
        sim = GeisterSimulator(mentalmodel)


        #self.inner_policy = WrapGeisterAI(geister.Ichi())

    def choice(self, view):
        if not tree:
            # first time
            sim.initial_observation = view
            print 'no tree'
            self.prev_history = None
            a = search(None)
        else:
            hao = sim.make_new_history(
                self.prev_history, self.prev_action, view)
            print 'hao', hao
            if tree.has_key(hao):
                print 'has key in', len(tree)
                if 1:
                    thao = tree[hao]
                    tree.clear()
                    tree['ROOT'] = thao
                    self.prev_history = 'ROOT'
                else:
                    self.prev_history = hao
                a = search(self.prev_history)
            else:
                print 'no key in', len(tree)  # particles are vanished
                sim.initial_observation = view
                tree.clear()
                self.prev_history = None
                a = search(None)
        self.prev_action = a

        target = view[sim.j_to_i[a[0]]]
        direction = a[1]
        if direction == 1:
            ret = (target, 'E')
        if direction == -1:
            ret = (target, 'W')
        if direction == -6:
            ret = (target, 'N')
        if direction == 6:
            ret = (target, 'S')
        print "ret:", ret
        return ret

