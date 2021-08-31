from aster.parsing_tree import *

class ParsingResult:
    def __init__(self, index, success, node):
        self.success = success
        self.index = index
        self.node = node

    @staticmethod
    def back_to(index):
        return ParsingResult(index, False, None)

    @staticmethod
    def escape(text):
        return ParsingResult(len(text), False, None)

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

class Parser(ParsingTreeVisitor):
    def __init__(self):
        self.cache = {}
        self.errors = []
        self.nodes = []

    def report(self, error):
        self.errors.append(error.replace('\n', '\\n').replace('\t', '\\t'))

    def visit_parsing_node(self, parsing_node):
        raise Exception('Parsing > Not implemented > ' + str(parsing_node))

    def visit_matcher(self, matcher, position, text):
        return matcher.rule.accept(self, position, text)

    def visit_branch(self, branch, position, text, nodes_base):
        index = position
        real_initial_base = len(self.nodes)

        for it in range(len(branch.matchers)):
            matcher = branch.matchers[it]

            if not matcher.forbids_indent:
                index = skip_indent(index, text)

            result = None
            cacke_key = (matcher.rule.name, index)

            if cacke_key not in self.cache:
                # We know for sure this is a Matcher
                result = matcher.rule.accept(self, index, text)
            else:
                result = self.cache[cacke_key]

            if not result.success:
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
        return ParsingResult(index, True, result_node)

    def visit_branch_group(self, branch_group, position, text, nodes_base):
        for branch in branch_group.branches:
            # We know for sure this is a Branch
            branch_result = self.visit_branch(branch, position, text, nodes_base)

            if branch_result.success:
                return branch_result

        return ParsingResult.back_to(position)

    def visit_symbol_rule(self, rule, position, text):
        next_symbol = text[position]

        if rule.symbol_checker(next_symbol):
            return ParsingResult(position + 1, True, next_symbol)

        return ParsingResult.back_to(position)

    def visit_sequence_rule(self, rule, position, text):
        index = position

        if not rule.symbol_checker(text[index]):
            return ParsingResult.back_to(position)

        token = text[index]
        index += 1

        while rule.symbol_checker(text[index]):
            token += text[index]
            index += 1

        return ParsingResult(index, True, token)

    def visit_token_rule(self, rule, position, text):
        token_size = len(rule.token)

        if len(text) - position < token_size:
            return ParsingResult.back_to(position)

        next_portion = text[position:position + token_size]

        if next_portion != rule.token:
            return ParsingResult.back_to(position)

        return ParsingResult(position + token_size, True, next_portion)

    def visit_lexing_rule(self, rule, position, text):
        return rule.lexer(position, text)

    def visit_branching_rule(self, rule, position, text):
        index = position

        # We know for sure this is a BranchGroup
        normal_result = self.visit_branch_group(rule.normal_branches, index, text, len(self.nodes))

        if not normal_result.success:
            return ParsingResult.back_to(position)

        result = normal_result.node
        index = normal_result.index
        # Because if there're no branches and we append the
        # result to the self.nodes, it won't be deleted
        some_recurrent_branch_worked = True and len(rule.recurrent_branches.branches) > 0

        while some_recurrent_branch_worked:
            self.nodes.append(result)
            # We know for sure this is a BranchGroup
            recurrent_result = self.visit_branch_group(rule.recurrent_branches, index, text, len(self.nodes) - 1)
            some_recurrent_branch_worked = recurrent_result.success

            if some_recurrent_branch_worked:
                result = recurrent_result.node
                index = recurrent_result.index
            else:
                del self.nodes[-1]

        return ParsingResult(index, True, result)

    def visit_grammar(self, grammar, position, text):
        return grammar.top_level_matcher.accept(self, position, text)
