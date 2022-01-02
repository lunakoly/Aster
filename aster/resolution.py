from aster.grammar import *

class NameReference:
    def __init__(self, name):
        self.name = name

class ResolutionContext:
    def __init__(self):
        self.rules_mapping = {}
        self.symbols_mapping = {}
        self.upper_mapping = {}
        self.tokens_mapping = {}

class ParsingTreeResolver(Visitor):
    def __init__(self, resolution_context):
        self.context = resolution_context
        self.current_rule = None

    def visit_object(self, it):
        raise Exception('ParsingTreeResolver > Not implemented > ' + str(it))

    def visit_symbol_matcher(self, _):
        pass

    def visit_symbol_sequence_matcher(self, matcher):
        matcher.symbol_checker = self.context.symbols_mapping[matcher.symbol_checker.name].symbol_checker

    def visit_token_matcher(self, _):
        pass

    def visit_lexing_matcher(self, _):
        pass

    def visit_matcher_call(self, call):
        if not isinstance(call.matcher, NameReference):
            return

        if call.matcher.name == '$self':
            call.matcher = self.current_rule
        elif call.matcher.name == '$upper':
            call.matcher = self.context.upper_mapping[self.current_rule]
        else:
            call.matcher = self.context.rules_mapping[call.matcher.name[1:]]

    def visit_matcher_sequence(self, sequence):
        for matcher in sequence.matchers:
            matcher.accept(self)

    def visit_matcher_union(self, union):
        for branch in union.matchers:
            branch.accept(self)

    def visit_rule_matcher(self, rule):
        self.current_rule = rule

        unsorted_branches = rule.normal_branches

        rule.normal_branches = MatcherUnion()
        rule.recurrent_branches = MatcherUnion()

        for branch in unsorted_branches.matchers:
            branch.accept(self)

            if branch.matchers[0].matcher == rule:
                branch.matchers.pop(0)
                rule.recurrent_branches.add_matcher(branch)
            else:
                rule.normal_branches.add_matcher(branch)

        self.current_rule = None

    def visit_recursive_matcher(self, matcher):
        for rule in matcher.rules:
            rule.accept(self)

        matcher.top_level_matcher.accept(self)
