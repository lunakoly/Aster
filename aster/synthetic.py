import inspect

from codegen import visitable, wrap_floordiv, wrap_matmul

class Placeholder:
    pass

class Required(Placeholder):
    pass

required = Required()

def create_builder(callback, *args, **kwargs):
    return wrap_floordiv(callback, *args, **kwargs)

def create_accessor(callback, *args, **kwargs):
    return wrap_matmul(callback, *args, **kwargs)

def is_handler(it):
    return callable(it)

def substitute_handlers(value, results):
    if is_handler(value):
        return value(results)

    if isinstance(value, list):
        return list(map(lambda it: substitute_handlers(it, results), value))

    return value

def initialize(cls, fields, results):
    instance = cls()

    for it in fields:
        instance.__dict__[it] = substitute_handlers(fields[it], results)

    return instance

def create_initializer(cls, fields):
    required = set()

    for (it, that) in inspect.getmembers(cls):
        if isinstance(that, Required):
            required.add(it)

    for it in fields:
        if it in required:
            required.remove(it)

    if len(required) > 0:
        raise Exception(f'Some `{cls.__name__}` contains unassigned attributes > {required}')

    return lambda results: initialize(cls, fields, results)

def initializable(cls):
    setattr(cls, 'new', create_builder(lambda fields: create_initializer(cls, fields)))
    return cls

def ast_node(cls):
    return initializable(visitable(cls))
