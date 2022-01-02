from . import tree

TAB = ' ' * 4

class Printer(tree.Visitor):
    def visit_let_declaration(self, it, indent=''):
        print('let ', end='')
        it.name.accept(self, indent)

        if it.type is not None:
            print(': ', end='')
            it.type.accept(self, indent)

        if it.value is not None:
            print(' = ', end='')
            it.value.accept(self, indent)

    def print_binary(self, it, indent='', operator='?'):
        print('(', end='')
        it.lefter.accept(self, indent)
        print(' ' + operator + ' ', end='')
        it.righter.accept(self, indent)
        print(')', end='')

    def visit_plus(self, it, indent=''):
        self.print_binary(it, indent, '+')

    def visit_minus(self, it, indent=''):
        self.print_binary(it, indent, '-')

    def visit_times(self, it, indent=''):
        self.print_binary(it, indent, '*')

    def visit_divide(self, it, indent=''):
        self.print_binary(it, indent, '/')

    def visit_unary_minus(self, it, indent=''):
        print('-', end='')
        it.target.accept(self, indent)

    def visit_closure(self, it, indent=''):
        print('{', end='\n')

        if it.arguments is not None:
            it.arguments.accept(self, indent + TAB, ',')
            print(indent + '->', end='\n')

        it.statements.accept(self, indent + TAB, ';')
        print(indent + '}', end='')

    def print_list(self, opening, it, closing, indent='', delimiter=''):
        print(opening, end='\n')
        it.accept(self, indent + TAB, delimiter)
        print(indent + closing, end='')

    def visit_subscript(self, it, indent=''):
        it.receiver.accept(self, indent)
        self.print_list('[', it.arguments, ']', indent, ',')

    def visit_call(self, it, indent=''):
        it.receiver.accept(self, indent)
        self.print_list('(', it.arguments, ')', indent, ',')

    def visit_error(self, it, indent=''):
        print(f'<!{it.token}!>', end='')

    def visit_identifier(self, it, indent=''):
        print(it.name, end='')

    def visit_number(self, it, indent=''):
        print(it.value + '#' + str(it.base), end='')

    def visit_list(self, it, indent='', delimiter=''):
        for that in it.values:
            print(indent, end='')
            that.accept(self, indent)
            print(delimiter)

    def visit_string(self, it, indent=''):
        filtered = it.value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')
        print('"' + filtered + '"', end='')
