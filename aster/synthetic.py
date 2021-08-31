###### Generating Synthetic Things ########

LETTERS_SMALL = 'abcdefghijklmnopqrstuvwxyz'
LETTERS_LARGE = LETTERS_SMALL.upper()

def to_snake_case(class_name):
    result = class_name[0].lower()

    for it in range(1, len(class_name)):
        that = class_name[it]

        if that in LETTERS_LARGE:
            result += '_' + that.lower()
        else:
            result += that

    return result

def substitute_accessor(accessor, nodes):
    if isinstance(accessor, str):
        if accessor.startswith('$'):
            index = int(accessor[1:])
            return nodes[index]

    if isinstance(accessor, list):
        substituted = []

        for it in accessor:
            substituted.append(substitute_accessor(it, nodes))

        return substituted

    return accessor

def create_initializer(ast, fields):
    def initialize(nodes):
        return ast(nodes, fields)
    return initialize

def get_initializer_key(class_name, fields):
    return f'{class_name}:{id(fields)}'

class TypeContainer:
    pass

class TypeBuilder:
    def __init__(self):
        self.ast_initializers = {}
        self.types = TypeContainer()

        class Visitor:
            def visit_node(self, node, *args, **kwargs):
                pass

        self.types.Visitor = Visitor

        class Node:
            def accept(self, visitor, *args, **kwargs):
                return visitor.visit_node(self, *args, **kwargs)

        self.types.Node = Node

        self.provide_ast('List', {
            'values': ['$0'],
        })

    def create_ast(self, class_name):
        def constructor(self, nodes, fields):
            for it in fields:
                accessor = fields[it]
                self.__dict__[it] = substitute_accessor(accessor, nodes)

        snake_name = to_snake_case(class_name)
        accept_source = f"def accept(self, visitor, *args, **kwargs):\n\treturn visitor.visit_{snake_name}(self, *args, **kwargs)"
        exec(accept_source)

        visit_source = f"def visit_{snake_name}(self, {snake_name}, *args, **kwargs):\n\treturn self.visit_node({snake_name}, *args, **kwargs)"
        exec(visit_source)

        setattr(self.types.Visitor, f'visit_{snake_name}', locals()[f'visit_{snake_name}'])

        return type(class_name, (self.types.Node,), {
            '__init__': constructor,
            'accept': locals()['accept']
        })

    def provide_ast(self, class_name, fields):
        if class_name in self.__dict__:
            ast = self.__dict__[class_name]
        else:
            ast = self.create_ast(class_name)
            setattr(self.types, class_name, ast)

        key = get_initializer_key(class_name, fields)

        if key in self.ast_initializers:
            initializer = self.ast_initializers[key]
        else:
            initializer = create_initializer(ast, fields)
            self.ast_initializers[key] = initializer

        return initializer
