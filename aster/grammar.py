from codegen import visitable, visit_all_visitables

from .synthetic import create_builder

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
    def __init__(self, handler, matchers, non_returnable_index):
        self.handler = handler
        self.matchers = matchers
        self.non_returnable_index = non_returnable_index

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

@visitable
class Template(Node):
    pass

@visitable
class RuleMatcherTemplate(Template):
    def __init__(self, template):
        self.template = template

rule_template = create_builder(RuleMatcherTemplate)

@visitable
class RecursiveMatcherTemplate(Template):
    def __init__(self):
        self.rules = {}
        self.top_level_matcher_name = 'main'

    def __iadd__(self, rules):
        for it in rules:
            self.rules[it] = rules[it]

        return self

    def symbol(self, symbol_checker):
        name = symbol_checker.__name__

        symbol_matcher = SymbolMatcher(symbol_checker)
        self.rules[name] = symbol_matcher

        symbol_sequence_matcher = SymbolSequenceMatcher(symbol_checker)
        self.rules[name + '_sequence'] = symbol_sequence_matcher

        return symbol_checker

    def lexing(self, lexer):
        name = lexer.__name__

        matcher = LexingMatcher(lexer)
        self.rules[name] = matcher

        return lexer

@visit_all_visitables(globals())
class Visitor:
    pass
