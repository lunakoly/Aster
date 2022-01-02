import re

from aster.grammar import *
from aster.resolution import NameReference

def build_symbol_matcher(symbol_checker):
    return SymbolMatcher(symbol_checker)

def build_symbol_sequence_matcher(rule_template):
    symbol_group = rule_template['symbolGroup']
    return SymbolSequenceMatcher(NameReference(symbol_group))

def build_token_matcher(token):
    return TokenMatcher(token)

def build_lexing_matcher(rule_template):
    lexer = rule_template['lexer']
    return LexingMatcher(lexer)

def build_matcher_call(context, part):
    forbids_indent = True

    if part.startswith(' '):
        forbids_indent = False
        part = part[1:]

    if part.startswith('#'):
        symbol_group_name = part[1:]
        return MatcherCall(context.symbols_mapping[symbol_group_name], forbids_indent)

    if part.startswith('$') or part.startswith('@'):
        return MatcherCall(NameReference(part), forbids_indent)

    if part in context.tokens_mapping:
        matcher = context.tokens_mapping[part]
    else:
        matcher = build_token_matcher(part)
        context.tokens_mapping[part] = matcher

    return MatcherCall(matcher, forbids_indent)

def split_branch_pattern(branch_pattern):
    branch_pattern = branch_pattern.strip()
    branch_pattern = re.sub(r'\s+', '~ ', branch_pattern)
    branch_pattern = re.sub(r' \|', '|', branch_pattern)
    branch_pattern = re.sub(r'(?!<\\)\|', '~|~', branch_pattern)
    branch_pattern = re.sub(r'\\\|', '|', branch_pattern)
    branch_pattern = re.sub(r'~+', '~', branch_pattern)
    branch_pattern = re.sub(r'^~', '', branch_pattern)
    branch_pattern = re.sub(r'~$', '', branch_pattern)
    return branch_pattern.split('~')

def build_matcher_sequence(context, branch_pattern, branch_action):
    parts = split_branch_pattern(branch_pattern)
    non_returnable_index = -1
    matchers = []

    for it in range(len(parts)):
        part = parts[it]

        if part == '|':
            if non_returnable_index != -1:
                raise Exception('Error > Duplicate "non-returnable bar" found > ' + branch_pattern)
            non_returnable_index = it
        else:
            matchers.append(build_matcher_call(context, part))

    if non_returnable_index == -1:
        non_returnable_index = len(matchers)

    return MatcherSequence(branch_action, matchers, non_returnable_index)

def build_rule_matcher(context, rule_template):
    unsorted_branches = MatcherUnion()
    rule = RuleMatcher(unsorted_branches)

    for it in range(len(rule_template)):
        branch_pattern = list(rule_template.keys())[it]
        branch_action = rule_template[branch_pattern]
        branch = build_matcher_sequence(context, branch_pattern, branch_action)
        unsorted_branches.add_matcher(branch)

    return rule

def build_rule(context, rule_template, name_parts):
    if any(it == 'lexing' for it in name_parts):
        return build_lexing_matcher(rule_template)

    if any(it == 'sequence' for it in name_parts):
        return build_symbol_sequence_matcher(rule_template)

    return build_rule_matcher(context, rule_template)

def build_recursive_matcher(context, grammar_template):
    grammar = RecursiveMatcher()

    for symbol_group_name in grammar_template['symbolGroups']:
        symbol_checker = grammar_template['symbolGroups'][symbol_group_name]
        context.symbols_mapping[symbol_group_name] = build_symbol_matcher(symbol_checker)

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
    top_level_matcher = MatcherCall(NameReference(top_level_rule_name), False)
    grammar.set_top_level_matcher(top_level_matcher)

    return grammar
