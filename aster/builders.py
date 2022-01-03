from .grammar import rule_template
from .handlers import *

def build_forward_to_upper():
    return {
        '$upper': result@0,
    }

def build_comma_list_rule(rule, list_type):
    list_rule = rule + '_list'

    return {
        list_rule: rule_template // {
            f'@{list_rule} , | @{rule}': list_append(2),
            '@' + rule: list_type.new // {
                'values': [result@0],
            },
        },
    }

