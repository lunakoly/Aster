from codegen import visit_all_visitables

from aster.synthetic import ast_node, required

@ast_node
class Node:
    pass

@ast_node
class Error(Node):
    token = required

@ast_node
class List(Node):
    values = required

@ast_node
class Number(Node):
   value = required
   base = 10

@ast_node
class Identifier(Node):
    name = required

@ast_node
class String(Node):
    value = required

@ast_node
class Closure(Node):
    arguments = required
    statements = required

@ast_node
class Call(Node):
    receiver = required
    arguments = required

@ast_node
class Subscript(Node):
    receiver = required
    arguments = required

@ast_node
class UnaryMinus(Node):
    target = required

@ast_node
class Binary(Node):
    lefter = required
    righter = required

    @classmethod
    def new_from(cls, lefter, righter):
        return cls.new // { 'lefter': lefter, 'righter': righter }

@ast_node
class Times(Binary):
    pass

@ast_node
class Divide(Binary):
    pass

@ast_node
class Plus(Binary):
    pass

@ast_node
class Minus(Binary):
    pass

@ast_node
class LetDeclaration(Node):
    name = required
    type = None
    value = None

@visit_all_visitables(globals())
class Visitor:
    pass
