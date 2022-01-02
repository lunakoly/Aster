from codegen import visitable, visit_all_visitables

@visitable
class Node:
    pass

@visitable
class SymbolMatcher(Node):
    def __init__(self, symbol_checker):
        self.symbol_checker = symbol_checker

@visitable
class SymbolSequenceMatcher(Node):
    def __init__(self, symbol_checker):
        self.symbol_checker = symbol_checker

@visitable
class TokenMatcher(Node):
    def __init__(self, token):
        self.token = token

@visitable
class LexingMatcher(Node):
    def __init__(self, lexer):
        self.lexer = lexer

@visitable
class MatcherCall(Node):
    def __init__(self, matcher, forbids_indent):
        self.matcher = matcher
        self.forbids_indent = forbids_indent

@visitable
class MatcherSequence(Node):
    def __init__(self, action, matchers, non_returnable_index):
        self.action = action
        self.matchers = matchers
        self.non_returnable_index = non_returnable_index

    def add_matcher(self, matcher, *args, **kwargs):
        self.matchers.append(matcher, *args, **kwargs)

@visitable
class MatcherUnion(Node):
    def __init__(self):
        self.matchers = []

    def add_matcher(self, it):
        self.matchers.append(it)

@visitable
class RuleMatcher(Node):
    def __init__(self, unsorted_branches):
        self.normal_branches = unsorted_branches
        self.recurrent_branches = unsorted_branches

@visitable
class RecursiveMatcher(Node):
    def __init__(self):
        self.rules = []
        self.top_level_matcher = None

    def add_rule(self, rule):
        self.rules.append(rule)

    def set_top_level_matcher(self, matcher):
        self.top_level_matcher = matcher

@visit_all_visitables(globals())
class Visitor:
    pass
