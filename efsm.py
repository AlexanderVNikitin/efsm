import json
import re
import logging
import copy


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartObject(object):
    def __init__(self, d):
        self.__dict__ = d

    def __eq__(self, obj):
        return self.__dict__ == obj.__dict__ 

    def __hash__(self):
        return hash(tuple(self.__dict__.items()))


class Edge(object):
    def __init__(self, begin, to, inp, output_function, enabling_function, update_function):
        self.begin = begin
        self.to = to
        self.inp = inp
        self.output_function = output_function
        self.enabling_function = enabling_function
        self.update_function = update_function
        self.context_vars = {}

    def can_move(self, inp):
        return self.enabling_function(inp, self.context_vars)

    def move(self, inp):
        self.context_vars = self.update_function(inp, self.context_vars)
        return self.output_function(inp, self.context_vars)


class EFSM(object):
    def __init__(self, init=None, edges=None, context_vars=None):
        self.init = init
        self.current = init
        self.context_vars = context_vars or {}
        self.edges = edges or {} # dict: (from, input) -> [Edge]

        # TODO: remove it
        self.context_vars = SmartObject({"a": 1, "b": 1, "x": 1, "y": 1})

    def can_move(self, edge):
        if not edge:
            return False
        return edge.enabling_function(self.context_vars, edge.inp)

    def move(self, inp):
        edges = self.edges.get((self.current, inp))
        edge = edges[0] if edges else None
        if not edge:
            logger.warn("No edge vertex: {} by input: {}".format(self.current, inp))
            return

        if not self.can_move(edge):
            logger.warn("Cannot move from vertex: {} by input: {}".format(self.current, inp))
            return
        edge.update_function(self.context_vars, edge.inp)
        self.current = edge.to

    def set_initial(self, init_v):
        self.init = init_v
        self.current = init_v

    def get_initial(self):
        return self.init

    def add_edge(self, edge):
        edge = Edge(
            begin=edge["from"],
            to=edge["to"],
            inp=SmartObject(json.loads(edge["input"])),
            output_function=edge["output"],
            enabling_function=edge["predicate"],
            update_function=edge["update"])
        if self.edges.get((edge.begin, edge.inp)):
            self.edges[(edge.begin, edge.inp)].append(edge)
        else:
            self.edges[(edge.begin, edge.inp)] = [edge]

    def get_possible_inputs(self, vertex):
        '''
        Returns List of SmartObject: all possible input dicts for vertex
        '''
        return [x[1] for x in filter(lambda x: x[0] == vertex, self.edges.keys())]


class DFS(object):
    '''
    Aim of this class is to extract tests from efsm
    '''
    def __init__(self):
        self.tests = []

    def _get_tests_impl(self, vertex, current_test, used, efsm):
        if vertex in used:
            return
        used.add(vertex)
        symbols = efsm.get_possible_inputs(vertex)

        for s in symbols:
            current_edges = efsm.edges.get((vertex, s))
            for current_edge in current_edges:
                if current_edge:
                    if current_edge.to not in used and efsm.can_move(current_edge):
                        current_test.append(s.__dict__)
                        self.tests.append(copy.copy(current_test))
                        efsm.move(s)
                        self._get_tests_impl(current_edge.to, current_test, used, efsm)

    def get_tests(self, efsm):
        self.tests = []
        self._get_tests_impl(efsm.get_initial(), [], set(), efsm)
        return self.tests
