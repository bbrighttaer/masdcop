# Author: bbrighttaer
# Project: masdcop
# Date: 5/13/2021
# Time: 4:34 AM
# File: algo.py

from collections import namedtuple

from masdcop.agent import NIL_DOMAIN, SingleVariableAgent, PseudoTree


class SyncBB:
    PathElement = namedtuple('PathElement', ['var_label', 'value', 'violations'])

    def __init__(self, check_constraints, pseudo_tree: PseudoTree):
        """

        :param check_constraints: callable
            A function from the environment that performs constraint checking. Should return true if all constraints
            are satisfied else false.
        """
        assert callable(check_constraints)
        self.checkConstraints = check_constraints
        self.pseudo_tree = pseudo_tree

    def initiate(self, agent: SingleVariableAgent):
        """
        Initializes the state of an agent.

        :param agent: ::class::BaseAgent
            The state of the agent
        :return:
        """
        # Get first value in domain
        self.get_next(agent)
        recipient = self.pseudo_tree.nextTo(agent)
        if recipient:
            agent.send(recipient.label, message={
                'agent_label': agent.label,
                'token': None,
                'path': list(agent.state.new_path),
                'upperBound': agent.state.upper_bound
            })

    def get_next(self, agent: SingleVariableAgent):
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
            return self.get_next(agent)

    def check(self, path, agent: SingleVariableAgent) -> bool:
        """
        Checks a path for constraint violations.

        :param path:
        :param agent:
        :return:
        """
        # if path is empty (first agent in the order)
        if not path:
            agent.state.new_path.add(self.PathElement(var_label=agent.variable.label,
                                                      value=agent.variable.d,
                                                      violations=0))
            return True
        else:
            # first element in path
            prev_el = path[0]

            # apply constraints. The constraint function returns true if all constraints are resolved
            if not self.checkConstraints(((prev_el.var_label, prev_el.value),
                                          (agent.variable.label, agent.variable.d))):
                agent.state.counter += 1
                ubound = agent.state.upper_bound
                if agent.state.counter >= ubound or (prev_el.violations + 1) >= ubound:
                    return False
                else:
                    agent.state.new_path.add(self.PathElement(var_label=prev_el.var_label,
                                                              value=prev_el.value,
                                                              violations=prev_el.violations + 1))
                    return self.check(path[1:], agent)
            else:
                agent.state.new_path.add(self.PathElement(var_label=prev_el.var_label,
                                                          value=prev_el.value,
                                                          violations=prev_el.violations))
                return self.check(path[1:], agent)

    def receive(self, agent: SingleVariableAgent):
        """
        Receives a message from the agent communication network.

        :param agent:
        :return:
        """
        agent.receive()
        payload = agent.payload
        sender = payload.sender
        message = payload.message
