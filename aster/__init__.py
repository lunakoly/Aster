from .conversion import ConversionContext, GrammarConverter
from .resolution import ResolutionContext, GrammarResolver
from .parsing import Parser

def compile_grammar(matcher, errors_collector):
    conversion_context = ConversionContext()
    converted = matcher.accept(GrammarConverter(conversion_context))

    resolution_context = ResolutionContext(conversion_context)
    converted.accept(GrammarResolver(resolution_context))

    return converted.accept(Parser(errors_collector))

def parse(text, matcher):
    errors = []
    result = compile_grammar(matcher, errors)(0, text)

    if result.is_success:
        return result.data, errors

    return None, errors
