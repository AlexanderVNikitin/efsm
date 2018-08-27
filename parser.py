from pyparsing import Word, alphas, alphanums
import pyparsing
import logging
import json

import efsm
import expression_parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


'''
TOKENS
'''

EDGES = "edges"
VERTEXES = "vertexes"
INIT = "init"
CONTEXT_VARS = "context_vars"

EDGE_FROM = "from"
EDGE_TO = "to"
EDGE_INPUT = "input"
EDGE_OUTPUT = "output"
EDGE_PREDICATE = "predicate"
EDGE_UPDATE = "update"

'''
TODO:
-- Word doesnt force order
'''

integer = Word(pyparsing.nums)

"""
possible_chars = 'A-Za-z0-9-_.~%+=><-*/^ ()|'
EXPR_DELIM = ;
LIST_DELIM = ,
state = possible_chars*
context_vars = c_var.(word)

predicate_expr = PYTHON_CODE;
update_expr = PYTHON_CODE;

transition_from = from: integer;
transition_to = to: integer;
transition_input = input: {};
transition_output = output: {};
transition_predicate = predicate: predicate_expr
transition_update = update: delimitedList(update_expr)
transition = {transition_from + transition_to + transition_input + transition_output + transition_predicate + transition_update};

transition = "transitions: [" delimitedList(transition) "];"

states = "states:" + delimitedList(state, delim=LIST_DELIM) + EXPR_DELIM
init = "init: " + state + EXPR_DELIM

grammar = states + init + transition
"""
possible_chars = alphanums + '-_.~%+=*/^()|: ",><'
EXPR_DELIM = ";"
OBJECT_START = "{"
OBJECT_END = "}"
LIST_START = "["
LIST_END = "]"
LIST_DELIM = ","
context_var = pyparsing.Combine("c_var." + Word(alphas))


predicate_expr = Word(possible_chars)
update_expr = Word(possible_chars)
output_expr = Word(possible_chars)


vertexes = Word(VERTEXES) + ":" + pyparsing.delimitedList(integer, delim=LIST_DELIM) + EXPR_DELIM
init = Word(INIT) + ":" + integer + EXPR_DELIM
context_vars = Word(CONTEXT_VARS) + ":" + OBJECT_START + pyparsing.ZeroOrMore(predicate_expr + EXPR_DELIM) + OBJECT_END + EXPR_DELIM


edge_from = Word(EDGE_FROM) + ":" + integer + EXPR_DELIM
edge_to = Word(EDGE_TO) + ":" + integer + EXPR_DELIM
edge_input = Word(EDGE_INPUT) + ":" + pyparsing.Optional(Word(possible_chars + "{}")) + EXPR_DELIM
edge_output = Word(EDGE_OUTPUT) + ":" + OBJECT_START + pyparsing.ZeroOrMore(output_expr + EXPR_DELIM) + OBJECT_END
edge_predicate = Word(EDGE_PREDICATE) + ":" + OBJECT_START + pyparsing.ZeroOrMore(predicate_expr + EXPR_DELIM) + OBJECT_END
edge_update = Word(EDGE_UPDATE) + ":" + OBJECT_START + pyparsing.ZeroOrMore(update_expr + EXPR_DELIM) + OBJECT_END
edge = OBJECT_START + edge_from + edge_to + edge_input + edge_output + edge_predicate + edge_update + OBJECT_END + pyparsing.Optional(EXPR_DELIM)
edges = Word(EDGES) + ":" + LIST_START + pyparsing.Optional(pyparsing.delimitedList(edge, delim=LIST_DELIM)) + LIST_END + EXPR_DELIM

EFSM_bnf = vertexes  + init + context_vars + edges


###################################
#
# Syntax Parsing
#
###################################
class EFSM_SyntaxParser(object):
    def __init__(self):
        self.efsm = efsm.EFSM()
        self._current_pos = -1
        self._tokens = None
        self._current_edge = {}

    def _current_token(self):
        return self._tokens[self._current_pos] if 0 <= self._current_pos < len(self._tokens) else None

    def _next_token(self, k=1):
        self._current_pos += k
        return self._tokens[self._current_pos]

    def is_parsing_finished(self):
        return self._current_pos + 1 >= len(self._tokens)

    def read_initial(self):
        token = self._current_token()
        while token != EXPR_DELIM:
            self.efsm.set_initial(token)
            token = self._next_token()

    def _read_list(self):
        token = self._current_token()
        result = []
        while token != EXPR_DELIM:
            if token != LIST_DELIM:
                result.append(token)
            token = self._next_token()
        return result

    def _read_single_value(self, name):
        token = self._current_token()

        if token != name:
            logger.error("Cannot read value of {} because next token is: {}".format(name, token))
        result = self._next_token(2)
        if result != EXPR_DELIM:
            self._next_token()
            return result
        else:
            return None

    def _read_edge_internal(self, name):
        result = self._read_single_value(name)
        self._current_edge[name] = result

    def _read_edge_internal_json(self, name):
        result = self._read_single_value(name)
        self._current_edge[name] = json.loads(result)

    def _read_object(self):
        token = self._current_token()
        if token != OBJECT_START:
            logger.error("Trying to read object which is not starting from OBJECT_START")
            return None
        result = ""
        while token != OBJECT_END:
            result += token + "\n"
            token = self._next_token()
        return result


    def _read_function(self, name):
        token = self._next_token(2) # name + :
        source_code = ""
        while token != OBJECT_END:
            if token != OBJECT_START and token != EXPR_DELIM:
                source_code += token + ";"
            token = self._next_token()
        self._current_edge[name] = expression_parser.parse_func(source_code)

    def read_edge(self):
        token = self._current_token()
        if token != OBJECT_START:
            logger.error("Trying to read edge when the next token is {}".format(token))
        while (token != OBJECT_END):
            token = self._next_token()
            if token == EDGE_FROM or token == EDGE_TO:
                self._read_edge_internal(token)
            elif token == EDGE_INPUT:
                self._read_edge_internal(token)
            elif token == EDGE_PREDICATE or token == EDGE_UPDATE or token == EDGE_OUTPUT:
                self._read_function(token)
            elif token == OBJECT_END:
                continue
            else:
                logger.info("TODO: {}".format(token))
                continue
        self.efsm.add_edge(self._current_edge)
        self._current_edge = {}

    def read_vertexes(self):
        token = self._current_token()
        vertexes = []
        while token != EXPR_DELIM:
            if token != LIST_DELIM:
                vertexes.append(token)
            token = self._next_token()

    def read_context_vars(self):
        self._read_object()

    def read_edges(self):
        token = self._current_token()
        if token != LIST_START:
            logger.error("Trying to read edges when the next token is {} but should be '['".format(token))
        token = self._next_token()
        while token == OBJECT_START:
            self.read_edge()
            token = self._next_token()
            if token == LIST_DELIM:
                token = self._next_token()

    def parse(self, tokens):
        self._tokens = tokens
        while not self.is_parsing_finished():
            token = self._next_token()
            if token == INIT:
                self._next_token(2)
                self.read_initial()
            elif token == CONTEXT_VARS:
                self._next_token(2)
                self.read_context_vars()
            elif token == VERTEXES:
                self._next_token(2)
                self.read_vertexes()
            elif token == EDGES:
                self._next_token(2) # edges + :
                self.read_edges()


def load_efsm(filepath):
    tokens = EFSM_bnf.parseString(open(filepath, "r").read())
    syntax_parser = EFSM_SyntaxParser()
    syntax_parser.parse(tokens)
    return syntax_parser.efsm


if __name__ == "__main__":
    import sys
    #load_efsm("automata/example_empty_edges.efsm")
    #load_efsm("automata/example_simple_multiedges.efsm")
    #load_efsm("automata/example_simple.efsm")
    efsm_automata = load_efsm(sys.argv[1])
    dfs = efsm.DFS()
    import ipdb; ipdb.set_trace()
    print dfs.get_tests(efsm_automata)
