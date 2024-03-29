import gc
import pathlib
import random
import string

from sksequitur import Grammar, Mark, Parser, parse

module_dir = pathlib.Path(__file__).parent


def test_parser():
    parser = Parser()
    parser.feed('ab')
    assert len(parser.bigrams) == 1
    grammar = Grammar(parser.tree)
    assert str(grammar) == '0 -> a b'
    assert grammar.lengths() == {0: 2}
    assert grammar.counts() == {0: 1}
    assert grammar.depths() == {0: 0}
    assert list(grammar.expand(0)) == ['a', 'b']


def test_hello2():
    iterable = 'hello hello\n'
    grammar = parse(iterable)
    # print(grammar)
    result = """\
0 -> 1 _ 1 ↵
1 -> h e l l o                                    hello\
"""
    assert str(grammar) == result
    assert grammar.lengths() == {0: len(iterable), 1: 5}
    assert grammar.counts() == {0: 1, 1: 2}
    assert grammar.depths() == {0: 0, 1: 1}
    assert list(grammar.expand(0)) == list(iterable)


def test_abcabdabcabd():
    iterable = 'abcabdabcabd'
    grammar = parse(iterable)
    # print(grammar)
    result = """\
0 -> 1 1
1 -> 2 c 2 d                                      abcabd
2 -> a b                                          ab\
"""
    assert str(grammar) == result
    assert grammar.lengths() == {0: len(iterable), 1: 6, 2: 2}
    assert grammar.counts() == {0: 1, 1: 2, 2: 2}
    assert grammar.depths() == {0: 0, 1: 1, 2: 2}
    assert list(grammar.expand(0)) == list(iterable)


def test_abbbabcbb():
    iterable = 'abbbabcbb'
    grammar = parse(iterable)
    # print(grammar)
    result = """\
0 -> 1 2 1 c 2
1 -> a b                                          ab
2 -> b b                                          bb\
"""
    assert str(grammar) == result
    assert grammar.lengths() == {0: len(iterable), 1: 2, 2: 2}
    assert grammar.counts() == {0: 1, 1: 2, 2: 2}
    assert grammar.depths() == {0: 0, 1: 1, 2: 1}
    assert list(grammar.expand(0)) == list(iterable)


def test_pease_porridge():
    iterable = """\
pease porridge hot,
pease porridge cold,
pease porridge in the pot,
nine days old.

some like it hot,
some like it cold,
some like it in the pot,
nine days old.\
"""
    grammar = parse(iterable)
    # print(grammar)
    result = """\
0 -> 1 2 3 4 3 5 ↵ ↵ 6 2 7 4 7 5
1 -> p e a s 8 r r i d g 9                        pease_porridge_
2 -> h o t                                        hot
3 -> 10 1                                         ,↵pease_porridge_
4 -> c 11                                         cold
5 -> 12 _ t h 8 t 10 n 12 9 d a y s _ 11 .        in_the_pot,↵nine_days_old.
6 -> s o m 9 l i k 9 i t _                        some_like_it_
7 -> 10 6                                         ,↵some_like_it_
8 -> 9 p o                                        e_po
9 -> e _                                          e_
10 -> , ↵                                         ,↵
11 -> o l d                                       old
12 -> i n                                         in\
"""
    assert str(grammar) == result
    assert list(grammar.expand(0)) == list(iterable)


def test_genesis():
    with open(module_dir / 'genesis_input.txt', encoding='utf-8') as reader:
        iterable = reader.read()
    grammar = parse(iterable)
    # print(grammar)
    with open(module_dir / 'genesis_result.txt', encoding='utf-8') as reader:
        result = reader.read()
    assert result.endswith('\n')
    assert str(grammar) == result[:-1]
    assert list(grammar.expand(0)) == list(iterable)


def test_green_eggs_ham():
    with open(module_dir / 'iamsam_input.txt', encoding='utf-8') as reader:
        iterable = reader.read()
    grammar = parse(iterable)
    # print(grammar)
    with open(module_dir / 'iamsam_result.txt', encoding='utf-8') as reader:
        result = reader.read()
    assert result.endswith('\n')
    assert str(grammar) == result[:-1]
    assert list(grammar.expand(0)) == list(iterable)


def test_gc():
    with open(module_dir / 'iamsam_input.txt', encoding='utf-8') as reader:
        iterable = reader.read()
    parser = Parser()
    gc.collect()
    parser.feed(iterable)
    # gc.set_debug(gc.DEBUG_SAVEALL)
    assert gc.collect() == 0
    # print(gc.garbage)
    grammar = Grammar(parser.tree)
    # print(grammar)
    with open(module_dir / 'iamsam_result.txt', encoding='utf-8') as reader:
        result = reader.read()
    assert result.endswith('\n')
    assert str(grammar) == result[:-1]


def test_nums():
    iterable = [1, 2, 3, 4, 1, 2, 3, 5, 1, 2, 3]
    grammar = parse(iterable)
    # print(grammar)
    result = """\
0 -> 1 4 1 5 1
1 -> 1 2 3                                        123\
"""
    assert str(grammar) == result
    assert grammar.lengths() == {0: 11, 1: 3}
    assert grammar.counts() == {0: 1, 1: 3}
    assert grammar.depths() == {0: 0, 1: 1}
    assert list(grammar.expand(0)) == iterable


def benchmark_parsing(iterable):
    parser = Parser()
    parser.feed(iterable)


def test_benchmark_parsing(benchmark):
    rand = random.Random(0)
    iterable = rand.choices(string.ascii_lowercase, k=100_000)
    benchmark(benchmark_parsing, iterable)


def test_issue_7():
    # fmt: off
    grammar = parse([
        Mark(), 0, 18, 54, 22, Mark(), Mark(), 0, 0, 20, Mark(), 22, Mark(),
        24, Mark(), 0, 0, 20, 56, Mark(), 20, Mark(), 56, Mark(), 20, Mark(),
        18, 20, 20, Mark(), Mark(), 1, 15, 20, 20, 20, 20, Mark(), 0, 20, 20,
        40, Mark(), 20, Mark(), 20, 20, 56, Mark(), 20, 20, Mark(), 20, 20, 56,
        Mark(), 20, 20, Mark(), 24, 56, Mark(), Mark(), 20, 20, Mark(), 20, 43,
        Mark(), 55, Mark(), 20, 20, Mark(), 0, Mark(), 20, 38, Mark(), 20, 20,
        27, Mark(), 0, 10, 10, 41, Mark(), 20, Mark(), 55, 55, 20, 20, 20, 20,
        20, 35, Mark(), Mark(), 20, Mark(), Mark(), 0, 24, Mark(), Mark(), 22,
        Mark(), Mark(), 0, 0,
    ])
    # fmt: on
    assert grammar.lengths() == {0: 112, 1: 3, 2: 2, 3: 4, 4: 2, 5: 3}
    assert grammar.counts() == {0: 1, 1: 2, 2: 9, 3: 2, 4: 2, 5: 2}
    assert grammar.depths() == {0: 0, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1}
