# Author: bbrighttaer
# Project: masdcop
# Date: 5/13/2021
# Time: 4:34 AM
# File: algo.py

from collections import namedtuple

NIL_DOMAIN = "exhausted"


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
            self.d = NIL_DOMAIN
        # if another value can be sampled
        else:
            self.d = self._domain[self._i]
            self._i += 1
        return self.d

    def reset(self):
        self._i = 0


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

    def hasNext(self) -> bool:
        return self._i < len(self.agents)

    def next(self):
        if self._i < len(self.agents):
            self._i += 1
            return self.agents[self._i]
        else:
            return None

    def previous(self):
        if self._i > 0:
            self._i -= 1
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

    def getAgent(self, label):
        for agent in self.agents:
            if agent.label == label:
                return agent
        return None

    def isLast(self, agent):
        return self.agents[-1] == agent

    def getLast(self):
        return self.agents[-1]

    def getCurrentAgent(self):
        return self.agents[self._i]


class SyncBB:
    PathElement = namedtuple('PathElement', ['var_label', 'value', 'violations'])

    def __init__(self, check_constraints, pseudo_tree: PseudoTree, max_cost):
        """

        :param check_constraints: callable
            A function from the environment that performs constraint checking. Should return true if all constraints
            are satisfied else false.
        """
        assert callable(check_constraints)
        self.checkConstraints = check_constraints
        self.pseudo_tree = pseudo_tree
        self.max_cost = max_cost
        self.terminate = False
        self.sol = None

    def initiate(self, agent):
        """
        Initializes the state of an agent.

        :param agent: ::class::BaseAgent
            The state of the agent
        :return:
        """
        # Get first value in domain
        self.getNext(agent)
        self.sendMessage(agent)

    def sendMessage(self, agent):
        if agent.variable.d is not NIL_DOMAIN:
            if self.pseudo_tree.isLast(agent):
                cost = 0
                next_to_next = self.getNext(agent)
                while next_to_next is not NIL_DOMAIN:
                    best_path = agent.state.new_path
                    cost = max([p.violations for p in best_path])
                    if cost <= self.max_cost:
                        self.terminate = True
                        break
                    self.sol = (best_path, cost)
                    next_to_next = self.getNext(agent)
                agent.state.upper_bound = cost
                self.sendToPrevious(agent)
            else:
                self.sendToNext(agent)
        else:
            if self.pseudo_tree.agents.index(agent) == 0:  # first agent
                self.terminate = True
            else:
                self.sendToPrevious(agent)

    def sendToNext(self, agent):
        next_agent = self.pseudo_tree.next()
        if next_agent:
            agent.send(next_agent.label, message={
                # 'agent_label': agent.label,
                'token': None,
                'path': list(agent.state.new_path),
                'upperBound': agent.state.upper_bound
            })

    def sendToPrevious(self, agent):
        prev_agent = self.pseudo_tree.previous()
        if prev_agent:
            agent.send(prev_agent.label, message={
                # 'agent_label': agent.label,
                'token': None,
                'path': list(agent.state.previous_path),
                'upperBound': agent.state.upper_bound
            })

    def getNext(self, agent):
        """
        Gets the next domain value of an agent

        :param self:
        :param agent:
        :return:
        """
        d = agent.variable.next()
        if d == NIL_DOMAIN:
            return NIL_DOMAIN

        agent.state.new_path = list()
        agent.state.counter = 0

        if self.check(agent.state.previous_path, agent):
            return d
        else:
            return self.getNext(agent)

    def check(self, path, agent) -> bool:
        """
        Checks a path for constraint violations.

        :param path:
        :param agent:
        :return:
        """
        # if path is empty (first agent in the order)
        if not path:
            agent.state.new_path.append(self.PathElement(var_label=agent.variable.label,
                                                         value=agent.variable.d,
                                                         violations=0))
            return True
        else:
            # first element in path
            prev_el = path[0]

            # apply constraints. The constraint function returns true if all constraints are resolved
            if not self.checkConstraints((prev_el.var_label, prev_el.value),
                                         (agent.variable.label, agent.variable.d)):
                agent.state.counter += 1
                ubound = agent.state.upper_bound
                if agent.state.counter >= ubound or (prev_el.violations + 1) >= ubound:
                    return False
                else:
                    agent.state.new_path.append(self.PathElement(var_label=prev_el.var_label,
                                                                 value=prev_el.value,
                                                                 violations=prev_el.violations + 1))
                    return self.check(path[1:], agent)
            else:
                agent.state.new_path.append(self.PathElement(var_label=prev_el.var_label,
                                                             value=prev_el.value,
                                                             violations=prev_el.violations))
                return self.check(path[1:], agent)

    def receive(self, agent):
        """
        Receives a message from the agent communication network.

        :param agent:
        :return:
        """
        agent.receive()
        payload = agent.payload
        sender = payload.sender
        message = payload.message
        # if the received message is from the agent ahead or the agent before the given agent
        if self.pseudo_tree.isParent(agent, self.pseudo_tree.getAgent(sender)):
            tail_path_elmt = message['path'][-1]
            agent.state.upper_bound = message['upperBound']
            d = self.getNext(agent)
            if agent.state.new_path:
                agent.state.new_path.pop()
            agent.state.new_path.append(self.PathElement(var_label=agent.variable.label,
                                                         value=d,
                                                         violations=tail_path_elmt.violations))
            # self.sendMessage(agent)
        else:
            agent.state.previous_path = message['path']
            agent.state.upper_bound = message['upperBound']
            self.getNext(agent)
            # self.sendMessage(agent)
