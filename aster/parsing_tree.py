class ParsingTreeVisitor:
    def visit_parsing_tree_node(self, parsing_tree_node, *args, **kwargs):
        pass

    def visit_matcher(self, matcher, *args, **kwargs):
        return self.visit_parsing_tree_node(matcher, *args, **kwargs)

    def visit_branch(self, branch, *args, **kwargs):
        return self.visit_parsing_tree_node(branch, *args, **kwargs)

    def visit_branch_group(self, branch_group, *args, **kwargs):
        return self.visit_parsing_tree_node(branch_group, *args, **kwargs)

    def visit_rule(self, rule, *args, **kwargs):
        return self.visit_parsing_tree_node(rule, *args, **kwargs)

    def visit_symbol_rule(self, symbol_matcher, *args, **kwargs):
        return self.visit_rule(symbol_matcher, *args, **kwargs)

    def visit_sequence_rule(self, sequence_rule, *args, **kwargs):
        return self.visit_parsing_tree_node(sequence_rule, *args, **kwargs)

    def visit_token_rule(self, token_matcher, *args, **kwargs):
        return self.visit_rule(token_matcher, *args, **kwargs)

    def visit_lexing_rule(self, rule, *args, **kwargs):
        return self.visit_parsing_tree_node(rule, *args, **kwargs)

    def visit_branching_rule(self, rule, *args, **kwargs):
        return self.visit_parsing_tree_node(rule, *args, **kwargs)

    def visit_grammar(self, grammar, *args, **kwargs):
        return self.visit_parsing_tree_node(grammar, *args, **kwargs)

class ParsingTreeNode:
    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_parsing_tree_node(self, *args, **kwargs)

class Matcher(ParsingTreeNode):
    def __init__(self, rule, forbids_indent):
        super().__init__()
        self.rule = rule
        self.forbids_indent = forbids_indent

    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_matcher(self, *args, **kwargs)

class Branch(ParsingTreeNode):
    def __init__(self, action, matchers, non_returnable_index):
        super().__init__()
        self.action = action
        self.matchers = matchers
        self.non_returnable_index = non_returnable_index

    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_branch(self, *args, **kwargs)

    def add_matcher(self, matcher, *args, **kwargs):
        self.matchers.append(matcher, *args, **kwargs)

class BranchGroup(ParsingTreeNode):
    def __init__(self):
        super().__init__()
        self.branches = []

    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_branch_group(self, *args, **kwargs)

    def add_branch(self, it):
        self.branches.append(it)

class Rule(ParsingTreeNode):
    def __init__(self, name, returnable):
        super().__init__()
        self.name = name
        self.returnable = returnable

    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_rule(self, *args, **kwargs)

class SymbolRule(Rule):
    def __init__(self, name, symbol_checker):
        super().__init__(name, returnable=True)
        self.symbol_checker = symbol_checker

    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_symbol_rule(self, *args, **kwargs)

class SequenceRule(Rule):
    def __init__(self, name, symbol_checker, returnable):
        super().__init__(name, returnable)
        self.symbol_checker = symbol_checker

    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_sequence_rule(self, *args, **kwargs)

class TokenRule(Rule):
    def __init__(self, name, token):
        super().__init__(name, returnable=True)
        self.token = token

    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_token_rule(self, *args, **kwargs)

class LexingRule(Rule):
    def __init__(self, name, lexer, returnable):
        super().__init__(name, returnable)
        self.lexer = lexer

    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_lexing_rule(self, *args, **kwargs)

class BranchingRule(Rule):
    def __init__(self, name, unsorted_branches, returnable):
        super().__init__(name, returnable)
        self.normal_branches = unsorted_branches
        self.recurrent_branches = unsorted_branches

    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_branching_rule(self, *args, **kwargs)

class Grammar(ParsingTreeNode):
    def __init__(self, types):
        super().__init__()
        self.rules = []
        self.top_level_matcher = None
        self.types = types

    def accept(self, visitor, *args, **kwargs):
        return visitor.visit_grammar(self, *args, **kwargs)

    def add_rule(self, rule):
        self.rules.append(rule)

    def set_top_level_matcher(self, matcher):
        self.top_level_matcher = matcher
