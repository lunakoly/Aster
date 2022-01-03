import re

from .resolution import NameReference
from .grammar import *

class ConversionContext:
    def __init__(self):
        self.rules = {}
        self.matcher_calls_cache = {}

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

class GrammarConverter(Visitor):
    def __init__(self, context):
        self.context = context
        self.literal_matchers_cache = {}

    def visit_object(self, it):
        return it

    def visit_matcher_sequence(self, sequence):
        for matcher in sequence.matchers:
            matcher.accept(self)

    def visit_matcher_union(self, union):
        for branch in union.matchers:
            branch.accept(self)

    def visit_template(self, it):
        raise Exception(f'GrammarConverter > Not implemented > {it}')

    def build_literal_matcher(self, token):
        if len(token) > 1:
            return TokenMatcher(token)

        def check_symbol(next):
            return next == token

        return SymbolMatcher(check_symbol)

    def build_matcher_call(self, part):
        forbids_indent = True

        if part.startswith(' '):
            forbids_indent = False
            part = part[1:]

        if part.startswith('@'):
            return MatcherCall(NameReference(part[1:]), forbids_indent)

        if part.startswith('$'):
            return MatcherCall(NameReference(part), forbids_indent)

        if part in self.literal_matchers_cache:
            matcher = self.literal_matchers_cache[part]
        else:
            matcher = self.build_literal_matcher(part)
            self.literal_matchers_cache[part] = matcher
            # Helps debugging
            matcher.debug_name = part

        # At this stage we can cache calls to
        # literal matchers to remove duplicates

        cache_key = (id(matcher), forbids_indent)

        if cache_key in self.context.matcher_calls_cache:
            return self.context.matcher_calls_cache[cache_key]

        call = MatcherCall(matcher, forbids_indent)
        self.context.matcher_calls_cache[cache_key] = call
        return call

    def build_matcher_sequence(self, branch_pattern, branch_handler):
        parts = split_branch_pattern(branch_pattern)
        non_returnable_index = -1
        matchers = []

        for it in range(len(parts)):
            part = parts[it]

            if part == '|':
                if non_returnable_index != -1:
                    raise Exception(f'Conversion Error > Duplicate "non-returnable bar" found > {branch_pattern}')
                non_returnable_index = it
            else:
                matchers.append(self.build_matcher_call(part))

        if non_returnable_index == -1:
            non_returnable_index = len(matchers)

        return MatcherSequence(branch_handler, matchers, non_returnable_index)

    def visit_rule_matcher_template(self, rule_template):
        unsorted_branches = MatcherUnion()
        rule = RuleMatcher(unsorted_branches)

        for (branch_pattern, branch_handler) in rule_template.template.items():
            branch = self.build_matcher_sequence(branch_pattern, branch_handler)
            unsorted_branches.add_matcher(branch)

        return rule

    def visit_recursive_matcher_template(self, matcher_template):
        matcher = RecursiveMatcher()

        for (name, rule) in matcher_template.rules.items():
            self.context.rules[name] = rule.accept(self)
            # Helps debugging
            self.context.rules[name].debug_name = name

        matcher.rules = list(self.context.rules.values())
        matcher.top_level_matcher = NameReference(matcher_template.top_level_matcher_name)

        return matcher
