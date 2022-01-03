from codegen import wrap_matmul

from .grammar import *

class NameReference:
    def __init__(self, name):
        self.name = name

class ResolutionContext:
    def __init__(self, conversion_context):
        self.conversion = conversion_context

class GrammarResolver(Visitor):
    def __init__(self, resolution_context):
        self.context = resolution_context
        self.current_rule = None
        self.upper_rule = None

    def visit_object(self, it):
        raise Exception(f'GrammarResolver > Not implemented > {it}')

    def visit_symbol_matcher(self, matcher):
        return matcher

    def visit_symbol_sequence_matcher(self, matcher):
        return matcher

    def visit_token_matcher(self, matcher):
        return matcher

    def visit_manual_matcher(self, matcher):
        return matcher

    def visit_matcher_call(self, call):
        if not isinstance(call.matcher, NameReference):
            return call

        if call.matcher.name == '$self':
            call.matcher = self.current_rule
        elif call.matcher.name == '$upper':
            call.matcher = self.upper_rule
        else:
            call.matcher = self.context.conversion.rules[call.matcher.name]

        # Check for possible duplicates
        # after the name resolution

        cache_key = (id(call.matcher), call.forbids_indent)

        if cache_key in self.context.conversion.matcher_calls_cache:
            return self.context.conversion.matcher_calls_cache[cache_key]

        self.context.conversion.matcher_calls_cache[cache_key] = call
        return call

    def visit_matcher_sequence(self, sequence):
        resolved = []

        for matcher in sequence.matchers:
            resolved.append(matcher.accept(self))

        sequence.matchers = resolved
        return sequence

    def visit_matcher_union(self, union):
        resolved = []

        for branch in union.matchers:
            resolved.append(branch.accept(self))

        union.matchers = resolved
        return union

    def visit_rule_matcher(self, rule):
        self.current_rule = rule

        unsorted_branches = rule.normal_branches

        rule.normal_branches = MatcherUnion()
        rule.recurrent_branches = MatcherUnion()

        for branch in unsorted_branches.matchers:
            resolved = branch.accept(self)

            if resolved.matchers[0].matcher == rule:
                resolved.matchers.pop(0)
                rule.recurrent_branches.add_matcher(resolved)
            else:
                rule.normal_branches.add_matcher(resolved)

        self.upper_rule = self.current_rule
        self.current_rule = None
        return rule

    def visit_recursive_matcher(self, matcher):
        resolved_rules = []

        for rule in matcher.rules:
            resolved_rules.append(rule.accept(self))

        matcher.rules = resolved_rules

        if matcher.top_level_matcher.name not in self.context.conversion.rules:
            raise Exception(f'Top level matcher not found > `{matcher.top_level_matcher.name}`')

        matcher.top_level_matcher = self.context.conversion.rules[matcher.top_level_matcher.name]
        return matcher
