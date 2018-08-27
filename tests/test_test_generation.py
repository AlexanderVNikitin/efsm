import parser
import efsm

import unittest


class TestGeneration(unittest.TestCase):
    def test_loading(self):
        parser.load_efsm("automata/example_simple.efsm")
        parser.load_efsm("automata/example_empty_edges.efsm")
        parser.load_efsm("automata/example_simple_multiedges.efsm")
        # doesn't throw an exception

    def test_testcase_generation(self):
        efsm_ = parser.load_efsm("automata/example_simple_multiedges.efsm")
        dfs = efsm.DFS()
        assert dfs.get_tests(efsm_) == [[{u'a': 1}]]




if __name__ == '__main__':
    unittest.main()


