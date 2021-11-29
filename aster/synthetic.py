from codegen import visitable, visit

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

        @visitable
        class Node:
            pass

        self.types.Node = Node

        @visit(Node)
        class Visitor:
            pass

        self.types.Visitor = Visitor

        self.provide_ast('List', {
            'values': ['$0'],
        })

    def create_ast(self, class_name):
        def constructor(self, nodes, fields):
            for it in fields:
                accessor = fields[it]
                self.__dict__[it] = substitute_accessor(accessor, nodes)

        raw_node = type(class_name, (self.types.Node,), {
            '__init__': constructor,
        })

        node = visitable(raw_node)

        setattr(self.types, class_name, node)
        self.types.Visitor = visit(node)(self.types.Visitor)

        return node

    def provide_ast(self, class_name, fields):
        if class_name in self.__dict__:
            ast = self.__dict__[class_name]
        else:
            ast = self.create_ast(class_name)

        key = get_initializer_key(class_name, fields)

        if key in self.ast_initializers:
            initializer = self.ast_initializers[key]
        else:
            initializer = create_initializer(ast, fields)
            self.ast_initializers[key] = initializer

        return initializer
