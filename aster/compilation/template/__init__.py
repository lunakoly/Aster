from aster.resolution import ParsingTreeResolver, ResolutionContext
from aster.synthetic import TypeBuilder

from .handlers import *

from . import conversion

class TemplateBuilder:
    def __init__(self):
        self.type_builder = TypeBuilder()

    @staticmethod
    def get_returnable_suffix(returnable):
        return '|returnable' if returnable else ''

    @staticmethod
    def build_sequence_rule(symbol_group):
        rule = symbol_group + 'Sequence'

        return {
            rule + '|sequence': {
                'symbolGroup': symbol_group,
            },
        }

    @staticmethod
    def build_forward_to_upper():
        return {
            '$upper': take(0),
        }

    def build_ast(self, class_name, fields):
        return self.type_builder.provide_ast(class_name, fields)

    def build_binary_ast(self, class_name, left_accessor, right_accessor):
        return self.build_ast(class_name, {
            'lefter': left_accessor,
            'righter': right_accessor,
        })

    def build_comma_list_rule(self, rule):
        list_rule = rule + 'List'

        return {
            list_rule: {
                f'@{list_rule} , | @{rule}': list_append(2),
                '@' + rule: self.build_ast('List', {
                    'values': ['$0'],
                }),
            },
        }

    def compile_grammar_from_template(self, grammar_template):
        context = ResolutionContext()
        grammar = conversion.build_grammar(context, grammar_template, self.type_builder.types)
        ParsingTreeResolver(context).visit_grammar(grammar)
        return grammar
