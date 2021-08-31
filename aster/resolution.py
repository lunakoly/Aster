from aster.parsing_tree import *

class NameReference:
    def __init__(self, name):
        self.name = name

class ResolutionContext:
    def __init__(self):
        self.rules_mapping = {}
        self.symbols_mapping = {}
        self.upper_mapping = {}
        self.tokens_mapping = {}

class ParsingTreeResolver(ParsingTreeVisitor):
    def __init__(self, resolution_context):
        self.context = resolution_context
        self.current_rule = None

    def visit_parsing_node(self, parsing_node):
        raise Exception('ParsingTreeResolver > Not implemented > ' + str(parsing_node))

    def visit_matcher(self, matcher):
        if not isinstance(matcher.rule, NameReference):
            return

        if matcher.rule.name == '$self':
            matcher.rule = self.current_rule
        elif matcher.rule.name == '$upper':
            matcher.rule = self.context.upper_mapping[self.current_rule]
        else:
            matcher.rule = self.context.rules_mapping[matcher.rule.name[1:]]

    def visit_branch(self, branch):
        for matcher in branch.matchers:
            matcher.accept(self)

    def visit_branch_group(self, branch_group):
        for branch in branch_group.branches:
            branch.accept(self)

    def visit_symbol_rule(self, _):
        pass

    def visit_sequence_rule(self, rule):
        rule.symbol_checker = self.context.symbols_mapping[rule.symbol_checker.name].symbol_checker

    def visit_token_rule(self, _):
        pass

    def visit_lexing_rule(self, _):
        pass

    def visit_branching_rule(self, rule):
        self.current_rule = rule

        unsorted_branches = rule.normal_branches

        rule.normal_branches = BranchGroup()
        rule.recurrent_branches = BranchGroup()

        for branch in unsorted_branches.branches:
            branch.accept(self)

            if branch.matchers[0].rule == rule:
                branch.matchers.pop(0)
                rule.recurrent_branches.add_branch(branch)
            else:
                rule.normal_branches.add_branch(branch)

        self.current_rule = None

    def visit_grammar(self, grammar):
        for rule in grammar.rules:
            rule.accept(self)

        grammar.top_level_matcher.accept(self)
