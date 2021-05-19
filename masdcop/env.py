# Author: bbrighttaer
# Project: masdcop
# Date: 5/13/2021
# Time: 4:34 AM
# File: env.py
from masdcop.agent import SingleVariableAgent
from masdcop.algo import PseudoTree, SyncBB

import numpy as np


class FourQueens:

    def __init__(self, num_agents):
        self._max_cost = 0
        self.domain = [(i, j) for i in range(0, 4) for j in range(0, 4)]
        self.agents = [SingleVariableAgent(i + 1, self.domain) for i in range(num_agents)]
        self.pseudo_tree = PseudoTree(self.agents)
        self.algo = SyncBB(self.check_constraints, self.pseudo_tree, self._max_cost)
        self.grid = np.zeros((4, 4))
        self.history = {}

    def check_constraints(self, *args) -> bool:
        # update grid and history
        cleared = []
        for var in args:
            if var[0] in self.history and self.history[var[0]] not in cleared:
                self.grid[self.history[var[0]]] = 0
                cleared.append(self.history[var[0]])
            self.grid[var[1]] += 1
            self.history[var[0]] = var[1]

        # check for violations
        if (not np.sum(np.sum(self.grid, 1) > 1) == 0) or \
                (not np.sum(np.sum(self.grid, 0) > 1) == 0) or \
                not _diags_check(self.grid) or not _diags_check(np.fliplr(self.grid)):
            return False
        return True

    def resolve(self, verbose=False):
        self.algo.initiate(self.pseudo_tree.next())
        while not self.algo.terminate:
            agent = self.pseudo_tree.getCurrentAgent()
            if agent:
                self.algo.receive(agent)
                self.algo.sendMessage(agent)
            else:
                break


def _diags_check(m) -> bool:
    """
    Checks for diagonals constraint violation.

    :return: bool
        True if all constraints are satisfied else False
    """
    for i in range(m.shape[0]):
        if np.trace(m, i) > 1 or np.trace(m, -1) > 1:
            return False
    return True
