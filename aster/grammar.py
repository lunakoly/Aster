from codegen import visitable, visit_all_visitables

@visitable
class Node:
    pass

@visitable
class Matcher(Node):
    def __init__(self, rule, forbids_indent):
        super().__init__()
        self.rule = rule
        self.forbids_indent = forbids_indent

@visitable
class Branch(Node):
    def __init__(self, action, matchers, non_returnable_index):
        super().__init__()
        self.action = action
        self.matchers = matchers
        self.non_returnable_index = non_returnable_index

    def add_matcher(self, matcher, *args, **kwargs):
        self.matchers.append(matcher, *args, **kwargs)

@visitable
class BranchGroup(Node):
    def __init__(self):
        super().__init__()
        self.branches = []

    def add_branch(self, it):
        self.branches.append(it)

@visitable
class Rule(Node):
    def __init__(self, name):
        super().__init__()
        self.name = name

@visitable
class SymbolRule(Rule):
    def __init__(self, name, symbol_checker):
        super().__init__(name)
        self.symbol_checker = symbol_checker

@visitable
class SequenceRule(Rule):
    def __init__(self, name, symbol_checker):
        super().__init__(name)
        self.symbol_checker = symbol_checker

@visitable
class TokenRule(Rule):
    def __init__(self, name, token):
        super().__init__(name)
        self.token = token

@visitable
class LexingRule(Rule):
    def __init__(self, name, lexer):
        super().__init__(name)
        self.lexer = lexer

@visitable
class BranchingRule(Rule):
    def __init__(self, name, unsorted_branches):
        super().__init__(name)
        self.normal_branches = unsorted_branches
        self.recurrent_branches = unsorted_branches

@visitable
class Grammar(Node):
    def __init__(self):
        super().__init__()
        self.rules = []
        self.top_level_matcher = None

    def add_rule(self, rule):
        self.rules.append(rule)

    def set_top_level_matcher(self, matcher):
        self.top_level_matcher = matcher

@visit_all_visitables(globals())
class Visitor:
    pass
