from .conversion import ConversionContext, GrammarConverter
from .resolution import ResolutionContext, GrammarResolver
from .parsing import ParserGenerator

def prepare_grammar(matcher):
    conversion_context = ConversionContext()
    converted = matcher.accept(GrammarConverter(conversion_context))

    resolution_context = ResolutionContext(conversion_context)
    resolved = converted.accept(GrammarResolver(resolution_context))

    return resolved

def compile_grammar(matcher, errors_collector):
    resolved = prepare_grammar(matcher)
    return resolved.accept(ParserGenerator(errors_collector))

def parse(text, matcher):
    errors = []
    result = compile_grammar(matcher, errors)(0, text)

    if result.is_success:
        return result.data, errors

    return None, errors
