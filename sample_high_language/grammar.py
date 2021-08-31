from aster.compilation.template import TemplateBuilder
from aster.compilation.template import handlers
from aster.compilation import preprocessing
from aster.parsing import ParsingResult

from . import symbols

builder = TemplateBuilder()

string_initializer = builder.build_ast('String', {
    'value': '$0',
})

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

    return ParsingResult(index + 1, True, string_initializer([result]))

grammar = builder.compile_grammar_from_template({
    'symbolGroups': preprocessing.collect_symbol_groups(symbols.__dict__),
    'rules': {
        **builder.build_sequence_rule('binary'),
        **builder.build_sequence_rule('octal'),
        **builder.build_sequence_rule('decimal'),
        **builder.build_sequence_rule('hexadecimal'),
        'binaryNumber|returnable': {
            '@binarySequence~b': builder.build_ast('Number', {
                'value': '$0',
                'base': 2,
            }),
        },
        'octalNumber|returnable': {
            '@octalSequence~o': builder.build_ast('Number', {
                'value': '$0',
                'base': 8,
            }),
        },
        'hexadecimalNumber|returnable': {
            '@hexadecimalSequence~h': builder.build_ast('Number', {
                'value': '$0',
                'base': 16,
            }),
        },
        'decimalNumber|returnable': {
            '@decimalSequence': builder.build_ast('Number', {
                'value': '$0',
                'base': 10,
            }),
        },
        'name|returnable': {
            '@name~#nameInner': handlers.string_append,
            '#nameStart': handlers.take(0),
        },
        'identifier|returnable': {
            '@name': builder.build_ast('Identifier', {
                'name': '$0',
            }),
        },
        'expectedIdentifier': {
            '@name': builder.build_ast('Identifier', {
                'name': '$0',
            }),
        },
        **builder.build_comma_list_rule('expectedIdentifier'),
        'string|returnable|lexing': {
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
            '@errorToken': builder.build_ast('Error', {
                'token': '$0',
            }),
        },
        'anyToken|returnable': {
            '@binaryNumber': handlers.take(0),
            '@octalNumber': handlers.take(0),
            '@hexadecimalNumber': handlers.take(0),
            '@decimalNumber': handlers.take(0),
            '@identifier': handlers.take(0),
            '@string': handlers.take(0),
        },
        'item': {
            '@anyToken': handlers.take(0),
            '( @expression )': handlers.take(1),
            '@item ( @expressionList )': builder.build_ast('Call', {
                'receiver': '$0',
                'arguments': '$2',
            }),
            '@item [ @expressionList ]': builder.build_ast('Subscript', {
                'receiver': '$0',
                'arguments': '$2',
            }),
            '{ @expectedIdentifierList -> @statementList }': builder.build_ast('Closure', {
                'arguments': '$1',
                'statements': '$3',
            }),
            '{ @statementList }': builder.build_ast('Closure', {
                'arguments': None,
                'statements': '$1',
            }),
            '@error': handlers.take(0),
        },
        'unaryMinus': {
            '- $upper': builder.build_ast('UnaryMinus', {
                'target': '$1',
            }),
            '$upper': handlers.take(0),
        },
        'timesOrDivide': {
            '$self * $upper': builder.build_binary_ast('Times', '$0', '$2'),
            '$self / $upper': builder.build_binary_ast('Divide', '$0', '$2'),
            **builder.build_forward_to_upper(),
        },
        'plusOrMinus': {
            '$self + $upper': builder.build_binary_ast('Plus', '$0', '$2'),
            '$self - $upper': builder.build_binary_ast('Minus', '$0', '$2'),
            **builder.build_forward_to_upper(),
        },
        'expression': {
            **builder.build_forward_to_upper(),
        },
        **builder.build_comma_list_rule('expression'),
        'letDeclaration|returnable': {
            ': @identifier = @expression': builder.build_ast('LetDeclaration', {
                'name': '$-1',
                'type': '$1',
                'value': '$3',
            }),
            '= @expression': builder.build_ast('LetDeclaration', {
                'name': '$-1',
                'type': None,
                'value': '$1',
            }),
            ': @identifier': builder.build_ast('LetDeclaration', {
                'name': '$-1',
                'type': '$1',
                'value': None,
            }),
        },
        'statement': {
            'let~@blankSequence~@identifier @letDeclaration': handlers.take(3),
            '@expression': handlers.take(0),
        },
        **builder.build_comma_list_rule('statement'),
        'topLevelClosure': {
            '@blankSequence~@statementList': builder.build_ast('Closure', {
                'arguments': None,
                'statements': '$1',
            }),
            '@statementList': builder.build_ast('Closure', {
                'arguments': None,
                'statements': '$0',
            }),
        },
    },
    'top_level_rule': 'topLevelClosure',
})
