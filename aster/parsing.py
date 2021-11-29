from aster.grammar import *

class ParsingResult:
    def __init__(self, index, node):
        self.index = index
        self.node = node

    def is_success(self):
        return self.node is not None

    @staticmethod
    def back_to(index):
        return ParsingResult(index, None)

    @staticmethod
    def escape(text):
        return ParsingResult(len(text), None)

class NodesView:
    def __init__(self, nodes, base):
        self.nodes = nodes
        self.base = base

    def get_arguments(self):
        return self.nodes[self.base:]

    def __getitem__(self, index):
        return self.nodes[index + self.base]

    def __len__(self):
        return len(self.nodes) - self.base

    class Iterator:
        def __init__(self, nodes_view):
            self.nodes_view = nodes_view
            self.index = nodes_view.base

        def __next__(self):
            if self.index >= len(self.nodes_view.nodes):
                raise StopIteration()

            result = self.nodes_view.nodes[self.index]
            self.index += 1
            return result

    def __iter__(self):
        return NodesView.Iterator(self)

def skip_indent(position, text):
    while position < len(text) and text[position] in ' \t\n':
        position += 1
    return position

class Parser(Visitor):
    def __init__(self):
        self.cache = {}
        self.errors = []
        self.nodes = []
        self.runners = {}
        self.waiters = {}
        self.runners_stack = []

    def report(self, error):
        self.errors.append(error.replace('\n', '\\n').replace('\t', '\\t'))

    def create_runner(self, node, *args, **kwargs):
        if id(node) in self.runners:
            return self.runners[id(node)]

        if id(node) in self.waiters:
            waiters = self.waiters[id(node)]
        else:
            waiters = []
            self.waiters[id(node)] = waiters

        if node in self.runners_stack:
            waiter = {
                'link': None,
            }

            def inner(*args, **kwargs):
                return waiter['link'](*args, **kwargs)

            waiters.append(waiter)
            runner = inner
        else:
            self.runners_stack.append(node)
            runner = node.accept(self, *args, **kwargs)
            self.runners_stack.pop()

        self.runners[id(node)] = runner

        for waiter in self.waiters[id(node)]:
            waiter['link'] = runner

        return runner

    def visit_parsing_node(self, parsing_node):
        raise Exception('Parsing > Not implemented > ' + str(parsing_node))

    def visit_matcher(self, matcher):
        return self.create_runner(matcher.rule)

    def visit_branch(self, branch):
        matcher_runners = []

        for matcher in branch.matchers:
            matcher_runners.append(self.create_runner(matcher))

        def inner(position, text, nodes_base):
            index = position
            real_initial_base = len(self.nodes)

            for it in range(len(branch.matchers)):
                matcher = branch.matchers[it]

                if not matcher.forbids_indent:
                    index = skip_indent(index, text)

                result = None
                cacke_key = (matcher.rule.name, index)

                if cacke_key not in self.cache:
                    result = matcher_runners[it](index, text)
                else:
                    result = self.cache[cacke_key]

                if not result.is_success():
                    if it <= branch.non_returnable_index:
                        del self.nodes[real_initial_base:]
                        return ParsingResult.back_to(position)

                    self.report(f'Expected a "{matcher.rule.name}", but `{text[index:index+10]}` found (index: {index})')
                    return ParsingResult.escape(text)

                self.cache[cacke_key] = result

                self.nodes.append(result.node)
                index = result.index

            result_node = branch.action(NodesView(self.nodes, nodes_base))
            del self.nodes[nodes_base:]
            return ParsingResult(index, result_node)

        return inner

    def visit_branch_group(self, branch_group):
        branch_runners = []

        for branch in branch_group.branches:
            branch_runners.append(self.create_runner(branch))

        def inner(position, text, nodes_base):
            for run_branch in branch_runners:
                branch_result = run_branch(position, text, nodes_base)

                if branch_result.is_success():
                    return branch_result

            return ParsingResult.back_to(position)

        return inner

    def visit_symbol_rule(self, rule):
        def inner(position, text):
            next_symbol = text[position]

            if rule.symbol_checker(next_symbol):
                return ParsingResult(position + 1, next_symbol)

            return ParsingResult.back_to(position)

        return inner

    def visit_sequence_rule(self, rule):
        def inner(position, text):
            index = position

            if not rule.symbol_checker(text[index]):
                return ParsingResult.back_to(position)

            token = text[index]
            index += 1

            while rule.symbol_checker(text[index]):
                token += text[index]
                index += 1

            return ParsingResult(index, token)

        return inner

    def visit_token_rule(self, rule):
        def inner(position, text):
            token_size = len(rule.token)

            if len(text) - position < token_size:
                return ParsingResult.back_to(position)

            next_portion = text[position:position + token_size]

            if next_portion != rule.token:
                return ParsingResult.back_to(position)

            return ParsingResult(position + token_size, next_portion)

        return inner

    def visit_lexing_rule(self, rule):
        return rule.lexer

    def visit_branching_rule(self, rule):
        run_normal_branches = self.create_runner(rule.normal_branches)
        run_recurrent_branches = self.create_runner(rule.recurrent_branches)

        def inner(position, text):
            index = position

            normal_result = run_normal_branches(index, text, len(self.nodes))

            if not normal_result.is_success():
                return ParsingResult.back_to(position)

            result = normal_result.node
            index = normal_result.index
            # Because if there're no branches and we append the
            # result to the self.nodes, it won't be deleted
            some_recurrent_branch_worked = True and len(rule.recurrent_branches.branches) > 0

            while some_recurrent_branch_worked:
                self.nodes.append(result)
                recurrent_result = run_recurrent_branches(index, text, len(self.nodes) - 1)
                some_recurrent_branch_worked = recurrent_result.is_success()

                if some_recurrent_branch_worked:
                    result = recurrent_result.node
                    index = recurrent_result.index
                else:
                    del self.nodes[-1]

            return ParsingResult(index, result)

        return inner

    def visit_grammar(self, grammar):
        return self.create_runner(grammar.top_level_matcher)
