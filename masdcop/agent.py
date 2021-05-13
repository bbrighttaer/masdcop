# Author: bbrighttaer
# Project: masdcop
# Date: 5/13/2021
# Time: 4:34 AM
# File: agent.py

import math
from collections import namedtuple

NIL_DOMAIN = "exhausted"


class PigeonHole:
    """A pigeonhole communication system for agents"""

    # models the holes for storing info for agents
    _divs = {}

    Payload = namedtuple('Payload', ['sender', 'message'])

    @staticmethod
    def send(cls, sender, recipient, message: dict):
        cls._divs[recipient] = cls.Payload(sender=sender, message=message)

    @staticmethod
    def receive(cls, key) -> Payload:
        return cls.Payload[key]


class State:
    """Maintains all state information of an agent"""

    def __init__(self):
        self.upper_bound = math.inf
        self.counter = 0
        self.new_path = None
        self.previous_path = None


class Variable:
    """Models a DCOP variable"""

    def __init__(self, label, domain: list):
        """
        Creates a DCOP variable
        :param domain: The domain values of variable
        """
        self.label = label
        self._domain = domain
        self._i = 0
        self.d = None

    @property
    def domain(self) -> list:
        return list(self._domain)

    @domain.setter
    def domain(self, d: list):
        self._domain = list(d)

    def next(self):
        # domain exhausted case
        if self._i == len(self.domain):
            return NIL_DOMAIN
        # if another value can be sampled
        else:
            d = self._domain[self._i]
            self.d = d
            self._i += 1
            return d

    def reset(self):
        self._i = 0


class BaseAgent:
    """
    Base class for modeling an agent.
    """

    def __init__(self, label):
        self.state = State()
        self.label = label


class SingleVariableAgent(BaseAgent):
    """Models a DCOP agent with only one variable"""

    def __init__(self, label, domain: list):
        super().__init__(label)
        self.variable = Variable(label, domain)
        self._network = PigeonHole()
        self.payload = None

    def send(self, recipient, message):
        self._network.send(self.label, recipient, message)

    def receive(self):
        self.payload = self._network.receive(self.label)


class PseudoTree:

    def __init__(self, agents: list):
        self.agents = agents
        self._i = -1

    def nextTo(self, agent):
        index = self.agents.index(agent) + 1
        if index < len(self.agents):
            return self.agents[index]
        else:
            return None

    def next(self):
        if self._i < len(self.agents):
            self._i += 1
            return self.agents[self._i]
        else:
            return None

    def isParent(self, p_agent, c_agent) -> bool:
        """
        Checks if the p_agent comes before c_agent in the order or tree (parent or not to c_agent).

        :param p_agent: Agent whose status is being queried.
        :param c_agent: The agent to be used for the check
        :return: bool
            True if p_agent is parent/comes before c_agent in the pseudo tree
        """
        return self.agents.index(p_agent) < self.agents.index(c_agent)