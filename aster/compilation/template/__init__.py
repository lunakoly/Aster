from aster.resolution import ParsingTreeResolver, ResolutionContext

from .handlers import *

from . import conversion

class TemplateBuilder:
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
            '$upper': result@0,
        }

    def build_comma_list_rule(self, rule, list_type):
        list_rule = rule + 'List'

        return {
            list_rule: {
                f'@{list_rule} , | @{rule}': list_append(2),
                '@' + rule: list_type.new // {
                    'values': [result@0],
                },
            },
        }

    def compile_grammar_from_template(self, grammar_template):
        context = ResolutionContext()
        grammar = conversion.build_recursive_matcher(context, grammar_template)
        ParsingTreeResolver(context).visit_recursive_matcher(grammar)
        return grammar
