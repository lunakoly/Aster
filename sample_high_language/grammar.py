from aster.compilation.template import TemplateBuilder
from aster.compilation.template import handlers
from aster.compilation import preprocessing
from aster.parsing import ParsingResult
from aster.synthetic import parameter

from . import symbols
from .tree import *

builder = TemplateBuilder()

string_initializer = String.create@{
    'value': parameter@0,
}

def parse_string(position, text):
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

def parse_name(position, text):
    index = position

    if not symbols.is_nameStart(text[index]):
        return ParsingResult.back_to(position)

    index += 1

    while symbols.is_nameInner(text[index]):
        index += 1

    result = text[position:index]
    return ParsingResult(index, result)

grammar = builder.compile_grammar_from_template({
    'symbolGroups': preprocessing.collect_symbol_groups(symbols.__dict__),
    'rules': {
        **builder.build_sequence_rule('binary'),
        **builder.build_sequence_rule('octal'),
        **builder.build_sequence_rule('decimal'),
        **builder.build_sequence_rule('hexadecimal'),
        'binaryNumber': {
            '@binarySequence~b': Number.create@{
                'value': parameter@0,
                'base': 2,
            },
        },
        'octalNumber': {
            '@octalSequence~o': Number.create@{
                'value': parameter@0,
                'base': 8,
            },
        },
        'hexadecimalNumber': {
            '@hexadecimalSequence~h': Number.create@{
                'value': parameter@0,
                'base': 16,
            },
        },
        'decimalNumber': {
            '@decimalSequence': Number.create@{
                'value': parameter@0,
                'base': 10,
            },
        },
        'name|lexing': {
            'lexer': parse_name,
        },
        'identifier': {
            '@name': Identifier.create@{
                'name': parameter@0,
            },
        },
        'expectedIdentifier': {
            '|@name': Identifier.create@{
                'name': parameter@0,
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
            '@blankSequence': handlers.take(0),
            '@notBlankSequence': handlers.take(0),
        },
        'error': {
            '|@errorToken': Error.create@{
                'token': parameter@0,
            },
        },
        'anyToken': {
            '@identifier': handlers.take(0),
            '@string': handlers.take(0),
            '@binaryNumber': handlers.take(0),
            '@octalNumber': handlers.take(0),
            '@hexadecimalNumber': handlers.take(0),
            '@decimalNumber': handlers.take(0),
        },
        'closureContents': {
            '@expectedIdentifierList -> | @statementList': Closure.create@{
                'arguments': parameter@0,
                'statements': parameter@2,
            },
            '@statementList': Closure.create@{
                'arguments': None,
                'statements': parameter@0,
            },
        },
        'item': {
            '@anyToken': handlers.take(0),
            '( | @expression )': handlers.take(1),
            '@item ( | @expressionList )': Call.create@{
                'receiver': parameter@0,
                'arguments': parameter@2,
            },
            '@item [ | @expressionList ]': Subscript.create@{
                'receiver': parameter@0,
                'arguments': parameter@2,
            },
            '{ | @closureContents }': handlers.take(1),
            '@error': handlers.take(0),
        },
        'unaryMinus': {
            '- | $upper': UnaryMinus.create@{
                'target': parameter@1,
            },
            '$upper': handlers.take(0),
        },
        'timesOrDivide': {
            '$self * | $upper': Times.create_from(parameter@0, parameter@2),
            '$self / | $upper': Divide.create_from(parameter@0, parameter@2),
            **builder.build_forward_to_upper(),
        },
        'plusOrMinus': {
            '$self + | $upper': Plus.create_from(parameter@0, parameter@2),
            '$self - | $upper': Minus.create_from(parameter@0, parameter@2),
            **builder.build_forward_to_upper(),
        },
        'expression': {
            **builder.build_forward_to_upper(),
        },
        **builder.build_comma_list_rule('expression', List),
        'letDeclarationContents': {
            ': | @expectedIdentifier = @expression': LetDeclaration.create@{
                'name': parameter@-1,
                'type': parameter@1,
                'value': parameter@3,
            },
            '= | @expression': LetDeclaration.create@{
                'name': parameter@-1,
                'type': None,
                'value': parameter@1,
            },
            ': | @expectedIdentifier': LetDeclaration.create@{
                'name': parameter@-1,
                'type': parameter@1,
                'value': None,
            },
        },
        'statement': {
            'let|@blankSequence~@identifier @letDeclarationContents': handlers.take(3),
            '@expression': handlers.take(0),
        },
        **builder.build_comma_list_rule('statement', List),
        'topLevelClosure': {
            '@blankSequence|@statementList': Closure.create@{
                'arguments': None,
                'statements': parameter@1,
            },
            '@statementList': Closure.create@{
                'arguments': None,
                'statements': parameter@0,
            },
        },
    },
    'top_level_rule': 'topLevelClosure',
})
