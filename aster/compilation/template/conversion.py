import re

from aster.parsing_tree import *
from aster.resolution import NameReference

def build_matcher(context, part):
    forbids_indent = True

    if part.startswith(' '):
        forbids_indent = False
        part = part[1:]

    if part.startswith('#'):
        symbol_group_name = part[1:]
        return Matcher(context.symbols_mapping[symbol_group_name], forbids_indent)

    if part.startswith('$') or part.startswith('@'):
        return Matcher(NameReference(part), forbids_indent)

    if part in context.tokens_mapping:
        rule = context.tokens_mapping[part]
    else:
        rule = build_token_rule(part)
        context.tokens_mapping[part] = rule

    return Matcher(rule, forbids_indent)

def split_branch_pattern(branch_pattern):
    branch_pattern = branch_pattern.strip()
    branch_pattern = re.sub(r'\s+', '~ ', branch_pattern)
    branch_pattern = re.sub(r'(?!<\\)\|', '~|~', branch_pattern)
    branch_pattern = re.sub(r'~+', '~', branch_pattern)
    return branch_pattern.split('~')

def build_branch(context, branch_pattern, branch_action):
    parts = split_branch_pattern(branch_pattern)
    non_returnable_index = -1
    matchers = []

    for it in range(len(parts)):
        part = parts[it]

        if part == '|':
            non_returnable_index = it
        else:
            matchers.append(build_matcher(context, part))

    if non_returnable_index == -1:
        non_returnable_index = len(matchers)

    return Branch(branch_action, matchers, non_returnable_index)

def build_symbol_rule(symbol_group_name, symbol_checker):
    return SymbolRule(symbol_group_name, symbol_checker)

def build_sequence_rule(context, rule_template, name, returnable):
    symbol_group = rule_template['symbolGroup']
    return SequenceRule(name, NameReference(symbol_group), returnable)

def build_token_rule(token):
    return TokenRule(token, token)

def build_lexing_rule(context, rule_template, name, returnable):
    lexer = rule_template['lexer']
    return LexingRule(name, lexer, returnable)

def build_branching_rule(context, rule_template, name, returnable):
    unsorted_branches = BranchGroup()
    rule = BranchingRule(name, unsorted_branches, returnable)

    for it in range(len(rule_template)):
        branch_pattern = list(rule_template.keys())[it]
        branch_action = rule_template[branch_pattern]
        branch = build_branch(context, branch_pattern, branch_action)
        unsorted_branches.add_branch(branch)

    return rule

def build_rule(context, rule_template, name_parts):
    name = name_parts[0]
    returnable = any(it == 'returnable' for it in name_parts)

    if any(it == 'lexing' for it in name_parts):
        return build_lexing_rule(context, rule_template, name, returnable)

    if any(it == 'sequence' for it in name_parts):
        return build_sequence_rule(context, rule_template, name, returnable)

    return build_branching_rule(context, rule_template, name, returnable)

def build_grammar(context, grammar_template, types):
    grammar = Grammar(types)

    for symbol_group_name in grammar_template['symbolGroups']:
        symbol_checker = grammar_template['symbolGroups'][symbol_group_name]
        context.symbols_mapping[symbol_group_name] = build_symbol_rule(symbol_group_name, symbol_checker)

    previous = None

    for rule_name in grammar_template['rules']:
        rule_name_parts = rule_name.split('|')
        name = rule_name_parts[0]
        rule_template = grammar_template['rules'][rule_name]
        rule = build_rule(context, rule_template, rule_name_parts)
        grammar.add_rule(rule)
        context.rules_mapping[name] = rule
        context.upper_mapping[rule] = previous
        previous = rule

    top_level_rule_name = '@' + grammar_template['top_level_rule']
    top_level_matcher = Matcher(NameReference(top_level_rule_name), False)
    grammar.set_top_level_matcher(top_level_matcher)

    return grammar
