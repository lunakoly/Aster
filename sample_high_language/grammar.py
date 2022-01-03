from aster.handlers import result, string_append
from aster.builders import build_forward_to_upper, build_comma_list_rule
from aster.grammar import RecursiveMatcherTemplate, rule_template
from aster.parsing import ParsingResult

from codegen import ENGLISH

from .ast import *

grammar = RecursiveMatcherTemplate()

@grammar.symbol
def blank(next):
    return next in ' \t\n'

@grammar.symbol
def not_blank(next):
    return not blank(next)

@grammar.symbol
def binary(next):
    return next in '01'

@grammar.symbol
def octal(next):
    return binary(next) or next in '234567'

@grammar.symbol
def decimal(next):
    return octal(next) or next in '89'

@grammar.symbol
def hexadecimal(next):
    return decimal(next) or next in 'abcdefABCDEF'

@grammar.symbol
def name_start(next):
    return next == '_' or next in ENGLISH

@grammar.symbol
def name_inner(next):
    return name_start(next) or decimal(next)

@grammar.lexing
def name(position, text):
    index = position

    if not name_start(text[index]):
        return ParsingResult.back_to(position)

    index += 1

    while name_inner(text[index]):
        index += 1

    result = text[position:index]
    return ParsingResult(index, result)

string_initializer = String.new // {
    'value': result@0,
}

@grammar.lexing
def string(position, text):
    index = position

    if text[index] != '"':
        return ParsingResult.back_to(position)

    result = ''
    index += 1

    while text[index] != '"':
        if text[index] == '\\':
            index += 1
        result += text[index]
        index += 1

    return ParsingResult(index + 1, string_initializer([result]))

grammar += {
    'binary_number': rule_template // {
        '@binary_sequence~b': Number.new // {
            'value': result@0,
            'base': 2,
        },
    },
    'octal_number': rule_template // {
        '@octal_sequence~o': Number.new // {
            'value': result@0,
            'base': 8,
        },
    },
    'hexadecimal_number': rule_template // {
        '@hexadecimal_sequence~h': Number.new // {
            'value': result@0,
            'base': 16,
        },
    },
    'decimal_number': rule_template // {
        '@decimal_sequence': Number.new // {
            'value': result@0,
            'base': 10,
        },
    },
    'identifier': rule_template // {
        '@name': Identifier.new // {
            'name': result@0,
        },
    },
    'expected_identifier': rule_template // {
        '|@name': Identifier.new // {
            'name': result@0,
        },
    },
    **build_comma_list_rule('expected_identifier', List),
    'error_token': rule_template // {
        '@error_token~@not_blank': string_append,
        '@blank_sequence': result@0,
        '@not_blank_sequence': result@0,
    },
    'error': rule_template // {
        '|@error_token': Error.new // {
            'token': result@0,
        },
    },
    'any_token': rule_template // {
        '@identifier': result@0,
        '@string': result@0,
        '@binary_number': result@0,
        '@octal_number': result@0,
        '@hexadecimal_number': result@0,
        '@decimal_number': result@0,
    },
    'closure_contents': rule_template // {
        '@expected_identifier_list -> | @statement_list': Closure.new // {
            'arguments': result@0,
            'statements': result@2,
        },
        '@statement_list': Closure.new // {
            'arguments': None,
            'statements': result@0,
        },
    },
    'item': rule_template // {
        '@any_token': result@0,
        '( | @expression )': result@1,
        '@item ( | @expression_list )': Call.new // {
            'receiver': result@0,
            'arguments': result@2,
        },
        '@item [ | @expression_list ]': Subscript.new // {
            'receiver': result@0,
            'arguments': result@2,
        },
        '{ | @closure_contents }': result@1,
        '@error': result@0,
    },
    'unary_minus': rule_template // {
        '- | $upper': UnaryMinus.new // {
            'target': result@1,
        },
        '$upper': result@0,
    },
    'times_or_divide': rule_template // {
        '$self * | $upper': Times.new_from(result@0, result@2),
        '$self / | $upper': Divide.new_from(result@0, result@2),
        **build_forward_to_upper(),
    },
    'plus_or_minus': rule_template // {
        '$self + | $upper': Plus.new_from(result@0, result@2),
        '$self - | $upper': Minus.new_from(result@0, result@2),
        **build_forward_to_upper(),
    },
    'expression': rule_template // {
        **build_forward_to_upper(),
    },
    **build_comma_list_rule('expression', List),
    'let_declaration_contents': rule_template // {
        ': | @expected_identifier = @expression': LetDeclaration.new // {
            'name': result@-1,
            'type': result@1,
            'value': result@3,
        },
        '= | @expression': LetDeclaration.new // {
            'name': result@-1,
            'type': None,
            'value': result@1,
        },
        ': | @expected_identifier': LetDeclaration.new // {
            'name': result@-1,
            'type': result@1,
            'value': None,
        },
    },
    'statement': rule_template // {
        'let|@blank_sequence~@identifier @let_declaration_contents': result@3,
        '@expression': result@0,
    },
    **build_comma_list_rule('statement', List),
    'top_level_closure': rule_template // {
        '@blank_sequence|@statement_list': Closure.new // {
            'arguments': None,
            'statements': result@1,
        },
        '@statement_list': Closure.new // {
            'arguments': None,
            'statements': result@0,
        },
    },
}

grammar.top_level_matcher_name = 'top_level_closure'
