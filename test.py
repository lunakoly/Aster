import time
import aster

from sample_high_language import grammar, printer

from utils import prettifier

import aster.synthetic

import cProfile

from pstats import Stats

def measure(code, count):
    # with cProfile.Profile() as pr:
    #     start = time.time()

    #     for _ in range(count):
    #         code()

    #     stop = time.time()

    start = time.time()

    for _ in range(count):
        code()

    stop = time.time()

    print(f'Average time for {count} runs: {(stop - start) / count} s')

    # with open('stats.txt', 'w') as stream:
    #     stats = Stats(pr, stream=stream)
    #     stats.strip_dirs()
    #     stats.sort_stats('time')
    #     stats.dump_stats('stats.profiling')
    #     stats.print_stats()

def to_marker(ast):
    if ast is not None:
        return 'OK'
    return 'FAIL'

def test_parse(source_code):
    ast = None
    messages = None

    def parse_wrapper():
        nonlocal ast
        nonlocal messages
        ast, messages = aster.parse(source_code, grammar.grammar)

    measure(parse_wrapper, count=1000)

    print(f'[{to_marker(ast)}] Test Case:')
    print()

    if ast is not None:
        # print('Tree:', end=' ')
        # prettifier.print_pretty(ast)
        # print()
        print('Printer:', end=' ')
        ast.accept(printer.Printer())
        print()
        print()

    print('Messages:', end=' ')
    prettifier.print_pretty(messages)
    print()

    print(grammar.grammar.types.List)
    print(grammar.grammar.types.LetDeclaration)

if __name__ == '__main__':
    test_parse("""
        let a: Double = 10 * 2 + 3 * f(2, 4) - 4 * -1 + (1 - 2) - {
            a, b -> let c: String = "Hel\\lo\n\t\\"there\\"!"
        } * { let d = 2 } - {x,y->3}
    """)
    test_parse("""
        a + b * c--g(4, 5o)(2) [  deadbeefh]
    """)
