def parse_func(string):
    python_spec = "def f(c_vars=None, input=None, output=None): {}".format(string)
    exec(python_spec)
    return f