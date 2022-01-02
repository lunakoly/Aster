from codegen import visit_all_visitables

from aster.synthetic import required, node

@node
class Node:
    pass

@node
class Error(Node):
    token = required

@node
class List(Node):
    values = required

@node
class Number(Node):
   value = required
   base = 10

@node
class Identifier(Node):
    name = required

@node
class String(Node):
    value = required

@node
class Closure(Node):
    arguments = required
    statements = required

@node
class Call(Node):
    receiver = required
    arguments = required

@node
class Subscript(Node):
    receiver = required
    arguments = required

@node
class UnaryMinus(Node):
    target = required

@node
class Binary(Node):
    lefter = required
    righter = required

    @classmethod
    def create_from(cls, lefter, righter):
        return cls.create@{ 'lefter': lefter, 'righter': righter }

@node
class Times(Binary):
    pass

@node
class Divide(Binary):
    pass

@node
class Plus(Binary):
    pass

@node
class Minus(Binary):
    pass

@node
class LetDeclaration(Node):
    name = required
    type = None
    value = None

@visit_all_visitables(globals())
class Visitor:
    pass
