LETTERS_SMALL = 'abcdefghijklmnopqrstuvwxyz'
LETTERS_LARGE = LETTERS_SMALL.upper()

def to_snake_case(name):
    result = name[0].lower()

    for it in range(1, len(name)):
        that = name[it]

        if that in LETTERS_LARGE:
            result += '_' + that.lower()
        else:
            result += that

    return result

def wrap(operator, callback, name='Wrapper'):
    def wrapped(self, other):
        return callback(other)

    Wrapper = type(name, (), {
        operator: wrapped,
    })

    return Wrapper()

def wrap_matmul(callback, *args, **kwargs):
    return wrap('__matmul__', callback, *args, **kwargs)

# A meaningful `name` simplifies debugging
def generate_function(body, name):
    source = f"def {name}{body}"
    exec(source)
    return locals()[name]

def generate_accept_for(node, name):
    return generate_function(f'(self, visitor, *args, **kwargs): return visitor.visit_{node}(self, *args, **kwargs)', name=name)

def generate_visit_for(node, delegate, name):
    return generate_function(f'(self, {node}, *args, **kwargs): return self.visit_{delegate}({node}, *args, **kwargs)', name=name)

def generate_visit_delegating_to(delegate, name):
    return generate_function(f'(self, it, *args, **kwargs): return self.visit_{delegate}(it, *args, **kwargs)', name=name)

def visitable(cls):
    snake_name = to_snake_case(cls.__name__)
    debug_name = f'{snake_name}__accept'
    setattr(cls, 'accept', generate_accept_for(snake_name, name=debug_name))
    return cls

def is_visitable(cls):
    return hasattr(cls, 'accept')

def visit(node):
    if not is_visitable(node):
        print(f'Warning > {node} doesn\'t have an \'accept\' method')

    snake_name = to_snake_case(node.__name__)
    first_base = to_snake_case(node.__bases__[0].__name__)
    debug_name = f'AbstractVisitor__visit_{snake_name}__{first_base}'
    visit = generate_visit_delegating_to(first_base, name=debug_name)

    def inner(cls):
        setattr(cls, f'visit_{snake_name}', visit)
        return cls

    return inner

def visit_all(nodes):
    def inner(cls):
        it = cls

        for node in nodes:
            it = visit(node)(it)

        return it

    return inner

def visit_all_visitables(dict):
    nodes = [it for it in dict.values() if is_visitable(it)]
    return visit_all(nodes)
