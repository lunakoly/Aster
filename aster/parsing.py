from aster.grammar import *

class MatchingResult:
    def __init__(self, index, data, is_success=True):
        self.is_success = is_success
        self.index = index
        self.data = data

    @staticmethod
    def back_to(index):
        return MatchingResult(index, None, is_success=False)

    @staticmethod
    def escape(text):
        return MatchingResult(len(text), None, is_success=False)

class Waiter:
    def __init__(self):
        self.link = None

    def run(self, *args, **kwargs):
        return self.link(*args, **kwargs)

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
    def __init__(self):
        self.cache = {}
        self.errors = []
        self.results = []
        self.runners = {}
        self.waiters = {}
        self.active_runners = set()

        # RecursiveMatcher's context
        self.results_base = 0

    def report(self, error):
        self.errors.append(error.replace('\n', '\\n').replace('\t', '\\t'))

    def create_runner(self, matcher, *args, **kwargs):
        if id(matcher) in self.runners:
            return self.runners[id(matcher)]

        if id(matcher) in self.waiters:
            return self.waiters[id(matcher)].run

        waiter = Waiter()
        self.waiters[id(matcher)] = waiter

        if matcher in self.active_runners:
            return waiter.run

        self.active_runners.add(matcher)
        runner = matcher.accept(self, *args, **kwargs)
        self.active_runners.remove(matcher)

        self.runners[id(matcher)] = runner
        waiter.link = runner
        return runner

    def visit_object(self, it):
        raise Exception('Parsing > Not implemented > ' + str(it))

    def visit_symbol_matcher(self, matcher):
        def inner(position, text):
            next_symbol = text[position]

            if matcher.symbol_checker(next_symbol):
                return MatchingResult(position + 1, next_symbol)

            return MatchingResult.back_to(position)

        return inner

    def visit_symbol_sequence_matcher(self, matcher):
        def inner(position, text):
            index = position

            if not matcher.symbol_checker(text[index]):
                return MatchingResult.back_to(position)

            token = text[index]
            index += 1

            while matcher.symbol_checker(text[index]):
                token += text[index]
                index += 1

            return MatchingResult(index, token)

        return inner

    def visit_token_matcher(self, matcher):
        def inner(position, text):
            token_size = len(matcher.token)

            if len(text) - position < token_size:
                return MatchingResult.back_to(position)

            next_portion = text[position:position + token_size]

            if next_portion != matcher.token:
                return MatchingResult.back_to(position)

            return MatchingResult(position + token_size, next_portion)

        return inner

    def visit_lexing_matcher(self, matcher):
        return matcher.lexer

    def visit_matcher_call(self, call):
        return self.create_runner(call.matcher)

    def visit_matcher_sequence(self, sequence):
        runners = []

        for matcher in sequence.matchers:
            runners.append(self.create_runner(matcher))

        def inner(position, text):
            index = position
            real_initial_base = len(self.results)

            for it in range(len(sequence.matchers)):
                matcher = sequence.matchers[it]

                if not matcher.forbids_indent:
                    index = skip_indent(index, text)

                result = None
                cacke_key = (id(matcher), index)

                if cacke_key not in self.cache:
                    result = runners[it](index, text)
                    self.cache[cacke_key] = result
                else:
                    result = self.cache[cacke_key]

                if not result.is_success:
                    if it <= sequence.non_returnable_index:
                        del self.results[real_initial_base:]
                        return MatchingResult.back_to(position)

                    self.report(f'Expected a "<todo>", but `{text[index:index+10]}` found (index: {index})')
                    return MatchingResult.escape(text)

                self.results.append(result.data)
                index = result.index

            result_data = sequence.action(ResultsView(self.results, self.results_base))
            del self.results[self.results_base:]
            self.results.append(result_data)
            return MatchingResult(index, result_data)

        return inner

    def visit_matcher_union(self, union):
        runners = []

        for branch in union.matchers:
            runners.append(self.create_runner(branch))

        def inner(position, text):
            for run_branch in runners:
                branch_result = run_branch(position, text)

                if branch_result.is_success:
                    return branch_result

            return MatchingResult.back_to(position)

        return inner

    def visit_rule_matcher(self, rule):
        run_normal_branches = self.create_runner(rule.normal_branches)
        run_recurrent_branches = self.create_runner(rule.recurrent_branches)

        def inner(position, text):
            index = position

            old_results_base = self.results_base
            self.results_base = len(self.results)
            normal_result = run_normal_branches(index, text)

            if not normal_result.is_success:
                self.results_base = old_results_base
                return MatchingResult.back_to(position)

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

            return MatchingResult(index, result)

        return inner

    def visit_recursive_matcher(self, matcher):
        return self.create_runner(matcher.top_level_matcher)
