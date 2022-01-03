import time

from sample_high_language import ast, grammar, printer

from utils import prettifier

import aster
import aster.synthetic

from aster.parsing import ParserGenerator
from aster.grammar import Visitor, SymbolMatcher, SymbolSequenceMatcher, TokenMatcher, ManualMatcher

import cProfile

from pstats import Stats

class DuplicatesCollector(Visitor):
    def __init__(self):
        self.matcher_calls_cache = {}
        self.symbol_matchers_cache = {}
        self.symbol_sequence_matchers_cache = {}
        self.token_matchers_cache = {}
        self.manual_matchers_cache = {}

    def problems(self):
        problems = []

        check_list = [
            (self.matcher_calls_cache, 'MatcherCalls'),
            (self.symbol_matchers_cache, 'SymbolMatchers'),
            (self.symbol_sequence_matchers_cache, 'SymbolSequenceMatchers'),
            (self.token_matchers_cache, 'TokenMatchers'),
            (self.manual_matchers_cache, 'MatcherCalls'),
        ]

        for it in check_list:
            for (key, objects) in it[0].items():
                if len(objects) > 1:
                    problems.append(f'Duplicate {it[1]} > {key} > {len(objects)} times')

        return problems

    def update_cache(self, cache, key, it):
        if key not in cache:
            cache[key] = [it]
        else:
            other = cache[key]
            is_new = True

            for that in other:
                if id(it) == id(that):
                    is_new = False

            if is_new:
                other.append(it)

    def visit_object(self, _):
        pass

    def visit_matcher_call(self, call):
        cache_key = (call.matcher.debug_name, call.forbids_indent)
        self.update_cache(self.matcher_calls_cache, cache_key, call)

        if isinstance(call.matcher, SymbolMatcher):
            key = call.matcher.debug_name
            self.update_cache(self.symbol_matchers_cache, key, call.matcher)

        elif isinstance(call.matcher, SymbolSequenceMatcher):
            key = call.matcher.debug_name
            self.update_cache(self.symbol_sequence_matchers_cache, key, call.matcher)

        elif isinstance(call.matcher, TokenMatcher):
            key = call.matcher.token
            self.update_cache(self.token_matchers_cache, key, call.matcher)

        elif isinstance(call.matcher, ManualMatcher):
            key = call.matcher.parse.__name__
            self.update_cache(self.manual_matchers_cache, key, call.matcher)

    def visit_matcher_sequence(self, sequence):
        for matcher in sequence.matchers:
            matcher.accept(self)

    def visit_matcher_union(self, union):
        for matcher in union.matchers:
            matcher.accept(self)

    def visit_rule_matcher(self, rule):
        for branch in rule.normal_branches.matchers:
            branch.accept(self)

        for branch in rule.recurrent_branches.matchers:
            branch.accept(self)

    def visit_recursive_matcher(self, matcher):
        for rule in matcher.rules:
            rule.accept(self)

def measure(code, count, warmup):
    # with cProfile.Profile() as pr:
    #     start = time.time()

    #     for _ in range(count):
    #         code()

    #     stop = time.time()

    for _ in range(warmup):
        code()

    start = time.time()

    for _ in range(count):
        code()

    stop = time.time()

    print(f'Average time for {count} runs: {(stop - start) / count} s')

    # with open('stats.txt', 'w') as stream:
    #     stats = Stats(pr, stream=stream)
    #     stats.strip_dirs()
    #     stats.sort_stats('time')
    #     stats.dump_stats('stats.profiling')
    #     stats.print_stats()

def to_marker(result, messages):
    if result.is_success and len(messages) == 0:
        return 'OK'
    return 'FAIL'

def test_parse(source_code):
    resolved_grammar = aster.prepare_grammar(grammar.grammar)
    duplicates_collector = DuplicatesCollector()
    resolved_grammar.accept(duplicates_collector)
    resolution_messages = duplicates_collector.problems()

    messages = []
    result = None
    parse = resolved_grammar.accept(ParserGenerator(messages))

    def parse_wrapper():
        nonlocal result
        nonlocal messages

        messages.clear()
        result = parse(0, source_code)

    measure(parse_wrapper, count=1000, warmup=10)

    marker = to_marker(result, messages + resolution_messages)
    print(f'[{marker}] Test Case:')
    print()

    if result.data is not None:
        # print('Tree:', end=' ')
        # prettifier.print_pretty(tree)
        # print()
        print('Printer:', end=' ')
        result.data.accept(printer.Printer())
        print()
        print()

    print('Resolution Messages:', end=' ')
    prettifier.print_pretty(resolution_messages)
    print()

    print('Parsing Messages:', end=' ')
    prettifier.print_pretty(messages)
    print()

if __name__ == '__main__':
    test_parse("""
        let a: Double = 10 * 2 + 3 * f(2, 4) - 4 * -1 + (1 - 2) - {
            a, b -> let c: String = "Hel\\lo\n\t\\"there\\"!"
        } * { let d = 2 } - {x,y->3}
    """)
    test_parse("""
        a + b * c--g(4, 5o)(2) [  deadbeefh]
    """)
