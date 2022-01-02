import inspect

from codegen import visitable, wrap_matmul

class Placeholder:
    pass

class Required(Placeholder):
    pass

required = Required()

class Parameter(Placeholder):
    def __init__(self, index):
        self.index = index

parameter = wrap_matmul(Parameter, name='ParameterBuilder')

def substitute_accessor(accessor, results):
    if isinstance(accessor, Parameter):
        return results[accessor.index]

    if isinstance(accessor, list):
        return list(map(lambda it: substitute_accessor(it, results), accessor))

    return accessor

def initialize_node(node, fields, results):
    instance = node()

    for it in fields:
        instance.__dict__[it] = substitute_accessor(fields[it], results)

    return instance

def create_initializer(node, fields):
    required = set()

    for (it, that) in inspect.getmembers(node):
        if isinstance(that, Required):
            required.add(it)

    for it in fields:
        if it in required:
            required.remove(it)

    if len(required) > 0:
        raise Exception(f'Node `{node.__name__}` contains unassigned attributes > {required}')

    return lambda results: initialize_node(node, fields, results)

def initializable(cls):
    setattr(cls, 'create', wrap_matmul(lambda fields: create_initializer(cls, fields)))
    return cls

def node(cls):
    return initializable(visitable(cls))
