# Author: bbrighttaer
# Project: masdcop
# Date: 5/13/2021
# Time: 4:34 AM
# File: agent.py

import math
from collections import namedtuple

from masdcop.algo import Variable


class PigeonHole:
    """A pigeonhole communication system for agents"""

    # models the holes for storing info for agents
    _holes = {}

    Payload = namedtuple('Payload', ['sender', 'message'])

    @staticmethod
    def send(sender, recipient, message: dict):
        PigeonHole._holes[recipient] = PigeonHole.Payload(sender=sender, message=message)

    @staticmethod
    def receive(key) -> Payload:
        return PigeonHole._holes[key]


class State:
    """Maintains all state information of an agent"""

    def __init__(self):
        self.upper_bound = math.inf
        self.counter = 0
        self.new_path = None
        self.previous_path = None


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
