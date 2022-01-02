from aster.compilation.template import TemplateBuilder
from aster.compilation.template import handlers
from aster.compilation import preprocessing
from aster.parsing import MatchingResult

from . import symbols
from .ast import *

from aster.compilation.template.handlers import result

builder = TemplateBuilder()

string_initializer = String.new // {
    'value': result@0,
}

def parse_string(position, text):
    index = position

    if text[index] != '"':
        return MatchingResult.back_to(position)

    result = ''
    index += 1

    while text[index] != '"':
        if text[index] == '\\':
            index += 1
        result += text[index]
        index += 1

    return MatchingResult(index + 1, string_initializer([result]))

def parse_name(position, text):
    index = position

    if not symbols.is_nameStart(text[index]):
        return MatchingResult.back_to(position)

    index += 1

    while symbols.is_nameInner(text[index]):
        index += 1

    result = text[position:index]
    return MatchingResult(index, result)

grammar = builder.compile_grammar_from_template({
    'symbolGroups': preprocessing.collect_symbol_groups(symbols.__dict__),
    'rules': {
        **builder.build_sequence_rule('binary'),
        **builder.build_sequence_rule('octal'),
        **builder.build_sequence_rule('decimal'),
        **builder.build_sequence_rule('hexadecimal'),
        'binaryNumber': {
            '@binarySequence~b': Number.new // {
                'value': result@0,
                'base': 2,
            },
        },
        'octalNumber': {
            '@octalSequence~o': Number.new // {
                'value': result@0,
                'base': 8,
            },
        },
        'hexadecimalNumber': {
            '@hexadecimalSequence~h': Number.new // {
                'value': result@0,
                'base': 16,
            },
        },
        'decimalNumber': {
            '@decimalSequence': Number.new // {
                'value': result@0,
                'base': 10,
            },
        },
        'name|lexing': {
            'lexer': parse_name,
        },
        'identifier': {
            '@name': Identifier.new // {
                'name': result@0,
            },
        },
        'expectedIdentifier': {
            '|@name': Identifier.new // {
                'name': result@0,
            },
        },
        **builder.build_comma_list_rule('expectedIdentifier', List),
        'string|lexing': {
            'lexer': parse_string,
        },
        **builder.build_sequence_rule('blank'),
        **builder.build_sequence_rule('notBlank'),
        'errorToken': {
            '@errorToken~#notBlank': handlers.string_append,
            '@blankSequence': result@0,
            '@notBlankSequence': result@0,
        },
        'error': {
            '|@errorToken': Error.new // {
                'token': result@0,
            },
        },
        'anyToken': {
            '@identifier': result@0,
            '@string': result@0,
            '@binaryNumber': result@0,
            '@octalNumber': result@0,
            '@hexadecimalNumber': result@0,
            '@decimalNumber': result@0,
        },
        'closureContents': {
            '@expectedIdentifierList -> | @statementList': Closure.new // {
                'arguments': result@0,
                'statements': result@2,
            },
            '@statementList': Closure.new // {
                'arguments': None,
                'statements': result@0,
            },
        },
        'item': {
            '@anyToken': result@0,
            '( | @expression )': result@1,
            '@item ( | @expressionList )': Call.new // {
                'receiver': result@0,
                'arguments': result@2,
            },
            '@item [ | @expressionList ]': Subscript.new // {
                'receiver': result@0,
                'arguments': result@2,
            },
            '{ | @closureContents }': result@1,
            '@error': result@0,
        },
        'unaryMinus': {
            '- | $upper': UnaryMinus.new // {
                'target': result@1,
            },
            '$upper': result@0,
        },
        'timesOrDivide': {
            '$self * | $upper': Times.new_from(result@0, result@2),
            '$self / | $upper': Divide.new_from(result@0, result@2),
            **builder.build_forward_to_upper(),
        },
        'plusOrMinus': {
            '$self + | $upper': Plus.new_from(result@0, result@2),
            '$self - | $upper': Minus.new_from(result@0, result@2),
            **builder.build_forward_to_upper(),
        },
        'expression': {
            **builder.build_forward_to_upper(),
        },
        **builder.build_comma_list_rule('expression', List),
        'letDeclarationContents': {
            ': | @expectedIdentifier = @expression': LetDeclaration.new // {
                'name': result@-1,
                'type': result@1,
                'value': result@3,
            },
            '= | @expression': LetDeclaration.new // {
                'name': result@-1,
                'type': None,
                'value': result@1,
            },
            ': | @expectedIdentifier': LetDeclaration.new // {
                'name': result@-1,
                'type': result@1,
                'value': None,
            },
        },
        'statement': {
            'let|@blankSequence~@identifier @letDeclarationContents': result@3,
            '@expression': result@0,
        },
        **builder.build_comma_list_rule('statement', List),
        'topLevelClosure': {
            '@blankSequence|@statementList': Closure.new // {
                'arguments': None,
                'statements': result@1,
            },
            '@statementList': Closure.new // {
                'arguments': None,
                'statements': result@0,
            },
        },
    },
    'top_level_rule': 'topLevelClosure',
})
