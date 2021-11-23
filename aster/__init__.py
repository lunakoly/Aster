from .compilation import template

from .parsing import Parser

def parse(text, grammar):
    parser = Parser()
    result = parser.visit_grammar(grammar)(0, text)

    if result.is_success():
        return result.node, parser.errors

    return None, parser.errors

def compile_grammar_from_template(grammar_template):
    return template.compile_grammar_from_template(grammar_template)
