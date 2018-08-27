[![Build Status](https://travis-ci.com/alexnikleo/efsm.svg?token=RGFuM5BTpp4pmsnXs3mL&branch=master)](https://travis-ci.com/alexnikleo/efsm)

A python library for extended finite state machines.

## efsm
This library contains methods for parsing and simulating the work of extended finite
state machines [1] represented in human readable format [2] described below.
Possible applications include the derivation of a number of slices, test suite
generation with guaranteed fault coverage, etc.

## Format specification
For better understanding of the format specification let's look at pseudocode:
```
states: v1, v2, ..., vn;
init: vi;
context_vars: {
  c_vars.x = 11;
  c_vars.y = 0;
};
transitions: [
{
  from: v1;
  to: v2;
  input: {"a": 1};
  predicate: {
    return input.a == 1 and c_vars.x = 2;
  };
  update:
    c_vars.x = c_vars.x + 10;
  output:
  	return c_vars.x;
},
...
];
```


Formally specification can be described with BNF:
```
possible_chars = 'A-Za-z0-9-_.~%+=*/^ ()|'
EXPR_DELIM = ;
LIST_DELIM = ,
state = possible_chars*
context_vars = c_var.(word)

predicate_expr = PYTHON_CODE;
update_expr = PYTHON_CODE;

transition_from = from: integer;
transition_to = to: integer;
transition_input = input: {};
transition_output = output: predicate_expr
transition_predicate = predicate: predicate_expr
transition_update = update: delimitedList(update_expr)
transition = {transition_from + transition_to +
                    transition_input + transition_output + 
                    transition_predicate + transition_update};

transition = "transitions: [" delimitedList(transition) "];"

states = "states:" + delimitedList(state, delim=LIST_DELIM) + EXPR_DELIM
init = "init: " + state + EXPR_DELIM

grammar = states + init + transition
```

## Usage
Download library with:
` git clone `

To manage virtual environments we use Pipenv (see https://github.com/pypa/pipenv for details). We also keep requirements.txt to workaround pipenv and [travis-ci issue](https://github.com/pypa/pipenv/issues/2120).
You can enter virtual environment with simple
` pipenv shell `
and start working with library.

You can describe a given finite state machine in the proposed format (watch `automata/` for examples). Then you can run parser that produces the EFSM object, which you can use in your applications.

```
efsm_automata = parser.load_efsm('path/to/your/efsm')
```

After that we can traverse transitions of produced automata using the DFS object or your own implementation:
```
dfs = efsm.DFS()
print dfs.get_tests()
```


## Tests
To run unit tests use:
```
pytest
```

## References
1. Confirming configurations in EFSM testing
A Petrenko, S Boroday, R Groz
IEEE Transactions on Software Engineering 30 (1), 29-42

2. Human readable Extended Finite State Machine
format. 
Alexander Nikitin
Proceedings of the 12th Spring Summer Young Researchers’ Colloquium on Software Engineering, Novgorod, Russia, 2018.
