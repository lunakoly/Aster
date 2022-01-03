from re import S
from .grammar import *

class ParsingResult:
    def __init__(self, index, data, is_success=True):
        self.is_success = is_success
        self.index = index
        self.data = data

    @staticmethod
    def back_to(index):
        return ParsingResult(index, None, is_success=False)

    @staticmethod
    def escape(text):
        return ParsingResult(len(text), None, is_success=False)

class ResultsView:
    def __init__(self, results, base):
        self.results = results
        self.base = base

    def get_arguments(self):
        return self.results[self.base:]

    def __getitem__(self, index):
        return self.results[index + self.base]

    def __len__(self):
        return len(self.results) - self.base

    class Iterator:
        def __init__(self, results_view):
            self.results_view = results_view
            self.index = results_view.base

        def __next__(self):
            if self.index >= len(self.results_view.results):
                raise StopIteration()

            result = self.results_view.results[self.index]
            self.index += 1
            return result

    def __iter__(self):
        return ResultsView.Iterator(self)

def skip_indent(position, text):
    while position < len(text) and text[position] in ' \t\n':
        position += 1
    return position

class Parser(Visitor):
    def __init__(self, errors_collector):
        self.errors = errors_collector

        self.cache = Cache(self)
        self.simple = SimpleParser(self)
        self.recursive = RecursiveParser(self)

        # Switching the `cache.backend` each time
        # is simply a way to use the same `Cache`
        # instance with multiple other Parsers

    def report(self, error):
        self.errors.append(error.replace('\n', '\\n').replace('\t', '\\t'))

    def visit_object(self, it):
        self.cache.backend = self.simple
        return it.accept(self.cache)

    def visit_matcher_call(self, call):
        self.cache.backend = self.recursive
        return call.accept(self.cache)

    def visit_matcher_sequence(self, sequence):
        self.cache.backend = self.recursive
        return sequence.accept(self.cache)

    def visit_rule_matcher(self, rule):
        self.cache.backend = self.recursive
        return rule.accept(self.cache)

    def visit_recursive_matcher(self, matcher):
        self.cache.backend = self.recursive
        return matcher.accept(self.cache)

class ParserComponent(Visitor):
    def __init__(self, owner):
        self.owner = owner

    def report(self, error):
        return self.owner.report(error)

class Cache(ParserComponent):
    def __init__(self, owner):
        super().__init__(owner)

        self.results_cache = {}

        self.parsers_cache = {}
        self.backend = None

    def with_results_cache(self, parser):
        def parse(position, text):
            cacke_key = (id(parser), position)

            if cacke_key not in self.results_cache:
                result = parser(position, text)
                self.results_cache[cacke_key] = result
            else:
                result = self.results_cache[cacke_key]

            return result

        return parse

    def visit_object(self, it, *args, **kwargs):
        if id(it) in self.parsers_cache:
            return self.parsers_cache[id(it)]

        parser = self.with_results_cache(it.accept(self.backend, *args, **kwargs))
        self.parsers_cache[id(it)] = parser
        return parser

class SimpleParser(ParserComponent):
    def __init__(self, owner):
        super().__init__(owner)

    def visit_object(self, it):
        raise Exception(f'SimpleParser > Not implemented > {it}')

    def visit_symbol_matcher(self, matcher):
        def parse(position, text):
            if position >= len(text):
                return ParsingResult.back_to(position)

            next_symbol = text[position]

            if matcher.symbol_checker(next_symbol):
                return ParsingResult(position + 1, next_symbol)

            return ParsingResult.back_to(position)

        return parse

    def visit_symbol_sequence_matcher(self, matcher):
        def parse(position, text):
            if position >= len(text):
                return ParsingResult.back_to(position)

            index = position

            if not matcher.symbol_checker(text[index]):
                return ParsingResult.back_to(position)

            token = text[index]
            index += 1

            while index < len(text) and matcher.symbol_checker(text[index]):
                token += text[index]
                index += 1

            return ParsingResult(index, token)

        return parse

    def visit_token_matcher(self, matcher):
        def parse(position, text):
            token_size = len(matcher.token)

            if len(text) - position < token_size:
                return ParsingResult.back_to(position)

            next_portion = text[position:position + token_size]

            if next_portion != matcher.token:
                return ParsingResult.back_to(position)

            return ParsingResult(position + token_size, next_portion)

        return parse

    def visit_manual_matcher(self, matcher):
        return matcher.parse

    def visit_matcher_union(self, union):
        parsers = []

        for matcher in union.matchers:
            parsers.append(matcher.accept(self.owner))

        def parse(position, text):
            for parser in parsers:
                result = parser(position, text)

                if result.is_success:
                    return result

            return ParsingResult.back_to(position)

        return parse

class Waiter:
    def __init__(self):
        self.link = None

    def parse(self, *args, **kwargs):
        return self.link(*args, **kwargs)

class RecursiveParser(ParserComponent):
    def __init__(self, owner):
        super().__init__(owner)

        self.results = []
        self.results_base = 0

        self.waiters = {}
        self.active_matchers = set()

    def visit_object(self, it):
        raise Exception(f'RecursiveParser > Not implemented > {it}')

    def visit_matcher_call(self, call):
        # Don't forget that `cache`
        # may contain same values: we can have
        # different MatcherCalls but with the same
        # matcher. Though, note that we shouldn't have
        # multiple identical MatcherCalls

        # visiting a MatcherCall *is* the point
        # from where a possible recursion may start,
        # that's why this is where we keep track of the
        # waiters.

        matcher = call.matcher

        if id(matcher) in self.waiters:
            return self.waiters[id(matcher)].parse

        if matcher in self.active_matchers:
            waiter = Waiter()
            self.waiters[id(matcher)] = waiter
            return waiter.parse

        parser = matcher.accept(self.owner)

        if id(matcher) in self.waiters:
            self.waiters[id(matcher)].link = parser

        return parser

    def visit_matcher_sequence(self, sequence):
        parsers = []

        for matcher in sequence.matchers:
            parsers.append(matcher.accept(self.owner))

        def parse(position, text):
            index = position
            real_initial_base = len(self.results)

            for it in range(len(sequence.matchers)):
                call = sequence.matchers[it]

                if not call.forbids_indent:
                    index = skip_indent(index, text)

                result = parsers[it](index, text)

                if not result.is_success:
                    if it <= sequence.non_returnable_index:
                        del self.results[real_initial_base:]
                        return ParsingResult.back_to(position)

                    self.report(f'Expected a "<todo>", but `{text[index:index+10]}` found (index: {index})')
                    return ParsingResult.escape(text)

                self.results.append(result.data)
                index = result.index

            result_data = sequence.handler(ResultsView(self.results, self.results_base))
            del self.results[self.results_base:]
            self.results.append(result_data)
            return ParsingResult(index, result_data)

        return parse

    def visit_rule_matcher(self, rule):
        self.active_matchers.add(rule)

        run_normal_branches = rule.normal_branches.accept(self.owner)
        run_recurrent_branches = rule.recurrent_branches.accept(self.owner)

        self.active_matchers.remove(rule)

        def parse(position, text):
            index = position

            old_results_base = self.results_base
            self.results_base = len(self.results)
            normal_result = run_normal_branches(index, text)

            if not normal_result.is_success:
                self.results_base = old_results_base
                return ParsingResult.back_to(position)

            result = normal_result.data
            index = normal_result.index
            try_more_recurrent_branches = len(rule.recurrent_branches.matchers) > 0

            while try_more_recurrent_branches:
                recurrent_result = run_recurrent_branches(index, text)
                try_more_recurrent_branches = recurrent_result.is_success

                if try_more_recurrent_branches:
                    result = recurrent_result.data
                    index = recurrent_result.index

            self.results_base = old_results_base
            del self.results[-1]

            return ParsingResult(index, result)

        return parse

    def visit_recursive_matcher(self, matcher):
        return matcher.top_level_matcher.accept(self.owner)
